"""
AlphaCopy - Polymarket Copy Bot

Uses:
  - Polymarket CLOB API (clob.polymarket.com) for order execution
  - Gamma API (gamma-api.polymarket.com) for market metadata
  - The Graph / Polygon RPC for on-chain wallet monitoring
  - polymarketanalytics.com data for leaderboard scraping

Key differences from perps:
  - No leverage, no traditional stop-loss (binary outcome)
  - Position is a YES/NO share (price 0-1, pays $1 on win)
  - "Stop loss" = price-based exit (e.g. sell if drops 50%)
  - Slippage in thin order books can be severe — size carefully

Install: pip install py_clob_client aiohttp
"""
import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import aiohttp

from config.settings import PolymarketConfig
from core.risk_manager import RiskManager, Position
from core.trader_selector import TraderProfile, TraderScorer, TraderFilter
from utils.notifier import Notifier

logger = logging.getLogger(__name__)

CLOB_BASE   = "https://clob.polymarket.com"
GAMMA_BASE  = "https://gamma-api.polymarket.com"
ANALYTICS   = "https://polymarketanalytics.com/api"  # Third-party analytics


class PolymarketBot:
    """
    Polymarket copy trading bot.

    Flow:
      1. Fetch top traders from analytics API / on-chain data
      2. Monitor their wallet activity (polling CLOB trade history)
      3. On new position from whale: validate with consensus filter
      4. Execute via py_clob_client
      5. Exit: whale exit, profit target, or price-based stop
    """

    def __init__(self, config: PolymarketConfig, risk_manager: RiskManager,
                 notifier: Notifier, dry_run: bool = True):
        self.cfg      = config
        self.risk     = risk_manager
        self.notifier = notifier
        self.dry_run  = dry_run
        self.scorer   = TraderScorer()
        self.targets: List[TraderProfile]       = []
        self._position_cache: Dict[str, Dict]   = {}  # wallet → {market_id: position}
        self._consensus_signals: Dict[str, int] = {}  # market_id → whale_count
        self._running = False

        # Initialize CLOB client
        try:
            from py_clob_client.client import ClobClient
            from py_clob_client.clob_types import ApiCreds
            self._clob = ClobClient(
                host     = config.clob_host,
                key      = config.private_key,
                chain_id = config.chain_id,
                signature_type=0
            )
            # Derive API credentials from private key
            self._api_creds = self._clob.create_or_derive_api_creds()
            self._clob.set_api_creds(self._api_creds)
            self._sdk_available = True
            logger.info("Polymarket CLOB client initialized")
        except ImportError:
            logger.warning("py_clob_client not installed. Dry-run only.")
            self._sdk_available = False
        except Exception as e:
            logger.warning(f"CLOB init failed (key not set?): {e}")
            self._sdk_available = False

    # ─────────────────────────────────────────────────────────────────────
    # Trader selection
    # ─────────────────────────────────────────────────────────────────────
    async def fetch_top_traders(self, session: aiohttp.ClientSession) -> List[TraderProfile]:
        """
        Fetch top traders from polymarketanalytics.com.
        Falls back to known whale addresses from research.
        """
        traders = []

        # Attempt to scrape analytics API
        try:
            url = f"{ANALYTICS}/traders?limit=100&sort=pnl&order=desc"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    data = await r.json()
                    for row in data.get("traders", []):
                        t = TraderProfile(
                            address      = row.get("address", ""),
                            platform     = "polymarket",
                            display_name = row.get("username", row.get("address", "")[:10]),
                            pnl_all_time = float(row.get("pnl", 0)),
                            pnl_30d      = float(row.get("pnl30d", 0)),
                            win_rate     = float(row.get("winRate", 0)),
                            total_trades = int(row.get("totalTrades", 0)),
                            volume_30d   = float(row.get("volume30d", 0)),
                        )
                        t.sharpe_ratio = t.pnl_30d / max(1, t.volume_30d) * 100
                        traders.append(t)
                    logger.info(f"Fetched {len(traders)} traders from analytics API")
        except Exception as e:
            logger.debug(f"Analytics API error: {e}")

        # Also include manually specified wallets
        for addr in self.cfg.target_wallets:
            if not any(t.address.lower() == addr.lower() for t in traders):
                traders.append(TraderProfile(
                    address  = addr,
                    platform = "polymarket",
                    pnl_30d  = self.cfg.min_pnl_usd + 1,  # Skip filter
                    win_rate = self.cfg.min_win_rate + 0.01,
                    total_trades = self.cfg.min_trades + 1,
                ))

        return traders

    async def select_targets(self) -> List[TraderProfile]:
        async with aiohttp.ClientSession() as session:
            traders = await self.fetch_top_traders(session)

        filt = TraderFilter(
            min_pnl_30d   = self.cfg.min_pnl_usd,
            min_win_rate  = self.cfg.min_win_rate,
            min_total_trades = self.cfg.min_trades,
        )
        ranked = self.scorer.filter_and_rank(traders, filt)
        final  = ranked[:5] if ranked else []

        for t in final:
            logger.info(f"Poly Target: {t.display_name} PnL=${t.pnl_all_time:,.0f} "
                        f"WR={t.win_rate:.1%}")
        return final

    # ─────────────────────────────────────────────────────────────────────
    # Position monitoring
    # ─────────────────────────────────────────────────────────────────────
    async def fetch_wallet_positions(self, session: aiohttp.ClientSession,
                                      wallet: str) -> Dict[str, dict]:
        """Fetch current open positions for a wallet via CLOB API."""
        url = f"{CLOB_BASE}/trades?maker_address={wallet}&limit=500"
        try:
            async with session.get(url) as r:
                if r.status == 200:
                    trades = await r.json()
                    return aggregate_positions(trades)
        except Exception as e:
            logger.debug(f"Position fetch error for {wallet[:8]}: {e}")
        return {}

    async def poll_positions(self) -> None:
        async with aiohttp.ClientSession() as session:
            for target in self.targets:
                wallet  = target.address
                current = await self.fetch_wallet_positions(session, wallet)
                cached  = self._position_cache.get(wallet, {})

                # New positions (token IDs the whale just opened)
                for token_id, pos_data in current.items():
                    if token_id not in cached:
                        await self.on_new_position(target, token_id, pos_data, session)

                # Closed positions
                for token_id in list(cached.keys()):
                    if token_id not in current and self.cfg.exit_on_whale_exit:
                        our_key = f"{wallet}:{token_id}"
                        our_pos = self.risk.states["polymarket"].positions.get(our_key)
                        if our_pos and our_pos.status == "OPEN":
                            cur_price = await self._get_market_price(session, token_id)
                            self.risk.close_position("polymarket", our_key,
                                                      cur_price, "TRADER_CLOSED")
                            await self._execute_sell(token_id, our_pos, cur_price)

                self._position_cache[wallet] = current

    async def on_new_position(self, target: TraderProfile, token_id: str,
                               pos_data: dict, session: aiohttp.ClientSession) -> None:
        size_usd  = float(pos_data.get("size_usd", 0))
        avg_price = float(pos_data.get("avg_price", 0.5))
        outcome   = pos_data.get("outcome", "YES")  # "YES" | "NO"

        # Skip small trades and bad price zones
        if size_usd < self.cfg.min_whale_size_usd:
            logger.debug(f"Whale trade too small: ${size_usd:.0f}")
            return
        if not (self.cfg.min_price <= avg_price <= self.cfg.max_price):
            logger.debug(f"Price {avg_price:.2f} outside range [{self.cfg.min_price}, {self.cfg.max_price}]")
            return

        # Consensus filter: count how many whales are in this market
        self._consensus_signals[token_id] = self._consensus_signals.get(token_id, 0) + 1
        if self._consensus_signals[token_id] < self.cfg.consensus_threshold:
            logger.info(f"Waiting for consensus: {token_id[:8]}… "
                        f"({self._consensus_signals[token_id]}/{self.cfg.consensus_threshold} whales)")
            return

        our_size = size_usd * self.cfg.copy_ratio
        position_key = f"{target.address}:{token_id}"

        approved, reason, adj_size = self.risk.check_trade(
            "polymarket", position_key, our_size, outcome, target.address)

        if not approved:
            logger.warning(f"[POLY] Blocked: {reason}")
            return

        # Stop-loss for prediction markets: sell if price drops 50% from entry
        sl = avg_price * (1 - self.cfg.max_loss_pct)
        tp = avg_price * self.cfg.profit_target_multiplier

        # Clamp TP to 0.99 (max prediction market value)
        tp = min(0.99, tp)

        position = Position(
            bot           = "polymarket",
            symbol        = token_id[:16] + "…",
            side          = outcome,
            entry_price   = avg_price,
            size_usd      = adj_size,
            size_units    = adj_size,   # In USDC for poly (not base units)
            stop_loss     = sl,
            take_profit   = tp,
            trailing_stop_pct = 0.0,    # Not typical for poly
            source_wallet = target.address,
            trade_id      = str(uuid.uuid4())[:8]
        )

        self.risk.open_position("polymarket", position)
        await self._execute_buy(token_id, outcome, adj_size, avg_price, position)

    # ─────────────────────────────────────────────────────────────────────
    # Price monitoring & exits
    # ─────────────────────────────────────────────────────────────────────
    async def monitor_positions(self, session: aiohttp.ClientSession) -> None:
        open_pos = {
            key: pos
            for key, pos in self.risk.states["polymarket"].positions.items()
            if pos.status == "OPEN"
        }
        for key, pos in open_pos.items():
            token_id  = key.split(":")[1] if ":" in key else key
            cur_price = await self._get_market_price(session, token_id)
            if cur_price <= 0:
                continue

            # Manual SL/TP check (prediction markets have special handling)
            action = None
            if pos.side in ("YES",) and cur_price >= pos.take_profit:
                action = "TAKE_PROFIT"
            elif pos.side in ("YES",) and cur_price <= pos.stop_loss:
                action = "STOP_LOSS"
            elif pos.side in ("NO",) and cur_price <= pos.take_profit:
                action = "TAKE_PROFIT"
            elif pos.side in ("NO",) and cur_price >= pos.stop_loss:
                action = "STOP_LOSS"

            if action:
                self.risk.close_position("polymarket", key, cur_price, action)
                await self._execute_sell(token_id, pos, cur_price)
                await self.notifier.send(
                    f"[POLY] {action}: {pos.symbol} @ {cur_price:.3f} "
                    f"PnL ${pos.pnl_usd:+.2f}")

    async def _get_market_price(self, session: aiohttp.ClientSession,
                                 token_id: str) -> float:
        try:
            url = f"{CLOB_BASE}/midpoint?token_id={token_id}"
            async with session.get(url) as r:
                if r.status == 200:
                    data = await r.json()
                    return float(data.get("mid", 0))
        except Exception:
            pass
        return 0.0

    # ─────────────────────────────────────────────────────────────────────
    # Order execution
    # ─────────────────────────────────────────────────────────────────────
    async def _execute_buy(self, token_id: str, outcome: str,
                            size_usdc: float, price: float,
                            position: Position) -> None:
        if self.dry_run:
            logger.info(f"[DRY-RUN][POLY] BUY {outcome} {token_id[:16]}… "
                        f"${size_usdc:.0f} @ {price:.3f}")
            await self.notifier.send(
                f"🎯 [POLY DRY] BUY {outcome} {position.symbol} "
                f"${size_usdc:.0f} @ {price:.3f} "
                f"SL:{position.stop_loss:.3f} TP:{position.take_profit:.3f}")
            return

        try:
            if self._sdk_available:
                from py_clob_client.clob_types import MarketOrderArgs
                from py_clob_client.order_builder.constants import BUY
                order_args = MarketOrderArgs(
                    token_id=token_id,
                    amount=size_usdc,
                )
                result = self._clob.create_and_post_market_order(
                    order_args, options=None)
                logger.info(f"[POLY] Buy result: {result}")
        except Exception as e:
            logger.error(f"[POLY] Buy failed: {e}")

    async def _execute_sell(self, token_id: str, pos: Position, price: float) -> None:
        if self.dry_run:
            logger.info(f"[DRY-RUN][POLY] SELL {token_id[:16]}… @ {price:.3f}")
            return
        try:
            if self._sdk_available:
                from py_clob_client.clob_types import MarketOrderArgs
                from py_clob_client.order_builder.constants import SELL
                order_args = MarketOrderArgs(
                    token_id=token_id,
                    amount=pos.size_usd,
                )
                result = self._clob.create_and_post_market_order(
                    order_args, options=None)
                logger.info(f"[POLY] Sell result: {result}")
        except Exception as e:
            logger.error(f"[POLY] Sell failed: {e}")

    # ─────────────────────────────────────────────────────────────────────
    # Main loop
    # ─────────────────────────────────────────────────────────────────────
    async def run(self) -> None:
        self._running = True
        self.targets  = await self.select_targets()

        if not self.targets:
            logger.warning("[POLY] No qualified traders. Exiting.")
            return

        await self.notifier.send(
            f"✅ Polymarket Bot started | Watching {len(self.targets)} traders | "
            f"Dry-run: {self.dry_run}")

        while self._running:
            try:
                async with aiohttp.ClientSession() as session:
                    await self.poll_positions()
                    await self.monitor_positions(session)
            except Exception as e:
                logger.error(f"[POLY] Loop error: {e}")
            await asyncio.sleep(self.cfg.polling_interval_sec)

    def stop(self) -> None:
        self._running = False


# ── Helper ────────────────────────────────────────────────────────────────
def aggregate_positions(trades: list) -> Dict[str, dict]:
    """
    Aggregate raw CLOB trades into net positions per token_id.
    Returns {token_id: {avg_price, size_usd, outcome}} for open positions.
    """
    book: Dict[str, dict] = {}
    for trade in trades:
        tid    = trade.get("asset_id") or trade.get("token_id", "")
        side   = trade.get("side", "BUY").upper()
        amount = float(trade.get("size", 0))    # USDC
        price  = float(trade.get("price", 0.5))

        if tid not in book:
            book[tid] = {"net_usd": 0.0, "cost": 0.0, "outcome": "YES"}

        if side == "BUY":
            book[tid]["net_usd"] += amount
            book[tid]["cost"]    += amount
        else:
            book[tid]["net_usd"] -= amount

    # Only return positive (open long) positions
    open_pos = {}
    for tid, b in book.items():
        if b["net_usd"] > 10:
            avg_p = b["cost"] / b["net_usd"] if b["net_usd"] > 0 else 0.5
            open_pos[tid] = {
                "size_usd":  b["net_usd"],
                "avg_price": avg_p,
                "outcome":   b.get("outcome", "YES"),
            }
    return open_pos
