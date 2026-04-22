"""
AlphaCopy - Binance Futures Copy Bot

Data source: Binance's unofficial leaderboard endpoints (scraping public API)
             + official Binance Futures API for execution.

Note: Binance's official Copy Trading is closed to new portfolio creation in many
regions. This bot monitors public leaderboard positions and mirrors them via
the official Futures API using your own API key.

Install: pip install python-binance aiohttp
"""
import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional
import aiohttp

from config.settings import BinanceConfig
from core.risk_manager import RiskManager, Position
from core.trader_selector import TraderProfile, TraderScorer, TraderFilter, detect_wash_trader
from utils.notifier import Notifier

logger = logging.getLogger(__name__)

# Binance endpoints (unofficial public leaderboard)
LEADERBOARD_SEARCH  = "https://www.binance.com/bapi/futures/v3/public/future/leaderboard/getLeaderboardRank"
LEADERBOARD_POS     = "https://www.binance.com/bapi/futures/v1/public/future/leaderboard/getOtherPosition"
LEADERBOARD_DETAIL  = "https://www.binance.com/bapi/futures/v2/public/future/leaderboard/getOtherLeaderboardBaseInfo"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Content-Type": "application/json",
}


class BinanceBot:
    """
    Binance Futures copy trading bot.

    Flow:
      1. Scrape leaderboard → score → pick top UIDs
      2. Poll their positions every N seconds
      3. On new position: mirror with our Binance Futures API
      4. Risk manager handles SL/TP
    """

    def __init__(self, config: BinanceConfig, risk_manager: RiskManager,
                 notifier: Notifier, dry_run: bool = True):
        self.cfg      = config
        self.risk     = risk_manager
        self.notifier = notifier
        self.dry_run  = dry_run
        self.scorer   = TraderScorer()
        self.targets: List[TraderProfile] = []
        self._running = False

        # Snapshot of last-known positions per UID
        self._position_cache: Dict[str, Dict] = {}

        # Try official Binance SDK
        try:
            from binance.client import Client
            from binance.exceptions import BinanceAPIException
            self._bn = Client(config.api_key, config.api_secret,
                              testnet=config.testnet)
            self._sdk_available = True
        except ImportError:
            logger.warning("python-binance not installed. Using raw HTTP for execution.")
            self._sdk_available = False

    # ─────────────────────────────────────────────────────────────────────
    # Leaderboard scraping
    # ─────────────────────────────────────────────────────────────────────
    async def fetch_leaderboard(self, session: aiohttp.ClientSession) -> List[TraderProfile]:
        payload = {
            "isShared":   True,
            "tradeType":  "PERPETUAL",
            "periodType": self.cfg.leaderboard_period,
            "statisticsType": self.cfg.leaderboard_sort_by,
        }
        try:
            async with session.post(LEADERBOARD_SEARCH, json=payload,
                                    headers=HEADERS) as r:
                data = await r.json()
        except Exception as e:
            logger.error(f"Leaderboard fetch failed: {e}")
            return []

        rows     = data.get("data", [])[:self.cfg.leaderboard_top_n * 3]
        traders  = []
        for row in rows:
            uid  = row.get("encryptedUid", "")
            stat = row.get("value", 0)

            t = TraderProfile(
                address      = uid,
                platform     = "binance",
                display_name = row.get("nickName", uid[:8]),
                pnl_30d      = float(row.get("pnl", 0)) if self.cfg.leaderboard_sort_by == "PNL" else 0,
                roi_30d      = float(row.get("roi", 0)) if self.cfg.leaderboard_sort_by == "ROI" else 0,
                volume_30d   = float(row.get("volume", 0)),
                has_sharing_enabled = row.get("positionShared", False),
            )
            traders.append(t)

        # Enrich top N with detailed stats
        for t in traders[:self.cfg.leaderboard_top_n]:
            await self._enrich_trader(session, t)

        logger.info(f"Fetched {len(traders)} Binance traders")
        return traders

    async def _enrich_trader(self, session: aiohttp.ClientSession,
                              trader: TraderProfile) -> None:
        payload = {"encryptedUid": trader.address, "tradeType": "PERPETUAL"}
        try:
            async with session.post(LEADERBOARD_DETAIL, json=payload,
                                    headers=HEADERS) as r:
                data   = (await r.json()).get("data", {})
                detail = data.get("futureUser", {})

            trader.win_rate       = float(detail.get("winRate", 0.5))
            trader.max_drawdown_pct = abs(float(detail.get("maxDrawdown", 0)))
            trader.total_trades   = int(detail.get("totalTrades", 0))
            if trader.max_drawdown_pct > 0:
                trader.sharpe_ratio = trader.roi_30d / trader.max_drawdown_pct
        except Exception as e:
            logger.debug(f"Enrichment failed for {trader.address[:8]}: {e}")

    async def select_targets(self) -> List[TraderProfile]:
        async with aiohttp.ClientSession() as session:
            traders = await self.fetch_leaderboard(session)

        filt = TraderFilter(
            min_pnl_30d    = 10_000.0,
            min_roi_30d    = 0.20,
            min_win_rate   = 0.48,
            require_sharing = True,
        )
        ranked = self.scorer.filter_and_rank(traders, filt)

        manual = [a for a in self.cfg.target_encrypted_uids]
        if manual:
            final = [t for t in ranked if t.address in manual]
        else:
            final = ranked[:3]

        for t in final:
            logger.info(f"Binance Target: {t.display_name} ({t.address[:8]}…) "
                        f"Score={t.alpha_score} 30d_ROI={t.roi_30d:.1%}")
        return final

    # ─────────────────────────────────────────────────────────────────────
    # Position polling
    # ─────────────────────────────────────────────────────────────────────
    async def fetch_positions(self, session: aiohttp.ClientSession,
                              uid: str) -> List[dict]:
        payload = {"encryptedUid": uid, "tradeType": "PERPETUAL"}
        try:
            async with session.post(LEADERBOARD_POS, json=payload,
                                    headers=HEADERS) as r:
                data = await r.json()
            return data.get("data", {}).get("otherPositionRetList", [])
        except Exception as e:
            logger.error(f"Position fetch error for {uid[:8]}: {e}")
            return []

    async def poll_positions(self) -> None:
        """
        Detect new/closed positions by diffing against cached snapshot.
        """
        async with aiohttp.ClientSession() as session:
            for target in self.targets:
                uid        = target.address
                current    = await fetch_positions_normalized(session, uid)
                cached     = self._position_cache.get(uid, {})

                # New positions
                for sym, pos_data in current.items():
                    if sym not in cached:
                        logger.info(f"[BN] NEW position detected: {uid[:8]}… {sym}")
                        await self.on_new_position(target, sym, pos_data)

                # Closed positions
                for sym in list(cached.keys()):
                    if sym not in current:
                        logger.info(f"[BN] CLOSED position detected: {uid[:8]}… {sym}")
                        our_pos = self.risk.states["binance"].positions.get(sym)
                        if our_pos and our_pos.status == "OPEN":
                            mkt_price = await self._get_market_price(sym)
                            self.risk.close_position("binance", sym, mkt_price, "TRADER_CLOSED")
                            await self._execute_close(sym, our_pos, mkt_price)

                self._position_cache[uid] = current

    async def on_new_position(self, target: TraderProfile,
                               symbol: str, pos_data: dict) -> None:
        entry_price = float(pos_data.get("entryPrice", 0))
        amount      = float(pos_data.get("amount", 0))
        side        = "LONG" if amount > 0 else "SHORT"
        trader_size = abs(amount) * entry_price

        our_size = trader_size * self.cfg.copy_ratio
        approved, reason, adj_size = self.risk.check_trade(
            "binance", symbol, our_size, side, target.address)

        if not approved:
            logger.warning(f"[BN] Blocked {symbol}: {reason}")
            return

        if side == "LONG":
            sl = entry_price * (1 - self.cfg.stop_loss_pct)
            tp = entry_price * (1 + self.cfg.take_profit_pct)
        else:
            sl = entry_price * (1 + self.cfg.stop_loss_pct)
            tp = entry_price * (1 - self.cfg.take_profit_pct)

        risk_sized = self.risk.compute_position_size("binance", entry_price, sl)
        final_size = min(adj_size, risk_sized)

        position = Position(
            bot           = "binance",
            symbol        = symbol,
            side          = side,
            entry_price   = entry_price,
            size_usd      = final_size,
            size_units    = final_size / entry_price,
            stop_loss     = sl,
            take_profit   = tp,
            trailing_stop_pct = self.cfg.trailing_stop_pct,
            source_wallet = target.address,
            trade_id      = str(uuid.uuid4())[:8]
        )
        position.trailing_high = entry_price

        self.risk.open_position("binance", position)
        await self._execute_open(position)

    # ─────────────────────────────────────────────────────────────────────
    # SL/TP monitoring
    # ─────────────────────────────────────────────────────────────────────
    async def monitor_positions(self) -> None:
        open_pos = {
            sym: pos
            for sym, pos in self.risk.states["binance"].positions.items()
            if pos.status == "OPEN"
        }
        for sym, pos in open_pos.items():
            price  = await self._get_market_price(sym)
            action = self.risk.update_position("binance", sym, price)
            if action:
                await self._execute_close(sym, pos, price)
                await self.notifier.send(
                    f"[BN] {action}: {sym} @ {price:.4f} PnL ${pos.pnl_usd:+.2f}")

    async def _get_market_price(self, symbol: str) -> float:
        clean = symbol.replace("-PERP", "").replace("/", "") + "USDT"
        try:
            if self._sdk_available:
                ticker = self._bn.futures_symbol_ticker(symbol=clean)
                return float(ticker["price"])
        except Exception:
            pass
        return 0.0

    # ─────────────────────────────────────────────────────────────────────
    # Order execution
    # ─────────────────────────────────────────────────────────────────────
    async def _execute_open(self, pos: Position) -> None:
        if self.dry_run:
            logger.info(f"[DRY-RUN][BN] OPEN {pos.symbol} {pos.side} "
                        f"${pos.size_usd:.0f} @ {pos.entry_price}")
            await self.notifier.send(
                f"🤖 [BN DRY] OPEN {pos.symbol} {pos.side} "
                f"${pos.size_usd:.0f} @ {pos.entry_price:.4f} "
                f"SL:{pos.stop_loss:.4f} TP:{pos.take_profit:.4f}")
            return

        try:
            if self._sdk_available:
                symbol = pos.symbol.replace("-PERP", "") + "USDT"
                side   = "BUY" if pos.side == "LONG" else "SELL"
                qty    = round(pos.size_units, 3)
                # Set leverage
                self._bn.futures_change_leverage(symbol=symbol,
                                                 leverage=self.cfg.default_leverage)
                # Market entry
                order = self._bn.futures_create_order(
                    symbol=symbol, side=side, type="MARKET", quantity=qty)
                logger.info(f"[BN] Order placed: {order}")
                # Attach SL/TP as separate orders
                sl_side = "SELL" if pos.side == "LONG" else "BUY"
                self._bn.futures_create_order(
                    symbol=symbol, side=sl_side, type="STOP_MARKET",
                    stopPrice=round(pos.stop_loss, 4),
                    closePosition="true")
                self._bn.futures_create_order(
                    symbol=symbol, side=sl_side, type="TAKE_PROFIT_MARKET",
                    stopPrice=round(pos.take_profit, 4),
                    closePosition="true")
        except Exception as e:
            logger.error(f"[BN] Order failed: {e}")

    async def _execute_close(self, symbol: str, pos: Position, price: float) -> None:
        if self.dry_run:
            logger.info(f"[DRY-RUN][BN] CLOSE {symbol} @ {price}")
            return
        try:
            if self._sdk_available:
                sym  = symbol.replace("-PERP", "") + "USDT"
                side = "SELL" if pos.side == "LONG" else "BUY"
                self._bn.futures_create_order(
                    symbol=sym, side=side, type="MARKET",
                    quantity=round(pos.size_units, 3), reduceOnly=True)
        except Exception as e:
            logger.error(f"[BN] Close failed: {e}")

    # ─────────────────────────────────────────────────────────────────────
    # Main loop
    # ─────────────────────────────────────────────────────────────────────
    async def run(self) -> None:
        self._running = True
        self.targets  = await self.select_targets()

        if not self.targets:
            logger.error("[BN] No qualified traders. Exiting.")
            return

        await self.notifier.send(
            f"✅ Binance Bot started | Watching {len(self.targets)} traders | "
            f"Dry-run: {self.dry_run}")

        while self._running:
            try:
                await self.poll_positions()
                await self.monitor_positions()
            except Exception as e:
                logger.error(f"[BN] Loop error: {e}")
            await asyncio.sleep(self.cfg.polling_interval_sec)

    def stop(self) -> None:
        self._running = False


# ── Helper ────────────────────────────────────────────────────────────────
async def fetch_positions_normalized(session: aiohttp.ClientSession,
                                      uid: str) -> Dict:
    """Fetch and normalize positions to {symbol: pos_data}."""
    payload = {"encryptedUid": uid, "tradeType": "PERPETUAL"}
    try:
        async with session.post(LEADERBOARD_POS, json=payload,
                                headers=HEADERS) as r:
            data = await r.json()
        positions = data.get("data", {}).get("otherPositionRetList", [])
        return {p["symbol"]: p for p in positions}
    except Exception:
        return {}
