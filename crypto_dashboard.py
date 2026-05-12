"""
Crypto Options & Liquidation Dashboard.
Fetches and displays market data for crypto options and liquidations.
"""

import time
import sys
import requests
import json
import threading
import websocket
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

POLL_INTERVAL = 5
console = Console(width=107)

# ── Liquidation Collector ───────────────────────────────────────────────────

class LiquidationCollector:
    """
    Collects real-time liquidations from Binance and Bybit via WebSockets.
    Maintains a rolling buffer of events for each symbol.
    """
    def __init__(self, symbols=["BTC", "ETH", "SOL"]):
        self.symbols = symbols
        self.buffer = defaultdict(list)
        self.max_buffer_size = 500
        self.lock = threading.Lock()
        self.running = True
        
    def add_event(self, symbol, price, qty, exchange):
        with self.lock:
            self.buffer[symbol].append({
                "price": price,
                "qty": qty,
                "exchange": exchange,
                "timestamp": time.time()
            })
            # Trim buffer
            if len(self.buffer[symbol]) > self.max_buffer_size:
                self.buffer[symbol].pop(0)

    def get_events(self, symbol):
        # Cleanup old events (older than 24h)
        now = time.time()
        with self.lock:
            self.buffer[symbol] = [e for e in self.buffer[symbol] if now - e["timestamp"] < 86400]
            return list(self.buffer[symbol])

    def _on_binance_message(self, ws, message):
        try:
            data = json.loads(message)
            order = data.get("o", {})
            raw_sym = order.get("s", "")
            for s in self.symbols:
                if raw_sym == f"{s}USDT":
                    self.add_event(s, float(order["p"]), float(order["q"]), "Binance")
                    break
        except Exception:
            pass

    def _on_bybit_message(self, ws, message):
        try:
            data = json.loads(message)
            # Bybit V5: {"topic":"allLiquidation.BTCUSDT","data":{...}}
            topic = data.get("topic", "")
            if "allLiquidation" in topic:
                liq_data = data.get("data", {})
                raw_sym = liq_data.get("s", "")
                for s in self.symbols:
                    if raw_sym == f"{s}USDT":
                        self.add_event(s, float(liq_data["p"]), float(liq_data["v"]), "Bybit")
                        break
        except Exception:
            pass

    def _run_binance(self):
        url = "wss://fstream.binance.com/ws/!forceOrder@arr"
        while self.running:
            try:
                ws = websocket.WebSocketApp(url, on_message=self._on_binance_message)
                ws.run_forever()
            except Exception:
                time.sleep(5)

    def _run_bybit(self):
        url = "wss://stream.bybit.com/v5/public/linear"
        while self.running:
            try:
                ws = websocket.WebSocketApp(url, on_message=self._on_bybit_message)
                def on_open(ws):
                    subs = [f"allLiquidation.{s}USDT" for s in self.symbols]
                    ws.send(json.dumps({"op": "subscribe", "args": subs}))
                ws.on_open = on_open
                ws.run_forever()
            except Exception:
                time.sleep(5)

    def start(self):
        threading.Thread(target=self._run_binance, daemon=True).start()
        threading.Thread(target=self._run_bybit, daemon=True).start()

    def stop(self):
        self.running = False

# Global collector instance
liq_collector = LiquidationCollector()

# ── Fetchers ────────────────────────────────────────────────────────────────

def fetch_deribit_quotes(currency):
    """Fetch options book summary from Deribit."""
    url = f"https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency={currency}&kind=option"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.RequestException, ValueError):
        return None

def fetch_perp_oi(symbol):
    """Fetch Perpetual Open Interest from Binance."""
    url = f"https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol}USDT"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        return float(data.get("openInterest", 0))
    except Exception:
        return 0.0

# ── Logic ───────────────────────────────────────────────────────────────────

def calculate_pcr(options_data):
    if not options_data: return 0.0
    call_oi = 0.0
    put_oi = 0.0
    for opt in options_data:
        instrument = opt.get("instrument_name", "")
        oi = opt.get("open_interest", 0)
        if instrument.endswith("-C"): call_oi += oi
        elif instrument.endswith("-P"): put_oi += oi
    return put_oi / call_oi if call_oi > 0 else 0.0

def calculate_max_pain(options_data):
    if not options_data: return 0.0
    parsed_data = []
    strikes = set()
    for opt in options_data:
        name = opt.get("instrument_name", "")
        parts = name.split("-")
        if len(parts) < 4: continue
        try:
            strike = float(parts[2])
            opt_type = parts[3]
            oi = float(opt.get("open_interest", 0))
            strikes.add(strike)
            parsed_data.append({"strike": strike, "type": opt_type, "oi": oi})
        except (ValueError, IndexError): continue
    if not strikes: return 0.0
    min_loss = float('inf')
    max_pain_strike = 0.0
    for ep in sorted(strikes):
        loss = sum(max(0, ep - o["strike"]) * o["oi"] if o["type"] == "C" else max(0, o["strike"] - ep) * o["oi"] for o in parsed_data)
        if loss < min_loss:
            min_loss = loss
            max_pain_strike = ep
    return max_pain_strike

def aggregate_liquidation_bins(symbol):
    events = liq_collector.get_events(symbol)
    if not events: return []
    bin_size = 100 if symbol == "BTC" else (10 if symbol == "ETH" else 1)
    bins = {}
    for e in events:
        price = e["price"]
        vol = price * e["qty"]
        bin_price = int(round(price / bin_size) * bin_size)
        bins[bin_price] = bins.get(bin_price, 0) + vol
    return sorted(bins.items(), key=lambda x: x[1], reverse=True)[:10]

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
            strike = float(parts[2])
            opt_type = parts[3]
            ltp = float(opt.get("last_price", 0)) * spot_price
            oi = float(opt.get("open_interest", 0))
            if strike not in strikes_data: strikes_data[strike] = {"C": {"ltp": 0, "oi": 0}, "P": {"ltp": 0, "oi": 0}}
            strikes_data[strike][opt_type] = {"ltp": ltp, "oi": oi}
        except Exception: continue
    sorted_s = sorted(strikes_data.keys())
    if not sorted_s: return table
    atm_idx = min(range(len(sorted_s)), key=lambda i: abs(sorted_s[i] - spot_price))
    for s in sorted_s[max(0, atm_idx-3):min(len(sorted_s), atm_idx+4)]:
        d = strikes_data[s]
        table.add_row(f"{d['C']['ltp']:,.1f}", f"{d['C']['oi']:,.1f}", f"{s:,.0f}", f"{d['P']['oi']:,.1f}", f"{d['P']['ltp']:,.1f}")
    return table

def make_liquidation_table(liq_bins, perp_oi):
    table = Table(title="Liquidation Density (Live)", expand=True)
    table.add_column("PRICE", justify="left")
    table.add_column("VOLUME", justify="right")
    table.add_column("DENSITY", justify="left")
    if not liq_bins:
        table.add_row("Waiting for data...", f"OI: {perp_oi:,.0f}", "[░░░░░░░░░░░░░░░]")
        return table
    max_vol = max(b[1] for b in liq_bins)
    for price, vol in liq_bins:
        bar_len = int((vol / max_vol) * 15)
        table.add_row(f"{price:,.0f}", f"${vol/1e3:.1f}k" if vol < 1e6 else f"${vol/1e6:.1f}M", f"[{'█'*bar_len}{'░'*(15-bar_len)}]")
    return table

def render_dashboard(asset):
    with ThreadPoolExecutor(max_workers=2) as executor:
        f_deribit = executor.submit(fetch_deribit_quotes, asset)
        f_oi = executor.submit(fetch_perp_oi, asset)
        res_deribit = f_deribit.result()
        perp_oi = f_oi.result()

    data = res_deribit.get("result", []) if res_deribit else []
    spot = data[0].get("underlying_price", 0) if data else 0
    pcr, mp = calculate_pcr(data), calculate_max_pain(data)
    liq_bins = aggregate_liquidation_bins(asset)
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    header = Panel(Text.from_markup(f"[bold green]{asset}-DASHBOARD[/] | {timestamp} | SPOT: {spot:,.2f} | MAX PAIN: {mp:,.0f} | PCR: {pcr:.2f}"), style="white")
    
    layout = Layout()
    layout.split_column(Layout(header, size=3), Layout(name="main"))
    layout["main"].split_row(Layout(Panel(make_options_table(data, spot))), Layout(Panel(make_liquidation_table(liq_bins, perp_oi))))
    return layout

def main():
    liq_collector.start()
    assets, idx = ["BTC", "ETH", "SOL"], 0
    try:
        with Live(render_dashboard(assets[0]), refresh_per_second=1, screen=True) as live:
            while True:
                live.update(render_dashboard(assets[idx]))
                time.sleep(POLL_INTERVAL)
                idx = (idx + 1) % len(assets)
    except KeyboardInterrupt:
        liq_collector.stop()
        sys.exit(0)

if __name__ == "__main__":
    main()
