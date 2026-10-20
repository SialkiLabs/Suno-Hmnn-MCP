"""All tests are offline. Unexpected HTTP and DNS access fail the test."""

import socket
import httpx
import pytest


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("SUNO_OUTPUT_DIR", str(tmp_path / "music"))
    monkeypatch.setenv("SUNO_DATABASE_PATH", str(tmp_path / "library.db"))
    for name in ("SUNO_COOKIE", "SUNO_SESSION_TOKEN", "BYPASS_AUTH_FOR_TESTS"):
        monkeypatch.delenv(name, raising=False)

    async def unexpected_http(*args, **kwargs):
        raise AssertionError("Unexpected network request in offline test")

    def unexpected_dns(*args, **kwargs):
        raise AssertionError("Unexpected DNS request in offline test")

    monkeypatch.setattr(
        httpx.AsyncHTTPTransport, "handle_async_request", unexpected_http
    )
    monkeypatch.setattr(socket, "getaddrinfo", unexpected_dns)


@pytest.fixture
def http_mock(monkeypatch):
    original = httpx.AsyncClient

    def install(handler):
        def client(*args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            return original(*args, **kwargs)

        monkeypatch.setattr(httpx, "AsyncClient", client)

    return install
