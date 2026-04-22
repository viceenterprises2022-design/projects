"""
AlphaCopy - Unified Risk Manager
Enforces position limits, drawdown stops, and sizing across all 3 bots.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class RiskEvent(Enum):
    POSITION_OPENED   = "POSITION_OPENED"
    POSITION_CLOSED   = "POSITION_CLOSED"
    STOP_LOSS_HIT     = "STOP_LOSS_HIT"
    TAKE_PROFIT_HIT   = "TAKE_PROFIT_HIT"
    DRAWDOWN_HALT     = "DRAWDOWN_HALT"
    SIZE_CAPPED       = "SIZE_CAPPED"
    TRADE_SKIPPED     = "TRADE_SKIPPED"


@dataclass
class Position:
    bot: str                   # "hyperliquid" | "binance" | "polymarket"
    symbol: str
    side: str                  # "LONG" | "SHORT" | "YES" | "NO"
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
    status: str                = "OPEN"   # OPEN | CLOSED | STOPPED
    source_wallet: str         = ""        # Trader being copied
    trade_id: str              = ""


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
    """
    Central risk engine for all three copy bots.
    Call check_trade() before placing any order.
    Call update_position() on every price tick.
    """

    def __init__(self, config):
        self.config = config
        self.states: Dict[str, BotState] = {
            "hyperliquid": BotState("hyperliquid", config.hyperliquid.allocated_capital_usd,
                                    config.hyperliquid.allocated_capital_usd,
                                    config.hyperliquid.allocated_capital_usd),
            "binance":     BotState("binance",     config.binance.allocated_capital_usd,
                                    config.binance.allocated_capital_usd,
                                    config.binance.allocated_capital_usd),
            "polymarket":  BotState("polymarket",  config.polymarket.allocated_capital_usd,
                                    config.polymarket.allocated_capital_usd,
                                    config.polymarket.allocated_capital_usd),
        }
        self.event_log: List[dict] = []

    # ─────────────────────────────────────────────────────────────────────
    # Pre-trade checks
    # ─────────────────────────────────────────────────────────────────────
    def check_trade(self, bot: str, symbol: str, size_usd: float,
                    side: str, source_wallet: str) -> tuple[bool, str, float]:
        """
        Returns: (approved, reason, adjusted_size_usd)
        """
        state = self.states[bot]
        cfg   = getattr(self.config, bot)

        # 1. Bot halted?
        if state.halted:
            return False, f"Bot halted: {state.halt_reason}", 0.0

        # 2. Max open positions
        open_pos = [p for p in state.positions.values() if p.status == "OPEN"]
        if len(open_pos) >= cfg.max_open_positions:
            return False, f"Max open positions ({cfg.max_open_positions}) reached", 0.0

        # 3. Already have this symbol?
        if symbol in state.positions and state.positions[symbol].status == "OPEN":
            return False, f"Already in {symbol}", 0.0

        # 4. Drawdown check
        drawdown = (state.peak_equity - state.current_equity) / state.peak_equity
        if drawdown >= cfg.max_drawdown_pct:
            self._halt_bot(bot, f"Max drawdown {drawdown:.1%} hit")
            return False, "Drawdown limit triggered - bot halted", 0.0

        # 5. Size enforcement
        max_size = min(
            state.current_equity * cfg.max_position_pct,
            cfg.max_copy_size_usd
        )
        adjusted = max(cfg.min_copy_size_usd, min(size_usd, max_size))

        if adjusted != size_usd:
            self._log_event(bot, RiskEvent.SIZE_CAPPED,
                            f"{symbol}: {size_usd:.0f} → {adjusted:.0f} USD")

        return True, "OK", adjusted

    # ─────────────────────────────────────────────────────────────────────
    # Position lifecycle
    # ─────────────────────────────────────────────────────────────────────
    def open_position(self, bot: str, position: Position) -> None:
        state = self.states[bot]
        state.positions[position.symbol] = position
        state.total_trades += 1
        self._log_event(bot, RiskEvent.POSITION_OPENED,
                        f"{position.symbol} {position.side} ${position.size_usd:.0f} "
                        f"@ {position.entry_price} | SL:{position.stop_loss} TP:{position.take_profit}")
        logger.info(f"[{bot.upper()}] OPENED {position.symbol} {position.side} "
                    f"${position.size_usd:.0f} @ {position.entry_price}")

    def update_position(self, bot: str, symbol: str, current_price: float) -> Optional[str]:
        """
        Evaluate SL/TP/trailing stop.
        Returns action: None | "STOP_LOSS" | "TAKE_PROFIT" | "TRAILING_STOP"
        """
        state = self.states[bot]
        if symbol not in state.positions:
            return None
        pos = state.positions[symbol]
        if pos.status != "OPEN":
            return None

        # Trailing stop update
        if pos.side in ("LONG", "YES"):
            pos.trailing_high = max(pos.trailing_high or current_price, current_price)
            trail_price       = pos.trailing_high * (1 - pos.trailing_stop_pct)
            if current_price <= pos.stop_loss:
                return self._close_position(bot, symbol, current_price, "STOP_LOSS")
            if current_price >= pos.take_profit:
                return self._close_position(bot, symbol, current_price, "TAKE_PROFIT")
            if current_price <= trail_price and pos.trailing_high > pos.entry_price:
                return self._close_position(bot, symbol, current_price, "TRAILING_STOP")
        else:  # SHORT / NO
            pos.trailing_high = min(pos.trailing_high or current_price, current_price)
            trail_price       = pos.trailing_high * (1 + pos.trailing_stop_pct)
            if current_price >= pos.stop_loss:
                return self._close_position(bot, symbol, current_price, "STOP_LOSS")
            if current_price <= pos.take_profit:
                return self._close_position(bot, symbol, current_price, "TAKE_PROFIT")
            if current_price >= trail_price and pos.trailing_high < pos.entry_price:
                return self._close_position(bot, symbol, current_price, "TRAILING_STOP")
        return None

    def close_position(self, bot: str, symbol: str, current_price: float,
                       reason: str = "MANUAL") -> Optional[Position]:
        """Externally triggered close (e.g. trader closed their position)."""
        return self._close_position(bot, symbol, current_price, reason)

    def _close_position(self, bot: str, symbol: str, price: float,
                        reason: str) -> str:
        state = self.states[bot]
        pos   = state.positions.get(symbol)
        if not pos or pos.status != "OPEN":
            return reason

        pos.status    = "CLOSED"
        pos.closed_at = datetime.utcnow()

        # PnL calc
        if pos.side in ("LONG", "YES"):
            pnl_pct = (price - pos.entry_price) / pos.entry_price
        else:
            pnl_pct = (pos.entry_price - price) / pos.entry_price
        pos.pnl_usd = pos.size_usd * pnl_pct

        # Update equity
        state.current_equity = max(0, state.current_equity + pos.pnl_usd)
        state.peak_equity    = max(state.peak_equity, state.current_equity)

        if pos.pnl_usd >= 0:
            state.winning_trades += 1
        else:
            state.losing_trades += 1

        event = RiskEvent.STOP_LOSS_HIT if reason == "STOP_LOSS" else RiskEvent.TAKE_PROFIT_HIT
        self._log_event(bot, event,
                        f"{symbol} closed @ {price} | PnL: ${pos.pnl_usd:+.2f} | Reason: {reason}")
        logger.info(f"[{bot.upper()}] CLOSED {symbol} @ {price} | "
                    f"PnL: ${pos.pnl_usd:+.2f} | Reason: {reason}")
        return reason

    # ─────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────
    def _halt_bot(self, bot: str, reason: str) -> None:
        self.states[bot].halted      = True
        self.states[bot].halt_reason = reason
        self._log_event(bot, RiskEvent.DRAWDOWN_HALT, reason)
        logger.critical(f"[{bot.upper()}] BOT HALTED — {reason}")

    def _log_event(self, bot: str, event: RiskEvent, detail: str) -> None:
        self.event_log.append({
            "ts": datetime.utcnow().isoformat(),
            "bot": bot,
            "event": event.value,
            "detail": detail
        })

    def get_summary(self, bot: str) -> dict:
        state = self.states[bot]
        cfg   = getattr(self.config, bot)
        open_pos = [p for p in state.positions.values() if p.status == "OPEN"]
        drawdown = (state.peak_equity - state.current_equity) / state.peak_equity
        win_rate = (state.winning_trades / state.total_trades
                    if state.total_trades > 0 else 0)
        return {
            "bot":            bot,
            "equity":         round(state.current_equity, 2),
            "pnl":            round(state.current_equity - cfg.allocated_capital_usd, 2),
            "drawdown_pct":   round(drawdown * 100, 2),
            "open_positions": len(open_pos),
            "total_trades":   state.total_trades,
            "win_rate":       round(win_rate * 100, 2),
            "halted":         state.halted,
        }

    def compute_position_size(self, bot: str, entry_price: float,
                               stop_loss: float, risk_pct: float = 0.01) -> float:
        """
        Kelly-inspired fixed-risk sizing.
        risk_pct = fraction of equity to risk per trade (default 1%).
        """
        state        = self.states[bot]
        risk_dollars = state.current_equity * risk_pct
        sl_distance  = abs(entry_price - stop_loss) / entry_price
        if sl_distance == 0:
            return getattr(getattr(self.config, bot), "min_copy_size_usd")
        size = risk_dollars / sl_distance
        return round(size, 2)
