"""
HomeConnect API Client for ARIA

Connects to BSH HomeConnect (Siemens/Gaggenau appliances) and reads
appliance data. Works against either the simulator or the real API,
depending on which base_url is passed in.

Current Access: Read-only (appliance list)
Future Access: Appliance status/settings, control
"""

import requests
import json
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class HomeConnectClient:
    """
    Client to communicate with the HomeConnect API.

    Handles loading a saved OAuth token and using it to read appliance data.
    """

    def __init__(self, base_url: str, token_file: str = "data/homeconnect_tokens.json"):
        """
        Initialize HomeConnect client.

        Args:
            base_url: API host, e.g. "https://simulator.home-connect.com"
                      or "https://api.home-connect.com"
            token_file: Path to the JSON file holding saved OAuth tokens
        """
        self.base_url = base_url
        self.token_file = token_file

        logger.info(f"HomeConnect client initialized for {base_url}")

    def _load_access_token(self) -> Optional[str]:
        """Load the saved access token from disk."""
        if not os.path.exists(self.token_file):
            logger.warning(f"No token file found at {self.token_file} - run homeconnect_login.py first")
            return None

        try:
            with open(self.token_file, "r") as file:
                tokens = json.load(file)
            return tokens.get("access_token")
        except Exception as e:
            logger.error(f"Error loading HomeConnect tokens: {e}")
            return None

    def get_appliances(self) -> Optional[List[Dict]]:
        """
        Get all HomeConnect appliances (fridge, oven, etc.) for this account.

        Returns:
            List of appliance dictionaries, or None if the request fails.
        """
        access_token = self._load_access_token()
        if not access_token:
            return None

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.bsh.sdk.v1+json"
        }

        try:
            response = requests.get(f"{self.base_url}/api/homeappliances", headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            appliances = data.get("data", {}).get("homeappliances", [])
            logger.info(f"Found {len(appliances)} HomeConnect appliance(s)")
            return appliances

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching HomeConnect appliances: {e}")
            return None