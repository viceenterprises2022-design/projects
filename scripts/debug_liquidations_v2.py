
import requests
import json

def test_okx():
    print("Testing OKX Liquidation Endpoint...")
    instId = "BTC-USDT-SWAP"
    url = f"https://www.okx.com/api/v5/public/liquidation-orders?instType=SWAP&instId={instId}"
    try:
        r = requests.get(url, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

def test_gate():
    print("\nTesting Gate.io Liquidation Endpoint...")
    settle = "usdt"
    url = f"https://api.gateio.ws/api/v4/futures/{settle}/liquidations?contract=BTC_USDT"
    try:
        r = requests.get(url, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_okx()
    test_gate()
