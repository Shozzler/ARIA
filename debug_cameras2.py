"""
Debug script to find Ubiquiti Protect camera endpoints
Trying different base paths
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
print("Testing Ubiquiti Protect Camera API Endpoints")
print("=" * 80)

headers = {
    "X-API-KEY": API_KEY,
    "Accept": "application/json"
}

# Try different base paths and endpoints
tests = [
    # Direct protect API
    ("https://{ip}/api/protect/cameras", "Direct Protect API"),
    ("https://{ip}/api/bootstrap/cameras", "Bootstrap API"),
    ("https://{ip}/protect/api/cameras", "Protect API v2"),

    # Through proxy with different paths
    ("https://{ip}/proxy/protect/api/cameras", "Proxy Protect API"),
    ("https://{ip}/proxy/protect/cameras", "Proxy Protect"),

    # Alternative paths
    ("https://{ip}/api/cameras", "Root API Cameras"),
    ("https://{ip}/api/v1/cameras", "Root API v1"),
]

for url_template, description in tests:
    url = url_template.format(ip=CONTROLLER_IP)

    print(f"\n{'='*80}")
    print(f"{description}")
    print(f"URL: {url}")
    print(f"{'='*80}")

    try:
        response = requests.get(
            url,
            headers=headers,
            verify=False,
            timeout=10
        )

        print(f"Status: {response.status_code}")

        if response.status_code in [200, 201]:
            data = response.json()
            print("✓ SUCCESS!")
            print("\nResponse preview:")
            print(json.dumps(data, indent=2)[:500])
        else:
            print(f"Status: {response.status_code}")

    except Exception as e:
        print(f"Error: {str(e)[:100]}")

print("\n" + "=" * 80)
print("Done!")
print("=" * 80)
