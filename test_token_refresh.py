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

print("\n--- CoffeeMaker available programs ---")
programs = client.get_available_programs("BOSCH-HCS06COM1-E896B6758BFC")
if programs is None:
    print("Could not get programs (see logs above)")
else:
    for p in programs:
        print(f"  {p}")

print("\n--- Starting Cotton wash on Washer ---")
ok = client.start_program("SIEMENS-HCS03WCH1-7E6E6A555B36", "LaundryCare.Washer.Program.Cotton")
print("Success!" if ok else "Failed - check logs above")

print("\n--- Checking status after start ---")
status = client.get_appliance_status("SIEMENS-HCS03WCH1-7E6E6A555B36")
for item in status:
    print(f"  {item.get('key')}: {item.get('value')}")

print("\n--- Stopping program ---")
ok = client.stop_program("SIEMENS-HCS03WCH1-7E6E6A555B36")
print("Success!" if ok else "Failed - check logs above")


print("\n--- Washer available programs ---")
programs = client.get_available_programs("SIEMENS-HCS03WCH1-7E6E6A555B36")
if programs is None:
    print("Could not get programs (see logs above)")
else:
    for p in programs:
        print(f"  {p}")

print("\n--- Full settings for CoffeeMaker ---")
settings = client.get_appliance_settings("BOSCH-HCS06COM1-E896B6758BFC")
for s in settings:
    print(f"  {s.get('key')}: {s.get('value')}")

print("\n--- Full settings for Washer ---")
settings = client.get_appliance_settings("SIEMENS-HCS03WCH1-7E6E6A555B36")
for s in settings:
    print(f"  {s.get('key')}: {s.get('value')}")