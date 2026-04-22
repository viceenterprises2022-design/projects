"""
AlphaCopy - Performance Dashboard
Console + JSON reporting for all three bots.
"""
import json
import logging
from datetime import datetime
from typing import Dict
from core.risk_manager import RiskManager

logger = logging.getLogger(__name__)


class Dashboard:
    def __init__(self, risk: RiskManager):
        self.risk = risk

    def print_summary(self) -> None:
        print("\n" + "═" * 65)
        print(f"  AlphaCopy Dashboard — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        print("═" * 65)
        for bot in ["hyperliquid", "binance", "polymarket"]:
            s = self.risk.get_summary(bot)
            cfg = getattr(self.risk.config, bot)
            pnl_pct = s["pnl"] / cfg.allocated_capital_usd * 100
            status  = "🔴 HALTED" if s["halted"] else "🟢 ACTIVE"
            print(f"\n  {bot.upper():15s} {status}")
            print(f"    Equity:     ${s['equity']:>10,.2f}  ({pnl_pct:+.1f}%)")
            print(f"    Drawdown:   {s['drawdown_pct']:>7.1f}%")
            print(f"    Positions:  {s['open_positions']:>3d} open")
            print(f"    Trades:     {s['total_trades']:>3d} total  "
                  f"({s['win_rate']:.0f}% win rate)")

        print("\n" + "═" * 65)
        total_allocated = sum(
            getattr(self.risk.config, b).allocated_capital_usd
            for b in ["hyperliquid", "binance", "polymarket"]
        )
        total_equity = sum(
            self.risk.states[b].current_equity
            for b in ["hyperliquid", "binance", "polymarket"]
        )
        total_pnl = total_equity - total_allocated
        total_pct = total_pnl / total_allocated * 100
        print(f"  PORTFOLIO TOTAL: ${total_equity:>10,.2f}  ({total_pct:+.1f}%)")
        print("═" * 65 + "\n")

    def to_json(self) -> str:
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "bots": {b: self.risk.get_summary(b)
                     for b in ["hyperliquid", "binance", "polymarket"]},
            "recent_events": self.risk.event_log[-20:]
        }
        return json.dumps(data, indent=2)
