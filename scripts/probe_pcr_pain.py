import os
import requests
import json
import datetime

upstox_token = None
env_path = "/home/vreddy1/Desktop/Projects/scripts/.env"
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            if line.startswith("UPSTOX_TOKEN="):
                upstox_token = line.strip().split("=", 1)[1]
                break

headers = {
    "Authorization": f"Bearer {upstox_token}",
    "Accept": "application/json"
}

# Get expiries
r = requests.get("https://api.upstox.com/v2/option/contract", headers=headers, params={"instrument_key": "NSE_INDEX|Nifty 50"}, timeout=10)
if r.status_code == 200:
    data = r.json()
    raw = data.get("data", [])
    if raw and isinstance(raw[0], str):
        expiries = sorted(raw)
    elif raw and isinstance(raw[0], dict):
        expiries = sorted([x.get("expiry", "") for x in raw if x.get("expiry")])
    else:
        expiries = []
        
    print(f"Expiries parsed: {expiries[:5]}")
    
    if expiries:
        nearest = expiries[0]
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        
        # Test PCR
        r_pcr = requests.get("https://api.upstox.com/v2/market/pcr", headers=headers, params={
            "instrument_key": "NSE_INDEX|Nifty 50",
            "expiry": nearest,
            "date": today_str,
            "bucket_interval": 60
        })
        print(f"PCR Status: {r_pcr.status_code}")
        if r_pcr.status_code == 200:
            print("PCR Response:")
            print(json.dumps(r_pcr.json(), indent=2)[:1000])
        else:
            print(r_pcr.text)

        # Test Max Pain
        r_mp = requests.get("https://api.upstox.com/v2/market/max-pain", headers=headers, params={
            "instrument_key": "NSE_INDEX|Nifty 50",
            "expiry": nearest,
            "date": today_str,
            "bucket_interval": 60
        })
        print(f"Max Pain Status: {r_mp.status_code}")
        if r_mp.status_code == 200:
            print("Max Pain Response:")
            print(json.dumps(r_mp.json(), indent=2)[:1000])
        else:
            print(r_mp.text)
