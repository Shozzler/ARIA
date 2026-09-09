import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

CONTROLLER_IP = os.getenv("UNIFI_CONTROLLER_IP", "10.20.40.1")
SITE_ID = os.getenv("UNIFI_SITE_ID")
API_KEY = os.getenv("UNIFI_API_KEY")

headers = {
    "X-API-KEY": API_KEY,
    "Accept": "application/json"
}

url = f"https://{CONTROLLER_IP}/proxy/network/integration/v1/sites/{SITE_ID}/network/status"

response = requests.get(url, headers=headers, verify=False, timeout=10)

print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))
