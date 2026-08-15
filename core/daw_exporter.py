import os
import httpx
from pathlib import Path
import platformdirs
import aiofiles
from .database import db

# Force output to local dir to avoid isolated path permission errors
OUTPUT_DIR = Path(__file__).parent.parent / "music-outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

async def download_audio_file(audio_url: str, filename: str, file_format: str = "wav", clip_id: str = None) -> dict:
    """
    Downloads an audio file asynchronously in chunks to prevent memory spikes.
    Supports .mp3, .wav, and stems.
    """
    if not audio_url:
        return {"error": "No audio URL provided for download."}
        
    if not filename.endswith(f".{file_format}"):
        filename = f"{filename}.{file_format}"
        
    save_path = OUTPUT_DIR / filename
    
    print(f"[Exporter] Downloading {file_format.upper()} to {save_path}...")
    
    try:
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            async with client.stream("GET", audio_url) as response:
                if response.status_code == 200:
                    async with aiofiles.open(save_path, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            await f.write(chunk)
                            
                    size = os.path.getsize(save_path)
                    print(f"[Exporter] Successfully saved {filename} ({size} bytes).")
                    
                    # Update DB if clip_id is known
                    if clip_id:
                        db.update_track_status(clip_id, "downloaded", local_path=str(save_path))
                        
                    return {
                        "status": "success",
                        "file_path": str(save_path),
                        "size_bytes": size,
                        "format": file_format
                    }
                else:
                    return {"error": f"Failed to download audio. HTTP {response.status_code}"}
                    
    except Exception as e:
        return {"error": f"Network exception during download: {str(e)}"}