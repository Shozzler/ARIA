"""
LG webOS TV Integration for ARIA

Connects to an LG Smart TV on the local network using the webOS
websocket API. No cloud account, API key, or LG ThinQ registration is
needed - just the TV's local IP address and a one-time on-screen
pairing.

Current Access: Status (power/volume/mute/current app), volume, mute,
launch app, power off
Future Access: Input switching, channel control, media playback

Pairing:
    The very first connection triggers an on-screen prompt on the TV
    asking the user to allow the connection. Run pair_tv.py once,
    locally on the same network as the TV, to accept that prompt and
    save the resulting pairing key to data/webos_tv_key.json. Every
    connection after that is silent - no prompt, no browser, no
    account.

Note on power on:
    aiowebostv's power_on() only works while the TV is in a low-power
    standby state (e.g. screen off but still reachable on the
    network) - it is a no-op if the TV has been fully powered off.
    Waking a fully-off TV needs Wake-on-LAN, which this client does
    not implement yet, so power_on is intentionally not exposed here
    to avoid a button that looks like it works but usually won't.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

from aiowebostv import WebOsClient
from aiowebostv.exceptions import WebOsTvCommandError, WebOsTvPairError

logger = logging.getLogger(__name__)


class WebOSTVClient:
    """
    Synchronous wrapper around aiowebostv's async WebOsClient.

    Handles loading/saving the paired client key and bridging each
    call through asyncio.run(), so it can be used from ARIA's
    synchronous Flask routes the same way the other integration
    clients are.
    """

    def __init__(self, host: str, key_file: str = "data/webos_tv_key.json"):
        """
        Initialize the webOS TV client.

        Args:
            host: The TV's local IP address, e.g. "10.20.40.60"
            key_file: Path to the JSON file holding the saved pairing key
        """
        self.host = host
        self.key_file = key_file
        logger.info(f"WebOS TV client initialized for {host}")

    def _load_client_key(self) -> Optional[str]:
        """Load the saved pairing key from disk, if any."""
        if not os.path.exists(self.key_file):
            logger.warning(f"No pairing key found at {self.key_file} - run pair_tv.py first")
            return None

        try:
            with open(self.key_file, "r") as file:
                data = json.load(file)
            return data.get("client_key")
        except Exception as e:
            logger.error(f"Error loading webOS TV pairing key: {e}")
            return None

    def _save_client_key(self, client_key: str):
        """Save the pairing key to disk."""
        key_dir = os.path.dirname(self.key_file)
        if key_dir:
            os.makedirs(key_dir, exist_ok=True)
        with open(self.key_file, "w") as file:
            json.dump({"client_key": client_key}, file, indent=2)
        logger.info(f"webOS TV pairing key saved to {self.key_file}")

    async def _with_client(self, action):
        """
        Connect to the TV, run one action against the client, then
        disconnect. Shared by every public method so each call gets a
        fresh websocket connection rather than holding one open
        between Flask requests.
        """
        client_key = self._load_client_key()
        client = WebOsClient(self.host, client_key=client_key)
        try:
            await client.connect()
            if client.client_key and client.client_key != client_key:
                # A new key was issued (e.g. TV was re-paired) - keep it.
                self._save_client_key(client.client_key)
            return await action(client)
        finally:
            await client.disconnect()

    def _call(self, action):
        """Run an async TV action synchronously, returning None on failure."""
        try:
            return asyncio.run(self._with_client(action))
        except WebOsTvPairError:
            logger.error("webOS TV is not paired yet - run pair_tv.py first")
            return None
        except WebOsTvCommandError as e:
            # Covers command failures, timeouts, bad responses, and
            # "service not found" - all subclasses of this error.
            logger.error(f"webOS TV command failed: {e}")
            return None
        except OSError as e:
            logger.error(f"Could not reach webOS TV at {self.host}: {e}")
            return None

    # --- Status ---

    def get_status(self) -> Optional[Dict[str, Any]]:
        """
        Return a snapshot of the TV's current state: power, volume,
        mute, and current app - or None if the TV can't be reached.
        """
        async def _status(client: WebOsClient):
            power_state = await client.get_power_state()
            volume = await client.get_volume()
            muted = await client.get_muted()
            current_app = await client.get_current_app()
            return {
                "is_on": bool(client.tv_state.is_on),
                "power_state": power_state,
                "volume": volume,
                "muted": muted,
                "current_app": current_app,
            }

        return self._call(_status)

    def get_apps(self) -> Optional[Dict[str, Any]]:
        """Return the TV's installed apps (launch points)."""
        return self._call(lambda client: client.get_apps())

    # --- Control ---

    def power_off(self) -> bool:
        """Turn the TV off."""
        return self._call(lambda client: client.power_off()) is not None

    def set_volume(self, volume: int) -> bool:
        """Set the TV's volume (0-100)."""
        return self._call(lambda client: client.set_volume(volume)) is not None

    def volume_up(self) -> bool:
        """Raise the TV's volume by one step."""
        return self._call(lambda client: client.volume_up()) is not None

    def volume_down(self) -> bool:
        """Lower the TV's volume by one step."""
        return self._call(lambda client: client.volume_down()) is not None

    def set_mute(self, mute: bool) -> bool:
        """Mute or unmute the TV."""
        return self._call(lambda client: client.set_mute(mute)) is not None

    def launch_app(self, app_id: str) -> bool:
        """Launch an app by its id (e.g. 'netflix', 'youtube.leanback.v4')."""
        return self._call(lambda client: client.launch_app(app_id)) is not None

    # --- Pairing ---

    def pair(self) -> Optional[str]:
        """
        Connect to the TV, triggering the on-screen pairing prompt if
        needed, and return the pairing key once accepted.

        Intended to be run once, locally, via pair_tv.py - not from a
        Flask request, since it blocks until someone accepts the
        prompt on the TV with the remote.
        """
        async def _pair():
            client_key = self._load_client_key()
            client = WebOsClient(self.host, client_key=client_key)
            try:
                await client.connect()
                return client.client_key
            finally:
                await client.disconnect()

        try:
            key = asyncio.run(_pair())
        except WebOsTvPairError:
            logger.error("Pairing was not accepted on the TV")
            return None
        except OSError as e:
            logger.error(f"Could not reach webOS TV at {self.host}: {e}")
            return None

        if key:
            self._save_client_key(key)
        return key
