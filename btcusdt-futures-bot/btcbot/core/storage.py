from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from btcbot.core.config import BotConfig
from btcbot.core.models import Candle, Position, Signal, Trade


class Store:
    def __init__(self, path: str | Path, cfg: BotConfig):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.cfg = cfg
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.init()

    def init(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS candles (
              start_ms INTEGER PRIMARY KEY,
              end_ms INTEGER NOT NULL,
              open REAL NOT NULL,
              high REAL NOT NULL,
              low REAL NOT NULL,
              close REAL NOT NULL,
              volume REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS signals (
              ts_ms INTEGER PRIMARY KEY,
              side TEXT NOT NULL,
              price REAL NOT NULL,
              atr REAL NOT NULL,
              breakout_level REAL NOT NULL,
              reason TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS trades (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              side TEXT NOT NULL,
              entry_ts_ms INTEGER NOT NULL,
              exit_ts_ms INTEGER,
              entry_price REAL NOT NULL,
              exit_price REAL,
              size_usd REAL NOT NULL,
              size_units REAL NOT NULL,
              gross_pnl REAL,
              fees REAL DEFAULT 0,
              slippage REAL DEFAULT 0,
              net_pnl REAL,
              reason TEXT
            );
            CREATE TABLE IF NOT EXISTS state (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            );
            """
        )
        if self.get_state("equity") is None:
            self.set_state("equity", self.cfg.paper_equity_usd)
            self.set_state("peak_equity", self.cfg.paper_equity_usd)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def set_state(self, key: str, value: Any) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)",
            (key, json.dumps(value)),
        )
        self.conn.commit()

    def get_state(self, key: str) -> Any:
        row = self.conn.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
        return json.loads(row["value"]) if row else None

    def equity(self) -> float:
        return float(self.get_state("equity") or self.cfg.paper_equity_usd)

    def peak_equity(self) -> float:
        return float(self.get_state("peak_equity") or self.cfg.paper_equity_usd)

    def update_equity(self, equity: float) -> None:
        self.set_state("equity", equity)
        self.set_state("peak_equity", max(self.peak_equity(), equity))

    def drawdown_pct(self) -> float:
        peak = self.peak_equity()
        return 0.0 if peak <= 0 else (peak - self.equity()) / peak

    def save_candles(self, candles: list[Candle]) -> None:
        self.conn.executemany(
            """
            INSERT OR REPLACE INTO candles
            (start_ms, end_ms, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [(c.start_ms, c.end_ms, c.open, c.high, c.low, c.close, c.volume) for c in candles],
        )
        self.conn.commit()

    def save_signal(self, signal: Signal) -> None:
        self.conn.execute(
            """
            INSERT OR IGNORE INTO signals
            (ts_ms, side, price, atr, breakout_level, reason)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (signal.ts_ms, signal.side, signal.price, signal.atr, signal.breakout_level, signal.reason),
        )
        self.conn.commit()

    def last_processed_ts(self) -> int:
        return int(self.get_state("last_processed_ts") or 0)

    def set_last_processed_ts(self, ts_ms: int) -> None:
        self.set_state("last_processed_ts", ts_ms)

    def open_position(self) -> Position | None:
        row = self.conn.execute("SELECT * FROM trades WHERE exit_ts_ms IS NULL ORDER BY id DESC LIMIT 1").fetchone()
        if not row:
            return None
        return Position(
            side=row["side"],
            entry_ts_ms=row["entry_ts_ms"],
            entry_price=row["entry_price"],
            size_usd=row["size_usd"],
            size_units=row["size_units"],
            stop_loss=float(self.get_state("open_stop_loss")),
            take_profit=float(self.get_state("open_take_profit")),
            atr=float(self.get_state("open_atr")),
            highest_price=float(self.get_state("open_highest_price")),
            lowest_price=float(self.get_state("open_lowest_price")),
        )

    def create_position(self, pos: Position) -> None:
        self.conn.execute(
            """
            INSERT INTO trades (side, entry_ts_ms, entry_price, size_usd, size_units)
            VALUES (?, ?, ?, ?, ?)
            """,
            (pos.side, pos.entry_ts_ms, pos.entry_price, pos.size_usd, pos.size_units),
        )
        self.set_state("open_stop_loss", pos.stop_loss)
        self.set_state("open_take_profit", pos.take_profit)
        self.set_state("open_atr", pos.atr)
        self.set_state("open_highest_price", pos.highest_price)
        self.set_state("open_lowest_price", pos.lowest_price)
        self.conn.commit()

    def update_open_position_marks(self, pos: Position) -> None:
        self.set_state("open_stop_loss", pos.stop_loss)
        self.set_state("open_highest_price", pos.highest_price)
        self.set_state("open_lowest_price", pos.lowest_price)

    def close_position(self, trade: Trade) -> None:
        self.conn.execute(
            """
            UPDATE trades
            SET exit_ts_ms=?, exit_price=?, gross_pnl=?, fees=?, slippage=?, net_pnl=?, reason=?
            WHERE exit_ts_ms IS NULL
            """,
            (
                trade.exit_ts_ms,
                trade.exit_price,
                trade.gross_pnl,
                trade.fees,
                trade.slippage,
                trade.net_pnl,
                trade.reason,
            ),
        )
        self.update_equity(self.equity() + trade.net_pnl)
        self.conn.commit()

    def summary(self) -> dict[str, Any]:
        trades = self.conn.execute("SELECT * FROM trades WHERE exit_ts_ms IS NOT NULL").fetchall()
        wins = [t for t in trades if (t["net_pnl"] or 0) >= 0]
        return {
            "equity": round(self.equity(), 2),
            "pnl": round(self.equity() - self.cfg.paper_equity_usd, 2),
            "drawdown_pct": round(self.drawdown_pct() * 100, 2),
            "closed_trades": len(trades),
            "win_rate": round((len(wins) / len(trades) * 100) if trades else 0, 2),
            "open_position": self.open_position(),
            "last_processed_ts": self.last_processed_ts(),
        }

