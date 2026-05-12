"""
Crypto Options & Liquidation Dashboard.
Fetches and displays market data for crypto options and liquidations.
"""

import time
import sys
import requests

POLL_INTERVAL = 5

def fetch_deribit_quotes(currency):
    """
    Fetch options book summary from Deribit for a given currency.
    Args:
        currency (str): Currency symbol (e.g., 'BTC', 'ETH').
    Returns:
        dict: JSON response from Deribit API or None on error.
    """
    url = f"https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency={currency}&kind=option"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Deribit quotes for {currency}: {e}")
        return None

def calculate_pcr(options_data):
    """
    Calculate Put-Call Ratio based on Open Interest.
    PCR = Sum(Put OI) / Sum(Call OI)
    """
    if not options_data:
        return 0.0
        
    call_oi = 0.0
    put_oi = 0.0
    
    for opt in options_data:
        instrument = opt.get("instrument_name", "")
        oi = opt.get("open_interest", 0)
        
        if instrument.endswith("-C"):
            call_oi += oi
        elif instrument.endswith("-P"):
            put_oi += oi
            
    if call_oi == 0:
        return 0.0
        
    return put_oi / call_oi

def main():
    """Main execution loop."""
    try:
        while True:
            print("Fetching data...")
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)

if __name__ == "__main__":
    main()
