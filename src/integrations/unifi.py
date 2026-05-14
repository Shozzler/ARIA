"""
UniFi API Client for ARIA

Connects to UniFi Dream Machine and reads:
- Connected devices (cameras, smart appliances)
- Device status
- Network information

Current Access: Read-only
Future Access: Write (block/allow internet, control devices)
"""

import requests
import logging
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)


class UniFiClient:
    """
    Client to communicate with UniFi Dream Machine API.

    Handles authentication and provides methods to read device data.
    """

    def __init__(self, controller_ip: str, api_key: str, verify_ssl: bool = False):
        """
        Initialize UniFi client.

        Args:
            controller_ip: IP address of UniFi Dream Machine (e.g., "10.20.40.1")
            api_key: API key for authentication
            verify_ssl: Whether to verify SSL certificate (default: False for self-signed)
        """
        self.controller_ip = controller_ip
        self.api_key = api_key
        self.verify_ssl = verify_ssl

        # Base URL for API calls
        self.base_url = f"https://{controller_ip}/proxy/network/integration/v1"

        # Headers for all requests
        self.headers = {
            "X-API-KEY": api_key,
            "Accept": "application/json"
        }

        logger.info(f"UniFi client initialized for {controller_ip}")

    def _make_request(self, endpoint: str, method: str = "GET") -> Optional[Dict]:
        """
        Make HTTP request to UniFi API.

        Args:
            endpoint: API endpoint (e.g., "/sites")
            method: HTTP method (GET, POST, etc.)

        Returns:
            Response JSON or None if request fails
        """
        url = f"{self.base_url}{endpoint}"

        try:
            logger.debug(f"Making {method} request to {endpoint}")

            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=10
            )

            response.raise_for_status()  # Raise exception for bad status codes

            return response.json()

        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error: Cannot reach {self.controller_ip}")
            return None
        except requests.exceptions.Timeout:
            logger.error(f"Timeout: Request to {endpoint} took too long")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error making request to {endpoint}: {str(e)}")
            return None

    def get_sites(self) -> Optional[List[Dict]]:
        """
        Get all sites (networks) from the controller.

        Returns:
            List of site dictionaries or None if request fails
        """
        response = self._make_request("/sites")

        if response and "data" in response:
            sites = response["data"]
            logger.info(f"Found {len(sites)} site(s)")
            for site in sites:
                logger.debug(f"Site: {site.get('name', 'Unknown')} (ID: {site.get('id', 'N/A')})")
            return sites

        logger.warning("No sites found or error retrieving sites")
        return None

    def get_devices(self, site_id: str) -> Optional[List[Dict]]:
        """
        Get all devices connected to a specific site.

        Args:
            site_id: The site ID to get devices from

        Returns:
            List of device dictionaries or None if request fails
        """
        endpoint = f"/sites/{site_id}/devices"
        response = self._make_request(endpoint)

        if response and "data" in response:
            devices = response["data"]
            logger.info(f"Found {len(devices)} device(s) on site {site_id}")
            return devices

        logger.warning(f"No devices found on site {site_id}")
        return None

    def get_device_status(self, site_id: str, device_id: str) -> Optional[Dict]:
        """
        Get detailed status of a specific device.

        Args:
            site_id: The site ID
            device_id: The device ID

        Returns:
            Device details dictionary or None if request fails
        """
        endpoint = f"/sites/{site_id}/devices/{device_id}"
        response = self._make_request(endpoint)

        if response and "data" in response:
            device = response["data"]
            logger.info(f"Retrieved status for device {device_id}")
            return device

        logger.warning(f"Could not get status for device {device_id}")
        return None

    def get_network_status(self, site_id: str) -> Optional[Dict]:
        """
        Get overall network status and statistics.

        Args:
            site_id: The site ID

        Returns:
            Network status dictionary or None if request fails
        """
        endpoint = f"/sites/{site_id}/network/status"
        response = self._make_request(endpoint)

        if response and "data" in response:
            status = response["data"]
            logger.info(f"Retrieved network status for site {site_id}")
            return status

        logger.warning(f"Could not get network status for site {site_id}")
        return None

    def list_cameras(self, site_id: str) -> Optional[List[Dict]]:
        """
        Get all cameras connected to the network.

        Args:
            site_id: The site ID

        Returns:
            List of camera dictionaries
        """
        devices = self.get_devices(site_id)

        if not devices:
            return None

        # Filter for cameras by checking the model field for known camera models
        # (Nano HD, Turret, Bullet, Doorbell, etc.)
        camera_keywords = ["nano", "turret", "bullet", "doorbell", "camera"]
        cameras = [
            d for d in devices
            if any(keyword in d.get("model", "").lower() for keyword in camera_keywords)
        ]

        logger.info(f"Found {len(cameras)} camera(s)")

        return cameras if cameras else None

    def get_connected_devices_count(self, site_id: str) -> Optional[int]:
        """
        Get count of connected devices on the network.

        Args:
            site_id: The site ID

        Returns:
            Number of connected devices or None if error
        """
        devices = self.get_devices(site_id)

        if devices:
            return len(devices)

        return None

    def test_connection(self) -> bool:
        """
        Test if connection to UniFi controller is working.

        Returns:
            True if connection successful, False otherwise
        """
        sites = self.get_sites()
        return sites is not None


if __name__ == "__main__":
    # Example usage (for testing)
    # Note: Replace with actual API key

    client = UniFiClient(
        controller_ip="10.20.40.1",
        api_key="YOUR_API_KEY_HERE"
    )

    if client.test_connection():
        print("✓ Connection successful!")
    else:
        print("✗ Connection failed!")
