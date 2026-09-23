from mcp.server.mcpserver import MCPServer

import os
import sys
import time

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Claude Desktop starts this script from its own folder, not from ARIA's.
# Switch to ARIA's folder so relative paths (.env, data/webos_tv_key.json)
# are found no matter who starts the server.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from src.integrations.webos_tv import WebOSTVClient  # noqa: E402

load_dotenv()

mcp = MCPServer("ARIA")


@mcp.tool()
def tv_status() -> dict:
    """Get the LG TV's current state: whether it is on, the volume,
    whether it is muted, and which app is open."""
    tv_ip = os.getenv("TV_IP")
    if not tv_ip:
        return {"error": "TV_IP is not set in .env"}

    client = WebOSTVClient(tv_ip)
    status = client.get_status()

    if status is None:
        return {"error": "The TV is off or unreachable."}
    return status


@mcp.tool()
def tv_power_on() -> dict:
    """Turn the LG TV on. Sends a Wake-on-LAN packet, then waits up to
    about 20 seconds and reports whether the TV actually came on."""
    tv_ip = os.getenv("TV_IP")
    tv_mac = os.getenv("TV_MAC")
    if not tv_ip or not tv_mac:
        return {"error": "TV_IP and TV_MAC must both be set in .env"}

    client = WebOSTVClient(tv_ip, mac=tv_mac)

    # Already on? Nothing to do.
    status = client.get_status()
    if status is not None and status.get("is_on"):
        return {"success": True, "message": "The TV was already on."}

    if not client.power_on():
        return {"success": False, "error": "Could not send the Wake-on-LAN packet."}

    # Wake-on-LAN gets no reply, so check a few times whether it woke up.
    for _ in range(6):
        time.sleep(3)
        status = client.get_status()
        if status is not None and status.get("is_on"):
            return {"success": True, "message": "The TV is now on."}

    return {
        "success": False,
        "error": "Wake-on-LAN packet sent, but the TV did not respond. "
                 "Check that 'Turn on via Wi-Fi' is enabled on the TV.",
    }


@mcp.tool()
def tv_power_off() -> dict:
    """Turn the LG TV off."""
    tv_ip = os.getenv("TV_IP")
    if not tv_ip:
        return {"error": "TV_IP is not set in .env"}

    client = WebOSTVClient(tv_ip)
    if client.power_off():
        return {"success": True, "message": "The TV is turning off."}
    return {"success": False, "error": "The TV is already off or unreachable."}


if __name__ == "__main__":
    mcp.run()
