
import requests
import json

def test_deribit_liquidation():
    print("Testing Deribit Perpetual Trades (Liquidation) Endpoint...")
    instrument = "BTC-PERPETUAL"
    url = f"https://www.deribit.com/api/v2/public/get_last_trades_by_instrument?instrument_name={instrument}&count=100"
    try:
        r = requests.get(url, timeout=10)
        print(f"Status: {r.status_code}")
        data = r.json()
        trades = data.get("result", {}).get("trades", [])
        liquidations = [t for t in trades if t.get("liquidation")]
        print(f"Total Trades: {len(trades)}")
        print(f"Liquidations found: {len(liquidations)}")
        if liquidations:
            print(f"Sample Liq: {liquidations[0]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_deribit_liquidation()
