import httpx
import asyncio
from .auth import auth_manager
from .database import db


class SunoClient:
    def __init__(self):
        self.app_url = "https://app.suno.ai"

    async def _execute_with_retry(self, method: str, path: str, **kwargs) -> dict:
        """Retry only an explicit authentication rejection, never an ambiguous write."""
        try:
            headers = await auth_manager.get_headers()
            async with httpx.AsyncClient(
                timeout=30.0, follow_redirects=False
            ) as client:
                response = await client.request(
                    method, f"{self.app_url}{path}", headers=headers, **kwargs
                )
                if response.status_code == 401:
                    rejected = headers.get("Authorization", "").removeprefix("Bearer ")
                    if not await auth_manager._refresh_token(
                        force=True, rejected_token=rejected
                    ):
                        return {"error": "authentication_failed"}
                    headers = await auth_manager.get_headers()
                    response = await client.request(
                        method, f"{self.app_url}{path}", headers=headers, **kwargs
                    )
                if response.status_code not in (200, 201):
                    return {
                        "error": "http_error",
                        "http_status": response.status_code,
                        "submission_state": "unknown"
                        if method == "POST" and response.status_code >= 500
                        else "rejected",
                    }
                data = response.json()
                if not isinstance(data, dict):
                    return {
                        "error": "unexpected_response_shape",
                        "submission_state": "unknown"
                        if method == "POST"
                        else "not_applicable",
                    }
                return data
        except RuntimeError:
            return {"error": "authentication_unavailable"}
        except (httpx.HTTPError, ValueError):
            # A timeout after POST does not establish whether a billed operation was accepted.
            return {
                "error": "request_failed",
                "submission_state": "unknown" if method == "POST" else "not_applicable",
                "details": "Do not automatically resubmit an uncertain generation.",
            }

    async def _post(self, path: str, json_data: dict) -> dict:
        return await self._execute_with_retry("POST", path, json=json_data)

    async def _get(self, path: str) -> dict:
        return await self._execute_with_retry("GET", path)

    async def get_credits(self):
        # We fetch the billing info which now includes the download limits (WMG partnership update)
        return await self._get("/api/billing/info")

    async def generate(
        self,
        prompt,
        tags,
        title,
        make_instrumental,
        model_version,
        custom_lyrics,
        wait_for_audio=True,
        custom_model_id=None,
    ):
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
                model_version=model_version,
            )

        if wait_for_audio and clips:
            clip_ids = [c["id"] for c in clips]
            return await self._wait_for_clips(clip_ids)

        return response

    async def extend(
        self,
        clip_id,
        continue_at,
        prompt,
        tags,
        title,
        model_version,
        wait_for_audio=True,
    ):
        payload = {
            "mv": model_version,
            "continue_clip_id": clip_id,
            "continue_at": continue_at,
            "prompt": prompt,
            "tags": tags,
            "title": title,
        }
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
                model_version=model_version,
            )

        if wait_for_audio and clips:
            clip_ids = [c["id"] for c in clips]
            return await self._wait_for_clips(clip_ids)

        return response

    async def generate_from_midi(
        self,
        midi_base64: str,
        tags: str,
        title: str,
        model_version: str,
        wait_for_audio=True,
    ):
        """Submit a MIDI file (base64 encoded) to Suno Studio 2.0 to generate a track."""
        payload = {
            "mv": model_version,
            "midi_data": midi_base64,
            "tags": tags,
            "title": title,
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
                model_version=model_version,
            )

        if wait_for_audio and clips:
            clip_ids = [c["id"] for c in clips]
            return await self._wait_for_clips(clip_ids)

        return response

    async def generate_from_audio(
        self,
        audio_id: str,
        tags: str,
        title: str,
        model_version: str,
        wait_for_audio=True,
    ):
        """Submit an uploaded audio file ID to use as an Audio Prompt."""
        payload = {
            "mv": model_version,
            "audio_prompt_id": audio_id,
            "tags": tags,
            "title": title,
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
                model_version=model_version,
            )

        if wait_for_audio and clips:
            clip_ids = [c["id"] for c in clips]
            return await self._wait_for_clips(clip_ids)

        return response

    async def separate_stems(self, clip_id):
        return await self._post(f"/api/edit/separate_stems/{clip_id}/", {})

    async def get_clip(self, clip_id):
        return await self._get(f"/api/feed/v2?ids={clip_id}")

    async def _wait_for_clips(
        self, clip_ids: list, max_retries: int = 60, sleep_time: int = 5
    ) -> dict:
        """Report previews, failures and timeouts separately from completed audio."""
        if not clip_ids:
            return {"status": "empty", "clips_ready": 0, "clips_failed": 0, "clips": []}
        observed = {}
        expected = set(clip_ids)
        for attempt in range(max_retries):
            for cid in clip_ids:
                previous = observed.get(cid, {})
                if previous.get("status") == "error" or (
                    previous.get("status") == "complete" and previous.get("audio_url")
                ):
                    continue
                data = await self.get_clip(cid)
                if "error" in data:
                    return {
                        **data,
                        "status": "polling_failed",
                        "clips": list(observed.values()),
                    }
                clips = data.get("clips", [])
                match = next((c for c in clips if c.get("id") == cid), None)
                if match is not None:
                    observed[cid] = match
                    db.update_track_status(
                        cid, match.get("status", "unknown"), match.get("audio_url")
                    )
            ready = sum(
                c.get("status") == "complete" and bool(c.get("audio_url"))
                for c in observed.values()
            )
            failed = sum(c.get("status") == "error" for c in observed.values())
            if ready + failed == len(expected):
                state = (
                    "complete"
                    if ready == len(expected)
                    else ("failed" if ready == 0 else "partial_failure")
                )
                return {
                    "status": state,
                    "clips_ready": ready,
                    "clips_failed": failed,
                    "clips": list(observed.values()),
                }
            if attempt + 1 < max_retries:
                await asyncio.sleep(sleep_time)
        return {
            "status": "timed_out",
            "clips_ready": sum(
                c.get("status") == "complete" and bool(c.get("audio_url"))
                for c in observed.values()
            ),
            "clips_failed": sum(c.get("status") == "error" for c in observed.values()),
            "pending_clip_ids": [
                cid
                for cid in clip_ids
                if observed.get(cid, {}).get("status") != "error"
                and not (
                    observed.get(cid, {}).get("status") == "complete"
                    and observed.get(cid, {}).get("audio_url")
                )
            ],
            "clips": list(observed.values()),
        }
