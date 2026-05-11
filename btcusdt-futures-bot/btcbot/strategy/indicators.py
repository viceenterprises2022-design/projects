from __future__ import annotations

from btcbot.core.models import Candle


def true_ranges(candles: list[Candle]) -> list[float]:
    ranges: list[float] = []
    prev_close: float | None = None
    for candle in candles:
        if prev_close is None:
            tr = candle.high - candle.low
        else:
            tr = max(
                candle.high - candle.low,
                abs(candle.high - prev_close),
                abs(candle.low - prev_close),
            )
        ranges.append(tr)
        prev_close = candle.close
    return ranges


def sma(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def ema(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    
    # Simple SMA seed
    current_ema = sum(values[:period]) / period
    multiplier = 2 / (period + 1)
    
    for val in values[period:]:
        current_ema = (val - current_ema) * multiplier + current_ema
        
    return current_ema


def atr(candles: list[Candle], period: int = 14) -> float | None:
    """Standard SMA-based ATR."""
    if len(candles) < period + 1:
        return None
    trs = true_ranges(candles)
    return sma(trs, period)


def wilders_atr(candles: list[Candle], period: int = 14) -> float | None:
    """Wilder's Smoothing ATR (Standard for technical analysis)."""
    if len(candles) < period + 1:
        return None
    
    trs = true_ranges(candles)
    # First ATR is SMA of TRs
    current_atr = sum(trs[:period]) / period
    
    for tr in trs[period:]:
        current_atr = (current_atr * (period - 1) + tr) / period
        
    return current_atr

