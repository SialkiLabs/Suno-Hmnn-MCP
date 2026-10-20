import os
import stat
from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
import wizard


async def test_failed_auth_does_not_save_credentials(monkeypatch, tmp_path):
    auth = SimpleNamespace(
        cookie="", jwt_token="", _refresh_token=AsyncMock(return_value=False)
    )
    monkeypatch.setattr(wizard, "auth_manager", auth)
    target = tmp_path / ".env"
    assert not await wizard.verify_and_save("dummy", target)
    assert not target.exists()
    auth._refresh_token.assert_awaited_once_with(force=True)


async def test_success_requires_awaited_auth_and_credits(monkeypatch, tmp_path):
    auth = SimpleNamespace(
        cookie="", jwt_token="dummy-token", _refresh_token=AsyncMock(return_value=True)
    )
    monkeypatch.setattr(wizard, "auth_manager", auth)
    monkeypatch.setattr(
        wizard,
        "SunoClient",
        lambda: SimpleNamespace(get_credits=AsyncMock(return_value={"credits": 1})),
    )
    target = tmp_path / ".env"
    assert await wizard.verify_and_save("dummy-cookie", target)
    assert 'SUNO_SESSION_TOKEN="dummy-token"' in target.read_text()
    if os.name != "nt":
        assert stat.S_IMODE(target.stat().st_mode) == 0o600


async def test_credit_check_failure_does_not_save(monkeypatch, tmp_path):
    auth = SimpleNamespace(
        cookie="", jwt_token="dummy", _refresh_token=AsyncMock(return_value=True)
    )
    monkeypatch.setattr(wizard, "auth_manager", auth)
    monkeypatch.setattr(
        wizard,
        "SunoClient",
        lambda: SimpleNamespace(
            get_credits=AsyncMock(return_value={"error": "denied"})
        ),
    )
    assert not await wizard.verify_and_save("dummy", tmp_path / ".env")
    assert not (tmp_path / ".env").exists()


def test_unsafe_credential_does_not_overwrite_existing_file(tmp_path):
    target = tmp_path / ".env"
    target.write_text("original")
    with pytest.raises(ValueError):
        wizard.save_credentials(target, "bad\nvalue", "token")
    assert target.read_text() == "original"


def test_anonymous_client_cookie_is_not_a_completed_login():
    context = SimpleNamespace(
        cookies=lambda: [
            {"domain": ".suno.com", "name": "__client", "value": "anonymous"}
        ]
    )
    assert wizard.capture_cookies(context) is None


def test_cookie_capture_restricts_domains():
    context = SimpleNamespace(
        cookies=lambda: [
            {"domain": ".suno.com", "name": "__session", "value": "offline-session"},
            {
                "domain": "suno.com.evil.invalid",
                "name": "secret",
                "value": "do-not-capture",
            },
        ]
    )
    assert wizard.capture_cookies(context) == "__session=offline-session"
