import aiosqlite, json, time
from pathlib import Path
from typing import Optional
from core.config import setup_logger

logger = setup_logger("db")
DB_PATH = Path(__file__).parent.parent / "data" / "bot.db"

async def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_id TEXT NOT NULL UNIQUE, condition_id TEXT, question TEXT,
                outcome_label TEXT, side TEXT DEFAULT 'BUY', shares REAL NOT NULL,
                entry_price REAL NOT NULL, cost_usd REAL NOT NULL, entry_time INTEGER NOT NULL,
                whale_wallet TEXT, signal_type TEXT, stop_loss_price REAL, take_profit_price REAL,
                status TEXT DEFAULT 'OPEN', exit_price REAL, exit_time INTEGER, pnl_usd REAL
            );
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT, token_id TEXT NOT NULL, condition_id TEXT, question TEXT,
                side TEXT NOT NULL, shares REAL NOT NULL, price REAL NOT NULL, cost_usd REAL,
                timestamp INTEGER NOT NULL, whale_wallet TEXT, signal_type TEXT,
                dry_run INTEGER DEFAULT 0, raw_response TEXT
            );
            CREATE TABLE IF NOT EXISTS whale_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet TEXT NOT NULL, token_id TEXT NOT NULL, condition_id TEXT,
                signal_type TEXT, delta_shares REAL, detected_at INTEGER NOT NULL,
                copied INTEGER DEFAULT 0, skip_reason TEXT
            );
            CREATE TABLE IF NOT EXISTS daily_pnl (
                date TEXT PRIMARY KEY, realized_pnl REAL DEFAULT 0, unrealized_pnl REAL DEFAULT 0,
                open_positions INTEGER DEFAULT 0, total_trades INTEGER DEFAULT 0,
                win_trades INTEGER DEFAULT 0, capital_usd REAL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS bot_state (key TEXT PRIMARY KEY, value TEXT);
        """)
        await db.commit()
    logger.info("Database initialized: %s", DB_PATH)

class Database:
    async def save_position(self, pos: dict) -> int:
        async with aiosqlite.connect(DB_PATH) as db:
            c = await db.execute("""
                INSERT OR REPLACE INTO positions
                (token_id,condition_id,question,outcome_label,side,shares,entry_price,cost_usd,
                 entry_time,whale_wallet,signal_type,stop_loss_price,take_profit_price,status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (pos["token_id"],pos.get("condition_id"),pos.get("question"),
                 pos.get("outcome_label","YES"),pos.get("side","BUY"),pos["shares"],
                 pos["entry_price"],pos["cost_usd"],pos.get("entry_time",int(time.time())),
                 pos.get("whale_wallet"),pos.get("signal_type"),
                 pos.get("stop_loss_price"),pos.get("take_profit_price"),"OPEN"))
            await db.commit(); return c.lastrowid

    async def get_open_positions(self) -> list:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            c = await db.execute("SELECT * FROM positions WHERE status='OPEN' ORDER BY entry_time DESC")
            return [dict(r) for r in await c.fetchall()]

    async def get_position_by_token(self, token_id: str) -> Optional[dict]:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            c = await db.execute("SELECT * FROM positions WHERE token_id=? AND status='OPEN'", (token_id,))
            r = await c.fetchone(); return dict(r) if r else None

    async def close_position(self, token_id: str, exit_price: float, pnl_usd: float):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE positions SET status='CLOSED',exit_price=?,exit_time=?,pnl_usd=? WHERE token_id=? AND status='OPEN'",
                             (exit_price, int(time.time()), pnl_usd, token_id))
            await db.commit()

    async def log_trade(self, trade: dict):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""INSERT INTO trades (order_id,token_id,condition_id,question,side,shares,price,cost_usd,timestamp,whale_wallet,signal_type,dry_run,raw_response)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (trade.get("order_id"),trade["token_id"],trade.get("condition_id"),trade.get("question"),
                 trade["side"],trade["shares"],trade["price"],trade.get("cost_usd"),
                 trade.get("timestamp",int(time.time())),trade.get("whale_wallet"),trade.get("signal_type"),
                 1 if trade.get("dry_run") else 0, json.dumps(trade.get("raw_response",{}))))
            await db.commit()

    async def log_whale_signal(self, signal: dict, copied: bool, skip_reason: str = None):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO whale_signals (wallet,token_id,condition_id,signal_type,delta_shares,detected_at,copied,skip_reason) VALUES (?,?,?,?,?,?,?,?)",
                (signal["wallet"],signal["token_id"],signal.get("condition_id"),signal["type"],
                 signal.get("delta_shares"),int(time.time()),1 if copied else 0,skip_reason))
            await db.commit()

    async def get_today_pnl(self) -> dict:
        from datetime import date
        today = date.today().isoformat()
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            c = await db.execute("SELECT * FROM daily_pnl WHERE date=?", (today,))
            r = await c.fetchone(); return dict(r) if r else {"date":today,"realized_pnl":0.0}

    async def update_daily_pnl(self, realized, unrealized, open_pos, total_trades, wins, capital):
        from datetime import date
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR REPLACE INTO daily_pnl (date,realized_pnl,unrealized_pnl,open_positions,total_trades,win_trades,capital_usd) VALUES (?,?,?,?,?,?,?)",
                (date.today().isoformat(),realized,unrealized,open_pos,total_trades,wins,capital))
            await db.commit()

    async def get_closed_trades_stats(self) -> dict:
        async with aiosqlite.connect(DB_PATH) as db:
            c = await db.execute("SELECT COUNT(*),SUM(CASE WHEN pnl_usd>0 THEN 1 ELSE 0 END),SUM(CASE WHEN pnl_usd<=0 THEN 1 ELSE 0 END),SUM(pnl_usd),AVG(pnl_usd),MAX(pnl_usd),MIN(pnl_usd) FROM positions WHERE status='CLOSED'")
            r = await c.fetchone()
            if not r or not r[0]: return {"total":0,"wins":0,"losses":0,"total_pnl":0.0,"win_rate":0.0,"avg_pnl":0.0}
            total=r[0]; wins=r[1] or 0
            return {"total":total,"wins":wins,"losses":r[2] or 0,"total_pnl":round(r[3] or 0,2),
                    "avg_pnl":round(r[4] or 0,2),"best_trade":round(r[5] or 0,2),
                    "worst_trade":round(r[6] or 0,2),"win_rate":round(wins/total,4) if total else 0.0}

    async def get_pnl_summary(self, days=30) -> list:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            c = await db.execute("SELECT * FROM daily_pnl ORDER BY date DESC LIMIT ?", (days,))
            return [dict(r) for r in await c.fetchall()]

    async def get_signals_for_wallet(self, wallet: str, days: int = 7) -> list:
        cutoff = int(time.time()) - days * 86400
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            c = await db.execute("SELECT ws.*,p.pnl_usd FROM whale_signals ws LEFT JOIN positions p ON ws.token_id=p.token_id WHERE ws.wallet=? AND ws.detected_at>=? AND ws.copied=1",
                                 (wallet.lower(), cutoff))
            return [dict(r) for r in await c.fetchall()]

    async def set_state(self, key, value):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR REPLACE INTO bot_state (key,value) VALUES (?,?)", (key,value)); await db.commit()

    async def get_state(self, key, default=None):
        async with aiosqlite.connect(DB_PATH) as db:
            c = await db.execute("SELECT value FROM bot_state WHERE key=?", (key,)); r=await c.fetchone(); return r[0] if r else default

db = Database()
