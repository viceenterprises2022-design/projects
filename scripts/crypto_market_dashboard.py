#!/usr/bin/env python3
import requests
import datetime
import time
import os
import sys

# ── Config ────────────────────────────────────────────────────────────────────
SYMBOLS = ["BTC", "ETH", "SOL"]

# API Endpoints
BINANCE_SPOT_URL = "https://api.binance.com/api/v3/klines"
BINANCE_FUT_URL = "https://fapi.binance.com/fapi/v1/klines"
BINANCE_FUT_OI_URL = "https://fapi.binance.com/fapi/v1/openInterest"
DERIBIT_URL = "https://www.deribit.com/api/v2/public"

# ── Helper Functions ──────────────────────────────────────────────────────────

def fetch_json(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def get_ohlc_flags(o, h, l):
    """Flag O=H and O=L strategies."""
    if not o: return ""
    flags = []
    if o == h and o > 0: flags.append("OH")
    if o == l and o > 0: flags.append("OL")
    return "|".join(flags)

def format_money(val):
    if val >= 1_000_000_000: return f"${val/1_000_000_000:.2f}B"
    if val >= 1_000_000: return f"${val/1_000_000:.2f}M"
    if val >= 1_000: return f"${val/1_000:.2f}K"
    return f"${val:.2f}"

def format_ohlc_row(label, o, h, l, c, extra="", is_bullish_bias=True):
    G, R, W = "\033[92m", "\033[91m", "\033[0m"
    flags = get_ohlc_flags(o, h, l)
    
    o_s = f"{o:10.2f}"
    f_tag = ""
    
    if "OL" in flags:
        o_s = f"{G}{o_s}{W}" if is_bullish_bias else f"{R}{o_s}{W}"
        f_tag = f"{G}[OL]{W}" if is_bullish_bias else f"{R}[OL]{W}"
    elif "OH" in flags:
        o_s = f"{R}{o_s}{W}" if is_bullish_bias else f"{G}{o_s}{W}"
        f_tag = f"{R}[OH]{W}" if is_bullish_bias else f"{G}[OH]{W}"
        
    return f"  {label:<10} | {o_s} {h:10.2f} {l:10.2f} {c:10.2f} | {f_tag:<10} | {extra}"

# ── Data Fetchers ─────────────────────────────────────────────────────────────

def get_binance_spot(symbol):
    data = fetch_json(BINANCE_SPOT_URL, {"symbol": f"{symbol}USDT", "interval": "1d", "limit": 1})
    if data:
        k = data[0]
        return {"o": float(k[1]), "h": float(k[2]), "l": float(k[3]), "c": float(k[4])}
    return None

def get_binance_fut(symbol):
    klines = fetch_json(BINANCE_FUT_URL, {"symbol": f"{symbol}USDT", "interval": "1d", "limit": 1})
    oi_data = fetch_json(BINANCE_FUT_OI_URL, {"symbol": f"{symbol}USDT"})
    if klines and oi_data:
        k = klines[0]
        return {
            "o": float(k[1]), "h": float(k[2]), "l": float(k[3]), "c": float(k[4]),
            "oi": float(oi_data.get("openInterest", 0))
        }
    return None

def get_deribit_options(symbol, spot_price):
    # 1. Get Summary for the currency
    summary = fetch_json(f"{DERIBIT_URL}/get_book_summary_by_currency", {"currency": symbol, "kind": "option"})
    if not summary: return None
    
    # 2. Extract unique expiries and find nearest
    instruments = [s.get("instrument_name") for s in summary.get("result", [])]
    # Name format: BTC-27JUN25-90000-C
    
    def parse_expiry(name):
        parts = name.split('-')
        if len(parts) < 2: return "99999999"
        return parts[1] # e.g. 27JUN25
        
    unique_expiries = sorted(list(set([parse_expiry(i) for i in instruments])))
    if not unique_expiries: return None
    nearest_exp = unique_expiries[0]
    
    # 3. Filter for nearest expiry and find ATM strike
    nearest_data = [s for s in summary.get("result", []) if nearest_exp in s.get("instrument_name")]
    
    def get_strike(name):
        parts = name.split('-')
        return float(parts[2]) if len(parts) > 2 else 0
        
    strikes = sorted(list(set([get_strike(s.get("instrument_name")) for s in nearest_data])))
    if not strikes: return None
    atm_strike = min(strikes, key=lambda x: abs(x - spot_price))
    
    # 4. Get CE and PE details
    ce_data = next((s for s in nearest_data if f"-{int(atm_strike)}-C" in s.get("instrument_name")), None)
    pe_data = next((s for s in nearest_data if f"-{int(atm_strike)}-P" in s.get("instrument_name")), None)
    
    return {
        "expiry": nearest_exp,
        "strike": atm_strike,
        "ce": ce_data,
        "pe": pe_data
    }

# ── Main Loop ─────────────────────────────────────────────────────────────────

def main():
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print("=" * 125)
        print(f" CRYPTO MARKET REAL-TIME DASHBOARD | {ts}")
        print("=" * 125)
        
        for sym in SYMBOLS:
            print(f"\n>>> {sym} MARKET")
            print("-" * 125)
            
            spot = get_binance_spot(sym)
            fut = get_binance_fut(sym)
            
            if not spot:
                print(f"  [!] Failed to fetch Spot data for {sym}")
                continue
                
            # Spot & Futures Display
            print(f"  {'TYPE':<10} | {'OPEN':>10} {'HIGH':>10} {'LOW':>10} {'CLOSE':>10} | {'FLAGS':<10} | {'INFO'}")
            print(format_ohlc_row("SPOT", spot['o'], spot['h'], spot['l'], spot['c']))
            
            if fut:
                oi_notional = fut['oi'] * spot['c']
                print(format_ohlc_row("FUTURES", fut['o'], fut['h'], fut['l'], fut['c'], f"OI: {fut['oi']:,.2f} ({format_money(oi_notional)})"))
            
            # Options Display
            opt = get_deribit_options(sym, spot['c'])
            if opt:
                print(f"  {'OPTIONS':<10} | Expiry: {opt['expiry']} | ATM Strike: {opt['strike']}")
                
                # CE
                if opt['ce']:
                    c = opt['ce']
                    print(format_ohlc_row("CALL (CE)", c.get("open_low",0), c.get("high",0), c.get("low",0), c.get("last",0), 
                                          f"OI: {c.get('open_interest',0):,.1f} | LTP: {c.get('last',0)}", True))
                else:
                    print(f"  {'CALL (CE)':<10} | No Data")
                    
                # PE
                if opt['pe']:
                    p = opt['pe']
                    print(format_ohlc_row("PUT (PE)", p.get("open_low",0), p.get("high",0), p.get("low",0), p.get("last",0), 
                                          f"OI: {p.get('open_interest',0):,.1f} | LTP: {p.get('last',0)}", False))
                else:
                    print(f"  {'PUT (PE)':<10} | No Data")

        print("\n" + "=" * 125)
        print("Polling every 15s. Press Ctrl+C to exit.")
        time.sleep(15)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
