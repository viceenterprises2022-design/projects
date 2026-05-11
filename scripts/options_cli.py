#!/usr/bin/env python3
import requests
import datetime
import time
import sqlite3
import os
import sys
from pathlib import Path

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

# ── Database Logic ────────────────────────────────────────────────────────────

def init_db():
    """Create table and delete data from previous days."""
    conn = sqlite3.connect(DB_PATH)
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
    try:
        r = requests.get(url, headers=UH, params=params, timeout=12)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}

def fetch_quote(key):
    d = upstox_get("https://api.upstox.com/v2/market-quote/quotes", {"instrument_key": key})
    if d.get("status") == "success" and d.get("data"):
        q = list(d["data"].values())[0]
        return q.get("last_price", 0)
    return None

def fetch_expiries(key):
    d = upstox_get("https://api.upstox.com/v2/option/contract", {"instrument_key": key})
    if d.get("status") == "success" and d.get("data"):
        raw = d["data"]
        if raw and isinstance(raw[0], str):
            return sorted(raw)
        elif raw and isinstance(raw[0], dict):
            return sorted([x.get("expiry","") for x in raw if x.get("expiry")])
    return []

def fetch_option_chain(key, expiry):
    d = upstox_get("https://api.upstox.com/v2/option/chain", {"instrument_key": key, "expiry_date": expiry})
    if d.get("status") == "success":
        return d.get("data", [])
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
        return f"{n/10000000:6.2f}C"
    if n >= 100000:
        return f"{n/100000:6.2f}L"
    return f"{n:7.0f}"

def print_row(strike, ce_data, pe_data, is_atm=False):
    marker = ">> " if is_atm else "   "
    
    def fmt_ohlc(d):
        ohlc = d.get("ohlc") or {}
        o, h, l = ohlc.get("open", 0), ohlc.get("high", 0), ohlc.get("low", 0)
        flags = get_ohlc_flags(ohlc)
        f_str = f" [{flags}]" if flags else ""
        return f"{o:g}/{h:g}/{l:g}{f_str}"

    c_ohlc = fmt_ohlc(ce_data)
    p_ohlc = fmt_ohlc(pe_data)
    c_oi = format_oi(ce_data.get("oi", 0))
    p_oi = format_oi(pe_data.get("oi", 0))
    
    print(f"{marker}{c_ohlc:>20} | {ce_data.get('ltp',0):10.2f} | {c_oi:>9} | {strike:8} | {p_oi:>9} | {pe_data.get('ltp',0):10.2f} | {p_ohlc:<20}")

# ── Main Loop ─────────────────────────────────────────────────────────────────

def main():
    conn = init_db()

    try:
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print("=" * 110)
            print(f" LIVE MULTI-INDEX OPTIONS DASHBOARD | {ts}")
            print("=" * 110)

            for _, inst in INSTRUMENTS.items():
                name = inst["name"]
                key = inst["key"]
                step = inst["step"]
                exch = inst["exch"]

                # 1. Fetch Spot & Future
                spot = fetch_quote(key)
                if not spot:
                    print(f"\n[{name}] Error: Could not fetch spot price.")
                    continue
                
                fut = fetch_quote(inst["fut_key"]) or spot # Fallback to spot
                
                # 2. Determine Strikes
                # NIFTY Specific: Force 100-point round strikes only
                display_step = 100 if name == "NIFTY" else step
                atm_strike = round(spot / display_step) * display_step
                target_strikes = [atm_strike + (offset * (display_step // step) * step) for offset in [-3, -2, -1, 0, 1, 2, 3]]
                
                # Double-check: If NIFTY, filter out any non-round strikes just in case
                if name == "NIFTY":
                    target_strikes = [s for s in target_strikes if s % 100 == 0]
                    # Ensure we still have 7 rows if possible, or at least the round ones
                    if len(target_strikes) < 7:
                        target_strikes = [atm_strike + (i * 100) for i in range(-3, 4)]

                # 3. Fetch Expiry & Chain
                expiries = fetch_expiries(key)
                if not expiries:
                    print(f"[{name}] Error: No expiries found.")
                    continue
                
                nearest_expiry = expiries[0]
                chain = fetch_option_chain(key, nearest_expiry)
                if not chain:
                    print(f"[{name}] Error: Empty option chain.")
                    continue

                # 4. Batch Fetch OHLC for target strikes
                chain_lookup = {row.get("strike_price"): row for row in chain if isinstance(row, dict)}
                option_keys = []
                for strike in target_strikes:
                    row = chain_lookup.get(strike, {})
                    ckey = (row.get("call_options") or {}).get("instrument_key")
                    pkey = (row.get("put_options") or {}).get("instrument_key")
                    if ckey: option_keys.append(ckey)
                    if pkey: option_keys.append(pkey)
                
                batch_quotes = fetch_quotes(option_keys)

                # 5. Map & Display
                print(f"\n>>> {name} | SPOT: {spot:10.2f} | FUT: {fut:10.2f} | Expiry: {nearest_expiry}")
                print("-" * 110)
                print(f"   {'CE OPEN/HI/LO':>20} | {'CE LTP':>10} | {'CE OI':>9} | {'STRIKE':>8} | {'PE OI':>9} | {'PE LTP':>10} | {'PE OPEN/HI/LO':<20}")
                print("-" * 110)

                snapshot_rows = []
                for strike in target_strikes:
                    row = chain_lookup.get(strike, {})
                    c_opt = row.get("call_options") or {}
                    p_opt = row.get("put_options") or {}
                    
                    ckey = c_opt.get("instrument_key")
                    pkey = p_opt.get("instrument_key")
                    
                    # Merge data from chain and batch fetch
                    c_full = batch_quotes.get(ckey, {})
                    p_full = batch_quotes.get(pkey, {})
                    
                    ce_data = {
                        "ltp": c_full.get("last_price") or (c_opt.get("market_data") or {}).get("ltp", 0),
                        "oi":  (c_opt.get("market_data") or {}).get("oi", 0),
                        "ohlc": c_full.get("ohlc")
                    }
                    pe_data = {
                        "ltp": p_full.get("last_price") or (p_opt.get("market_data") or {}).get("ltp", 0),
                        "oi":  (p_opt.get("market_data") or {}).get("oi", 0),
                        "ohlc": p_full.get("ohlc")
                    }

                    snapshot_rows.append({"strike": strike, "ce_ltp": ce_data['ltp'], "ce_oi": ce_data['oi'], "pe_ltp": pe_data['ltp'], "pe_oi": pe_data['oi']})
                    
                    print_row(strike, ce_data, pe_data, strike == atm_strike)

                # 6. Save to DB
                save_to_db(conn, ts, name, spot, snapshot_rows)

            print("\n" + "=" * 110)
            print("Polling every 5s. Press Ctrl+C to exit.")

            time.sleep(5)

    except KeyboardInterrupt:
        print("\nExiting. Closing database connection...")
        conn.close()
        sys.exit(0)

if __name__ == "__main__":
    main()
