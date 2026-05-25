#!/usr/bin/env python3
"""
AlphaEdge Pro — Unified Live Terminal Dashboard
================================================
Merges:
  • market_analysis_v3.py  → 10-factor signal engine, PCR/Max Pain,
                              Yahoo macro (DXY/Crude/US30/VIX), SQLite intraday OI
  • fo_breakout_scanner.py → Live async F&O chain, greeks (Δ/IV/Vol-OI),
                              OI walls, buildup classification, IV squeeze alerts

Layout (fullscreen Rich Live):
  ┌──────────────────────── HEADER (5 rows) ─────────────────────────────────┐
  │ AlphaEdge Pro │ INDEX spot (chg%) │ Fut │ Expiry+DTE │ VIX │ Signal bar │
  │ Time │ Poll every Xs │ Last HH:MM │ Next Xs │ Status                     │
  ├────── CALLS ──────┬── STRIKE ──┬────── PUTS ──────────────────────────────┤
  │ BUILD│Δ│IV│V/OI   │  STRIKE    │  LTP│OI│OI CHG│V/OI│IV│Δ│BUILD        │
  │  ATM ±5 rows      │ ATM+MP mkd │  ATM ±5 rows                            │
  ├─── INDICATORS ────┴────────────┴──── OI WALLS ─────┬── ALERTS & MACRO ──┤
  │ 10-factor signal condensed     │ Resist/Support/PCR │ Spurts/IV/Macro    │
  └────────────────────────────────┴────────────────────┴────────────────────┘

Usage:  python3 alphaedge_pro.py
Press Ctrl+C to exit.
"""

import asyncio
import aiohttp
import sqlite3
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

# ── Credentials (from .env) ───────────────────────────────────────────────────
_upstox_token = None
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            if _line.startswith("UPSTOX_TOKEN="):
                _upstox_token = _line.strip().split("=", 1)[1]
                break

if not _upstox_token:
    print("[ERROR] UPSTOX_TOKEN not found in .env file")
    sys.exit(1)

UPSTOX_HEADERS = {"Authorization": f"Bearer {_upstox_token}", "Accept": "application/json"}
YAHOO_HEADERS  = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# ── Config ────────────────────────────────────────────────────────────────────
INDICES = {
    "NIFTY 50":   "NSE_INDEX|Nifty 50",
    "NIFTY BANK": "NSE_INDEX|Nifty Bank",
    "SENSEX":     "BSE_INDEX|SENSEX",
}
INDEX_MENU = {"1": "NIFTY 50", "2": "NIFTY BANK", "3": "SENSEX"}
# Canonical symbol name used for futures key construction and DB
SYM_MAP = {"NIFTY 50": "NIFTY", "NIFTY BANK": "BANKNIFTY", "SENSEX": "SENSEX"}

YAHOO_SYM = {"DXY": "DX-Y.NYB", "CRUDE": "CL=F", "US30": "^DJI", "VIX": "^VIX"}

POLL_INTERVAL   = 5    # seconds: spot + option chain + indicators
MACRO_INTERVAL  = 300  # seconds: Yahoo Finance macro data
CANDLE_INTERVAL = 300  # seconds: Upstox historical daily candles
DB_INTERVAL     = 60   # seconds: SQLite OI snapshot

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "intraday_oi.db")

# ── SQLite Intraday OI Store ──────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS trending_oi
        (timestamp TEXT, symbol TEXT, ltp REAL, call_oi REAL, put_oi REAL)
    """)
    c.execute("DELETE FROM trending_oi WHERE date(timestamp) < date('now', 'localtime')")
    conn.commit()
    conn.close()

def db_write_oi(sym, ltp, call_oi, put_oi):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:00")
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT 1 FROM trending_oi WHERE timestamp=? AND symbol=? LIMIT 1", (ts, sym))
        if not c.fetchone():
            c.execute("INSERT INTO trending_oi VALUES (?,?,?,?,?)", (ts, sym, ltp, call_oi, put_oi))
            conn.commit()
        conn.close()
    except Exception:
        pass

def db_read_oi(sym, limit=5):
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            "SELECT timestamp, ltp, call_oi, put_oi FROM trending_oi "
            "WHERE symbol=? ORDER BY timestamp DESC LIMIT ?", (sym, limit)
        ).fetchall()
        conn.close()
        return rows
    except Exception:
        return []

# ── Async HTTP Helper ─────────────────────────────────────────────────────────
async def safe_get(session, url, params=None, headers=None, timeout=12):
    try:
        h = headers if headers is not None else UPSTOX_HEADERS
        async with session.get(
            url, headers=h, params=params,
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as r:
            if r.status == 200:
                return await r.json(content_type=None)
            return {"error": f"HTTP {r.status}"}
    except Exception as e:
        return {"error": str(e)}

# ── Upstox Async Fetchers ─────────────────────────────────────────────────────
async def fetch_spot(session, key):
    """Return dict with ltp, change_pct, ohlc etc. or None on failure."""
    res = await safe_get(session, "https://api.upstox.com/v2/market-quote/quotes",
                         {"instrument_key": key})
    if isinstance(res, dict) and res.get("status") == "success":
        data = res.get("data", {})
        api_key = key.replace("|", ":")
        q = data.get(api_key, {})
        ltp   = q.get("last_price", 0.0)
        ohlc  = q.get("ohlc", {})
        close = ohlc.get("close", 0.0) or ltp or 1.0
        chg   = ((ltp - close) / close) * 100
        return {
            "ltp": ltp, "open": ohlc.get("open", 0.0), "high": ohlc.get("high", 0.0),
            "low": ohlc.get("low", 0.0), "close": close,
            "volume": q.get("volume", 0), "change": ltp - close, "change_pct": chg,
        }
    return None

async def fetch_expiries(session, key):
    res = await safe_get(session, "https://api.upstox.com/v2/option/contract",
                         {"instrument_key": key})
    if isinstance(res, dict) and res.get("status") == "success":
        raw = res.get("data", [])
        if raw and isinstance(raw[0], str):
            return sorted(raw)
        elif raw and isinstance(raw[0], dict):
            return sorted([x.get("expiry", "") for x in raw if x.get("expiry")])
    return []

async def fetch_option_chain(session, key, expiry):
    res = await safe_get(session, "https://api.upstox.com/v2/option/chain",
                         {"instrument_key": key, "expiry_date": expiry})
    if isinstance(res, dict) and res.get("status") == "success":
        return res.get("data", [])
    return []

async def fetch_candles(session, key, days=90):
    today = datetime.date.today()
    frm   = (today - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    to    = today.strftime("%Y-%m-%d")
    url   = f"https://api.upstox.com/v2/historical-candle/{key}/day/{to}/{frm}"
    res   = await safe_get(session, url, {})
    if isinstance(res, dict) and res.get("status") == "success":
        raw = res.get("data", {}).get("candles", [])
        return [[c[0], float(c[1]), float(c[2]), float(c[3]), float(c[4]),
                 float(c[5]) if len(c) > 5 else 0] for c in raw]
    return []

async def fetch_futures_quote(session, sym):
    """Fetch nearest month futures, fall back to next month."""
    now = datetime.datetime.now()
    yr, mo = now.strftime("%y"), now.strftime("%b").upper()
    key = f"BSE_FO|SENSEX{yr}{mo}FUT" if sym == "SENSEX" else f"NSE_FO|{sym}{yr}{mo}FUT"
    q = await fetch_spot(session, key)
    if not q:
        if now.month == 12:
            nm = now.replace(year=now.year + 1, month=1)
        else:
            nm = now.replace(month=now.month + 1)
        yr2, mo2 = nm.strftime("%y"), nm.strftime("%b").upper()
        key2 = f"BSE_FO|SENSEX{yr2}{mo2}FUT" if sym == "SENSEX" else f"NSE_FO|{sym}{yr2}{mo2}FUT"
        q = await fetch_spot(session, key2)
    return q

async def fetch_yahoo(session, symbol, days=5):
    """Async Yahoo Finance quote — used for macro (DXY, Crude, US30, VIX)."""
    end   = int(time.time())
    start = end - days * 86400
    url   = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    res   = await safe_get(session, url, {"period1": start, "period2": end, "interval": "1d"},
                           headers=YAHOO_HEADERS, timeout=15)
    try:
        result = (res.get("chart", {}).get("result") or [None])[0]
        if not result:
            return None
        q  = result["indicators"]["quote"][0]
        ts = result.get("timestamp", [])
        valid = [
            (t, o, h, l, c, v) for t, o, h, l, c, v in
            zip(ts, q.get("open", []), q.get("high", []), q.get("low", []),
                q.get("close", []), q.get("volume", []))
            if c is not None and o is not None
        ]
        if not valid:
            return None
        last = valid[-1]
        prev = valid[-2][4] if len(valid) > 1 else last[4]
        chg  = last[4] - prev
        return {
            "ltp": last[4], "open": last[1], "high": last[2], "low": last[3],
            "close": prev,  "volume": last[5] or 0,
            "change": chg,  "change_pct": chg / prev * 100 if prev else 0,
        }
    except Exception:
        return None

# ── Technical Indicators ──────────────────────────────────────────────────────
def _ema(v, n):
    if len(v) < n:
        return []
    out = [sum(v[:n]) / n]
    k = 2 / (n + 1)
    for x in v[n:]:
        out.append(x * k + out[-1] * (1 - k))
    return out

def _rsi(closes, n=14):
    if len(closes) < n + 2:
        return 50.0
    g = [max(closes[i] - closes[i-1], 0) for i in range(1, len(closes))]
    l = [max(closes[i-1] - closes[i], 0) for i in range(1, len(closes))]
    ag, al = sum(g[-n:]) / n, sum(l[-n:]) / n
    return 100.0 if al == 0 else 100 - 100 / (1 + ag / al)

def _atr(c, n=14):
    trs = [max(c[i][2] - c[i][3], abs(c[i][2] - c[i-1][4]), abs(c[i][3] - c[i-1][4]))
           for i in range(1, len(c))]
    return sum(trs[-n:]) / min(n, len(trs)) if trs else 0

def _supertrend(c, n=10, m=3):
    if len(c) < n + 2:
        return None, 0
    a = _atr(c, n)
    if a == 0:
        return None, 0
    hl2 = (c[-1][2] + c[-1][3]) / 2
    lo  = hl2 - m * a
    d   = 1 if c[-1][4] > lo else -1
    return (lo if d == 1 else hl2 + m * a), d

def _vwap(c, bars=20):
    tv = vol = 0.0
    for x in c[-bars:]:
        v = x[5] or 0
        tp = (x[2] + x[3] + x[4]) / 3
        tv += tp * v; vol += v
    return tv / vol if vol > 0 else None

def _trend(c):
    cl = [x[4] for x in c]
    if len(cl) < 20:
        return "N/A", 0, ""
    e20  = _ema(cl, 20)[-1]
    e50  = _ema(cl, min(50, len(cl)))[-1]
    e200l = _ema(cl, min(200, len(cl)))
    e200 = e200l[-1] if e200l else None
    cur  = cl[-1]
    det  = f"EMA20={e20:,.0f} EMA50={e50:,.0f}"
    if e200:
        det += f" EMA200={e200:,.0f}"
        if cur > e20 > e50 > e200: return "STRONG UP",   2, det
        if cur < e20 < e50 < e200: return "STRONG DN",  -2, det
    if cur > e20 > e50: return "UPTREND",     1, det
    if cur < e20 < e50: return "DOWNTREND",  -1, det
    if cur > e20:       return "MILD UP",     1, det
    if cur < e20:       return "MILD DN",    -1, det
    return "SIDEWAYS", 0, det

# ── OI Analysis ───────────────────────────────────────────────────────────────
def build_oi_summary(chain_data, spot, oi_range=1500):
    """Compute total OI, PCR, Max Pain from the full option chain."""
    if not chain_data:
        return None
    lo, hi = spot - oi_range, spot + oi_range
    strikes = []
    total_call_oi = total_put_oi = 0

    for row in chain_data:
        if not isinstance(row, dict):
            continue
        strike = row.get("strike_price", 0)
        if not (lo <= strike <= hi):
            continue
        cmd = (row.get("call_options") or {}).get("market_data") or {}
        pmd = (row.get("put_options")  or {}).get("market_data") or {}
        c_oi  = cmd.get("oi", 0) or 0
        p_oi  = pmd.get("oi", 0) or 0
        c_doi = cmd.get("change_in_oi", 0) or 0
        p_doi = pmd.get("change_in_oi", 0) or 0
        c_ltp = cmd.get("ltp", 0) or 0
        p_ltp = pmd.get("ltp", 0) or 0
        total_call_oi += c_oi
        total_put_oi  += p_oi
        strikes.append({
            "strike": strike, "call_oi": c_oi, "put_oi": p_oi,
            "call_doi": c_doi, "put_doi": p_doi,
            "call_ltp": c_ltp, "put_ltp": p_ltp,
            "pcr": round(p_oi / max(c_oi, 1), 3),
        })

    if not strikes:
        return None
    strikes.sort(key=lambda x: x["strike"])

    # Max Pain
    def mp_loss(target):
        return sum(
            s["call_oi"] * max(target - s["strike"], 0) +
            s["put_oi"]  * max(s["strike"] - target, 0)
            for s in strikes
        )
    max_pain = min(strikes, key=lambda s: mp_loss(s["strike"]))["strike"]
    total_pcr = round(total_put_oi / max(total_call_oi, 1), 3)

    return {
        "strikes": strikes, "max_pain": max_pain,
        "total_call_oi": total_call_oi, "total_put_oi": total_put_oi,
        "total_pcr": total_pcr,
    }

def calculate_buildup(chg_pct, oi_chg_pct):
    """LBU/SBU/LUW/SCV buildup classification."""
    if chg_pct >= 0 and oi_chg_pct >= 0:  return "LBU", "bold green",  "Long Buildup"
    if chg_pct  < 0 and oi_chg_pct >= 0:  return "SBU", "bold red",    "Short Buildup"
    if chg_pct  < 0 and oi_chg_pct  < 0:  return "LUW", "dim yellow",  "Long Unwinding"
    return                                        "SCV", "bold cyan",   "Short Covering"

def process_option_chain(chain_data, spot):
    """ATM ±5 rows, walls, volume spurts, IV squeeze."""
    empty = {"visible_rows": [], "walls": {}, "fo_alerts": {"volume_spurts": [], "iv_squeeze": ""}}
    if not chain_data:
        return empty

    chain_data.sort(key=lambda x: x.get("strike_price", 0))
    closest   = min(chain_data, key=lambda x: abs(x.get("strike_price", 0) - spot))
    atm_strike = closest.get("strike_price", spot)
    atm_idx    = next((i for i, r in enumerate(chain_data) if r.get("strike_price") == atm_strike), 0)

    s_idx, e_idx = max(0, atm_idx - 5), min(len(chain_data), atm_idx + 6)
    visible_rows = [
        {"strike": r.get("strike_price"), "call": r.get("call_options"), "put": r.get("put_options")}
        for r in chain_data[s_idx:e_idx]
    ]

    res_strike = res_oi = res_oi_chg = None
    sup_strike = sup_oi = sup_oi_chg = None
    res_oi = sup_oi = 0
    volume_spurts = []

    for row in chain_data:
        strike = row.get("strike_price", 0.0)
        ce = row.get("call_options")
        if ce:
            md  = ce.get("market_data", {})
            oi  = md.get("oi", 0.0)
            if oi > res_oi:
                res_oi = oi; res_strike = strike
                prev = md.get("prev_oi", 0.0)
                res_oi_chg = ((oi - prev) / prev * 100) if prev > 0 else 0.0
            vol = md.get("volume", 0.0)
            if oi > 0 and vol / oi > 10.0:
                ltp = md.get("ltp", 0.0); cl = md.get("close_price", 0.0) or ltp or 1.0
                volume_spurts.append({"strike": strike, "type": "CE",
                                      "vol_oi": vol / oi, "ltp": ltp, "chg": ((ltp - cl) / cl) * 100})
        pe = row.get("put_options")
        if pe:
            md  = pe.get("market_data", {})
            oi  = md.get("oi", 0.0)
            if oi > sup_oi:
                sup_oi = oi; sup_strike = strike
                prev = md.get("prev_oi", 0.0)
                sup_oi_chg = ((oi - prev) / prev * 100) if prev > 0 else 0.0
            vol = md.get("volume", 0.0)
            if oi > 0 and vol / oi > 10.0:
                ltp = md.get("ltp", 0.0); cl = md.get("close_price", 0.0) or ltp or 1.0
                volume_spurts.append({"strike": strike, "type": "PE",
                                      "vol_oi": vol / oi, "ltp": ltp, "chg": ((ltp - cl) / cl) * 100})

    volume_spurts.sort(key=lambda x: x["vol_oi"], reverse=True)

    # ATM IV squeeze detection
    ce_iv = (closest.get("call_options") or {}).get("option_greeks", {}).get("iv", 0.0)
    pe_iv = (closest.get("put_options")  or {}).get("option_greeks", {}).get("iv", 0.0)
    if ce_iv < 1.0: ce_iv *= 100
    if pe_iv < 1.0: pe_iv *= 100
    iv_squeeze = ""
    if ce_iv > 0 and pe_iv > 0:
        iv_squeeze = f"CE IV: {ce_iv:.1f}%  PE IV: {pe_iv:.1f}%"
        if ce_iv < 11.0 and pe_iv < 11.0:
            iv_squeeze += "  ⚡ CRITICAL SQUEEZE"

    return {
        "visible_rows": visible_rows,
        "walls": {
            "resistance_strike": res_strike, "resistance_oi": res_oi, "resistance_oi_chg": res_oi_chg,
            "support_strike":    sup_strike, "support_oi":    sup_oi, "support_oi_chg":    sup_oi_chg,
        },
        "fo_alerts": {"volume_spurts": volume_spurts, "iv_squeeze": iv_squeeze},
    }

# ── 10-Factor Signal Engine ───────────────────────────────────────────────────
def _sig_color(sc, fa):
    r = sc / max(fa, 1)
    if r >=  0.35: return "BUY",     "green"
    if r <= -0.35: return "SELL",    "red"
    return              "NEUTRAL", "yellow"

def run_analyze(sym, quote, candles, oi_summary, macro):
    """
    10 factors → BUY / SELL / NEUTRAL signal with score /10.
    Returns {"indicators": {...}, "signal": str, "signal_color": str, "score": int}
    """
    res = {}; sc = fa = 0
    c   = candles or []
    ltp = (quote or {}).get("ltp", 0)

    # 1. TREND
    if len(c) >= 20:
        lb, s, dt = _trend(c)
        res["TREND"] = {"label": lb, "score": s, "detail": dt}
        sc += s; fa += 2
    else:
        res["TREND"] = {"label": "N/A", "score": 0, "detail": f"{len(c)} bars"}

    # 2. DOW JONES
    u = macro.get("US30")
    if u:
        ch = u["change_pct"]
        s  = 1 if ch > 0.3 else (-1 if ch < -0.3 else 0)
        lb = "BULLISH" if s > 0 else ("BEARISH" if s < 0 else "FLAT")
        res["DOW"] = {"label": f"{lb} ({ch:+.2f}%)", "score": s, "detail": f"DJIA:{u['ltp']:,.0f}"}
        sc += s; fa += 1
    else:
        res["DOW"] = {"label": "N/A", "score": 0, "detail": "Unavailable"}

    # 3. INDIA VIX
    v = macro.get("VIX")
    if v:
        vv = v["ltp"]
        if vv < 13:    s, lb = 1,  f"LOW ({vv:.2f})"
        elif vv <= 17: s, lb = 1,  f"NORMAL ({vv:.2f})"
        elif vv <= 21: s, lb = 0,  f"ELEVATED ({vv:.2f})"
        else:          s, lb = -1, f"HIGH ({vv:.2f}) ⚠"
        res["VIX"] = {"label": lb, "score": s, "detail": f"Chg:{v.get('change_pct',0):+.2f}%"}
        sc += s; fa += 1
    else:
        res["VIX"] = {"label": "N/A", "score": 0, "detail": "Unavailable"}

    # 4. OI SKEW
    if oi_summary:
        tc, tp = oi_summary["total_call_oi"], oi_summary["total_put_oi"]
        r = tc / max(tp, 1)
        if r > 1.3:    s, lb = -1, "CALL HEAVY"
        elif r > 1.1:  s, lb = -1, "MILD CALL HVY"
        elif r < 0.7:  s, lb =  1, "PUT HEAVY"
        elif r < 0.9:  s, lb =  1, "MILD PUT HVY"
        else:          s, lb =  0, "BALANCED OI"
        res["OI"] = {"label": lb, "score": s, "detail": f"C:{tc/1e5:.1f}L P:{tp/1e5:.1f}L"}
        sc += s; fa += 1
    else:
        res["OI"] = {"label": "N/A", "score": 0, "detail": "No OI data"}

    # 5. VWAP
    if c and ltp:
        vw = _vwap(c)
        if vw:
            dp = (ltp - vw) / vw * 100
            if ltp > vw * 1.002:   s, lb = 1,  f"ABOVE (+{dp:.2f}%)"
            elif ltp < vw * 0.998: s, lb = -1, f"BELOW ({dp:.2f}%)"
            else:                  s, lb = 0,  "AT VWAP"
            res["VWAP"] = {"label": lb, "score": s, "detail": f"VWAP:{vw:,.0f}"}
            sc += s; fa += 1
        else:
            res["VWAP"] = {"label": "N/A", "score": 0, "detail": "No volume"}
    else:
        res["VWAP"] = {"label": "N/A", "score": 0, "detail": "No candles"}

    # 6. SUPERTREND
    if len(c) >= 12:
        stv, std = _supertrend(c)
        if std == 1:    lb = f"BULLISH ({stv:,.0f})" if stv else "BULLISH"
        elif std == -1: lb = f"BEARISH ({stv:,.0f})" if stv else "BEARISH"
        else:           lb = "NEUTRAL"
        res["S-TREND"] = {"label": lb, "score": std, "detail": "ATR(10)×3"}
        sc += std; fa += 1
    else:
        res["S-TREND"] = {"label": "N/A", "score": 0, "detail": "Need ≥12 bars"}

    # 7. RSI
    if len(c) >= 16:
        rv = _rsi([x[4] for x in c])
        if rv >= 75:    s, lb = -1, f"OVERBOUGHT ({rv:.0f})"
        elif rv >= 60:  s, lb =  1, f"BULLISH ({rv:.0f})"
        elif rv <= 25:  s, lb =  1, f"OVERSOLD ({rv:.0f})"
        elif rv <= 40:  s, lb = -1, f"BEARISH ({rv:.0f})"
        else:           s, lb =  0, f"NEUTRAL ({rv:.0f})"
        res["RSI"] = {"label": lb, "score": s, "detail": "RSI(14) Daily"}
        sc += s; fa += 1
    else:
        res["RSI"] = {"label": "N/A", "score": 0, "detail": "Need ≥16 bars"}

    # 8. DXY
    dx = macro.get("DXY")
    if dx:
        ch = dx["change_pct"]
        if ch > 0.5:    s, lb = -1, f"SURGING ({ch:+.2f}%)"
        elif ch > 0.2:  s, lb = -1, f"STRENGTHEN ({ch:+.2f}%)"
        elif ch < -0.5: s, lb =  1, f"WEAKENING ({ch:+.2f}%)"
        elif ch < -0.2: s, lb =  1, f"SOFTENING ({ch:+.2f}%)"
        else:           s, lb =  0, f"STABLE ({ch:+.2f}%)"
        res["DXY"] = {"label": lb, "score": s, "detail": f"DXY:{dx['ltp']:.2f}"}
        sc += s; fa += 1
    else:
        res["DXY"] = {"label": "N/A", "score": 0, "detail": "Unavailable"}

    # 9. CRUDE OIL
    cr = macro.get("CRUDE")
    if cr:
        ch = cr["change_pct"]
        if ch > 2.0:    s, lb = -1, f"SURGING ({ch:+.2f}%)"
        elif ch > 0.8:  s, lb = -1, f"RISING ({ch:+.2f}%)"
        elif ch < -2.0: s, lb =  1, f"CRASHING ({ch:+.2f}%)"
        elif ch < -0.8: s, lb =  1, f"FALLING ({ch:+.2f}%)"
        else:           s, lb =  0, f"STABLE ({ch:+.2f}%)"
        res["CRUDE"] = {"label": lb, "score": s, "detail": f"WTI:${cr['ltp']:.1f}"}
        sc += s; fa += 1
    else:
        res["CRUDE"] = {"label": "N/A", "score": 0, "detail": "Unavailable"}

    # 10. PCR
    if oi_summary:
        pcr = oi_summary["total_pcr"]
        mp  = oi_summary["max_pain"]
        if pcr > 1.3:    s, lb = 1,  f"BULLISH PCR {pcr:.2f}"
        elif pcr > 1.1:  s, lb = 1,  f"MILD BULL {pcr:.2f}"
        elif pcr < 0.7:  s, lb = -1, f"BEARISH PCR {pcr:.2f}"
        elif pcr < 0.9:  s, lb = -1, f"MILD BEAR {pcr:.2f}"
        else:            s, lb = 0,  f"NEUTRAL {pcr:.2f}"
        res["PCR"] = {"label": lb, "score": s, "detail": f"MaxPain:{mp:,.0f}"}
        sc += s; fa += 1
    else:
        res["PCR"] = {"label": "N/A", "score": 0, "detail": "Need chain"}

    signal, sig_clr = _sig_color(sc, fa)
    return {
        "indicators": res,
        "signal":     signal,
        "signal_color": sig_clr,
        "score":      min(abs(sc), 10),
        "raw_score":  sc,
        "factors":    fa,
    }

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_oi(v):
    if not v: return "—"
    l = v / 100_000
    return f"{l:,.0f}L" if l >= 100 else f"{l:.1f}L"

def days_to_expiry(expiry_str):
    try:
        exp = datetime.datetime.strptime(expiry_str, "%Y-%m-%d").date()
        return (exp - datetime.date.today()).days
    except Exception:
        return "?"

# ── Layout Construction ───────────────────────────────────────────────────────
def make_layout(mode="unified") -> Layout:
    layout = Layout()
    if mode == "classic":
        layout.split_column(
            Layout(name="header",  size=5),
            Layout(name="body",    ratio=1),
            Layout(name="footer",  size=11),
        )
        layout["body"].split_row(
            Layout(name="indicators_panel",     ratio=3),
            Layout(name="classic_option_chain", ratio=6),
            Layout(name="classic_intel",        ratio=3),
        )
    elif mode == "breakout":
        layout.split_column(
            Layout(name="header",  size=5),
            Layout(name="body",    ratio=1),
            Layout(name="intel",   size=11),
        )
        layout["body"].split_row(
            Layout(name="calls_panel",   ratio=1),
            Layout(name="strikes_panel", size=14),
            Layout(name="puts_panel",    ratio=1),
        )
        layout["intel"].split_row(
            Layout(name="indicators_panel", ratio=3),
            Layout(name="walls_panel",      ratio=2),
            Layout(name="alerts_panel",     ratio=2),
        )
    else:  # unified
        layout.split_column(
            Layout(name="header",  size=5),
            Layout(name="body",    ratio=1),
            Layout(name="intel",   size=11),
        )
        layout["body"].split_row(
            Layout(name="breakout_section", ratio=3),
            Layout(name="classic_section",  ratio=2),
        )
        layout["breakout_section"].split_row(
            Layout(name="calls_panel",   ratio=1),
            Layout(name="strikes_panel", size=14),
            Layout(name="puts_panel",    ratio=1),
        )
        layout["classic_section"].split_row(
            Layout(name="classic_option_chain", ratio=2),
            Layout(name="classic_intel",        ratio=1),
        )
        layout["intel"].split_row(
            Layout(name="indicators_panel",  ratio=3),
            Layout(name="trending_oi_panel", ratio=5),
            Layout(name="walls_panel",       ratio=4),
            Layout(name="alerts_panel",      ratio=3),
        )
    return layout


# ── Render: Header ────────────────────────────────────────────────────────────
def render_header(state) -> Panel:
    now     = datetime.datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    idx     = state["active_idx"]
    spot    = state["spots"].get(idx, 0.0)
    chg     = state["spots_chg"].get(idx, 0.0)
    cc      = "green" if chg >= 0 else "red"

    # Futures
    fq      = state.get("futures_quote")
    fut_str = ""
    if fq:
        fc = fq.get("change_pct", 0.0)
        fc_c = "green" if fc >= 0 else "red"
        fut_str = f"  │  Fut: [{fc_c}]{fq['ltp']:,.2f} ({fc:+.2f}%)[/{fc_c}]"

    # Expiry + DTE
    expiry  = state.get("current_expiry")
    exp_str = f"Exp: [bold magenta]{expiry}[/] [dim]({days_to_expiry(expiry)}d)[/]" if expiry else "Exp: [dim]---[/]"

    # VIX from macro
    vix_d   = state.get("macro", {}).get("VIX")
    vix_str = f"VIX: [bold white]{vix_d['ltp']:.2f}[/]" if vix_d else "VIX: [dim]---[/]"

    # Signal + score bar
    sig     = state.get("signal", "---")
    sc      = state.get("signal_score", 0)
    sig_c   = {"BUY": "green", "SELL": "red", "NEUTRAL": "yellow"}.get(sig, "dim white")
    filled  = round(sc / 10 * 8) if sc else 0
    bar     = f"[{sig_c}]{'█' * filled}[/][dim]{'░' * (8 - filled)}[/]"

    # Refresh timer
    poll_iv = state.get("poll_interval", POLL_INTERVAL)
    last_r  = state.get("last_refreshed")
    if last_r:
        elapsed  = (now - last_r).total_seconds()
        next_in  = max(0, poll_iv - elapsed)
        last_str = last_r.strftime("%H:%M:%S")
        rc       = "green" if next_in > 3 else ("yellow" if next_in > 1 else "bold red")
        ref_str  = f"Last: [dim]{last_str}[/]  Next: [{rc}]{next_in:.0f}s[/{rc}]"
    else:
        ref_str  = "[dim]Fetching...[/]"

    status  = state.get("status", "")
    st_str  = "[bold green]● LIVE[/]" if "error" not in status.lower() else f"[bold red]● {status[:35]}[/]"

    line1 = (
        f"[bold cyan]⚡ AlphaEdge Pro[/]  │  "
        f"[bold yellow]{idx}[/]: [bold white]{spot:,.2f}[/] [{cc}]({chg:+.2f}%)[/{cc}]{fut_str}"
        f"  │  {exp_str}  │  {vix_str}"
        f"  │  Signal: [{sig_c}]{sig}[/{sig_c}] {bar} ({sc}/10)"
    )
    line2 = (
        f"[dim]{now_str}[/]  │  "
        f"[dim]Poll: {poll_iv}s[/]  │  {ref_str}  │  {st_str}"
    )

    return Panel(
        Align.center(Text.from_markup(f"{line1}\n{line2}"), vertical="middle"),
        style="cyan", box=box.ROUNDED,
    )

# ── Render: Option Chain Panels ───────────────────────────────────────────────
def render_chains(state, side) -> Panel:
    border = "cyan" if side == "CALLS" else "magenta"
    hdr_st = "bold cyan" if side == "CALLS" else "bold magenta"
    table  = Table(show_header=True, header_style=hdr_st, box=box.SIMPLE,
                   expand=True, padding=(0, 1))

    if side == "CALLS":
        table.add_column("BUILD", justify="center")
        table.add_column("Δ",     justify="right",  style="dim")
        table.add_column("IV",    justify="right",  style="dim")
        table.add_column("V/OI",  justify="right",  style="dim")
        table.add_column("OI CHG",justify="right")
        table.add_column("OI",    justify="right")
        table.add_column("LTP",   justify="right")
    else:
        table.add_column("LTP",   justify="left")
        table.add_column("OI",    justify="left")
        table.add_column("OI CHG",justify="left")
        table.add_column("V/OI",  justify="left",   style="dim")
        table.add_column("IV",    justify="left",   style="dim")
        table.add_column("Δ",     justify="left",   style="dim")
        table.add_column("BUILD", justify="center")

    rows = state.get("visible_rows", [])
    if not rows:
        return Panel(
            Align.center("[dim]No option chain data[/]", vertical="middle"),
            title=f"[bold {border}]{'CALL OPTIONS (CE)' if side == 'CALLS' else 'PUT OPTIONS (PE)'}[/]",
            border_style=border,
        )

    for r in rows:
        opt = r["call"] if side == "CALLS" else r["put"]
        if not opt:
            table.add_row(*["—"] * 7)
            continue
        md  = opt.get("market_data", {})
        gr  = opt.get("option_greeks", {})
        ltp = md.get("ltp", 0.0)
        cl  = md.get("close_price", 0.0) or ltp or 1.0
        chg_p   = ((ltp - cl) / cl) * 100
        oi      = md.get("oi", 0.0)
        prev_oi = md.get("prev_oi", 0.0) or oi or 1.0
        oi_chg  = ((oi - prev_oi) / prev_oi) * 100
        vol     = md.get("volume", 0.0)
        vol_oi  = vol / oi if oi > 0 else 0.0
        iv      = gr.get("iv", 0.0)
        if iv < 1.0: iv *= 100
        delta   = gr.get("delta", 0.0)

        b_code, b_color, _ = calculate_buildup(chg_p, oi_chg)
        pc  = "green" if chg_p >= 0 else "red"
        oc  = "green" if oi_chg >= 0 else "red"
        vc  = "yellow" if vol_oi > 10 else "dim white"

        cells = [
            f"[{b_color}]{b_code}[/]",
            f"{delta:+.2f}",
            f"{iv:.1f}%",
            f"[{vc}]{vol_oi:.1f}x[/]",
            f"[{oc}]{oi_chg:+.1f}%[/]",
            fmt_oi(oi),
            f"[bold {pc}]{ltp:,.1f}[/] [dim]({chg_p:+.1f}%)[/]",
        ]
        table.add_row(*cells) if side == "CALLS" else table.add_row(*reversed(cells))

    title = "[bold cyan]CALL OPTIONS (CE)[/]" if side == "CALLS" else "[bold magenta]PUT OPTIONS (PE)[/]"
    return Panel(table, title=title, border_style=border)

def render_strikes(state) -> Panel:
    table = Table(show_header=True, header_style="bold yellow",
                  box=box.SIMPLE, expand=True, padding=(0, 0))
    table.add_column("STRIKE", justify="center")

    rows = state.get("visible_rows", [])
    if not rows:
        return Panel(Align.center("[dim]---[/]", vertical="middle"), border_style="yellow")

    spot      = state["spots"].get(state["active_idx"], 0.0)
    oi_sum    = state.get("oi_summary") or {}
    max_pain  = oi_sum.get("max_pain")
    # ATM proximity: NIFTY 50 strikes are 50pt apart, BANK/SENSEX 100pt
    atm_tol   = 26 if "BANK" not in state["active_idx"] and "SENSEX" not in state["active_idx"] else 51

    for r in rows:
        k      = r["strike"]
        is_atm = abs(k - spot) < atm_tol
        is_mp  = max_pain is not None and abs(k - max_pain) < 1
        label  = f"[bold reverse yellow] {k:,.0f} [/]" if is_atm else f"[bold white]{k:,.0f}[/]"
        if is_mp:
            label += " [magenta]MP[/]"
        table.add_row(label)

    return Panel(table, title="[bold yellow]STRIKE[/]", border_style="yellow")

# ── Render: Intel Bar ─────────────────────────────────────────────────────────
def render_indicators(state) -> Panel:
    """Condensed 10-factor signal table."""
    indicators = state.get("indicators", {})
    signal     = state.get("signal", "---")
    score      = state.get("signal_score", 0)
    sig_c      = {"BUY": "green", "SELL": "red", "NEUTRAL": "yellow"}.get(signal, "dim white")

    t = Table(box=None, show_header=True, header_style="bold dim",
              padding=(0, 1), expand=True)
    t.add_column("IND",    style="dim cyan", width=8)
    t.add_column("STATUS", ratio=1)
    t.add_column("S",      justify="center", width=3)

    sc_clr = {2: "bold green", 1: "green", 0: "yellow", -1: "red", -2: "bold red"}

    if not indicators:
        t.add_row("[dim]Calculating...[/]", "", "")
    else:
        for k, v in indicators.items():
            s    = v["score"]
            s_str = f"[{sc_clr.get(s, 'white')}]{s:+d}[/]"
            t.add_row(k, v["label"][:24], s_str)

    title = f"[bold cyan]10-Factor Signals  [{sig_c}]{signal} {score}/10[/{sig_c}][/]"
    return Panel(t, title=title, border_style="cyan", padding=(0, 0))


def render_walls(state) -> Panel:
    """OI walls + PCR + Max Pain + trailing intraday OI rows."""
    items  = []
    walls  = state.get("walls", {})
    oi_sum = state.get("oi_summary") or {}
    spot   = state["spots"].get(state["active_idx"], 0.0)
    mode   = state.get("mode", "unified")

    # Resistance wall
    rs = walls.get("resistance_strike")
    ro = walls.get("resistance_oi", 0)
    if rs and spot > 0:
        dist = ((rs - spot) / spot) * 100
        dc   = "bold red" if abs(dist) < 0.5 else "yellow"
        oi_chg = walls.get("resistance_oi_chg", 0) or 0
        squeeze = "  ⚡[blink bold red]SQUEEZE[/]" if abs(dist) < 0.25 and oi_chg < 0 else \
                  "  ⚠[bold yellow]NEAR[/]"         if abs(dist) < 0.25 else ""
        items.append(f"[red]▲ RESIST[/]  [white]{rs:,.0f}[/]  OI:[white]{fmt_oi(ro)}[/]  [{dc}]{dist:+.2f}%[/]{squeeze}")
    else:
        items.append("[red]▲ RESIST[/]  [dim]Scanning...[/]")

    # Support wall
    ss = walls.get("support_strike")
    so = walls.get("support_oi", 0)
    if ss and spot > 0:
        dist = ((ss - spot) / spot) * 100
        dc   = "bold green" if abs(dist) < 0.5 else "yellow"
        oi_chg = walls.get("support_oi_chg", 0) or 0
        squeeze = "  ⚡[blink bold green]SQUEEZE[/]" if abs(dist) < 0.25 and oi_chg < 0 else \
                  "  ⚠[bold yellow]NEAR[/]"           if abs(dist) < 0.25 else ""
        items.append(f"[green]▼ SUPPORT[/] [white]{ss:,.0f}[/]  OI:[white]{fmt_oi(so)}[/]  [{dc}]{dist:+.2f}%[/]{squeeze}")
    else:
        items.append("[green]▼ SUPPORT[/] [dim]Scanning...[/]")

    # PCR + Max Pain
    if oi_sum:
        pcr = oi_sum.get("total_pcr", 0)
        mp  = oi_sum.get("max_pain", 0)
        pc  = "green" if pcr >= 1.0 else ("yellow" if pcr >= 0.7 else "red")
        items.append(f"PCR: [{pc}]{pcr:.2f}[/]  │  MaxPain: [magenta]{mp:,.0f}[/]")

    if mode == "unified":
        if oi_sum:
            tc, tp = oi_sum.get("total_call_oi", 0), oi_sum.get("total_put_oi", 0)
            chg_p  = state["spots_chg"].get(state["active_idx"], 0.0)
            total_oi_chg = sum(s.get("call_doi", 0) + s.get("put_doi", 0) for s in oi_sum.get("strikes", []))
            if chg_p > 0 and total_oi_chg > 0:   buildup, b_clr = "Long Buildup", "bold green"
            elif chg_p > 0 and total_oi_chg < 0: buildup, b_clr = "Short Covering", "bold cyan"
            elif chg_p < 0 and total_oi_chg > 0: buildup, b_clr = "Short Buildup", "bold red"
            elif chg_p < 0 and total_oi_chg < 0: buildup, b_clr = "Long Unwinding", "dim yellow"
            else:                                buildup, b_clr = "Neutral", "dim white"
            
            items.append(Rule(style="dim"))
            items.append(f"Calls OI: [green]{fmt_oi(tc)}[/green]  │  Puts OI: [red]{fmt_oi(tp)}[/red]")
            items.append(f"OI Build: [{b_clr}]{buildup}[/{b_clr}]")
    else:
        # Intraday OI trail (SQLite — last 4 rows)
        toi = state.get("trending_oi", [])
        if toi:
            items.append(Rule(style="dim"))
            items.append("[dim]Time   LTP        C.OI     P.OI[/]")
            for row in toi[:4]:
                ts, ltp, c_oi, p_oi = row
                diff = p_oi - c_oi
                sc   = "green" if diff > 0 else "red"
                items.append(
                    f"[dim]{ts.split(' ')[1][:5]}[/]  "
                    f"[white]{ltp:>9,.0f}[/]  "
                    f"[{sc}]{fmt_oi(c_oi)}[/]  [{sc}]{fmt_oi(p_oi)}[/]"
                )

    return Panel(Group(*items), title="[bold yellow]OI Walls & Intelligence[/]",
                 border_style="yellow", padding=(0, 1))


def render_alerts(state) -> Panel:
    """Volume spurts + IV squeeze + macro summary (DXY / Crude / Dow)."""
    items    = []
    fo_alerts = state.get("fo_alerts", {})

    # Volume spurts
    spurts = fo_alerts.get("volume_spurts", [])
    if spurts:
        for s in spurts[:2]:
            cc = "green" if s["chg"] >= 0 else "red"
            items.append(
                f"[yellow]⚡ SPURT[/]  [white]{s['strike']} {s['type']}[/]  "
                f"LTP:[{cc}]{s['ltp']:.1f}[/]  V/OI:[magenta]{s['vol_oi']:.1f}x[/]"
            )
    else:
        items.append("[dim]No volume spurts detected[/]")

    # IV squeeze
    iv_sq = fo_alerts.get("iv_squeeze", "")
    if iv_sq:
        items.append(Rule(style="dim"))
        items.append(f"[cyan]IV Squeeze:[/]  {iv_sq}")

    # Macro panel
    macro = state.get("macro", {})
    if macro:
        items.append(Rule(style="dim"))
        dx = macro.get("DXY")
        cr = macro.get("CRUDE")
        us = macro.get("US30")
        if dx:
            dc = "red" if dx["change_pct"] > 0.2 else ("green" if dx["change_pct"] < -0.2 else "dim white")
            items.append(f"DXY   [{dc}]{dx['ltp']:.2f}  ({dx['change_pct']:+.2f}%)[/]")
        if cr:
            cc = "red" if cr["change_pct"] > 0.8 else ("green" if cr["change_pct"] < -0.8 else "dim white")
            items.append(f"WTI   [{cc}]${cr['ltp']:.1f}  ({cr['change_pct']:+.2f}%)[/]")
        if us:
            uc = "green" if us["change_pct"] >= 0 else "red"
            items.append(f"DOW   [{uc}]{us['ltp']:,.0f}  ({us['change_pct']:+.2f}%)[/]")
    else:
        items.append(Rule(style="dim"))
        items.append("[dim]Macro data loading...[/]")

    return Panel(Group(*items), title="[bold magenta]Alerts & Macro[/]",
                 border_style="magenta", padding=(0, 1))


# ── Classic Render Panels ─────────────────────────────────────────────────────
def render_classic_option_chain(state) -> Panel:
    """Classic combined option chain table: C.LTP | C.OI | STRIKE | P.OI | P.LTP."""
    oi_sum = state.get("oi_summary")
    spot   = state["spots"].get(state["active_idx"], 0.0)
    if not oi_sum or not spot:
        return Panel(
            Align.center("[dim]Option chain unavailable[/]", vertical="middle"),
            title="[bold yellow]Classic Option Chain[/]",
            border_style="yellow",
        )

    expiry  = state.get("current_expiry", "?")
    dte     = days_to_expiry(expiry)
    strikes = oi_sum.get("strikes", [])
    max_p   = oi_sum.get("max_pain", 0)
    lo, hi  = spot - 500, spot + 500
    visible = [s for s in strikes if lo <= s["strike"] <= hi] or strikes

    oc_table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold yellow",
                     expand=True, padding=(0, 1))
    oc_table.add_column("C.LTP",  justify="right", style="green")
    oc_table.add_column("C.OI",   justify="right", style="green")
    oc_table.add_column("STRIKE", justify="center", style="bold white")
    oc_table.add_column("P.OI",   justify="right", style="red")
    oc_table.add_column("P.LTP",  justify="right", style="red")

    # ATM proximity: NIFTY 50 strikes are 50pt apart, BANK/SENSEX 100pt
    atm_tol = 26 if "BANK" not in state["active_idx"] and "SENSEX" not in state["active_idx"] else 51

    for s in visible:
        k = s["strike"]
        is_atm = abs(k - spot) < atm_tol
        is_mp  = abs(k - max_p) < 1

        c_ltp = f"{s['call_ltp']:.1f}" if s['call_ltp'] else "—"
        c_oi  = fmt_oi(s['call_oi'])
        p_ltp = f"{s['put_ltp']:.1f}" if s['put_ltp'] else "—"
        p_oi  = fmt_oi(s['put_oi'])

        strike_str = f"[bold reverse yellow] {k:,.0f} [/]" if is_atm else f"{k:,.0f}"
        if is_mp:
            strike_str += " [magenta]MP[/]"

        oc_table.add_row(c_ltp, c_oi, strike_str, p_oi, p_ltp)

    title = f"[bold yellow]Option Chain — Exp: {expiry} (DTE: {dte}d) | MP: {max_p:,.0f}[/]"
    return Panel(oc_table, title=title, border_style="yellow")


def render_classic_trending_oi(state) -> Panel:
    """Beautiful intraday trending OI table from market_analysis_v3.py."""
    toi = state.get("trending_oi", [])
    if not toi:
        return Panel(
            Align.center("[dim]Waiting for SQLite intraday snapshots...[/]", vertical="middle"),
            title="[bold cyan]Trending OI (Intraday)[/]",
            border_style="cyan",
        )

    t = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold cyan",
              expand=True, padding=(0, 1))
    t.add_column("Time",      justify="center")
    t.add_column("LTP",       justify="right")
    t.add_column("ΔCall OI",  justify="right")
    t.add_column("ΔPut OI",   justify="right")
    t.add_column("Diff",      justify="right")
    t.add_column("PCR",       justify="right")
    t.add_column("Sentiment", justify="center")

    base_c, base_p = toi[-1][2], toi[-1][3]
    for r in toi:
        ts, ltp, c_oi, p_oi = r
        d_c = c_oi - base_c
        d_p = p_oi - base_p
        diff = p_oi - c_oi
        pcr = p_oi / c_oi if c_oi > 0 else 0.0
        
        sent = "[green]Bullish[/green]" if diff > 0 else "[red]Bearish[/red]"
        dc_str = f"[green]{d_c:+,.0f}[/green]" if d_c > 0 else f"[red]{d_c:+,.0f}[/red]" if d_c < 0 else "[yellow]0[/yellow]"
        dp_str = f"[green]{d_p:+,.0f}[/green]" if d_p > 0 else f"[red]{d_p:+,.0f}[/red]" if d_p < 0 else "[yellow]0[/yellow]"
        diff_str = f"[green]{diff:+,.0f}[/green]" if diff > 0 else f"[red]{diff:+,.0f}[/red]" if diff < 0 else "[yellow]0[/yellow]"

        t.add_row(
            ts.split(" ")[1][:5],
            f"{ltp:,.2f}",
            dc_str,
            dp_str,
            diff_str,
            f"{pcr:.2f}",
            sent
        )

    return Panel(t, title="[bold cyan]Trending OI (Intraday Snapshots)[/]", border_style="cyan")


def render_classic_intel(state) -> Panel:
    """Classic compact Intelligence Panel."""
    oi_sum = state.get("oi_summary")
    spot   = state["spots"].get(state["active_idx"], 0.0)
    chg_p  = state["spots_chg"].get(state["active_idx"], 0.0)
    
    intel = Table(box=None, show_header=False, padding=(0, 1), expand=True)
    intel.add_column("L", justify="left",  style="cyan")
    intel.add_column("V", justify="right", style="white")

    if oi_sum and spot > 0:
        total_pcr = oi_sum.get("total_pcr", 0.0)
        max_pain  = oi_sum.get("max_pain", 0.0)
        total_c_oi = oi_sum.get("total_call_oi", 0.0)
        total_p_oi = oi_sum.get("total_put_oi", 0.0)
        
        # Calculate buildup
        total_oi_chg = sum(s.get("call_doi", 0) + s.get("put_doi", 0) for s in oi_sum.get("strikes", []))
        if chg_p > 0 and total_oi_chg > 0:   buildup = "[green]Long Buildup[/green]"
        elif chg_p > 0 and total_oi_chg < 0: buildup = "[cyan]Short Covering[/cyan]"
        elif chg_p < 0 and total_oi_chg > 0: buildup = "[red]Short Buildup[/red]"
        elif chg_p < 0 and total_oi_chg < 0: buildup = "[yellow]Long Unwinding[/yellow]"
        else:                                buildup = "[dim]Neutral[/dim]"

        pcr_color = "green" if total_pcr >= 1.0 else "yellow" if total_pcr >= 0.7 else "red"
        
        walls = state.get("walls", {})
        res_strike = walls.get("resistance_strike", 0.0)
        sup_strike = walls.get("support_strike", 0.0)

        intel.add_row("PCR", f"[{pcr_color}]{total_pcr:.2f}[/{pcr_color}]")
        intel.add_row("Max Pain", f"[magenta]{max_pain:,.0f}[/magenta]")
        intel.add_row("OI Build", buildup)
        intel.add_row("Calls OI", f"[green]{fmt_oi(total_c_oi)}[/green]")
        intel.add_row("Puts OI", f"[red]{fmt_oi(total_p_oi)}[/red]")
        intel.add_row("Resistance", f"[red]{res_strike:,.0f}[/red]" if res_strike else "[dim]—[/dim]")
        intel.add_row("Support", f"[green]{sup_strike:,.0f}[/green]" if sup_strike else "[dim]—[/dim]")
    else:
        intel.add_row("[dim]Scanning...[/]", "")

    return Panel(intel, title="[bold magenta]Intelligence[/]", border_style="magenta", padding=(0, 1))


# ── Async Data Loops ──────────────────────────────────────────────────────────
async def prefetch_state(state):
    """Warm all state before Live starts — ensures frame 1 has real data."""
    idx = state["active_idx"]
    key = INDICES[idx]
    sym = SYM_MAP[idx]

    async with aiohttp.ClientSession() as session:
        try:
            # Spot price
            q = await fetch_spot(session, key)
            if q:
                state["spots"][idx]     = q["ltp"]
                state["spots_chg"][idx] = q["change_pct"]
                state["status"]         = "OK"
            else:
                state["status"] = "Spot fetch failed at startup"
                return

            # Futures quote
            fq = await fetch_futures_quote(session, sym)
            if fq:
                state["futures_quote"] = fq

            # Option chain + processing
            expiries = await fetch_expiries(session, key)
            if expiries:
                state["current_expiry"] = expiries[0]
                chain_raw = await fetch_option_chain(session, key, expiries[0])
                spot = state["spots"][idx]
                if chain_raw and spot > 0:
                    processed            = process_option_chain(chain_raw, spot)
                    state["visible_rows"] = processed["visible_rows"]
                    state["walls"]        = processed["walls"]
                    state["fo_alerts"]    = processed["fo_alerts"]
                    state["oi_summary"]   = build_oi_summary(chain_raw, spot)

            # Historical candles (for technical indicators)
            candles = await fetch_candles(session, key)
            state["candles"] = candles

            # SQLite Intraday OI snapshot trail warm-up
            try:
                state["trending_oi"] = db_read_oi(sym, limit=15)
            except Exception:
                pass

            # Initial signal (macro will be empty until macro_loop runs)
            a = run_analyze(sym, q, candles, state.get("oi_summary"), state.get("macro", {}))
            state["indicators"]   = a["indicators"]
            state["signal"]       = a["signal"]
            state["signal_score"] = a["score"]

        except Exception as e:
            state["status"] = f"Prefetch error: {e}"


async def fast_data_loop(state):
    """Every POLL_INTERVAL s: spot + futures + option chain + signal refresh."""
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                idx = state["active_idx"]
                key = INDICES[idx]
                sym = SYM_MAP[idx]

                q = await fetch_spot(session, key)
                if q:
                    state["spots"][idx]     = q["ltp"]
                    state["spots_chg"][idx] = q["change_pct"]
                    state["status"]         = "OK"
                else:
                    state["status"] = "Spot fetch error"

                fq = await fetch_futures_quote(session, sym)
                if fq:
                    state["futures_quote"] = fq

                expiries = await fetch_expiries(session, key)
                if expiries:
                    state["current_expiry"] = expiries[0]
                    chain_raw = await fetch_option_chain(session, key, expiries[0])
                    spot = state["spots"].get(idx, 0.0)
                    if chain_raw and spot > 0:
                        processed            = process_option_chain(chain_raw, spot)
                        state["visible_rows"] = processed["visible_rows"]
                        state["walls"]        = processed["walls"]
                        state["fo_alerts"]    = processed["fo_alerts"]
                        state["oi_summary"]   = build_oi_summary(chain_raw, spot)

                # Refresh signal with latest OI + candles + macro
                a = run_analyze(sym, q, state.get("candles", []),
                                state.get("oi_summary"), state.get("macro", {}))
                state["indicators"]   = a["indicators"]
                state["signal"]       = a["signal"]
                state["signal_score"] = a["score"]

            except Exception as e:
                state["status"] = f"Data loop error: {e}"

            state["last_refreshed"] = datetime.datetime.now()
            await asyncio.sleep(POLL_INTERVAL)


async def macro_data_loop(state):
    """Every MACRO_INTERVAL s: Yahoo Finance — DXY, Crude, US30, VIX."""
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                macro = {}
                for k, sym in YAHOO_SYM.items():
                    d = await fetch_yahoo(session, sym, days=5)
                    if d:
                        macro[k] = d
                if macro:
                    state["macro"] = macro
            except Exception:
                pass  # Keep stale macro data on transient failure
            await asyncio.sleep(MACRO_INTERVAL)


async def candle_data_loop(state):
    """Every CANDLE_INTERVAL s: Upstox daily candles (for RSI/VWAP/SuperTrend)."""
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                key     = INDICES[state["active_idx"]]
                candles = await fetch_candles(session, key)
                if candles:
                    state["candles"] = candles
            except Exception:
                pass
            await asyncio.sleep(CANDLE_INTERVAL)


async def oi_db_loop(state):
    """Every DB_INTERVAL s: write OI snapshot to SQLite and read back for display."""
    while True:
        try:
            oi_sum = state.get("oi_summary")
            spot   = state["spots"].get(state["active_idx"], 0.0)
            sym    = SYM_MAP[state["active_idx"]]
            if oi_sum and spot > 0:
                db_write_oi(sym, spot, oi_sum["total_call_oi"], oi_sum["total_put_oi"])
            state["trending_oi"] = db_read_oi(sym, limit=15)
        except Exception:
            pass
        await asyncio.sleep(DB_INTERVAL)


# ── Main Dashboard ────────────────────────────────────────────────────────────
async def run_dashboard(selected_idx: str, mode: str):
    console = Console()
    layout  = make_layout(mode)

    state = {
        "active_idx":    selected_idx,
        "mode":          mode,
        "spots":         {selected_idx: 0.0},
        "spots_chg":     {selected_idx: 0.0},
        "futures_quote": None,
        "current_expiry": None,
        "visible_rows":  [],
        "walls":         {},
        "oi_summary":    None,
        "fo_alerts":     {"volume_spurts": [], "iv_squeeze": ""},
        "candles":       [],
        "macro":         {},
        "indicators":    {},
        "signal":        "---",
        "signal_score":  0,
        "trending_oi":   [],
        "last_refreshed": None,
        "poll_interval": POLL_INTERVAL,
        "status":        "Initializing...",
    }

    # ── Phase 1: Pre-fetch option chain + candles ──────────────────────────────
    console.print(
        f"\n[bold cyan]⚡ AlphaEdge Pro[/] — Warming up [bold yellow]{selected_idx}[/] ({mode.upper()} view)..."
    )
    console.print("[dim]  › Fetching spot price, option chain, historical candles...[/]")
    await prefetch_state(state)

    # ── Phase 2: Pre-fetch macro data (DXY / Crude / US30 / VIX) ──────────────
    console.print("[dim]  › Fetching macro data (DXY, Crude, US30, VIX)...[/]")
    try:
        async with aiohttp.ClientSession() as sess:
            macro = {}
            for k, sym in YAHOO_SYM.items():
                d = await fetch_yahoo(sess, sym, days=5)
                if d:
                    macro[k] = d
            state["macro"] = macro
    except Exception:
        pass

    # ── Phase 3: Re-run analysis with macro now loaded ─────────────────────────
    sym    = SYM_MAP[selected_idx]
    q_stub = {"ltp": state["spots"].get(selected_idx, 0),
              "change_pct": state["spots_chg"].get(selected_idx, 0)}
    a = run_analyze(sym, q_stub, state.get("candles", []),
                    state.get("oi_summary"), state.get("macro", {}))
    state["indicators"]   = a["indicators"]
    state["signal"]       = a["signal"]
    state["signal_score"] = a["score"]
    state["last_refreshed"] = datetime.datetime.now()

    console.print(
        f"[dim]  › Ready.  "
        f"Spot: {state['spots'].get(selected_idx, 0):,.2f}  "
        f"Signal: {state['signal']} ({state['signal_score']}/10)  "
        f"Chain rows: {len(state.get('visible_rows', []))}  "
        f"Macro: {len(state['macro'])} sources[/]\n"
    )

    # ── Start background async tasks ───────────────────────────────────────────
    asyncio.create_task(fast_data_loop(state))
    asyncio.create_task(macro_data_loop(state))
    asyncio.create_task(candle_data_loop(state))
    asyncio.create_task(oi_db_loop(state))

    # ── Live display ───────────────────────────────────────────────────────────
    with Live(layout, console=console, screen=True, refresh_per_second=2):
        while True:
            layout["header"].update(render_header(state))
            if mode == "classic":
                layout["indicators_panel"].update(render_indicators(state))
                layout["classic_option_chain"].update(render_classic_option_chain(state))
                layout["classic_intel"].update(render_classic_intel(state))
                layout["footer"].update(render_classic_trending_oi(state))
            elif mode == "breakout":
                layout["calls_panel"].update(render_chains(state, "CALLS"))
                layout["strikes_panel"].update(render_strikes(state))
                layout["puts_panel"].update(render_chains(state, "PUTS"))
                layout["indicators_panel"].update(render_indicators(state))
                layout["walls_panel"].update(render_walls(state))
                layout["alerts_panel"].update(render_alerts(state))
            else:  # unified
                layout["calls_panel"].update(render_chains(state, "CALLS"))
                layout["strikes_panel"].update(render_strikes(state))
                layout["puts_panel"].update(render_chains(state, "PUTS"))
                layout["classic_option_chain"].update(render_classic_option_chain(state))
                layout["classic_intel"].update(render_classic_intel(state))
                layout["indicators_panel"].update(render_indicators(state))
                layout["trending_oi_panel"].update(render_classic_trending_oi(state))
                layout["walls_panel"].update(render_walls(state))
                layout["alerts_panel"].update(render_alerts(state))
            await asyncio.sleep(0.5)


def select_index() -> tuple:
    """Startup menu to select index and dashboard layout mode."""
    print()
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║     ⚡  AlphaEdge Pro — Unified Terminal         ║")
    print("  ╠══════════════════════════════════════════════════╣")
    print("  ║  Live F&O Scanner  +  10-Factor Signal Engine   ║")
    print("  ║  OI Walls  •  Greeks  •  PCR  •  Macro          ║")
    print("  ╠══════════════════════════════════════════════════╣")
    print("  ║   1  →  NIFTY 50                                ║")
    print("  ║   2  →  NIFTY BANK                              ║")
    print("  ║   3  →  SENSEX                                  ║")
    print("  ╚══════════════════════════════════════════════════╝")
    print()
    
    while True:
        choice = input("  Select index [1/2/3]: ").strip()
        if choice in INDEX_MENU:
            selected_idx = INDEX_MENU[choice]
            break
        print("  Invalid choice — please enter 1, 2 or 3.")

    print()
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║     📊  Select Dashboard View Mode               ║")
    print("  ╠══════════════════════════════════════════════════╣")
    print("  ║   1  →  Ultimate Unified View (All in One)      ║")
    print("  ║   2  →  Pro F&O Breakout View (fo_breakout)     ║")
    print("  ║   3  →  Classic Intelligence View (v3 style)    ║")
    print("  ╚══════════════════════════════════════════════════╝")
    print()
    
    while True:
        mode_choice = input("  Select view mode [1/2/3]: ").strip()
        if mode_choice == "1":
            mode = "unified"
            print(f"  → Launching Ultimate Unified View for [bold]{selected_idx}[/bold]...")
            break
        elif mode_choice == "2":
            mode = "breakout"
            print(f"  → Launching Pro F&O Breakout View for [bold]{selected_idx}[/bold]...")
            break
        elif mode_choice == "3":
            mode = "classic"
            print(f"  → Launching Classic Intelligence View for [bold]{selected_idx}[/bold]...")
            break
        print("  Invalid choice — please enter 1, 2 or 3.")
        
    print()
    return selected_idx, mode


if __name__ == "__main__":
    init_db()
    try:
        chosen, mode = select_index()
        asyncio.run(run_dashboard(chosen, mode))
    except KeyboardInterrupt:
        print("\n  [AlphaEdge Pro] Session ended.")

