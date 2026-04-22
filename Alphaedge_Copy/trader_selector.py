"""
AlphaCopy - Trader Selection Engine
Scores and ranks leaderboard traders using multi-factor analysis.
Filters out gamblers, flash-in-the-pan ROIs, and wash traders.
"""
import logging
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TraderProfile:
    address: str               # Wallet address or encrypted UID
    platform: str              # hyperliquid | binance | polymarket
    display_name: str = ""

    # Performance metrics
    pnl_all_time: float   = 0.0
    pnl_30d: float        = 0.0
    pnl_7d: float         = 0.0
    roi_all_time: float   = 0.0
    roi_30d: float        = 0.0
    win_rate: float       = 0.0
    total_trades: int     = 0
    avg_trade_duration_h: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float   = 0.0
    volume_30d: float     = 0.0

    # Computed score
    alpha_score: float = 0.0
    rank: int          = 0
    last_updated: datetime = None

    # Quality flags
    is_wash_trader: bool     = False
    is_new_account: bool     = False
    has_sharing_enabled: bool = True   # Binance specific


@dataclass
class TraderFilter:
    """Criteria to qualify a trader for copying"""
    min_pnl_30d: float       = 10_000.0
    min_roi_30d: float        = 0.20      # 20%
    min_win_rate: float       = 0.50
    min_total_trades: int     = 20
    max_drawdown_pct: float   = 0.30      # 30% max DD
    min_account_age_days: int = 30
    require_sharing: bool     = True
    exclude_wash_traders: bool = True


class TraderScorer:
    """
    Multi-factor scoring model for ranking traders.
    Score = weighted sum of normalized metrics.

    Weights (total = 1.0):
      - Risk-adjusted return (Sharpe): 0.30
      - 30-day ROI:                    0.20
      - Win rate:                      0.20
      - Max drawdown (penalty):        0.15
      - Trade consistency (7d vs 30d): 0.10
      - Trade count (experience):      0.05
    """

    WEIGHTS = {
        "sharpe":      0.30,
        "roi_30d":     0.20,
        "win_rate":    0.20,
        "drawdown":    0.15,  # inverted — lower is better
        "consistency": 0.10,
        "experience":  0.05,
    }

    def score(self, trader: TraderProfile) -> float:
        """Returns 0-100 alpha score"""
        if trader.is_wash_trader:
            return 0.0

        # Normalize each factor to [0, 1]
        sharpe_norm      = min(1.0, max(0.0, trader.sharpe_ratio / 3.0))
        roi_norm         = min(1.0, max(0.0, trader.roi_30d / 1.0))     # Saturates at 100% ROI
        win_rate_norm    = min(1.0, max(0.0, (trader.win_rate - 0.40) / 0.40))  # 40-80% range
        drawdown_penalty = min(1.0, max(0.0, 1.0 - trader.max_drawdown_pct / 0.50))

        # 7d / 30d ROI consistency (avoids one-hit wonders)
        if trader.roi_30d > 0 and trader.pnl_7d is not None:
            roi_7d_ann = (trader.pnl_7d / max(1, trader.volume_30d / 4)) * 52
            consistency_norm = min(1.0, max(0.0, roi_7d_ann / max(0.001, trader.roi_30d * 12)))
        else:
            consistency_norm = 0.5

        experience_norm  = min(1.0, trader.total_trades / 200.0)

        score = (
            self.WEIGHTS["sharpe"]      * sharpe_norm      +
            self.WEIGHTS["roi_30d"]     * roi_norm         +
            self.WEIGHTS["win_rate"]    * win_rate_norm    +
            self.WEIGHTS["drawdown"]    * drawdown_penalty +
            self.WEIGHTS["consistency"] * consistency_norm +
            self.WEIGHTS["experience"]  * experience_norm
        ) * 100

        return round(score, 2)

    def filter_and_rank(self, traders: List[TraderProfile],
                        f: TraderFilter) -> List[TraderProfile]:
        qualified = []
        for t in traders:
            reasons = []
            if t.pnl_30d < f.min_pnl_30d:
                reasons.append(f"pnl_30d {t.pnl_30d:.0f} < {f.min_pnl_30d:.0f}")
            if t.roi_30d < f.min_roi_30d:
                reasons.append(f"roi_30d {t.roi_30d:.1%} < {f.min_roi_30d:.1%}")
            if t.win_rate < f.min_win_rate:
                reasons.append(f"win_rate {t.win_rate:.1%} < {f.min_win_rate:.1%}")
            if t.total_trades < f.min_total_trades:
                reasons.append(f"trades {t.total_trades} < {f.min_total_trades}")
            if t.max_drawdown_pct > f.max_drawdown_pct:
                reasons.append(f"maxDD {t.max_drawdown_pct:.1%} > {f.max_drawdown_pct:.1%}")
            if f.require_sharing and not t.has_sharing_enabled:
                reasons.append("position sharing disabled")
            if f.exclude_wash_traders and t.is_wash_trader:
                reasons.append("wash trader detected")

            if reasons:
                logger.debug(f"Excluded {t.address[:8]}…: {', '.join(reasons)}")
                continue

            t.alpha_score = self.score(t)
            qualified.append(t)

        qualified.sort(key=lambda x: x.alpha_score, reverse=True)
        for i, t in enumerate(qualified):
            t.rank = i + 1
        return qualified


def detect_wash_trader(trader: TraderProfile) -> bool:
    """
    Heuristics to detect wash-trading / airdrop farming.
    """
    flags = 0

    # Very high win rate with low PnL → small scalps, gaming metrics
    if trader.win_rate > 0.90 and trader.pnl_30d < 5_000:
        flags += 1

    # Extreme ROI spike without volume
    if trader.roi_30d > 5.0 and trader.volume_30d < 50_000:
        flags += 1

    # Very short avg trade duration (HFT-style on a DEX = suspicious)
    if 0 < trader.avg_trade_duration_h < 0.1:
        flags += 1

    return flags >= 2
