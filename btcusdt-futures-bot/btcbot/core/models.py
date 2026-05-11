from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Side = Literal["LONG", "SHORT"]


@dataclass(frozen=True)
class Candle:
    start_ms: int
    end_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Signal:
    ts_ms: int
    side: Side
    price: float
    atr: float
    breakout_level: float
    reason: str


@dataclass
class Position:
    side: Side
    entry_ts_ms: int
    entry_price: float
    size_usd: float
    size_units: float
    stop_loss: float
    take_profit: float
    atr: float
    highest_price: float
    lowest_price: float


@dataclass(frozen=True)
class Trade:
    side: Side
    entry_ts_ms: int
    exit_ts_ms: int
    entry_price: float
    exit_price: float
    size_usd: float
    size_units: float
    gross_pnl: float
    fees: float
    slippage: float
    net_pnl: float
    reason: str

