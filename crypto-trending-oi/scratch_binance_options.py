import requests

def test_binance_options():
    # Fetch all options tickers from Binance
    url = "https://eapi.binance.com/eapi/v1/ticker"
    res = requests.get(url)
    
    if res.status_code == 200:
        data = res.json()
        
        total_call_oi = 0
        total_put_oi = 0
        
        for item in data:
            symbol = item.get("symbol", "")
            # Binance options symbols look like: BTC-240426-65000-C
            if symbol.startswith("BTC-"):
                if symbol.endswith("-C"):
                    total_call_oi += float(item.get("sumOpenInterest", 0))
                elif symbol.endswith("-P"):
                    total_put_oi += float(item.get("sumOpenInterest", 0))
                    
        print(f"Binance BTC Call OI: {total_call_oi:.2f} BTC")
        print(f"Binance BTC Put OI:  {total_put_oi:.2f} BTC")
        print(f"Total OI: {total_call_oi + total_put_oi:.2f} BTC")
        if total_put_oi > 0:
            print(f"PCR: {total_put_oi / total_call_oi:.2f}")
    else:
        print("Failed to fetch Binance Options:", res.status_code)

if __name__ == "__main__":
    test_binance_options()
