"""
whale/scorer.py — Vet a wallet before tracking it.
Usage: python -m whale.scorer 0xWALLET_ADDRESS
"""
import asyncio, sys, requests
from core.config import cfg, setup_logger
from core.subgraph_client import subgraph

logger = setup_logger("scorer")

async def score_wallet(address: str) -> dict:
    logger.info("Scoring wallet: %s", address)
    positions = await subgraph.get_wallet_positions(address)
    stats     = await subgraph.get_wallet_stats(address)
    lb_data   = _fetch_leaderboard(address)
    score = 0; breakdown = {}; reasons = []
    total_pnl = lb_data.get("profit", 0) or 0
    pnl_min   = cfg.whale_filters.get("min_total_pnl_usd", 5000)
    pnl_score = min(30, int((total_pnl / pnl_min) * 30)) if total_pnl > 0 else 0
    score += pnl_score; breakdown["pnl"] = {"score": pnl_score, "value": f"${total_pnl:,.0f}"}
    if total_pnl < pnl_min: reasons.append(f"Low P&L: ${total_pnl:,.0f} < ${pnl_min:,.0f}")
    win_rate = lb_data.get("winRate", 0) or 0
    min_wr   = cfg.whale_filters.get("min_win_rate", 0.55)
    wr_score = min(25, int((win_rate / min_wr) * 25)) if win_rate > 0 else 0
    score += wr_score; breakdown["win_rate"] = {"score": wr_score, "value": f"{win_rate*100:.1f}%"}
    if win_rate < min_wr: reasons.append(f"Low win rate: {win_rate*100:.1f}% < {min_wr*100:.0f}%")
    trades     = lb_data.get("positionsCount", 0) or stats.get("total_trades", 0)
    min_trades = cfg.whale_filters.get("min_total_trades", 30)
    tc_score   = min(20, int((trades / min_trades) * 20)) if trades > 0 else 0
    score += tc_score; breakdown["trade_count"] = {"score": tc_score, "value": str(trades)}
    if trades < min_trades: reasons.append(f"Too few trades: {trades} < {min_trades}")
    n_markets = len(positions); ds = min(15, n_markets*3)
    score += ds; breakdown["diversity"] = {"score": ds, "value": f"{n_markets} markets"}
    if positions:
        total_b = sum(p["balance"] for p in positions)
        max_b   = max(p["balance"] for p in positions) if positions else 0
        conc    = max_b / total_b if total_b > 0 else 1.0
        max_c   = cfg.whale_filters.get("max_single_market_concentration", 0.80)
        cs = 10 if conc <= max_c else 0; score += cs
        breakdown["concentration"] = {"score": cs, "value": f"{conc*100:.0f}%"}
        if conc > max_c: reasons.append(f"High concentration: {conc*100:.0f}%")
    score = min(100, score)
    if score >= 70: rec = "✅ STRONG — Highly recommended"
    elif score >= 50: rec = "⚠️  MODERATE — Track with smaller sizes"
    elif score >= 30: rec = "❌ WEAK — Not recommended"
    else: rec = "🚫 AVOID"
    return {"address": address, "score": score, "recommendation": rec,
            "breakdown": breakdown, "reasons": reasons,
            "raw": {"total_pnl": total_pnl, "win_rate": win_rate, "trades": trades, "positions": len(positions)}}

def _fetch_leaderboard(address: str) -> dict:
    try:
        r = requests.get(f"https://data-api.polymarket.com/profile/{address.lower()}", timeout=10)
        if r.status_code == 200: return r.json()
    except Exception: pass
    return {}

def print_score_report(result: dict):
    print("\n" + "="*60)
    print(f"  WHALE WALLET SCORE REPORT")
    print(f"  {result['address']}")
    print("="*60)
    print(f"\n  SCORE: {result['score']}/100")
    print(f"  {result['recommendation']}")
    print("\n  Breakdown:")
    for cat, data in result["breakdown"].items():
        bar = "█" * min(data["score"], 30)
        print(f"    {cat:<20} {data['score']:3d}pts  [{bar:<15}]  {data['value']}")
    raw = result["raw"]
    print(f"\n  Stats: P&L=${raw['total_pnl']:,.0f} | WR={raw['win_rate']*100:.1f}% | Trades={raw['trades']} | Positions={raw['positions']}")
    if result["reasons"]:
        print("\n  Issues:")
        for r in result["reasons"]: print(f"    - {r}")
    if result["score"] >= 50:
        print(f"\n  Add to config.yaml whale_wallets:")
        print(f'    - address: "{result["address"]}"')
        print(f'      label: "Score{result["score"]}"')
    print("="*60 + "\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m whale.scorer 0xWALLET_ADDRESS"); sys.exit(1)
    result = asyncio.run(score_wallet(sys.argv[1]))
    print_score_report(result)
