import logging
logging.basicConfig(level=logging.INFO)

from dotenv import load_dotenv
load_dotenv()


from src.integrations.homeconnect import HomeConnectClient

client = HomeConnectClient(base_url="https://simulator.home-connect.com")
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

print("\n--- CoffeeMaker settings ---")
settings = client.get_appliance_settings("BOSCH-HCS06COM1-E896B6758BFC")
if settings is None:
    print("Could not get settings (see logs above)")
elif len(settings) == 0:
    print("Settings list is empty")
else:
    for item in settings:
        print(f"  {item.get('key')}: {item.get('value')}")  

print("\n--- Turning CoffeeMaker off ---")
ok = client.set_appliance_setting(
    "BOSCH-HCS06COM1-E896B6758BFC",
    "BSH.Common.Setting.PowerState",
    "BSH.Common.EnumType.PowerState.Standby"
)
print("Success!" if ok else "Failed - check logs above")

print("\n--- Checking settings after change ---")
settings = client.get_appliance_settings("BOSCH-HCS06COM1-E896B6758BFC")
for item in settings:
    print(f"  {item.get('key')}: {item.get('value')}")

print("\n--- Turning CoffeeMaker back on ---")
ok = client.set_appliance_setting(
    "BOSCH-HCS06COM1-E896B6758BFC",
    "BSH.Common.Setting.PowerState",
    "BSH.Common.EnumType.PowerState.On"
)
print("Success!" if ok else "Failed - check logs above")
print("\n--- Inspecting PowerState setting detail ---")
access_token = client._load_access_token()
resp = requests.get(
    "https://simulator.home-connect.com/api/homeappliances/BOSCH-HCS06COM1-E896B6758BFC/settings/BSH.Common.Setting.PowerState",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.bsh.sdk.v1+json"
    }
)
print(resp.status_code)
print(resp.text)