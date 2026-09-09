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
import time
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class HomeConnectClient:
    """
    Client to communicate with the HomeConnect API.

    Handles loading a saved OAuth token and using it to read appliance data.
    """

    def __init__(self, base_url: str, token_file: str = "data/homeconnect_tokens.json",
             client_id: str = None, client_secret: str = None):       
        """
        Initialize HomeConnect client.

        Args:
            base_url: API host, e.g. "https://simulator.home-connect.com"
                      or "https://api.home-connect.com"
            token_file: Path to the JSON file holding saved OAuth tokens
        """
        self.base_url = base_url
        self.token_file = token_file
        self.client_id = client_id or os.getenv("HOMECONNECT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("HOMECONNECT_CLIENT_SECRET")

        logger.info(f"HomeConnect client initialized for {base_url}")

    def _load_tokens(self) -> Optional[Dict]:
        """Load the saved tokens dict from disk."""
        if not os.path.exists(self.token_file):
            logger.warning(f"No token file found at {self.token_file} - run homeconnect_login.py first")
            return None

        try:
            with open(self.token_file, "r") as file:
                tokens = json.load(file)
            return tokens
        except Exception as e:
            logger.error(f"Error loading HomeConnect tokens: {e}")
            return None


    def _is_expired(self, tokens: Dict) -> bool:
        """Check whether the saved tokens are expired (or about to expire)."""
        obtained_at = tokens.get("obtained_at", 0)
        expires_in = tokens.get("expires_in", 0)
        buffer_seconds = 60
        return time.time() >= (obtained_at + expires_in - buffer_seconds)

    def _save_tokens(self, tokens: Dict):
        """Save tokens to disk with a fresh obtained_at timestamp."""
        tokens["obtained_at"] = time.time()
        with open(self.token_file, "w") as file:
            json.dump(tokens, file, indent=2)
        logger.info(f"Tokens saved to {self.token_file}")

    def _refresh_tokens(self, tokens: Dict) -> Optional[Dict]:
        """Use the refresh_token to get a new access_token from HomeConnect."""
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            logger.error("No refresh_token available - re-run homeconnect_login.py")
            return None

        try:
            response = requests.post(
                f"{self.base_url}/security/oauth/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )

            if response.status_code != 200:
                logger.error(f"Token refresh failed ({response.status_code}): {response.text}")
                return None

            new_tokens = response.json()
            # HomeConnect doesn't always send back a new refresh_token - keep the old one if so
            if "refresh_token" not in new_tokens:
                new_tokens["refresh_token"] = refresh_token

            self._save_tokens(new_tokens)
            logger.info("HomeConnect access token refreshed")
            return new_tokens

        except requests.exceptions.RequestException as e:
            logger.error(f"Error refreshing HomeConnect token: {e}")
            return None

    def _load_access_token(self) -> Optional[str]:
        """Return a valid access token, refreshing it first if it's expired."""
        tokens = self._load_tokens()
        if not tokens:
            return None

        if self._is_expired(tokens):
            logger.info("HomeConnect access token expired, refreshing...")
            tokens = self._refresh_tokens(tokens)
            if not tokens:
                return None

        return tokens.get("access_token")

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

    def get_appliance_status(self, ha_id: str) -> Optional[List[Dict]]:
        """
        Get the current status (door state, operation state, etc.) for one appliance.

        Args:
            ha_id: The appliance's haId, e.g. "SIEMENS-HCS05FRF1-6D36A5AC9851"

        Returns:
            List of status dicts (each with "key" and "value"), or None if the request fails.
        """
        access_token = self._load_access_token()
        if not access_token:
            return None

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.bsh.sdk.v1+json"
        }

        try:
            response = requests.get(f"{self.base_url}/api/homeappliances/{ha_id}/status", headers=headers, timeout=10)

            if response.status_code != 200:
                logger.error(f"Error fetching status for {ha_id} ({response.status_code}): {response.text}")
                return None

            data = response.json()
            status = data.get("data", {}).get("status", [])
            logger.info(f"Got {len(status)} status item(s) for {ha_id}")
            return status

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching HomeConnect status for {ha_id}: {e}")
            return None

    def get_appliance_settings(self, ha_id: str) -> Optional[List[Dict]]:
        """
        Get the current settings (e.g. PowerState) for one appliance.

        Args:
            ha_id: The appliance's haId

        Returns:
            List of setting dicts (each with "key" and "value"), or None if the request fails.
        """
        access_token = self._load_access_token()
        if not access_token:
            return None

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.bsh.sdk.v1+json"
        }

        try:
            response = requests.get(f"{self.base_url}/api/homeappliances/{ha_id}/settings", headers=headers, timeout=10)

            if response.status_code != 200:
                logger.error(f"Error fetching settings for {ha_id} ({response.status_code}): {response.text}")
                return None

            data = response.json()
            settings = data.get("data", {}).get("settings", [])
            logger.info(f"Got {len(settings)} setting(s) for {ha_id}")
            return settings

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching HomeConnect settings for {ha_id}: {e}")
            return None

    def set_appliance_setting(self, ha_id: str, key: str, value) -> bool:
        """
        Change one setting on an appliance (e.g. turn it on/off).

        Args:
            ha_id: The appliance's haId
            key: The setting key, e.g. "BSH.Common.Setting.PowerState"
            value: The new value, e.g. "BSH.Common.EnumType.PowerState.Off"

        Returns:
            True if the change was accepted, False otherwise.
        """
        access_token = self._load_access_token()
        if not access_token:
            return False

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/vnd.bsh.sdk.v1+json",
            "Accept": "application/vnd.bsh.sdk.v1+json"
        }

        body = {
            "data": {
                "key": key,
                "value": value
            }
        }

        try:
            response = requests.put(
                f"{self.base_url}/api/homeappliances/{ha_id}/settings/{key}",
                headers=headers,
                json=body,
                timeout=10
            )

            if response.status_code not in (200, 204):
                logger.error(f"Error setting {key} on {ha_id} ({response.status_code}): {response.text}")
                return False

            logger.info(f"Set {key} = {value} on {ha_id}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Error setting {key} on {ha_id}: {e}")
            return False

def format_status(status_list: List[Dict]) -> List[Dict]:
    """
    Convert raw HomeConnect status items into a friendlier display format.

    "BSH.Common.Status.DoorState" -> label "Door State"
    "BSH.Common.EnumType.DoorState.Closed" -> value "Closed"
    """
    formatted = []
    for item in status_list:
        key = item.get("key", "")
        value = item.get("value")

        short_key = key.split(".")[-1]
        label = re.sub(r'(?<!^)(?=[A-Z])', ' ', short_key)

        if isinstance(value, str) and "." in value:
            value = value.split(".")[-1]

        formatted.append({"label": label, "value": value})
    return formatted