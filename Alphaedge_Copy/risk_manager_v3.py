"""
AlphaCopy — Unified Risk Manager v3
════════════════════════════════════════════════════════════════════════════════
Merges per-bot state tracking with the GlobalRiskEngine.
This is the ONLY class bots should interact with.

Every trade flows through:
    check_and_size_trade()  ← calls GlobalRiskEngine.validate_trade()
    open_position()         ← records position, fires Telegram ENTERED alert
    update_position()       ← SL/TP/trailing evaluation on every tick
    close_position()        ← records close, fires Telegram EXITED alert,
                               calls GlobalRiskEngine.on_position_closed()
════════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, TYPE_CHECKING

from core.global_risk_engine import GlobalRiskEngine, TradeValidationResult, KillSwitchEvent

if TYPE_CHECKING:
    from utils.telegram_journal import TelegramJournal
    from config.settings import GlobalConfig

logger = logging.getLogger("alphacopy.risk")


# ─────────────────────────────────────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Position:
    bot:          str
    symbol:       str
    side:         str              # LONG | SHORT | YES | NO
    entry_price:  float
    size_usd:     float
    size_units:   float
    stop_loss:    float
    take_profit:  float
    trailing_stop_pct:    float    = 0.03
    trailing_high:        float    = 0.0
    opened_at:            datetime = field(default_factory=datetime.utcnow)
    closed_at:    Optional[datetime] = None
    pnl_usd:      float            = 0.0
    status:       str              = "OPEN"    # OPEN | CLOSED
    source_wallet: str             = ""
    trade_id:     str              = ""
    leverage:     int              = 1
    # Risk metadata (set by GlobalRiskEngine)
    risk_usd:     float            = 0.0
    risk_pct:     float            = 0.0
    rr_ratio:     float            = 0.0


@dataclass
class BotState:
    bot_name:         str
    allocated_capital: float
    current_equity:   float
    peak_equity:      float
    positions:        Dict[str, Position] = field(default_factory=dict)
    total_trades:     int  = 0
    winning_trades:   int  = 0
    losing_trades:    int  = 0
    halted:           bool = False
    halt_reason:      str  = ""


# ─────────────────────────────────────────────────────────────────────────────
# Unified Risk Manager
# ─────────────────────────────────────────────────────────────────────────────

class RiskManager:
    """
    Central risk manager. One instance shared across all three bots.

    Args:
        config:  GlobalConfig (from config/settings.py)
        engine:  GlobalRiskEngine (holds all 6 rule validators)
        journal: TelegramJournal (for trade alerts)
    """

    def __init__(self,
                 config: "GlobalConfig",
                 engine: Optional[GlobalRiskEngine] = None,
                 journal: Optional["TelegramJournal"] = None):
        self.config  = config
        self.engine  = engine or GlobalRiskEngine()
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
    # STEP 1: Validate + size a trade (call before building Position)
    # ─────────────────────────────────────────────────────────────────────
    def check_and_size_trade(self,
                              bot: str,
                              symbol: str,
                              side: str,
                              entry_price: float,
                              stop_loss: Optional[float],
                              take_profit: Optional[float],
                              requested_size_usd: float,
                              source_wallet: str = "",
                              live_mode: bool = False) -> TradeValidationResult:
        """
        Master pre-trade gate.
        Returns TradeValidationResult — use .approved to decide, 
        .adjusted_size_usd / .computed_sl / .computed_tp for the actual order.
        """
        state = self.states.get(bot)
        if not state:
            return self.engine._reject(
                __import__('core.global_risk_engine', fromlist=['RuleViolation']).RuleViolation.KILL_SWITCH_BOT,
                f"Unknown bot: {bot}", requested_size_usd, 0, 0, 0, 0
            )

        # Bot-level halted flag (set by kill switch or manually)
        if state.halted:
            from core.global_risk_engine import RuleViolation
            return self.engine._reject(
                RuleViolation.KILL_SWITCH_BOT,
                f"Bot '{bot}' halted: {state.halt_reason}",
                requested_size_usd, stop_loss or 0, take_profit or 0, 0, 0
            )

        # Per-bot position cap (before calling global engine)
        cfg      = getattr(self.config, bot)
        open_pos = [p for p in state.positions.values() if p.status == "OPEN"]
        if len(open_pos) >= cfg.max_open_positions:
            from core.global_risk_engine import RuleViolation
            return self.engine._reject(
                RuleViolation.GLOBAL_POSITION_CAP,
                f"Bot '{bot}': max open positions ({cfg.max_open_positions}) reached",
                requested_size_usd, stop_loss or 0, take_profit or 0, 0, 0
            )

        # Duplicate symbol guard
        if symbol in state.positions and state.positions[symbol].status == "OPEN":
            from core.global_risk_engine import RuleViolation
            return self.engine._reject(
                RuleViolation.GLOBAL_POSITION_CAP,
                f"Already holding {symbol} on {bot}",
                requested_size_usd, stop_loss or 0, take_profit or 0, 0, 0
            )

        # ── Delegate to GlobalRiskEngine for all 6 rules ────────────────
        result = self.engine.validate_trade(
            bot               = bot,
            symbol            = symbol,
            side              = side,
            entry_price       = entry_price,
            stop_loss         = stop_loss,
            take_profit       = take_profit,
            requested_size_usd = requested_size_usd,
            all_states        = self.states,
            live_mode         = live_mode,
        )

        if not result.approved:
            self._log("REJECTED", bot, symbol, str(result))
            if self.journal:
                asyncio.create_task(
                    self.journal.trade_skipped(bot, symbol, result.reason)
                )

        return result

    # ─────────────────────────────────────────────────────────────────────
    # STEP 2: Record opened position
    # ─────────────────────────────────────────────────────────────────────
    def open_position(self, bot: str, position: Position) -> None:
        state = self.states[bot]
        state.positions[position.symbol] = position
        state.total_trades += 1

        self._log("OPENED", bot, position.symbol,
                  f"{position.side} ${position.size_usd:.0f} @ {position.entry_price} | "
                  f"Risk: ${position.risk_usd:.2f} ({position.risk_pct:.2f}%) | "
                  f"R:R: {position.rr_ratio:.1f}")

        logger.info(
            f"[{bot.upper()}] OPENED  {position.symbol} {position.side} "
            f"${position.size_usd:.0f} @ {position.entry_price:.4f} | "
            f"SL: {position.stop_loss:.4f}  TP: {position.take_profit:.4f} | "
            f"Risk: ${position.risk_usd:.2f} ({position.risk_pct:.2f}%) | "
            f"R:R: {position.rr_ratio:.1f} | ID: {position.trade_id}"
        )

        # Notify kill switch engine of new trade
        kill_event = self.engine.on_position_opened(bot)
        if kill_event:
            self._apply_kill_switch(kill_event)

        # Telegram alert
        if self.journal:
            asyncio.create_task(
                self.journal.trade_entered(
                    platform      = bot,
                    symbol        = position.symbol,
                    side          = position.side,
                    entry_price   = position.entry_price,
                    size_usd      = position.size_usd,
                    stop_loss     = position.stop_loss,
                    take_profit   = position.take_profit,
                    source_wallet = position.source_wallet,
                    leverage      = position.leverage,
                    trade_id      = position.trade_id,
                    opened_at     = position.opened_at,
                )
            )

    # ─────────────────────────────────────────────────────────────────────
    # STEP 3: Update on every price tick (SL/TP/trailing)
    # ─────────────────────────────────────────────────────────────────────
    def update_position(self, bot: str, symbol: str, current_price: float) -> Optional[str]:
        state = self.states[bot]
        pos   = state.positions.get(symbol)
        if not pos or pos.status != "OPEN":
            return None

        long_side = pos.side in ("LONG", "YES")

        if long_side:
            pos.trailing_high = max(pos.trailing_high or current_price, current_price)
            trail_sl = pos.trailing_high * (1 - pos.trailing_stop_pct)

            if current_price <= pos.stop_loss:
                return self._close_position(bot, symbol, current_price, "STOP_LOSS")
            if current_price >= pos.take_profit:
                return self._close_position(bot, symbol, current_price, "TAKE_PROFIT")
            if current_price <= trail_sl and pos.trailing_high > pos.entry_price * 1.005:
                return self._close_position(bot, symbol, current_price, "TRAILING_STOP")
        else:
            pos.trailing_high = min(pos.trailing_high or current_price, current_price)
            trail_sl = pos.trailing_high * (1 + pos.trailing_stop_pct)

            if current_price >= pos.stop_loss:
                return self._close_position(bot, symbol, current_price, "STOP_LOSS")
            if current_price <= pos.take_profit:
                return self._close_position(bot, symbol, current_price, "TAKE_PROFIT")
            if current_price >= trail_sl and pos.trailing_high < pos.entry_price * 0.995:
                return self._close_position(bot, symbol, current_price, "TRAILING_STOP")
        return None

    # ─────────────────────────────────────────────────────────────────────
    # STEP 4: External close (trader closed, dashboard CLOSE button, etc.)
    # ─────────────────────────────────────────────────────────────────────
    def close_position(self, bot: str, symbol: str, price: float,
                       reason: str = "MANUAL") -> Optional[str]:
        return self._close_position(bot, symbol, price, reason)

    def _close_position(self, bot: str, symbol: str,
                        price: float, reason: str) -> str:
        state = self.states[bot]
        pos   = state.positions.get(symbol)
        if not pos or pos.status != "OPEN":
            return reason

        pos.status    = "CLOSED"
        pos.closed_at = datetime.utcnow()

        long_side    = pos.side in ("LONG", "YES")
        pnl_pct      = ((price - pos.entry_price) / pos.entry_price
                        if long_side else
                        (pos.entry_price - price) / pos.entry_price)
        pos.pnl_usd  = pos.size_usd * pnl_pct

        state.current_equity = max(0.0, state.current_equity + pos.pnl_usd)
        state.peak_equity    = max(state.peak_equity, state.current_equity)

        if pos.pnl_usd >= 0:
            state.winning_trades += 1
        else:
            state.losing_trades += 1

        self._log(reason, bot, symbol,
                  f"@ {price:.4f} | PnL: ${pos.pnl_usd:+.2f} "
                  f"({pnl_pct:+.2%}) | R achieved: {pnl_pct / (pos.risk_pct / 100):.1f}R"
                  if pos.risk_pct else "")

        logger.info(
            f"[{bot.upper()}] CLOSED  {symbol} @ {price:.4f} | "
            f"PnL: ${pos.pnl_usd:+.2f} ({pnl_pct:+.2%}) | "
            f"Reason: {reason} | ID: {pos.trade_id}"
        )

        # GlobalRiskEngine post-close check (kill switches)
        kill_event = self.engine.on_position_closed(bot, pos.pnl_usd, self.states)
        if kill_event:
            self._apply_kill_switch(kill_event)

        # Telegram journal
        if self.journal:
            asyncio.create_task(
                self.journal.trade_exited(
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
            )

        return reason

    # ─────────────────────────────────────────────────────────────────────
    # Kill switch application
    # ─────────────────────────────────────────────────────────────────────
    def _apply_kill_switch(self, event: KillSwitchEvent) -> None:
        from core.global_risk_engine import KillSwitchLevel
        if event.level == KillSwitchLevel.BOT_HALT and event.bot:
            state = self.states.get(event.bot)
            if state:
                state.halted      = True
                state.halt_reason = event.trigger
                logger.critical(f"[KILL SWITCH] {event.bot.upper()} HALTED: {event.trigger}")

        elif event.level in (KillSwitchLevel.PORTFOLIO, KillSwitchLevel.EMERGENCY):
            for bot_name, state in self.states.items():
                state.halted      = True
                state.halt_reason = f"Portfolio kill switch: {event.trigger}"
            logger.critical(f"[KILL SWITCH] ALL BOTS HALTED: {event.trigger}")

    # ─────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────
    def _log(self, event: str, bot: str, symbol: str, detail: str) -> None:
        self.event_log.append({
            "ts": datetime.utcnow().isoformat(),
            "bot": bot, "event": event,
            "symbol": symbol, "detail": detail
        })

    def get_summary(self, bot: str) -> dict:
        state    = self.states[bot]
        cfg      = getattr(self.config, bot)
        open_pos = [p for p in state.positions.values() if p.status == "OPEN"]
        drawdown = (state.peak_equity - state.current_equity) / state.peak_equity
        win_rate = (state.winning_trades / state.total_trades * 100
                    if state.total_trades > 0 else 0.0)
        return {
            "bot":            bot,
            "equity":         round(state.current_equity, 2),
            "pnl":            round(state.current_equity - cfg.allocated_capital_usd, 2),
            "drawdown_pct":   round(drawdown * 100, 2),
            "open_positions": len(open_pos),
            "total_trades":   state.total_trades,
            "win_rate":       round(win_rate, 1),
            "halted":         state.halted,
            "halt_reason":    state.halt_reason,
        }

    def get_full_risk_status(self) -> dict:
        """For dashboard: full risk engine status."""
        return self.engine.get_full_status(self.states)

    def build_position(self, bot: str, symbol: str, side: str,
                        entry_price: float, source_wallet: str,
                        validation: TradeValidationResult,
                        leverage: int = 1) -> Position:
        """
        Convenience method: build a Position object from a validated result.
        Use after check_and_size_trade() returns approved=True.
        """
        return Position(
            bot           = bot,
            symbol        = symbol,
            side          = side,
            entry_price   = entry_price,
            size_usd      = validation.adjusted_size_usd,
            size_units     = validation.adjusted_size_usd / entry_price,
            stop_loss     = validation.computed_sl,
            take_profit   = validation.computed_tp,
            trailing_stop_pct = getattr(self.config, bot).trailing_stop_pct,
            trailing_high = entry_price,
            source_wallet = source_wallet,
            trade_id      = str(uuid.uuid4())[:8],
            leverage      = leverage,
            risk_usd      = validation.risk_usd,
            risk_pct      = validation.risk_pct,
            rr_ratio      = validation.actual_rr,
        )
