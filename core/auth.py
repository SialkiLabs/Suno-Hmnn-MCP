"""Consumer-session authentication. This is not Suno Platform API access."""

import asyncio
import base64
import json
import logging
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
# Explicit process environment takes precedence over the local credential file.
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)


def token_expiry(token: str) -> float:
    """Read exp only to schedule refresh, not to authenticate or verify a JWT."""
    if not isinstance(token, str):
        return 0.0
    try:
        payload = token.split(".")[1]
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        expiry = float(data["exp"])
        return expiry if expiry > 0 else 0.0
    except (IndexError, KeyError, ValueError, TypeError, UnicodeError):
        return 0.0


class ClerkAuthManager:
    def __init__(self):
        self.cookie = os.getenv("SUNO_COOKIE", "")
        self.jwt_token = os.getenv("SUNO_SESSION_TOKEN", "")
        # An unknown expiry must not be replaced with an invented token lifetime.
        self.expires_at = token_expiry(self.jwt_token)
        self._lock = asyncio.Lock()
        auth_file = Path(__file__).resolve().parent.parent / ".suno_auth.json"
        if auth_file.exists() and not self.cookie:
            try:
                data = json.loads(auth_file.read_text(encoding="utf-8"))
                self.cookie = data.get("SUNO_COOKIE", "")
                if not self.jwt_token:
                    self.jwt_token = data.get("SUNO_SESSION_TOKEN", "")
                    self.expires_at = token_expiry(self.jwt_token)
            except (OSError, ValueError, TypeError):
                logger.warning("Could not load local authentication file")

    async def _refresh_token(
        self, force: bool = False, rejected_token: str | None = None
    ) -> bool:
        async with self._lock:
            valid = bool(self.jwt_token) and time.time() + 10 < self.expires_at
            # A concurrent request may already have replaced the rejected token.
            if valid and (
                not force
                or (rejected_token is not None and self.jwt_token != rejected_token)
            ):
                return True
            if force:
                self.jwt_token = ""
                self.expires_at = 0.0
            if not isinstance(self.cookie, str) or not self.cookie:
                return False
            # Reject malformed credentials instead of silently mutating them.
            if any(ord(c) < 32 or ord(c) > 126 for c in self.cookie):
                logger.warning("Session cookie has invalid header characters")
                return False
            headers = {
                "Cookie": self.cookie,
                "Accept": "application/json",
                "Origin": "https://suno.com",
                "Referer": "https://suno.com/",
            }
            try:
                async with httpx.AsyncClient(
                    timeout=10.0, follow_redirects=False
                ) as client:
                    response = await client.get(
                        "https://clerk.suno.com/v1/client?_clerk_js_version=4.73.4",
                        headers=headers,
                    )
                if response.status_code != 200:
                    logger.warning(
                        "Session refresh rejected (HTTP %s)", response.status_code
                    )
                    return False
                sessions = response.json().get("response", {}).get("sessions", [])
                for session in sessions:
                    token = session.get("last_active_token", {}).get("jwt", "")
                    expiry = token_expiry(token)
                    if token and expiry > time.time() + 10:
                        self.jwt_token, self.expires_at = token, expiry
                        return True
                return False
            except (httpx.HTTPError, ValueError, TypeError, AttributeError):
                logger.warning(
                    "Session refresh failed; credentials and response body withheld"
                )
                return False

    async def get_valid_token(self) -> str:
        if not self.jwt_token or time.time() + 10 >= self.expires_at:
            if not await self._refresh_token():
                raise RuntimeError(
                    "Authentication expired or unavailable. Run the setup wizard again."
                )
        return self.jwt_token

    async def get_headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {await self.get_valid_token()}",
        }


auth_manager = ClerkAuthManager()


async def get_headers() -> dict:
    return await auth_manager.get_headers()
