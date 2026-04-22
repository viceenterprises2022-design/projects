import aiohttp, asyncio
from typing import Optional
from core.config import cfg, setup_logger

logger = setup_logger("subgraph")
POSITIONS_URL = cfg.api["positions_subgraph"]
ACTIVITY_URL  = cfg.api["activity_subgraph"]

class SubgraphClient:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))
        return self._session

    async def _query(self, url: str, query: str, variables: dict = None) -> dict:
        session = await self._get_session()
        payload = {"query": query}
        if variables: payload["variables"] = variables
        try:
            async with session.post(url, json=payload) as r:
                if r.status != 200: return {}
                result = await r.json()
                return result.get("data", {})
        except Exception as e:
            logger.warning("Subgraph query failed: %s", e)
            return {}

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_wallet_positions(self, wallet: str) -> list:
        data = await self._query(POSITIONS_URL, """
        query WalletPositions($wallet: String!) {
          positions(where: { user: $wallet, balance_gt: "0" } first: 100 orderBy: balance orderDirection: desc) {
            id condition outcomeIndex balance user { id }
          }
        }""", {"wallet": wallet.lower()})
        positions = []
        for pos in data.get("positions", []):
            try:
                balance = int(pos.get("balance","0")) / 1e18
                if balance < 0.01: continue
                positions.append({
                    "token_id": pos.get("id","").split("-")[0],
                    "condition_id": pos.get("condition",""),
                    "outcome_index": int(pos.get("outcomeIndex",0)),
                    "balance": round(balance, 4),
                    "wallet": wallet.lower(),
                })
            except Exception:
                continue
        return positions

    async def get_wallet_stats(self, wallet: str) -> dict:
        data = await self._query(ACTIVITY_URL, """
        query WalletActivity($wallet: String!) {
          positionSpliteds(where: { user: $wallet } first: 1000) { id amount timestamp }
        }""", {"wallet": wallet.lower()})
        splits = data.get("positionSpliteds", [])
        total_volume = sum(int(s.get("amount",0)) / 1e6 for s in splits)
        return {"total_trades": len(splits), "total_volume_usd": round(total_volume, 2)}

    async def get_all_wallet_positions(self, wallets: list[str]) -> dict:
        wallets_lc = [w.lower() for w in wallets]
        data = await self._query(POSITIONS_URL, """
        query AllWalletPositions($wallets: [String!]) {
          positions(where: { user_in: $wallets, balance_gt: "0" } first: 1000 orderBy: balance orderDirection: desc) {
            id condition outcomeIndex balance user { id }
          }
        }""", {"wallets": wallets_lc})
        
        positions_by_wallet = {w: [] for w in wallets_lc}
        for pos in data.get("positions", []):
            try:
                balance = int(pos.get("balance","0")) / 1e18
                if balance < 0.01: continue
                wallet = pos.get("user", {}).get("id", "").lower()
                if wallet not in positions_by_wallet:
                    positions_by_wallet[wallet] = []
                positions_by_wallet[wallet].append({
                    "token_id": pos.get("id","").split("-")[0],
                    "condition_id": pos.get("condition",""),
                    "outcome_index": int(pos.get("outcomeIndex",0)),
                    "balance": round(balance, 4),
                    "wallet": wallet,
                })
            except Exception:
                continue
        return positions_by_wallet

    def compute_signals(self, wallet: str, previous: dict, current: list) -> list:
        current_map = {p["token_id"]: p for p in current}
        signals = []
        for token_id, pos in current_map.items():
            prev = previous.get(token_id, {})
            prev_balance = prev.get("balance", 0)
            delta = pos["balance"] - prev_balance
            if delta > 0.5:
                signals.append({
                    "type": "NEW" if prev_balance == 0 else "INCREASED",
                    "token_id": token_id,
                    "condition_id": pos["condition_id"],
                    "outcome_index": pos["outcome_index"],
                    "delta_shares": round(delta, 4),
                    "current_balance": pos["balance"],
                    "wallet": wallet,
                })
        for token_id, prev in previous.items():
            if token_id not in current_map and prev.get("balance", 0) > 0.5:
                signals.append({
                    "type": "CLOSED",
                    "token_id": token_id,
                    "condition_id": prev.get("condition_id",""),
                    "outcome_index": prev.get("outcome_index", 0),
                    "delta_shares": -prev["balance"],
                    "current_balance": 0,
                    "wallet": wallet,
                })
        return signals

subgraph = SubgraphClient()
