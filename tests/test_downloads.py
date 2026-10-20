import socket
from pathlib import Path
import httpx
import pytest
import core.daw_exporter as module
from core.daw_exporter import download_audio_file, safe_destination, validate_audio_url

URL = "https://cdn1.suno.ai/track.mp3"
MP3 = b"ID3" + b"x" * 50
WAV = b"RIFF" + b"0000WAVE" + b"x" * 50


@pytest.fixture
def public_dns(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))],
    )


@pytest.mark.parametrize(
    "name",
    [
        "../escape",
        "../../escape",
        "/absolute",
        "a\\b",
        "CON",
        "a:stream",
        "a?",
        "a.",
        "a ",
        "a\n",
    ],
)
def test_rejects_unsafe_filename(name):
    with pytest.raises(ValueError):
        safe_destination(name, "mp3")


@pytest.mark.parametrize(
    "url",
    [
        "http://cdn1.suno.ai/a",
        "https://127.0.0.1/a",
        "https://cdn1.suno.ai.evil.invalid/a",
        "https://user:secret@cdn1.suno.ai/a",
        "https://cdn1.suno.ai:8080/a",
    ],
)
async def test_rejects_unapproved_url(url):
    with pytest.raises(ValueError):
        await validate_audio_url(url)


@pytest.mark.parametrize(
    "ip", ["127.0.0.1", "10.0.0.1", "169.254.169.254", "::1", "fc00::1"]
)
async def test_rejects_private_dns_resolution(monkeypatch, ip):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443))],
    )
    with pytest.raises(ValueError):
        await validate_audio_url(URL)


@pytest.mark.parametrize("body,fmt", [(MP3, "mp3"), (WAV, "wav")])
async def test_valid_download_is_atomically_saved(http_mock, public_dns, body, fmt):
    http_mock(lambda request: httpx.Response(200, content=body))
    result = await download_audio_file(URL, "song", fmt)
    assert result["status"] == "success"
    assert Path(result["file_path"]).read_bytes() == body
    assert not list(Path(result["file_path"]).parent.glob("*.part"))


async def test_mp3_cannot_be_mislabeled_wav(http_mock, public_dns):
    http_mock(lambda request: httpx.Response(200, content=MP3))
    result = await download_audio_file(URL, "song", "wav")
    assert "error" in result
    assert not list(module.output_directory().iterdir())


async def test_existing_file_is_not_overwritten(http_mock, public_dns):
    target = safe_destination("song", "mp3")
    target.write_bytes(b"original")
    result = await download_audio_file(URL, "song", "mp3")
    assert "error" in result and target.read_bytes() == b"original"


async def test_redirect_cannot_access_private_service(http_mock, public_dns):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(
            302, headers={"location": "http://169.254.169.254/secret"}
        )

    http_mock(handler)
    result = await download_audio_file(URL, "song", "mp3")
    assert "error" in result and len(calls) == 1


async def test_redirect_loop_is_bounded(http_mock, public_dns):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(302, headers={"location": URL})

    http_mock(handler)
    result = await download_audio_file(URL, "song", "mp3")
    assert "error" in result and len(calls) == module.MAX_REDIRECTS + 1


async def test_size_limit_is_enforced(http_mock, public_dns, monkeypatch):
    monkeypatch.setattr(module, "MAX_DOWNLOAD_BYTES", 5)
    http_mock(lambda request: httpx.Response(200, content=MP3))
    assert "error" in await download_audio_file(URL, "song", "mp3")


async def test_stream_size_limit_without_content_length(
    http_mock, public_dns, monkeypatch
):
    class Chunks(httpx.AsyncByteStream):
        async def __aiter__(self):
            yield MP3

    monkeypatch.setattr(module, "MAX_DOWNLOAD_BYTES", 5)
    http_mock(lambda request: httpx.Response(200, stream=Chunks()))
    assert "error" in await download_audio_file(URL, "song", "mp3")
    assert not list(module.output_directory().iterdir())


async def test_partial_file_is_removed_on_network_failure(http_mock, public_dns):
    class Broken(httpx.AsyncByteStream):
        async def __aiter__(self):
            yield MP3
            raise httpx.ReadError("offline interrupted")

    http_mock(lambda request: httpx.Response(200, stream=Broken()))
    assert "error" in await download_audio_file(URL, "song", "mp3")
    assert not list(module.output_directory().iterdir())


async def test_fake_environment_cannot_create_mock_audio(monkeypatch):
    monkeypatch.setenv("BYPASS_AUTH_FOR_TESTS", "1")
    result = await download_audio_file("https://example.invalid/a", "song", "mp3")
    assert "error" in result


def test_filename_extension_must_match_format():
    with pytest.raises(ValueError):
        safe_destination("song.mp3", "wav")
