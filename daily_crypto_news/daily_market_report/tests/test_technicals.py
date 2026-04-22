import pandas as pd

from daily_market_report.tools.technicals import build_technicals_from_yahoo_df


def test_pivot_above_flag():
    idx = pd.date_range("2026-01-01", periods=3, freq="D")
    df = pd.DataFrame(
        {
            "Open": [100, 100, 100],
            "High": [110, 110, 110],
            "Low": [90, 90, 90],
            "Close": [105, 106, 120],
        },
        index=idx,
    )
    tech = build_technicals_from_yahoo_df(df, current_last=120.0)
    assert tech.levels.pivot is not None
    assert tech.levels.above_pivot is True
