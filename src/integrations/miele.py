"""
Miele API Client for ARIA

Connects to Miele's 3rd Party API (legacy/EU-fallback provider) and reads
appliance data. Built against the real API — no simulator exists for Miele.

Current Access: Read-only (device list/state, available actions)
Future Access: Control (power on)
"""

import requests
import json
import os
import logging
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class MieleClient:
    """
    Client to communicate with the Miele 3rd Party API.

    Handles loading a saved OAuth token and using it to read/control appliance data.
    """

    def __init__(self, token_file: str = "data/miele_tokens.json",
                 client_id: str = None, client_secret: str = None):
        self.base_url = "https://api.mcs3.miele.com"
        self.token_file = token_file
        self.client_id = client_id or os.getenv("MIELE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("MIELE_CLIENT_SECRET")

        logger.info("Miele client initialized")

    def _load_tokens(self) -> Optional[Dict]:
        """Load the saved tokens dict from disk."""
        if not os.path.exists(self.token_file):
            logger.warning(f"No token file found at {self.token_file} - run miele_login.py first")
            return None

        try:
            with open(self.token_file, "r") as file:
                tokens = json.load(file)
            return tokens
        except Exception as e:
            logger.error(f"Error loading Miele tokens: {e}")
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
        """Use the refresh_token to get a new access_token from Miele."""
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            logger.error("No refresh_token available - re-run miele_login.py")
            return None

        try:
            response = requests.post(
                f"{self.base_url}/thirdparty/token",
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
            if "refresh_token" not in new_tokens:
                new_tokens["refresh_token"] = refresh_token

            self._save_tokens(new_tokens)
            logger.info("Miele access token refreshed")
            return new_tokens

        except requests.exceptions.RequestException as e:
            logger.error(f"Error refreshing Miele token: {e}")
            return None

    def _load_access_token(self) -> Optional[str]:
        """Return a valid access token, refreshing it first if it's expired."""
        tokens = self._load_tokens()
        if not tokens:
            return None

        if self._is_expired(tokens):
            logger.info("Miele access token expired, refreshing...")
            tokens = self._refresh_tokens(tokens)
            if not tokens:
                return None

        return tokens.get("access_token")

    def get_appliances(self) -> Optional[List[Dict]]:
        """
        Get all Miele appliances for this account, with device id included in each.

        Returns:
            List of appliance dictionaries (each with "id", "ident", "state"),
            or None if the request fails.
        """
        access_token = self._load_access_token()
        if not access_token:
            return None

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

        try:
            response = requests.get(f"{self.base_url}/v1/devices", headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            appliances = []
            for device_id, device_data in data.items():
                appliance = {"id": device_id}
                appliance.update(device_data)
                appliances.append(appliance)

            logger.info(f"Found {len(appliances)} Miele appliance(s)")
            return appliances

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Miele appliances: {e}")
            return None

    def get_appliance_actions(self, device_id: str) -> Optional[Dict]:
        """
        Get the available actions for one appliance right now (what it can currently do).

        Args:
            device_id: The appliance's id (fabNumber), e.g. "000176844679"

        Returns:
            Dict of action keys to their allowed values, or None if the request fails.
        """
        access_token = self._load_access_token()
        if not access_token:
            return None

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

        try:
            response = requests.get(f"{self.base_url}/v1/devices/{device_id}/actions", headers=headers, timeout=10)

            if response.status_code != 200:
                logger.error(f"Error fetching actions for {device_id} ({response.status_code}): {response.text}")
                return None

            actions = response.json()
            logger.info(f"Got actions for {device_id}")
            return actions

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Miele actions for {device_id}: {e}")
            return None

    def set_appliance_power(self, device_id: str, on: bool = True) -> bool:
        """
        Turn an appliance on (or off, where supported).

        Args:
            device_id: The appliance's id (fabNumber)
            on: True to power on, False to power off

        Returns:
            True if the action was accepted, False otherwise.
        """
        access_token = self._load_access_token()
        if not access_token:
            return False

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        body = {"powerOn": True} if on else {"powerOff": True}

        try:
            response = requests.put(
                f"{self.base_url}/v1/devices/{device_id}/actions",
                headers=headers,
                json=body,
                timeout=10
            )

            if response.status_code not in (200, 204):
                logger.error(f"Error setting power for {device_id} ({response.status_code}): {response.text}")
                return False

            logger.info(f"Set power {'on' if on else 'off'} for {device_id}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Error setting power for {device_id}: {e}")
            return False