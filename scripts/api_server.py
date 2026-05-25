#!/usr/bin/env python3
"""
DVR Portfolio API Server
FastAPI on localhost:8765

Endpoints:
    GET /                                            — DVR Portfolio dashboard
    GET /pixi                                        — PixiJS Options Intelligence
    GET /api/latest                                  — latest snapshot (all symbols + macro)
    GET /api/history?sym=NIFTY&days=30               — time-series for Chart.js
    GET /api/symbols                                 — list available symbols
    GET /api/portfolio/pnl                           — multi-broker portfolio P&L
    GET /api/pixi/chain?symbol=NIFTY                 — live options chain (all strikes)
    GET /api/pixi/oi-trend?symbol=NIFTY              — intraday total Call/Put OI trend
    GET /api/pixi/signal?symbol=NIFTY                — signal, score, all 10 factor values
    GET /api/pixi/macro                              — latest macro snapshot
    GET /api/pixi/strike-history?symbol=NIFTY&strike=23700  — per-minute OI for one strike
    GET /api/strategies/nifty200-momentum                  — Nifty 200 scanner results
"""

import os
import sys
import sqlite3
import json as _json
import time
import threading
import urllib.request
from pathlib import Path
import requests

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

sys.path.insert(0, os.path.dirname(__file__))
import alphaedge_db as db
import pnl_poller

# ── Extra DB Paths (PixiJS endpoints) ─────────────────────────────────────────
_BASE        = Path(__file__).parent
DB_OPT_CLI   = _BASE / "intraday_options_cli.db"
DB_INTRA_OI  = _BASE / "intraday_oi.db"
STRAT_REPORT = _BASE / "strategies" / "nifty200_momentum_report.json"
DB_ALPHA     = _BASE / "alphaedge.db"

def _pixi_conn(db_path: Path) -> sqlite3.Connection:
    """Open a SQLite connection with Row factory (not read-only so it can
    recover hot journals from concurrent writers)."""
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="DVR Portfolio API",
    description="Multi-Broker Portfolio Aggregator & Macro Data Service",
    version="1.0.0",
)

# Allow dashboard.html loaded from file:// or localhost:* to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).parent / "frontend"
SYMBOLS = ("NIFTY", "SENSEX", "BANKNIFTY")


# ── Static Files + Dashboard ──────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def serve_dashboard():
    index = FRONTEND_DIR / "dashboard.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="dashboard.html not found")
    return FileResponse(str(index))


@app.get("/market", include_in_schema=False)
def serve_market():
    f = FRONTEND_DIR / "market.html"
    if not f.exists():
        raise HTTPException(status_code=404, detail="market.html not found")
    return FileResponse(str(f))


@app.get("/portfolio", include_in_schema=False)
def serve_portfolio():
    f = FRONTEND_DIR / "portfolio.html"
    if not f.exists():
        raise HTTPException(status_code=404, detail="portfolio.html not found")
    return FileResponse(str(f))


@app.get("/holdings", include_in_schema=False)
def serve_holdings():
    f = FRONTEND_DIR / "holdings.html"
    if not f.exists():
        raise HTTPException(status_code=404, detail="holdings.html not found")
    return FileResponse(str(f))


@app.get("/positions", include_in_schema=False)
def serve_positions():
    f = FRONTEND_DIR / "positions.html"
    if not f.exists():
        raise HTTPException(status_code=404, detail="positions.html not found")
    return FileResponse(str(f))


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# ── API Endpoints ─────────────────────────────────────────────────────────────

@app.get("/api/latest")
def api_latest():
    """
    Returns the most recent snapshot for all three symbols plus the latest macro data.

    Response shape:
    {
      "recorded_at": "...",
      "symbols": {
        "NIFTY":     { ltp, change_pct, signal, score, factors, pcr, max_pain, indicators },
        "SENSEX":    { ... },
        "BANKNIFTY": { ... }
      },
      "macro": { vix, dxy, crude, us30, gold, silver, ... }
    }
    """
    db.init_db()
    data = db.query_latest(SYMBOLS)
    if not data["symbols"]:
        raise HTTPException(status_code=503, detail="No data yet. Run collector.py first.")

    # Surface recorded_at from first available symbol
    recorded_at = next(iter(data["symbols"].values()), {}).get("recorded_at")
    stale = _check_stale(recorded_at)

    live_macro = _get_macro_cached()
    db_row = data.get("macro") or {}
    def _merge(key):
        if live_macro.get(key) and live_macro[key].get("ltp") is not None:
            return live_macro[key]
        return {"ltp": db_row.get(key), "chg": db_row.get(f"{key}_chg")}
    return {
        "recorded_at": recorded_at,
        "stale": stale,
        "symbols": {
            sym: _format_metric_row(row)
            for sym, row in data["symbols"].items()
        },
        "macro": {
            "recorded_at": recorded_at,
            "vix":   _merge("vix"),
            "dxy":   _merge("dxy"),
            "crude": _merge("crude"),
            "us30":  _merge("us30"),
            "gold":  _merge("gold"),
            "silver":_merge("silver"),
        },
    }


@app.get("/api/history")
def api_history(
    sym: str = Query(..., description="Symbol: NIFTY | SENSEX | BANKNIFTY"),
    days: int = Query(30, ge=1, le=365, description="Look-back window in days"),
):
    """
    Returns time-series rows for a symbol, ready for Chart.js consumption.

    Response shape:
    {
      "symbol": "NIFTY",
      "days": 30,
      "rows": [
        { recorded_at, ltp, change_pct, signal, score, pcr, max_pain, ... },
        ...
      ]
    }
    """
    sym = sym.upper()
    if sym not in SYMBOLS:
        raise HTTPException(status_code=400, detail=f"sym must be one of {SYMBOLS}")

    db.init_db()
    rows = db.query_history(sym, days)
    return {"symbol": sym, "days": days, "rows": rows}


@app.get("/api/symbols")
def api_symbols():
    return {"symbols": list(SYMBOLS)}


@app.get("/api/portfolio/pnl")
def api_portfolio_pnl():
    """
    Returns the aggregated portfolio P&L data from Upstox, Dhan, and TradeSmart.
    """
    try:
        return pnl_poller.get_aggregated_portfolio()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── PixiJS Data Endpoints ─────────────────────────────────────────────────────

@app.get("/api/pixi/chain")
def api_pixi_chain(
    symbol: str = Query("NIFTY", description="NIFTY | SENSEX | BANKNIFTY"),
):
    """
    Returns the latest full options chain snapshot from intraday_options_cli.db.
    All strikes for the given symbol at the most recent recorded timestamp.
    """
    symbol = symbol.upper()
    conn = _pixi_conn(DB_OPT_CLI)
    try:
        row = conn.execute(
            "SELECT MAX(timestamp) AS ts FROM options_data WHERE index_name = ?",
            (symbol,)
        ).fetchone()
        latest_ts = row["ts"] if row else None
        if not latest_ts:
            return {"symbol": symbol, "timestamp": None, "spot": None, "strikes": []}

        rows = conn.execute(
            """
            SELECT strike, ce_ltp, ce_oi, pe_ltp, pe_oi, spot
            FROM   options_data
            WHERE  index_name = ? AND timestamp = ?
            ORDER  BY strike
            """,
            (symbol, latest_ts),
        ).fetchall()

        spot = rows[0]["spot"] if rows else None
        stale = _check_stale(latest_ts.replace(" ", "T") if latest_ts else None)
        return {
            "symbol":    symbol,
            "timestamp": latest_ts,
            "stale":      stale,
            "spot":      spot,
            "strikes":   [dict(r) for r in rows],
        }
    finally:
        conn.close()


@app.get("/api/pixi/oi-trend")
def api_pixi_oi_trend(
    symbol: str = Query("NIFTY", description="NIFTY | SENSEX | BANKNIFTY"),
):
    """
    Returns the full intraday total Call OI vs Put OI time-series from intraday_oi.db.
    """
    symbol = symbol.upper()
    conn = _pixi_conn(DB_INTRA_OI)
    try:
        rows = conn.execute(
            "SELECT timestamp, ltp, call_oi, put_oi FROM trending_oi "
            "WHERE symbol = ? ORDER BY timestamp",
            (symbol,),
        ).fetchall()
        return {"symbol": symbol, "series": [dict(r) for r in rows]}
    finally:
        conn.close()


@app.get("/api/pixi/signal")
def api_pixi_signal(
    symbol: str = Query("NIFTY", description="NIFTY | SENSEX | BANKNIFTY"),
):
    """
    Returns the latest signal row from alphaedge.db including all 10 factor scores.
    """
    symbol = symbol.upper()
    conn = _pixi_conn(DB_ALPHA)
    try:
        row = conn.execute(
            "SELECT * FROM metrics_history WHERE symbol = ? "
            "ORDER BY recorded_at DESC LIMIT 1",
            (symbol,),
        ).fetchone()
        if not row:
            return {"symbol": symbol, "signal": None}
        d = dict(row)
        indicators = {}
        try:
            indicators = _json.loads(d.get("indicators_json") or "{}")
        except Exception:
            pass
        stale = _check_stale(d.get("recorded_at"))
        return {
            "symbol":      symbol,
            "recorded_at": d["recorded_at"],
            "stale":       stale,
            "ltp":         d["ltp"],
            "signal":      d["signal"],
            "score":       d["score"],
            "factors":     d["factors"],
            "pcr":         d["pcr"],
            "max_pain":    d["max_pain"],
            "expiry":      d["expiry"],
            "factors_detail": {
                "trend":      d["f_trend"],
                "dow":        d["f_dow"],
                "india_vix":  d["f_vix"],
                "oi":         d["f_oi"],
                "vwap":       d["f_vwap"],
                "supertrend": d["f_supertrend"],
                "rsi":        d["f_rsi"],
                "dxy":        d["f_dxy"],
                "crude":      d["f_crude"],
                "pcr":        d["f_pcr"],
            },
            "indicators": indicators,
        }
    finally:
        conn.close()


# ── Live Macro Fetcher (Yahoo Finance, 5-min cache) ───────────────────────────
_MACRO_SYMBOLS = {
    "vix":   "^VIX",          # CBOE Volatility Index
    "dxy":   "DX-Y.NYB",     # US Dollar Index
    "crude": "CL=F",         # WTI Crude Oil Futures
    "gold":  "GC=F",         # Gold Futures
    "silver":"SI=F",         # Silver Futures
    "us30":  "^DJI",         # Dow Jones Industrial Average
}
_macro_cache: dict = {}
_macro_cache_ts: float = 0.0
_macro_lock = threading.Lock()
_MACRO_TTL = 300  # seconds (5 min)

def _yahoo_quote(ticker: str) -> dict | None:
    """Fetch a single quote from Yahoo Finance v8 JSON API."""
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        "?interval=1d&range=5d"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = _json.loads(r.read())
        result = data["chart"]["result"][0]
        meta   = result["meta"]
        ltp    = meta.get("regularMarketPrice") or meta.get("previousClose")
        prev   = meta.get("previousClose") or meta.get("chartPreviousClose")
        chg_pct = ((ltp - prev) / prev) if prev and ltp else 0.0
        return {"ltp": ltp, "chg": chg_pct}
    except Exception as exc:
        print(f"[Macro Yahoo] {ticker}: {exc}")
        return None

def _fetch_live_macro() -> dict:
    """Fetch all macro symbols, update cache, return result dict."""
    result = {}
    for key, ticker in _MACRO_SYMBOLS.items():
        q = _yahoo_quote(ticker)
        if q:
            result[key] = q
    return result

def _get_macro_cached() -> dict:
    """Return cached macro data, refreshing if stale."""
    global _macro_cache, _macro_cache_ts
    with _macro_lock:
        if time.time() - _macro_cache_ts > _MACRO_TTL or not _macro_cache:
            fresh = _fetch_live_macro()
            if fresh:  # only update if we got something
                _macro_cache    = fresh
                _macro_cache_ts = time.time()
        return dict(_macro_cache)


@app.get("/api/pixi/macro")
def api_pixi_macro():
    """
    Returns live macro snapshot (VIX, DXY, Crude, Gold, Silver, US30).
    Fetched directly from Yahoo Finance with a 5-minute in-memory cache.
    Falls back to DB for VIX/DXY if Yahoo is unavailable.
    """
    live = _get_macro_cached()

    # DB fallback for VIX / DXY only
    db_row = {}
    if not live.get("vix") or not live.get("dxy"):
        try:
            conn = _pixi_conn(DB_ALPHA)
            row  = conn.execute(
                "SELECT * FROM macro_history ORDER BY recorded_at DESC LIMIT 1"
            ).fetchone()
            conn.close()
            if row:
                db_row = dict(row)
        except Exception:
            pass

    def _val(key, db_key, db_chg_key):
        if live.get(key):
            return {"value": live[key]["ltp"], "chg": live[key]["chg"]}
        return {"value": db_row.get(db_key), "chg": db_row.get(db_chg_key)}

    import datetime
    return {
        "recorded_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "vix":    _val("vix",   "vix",   "vix_chg"),
        "dxy":    _val("dxy",   "dxy",   "dxy_chg"),
        "crude":  _val("crude", "crude", "crude_chg"),
        "gold":   _val("gold",  "gold",  "gold_chg"),
        "silver": _val("silver","silver","silver_chg"),
        "us30":   _val("us30",  "us30",  "us30_chg"),
    }


@app.get("/api/pixi/strike-history")
def api_pixi_strike_history(
    symbol: str  = Query("NIFTY",   description="NIFTY | SENSEX | BANKNIFTY"),
    strike: float = Query(...,        description="Strike price (e.g. 23700)"),
):
    """
    Returns the per-minute CE and PE OI time-series for a specific strike today.
    Used by the PixiJS click-to-drill-down feature.
    """
    symbol = symbol.upper()
    conn = _pixi_conn(DB_OPT_CLI)
    try:
        rows = conn.execute(
            """
            SELECT timestamp, ce_ltp, ce_oi, pe_ltp, pe_oi
            FROM   options_data
            WHERE  index_name = ? AND strike = ?
            ORDER  BY timestamp
            """,
            (symbol, strike),
        ).fetchall()
        return {"symbol": symbol, "strike": strike, "series": [dict(r) for r in rows]}
    finally:
        conn.close()


# ── Gainers / Losers ───────────────────────────────────────────────────────────

NSE_STOCKS = {
    "RELIANCE":    "NSE_EQ|INE002A01018",
    "HDFCBANK":    "NSE_EQ|INE040A01034",
    "ICICIBANK":   "NSE_EQ|INE090A01021",
    "INFY":        "NSE_EQ|INE009A01021",
    "TCS":         "NSE_EQ|INE467B01029",
    "ITC":         "NSE_EQ|INE154A01025",
    "LT":          "NSE_EQ|INE018A01030",
    "SBIN":        "NSE_EQ|INE062A01020",
    "BHARTIARTL":  "NSE_EQ|INE397D01024",
    "AXISBANK":    "NSE_EQ|INE238A01034",
    "HINDUNILVR":  "NSE_EQ|INE030A01027",
    "MARUTI":      "NSE_EQ|INE585B01010",
    "TATAMOTORS":  "NSE_EQ|INE155A01022",
    "TATASTEEL":   "NSE_EQ|INE081A01020",
    "BAJFINANCE":  "NSE_EQ|INE296A01024",
    "WIPRO":       "NSE_EQ|INE075A01022",
    "TITAN":       "NSE_EQ|INE280A01028",
    "ASIANPAINT":  "NSE_EQ|INE021A01026",
    "NTPC":        "NSE_EQ|INE733E01010",
    "KOTAKBANK":   "NSE_EQ|INE237A01028",
    "POWERGRID":   "NSE_EQ|INE752E01010",
    "ONGC":        "NSE_EQ|INE213A01029",
    "SUNPHARMA":   "NSE_EQ|INE044A01036",
    "HCLTECH":     "NSE_EQ|INE860A01027",
    "TECHM":       "NSE_EQ|INE669A01022",
    "ULTRACEMCO":  "NSE_EQ|INE481G01114",
    "NESTLEIND":   "NSE_EQ|INE239A01024",
    "HEROMOTOCO":  "NSE_EQ|INE158A01026",
    "M&M":         "NSE_EQ|INE101A01026",
    "JSWSTEEL":    "NSE_EQ|INE019C01026",
    "INDUSINDBK":  "NSE_EQ|INE095A01012",
    "CIPLA":       "NSE_EQ|INE059A01014",
    "GRASIM":      "NSE_EQ|INE047A01021",
    "HINDALCO":    "NSE_EQ|INE038A01020",
    "APOLLOHOSP":  "NSE_EQ|INE437A01028",
    "BPCL":        "NSE_EQ|INE029A01010",
    "COALINDIA":   "NSE_EQ|INE522F01014",
    "ADANIENT":    "NSE_EQ|INE423A01024",
    "ADANIPORTS":  "NSE_EQ|INE742F01042",
    "EICHERMOT":   "NSE_EQ|INE066A01013",
    "VEDL":        "NSE_EQ|INE205A01025",
    "DIVISLAB":    "NSE_EQ|INE361B01024",
    "DRREDDY":     "NSE_EQ|INE089A01031",
    "BAJAJFINSV":  "NSE_EQ|INE918I01026",
    "BRITANNIA":   "NSE_EQ|INE216A01030",
    "BAJAJ-AUTO":  "NSE_EQ|INE917I01010",
    "MARICO":      "NSE_EQ|INE196A01026",
    "TRENT":       "NSE_EQ|INE849A01020",
    "BEL":         "NSE_EQ|INE263A01024",
    "HAL":         "NSE_EQ|INE548A01028",
    "ZOMATO":      "NSE_EQ|INE758T01015",
    "IOC":         "NSE_EQ|INE242A01010",
    "GAIL":        "NSE_EQ|INE129A01019",
}

NSE_QUOTE_CACHE: dict = {}
NSE_QUOTE_CACHE_TS: float = 0.0
NSE_QUOTE_LOCK = threading.Lock()
NSE_QUOTE_TTL = 30  # seconds

def _fetch_nse_quotes() -> dict:
    token = os.environ.get("UPSTOX_TOKEN")
    if not token:
        return {}
    keys = ",".join(NSE_STOCKS.values())
    try:
        r = requests.get(
            "https://api.upstox.com/v2/market-quote/quotes",
            params={"instrument_key": keys},
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=10,
        )
        if r.status_code != 200:
            return {}
        data = r.json().get("data", {})
        result = {}
        # Response keys are NSE_EQ:SYMBOL e.g. NSE_EQ:RELIANCE
        for resp_key, q in data.items():
            sym = resp_key.split(":", 1)[-1]
            if sym not in NSE_STOCKS:
                continue
            ltp = q.get("last_price", 0)
            net_chg = q.get("net_change", 0)
            prev_close = ltp - net_chg
            chg_pct = (net_chg / prev_close * 100) if prev_close else 0
            result[sym] = {
                "ltp": round(ltp, 2),
                "change": round(net_chg, 2),
                "change_pct": round(chg_pct, 2),
            }
        return result
    except Exception:
        return {}

def _get_nse_quotes_cached() -> dict:
    global NSE_QUOTE_CACHE, NSE_QUOTE_CACHE_TS
    with NSE_QUOTE_LOCK:
        now = time.time()
        if now - NSE_QUOTE_CACHE_TS > NSE_QUOTE_TTL or not NSE_QUOTE_CACHE:
            fresh = _fetch_nse_quotes()
            if fresh:
                NSE_QUOTE_CACHE = fresh
                NSE_QUOTE_CACHE_TS = now
        return dict(NSE_QUOTE_CACHE)

@app.get("/api/gainers-losers")
def api_gainers_losers():
    quotes = _get_nse_quotes_cached()
    if not quotes:
        raise HTTPException(status_code=503, detail="No quotes available")
    sorted_by_chg = sorted(quotes.items(), key=lambda x: x[1]["change_pct"], reverse=True)
    gainers = [{"symbol": s, **d} for s, d in sorted_by_chg[:5]]
    losers  = [{"symbol": s, **d} for s, d in sorted_by_chg[-5:]]
    losers.reverse()
    import datetime
    return {
        "gainers": gainers,
        "losers": losers,
        "updated_at": datetime.datetime.now(datetime.UTC).isoformat(),
    }


@app.get("/api/strategies/nifty200-momentum")
def api_nifty200_momentum():
    if not STRAT_REPORT.exists():
        raise HTTPException(status_code=404, detail="Report not yet generated. Run: python3 strategies/nifty200_momentum.py")
    data = _json.loads(STRAT_REPORT.read_text())
    file_mtime = STRAT_REPORT.stat().st_mtime
    stale = (time.time() - file_mtime) > STALE_SECONDS
    data["stale"] = stale
    return data


# ── Staleness Helper ──────────────────────────────────────────────────────────

STALE_SECONDS = 300  # 5 minutes

def _check_stale(recorded_at: str | None) -> bool:
    """Return True if recorded_at is older than STALE_SECONDS."""
    if not recorded_at:
        return True
    try:
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(recorded_at)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds() > STALE_SECONDS
    except Exception:
        return True


# ── Formatters ────────────────────────────────────────────────────────────────

def _format_metric_row(row: dict) -> dict:
    """Strip raw DB fields, expose clean API shape."""
    return {
        "recorded_at": row.get("recorded_at"),
        "ltp":         row.get("ltp"),
        "open":        row.get("open"),
        "high":        row.get("high"),
        "low":         row.get("low"),
        "change_pct":  row.get("change_pct"),
        "signal":      row.get("signal"),
        "score":       row.get("score"),
        "factors":     row.get("factors"),
        "pcr":         row.get("pcr"),
        "max_pain":    row.get("max_pain"),
        "expiry":      row.get("expiry"),
        "total_call_oi": row.get("total_call_oi"),
        "total_put_oi":  row.get("total_put_oi"),
        "indicators":  row.get("indicators", {}),
    }


def _format_macro_row(row: dict) -> dict:
    return {
        "recorded_at": row.get("recorded_at"),
        "vix":   {"ltp": row.get("vix"),   "chg": row.get("vix_chg")},
        "dxy":   {"ltp": row.get("dxy"),   "chg": row.get("dxy_chg")},
        "crude": {"ltp": row.get("crude"), "chg": row.get("crude_chg")},
        "us30":  {"ltp": row.get("us30"),  "chg": row.get("us30_chg")},
        "gold":  {"ltp": row.get("gold"),  "chg": row.get("gold_chg")},
        "silver":{"ltp": row.get("silver"),"chg": row.get("silver_chg")},
    }


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="127.0.0.1", port=8765, reload=True)
