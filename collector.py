#!/usr/bin/env python3
"""
AlphaEdge Data Collector
Fetches market data from Upstox + Yahoo Finance, runs the 10-factor signal engine,
and writes results to alphaedge.db via alphaedge_db.py.

Usage:
    # Single run:
    python collector.py

    # Continuous (every N minutes):
    python collector.py --loop --interval 5
"""

import requests
import datetime
import time
import json
import argparse
import sys
import os

# Ensure we can import alphaedge_db from same dir
sys.path.insert(0, os.path.dirname(__file__))
import alphaedge_db as db

# ── Config ────────────────────────────────────────────────────────────────────
UPSTOX_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJGVzY0MDYiLCJqdGkiOiI2OWVjZDE1NTU0ZTdlMzBhNmY0NTZkODYiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaXNFeHRlbmRlZCI6dHJ1ZSwiaWF0IjoxNzc3MTI3NzY1LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE4MDg2OTA0MDB9.lxl6fYYoKH1_2AItX-XN40eNsYhbAzbjnwbvyopgSUo"
UH = {"Authorization": f"Bearer {UPSTOX_TOKEN}", "Accept": "application/json"}

INSTRUMENTS = {
    "NIFTY":     "NSE_INDEX|Nifty 50",
    "SENSEX":    "BSE_INDEX|SENSEX",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "INDIA_VIX": "NSE_INDEX|India VIX",
}
OI_INSTRUMENTS = {
    "NIFTY":     "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "SENSEX":    "BSE_INDEX|SENSEX",
}
OI_RANGE = 1000
YAHOO_SYM = {"DXY": "DX-Y.NYB", "CRUDE_OIL": "CL=F", "US30": "YM=F", "GOLD": "GC=F", "SILVER": "SI=F"}
YAHOO_IDX = {"NIFTY": "^NSEI", "SENSEX": "^BSESN", "BANKNIFTY": "^NSEBANK"}
YH = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


# ── Upstox Fetchers ───────────────────────────────────────────────────────────

def upstox_get(url, params):
    try:
        r = requests.get(url, headers=UH, params=params, timeout=12)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"    [W] {url.split('/')[-1]} {params}: {e}")
    return {}


def fetch_quote(key):
    d = upstox_get("https://api.upstox.com/v2/market-quote/quotes", {"instrument_key": key})
    if d.get("status") == "success" and d.get("data"):
        q = list(d["data"].values())[0]
        ohlc = q.get("ohlc", {}); prev = ohlc.get("close", 0) or 1
        ltp = q.get("last_price", 0); chg = ltp - prev
        return {"ltp": ltp, "open": ohlc.get("open", 0), "high": ohlc.get("high", 0),
                "low": ohlc.get("low", 0), "close": prev, "volume": q.get("volume", 0),
                "change": chg, "change_pct": chg / prev * 100}
    return None


def fetch_candles(key, days=90):
    today = datetime.date.today()
    f = (today - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    t = today.strftime("%Y-%m-%d")
    d = upstox_get(f"https://api.upstox.com/v2/historical-candle/{key}/day/{t}/{f}", {})
    if d.get("status") == "success":
        raw = d.get("data", {}).get("candles", [])
        return [[c[0], float(c[1]), float(c[2]), float(c[3]), float(c[4]),
                 float(c[5]) if len(c) > 5 else 0] for c in raw]
    return []


def fetch_expiries(key):
    d = upstox_get("https://api.upstox.com/v2/option/contract", {"instrument_key": key})
    if d.get("status") == "success" and d.get("data"):
        raw = d["data"]
        if raw and isinstance(raw[0], str):
            return sorted(raw)
        elif raw and isinstance(raw[0], dict):
            return sorted([x.get("expiry", "") for x in raw if x.get("expiry")])
    return []


def fetch_option_chain(key, expiry):
    d = upstox_get("https://api.upstox.com/v2/option/chain",
                   {"instrument_key": key, "expiry_date": expiry})
    if d.get("status") == "success":
        return d.get("data", [])
    return []


def build_oi_data(symbol, spot):
    """Fetch option chain and return only derived metrics (no raw strikes stored)."""
    key = OI_INSTRUMENTS.get(symbol)
    if not key:
        return None
    expiries = fetch_expiries(key)
    if not expiries:
        return None
    nearest = expiries[0]
    chain = fetch_option_chain(key, nearest)
    if not chain:
        return None

    lo, hi = spot - OI_RANGE, spot + OI_RANGE
    strikes = []
    total_call_oi = total_put_oi = 0

    for row in chain:
        if not isinstance(row, dict):
            continue
        strike = row.get("strike_price", 0)
        if not (lo <= strike <= hi):
            continue
        cmd = (row.get("call_options") or {}).get("market_data") or {}
        pmd = (row.get("put_options") or {}).get("market_data") or {}
        c_oi = cmd.get("oi", 0) or 0
        p_oi = pmd.get("oi", 0) or 0
        total_call_oi += c_oi
        total_put_oi += p_oi
        strikes.append({
            "strike": strike, "call_oi": c_oi, "put_oi": p_oi,
            "call_doi": cmd.get("change_in_oi", 0) or 0,
            "put_doi": pmd.get("change_in_oi", 0) or 0,
            "pcr": round(p_oi / max(c_oi, 1), 3),
        })

    if not strikes:
        return None
    strikes.sort(key=lambda x: x["strike"])

    # Max Pain
    def mp_loss(target):
        loss = 0
        for s in strikes:
            k = s["strike"]
            if target > k: loss += s["call_oi"] * (target - k)
            if target < k: loss += s["put_oi"] * (k - target)
        return loss

    min_loss, max_pain_strike = None, strikes[0]["strike"]
    for s in strikes:
        loss = mp_loss(s["strike"])
        if min_loss is None or loss < min_loss:
            min_loss = loss
            max_pain_strike = s["strike"]

    total_pcr = round(total_put_oi / max(total_call_oi, 1), 3)
    return {
        "expiry": nearest, "spot": spot,
        "total_call_oi": total_call_oi, "total_put_oi": total_put_oi,
        "total_pcr": total_pcr, "max_pain": max_pain_strike,
    }


# ── Yahoo Fetcher ─────────────────────────────────────────────────────────────

def fetch_yahoo(symbol, days=60, interval="1d"):
    end = int(time.time()); start = end - days * 86400
    try:
        r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                         params={"period1": start, "period2": end, "interval": interval},
                         headers=YH, timeout=12)
        res = (r.json().get("chart", {}).get("result") or [None])[0]
        if not res: return None
        q = res["indicators"]["quote"][0]; ts = res.get("timestamp", [])
        valid = [(t, o, h, l, c, v) for t, o, h, l, c, v in
                 zip(ts, q.get("open", []), q.get("high", []), q.get("low", []),
                     q.get("close", []), q.get("volume", []))
                 if c is not None and o is not None]
        if not valid: return None
        last = valid[-1]; prev = valid[-2][4] if len(valid) > 1 else last[4]
        chg = last[4] - prev
        return {"ltp": last[4], "open": last[1], "high": last[2], "low": last[3],
                "close": prev, "volume": last[5] or 0, "change": chg,
                "change_pct": chg / prev * 100 if prev else 0,
                "candles": [[t, o, h, l, c, v or 0] for t, o, h, l, c, v in valid]}
    except Exception as e:
        print(f"    [W] Yahoo {symbol}: {e}")
    return None


# ── Indicators ────────────────────────────────────────────────────────────────

def ema(v, n):
    if len(v) < n: return []
    out = [sum(v[:n]) / n]; k = 2 / (n + 1)
    for x in v[n:]: out.append(x * k + out[-1] * (1 - k))
    return out


def rsi_val(closes, n=14):
    if len(closes) < n + 2: return 50.0
    g = [max(closes[i] - closes[i - 1], 0) for i in range(1, len(closes))]
    l = [max(closes[i - 1] - closes[i], 0) for i in range(1, len(closes))]
    ag = sum(g[-n:]) / n; al = sum(l[-n:]) / n
    return 100.0 if al == 0 else 100 - 100 / (1 + ag / al)


def atr_val(c, n=14):
    trs = [max(c[i][2] - c[i][3], abs(c[i][2] - c[i - 1][4]), abs(c[i][3] - c[i - 1][4]))
           for i in range(1, len(c))]
    return sum(trs[-n:]) / min(n, len(trs)) if trs else 0


def supertrend(c, n=10, m=3):
    if len(c) < n + 2: return None, 0
    a = atr_val(c, n)
    if a == 0: return None, 0
    hl2 = (c[-1][2] + c[-1][3]) / 2; lo = hl2 - m * a
    d = 1 if c[-1][4] > lo else -1
    return (lo if d == 1 else hl2 + m * a), d


def vwap_val(c, bars=20):
    tv = vol = 0.0
    for x in c[-bars:]:
        v = x[5] or 0; tp = (x[2] + x[3] + x[4]) / 3; tv += tp * v; vol += v
    return tv / vol if vol > 0 else None


def trend_analysis(c):
    cl = [x[4] for x in c]
    if len(cl) < 20: return "N/A", 0, ""
    e20 = ema(cl, 20)[-1]; e50 = ema(cl, min(50, len(cl)))[-1]
    e200l = ema(cl, min(200, len(cl))); e200 = e200l[-1] if e200l else None
    cur = cl[-1]; det = f"EMA20={e20:,.0f} | EMA50={e50:,.0f}"
    if e200: det += f" | EMA200={e200:,.0f}"
    if e200:
        if cur > e20 > e50 > e200: return "Strong Uptrend", 2, det
        if cur < e20 < e50 < e200: return "Strong Downtrend", -2, det
    if cur > e20 > e50: return "Uptrend", 1, det
    if cur < e20 < e50: return "Downtrend", -1, det
    if cur > e20: return "Mild Uptrend", 1, det
    if cur < e20: return "Mild Downtrend", -1, det
    return "Sideways", 0, det


def sig_color(sc, fa):
    r = sc / max(fa, 1)
    if r >= 0.35: return "BUY"
    if r <= -0.35: return "SELL"
    return "NEUTRAL"


# ── 10-Factor Analyzer ────────────────────────────────────────────────────────

def analyze(sym, quote, uc, oi_raw, gd, yc):
    res = {}; sc = fa = 0
    c = uc if len(uc) >= 10 else yc
    ltp = (quote or {}).get("ltp", 0)

    # 1 TREND
    if len(c) >= 20:
        lb, s, dt = trend_analysis(c)
        res["trend"] = {"label": lb, "score": s, "detail": dt}
        sc += s; fa += 2
    else:
        res["trend"] = {"label": "N/A", "score": 0, "detail": f"{len(c)} bars"}

    # 2 DOW JONES
    u = gd.get("US30")
    if u:
        ch = u["change_pct"]; s = 1 if ch > 0.3 else (-1 if ch < -0.3 else 0)
        res["dow_jones"] = {"label": f"{'Bullish' if s > 0 else 'Bearish' if s < 0 else 'Flat'} ({ch:+.2f}%)",
                            "score": s, "detail": f"DJIA Fut: {u['ltp']:,.0f}"}
        sc += s; fa += 1
    else:
        res["dow_jones"] = {"label": "N/A", "score": 0, "detail": "Unavailable"}

    # 3 INDIA VIX
    v = gd.get("VIX")
    if v:
        vv = v["ltp"]
        if vv < 13:      s, lb = 1,  f"Low ({vv:.2f}) — Calm"
        elif vv <= 17:   s, lb = 1,  f"Normal ({vv:.2f}) — Stable"
        elif vv <= 21:   s, lb = 0,  f"Elevated ({vv:.2f}) — Caution"
        else:            s, lb = -1, f"High ({vv:.2f}) — Fear"
        res["india_vix"] = {"label": lb, "score": s, "detail": f"Chg: {v.get('change_pct', 0):+.2f}%"}
        sc += s; fa += 1
    else:
        res["india_vix"] = {"label": "N/A", "score": 0, "detail": "Unavailable"}

    # 4 OPEN INTEREST
    if oi_raw:
        total_c = oi_raw["total_call_oi"]; total_p = oi_raw["total_put_oi"]
        oi_ratio = total_c / max(total_p, 1)
        if oi_ratio > 1.3:    s, lb = -1, "Call Heavy — Resistance strong"
        elif oi_ratio > 1.1:  s, lb = -1, "Mild Call Heavy"
        elif oi_ratio < 0.7:  s, lb = 1,  "Put Heavy — Support strong"
        elif oi_ratio < 0.9:  s, lb = 1,  "Mild Put Heavy"
        else:                  s, lb = 0,  "Balanced OI"
        cL = total_c / 1e5; pL = total_p / 1e5
        res["oi"] = {"label": lb, "score": s,
                     "detail": f"Calls:{cL:.1f}L | Puts:{pL:.1f}L | Exp:{oi_raw['expiry']}"}
        sc += s; fa += 1
    else:
        res["oi"] = {"label": "N/A", "score": 0, "detail": "Market closed / no chain"}

    # 5 VWAP
    if c and ltp:
        vw = vwap_val(c)
        if vw:
            dp = (ltp - vw) / vw * 100
            if ltp > vw * 1.002:    s, lb = 1,  f"Above (+{dp:.2f}%)"
            elif ltp < vw * 0.998:  s, lb = -1, f"Below ({dp:.2f}%)"
            else:                    s, lb = 0,  f"At VWAP ({dp:+.2f}%)"
            res["vwap"] = {"label": lb, "score": s, "detail": f"VWAP:{vw:,.2f} | LTP:{ltp:,.2f}"}
            sc += s; fa += 1
        else:
            res["vwap"] = {"label": "N/A", "score": 0, "detail": "No volume data"}
    else:
        res["vwap"] = {"label": "N/A", "score": 0, "detail": "No candles"}

    # 6 SUPERTREND
    if len(c) >= 12:
        stv, std = supertrend(c)
        if std == 1:    lb = f"Bullish (Sup≈{stv:,.0f})" if stv else "Bullish"
        elif std == -1: lb = f"Bearish (Res≈{stv:,.0f})" if stv else "Bearish"
        else:            lb = "Neutral"
        res["supertrend"] = {"label": lb, "score": std, "detail": "ATR(10) × 3"}
        sc += std; fa += 1
    else:
        res["supertrend"] = {"label": "N/A", "score": 0, "detail": "Need ≥12 bars"}

    # 7 RSI
    if len(c) >= 16:
        rv = rsi_val([x[4] for x in c])
        if rv >= 75:    s, lb = -1, f"Overbought ({rv:.1f})"
        elif rv >= 60:  s, lb = 1,  f"Bullish Zone ({rv:.1f})"
        elif rv <= 25:  s, lb = 1,  f"Oversold ({rv:.1f})"
        elif rv <= 40:  s, lb = -1, f"Bearish Zone ({rv:.1f})"
        else:            s, lb = 0,  f"Neutral ({rv:.1f})"
        res["rsi"] = {"label": lb, "score": s, "detail": "RSI(14) Daily"}
        sc += s; fa += 1
    else:
        res["rsi"] = {"label": "N/A", "score": 0, "detail": "Need ≥16 bars"}

    # 8 DXY
    dx = gd.get("DXY")
    if dx:
        ch = dx["change_pct"]
        if ch > 0.5:    s, lb = -1, f"Surging ({ch:+.2f}%) — EM risk"
        elif ch > 0.2:  s, lb = -1, f"Strengthening ({ch:+.2f}%)"
        elif ch < -0.5: s, lb = 1,  f"Weakening ({ch:+.2f}%) — EM positive"
        elif ch < -0.2: s, lb = 1,  f"Softening ({ch:+.2f}%)"
        else:            s, lb = 0,  f"Stable ({ch:+.2f}%)"
        res["dxy"] = {"label": lb, "score": s, "detail": f"DXY: {dx['ltp']:.3f}"}
        sc += s; fa += 1
    else:
        res["dxy"] = {"label": "N/A", "score": 0, "detail": "Unavailable"}

    # 9 CRUDE OIL
    cr = gd.get("CRUDE_OIL")
    if cr:
        ch = cr["change_pct"]
        if ch > 2.0:    s, lb = -1, f"Surging ({ch:+.2f}%) — Inflation risk"
        elif ch > 0.8:  s, lb = -1, f"Rising ({ch:+.2f}%)"
        elif ch < -2.0: s, lb = 1,  f"Crashing ({ch:+.2f}%)"
        elif ch < -0.8: s, lb = 1,  f"Falling ({ch:+.2f}%)"
        else:            s, lb = 0,  f"Stable ({ch:+.2f}%)"
        res["crude"] = {"label": lb, "score": s, "detail": f"WTI: ${cr['ltp']:.2f}"}
        sc += s; fa += 1
    else:
        res["crude"] = {"label": "N/A", "score": 0, "detail": "Unavailable"}

    # 10 PCR
    if oi_raw:
        pcr = oi_raw["total_pcr"]; mp = oi_raw["max_pain"]
        if pcr > 1.3:    s, lb = 1,  f"Bullish — PCR {pcr:.2f}"
        elif pcr > 1.1:  s, lb = 1,  f"Mildly Bullish — PCR {pcr:.2f}"
        elif pcr < 0.7:  s, lb = -1, f"Bearish — PCR {pcr:.2f}"
        elif pcr < 0.9:  s, lb = -1, f"Mildly Bearish — PCR {pcr:.2f}"
        else:             s, lb = 0,  f"Neutral — PCR {pcr:.2f}"
        res["pcr"] = {"label": lb, "score": s,
                      "detail": f"Max Pain: {mp:,.0f} | Total PCR: {pcr:.2f}"}
        sc += s; fa += 1
    else:
        res["pcr"] = {"label": "N/A", "score": 0, "detail": "Requires option chain"}

    return {"indicators": res, "score": sc, "factors": fa, "signal": sig_color(sc, fa)}


# ── Collection Run ────────────────────────────────────────────────────────────

def run_once():
    ts = datetime.datetime.utcnow().isoformat()
    print(f"\n{'='*56}")
    print(f"  AlphaEdge Collector — {ts} UTC")
    print(f"{'='*56}")

    # 1. Global / macro data
    print("\n[1/4] Macro data...")
    gdata = {}
    vq = fetch_quote(INSTRUMENTS["INDIA_VIX"])
    if vq: gdata["VIX"] = vq; print(f"  ✓ VIX {vq['ltp']:.2f}")
    else: print("  ✗ VIX unavailable")
    for key, ytick in YAHOO_SYM.items():
        d = fetch_yahoo(ytick, days=5, interval="1h")
        if d: gdata[key] = d; print(f"  ✓ {key:<15} {d['ltp']:.3f} ({d['change_pct']:+.2f}%)")
        else: print(f"  ✗ {key} unavailable")

    # 2. Index quotes
    print("\n[2/4] Index quotes...")
    quotes = {}
    for sym, key in {k: v for k, v in INSTRUMENTS.items() if k != "INDIA_VIX"}.items():
        q = fetch_quote(key); quotes[sym] = q or {}
        if q: print(f"  ✓ {sym:<12} {q['ltp']:>12,.2f} ({q['change_pct']:+.2f}%)")
        else: print(f"  ✗ {sym} unavailable")

    # 3. Candles
    print("\n[3/4] Candles + Option Chain OI...")
    uc, yc, oi_map = {}, {}, {}
    for sym, key in {k: v for k, v in INSTRUMENTS.items() if k != "INDIA_VIX"}.items():
        c = fetch_candles(key, days=90); uc[sym] = c
        print(f"  Upstox {sym:<12} {len(c)} bars")
    for sym, ytick in YAHOO_IDX.items():
        d = fetch_yahoo(ytick, days=90, interval="1d")
        if d and "candles" in d:
            yc[sym] = d["candles"]
            print(f"  Yahoo  {sym:<12} {len(d['candles'])} bars")
            if not quotes.get(sym, {}).get("ltp"): quotes[sym] = d
        else:
            yc[sym] = []

    for sym in ["NIFTY", "SENSEX", "BANKNIFTY"]:
        spot = quotes.get(sym, {}).get("ltp", 0)
        if spot:
            oi = build_oi_data(sym, spot)
            if oi:
                oi_map[sym] = oi
                print(f"  OI {sym:<12} PCR={oi['total_pcr']:.2f} MaxPain={oi['max_pain']:,.0f}")
            else:
                print(f"  OI {sym:<12} unavailable")

    # 4. Signals + write to DB
    print("\n[4/4] Computing signals + writing DB...")
    for sym in ["NIFTY", "SENSEX", "BANKNIFTY"]:
        a = analyze(sym, quotes.get(sym, {}), uc.get(sym, []),
                    oi_map.get(sym), gdata, yc.get(sym, []))
        db.insert_metric(ts, sym, quotes.get(sym, {}), a, oi_map.get(sym))
        emoji = {"BUY": "🟢", "SELL": "🔴", "NEUTRAL": "🟡"}.get(a["signal"], "⚪")
        print(f"  {emoji} {sym:<12} {a['signal']:<8} Score:{a['score']:+d}/{a['factors']}")

    db.insert_macro(ts, gdata)
    print(f"\n  ✅  Written to alphaedge.db at {ts}")


def main():
    parser = argparse.ArgumentParser(description="AlphaEdge Data Collector")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=5, help="Minutes between runs (default: 5)")
    args = parser.parse_args()

    db.init_db()

    if args.loop:
        print(f"[Collector] Continuous mode — every {args.interval} min. Ctrl+C to stop.")
        while True:
            try:
                run_once()
            except Exception as e:
                print(f"[ERROR] {e}")
            print(f"\n  ⏱ Next run in {args.interval} minutes...\n")
            time.sleep(args.interval * 60)
    else:
        run_once()


if __name__ == "__main__":
    main()
