import random
import datetime

def fetch_all_factors(use_mock=True):
    """
    Fetches the 13 minimal factors required for the AlphaEdge Crypto Signal Engine.
    If API keys are missing or use_mock is True, returns mocked data.
    """
    if use_mock:
        return fetch_mock_data()
    
    # In a real implementation, you would call various APIs here using config.API_KEYS
    # such as FRED, Alpha Vantage, CoinGlass, Glassnode, DefiLlama, etc.
    # Since this is an MVP without explicit keys, we fallback to mock data.
    return fetch_mock_data()

def fetch_mock_data():
    """
    Returns realistic mocked data for the 13 core features and some contextual data.
    We randomize slightly to simulate live changes.
    """
    today = datetime.date.today()
    
    return {
        # Macro (Layer 1)
        "dxy_1d_pct_change": random.uniform(-0.8, 0.8),
        "vix_level": random.uniform(12.0, 35.0),
        "us10y_real": random.uniform(-0.5, 2.5),
        "ndx_1d_pct_change": random.uniform(-2.0, 2.5),
        "global_m2_13w_change": random.uniform(-1.0, 4.0),
        "fed_cut_probability_1m": random.uniform(20.0, 80.0),
        
        # On-chain (Layer 2)
        "btc_etf_net_flow_7d": random.uniform(-500_000_000, 1_000_000_000),  # in USD
        "stablecoin_total_7d_change": random.uniform(-2_000_000_000, 3_000_000_000), # in USD
        "mvrv_z_score": random.uniform(-1.0, 7.5),
        "btc_exchange_netflow": random.uniform(-10000, 10000), # Positive means inflows (bearish)
        "whale_wallet_change_7d": random.uniform(-5, 5), # % change
        "btc_dominance_trend": random.uniform(-1.0, 1.0), # Change in dominance
        "halving_cycle_day": (today - datetime.date(2024, 4, 20)).days,
        
        # Intraday (Layer 3)
        "perp_funding_rate": random.uniform(-0.08, 0.15),
        "oi_change": random.uniform(-5.0, 5.0), # % change
        "price_change": random.uniform(-3.0, 3.0), # % change
        "liq_imbalance": random.uniform(-50_000_000, 50_000_000), # Positive = short liquidations (bullish), Negative = long liqs (bearish)
        "deribit_25d_skew": random.uniform(-10.0, 10.0), # Negative = put premium
        
        # Additional context for display
        "dxy_value": 104.50 + random.uniform(-1, 1),
        "btc_price": 65000 + random.uniform(-2000, 2000),
        "stablecoin_supply_total": 160_000_000_000 + random.uniform(-1_000_000_000, 1_000_000_000),
    }

def get_event_flags():
    """
    Mock events for the regulatory/event layer.
    """
    return [
        {
            "timestamp": datetime.date.today() - datetime.timedelta(days=2),
            "type": "cpi_print",
            "entity": "US BLS",
            "impact_score": 1, # Slightly positive CPI surprise
            "impact_duration_days": 5,
            "decay_function": "linear",
            "notes": "CPI cooled slightly, dovish signal"
        }
    ]
