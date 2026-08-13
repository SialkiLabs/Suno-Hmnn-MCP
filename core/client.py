import httpx
from .auth import get_headers

class SunoClient:
    def __init__(self):
        self.app_url = "https://app.suno.ai"
        
    def _post(self, path: str, json_data: dict) -> dict:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(f"{self.app_url}{path}", headers=get_headers(), json=json_data)
            return resp.json() if resp.status_code in (200, 201) else {"error": resp.text}
            
    def _get(self, path: str) -> dict:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(f"{self.app_url}{path}", headers=get_headers())
            return resp.json() if resp.status_code == 200 else {"error": resp.text}

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
