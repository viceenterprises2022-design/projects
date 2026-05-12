#!/usr/bin/env python3
import requests
import datetime
import time
import os
import sys
import math
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.columns import Columns
from rich.box import ROUNDED, DOUBLE_EDGE

# ── Config ────────────────────────────────────────────────────────────────────
SYMBOLS = ["BTC", "ETH", "SOL"]
POLL_INTERVAL = 30 # Seconds

# API Endpoints
BINANCE_SPOT_URL = "https://api.binance.com/api/v3/klines"
BINANCE_FUT_URL = "https://fapi.binance.com/fapi/v1/klines"
BINANCE_FUT_OI_URL = "https://fapi.binance.com/fapi/v1/openInterest"
DERIBIT_URL = "https://www.deribit.com/api/v2/public"
YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/"
YH = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

console = Console()

# ── State ─────────────────────────────────────────────────────────────────────
history = {} # Stores trending OI data {symbol: [row1, row2, ...]}
prev_oi = {} # {symbol: {call_oi: X, put_oi: Y}}

# ── Data Fetching ─────────────────────────────────────────────────────────────

def fetch_json(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=10, headers=YH)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def fetch_yahoo(symbol):
    end = int(time.time()); start = end - 5 * 86400 # 5 days for data
    data = fetch_json(f"{YAHOO_URL}{symbol}", {"period1": start, "period2": end, "interval": "1d"})
    try:
        res = data["chart"]["result"][0]
        closes = res["indicators"]["quote"][0]["close"]
        closes = [c for c in closes if c is not None]
        if len(closes) >= 2:
            ltp = closes[-1]
            prev = closes[-2]
            chg_pct = (ltp - prev) / prev * 100
            return {"ltp": ltp, "change_pct": chg_pct}
    except:
        pass
    return None

def get_binance_data(symbol):
    # Fetch 100 candles for indicators
    spot_klines = fetch_json(BINANCE_SPOT_URL, {"symbol": f"{symbol}USDT", "interval": "1d", "limit": 100})
    oi_data = fetch_json(BINANCE_FUT_OI_URL, {"symbol": f"{symbol}USDT"})
    
    if not spot_klines: return None
    
    candles = [[float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])] for c in spot_klines] # O, H, L, C, V
    ltp = candles[-1][3]
    prev_close = candles[-2][3] if len(candles) > 1 else ltp
    change_pct = (ltp - prev_close) / prev_close * 100
    
    res = {
        "ltp": ltp,
        "change_pct": change_pct,
        "ohlc": {"o": candles[-1][0], "h": candles[-1][1], "l": candles[-1][2], "c": candles[-1][3]},
        "candles": candles,
        "oi": float(oi_data.get("openInterest", 0)) if oi_data else 0
    }
    return res

def get_deribit_data(symbol, spot_price):
    summary = fetch_json(f"{DERIBIT_URL}/get_book_summary_by_currency", {"currency": symbol, "kind": "option"})
    if not summary or "result" not in summary: return None
    
    results = summary["result"]
    
    # Nearest expiry
    def parse_expiry(name):
        parts = name.split('-')
        return parts[1] if len(parts) > 1 else "99999999"
    
    unique_expiries = sorted(list(set([parse_expiry(s["instrument_name"]) for s in results])))
    if not unique_expiries: return None
    nearest_exp = unique_expiries[0]
    
    # Filter for nearest expiry
    expiry_data = [s for s in results if nearest_exp in s["instrument_name"]]
    
    # Build chain
    chain = {}
    for s in expiry_data:
        name = s["instrument_name"]
        parts = name.split('-')
        if len(parts) < 4: continue
        strike = float(parts[2])
        side = parts[3] # C or P
        
        if strike not in chain:
            chain[strike] = {"strike": strike, "call": None, "put": None}
        
        # Underlying price for conversion (options usually in BTC/ETH)
        u_price = s.get("underlying_price", spot_price) or spot_price
        
        data = {
            "ltp": (s.get("last", 0) or 0) * u_price,
            "oi": s.get("open_interest", 0) or 0,
            "iv": s.get("bid_iv", 0) or s.get("ask_iv", 0) or 0
        }
        
        if side == "C": chain[strike]["call"] = data
        else: chain[strike]["put"] = data
        
    strikes = sorted(chain.keys())
    # Filter strikes around ATM
    step = strikes_step(spot_price)
    atm_strike = min(strikes, key=lambda x: abs(x - spot_price))
    idx = strikes.index(atm_strike)
    start = max(0, idx - 10)
    end = min(len(strikes), idx + 11)
    filtered_strikes = [chain[s] for s in strikes[start:end]]
    
    # Calculate PCR and Max Pain
    total_call_oi = sum(s["call"]["oi"] for s in chain.values() if s["call"])
    total_put_oi = sum(s["put"]["oi"] for s in chain.values() if s["put"])
    pcr = total_put_oi / max(total_call_oi, 1)
    
    # Max Pain
    def mp_loss(target):
        loss = 0
        for s in chain.values():
            k = s["strike"]
            if target > k and s["call"]: loss += s["call"]["oi"] * (target - k)
            if target < k and s["put"]: loss += s["put"]["oi"] * (k - target)
        return loss
    
    min_loss = float('inf')
    max_pain = atm_strike
    for s in strikes:
        loss = mp_loss(s)
        if loss < min_loss:
            min_loss = loss
            max_pain = s
            
    # Resistance/Support (Strikes with max OI)
    calls = sorted([s for s in chain.values() if s["call"]], key=lambda x: x["call"]["oi"], reverse=True)
    puts = sorted([s for s in chain.values() if s["put"]], key=lambda x: x["put"]["oi"], reverse=True)
    
    return {
        "expiry": nearest_exp,
        "strikes": filtered_strikes,
        "pcr": pcr,
        "max_pain": max_pain,
        "total_call_oi": total_call_oi,
        "total_put_oi": total_put_oi,
        "resist": [c["strike"] for c in calls[:3]],
        "support": [p["strike"] for p in puts[:3]]
    }

# ── Indicators Logic ──────────────────────────────────────────────────────────

def calculate_indicators(candles, ltp):
    closes = [c[3] for c in candles]
    
    def ema(v, n):
        if len(v) < n: return v[-1] if v else 0
        k = 2 / (n + 1)
        res = sum(v[:n]) / n
        for x in v[n:]:
            res = x * k + res * (1 - k)
        return res

    # 1. TREND
    e20 = ema(closes, 20)
    e50 = ema(closes, 50)
    label, score = "NEUTRAL", 0
    if ltp > e20 > e50: label, score = "STRONG UPTREND", 1
    elif ltp < e20 < e50: label, score = "STRONG DOWNTREND", -1
    elif ltp > e20: label, score = "UPTREND", 1
    elif ltp < e20: label, score = "DOWNTREND", -1
    trend = {"label": label, "score": score}

    # 2. RSI
    def rsi_val(v, n=14):
        if len(v) < n + 1: return 50
        gains = [max(v[i] - v[i-1], 0) for i in range(1, len(v))]
        losses = [max(v[i-1] - v[i], 0) for i in range(1, len(v))]
        ag = sum(gains[-n:]) / n
        al = sum(losses[-n:]) / n
        if al == 0: return 100
        return 100 - 100 / (1 + ag / al)
    
    rv = rsi_val(closes)
    rsi_label, rsi_score = "NEUTRAL", 0
    if rv > 70: rsi_label, rsi_score = f"OVERBOUGHT ({rv:.1f})", -1
    elif rv > 60: rsi_label, rsi_score = f"BULLISH ZONE ({rv:.1f})", 1
    elif rv < 30: rsi_label, rsi_score = f"OVERSOLD ({rv:.1f})", 1
    elif rv < 40: rsi_label, rsi_score = f"BEARISH ZONE ({rv:.1f})", -1
    else: rsi_label = f"NEUTRAL ({rv:.1f})"
    rsi = {"label": rsi_label, "score": rsi_score}

    # 3. SUPERTREND (Simulated)
    def atr(c, n=14):
        if len(c) < n + 1: return 0
        trs = [max(c[i][1] - c[i][2], abs(c[i][1] - c[i-1][3]), abs(c[i][2] - c[i-1][3])) for i in range(1, len(c))]
        return sum(trs[-n:]) / n
    
    a = atr(candles)
    hl2 = (candles[-1][1] + candles[-1][2]) / 2
    sup = hl2 - 3 * a
    st_label, st_score = ("BULLISH", 1) if ltp > sup else ("BEARISH", -1)
    supertrend = {"label": f"{st_label} (Sup≈{sup:,.0f})", "score": st_score}
    
    # 4. VWAP
    def vwap(c, n=20):
        total_pv = sum(((x[1]+x[2]+x[3])/3) * x[4] for x in c[-n:])
        total_v = sum(x[4] for x in c[-n:])
        return total_pv / total_v if total_v > 0 else ltp
    
    vw = vwap(candles)
    vw_label = f"ABOVE (+{(ltp-vw)/vw*100:.2f}%)" if ltp > vw else f"BELOW ({(ltp-vw)/vw*100:.2f}%)"
    vwap_data = {"label": vw_label, "score": 1 if ltp > vw else -1}

    return {
        "TREND": trend,
        "RSI": rsi,
        "SUPERTREND": supertrend,
        "VWAP": vwap_data
    }

# ── Rendering ─────────────────────────────────────────────────────────────────

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=4),
        Layout(name="indicators", size=12),
        Layout(name="options", size=25),
        Layout(name="footer", size=25)
    )
    return layout

def get_diagnostics(symbol, binance, deribit, macro):
    indicators = calculate_indicators(binance["candles"], binance["ltp"])
    
    sc = sum(i["score"] for i in indicators.values())
    factors = len(indicators)
    
    # Add macro scores
    if macro["DXY"]:
        chg = macro["DXY"]["change_pct"]
        sc += (-1 if chg > 0.1 else 1 if chg < -0.1 else 0)
        factors += 1
        
    signal = "NEUTRAL"
    if sc >= 3: signal = "BULLISH"
    elif sc <= -3: signal = "BEARISH"
    
    score_text = f"{signal} ({sc}/{factors})"
    color = "green" if sc > 0 else "red" if sc < 0 else "yellow"
    
    content = Text.assemble(
        (" LTP: ", "white"), (f"{binance['ltp']:,.2f}", "cyan bold"),
        (f" ({binance['change_pct']:+.2f}%)", "green" if binance['change_pct'] >= 0 else "red"),
        ("  |  Signal: ", "white"), (score_text, f"{color} bold")
    )
    
    return Panel(content, title=f" ⚡ AlphaEdge Diagnostics: {symbol} ", border_style="white", box=ROUNDED, padding=(0, 2))

def get_indicators_table(symbol, binance, deribit, macro):
    table = Table(box=None, padding=(0, 2), expand=True, show_header=True)
    table.add_column("Indicator", style="white", width=15)
    table.add_column("Status", style="white", width=40)
    table.add_column("Score", justify="right", width=10)
    
    inds = calculate_indicators(binance["candles"], binance["ltp"])
    
    for name, data in inds.items():
        score_str = f"{data['score']:+d}"
        color = "green" if data['score'] > 0 else "red" if data['score'] < 0 else "white"
        table.add_row(name, data['label'], f"[{color}]{score_str}[/]")
        
    # Macro rows
    if macro["DXY"]:
        chg = macro["DXY"]["change_pct"]
        s = -1 if chg > 0.1 else 1 if chg < -0.1 else 0
        table.add_row("DXY", f"{'STRENGTHENING' if chg > 0.1 else 'WEAKENING' if chg < -0.1 else 'STABLE'} ({chg:+.2f}%)", f"{s:+d}")
        
    if macro["VIX"]:
        val = macro["VIX"]["ltp"]
        s = 0
        if val < 13: s, status = 1, "CALM"
        elif val <= 17: s, status = 1, "STABLE"
        elif val <= 21: s, status = 0, "CAUTION"
        else: s, status = -1, "FEAR"
        table.add_row("VIX (US)", f"{status} ({val:.2f})", f"{s:+d}")

    if deribit:
        pcr = deribit["pcr"]
        s = 1 if pcr > 1.1 else -1 if pcr < 0.7 else 0
        status = "NEUTRAL"
        if pcr > 1.1: status = "BULLISH"
        elif pcr < 0.7: status = "BEARISH"
        table.add_row("PCR", f"{status} — PCR {pcr:.2f}", f"{s:+d}")

    return table

def get_option_chain_table(deribit, spot):
    if not deribit: return Panel("Option Chain Data Unavailable", border_style="red")
    
    title = f" Option Chain — Expiry: {deribit['expiry']} | DTE: ? | Max Pain: {deribit['max_pain']:,.0f} "
    table = Table(title=title, box=None, header_style="bold cyan", padding=(0, 1), expand=True)
    
    table.add_column("C.LTP", justify="right")
    table.add_column("C.IV%", justify="right")
    table.add_column("C.OI", justify="right")
    table.add_column("C.ΔOI", justify="right")
    table.add_column("STRIKE", justify="center", style="yellow bold")
    table.add_column("P.ΔOI", justify="right")
    table.add_column("P.OI", justify="right")
    table.add_column("P.IV%", justify="right")
    table.add_column("P.LTP", justify="right")
    
    step = strikes_step(spot)
    for s in deribit["strikes"]:
        c = s["call"]
        p = s["put"]
        strike = s["strike"]
        
        strike_str = f"{strike:,.0f}"
        if abs(strike - spot) < (step / 2):
            strike_str = f"►{strike_str}◄"
        if strike == deribit["max_pain"]:
            strike_str += " MP"
            
        table.add_row(
            f"{c['ltp']:.1f}" if c else "—",
            f"{c['iv']*100:.1f}" if c else "—",
            f"{c['oi']/1000:.1f}L" if c else "—", # Use L for Lakh equivalent or just K for Crypto
            "—",
            strike_str,
            "—",
            f"{p['oi']/1000:.1f}L" if p else "—",
            f"{p['iv']*100:.1f}" if p else "—",
            f"{p['ltp']:.1f}" if p else "—"
        )
        
    return table

def strikes_step(price):
    if price > 20000: return 500
    if price > 1000: return 50
    return 10

def get_market_intelligence(symbol, deribit):
    if not deribit: return Panel("N/A")
    
    # PCR Panel
    pcr_text = Text.assemble(
        ("  PCR       ", "white"), (f"{deribit['pcr']:.2f}\n", "cyan"),
        ("  Max Pain  ", "white"), (f"{deribit['max_pain']:,.0f}\n", "cyan"),
        ("  OI Build  ", "white"), ("Neutral\n", "yellow"),
        ("  Calls     ", "white"), (f"{deribit['total_call_oi']/1000:,.0f}L\n", "red"),
        ("  Puts      ", "white"), (f"{deribit['total_put_oi']/1000:,.0f}L", "green")
    )
    pcr_panel = Panel(pcr_text, border_style="white", box=ROUNDED, expand=False)
    
    # Support/Resistance Panel
    sr_text = Text.assemble(
        ("  Resist   ", "white"), (", ".join([f"{x:,.0f}" for x in deribit['resist']]), "red"), ("\n", ""),
        ("  Support  ", "white"), (", ".join([f"{x:,.0f}" for x in deribit['support']]), "green")
    )
    sr_panel = Panel(sr_text, border_style="white", box=ROUNDED, expand=False)
    
    return Columns([pcr_panel, sr_panel], padding=(0, 2))

def get_trending_oi_table(symbol, binance, deribit):
    table = Table(title=" Trending OI (Intraday) ", box=None, header_style="bold cyan", padding=(0, 2), expand=True)
    table.add_column("Time", style="dim")
    table.add_column("LTP", justify="right")
    table.add_column("ΔCall OI", justify="right")
    table.add_column("ΔPut OI", justify="right")
    table.add_column("Diff", justify="right")
    table.add_column("PCR", justify="right")
    table.add_column("Sentiment", justify="center")
    
    now = datetime.datetime.now().strftime("%H:%M")
    ltp = binance["ltp"]
    pcr = deribit["pcr"] if deribit else 0
    
    if symbol not in history: history[symbol] = []
    
    # Delta calculation
    d_call = 0
    d_put = 0
    if deribit:
        if symbol in prev_oi:
            d_call = deribit["total_call_oi"] - prev_oi[symbol]["call_oi"]
            d_put = deribit["total_put_oi"] - prev_oi[symbol]["put_oi"]
        prev_oi[symbol] = {"call_oi": deribit["total_call_oi"], "put_oi": deribit["total_put_oi"]}
        
    diff = (deribit["total_put_oi"] - deribit["total_call_oi"]) if deribit else 0
    sentiment = "Bullish" if pcr > 1.1 else "Bearish" if pcr < 0.9 else "Neutral"
    sent_color = "green" if sentiment == "Bullish" else "red" if sentiment == "Bearish" else "yellow"
    
    row = [now, f"{ltp:,.2f}", f"{d_call:,.0f}", f"{d_put:,.0f}", f"{diff:,.0f}", f"{pcr:.2f}", f"[{sent_color}]{sentiment}[/]"]
    
    # Only add row if it's a new minute or first entry
    if not history[symbol] or history[symbol][0][0] != now:
        history[symbol].insert(0, row)
        history[symbol] = history[symbol][:15]
    else:
        # Update current row
        history[symbol][0] = row
    
    for r in history[symbol]:
        table.add_row(*r)
        
    return table

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    with Live(auto_refresh=False, screen=True) as live:
        while True:
            # 1. Fetch Global Macro
            macro = {
                "DXY": fetch_yahoo("DX-Y.NYB"),
                "VIX": fetch_yahoo("^VIX")
            }
            
            for sym in SYMBOLS:
                binance = get_binance_data(sym)
                if not binance: continue
                
                deribit = get_deribit_data(sym, binance["ltp"])
                
                layout = make_layout()
                layout["header"].update(get_diagnostics(sym, binance, deribit, macro))
                layout["indicators"].update(get_indicators_table(sym, binance, deribit, macro))
                layout["options"].update(get_option_chain_table(deribit, binance["ltp"]))
                
                footer_layout = Layout()
                footer_layout.split_column(
                    Layout(get_market_intelligence(sym, deribit), name="intel", size=7),
                    Layout(get_trending_oi_table(sym, binance, deribit), name="trending")
                )
                layout["footer"].update(footer_layout)
                
                live.update(layout, refresh=True)
                time.sleep(POLL_INTERVAL / len(SYMBOLS))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]Exiting...[/]")
        sys.exit(0)
    except Exception as e:
        console.print_exception()
        sys.exit(1)
