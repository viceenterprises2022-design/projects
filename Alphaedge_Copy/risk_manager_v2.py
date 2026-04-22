"""
AlphaCopy - Enhanced Risk Manager v2
Integrates Telegram journal for all trade lifecycle events.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from utils.telegram_journal import TelegramJournal

logger = logging.getLogger(__name__)


@dataclass
class Position:
    bot: str
    symbol: str
    side: str
    entry_price: float
    size_usd: float
    size_units: float
    stop_loss: float
    take_profit: float
    trailing_stop_pct: float   = 0.03
    trailing_high: float       = 0.0
    opened_at: datetime        = field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None
    pnl_usd: float             = 0.0
    status: str                = "OPEN"
    source_wallet: str         = ""
    trade_id: str              = ""
    leverage: int              = 1


@dataclass
class BotState:
    bot_name: str
    allocated_capital: float
    current_equity: float
    peak_equity: float
    positions: Dict[str, Position] = field(default_factory=dict)
    total_trades: int  = 0
    winning_trades: int = 0
    losing_trades: int  = 0
    halted: bool        = False
    halt_reason: str    = ""


class RiskManager:
    def __init__(self, config, journal: Optional["TelegramJournal"] = None):
        self.config  = config
        self.journal = journal
        self.states: Dict[str, BotState] = {
            "hyperliquid": BotState(
                "hyperliquid",
                config.hyperliquid.allocated_capital_usd,
                config.hyperliquid.allocated_capital_usd,
                config.hyperliquid.allocated_capital_usd,
            ),
            "binance": BotState(
                "binance",
                config.binance.allocated_capital_usd,
                config.binance.allocated_capital_usd,
                config.binance.allocated_capital_usd,
            ),
            "polymarket": BotState(
                "polymarket",
                config.polymarket.allocated_capital_usd,
                config.polymarket.allocated_capital_usd,
                config.polymarket.allocated_capital_usd,
            ),
        }
        self.event_log: List[dict] = []

    # ─────────────────────────────────────────────────────────────────────
    # Pre-trade gate
    # ─────────────────────────────────────────────────────────────────────
    def check_trade(self, bot: str, symbol: str, size_usd: float,
                    side: str, source_wallet: str) -> tuple[bool, str, float]:
        state = self.states[bot]
        cfg   = getattr(self.config, bot)

        if state.halted:
            return False, f"Bot halted: {state.halt_reason}", 0.0

        open_pos = [p for p in state.positions.values() if p.status == "OPEN"]
        if len(open_pos) >= cfg.max_open_positions:
            return False, f"Max open positions ({cfg.max_open_positions}) reached", 0.0

        if symbol in state.positions and state.positions[symbol].status == "OPEN":
            return False, f"Already in {symbol}", 0.0

        drawdown = (state.peak_equity - state.current_equity) / state.peak_equity
        if drawdown >= cfg.max_drawdown_pct:
            self._halt_bot(bot, f"Max drawdown {drawdown:.1%} hit")
            return False, "Drawdown limit triggered", 0.0

        max_size = min(
            state.current_equity * cfg.max_position_pct,
            cfg.max_copy_size_usd
        )
        adjusted = max(cfg.min_copy_size_usd, min(size_usd, max_size))

        return True, "OK", adjusted

    # ─────────────────────────────────────────────────────────────────────
    # Position lifecycle
    # ─────────────────────────────────────────────────────────────────────
    def open_position(self, bot: str, position: Position) -> None:
        state = self.states[bot]
        state.positions[position.symbol] = position
        state.total_trades += 1
        self._log("OPENED", bot, position.symbol,
                  f"{position.side} ${position.size_usd:.0f} @ {position.entry_price}")
        logger.info(f"[{bot.upper()}] OPENED {position.symbol} {position.side} "
                    f"${position.size_usd:.0f} @ {position.entry_price}")

        # Fire-and-forget Telegram alert
        if self.journal:
            import asyncio
            asyncio.create_task(
                self.journal.trade_entered(
                    platform     = bot,
                    symbol       = position.symbol,
                    side         = position.side,
                    entry_price  = position.entry_price,
                    size_usd     = position.size_usd,
                    stop_loss    = position.stop_loss,
                    take_profit  = position.take_profit,
                    source_wallet= position.source_wallet,
                    leverage     = position.leverage,
                    trade_id     = position.trade_id,
                    opened_at    = position.opened_at,
                )
            )

    def update_position(self, bot: str, symbol: str,
                        current_price: float) -> Optional[str]:
        state = self.states[bot]
        if symbol not in state.positions:
            return None
        pos = state.positions[symbol]
        if pos.status != "OPEN":
            return None

        if pos.side in ("LONG", "YES"):
            pos.trailing_high = max(pos.trailing_high or current_price, current_price)
            trail_sl          = pos.trailing_high * (1 - pos.trailing_stop_pct)
            if current_price <= pos.stop_loss:
                return self._close_position(bot, symbol, current_price, "STOP_LOSS")
            if current_price >= pos.take_profit:
                return self._close_position(bot, symbol, current_price, "TAKE_PROFIT")
            if current_price <= trail_sl and pos.trailing_high > pos.entry_price:
                return self._close_position(bot, symbol, current_price, "TRAILING_STOP")
        else:
            pos.trailing_high = min(pos.trailing_high or current_price, current_price)
            trail_sl          = pos.trailing_high * (1 + pos.trailing_stop_pct)
            if current_price >= pos.stop_loss:
                return self._close_position(bot, symbol, current_price, "STOP_LOSS")
            if current_price <= pos.take_profit:
                return self._close_position(bot, symbol, current_price, "TAKE_PROFIT")
            if current_price >= trail_sl and pos.trailing_high < pos.entry_price:
                return self._close_position(bot, symbol, current_price, "TRAILING_STOP")
        return None

    def close_position(self, bot: str, symbol: str, price: float,
                       reason: str = "MANUAL") -> Optional[str]:
        return self._close_position(bot, symbol, price, reason)

    def _close_position(self, bot: str, symbol: str, price: float,
                        reason: str) -> str:
        state = self.states[bot]
        pos   = state.positions.get(symbol)
        if not pos or pos.status != "OPEN":
            return reason

        pos.status    = "CLOSED"
        pos.closed_at = datetime.utcnow()

        if pos.side in ("LONG", "YES"):
            pnl_pct = (price - pos.entry_price) / pos.entry_price
        else:
            pnl_pct = (pos.entry_price - price) / pos.entry_price
        pos.pnl_usd = pos.size_usd * pnl_pct

        state.current_equity = max(0, state.current_equity + pos.pnl_usd)
        state.peak_equity    = max(state.peak_equity, state.current_equity)

        if pos.pnl_usd >= 0:
            state.winning_trades += 1
        else:
            state.losing_trades += 1

        self._log(reason, bot, symbol,
                  f"@ {price} | PnL: ${pos.pnl_usd:+.2f}")
        logger.info(f"[{bot.upper()}] CLOSED {symbol} @ {price} | "
                    f"PnL: ${pos.pnl_usd:+.2f} | Reason: {reason}")

        # Telegram journal
        if self.journal:
            import asyncio
            coro = self.journal.trade_exited(
                platform    = bot,
                symbol      = pos.symbol,
                side        = pos.side,
                entry_price = pos.entry_price,
                exit_price  = price,
                size_usd    = pos.size_usd,
                pnl_usd     = pos.pnl_usd,
                stop_loss   = pos.stop_loss,
                reason      = reason,
                trade_id    = pos.trade_id,
                opened_at   = pos.opened_at,
            )
            asyncio.create_task(coro)

        return reason

    def _halt_bot(self, bot: str, reason: str) -> None:
        state = self.states[bot]
        state.halted      = True
        state.halt_reason = reason
        self._log("HALTED", bot, "—", reason)
        logger.critical(f"[{bot.upper()}] BOT HALTED — {reason}")

        if self.journal:
            import asyncio
            dd = (state.peak_equity - state.current_equity) / state.peak_equity * 100
            asyncio.create_task(
                self.journal.bot_halted(bot, reason, dd)
            )

    def _log(self, event: str, bot: str, symbol: str, detail: str) -> None:
        self.event_log.append({
            "ts": datetime.utcnow().isoformat(),
            "bot": bot, "event": event,
            "symbol": symbol, "detail": detail
        })

    def get_summary(self, bot: str) -> dict:
        state = self.states[bot]
        cfg   = getattr(self.config, bot)
        open_pos = [p for p in state.positions.values() if p.status == "OPEN"]
        drawdown = (state.peak_equity - state.current_equity) / state.peak_equity
        win_rate = (state.winning_trades / state.total_trades * 100
                    if state.total_trades > 0 else 0)
        return {
            "bot":            bot,
            "equity":         round(state.current_equity, 2),
            "pnl":            round(state.current_equity - cfg.allocated_capital_usd, 2),
            "drawdown_pct":   round(drawdown * 100, 2),
            "open_positions": len(open_pos),
            "total_trades":   state.total_trades,
            "win_rate":       round(win_rate, 1),
            "halted":         state.halted,
        }

    def compute_position_size(self, bot: str, entry_price: float,
                               stop_loss: float, risk_pct: float = 0.01) -> float:
        state        = self.states[bot]
        risk_dollars = state.current_equity * risk_pct
        sl_distance  = abs(entry_price - stop_loss) / entry_price
        if sl_distance == 0:
            return getattr(getattr(self.config, bot), "min_copy_size_usd")
        return round(risk_dollars / sl_distance, 2)
