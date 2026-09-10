"""
Quick test: list the oven's available programs, then inspect the option
constraints (e.g. temperature range/step) for the first one.
"""
import logging, os, json
logging.basicConfig(level=logging.INFO)
from dotenv import load_dotenv
load_dotenv()

from src.integrations.homeconnect import HomeConnectClient

base_url = os.getenv("HOMECONNECT_BASE_URL", "https://simulator.home-connect.com")
client = HomeConnectClient(base_url=base_url)

oven_id = "GAGGENAU-BOP251132-68A40EC3B7E2"

print("--- Available programs for oven ---")
programs = client.get_available_programs(oven_id)
if not programs:
    print("Failed to get programs - check the log lines above")
else:
    for p in programs:
        print(f"  {p.get('key')}")

    first_key = programs[0]["key"]
    print(f"\n--- Options for first program: {first_key} ---")
    options = client.get_program_options(oven_id, first_key)
    if options is None:
        print("Failed to get options - check the log lines above")
    else:
        print(json.dumps(options, indent=2))
