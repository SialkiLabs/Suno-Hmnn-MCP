import asyncio
import sys
from core.client import SunoClient
from core.daw_exporter import download_audio_file

async def main():
    client = SunoClient()
    
    tags = "news broadcast countdown, dramatic orchestral, electronic pulse, ticking clock, suspense, urgent, instrumental"
    prompt = """[Intro | Ticking Clock | Urgent Synth Pulse]
[Build | Staccato Strings | Deep Bass Hits]
[Climax | Explosive Brass | Fast Paced News Theme]
[Outro | gradual fade | solo ticking clock]

[Silence]"""
    
    print("[*] Submitting generation request to Suno (chirp-v5-5-pro)...")
    res = await client.generate(
        prompt=prompt,
        tags=tags,
        title="Bombiel TV News Countdown",
        make_instrumental=True,
        model_version="chirp-v5-5-pro",
        custom_lyrics="",
        wait_for_audio=True
    )
    
    if "error" in res:
        print(f"❌ ERROR: {res['error']}")
        if "details" in res:
            print(f"Details: {res['details']}")
        sys.exit(1)
        
    clips = res.get("clips", [])
    if not clips:
        print("❌ No clips returned.")
        sys.exit(1)
        
    clip = clips[0]
    audio_url = clip.get("audio_url")
    clip_id = clip.get("id")
    
    print(f"[*] Generation successful! Clip ID: {clip_id}")
    
    if audio_url:
        print(f"[*] Downloading audio...")
        dl = await download_audio_file(audio_url, f"bombiel_tv_countdown_{clip_id}", "mp3", clip_id)
        if "error" not in dl:
            print(f"✅ MEDIA_PATH: {dl['file_path']}")
        else:
            print(f"❌ Download error: {dl['error']}")
    else:
        print("❌ Audio URL not found in response.")

asyncio.run(main())
