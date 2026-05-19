"""
Debug script to find all connected clients on the network
Tests different endpoints to find network clients
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

CONTROLLER_IP = os.getenv("UNIFI_CONTROLLER_IP", "10.20.40.1")
SITE_ID = os.getenv("UNIFI_SITE_ID")
API_KEY = os.getenv("UNIFI_API_KEY")

if not SITE_ID or not API_KEY:
    print("❌ Missing credentials in .env")
    exit(1)

headers = {
    "X-API-KEY": API_KEY,
    "Accept": "application/json"
}

# Try different endpoints
endpoints = [
    f"/sites/{SITE_ID}/clients",
    f"/sites/{SITE_ID}/network-clients",
    f"/sites/{SITE_ID}/insights/device-list",
    f"/sites/{SITE_ID}/devices",  # We already know this one
]

for endpoint in endpoints:
    print(f"\n{'='*80}")
    print(f"Testing endpoint: {endpoint}")
    print(f"{'='*80}")

    url = f"https://{CONTROLLER_IP}/proxy/network/integration/v1{endpoint}"

    try:
        response = requests.get(
            url,
            headers=headers,
            verify=False,
            timeout=10
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                count = len(data.get("data", []))
                print(f"✓ Found {count} item(s)")

                if count > 0:
                    print("\nFirst item:")
                    print(json.dumps(data["data"][0], indent=2))
            else:
                print("Response:")
                print(json.dumps(data, indent=2))
        else:
            print(f"Error: {response.text[:200]}")

    except Exception as e:
        print(f"Error: {e}")
