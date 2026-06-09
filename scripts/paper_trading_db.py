#!/usr/bin/env python3
"""
AlphaEdge Paper Trading Database Layer
Handles SQLite schema definition and CRUD operations for simulated BTC/ETH trading.
"""

import sqlite3
import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "paper_trading.db"

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes tables and populates starting account values if empty."""
    with get_conn() as conn:
        # Create tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS paper_account (
                id INTEGER PRIMARY KEY,
                balance REAL,
                equity REAL,
                today_pnl REAL,
                total_pnl REAL,
                start_date TEXT,
                last_update TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS paper_positions (
                symbol TEXT,
                side TEXT,
                size REAL,
                entry_price REAL,
                leverage REAL,
                margin REAL,
                unrealized_pnl REAL,
                tp_price REAL,
                sl_price REAL,
                timestamp TEXT,
                PRIMARY KEY (symbol, side)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS paper_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                side TEXT,
                type TEXT,
                price REAL,
                size REAL,
                pnl REAL,
                tp_price REAL,
                sl_price REAL,
                timestamp TEXT
            )
        """)
        
        # Check and alter tables for backwards compatibility
        try:
            conn.execute("ALTER TABLE paper_positions ADD COLUMN tp_price REAL")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE paper_positions ADD COLUMN sl_price REAL")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE paper_trades ADD COLUMN tp_price REAL")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE paper_trades ADD COLUMN sl_price REAL")
        except sqlite3.OperationalError:
            pass

        conn.execute("""
            CREATE TABLE IF NOT EXISTS paper_daily_pnl (
                date TEXT PRIMARY KEY,
                pnl REAL
            )
        """)
        
        # Insert initial account state if empty
        row = conn.execute("SELECT id FROM paper_account WHERE id = 1").fetchone()
        if not row:
            now_str = datetime.datetime.utcnow().isoformat()
            conn.execute("""
                INSERT INTO paper_account (id, balance, equity, today_pnl, total_pnl, start_date, last_update)
                VALUES (1, 100000.0, 100000.0, 0.0, 0.0, ?, ?)
            """, (now_str, now_str))
            
            # Seed some dummy daily PnLs to show chart progression (matching visual month PnL)
            today = datetime.date.today()
            for i in range(10, 0, -1):
                date_str = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
                # Deterministic random walks to look pretty
                pnl = 1500 * (1 if i % 3 != 0 else -2) + (i * 200)
                conn.execute("INSERT OR REPLACE INTO paper_daily_pnl (date, pnl) VALUES (?, ?)", (date_str, pnl))
        conn.commit()

def get_account():
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM paper_account WHERE id = 1").fetchone()
        return dict(row) if row else None

def update_account(balance: float, equity: float, today_pnl: float, total_pnl: float):
    now_str = datetime.datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute("""
            UPDATE paper_account
            SET balance = ?, equity = ?, today_pnl = ?, total_pnl = ?, last_update = ?
            WHERE id = 1
        """, (balance, equity, today_pnl, total_pnl, now_str))
        conn.commit()

def get_positions():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM paper_positions").fetchall()
        return [dict(r) for r in rows]

def get_position(symbol: str, side: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM paper_positions WHERE symbol = ? AND side = ?", (symbol, side)).fetchone()
        return dict(row) if row else None

def upsert_position(symbol: str, side: str, size: float, entry_price: float, leverage: float, margin: float, unrealized_pnl: float, tp_price: float = None, sl_price: float = None):
    now_str = datetime.datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO paper_positions (symbol, side, size, entry_price, leverage, margin, unrealized_pnl, tp_price, sl_price, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, side) DO UPDATE SET
                size = excluded.size,
                entry_price = excluded.entry_price,
                margin = excluded.margin,
                unrealized_pnl = excluded.unrealized_pnl,
                tp_price = COALESCE(excluded.tp_price, tp_price),
                sl_price = COALESCE(excluded.sl_price, sl_price),
                timestamp = excluded.timestamp
        """, (symbol, side, size, entry_price, leverage, margin, unrealized_pnl, tp_price, sl_price, now_str))
        conn.commit()

def update_position_sltp(symbol: str, side: str, tp_price: float, sl_price: float):
    with get_conn() as conn:
        conn.execute("""
            UPDATE paper_positions
            SET tp_price = ?, sl_price = ?
            WHERE symbol = ? AND side = ?
        """, (tp_price, sl_price, symbol, side))
        conn.commit()

def delete_position(symbol: str, side: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM paper_positions WHERE symbol = ? AND side = ?", (symbol, side))
        conn.commit()

def add_trade(symbol: str, side: str, type_str: str, price: float, size: float, pnl: float, tp_price: float = None, sl_price: float = None):
    now_str = datetime.datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO paper_trades (symbol, side, type, price, size, pnl, tp_price, sl_price, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (symbol, side, type_str, price, size, pnl, tp_price, sl_price, now_str))
        conn.commit()

def get_trades(limit=15):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM paper_trades ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

def get_daily_pnls(limit=10):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM paper_daily_pnl ORDER BY date DESC LIMIT ?", (limit,)).fetchall()
        res = [dict(r) for r in rows]
        res.reverse()
        return res

def record_daily_pnl(date_str: str, pnl: float):
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO paper_daily_pnl (date, pnl)
            VALUES (?, ?)
        """, (date_str, pnl))
        conn.commit()

def reset_db():
    """Wipes transactions and resets balance to 100,000 USDT."""
    with get_conn() as conn:
        conn.execute("DELETE FROM paper_positions")
        conn.execute("DELETE FROM paper_trades")
        conn.execute("DELETE FROM paper_daily_pnl")
        now_str = datetime.datetime.utcnow().isoformat()
        conn.execute("""
            UPDATE paper_account
            SET balance = 100000.0, equity = 100000.0, today_pnl = 0.0, total_pnl = 0.0, last_update = ?
            WHERE id = 1
        """, (now_str,))
        
        # Seed dummy daily PnLs
        today = datetime.date.today()
        for i in range(10, 0, -1):
            date_str = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            pnl = 1500 * (1 if i % 3 != 0 else -2) + (i * 200)
            conn.execute("INSERT OR REPLACE INTO paper_daily_pnl (date, pnl) VALUES (?, ?)", (date_str, pnl))
        conn.commit()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
    print("Account state:", get_account())
    print("Daily PnLs:", get_daily_pnls())
