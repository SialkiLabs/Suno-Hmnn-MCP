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

def capture_cookies(context):
    cookies = context.cookies()
    has_session = any(c['name'] == '__session' and ('suno.ai' in c['domain'] or 'suno.com' in c['domain']) for c in cookies)
    if has_session:
        cookie_pairs = [f"{c['name']}={c['value']}" for c in cookies if 'suno.ai' in c['domain'] or 'suno.com' in c['domain']]
        return "; ".join(cookie_pairs)
    return None

def main():
    print_header()
    full_cookie_string = None
    
    possible_profile_dirs = [
        Path(__file__).parent / "suno_auth_profile",
        Path(__file__).parent.parent / "suno_auth_profile"
    ]

    with sync_playwright() as p:
        print("[+] Checking existing browser sessions silently...")
        for profile_dir in possible_profile_dirs:
            if not profile_dir.exists():
                continue
            try:
                for channel in ["chrome", "msedge"]:
                    try:
                        context = p.chromium.launch_persistent_context(
                            user_data_dir=str(profile_dir),
                            headless=True,
                            channel=channel,
                            args=["--disable-blink-features=AutomationControlled"]
                        )
                        page = context.pages[0] if context.pages else context.new_page()
                        page.goto("https://app.suno.ai/", wait_until="domcontentloaded", timeout=10000)
                        time.sleep(2)
                        
                        full_cookie_string = capture_cookies(context)
                        context.close()
                        
                        if full_cookie_string:
                            print(f"✅ Active session found in {channel.upper()} profile! Proceeding...")
                            break
                    except Exception:
                        continue
                if full_cookie_string:
                    break
            except Exception:
                pass

        if not full_cookie_string:
            print("\n[+] Launching Chrome... Please complete your Suno login.")
            target_dir = possible_profile_dirs[0]
            context = None
            for channel in ["chrome", "msedge"]:
                try:
                    context = p.chromium.launch_persistent_context(
                        user_data_dir=str(target_dir),
                        headless=False,
                        channel=channel,
                        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
                        ignore_default_args=["--enable-automation"],
                        viewport={"width": 1200, "height": 800}
                    )
                    print(f"[*] Launched native {channel.upper()}!")
                    break
                except Exception:
                    continue

            if not context:
                print("\n❌ Error: Could not launch Chrome or Edge.")
                sys.exit(1)

            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://app.suno.ai/")
            
            print("[*] Waiting for login...")
            for _ in range(300):
                full_cookie_string = capture_cookies(context)
                if full_cookie_string:
                    break
                time.sleep(2)

            context.close()

    if not full_cookie_string:
        print("\n❌ Error: Login timed out or cookies not found.")
        sys.exit(1)

    # 1. Test JWT Generation
    print("\n[+] Testing connection to Suno Authentication Servers...")
    auth_manager.cookie = full_cookie_string
    
    success = auth_manager._refresh_token()
    if not success:
        print("❌ Error: Failed to generate a JWT from the captured session.")
        sys.exit(1)
        
    print("✅ Authentication Successful! Valid JWT Bearer Token generated.")
    
    # 2. SAVE CREDENTIALS IMMEDIATELY!
    env_path = Path(__file__).parent / ".env"
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(f'SUNO_COOKIE="{full_cookie_string}"\n')
        # 1. Capture the raw JWT from the frontend API directly via the live browser context
        # This gives us a guaranteed-fresh Bearer token without relying on the python backend
        try:
            page = browser.contexts[0].new_page()
            # Navigate to the clerk client API to extract the token directly
            page.goto("https://clerk.suno.com/v1/client?_clerk_js_version=4.73.4", wait_until="networkidle")
            response_text = page.locator("body").inner_text()
            
            jwt_token = ""
            import json
            data = json.loads(response_text)
            sessions = data.get("response", {}).get("sessions", [])
            if sessions:
                jwt_token = sessions[0].get("last_active_token", {}).get("jwt", "")
                
            if jwt_token:
                f.write(f'SUNO_SESSION_TOKEN="{jwt_token}"\n')
            page.close()
        except Exception as e:
            pass
            
        f.write('SUNO_PLAN="Premier"\n')
        
    print(f"🎉 Credentials saved securely to {env_path.absolute()}")

    # 3. Secondary Informational Check (Credits / Tier)
    import asyncio
    print("\n[+] Testing Premier Client Access & Account Tier...")
    client = SunoClient()
    
    # We force the auth manager to reload from the newly written .env
    from dotenv import load_dotenv
    # explicitly parse the file we just wrote instead of relying on os.environ overwriting bugs
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("SUNO_COOKIE="):
                auth_manager.cookie = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("SUNO_SESSION_TOKEN="):
                auth_manager.jwt_token = line.split("=", 1)[1].strip().strip('"')
    
    credits_info = asyncio.run(client.get_credits())
    
    if "error" in credits_info:
        print(f"⚠️ Note: Credit status check returned ({credits_info['error']}), but authentication is active.")
    else:
        balance = credits_info.get("total_credits_left", "Unknown")
        plan = credits_info.get("plan_name", "Premier")
        
        print("=" * 40)
        print(f"✅ Connection Verified!")
        print(f"👤 Account Tier : {plan}")
        print(f"🪙 Credits Left : {balance}")
        print("=" * 40)
        
    print("\nYou can now plug this MCP server into Hermes Agent, Antigravity IDE, or Claude.\n")

if __name__ == "__main__":
    main()
