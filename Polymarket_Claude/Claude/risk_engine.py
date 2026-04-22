import time
from dataclasses import dataclass
from typing import Optional
from core.config import cfg, setup_logger
from core.clob_client import polymarket
from core.gamma_client import gamma
from storage.db import db

logger = setup_logger("risk")

@dataclass
class TradeDecision:
    approved: bool; reason: str; amount_usd: float = 0.0
    token_id: str = ""; signal: object = None

class RiskEngine:
    def __init__(self):
        self._paused = False
        self._daily_realized_pnl = 0.0

    @property
    def is_paused(self): return self._paused
    def pause(self, reason="Manual"): self._paused=True; logger.warning("Bot PAUSED: %s", reason)
    def resume(self): self._paused=False; logger.info("Bot RESUMED")
    def update_daily_pnl(self, delta): self._daily_realized_pnl += delta

    async def evaluate(self, signal) -> TradeDecision:
        token_id = signal.token_id
        if self._paused: return TradeDecision(False, "Paused", token_id=token_id)
        if signal.direction == "SELL": return TradeDecision(False, "Sell handled by monitor", token_id=token_id)
        today = await db.get_today_pnl()
        if today.get("realized_pnl",0) <= -cfg.risk.get("daily_loss_limit_usd",200):
            self.pause("Daily loss limit hit")
            return TradeDecision(False, "Daily loss limit hit", token_id=token_id)
        open_pos = await db.get_open_positions()
        if len(open_pos) >= cfg.risk.get("max_open_positions",10):
            return TradeDecision(False, f"Max positions ({len(open_pos)})", token_id=token_id)
        if await db.get_position_by_token(token_id):
            return TradeDecision(False, "Already in position", token_id=token_id)
        ok, reason = await gamma.validate_market_for_trade(token_id, 25)
        if not ok: return TradeDecision(False, f"Market: {reason}", token_id=token_id)
        current = await polymarket.async_get_midpoint(token_id)
        whale_p = signal.whale_entry_price
        if whale_p > 0 and current > 0:
            slippage = abs(current - whale_p) / whale_p
            if slippage > cfg.risk.get("max_slippage_pct", 0.10):
                return TradeDecision(False, f"Slippage {slippage:.1%}", token_id=token_id)
        min_consensus = cfg.whale_filters.get("consensus_threshold", 1)
        if signal.consensus_count < min_consensus:
            return TradeDecision(False, f"Consensus {signal.consensus_count}<{min_consensus}", token_id=token_id)
            
        m = await gamma.get_market_by_token_id(token_id)
        days = await gamma.get_days_to_resolution(token_id)
        agent_signal = {
            "whale_label": signal.whale_label,
            "signal_type": signal.signal_type,
            "question": signal.question,
            "consensus_count": signal.consensus_count,
            "current_price": current,
            "outcome_label": signal.outcome_label,
            "volume_24h": float(m.get("volume24hr", 0)) if m else 0,
            "days_to_resolution": days if days is not None else -1
        }
        
        logger.info("Static rules passed. Querying Hyperagent LLM for %s...", token_id[:8])
        from hyperagent import hyperagent
        try:
            llm_decision = await hyperagent.forward(agent_signal)
        except Exception as e:
            logger.error("Hyperagent LLM failure: %s", e)
            return TradeDecision(False, "LLM Failure", token_id=token_id)
            
        if llm_decision.get("decision") != "COPY":
            return TradeDecision(False, f"LLM rejected: {llm_decision.get('reasoning', 'No reason')}", token_id=token_id)
            
        amount_usd = llm_decision.get("amount_usd")
        if not amount_usd or float(amount_usd) <= 0:
            amount_usd = self._calc_size(signal)
        else:
            amount_usd = float(amount_usd)

        if amount_usd < 1.0: return TradeDecision(False, "Size too small", token_id=token_id)
        balance = polymarket.get_balance()
        if not cfg.dry_run and balance < amount_usd:
            return TradeDecision(False, f"Insufficient balance ${balance:.2f}", token_id=token_id)
        logger.info("Risk OK: %s → $%.2f", signal.question[:40], amount_usd)
        return TradeDecision(True, "OK", amount_usd=amount_usd, token_id=token_id, signal=signal)

    def _calc_size(self, signal=None) -> float:
        ps = cfg.position_sizing; mode = ps.get("mode","fixed")
        if mode == "tiered" and signal:
            sc = signal.confidence_score
            tiers = ps.get("tiers",{})
            if sc >= 0.80: return float(tiers.get("high_confidence",50))
            if sc >= 0.60: return float(tiers.get("medium_confidence",25))
            return float(tiers.get("low_confidence",10))
        return float(ps.get("fixed_amount_usd",25))

    def calc_sl(self, entry: float) -> float:
        return round(entry * (1 - cfg.risk.get("stop_loss_pct",0.50)), 4)
    def calc_tp(self, entry: float) -> float:
        return round(min(1.0, entry * (1 + cfg.risk.get("take_profit_pct",1.00))), 4)

risk_engine = RiskEngine()
