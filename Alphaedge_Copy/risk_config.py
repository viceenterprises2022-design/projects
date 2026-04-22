"""
AlphaCopy — Global Risk Configuration
All industry-standard risk parameters in one authoritative place.
Enforced system-wide across HL / Binance / Polymarket bots.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class RiskTier(Enum):
    """Portfolio risk appetite tiers."""
    CONSERVATIVE = "conservative"   # 0.5% risk/trade, 1:2 RRR min
    MODERATE     = "moderate"       # 1.0% risk/trade, 1:2 RRR min  ← default
    AGGRESSIVE   = "aggressive"     # 2.0% risk/trade, 1:1.5 RRR min


# ── Asset Correlation Groups ──────────────────────────────────────────────
# Assets within the same group are considered correlated.
# The system limits total exposure per group.
CORRELATION_GROUPS: Dict[str, List[str]] = {
    "BTC_CORE":    ["BTC", "BTCUSDT", "BTC-PERP"],
    "ETH_CORE":    ["ETH", "ETHUSDT", "ETH-PERP"],
    "LARGE_CAP":   ["SOL", "BNB", "AVAX", "MATIC", "ADA"],
    "MID_CAP":     ["DOGE", "SHIB", "DOT", "LINK", "ATOM"],
    "DEFI":        ["UNI", "AAVE", "CRV", "MKR", "COMP"],
    "L2":          ["ARB", "OP", "MANTA", "ZK"],
    "PREDICTION":  ["BTC>$100k", "ETH>$5k", "BTC>$150k"],  # Polymarket
    "MACRO_POLY":  ["Fed Cut", "Recession", "CPI", "Rate Hike"],
    "ELECTION":    ["Trump", "Biden", "Election", "Vote"],
    "CRYPTO_POLY": ["Bitcoin", "Ethereum", "Crypto"],
}

# Maximum % of total portfolio in any single correlation group
MAX_GROUP_EXPOSURE_PCT = 0.25  # 25% max in one correlated group


@dataclass
class GlobalRiskConfig:
    """
    Single source of truth for all risk rules.
    Applied to EVERY trade before execution.
    """

    # ── Rule 1: The 1%-2% Rule ────────────────────────────────────────────
    risk_per_trade_pct: float      = 0.01   # 1% of total portfolio equity
    max_risk_per_trade_pct: float  = 0.02   # Hard ceiling: never exceed 2%
    risk_tier: RiskTier            = RiskTier.MODERATE

    # ── Rule 2: Mandatory Stop-Loss ───────────────────────────────────────
    require_stop_loss: bool        = True    # CANNOT be disabled
    min_sl_distance_pct: float     = 0.005  # SL must be at least 0.5% from entry
    max_sl_distance_pct: float     = 0.10   # SL cannot be more than 10% from entry
    default_sl_pct: float          = 0.05   # Default 5% SL if none provided

    # ── Rule 3: Risk-Reward Ratio ─────────────────────────────────────────
    min_rr_ratio: float            = 2.0    # Minimum 1:2 R:R (reject trades below)
    target_rr_ratio: float         = 3.0    # Target 1:3 R:R
    enforce_rr: bool               = True   # Hard-block trades with bad R:R

    # ── Rule 4: Diversification ───────────────────────────────────────────
    max_correlated_exposure_pct: float = 0.25   # Max 25% in same correlation group
    max_single_asset_pct: float        = 0.15   # Max 15% in any single asset
    max_single_bot_pct: float          = 0.40   # Max 40% of portfolio in one bot
    max_open_positions_global: int     = 15     # System-wide open position cap
    min_diversification_count: int     = 3      # Must hold positions in 3+ assets

    # ── Rule 5: Kill Switches ─────────────────────────────────────────────
    # Portfolio-level triggers (affects ALL bots simultaneously)
    portfolio_max_drawdown_pct: float  = 0.15   # 15% portfolio DD → kill all
    portfolio_daily_loss_pct: float    = 0.05   # 5% daily loss → kill all
    portfolio_weekly_loss_pct: float   = 0.10   # 10% weekly loss → pause all

    # Bot-level triggers
    bot_max_drawdown_pct: float        = 0.20   # 20% bot DD → kill that bot
    bot_daily_loss_pct: float          = 0.07   # 7% daily loss per bot → halt bot
    consecutive_loss_limit: int        = 5      # 5 consecutive losses → pause bot

    # Velocity / anomaly triggers
    max_trades_per_hour: int           = 10     # >10 trades/hour → pause (algo anomaly)
    max_trades_per_day: int            = 50     # >50 trades/day → full stop
    max_loss_in_1min_usd: float        = 500.0  # >$500 loss in 1 min → emergency kill
    max_position_size_usd: float       = 5000.0 # Hard cap: no single trade > $5k

    # ── Rule 6: Algo Validation ───────────────────────────────────────────
    backtest_min_trades: int           = 30     # Need 30+ backtest trades to go live
    backtest_min_sharpe: float         = 1.0    # Min Sharpe ratio in backtest
    backtest_max_drawdown: float       = 0.20   # Max DD in backtest
    paper_trade_days_required: int     = 14     # Min 14 days paper trading before live
    paper_trade_min_pnl: float         = 0.0    # Paper PnL must be non-negative

    # ── Session / Time Rules ─────────────────────────────────────────────
    # Block trading during high-volatility announcement windows
    block_major_announcements: bool    = True   # Block 30min around FOMC, CPI, NFP
    max_trade_duration_days: int       = 30     # Force-close any position > 30 days old

    # ── Portfolio-Level Allocation ────────────────────────────────────────
    total_portfolio_usd: float         = 30_000.0
    bot_allocations: Dict[str, float]  = field(default_factory=lambda: {
        "hyperliquid": 10_000.0,
        "binance":     10_000.0,
        "polymarket":  10_000.0,
    })


# Singleton — import this everywhere
GLOBAL_RISK = GlobalRiskConfig()
