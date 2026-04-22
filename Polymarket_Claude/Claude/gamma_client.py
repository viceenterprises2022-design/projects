import aiohttp
from datetime import datetime, timezone
from typing import Optional
from core.config import cfg, setup_logger

logger = setup_logger("gamma")
GAMMA_BASE = cfg.api["gamma_host"]

class GammaClient:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache: dict = {}
        self._cache_ttl = 300

    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_market_by_token_id(self, token_id: str) -> Optional[dict]:
        if token_id in self._cache:
            cached = self._cache[token_id]
            if (datetime.now(timezone.utc) - cached["at"]).seconds < self._cache_ttl:
                return cached["data"]
        session = await self._get_session()
        try:
            async with session.get(f"{GAMMA_BASE}/markets", params={"token_id": token_id}) as r:
                if r.status != 200: return None
                data = await r.json()
                if not data: return None
                market = data[0] if isinstance(data, list) else data
                self._cache[token_id] = {"data": market, "at": datetime.now(timezone.utc)}
                return market
        except Exception as e:
            logger.warning("get_market failed for %s: %s", token_id[:12], e)
            return None

    async def get_market_question(self, token_id: str) -> str:
        m = await self.get_market_by_token_id(token_id)
        return m.get("question", f"Market {token_id[:12]}...") if m else f"Market {token_id[:12]}..."

    async def get_outcome_label(self, token_id: str) -> str:
        m = await self.get_market_by_token_id(token_id)
        if not m: return "YES"
        for t in m.get("tokens", []):
            if t.get("token_id") == token_id or t.get("tokenId") == token_id:
                return t.get("outcome", "YES")
        return "YES"

    async def get_days_to_resolution(self, token_id: str) -> Optional[int]:
        m = await self.get_market_by_token_id(token_id)
        if not m: return None
        end_str = m.get("endDate") or m.get("end_date")
        if not end_str: return None
        try:
            end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
            return max(0, (end_dt - datetime.now(timezone.utc)).days)
        except Exception:
            return None

    async def validate_market_for_trade(self, token_id: str, amount_usd: float) -> tuple:
        mf = cfg.market_filters
        m = await self.get_market_by_token_id(token_id)
        if not m: return False, "Market not found"
        if not m.get("active", True): return False, "Market closed"
        vol = float(m.get("volume24hr", 0) or 0)
        if vol < mf.get("min_volume_24h_usd", 1000): return False, f"Low volume ${vol:,.0f}"
        liq = float(m.get("liquidity", 0) or 0)
        if liq < cfg.risk.get("min_market_liquidity_usd", 5000): return False, f"Low liquidity ${liq:,.0f}"
        days = await self.get_days_to_resolution(token_id)
        if days is not None:
            if days < mf.get("min_days_to_resolution", 1): return False, f"Resolves too soon ({days}d)"
            if days > mf.get("max_days_to_resolution", 90): return False, f"Too far out ({days}d)"
        if mf.get("skip_near_certain_markets", True):
            threshold = mf.get("near_certain_threshold", 0.95)
            price = float(m.get("lastTradePrice", 0.5) or 0.5)
            if price >= threshold or price <= (1 - threshold):
                return False, f"Near certain price={price:.2f}"
        return True, "OK"

gamma = GammaClient()
