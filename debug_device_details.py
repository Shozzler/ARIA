"""
Debug script to see detailed device data structure
Shows all available fields for each device
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

CONTROLLER_IP = os.getenv("UNIFI_CONTROLLER_IP", "10.20.40.1")
SITE_ID = os.getenv("UNIFI_SITE_ID")
API_KEY = os.getenv("UNIFI_API_KEY")

# Check if settings are available
if not SITE_ID or not API_KEY:
    print("❌ Missing UNIFI_SITE_ID or UNIFI_API_KEY in .env file")
    exit(1)

print("=" * 80)
print("Fetching detailed device information...")
print("=" * 80)

# Make request
url = f"https://{CONTROLLER_IP}/proxy/network/integration/v1/sites/{SITE_ID}/devices"
headers = {
    "X-API-KEY": API_KEY,
    "Accept": "application/json"
}

try:
    response = requests.get(
        url,
        headers=headers,
        verify=False,
        timeout=10
    )

    data = response.json()

    if "data" in data and len(data["data"]) > 0:
        print(f"\n✓ Found {len(data['data'])} device(s)\n")

        # Show each device with ALL available fields
        for i, device in enumerate(data["data"], 1):
            print("=" * 80)
            print(f"DEVICE {i}: {device.get('name', 'Unknown')}")
            print("=" * 80)
            print(json.dumps(device, indent=2))
            print()

        # Show available fields summary
        print("\n" + "=" * 80)
        print("AVAILABLE FIELDS SUMMARY:")
        print("=" * 80)
        if data["data"]:
            all_fields = set()
            for device in data["data"]:
                all_fields.update(device.keys())

            print(f"\nTotal unique fields across all devices: {len(all_fields)}")
            print("\nFields:")
            for field in sorted(all_fields):
                print(f"  • {field}")

except Exception as e:
    print(f"Error: {e}")
