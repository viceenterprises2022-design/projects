#!/usr/bin/env python3
import requests
import datetime
import time
import sqlite3
import sys
import re
import os
from pathlib import Path
from rich.live import Live
from rich.text import Text

try:
    import fyers_client
except ImportError:
    fyers_client = None

# ── Config ────────────────────────────────────────────────────────────────────
UPSTOX_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJGVzY0MDYiLCJqdGkiOiI2OWVjZDE1NTU0ZTdlMzBhNmY0NTZkODYiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaXNFeHRlbmRlZCI6dHJ1ZSwiaWF0IjoxNzc3MTI3NzY1LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE4MDg2OTA0MDB9.lxl6fYYoKH1_2AItX-XN40eNsYhbAzbjnwbvyopgSUo"
UH = {"Authorization": f"Bearer {UPSTOX_TOKEN}", "Accept": "application/json"}

DB_PATH = Path(__file__).parent / "intraday_options_cli.db"

INSTRUMENTS = {
    1: {"name": "NIFTY",     "key": "NSE_INDEX|Nifty 50",   "fut_key": "NSE_FO|66071",  "exch": "NSE_FO", "step": 50},
    2: {"name": "SENSEX",    "key": "BSE_INDEX|SENSEX",     "fut_key": "BSE_FO|870220", "exch": "BSE_FO", "step": 100},
    3: {"name": "BANKNIFTY", "key": "NSE_INDEX|Nifty Bank", "fut_key": "NSE_FO|66068",  "exch": "NSE_FO", "step": 100}
}

def get_futures_key(name, exch):
    """
    Construct dynamic Futures key for the current month.
    Format: EXCH|SYMBOL<YY><MMM>FUT (e.g., NSE_FO|NIFTY26MAYFUT)
    """
    now = datetime.datetime.now()
    year_short = now.strftime("%y")
    month_upper = now.strftime("%b").upper()
    return f"{exch}|{name}{year_short}{month_upper}FUT"

# ── Helpers ───────────────────────────────────────────────────────────────────

def strip_ansi(text):
    """Remove ANSI escape sequences for length calculation."""
    return re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])').sub('', text)

def pad_colored(text, width, align='left'):
    """Pad a string containing ANSI color codes correctly."""
    visible_len = len(strip_ansi(text))
    padding = " " * max(0, width - visible_len)
    if align == 'left': return text + padding
    return padding + text

# ── Database Logic ────────────────────────────────────────────────────────────

def init_db():
    """Create table and delete data from previous days."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS options_data
                 (timestamp TEXT, index_name TEXT, spot REAL, strike REAL, 
                  ce_ltp REAL, ce_oi REAL, pe_ltp REAL, pe_oi REAL)''')
    
    # Delete data older than today
    c.execute("DELETE FROM options_data WHERE date(timestamp) < date('now', 'localtime')")
    conn.commit()
    return conn

def save_to_db(conn, timestamp, index_name, spot, data_rows):
    """Save the snapshot of option chain strikes to DB."""
    c = conn.cursor()
    for row in data_rows:
        c.execute("INSERT INTO options_data VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (timestamp, index_name, spot, row['strike'], 
                   row['ce_ltp'], row['ce_oi'], row['pe_ltp'], row['pe_oi']))
    conn.commit()

# ── Upstox Fetchers ───────────────────────────────────────────────────────────

def upstox_get(url, params):
    max_retries = 3
    backoff = 1.0
    # Spacing to prevent burst rate limit
    time.sleep(0.15)
    for attempt in range(max_retries):
        try:
            r = requests.get(url, headers=UH, params=params, timeout=12)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 429:
                print(f"    [W] Upstox 429 Rate Limit on {url.split('/')[-1]}. Retrying in {backoff}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(backoff)
                backoff *= 2
            else:
                print(f"    [W] Upstox API {r.status_code} on {url.split('/')[-1]}: {r.text[:200]}")
                break
        except Exception as e:
            print(f"    [W] Connection error on {url.split('/')[-1]}: {e}")
            time.sleep(0.5)
    return {}

def get_symbol_from_key(key):
    for inst in INSTRUMENTS.values():
        if inst["key"] == key:
            return inst["name"]
    return None

def fetch_quote(key):
    d = upstox_get("https://api.upstox.com/v2/market-quote/quotes", {"instrument_key": key})
    if d.get("status") == "success" and d.get("data"):
        q = list(d["data"].values())[0]
        return q.get("last_price", 0)
        
    # Fallback to Fyers
    sym = get_symbol_from_key(key)
    if sym and fyers_client and fyers_client.is_fyers_configured():
        ltp = fyers_client.fetch_fyers_ltp(sym)
        if ltp is not None:
            return float(ltp)
    return None

def fetch_expiries(key):
    d = upstox_get("https://api.upstox.com/v2/option/contract", {"instrument_key": key})
    if d.get("status") == "success" and d.get("data"):
        raw = d["data"]
        if raw and isinstance(raw[0], str):
            return sorted(raw)
        elif raw and isinstance(raw[0], dict):
            return sorted([x.get("expiry","") for x in raw if x.get("expiry")])
            
    # Fallback to Fyers
    sym = get_symbol_from_key(key)
    if sym and fyers_client and fyers_client.is_fyers_configured():
        fyers_exp = fyers_client.fetch_fyers_expiries(sym)
        if fyers_exp:
            return fyers_exp
    return []

def fetch_option_chain(key, expiry):
    d = upstox_get("https://api.upstox.com/v2/option/chain", {"instrument_key": key, "expiry_date": expiry})
    if d.get("status") == "success":
        return d.get("data", [])
        
    # Fallback to Fyers
    sym = get_symbol_from_key(key)
    if sym and fyers_client and fyers_client.is_fyers_configured():
        fyers_chain = fyers_client.fetch_fyers_option_chain(sym, expiry)
        if fyers_chain:
            return fyers_chain
    return []

EXPIRY_CACHE = {} # {instrument_key: (expiry_date, timestamp)}

def get_cached_expiry(key):
    """Fetch expiry once every 30 mins to avoid redundant calls."""
    now = time.time()
    if key in EXPIRY_CACHE:
        expiry, ts = EXPIRY_CACHE[key]
        if now - ts < 1800: # 30 mins
            return expiry
    expiries = fetch_expiries(key)
    if expiries:
        expiry = expiries[0]
        EXPIRY_CACHE[key] = (expiry, now)
        return expiry
    return None

def fetch_quotes(key_list):
    """Fetch multiple quotes at once."""
    if not key_list: return {}
    d = upstox_get("https://api.upstox.com/v2/market-quote/quotes", {"instrument_key": ",".join(key_list)})
    if d.get("status") == "success" and d.get("data"):
        return {v.get("instrument_token"): v for v in d["data"].values()}
    return {}

def get_ohlc_flags(ohlc):
    """Flag O=H and O=L strategies."""
    if not ohlc: return ""
    o, h, l = ohlc.get("open"), ohlc.get("high"), ohlc.get("low")
    if not o: return ""
    flags = []
    if o == h and o > 0: flags.append("OH")
    if o == l and o > 0: flags.append("OL")
    return "|".join(flags)

# ── Formatting ────────────────────────────────────────────────────────────────

def format_oi(n):
    """Format OI to Lakhs (L) or Crores (C)."""
    if n >= 10000000:
        return f"{n/10000000:5.2f}C"
    if n >= 100000:
        return f"{n/100000:5.2f}L"
    return f"{n:6.0f}"

def format_row(strike, ce_data, pe_data, is_atm=False):
    marker = ">> " if is_atm else "   "
    G, R, W = "\033[92m", "\033[91m", "\033[0m" # Green, Red, Reset
    
    def get_cols(d, is_ce):
        ohlc = d.get("ohlc") or {}
        o, h, l, c = ohlc.get("open", 0), ohlc.get("high", 0), ohlc.get("low", 0), ohlc.get("close", 0)
        ltp = d.get("ltp", 0)
        oi = format_oi(d.get("oi", 0))
        
        # Strategy Coloring
        flags = get_ohlc_flags(ohlc)
        o_s = f"{o:6.1f}"
        if "OL" in flags: o_s = f"{G}{o_s}{W}" if is_ce else f"{R}{o_s}{W}"
        if "OH" in flags: o_s = f"{R}{o_s}{W}" if is_ce else f"{G}{o_s}{W}"
        
        f_tags = []
        if "OL" in flags: f_tags.append(f"{G}OL{W}" if is_ce else f"{R}OL{W}")
        if "OH" in flags: f_tags.append(f"{R}OH{W}" if is_ce else f"{G}OH{W}")
        f_tag_str = "|".join(f_tags)
        
        return o_s, f"{h:6.1f}", f"{l:6.1f}", f"{c:6.1f}", f"{ltp:7.2f}", f"{oi:>6}", f_tag_str

    co, ch, cl, cc, cltp, coi, cf = get_cols(ce_data, True)
    po, ph, pl, pc, pltp, poi, pf = get_cols(pe_data, False)
    
    # CE Side | Strike | PE Side
    cf_col = pad_colored(cf, 5, 'left')
    pf_col = pad_colored(pf, 5, 'left')
    return f"{marker}{cf_col}|{co} {ch} {cl} {cc}|{cltp}|{coi}|{strike:6.0f}|{poi}|{pltp}|{po} {ph} {pl} {pc}|{pf_col}"

# ── Main Loop ─────────────────────────────────────────────────────────────────

def main():
    conn = init_db()

    try:
        with Live(refresh_per_second=4, screen=True) as live:
            while True:
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # 1. Batch Fetch Spot & Fut for all indices
                sf_keys = []
                for inst in INSTRUMENTS.values():
                    sf_keys.append(inst["key"])
                    sf_keys.append(inst["fut_key"])
                sf_quotes = fetch_quotes(sf_keys)

                # 2. Gather index data and collect all option keys
                all_index_data = []
                all_option_keys = []

                for _, inst in INSTRUMENTS.items():
                    name = inst["name"]
                    key = inst["key"]
                    step = inst["step"]
                    
                    spot_data = sf_quotes.get(key, {})
                    spot = spot_data.get("last_price")
                    if not spot: continue
                    fut_data = sf_quotes.get(inst["fut_key"], {})
                    fut = fut_data.get("last_price") or spot
                    
                    expiry = get_cached_expiry(key)
                    if not expiry: continue
                    
                    chain = fetch_option_chain(key, expiry)
                    if not chain: continue

                    display_step = 100 if name == "NIFTY" else step
                    atm_strike = round(spot / display_step) * display_step
                    target_strikes = [atm_strike + (offset * (display_step // step) * step) for offset in [-3, -2, -1, 0, 1, 2, 3]]
                    if name == "NIFTY":
                        target_strikes = [s for s in target_strikes if s % 100 == 0]
                        if len(target_strikes) < 7: target_strikes = [atm_strike + (i * 100) for i in range(-3, 4)]

                    chain_lookup = {row.get("strike_price"): row for row in chain if isinstance(row, dict)}
                    for strike in target_strikes:
                        row = chain_lookup.get(strike, {})
                        ckey = (row.get("call_options") or {}).get("instrument_key")
                        pkey = (row.get("put_options") or {}).get("instrument_key")
                        if ckey: all_option_keys.append(ckey)
                        if pkey: all_option_keys.append(pkey)

                    all_index_data.append({
                        "inst": inst, "spot": spot, "fut": fut, "expiry": expiry,
                        "target_strikes": target_strikes, "chain_lookup": chain_lookup,
                        "atm_strike": atm_strike,
                        "spot_ohlc": spot_data.get("ohlc") or {},
                        "fut_ohlc": fut_data.get("ohlc") or {}
                    })

                # 3. Batch Fetch OHLC for ALL options
                option_quotes = fetch_quotes(all_option_keys)

                # 4. Build display
                lines = []
                lines.append("=" * 107)
                lines.append(f" LIVE MULTI-INDEX OPTIONS DASHBOARD | {ts}")
                lines.append("=" * 107)

                for idx in all_index_data:
                    name, spot, fut, expiry = idx["inst"]["name"], idx["spot"], idx["fut"], idx["expiry"]
                    so = idx.get("spot_ohlc", {})
                    fo = idx.get("fut_ohlc", {})
                    so_str = f"O:{so.get('open',0):.2f} H:{so.get('high',0):.2f} L:{so.get('low',0):.2f} C:{so.get('close',0):.2f}"
                    fo_str = f"O:{fo.get('open',0):.2f} H:{fo.get('high',0):.2f} L:{fo.get('low',0):.2f} C:{fo.get('close',0):.2f}"
                    lines.append(f"\n>>> {name} | SPOT: {spot:8.2f} {so_str} | FUT: {fut:8.2f} {fo_str} | Exp: {expiry}")
                    lines.append("-" * 107)
                    lines.append("   FLAGS|  OPEN  HIGH   LOW CLOSE| CE LTP| CE OI|STRIKE| PE OI| PE LTP|  OPEN  HIGH   LOW CLOSE|FLAGS")
                    lines.append("-" * 107)

                    snapshot_rows = []
                    for strike in idx["target_strikes"]:
                        row = idx["chain_lookup"].get(strike, {})
                        c_opt, p_opt = row.get("call_options") or {}, row.get("put_options") or {}
                        c_full, p_full = option_quotes.get(c_opt.get("instrument_key"), {}), option_quotes.get(p_opt.get("instrument_key"), {})
                        
                        ce_data = {"ltp": c_full.get("last_price") or (c_opt.get("market_data") or {}).get("ltp", 0),
                                   "oi":  (c_opt.get("market_data") or {}).get("oi", 0), "ohlc": c_full.get("ohlc")}
                        pe_data = {"ltp": p_full.get("last_price") or (p_opt.get("market_data") or {}).get("ltp", 0),
                                   "oi":  (p_opt.get("market_data") or {}).get("oi", 0), "ohlc": p_full.get("ohlc")}

                        snapshot_rows.append({"strike": strike, "ce_ltp": ce_data['ltp'], "ce_oi": ce_data['oi'], "pe_ltp": pe_data['ltp'], "pe_oi": pe_data['oi']})
                        lines.append(format_row(strike, ce_data, pe_data, strike == idx["atm_strike"]))

                    save_to_db(conn, ts, name, spot, snapshot_rows)

                lines.append("")
                lines.append("=" * 107)
                lines.append("Polling every 5s (Batch Mode). Press Ctrl+C to exit.")
                live.update(Text.from_ansi("\n".join(lines)))
                time.sleep(5)

    except KeyboardInterrupt:
        print("\nExiting. Closing database connection...")
        conn.close()
        sys.exit(0)

if __name__ == "__main__":
    main()
