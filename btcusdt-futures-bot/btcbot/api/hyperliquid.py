from __future__ import annotations

import json
import time
import urllib.request
from typing import Any

from btcbot.core.models import Candle


HL_INFO_URL = "https://api.hyperliquid.xyz/info"


def _post_json(url: str, payload: dict[str, Any], timeout: float = 20.0) -> Any:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "btcusdt-futures-bot/0.1"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def normalize_candle(row: dict[str, Any]) -> Candle:
    return Candle(
        start_ms=int(row.get("t", 0)),
        end_ms=int(row.get("T", 0)),
        open=float(row["o"]),
        high=float(row["h"]),
        low=float(row["l"]),
        close=float(row["c"]),
        volume=float(row.get("v", 0)),
    )


def fetch_candles(symbol: str = "BTC", interval: str = "15m", lookback: int = 200) -> list[Candle]:
    end_ms = int(time.time() * 1000)
    interval_ms = interval_to_ms(interval)
    start_ms = end_ms - (lookback + 5) * interval_ms
    payload = {
        "type": "candleSnapshot",
        "req": {
            "coin": symbol,
            "interval": interval,
            "startTime": start_ms,
            "endTime": end_ms,
        },
    }
    raw = _post_json(HL_INFO_URL, payload)
    if not isinstance(raw, list):
        raise RuntimeError(f"Unexpected Hyperliquid candle response: {raw}")
    candles = sorted((normalize_candle(r) for r in raw), key=lambda c: c.start_ms)
    # Use closed candles only; leave a small clock-skew buffer.
    cutoff = end_ms - 10_000
    return [c for c in candles if c.end_ms <= cutoff][-lookback:]


def interval_to_ms(interval: str) -> int:
    table = {
        "1m": 60_000,
        "5m": 5 * 60_000,
        "15m": 15 * 60_000,
        "1h": 60 * 60_000,
        "4h": 4 * 60 * 60_000,
        "1d": 24 * 60 * 60_000,
    }
    if interval not in table:
        raise ValueError(f"Unsupported interval: {interval}")
    return table[interval]

