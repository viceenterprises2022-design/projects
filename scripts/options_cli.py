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
    1: {"name": "NIFTY",     "key": "NSE_INDEX|Nifty 50",   "exch": "NSE_FO", "step": 50},
    2: {"name": "SENSEX",    "key": "BSE_INDEX|SENSEX",     "exch": "BSE_FO", "step": 100},
    3: {"name": "BANKNIFTY", "key": "NSE_INDEX|Nifty Bank", "exch": "NSE_FO", "step": 100}
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

# ── Formatting ────────────────────────────────────────────────────────────────

def format_oi(n):
    """Format OI to Lakhs (L) or Crores (C)."""
    if n >= 10000000:
        return f"{n/10000000:6.2f}C"
    if n >= 100000:
        return f"{n/100000:6.2f}L"
    return f"{n:7.0f}"

def print_row(strike, ce_ltp, ce_oi, pe_ltp, pe_oi, is_atm=False):
    marker = ">> " if is_atm else "   "
    c_oi_s = format_oi(ce_oi)
    p_oi_s = format_oi(pe_oi)
    print(f"{marker}{ce_ltp:10.2f} | {c_oi_s:>9} | {strike:8} | {p_oi_s:>9} | {pe_ltp:10.2f}")

# ── Main Loop ─────────────────────────────────────────────────────────────────

def main():
    conn = init_db()

    try:
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print("=" * 85)
            print(f" LIVE MULTI-INDEX OPTIONS DASHBOARD | {ts}")
            print("=" * 85)

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
                
                fut_key = get_futures_key(name, exch)
                fut = fetch_quote(fut_key) or spot # Fallback to spot
                
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

                # 4. Map & Display
                chain_lookup = {row.get("strike_price"): row for row in chain if isinstance(row, dict)}
                
                print(f"\n>>> {name} | SPOT: {spot:10.2f} | FUT: {fut:10.2f} | Expiry: {nearest_expiry}")
                print("-" * 85)
                print(f"   {'CE LTP':>10} | {'CE OI':>9} | {'STRIKE':>8} | {'PE OI':>9} | {'PE LTP':>10}")
                print("-" * 85)

                snapshot_rows = []
                for strike in target_strikes:
                    row = chain_lookup.get(strike, {})
                    cmd = (row.get("call_options") or {}).get("market_data") or {}
                    pmd = (row.get("put_options")  or {}).get("market_data") or {}

                    r_data = {
                        "strike": strike,
                        "ce_ltp": cmd.get("ltp", 0) or 0,
                        "ce_oi":  cmd.get("oi", 0) or 0,
                        "pe_ltp": pmd.get("ltp", 0) or 0,
                        "pe_oi":  pmd.get("oi", 0) or 0
                    }
                    snapshot_rows.append(r_data)
                    
                    print_row(strike, r_data['ce_ltp'], r_data['ce_oi'], 
                              r_data['pe_ltp'], r_data['pe_oi'], strike == atm_strike)

                # 5. Save to DB
                save_to_db(conn, ts, name, spot, snapshot_rows)

            print("\n" + "=" * 85)
            print("Polling every 5s. Press Ctrl+C to exit.")

            time.sleep(5)

    except KeyboardInterrupt:
        print("\nExiting. Closing database connection...")
        conn.close()
        sys.exit(0)

if __name__ == "__main__":
    main()
