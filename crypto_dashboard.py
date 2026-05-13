"""
Crypto Options & Liquidation Dashboard (Depth Edition).
Shows Buy/Sell depth for both options and liquidity zones in a compact view.
"""

import time
import sys
import requests
import json
import threading
import logging
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

POLL_INTERVAL = 15
console = Console(width=105)

# ── Logging ──────────────────────────────────────────────────────────────────

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

# ── Fetchers ────────────────────────────────────────────────────────────────

def fetch_deribit_quotes(currency):
    target_curr = "USDC" if currency == "SOL" else currency
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
    url = f"https://fapi.binance.com/fapi/v1/depth?symbol={symbol}USDT&limit=1000"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.json()
    except: return None

# ── Logic ───────────────────────────────────────────────────────────────────

def calculate_pcr(options_data):
    if not options_data: return 0.0
    now = datetime.now()
    near_term_oi_call = 0.0
    near_term_oi_put = 0.0
    
    for opt in options_data:
        parts = opt.get("instrument_name", "").split("-")
        if len(parts) < 4: continue
        try:
            exp_date = datetime.strptime(parts[1], "%d%b%y")
            if (exp_date - now).days <= 7:
                oi = float(opt.get("open_interest", 0))
                if parts[3] == "C": near_term_oi_call += oi
                else: near_term_oi_put += oi
        except: continue
        
    return near_term_oi_put / near_term_oi_call if near_term_oi_call > 0 else 0.0

def calculate_max_pain(options_data):
    if not options_data: return 0.0
    now = datetime.now()
    parsed, strikes = [], set()
    
    for opt in options_data:
        parts = opt.get("instrument_name", "").split("-")
        if len(parts) < 4: continue
        try:
            exp_date = datetime.strptime(parts[1], "%d%b%y")
            # Only include expiries in the next 7 days
            if (exp_date - now).days <= 7:
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
    # Reduced bin sizes to increase resolution for BTC and ETH
    bin_size = 10 if symbol == "BTC" else (1 if symbol == "ETH" else 1)
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
    # Get top 10 by total volume first
    top_vols = sorted(flattened, key=lambda x: x[3], reverse=True)[:10]
    # Then sort those 10 by price (Zone) descending for a natural price map view
    return sorted(top_vols, key=lambda x: x[0], reverse=True)

# ── UI ──────────────────────────────────────────────────────────────────────

def make_options_table(options_data, spot_price):
    """Shows Call OI | Strike | Put OI depth."""
    table = Table(expand=True, box=None, padding=(0,1))
    table.add_column("C-OI", justify="right", style="cyan")
    table.add_column("STRIKE", justify="center", style="bold white")
    table.add_column("P-OI", justify="right", style="magenta")
    
    if not options_data or not spot_price:
        table.add_row("-", "-", "-")
        return table
        
    strikes_data = {}
    for opt in options_data:
        parts = opt.get("instrument_name", "").split("-")
        if len(parts) < 4: continue
        try:
            s, t = float(parts[2]), parts[3]
            if s not in strikes_data: strikes_data[s] = {"C": 0, "P": 0}
            strikes_data[s][t] = float(opt.get("open_interest", 0))
        except: continue
        
    sorted_s = sorted(strikes_data.keys())
    if not sorted_s: return table
    
    atm_idx = min(range(len(sorted_s)), key=lambda i: abs(sorted_s[i] - spot_price))
    # Show 10 strikes
    for s in sorted_s[max(0, atm_idx-4):min(len(sorted_s), atm_idx+6)]:
        d = strikes_data[s]
        table.add_row(f"{d['C']:,.1f}", f"{s:,.0f}", f"{d['P']:,.1f}")
    return table

def make_liquidation_map_table(liq_map):
    """Shows Buy Liquidity | Zone | Sell Liquidity depth."""
    table = Table(expand=True, box=None, padding=(0,1))
    table.add_column("BUY", justify="right", style="green")
    table.add_column("ZONE", justify="center", style="yellow")
    table.add_column("SELL", justify="left", style="red")
    
    if not liq_map:
        table.add_row("-", "-", "-")
        return table
        
    for price, buy, sell, total in liq_map:
        table.add_row(f"${buy/1e6:,.1f}M", f"{price:,.0f}", f"${sell/1e6:,.1f}M")
    return table

def create_asset_panel(asset, data, depth_data):
    spot = data[0].get("underlying_price", 0) if data else 0
    pcr, mp = calculate_pcr(data), calculate_max_pain(data)
    liq_map = generate_liquidation_map(depth_data, asset)
    
    header = f"[bold]{asset}[/] ${spot:,.0f} | MP:{mp:,.0f} | PCR:{pcr:.2f}"
    
    content_layout = Layout()
    content_layout.split_row(
        Layout(make_options_table(data, spot), ratio=1),
        Layout(make_liquidation_map_table(liq_map), ratio=1)
    )
    
    return Panel(content_layout, title=header, title_align="left", height=15)

def render_full_dashboard(all_data, countdown):
    timestamp = datetime.now().strftime("%H:%M:%S")
    root = Layout()
    root.split_column(
        Layout(Text(f"CRYPTO DEPTH MAP | {timestamp} | NEXT POLL: {countdown}s", justify="center", style="bold reverse"), size=1),
        Layout(name="assets")
    )
    
    root["assets"].split_column(
        Layout(create_asset_panel("BTC", all_data["BTC"]["options"], all_data["BTC"]["depth"])),
        Layout(create_asset_panel("ETH", all_data["ETH"]["options"], all_data["ETH"]["depth"])),
        Layout(create_asset_panel("SOL", all_data["SOL"]["options"], all_data["SOL"]["depth"]))
    )
    return root

def main():
    assets = ["BTC", "ETH", "SOL"]
    last_data = {a: {"options": [], "depth": None} for a in assets}
    
    def fetch_all():
        data = {}
        with ThreadPoolExecutor(max_workers=6) as executor:
            f_deribit = {a: executor.submit(fetch_deribit_quotes, a) for a in assets}
            f_depth = {a: executor.submit(fetch_binance_depth, a) for a in assets}
            for a in assets:
                res_d, res_depth = f_deribit[a].result(), f_depth[a].result()
                data[a] = {"options": res_d.get("result", []) if res_d else [], "depth": res_depth}
        return data

    try:
        last_data = fetch_all()
        countdown = POLL_INTERVAL
        with Live(render_full_dashboard(last_data, countdown), refresh_per_second=1, screen=True) as live:
            while True:
                time.sleep(1)
                countdown -= 1
                if countdown <= 0:
                    last_data = fetch_all()
                    countdown = POLL_INTERVAL
                live.update(render_full_dashboard(last_data, countdown))
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()
