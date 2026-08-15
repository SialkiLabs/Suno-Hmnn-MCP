import os
import time
from enum import Enum
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP
from core.client import SunoClient
from core.database import db

mcp = FastMCP("Suno-Hmnn-MCP")
client = SunoClient()

# Enums for strong typing
class ModelVersion(str, Enum):
    CHIRP_V5_5_PRO = "chirp-v5-5-pro"
    CHIRP_V5_5 = "chirp-v5-5"
    CHIRP_V5 = "chirp-v5"
    CHIRP_V4 = "chirp-v4"
    CHIRP_V3_5 = "chirp-v3-5"
    CHIRP_V3 = "chirp-v3"

@mcp.tool()
async def suno_get_credits() -> dict:
    """Get current Suno Premier credit balance."""
    return await client.get_credits()

@mcp.tool()
async def suno_generate(
    prompt: str = Field("", description="Style/genre prompt or GPT description", max_length=3000),
    tags: str = Field("", description="Style tags (e.g. 'pop, upbeat, female vocal')", max_length=120),
    title: str = Field("", description="Title of the song"),
    make_instrumental: bool = Field(False, description="Set to True for instrumental only"),
    model_version: ModelVersion = Field(ModelVersion.CHIRP_V5_5_PRO, description="Suno model version to use"),
    custom_lyrics: str = Field("", description="Custom lyrics (if provided, prompt becomes style)"),
    wait_for_audio: bool = Field(True, description="Wait until generation completes and audio is ready")
) -> dict:
    """Generate new Suno music tracks (Custom Mode or Prompt Mode). Will wait for completion by default."""
    return await client.generate(
        prompt, tags, title, make_instrumental, model_version.value, custom_lyrics, wait_for_audio
    )

@mcp.tool()
async def suno_extend(
    clip_id: str = Field(..., description="ID of the clip to extend"),
    continue_at: float = Field(..., description="Timestamp in seconds to extend from"),
    prompt: str = Field("", description="Custom lyrics to continue with"),
    tags: str = Field("", description="Style tags"),
    title: str = Field("", description="New title"),
    model_version: ModelVersion = Field(ModelVersion.CHIRP_V5_5_PRO, description="Model version"),
    wait_for_audio: bool = Field(True, description="Wait until generation completes")
) -> dict:
    """Extend an existing clip starting at a specific timestamp."""
    return await client.extend(
        clip_id, continue_at, prompt, tags, title, model_version.value, wait_for_audio
    )

@mcp.tool()
async def suno_separate_stems(clip_id: str) -> dict:
    """Trigger Premier Stem Separation (Vocals vs Instrumental)."""
    return await client.separate_stems(clip_id)

@mcp.tool()
async def suno_get_clip(clip_id: str) -> dict:
    """Get metadata, audio URLs, stems status, and WAV download link."""
    return await client.get_clip(clip_id)

@mcp.tool()
async def suno_download_file(
    audio_url: str = Field(..., description="URL of the audio file to download"),
    filename: str = Field(..., description="Desired local filename (e.g. 'my_song')"),
    file_format: str = Field("wav", description="Format extension ('wav' or 'mp3')"),
    clip_id: str = Field(None, description="Optional clip ID to update in local database")
) -> dict:
    """
    Download high-fidelity WAV, MP3, or Stems to local storage directory.
    Uses async chunked streaming to prevent memory spikes.
    """
    from core.daw_exporter import download_audio_file
    return await download_audio_file(audio_url, filename, file_format, clip_id)

@mcp.tool()
async def suno_list_local_library(limit: int = 50) -> dict:
    """List recent tracks generated and tracked in the local SQLite database."""
    tracks = db.list_tracks(limit)
    return {"tracks": tracks, "count": len(tracks)}

@mcp.tool()
async def suno_auth_status() -> dict:
    """Check the health of the Token Rotation Engine."""
    from core.auth import auth_manager
    
    status = {
        "cookie_configured": bool(auth_manager.cookie),
        "jwt_configured_or_fetched": bool(auth_manager.jwt_token),
        "seconds_until_expiry": max(0, auth_manager.expires_at - time.time()) if auth_manager.expires_at else 0
    }
    
    # Attempt a forced refresh test if we have a cookie but no JWT
    if status["cookie_configured"] and not status["jwt_configured_or_fetched"]:
        success = await auth_manager._refresh_token()
        status["refresh_test_successful"] = success
        status["jwt_configured_or_fetched"] = bool(auth_manager.jwt_token)
        
    return status

if __name__ == "__main__":
    mcp.run()