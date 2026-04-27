import random
import datetime
import asyncio
import aiohttp
import pandas as pd
import numpy as np

async def fetch_factor_mock_history(factor_name, days=90, base=0, drift=0, vol=1):
    """
    Simulates an async API call returning a 90-day historical time series for a single factor.
    """
    # Simulate network delay
    await asyncio.sleep(random.uniform(0.1, 0.3))
    
    dates = pd.date_range(end=datetime.date.today(), periods=days)
    
    # Generate random walk with drift
    steps = np.random.normal(loc=drift, scale=vol, size=days)
    values = base + np.cumsum(steps)
    
    return pd.Series(values, index=dates, name=factor_name)

async def fetch_all_factors(use_mock=True):
    """
    Fetches the 13 minimal factors concurrently using asyncio.
    Returns a Pandas DataFrame with 90 days of history for proper Z-Score normalization.
    """
    if not use_mock:
        # In a real implementation:
        # async with aiohttp.ClientSession() as session:
        #     task1 = fetch_fred(session, "DGS10")
        #     task2 = fetch_coinglass(session, "funding")
        #     ...
        #     results = await asyncio.gather(task1, task2, ...)
        pass
        
    # Mock data generation concurrently
    tasks = [
        fetch_factor_mock_history("dxy_1d_pct_change", base=0, vol=0.5),
        fetch_factor_mock_history("vix_level", base=18.0, drift=0, vol=1.5),
        fetch_factor_mock_history("us10y_real", base=1.5, vol=0.1),
        fetch_factor_mock_history("ndx_1d_pct_change", base=0, vol=1.0),
        fetch_factor_mock_history("global_m2_13w_change", base=1.0, vol=0.2),
        fetch_factor_mock_history("fed_cut_probability_1m", base=50.0, vol=5.0),
        
        fetch_factor_mock_history("btc_etf_net_flow_7d", base=100_000_000, vol=100_000_000),
        fetch_factor_mock_history("stablecoin_total_7d_change", base=500_000_000, vol=200_000_000),
        fetch_factor_mock_history("mvrv_z_score", base=1.5, vol=0.1),
        fetch_factor_mock_history("btc_exchange_netflow", base=0, vol=2000),
        fetch_factor_mock_history("whale_wallet_change_7d", base=0, vol=1.0),
        fetch_factor_mock_history("btc_dominance_trend", base=50.0, vol=0.2),
        fetch_factor_mock_history("halving_cycle_day", base=(datetime.date.today() - datetime.date(2024, 4, 20)).days - 90, drift=1, vol=0),
        
        fetch_factor_mock_history("perp_funding_rate", base=0.01, vol=0.02),
        fetch_factor_mock_history("oi_change", base=0, vol=2.0),
        fetch_factor_mock_history("price_change", base=0, vol=2.0),
        fetch_factor_mock_history("liq_imbalance", base=0, vol=10_000_000),
        fetch_factor_mock_history("deribit_25d_skew", base=0, vol=3.0),
        
        # Context Display
        fetch_factor_mock_history("dxy_value", base=104.5, vol=0.2),
        fetch_factor_mock_history("btc_price", base=65000, drift=50, vol=1000),
        fetch_factor_mock_history("stablecoin_supply_total", base=160_000_000_000, drift=100_000_000, vol=50_000_000),
        fetch_factor_mock_history("btc_call_oi_total", base=50000, vol=1000),
        fetch_factor_mock_history("btc_put_oi_total", base=45000, vol=1000),
    ]
    
    series_list = await asyncio.gather(*tasks)
    
    # Combine all series into a single DataFrame
    df = pd.concat(series_list, axis=1)
    return df

def get_event_flags():
    """
    Mock events for the regulatory/event layer.
    """
    return [
        {
            "timestamp": datetime.date.today() - datetime.timedelta(days=2),
            "type": "cpi_print",
            "entity": "US BLS",
            "impact_score": 1,
            "impact_duration_days": 5,
            "decay_function": "linear",
            "notes": "CPI cooled slightly, dovish signal"
        }
    ]
