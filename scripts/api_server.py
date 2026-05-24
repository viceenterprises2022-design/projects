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
"""

import os
import sys
import sqlite3
import json as _json
import time
import threading
import urllib.request
from pathlib import Path

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


@app.get("/pixi", include_in_schema=False)
def serve_pixi():
    pixi = FRONTEND_DIR / "pixi_dashboard.html"
    if not pixi.exists():
        raise HTTPException(status_code=404, detail="pixi_dashboard.html not found")
    return FileResponse(str(pixi))


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

    return {
        "recorded_at": recorded_at,
        "symbols": {
            sym: _format_metric_row(row)
            for sym, row in data["symbols"].items()
        },
        "macro": _format_macro_row(data["macro"]),
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
        return {
            "symbol":    symbol,
            "timestamp": latest_ts,
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
        return {
            "symbol":      symbol,
            "recorded_at": d["recorded_at"],
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
        "recorded_at": datetime.datetime.utcnow().isoformat(),
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
