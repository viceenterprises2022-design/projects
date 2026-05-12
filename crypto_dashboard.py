"""
Crypto Options & Liquidation Dashboard.
Fetches and displays market data for crypto options and liquidations.
"""

import time
import sys
import requests
from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

POLL_INTERVAL = 5
console = Console(width=107)

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
    url = f"https://api.bybit.com/v5/market/all-liquidation?category=linear&symbol={symbol}USDT&limit=50"
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

def make_options_table(options_data, spot_price):
    """Create a Rich table for the options chain around the ATM strike."""
    table = Table(title="Options Chain (ATM)", expand=True)
    table.add_column("CALL LTP", justify="right", style="cyan")
    table.add_column("CALL OI", justify="right", style="magenta")
    table.add_column("STRIKE", justify="center", style="bold white")
    table.add_column("PUT OI", justify="right", style="magenta")
    table.add_column("PUT LTP", justify="right", style="cyan")

    if not options_data:
        return table

    strikes_data = {}
    for opt in options_data:
        name = opt.get("instrument_name", "")
        parts = name.split("-")
        if len(parts) < 4:
            continue
        try:
            strike = float(parts[2])
            opt_type = parts[3]
            ltp = float(opt.get("last_price", 0)) * spot_price if opt.get("last_price") else 0
            oi = float(opt.get("open_interest", 0))
            if strike not in strikes_data:
                strikes_data[strike] = {"C": {"ltp": 0, "oi": 0}, "P": {"ltp": 0, "oi": 0}}
            strikes_data[strike][opt_type] = {"ltp": ltp, "oi": oi}
        except (ValueError, IndexError):
            continue

    sorted_strikes = sorted(strikes_data.keys())
    if not sorted_strikes:
        return table
        
    atm_idx = min(range(len(sorted_strikes)), key=lambda i: abs(sorted_strikes[i] - spot_price))
    start = max(0, atm_idx - 3)
    end = min(len(sorted_strikes), atm_idx + 4)

    for s in sorted_strikes[start:end]:
        d = strikes_data[s]
        table.add_row(
            f"{d['C']['ltp']:,.1f}", f"{d['C']['oi']:,.1f}",
            f"{s:,.0f}",
            f"{d['P']['oi']:,.1f}", f"{d['P']['ltp']:,.1f}"
        )
    return table

def make_liquidation_table(liq_bins):
    """Create a Rich table for liquidation density with a visual bar."""
    table = Table(title="Liquidation Density (24H)", expand=True)
    table.add_column("PRICE", justify="left")
    table.add_column("VOLUME", justify="right")
    table.add_column("DENSITY", justify="left")

    if not liq_bins:
        return table

    max_vol = max(b[1] for b in liq_bins) if liq_bins else 1
    for price, vol in liq_bins:
        bar_len = int((vol / max_vol) * 15)
        bar = "█" * bar_len + "░" * (15 - bar_len)
        table.add_row(f"{price:,.0f}", f"${vol/1e6:.1f}M", f"[{bar}]")
    return table

def render_dashboard(asset):
    """Fetch data and construct the full dashboard layout for a given asset."""
    res = fetch_deribit_quotes(asset)
    data = res.get("result", []) if res else []
    
    spot = 0
    if data:
        spot = data[0].get("underlying_price", 0)
    
    pcr = calculate_pcr(data)
    max_pain = calculate_max_pain(data)
    
    binance_liq = fetch_binance_liquidations(asset)
    bybit_liq = fetch_bybit_liquidations(asset)
    liq_bins = aggregate_liquidation_bins(binance_liq, bybit_liq, asset)
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    header = Panel(
        Text.from_markup(f"[bold green]{asset}-DASHBOARD[/] | {timestamp} | SPOT: {spot:,.2f} | MAX PAIN: {max_pain:,.0f} | PCR: {pcr:.2f}"),
        style="white"
    )
    
    layout = Layout()
    layout.split_column(
        Layout(header, size=3),
        Layout(name="main")
    )
    layout["main"].split_row(
        Layout(Panel(make_options_table(data, spot))),
        Layout(Panel(make_liquidation_table(liq_bins)))
    )
    return layout

def main():
    """Main execution loop cycling through BTC, ETH, and SOL."""
    assets = ["BTC", "ETH", "SOL"]
    idx = 0
    try:
        with Live(render_dashboard(assets[0]), refresh_per_second=1, screen=True) as live:
            while True:
                live.update(render_dashboard(assets[idx]))
                time.sleep(POLL_INTERVAL)
                idx = (idx + 1) % len(assets)
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()
