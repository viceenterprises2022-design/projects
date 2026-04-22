"""
AlphaCopy - Main Orchestrator
Runs all three copy bots concurrently with shared risk management.

Usage:
  python main.py                  # Dry-run all bots
  python main.py --live           # Live trading (DANGER!)
  python main.py --bot hl         # Only Hyperliquid
  python main.py --bot bn         # Only Binance
  python main.py --bot poly       # Only Polymarket
  python main.py --dashboard      # Show dashboard snapshot
"""
import asyncio
import argparse
import logging
import signal
import sys

from config.settings import CONFIG
from core.risk_manager import RiskManager
from bots.hyperliquid_bot import HyperliquidBot
from bots.binance_bot import BinanceBot
from bots.polymarket_bot import PolymarketBot
from utils.notifier import Notifier
from utils.dashboard import Dashboard


def setup_logging(level: str = "INFO") -> None:
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(
        level=getattr(logging, level),
        format=fmt,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(CONFIG.log_file),
        ]
    )


async def run_dashboard_loop(dashboard: Dashboard, interval: int = 60) -> None:
    while True:
        dashboard.print_summary()
        await asyncio.sleep(interval)


async def main(bots_to_run: list, live: bool = False) -> None:
    setup_logging(CONFIG.log_level)
    logger = logging.getLogger("alphacopy.main")

    logger.info("=" * 60)
    logger.info("  AlphaCopy Starting")
    logger.info(f"  Mode: {'LIVE TRADING' if live else 'DRY RUN (safe)'}")
    logger.info(f"  Bots: {', '.join(bots_to_run)}")
    logger.info("=" * 60)

    if live:
        logger.warning("LIVE TRADING MODE — Real money at risk!")
        await asyncio.sleep(3)

    risk      = RiskManager(CONFIG)
    notifier  = Notifier(
        telegram_token   = CONFIG.telegram_bot_token,
        telegram_chat_id = CONFIG.telegram_chat_id,
        discord_webhook  = CONFIG.discord_webhook_url,
    )
    dashboard = Dashboard(risk)

    tasks = []

    if "hl" in bots_to_run:
        hl_bot = HyperliquidBot(CONFIG.hyperliquid, risk, notifier, dry_run=not live)
        tasks.append(asyncio.create_task(hl_bot.run(), name="hyperliquid"))

    if "bn" in bots_to_run:
        bn_bot = BinanceBot(CONFIG.binance, risk, notifier, dry_run=not live)
        tasks.append(asyncio.create_task(bn_bot.run(), name="binance"))

    if "poly" in bots_to_run:
        poly_bot = PolymarketBot(CONFIG.polymarket, risk, notifier, dry_run=not live)
        tasks.append(asyncio.create_task(poly_bot.run(), name="polymarket"))

    tasks.append(asyncio.create_task(run_dashboard_loop(dashboard, 120), name="dashboard"))

    def handle_signal():
        for task in tasks:
            task.cancel()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal)

    await notifier.send(
        f"AlphaCopy started | Mode: {'LIVE' if live else 'DRY'} | "
        f"Bots: {', '.join(bots_to_run)}")

    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except asyncio.CancelledError:
        pass
    finally:
        dashboard.print_summary()
        logger.info("AlphaCopy shutdown complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AlphaCopy")
    parser.add_argument("--live",      action="store_true")
    parser.add_argument("--bot",       default="all")
    parser.add_argument("--dashboard", action="store_true")
    args = parser.parse_args()

    if args.dashboard:
        setup_logging("INFO")
        Dashboard(RiskManager(CONFIG)).print_summary()
        sys.exit(0)

    bots = {"all": ["hl","bn","poly"], "hl": ["hl"],
            "bn": ["bn"], "poly": ["poly"]}.get(args.bot, ["hl","bn","poly"])

    asyncio.run(main(bots, live=args.live))
