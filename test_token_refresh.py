import logging
logging.basicConfig(level=logging.INFO)

from dotenv import load_dotenv
load_dotenv()


from src.integrations.homeconnect import HomeConnectClient

import os
base_url = os.getenv("HOMECONNECT_BASE_URL", "https://simulator.home-connect.com")
client = HomeConnectClient(base_url=base_url)
appliances = client.get_appliances()

if not appliances:
    print("\nFailed to get appliances - check the log lines above for why")
else:
    print(f"\nGot {len(appliances)} appliances:")
    for a in appliances:
        print(f"\n- {a['name']} ({a['type']}) haId={a['haId']}")
        status = client.get_appliance_status(a['haId'])
        if status is None:
            print("  Could not get status (see logs above)")
        elif len(status) == 0:
            print("  Status list is empty")
        else:
            for item in status:
                print(f"  {item.get('key')}: {item.get('value')}")

print("\n--- Settings for oven 'Four' ---")
settings = client.get_appliance_settings("GAGGENAU-BSP261131-68A40EAF1ACC")
if settings:
    for s in settings:
        print(f"  {s.get('key')}: {s.get('value')}")

print("\n--- Settings for fridge ---")
settings = client.get_appliance_settings("255090392381007400")
if settings:
    for s in settings:
        print(f"  {s.get('key')}: {s.get('value')}")

print("\n--- Toggling fridge internal light off ---")
ok = client.set_appliance_setting("255090392381007400", "Refrigeration.Common.Setting.Light.Internal.Power", False)
print("Success!" if ok else "Failed - check logs above")

print("\n--- Toggling fridge internal light ON ---")
ok = client.set_appliance_setting("255090392381007400", "Refrigeration.Common.Setting.Light.Internal.Power", True)
print("Success!" if ok else "Failed - check logs above")