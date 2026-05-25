#!/usr/bin/env python3
import asyncio
import aiohttp
import os
import sys
import datetime
import time
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.text import Text
from rich import box
from rich.rule import Rule

# ── Load Credentials ──────────────────────────────────────────────────────────
upstox_token = None
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            if line.startswith("UPSTOX_TOKEN="):
                upstox_token = line.strip().split("=", 1)[1]
                break

if not upstox_token:
    print("[ERROR] UPSTOX_TOKEN not found in .env file")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {upstox_token}",
    "Accept": "application/json"
}

# ── Config ────────────────────────────────────────────────────────────────────
INDICES = {
    "NIFTY 50": "NSE_INDEX|Nifty 50",
    "NIFTY BANK": "NSE_INDEX|Nifty Bank",
    "INDIA VIX": "NSE_INDEX|India VIX"
}

WATCHLIST = {
    "RELIANCE": "NSE_EQ|INE002A01018",
    "HDFCBANK": "NSE_EQ|INE040A01034",
    "ICICIBANK": "NSE_EQ|INE090A01021",
    "INFY": "NSE_EQ|INE009A01021",
    "TCS": "NSE_EQ|INE467B01029",
    "ITC": "NSE_EQ|INE154A01025",
    "LT": "NSE_EQ|INE018A01030",
    "SBIN": "NSE_EQ|INE062A01020",
    "BHARTIARTL": "NSE_EQ|INE397D01024",
    "AXISBANK": "NSE_EQ|INE238A01034"
}

ALL_SYMBOLS_LIST = list(INDICES.values()) + list(WATCHLIST.values())

# ── Technical Indicator Helpers ───────────────────────────────────────────────
def ema(values, period):
    if len(values) < period:
        return []
    out = [sum(values[:period]) / period]
    k = 2 / (period + 1)
    for x in values[period:]:
        out.append(x * k + out[-1] * (1 - k))
    return out

def rsi_val(closes, period=14):
    if len(closes) < period + 2:
        return 50.0
    gains = [max(closes[i] - closes[i-1], 0) for i in range(1, len(closes))]
    losses = [max(closes[i-1] - closes[i], 0) for i in range(1, len(closes))]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    return 100.0 if avg_loss == 0 else 100 - (100 / (1 + avg_gain / avg_loss))

def atr_val(candles, period=14):
    if len(candles) < 2:
        return 0
    trs = [max(c[2] - c[3], abs(c[2] - candles[i-1][4]), abs(c[3] - candles[i-1][4]))
           for i, c in enumerate(candles) if i > 0]
    return sum(trs[-period:]) / min(period, len(trs)) if trs else 0

def supertrend(candles, period=10, multiplier=3):
    if len(candles) < period + 2:
        return None, 0
    atr = atr_val(candles, period)
    if atr == 0:
        return None, 0
    hl2 = (candles[-1][2] + candles[-1][3]) / 2
    lower_band = hl2 - multiplier * atr
    direction = 1 if candles[-1][4] > lower_band else -1
    return lower_band if direction == 1 else hl2 + multiplier * atr, direction

# ── Fetching Engine ──────────────────────────────────────────────────────────
async def safe_get(session, url, params=None):
    try:
        async with session.get(url, headers=HEADERS, params=params, timeout=10) as r:
            if r.status == 200:
                return await r.json()
            else:
                return {"error": f"HTTP {r.status}", "text": await r.text()}
    except Exception as e:
        return {"error": str(e)}

async def fetch_expiries(session, key):
    url = "https://api.upstox.com/v2/option/contract"
    res = await safe_get(session, url, {"instrument_key": key})
    if isinstance(res, dict) and res.get("status") == "success":
        raw = res.get("data", [])
        if raw and isinstance(raw[0], str):
            return sorted(raw)
        elif raw and isinstance(raw[0], dict):
            return sorted([x.get("expiry", "") for x in raw if x.get("expiry")])
    return []

async def fetch_pcr(session, key, expiry, today_str):
    url = "https://api.upstox.com/v2/market/pcr"
    res = await safe_get(session, url, {
        "instrument_key": key,
        "expiry": expiry,
        "date": today_str,
        "bucket_interval": 60
    })
    if isinstance(res, dict) and res.get("status") == "success":
        return res.get("data", {})
    return None

async def fetch_max_pain(session, key, expiry, today_str):
    url = "https://api.upstox.com/v2/market/max-pain"
    res = await safe_get(session, url, {
        "instrument_key": key,
        "expiry": expiry,
        "date": today_str,
        "bucket_interval": 60
    })
    if isinstance(res, dict) and res.get("status") == "success":
        return res.get("data", {})
    return None

async def fetch_fii_dii(session):
    url_fii = "https://api.upstox.com/v2/market/fii"
    url_dii = "https://api.upstox.com/v2/market/dii"
    params = {"data_type": "NSE_EQ|CASH", "interval": "1D"}
    fii, dii = await asyncio.gather(
        safe_get(session, url_fii, params),
        safe_get(session, url_dii, params)
    )
    
    fii_data = fii.get("data", {}).get("NSE_EQ|CASH", []) if isinstance(fii, dict) else []
    dii_data = dii.get("data", {}).get("NSE_EQ|CASH", []) if isinstance(dii, dict) else []
    return fii_data, dii_data

async def fetch_candles(session, key):
    today = datetime.date.today()
    f = (today - datetime.timedelta(days=90)).strftime("%Y-%m-%d")
    t = today.strftime("%Y-%m-%d")
    url = f"https://api.upstox.com/v2/historical-candle/{key}/day/{t}/{f}"
    res = await safe_get(session, url)
    if isinstance(res, dict) and res.get("status") == "success":
        raw = res.get("data", {}).get("candles", [])
        # Upstox returns descending order, reverse to chronological ascending for indicators
        candles = [[c[0], float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5]) if len(c)>5 else 0] for c in raw]
        return candles[::-1]
    return []

# ── Render Helpers ────────────────────────────────────────────────────────────
def make_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body")
    )
    layout["body"].split_row(
        Layout(name="technicals", ratio=4),
        Layout(name="movers", ratio=5),
        Layout(name="sentiment", ratio=4)
    )
    return layout

def render_header(refresh_in: int, status_msg: str) -> Panel:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_styled = "[bold green]ONLINE[/]" if "error" not in status_msg.lower() else f"[bold red]ERROR: {status_msg}[/]"
    return Panel(
        Align.center(f"[bold cyan]AlphaEdge Live Diagnostics 2.0[/] | Time: [white]{now}[/] | Refresh: [bold yellow]{refresh_in}s[/] | Status: {status_styled}", vertical="middle"),
        style="blue",
        box=box.ROUNDED
    )

def render_technicals(quotes, technicals) -> Panel:
    table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE, expand=True, padding=(0, 1))
    table.add_column("INDEX", justify="left")
    table.add_column("LTP", justify="right")
    table.add_column("CHG", justify="right")
    table.add_column("RANGE (H/L)", justify="center")

    for name, key in INDICES.items():
        q = quotes.get(name.upper())
        if not q:
            table.add_row(name, "---", "---", "---")
            continue
        ltp = q.get("last_price", 0)
        ohlc = q.get("ohlc", {})
        close = ohlc.get("close", 0) or 1
        chg = ((ltp - close) / close) * 100
        chg_color = "green" if chg >= 0 else "red"
        high = ohlc.get("high", 0)
        low = ohlc.get("low", 0)
        table.add_row(
            f"[bold white]{name}[/]", 
            f"{ltp:,.2f}", 
            f"[{chg_color}]{chg:+.2f}%[/{chg_color}]", 
            f"[dim]{high:,.0f} / {low:,.0f}[/]"
        )

    tech_group = [table]

    if technicals:
        tech_table = Table(show_header=False, box=box.SIMPLE, expand=True, padding=(0, 0))
        tech_table.add_column("Indicator", style="dim")
        tech_table.add_column("Value", justify="right")
        
        rsi = technicals.get("rsi", 50.0)
        rsi_color = "red" if rsi >= 70 else "green" if rsi <= 30 else "white"
        tech_table.add_row("RSI (14)", f"[{rsi_color}]{rsi:.1f}[/]")

        st_val, st_dir = technicals.get("supertrend", (None, 0))
        st_color = "green" if st_dir == 1 else "red"
        st_label = "BUY" if st_dir == 1 else "SELL"
        tech_table.add_row("SUPERTREND", f"[{st_color}]{st_label} ({st_val:,.1f})[/{st_color}]" if st_val else "---")

        trend_str = technicals.get("trend", "NEUTRAL")
        trend_color = "green" if "UPTREND" in trend_str else "red" if "DOWNTREND" in trend_str else "yellow"
        tech_table.add_row("EMA TREND", f"[{trend_color}]{trend_str}[/{trend_color}]")

        tech_group.append(Rule(style="magenta"))
        tech_group.append(tech_table)

    return Panel(Group(*tech_group), title="[bold cyan]Indices & Technicals[/]", border_style="cyan")

def render_movers(quotes) -> Panel:
    stock_data = []
    advances = 0
    declines = 0
    
    for name, key in WATCHLIST.items():
        q = quotes.get(name.upper())
        if not q:
            continue
        ltp = q.get("last_price", 0)
        ohlc = q.get("ohlc", {})
        close = ohlc.get("close", 0) or 1
        chg = ((ltp - close) / close) * 100
        vol = q.get("volume", 0)
        
        if chg >= 0:
            advances += 1
        else:
            declines += 1
            
        stock_data.append({
            "symbol": name,
            "ltp": ltp,
            "change": chg,
            "volume": vol
        })
    
    # Sort dynamically by performance change pct descending
    stock_data.sort(key=lambda x: x["change"], reverse=True)
    
    table = Table(show_header=True, header_style="bold yellow", box=box.SIMPLE, expand=True, padding=(0, 1))
    table.add_column("SYM", justify="left")
    table.add_column("LTP", justify="right")
    table.add_column("CHG", justify="right")
    table.add_column("VOL", justify="right", style="dim")
    
    for row in stock_data:
        chg_color = "green" if row["change"] >= 0 else "red"
        vol_fmt = f"{row['volume']/1e5:.1f}L" if row["volume"] >= 1e5 else f"{row['volume']:,}"
        table.add_row(
            row["symbol"], 
            f"{row['ltp']:,.2f}", 
            f"[{chg_color}]{row['change']:+.2f}%[/{chg_color}]", 
            vol_fmt
        )
        
    summary_text = Text(f"A/D Ratio: {advances} Advances │ {declines} Declines", style="bold yellow", justify="center")
    
    return Panel(Group(summary_text, table), title="[bold yellow]Dynamic movers & watchlist[/]", border_style="yellow")

def render_sentiment(pcr_data, max_pain_data, fii_dii_data) -> Panel:
    sentiment_items = []
    
    # Derivatives Sentiment Panel
    deriv_table = Table(show_header=False, box=box.SIMPLE, expand=True, padding=(0, 0))
    deriv_table.add_column("Metric", style="dim")
    deriv_table.add_column("Value", justify="right")
    
    if pcr_data:
        pcr = pcr_data.get("pcr", 0.0)
        pcr_color = "green" if pcr >= 1.0 else "yellow" if pcr >= 0.7 else "red"
        deriv_table.add_row("Nifty PCR (OI)", f"[{pcr_color}]{pcr:.3f}[/{pcr_color}]")
    else:
        deriv_table.add_row("Nifty PCR (OI)", "---")
        
    if max_pain_data:
        mp = max_pain_data.get("max_pain", 0.0)
        deriv_table.add_row("Nifty Max Pain", f"[magenta]{mp:,.0f}[/magenta]")
    else:
        deriv_table.add_row("Nifty Max Pain", "---")
        
    sentiment_items.append(deriv_table)
    
    # Institutional flows
    if fii_dii_data:
        fii_list, dii_list = fii_dii_data
        inst_table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE, expand=True, padding=(0, 1))
        inst_table.add_column("DATE/TIME", justify="center")
        inst_table.add_column("FII NET", justify="right")
        inst_table.add_column("DII NET", justify="right")
        
        # Display latest 4 days
        for i in range(min(4, len(fii_list), len(dii_list))):
            fii = fii_list[i]
            dii = dii_list[i]
            
            fii_net = fii["buy_amount"] - fii["sell_amount"]
            dii_net = dii["buy_amount"] - dii["sell_amount"]
            
            fii_color = "green" if fii_net >= 0 else "red"
            dii_color = "green" if dii_net >= 0 else "red"
            
            # Format timestamp
            dt = datetime.datetime.fromtimestamp(fii["time_stamp"] / 1000)
            date_str = dt.strftime("%b %d")
            
            inst_table.add_row(
                date_str,
                f"[{fii_color}]{fii_net:+.1f} Cr[/{fii_color}]",
                f"[{dii_color}]{dii_net:+.1f} Cr[/{dii_color}]"
            )
        sentiment_items.append(Rule(title="Institutional CASH Flows (Cr)", style="magenta"))
        sentiment_items.append(inst_table)
        
    return Panel(Group(*sentiment_items), title="[bold magenta]Derivatives & Institutional Sentiment[/]", border_style="magenta")

# ── Dynamic Update Logic ──────────────────────────────────────────────────────
async def update_data_loop(state):
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # 1. Fetch quotes for all symbols
                url_quotes = "https://api.upstox.com/v2/market-quote/quotes"
                quotes_res = await safe_get(session, url_quotes, {"instrument_key": ",".join(ALL_SYMBOLS_LIST)})
                if isinstance(quotes_res, dict) and quotes_res.get("status") == "success":
                    raw_data = quotes_res.get("data", {})
                    normalized = {}
                    for k, v in raw_data.items():
                        symbol_name = v.get("symbol")
                        if not symbol_name or symbol_name == "NA":
                            symbol_name = k.split(":")[-1]
                        
                        if symbol_name:
                            normalized[symbol_name.upper()] = v
                    state["quotes"] = normalized
                    state["status"] = "OK"
                else:
                    state["status"] = f"Quotes Error: {quotes_res.get('error', 'Unknown')}"
                    
                # 2. Fetch Nifty Expiry, PCR & Max Pain
                expiries = await fetch_expiries(session, INDICES["NIFTY 50"])
                if expiries:
                    nearest = expiries[0]
                    today_str = datetime.date.today().strftime("%Y-%m-%d")
                    pcr, mp = await asyncio.gather(
                        fetch_pcr(session, INDICES["NIFTY 50"], nearest, today_str),
                        fetch_max_pain(session, INDICES["NIFTY 50"], nearest, today_str)
                    )
                    if pcr:
                        state["pcr"] = pcr
                    if mp:
                        state["max_pain"] = mp
                        
                # 3. Calculate Technicals on Nifty 50 once at startup / periodically
                if not state["technicals"]:
                    candles = await fetch_candles(session, INDICES["NIFTY 50"])
                    if candles:
                        closes = [c[4] for c in candles]
                        rsi = rsi_val(closes)
                        st_val, st_dir = supertrend(candles)
                        
                        # Simple Trend (EMA 20 vs 50)
                        ema20 = ema(closes, 20)
                        ema50 = ema(closes, 50)
                        trend = "NEUTRAL"
                        if ema20 and ema50:
                            if ema20[-1] > ema50[-1]:
                                trend = "UPTREND"
                            else:
                                trend = "DOWNTREND"
                                
                        state["technicals"] = {
                            "rsi": rsi,
                            "supertrend": (st_val, st_dir),
                            "trend": trend
                        }
                        
            except Exception as e:
                state["status"] = f"Loop error: {e}"
                
            await asyncio.sleep(10)

async def update_fii_dii_loop(state):
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                fii_data, dii_data = await fetch_fii_dii(session)
                if fii_data and dii_data:
                    state["fii_dii"] = (fii_data, dii_data)
            except Exception as e:
                pass
            await asyncio.sleep(600) # Poll every 10 minutes

# ── Main Loop ─────────────────────────────────────────────────────────────────
async def run_dashboard():
    console = Console()
    layout = make_layout()
    
    state = {
        "quotes": {},
        "pcr": None,
        "max_pain": None,
        "fii_dii": None,
        "technicals": None,
        "status": "Initializing...",
        "refresh_in": 10
    }
    
    # Start tasks
    asyncio.create_task(update_data_loop(state))
    asyncio.create_task(update_fii_dii_loop(state))
    
    refresh_interval = 10
    counter = 0
    
    with Live(layout, console=console, screen=True, refresh_per_second=1) as live:
        while True:
            refresh_in = refresh_interval - (counter % refresh_interval)
            
            # Update Layout Panels
            layout["header"].update(render_header(refresh_in, state["status"]))
            layout["technicals"].update(render_technicals(state["quotes"], state["technicals"]))
            layout["movers"].update(render_movers(state["quotes"]))
            layout["sentiment"].update(render_sentiment(state["pcr"], state["max_pain"], state["fii_dii"]))
            
            await asyncio.sleep(1)
            counter += 1

if __name__ == "__main__":
    try:
        asyncio.run(run_dashboard())
    except KeyboardInterrupt:
        pass
