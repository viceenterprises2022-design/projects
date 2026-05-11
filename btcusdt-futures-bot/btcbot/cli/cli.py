from __future__ import annotations

import argparse
import json
from pathlib import Path

from btcbot.engine.backtest import run_backtest
from btcbot.engine.broker import PaperBroker
from btcbot.core.config import load_config
from btcbot.api.notifier import SlackNotifier
from btcbot.engine.runner import run_loop
from btcbot.core.storage import Store


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BTCUSDT Hyperliquid paper-trading bot")
    sub = parser.add_subparsers(dest="command", required=True)
    run_p = sub.add_parser("run")
    run_p.add_argument("--once", action="store_true")
    status_p = sub.add_parser("status")
    status_p.add_argument("--json", action="store_true")
    backtest_p = sub.add_parser("backtest")
    backtest_p.add_argument("--days", type=int, default=30)
    close_p = sub.add_parser("close")
    close_p.add_argument("--reason", default="manual")
    sub.add_parser("test-slack")
    args = parser.parse_args(argv)

    root = Path.cwd()
    cfg = load_config(root)
    if cfg.mode != "paper":
        raise SystemExit("Only MODE=paper is supported in v1. Live trading is not implemented.")

    if args.command == "run":
        run_loop(cfg, root, once=args.once)
        return 0
    if args.command == "status":
        store = Store(root / cfg.db_path, cfg)
        try:
            summary = store.summary()
            if args.json:
                print(json.dumps(summary, default=str, indent=2))
            else:
                print(f"Equity: ${summary['equity']}")
                print(f"PnL: ${summary['pnl']}")
                print(f"Drawdown: {summary['drawdown_pct']}%")
                print(f"Closed trades: {summary['closed_trades']} | Win rate: {summary['win_rate']}%")
                print(f"Open position: {summary['open_position']}")
            return 0
        finally:
            store.close()
    if args.command == "backtest":
        print(json.dumps(run_backtest(cfg, args.days), indent=2))
        return 0
    if args.command == "close":
        store = Store(root / cfg.db_path, cfg)
        try:
            pos = store.open_position()
            if not pos:
                print("No open paper position.")
                return 0
            broker = PaperBroker(cfg)
            trade = broker.exit(pos, store.last_processed_ts(), pos.entry_price, args.reason)
            store.close_position(trade)
            print(f"Closed {pos.side}. PnL ${trade.net_pnl:+.2f}")
            return 0
        finally:
            store.close()
    if args.command == "test-slack":
        ok = SlackNotifier(cfg.slack_webhook_url, cfg.slack_username).send("BTC bot test", "Slack integration OK.")
        print(f"Slack sent: {ok}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

