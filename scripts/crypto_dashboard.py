"""
Crypto Options & Liquidation Dashboard (Map Edition).
Uses Order Book Depth to predict liquidation zones.
"""

import time
import sys
import requests
import json
import threading
import logging
import ssl
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

POLL_INTERVAL = 10
console = Console(width=107)

# ── Logging ──────────────────────────────────────────────────────────────────

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

# ── Fetchers ────────────────────────────────────────────────────────────────

def fetch_deribit_quotes(currency):
    url = f"https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency={currency}&kind=option"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except: return None

def fetch_binance_depth(symbol):
    """Fetch 1000 levels of depth to find liquidity walls."""
    url = f"https://fapi.binance.com/fapi/v1/depth?symbol={symbol}USDT&limit=1000"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.json()
    except: return None

def fetch_perp_oi(symbol):
    url = f"https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol}USDT"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        return float(data.get("openInterest", 0))
    except: return 0.0

# ── Logic ───────────────────────────────────────────────────────────────────

def calculate_pcr(options_data):
    if not options_data: return 0.0
    call_oi = sum(opt.get("open_interest", 0) for opt in options_data if opt.get("instrument_name", "").endswith("-C"))
    put_oi = sum(opt.get("open_interest", 0) for opt in options_data if opt.get("instrument_name", "").endswith("-P"))
    return put_oi / call_oi if call_oi > 0 else 0.0

def calculate_max_pain(options_data):
    if not options_data: return 0.0
    parsed = []
    strikes = set()
    for opt in options_data:
        parts = opt.get("instrument_name", "").split("-")
        if len(parts) < 4: continue
        try:
            s, t, oi = float(parts[2]), parts[3], float(opt.get("open_interest", 0))
            strikes.add(s)
            parsed.append({"strike": s, "type": t, "oi": oi})
        except: continue
    if not strikes: return 0.0
    min_loss, mp_strike = float('inf'), 0.0
    for ep in sorted(strikes):
        loss = sum(max(0, ep-o["strike"])*o["oi"] if o["type"] == "C" else max(0, o["strike"]-ep)*o["oi"] for o in parsed)
        if loss < min_loss: min_loss, mp_strike = loss, ep
    return mp_strike

def generate_liquidation_map(depth_data, symbol):
    """
    Groups order book depth into price bins to identify Liquidity Walls.
    Walls are high-density zones where liquidations are triggered or absorbed.
    """
    if not depth_data: return []
    
    bin_size = 100 if symbol == "BTC" else (10 if symbol == "ETH" else 1)
    bins = defaultdict(float)
    
    # Process Bids (Buy Walls) and Asks (Sell Walls)
    for side in ["bids", "asks"]:
        for price_str, qty_str in depth_data.get(side, []):
            p, q = float(price_str), float(qty_str)
            bin_p = int(round(p / bin_size) * bin_size)
            bins[bin_p] += (p * q)
            
    # Sort by notional volume (Liquidity Density)
    sorted_bins = sorted(bins.items(), key=lambda x: x[1], reverse=True)
    return sorted_bins[:10]

# ── UI ──────────────────────────────────────────────────────────────────────

def make_options_table(options_data, spot_price):
    table = Table(title="Options Chain (ATM)", expand=True)
    table.add_column("CALL LTP", justify="right", style="cyan")
    table.add_column("CALL OI", justify="right", style="magenta")
    table.add_column("STRIKE", justify="center", style="bold white")
    table.add_column("PUT OI", justify="right", style="magenta")
    table.add_column("PUT LTP", justify="right", style="cyan")
    if not options_data or not spot_price: return table
    strikes_data = {}
    for opt in options_data:
        parts = opt.get("instrument_name", "").split("-")
        if len(parts) < 4: continue
        try:
            s, t = float(parts[2]), parts[3]
            ltp = float(opt.get("last_price", 0)) * spot_price
            if s not in strikes_data: strikes_data[s] = {"C": {"ltp": 0, "oi": 0}, "P": {"ltp": 0, "oi": 0}}
            strikes_data[s][t] = {"ltp": ltp, "oi": float(opt.get("open_interest", 0))}
        except: continue
    sorted_s = sorted(strikes_data.keys())
    if not sorted_s: return table
    atm_idx = min(range(len(sorted_s)), key=lambda i: abs(sorted_s[i] - spot_price))
    for s in sorted_s[max(0, atm_idx-3):min(len(sorted_s), atm_idx+4)]:
        d = strikes_data[s]
        table.add_row(f"{d['C']['ltp']:,.1f}", f"{d['C']['oi']:,.1f}", f"{s:,.0f}", f"{d['P']['oi']:,.1f}", f"{d['P']['ltp']:,.1f}")
    return table

def make_liquidation_map_table(liq_map, perp_oi):
    table = Table(title="Liquidation Map (Liquidity Walls)", expand=True)
    table.add_column("ZONE (PRICE)", justify="left", style="yellow")
    table.add_column("LIQUIDITY", justify="right", style="green")
    table.add_column("DENSITY", justify="left")
    
    if not liq_map:
        table.add_row("Calculating...", f"OI: {perp_oi:,.0f}", "[░░░░░░░░░░░░░░░]")
        return table
        
    max_liq = max(b[1] for b in liq_map)
    for price, liq in liq_map:
        bar_len = int((liq / max_liq) * 15)
        bar = "█" * bar_len + "░" * (15 - bar_len)
        percentage = (liq / max_liq) * 100
        table.add_row(f"{price:,.0f}", f"${liq/1e6:.1f}M", f"[{bar}] {percentage:.0f}%")
    return table

def render_dashboard(asset):
    with ThreadPoolExecutor(max_workers=3) as executor:
        f_deribit = executor.submit(fetch_deribit_quotes, asset)
        f_depth = executor.submit(fetch_binance_depth, asset)
        f_oi = executor.submit(fetch_perp_oi, asset)
        
        res_deribit, depth_data, perp_oi = f_deribit.result(), f_depth.result(), f_oi.result()

    data = res_deribit.get("result", []) if res_deribit else []
    spot = data[0].get("underlying_price", 0) if data else 0
    pcr, mp = calculate_pcr(data), calculate_max_pain(data)
    liq_map = generate_liquidation_map(depth_data, asset)
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    header_text = f"[bold green]{asset}-DASHBOARD[/] | {timestamp} | SPOT: {spot:,.2f} | MAX PAIN: {mp:,.0f} | PCR: {pcr:.2f}"
    header = Panel(Text.from_markup(header_text), style="white")
    
    layout = Layout()
    layout.split_column(Layout(header, size=3), Layout(name="main"))
    layout["main"].split_row(
        Layout(Panel(make_options_table(data, spot))),
        Layout(Panel(make_liquidation_map_table(liq_map, perp_oi)))
    )
    return layout

def main():
    assets, idx = ["BTC", "ETH", "SOL"], 0
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
