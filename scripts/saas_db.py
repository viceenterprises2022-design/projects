#!/usr/bin/env python3
"""
Hyperliquid SaaS Bot Database Layer
Handles SQLite schema definition and CRUD operations for multi-user trading.
"""

import sqlite3
import datetime
from pathlib import Path
import contextlib

DB_PATH = Path(__file__).parent / "saas_trading.db"

@contextlib.contextmanager
def get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initializes multi-user SaaS trading tables."""
    with get_conn() as conn:
        # Create users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                hl_wallet TEXT,
                hl_api_key TEXT,
                hl_api_secret TEXT, -- encrypted or raw for testing
                risk_multiplier REAL DEFAULT 1.0,
                max_leverage INTEGER DEFAULT 10,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT
            )
        """)

        # Create strategy configurations table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS strategy_configs (
                user_id INTEGER,
                symbol TEXT,
                active BOOLEAN DEFAULT 1,
                size_pct_per_trade REAL DEFAULT 5.0,
                hard_stop_loss_pct REAL DEFAULT 2.0,
                hard_take_profit_pct REAL DEFAULT 6.0,
                PRIMARY KEY (user_id, symbol),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Create client active positions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS client_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                symbol TEXT,
                side TEXT,
                size REAL,
                entry_price REAL,
                leverage REAL,
                margin REAL,
                tp_price REAL,
                sl_price REAL,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE (user_id, symbol, side)
            )
        """)

        # Create client trades log table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS client_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                symbol TEXT,
                side TEXT,
                price REAL,
                size REAL,
                pnl REAL,
                trigger_type TEXT, -- e.g. TV_SIGNAL, STOP_LOSS, TAKE_PROFIT, MANUAL
                timestamp TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Create risk audits table (for AI analysis reports)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS risk_audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                audit_report TEXT,
                suggested_leverage_limit INTEGER,
                daily_volatility_multiplier REAL
            )
        """)

        conn.commit()

# --- User Management ---

def add_user(email: str, hl_wallet: str = None, hl_api_key: str = None, hl_api_secret: str = None, risk_mult: float = 1.0, max_lev: int = 10) -> int:
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_conn() as conn:
        cursor = conn.execute("""
            INSERT INTO users (email, hl_wallet, hl_api_key, hl_api_secret, risk_multiplier, max_leverage, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """, (email, hl_wallet, hl_api_key, hl_api_secret, risk_mult, max_lev, now_str))
        conn.commit()
        return cursor.lastrowid

def get_user(user_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

def get_active_users():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM users WHERE is_active = 1").fetchall()
        return [dict(r) for r in rows]

# --- Strategy Configs ---

def upsert_strategy_config(user_id: int, symbol: str, active: bool, size_pct: float, stop_loss: float, take_profit: float):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO strategy_configs (user_id, symbol, active, size_pct_per_trade, hard_stop_loss_pct, hard_take_profit_pct)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, symbol) DO UPDATE SET
                active = excluded.active,
                size_pct_per_trade = excluded.size_pct_per_trade,
                hard_stop_loss_pct = excluded.hard_stop_loss_pct,
                hard_take_profit_pct = excluded.hard_take_profit_pct
        """, (user_id, symbol.upper(), 1 if active else 0, size_pct, stop_loss, take_profit))
        conn.commit()

def get_strategy_configs_for_symbol(symbol: str):
    """Fetches all active strategy configs for users trading a specific symbol."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT sc.*, u.hl_wallet, u.hl_api_key, u.hl_api_secret, u.risk_multiplier, u.max_leverage
            FROM strategy_configs sc
            JOIN users u ON sc.user_id = u.id
            WHERE sc.symbol = ? AND sc.active = 1 AND u.is_active = 1
        """, (symbol.upper(),)).fetchall()
        return [dict(r) for r in rows]

# --- Positions ---

def upsert_client_position(user_id: int, symbol: str, side: str, size: float, entry_price: float, leverage: float, margin: float, tp_price: float = None, sl_price: float = None):
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO client_positions (user_id, symbol, side, size, entry_price, leverage, margin, tp_price, sl_price, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, symbol, side) DO UPDATE SET
                size = excluded.size,
                entry_price = excluded.entry_price,
                margin = excluded.margin,
                tp_price = COALESCE(excluded.tp_price, tp_price),
                sl_price = COALESCE(excluded.sl_price, sl_price),
                updated_at = excluded.updated_at
        """, (user_id, symbol.upper(), side.upper(), size, entry_price, leverage, margin, tp_price, sl_price, now_str))
        conn.commit()

def get_client_positions(user_id: int):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM client_positions WHERE user_id = ?", (user_id,)).fetchall()
        return [dict(r) for r in rows]

def delete_client_position(user_id: int, symbol: str, side: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM client_positions WHERE user_id = ? AND symbol = ? AND side = ?", (user_id, symbol.upper(), side.upper()))
        conn.commit()

# --- Trades Log ---

def add_client_trade(user_id: int, symbol: str, side: str, price: float, size: float, pnl: float, trigger_type: str):
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO client_trades (user_id, symbol, side, price, size, pnl, trigger_type, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, symbol.upper(), side.upper(), price, size, pnl, trigger_type, now_str))
        conn.commit()

def get_client_trades(user_id: int, limit: int = 50):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM client_trades WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)).fetchall()
        return [dict(r) for r in rows]

# --- Risk Audits ---

def add_risk_audit(report: str, leverage_limit: int, volatility_mult: float):
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO risk_audits (timestamp, audit_report, suggested_leverage_limit, daily_volatility_multiplier)
            VALUES (?, ?, ?, ?)
        """, (now_str, report, leverage_limit, volatility_mult))
        conn.commit()

def get_latest_risk_audit():
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM risk_audits ORDER BY id DESC LIMIT 1").fetchone()
        return dict(row) if row else None

if __name__ == "__main__":
    init_db()
    print("SaaS Trading Database initialized successfully at:", DB_PATH)
    # Seed a dummy user for testing
    try:
        uid = add_user("tester@example.com", "0x123...", "key_abc", "secret_xyz")
        upsert_strategy_config(uid, "BTC-PERP", True, 10.0, 1.5, 5.0)
        print("Seeded test user ID:", uid)
        print("Configs for BTC-PERP:", get_strategy_configs_for_symbol("BTC-PERP"))
    except sqlite3.IntegrityError:
        print("Test user already exists.")
