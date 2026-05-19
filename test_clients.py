"""
Test script to check if clients are being fetched properly
"""

import os
from dotenv import load_dotenv
from src.integrations.unifi import UniFiClient

load_dotenv()

CONTROLLER_IP = os.getenv("UNIFI_CONTROLLER_IP", "10.20.40.1")
SITE_ID = os.getenv("UNIFI_SITE_ID")
API_KEY = os.getenv("UNIFI_API_KEY")

if not SITE_ID or not API_KEY:
    print("❌ Missing credentials")
    exit(1)

print("Testing UniFiClient.get_all_clients()...\n")

client = UniFiClient(
    controller_ip=CONTROLLER_IP,
    api_key=API_KEY,
    verify_ssl=False
)

# Test getting clients
clients = client.get_all_clients(SITE_ID)

if clients:
    print(f"✓ Found {len(clients)} client(s)\n")

    # Show first 5 clients
    for i, c in enumerate(clients[:5], 1):
        print(f"{i}. {c.get('name', 'Unknown')}")
        print(f"   IP: {c.get('ipAddress', 'N/A')}")
        print(f"   Type: {c.get('type', 'N/A')}")
        print(f"   Connected At: {c.get('connectedAt', 'N/A')}")
        print()
else:
    print("❌ No clients found (or error)")
