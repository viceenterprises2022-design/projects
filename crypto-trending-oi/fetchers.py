import random
import datetime
import asyncio
import aiohttp
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

# Load API keys
API_KEYS = {
    "fred": os.getenv("FRED_API_KEY", ""),
    "twelvedata": os.getenv("TWELVEDATA_API_KEY", ""),
    "coinmarketcap": os.getenv("COINMARKETCAP_API_KEY", "")
}

async def fetch_mock_factor(factor_name, days=90, base=0, drift=0, vol=1):
    """Fallback for missing data points."""
    await asyncio.sleep(0.01)
    dates = pd.date_range(end=datetime.date.today(), periods=days)
    steps = np.random.normal(loc=drift, scale=vol, size=days)
    values = base + np.cumsum(steps)
    return pd.Series(values, index=dates, name=factor_name)

async def fetch_fred(session, series_id, name, transform='none', days=90):
    """Fetch economic data from FRED."""
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={API_KEYS['fred']}&file_type=json"
        async with session.get(url) as response:
            data = await response.json()
            if 'observations' not in data:
                return await fetch_mock_factor(name)
                
            obs = data['observations']
            dates = [o['date'] for o in obs if o['value'] != '.']
            values = [float(o['value']) for o in obs if o['value'] != '.']
            
            series = pd.Series(values, index=pd.to_datetime(dates))
            series.name = name
            
            if transform == 'pct_change':
                series = series.pct_change() * 100
            elif transform == '13w_change':
                # M2 is usually monthly or weekly, calculate approx 13w (3 months) change
                series = series.pct_change(periods=13) * 100
                
            return series.tail(days)
    except Exception as e:
        print(f"Error fetching FRED {series_id}: {e}")
        return await fetch_mock_factor(name)

async def fetch_defillama_stablecoins(session, days=90):
    """Fetch total stablecoin supply from DefiLlama (Free)."""
    try:
        url = "https://stablecoins.llama.fi/stablecoincharts/all"
        async with session.get(url) as response:
            data = await response.json()
            # Must cast d['date'] to int to prevent pandas from interpreting it as a year string
            dates = [pd.to_datetime(int(d['date']), unit='s') for d in data]
            values = [float(d['totalCirculatingUSD']['peggedUSD']) for d in data]
            
            series = pd.Series(values, index=dates)
            
            # Calculate 7d change for the spec
            change_7d = series.diff(periods=7)
            change_7d.name = "stablecoin_total_7d_change"
            return change_7d.tail(days)
    except Exception as e:
        print(f"Error fetching DefiLlama: {e}")
        return await fetch_mock_factor("stablecoin_total_7d_change")

async def fetch_binance_oi(session, days=90):
    """Fetch open interest from Binance Futures."""
    try:
        # Correct Binance endpoint for Futures OI History
        url = "https://fapi.binance.com/futures/data/openInterestHist?symbol=BTCUSDT&period=1d&limit=90"
        async with session.get(url) as response:
            data = await response.json()
            dates = [pd.to_datetime(d['timestamp'], unit='ms') for d in data]
            values = [float(d['sumOpenInterest']) for d in data]
            
            series = pd.Series(values, index=dates)
            oi_change = series.pct_change() * 100
            oi_change.name = "oi_change"
            return oi_change.tail(days)
    except Exception as e:
        print(f"Error fetching Binance OI: {e}")
        return await fetch_mock_factor("oi_change")

async def fetch_binance_klines(session, days=90):
    """Fetch BTC price history from Binance."""
    try:
        url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=90"
        async with session.get(url) as response:
            data = await response.json()
            dates = [pd.to_datetime(d[0], unit='ms') for d in data]
            closes = [float(d[4]) for d in data]
            
            price_series = pd.Series(closes, index=dates, name="btc_price")
            price_change = price_series.pct_change() * 100
            price_change.name = "price_change"
            
            return price_series, price_change
    except Exception as e:
        print(f"Error fetching Binance Klines: {e}")
        price = await fetch_mock_factor("btc_price", base=65000)
        px_change = await fetch_mock_factor("price_change", base=0)
        return price, px_change

async def fetch_all_factors(use_mock=False):
    """
    Fetches the 13 minimal factors concurrently using real APIs where available,
    falling back to mocks for paid/complex scraping data.
    """
    async with aiohttp.ClientSession() as session:
        # 1. Macro (Using FRED exclusively since it has DXY, VIX, NDX for free)
        task_dxy = fetch_fred(session, "DTWEXBGS", "dxy_1d_pct_change", transform='pct_change')
        task_vix = fetch_fred(session, "VIXCLS", "vix_level", transform='none')
        task_ndx = fetch_fred(session, "NASDAQ100", "ndx_1d_pct_change", transform='pct_change')
        task_us10y = fetch_fred(session, "DFII10", "us10y_real", transform='none')
        task_m2 = fetch_fred(session, "M2SL", "global_m2_13w_change", transform='13w_change')
        task_fed_prob = fetch_mock_factor("fed_cut_probability_1m", base=50.0, vol=5.0)
        
        # 2. Onchain (Real: DefiLlama | Mock: Glassnode/Farside)
        task_stablecoin = fetch_defillama_stablecoins(session)
        task_etf = fetch_mock_factor("btc_etf_net_flow_7d", base=100_000_000, vol=50_000_000)
        task_mvrv = fetch_mock_factor("mvrv_z_score", base=1.5, vol=0.1)
        task_netflow = fetch_mock_factor("btc_exchange_netflow", base=0, vol=1000)
        task_whales = fetch_mock_factor("whale_wallet_change_7d", base=0, vol=1.0)
        task_btc_dom = fetch_mock_factor("btc_dominance_trend", base=54.0, vol=0.2)
        task_halving = fetch_mock_factor("halving_cycle_day", base=(datetime.date.today() - datetime.date(2024, 4, 20)).days - 90, drift=1, vol=0)
        
        # 3. Intraday (Real: Binance | Mock: Coinglass/Deribit)
        task_funding = fetch_mock_factor("perp_funding_rate", base=0.01, vol=0.01) # Funding rate history needs ws/complex API, mocking
        task_oi = fetch_binance_oi(session)
        task_price_tuple = fetch_binance_klines(session)
        task_liq = fetch_mock_factor("liq_imbalance", base=0, vol=1_000_000)
        task_skew = fetch_mock_factor("deribit_25d_skew", base=0, vol=2.0)
        
        # Additional Display Data
        task_dxy_val = fetch_fred(session, "DTWEXBGS", "dxy_value", transform='none')
        task_supply = fetch_mock_factor("stablecoin_supply_total", base=160_000_000_000)
        task_c_oi = fetch_mock_factor("btc_call_oi_total", base=50000, vol=1000)
        task_p_oi = fetch_mock_factor("btc_put_oi_total", base=45000, vol=1000)

        results = await asyncio.gather(
            task_dxy, task_vix, task_ndx, task_us10y, task_m2, task_fed_prob,
            task_stablecoin, task_etf, task_mvrv, task_netflow, task_whales, task_btc_dom, task_halving,
            task_funding, task_oi, task_price_tuple, task_liq, task_skew,
            task_dxy_val, task_supply, task_c_oi, task_p_oi
        )
        
        # task_price_tuple returns two series (price, change), flatten them
        series_list = []
        for r in results:
            if isinstance(r, tuple):
                series_list.extend(r)
            else:
                series_list.append(r)
                
        # Combine all series into a single DataFrame aligned by date
        df = pd.concat(series_list, axis=1)
        
        # CRITICAL: Forward fill missing TradFi weekend data!
        df = df.ffill()
        
        # Ensure no NAs trickled into the final rows by filling backward for any edge cases
        df = df.bfill()
        
        return df

def get_event_flags():
    """Mock events for the regulatory/event layer."""
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
