#!/usr/bin/env python3
"""
AlphaEdge API Server
FastAPI on localhost:8765

Endpoints:
    GET /api/latest                       — latest snapshot for all symbols + macro
    GET /api/history?sym=NIFTY&days=30   — time-series for Chart.js
    GET /api/symbols                      — list available symbols
    GET /                                 — serves dashboard.html
"""

import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

sys.path.insert(0, os.path.dirname(__file__))
import alphaedge_db as db

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AlphaEdge API",
    description="Market Intelligence API for NIFTY, SENSEX, BANKNIFTY",
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
