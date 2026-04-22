import asyncio, time
from dataclasses import dataclass, field
from typing import Callable
from collections import defaultdict
from core.config import cfg, setup_logger
from core.subgraph_client import subgraph
from core.gamma_client import gamma

logger = setup_logger("tracker")

@dataclass
class CopySignal:
    token_id: str; condition_id: str; question: str; outcome_label: str
    outcome_index: int; direction: str; signal_type: str
    whale_wallet: str; whale_label: str; delta_shares: float
    current_price: float; whale_entry_price: float
    consensus_count: int = 1; confidence_score: float = 0.5
    detected_at: int = field(default_factory=lambda: int(time.time()))

class WhaleTracker:
    def __init__(self):
        self._position_cache: dict = {}
        self._wallet_labels: dict = {}
        self._consensus_tracker: dict = defaultdict(list)
        self._signal_handlers: list = []
        self._running = False
        self._poll_interval = cfg.whale_filters.get("poll_interval_seconds", 5)
        for w in cfg.whale_wallets:
            addr = w["address"].lower()
            self._wallet_labels[addr] = w.get("label", addr[:10])
            self._position_cache[addr] = {}
        logger.info("Whale Tracker: tracking %d wallets", len(self._wallet_labels))

    def add_signal_handler(self, handler: Callable): self._signal_handlers.append(handler)
    def add_wallet(self, address, label=None):
        addr = address.lower(); self._wallet_labels[addr]=label or addr[:10]; self._position_cache[addr]={}
    def remove_wallet(self, address):
        addr=address.lower(); self._wallet_labels.pop(addr,None); self._position_cache.pop(addr,None)
    def get_tracked_wallets(self): return [{"address":a,"label":l} for a,l in self._wallet_labels.items()]
    def stop(self): self._running = False

    async def start(self):
        self._running = True
        logger.info("Whale tracking started (interval=%ds)", self._poll_interval)
        await self._snapshot_all_wallets()
        while self._running:
            try:
                await self._poll_all_wallets()
                await asyncio.sleep(self._poll_interval)
            except asyncio.CancelledError: break
            except Exception as e:
                logger.error("Tracker loop error: %s", e)
                await asyncio.sleep(self._poll_interval * 2)

    async def _snapshot_all_wallets(self):
        wallets = list(self._wallet_labels.keys())
        if not wallets: return
        try:
            all_pos = await subgraph.get_all_wallet_positions(wallets)
            for w, positions in all_pos.items():
                self._position_cache[w] = {p["token_id"]: p for p in positions}
            logger.info("Initial snapshot complete")
        except Exception as e:
            logger.error("Snapshot failed: %s", e)

    async def _poll_all_wallets(self):
        wallets = list(self._wallet_labels.keys())
        if not wallets: return
        try:
            all_pos = await subgraph.get_all_wallet_positions(wallets)
            for w in wallets:
                previous = self._position_cache.get(w, {})
                current = all_pos.get(w, [])
                self._position_cache[w] = {p["token_id"]: p for p in current}
                signals = subgraph.compute_signals(w, previous, current)
                for s in signals:
                    if s["type"] in ("NEW","INCREASED"): await self._process_entry(s, w)
                    elif s["type"] == "CLOSED": await self._process_exit(s, w)
        except Exception as e:
            logger.debug("Poll failed: %s", e)

    async def _process_entry(self, raw, wallet):
        token_id = raw["token_id"]
        question = await gamma.get_market_question(token_id)
        outcome_label = await gamma.get_outcome_label(token_id)
        from core.clob_client import polymarket
        price = await polymarket.async_get_midpoint(token_id) if polymarket._initialized else 0.5
        key = f"{token_id}_{raw['outcome_index']}"
        now = time.time()
        self._consensus_tracker[key].append({"wallet": wallet, "at": int(now)})
        self._consensus_tracker[key] = [e for e in self._consensus_tracker[key] if now-e["at"]<60]
        consensus = len(set(e["wallet"] for e in self._consensus_tracker[key]))
        score = min(1.0, 0.5 + (0.1 if raw["type"]=="NEW" else 0) + (0.15*(consensus-1) if consensus>=2 else 0) + (0.1 if raw["delta_shares"]>100 else 0))
        signal = CopySignal(token_id=token_id, condition_id=raw.get("condition_id",""), question=question,
            outcome_label=outcome_label, outcome_index=raw["outcome_index"], direction="BUY",
            signal_type=raw["type"], whale_wallet=wallet, whale_label=self._wallet_labels.get(wallet,wallet[:10]),
            delta_shares=raw["delta_shares"], current_price=price, whale_entry_price=price,
            consensus_count=consensus, confidence_score=round(score,2))
        logger.info("Signal: %s | %s | %s %s shares | consensus=%d", signal.whale_label, signal.signal_type, signal.direction, f"{signal.delta_shares:.2f}", consensus)
        for h in self._signal_handlers:
            try: await h(signal)
            except Exception as e: logger.error("Handler error: %s", e)

    async def _process_exit(self, raw, wallet):
        signal = CopySignal(token_id=raw["token_id"], condition_id=raw.get("condition_id",""),
            question=await gamma.get_market_question(raw["token_id"]), outcome_label="",
            outcome_index=raw["outcome_index"], direction="SELL", signal_type="CLOSED",
            whale_wallet=wallet, whale_label=self._wallet_labels.get(wallet,wallet[:10]),
            delta_shares=abs(raw["delta_shares"]), current_price=0.0, whale_entry_price=0.0)
        for h in self._signal_handlers:
            try: await h(signal)
            except Exception as e: logger.error("Exit handler error: %s", e)
