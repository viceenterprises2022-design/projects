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
    "NIFTY BANK": "NSE_INDEX|Nifty Bank"
}

# ── Helper for HTTP Fetching ──────────────────────────────────────────────────
async def safe_get(session, url, params=None):
    try:
        async with session.get(url, headers=HEADERS, params=params, timeout=10) as r:
            if r.status == 200:
                return await r.json()
            else:
                return {"error": f"HTTP {r.status}", "text": await r.text()}
    except Exception as e:
        return {"error": str(e)}

# ── Upstox Option Chain Fetchers ──────────────────────────────────────────────
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

async def fetch_option_chain(session, key, expiry):
    url = "https://api.upstox.com/v2/option/chain"
    res = await safe_get(session, url, {
        "instrument_key": key,
        "expiry_date": expiry
    })
    if isinstance(res, dict) and res.get("status") == "success":
        return res.get("data", [])
    return []

# ── Build-Up Logic ────────────────────────────────────────────────────────────
def calculate_buildup(chg_pct, oi_chg_pct):
    """
    Classify the position building category:
    LBU: Price Up + OI Up (Bullish Continuation)
    SBU: Price Down + OI Up (Bearish Continuation)
    LUW: Price Down + OI Down (Bullish Exhaustion / Profit Booking)
    SCV: Price Up + OI Down (Short Covering Squeeze)
    """
    if chg_pct >= 0 and oi_chg_pct >= 0:
        return "LBU", "bold green", "Long Buildup"
    elif chg_pct < 0 and oi_chg_pct >= 0:
        return "SBU", "bold red", "Short Buildup"
    elif chg_pct < 0 and oi_chg_pct < 0:
        return "LUW", "dim yellow", "Long Unwinding"
    else:
        return "SCV", "bold cyan", "Short Covering"

# ── Layout Construction ───────────────────────────────────────────────────────
def make_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=4),
        Layout(name="body", ratio=1),
        Layout(name="footer", size=8)
    )
    layout["body"].split_row(
        Layout(name="calls_panel", ratio=1),
        Layout(name="strikes_panel", size=14),
        Layout(name="puts_panel", ratio=1)
    )
    layout["footer"].split_row(
        Layout(name="walls_panel", ratio=1),
        Layout(name="alerts_panel", ratio=1)
    )
    return layout

# ── Render Component Functions ────────────────────────────────────────────────
def render_header(state) -> Panel:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    active_idx = state["active_idx"]
    status_msg = state["status"]
    
    status_styled = "[bold green]ONLINE[/]" if "error" not in status_msg.lower() else f"[bold red]ERROR: {status_msg}[/]"
    
    # Render mini-banners for both indices
    banners = []
    for idx_name, idx_key in INDICES.items():
        spot = state["spots"].get(idx_name, 0.0)
        chg = state["spots_chg"].get(idx_name, 0.0)
        chg_color = "green" if chg >= 0 else "red"
        
        border_style = "bold yellow" if idx_name == active_idx else "dim white"
        active_indicator = "●" if idx_name == active_idx else "○"
        
        banners.append(f"[{border_style}]{active_indicator} {idx_name}: {spot:,.2f} ({chg:+.2f}%)[/{border_style}]")
        
    banners_str = "  │  ".join(banners)
    expiry_info = f"Expiry: [bold magenta]{state['current_expiry']}[/]" if state['current_expiry'] else "Expiry: ---"
    
    header_text = Text.from_markup(
        f"[bold cyan]AlphaEdge F&O Breakout Scanner 2.0[/]  │  {banners_str}  │  {expiry_info}\n"
        f"Time: {now}  │  Auto-Switching index in {state['switch_in']}s  │  Status: {status_styled}"
    )
    
    return Panel(
        Align.center(header_text, vertical="middle"),
        style="cyan",
        box=box.ROUNDED
    )

def render_chains(state, side):
    """
    Renders either CALLS or PUTS table.
    """
    table = Table(show_header=True, header_style="bold cyan" if side == "CALLS" else "bold pink", box=box.SIMPLE, expand=True, padding=(0, 1))
    
    if side == "CALLS":
        table.add_column("BUILDUP", justify="center")
        table.add_column("DELTA", justify="right", style="dim")
        table.add_column("IV", justify="right", style="dim")
        table.add_column("VOL/OI", justify="right", style="dim")
        table.add_column("OI CHG", justify="right")
        table.add_column("OI (L)", justify="right")
        table.add_column("LTP", justify="right")
    else:
        table.add_column("LTP", justify="left")
        table.add_column("OI (L)", justify="left")
        table.add_column("OI CHG", justify="left")
        table.add_column("VOL/OI", justify="left", style="dim")
        table.add_column("IV", justify="left", style="dim")
        table.add_column("DELTA", justify="left", style="dim")
        table.add_column("BUILDUP", justify="center")

    rows = state["visible_rows"]
    if not rows:
        return Panel(Align.center("[dim]No option chain data available[/]", vertical="middle"), border_style="cyan" if side == "CALLS" else "pink")

    for r in rows:
        strike = r["strike"]
        opt = r["call"] if side == "CALLS" else r["put"]
        
        if not opt:
            if side == "CALLS":
                table.add_row("---", "---", "---", "---", "---", "---", "---")
            else:
                table.add_row("---", "---", "---", "---", "---", "---", "---")
            continue
            
        mdata = opt.get("market_data", {})
        greeks = opt.get("option_greeks", {})
        
        ltp = mdata.get("ltp", 0.0)
        close = mdata.get("close_price", 0.0) or ltp or 1.0
        chg_pct = ((ltp - close) / close) * 100
        
        oi = mdata.get("oi", 0.0)
        prev_oi = mdata.get("prev_oi", 0.0) or oi or 1.0
        oi_chg_pct = ((oi - prev_oi) / prev_oi) * 100
        
        vol = mdata.get("volume", 0.0)
        vol_oi_ratio = vol / oi if oi > 0 else 0.0
        
        # IV scaling
        iv = greeks.get("iv", 0.0)
        if iv < 1.0:
            iv *= 100
            
        delta = greeks.get("delta", 0.0)
        
        b_code, b_color, b_name = calculate_buildup(chg_pct, oi_chg_pct)
        
        # Formatted cells
        b_cell = f"[{b_color}]{b_code}[/{b_color}]"
        chg_color = "green" if chg_pct >= 0 else "red"
        ltp_cell = f"[bold {chg_color}]{ltp:,.1f}[/] [dim]({chg_pct:+.1f}%)[/]"
        oi_cell = f"{oi/1e5:.1f}L"
        
        oi_chg_color = "green" if oi_chg_pct >= 0 else "red"
        oi_chg_cell = f"[{oi_chg_color}]{oi_chg_pct:+.1f}%[/{oi_chg_color}]"
        
        # Highlight extreme Volume-to-OI speculation spurt
        vol_oi_color = "yellow" if vol_oi_ratio > 10 else "dim white"
        vol_oi_cell = f"[{vol_oi_color}]{vol_oi_ratio:.1f}x[/{vol_oi_color}]"
        
        iv_cell = f"{iv:.1f}%"
        delta_cell = f"{delta:+.2f}"
        
        if side == "CALLS":
            table.add_row(b_cell, delta_cell, iv_cell, vol_oi_cell, oi_chg_cell, oi_cell, ltp_cell)
        else:
            table.add_row(ltp_cell, oi_cell, oi_chg_cell, vol_oi_cell, iv_cell, delta_cell, b_cell)
            
    title = "[bold cyan]CALL OPTIONS (CE)[/]" if side == "CALLS" else "[bold pink]PUT OPTIONS (PE)[/]"
    return Panel(table, title=title, border_style="cyan" if side == "CALLS" else "pink")

def render_strikes(state):
    """
    Renders the middle strike column table.
    """
    table = Table(show_header=True, header_style="bold yellow", box=box.SIMPLE, expand=True, padding=(0, 1))
    table.add_column("STRIKE", justify="center")
    
    rows = state["visible_rows"]
    if not rows:
        return Panel(Align.center("---", vertical="middle"), border_style="yellow")
        
    spot = state["spots"].get(state["active_idx"], 0.0)
    
    for r in rows:
        strike = r["strike"]
        # Highlight strike close to Spot
        if abs(strike - spot) <= (50 if "BANK" not in state["active_idx"] else 100) / 2:
            table.add_row(f"[bold reverse yellow] {strike:,.0f} [/]")
        else:
            table.add_row(f"[bold white]{strike:,.0f}[/]")
            
    return Panel(table, title="[bold yellow]STRIKE[/]", border_style="yellow")

def render_walls(state) -> Panel:
    """
    Display Major OI Walls (Support & Resistance).
    """
    walls_text = []
    
    # 1. Resistance Wall (Call Options)
    r_strike = state["walls"].get("resistance_strike")
    r_oi = state["walls"].get("resistance_oi", 0)
    if r_strike:
        spot = state["spots"].get(state["active_idx"], 0.0)
        dist_pct = ((r_strike - spot) / spot) * 100 if spot > 0 else 0
        dist_color = "red" if abs(dist_pct) < 0.25 else "yellow"
        
        # Check for breach or squeeze
        squeeze_status = ""
        r_oi_chg = state["walls"].get("resistance_oi_chg", 0)
        if abs(dist_pct) <= 0.25:
            if r_oi_chg < 0:
                squeeze_status = " ⚡ [blink bold red]CALL SQUEEZE TRIGGERED[/]"
            else:
                squeeze_status = " ⚠️ [bold yellow]PROXIMITY WARNING[/]"
                
        walls_text.append(
            f"[bold red]MAJOR RESISTANCE WALL (Highest Call OI)[/]\n"
            f"Strike: [bold white]{r_strike:,.0f}[/] │ OI: [bold white]{r_oi/1e5:.1f}L contracts[/] │ "
            f"Distance: [{dist_color}]{dist_pct:+.2f}%[/{dist_color}]{squeeze_status}"
        )
    else:
        walls_text.append("[bold red]MAJOR RESISTANCE WALL[/]: [dim]Scanning...[/]")
        
    walls_text.append(Rule(style="dim white"))
    
    # 2. Support Wall (Put Options)
    s_strike = state["walls"].get("support_strike")
    s_oi = state["walls"].get("support_oi", 0)
    if s_strike:
        spot = state["spots"].get(state["active_idx"], 0.0)
        dist_pct = ((s_strike - spot) / spot) * 100 if spot > 0 else 0
        dist_color = "green" if abs(dist_pct) < 0.25 else "yellow"
        
        squeeze_status = ""
        s_oi_chg = state["walls"].get("support_oi_chg", 0)
        if abs(dist_pct) <= 0.25:
            if s_oi_chg < 0:
                squeeze_status = " ⚡ [blink bold green]PUT SQUEEZE TRIGGERED[/]"
            else:
                squeeze_status = " ⚠️ [bold yellow]PROXIMITY WARNING[/]"
                
        walls_text.append(
            f"[bold green]MAJOR SUPPORT WALL (Highest Put OI)[/]\n"
            f"Strike: [bold white]{s_strike:,.0f}[/] │ OI: [bold white]{s_oi/1e5:.1f}L contracts[/] │ "
            f"Distance: [{dist_color}]{dist_pct:+.2f}%[/{dist_color}]{squeeze_status}"
        )
    else:
        walls_text.append("[bold green]MAJOR SUPPORT WALL[/]: [dim]Scanning...[/]")
        
    return Panel(Group(*walls_text), title="[bold yellow]OI Concentration Walls & Breaches[/]", border_style="yellow")

def render_alerts(state) -> Panel:
    """
    Renders greeks and speculative volume spurt alerts.
    """
    alerts = []
    
    # 1. Volume Spurt Alerts (Ratio > 10)
    spurts = state["alerts"].get("volume_spurts", [])
    if spurts:
        spurt_rows = []
        for s in spurts[:2]:
            chg_color = "green" if s["chg"] >= 0 else "red"
            spurt_rows.append(
                f"[bold yellow]Spurt alert[/]: [bold white]{s['strike']} {s['type']}[/] "
                f"LTP: [{chg_color}]{s['ltp']:.1f}[/] │ Vol/OI: [bold magenta]{s['vol_oi']:.1f}x[/]"
            )
        alerts.append("\n".join(spurt_rows))
    else:
        alerts.append("[dim]No abnormal speculative volume spurts detected.[/]")
        
    alerts.append(Rule(style="dim white"))
    
    # 2. IV Compression & Squeezes
    iv_compression = state["alerts"].get("iv_squeeze", "")
    if iv_compression:
        alerts.append(f"[bold cyan]ATM IV Alert[/]: {iv_compression}")
    else:
        alerts.append("[dim]ATM Implied Volatility normal.[/]")
        
    return Panel(Group(*alerts), title="[bold magenta]Greeks & Speculation Spurt Alerts[/]", border_style="magenta")

# ── Dynamic Calculation Engine ────────────────────────────────────────────────
def process_option_chain(chain_data, spot):
    """
    Analyzes raw option chain data to locate ATM strike, filter rows, find walls,
    and detect volume/IV alerts.
    """
    if not chain_data:
        return {
            "visible_rows": [],
            "walls": {},
            "alerts": {"volume_spurts": [], "iv_squeeze": ""}
        }
        
    # 1. Find ATM Strike
    chain_data.sort(key=lambda x: x.get("strike_price", 0))
    closest_strike_row = min(chain_data, key=lambda x: abs(x.get("strike_price", 0) - spot))
    atm_strike = closest_strike_row.get("strike_price", spot)
    
    # Find index of ATM strike
    atm_idx = 0
    for idx, row in enumerate(chain_data):
        if row.get("strike_price") == atm_strike:
            atm_idx = idx
            break
            
    # Filter ATM +- 5 strikes
    start_idx = max(0, atm_idx - 5)
    end_idx = min(len(chain_data), atm_idx + 6)
    visible_strikes_data = chain_data[start_idx:end_idx]
    
    # Map visible strikes to rows structure
    visible_rows = []
    for s_data in visible_strikes_data:
        visible_rows.append({
            "strike": s_data.get("strike_price"),
            "call": s_data.get("call_options"),
            "put": s_data.get("put_options")
        })
        
    # 2. Find Major OI Walls across the entire chain
    res_strike = None
    res_oi = 0
    res_oi_chg = 0
    
    sup_strike = None
    sup_oi = 0
    sup_oi_chg = 0
    
    all_volume_spurts = []
    
    for row in chain_data:
        strike = row.get("strike_price", 0.0)
        
        # CALL Options analysis
        ce = row.get("call_options")
        if ce:
            mdata = ce.get("market_data", {})
            oi = mdata.get("oi", 0.0)
            if oi > res_oi:
                res_oi = oi
                res_strike = strike
                
                prev_oi = mdata.get("prev_oi", 0.0)
                res_oi_chg = ((oi - prev_oi) / prev_oi * 100) if prev_oi > 0 else 0.0
                
            vol = mdata.get("volume", 0.0)
            vol_oi = vol / oi if oi > 0 else 0.0
            if vol_oi > 10.0:
                ltp = mdata.get("ltp", 0.0)
                close = mdata.get("close_price", 0.0) or ltp or 1.0
                chg = ((ltp - close) / close) * 100
                all_volume_spurts.append({
                    "strike": strike,
                    "type": "CE",
                    "vol_oi": vol_oi,
                    "ltp": ltp,
                    "chg": chg
                })
                
        # PUT Options analysis
        pe = row.get("put_options")
        if pe:
            mdata = pe.get("market_data", {})
            oi = mdata.get("oi", 0.0)
            if oi > sup_oi:
                sup_oi = oi
                sup_strike = strike
                
                prev_oi = mdata.get("prev_oi", 0.0)
                sup_oi_chg = ((oi - prev_oi) / prev_oi * 100) if prev_oi > 0 else 0.0
                
            vol = mdata.get("volume", 0.0)
            vol_oi = vol / oi if oi > 0 else 0.0
            if vol_oi > 10.0:
                ltp = mdata.get("ltp", 0.0)
                close = mdata.get("close_price", 0.0) or ltp or 1.0
                chg = ((ltp - close) / close) * 100
                all_volume_spurts.append({
                    "strike": strike,
                    "type": "PE",
                    "vol_oi": vol_oi,
                    "ltp": ltp,
                    "chg": chg
                })
                
    walls = {
        "resistance_strike": res_strike,
        "resistance_oi": res_oi,
        "resistance_oi_chg": res_oi_chg,
        "support_strike": sup_strike,
        "support_oi": sup_oi,
        "support_oi_chg": sup_oi_chg
    }
    
    # Sort volume spurts
    all_volume_spurts.sort(key=lambda x: x["vol_oi"], reverse=True)
    
    # Compute ATM IV details
    iv_squeeze = ""
    atm_ce = closest_strike_row.get("call_options", {})
    atm_pe = closest_strike_row.get("put_options", {})
    ce_iv = atm_ce.get("option_greeks", {}).get("iv", 0.0)
    pe_iv = atm_pe.get("option_greeks", {}).get("iv", 0.0)
    
    if ce_iv < 1.0: ce_iv *= 100
    if pe_iv < 1.0: pe_iv *= 100
    
    if ce_iv > 0 and pe_iv > 0:
        iv_squeeze = f"ATM CE IV: [bold white]{ce_iv:.1f}%[/] │ PE IV: [bold white]{pe_iv:.1f}%[/]"
        if ce_iv < 11.0 and pe_iv < 11.0:
            iv_squeeze += " ⚡ [blink bold yellow]CRITICAL IV SQUEEZE DETECTED[/]"
            
    return {
        "visible_rows": visible_rows,
        "walls": walls,
        "alerts": {
            "volume_spurts": all_volume_spurts,
            "iv_squeeze": iv_squeeze
        }
    }

# ── One-shot pre-fetch (runs before Live starts) ─────────────────────────────
async def prefetch_state(state):
    """Fetch one full tick of data before Live starts so frame 1 is never blank."""
    async with aiohttp.ClientSession() as session:
        try:
            url_quotes = "https://api.upstox.com/v2/market-quote/quotes"
            quotes_res = await safe_get(session, url_quotes, {"instrument_key": ",".join(INDICES.values())})
            if isinstance(quotes_res, dict) and quotes_res.get("status") == "success":
                raw_data = quotes_res.get("data", {})
                for idx_name, idx_key in INDICES.items():
                    api_key = idx_key.replace('|', ':')
                    q = raw_data.get(api_key, {})
                    spot = q.get("last_price", 0.0)
                    ohlc = q.get("ohlc", {})
                    close = ohlc.get("close", 0.0) or spot or 1.0
                    chg = ((spot - close) / close) * 100
                    state["spots"][idx_name] = spot
                    state["spots_chg"][idx_name] = chg
                state["status"] = "OK"
            else:
                state["status"] = f"Prefetch Spot Error: {quotes_res.get('error', str(quotes_res))}"
                return

            active_idx = state["active_idx"]
            active_key = INDICES[active_idx]
            expiries = await fetch_expiries(session, active_key)
            if expiries:
                state["current_expiry"] = expiries[0]
                chain_raw = await fetch_option_chain(session, active_key, expiries[0])
                spot = state["spots"].get(active_idx, 0.0)
                if chain_raw and spot > 0:
                    processed = process_option_chain(chain_raw, spot)
                    state["visible_rows"] = processed["visible_rows"]
                    state["walls"] = processed["walls"]
                    state["alerts"] = processed["alerts"]
                else:
                    state["status"] = f"Prefetch: chain empty or spot=0 (spot={spot}, chain_len={len(chain_raw)})"
            else:
                state["status"] = f"Prefetch: No expiries returned for {active_idx}"
        except Exception as e:
            state["status"] = f"Prefetch error: {e}"

# ── Dynamic Async Loops ───────────────────────────────────────────────────────
async def update_data_loop(state):
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # 1. Fetch spot prices for indices
                url_quotes = "https://api.upstox.com/v2/market-quote/quotes"
                quotes_res = await safe_get(session, url_quotes, {"instrument_key": ",".join(INDICES.values())})
                if isinstance(quotes_res, dict) and quotes_res.get("status") == "success":
                    raw_data = quotes_res.get("data", {})
                    for idx_name, idx_key in INDICES.items():
                        api_key = idx_key.replace('|', ':')
                        q = raw_data.get(api_key, {})
                        spot = q.get("last_price", 0.0)
                        ohlc = q.get("ohlc", {})
                        close = ohlc.get("close", 0.0) or spot or 1.0
                        chg = ((spot - close) / close) * 100
                        state["spots"][idx_name] = spot
                        state["spots_chg"][idx_name] = chg
                    state["status"] = "OK"
                else:
                    state["status"] = f"Spot Fetch Error: {quotes_res.get('error', str(quotes_res))}"

                # 2. Fetch Option Expiries & Chain for active index
                active_idx = state["active_idx"]
                active_key = INDICES[active_idx]

                expiries = await fetch_expiries(session, active_key)
                if expiries:
                    state["current_expiry"] = expiries[0]
                    chain_raw = await fetch_option_chain(session, active_key, expiries[0])
                    spot = state["spots"].get(active_idx, 0.0)
                    if chain_raw and spot > 0:
                        processed = process_option_chain(chain_raw, spot)
                        state["visible_rows"] = processed["visible_rows"]
                        state["walls"] = processed["walls"]
                        state["alerts"] = processed["alerts"]

            except Exception as e:
                state["status"] = f"Update loop error: {e}"

            await asyncio.sleep(5)  # Poll option chain every 5 seconds

# ── Index Switcher Loop ───────────────────────────────────────────────────────
async def index_switcher_loop(state):
    while True:
        state["switch_in"] = 15
        while state["switch_in"] > 0:
            await asyncio.sleep(1)
            state["switch_in"] -= 1
            
        # Switch index
        keys = list(INDICES.keys())
        curr_idx = keys.index(state["active_idx"])
        next_idx = keys[(curr_idx + 1) % len(keys)]
        state["active_idx"] = next_idx
        state["visible_rows"] = []
        state["walls"] = {}
        state["alerts"] = {"volume_spurts": [], "iv_squeeze": ""}

# ── Main Run Dashboard ────────────────────────────────────────────────────────
async def run_scanner():
    console = Console()
    layout = make_layout()

    state = {
        "spots": {"NIFTY 50": 0.0, "NIFTY BANK": 0.0},
        "spots_chg": {"NIFTY 50": 0.0, "NIFTY BANK": 0.0},
        "active_idx": "NIFTY 50",
        "current_expiry": None,
        "visible_rows": [],
        "walls": {},
        "alerts": {"volume_spurts": [], "iv_squeeze": ""},
        "status": "Initializing...",
        "switch_in": 15
    }

    # ── PRE-FETCH: Warm state before Live starts so frame 1 is never blank ──
    console.print("[bold cyan]AlphaEdge F&O Scanner[/] — Fetching initial data...", highlight=False)
    await prefetch_state(state)
    console.print(f"[dim]Pre-fetch complete. Status: {state['status']} | Spot NIFTY 50: {state['spots'].get('NIFTY 50', 0):.2f} | Rows: {len(state['visible_rows'])}[/]")

    # ── Start background polling tasks ──
    asyncio.create_task(update_data_loop(state))
    asyncio.create_task(index_switcher_loop(state))

    # screen=False: avoids alternate-buffer issues in some terminals;
    # auto_refresh=False: we control refresh timing ourselves via asyncio.sleep.
    with Live(layout, console=console, screen=False, auto_refresh=False, transient=False) as live:
        while True:
            # Render all panels into the layout
            layout["header"].update(render_header(state))
            layout["calls_panel"].update(render_chains(state, "CALLS"))
            layout["strikes_panel"].update(render_strikes(state))
            layout["puts_panel"].update(render_chains(state, "PUTS"))
            layout["walls_panel"].update(render_walls(state))
            layout["alerts_panel"].update(render_alerts(state))

            live.refresh()  # Explicit refresh after each update cycle
            await asyncio.sleep(0.5)

if __name__ == "__main__":
    try:
        asyncio.run(run_scanner())
    except KeyboardInterrupt:
        pass
