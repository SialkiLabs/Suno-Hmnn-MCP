import os
from mcp.server.fastmcp import FastMCP
from core.client import SunoClient
from core.auth import get_headers

mcp = FastMCP("suno-premier-studio-os")
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

if __name__ == "__main__":
    mcp.run()
