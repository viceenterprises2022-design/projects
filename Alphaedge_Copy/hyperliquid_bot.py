"""
AlphaCopy - Hyperliquid Copy Bot
Uses official hyperliquid-python-sdk for execution.
Monitors target wallets via WebSocket fills, mirrors trades with
proportional sizing + SL/TP management.

Install: pip install hyperliquid-python-sdk websockets
"""
import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any
import aiohttp
import websockets

from config.settings import HyperliquidConfig
from core.risk_manager import RiskManager, Position
from core.trader_selector import TraderProfile, TraderScorer, TraderFilter, detect_wash_trader
from utils.notifier import Notifier

logger = logging.getLogger(__name__)

HL_INFO_URL   = "https://api.hyperliquid.xyz/info"
HL_WS_URL     = "wss://api.hyperliquid.xyz/ws"
HL_TESTNET_WS = "wss://api.hyperliquid-testnet.xyz/ws"


class HyperliquidBot:
    """
    Hyperliquid copy trading bot.

    Flow:
      1. Fetch leaderboard → score → pick top wallets
      2. Subscribe to WebSocket fills for each target wallet
      3. On fill → compute our position size → open mirrored trade
      4. Risk manager runs SL/TP/trailing stop every tick
    """

    def __init__(self, config: HyperliquidConfig, risk_manager: RiskManager,
                 notifier: Notifier, dry_run: bool = True):
        self.cfg         = config
        self.risk        = risk_manager
        self.notifier    = notifier
        self.dry_run     = dry_run
        self.scorer      = TraderScorer()
        self.targets: List[TraderProfile] = []
        self._running    = False
        self._ws         = None

        # Try to import the official SDK
        try:
            from hyperliquid.info import Info
            from hyperliquid.exchange import Exchange
            from hyperliquid.utils import constants
            self.info_client = Info(
                constants.TESTNET_API_URL if config.use_testnet else constants.MAINNET_API_URL,
                skip_ws=True
            )
            self.exchange_client = None  # Init after wallet setup
            self._sdk_available  = True
        except ImportError:
            logger.warning("hyperliquid-python-sdk not installed. Using raw HTTP.")
            self._sdk_available = False

    # ─────────────────────────────────────────────────────────────────────
    # Leaderboard scraping & trader selection
    # ─────────────────────────────────────────────────────────────────────
    async def fetch_leaderboard(self, session: aiohttp.ClientSession) -> List[TraderProfile]:
        """Fetch top traders from Hyperliquid leaderboard endpoint."""
        payload = {"type": "leaderboard"}
        try:
            async with session.post(HL_INFO_URL, json=payload) as resp:
                data = await resp.json()
        except Exception as e:
            logger.error(f"Leaderboard fetch failed: {e}")
            return []

        traders = []
        # leaderboardRows is a list of dicts with fields: ethAddress, prize, windowPerformances
        for row in data.get("leaderboardRows", []):
            addr = row.get("ethAddress", "")
            perf = {p["window"]: p for p in row.get("windowPerformances", [])}
            all_t = perf.get("allTime", {})
            month = perf.get("month", {})

            t = TraderProfile(
                address       = addr,
                platform      = "hyperliquid",
                pnl_all_time  = float(all_t.get("pnl", 0)),
                pnl_30d       = float(month.get("pnl", 0)),
                roi_30d       = float(month.get("roi", 0)),
                win_rate      = float(month.get("winRate", 0.5)),
                total_trades  = int(all_t.get("numTrades", 0)),
                max_drawdown_pct = abs(float(month.get("maxDrawdown", 0))),
                volume_30d    = float(month.get("vlm", 0)),
            )
            # Approximate Sharpe from ROI / MaxDD
            if t.max_drawdown_pct > 0:
                t.sharpe_ratio = t.roi_30d / t.max_drawdown_pct
            t.is_wash_trader = detect_wash_trader(t)
            traders.append(t)

        logger.info(f"Fetched {len(traders)} traders from Hyperliquid leaderboard")
        return traders

    async def select_targets(self) -> List[TraderProfile]:
        """Score and pick the best traders to copy."""
        async with aiohttp.ClientSession() as session:
            traders = await self.fetch_leaderboard(session)

        filt = TraderFilter(
            min_pnl_30d     = self.cfg.leaderboard_min_pnl_30d,
            min_roi_30d     = self.cfg.leaderboard_min_roi_30d,
            max_drawdown_pct = self.cfg.leaderboard_max_drawdown,
        )
        ranked = self.scorer.filter_and_rank(traders, filt)

        # Also include any manually specified wallets
        manual = [a.lower() for a in self.cfg.target_wallets]
        final  = [t for t in ranked if t.address.lower() in manual] if manual else ranked[:5]
        if not final and ranked:
            final = ranked[:5]

        for t in final:
            logger.info(f"Target: {t.address[:10]}… Score={t.alpha_score} "
                        f"PnL_30d=${t.pnl_30d:,.0f} ROI={t.roi_30d:.1%} WR={t.win_rate:.1%}")
        return final

    # ─────────────────────────────────────────────────────────────────────
    # WebSocket monitoring
    # ─────────────────────────────────────────────────────────────────────
    async def subscribe_fills(self, ws, wallet_address: str) -> None:
        """Subscribe to userFills for a target wallet."""
        sub = {
            "method": "subscribe",
            "subscription": {
                "type": "userFills",
                "user": wallet_address
            }
        }
        await ws.send(json.dumps(sub))
        logger.info(f"Subscribed to fills for {wallet_address[:10]}…")

    async def subscribe_price_feed(self, ws) -> None:
        """Subscribe to all marks for SL/TP monitoring."""
        sub = {
            "method": "subscribe",
            "subscription": {"type": "allMids"}
        }
        await ws.send(json.dumps(sub))

    async def on_fill_event(self, fill: dict, source_wallet: str) -> None:
        """
        Process a fill from a target wallet and mirror it.
        fill schema: {coin, side, sz, px, closedPnl, liquidation, oid, ...}
        """
        coin  = fill.get("coin", "")
        side  = "LONG" if fill.get("side") == "B" else "SHORT"
        sz    = float(fill.get("sz", 0))      # in base asset
        price = float(fill.get("px", 0))
        is_close = fill.get("dir", "") in ("Close Long", "Close Short")

        logger.info(f"[HL FILL] {source_wallet[:8]}… {side} {sz} {coin} @ {price}"
                    f" {'CLOSE' if is_close else 'OPEN'}")

        if is_close:
            # Mirror the close
            pos = self.risk.states["hyperliquid"].positions.get(coin)
            if pos and pos.status == "OPEN" and pos.source_wallet == source_wallet:
                self.risk.close_position("hyperliquid", coin, price, "TRADER_CLOSED")
                await self._execute_close(coin, pos, price)
            return

        # Compute our size proportionally
        trader_size_usd = sz * price
        our_size_usd    = trader_size_usd * self.cfg.copy_ratio

        approved, reason, adj_size = self.risk.check_trade(
            "hyperliquid", coin, our_size_usd, side, source_wallet)

        if not approved:
            logger.warning(f"Trade blocked: {reason}")
            await self.notifier.send(f"[HL] Skipped {coin} {side}: {reason}")
            return

        # SL / TP prices
        if side == "LONG":
            sl = price * (1 - self.cfg.stop_loss_pct)
            tp = price * (1 + self.cfg.take_profit_pct)
        else:
            sl = price * (1 + self.cfg.stop_loss_pct)
            tp = price * (1 - self.cfg.take_profit_pct)

        # Use risk-sized if it's smaller
        risk_sized = self.risk.compute_position_size(
            "hyperliquid", price, sl, risk_pct=0.01)
        final_size = min(adj_size, risk_sized)

        position = Position(
            bot           = "hyperliquid",
            symbol        = coin,
            side          = side,
            entry_price   = price,
            size_usd      = final_size,
            size_units    = final_size / price,
            stop_loss     = sl,
            take_profit   = tp,
            trailing_stop_pct = self.cfg.trailing_stop_pct,
            source_wallet = source_wallet,
            trade_id      = str(uuid.uuid4())[:8]
        )
        position.trailing_high = price

        self.risk.open_position("hyperliquid", position)
        await self._execute_open(position)

    async def on_price_update(self, mids: dict) -> None:
        """Update SL/TP/trailing for all open positions."""
        open_positions = {
            sym: pos
            for sym, pos in self.risk.states["hyperliquid"].positions.items()
            if pos.status == "OPEN"
        }
        for sym, pos in open_positions.items():
            if sym in mids:
                price  = float(mids[sym])
                action = self.risk.update_position("hyperliquid", sym, price)
                if action:
                    await self._execute_close(sym, pos, price)
                    await self.notifier.send(
                        f"[HL] {action}: {sym} @ {price:.4f} "
                        f"PnL ${pos.pnl_usd:+.2f}")

    # ─────────────────────────────────────────────────────────────────────
    # Order execution
    # ─────────────────────────────────────────────────────────────────────
    async def _execute_open(self, pos: Position) -> None:
        if self.dry_run:
            logger.info(f"[DRY-RUN] OPEN {pos.symbol} {pos.side} "
                        f"${pos.size_usd:.0f} @ {pos.entry_price}")
            await self.notifier.send(
                f"🤖 [HL DRY] OPEN {pos.symbol} {pos.side} "
                f"${pos.size_usd:.0f} @ {pos.entry_price:.4f} "
                f"SL:{pos.stop_loss:.4f} TP:{pos.take_profit:.4f}")
            return

        try:
            if self._sdk_available:
                from hyperliquid.exchange import Exchange
                from eth_account import Account
                acct = Account.from_key(self.cfg.private_key)
                exchange = Exchange(acct, self.cfg.api_url,
                                    account_address=self.cfg.account_address)
                is_buy = pos.side == "LONG"
                sz     = round(pos.size_units, 6)
                order_result = exchange.order(
                    pos.symbol, is_buy, sz, pos.entry_price,
                    {"limit": {"tif": "Gtc"}},
                    reduce_only=False
                )
                logger.info(f"Order result: {order_result}")
            else:
                logger.warning("SDK not available — order not sent")
        except Exception as e:
            logger.error(f"Order execution failed: {e}")

    async def _execute_close(self, symbol: str, pos: Position, price: float) -> None:
        if self.dry_run:
            logger.info(f"[DRY-RUN] CLOSE {symbol} @ {price}")
            return
        try:
            if self._sdk_available:
                from hyperliquid.exchange import Exchange
                from eth_account import Account
                acct     = Account.from_key(self.cfg.private_key)
                exchange = Exchange(acct, self.cfg.api_url,
                                    account_address=self.cfg.account_address)
                is_buy   = pos.side == "SHORT"   # reverse to close
                exchange.order(symbol, is_buy, pos.size_units, price,
                               {"limit": {"tif": "Ioc"}}, reduce_only=True)
        except Exception as e:
            logger.error(f"Close execution failed: {e}")

    # ─────────────────────────────────────────────────────────────────────
    # Main loop
    # ─────────────────────────────────────────────────────────────────────
    async def run(self) -> None:
        self._running = True
        self.targets  = await self.select_targets()

        if not self.targets:
            logger.error("No qualified traders found. Exiting.")
            return

        ws_url = HL_TESTNET_WS if self.cfg.use_testnet else HL_WS_URL
        logger.info(f"Connecting to {ws_url}")

        while self._running:
            try:
                async with websockets.connect(ws_url) as ws:
                    self._ws = ws
                    # Subscribe price feed
                    await self.subscribe_price_feed(ws)
                    # Subscribe fills for each target wallet
                    for t in self.targets:
                        await self.subscribe_fills(ws, t.address)

                    await self.notifier.send(
                        f"✅ HL Bot started | Watching {len(self.targets)} traders | "
                        f"Dry-run: {self.dry_run}")

                    async for raw in ws:
                        msg = json.loads(raw)
                        channel = msg.get("channel", "")

                        if channel == "userFills":
                            fills  = msg.get("data", {}).get("fills", [])
                            wallet = msg.get("data", {}).get("user", "")
                            for fill in fills:
                                await self.on_fill_event(fill, wallet)

                        elif channel == "allMids":
                            mids = msg.get("data", {}).get("mids", {})
                            await self.on_price_update(mids)

            except websockets.exceptions.ConnectionClosed:
                logger.warning("WS disconnected — reconnecting in 5s…")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"WS error: {e}")
                await asyncio.sleep(5)

    def stop(self) -> None:
        self._running = False
        logger.info("Hyperliquid bot stopping…")
