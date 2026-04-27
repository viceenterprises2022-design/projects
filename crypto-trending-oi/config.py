import os
from dotenv import load_dotenv

load_dotenv()

# Master feature list
MINIMAL_FEATURE_SET = [
    "dxy",              # USD strength
    "vix",              # Fear gauge
    "ndx",              # Equity risk appetite proxy
    "us10y_real",       # Opportunity cost
    "fed_cut_prob",     # Policy path probability
    "global_m2_13w",    # Global liquidity
    "btc_etf_flows_7d", # Institutional demand
    "stablecoin_total", # Deployable crypto liquidity
    "btc_mvrv",         # Cycle position / valuation
    "btc_oi",           # Open interest
    "btc_funding",      # Leverage crowding
    "btc_liquidations", # Amplification signal
    "btc_iv",           # Implied vol
]

# Internal alias map
SYMBOL_MAP = {
    "dxy":                ("DXY",           "DX-Y.NYB",      "ICE USDX"),
    "vix":                ("^VIX",          "VIX",           "I:VIX"),
    "ndx":                ("NDX",           "QQQ",           "^NDX"),
    "us10y_real":         ("DFII10",        "TIPS10",        None),
    "fed_cut_prob":       ("FEDFUNDS",      None,            None),
    "global_m2":          ("M2SL",          None,            None),
    "btc_etf_flows":      ("IBIT",          "FBTC",          "provider-specific"),
    "stablecoin_total":   ("USDT+USDC+all", "provider-specific", None),
    "btc_mvrv":           ("BTC",           "provider-specific", None),
    "btc_oi":             ("BTCUSDT",       "provider-specific", None),
    "btc_funding":        ("BTCUSDT perp",  "provider-specific", None),
    "btc_liquidations":   ("BTC",           "provider-specific", None),
    "btc_iv":             ("BTC-DVOL",      "provider-specific", None),
}

API_KEYS = {
    "fred": os.getenv("FRED_API_KEY", ""),
    "alphavantage": os.getenv("ALPHAVANTAGE_API_KEY", ""),
    "twelvedata": os.getenv("TWELVEDATA_API_KEY", ""),
    "eia": os.getenv("EIA_API_KEY", ""),
    "bls": os.getenv("BLS_API_KEY", ""),
    "coinmarketcap": os.getenv("COINMARKETCAP_API_KEY", ""),
    "metals": os.getenv("METALS_API_KEY", ""),
    "finnhub": os.getenv("FINNHUB_API_KEY", "")
}

# General config
LOOKBACK_WINDOW_DAYS = 90
