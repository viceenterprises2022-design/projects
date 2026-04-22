"""
evaluate.py — FIXED BACKTEST HARNESS. DO NOT MODIFY.
Equivalent to prepare.py in Karpathy's autoresearch.
If you modify this, you are cheating yourself (Goodhart's Law).

Output contract (grep-parseable):
  sharpe: {float}
  win_rate: {float}
  max_drawdown: {float}
  trade_count: {int}
  pnl_7d: {float}
  pnl_30d: {float}
  avg_hold_hours: {float}
  filtered_signals: {int}
  insufficient_data: true   (only if data < MIN_TRADES)

Usage:
  python evaluate.py                    # uses strategy.yaml
  python evaluate.py --config alt.yaml  # comparison run
"""
import argparse, sqlite3, yaml, sys, math
from pathlib import Path
from datetime import datetime, timezone, timedelta

# FIXED — never in strategy.yaml (protects against gaming)
EVAL_WINDOW_DAYS    = 90
OUT_OF_SAMPLE_DAYS  = 30
MIN_TRADES          = 5
DB_PATH             = "data/bot.db"

parser = argparse.ArgumentParser()
parser.add_argument("--config", default="strategy.yaml")
parser.add_argument("--window", type=int, default=EVAL_WINDOW_DAYS)
args = parser.parse_args()


def load_cfg(path):
    with open(path) as f: cfg = yaml.safe_load(f)
    if not cfg: raise ValueError(f"Empty config: {path}")
    return cfg


def load_signals(window_days):
    if not Path(DB_PATH).exists():
        print("insufficient_data: true"); print("error: no database"); sys.exit(0)
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row
    cutoff = int((datetime.now(timezone.utc) - timedelta(days=window_days)).timestamp())
    rows = conn.execute("""
        SELECT ws.token_id, ws.detected_at AS signal_time, ws.delta_shares, ws.wallet,
               p.entry_price, p.exit_price, p.cost_usd, p.entry_time, p.exit_time, p.pnl_usd,
               p.stop_loss_price, p.take_profit_price, p.status, p.shares
        FROM whale_signals ws
        LEFT JOIN positions p ON (ws.token_id = p.token_id AND ws.copied = 1)
        WHERE ws.detected_at >= ? AND ws.copied = 1
        ORDER BY ws.detected_at ASC
    """, (cutoff,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def apply_filters(signals, cfg):
    scoring = cfg.get("scoring", {})
    mf      = cfg.get("whale_filters", {})
    filtered = []
    for sig in signals:
        if not sig.get("entry_price") or sig["entry_price"] <= 0: continue
        delta = sig.get("delta_shares", 0) or 0
        conf  = min(1.0, 0.4 + (delta / 1000) * 0.3)
        if conf < scoring.get("min_confidence_to_trade", 0.40): continue
        filtered.append(sig)
    return filtered


def simulate_trade(sig, cfg):
    risk = cfg.get("risk", {}); ex = cfg.get("exit", {})
    ps   = cfg.get("position_sizing", {})
    entry_p = sig.get("entry_price")
    if not entry_p or entry_p <= 0: return None
    cost_usd = float(ps.get("fixed_amount_usd", 25.0))
    sl_price = entry_p * (1 - float(risk.get("stop_loss_pct", 0.50)))
    tp_price = min(1.0, entry_p * (1 + float(risk.get("take_profit_pct", 1.00))))
    max_hold = float(ex.get("max_hold_days", 30))
    actual_exit = sig.get("exit_price")
    entry_time  = sig.get("entry_time") or sig.get("signal_time", 0)
    exit_time   = sig.get("exit_time") or 0
    hold_days   = (exit_time - entry_time) / 86400 if exit_time > entry_time else 0
    if actual_exit and actual_exit > 0:
        if actual_exit <= sl_price:   eff = sl_price
        elif actual_exit >= tp_price: eff = tp_price
        else: eff = actual_exit
    else:
        eff = entry_p
    ret = (eff - entry_p) / entry_p
    return {"gross_return": round(ret, 6), "pnl_usd": round(ret * cost_usd, 4),
            "cost_usd": cost_usd, "entry_price": entry_p, "effective_exit": eff,
            "hold_days": round(hold_days, 2), "signal_time": sig.get("signal_time", 0),
            "hit_sl": eff == sl_price, "hit_tp": eff == tp_price}


def compute_metrics(trades, oos_cutoff_ts):
    oos = [t for t in trades if t["signal_time"] >= oos_cutoff_ts]
    if len(oos) < MIN_TRADES:
        return {"insufficient": True, "trade_count": len(oos)}
    returns = [t["gross_return"] for t in oos]; pnls = [t["pnl_usd"] for t in oos]
    n = len(returns); wins = sum(1 for r in returns if r > 0)
    mean_r = sum(returns) / n
    var    = sum((r - mean_r)**2 for r in returns) / max(n-1, 1)
    std_r  = math.sqrt(var) if var > 0 else 1e-9
    sharpe = (mean_r / std_r) * math.sqrt(252)
    cum = 1.0; peak = 1.0; max_dd = 0.0
    for r in returns:
        cum *= (1 + r); peak = max(peak, cum)
        max_dd = max(max_dd, (peak - cum) / peak)
    now = int(datetime.now(timezone.utc).timestamp())
    pnl_7d  = sum(t["pnl_usd"] for t in oos if t["signal_time"] >= now - 7*86400)
    pnl_30d = sum(t["pnl_usd"] for t in oos if t["signal_time"] >= now - 30*86400)
    avg_hold = sum(t["hold_days"]*24 for t in oos) / n
    return {"insufficient": False, "sharpe": round(sharpe,4), "win_rate": round(wins/n,4),
            "max_drawdown": round(max_dd,4), "trade_count": n, "total_pnl": round(sum(pnls),2),
            "mean_return": round(mean_r,6), "pnl_7d": round(pnl_7d,2), "pnl_30d": round(pnl_30d,2),
            "avg_hold_hours": round(avg_hold,1), "sl_hits": sum(1 for t in oos if t["hit_sl"]),
            "tp_hits": sum(1 for t in oos if t["hit_tp"])}


def main():
    cfg = load_cfg(args.config)
    window = args.window
    now_ts = int(datetime.now(timezone.utc).timestamp())
    oos_cutoff_ts = now_ts - (OUT_OF_SAMPLE_DAYS * 86400)
    all_signals = load_signals(window)
    if not all_signals:
        print("insufficient_data: true"); print("trade_count: 0"); sys.exit(0)
    filtered  = apply_filters(all_signals, cfg)
    trades    = [t for t in (simulate_trade(s, cfg) for s in filtered) if t]
    metrics   = compute_metrics(trades, oos_cutoff_ts)
    if metrics.get("insufficient"):
        print("insufficient_data: true")
        print(f"trade_count: {metrics['trade_count']}")
        print(f"filtered_signals: {len(filtered)}")
        sys.exit(0)
    print("---")
    print(f"sharpe: {metrics['sharpe']}")
    print(f"win_rate: {metrics['win_rate']}")
    print(f"max_drawdown: {metrics['max_drawdown']}")
    print(f"trade_count: {metrics['trade_count']}")
    print(f"pnl_7d: {metrics['pnl_7d']}")
    print(f"pnl_30d: {metrics['pnl_30d']}")
    print(f"avg_hold_hours: {metrics['avg_hold_hours']}")
    print(f"mean_return: {metrics['mean_return']}")
    print(f"total_pnl: {metrics['total_pnl']}")
    print(f"filtered_signals: {len(filtered)}")
    print(f"sl_hits: {metrics['sl_hits']}")
    print(f"tp_hits: {metrics['tp_hits']}")
    print("---")

if __name__ == "__main__":
    main()
