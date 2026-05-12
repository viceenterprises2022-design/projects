
import requests
import json

def test_binance_dapi():
    print("Testing Binance Coin-M Liquidation Endpoint...")
    symbol = "BTCUSD_PERP"
    url = f"https://dapi.binance.com/dapi/v1/allForceOrders?symbol={symbol}&limit=10"
    try:
        r = requests.get(url, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_binance_dapi()
