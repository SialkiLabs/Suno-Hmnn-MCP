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
    # Safe usage: os.name is a system constant
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=" * 60)
    print(" 🎵 SUNO-HMNN-MCP : Enterprise Studio OS Setup Wizard 🎵 ")
    print("=" * 60)
    print("Launching your NATIVE browser to bypass Google security blocks...\n")

def main():
    print_header()
    
    full_cookie_string = None
    
    try:
        with sync_playwright() as p:
            print("[+] Booting native Chrome/Edge...")
            user_data_dir = os.path.join(os.getcwd(), "suno_auth_profile")
            
            context = None
            for channel in ["msedge", "chrome"]:
                try:
                    context = p.chromium.launch_persistent_context(
                        user_data_dir=user_data_dir,
                        headless=False,
                        channel=channel,
                        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
                        ignore_default_args=["--enable-automation"],
                        viewport={"width": 1200, "height": 800}
                    )
                    print(f"[*] Successfully launched native {channel.upper()}!")
                    break
                except Exception:
                    continue
                    
            if not context:
                print("\n❌ Error: Could not launch native Microsoft Edge or Google Chrome.")
                sys.exit(1)

            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://app.suno.ai/")
            
            print("[*] Waiting for successful login... (Please log in normally. Do not close the browser!)")
            
            # Poll for the __session cookie and bundle ALL cookies together
            max_retries = 150 # 5 minutes max wait
            for _ in range(max_retries):
                cookies = context.cookies()
                has_session = any(c['name'] == '__session' and ('suno.ai' in c['domain'] or 'suno.com' in c['domain']) for c in cookies)
                
                if has_session:
                    # Construct full authentic cookie string containing ALL Suno cookies
                    cookie_pairs = []
                    for c in cookies:
                        if 'suno.ai' in c['domain'] or 'suno.com' in c['domain']:
                            cookie_pairs.append(f"{c['name']}={c['value']}")
                    
                    full_cookie_string = "; ".join(cookie_pairs)
                    break
                    
                time.sleep(2)
                
            if not full_cookie_string:
                print("\n❌ Error: Login timed out or cookies not found.")
                context.close()
                sys.exit(1)
                
            print("\n[+] Login detected! Capturing complete secure cookie bundle...")
            time.sleep(2)
            context.close()
            
    except Exception as e:
        print(f"\n❌ Browser automation error: {e}")
        sys.exit(1)
        
    # -----------------------------------------
    # Verification & Tier Check
    # -----------------------------------------
    print("[+] Testing connection to Suno Authentication Servers...")
    auth_manager.cookie = full_cookie_string
    
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
        f.write(f'SUNO_COOKIE="{full_cookie_string}"\n')
        f.write(f'SUNO_PLAN="{plan}"\n')
        
    print(f"\n🎉 Setup Complete! Configuration saved securely to {env_path.absolute()}")
    print("\nYou can now plug this MCP server into Hermes Agent, Antigravity IDE, or Claude.")
    print("Run `fastmcp run server.py:mcp` to start the engine.\n")

if __name__ == "__main__":
    main()
