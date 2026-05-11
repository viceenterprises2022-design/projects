from __future__ import annotations

import time
from pathlib import Path

from btcbot.engine.broker import PaperBroker
from btcbot.core.config import BotConfig
from btcbot.api.hyperliquid import fetch_candles
from btcbot.api.notifier import SlackNotifier
from btcbot.core.storage import Store
from btcbot.strategy.strategy import generate_breakout_signal


def run_once(cfg: BotConfig, root: Path) -> str:
    store = Store(root / cfg.db_path, cfg)
    broker = PaperBroker(cfg)
    notifier = SlackNotifier(cfg.slack_webhook_url, cfg.slack_username)
    try:
        candles = fetch_candles(cfg.symbol, cfg.timeframe, lookback=250)
        store.save_candles(candles)
        if not candles:
            return "No candles fetched"

        latest = candles[-1]
        if latest.end_ms <= store.last_processed_ts():
            return f"No new closed candle. last={latest.end_ms}"

        pos = store.open_position()
        if pos:
            trade = broker.maybe_exit(pos, latest)
            if trade:
                store.close_position(trade)
                notifier.send(
                    "BTC paper exit",
                    f"{trade.side} {trade.reason} @ {trade.exit_price:.2f}\n"
                    f"PnL: ${trade.net_pnl:+.2f} | Equity: ${store.equity():.2f}",
                )
            else:
                store.update_open_position_marks(pos)

        if not store.open_position():
            if store.drawdown_pct() >= cfg.max_drawdown_pct:
                notifier.send("BTC risk block", f"Drawdown {store.drawdown_pct():.2%}; no new trades.")
            else:
                signal = generate_breakout_signal(candles, cfg)
                if signal and signal.ts_ms > store.last_processed_ts():
                    store.save_signal(signal)
                    pos = broker.enter(store.equity(), signal)
                    store.create_position(pos)
                    notifier.send(
                        "BTC paper entry",
                        f"{signal.side} @ {pos.entry_price:.2f}\n"
                        f"Size: ${pos.size_usd:.2f} | SL: {pos.stop_loss:.2f} | TP: {pos.take_profit:.2f}\n"
                        f"Reason: {signal.reason}",
                    )

        store.set_last_processed_ts(latest.end_ms)
        s = store.summary()
        return f"Processed {cfg.symbol} {cfg.timeframe}. Equity ${s['equity']}; PnL ${s['pnl']}; open={bool(s['open_position'])}"
    finally:
        store.close()


def run_loop(cfg: BotConfig, root: Path, once: bool = False) -> None:
    notifier = SlackNotifier(cfg.slack_webhook_url, cfg.slack_username)
    notifier.send("BTC bot started", f"Mode: {cfg.mode} | Symbol: {cfg.symbol} | TF: {cfg.timeframe} | Max lev: {cfg.max_leverage}x")
    while True:
        try:
            print(run_once(cfg, root))
        except Exception as exc:
            notifier.send("BTC bot error", str(exc))
            print(f"ERROR: {exc}")
        if once:
            return
        time.sleep(cfg.poll_seconds)

