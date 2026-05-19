"""
Debug script to find Ubiquiti Protect camera endpoints
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
    print("❌ Missing credentials")
    exit(1)

print("=" * 80)
print("Testing Ubiquiti Protect Camera Endpoints")
print("=" * 80)

headers = {
    "X-API-KEY": API_KEY,
    "Accept": "application/json"
}

# Try different camera endpoints
endpoints = [
    f"/sites/{SITE_ID}/cameras",
    f"/sites/{SITE_ID}/protect/cameras",
    "/cameras",
    "/protect/cameras",
    f"/api/sites/{SITE_ID}/cameras",
    f"/api/protect/cameras",
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
            print("✓ SUCCESS!")
            print("\nResponse structure:")
            if isinstance(data, dict) and "data" in data:
                count = len(data.get("data", []))
                print(f"Found {count} item(s)")
                if count > 0:
                    print("\nFirst item:")
                    print(json.dumps(data["data"][0], indent=2))
            else:
                print(json.dumps(data, indent=2)[:500])
        elif response.status_code == 404:
            print("❌ Endpoint not found (404)")
        else:
            print(f"⚠️ Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")

    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("Testing complete!")
print("=" * 80)
