"""
AlphaCopy - Telegram Trade Journal
Posts beautifully formatted trade alerts to your Telegram channel.

All events:
  - Trade ENTERED    (entry price, size, SL, TP, R:R, source wallet)
  - Trade EXITED     (exit price, PnL $, PnL %, R:R achieved, duration)
  - Stop Loss hit    (loss amount, drawdown warning if significant)
  - Take Profit hit  (win celebration)
  - Trailing stop    (partial profit capture)
  - Bot halted       (emergency alert)
  - Daily summary    (posted at market close)
  - Weekly report    (comprehensive stats)

Setup:
  1. Create bot via @BotFather → get token
  2. Add bot to your channel as admin
  3. Get channel chat ID (use @getmyid_bot)
  4. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import aiohttp
from dataclasses import dataclass

logger = logging.getLogger(__name__)

PLATFORM_EMOJI = {
    "hyperliquid": "◈",
    "binance":     "⬡",
    "polymarket":  "◉",
    "hl":          "◈",
    "bn":          "⬡",
    "pm":          "◉",
}

SIDE_EMOJI = {
    "LONG":  "🟢 LONG",
    "SHORT": "🔴 SHORT",
    "YES":   "🟢 YES",
    "NO":    "🔴 NO",
}


def fmt_price(price: float) -> str:
    if price >= 1000:
        return f"{price:,.2f}"
    elif price >= 1:
        return f"{price:.4f}"
    else:
        return f"{price:.4f}"


def fmt_pnl(pnl: float) -> str:
    arrow = "▲" if pnl >= 0 else "▼"
    sign  = "+" if pnl >= 0 else ""
    return f"{arrow} {sign}${pnl:,.2f}"


def fmt_pct(pct: float) -> str:
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"


def calc_rr(entry: float, sl: float, tp: float, side: str) -> str:
    risk   = abs(entry - sl)
    reward = abs(tp - entry)
    if risk == 0:
        return "—"
    return f"{reward / risk:.2f}"


def calc_rr_achieved(entry: float, sl: float, exit_price: float, side: str) -> str:
    risk = abs(entry - sl)
    if risk == 0:
        return "—"
    if side in ("LONG", "YES"):
        achieved = (exit_price - entry) / risk
    else:
        achieved = (entry - exit_price) / risk
    return f"{achieved:.2f}R"


def duration_str(opened_at: datetime) -> str:
    delta = datetime.utcnow() - opened_at
    if delta.total_seconds() < 60:
        return f"{int(delta.total_seconds())}s"
    elif delta.total_seconds() < 3600:
        return f"{int(delta.total_seconds() / 60)}m"
    elif delta.total_seconds() < 86400:
        return f"{int(delta.total_seconds() / 3600)}h {int((delta.total_seconds() % 3600) / 60)}m"
    else:
        return f"{int(delta.days)}d {int((delta.total_seconds() % 86400) / 3600)}h"


class TelegramJournal:
    """
    Rich Telegram trade journal for all three bots.
    Uses HTML parse mode for formatting.
    """

    def __init__(self, bot_token: str, chat_id: str, dry_run: bool = False):
        self.token    = bot_token
        self.chat_id  = chat_id
        self.dry_run  = dry_run
        self.base_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        # Track trade stats for summary
        self._trade_log: List[dict] = []

    # ─────────────────────────────────────────────────────────────────────
    # Trade lifecycle messages
    # ─────────────────────────────────────────────────────────────────────
    async def trade_entered(self,
                             platform: str,
                             symbol: str,
                             side: str,
                             entry_price: float,
                             size_usd: float,
                             stop_loss: float,
                             take_profit: float,
                             source_wallet: str,
                             leverage: int = 1,
                             trade_id: str = "",
                             opened_at: Optional[datetime] = None) -> None:
        ts    = (opened_at or datetime.utcnow()).strftime("%H:%M:%S UTC")
        rr    = calc_rr(entry_price, stop_loss, take_profit, side)
        icon  = PLATFORM_EMOJI.get(platform, "•")
        sl_pct = abs(entry_price - stop_loss) / entry_price * 100
        tp_pct = abs(take_profit - entry_price) / entry_price * 100
        side_str = SIDE_EMOJI.get(side, side)
        lev_str  = f" {leverage}x" if leverage > 1 else ""

        msg = (
            f"{icon} <b>TRADE ENTERED</b>{lev_str}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 <b>{symbol}</b> — {side_str}\n"
            f"🏛 Platform: <code>{platform.upper()}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Entry:  <code>{fmt_price(entry_price)}</code>\n"
            f"📏 Size:   <code>${size_usd:,.0f}</code>\n"
            f"🛑 Stop:   <code>{fmt_price(stop_loss)}</code>  (-{sl_pct:.1f}%)\n"
            f"🎯 Target: <code>{fmt_price(take_profit)}</code>  (+{tp_pct:.1f}%)\n"
            f"⚖️ R:R:    <code>{rr}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Copying: <code>{source_wallet[:12]}…</code>\n"
            f"🕐 Time:   {ts}\n"
            f"🆔 ID:     <code>{trade_id}</code>"
        )

        await self._send(msg)
        self._log_trade("ENTERED", platform, symbol, side, entry_price,
                        size_usd, stop_loss, take_profit, trade_id, opened_at)

    async def trade_exited(self,
                            platform: str,
                            symbol: str,
                            side: str,
                            entry_price: float,
                            exit_price: float,
                            size_usd: float,
                            pnl_usd: float,
                            stop_loss: float,
                            reason: str = "MANUAL",
                            trade_id: str = "",
                            opened_at: Optional[datetime] = None) -> None:
        ts       = datetime.utcnow().strftime("%H:%M:%S UTC")
        icon     = PLATFORM_EMOJI.get(platform, "•")
        pnl_pct  = (pnl_usd / size_usd * 100)
        duration = duration_str(opened_at) if opened_at else "—"
        rr_ach   = calc_rr_achieved(entry_price, stop_loss, exit_price, side)
        side_str = SIDE_EMOJI.get(side, side)

        result_icon = "✅" if pnl_usd >= 0 else "❌"
        reason_map  = {
            "STOP_LOSS":    "🛑 Stop Loss Hit",
            "TAKE_PROFIT":  "🎯 Take Profit Hit",
            "TRAILING_STOP":"🔄 Trailing Stop",
            "TRADER_CLOSED":"👤 Trader Closed",
            "MANUAL":       "✋ Manual Close",
        }
        reason_str = reason_map.get(reason, reason)

        msg = (
            f"{icon} {result_icon} <b>TRADE EXITED</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 <b>{symbol}</b> — {side_str}\n"
            f"📋 {reason_str}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📥 Entry:  <code>{fmt_price(entry_price)}</code>\n"
            f"📤 Exit:   <code>{fmt_price(exit_price)}</code>\n"
            f"📏 Size:   <code>${size_usd:,.0f}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"💵 P&L:    <b>{fmt_pnl(pnl_usd)}</b>  ({fmt_pct(pnl_pct)})\n"
            f"⚖️ R Achieved: <code>{rr_ach}</code>\n"
            f"⏱ Duration: {duration}\n"
            f"🕐 Time:    {ts}\n"
            f"🆔 ID:      <code>{trade_id}</code>"
        )

        await self._send(msg)
        self._update_trade("EXITED", trade_id, exit_price, pnl_usd, reason)

    async def stop_loss_hit(self, platform: str, symbol: str, side: str,
                             entry: float, stop: float, size: float,
                             loss: float, trade_id: str = "",
                             opened_at: Optional[datetime] = None) -> None:
        """Specialized SL alert with loss analysis."""
        icon      = PLATFORM_EMOJI.get(platform, "•")
        loss_pct  = abs(loss / size * 100)
        duration  = duration_str(opened_at) if opened_at else "—"

        msg = (
            f"{icon} 🛑 <b>STOP LOSS HIT</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 <b>{symbol}</b> ({platform.upper()})\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📥 Entry: <code>{fmt_price(entry)}</code>\n"
            f"🛑 Stop:  <code>{fmt_price(stop)}</code>\n"
            f"📉 Loss:  <b>-${abs(loss):,.2f}</b>  (-{loss_pct:.1f}%)\n"
            f"⏱ Held:  {duration}\n"
            f"🆔 ID:    <code>{trade_id}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 Max risk per trade: 1% equity. Loss is contained."
        )
        await self._send(msg)

    async def take_profit_hit(self, platform: str, symbol: str, side: str,
                               entry: float, tp: float, size: float,
                               profit: float, rr: str = "",
                               trade_id: str = "",
                               opened_at: Optional[datetime] = None) -> None:
        icon      = PLATFORM_EMOJI.get(platform, "•")
        profit_pct = (profit / size * 100)
        duration  = duration_str(opened_at) if opened_at else "—"

        msg = (
            f"{icon} 🎯 <b>TAKE PROFIT HIT</b> 🎉\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 <b>{symbol}</b> ({platform.upper()})\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📥 Entry:   <code>{fmt_price(entry)}</code>\n"
            f"🎯 Target:  <code>{fmt_price(tp)}</code>\n"
            f"💵 Profit:  <b>+${profit:,.2f}</b>  (+{profit_pct:.1f}%)\n"
            f"⚖️ R:R got: <code>{rr}</code>\n"
            f"⏱ Held:    {duration}\n"
            f"🆔 ID:      <code>{trade_id}</code>"
        )
        await self._send(msg)

    async def trailing_stop(self, platform: str, symbol: str, side: str,
                             entry: float, exit_price: float,
                             pnl: float, trade_id: str = "") -> None:
        icon = PLATFORM_EMOJI.get(platform, "•")
        msg = (
            f"{icon} 🔄 <b>TRAILING STOP</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 <b>{symbol}</b> ({platform.upper()})\n"
            f"📥 Entry: <code>{fmt_price(entry)}</code>\n"
            f"📤 Exit:  <code>{fmt_price(exit_price)}</code>\n"
            f"💵 PnL:   <b>{fmt_pnl(pnl)}</b>  ({'profit locked' if pnl > 0 else 'partial loss'})\n"
            f"🆔 ID:    <code>{trade_id}</code>"
        )
        await self._send(msg)

    async def bot_halted(self, platform: str, reason: str,
                          drawdown_pct: float) -> None:
        icon = PLATFORM_EMOJI.get(platform, "•")
        msg = (
            f"🚨 <b>BOT HALTED — {platform.upper()}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ Reason: {reason}\n"
            f"📉 Drawdown: <b>{drawdown_pct:.1f}%</b>\n"
            f"🕐 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔧 Manual review required before restarting."
        )
        await self._send(msg)

    async def trade_skipped(self, platform: str, symbol: str, reason: str) -> None:
        icon = PLATFORM_EMOJI.get(platform, "•")
        msg = (
            f"{icon} ⏭ <b>Trade Skipped</b>\n"
            f"Symbol: {symbol} | {reason}"
        )
        await self._send(msg)

    # ─────────────────────────────────────────────────────────────────────
    # Summary reports
    # ─────────────────────────────────────────────────────────────────────
    async def daily_summary(self, summaries: Dict) -> None:
        """Post end-of-day portfolio summary."""
        ts = datetime.utcnow().strftime("%Y-%m-%d")
        total_pnl = sum(s.get("pnl", 0) for s in summaries.values())

        lines = [
            f"📊 <b>Daily Summary — {ts}</b>",
            "━━━━━━━━━━━━━━━━━━━━━",
        ]

        for platform, s in summaries.items():
            icon = PLATFORM_EMOJI.get(platform, "•")
            pnl  = s.get("pnl", 0)
            wr   = s.get("win_rate", 0)
            eq   = s.get("equity", 0)
            dd   = s.get("drawdown_pct", 0)
            trades = s.get("total_trades", 0)

            lines.append(
                f"\n{icon} <b>{platform.upper()}</b>\n"
                f"   Equity:   <code>${eq:,.2f}</code>\n"
                f"   Day PnL:  <b>{fmt_pnl(pnl)}</b>\n"
                f"   Win Rate: {wr:.0f}%  |  DD: {dd:.1f}%\n"
                f"   Trades:   {trades}"
            )

        lines += [
            "\n━━━━━━━━━━━━━━━━━━━━━",
            f"💼 <b>Portfolio PnL: {fmt_pnl(total_pnl)}</b>",
            f"📅 Allocated: $30,000",
        ]
        await self._send("\n".join(lines))

    async def weekly_report(self, summaries: Dict,
                             trade_history: List[dict]) -> None:
        """Post comprehensive weekly performance report."""
        wins   = [t for t in trade_history if t.get("pnl_usd", 0) > 0]
        losses = [t for t in trade_history if t.get("pnl_usd", 0) < 0]
        total_pnl = sum(t.get("pnl_usd", 0) for t in trade_history)

        avg_win  = sum(t["pnl_usd"] for t in wins)  / len(wins)  if wins  else 0
        avg_loss = sum(t["pnl_usd"] for t in losses) / len(losses) if losses else 0
        pf       = abs(avg_win / avg_loss) if avg_loss else 0

        lines = [
            "📈 <b>Weekly Performance Report</b>",
            f"Week ending {datetime.utcnow().strftime('%b %d, %Y')}",
            "━━━━━━━━━━━━━━━━━━━━━",
            f"📊 Trades: {len(trade_history)} total",
            f"✅ Winners: {len(wins)}  |  ❌ Losers: {len(losses)}",
            f"🎯 Win Rate: {len(wins)/len(trade_history)*100:.0f}%" if trade_history else "",
            f"💰 Avg Win:  +${avg_win:.2f}",
            f"📉 Avg Loss: -${abs(avg_loss):.2f}",
            f"⚖️ Profit Factor: {pf:.2f}",
            "━━━━━━━━━━━━━━━━━━━━━",
            f"💼 <b>Net PnL: {fmt_pnl(total_pnl)}</b>",
        ]
        await self._send("\n".join(lines))

    # ─────────────────────────────────────────────────────────────────────
    # Bot startup / shutdown
    # ─────────────────────────────────────────────────────────────────────
    async def bot_started(self, mode: str, bots: List[str],
                           allocated: float) -> None:
        msg = (
            f"🚀 <b>AlphaCopy Started</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"Mode: {'🔴 LIVE TRADING' if mode == 'LIVE' else '🟡 DRY RUN'}\n"
            f"Bots: {', '.join(b.upper() for b in bots)}\n"
            f"Capital: <code>${allocated:,.0f}</code>\n"
            f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        )
        await self._send(msg)

    async def bot_stopped(self, runtime: str, final_summaries: Dict) -> None:
        total_pnl = sum(s.get("pnl", 0) for s in final_summaries.values())
        msg = (
            f"⏹ <b>AlphaCopy Stopped</b>\n"
            f"Runtime: {runtime}\n"
            f"Final PnL: <b>{fmt_pnl(total_pnl)}</b>"
        )
        await self._send(msg)

    # ─────────────────────────────────────────────────────────────────────
    # Internal
    # ─────────────────────────────────────────────────────────────────────
    async def _send(self, text: str) -> None:
        if self.dry_run:
            logger.info(f"[TELEGRAM-DRY] {text[:100]}…")
            return
        if not self.token or not self.chat_id:
            logger.debug("Telegram not configured — skipping")
            return
        payload = {
            "chat_id":    self.chat_id,
            "text":       text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(self.base_url, json=payload,
                                  timeout=aiohttp.ClientTimeout(total=5)) as r:
                    if r.status != 200:
                        resp = await r.text()
                        logger.warning(f"Telegram API error {r.status}: {resp[:200]}")
        except Exception as e:
            logger.warning(f"Telegram send failed: {e}")

    def _log_trade(self, event: str, platform: str, symbol: str, side: str,
                   entry: float, size: float, sl: float, tp: float,
                   trade_id: str, opened_at: Optional[datetime]) -> None:
        self._trade_log.append({
            "event":      event,
            "platform":   platform,
            "symbol":     symbol,
            "side":       side,
            "entry":      entry,
            "size":       size,
            "sl":         sl,
            "tp":         tp,
            "trade_id":   trade_id,
            "opened_at":  opened_at or datetime.utcnow(),
            "status":     "OPEN",
            "pnl_usd":    0.0,
        })

    def _update_trade(self, event: str, trade_id: str, exit_price: float,
                      pnl_usd: float, reason: str) -> None:
        for t in self._trade_log:
            if t["trade_id"] == trade_id:
                t["event"]      = event
                t["exit_price"] = exit_price
                t["pnl_usd"]    = pnl_usd
                t["reason"]     = reason
                t["status"]     = "CLOSED"
                t["closed_at"]  = datetime.utcnow()
                break


# ─── Scheduler for daily/weekly summaries ────────────────────────────────
async def run_summary_scheduler(journal: TelegramJournal,
                                  risk_manager,
                                  close_hour_utc: int = 14) -> None:
    """Posts daily summary at specified UTC hour (e.g. 14:00 = NSE close)."""
    while True:
        now  = datetime.utcnow()
        next_run = now.replace(hour=close_hour_utc, minute=0, second=0)
        if now.hour >= close_hour_utc:
            next_run += timedelta(days=1)
        await asyncio.sleep((next_run - now).total_seconds())

        summaries = {
            b: risk_manager.get_summary(b)
            for b in ["hyperliquid", "binance", "polymarket"]
        }
        await journal.daily_summary(summaries)

        # Weekly report on Sundays
        if datetime.utcnow().weekday() == 6:
            await journal.weekly_report(summaries, journal._trade_log)
