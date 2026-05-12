
import requests
import json

def test_bitget():
    print("Testing Bitget Liquidation Endpoint...")
    symbol = "BTCUSDT"
    url = f"https://api.bitget.com/api/v2/mix/market/liquidation?symbol={symbol}&productType=USDT-FUTURES&limit=10"
    try:
        r = requests.get(url, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_bitget()
