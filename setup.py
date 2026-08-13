import os
import sys
import time
import getpass
from pathlib import Path

# Ensure core modules can be imported
sys.path.insert(0, str(Path(__file__).parent))
from core.auth import auth_manager
from core.client import SunoClient

def clear_screen():
    # Safe usage: os.name is a system constant ('nt' or 'posix'), no external input
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("=" * 60)
    print(" 🎵 SUNO-HMNN-MCP : Enterprise Studio OS Setup Wizard 🎵 ")
    print("=" * 60)
    print("This wizard will securely configure your local bridge to Suno AI.\n")

def main():
    clear_screen()
    print_header()
    
    print("Step 1: Suno Authentication")
    print("We need your Suno Session Cookie to generate API tokens on the fly.")
    print("1. Go to https://app.suno.ai in your browser and log in.")
    print("2. Open Developer Tools (F12) -> Application -> Cookies.")
    print("3. Copy the entire 'Cookie' string.")
    
    # Use getpass to hide the cookie input so it isn't printed on the screen (security)
    cookie_input = getpass.getpass("\nPaste your Suno Cookie (input will be hidden): ").strip()
    
    if not cookie_input:
        print("\n❌ Error: Cookie cannot be empty. Setup aborted.")
        sys.exit(1)
        
    print("\n[+] Testing connection to Suno Authentication Servers...")
    # Inject directly for testing
    auth_manager.cookie = cookie_input
    
    success = auth_manager._refresh_token()
    if not success:
        print("❌ Error: Failed to generate a JWT from that cookie. Please ensure it is valid and has not expired.")
        sys.exit(1)
        
    print("✅ Authentication Successful! Valid JWT Bearer Token generated.")
    
    print("\n[+] Testing Premier Client Access...")
    client = SunoClient()
    credits_info = client.get_credits()
    
    if "error" in credits_info:
        print(f"❌ Error fetching credits: {credits_info['error']}")
    else:
        balance = credits_info.get("total_credits_left", "Unknown")
        plan = credits_info.get("plan_name", "Free")
        print(f"✅ Connection Verified! Plan: {plan} | Credits Remaining: {balance}")
        
    # Securely save to .env
    env_path = Path(".env")
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(f'SUNO_COOKIE="{cookie_input}"\n')
        
    print(f"\n🎉 Setup Complete! Configuration saved securely to {env_path.absolute()}")
    print("\nYou can now plug this MCP server into Hermes Agent, Antigravity IDE, or Claude.")
    print("Run `fastmcp run server.py:mcp` to test it.\n")

if __name__ == "__main__":
    main()
