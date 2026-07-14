#!/usr/bin/env python3
"""
Hyperliquid & Gold SaaS Multi-Asset Database Layer
Handles SQLite schema definition and CRUD operations for multi-user, multi-asset trading.
"""

import sqlite3
import datetime
from pathlib import Path
import contextlib
import crypto_utils as crypto

DB_PATH = Path(__file__).parent / "saas_multi_trading.db"

@contextlib.contextmanager
def get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initializes multi-user SaaS trading tables for BTC, ETH, and Gold."""
    with get_conn() as conn:
        # Create users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT CHECK(role IN ('admin', 'user')) DEFAULT 'user',
                tier TEXT CHECK(tier IN ('free', 'pro', 'enterprise')) DEFAULT 'free',
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT
            )
        """)

        # Create user exchange credentials table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                broker_name TEXT CHECK(broker_name IN ('hyperliquid', 'upstox', 'oanda', 'mock')) NOT NULL,
                api_key TEXT NOT NULL,
                api_secret_encrypted TEXT NOT NULL,
                wallet_address TEXT,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Create strategy configurations table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS strategy_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                symbol TEXT NOT NULL, -- e.g., 'BTC-PERP', 'ETH-PERP', 'GOLD-MCX'
                asset_type TEXT CHECK(asset_type IN ('crypto', 'commodity')) NOT NULL,
                active BOOLEAN DEFAULT 1,
                leverage INTEGER DEFAULT 10,
                size_pct_per_trade REAL DEFAULT 5.0,
                hard_stop_loss_pct REAL DEFAULT 2.0,
                hard_take_profit_pct REAL DEFAULT 6.0,
                UNIQUE (user_id, symbol),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Create client active positions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS active_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                symbol TEXT NOT NULL,
                side TEXT CHECK(side IN ('LONG', 'SHORT')) NOT NULL,
                size REAL NOT NULL,
                entry_price REAL NOT NULL,
                leverage INTEGER NOT NULL,
                margin REAL NOT NULL,
                tp_price REAL,
                sl_price REAL,
                updated_at TEXT,
                UNIQUE (user_id, symbol, side),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Create client trades log table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trade_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                symbol TEXT NOT NULL,
                side TEXT CHECK(side IN ('LONG', 'SHORT')) NOT NULL,
                price REAL NOT NULL,
                size REAL NOT NULL,
                pnl REAL DEFAULT 0.0,
                trigger_type TEXT NOT NULL, -- e.g. TV_SIGNAL, STOP_LOSS, TAKE_PROFIT, MANUAL
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

def add_user(email: str, password_hash: str, role: str = "user", tier: str = "free") -> int:
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_conn() as conn:
        cursor = conn.execute("""
            INSERT INTO users (email, password_hash, role, tier, is_active, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
        """, (email, password_hash, role, tier, now_str))
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

# --- Credentials Management ---

def add_user_credential(user_id: int, broker_name: str, api_key: str, api_secret: str, wallet_address: str = None) -> int:
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    encrypted_secret = crypto.encrypt_secret(api_secret)
    with get_conn() as conn:
        cursor = conn.execute("""
            INSERT INTO user_credentials (user_id, broker_name, api_key, api_secret_encrypted, wallet_address, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, broker_name, api_key, encrypted_secret, wallet_address, now_str))
        conn.commit()
        return cursor.lastrowid

def get_user_credentials(user_id: int, broker_name: str):
    """Fetches and decrypts credentials for a specific broker."""
    with get_conn() as conn:
        row = conn.execute("""
            SELECT * FROM user_credentials WHERE user_id = ? AND broker_name = ?
        """, (user_id, broker_name)).fetchone()
        if not row:
            return None
        res = dict(row)
        if res.get("api_secret_encrypted"):
            res["api_secret"] = crypto.decrypt_secret(res["api_secret_encrypted"])
        return res

# --- Strategy Configs ---

def upsert_strategy_config(user_id: int, symbol: str, asset_type: str, active: bool, leverage: int, size_pct: float, stop_loss: float, take_profit: float):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO strategy_configs (user_id, symbol, asset_type, active, leverage, size_pct_per_trade, hard_stop_loss_pct, hard_take_profit_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, symbol) DO UPDATE SET
                active = excluded.active,
                leverage = excluded.leverage,
                size_pct_per_trade = excluded.size_pct_per_trade,
                hard_stop_loss_pct = excluded.hard_stop_loss_pct,
                hard_take_profit_pct = excluded.hard_take_profit_pct
        """, (user_id, symbol.upper(), asset_type.lower(), 1 if active else 0, leverage, size_pct, stop_loss, take_profit))
        conn.commit()

def get_strategy_configs_for_symbol(symbol: str):
    """Fetches all active strategy configs for users trading a specific symbol."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT sc.*, u.email, u.tier
            FROM strategy_configs sc
            JOIN users u ON sc.user_id = u.id
            WHERE sc.symbol = ? AND sc.active = 1 AND u.is_active = 1
        """, (symbol.upper(),)).fetchall()
        return [dict(r) for r in rows]

# --- Positions ---

def upsert_active_position(user_id: int, symbol: str, side: str, size: float, entry_price: float, leverage: int, margin: float, tp_price: float = None, sl_price: float = None):
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO active_positions (user_id, symbol, side, size, entry_price, leverage, margin, tp_price, sl_price, updated_at)
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

def get_active_positions(user_id: int = None):
    with get_conn() as conn:
        if user_id:
            rows = conn.execute("SELECT * FROM active_positions WHERE user_id = ?", (user_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM active_positions").fetchall()
        return [dict(r) for r in rows]

def delete_active_position(user_id: int, symbol: str, side: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM active_positions WHERE user_id = ? AND symbol = ? AND side = ?", (user_id, symbol.upper(), side.upper()))
        conn.commit()

# --- Trades Log ---

def add_trade_log(user_id: int, symbol: str, side: str, price: float, size: float, pnl: float, trigger_type: str):
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO trade_logs (user_id, symbol, side, price, size, pnl, trigger_type, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, symbol.upper(), side.upper(), price, size, pnl, trigger_type, now_str))
        conn.commit()

def get_trade_logs(user_id: int = None, limit: int = 50):
    with get_conn() as conn:
        if user_id:
            rows = conn.execute("SELECT * FROM trade_logs WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM trade_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
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
    print("Multi-Asset SaaS Database initialized successfully at:", DB_PATH)
