from __future__ import annotations

from btcbot.core.config import BotConfig
from btcbot.core.models import Candle, Position, Signal, Trade


class PaperBroker:
    def __init__(self, cfg: BotConfig):
        self.cfg = cfg

    def size_position(self, equity: float, signal: Signal) -> tuple[float, float, float, float]:
        if signal.side == "LONG":
            stop = signal.price - self.cfg.stop_atr_mult * signal.atr
            take = signal.price + self.cfg.take_profit_atr_mult * signal.atr
        else:
            stop = signal.price + self.cfg.stop_atr_mult * signal.atr
            take = signal.price - self.cfg.take_profit_atr_mult * signal.atr

        risk_dollars = equity * self.cfg.risk_per_trade_pct
        stop_distance_pct = abs(signal.price - stop) / signal.price
        if stop_distance_pct <= 0:
            raise ValueError("Stop distance is zero")
        risk_sized_notional = risk_dollars / stop_distance_pct
        leverage_cap_notional = equity * self.cfg.max_leverage
        size_usd = min(risk_sized_notional, leverage_cap_notional)
        size_units = size_usd / signal.price
        return size_usd, size_units, stop, take

    def enter(self, equity: float, signal: Signal) -> Position:
        size_usd, size_units, stop, take = self.size_position(equity, signal)
        fill_price = self._entry_fill(signal.price, signal.side)
        return Position(
            side=signal.side,
            entry_ts_ms=signal.ts_ms,
            entry_price=fill_price,
            size_usd=size_usd,
            size_units=size_units,
            stop_loss=stop,
            take_profit=take,
            atr=signal.atr,
            highest_price=fill_price,
            lowest_price=fill_price,
        )

    def maybe_exit(self, pos: Position, candle: Candle) -> Trade | None:
        if pos.side == "LONG":
            pos.highest_price = max(pos.highest_price, candle.high)
            if pos.highest_price >= pos.entry_price + self.cfg.trail_after_r * abs(pos.entry_price - pos.stop_loss):
                pos.stop_loss = max(pos.stop_loss, pos.highest_price - self.cfg.trail_atr_mult * pos.atr)
            if candle.low <= pos.stop_loss:
                return self.exit(pos, candle.end_ms, pos.stop_loss, "STOP_LOSS")
            if candle.high >= pos.take_profit:
                return self.exit(pos, candle.end_ms, pos.take_profit, "TAKE_PROFIT")
        else:
            pos.lowest_price = min(pos.lowest_price, candle.low)
            if pos.lowest_price <= pos.entry_price - self.cfg.trail_after_r * abs(pos.entry_price - pos.stop_loss):
                pos.stop_loss = min(pos.stop_loss, pos.lowest_price + self.cfg.trail_atr_mult * pos.atr)
            if candle.high >= pos.stop_loss:
                return self.exit(pos, candle.end_ms, pos.stop_loss, "STOP_LOSS")
            if candle.low <= pos.take_profit:
                return self.exit(pos, candle.end_ms, pos.take_profit, "TAKE_PROFIT")
        return None

    def exit(self, pos: Position, ts_ms: int, price: float, reason: str) -> Trade:
        fill_price = self._exit_fill(price, pos.side)
        if pos.side == "LONG":
            gross = (fill_price - pos.entry_price) * pos.size_units
        else:
            gross = (pos.entry_price - fill_price) * pos.size_units
        fees = (pos.entry_price * pos.size_units + fill_price * pos.size_units) * self.cfg.fee_rate
        slippage = (pos.entry_price * pos.size_units + fill_price * pos.size_units) * self.cfg.slippage_rate
        net = gross - fees - slippage
        return Trade(
            side=pos.side,
            entry_ts_ms=pos.entry_ts_ms,
            exit_ts_ms=ts_ms,
            entry_price=pos.entry_price,
            exit_price=fill_price,
            size_usd=pos.size_usd,
            size_units=pos.size_units,
            gross_pnl=gross,
            fees=fees,
            slippage=slippage,
            net_pnl=net,
            reason=reason,
        )

    def _entry_fill(self, price: float, side: str) -> float:
        return price * (1 + self.cfg.slippage_rate) if side == "LONG" else price * (1 - self.cfg.slippage_rate)

    def _exit_fill(self, price: float, side: str) -> float:
        return price * (1 - self.cfg.slippage_rate) if side == "LONG" else price * (1 + self.cfg.slippage_rate)

