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

def get_option_ohlc_deribit(instrument_name):
    """Fetch real OHLC for an instrument from Deribit."""
    now = int(time.time() * 1000)
    start = now - (24 * 3600 * 1000)
    data = fetch_json(f"{DERIBIT_URL}/get_tradingview_chart_data", {
        "instrument_name": instrument_name,
        "start_timestamp": start,
        "end_timestamp": now,
        "resolution": "1D"
    })
    if data and data.get("result", {}).get("status") == "ok":
        r = data["result"]
        if r.get("open"):
            # Return last candle
            return {"o": r["open"][-1], "h": r["high"][-1], "l": r["low"][-1], "c": r["close"][-1]}
    return None

def get_deribit_options(symbol, spot_price):
    # 1. Get Summary for the currency
    summary = fetch_json(f"{DERIBIT_URL}/get_book_summary_by_currency", {"currency": symbol, "kind": "option"})
    if not summary: return None
    
    # 2. Extract unique expiries and find nearest
    results = summary.get("result", [])
    if not results: return None
    
    instruments = [s.get("instrument_name") for s in results]
    
    def parse_expiry(name):
        parts = name.split('-')
        return parts[1] if len(parts) > 1 else "99999999"
        
    unique_expiries = sorted(list(set([parse_expiry(i) for i in instruments])))
    nearest_exp = unique_expiries[0]
    
    # 3. Filter for nearest expiry and find ATM strike
    nearest_data = [s for s in results if nearest_exp in s.get("instrument_name")]
    
    def get_strike(name):
        parts = name.split('-')
        return float(parts[2]) if len(parts) > 2 else 0
        
    strikes = sorted(list(set([get_strike(s.get("instrument_name")) for s in nearest_data])))
    atm_strike = min(strikes, key=lambda x: abs(x - spot_price))
    
    # 4. Get CE and PE names
    ce_name = next((s.get("instrument_name") for s in nearest_data if f"-{int(atm_strike)}-C" in s.get("instrument_name")), None)
    pe_name = next((s.get("instrument_name") for s in nearest_data if f"-{int(atm_strike)}-P" in s.get("instrument_name")), None)
    
    # 5. Fetch OHLC and merge with summary
    res = {"expiry": nearest_exp, "strike": atm_strike, "ce": None, "pe": None}
    
    for side, name in [("ce", ce_name), ("pe", pe_name)]:
        if not name: continue
        s_data = next((s for s in nearest_data if s.get("instrument_name") == name), {})
        ohlc = get_option_ohlc_deribit(name)
        
        # Convert to USD if available
        u_price = s_data.get("underlying_price", spot_price)
        
        def to_usd(val): return val * u_price if val else 0
        
        if ohlc:
            res[side] = {
                "o": to_usd(ohlc["o"]), "h": to_usd(ohlc["h"]), "l": to_usd(ohlc["l"]), "c": to_usd(ohlc["c"]),
                "oi": s_data.get("open_interest", 0),
                "ltp": to_usd(s_data.get("last", 0))
            }
        else:
            # Fallback to summary if no candle
            res[side] = {
                "o": to_usd(s_data.get("last", 0)), # Approximation
                "h": to_usd(s_data.get("high", 0)),
                "l": to_usd(s_data.get("low", 0)),
                "c": to_usd(s_data.get("last", 0)),
                "oi": s_data.get("open_interest", 0),
                "ltp": to_usd(s_data.get("last", 0))
            }
            
    return res

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
                
                for side, label, bias in [("ce", "CALL (CE)", True), ("pe", "PUT (PE)", False)]:
                    d = opt[side]
                    if d:
                        print(format_ohlc_row(label, d['o'], d['h'], d['l'], d['c'], 
                                              f"OI: {d['oi']:,.1f} | LTP: ${d['ltp']:.2f}", bias))
                    else:
                        print(f"  {label:<10} | No Data")

        print("\n" + "=" * 125)
        print("Polling every 15s. Press Ctrl+C to exit.")
        time.sleep(15)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
