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
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error fetching Deribit quotes for {currency}: {e}")
        return None

def fetch_binance_liquidations(symbol):
    """
    Fetch recent liquidations from Binance Futures for a given symbol.
    Args:
        symbol (str): Symbol without 'USDT' (e.g., 'BTC', 'ETH').
    Returns:
        list: List of liquidation orders or None on error.
    """
    url = f"https://fapi.binance.com/fapi/v1/allForceOrders?symbol={symbol}USDT&limit=100"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            return None
        return data
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error fetching Binance liquidations for {symbol}: {e}")
        return None

def fetch_bybit_liquidations(symbol):
    """
    Fetch recent liquidations from Bybit for a given symbol.
    Args:
        symbol (str): Symbol without 'USDT' (e.g., 'BTC', 'ETH').
    Returns:
        list: List of liquidation orders or None on error.
    """
    url = f"https://api.bybit.com/v5/market/liquidation?category=linear&symbol={symbol}USDT&limit=50"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("retCode") == 0:
            return data.get("result", {}).get("list", [])
        return None
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error fetching Bybit liquidations for {symbol}: {e}")
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

def calculate_max_pain(options_data):
    """
    Find strike price with minimum total loss for option buyers.
    """
    if not options_data:
        return 0.0
        
    strikes = set()
    parsed_data = []
    
    for opt in options_data:
        name = opt.get("instrument_name", "")
        parts = name.split("-")
        if len(parts) < 4:
            continue
        
        try:
            strike = float(parts[2])
            opt_type = parts[3] # 'C' or 'P'
            oi = float(opt.get("open_interest", 0))
            
            strikes.add(strike)
            parsed_data.append({"strike": strike, "type": opt_type, "oi": oi})
        except (ValueError, IndexError):
            continue
            
    if not strikes:
        return 0.0
        
    min_loss = float('inf')
    max_pain_strike = 0.0
    
    for expiry_price in sorted(strikes):
        total_loss = 0.0
        for opt in parsed_data:
            if opt["type"] == "C":
                loss = max(0, expiry_price - opt["strike"]) * opt["oi"]
            else: # 'P'
                loss = max(0, opt["strike"] - expiry_price) * opt["oi"]
            total_loss += loss
            
        if total_loss < min_loss:
            min_loss = total_loss
            max_pain_strike = expiry_price
            
    return max_pain_strike

def aggregate_liquidation_bins(binance_data, bybit_data, symbol):
    """
    Combine, bin, and sum liquidation volumes from Binance and Bybit.
    Returns sorted list of top 10 bins: [(price_bin, total_volume), ...]
    """
    if binance_data is None:
        binance_data = []
    if bybit_data is None:
        bybit_data = []
        
    bin_size = 100
    if symbol == "ETH":
        bin_size = 10
    elif symbol == "SOL":
        bin_size = 1
        
    bins = {}
    
    # Binance: price, origQty
    for item in binance_data:
        try:
            price = float(item.get("price", 0))
            qty = float(item.get("origQty", 0))
            volume = price * qty
            
            bin_price = int(round(price / bin_size) * bin_size)
            bins[bin_price] = bins.get(bin_price, 0) + volume
        except (ValueError, TypeError):
            continue
            
    # Bybit: price, size
    for item in bybit_data:
        try:
            price = float(item.get("price", 0))
            qty = float(item.get("size", 0))
            volume = price * qty
            
            bin_price = int(round(price / bin_size) * bin_size)
            bins[bin_price] = bins.get(bin_price, 0) + volume
        except (ValueError, TypeError):
            continue
            
    # Sort by volume descending and take top 10
    sorted_bins = sorted(bins.items(), key=lambda x: x[1], reverse=True)
    return sorted_bins[:10]

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
