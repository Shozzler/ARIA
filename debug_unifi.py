"""
Simple UniFi API debug script
"""

import requests
import json

# Your settings
CONTROLLER_IP = "10.20.40.1"
API_KEY = input("Enter API key: ").strip()

# Make request
url = f"https://{CONTROLLER_IP}/proxy/network/integration/v1/sites"
headers = {
    "X-API-KEY": API_KEY,
    "Accept": "application/json"
}

print(f"\nMaking request to: {url}")
print("=" * 60)

try:
    response = requests.get(
        url,
        headers=headers,
        verify=False,
        timeout=10
    )

    print(f"Status Code: {response.status_code}")
    print("\nRaw Response:")
    print(json.dumps(response.json(), indent=2))

except Exception as e:
    print(f"Error: {e}")
