import os

def get_headers() -> dict:
    token = os.getenv("SUNO_SESSION_TOKEN", "")
    cookie = os.getenv("SUNO_COOKIE", "")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/json",
        "Accept": "*/*",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if cookie:
        headers["Cookie"] = cookie
    return headers
