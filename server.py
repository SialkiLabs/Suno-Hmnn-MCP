import os
from mcp.server.fastmcp import FastMCP
from core.client import SunoClient
from core.auth import get_headers

mcp = FastMCP("Suno-Hmnn-MCP")
client = SunoClient()

@mcp.tool()
def suno_get_credits() -> dict:
    """Get current Suno Premier credit balance."""
    return client.get_credits()

@mcp.tool()
def suno_generate(prompt: str = "", tags: str = "", title: str = "", make_instrumental: bool = False, model_version: str = "chirp-v4", custom_lyrics: str = "") -> dict:
    """Generate new Suno music tracks (Custom Mode or Prompt Mode)."""
    return client.generate(prompt, tags, title, make_instrumental, model_version, custom_lyrics)

@mcp.tool()
def suno_extend(clip_id: str, continue_at: float, prompt: str = "", tags: str = "", title: str = "", model_version: str = "chirp-v4") -> dict:
    """Extend an existing clip starting at timestamp continue_at (in seconds)."""
    return client.extend(clip_id, continue_at, prompt, tags, title, model_version)

@mcp.tool()
def suno_separate_stems(clip_id: str) -> dict:
    """Trigger Premier Stem Separation (Vocals vs Instrumental)."""
    return client.separate_stems(clip_id)

@mcp.tool()
def suno_get_clip(clip_id: str) -> dict:
    """Get metadata, audio URLs, stems status, and WAV download link."""
    return client.get_clip(clip_id)

@mcp.tool()
def suno_auth_status() -> dict:
    """Check the health of the Token Rotation Engine."""
    from core.auth import auth_manager
    import time
    
    status = {
        "cookie_configured": bool(auth_manager.cookie),
        "jwt_configured_or_fetched": bool(auth_manager.jwt_token),
        "seconds_until_expiry": max(0, auth_manager.expires_at - time.time()) if auth_manager.expires_at else 0
    }
    
    # Attempt a forced refresh test if we have a cookie but no JWT
    if status["cookie_configured"] and not status["jwt_configured_or_fetched"]:
        success = auth_manager._refresh_token()
        status["refresh_test_successful"] = success
        status["jwt_configured_or_fetched"] = bool(auth_manager.jwt_token)
        
    return status

if __name__ == "__main__":
    mcp.run()
