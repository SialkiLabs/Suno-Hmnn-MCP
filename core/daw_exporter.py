"""Restricted audio downloads. File extensions never perform conversion."""

import asyncio
import ipaddress
import logging
import os
import re
import socket
import tempfile
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import aiofiles
import httpx
from .database import db
from .paths import output_directory

logger = logging.getLogger(__name__)
ALLOWED_AUDIO_HOSTS = frozenset(
    {"cdn1.suno.ai", "cdn2.suno.ai", "cdn1.suno.com", "cdn2.suno.com"}
)
MAX_DOWNLOAD_BYTES = 250 * 1024 * 1024
MAX_REDIRECTS = 3


async def validate_audio_url(url: str) -> str:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in ALLOWED_AUDIO_HOSTS
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
    ):
        raise ValueError(
            "Only HTTPS audio URLs on approved Suno CDN hosts are accepted"
        )
    addresses = await asyncio.to_thread(
        socket.getaddrinfo, parsed.hostname, 443, type=socket.SOCK_STREAM
    )
    if not addresses or any(
        not ipaddress.ip_address(row[4][0]).is_global for row in addresses
    ):
        raise ValueError("Audio host must resolve to public network addresses")
    return url


def safe_destination(filename: str, file_format: str) -> Path:
    if file_format not in {"mp3", "wav"}:
        raise ValueError("file_format must be mp3 or wav")
    if (
        not filename
        or filename in {".", ".."}
        or len(filename) > 160
        or re.search(r'[<>:"/\\|?*\x00-\x1f]', filename)
        or filename.endswith((".", " "))
    ):
        raise ValueError("filename must be a plain local filename")
    if filename.split(".")[0].upper() in {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *{f"COM{i}" for i in range(1, 10)},
        *{f"LPT{i}" for i in range(1, 10)},
    }:
        raise ValueError("Reserved filename")
    suffix = Path(filename).suffix
    if suffix and suffix.lower() != f".{file_format}":
        raise ValueError("Filename extension does not match file_format")
    if not suffix:
        filename += f".{file_format}"
    root = output_directory()
    root.mkdir(parents=True, exist_ok=True)
    target = root / filename
    if target.is_symlink() or target.exists() or target.resolve().parent != root:
        raise ValueError("Destination must be a new file inside the output directory")
    return target


def matches_format(prefix: bytes, file_format: str) -> bool:
    if file_format == "wav":
        return (
            len(prefix) >= 12
            and prefix[:4] in (b"RIFF", b"RF64")
            and prefix[8:12] == b"WAVE"
        )
    return prefix.startswith(b"ID3") or (
        len(prefix) >= 2 and prefix[0] == 255 and prefix[1] & 224 == 224
    )


async def download_audio_file(
    audio_url: str, filename: str, file_format: str = "wav", clip_id: str | None = None
) -> dict:
    temporary = None
    try:
        target = safe_destination(filename, file_format)
        async with httpx.AsyncClient(
            timeout=120.0, follow_redirects=False, trust_env=False
        ) as client:
            for redirect in range(MAX_REDIRECTS + 1):
                await validate_audio_url(audio_url)
                async with client.stream("GET", audio_url) as response:
                    if response.status_code in (301, 302, 303, 307, 308):
                        if redirect == MAX_REDIRECTS or not response.headers.get(
                            "location"
                        ):
                            raise ValueError(
                                "Audio redirect limit exceeded or missing target"
                            )
                        audio_url = urljoin(audio_url, response.headers["location"])
                        continue
                    if response.status_code != 200:
                        return {
                            "error": "download_http_error",
                            "http_status": response.status_code,
                        }
                    length = response.headers.get("content-length")
                    if length and int(length) > MAX_DOWNLOAD_BYTES:
                        raise ValueError("Audio exceeds the download size limit")
                    descriptor, name = tempfile.mkstemp(
                        prefix=".suno-", suffix=".part", dir=target.parent
                    )
                    os.close(descriptor)
                    temporary = Path(name)
                    size, prefix = 0, b""
                    async with aiofiles.open(temporary, "wb") as stream:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            size += len(chunk)
                            if size > MAX_DOWNLOAD_BYTES:
                                raise ValueError(
                                    "Audio exceeds the download size limit"
                                )
                            if len(prefix) < 16:
                                prefix = (prefix + chunk)[:16]
                            await stream.write(chunk)
                    if not matches_format(prefix, file_format):
                        raise ValueError(
                            "Audio signature does not match the requested format; no conversion performed"
                        )
                    if (
                        length
                        and not response.headers.get("content-encoding")
                        and size != int(length)
                    ):
                        raise ValueError("Audio download is incomplete")
                    # Atomic publication without overwriting an existing file or symlink.
                    os.link(temporary, target)
                    result = {
                        "status": "success",
                        "file_path": str(target),
                        "size_bytes": size,
                        "format": file_format,
                    }
                    if clip_id:
                        try:
                            db.update_track_status(
                                clip_id, "downloaded", local_path=str(target)
                            )
                        except Exception:
                            logger.warning(
                                "Audio saved, but local library update failed"
                            )
                            result["library_updated"] = False
                    return result
        return {"error": "download_unavailable"}
    except (ValueError, OSError, httpx.HTTPError):
        logger.warning(
            "Audio download failed; URL, credentials, and response body withheld"
        )
        return {
            "error": "download_rejected_or_failed",
            "details": "Check URL permissions, filename, size, network access, and actual audio format.",
        }
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
