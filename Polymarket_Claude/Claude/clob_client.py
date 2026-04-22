import time
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from core.config import cfg, setup_logger

logger = setup_logger("clob")

class PolymarketClient:
    def __init__(self):
        self._client = None
        self._initialized = False

    def initialize(self):
        if self._initialized: return
        try:
            from py_clob_client.client import ClobClient
            self._client = ClobClient(
                host=cfg.api["clob_host"],
                key=cfg.private_key,
                chain_id=cfg.api["chain_id"],
                signature_type=cfg.signature_type,
                funder=cfg.funder_address or None,
            )
            creds = self._client.create_or_derive_api_creds()
            self._client.set_api_creds(creds)
            self._initialized = True
            logger.info("CLOB client initialized (DRY_RUN=%s)", cfg.dry_run)
        except Exception as e:
            logger.error("CLOB init failed: %s", e)
            raise

    def get_midpoint(self, token_id: str) -> float:
        if not self._initialized: return 0.5
        try:
            r = self._client.get_midpoint(token_id)
            return float(r.get("mid", 0.5))
        except Exception:
            return 0.5

    def get_order_book(self, token_id: str) -> dict:
        try:
            book = self._client.get_order_book(token_id)
            return {
                "bids": [(float(b.price), float(b.size)) for b in book.bids],
                "asks": [(float(a.price), float(a.size)) for a in book.asks],
            }
        except Exception:
            return {"bids": [], "asks": []}

    def get_balance(self) -> float:
        if not self._initialized: return cfg.risk.get("total_capital_usd", 2000)
        try:
            b = self._client.get_balance_allowance()
            return float(b.get("balance", 0)) / 1e6
        except Exception:
            return 0.0

    def get_positions(self) -> list:
        if not self._initialized: return []
        try: return self._client.get_positions() or []
        except Exception: return []

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10),
           retry=retry_if_exception_type(Exception))
    def place_market_buy(self, token_id: str, amount_usd: float) -> dict:
        from py_clob_client.clob_types import MarketOrderArgs, OrderType
        from py_clob_client.order_builder.constants import BUY
        if cfg.dry_run:
            mid = self.get_midpoint(token_id)
            shares = round(amount_usd / max(mid, 0.01), 4)
            logger.info("[DRY] BUY $%.2f @ %.4f = %.4f shares", amount_usd, mid, shares)
            return {"order_id": f"DRY_{int(time.time())}", "status": "filled",
                    "side": "BUY", "token_id": token_id, "amount_usd": amount_usd,
                    "fill_price": mid, "shares": shares, "dry_run": True}
        mo = MarketOrderArgs(token_id=token_id, amount=amount_usd, side=BUY, order_type=OrderType.FOK)
        signed = self._client.create_market_order(mo)
        resp = self._client.post_order(signed, OrderType.FOK)
        return {"order_id": resp.get("orderID",""), "status": resp.get("status",""),
                "side": "BUY", "token_id": token_id, "amount_usd": amount_usd,
                "fill_price": float(resp.get("price",0)), "shares": float(resp.get("sizeMatched",0)),
                "dry_run": False}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10),
           retry=retry_if_exception_type(Exception))
    def place_market_sell(self, token_id: str, shares: float) -> dict:
        from py_clob_client.clob_types import MarketOrderArgs, OrderType
        from py_clob_client.order_builder.constants import SELL
        if cfg.dry_run:
            mid = self.get_midpoint(token_id)
            proceeds = round(shares * mid, 4)
            logger.info("[DRY] SELL %.4f shares @ %.4f = $%.2f", shares, mid, proceeds)
            return {"order_id": f"DRY_{int(time.time())}", "status": "filled",
                    "side": "SELL", "token_id": token_id, "shares": shares,
                    "fill_price": mid, "proceeds_usd": proceeds, "dry_run": True}
        mo = MarketOrderArgs(token_id=token_id, amount=shares, side=SELL, order_type=OrderType.FOK)
        signed = self._client.create_market_order(mo)
        resp = self._client.post_order(signed, OrderType.FOK)
        fp = float(resp.get("price", 0))
        return {"order_id": resp.get("orderID",""), "status": resp.get("status",""),
                "side": "SELL", "token_id": token_id, "shares": shares,
                "fill_price": fp, "proceeds_usd": float(resp.get("sizeMatched",0)) * fp, "dry_run": False}

    def cancel_all_orders(self) -> bool:
        if cfg.dry_run: return True
        try: self._client.cancel_all(); return True
        except Exception: return False

    async def async_get_midpoint(self, token_id: str) -> float:
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.get_midpoint, token_id)

    async def async_place_market_buy(self, token_id: str, amount_usd: float) -> dict:
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.place_market_buy, token_id, amount_usd)

    async def async_place_market_sell(self, token_id: str, shares: float) -> dict:
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.place_market_sell, token_id, shares)

polymarket = PolymarketClient()
