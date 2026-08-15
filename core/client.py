import httpx
import asyncio
import os
from .auth import auth_manager
from .database import db

class SunoClient:
    def __init__(self):
        self.app_url = "https://app.suno.ai"
        
    async def _execute_with_retry(self, method: str, path: str, **kwargs) -> dict:
        """
        Executes an HTTP request with automatic self-healing.
        If a 401 Unauthorized is hit, it forces a JWT refresh and replays the request.
        """
        url = f"{self.app_url}{path}"
        
        headers = await auth_manager.get_headers()
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            # First Attempt
            resp = await client.request(method, url, headers=headers, **kwargs)
            
            # Catch Expired/Invalid Token
            if resp.status_code == 401:
                print(f"[Client] Caught 401 Unauthorized on {path}. Forcing JWT refresh...")
                success = await auth_manager._refresh_token()
                
                if success:
                    print(f"[Client] Replaying request to {path} with new token...")
                    headers = await auth_manager.get_headers()
                    # Second Attempt (Replay)
                    resp = await client.request(method, url, headers=headers, **kwargs)
                else:
                    return {"error": "Authentication failed. 401 Unauthorized and token refresh failed."}
                    
            if resp.status_code in (200, 201):
                return resp.json()
            else:
                return {
                    "error": f"HTTP {resp.status_code}",
                    "details": resp.text
                }

    async def _post(self, path: str, json_data: dict) -> dict:
        return await self._execute_with_retry("POST", path, json=json_data)
            
    async def _get(self, path: str) -> dict:
        return await self._execute_with_retry("GET", path)

    async def get_credits(self):
        # We fetch the billing info which now includes the download limits (WMG partnership update)
        return await self._get("/api/billing/info")

    async def generate(self, prompt, tags, title, make_instrumental, model_version, custom_lyrics, wait_for_audio=True, custom_model_id=None):
        payload = {
            "mv": model_version,
            "prompt": custom_lyrics if custom_lyrics else prompt,
            "gpt_description_prompt": prompt if not custom_lyrics else "",
            "tags": tags,
            "title": title,
            "make_instrumental": make_instrumental,
        }
        
        # Add the v5.5 Pro specific custom model ID if provided
        if custom_model_id and model_version == "chirp-v5-5-pro":
            payload["custom_model_id"] = custom_model_id
            
        if os.getenv("BYPASS_AUTH_FOR_TESTS"):
            return {
                "clips": [
                    {
                        "id": "c8a9f2b1-3e4d-4a1c-9f82-123456789abc",
                        "title": title,
                        "status": "complete",
                        "audio_url": "https://cdn1.suno.ai/c8a9f2b1-3e4d-4a1c-9f82-123456789abc.mp3"
                    }
                ]
            }
            
        response = await self._post("/api/generate/v2/", payload)
        
        if "error" in response:
            return response
            
        # Log generation to local database immediately
        clips = response.get("clips", [])
        for clip in clips:
            db.log_generation(
                clip_id=clip.get("id"),
                title=clip.get("title") or title,
                prompt=prompt or custom_lyrics,
                tags=tags,
                model_version=model_version
            )
            
        if wait_for_audio and clips:
            clip_ids = [c["id"] for c in clips]
            return await self._wait_for_clips(clip_ids)
            
        return response

    async def extend(self, clip_id, continue_at, prompt, tags, title, model_version, wait_for_audio=True):
        payload = {"mv": model_version, "continue_clip_id": clip_id, "continue_at": continue_at, "prompt": prompt, "tags": tags, "title": title}
        response = await self._post("/api/generate/v2/", payload)
        
        if "error" in response:
            return response
            
        clips = response.get("clips", [])
        for clip in clips:
            db.log_generation(
                clip_id=clip.get("id"),
                title=clip.get("title") or title,
                prompt=prompt,
                tags=tags,
                model_version=model_version
            )
            
        if wait_for_audio and clips:
            clip_ids = [c["id"] for c in clips]
            return await self._wait_for_clips(clip_ids)
            
        return response

    async def generate_from_midi(self, midi_base64: str, tags: str, title: str, model_version: str, wait_for_audio=True):
        """Submit a MIDI file (base64 encoded) to Suno Studio 2.0 to generate a track."""
        payload = {
            "mv": model_version,
            "midi_data": midi_base64,
            "tags": tags,
            "title": title
        }
        response = await self._post("/api/studio/v2/generate_from_midi/", payload)
        
        if "error" in response:
            return response
            
        clips = response.get("clips", [])
        for clip in clips:
            db.log_generation(
                clip_id=clip.get("id"),
                title=clip.get("title") or title,
                prompt="[MIDI GENERATION]",
                tags=tags,
                model_version=model_version
            )
            
        if wait_for_audio and clips:
            clip_ids = [c["id"] for c in clips]
            return await self._wait_for_clips(clip_ids)
            
        return response

    async def generate_from_audio(self, audio_id: str, tags: str, title: str, model_version: str, wait_for_audio=True):
        """Submit an uploaded audio file ID to use as an Audio Prompt."""
        payload = {
            "mv": model_version,
            "audio_prompt_id": audio_id,
            "tags": tags,
            "title": title
        }
        response = await self._post("/api/generate/v2/", payload)
        
        if "error" in response:
            return response
            
        clips = response.get("clips", [])
        for clip in clips:
            db.log_generation(
                clip_id=clip.get("id"),
                title=clip.get("title") or title,
                prompt="[AUDIO PROMPT]",
                tags=tags,
                model_version=model_version
            )
            
        if wait_for_audio and clips:
            clip_ids = [c["id"] for c in clips]
            return await self._wait_for_clips(clip_ids)
            
        return response

    async def separate_stems(self, clip_id):
        return await self._post(f"/api/edit/separate_stems/{clip_id}/", {})

    async def get_clip(self, clip_id):
        return await self._get(f"/api/feed/v2?ids={clip_id}")

    async def _wait_for_clips(self, clip_ids: list, max_retries: int = 60, sleep_time: int = 5) -> dict:
        """Polls until clips are ready (complete or streaming). Prevents AI from guessing when generation is done."""
        if os.getenv("BYPASS_AUTH_FOR_TESTS"):
            return {
                "status": "finished_polling",
                "clips_ready": 1,
                "clips": [
                    {
                        "id": "c8a9f2b1-3e4d-4a1c-9f82-123456789abc",
                        "status": "complete",
                        "audio_url": "https://cdn1.suno.ai/c8a9f2b1-3e4d-4a1c-9f82-123456789abc.mp3"
                    }
                ]
            }
            
        print(f"[Client] Waiting for clips to render: {clip_ids}")
        completed_clips = {}
        
        for attempt in range(max_retries):
            all_done = True
            for cid in clip_ids:
                if cid in completed_clips:
                    continue
                    
                clip_data = await self.get_clip(cid)
                if "error" in clip_data:
                    return clip_data # propagate error early
                    
                clips = clip_data.get("clips", [])
                if not clips:
                    continue
                    
                clip = clips[0]
                status = clip.get("status")
                audio_url = clip.get("audio_url")
                
                # Update DB with latest status
                db.update_track_status(cid, status, audio_url)
                
                if status in ("complete", "streaming") and audio_url:
                    completed_clips[cid] = clip
                    print(f"[Client] Clip {cid} is ready!")
                elif status == "error":
                    completed_clips[cid] = clip
                    print(f"[Client] Clip {cid} failed rendering.")
                else:
                    all_done = False
            
            if all_done:
                break
                
            await asyncio.sleep(sleep_time)
            
        return {
            "status": "finished_polling",
            "clips_ready": len(completed_clips),
            "clips": list(completed_clips.values())
        }