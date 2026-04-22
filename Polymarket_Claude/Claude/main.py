"""
main.py — Polybot orchestrator.

Starts all async loops concurrently:
  - Whale tracker (polls whale wallets every 5s)
  - Position monitor (checks SL/TP every 30s)
  - Telegram bot polling

Usage:
    python main.py
    DRY_RUN=false python main.py   # live trading
"""
import asyncio, signal, sys
from core.config import cfg, setup_logger

logger = setup_logger("main")

async def main():
    mode = "🔵 DRY RUN" if cfg.dry_run else "⚡ LIVE"
    logger.info("="*60)
    logger.info("  POLYBOT — Polymarket Copy Trader")
    logger.info("  Mode: %s | Wallets: %d", mode, len(cfg.whale_wallets))
    logger.info("  Capital: $%.0f | Max position: $%.0f",
                cfg.risk.get("total_capital_usd",2000), cfg.risk.get("max_position_usd",100))
    logger.info("="*60)
    if cfg.dry_run:
        logger.warning("DRY RUN — no real orders. Set DRY_RUN=false to go live.")

    # Init DB
    from storage.db import init_db
    await init_db()

    # Init CLOB
    from core.clob_client import polymarket
    try:
        polymarket.initialize()
        logger.info("Balance: $%.2f USDC", polymarket.get_balance())
    except Exception as e:
        logger.error("CLOB init failed: %s", e)
        if not cfg.dry_run:
            logger.error("Cannot run LIVE without CLOB. Set DRY_RUN=true or fix credentials.")
            sys.exit(1)
        logger.warning("Continuing in DRY RUN without CLOB auth")

    # Import modules
    from whale.tracker import WhaleTracker
    from execution.risk_engine import risk_engine
    from execution.order_manager import order_manager
    from notifications.telegram_bot import telegram_bot

    whale_tracker = WhaleTracker()

    # Wire signal flow: whale → copy trade or exit
    async def on_signal(sig):
        if sig.direction == "BUY":
            await order_manager.execute_copy_trade(sig)
        elif sig.direction == "SELL":
            await order_manager.handle_whale_exit_signal(sig)

    whale_tracker.add_signal_handler(on_signal)
    order_manager.add_notification_handler(telegram_bot.handle_notification)

    # Init Telegram
    telegram_bot.inject_dependencies(risk_engine, whale_tracker, order_manager)
    await telegram_bot.initialize()

    # Startup message
    await telegram_bot.send_message(
        f"🚀 *Polybot Started*\n\nMode: `{mode}`\n"
        f"Capital: `${cfg.risk.get('total_capital_usd',2000):.0f}`\n"
        f"Tracking: `{len(cfg.whale_wallets)} whale wallets`\n"
        f"Position size: `${cfg.position_sizing.get('fixed_amount_usd',25)}/trade`\n"
        f"SL: `{cfg.risk.get('stop_loss_pct',0.5)*100:.0f}%` | "
        f"TP: `{cfg.risk.get('take_profit_pct',1.0)*100:.0f}%`\n\nUse /help for commands."
    )

    # Start all loops
    import asyncio as aio
    tasks = [
        aio.create_task(whale_tracker.start(),           name="whale_tracker"),
        aio.create_task(order_manager.start_position_monitor(), name="position_monitor"),
        aio.create_task(telegram_bot.start_polling(),    name="telegram"),
    ]

    loop = aio.get_event_loop()
    def shutdown(*_):
        logger.info("Shutdown signal received")
        for t in tasks: t.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try: loop.add_signal_handler(sig, shutdown)
        except (NotImplementedError, RuntimeError): pass  # Windows fallback

    try:
        await aio.gather(*tasks, return_exceptions=True)
    except aio.CancelledError:
        pass
    finally:
        logger.info("Cleaning up...")
        whale_tracker.stop()
        order_manager.stop_monitor()
        from core.gamma_client import gamma
        from core.subgraph_client import subgraph
        await gamma.close()
        await subgraph.close()
        await telegram_bot.send_message("🛑 *Polybot stopped.*")
        await telegram_bot.stop()
        logger.info("Shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt — bye")
