
import requests
import json
import time

def test_gate_v2():
    print("Testing Gate.io Liquidation Endpoint V2...")
    settle = "usdt"
    url = f"https://api.gateio.ws/api/v4/futures/{settle}/liquidations?contract=BTC_USDT&limit=10"
    headers = {
        "Timestamp": str(int(time.time()))
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_gate_v2()
