"""
Test script for UniFi API connection

This script tests if we can connect to your UniFi Dream Machine
and retrieve device information.

Usage:
    python test_unifi_connection.py
"""

import sys
from src.integrations.unifi import UniFiClient
import json


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def test_connection(api_key: str):
    """
    Test UniFi connection and retrieve basic information.

    Args:
        api_key: Your UniFi API key
    """

    print_section("🔌 UniFi Connection Test")

    # Initialize client
    print("\n1️⃣  Initializing UniFi client...")
    client = UniFiClient(
        controller_ip="10.20.40.1",
        api_key=api_key,
        verify_ssl=False
    )
    print("   ✓ Client created")

    # Test connection
    print("\n2️⃣  Testing connection to Dream Machine (10.20.40.1)...")
    if not client.test_connection():
        print("   ✗ Connection failed!")
        print("   Check:")
        print("   - Controller IP is correct (10.20.40.1)")
        print("   - API key is valid")
        print("   - Network connection is working")
        return False

    print("   ✓ Connection successful!")

    # Get sites
    print("\n3️⃣  Retrieving sites...")
    sites = client.get_sites()

    if not sites:
        print("   ✗ No sites found")
        return False

    print(f"   ✓ Found {len(sites)} site(s)")
    for site in sites:
        print(f"      - {site.get('name', 'Unknown')} (ID: {site.get('id', 'N/A')})")

    # Get site ID (use first site)
    site_id = sites[0].get("id")
    print(f"\n   Using site: {site_id}")

    # Get devices
    print("\n4️⃣  Retrieving connected devices...")
    devices = client.get_devices(site_id)

    if not devices:
        print("   ✗ No devices found")
        return False

    print(f"   ✓ Found {len(devices)} device(s)\n")

    # Display devices
    print("   Device Summary:")
    print("   " + "-" * 56)

    for device in devices:
        name = device.get("name", "Unknown")
        model = device.get("model", "Unknown")
        ip = device.get("ipAddress", "N/A")
        status = device.get("state", "unknown")

        # Emoji for cameras
        is_camera = any(keyword in model.lower() for keyword in ["nano", "turret", "bullet", "doorbell", "camera"])
        emoji = "📷" if is_camera else "📱"

        print(f"   {emoji} {name}")
        print(f"      Model: {model} | IP: {ip} | Status: {status}")

    # Get cameras only
    print("\n5️⃣  Filtering cameras...")
    cameras = client.list_cameras(site_id)

    if cameras:
        print(f"   ✓ Found {len(cameras)} camera(s)")
        for camera in cameras:
            name = camera.get("name", "Unknown")
            ip = camera.get("ipAddress", "N/A")
            model = camera.get("model", "Unknown")
            print(f"      📷 {name} ({model}) - IP: {ip}")
    else:
        print("   ⚠ No cameras found")

    # Get network status
    print("\n6️⃣  Retrieving network status...")
    status = client.get_network_status(site_id)

    if status:
        print("   ✓ Network status retrieved")
        print(f"   Connected devices: {status.get('device_count', 'N/A')}")
    else:
        print("   ⚠ Could not retrieve network status")

    # Success
    print_section("✅ All Tests Passed!")
    print("\nYour UniFi integration is working correctly!")
    print("You can now:")
    print("  - Monitor connected devices")
    print("  - Read camera status")
    print("  - Track network health")
    print("\nNext steps:")
    print("  1. Commit this test to GitHub")
    print("  2. Create main.py integration")
    print("  3. Add device tracking to dashboard")

    return True


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  ARIA - UniFi Connection Test")
    print("="*60)

    # Get API key from user
    print("\nEnter your UniFi API key (from 10.20.40.1):")
    api_key = input("API Key: ").strip()

    if not api_key:
        print("\n✗ API key is required!")
        sys.exit(1)

    # Run test
    success = test_connection(api_key)

    # Exit with appropriate code
    sys.exit(0 if success else 1)
