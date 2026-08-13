import os
import httpx
from pathlib import Path

# Base directory for all music exports
OUTPUT_DIR = Path(os.getenv("SUNO_OUTPUT_DIR", r"C:\Users\Getko\hermy-hq\music-outputs"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def download_audio_file(audio_url: str, filename: str, file_format: str = "wav") -> dict:
    """
    Downloads an audio file from a given URL and saves it to the output directory.
    Supports .mp3, .wav, and stems.
    """
    if not audio_url:
        return {"error": "No audio URL provided for download."}
        
    if not filename.endswith(f".{file_format}"):
        filename = f"{filename}.{file_format}"
        
    save_path = OUTPUT_DIR / filename
    
    print(f"[Exporter] Downloading {file_format.upper()} to {save_path}...")
    
    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.get(audio_url)
            
            if resp.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(resp.content)
                print(f"[Exporter] Successfully saved {filename} ({len(resp.content)} bytes).")
                return {
                    "status": "success",
                    "file_path": str(save_path),
                    "size_bytes": len(resp.content),
                    "format": file_format
                }
            else:
                return {"error": f"Failed to download audio. HTTP {resp.status_code}", "details": resp.text}
                
    except Exception as e:
        return {"error": f"Network exception during download: {str(e)}"}
