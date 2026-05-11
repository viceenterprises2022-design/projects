from __future__ import annotations

from btcbot.core.config import BotConfig
from btcbot.strategy.indicators import ema, wilders_atr, sma
from btcbot.core.models import Candle, Signal


def generate_breakout_signal(candles: list[Candle], cfg: BotConfig) -> Signal | None:
    needed = max(
        cfg.lookback_candles + 1,
        cfg.atr_period + 1,
        cfg.trend_ema_period + 1,
        cfg.volume_lookback + 1
    )
    if len(candles) < needed:
        return None

    latest = candles[-1]
    prior = candles[-(cfg.lookback_candles + 1) : -1]
    
    # 1. Trend Filter (EMA 200)
    closes = [c.close for c in candles[:-1]]
    current_ema = ema(closes, cfg.trend_ema_period)
    if current_ema is None:
        return None
        
    # 2. Volume Filter (Volume > Median of last 20)
    vols = [c.volume for c in candles[-(cfg.volume_lookback + 1):-1]]
    median_vol = sorted(vols)[len(vols) // 2]
    if latest.volume <= median_vol:
        return None

    # 3. Volatility (Wilder's ATR)
    current_atr = wilders_atr(candles[:-1], cfg.atr_period)
    if current_atr is None or current_atr <= 0:
        return None

    # 4. Breakout Levels
    high_breakout = max(c.high for c in prior)
    low_breakout = min(c.low for c in prior)

    # 5. Strong Close Filter
    candle_range = latest.high - latest.low
    if candle_range <= 0:
        return None
    
    relative_close = (latest.close - latest.low) / candle_range

    if latest.close > high_breakout and latest.close > current_ema:
        if relative_close > 0.75: # Close in top 25%
            return Signal(
                ts_ms=latest.end_ms,
                side="LONG",
                price=latest.close,
                atr=current_atr,
                breakout_level=high_breakout,
                reason=f"Breakout + Trend (>{current_ema:.2f}) + Vol + Strong Close",
            )
            
    if latest.close < low_breakout and latest.close < current_ema:
        if relative_close < 0.25: # Close in bottom 25%
            return Signal(
                ts_ms=latest.end_ms,
                side="SHORT",
                price=latest.close,
                atr=current_atr,
                breakout_level=low_breakout,
                reason=f"Breakout + Trend (<{current_ema:.2f}) + Vol + Strong Close",
            )
            
    return None

