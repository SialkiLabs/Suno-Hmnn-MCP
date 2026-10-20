from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
import httpx
import pytest
import core.client as module
from core.client import SunoClient


def prepare(monkeypatch, get_clip):
    client = SunoClient()
    client.get_clip = get_clip
    monkeypatch.setattr(module, "db", SimpleNamespace(update_track_status=Mock()))
    return client


async def test_empty_feed_is_polled_again(monkeypatch):
    get = AsyncMock(
        side_effect=[
            {"clips": []},
            {"clips": [{"id": "a", "status": "complete", "audio_url": "url"}]},
        ]
    )
    result = await prepare(monkeypatch, get)._wait_for_clips(
        ["a"], max_retries=2, sleep_time=0
    )
    assert result["status"] == "complete" and get.await_count == 2


async def test_streaming_is_not_completed_audio(monkeypatch):
    get = AsyncMock(
        return_value={
            "clips": [{"id": "a", "status": "streaming", "audio_url": "preview"}]
        }
    )
    result = await prepare(monkeypatch, get)._wait_for_clips(
        ["a"], max_retries=2, sleep_time=0
    )
    assert result["status"] == "timed_out" and result["clips_ready"] == 0
    assert result["pending_clip_ids"] == ["a"]


async def test_failed_clip_is_not_counted_ready(monkeypatch):
    get = AsyncMock(return_value={"clips": [{"id": "a", "status": "error"}]})
    result = await prepare(monkeypatch, get)._wait_for_clips(["a"], sleep_time=0)
    assert (
        result["status"] == "failed"
        and result["clips_ready"] == 0
        and result["clips_failed"] == 1
    )


async def test_mixed_results_are_partial_failure(monkeypatch):
    get = AsyncMock(
        side_effect=[
            {"clips": [{"id": "a", "status": "complete", "audio_url": "url"}]},
            {"clips": [{"id": "b", "status": "error"}]},
        ]
    )
    result = await prepare(monkeypatch, get)._wait_for_clips(["a", "b"], sleep_time=0)
    assert result["status"] == "partial_failure" and result["clips_ready"] == 1


async def test_wrong_clip_id_cannot_complete_request(monkeypatch):
    get = AsyncMock(
        return_value={
            "clips": [{"id": "other", "status": "complete", "audio_url": "url"}]
        }
    )
    result = await prepare(monkeypatch, get)._wait_for_clips(
        ["a"], max_retries=1, sleep_time=0
    )
    assert result["status"] == "timed_out"


async def test_polling_failure_remains_failure(monkeypatch):
    get = AsyncMock(return_value={"error": "http_error"})
    result = await prepare(monkeypatch, get)._wait_for_clips(["a"], sleep_time=0)
    assert result["status"] == "polling_failed"


@pytest.fixture
def auth(monkeypatch):
    auth = SimpleNamespace(
        get_headers=AsyncMock(return_value={"Authorization": "Bearer offline"}),
        _refresh_token=AsyncMock(return_value=True),
    )
    monkeypatch.setattr(module, "auth_manager", auth)
    return auth


async def test_explicit_401_is_refreshed_once(http_mock, auth):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(401 if len(calls) == 1 else 200, json={"clips": []})

    http_mock(handler)
    result = await SunoClient()._post("/offline", {})
    assert result == {"clips": []} and len(calls) == 2
    auth._refresh_token.assert_awaited_once_with(force=True, rejected_token="offline")


async def test_second_401_is_not_retried_again(http_mock, auth):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(401)

    http_mock(handler)
    result = await SunoClient()._post("/offline", {})
    assert result["http_status"] == 401 and len(calls) == 2


async def test_ambiguous_submission_is_not_replayed(http_mock, auth):
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("offline timeout", request=request)

    http_mock(handler)
    result = await SunoClient()._post("/offline", {})
    assert result["submission_state"] == "unknown" and len(calls) == 1


async def test_http_error_hides_sensitive_body(http_mock, auth):
    http_mock(lambda request: httpx.Response(403, text="SECRET_BODY"))
    result = await SunoClient()._get("/offline")
    assert "SECRET_BODY" not in str(result)


async def test_old_test_environment_cannot_fabricate_generation(monkeypatch):
    monkeypatch.setenv("BYPASS_AUTH_FOR_TESTS", "1")
    client = SunoClient()
    client._post = AsyncMock(return_value={"error": "offline"})
    result = await client.generate(
        "p", "t", "title", True, "unverified-model", "", False
    )
    assert result == {"error": "offline"}
    client._post.assert_awaited_once()


async def test_server_error_keeps_submission_state_unknown(http_mock, auth):
    http_mock(lambda request: httpx.Response(503))
    result = await SunoClient()._post("/offline", {})
    assert result["submission_state"] == "unknown"
