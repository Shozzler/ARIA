"""
Test UniFi connection using credentials from .env file
"""

import os
from dotenv import load_dotenv
from src.integrations.unifi import UniFiClient

# Load .env file
load_dotenv()

CONTROLLER_IP = os.getenv("UNIFI_CONTROLLER_IP", "10.20.40.1")
SITE_ID = os.getenv("UNIFI_SITE_ID")
API_KEY = os.getenv("UNIFI_API_KEY")

# Validate settings
if not SITE_ID or not API_KEY:
    print("❌ Missing UNIFI_SITE_ID or UNIFI_API_KEY in .env file")
    exit(1)

print("=" * 70)
print("  ARIA - UniFi Connection Test")
print("=" * 70)

# Initialize client
client = UniFiClient(
    controller_ip=CONTROLLER_IP,
    api_key=API_KEY,
    verify_ssl=False
)

print("\n✓ Testing connection...")
if not client.test_connection():
    print("✗ Connection failed!")
    exit(1)

print("✓ Connection successful!")

# Get devices
print("\n✓ Retrieving devices...")
devices = client.get_devices(SITE_ID)

if not devices:
    print("✗ No devices found")
    exit(1)

print(f"\n📊 Found {len(devices)} device(s):")
print("-" * 70)

for device in devices:
    name = device.get("name", "Unknown")
    model = device.get("model", "Unknown")
    ip = device.get("ipAddress", "N/A")
    mac = device.get("macAddress", "N/A")
    status = device.get("state", "unknown")

    # Check if it's a camera
    is_camera = any(keyword in model.lower() for keyword in ["nano", "turret", "bullet", "doorbell", "camera"])
    emoji = "📷" if is_camera else "📱"

    print(f"\n{emoji} {name}")
    print(f"   Model:  {model}")
    print(f"   IP:     {ip}")
    print(f"   MAC:    {mac}")
    print(f"   Status: {status}")

# Get cameras
print("\n" + "=" * 70)
cameras = client.list_cameras(SITE_ID)

if cameras:
    print(f"\n📷 Found {len(cameras)} camera(s):")
    print("-" * 70)
    for camera in cameras:
        name = camera.get("name", "Unknown")
        ip = camera.get("ipAddress", "N/A")
        model = camera.get("model", "Unknown")
        print(f"  • {name} ({model}) - IP: {ip}")
else:
    print("\n⚠ No cameras found")

print("\n" + "=" * 70)
print("✅ Test completed successfully!")
print("=" * 70)
