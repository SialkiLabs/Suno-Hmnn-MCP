import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

# Ensure core modules can be imported
sys.path.insert(0, str(Path(__file__).parent))
from core.auth import auth_manager
from core.client import SunoClient

def print_header():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=" * 60)
    print(" 🎵 SUNO-HMNN-MCP : Enterprise Studio OS Setup Wizard 🎵 ")
    print("=" * 60)
    print("Launching secure browser for authentication...\n")

def main():
    print_header()
    
    session_cookie = None
    
    try:
        with sync_playwright() as p:
            print("[+] Opening browser... Please log in to your Suno account.")
            # Launch visible browser
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.goto("https://app.suno.ai/")
            
            print("[*] Waiting for successful login... (Please log in normally. Do not close the browser!)")
            
            # Poll for the __session cookie
            max_retries = 150 # 5 minutes max wait
            for _ in range(max_retries):
                cookies = context.cookies()
                for c in cookies:
                    if c['name'] == '__session' and 'suno.ai' in c['domain']:
                        session_cookie = f"__session={c['value']}"
                        break
                
                if session_cookie:
                    break
                    
                time.sleep(2)
                
            if not session_cookie:
                print("\n❌ Error: Login timed out or cookie not found.")
                browser.close()
                sys.exit(1)
                
            print("\n[+] Login detected! Capturing secure session...")
            # Give it a tiny bit of time to settle just in case
            time.sleep(2)
            browser.close()
            
    except Exception as e:
        print(f"\n❌ Browser automation error: {e}")
        print("Ensure you have run: playwright install chromium")
        sys.exit(1)
        
    # -----------------------------------------
    # Verification & Tier Check
    # -----------------------------------------
    print("[+] Testing connection to Suno Authentication Servers...")
    auth_manager.cookie = session_cookie
    
    success = auth_manager._refresh_token()
    if not success:
        print("❌ Error: Failed to generate a JWT from the captured session.")
        sys.exit(1)
        
    print("✅ Authentication Successful! Valid JWT Bearer Token generated.")
    
    print("\n[+] Testing Premier Client Access & Account Tier...")
    client = SunoClient()
    credits_info = client.get_credits()
    
    if "error" in credits_info:
        print(f"❌ Error fetching credits: {credits_info['error']}")
        sys.exit(1)
    else:
        balance = credits_info.get("total_credits_left", "Unknown")
        plan = credits_info.get("plan_name", "Free")
        
        print("=" * 40)
        print(f"✅ Connection Verified!")
        print(f"👤 Account Tier : {plan}")
        print(f"🪙 Credits Left : {balance}")
        print("=" * 40)
        
        if plan and ("Premier" in plan or "Pro" in plan):
            print("[*] Tier Status: PREMIER capabilities UNLOCKED (WAV, Stems, Extensions).")
        else:
            print("[*] Tier Status: FREE tier detected. Advanced features will be restricted.")
        
    # Securely save to .env
    env_path = Path(".env")
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(f'SUNO_COOKIE="{session_cookie}"\n')
        f.write(f'SUNO_PLAN="{plan}"\n')
        
    print(f"\n🎉 Setup Complete! Configuration saved securely to {env_path.absolute()}")
    print("\nYou can now plug this MCP server into Hermes Agent, Antigravity IDE, or Claude.")
    print("Run `fastmcp run server.py:mcp` to start the engine.\n")

if __name__ == "__main__":
    main()
