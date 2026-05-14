"""
Debug script to see full device data structure

Reads settings from .env file
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get settings from .env
CONTROLLER_IP = os.getenv("UNIFI_CONTROLLER_IP", "10.20.40.1")
SITE_ID = os.getenv("UNIFI_SITE_ID")
API_KEY = os.getenv("UNIFI_API_KEY")

# Check if settings are available
if not SITE_ID:
    print("❌ UNIFI_SITE_ID not found in .env file")
    print("Please copy .env.example to .env and fill in your values")
    exit(1)

if not API_KEY:
    print("❌ UNIFI_API_KEY not found in .env file")
    print("Please copy .env.example to .env and fill in your values")
    exit(1)

print(f"✓ Using controller: {CONTROLLER_IP}")
print(f"✓ Using site ID: {SITE_ID}")
print(f"✓ Using API key: {API_KEY[:10]}... (hidden)")
print()

# Make request
url = f"https://{CONTROLLER_IP}/proxy/network/integration/v1/sites/{SITE_ID}/devices"
headers = {
    "X-API-KEY": API_KEY,
    "Accept": "application/json"
}

print(f"\nMaking request to: {url}")
print("=" * 80)

try:
    response = requests.get(
        url,
        headers=headers,
        verify=False,
        timeout=10
    )

    print(f"Status Code: {response.status_code}\n")

    data = response.json()

    if "data" in data and len(data["data"]) > 0:
        print(f"Found {len(data['data'])} device(s)\n")

        # Print first device completely to see structure
        print("=" * 80)
        print("FIRST DEVICE - FULL DATA:")
        print("=" * 80)
        print(json.dumps(data["data"][0], indent=2))

        print("\n" + "=" * 80)
        print("ALL DEVICES - SUMMARY:")
        print("=" * 80)

        for i, device in enumerate(data["data"], 1):
            print(f"\n{i}. Device:")
            print(f"   Name: {device.get('name', 'N/A')}")
            print(f"   Type: {device.get('type', 'N/A')}")
            print(f"   Model: {device.get('model', 'N/A')}")
            print(f"   IP: {device.get('ip', 'N/A')}")
            print(f"   MAC: {device.get('mac', 'N/A')}")
            print(f"   Status: {device.get('status', 'N/A')}")
            print(f"   Keys: {list(device.keys())}")

except Exception as e:
    print(f"Error: {e}")
