import requests
import json

TOKEN_FILE = "data/homeconnect_tokens.json"
API_BASE = "https://simulator.home-connect.com/api"


def load_access_token():
    with open(TOKEN_FILE, "r") as file:
        tokens = json.load(file)
    return tokens["access_token"]


def main():
    access_token = load_access_token()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.bsh.sdk.v1+json"
    }

    response = requests.get(f"{API_BASE}/homeappliances", headers=headers)

    if response.status_code != 200:
        print(f"Error response ({response.status_code}):")
        print(response.text)

    response.raise_for_status()

    data = response.json()
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()