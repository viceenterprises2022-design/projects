import time
from typing import Callable, Optional
from core.config import cfg, setup_logger
from core.clob_client import polymarket
from execution.risk_engine import risk_engine
from storage.db import db

logger = setup_logger("orders")

class OrderManager:
    def __init__(self):
        self._notification_handlers: list[Callable] = []
        self._monitor_interval = 30
        self._running = False

    def add_notification_handler(self, h: Callable): self._notification_handlers.append(h)

    async def _notify(self, event_type: str, data: dict):
        for h in self._notification_handlers:
            try: await h(event_type, data)
            except Exception as e: logger.error("Notify error: %s", e)

    async def execute_copy_trade(self, signal) -> Optional[dict]:
        decision = await risk_engine.evaluate(signal)
        if not decision.approved:
            logger.info("Trade skipped: %s | %s", signal.question[:40], decision.reason)
            await db.log_whale_signal({"wallet":signal.whale_wallet,"token_id":signal.token_id,
                "condition_id":signal.condition_id,"type":signal.signal_type,"delta_shares":signal.delta_shares},
                copied=False, skip_reason=decision.reason)
            return None
        token_id = signal.token_id; amount_usd = decision.amount_usd
        try:
            result = await polymarket.async_place_market_buy(token_id, amount_usd)
        except Exception as e:
            logger.error("Order failed: %s", e)
            await self._notify("trade_error", {"error":str(e),"signal":signal,"amount_usd":amount_usd})
            return None
        if result.get("status") not in ("filled","matched","MATCHED"):
            if not cfg.dry_run:
                logger.warning("Order not filled: %s", result); return None
        fill_price = result.get("fill_price", signal.current_price)
        shares     = result.get("shares", amount_usd / max(fill_price, 0.01))
        sl = risk_engine.calc_sl(fill_price); tp = risk_engine.calc_tp(fill_price)
        pos = {"token_id":token_id,"condition_id":signal.condition_id,"question":signal.question,
               "outcome_label":signal.outcome_label,"side":"BUY","shares":shares,"entry_price":fill_price,
               "cost_usd":amount_usd,"entry_time":int(time.time()),"whale_wallet":signal.whale_wallet,
               "signal_type":signal.signal_type,"stop_loss_price":sl,"take_profit_price":tp}
        await db.save_position(pos)
        await db.log_trade({"order_id":result.get("order_id"),"token_id":token_id,"condition_id":signal.condition_id,
            "question":signal.question,"side":"BUY","shares":shares,"price":fill_price,"cost_usd":amount_usd,
            "whale_wallet":signal.whale_wallet,"signal_type":signal.signal_type,"dry_run":result.get("dry_run",False),"raw_response":result})
        await db.log_whale_signal({"wallet":signal.whale_wallet,"token_id":token_id,
            "condition_id":signal.condition_id,"type":signal.signal_type,"delta_shares":signal.delta_shares}, copied=True)
        logger.info("Trade executed: BUY %.4f shares @ %.4f | $%.2f | SL=%.4f TP=%.4f", shares, fill_price, amount_usd, sl, tp)
        await self._notify("trade_entry", {"question":signal.question,"outcome_label":signal.outcome_label,
            "token_id":token_id,"shares":shares,"entry_price":fill_price,"cost_usd":amount_usd,
            "stop_loss":sl,"take_profit":tp,"whale_label":signal.whale_label,
            "signal_type":signal.signal_type,"consensus_count":signal.consensus_count,"dry_run":result.get("dry_run",False)})
        return pos

    async def exit_position(self, token_id: str, reason: str = "Manual") -> Optional[dict]:
        pos = await db.get_position_by_token(token_id)
        if not pos: return None
        try:
            result = await polymarket.async_place_market_sell(token_id, pos["shares"])
        except Exception as e:
            logger.error("Exit failed: %s", e); return None
        exit_price = result.get("fill_price") or await polymarket.async_get_midpoint(token_id)
        proceeds   = result.get("proceeds_usd", pos["shares"] * exit_price)
        pnl        = round(proceeds - pos["cost_usd"], 4)
        await db.close_position(token_id, exit_price, pnl)
        await db.log_trade({"order_id":result.get("order_id"),"token_id":token_id,
            "condition_id":pos.get("condition_id"),"question":pos.get("question"),
            "side":"SELL","shares":pos["shares"],"price":exit_price,"cost_usd":proceeds,
            "whale_wallet":pos.get("whale_wallet"),"signal_type":f"EXIT_{reason}","dry_run":result.get("dry_run",False)})
        risk_engine.update_daily_pnl(pnl)
        pnl_pct = (pnl / pos["cost_usd"] * 100) if pos["cost_usd"] else 0
        emoji = "🟢" if pnl >= 0 else "🔴"
        logger.info("%s Exit %s: P&L $%.2f (%.1f%%) reason=%s", emoji, pos.get("question","")[:30], pnl, pnl_pct, reason)
        await self._notify("trade_exit", {"question":pos.get("question",""),"outcome_label":pos.get("outcome_label",""),
            "token_id":token_id,"shares":pos["shares"],"entry_price":pos["entry_price"],"exit_price":exit_price,
            "cost_usd":pos["cost_usd"],"proceeds_usd":proceeds,"pnl_usd":pnl,"pnl_pct":pnl_pct,
            "reason":reason,"dry_run":result.get("dry_run",False)})
        return {"pnl_usd": pnl, "exit_price": exit_price}

    async def start_position_monitor(self):
        self._running = True
        logger.info("Position monitor started (interval=%ds)", self._monitor_interval)
        import asyncio
        while self._running:
            try:
                positions = await db.get_open_positions()
                if positions:
                    await asyncio.gather(*[self._check_position(pos) for pos in positions], return_exceptions=True)
                await asyncio.sleep(self._monitor_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Monitor error: %s", e)
                await asyncio.sleep(self._monitor_interval)

    def stop_monitor(self): self._running = False

    async def _check_position(self, pos: dict):
        import asyncio
        token_id    = pos["token_id"]
        entry_time  = pos.get("entry_time", int(time.time()))
        current_p   = await polymarket.async_get_midpoint(token_id)
        if not current_p: return
        sl = pos.get("stop_loss_price"); tp = pos.get("take_profit_price")
        if sl and current_p <= sl:
            logger.warning("STOP LOSS: %s @ %.4f", pos.get("question","")[:30], current_p)
            await self.exit_position(token_id, "STOP_LOSS"); return
        if tp and current_p >= tp:
            logger.info("TAKE PROFIT: %s @ %.4f", pos.get("question","")[:30], current_p)
            await self.exit_position(token_id, "TAKE_PROFIT"); return
        hold_days = (int(time.time()) - entry_time) / 86400
        max_hold  = cfg.exit.get("max_hold_days", 30)
        if hold_days > max_hold:
            await self.exit_position(token_id, "MAX_HOLD")

    async def handle_whale_exit_signal(self, signal):
        if not cfg.exit.get("follow_whale_exit", True): return
        if signal.direction != "SELL" and signal.signal_type != "CLOSED": return
        pos = await db.get_position_by_token(signal.token_id)
        if pos:
            await self.exit_position(signal.token_id, f"WHALE_EXIT_{signal.whale_label}")

import asyncio
order_manager = OrderManager()
