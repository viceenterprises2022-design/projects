from btcbot.strategy.indicators import atr
from btcbot.core.models import Candle


def c(i, o, h, l, close):
    return Candle(i, i + 1, o, h, l, close, 1)


def test_atr_uses_true_range():
    candles = [
        c(1, 100, 110, 90, 100),
        c(2, 100, 115, 95, 110),
        c(3, 110, 112, 100, 105),
    ]
    assert atr(candles, 2) == 16.0
