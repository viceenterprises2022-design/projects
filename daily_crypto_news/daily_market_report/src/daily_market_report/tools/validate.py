from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from daily_market_report.models.snapshot import QuotePayload


def _finite(x: float | None) -> bool:
    return x is not None and not math.isnan(x) and not math.isinf(x)


def validate_quote(q: QuotePayload | None, max_age_hours: int = 72) -> bool:
    if q is None or q.raw_error:
        return False
    if q.last is None or not _finite(q.last):
        return False
    if q.as_of_utc is None:
        return True
    now = datetime.now(timezone.utc)
    if q.as_of_utc.tzinfo is None:
        return True
    return now - q.as_of_utc < timedelta(hours=max_age_hours)


def relative_pct_diff(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return abs(a - b) / abs(b) * 100.0
