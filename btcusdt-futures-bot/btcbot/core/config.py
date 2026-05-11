from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def _parse_scalar(value: str) -> Any:
    text = value.strip().strip("\"'")
    if text.lower() in ("true", "false"):
        return text.lower() == "true"
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return text


def load_simple_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    out: dict[str, Any] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        out[key.strip()] = _parse_scalar(value)
    return out


@dataclass(frozen=True)
class BotConfig:
    symbol: str = "BTC"
    timeframe: str = "15m"
    mode: str = "paper"
    paper_equity_usd: float = 10_000.0
    risk_per_trade_pct: float = 0.02
    max_leverage: float = 20.0
    lookback_candles: int = 20
    atr_period: int = 14
    trend_ema_period: int = 200
    volume_lookback: int = 20
    stop_atr_mult: float = 1.5
    take_profit_atr_mult: float = 3.0
    trail_after_r: float = 1.0
    trail_atr_mult: float = 1.0
    fee_rate: float = 0.0004
    slippage_rate: float = 0.0002
    max_drawdown_pct: float = 0.10
    poll_seconds: int = 60
    db_path: str = "data/bot.sqlite"
    slack_webhook_url: str = ""
    slack_username: str = "AlphaEdge BTC Bot"


def load_config(base_dir: Path | None = None) -> BotConfig:
    root = base_dir or Path.cwd()
    load_dotenv(root / ".env")
    yaml_cfg = load_simple_yaml(root / "config.yaml")

    def val(name: str, env_name: str, default: Any) -> Any:
        if env_name in os.environ:
            return _parse_scalar(os.environ[env_name])
        return yaml_cfg.get(name, default)

    return BotConfig(
        symbol=str(val("symbol", "SYMBOL", "BTC")),
        timeframe=str(val("timeframe", "TIMEFRAME", "15m")),
        mode=str(val("mode", "MODE", "paper")),
        paper_equity_usd=float(val("paper_equity_usd", "PAPER_EQUITY_USD", 10_000.0)),
        risk_per_trade_pct=float(val("risk_per_trade_pct", "RISK_PER_TRADE_PCT", 0.02)),
        max_leverage=float(val("max_leverage", "MAX_LEVERAGE", 20.0)),
        lookback_candles=int(val("lookback_candles", "LOOKBACK_CANDLES", 20)),
        atr_period=int(val("atr_period", "ATR_PERIOD", 14)),
        trend_ema_period=int(val("trend_ema_period", "TREND_EMA_PERIOD", 200)),
        volume_lookback=int(val("volume_lookback", "VOLUME_LOOKBACK", 20)),
        stop_atr_mult=float(val("stop_atr_mult", "STOP_ATR_MULT", 1.5)),
        take_profit_atr_mult=float(val("take_profit_atr_mult", "TAKE_PROFIT_ATR_MULT", 3.0)),
        trail_after_r=float(val("trail_after_r", "TRAIL_AFTER_R", 1.0)),
        trail_atr_mult=float(val("trail_atr_mult", "TRAIL_ATR_MULT", 1.0)),
        fee_rate=float(val("fee_rate", "FEE_RATE", 0.0004)),
        slippage_rate=float(val("slippage_rate", "SLIPPAGE_RATE", 0.0002)),
        max_drawdown_pct=float(val("max_drawdown_pct", "MAX_DRAWDOWN_PCT", 0.10)),
        poll_seconds=int(val("poll_seconds", "POLL_SECONDS", 60)),
        db_path=str(val("db_path", "DB_PATH", "data/bot.sqlite")),
        slack_webhook_url=str(val("slack_webhook_url", "SLACK_WEBHOOK_URL", "")),
        slack_username=str(val("slack_username", "SLACK_USERNAME", "AlphaEdge BTC Bot")),
    )

