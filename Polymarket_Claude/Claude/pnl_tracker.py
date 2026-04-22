import time
from datetime import date
from core.config import cfg, setup_logger
from core.clob_client import polymarket
from storage.db import db

logger = setup_logger("pnl")

class PnLTracker:
    async def get_portfolio_snapshot(self) -> dict:
        positions = await db.get_open_positions()
        total_cost = 0.0; total_value = 0.0; details = []
        for pos in positions:
            token_id = pos["token_id"]; shares = pos["shares"]; cost = pos["cost_usd"]
            entry_p  = pos["entry_price"]
            current_p = polymarket.get_midpoint(token_id) if polymarket._initialized else entry_p
            cur_val = shares * (current_p or entry_p)
            unreal  = cur_val - cost; unreal_pct = (unreal/cost*100) if cost else 0
            hold_h  = (int(time.time()) - pos.get("entry_time",int(time.time()))) / 3600
            total_cost += cost; total_value += cur_val
            details.append({"question":pos.get("question","Unknown")[:50],"outcome_label":pos.get("outcome_label","YES"),
                "shares":shares,"entry_price":entry_p,"current_price":current_p or entry_p,
                "cost_usd":cost,"current_value_usd":round(cur_val,2),"unrealized_pnl":round(unreal,2),
                "unrealized_pct":round(unreal_pct,1),"hold_hours":round(hold_h,1),
                "whale_label":pos.get("whale_wallet","")[:10],"stop_loss":pos.get("stop_loss_price"),"take_profit":pos.get("take_profit_price")})
        unreal_total = total_value - total_cost
        unreal_pct   = (unreal_total/total_cost*100) if total_cost else 0
        today_stats  = await db.get_today_pnl()
        daily_real   = today_stats.get("realized_pnl",0.0)
        stats = await db.get_closed_trades_stats()
        await db.update_daily_pnl(daily_real, unreal_total, len(positions), stats.get("total",0), stats.get("wins",0), cfg.risk.get("total_capital_usd",2000))
        return {"open_positions":len(positions),"total_cost_usd":round(total_cost,2),
            "total_value_usd":round(total_value,2),"unrealized_pnl":round(unreal_total,2),
            "unrealized_pnl_pct":round(unreal_pct,1),"daily_realized_pnl":round(daily_real,2),
            "positions":sorted(details, key=lambda x:x["unrealized_pnl"], reverse=True)}

    async def get_overall_stats(self) -> dict:
        stats = await db.get_closed_trades_stats()
        hist  = await db.get_pnl_summary(30)
        return {**stats, "pnl_7d":round(sum(r.get("realized_pnl",0) for r in hist[:7]),2),
                "pnl_30d":round(sum(r.get("realized_pnl",0) for r in hist),2)}

    async def format_daily_report(self) -> str:
        snap  = await self.get_portfolio_snapshot()
        stats = await self.get_overall_stats()
        today = date.today().strftime("%A, %d %b %Y")
        r=snap["daily_realized_pnl"]; u=snap["unrealized_pnl"]; t=r+u
        re="🟢" if r>=0 else "🔴"; ue="🟢" if u>=0 else "🔴"; te="🟢" if t>=0 else "🔴"
        wr = f"{stats['win_rate']*100:.1f}%" if stats.get("win_rate") else "N/A"
        lines = [f"📊 *Daily Report — {today}*","",
            f"💰 *Today's P&L*",f"  {re} Realized:   `${r:+.2f}`",
            f"  {ue} Unrealized: `${u:+.2f}`",f"  {te} Total:      `${t:+.2f}`","",
            f"📈 *Portfolio*",f"  Open Positions: `{snap['open_positions']}`",
            f"  Deployed:       `${snap['total_cost_usd']:.2f}`",
            f"  Current Value:  `${snap['total_value_usd']:.2f}`","",
            f"🏆 *All-Time Stats*",f"  Total Trades:   `{stats.get('total',0)}`",
            f"  Win Rate:       `{wr}`",f"  Total P&L:      `${stats.get('total_pnl',0):+.2f}`",
            f"  7-Day P&L:      `${stats.get('pnl_7d',0):+.2f}`","",
            f"{'🔵 DRY RUN MODE' if cfg.dry_run else '⚡ LIVE MODE'}"]
        if snap["positions"]:
            lines += ["","📋 *Open Positions*"]
            for i, pos in enumerate(snap["positions"][:5], 1):
                em = "🟢" if pos["unrealized_pnl"]>=0 else "🔴"
                lines.append(f"  {i}. {em} `{pos['question'][:35]}`\n     {pos['outcome_label']} | ${pos['unrealized_pnl']:+.2f} ({pos['unrealized_pct']:+.1f}%)")
        return "\n".join(lines)

    async def format_position_list(self) -> str:
        snap = await self.get_portfolio_snapshot()
        if not snap["positions"]:
            return "📭 *No open positions*\n\nBot is monitoring whales..."
        lines = [f"📊 *Open Positions ({snap['open_positions']})*",
                 f"Value: `${snap['total_value_usd']:.2f}` | Unrealized: `${snap['unrealized_pnl']:+.2f}`",""]
        for i, pos in enumerate(snap["positions"], 1):
            em = "🟢" if pos["unrealized_pnl"]>=0 else "🔴"
            lines += [f"*{i}. {em} {pos['question'][:40]}*",
                f"   Outcome: `{pos['outcome_label']}` | Hold: `{pos['hold_hours']:.0f}h`",
                f"   Entry: `${pos['entry_price']:.4f}` → Now: `${pos['current_price']:.4f}`",
                f"   P&L: `${pos['unrealized_pnl']:+.2f}` ({pos['unrealized_pct']:+.1f}%)",
                f"   SL: `{pos['stop_loss']:.4f}` | TP: `{pos['take_profit']:.4f}`",""]
        return "\n".join(lines)

pnl_tracker = PnLTracker()
