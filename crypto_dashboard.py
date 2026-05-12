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
        dict: JSON response from Deribit API.
    """
    url = f"https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency={currency}&kind=option"
    response = requests.get(url, timeout=10)
    return response.json()

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
