import os
import time
import httpx
from datetime import datetime, timezone

class ClerkAuthManager:
    """
    Dual-layer authentication manager for Suno.
    Uses the session cookie to dynamically refresh Clerk Bearer JWTs.
    """
    def __init__(self):
        self.cookie = os.getenv("SUNO_COOKIE", "")
        self.jwt_token = os.getenv("SUNO_SESSION_TOKEN", "")
        self.expires_at = 0.0
        
        # We need this header to convince Clerk we are a real browser
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

    def _refresh_token(self) -> bool:
        """
        Hits the Clerk frontend API to exchange the session cookie for a fresh JWT.
        """
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
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, headers=headers)
                
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

    def get_valid_token(self) -> str:
        """Returns a valid JWT, refreshing it automatically if expired."""
        if not self.jwt_token or time.time() >= self.expires_at:
            success = self._refresh_token()
            if not success and not self.jwt_token:
                raise RuntimeError("Failed to obtain a valid Suno authentication token.")
        
        return self.jwt_token

    def get_headers(self) -> dict:
        """Returns the headers required for hitting Suno's internal API."""
        return {
            "User-Agent": self.user_agent,
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Authorization": f"Bearer {self.get_valid_token()}"
        }

# Global singleton instance for the app
auth_manager = ClerkAuthManager()

def get_headers() -> dict:
    return auth_manager.get_headers()
