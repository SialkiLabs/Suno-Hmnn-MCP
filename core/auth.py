import os
import time
import httpx
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
import asyncio

# Load the .env file automatically from the project root directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

class ClerkAuthManager:
    """
    Dual-layer authentication manager for Suno.
    Uses the session cookie to dynamically refresh Clerk Bearer JWTs.
    """
    def __init__(self):
        # Always reload on init to grab any live updates from wizard
        env_path = Path(__file__).parent.parent / ".env"
        load_dotenv(dotenv_path=env_path, override=True)
        
        self.cookie = os.getenv("SUNO_COOKIE", "")
        self.jwt_token = os.getenv("SUNO_SESSION_TOKEN", "")
        self.expires_at = 0.0
        
        # We need this header to convince Clerk we are a real browser
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        self._lock = asyncio.Lock()

    async def _refresh_token(self) -> bool:
        """
        Hits the Clerk frontend API to exchange the session cookie for a fresh JWT.
        """
        async with self._lock:
            # Check if someone else refreshed it while we were waiting for the lock
            if time.time() < self.expires_at and self.jwt_token:
                return True
                
            if not self.cookie:
                print("[Auth] No SUNO_COOKIE provided. Cannot refresh token.")
                return False
                
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [Auth] Refreshing Clerk JWT via Session Cookie...")
            
            url = "https://clerk.suno.com/v1/client?_clerk_js_version=4.73.4"
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "*/*",
                "Cookie": self.cookie,
                "Origin": "https://app.suno.ai",
                "Referer": "https://app.suno.ai/"
            }
            
            try:
                async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                    resp = await client.get(url, headers=headers)
                    
                if resp.status_code == 200:
                    data = resp.json()
                    
                    # Dig into Clerk's standard JSON response to find the active session JWT
                    sessions = data.get("response", {}).get("sessions", [])
                    if sessions:
                        active_session = sessions[0]
                        new_jwt = active_session.get("last_active_token", {}).get("jwt")
                        
                        if new_jwt:
                            self.jwt_token = new_jwt
                            # Clerk tokens usually last ~1 min to a few hours depending on their config.
                            # We force a refresh every 45 minutes to be safe.
                            self.expires_at = time.time() + (45 * 60)
                            print("[Auth] Successfully refreshed JWT.")
                            return True
                            
                    print("[Auth] Failed to parse JWT from Clerk response.")
                    return False
                else:
                    print(f"[Auth] Clerk rejected cookie. HTTP {resp.status_code}: {resp.text}")
                    return False
                    
            except Exception as e:
                print(f"[Auth] Network error during token refresh: {e}")
                return False

    async def get_valid_token(self) -> str:
        """Returns a valid JWT, refreshing it automatically if expired."""
        # If we have a JWT from the wizard, trust it on first boot (give it a 45 min lifespan)
        if self.jwt_token and self.expires_at == 0.0:
            self.expires_at = time.time() + (45 * 60)
            
        if not self.jwt_token or time.time() >= self.expires_at:
            success = await self._refresh_token()
            if not success and not self.jwt_token:
                raise RuntimeError("Failed to obtain a valid Suno authentication token.")
        
        return self.jwt_token

    async def get_headers(self) -> dict:
        """Returns the headers required for hitting Suno's internal API."""
        token = await self.get_valid_token()
        return {
            "User-Agent": self.user_agent,
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Authorization": f"Bearer {token}"
        }

# Global singleton instance for the app
auth_manager = ClerkAuthManager()

async def get_headers() -> dict:
    return await auth_manager.get_headers()