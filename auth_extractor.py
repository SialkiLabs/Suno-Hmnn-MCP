import rookiepy
import json

def get_suno_cookies():
    try:
        # Load cookies from all major browsers
        cookies = rookiepy.load()
        suno_cookie_str = ""
        for cookie in cookies:
            if "suno.com" in cookie["domain"] or "suno.ai" in cookie["domain"]:
                suno_cookie_str += f"{cookie['name']}={cookie['value']}; "
        
        if suno_cookie_str:
            print("Successfully extracted Suno cookies from active browser!")
            return suno_cookie_str
        else:
            print("No Suno cookies found in any browser. Please log into Suno.com on your normal browser first.")
            return None
    except Exception as e:
        print(f"Error extracting cookies: {e}")
        return None

if __name__ == "__main__":
    c = get_suno_cookies()
    if c:
        with open(".suno_auth.json", "w") as f:
            json.dump({"SUNO_COOKIE": c}, f, indent=4)
        print("Injected into JSON vault!")
