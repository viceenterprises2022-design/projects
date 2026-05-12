
import requests
import json

def test_hyperliquid_v2():
    print("Testing Hyperliquid Liquidation Endpoint V2...")
    url = "https://api.hyperliquid.xyz/info"
    payload = {"type": "liquidations"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"Status: {r.status_code}")
        data = r.json()
        print(f"Total Liquidations: {len(data)}")
        if data:
            print(f"Sample Liq: {data[0]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_hyperliquid_v2()
