"""Interactive local sign-in. Credentials are plaintext and must stay private."""

import asyncio
import os
import tempfile
from pathlib import Path

from core.auth import auth_manager
from core.client import SunoClient


def capture_cookies(context):
    cookies = [
        c
        for c in context.cookies()
        if c["domain"].lstrip(".")
        in {"suno.ai", "suno.com", "app.suno.ai", "clerk.suno.com"}
    ]
    if not any(c["name"] == "__session" for c in cookies):
        return None
    return "; ".join(f"{c['name']}={c['value']}" for c in cookies)


def save_credentials(path, cookie, token):
    if any(c in cookie + token for c in '\r\n"\\'):
        raise ValueError("Credentials contain unsupported environment-file characters")
    fd, temporary = tempfile.mkstemp(prefix=".suno-credentials-", dir=path.parent)
    try:
        # mkstemp uses owner-only permissions on systems that support them.
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(f'SUNO_COOKIE="{cookie}"\nSUNO_SESSION_TOKEN="{token}"\n')
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


async def verify_and_save(cookie, path):
    auth_manager.cookie = cookie
    if not await auth_manager._refresh_token(force=True):
        return False
    credits = await SunoClient().get_credits()
    if "error" in credits:
        return False
    save_credentials(path, cookie, auth_manager.jwt_token)
    return True


def main():
    import time
    from playwright.sync_api import sync_playwright

    root = Path(__file__).resolve().parent
    cookie = None
    print(
        "Sign in to Suno in the isolated browser window. No generation will be submitted."
    )
    with sync_playwright() as playwright:
        context = None
        for channel in ("chrome", "msedge", None):
            try:
                options = {
                    "user_data_dir": str(root / ".chrome_auth_profile"),
                    "headless": False,
                }
                if channel:
                    options["channel"] = channel
                context = playwright.chromium.launch_persistent_context(**options)
                break
            except Exception:
                continue
        if context is None:
            raise SystemExit(
                "Could not open a browser. Install Chrome/Edge or run playwright install chromium."
            )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://suno.com/")
            for _ in range(300):
                cookie = capture_cookies(context)
                if cookie:
                    break
                time.sleep(2)
        finally:
            context.close()
    if not cookie:
        raise SystemExit("Sign-in timed out. No credentials saved.")
    if not asyncio.run(verify_and_save(cookie, root / ".env")):
        raise SystemExit(
            "Could not verify session access. No credentials saved. Service access may have changed."
        )
    print(
        "Session access verified. Credentials saved locally in .env as plaintext. Keep it private."
    )


if __name__ == "__main__":
    main()
