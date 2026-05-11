from btcbot.engine.broker import PaperBroker
from btcbot.core.config import BotConfig
from btcbot.core.models import Candle, Signal


def test_position_size_respects_20x_cap():
    cfg = BotConfig(risk_per_trade_pct=0.02, max_leverage=20, stop_atr_mult=0.01)
    broker = PaperBroker(cfg)
    signal = Signal(1, "LONG", 100.0, 1.0, 99.0, "test")
    size_usd, _, _, _ = broker.size_position(10_000, signal)
    assert size_usd == 200_000


def test_take_profit_exit_long():
    cfg = BotConfig(fee_rate=0, slippage_rate=0)
    broker = PaperBroker(cfg)
    signal = Signal(1, "LONG", 100.0, 10.0, 99.0, "test")
    pos = broker.enter(10_000, signal)
    trade = broker.maybe_exit(pos, Candle(2, 3, 100, 131, 122, 130, 1))
    assert trade is not None
    assert trade.reason == "TAKE_PROFIT"
    assert trade.net_pnl > 0
