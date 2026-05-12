
import requests
import json

def test_binance():
    print("Testing Binance Liquidation Endpoint...")
    symbol = "BTCUSDT"
    url = f"https://fapi.binance.com/fapi/v1/allForceOrders?symbol={symbol}&limit=10"
    try:
        r = requests.get(url, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

def test_bybit():
    print("\nTesting Bybit Liquidation Endpoint...")
    symbol = "BTCUSDT"
    # Testing both potential endpoints
    urls = [
        f"https://api.bybit.com/v5/market/liquidation?category=linear&symbol={symbol}&limit=10",
        f"https://api.bybit.com/v5/market/all-liquidation?category=linear&symbol={symbol}&limit=10"
    ]
    for url in urls:
        print(f"URL: {url}")
        try:
            r = requests.get(url, timeout=10)
            print(f"Status: {r.status_code}")
            print(f"Response: {r.text[:500]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_binance()
    test_bybit()
