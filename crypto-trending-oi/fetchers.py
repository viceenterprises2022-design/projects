import random
import datetime
import asyncio
import aiohttp
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from config import API_KEYS

load_dotenv()
load_dotenv("API-KEYS.env")

# ─── Helpers ────────────────────────────────────────────────────────────────

async def fetch_mock_factor(factor_name, days=90, base=0, drift=0, vol=1):
    """Fallback for missing data points."""
    await asyncio.sleep(0.01)
    dates = pd.date_range(end=datetime.date.today(), periods=days)
    steps = np.random.normal(loc=drift, scale=vol, size=days)
    values = base + np.cumsum(steps)
    return pd.Series(values, index=dates, name=factor_name)

# ─── FRED ───────────────────────────────────────────────────────────────────

async def fetch_fred(session, series_id, name, transform='none', days=90):
    """Fetch economic data from FRED."""
    try:
        url = (
            f"https://api.stlouisfed.org/fred/series/observations"
            f"?series_id={series_id}&api_key={API_KEYS['fred']}&file_type=json"
        )
        async with session.get(url) as response:
            data = await response.json()
            if 'observations' not in data:
                return await fetch_mock_factor(name)

            obs = data['observations']
            dates  = [o['date']         for o in obs if o['value'] != '.']
            values = [float(o['value']) for o in obs if o['value'] != '.']

            series = pd.Series(values, index=pd.to_datetime(dates), name=name)

            if transform == 'pct_change':
                series = series.pct_change() * 100
            elif transform == '13w_change':
                series = series.pct_change(periods=13) * 100

            # Forward-fill weekend/holiday gaps then return tail
            return series.ffill().tail(days)
    except Exception as e:
        print(f"Error fetching FRED {series_id}: {e}")
        return await fetch_mock_factor(name)

# ─── DefiLlama ──────────────────────────────────────────────────────────────

async def fetch_defillama_stablecoins(session, days=90):
    """Fetch total stablecoin supply 7d change from DefiLlama (Free)."""
    try:
        url = "https://stablecoins.llama.fi/stablecoincharts/all"
        async with session.get(url) as response:
            data = await response.json()
            dates  = [pd.to_datetime(int(d['date']), unit='s') for d in data]
            values = [float(d['totalCirculatingUSD']['peggedUSD'])  for d in data]

            series = pd.Series(values, index=dates)
            change_7d = series.diff(periods=7)
            change_7d.name = "stablecoin_total_7d_change"
            return change_7d.tail(days)
    except Exception as e:
        print(f"Error fetching DefiLlama: {e}")
        return await fetch_mock_factor("stablecoin_total_7d_change")

# ─── Binance Futures ─────────────────────────────────────────────────────────

async def fetch_binance_oi(session, days=90):
    """Fetch open interest history from Binance Futures (free)."""
    try:
        url = "https://fapi.binance.com/futures/data/openInterestHist?symbol=BTCUSDT&period=1d&limit=90"
        async with session.get(url) as response:
            data = await response.json()
            dates  = [pd.to_datetime(d['timestamp'], unit='ms') for d in data]
            values = [float(d['sumOpenInterest'])                for d in data]

            series = pd.Series(values, index=dates)
            oi_change = series.pct_change() * 100
            oi_change.name = "oi_change"
            return oi_change.tail(days)
    except Exception as e:
        print(f"Error fetching Binance OI: {e}")
        return await fetch_mock_factor("oi_change")

async def fetch_binance_klines(session, days=90):
    """Fetch BTC price history from Binance Spot (free)."""
    try:
        url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=90"
        async with session.get(url) as response:
            data = await response.json()
            dates  = [pd.to_datetime(d[0], unit='ms') for d in data]
            closes = [float(d[4])                      for d in data]

            price_series = pd.Series(closes, index=dates, name="btc_price")
            price_change = price_series.pct_change() * 100
            price_change.name = "price_change"
            return price_series, price_change
    except Exception as e:
        print(f"Error fetching Binance Klines: {e}")
        price    = await fetch_mock_factor("btc_price",    base=65000)
        px_change = await fetch_mock_factor("price_change", base=0)
        return price, px_change

# ─── Metals API (Gold) ────────────────────────────────────────────────────────

async def fetch_metals_gold(session, days=90):
    """Fetch XAU/USD daily history from Metals-API."""
    try:
        key = API_KEYS.get("metals", "")
        if not key:
            raise ValueError("No Metals API key")

        # Metals-API: GET /timeseries?base=USD&symbols=XAU&start_date=...&end_date=...
        end_dt   = datetime.date.today()
        start_dt = end_dt - datetime.timedelta(days=days + 10)
        url = (
            f"https://metals-api.com/api/timeseries"
            f"?access_key={key}&base=USD&symbols=XAU"
            f"&start_date={start_dt}&end_date={end_dt}"
        )
        async with session.get(url) as response:
            data = await response.json()
            if not data.get("success"):
                raise ValueError(data.get("error", "Metals API error"))

            rates = data.get("rates", {})
            records = [(pd.to_datetime(dt), 1.0 / v["XAU"]) for dt, v in sorted(rates.items()) if "XAU" in v]
            if not records:
                raise ValueError("No XAU records")

            dates, values = zip(*records)
            series = pd.Series(list(values), index=list(dates), name="xau_price")
            pct = series.pct_change() * 100
            pct.name = "gold_1d_pct_change"
            return pct.tail(days)
    except Exception as e:
        print(f"Error fetching Gold (Metals API): {e}")
        return await fetch_mock_factor("gold_1d_pct_change", base=0, vol=0.5)

# ─── Finnhub (Funding Rate proxy via crypto candles) ─────────────────────────

async def fetch_finnhub_funding(session, days=90):
    """
    Fetches BTC perpetual funding rate from Finnhub (crypto candles).
    Finnhub doesn't expose raw funding, so we use open interest data from
    their stock/crypto candles as a sentiment proxy and fall back to mock if unavailable.
    """
    try:
        key = API_KEYS.get("finnhub", "")
        if not key:
            raise ValueError("No Finnhub API key")

        # Finnhub provides crypto candles; use close price as proxy for momentum
        # We'll compute a simple momentum-based funding rate estimate
        end_ts   = int(datetime.datetime.now().timestamp())
        start_ts = end_ts - (days * 86400)
        url = (
            f"https://finnhub.io/api/v1/crypto/candle"
            f"?symbol=BINANCE:BTCUSDT&resolution=D&from={start_ts}&to={end_ts}&token={key}"
        )
        async with session.get(url) as response:
            data = await response.json()
            if data.get("s") != "ok":
                raise ValueError(f"Finnhub status: {data.get('s')}")

            closes = data.get("c", [])
            timestamps = data.get("t", [])

            dates = [pd.to_datetime(t, unit="s") for t in timestamps]
            series = pd.Series(closes, index=dates, name="btc_close_finnhub")

            # Use 1d returns as a funding rate momentum proxy (high positive momentum → high funding pressure)
            pct = series.pct_change() * 100
            # Scale into funding-rate-like range (roughly 0.01% per 0.1% daily move)
            funding_proxy = (pct * 0.001).rename("perp_funding_rate")
            return funding_proxy.tail(days)
    except Exception as e:
        print(f"Error fetching Finnhub funding proxy: {e}")
        return await fetch_mock_factor("perp_funding_rate", base=0.01, vol=0.01)

# ─── Orchestrator ─────────────────────────────────────────────────────────────

async def fetch_all_factors(use_mock=False):
    """
    Fetches all 13+ scoring factors concurrently.
    Live:  FRED (DXY, VIX, NDX, US10Y_Real, M2, HY_Spread), DefiLlama, Binance, Metals API (Gold), Finnhub
    Mock:  ETF Flows, MVRV, Exchange Netflow, Miner Flow, Whale Wallets, BTC Dominance, Liquidations, Options Skew
    """
    async with aiohttp.ClientSession() as session:

        # ── Layer 1: Macro (FRED + Metals) ──────────────────────────────────
        task_dxy       = fetch_fred(session, "DTWEXBGS",        "dxy_1d_pct_change",    transform='pct_change')
        task_vix       = fetch_fred(session, "VIXCLS",          "vix_level",            transform='none')
        task_ndx       = fetch_fred(session, "NASDAQ100",       "ndx_1d_pct_change",    transform='pct_change')
        task_us10y     = fetch_fred(session, "DFII10",          "us10y_real",           transform='none')
        task_m2        = fetch_fred(session, "M2SL",            "global_m2_13w_change", transform='13w_change')
        task_hy_spread = fetch_fred(session, "BAMLH0A0HYM2EY",  "hy_spread_change",     transform='pct_change')  # 🆕 Credit spread
        task_gold      = fetch_metals_gold(session)                                                               # 🆕 Gold
        task_fed_prob  = fetch_mock_factor("fed_cut_probability_1m", base=50.0, vol=5.0)

        # ── Layer 2: On-Chain (DefiLlama live | rest mocked) ────────────────
        task_stablecoin = fetch_defillama_stablecoins(session)
        task_etf        = fetch_mock_factor("btc_etf_net_flow_7d",    base=100_000_000, vol=50_000_000)
        task_mvrv       = fetch_mock_factor("mvrv_z_score",            base=1.5, vol=0.1)
        task_netflow    = fetch_mock_factor("btc_exchange_netflow",     base=0, vol=1000)
        task_miner      = fetch_mock_factor("miner_outflow_30d",        base=0, vol=500)
        task_whales     = fetch_mock_factor("whale_wallet_change_7d",   base=0, vol=1.0)
        task_btc_dom    = fetch_mock_factor("btc_dominance_trend",      base=54.0, vol=0.2)

        # ── Halving Cycle — deterministic, no mock needed ───────────────────
        halving_day = (datetime.date.today() - datetime.date(2024, 4, 20)).days  # 🔧 Fix #7
        dates_90 = pd.date_range(end=datetime.date.today(), periods=90)
        halving_series = pd.Series(
            [halving_day - (89 - i) for i in range(90)],
            index=dates_90, name="halving_cycle_day"
        )

        # ── Layer 3: Intraday (Finnhub proxy | Binance | mocked rest) ───────
        task_funding      = fetch_finnhub_funding(session)                                     # 🆕 Finnhub
        task_oi           = fetch_binance_oi(session)
        task_price_tuple  = fetch_binance_klines(session)
        task_liq          = fetch_mock_factor("liq_imbalance",      base=0, vol=1_000_000)
        task_skew         = fetch_mock_factor("deribit_25d_skew",   base=0, vol=2.0)

        # ── Display-only extras ──────────────────────────────────────────────
        task_dxy_val = fetch_fred(session, "DTWEXBGS", "dxy_value", transform='none')
        task_supply  = fetch_mock_factor("stablecoin_supply_total", base=160_000_000_000)
        task_c_oi    = fetch_mock_factor("btc_call_oi_total", base=50000, vol=1000)
        task_p_oi    = fetch_mock_factor("btc_put_oi_total",  base=45000, vol=1000)

        results = await asyncio.gather(
            task_dxy, task_vix, task_ndx, task_us10y, task_m2, task_hy_spread, task_gold, task_fed_prob,
            task_stablecoin, task_etf, task_mvrv, task_netflow, task_miner, task_whales, task_btc_dom,
            task_funding, task_oi, task_price_tuple, task_liq, task_skew,
            task_dxy_val, task_supply, task_c_oi, task_p_oi
        )

        # Flatten tuples (price_tuple returns two series)
        series_list = []
        for r in results:
            if isinstance(r, tuple):
                series_list.extend(r)
            else:
                series_list.append(r)

        # Append deterministic halving series
        series_list.append(halving_series)

        # Combine into single DataFrame aligned by date
        df = pd.concat(series_list, axis=1)
        df = df.ffill().bfill()

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
