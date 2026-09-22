"""
pair_tv.py - one-time local pairing for the LG webOS TV integration.

Run this once, on a machine on the same network as the TV:

    python pair_tv.py

It will connect to the TV using TV_IP from your .env file. The TV will
show an on-screen prompt asking to allow the connection - accept it
with your remote within about 30 seconds. Once accepted, the pairing
key is saved to data/webos_tv_key.json and every future connection
from ARIA will be silent (no prompt, no account, nothing to renew).

If nothing shows up on the TV screen:
  - Make sure the TV is on.
  - On the TV, check Settings > General > External Device Manager (or
    Network) > LG Connect Apps / Mobile TV On, and make sure it's
    enabled - this is what lets apps like this pair with the TV at
    all.
  - Double check TV_IP in .env matches the TV's current IP.
"""

import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.integrations.webos_tv import WebOSTVClient  # noqa: E402

load_dotenv()


def main():
    tv_ip = os.getenv("TV_IP")
    if not tv_ip:
        print("TV_IP is not set in .env - add a line like TV_IP=10.20.40.60 and try again.")
        return

    print(f"Connecting to LG TV at {tv_ip} ...")
    print("Watch the TV screen - accept the connection prompt with your remote.")

    client = WebOSTVClient(tv_ip)
    key = client.pair()

    if key:
        print("Paired successfully. Pairing key saved to data/webos_tv_key.json")
        print("You can now use the TV integration from ARIA without pairing again.")
    else:
        print("Pairing failed - see the messages above. Common causes:")
        print("  - The prompt timed out before being accepted on the TV.")
        print("  - The TV's IP address has changed since TV_IP was set.")
        print("  - LG Connect Apps / Mobile TV On is disabled in the TV's settings.")


if __name__ == "__main__":
    main()
