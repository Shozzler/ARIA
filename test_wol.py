"""
test_wol.py - send a Wake-on-LAN "magic packet" to the LG TV.

Turn the TV fully off with the remote, wait ~10 seconds, then run:

    python test_wol.py

If the TV turns on, Wake-on-LAN works and ARIA's "Turn On" button will too.
"""

import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.integrations.webos_tv import send_magic_packet  # noqa: E402

load_dotenv()

tv_mac = os.getenv("TV_MAC")
tv_ip = os.getenv("TV_IP")

if not tv_mac:
    print("TV_MAC is not set in .env")
    sys.exit(1)

print(f"Sending Wake-on-LAN packet to {tv_mac} ...")
send_magic_packet(tv_mac, tv_ip)
print("Sent! The TV should turn on within a few seconds.")
