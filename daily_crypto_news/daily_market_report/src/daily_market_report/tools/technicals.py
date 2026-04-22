from __future__ import annotations

import math

from daily_market_report.models.snapshot import PivotLevels, TechnicalSnapshot


def pivots_from_prior_ohlc(high: float, low: float, close: float) -> PivotLevels:
    p = (high + low + close) / 3.0
    r1 = 2 * p - low
    s1 = 2 * p - high
    r2 = p + (high - low)
    s2 = p - (high - low)
    return PivotLevels(pivot=p, s1=s1, s2=s2, r1=r1, r2=r2)


def build_technicals_from_yahoo_df(df, current_last: float | None) -> TechnicalSnapshot:
    out = TechnicalSnapshot()
    if df is None or len(df) < 2:
        out.levels.unavailable_reason = "insufficient_yahoo_history"
        return out
    try:
        prior = df.iloc[-2]
        h, l, c = float(prior["High"]), float(prior["Low"]), float(prior["Close"])
        if not all(math.isfinite(v) for v in (h, l, c)):
            out.levels.unavailable_reason = "non_finite_prior_bar"
            return out
        levels = pivots_from_prior_ohlc(h, l, c)
        if current_last is not None and levels.pivot is not None:
            levels.above_pivot = current_last >= levels.pivot
        out.levels = levels
        out.sparkline_series = [float(x) for x in df["Close"].dropna().tail(6).tolist()]
    except Exception as ex:  # noqa: BLE001
        out.levels.unavailable_reason = str(ex)
    return out
