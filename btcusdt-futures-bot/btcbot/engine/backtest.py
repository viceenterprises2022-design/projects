from __future__ import annotations

from btcbot.engine.broker import PaperBroker
from btcbot.core.config import BotConfig
from btcbot.api.hyperliquid import fetch_candles
from btcbot.core.models import Position, Trade
from btcbot.strategy.strategy import generate_breakout_signal


def run_backtest(cfg: BotConfig, days: int = 30) -> dict:
    lookback = max(250, days * 24 * 4)
    candles = fetch_candles(cfg.symbol, cfg.timeframe, lookback=lookback)
    broker = PaperBroker(cfg)
    equity = cfg.paper_equity_usd
    peak = equity
    max_drawdown = 0.0
    pos: Position | None = None
    trades: list[Trade] = []

    warmup = max(cfg.lookback_candles + 1, cfg.atr_period + 1)
    for idx in range(warmup, len(candles)):
        window = candles[: idx + 1]
        candle = candles[idx]
        if pos:
            trade = broker.maybe_exit(pos, candle)
            if trade:
                trades.append(trade)
                equity += trade.net_pnl
                peak = max(peak, equity)
                if peak > 0:
                    max_drawdown = max(max_drawdown, (peak - equity) / peak)
                pos = None
        if pos is None:
            signal = generate_breakout_signal(window, cfg)
            if signal:
                pos = broker.enter(equity, signal)

    total_pnl = equity - cfg.paper_equity_usd
    wins = [t for t in trades if t.net_pnl >= 0]
    return {
        "candles": len(candles),
        "trades": len(trades),
        "wins": len(wins),
        "win_rate": round((len(wins) / len(trades) * 100) if trades else 0, 2),
        "equity": round(equity, 2),
        "pnl": round(total_pnl, 2),
        "max_drawdown_pct": round(max_drawdown * 100, 2),
        "open_position": pos is not None,
    }
