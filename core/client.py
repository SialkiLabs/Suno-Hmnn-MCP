import httpx
from .auth import auth_manager

class SunoClient:
    def __init__(self):
        self.app_url = "https://app.suno.ai"
        
    def _execute_with_retry(self, method: str, path: str, **kwargs) -> dict:
        """
        Executes an HTTP request with automatic self-healing.
        If a 401 Unauthorized is hit, it forces a JWT refresh and replays the request.
        """
        url = f"{self.app_url}{path}"
        
        with httpx.Client(timeout=30.0) as client:
            # First Attempt
            resp = client.request(method, url, headers=auth_manager.get_headers(), **kwargs)
            
            # Catch Expired/Invalid Token
            if resp.status_code == 401:
                print(f"[Client] Caught 401 Unauthorized on {path}. Forcing JWT refresh...")
                success = auth_manager._refresh_token()
                
                if success:
                    print(f"[Client] Replaying request to {path} with new token...")
                    # Second Attempt (Replay)
                    resp = client.request(method, url, headers=auth_manager.get_headers(), **kwargs)
                else:
                    return {"error": "Authentication failed. 401 Unauthorized and token refresh failed."}
                    
            if resp.status_code in (200, 201):
                return resp.json()
            else:
                return {
                    "error": f"HTTP {resp.status_code}",
                    "details": resp.text
                }

    def _post(self, path: str, json_data: dict) -> dict:
        return self._execute_with_retry("POST", path, json=json_data)
            
    def _get(self, path: str) -> dict:
        return self._execute_with_retry("GET", path)

    def get_credits(self):
        return self._get("/api/billing/info/")

    def generate(self, prompt, tags, title, make_instrumental, model_version, custom_lyrics):
        payload = {
            "mv": model_version,
            "prompt": custom_lyrics if custom_lyrics else prompt,
            "gpt_description_prompt": prompt if not custom_lyrics else "",
            "tags": tags,
            "title": title,
            "make_instrumental": make_instrumental,
        }
        return self._post("/api/generate/v2/", payload)

    def extend(self, clip_id, continue_at, prompt, tags, title, model_version):
        payload = {"mv": model_version, "continue_clip_id": clip_id, "continue_at": continue_at, "prompt": prompt, "tags": tags, "title": title}
        return self._post("/api/generate/v2/", payload)

    def separate_stems(self, clip_id):
        return self._post(f"/api/edit/separate_stems/{clip_id}/", {})

    def get_clip(self, clip_id):
        return self._get(f"/api/feed/v2?ids={clip_id}")
