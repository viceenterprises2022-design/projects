import pytest
from market_engine import MarketEngine

def test_rsi_calculation():
    me = MarketEngine()
    # Mock data: alternating gains and losses
    data = [10, 11, 10, 11, 10, 11, 10, 11, 10, 11, 10, 11, 10, 11, 10, 11]
    rsi = me.calculate_rsi(data)
    assert 0 <= rsi <= 100
    
def test_ema_calculation():
    me = MarketEngine()
    data = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    period = 3
    ema = me.calculate_ema(data, period)
    assert len(ema) == len(data) - period + 1
    # Check last value logic
    assert ema[-1] > ema[-2] # Increasing trend

def test_vwap_calculation():
    me = MarketEngine()
    # candles: [t, o, h, l, c, v]
    candles = [
        [0, 10, 12, 8, 11, 100],
        [1, 11, 13, 9, 12, 200]
    ]
    vwap = me.calculate_vwap(candles, period=2)
    # TP1 = (12+8+11)/3 = 10.33, V1=100 -> 1033.33
    # TP2 = (13+9+12)/3 = 11.33, V2=200 -> 2266.66
    # Total TV = 3300, Total V = 300 -> VWAP = 11.0
    assert vwap == pytest.approx(11.0, 0.1)

def test_supertrend_calculation():
    me = MarketEngine()
    # Minimal data for Supertrend (period 10)
    candles = [[i, 100, 110, 90, 105, 1000] for i in range(15)]
    val, direction = me.calculate_supertrend(candles, period=10, multiplier=3)
    assert direction in [1, -1]
    assert val > 0

def test_analyze_trend():
    me = MarketEngine()
    # Strong uptrend: Price > EMA20 > EMA50 > EMA200
    candles = [[i, 100, 100+i, 100-i, 200+i, 1000] for i in range(210)]
    label, score, detail = me.analyze_trend(candles)
    assert "Uptrend" in label
    assert score > 0

def test_correlation_calculation():
    me = MarketEngine()
    a = [1, 2, 3, 4, 5]
    b = [2, 4, 6, 8, 10] # Perfect positive
    c = [5, 4, 3, 2, 1] # Perfect negative
    assert me.calculate_correlation(a, b) == pytest.approx(1.0)
    assert me.calculate_correlation(a, c) == pytest.approx(-1.0)
