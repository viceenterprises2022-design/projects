#!/usr/bin/env python3
"""
AlphaEdge SQLite Database Layer
Manages schema creation and insert/query helpers for alphaedge.db
"""

import sqlite3
import datetime
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "alphaedge.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_conn()
    c = conn.cursor()

    # Per-symbol snapshot table
    c.execute("""
    CREATE TABLE IF NOT EXISTS metrics_history (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        recorded_at TEXT    NOT NULL,        -- ISO8601 UTC
        symbol      TEXT    NOT NULL,        -- NIFTY | SENSEX | BANKNIFTY
        ltp         REAL,
        open        REAL,
        high        REAL,
        low         REAL,
        change_pct  REAL,
        signal      TEXT,                   -- BUY | SELL | NEUTRAL
        score       INTEGER,
        factors     INTEGER,
        -- 10 factor scores (stored as int -1/0/+1)
        f_trend     INTEGER,
        f_dow       INTEGER,
        f_vix       INTEGER,
        f_oi        INTEGER,
        f_vwap      INTEGER,
        f_supertrend INTEGER,
        f_rsi       INTEGER,
        f_dxy       INTEGER,
        f_crude     INTEGER,
        f_pcr       INTEGER,
        -- Option chain derived metrics
        total_call_oi   REAL,
        total_put_oi    REAL,
        pcr             REAL,
        max_pain        REAL,
        expiry          TEXT,
        -- Full indicators JSON for API detail
        indicators_json TEXT
    )
    """)

    # Macro/global snapshot (one row per collection run)
    c.execute("""
    CREATE TABLE IF NOT EXISTS macro_history (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        recorded_at TEXT    NOT NULL,
        vix         REAL,
        vix_chg     REAL,
        dxy         REAL,
        dxy_chg     REAL,
        crude       REAL,
        crude_chg   REAL,
        us30        REAL,
        us30_chg    REAL,
        gold        REAL,
        gold_chg    REAL,
        silver      REAL,
        silver_chg  REAL
    )
    """)

    # Index for fast time-series queries
    c.execute("CREATE INDEX IF NOT EXISTS idx_metrics_sym_time ON metrics_history(symbol, recorded_at)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_macro_time ON macro_history(recorded_at)")

    conn.commit()
    conn.close()
    print(f"[DB] alphaedge.db ready at {DB_PATH}")


def insert_metric(recorded_at: str, symbol: str, quote: dict, analysis: dict, oi: dict | None):
    """Insert one symbol snapshot row into metrics_history."""
    conn = get_conn()
    inds = analysis.get("indicators", {})

    def s(key):
        return inds.get(key, {}).get("score", 0)

    oi_data = oi or {}
    conn.execute("""
    INSERT INTO metrics_history (
        recorded_at, symbol,
        ltp, open, high, low, change_pct,
        signal, score, factors,
        f_trend, f_dow, f_vix, f_oi, f_vwap,
        f_supertrend, f_rsi, f_dxy, f_crude, f_pcr,
        total_call_oi, total_put_oi, pcr, max_pain, expiry,
        indicators_json
    ) VALUES (
        ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?
    )
    """, (
        recorded_at, symbol,
        quote.get("ltp"), quote.get("open"), quote.get("high"),
        quote.get("low"), quote.get("change_pct"),
        analysis.get("signal"), analysis.get("score"), analysis.get("factors"),
        s("trend"), s("dow_jones"), s("india_vix"), s("oi"), s("vwap"),
        s("supertrend"), s("rsi"), s("dxy"), s("crude"), s("pcr"),
        oi_data.get("total_call_oi"), oi_data.get("total_put_oi"),
        oi_data.get("total_pcr"), oi_data.get("max_pain"), oi_data.get("expiry"),
        json.dumps({k: {"label": v.get("label"), "score": v.get("score"),
                        "detail": v.get("detail")} for k, v in inds.items()}),
    ))
    conn.commit()
    conn.close()


def insert_macro(recorded_at: str, gdata: dict):
    """Insert one macro snapshot row into macro_history."""
    conn = get_conn()

    def g(key, field):
        return gdata.get(key, {}).get(field)

    conn.execute("""
    INSERT INTO macro_history (
        recorded_at,
        vix, vix_chg, dxy, dxy_chg,
        crude, crude_chg, us30, us30_chg,
        gold, gold_chg, silver, silver_chg
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        recorded_at,
        g("VIX", "ltp"), g("VIX", "change_pct"),
        g("DXY", "ltp"), g("DXY", "change_pct"),
        g("CRUDE_OIL", "ltp"), g("CRUDE_OIL", "change_pct"),
        g("US30", "ltp"), g("US30", "change_pct"),
        g("GOLD", "ltp"), g("GOLD", "change_pct"),
        g("SILVER", "ltp"), g("SILVER", "change_pct"),
    ))
    conn.commit()
    conn.close()


def query_latest(symbols=("NIFTY", "SENSEX", "BANKNIFTY")):
    """Return the most recent row per symbol + latest macro row."""
    conn = get_conn()
    rows = {}
    for sym in symbols:
        row = conn.execute("""
            SELECT * FROM metrics_history
            WHERE symbol = ?
            ORDER BY recorded_at DESC LIMIT 1
        """, (sym,)).fetchone()
        if row:
            rows[sym] = dict(row)
            rows[sym]["indicators"] = json.loads(rows[sym].get("indicators_json") or "{}")

    macro = conn.execute("""
        SELECT * FROM macro_history ORDER BY recorded_at DESC LIMIT 1
    """).fetchone()
    conn.close()
    return {"symbols": rows, "macro": dict(macro) if macro else {}}


def query_history(symbol: str, days: int = 30):
    """Return time-series rows for one symbol over last N days."""
    conn = get_conn()
    since = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).isoformat()
    rows = conn.execute("""
        SELECT recorded_at, ltp, change_pct, signal, score, factors,
               pcr, max_pain, total_call_oi, total_put_oi,
               f_trend, f_dow, f_vix, f_oi, f_vwap,
               f_supertrend, f_rsi, f_dxy, f_crude, f_pcr
        FROM metrics_history
        WHERE symbol = ? AND recorded_at >= ?
        ORDER BY recorded_at ASC
    """, (symbol, since)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    init_db()
