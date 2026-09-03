import requests
import os
import webbrowser
import json
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs

load_dotenv()

CLIENT_ID = os.getenv("HOMECONNECT_CLIENT_ID")
CLIENT_SECRET = os.getenv("HOMECONNECT_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:5000/homeconnect/callback"
AUTH_BASE = "https://simulator.home-connect.com/security/oauth"

TOKEN_FILE = "data/homeconnect_tokens.json"


def save_tokens(tokens):
    """Save the tokens to a file so we don't have to log in every time."""
    os.makedirs("data", exist_ok=True)
    with open(TOKEN_FILE, "w") as file:
        json.dump(tokens, file, indent=2)
    print(f"Tokens saved to {TOKEN_FILE}")
    
def get_authorize_url():
    return (
        f"{AUTH_BASE}/authorize"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&scope=IdentifyAppliance"
        f"&redirect_uri={REDIRECT_URI}"
    )

def exchange_code_for_token(code):
    response = requests.post(
        f"{AUTH_BASE}/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
            "code": code
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if response.status_code != 200:
        print(f"Error response ({response.status_code}):")
        print(response.text)

    response.raise_for_status()
    return response.json()

def main():
    url = get_authorize_url()
    print("\nOpening your browser to log in...")
    print(f"(If it doesn't open automatically, visit this URL: {url})\n")

    webbrowser.open(url)

    print("Your browser will try to redirect to a page that doesn't exist yet")
    print("(localhost:5000/homeconnect/callback) - that's expected, ignore the error page.")
    print("Just copy the FULL URL from your browser's address bar once it redirects.\n")

    redirected_url = input("Paste the full redirected URL here: ").strip()

    parsed_url = urlparse(redirected_url)
    query_params = parse_qs(parsed_url.query)
    code = query_params.get("code", [None])[0]

    if not code:
        print("Couldn't find a 'code' in that URL. Did something go wrong?")
        return

    tokens = exchange_code_for_token(code)

    print("\nSuccess! Login worked.")
    print(f"Access token starts with: {tokens['access_token'][:15]}...")
    print(f"Expires in: {tokens['expires_in']} seconds")

    save_tokens(tokens)

if __name__ == "__main__":
    main()