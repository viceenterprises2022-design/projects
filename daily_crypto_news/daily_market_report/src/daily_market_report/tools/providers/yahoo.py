from __future__ import annotations

import math
from datetime import datetime, timezone

import yfinance as yf

from daily_market_report.models.snapshot import QuotePayload


def _finite(x: float | None) -> bool:
    return x is not None and not math.isnan(x) and not math.isinf(x)


def fetch_yahoo(symbol: str) -> tuple[QuotePayload, list[float]]:
    """Return quote payload and daily close series (up to ~6 points) for sparkline."""
    q = QuotePayload(source="yahoo", session_label="Yahoo Finance")
    series: list[float] = []
    try:
        t = yf.Ticker(symbol)
        df = t.history(period="8d", interval="1d", auto_adjust=True)
        if df is None or df.empty:
            q.raw_error = "empty_history"
            return q, series

        series = [float(x) for x in df["Close"].dropna().tail(6).tolist()]
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2] if len(df) > 1 else None

        last = float(last_row["Close"])
        open_ = float(last_row["Open"])
        high = float(last_row["High"])
        low = float(last_row["Low"])
        prev_close = float(prev_row["Close"]) if prev_row is not None else open_

        q.last = last
        q.open_ = open_
        q.high = high
        q.low = low
        q.prev_close = prev_close
        if prev_close and _finite(prev_close) and prev_close != 0:
            q.change_pct = (last - prev_close) / prev_close * 100.0
            q.change_abs = last - prev_close
        ts = last_row.name.to_pydatetime() if hasattr(last_row.name, "to_pydatetime") else datetime.utcnow()
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        q.as_of_utc = ts.astimezone(timezone.utc)

        if not all(_finite(v) for v in (last, open_, high, low, prev_close)):
            q.raw_error = "non_finite_values"
    except Exception as ex:  # noqa: BLE001
        q.raw_error = str(ex)
    return q, series


def yahoo_history_for_pivots(symbol: str):
    """OHLC dataframe for pivot calc; None on failure."""
    try:
        t = yf.Ticker(symbol)
        df = t.history(period="10d", interval="1d", auto_adjust=True)
        if df is None or df.empty:
            return None
        return df
    except Exception:  # noqa: BLE001
        return None
