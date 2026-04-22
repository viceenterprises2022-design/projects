"""
AlphaCopy — Global Risk Engine
════════════════════════════════════════════════════════════════════════════════
The single enforcement layer sitting ABOVE all three bots.
Every trade proposal must pass through validate_trade() before execution.
Every price tick runs through update_all() to check kill-switch thresholds.

Industry rules enforced:
  Rule 1 — 1%–2% Risk Per Trade     → compute_risk_sized_position()
  Rule 2 — Mandatory Stop-Loss      → validate_stop_loss()
  Rule 3 — Risk-Reward Ratio ≥ 1:2  → validate_rr_ratio()
  Rule 4 — Diversification          → validate_diversification()
  Rule 5 — Kill Switches            → check_kill_switches()
  Rule 6 — Algo Validation          → AlgoValidator class
════════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from core.risk_config import GlobalRiskConfig, GLOBAL_RISK, CORRELATION_GROUPS

if TYPE_CHECKING:
    from core.risk_manager_v2 import Position, BotState
    from utils.telegram_journal import TelegramJournal

logger = logging.getLogger("alphacopy.global_risk")


# ─────────────────────────────────────────────────────────────────────────────
# Enums & Structured Results
# ─────────────────────────────────────────────────────────────────────────────

class RuleViolation(Enum):
    NONE                    = "NONE"
    RISK_PCT_EXCEEDED       = "RISK_PCT_EXCEEDED"
    MISSING_STOP_LOSS       = "MISSING_STOP_LOSS"
    INVALID_STOP_LOSS       = "INVALID_STOP_LOSS"
    RR_BELOW_MINIMUM        = "RR_BELOW_MINIMUM"
    CORRELATED_EXPOSURE     = "CORRELATED_EXPOSURE"
    SINGLE_ASSET_LIMIT      = "SINGLE_ASSET_LIMIT"
    BOT_ALLOCATION_LIMIT    = "BOT_ALLOCATION_LIMIT"
    GLOBAL_POSITION_CAP     = "GLOBAL_POSITION_CAP"
    KILL_SWITCH_PORTFOLIO   = "KILL_SWITCH_PORTFOLIO"
    KILL_SWITCH_BOT         = "KILL_SWITCH_BOT"
    KILL_SWITCH_VELOCITY    = "KILL_SWITCH_VELOCITY"
    KILL_SWITCH_DAILY_LOSS  = "KILL_SWITCH_DAILY_LOSS"
    CONSECUTIVE_LOSSES      = "CONSECUTIVE_LOSSES"
    ANNOUNCEMENT_WINDOW     = "ANNOUNCEMENT_WINDOW"
    SIZE_EXCEEDS_HARD_CAP   = "SIZE_EXCEEDS_HARD_CAP"
    ALGO_NOT_VALIDATED      = "ALGO_NOT_VALIDATED"


class KillSwitchLevel(Enum):
    NONE       = "NONE"
    BOT_HALT   = "BOT_HALT"     # Stop one bot, others continue
    PORTFOLIO  = "PORTFOLIO"    # Stop all bots, close all positions
    EMERGENCY  = "EMERGENCY"    # Immediate market-close everything


@dataclass
class TradeValidationResult:
    """Immutable result object returned for every trade proposal."""
    approved: bool
    rule: RuleViolation
    reason: str
    original_size_usd: float
    adjusted_size_usd: float
    computed_sl: float        # Guaranteed SL price
    computed_tp: float        # Computed TP at target R:R
    actual_rr: float
    risk_usd: float           # Dollar risk on this trade
    risk_pct: float           # % of total portfolio being risked

    def __str__(self) -> str:
        status = "✅ APPROVED" if self.approved else "❌ REJECTED"
        return (
            f"{status} | {self.rule.value} | {self.reason} | "
            f"Size: ${self.adjusted_size_usd:.0f} | "
            f"Risk: ${self.risk_usd:.2f} ({self.risk_pct:.2f}%) | "
            f"R:R: {self.actual_rr:.1f}"
        )


@dataclass
class KillSwitchEvent:
    level: KillSwitchLevel
    trigger: str
    bot: Optional[str]        # None = all bots
    triggered_at: datetime    = field(default_factory=datetime.utcnow)
    value_at_trigger: float   = 0.0
    threshold: float          = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Rule 2: Stop-Loss Validator
# ─────────────────────────────────────────────────────────────────────────────

class StopLossValidator:
    """
    Validates and enforces mandatory stop-loss on every trade.
    Computes a safe SL if none provided or if provided SL is invalid.
    """

    def __init__(self, cfg: GlobalRiskConfig):
        self.cfg = cfg

    def validate(self, entry: float, sl: Optional[float], side: str) -> Tuple[bool, float, str]:
        """
        Returns: (valid, final_sl_price, message)
        final_sl_price is always set — either validated original or computed default.
        """
        if sl is None or sl <= 0:
            sl = self._compute_default_sl(entry, side)
            msg = f"No SL provided — computed default {self.cfg.default_sl_pct:.0%} SL: {sl:.4f}"
            return True, sl, msg

        # Validate direction
        if side in ("LONG", "YES") and sl >= entry:
            sl = self._compute_default_sl(entry, side)
            return True, sl, f"SL above entry for LONG — reset to {sl:.4f}"

        if side in ("SHORT", "NO") and sl <= entry:
            sl = self._compute_default_sl(entry, side)
            return True, sl, f"SL below entry for SHORT — reset to {sl:.4f}"

        # Validate distance
        sl_dist_pct = abs(entry - sl) / entry

        if sl_dist_pct < self.cfg.min_sl_distance_pct:
            # Too tight — widen to minimum
            sl = self._compute_sl_at_pct(entry, self.cfg.min_sl_distance_pct, side)
            return True, sl, f"SL too tight ({sl_dist_pct:.2%}) — widened to min {self.cfg.min_sl_distance_pct:.1%}: {sl:.4f}"

        if sl_dist_pct > self.cfg.max_sl_distance_pct:
            # Too wide — tighten to maximum
            sl = self._compute_sl_at_pct(entry, self.cfg.max_sl_distance_pct, side)
            return True, sl, f"SL too wide ({sl_dist_pct:.2%}) — tightened to max {self.cfg.max_sl_distance_pct:.1%}: {sl:.4f}"

        return True, sl, f"SL validated: {sl:.4f} ({sl_dist_pct:.2%} from entry)"

    def _compute_default_sl(self, entry: float, side: str) -> float:
        return self._compute_sl_at_pct(entry, self.cfg.default_sl_pct, side)

    @staticmethod
    def _compute_sl_at_pct(entry: float, pct: float, side: str) -> float:
        if side in ("LONG", "YES"):
            return round(entry * (1 - pct), 8)
        return round(entry * (1 + pct), 8)


# ─────────────────────────────────────────────────────────────────────────────
# Rule 1 + 3: Position Sizer (1% Rule + R:R Enforcement)
# ─────────────────────────────────────────────────────────────────────────────

class PositionSizer:
    """
    Computes the correct position size using fixed-risk model (1% rule),
    then validates the R:R ratio of the trade.

    Formula:
        Risk $ = Portfolio Equity × risk_per_trade_pct
        SL Distance = |entry - stop_loss| / entry
        Position Size = Risk $ / SL Distance
    """

    def __init__(self, cfg: GlobalRiskConfig):
        self.cfg = cfg

    def compute(self,
                portfolio_equity: float,
                entry: float,
                stop_loss: float,
                take_profit: float,
                side: str,
                requested_size_usd: Optional[float] = None) -> Tuple[float, float, float, float]:
        """
        Returns: (final_size_usd, risk_usd, risk_pct, actual_rr)
        """
        sl_dist_pct = abs(entry - stop_loss) / entry
        tp_dist_pct = abs(take_profit - entry) / entry if take_profit else 0

        # 1% rule sizing
        risk_dollars = portfolio_equity * self.cfg.risk_per_trade_pct
        if sl_dist_pct > 0:
            risk_sized = risk_dollars / sl_dist_pct
        else:
            risk_sized = portfolio_equity * self.cfg.risk_per_trade_pct * 10

        # Hard caps
        risk_sized = min(risk_sized, self.cfg.max_position_size_usd)
        risk_sized = min(risk_sized, portfolio_equity * self.cfg.max_risk_per_trade_pct / sl_dist_pct
                         if sl_dist_pct > 0 else risk_sized)

        # If a requested size is given, take the smaller (never increase risk)
        if requested_size_usd:
            final_size = min(risk_sized, requested_size_usd)
        else:
            final_size = risk_sized

        # Recalculate actual risk at final size
        actual_risk = final_size * sl_dist_pct
        actual_risk_pct = actual_risk / portfolio_equity * 100
        actual_rr = (tp_dist_pct / sl_dist_pct) if sl_dist_pct > 0 else 0

        return round(final_size, 2), round(actual_risk, 2), round(actual_risk_pct, 3), round(actual_rr, 2)

    def compute_tp_for_rr(self, entry: float, stop_loss: float, side: str,
                           target_rr: float) -> float:
        """Compute a take-profit price that achieves the target R:R."""
        sl_dist = abs(entry - stop_loss)
        tp_dist = sl_dist * target_rr
        if side in ("LONG", "YES"):
            return round(entry + tp_dist, 8)
        return round(entry - tp_dist, 8)


# ─────────────────────────────────────────────────────────────────────────────
# Rule 4: Diversification Engine
# ─────────────────────────────────────────────────────────────────────────────

class DiversificationEngine:
    """
    Tracks portfolio-wide correlations and enforces exposure limits.
    Prevents concentration in correlated assets across all three bots.
    """

    def __init__(self, cfg: GlobalRiskConfig):
        self.cfg = cfg

    def _get_correlation_group(self, symbol: str) -> Optional[str]:
        symbol_upper = symbol.upper()
        for group, members in CORRELATION_GROUPS.items():
            for m in members:
                if m.upper() in symbol_upper or symbol_upper in m.upper():
                    return group
        return None

    def check_new_position(self,
                            symbol: str,
                            proposed_size_usd: float,
                            bot: str,
                            all_states: Dict,
                            portfolio_equity: float) -> Tuple[bool, str]:
        """
        Returns: (approved, reason)
        Checks single-asset limit, group exposure, bot allocation.
        """
        # Gather all open positions across all bots
        all_positions = []
        for b, state in all_states.items():
            for sym, pos in state.positions.items():
                if pos.status == "OPEN":
                    all_positions.append(pos)

        # 1. Global open position cap
        if len(all_positions) >= self.cfg.max_open_positions_global:
            return False, f"Global position cap reached ({self.cfg.max_open_positions_global})"

        # 2. Single asset exposure
        symbol_exposure = sum(
            p.size_usd for p in all_positions
            if p.symbol.upper() == symbol.upper()
        )
        if (symbol_exposure + proposed_size_usd) / portfolio_equity > self.cfg.max_single_asset_pct:
            current_pct = (symbol_exposure + proposed_size_usd) / portfolio_equity * 100
            return False, (
                f"Single-asset limit: {symbol} would be {current_pct:.1f}% "
                f"(max {self.cfg.max_single_asset_pct:.0%})"
            )

        # 3. Correlation group exposure
        group = self._get_correlation_group(symbol)
        if group:
            group_members = CORRELATION_GROUPS[group]
            group_exposure = sum(
                p.size_usd for p in all_positions
                if self._get_correlation_group(p.symbol) == group
            )
            if (group_exposure + proposed_size_usd) / portfolio_equity > self.cfg.max_correlated_exposure_pct:
                current_pct = (group_exposure + proposed_size_usd) / portfolio_equity * 100
                return False, (
                    f"Correlated group '{group}' would be {current_pct:.1f}% "
                    f"(max {self.cfg.max_correlated_exposure_pct:.0%})"
                )

        # 4. Bot allocation limit
        bot_equity = all_states[bot].current_equity if bot in all_states else portfolio_equity / 3
        bot_exposure = sum(p.size_usd for p in all_positions if p.bot == bot)
        if (bot_exposure + proposed_size_usd) / portfolio_equity > self.cfg.max_single_bot_pct:
            current_pct = (bot_exposure + proposed_size_usd) / portfolio_equity * 100
            return False, (
                f"Bot '{bot}' allocation would be {current_pct:.1f}% "
                f"(max {self.cfg.max_single_bot_pct:.0%})"
            )

        return True, f"Diversification OK (group: {group or 'UNCORRELATED'})"

    def get_exposure_report(self, all_states: Dict, portfolio_equity: float) -> dict:
        """Returns current exposure breakdown for dashboard."""
        all_positions = [
            pos for state in all_states.values()
            for pos in state.positions.values()
            if pos.status == "OPEN"
        ]
        total_exposure  = sum(p.size_usd for p in all_positions)
        by_asset        = defaultdict(float)
        by_group        = defaultdict(float)
        by_bot          = defaultdict(float)

        for p in all_positions:
            by_asset[p.symbol] += p.size_usd
            group = self._get_correlation_group(p.symbol) or "UNCORRELATED"
            by_group[group] += p.size_usd
            by_bot[p.bot]   += p.size_usd

        return {
            "total_exposure_usd": round(total_exposure, 2),
            "total_exposure_pct": round(total_exposure / portfolio_equity * 100, 1),
            "by_asset":  {k: round(v / portfolio_equity * 100, 1) for k, v in sorted(by_asset.items())},
            "by_group":  {k: round(v / portfolio_equity * 100, 1) for k, v in sorted(by_group.items())},
            "by_bot":    {k: round(v / portfolio_equity * 100, 1) for k, v in sorted(by_bot.items())},
            "open_count": len(all_positions),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Rule 5: Kill Switch Engine
# ─────────────────────────────────────────────────────────────────────────────

class KillSwitchEngine:
    """
    Monitors real-time thresholds and triggers emergency halts.

    Triggers:
      BOT_HALT    — one bot exceeds drawdown/daily loss/consecutive losses
      PORTFOLIO   — overall portfolio exceeds thresholds
      EMERGENCY   — loss velocity anomaly (algo gone rogue)
    """

    def __init__(self, cfg: GlobalRiskConfig, journal: Optional["TelegramJournal"] = None):
        self.cfg     = cfg
        self.journal = journal

        # State tracking
        self._bot_halted: Dict[str, bool] = {}
        self._portfolio_halted: bool      = False
        self._kill_switch_log: List[KillSwitchEvent] = []

        # Daily P&L tracking (reset at midnight UTC)
        self._daily_start_equity: Dict[str, float] = {}
        self._daily_start_date: date                = date.today()

        # Weekly P&L tracking
        self._weekly_start_equity: Dict[str, float] = {}

        # Consecutive loss counter per bot
        self._consecutive_losses: Dict[str, int] = defaultdict(int)

        # Trade velocity tracker (rolling 1-hour window)
        self._trade_timestamps: Dict[str, deque] = defaultdict(lambda: deque(maxlen=200))
        self._daily_trade_counts: Dict[str, int] = defaultdict(int)

        # 1-minute PnL tracker for emergency kill
        self._recent_pnl: deque = deque(maxlen=100)

    # ── Main check called on every position close ─────────────────────────
    def on_trade_closed(self, bot: str, pnl_usd: float, current_equity: float,
                         peak_equity: float, all_equities: Dict[str, float],
                         all_peaks: Dict[str, float]) -> Optional[KillSwitchEvent]:
        """
        Call after every closed position.
        Returns a KillSwitchEvent if a trigger fires, else None.
        """
        self._reset_daily_if_needed(all_equities, all_peaks)

        # Track consecutive losses per bot
        if pnl_usd < 0:
            self._consecutive_losses[bot] += 1
        else:
            self._consecutive_losses[bot] = 0

        # Track rapid losses (emergency velocity check)
        self._recent_pnl.append((datetime.utcnow(), pnl_usd))

        return self._evaluate_all(bot, current_equity, peak_equity,
                                  all_equities, all_peaks)

    def on_trade_opened(self, bot: str) -> Optional[KillSwitchEvent]:
        """Track trade velocity."""
        now = datetime.utcnow()
        self._trade_timestamps[bot].append(now)
        self._daily_trade_counts[bot] += 1

        # Velocity: trades in last hour
        hour_ago = now - timedelta(hours=1)
        recent   = [t for t in self._trade_timestamps[bot] if t > hour_ago]
        if len(recent) > self.cfg.max_trades_per_hour:
            return self._fire(
                KillSwitchLevel.BOT_HALT, bot,
                f"Trade velocity anomaly: {len(recent)} trades in 1 hour "
                f"(max {self.cfg.max_trades_per_hour})",
                len(recent), self.cfg.max_trades_per_hour
            )

        if self._daily_trade_counts[bot] > self.cfg.max_trades_per_day:
            return self._fire(
                KillSwitchLevel.PORTFOLIO,
                bot,
                f"Daily trade count exceeded: {self._daily_trade_counts[bot]}",
                self._daily_trade_counts[bot], self.cfg.max_trades_per_day
            )
        return None

    # ── Periodic check (call every 60 seconds from main loop) ────────────
    def periodic_check(self, all_states: Dict) -> Optional[KillSwitchEvent]:
        """Heartbeat checks: portfolio DD, weekly loss, stale positions."""
        all_equities = {b: s.current_equity for b, s in all_states.items()}
        all_peaks    = {b: s.peak_equity    for b, s in all_states.items()}
        self._reset_daily_if_needed(all_equities, all_peaks)

        portfolio_equity = sum(all_equities.values())
        portfolio_peak   = sum(all_peaks.values())

        # Portfolio drawdown
        port_dd = (portfolio_peak - portfolio_equity) / portfolio_peak
        if port_dd >= self.cfg.portfolio_max_drawdown_pct:
            return self._fire(
                KillSwitchLevel.PORTFOLIO, None,
                f"Portfolio drawdown {port_dd:.1%} exceeds {self.cfg.portfolio_max_drawdown_pct:.1%}",
                port_dd * 100, self.cfg.portfolio_max_drawdown_pct * 100
            )

        # Per-bot checks
        for bot, state in all_states.items():
            event = self._evaluate_bot(bot, state.current_equity, state.peak_equity)
            if event:
                return event

        # 1-minute emergency loss velocity
        now     = datetime.utcnow()
        min_ago = now - timedelta(minutes=1)
        recent_loss = sum(
            pnl for ts, pnl in self._recent_pnl
            if ts > min_ago and pnl < 0
        )
        if abs(recent_loss) > self.cfg.max_loss_in_1min_usd:
            return self._fire(
                KillSwitchLevel.EMERGENCY, None,
                f"Emergency: ${abs(recent_loss):.0f} loss in 60s "
                f"(threshold ${self.cfg.max_loss_in_1min_usd:.0f})",
                abs(recent_loss), self.cfg.max_loss_in_1min_usd
            )
        return None

    # ── Internal helpers ─────────────────────────────────────────────────
    def _evaluate_all(self, bot: str, current_equity: float, peak_equity: float,
                      all_equities: Dict, all_peaks: Dict) -> Optional[KillSwitchEvent]:
        # Bot-level checks
        event = self._evaluate_bot(bot, current_equity, peak_equity)
        if event:
            return event

        # Portfolio-level daily loss
        portfolio_equity = sum(all_equities.values())
        start_equity     = sum(self._daily_start_equity.values())
        if start_equity > 0:
            daily_loss_pct = (start_equity - portfolio_equity) / start_equity
            if daily_loss_pct >= self.cfg.portfolio_daily_loss_pct:
                return self._fire(
                    KillSwitchLevel.PORTFOLIO, None,
                    f"Daily loss limit: portfolio down {daily_loss_pct:.1%} "
                    f"(limit {self.cfg.portfolio_daily_loss_pct:.1%})",
                    daily_loss_pct * 100, self.cfg.portfolio_daily_loss_pct * 100
                )
        return None

    def _evaluate_bot(self, bot: str, equity: float,
                      peak: float) -> Optional[KillSwitchEvent]:
        # Max drawdown
        dd = (peak - equity) / peak if peak > 0 else 0
        if dd >= self.cfg.bot_max_drawdown_pct:
            return self._fire(
                KillSwitchLevel.BOT_HALT, bot,
                f"{bot.upper()} drawdown {dd:.1%} exceeds {self.cfg.bot_max_drawdown_pct:.1%}",
                dd * 100, self.cfg.bot_max_drawdown_pct * 100
            )

        # Daily loss per bot
        start = self._daily_start_equity.get(bot, equity)
        daily_loss_pct = (start - equity) / start if start > 0 else 0
        if daily_loss_pct >= self.cfg.bot_daily_loss_pct:
            return self._fire(
                KillSwitchLevel.BOT_HALT, bot,
                f"{bot.upper()} daily loss {daily_loss_pct:.1%} exceeds {self.cfg.bot_daily_loss_pct:.1%}",
                daily_loss_pct * 100, self.cfg.bot_daily_loss_pct * 100
            )

        # Consecutive losses
        consec = self._consecutive_losses.get(bot, 0)
        if consec >= self.cfg.consecutive_loss_limit:
            return self._fire(
                KillSwitchLevel.BOT_HALT, bot,
                f"{bot.upper()} {consec} consecutive losses (limit {self.cfg.consecutive_loss_limit})",
                consec, self.cfg.consecutive_loss_limit
            )
        return None

    def _fire(self, level: KillSwitchLevel, bot: Optional[str],
              trigger: str, value: float, threshold: float) -> KillSwitchEvent:
        event = KillSwitchEvent(
            level=level, trigger=trigger, bot=bot,
            value_at_trigger=value, threshold=threshold
        )
        self._kill_switch_log.append(event)
        logger.critical(f"🚨 KILL SWITCH [{level.value}] | Bot: {bot} | {trigger}")

        if bot:
            self._bot_halted[bot] = True
        if level in (KillSwitchLevel.PORTFOLIO, KillSwitchLevel.EMERGENCY):
            self._portfolio_halted = True

        return event

    def _reset_daily_if_needed(self, all_equities: Dict, all_peaks: Dict) -> None:
        today = date.today()
        if today != self._daily_start_date:
            self._daily_start_date    = today
            self._daily_start_equity  = dict(all_equities)
            self._daily_trade_counts  = defaultdict(int)
            logger.info("Daily risk counters reset.")

    def is_halted(self, bot: Optional[str] = None) -> bool:
        if self._portfolio_halted:
            return True
        if bot:
            return self._bot_halted.get(bot, False)
        return False

    def reset_bot(self, bot: str) -> None:
        """Manually resume a halted bot (after human review)."""
        self._bot_halted[bot]           = False
        self._consecutive_losses[bot]   = 0
        logger.warning(f"[KILL SWITCH] {bot.upper()} manually resumed by operator.")

    def reset_all(self) -> None:
        """Full system reset (emergency use only)."""
        self._bot_halted       = {}
        self._portfolio_halted = False
        self._consecutive_losses = defaultdict(int)
        logger.warning("[KILL SWITCH] Full system reset by operator.")

    def get_status(self) -> dict:
        return {
            "portfolio_halted":    self._portfolio_halted,
            "bot_halted":          dict(self._bot_halted),
            "consecutive_losses":  dict(self._consecutive_losses),
            "daily_trade_counts":  dict(self._daily_trade_counts),
            "events_today":        len([
                e for e in self._kill_switch_log
                if e.triggered_at.date() == date.today()
            ]),
            "last_event":          str(self._kill_switch_log[-1].trigger)
                                   if self._kill_switch_log else None,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Rule 6: Algorithm Validator (Backtesting Gate)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BacktestTrade:
    entry: float
    exit: float
    side: str
    size_usd: float
    pnl_usd: float
    opened_at: datetime
    closed_at: datetime


@dataclass
class ValidationResult:
    passed: bool
    total_trades: int
    win_rate: float
    sharpe_ratio: float
    max_drawdown_pct: float
    profit_factor: float
    total_pnl: float
    avg_rr: float
    failures: List[str]


class AlgoValidator:
    """
    Validates a trading algorithm's backtest results before allowing live deployment.
    Also tracks live paper-trading performance to enforce paper_trade_days_required.
    """

    def __init__(self, cfg: GlobalRiskConfig):
        self.cfg             = cfg
        self._paper_start:   Optional[datetime] = None
        self._paper_trades:  List[BacktestTrade] = []
        self._is_validated:  Dict[str, bool]     = {}

    def validate_backtest(self, bot_name: str,
                           trades: List[BacktestTrade]) -> ValidationResult:
        """Run all validation checks on backtest results."""
        failures = []

        if len(trades) < self.cfg.backtest_min_trades:
            failures.append(
                f"Insufficient trades: {len(trades)} < {self.cfg.backtest_min_trades} required"
            )

        wins   = [t for t in trades if t.pnl_usd > 0]
        losses = [t for t in trades if t.pnl_usd < 0]

        win_rate     = len(wins) / len(trades) if trades else 0
        total_pnl    = sum(t.pnl_usd for t in trades)
        avg_win      = sum(t.pnl_usd for t in wins)  / len(wins)  if wins  else 0
        avg_loss     = sum(t.pnl_usd for t in losses) / len(losses) if losses else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss else 999

        # Sharpe ratio (annualized, assuming daily returns)
        returns = []
        if trades:
            sorted_trades = sorted(trades, key=lambda t: t.closed_at)
            equity = 10_000.0
            for t in sorted_trades:
                ret = t.pnl_usd / equity
                returns.append(ret)
                equity = max(0, equity + t.pnl_usd)

        import math
        if len(returns) > 1:
            mean_r  = sum(returns) / len(returns)
            std_r   = math.sqrt(sum((r - mean_r) ** 2 for r in returns) / len(returns))
            sharpe  = (mean_r / std_r * math.sqrt(252)) if std_r > 0 else 0
        else:
            sharpe = 0

        if sharpe < self.cfg.backtest_min_sharpe:
            failures.append(
                f"Sharpe {sharpe:.2f} < minimum {self.cfg.backtest_min_sharpe}"
            )

        # Max drawdown
        equity = 10_000.0
        peak   = equity
        max_dd = 0.0
        for t in sorted(trades, key=lambda t: t.closed_at):
            equity = max(0, equity + t.pnl_usd)
            peak   = max(peak, equity)
            dd     = (peak - equity) / peak
            max_dd = max(max_dd, dd)

        if max_dd > self.cfg.backtest_max_drawdown:
            failures.append(
                f"Backtest max DD {max_dd:.1%} exceeds {self.cfg.backtest_max_drawdown:.1%}"
            )

        # Average R:R (simplified)
        avg_rr = abs(avg_win / avg_loss) if avg_loss else 0

        passed = len(failures) == 0
        if passed:
            self._is_validated[bot_name] = True
            logger.info(f"[VALIDATOR] {bot_name} PASSED backtest validation. "
                        f"Sharpe:{sharpe:.2f} DD:{max_dd:.1%} WR:{win_rate:.1%}")
        else:
            logger.warning(f"[VALIDATOR] {bot_name} FAILED: {'; '.join(failures)}")

        return ValidationResult(
            passed=passed, total_trades=len(trades),
            win_rate=round(win_rate * 100, 1), sharpe_ratio=round(sharpe, 2),
            max_drawdown_pct=round(max_dd * 100, 1), profit_factor=round(profit_factor, 2),
            total_pnl=round(total_pnl, 2), avg_rr=round(avg_rr, 2), failures=failures
        )

    def start_paper_trading(self, bot_name: str) -> None:
        self._paper_start = datetime.utcnow()
        logger.info(f"[VALIDATOR] Paper trading started for {bot_name}.")

    def record_paper_trade(self, trade: BacktestTrade) -> None:
        self._paper_trades.append(trade)

    def check_paper_ready(self, bot_name: str) -> Tuple[bool, str]:
        """Can this bot graduate from paper trading to live?"""
        if not self._paper_start:
            return False, "Paper trading not started"

        days_elapsed = (datetime.utcnow() - self._paper_start).days
        if days_elapsed < self.cfg.paper_trade_days_required:
            remaining = self.cfg.paper_trade_days_required - days_elapsed
            return False, f"Need {remaining} more paper-trading days"

        paper_pnl = sum(t.pnl_usd for t in self._paper_trades)
        if paper_pnl < self.cfg.paper_trade_min_pnl:
            return False, f"Paper PnL ${paper_pnl:.2f} below minimum ${self.cfg.paper_trade_min_pnl:.2f}"

        return True, f"Paper trading complete: {days_elapsed}d, PnL ${paper_pnl:.2f}"

    def is_validated(self, bot_name: str) -> bool:
        return self._is_validated.get(bot_name, False)


# ─────────────────────────────────────────────────────────────────────────────
# GlobalRiskEngine — The Master Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

class GlobalRiskEngine:
    """
    THE single entry point for all trade decisions.
    All bots MUST call validate_trade() before placing any order.

    Usage:
        engine = GlobalRiskEngine(GLOBAL_RISK, journal)
        result = engine.validate_trade(
            bot="hyperliquid", symbol="BTC", side="LONG",
            entry_price=94210, stop_loss=89500, take_profit=108000,
            requested_size_usd=1200, all_states=risk_manager.states
        )
        if result.approved:
            place_order(result.adjusted_size_usd, result.computed_sl, ...)
    """

    def __init__(self, cfg: GlobalRiskConfig = GLOBAL_RISK,
                 journal: Optional["TelegramJournal"] = None):
        self.cfg           = cfg
        self.journal       = journal
        self.sl_validator  = StopLossValidator(cfg)
        self.sizer         = PositionSizer(cfg)
        self.diversifier   = DiversificationEngine(cfg)
        self.kill_switch   = KillSwitchEngine(cfg, journal)
        self.validator     = AlgoValidator(cfg)

    # ─────────────────────────────────────────────────────────────────────
    # MAIN GATE — Call before EVERY trade
    # ─────────────────────────────────────────────────────────────────────
    def validate_trade(self,
                        bot: str,
                        symbol: str,
                        side: str,
                        entry_price: float,
                        stop_loss: Optional[float],
                        take_profit: Optional[float],
                        requested_size_usd: float,
                        all_states: Dict,
                        live_mode: bool = False) -> TradeValidationResult:
        """
        Master validation. Returns a TradeValidationResult.
        Approved = True only if ALL rules pass.
        """
        portfolio_equity = sum(s.current_equity for s in all_states.values())

        # ── Kill switch check (fast path) ─────────────────────────────────
        if self.kill_switch.is_halted(bot):
            return self._reject(
                RuleViolation.KILL_SWITCH_BOT,
                f"Bot '{bot}' is halted by kill switch",
                requested_size_usd, stop_loss or 0, take_profit or 0, 0, 0
            )

        if self.kill_switch.is_halted():  # portfolio-level
            return self._reject(
                RuleViolation.KILL_SWITCH_PORTFOLIO,
                "Portfolio-level kill switch active — all bots halted",
                requested_size_usd, stop_loss or 0, take_profit or 0, 0, 0
            )

        # ── Rule 6: Algo validation gate (live mode only) ────────────────
        if live_mode and not self.validator.is_validated(bot):
            ready, msg = self.validator.check_paper_ready(bot)
            if not ready:
                return self._reject(
                    RuleViolation.ALGO_NOT_VALIDATED,
                    f"Bot not cleared for live trading: {msg}",
                    requested_size_usd, stop_loss or 0, take_profit or 0, 0, 0
                )

        # ── Rule 2: Mandatory stop-loss ───────────────────────────────────
        sl_valid, final_sl, sl_msg = self.sl_validator.validate(entry_price, stop_loss, side)
        if not sl_valid:
            return self._reject(
                RuleViolation.MISSING_STOP_LOSS, sl_msg,
                requested_size_usd, final_sl, take_profit or 0, 0, 0
            )
        logger.debug(f"[SL] {sl_msg}")

        # ── Rule 3: R:R ratio ─────────────────────────────────────────────
        # Compute TP if not provided (use target R:R)
        if take_profit is None or take_profit <= 0:
            final_tp = self.sizer.compute_tp_for_rr(
                entry_price, final_sl, side, self.cfg.target_rr_ratio)
            logger.debug(f"[RR] No TP provided — computed at {self.cfg.target_rr_ratio}:1 → {final_tp}")
        else:
            final_tp = take_profit

        # Validate R:R
        sl_dist  = abs(entry_price - final_sl)
        tp_dist  = abs(final_tp - entry_price)
        actual_rr = (tp_dist / sl_dist) if sl_dist > 0 else 0

        if self.cfg.enforce_rr and actual_rr < self.cfg.min_rr_ratio:
            if take_profit is not None:
                # Recompute TP to meet minimum R:R instead of hard-reject
                final_tp  = self.sizer.compute_tp_for_rr(
                    entry_price, final_sl, side, self.cfg.min_rr_ratio)
                actual_rr = self.cfg.min_rr_ratio
                logger.info(f"[RR] TP adjusted to meet {self.cfg.min_rr_ratio}:1 minimum → {final_tp}")
            else:
                return self._reject(
                    RuleViolation.RR_BELOW_MINIMUM,
                    f"R:R {actual_rr:.2f} below minimum {self.cfg.min_rr_ratio}:1",
                    requested_size_usd, final_sl, final_tp, actual_rr, 0
                )

        # ── Rule 1: 1% sizing ─────────────────────────────────────────────
        final_size, risk_usd, risk_pct, computed_rr = self.sizer.compute(
            portfolio_equity, entry_price, final_sl, final_tp,
            side, requested_size_usd
        )

        # Hard cap: never exceed 2% rule
        max_allowed_risk = portfolio_equity * self.cfg.max_risk_per_trade_pct
        if risk_usd > max_allowed_risk:
            return self._reject(
                RuleViolation.RISK_PCT_EXCEEDED,
                f"Trade risk ${risk_usd:.2f} ({risk_pct:.2f}%) exceeds "
                f"{self.cfg.max_risk_per_trade_pct:.0%} max",
                requested_size_usd, final_sl, final_tp, actual_rr, risk_usd
            )

        if final_size > self.cfg.max_position_size_usd:
            return self._reject(
                RuleViolation.SIZE_EXCEEDS_HARD_CAP,
                f"Position size ${final_size:.0f} exceeds hard cap ${self.cfg.max_position_size_usd:.0f}",
                requested_size_usd, final_sl, final_tp, actual_rr, risk_usd
            )

        # ── Rule 4: Diversification ───────────────────────────────────────
        diversified, div_reason = self.diversifier.check_new_position(
            symbol, final_size, bot, all_states, portfolio_equity
        )
        if not diversified:
            return self._reject(
                RuleViolation.CORRELATED_EXPOSURE, div_reason,
                requested_size_usd, final_sl, final_tp, actual_rr, risk_usd
            )

        # ── ALL RULES PASSED ──────────────────────────────────────────────
        result = TradeValidationResult(
            approved           = True,
            rule               = RuleViolation.NONE,
            reason             = (
                f"All rules passed | Risk: ${risk_usd:.2f} ({risk_pct:.2f}%) | "
                f"R:R: {actual_rr:.1f} | {div_reason}"
            ),
            original_size_usd  = requested_size_usd,
            adjusted_size_usd  = final_size,
            computed_sl        = final_sl,
            computed_tp        = final_tp,
            actual_rr          = actual_rr,
            risk_usd           = risk_usd,
            risk_pct           = risk_pct,
        )
        logger.info(f"[GLOBAL RISK] {bot.upper()} {symbol} {side}: {result}")
        return result

    # ─────────────────────────────────────────────────────────────────────
    # Kill switch integration — call after every close
    # ─────────────────────────────────────────────────────────────────────
    def on_position_closed(self, bot: str, pnl_usd: float,
                            all_states: Dict) -> Optional[KillSwitchEvent]:
        all_equities = {b: s.current_equity for b, s in all_states.items()}
        all_peaks    = {b: s.peak_equity    for b, s in all_states.items()}
        bot_state    = all_states[bot]

        event = self.kill_switch.on_trade_closed(
            bot, pnl_usd, bot_state.current_equity, bot_state.peak_equity,
            all_equities, all_peaks
        )
        if event:
            asyncio.create_task(self._alert_kill_switch(event))
        return event

    def on_position_opened(self, bot: str) -> Optional[KillSwitchEvent]:
        return self.kill_switch.on_trade_opened(bot)

    async def periodic_check(self, all_states: Dict) -> Optional[KillSwitchEvent]:
        event = self.kill_switch.periodic_check(all_states)
        if event:
            await self._alert_kill_switch(event)
        return event

    async def _alert_kill_switch(self, event: KillSwitchEvent) -> None:
        logger.critical(f"🚨 KILL SWITCH: {event.level.value} | {event.trigger}")
        if self.journal:
            msg = (
                f"🚨 <b>KILL SWITCH — {event.level.value}</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"Bot: {event.bot or 'ALL BOTS'}\n"
                f"Trigger: {event.trigger}\n"
                f"Value: {event.value_at_trigger:.2f} | Threshold: {event.threshold:.2f}\n"
                f"Time: {event.triggered_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"{'🔴 ALL BOTS HALTED' if event.level == KillSwitchLevel.PORTFOLIO else '🟡 Bot paused'}"
                f" — Manual review required."
            )
            await self.journal._send(msg)

    # ─────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────
    @staticmethod
    def _reject(rule: RuleViolation, reason: str,
                original: float, sl: float, tp: float,
                rr: float, risk: float) -> TradeValidationResult:
        logger.warning(f"[GLOBAL RISK] REJECTED — {rule.value}: {reason}")
        return TradeValidationResult(
            approved=False, rule=rule, reason=reason,
            original_size_usd=original, adjusted_size_usd=0.0,
            computed_sl=sl, computed_tp=tp,
            actual_rr=rr, risk_usd=risk, risk_pct=0.0
        )

    def get_full_status(self, all_states: Dict) -> dict:
        """Comprehensive risk status for dashboard."""
        portfolio_equity = sum(s.current_equity for s in all_states.values())
        return {
            "kill_switch":   self.kill_switch.get_status(),
            "exposure":      self.diversifier.get_exposure_report(all_states, portfolio_equity),
            "validated_bots": dict(self.validator._is_validated),
            "portfolio_equity": portfolio_equity,
        }
