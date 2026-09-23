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
    When the TV is fully off it is not listening on the webOS
    websocket, so power_on() can't use aiowebostv. Instead it sends a
    Wake-on-LAN "magic packet" to the TV's MAC address (TV_MAC in
    .env). This needs "Turn on via Wi-Fi" / "Mobile TV On" enabled in
    the TV's settings.
"""

import asyncio
import json
import logging
import os
import socket
from typing import Any, Dict, Optional

from aiowebostv import WebOsClient
from aiowebostv.exceptions import WebOsTvCommandError, WebOsTvPairError

logger = logging.getLogger(__name__)


def send_magic_packet(mac: str, ip: Optional[str] = None, port: int = 9):
    """
    Send a Wake-on-LAN "magic packet" to wake a device by its MAC address.

    The packet is 6 bytes of 0xFF followed by the MAC address repeated
    16 times, sent as a UDP broadcast. The device's network card stays
    listening for exactly this pattern even while the device is off.

    Args:
        mac: MAC address like "aa:bb:cc:dd:ee:ff" (":" or "-" separators)
        ip: The device's IP (optional). Used to also send to its subnet's
            broadcast address (e.g. 10.20.40.255), which gets out of a
            Docker container more reliably than 255.255.255.255.
        port: UDP port - 9 is the standard Wake-on-LAN port.
    """
    # "aa:bb:cc:dd:ee:ff" -> "aabbccddeeff" -> 6 raw bytes
    mac_clean = mac.replace(":", "").replace("-", "").strip()
    mac_bytes = bytes.fromhex(mac_clean)
    if len(mac_bytes) != 6:
        raise ValueError(f"Invalid MAC address: {mac}")

    packet = b"\xff" * 6 + mac_bytes * 16

    targets = ["255.255.255.255"]
    if ip:
        # Assumes a /24 network: 10.20.40.60 -> 10.20.40.255
        targets.append(ip.rsplit(".", 1)[0] + ".255")

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        for target in targets:
            sock.sendto(packet, (target, port))
            logger.info(f"Wake-on-LAN packet sent to {mac} via {target}:{port}")


class WebOSTVClient:
    """
    Synchronous wrapper around aiowebostv's async WebOsClient.

    Handles loading/saving the paired client key and bridging each
    call through asyncio.run(), so it can be used from ARIA's
    synchronous Flask routes the same way the other integration
    clients are.
    """

    def __init__(self, host: str, key_file: str = "data/webos_tv_key.json",
                 mac: Optional[str] = None):
        """
        Initialize the webOS TV client.

        Args:
            host: The TV's local IP address, e.g. "10.20.40.60"
            key_file: Path to the JSON file holding the saved pairing key
            mac: The TV's MAC address - only needed for power_on()
        """
        self.host = host
        self.mac = mac
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

    def power_on(self) -> bool:
        """
        Turn the TV on via Wake-on-LAN.

        Returns True if the packet was sent - this does NOT confirm the
        TV actually woke up (Wake-on-LAN gets no reply). Check
        get_status() a few seconds later for that.
        """
        if not self.mac:
            logger.error("Can't power on the TV - TV_MAC is not set in .env")
            return False
        try:
            send_magic_packet(self.mac, self.host)
            return True
        except (OSError, ValueError) as e:
            logger.error(f"Wake-on-LAN failed: {e}")
            return False

    def power_off(self) -> bool:
        """Turn the TV off."""
        async def _power_off(client: WebOsClient):
            # aiowebostv's power_off() returns None even when it works,
            # and _call() uses None to mean "failed" - so return True
            # ourselves once the command has been sent without an error.
            await client.power_off()
            return True

        return self._call(_power_off) is not None

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
