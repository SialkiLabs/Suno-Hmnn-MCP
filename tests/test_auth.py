import base64
import json
import time
from types import SimpleNamespace
import httpx
import pytest
from core.auth import ClerkAuthManager, token_expiry


def jwt(expiry):
    payload = (
        base64.urlsafe_b64encode(json.dumps({"exp": expiry}).encode())
        .decode()
        .rstrip("=")
    )
    return f"header.{payload}.signature"


def manager():
    auth = ClerkAuthManager()
    auth.cookie = "__client=offline-dummy"
    auth.jwt_token = ""
    auth.expires_at = 0
    return auth


@pytest.mark.parametrize("value", ["", "broken", "a.b.c", "a.e30.c", None, 12])
def test_invalid_token_has_no_invented_lifetime(value):
    assert token_expiry(value) == 0


async def test_refresh_attaches_cookie_and_reads_expiry(http_mock):
    token = jwt(time.time() + 3600)

    def handler(request):
        assert request.headers["cookie"] == "__client=offline-dummy"
        return httpx.Response(
            200,
            json={"response": {"sessions": [{"last_active_token": {"jwt": token}}]}},
        )

    http_mock(handler)
    auth = manager()
    assert await auth._refresh_token()
    assert auth.jwt_token == token
    assert auth.expires_at == token_expiry(token)


async def test_forced_refresh_replaces_cached_rejected_token(http_mock):
    calls = []
    token = jwt(time.time() + 7200)

    def handler(request):
        calls.append(request)
        return httpx.Response(
            200,
            json={"response": {"sessions": [{"last_active_token": {"jwt": token}}]}},
        )

    http_mock(handler)
    auth = manager()
    auth.jwt_token = jwt(time.time() + 3600)
    auth.expires_at = time.time() + 3600
    assert await auth._refresh_token(force=True, rejected_token=auth.jwt_token)
    assert len(calls) == 1 and auth.jwt_token == token


async def test_concurrent_refresh_reuses_new_token():
    auth = manager()
    auth.jwt_token = jwt(time.time() + 3600)
    auth.expires_at = time.time() + 3600
    assert await auth._refresh_token(force=True, rejected_token="previous-token")


@pytest.mark.parametrize("status", [401, 403, 500])
async def test_rejected_refresh_cannot_use_old_token(http_mock, status):
    http_mock(lambda request: httpx.Response(status, text="SECRET_RESPONSE"))
    auth = manager()
    auth.jwt_token = "stale"
    assert not await auth._refresh_token(force=True)
    assert auth.jwt_token == ""
    with pytest.raises(RuntimeError):
        await auth.get_valid_token()


async def test_expired_token_from_response_is_rejected(http_mock):
    http_mock(
        lambda request: httpx.Response(
            200,
            json={
                "response": {
                    "sessions": [{"last_active_token": {"jwt": jwt(time.time() - 60)}}]
                }
            },
        )
    )
    assert not await manager()._refresh_token()


async def test_invalid_cookie_is_not_silently_rewritten():
    auth = manager()
    auth.cookie = "secret\nheader"
    assert not await auth._refresh_token()


async def test_refresh_does_not_log_body_or_cookie(http_mock, caplog):
    http_mock(lambda request: httpx.Response(403, text="SECRET_RESPONSE"))
    auth = manager()
    assert not await auth._refresh_token(force=True)
    assert "SECRET_RESPONSE" not in caplog.text and auth.cookie not in caplog.text
