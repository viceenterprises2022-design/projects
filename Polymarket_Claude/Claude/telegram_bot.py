import asyncio
from datetime import time as dtime
from typing import Optional
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode
from core.config import cfg, setup_logger
from analytics.pnl_tracker import pnl_tracker

logger = setup_logger("telegram")

class TelegramBot:
    def __init__(self):
        self._app: Optional[Application] = None
        self._bot: Optional[Bot] = None
        self._chat_id = cfg.telegram_chat_id
        self._risk_engine = None
        self._whale_tracker = None
        self._order_manager = None

    def inject_dependencies(self, risk_engine, whale_tracker, order_manager):
        self._risk_engine = risk_engine
        self._whale_tracker = whale_tracker
        self._order_manager = order_manager

    async def initialize(self):
        self._app = Application.builder().token(cfg.telegram_token).build()
        self._bot = self._app.bot
        for name, handler in [
            ("start", self._cmd_start), ("status", self._cmd_status),
            ("positions", self._cmd_positions), ("pause", self._cmd_pause),
            ("resume", self._cmd_resume), ("wallets", self._cmd_wallets),
            ("addwallet", self._cmd_addwallet), ("removewallet", self._cmd_removewallet),
            ("pnl", self._cmd_pnl), ("help", self._cmd_help),
        ]:
            self._app.add_handler(CommandHandler(name, handler))
        h, m = map(int, cfg.telegram.get("daily_report_time", "20:00").split(":"))
        self._app.job_queue.run_daily(self._scheduled_report, time=dtime(hour=h, minute=m))
        logger.info("Telegram bot initialized")

    async def start_polling(self):
        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
        logger.info("Telegram polling started")

    async def stop(self):
        if self._app:
            await self._app.updater.stop()
            await self._app.stop()
            await self._app.shutdown()

    async def send_message(self, text: str, parse_mode=ParseMode.MARKDOWN):
        if not self._bot: return
        try:
            await self._bot.send_message(chat_id=self._chat_id, text=text, parse_mode=parse_mode)
        except Exception as e:
            logger.error("Telegram send failed: %s", e)

    async def handle_notification(self, event_type: str, data: dict):
        tg = cfg.telegram
        if event_type == "trade_entry" and tg.get("notify_on_trade_entry"):
            await self.send_message(self._fmt_entry(data))
        elif event_type == "trade_exit" and tg.get("notify_on_trade_exit"):
            await self.send_message(self._fmt_exit(data))
        elif event_type == "trade_error" and tg.get("notify_on_errors"):
            await self.send_message(f"❌ *Trade Error*\n\n`{data.get('error','Unknown')[:200]}`")

    def _fmt_entry(self, d: dict) -> str:
        dry = " 🔵 [DRY]" if d.get("dry_run") else " ⚡ [LIVE]"
        c = d.get("consensus_count", 1)
        cs = f" (🐋×{c})" if c > 1 else ""
        return (f"✅ *Trade Entered*{dry}\n\n"
                f"📋 `{d.get('question','')[:60]}`\n"
                f"📍 Outcome: `{d.get('outcome_label','YES')}`\n\n"
                f"💵 Spent:  `${d.get('cost_usd',0):.2f}`\n"
                f"📈 Entry:  `{d.get('entry_price',0):.4f}`\n"
                f"📊 Shares: `{d.get('shares',0):.4f}`\n\n"
                f"🎯 TP: `{d.get('take_profit',0):.4f}`\n"
                f"⛔ SL: `{d.get('stop_loss',0):.4f}`\n\n"
                f"🐋 Source: `{d.get('whale_label','')}` | {d.get('signal_type','')}{cs}")

    def _fmt_exit(self, d: dict) -> str:
        pnl = d.get("pnl_usd", 0); pct = d.get("pnl_pct", 0)
        em = "🟢" if pnl >= 0 else "🔴"
        dry = " 🔵 [DRY]" if d.get("dry_run") else " ⚡ [LIVE]"
        reason = d.get("reason","Unknown").replace("TAKE_PROFIT","🎯 Take Profit").replace("STOP_LOSS","⛔ Stop Loss").replace("MAX_HOLD","⏰ Max Hold").replace("WHALE_EXIT","🐋 Whale Exit")
        return (f"{em} *Trade Exited*{dry}\n\n"
                f"📋 `{d.get('question','')[:60]}`\n"
                f"📍 Outcome: `{d.get('outcome_label','YES')}`\n\n"
                f"📈 Entry: `{d.get('entry_price',0):.4f}`\n"
                f"📉 Exit:  `{d.get('exit_price',0):.4f}`\n"
                f"💰 P&L:   `${pnl:+.2f}` ({pct:+.1f}%)\n\n"
                f"🏷️ Reason: `{reason}`")

    async def _scheduled_report(self, context: ContextTypes.DEFAULT_TYPE):
        try:
            await self.send_message(await pnl_tracker.format_daily_report())
        except Exception as e:
            logger.error("Scheduled report failed: %s", e)

    # ── Commands ───────────────────────────────────────────────────────────────

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        mode = "🔵 DRY RUN" if cfg.dry_run else "⚡ LIVE"
        paused = "⏸️ PAUSED" if (self._risk_engine and self._risk_engine.is_paused) else "▶️ RUNNING"
        await update.message.reply_text(
            f"🤖 *Polybot — Polymarket Copy Trader*\n\nStatus: `{paused}`\nMode: `{mode}`\nTracking: `{len(cfg.whale_wallets)}` whale wallets\n\nUse /help for commands.",
            parse_mode=ParseMode.MARKDOWN)

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("⏳ Fetching...", parse_mode=ParseMode.MARKDOWN)
        try:
            report = await pnl_tracker.format_daily_report()
            header = "⏸️ *BOT IS PAUSED*\n\n" if (self._risk_engine and self._risk_engine.is_paused) else ""
            await update.message.reply_text(header + report, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def _cmd_positions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            await update.message.reply_text(await pnl_tracker.format_position_list(), parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def _cmd_pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self._risk_engine:
            self._risk_engine.pause("Telegram /pause")
        await update.message.reply_text("⏸️ *Bot PAUSED*\n\nNo new trades. Use /resume to restart.", parse_mode=ParseMode.MARKDOWN)

    async def _cmd_resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self._risk_engine:
            self._risk_engine.resume()
        await update.message.reply_text("▶️ *Bot RESUMED*\n\nMonitoring whales.", parse_mode=ParseMode.MARKDOWN)

    async def _cmd_wallets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._whale_tracker:
            await update.message.reply_text("❌ Tracker not connected"); return
        wallets = self._whale_tracker.get_tracked_wallets()
        if not wallets:
            await update.message.reply_text("📭 No wallets being tracked."); return
        lines = ["🐋 *Tracked Whale Wallets*\n"]
        for i, w in enumerate(wallets, 1):
            lines.append(f"`{i}. {w['label']} — {w['address'][:16]}...`")
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

    async def _cmd_addwallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Usage: `/addwallet 0xADDRESS label`", parse_mode=ParseMode.MARKDOWN); return
        address = context.args[0]
        label = " ".join(context.args[1:]) if len(context.args) > 1 else address[:10]
        if self._whale_tracker:
            self._whale_tracker.add_wallet(address, label)
        await update.message.reply_text(f"✅ Added: `{label}` (`{address[:16]}...`)", parse_mode=ParseMode.MARKDOWN)

    async def _cmd_removewallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Usage: `/removewallet 0xADDRESS`", parse_mode=ParseMode.MARKDOWN); return
        if self._whale_tracker:
            self._whale_tracker.remove_wallet(context.args[0])
        await update.message.reply_text(f"🗑️ Removed: `{context.args[0][:16]}...`", parse_mode=ParseMode.MARKDOWN)

    async def _cmd_pnl(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            stats = await pnl_tracker.get_overall_stats()
            wr = f"{stats.get('win_rate',0)*100:.1f}%"
            await update.message.reply_text(
                f"📈 *All-Time P&L Stats*\n\n"
                f"Total Trades:  `{stats.get('total',0)}`\n"
                f"Wins / Losses: `{stats.get('wins',0)} / {stats.get('losses',0)}`\n"
                f"Win Rate:      `{wr}`\n"
                f"Total P&L:     `${stats.get('total_pnl',0):+.2f}`\n"
                f"Best Trade:    `${stats.get('best_trade',0):+.2f}`\n"
                f"7-Day P&L:     `${stats.get('pnl_7d',0):+.2f}`\n"
                f"30-Day P&L:    `${stats.get('pnl_30d',0):+.2f}`",
                parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 *Polybot Commands*\n\n"
            "📊 *Info*\n"
            "  /start       — Status overview\n"
            "  /status      — Portfolio + daily P&L\n"
            "  /positions   — Open positions\n"
            "  /pnl         — All-time stats\n\n"
            "🐋 *Whale Management*\n"
            "  /wallets                  — List wallets\n"
            "  /addwallet `<addr>` `<label>` — Add wallet\n"
            "  /removewallet `<addr>`     — Remove wallet\n\n"
            "⚙️ *Control*\n"
            "  /pause       — Emergency stop\n"
            "  /resume      — Resume trading\n"
            "  /help        — This menu",
            parse_mode=ParseMode.MARKDOWN)

telegram_bot = TelegramBot()
