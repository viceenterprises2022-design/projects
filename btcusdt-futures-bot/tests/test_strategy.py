from btcbot.core.config import BotConfig
from btcbot.core.models import Candle
from btcbot.strategy.strategy import generate_breakout_signal


def candle(i, close, volume=100, high=None, low=None):
    h = high if high is not None else close + 1
    l = low if low is not None else close - 1
    return Candle(i * 1000, i * 1000 + 999, close - 0.5, h, l, close, volume)


def test_long_breakout_signal():
    # Small periods for testing
    cfg = BotConfig(lookback_candles=3, atr_period=3, trend_ema_period=3, volume_lookback=3)
    
    # 5 candles. 
    # Prior 3 for breakout: 100, 101, 102. High=103.
    # EMA 3 will be around 101.
    # Vols: 100, 100, 100, 100. Latest vol 200 > median 100.
    candles = [
        candle(1, 100), 
        candle(2, 101), 
        candle(3, 102), 
        candle(4, 103), 
        candle(5, 106, volume=200, high=106.1, low=105.0) # Close 106 is top 25% of [105, 106.1]
    ]
    signal = generate_breakout_signal(candles, cfg)
    assert signal is not None
    assert signal.side == "LONG"


def test_no_signal_inside_range():
    cfg = BotConfig(lookback_candles=3, atr_period=3, trend_ema_period=3, volume_lookback=3)
    candles = [
        candle(1, 100), 
        candle(2, 101), 
        candle(3, 102), 
        candle(4, 103), 
        candle(5, 102, volume=200)
    ]
    assert generate_breakout_signal(candles, cfg) is None


def test_trend_filter_prevents_signal():
    cfg = BotConfig(lookback_candles=3, atr_period=3, trend_ema_period=3, volume_lookback=3)
    # Price breaks high but is BELOW EMA
    # EMA 3 of [110, 105, 102, 101] will be > 103
    candles = [
        candle(1, 110),
        candle(2, 105),
        candle(3, 102),
        candle(4, 101),
        candle(5, 103, volume=200, high=103.1, low=102.0)
    ]
    assert generate_breakout_signal(candles, cfg) is None

