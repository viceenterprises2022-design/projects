"""
Crypto Options & Liquidation Dashboard (Unified Multi-Asset Edition).
Displays BTC, ETH, and SOL data simultaneously in a single window.
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
from rich.columns import Columns

POLL_INTERVAL = 15
console = Console(width=107)

# ── Logging ──────────────────────────────────────────────────────────────────

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

# ── Fetchers ────────────────────────────────────────────────────────────────

def fetch_deribit_quotes(currency):
    """Fetch options book summary from Deribit. Handles SOL via USDC-settled query."""
    target_curr = currency
    if currency == "SOL":
        target_curr = "USDC"
        
    url = f"https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency={target_curr}&kind=option"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if currency == "SOL":
            filtered = [item for item in data.get("result", []) if item.get("instrument_name", "").startswith("SOL_USDC")]
            return {"result": filtered}
        return data
    except: return None

def fetch_binance_depth(symbol):
    """Fetch 1000 levels of depth to find liquidity walls."""
    url = f"https://fapi.binance.com/fapi/v1/depth?symbol={symbol}USDT&limit=1000"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.json()
    except: return None

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
    if not depth_data: return []
    bin_size = 100 if symbol == "BTC" else (10 if symbol == "ETH" else 1)
    bins = defaultdict(lambda: {"buy": 0.0, "sell": 0.0})
    for side in ["bids", "asks"]:
        key = "buy" if side == "bids" else "sell"
        for price_str, qty_str in depth_data.get(side, []):
            p, q = float(price_str), float(qty_str)
            bin_p = int(round(p / bin_size) * bin_size)
            bins[bin_p][key] += (p * q)
    flattened = []
    for p, v in bins.items():
        total = v["buy"] + v["sell"]
        flattened.append((p, v["buy"], v["sell"], total))
    return sorted(flattened, key=lambda x: x[3], reverse=True)[:5] # Top 5 only for unified view

# ── UI ──────────────────────────────────────────────────────────────────────

def make_options_table(options_data, spot_price):
    table = Table(expand=True, show_header=True, header_style="bold cyan", box=None)
    table.add_column("LTP", justify="right")
    table.add_column("STRIKE", justify="center", style="bold white")
    table.add_column("OI", justify="right")
    
    if not options_data or not spot_price:
        table.add_row("", "No Data", "")
        return table
        
    strikes_data = {}
    for opt in options_data:
        parts = opt.get("instrument_name", "").split("-")
        if len(parts) < 4: continue
        try:
            s, t = float(parts[2]), parts[3]
            if s not in strikes_data: strikes_data[s] = {"C": {"ltp": 0, "oi": 0}, "P": {"ltp": 0, "oi": 0}}
            strikes_data[s][t] = {"ltp": float(opt.get("last_price", 0)) * spot_price, "oi": float(opt.get("open_interest", 0))}
        except: continue
        
    sorted_s = sorted(strikes_data.keys())
    if not sorted_s: return table
    
    atm_idx = min(range(len(sorted_s)), key=lambda i: abs(sorted_s[i] - spot_price))
    for s in sorted_s[max(0, atm_idx-2):min(len(sorted_s), atm_idx+3)]:
        d = strikes_data[s]
        # Merged representation: CE LTP | Strike | PE OI
        table.add_row(f"{d['C']['ltp']:,.0f}", f"{s:,.0f}", f"{d['P']['oi']:,.0f}")
    return table

def make_liquidation_map_table(liq_map):
    table = Table(expand=True, box=None)
    table.add_column("ZONE", justify="left", style="yellow")
    table.add_column("LIQ", justify="right")
    table.add_column("D", justify="left")
    
    if not liq_map:
        table.add_row("Loading...", "", "")
        return table
        
    max_liq = max(b[3] for b in liq_map)
    for price, buy, sell, total in liq_map:
        bar_len = int((total / max_liq) * 5)
        color = "[green]" if buy > sell else "[red]"
        bar = f"{color}{'█' * bar_len}[/]" + "░" * (5 - bar_len)
        table.add_row(f"{price:,.0f}", f"${total/1e6:.1f}M", bar)
    return table

def create_asset_panel(asset, data, depth_data):
    spot = data[0].get("underlying_price", 0) if data else 0
    pcr, mp = calculate_pcr(data), calculate_max_pain(data)
    liq_map = generate_liquidation_map(depth_data, asset)
    
    header_text = f"[bold green]{asset}[/] | SPOT: {spot:,.1f} | MP: {mp:,.0f} | PCR: {pcr:.2f}"
    
    content_layout = Layout()
    content_layout.split_row(
        Layout(make_options_table(data, spot), name="opts"),
        Layout(make_liquidation_map_table(liq_map), name="liq")
    )
    
    return Panel(content_layout, title=header_text, title_align="left", height=10)

def render_full_dashboard():
    assets = ["BTC", "ETH", "SOL"]
    all_data = {}
    
    with ThreadPoolExecutor(max_workers=6) as executor:
        f_deribit = {a: executor.submit(fetch_deribit_quotes, a) for a in assets}
        f_depth = {a: executor.submit(fetch_binance_depth, a) for a in assets}
        
        for a in assets:
            res_d = f_deribit[a].result()
            res_depth = f_depth[a].result()
            all_data[a] = {
                "options": res_d.get("result", []) if res_d else [],
                "depth": res_depth
            }

    timestamp = datetime.now().strftime("%H:%M:%S")
    root = Layout()
    root.split_column(
        Layout(Panel(Text(f"CRYPTO UNIFIED DASHBOARD | {timestamp}", justify="center", style="bold white"), style="blue"), size=3),
        Layout(name="assets")
    )
    
    root["assets"].split_column(
        Layout(create_asset_panel("BTC", all_data["BTC"]["options"], all_data["BTC"]["depth"])),
        Layout(create_asset_panel("ETH", all_data["ETH"]["options"], all_data["ETH"]["depth"])),
        Layout(create_asset_panel("SOL", all_data["SOL"]["options"], all_data["SOL"]["depth"]))
    )
    
    return root

def main():
    try:
        with Live(render_full_dashboard(), refresh_per_second=0.2, screen=True) as live:
            while True:
                live.update(render_full_dashboard())
                time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()
