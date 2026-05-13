import asyncio
import aiohttp
import time
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

class MarketEngine:
    """
    Asynchronous engine for fetching market data from multiple sources.
    """
    def __init__(self, symbols=["BTC", "ETH", "SOL"]):
        """
        Initializes the engine with a list of symbols.

        Args:
            symbols (list): List of ticker symbols to track.
        """
        self.symbols = symbols
        self.macro_cache = {}
        self.last_macro_update = 0
        self.history_cache = {}

    async def fetch_binance(self, session, symbol):
        """
        Fetches spot and futures kline data for a given symbol from Binance.

        Args:
            session (aiohttp.ClientSession): The async HTTP session.
            symbol (str): The symbol to fetch (e.g., 'BTC').

        Returns:
            tuple: (spot_data, futures_data) or (None, None) on error.
        """
        spot_symbol = symbol
        if symbol == "XAU":
            spot_symbol = "PAXG"
        
        url_spot = f"https://api.binance.com/api/v3/klines?symbol={spot_symbol}USDT&interval=1d&limit=100"
        url_fut = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}USDT&interval=1d&limit=100"
        
        async def safe_get(url):
            try:
                async with session.get(url) as r:
                    if r.status == 200:
                        return await r.json()
                    return None
            except Exception:
                return None

        try:
            spot, fut = await asyncio.gather(safe_get(url_spot), safe_get(url_fut))
            # Fallback for XAG which has no spot on Binance
            if not spot and fut:
                spot = fut # Use futures as spot proxy for technicals if spot is missing
            return spot, fut
        except Exception as e:
            return None, None

    async def fetch_deribit_options(self, session, currency):
        """Fetches Deribit option summaries."""
        url = f"https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency={currency}&kind=option"
        try:
            async with session.get(url) as r:
                return await r.json()
        except Exception as e:
            return None

    async def fetch_binance_depth(self, session, symbol):
        """Fetches order book depth for whale wall detection."""
        url = f"https://api.binance.com/api/v3/depth?symbol={symbol}USDT&limit=100"
        try:
            async with session.get(url) as r:
                return await r.json()
        except Exception as e:
            return None

    async def fetch_binance_futures_depth(self, session, symbol):
        """Fetches order book depth for whale wall detection from Futures."""
        url = f"https://fapi.binance.com/fapi/v1/depth?symbol={symbol}USDT&limit=1000"
        try:
            async with session.get(url) as r:
                return await r.json()
        except Exception as e:
            return None

    async def fetch_macro_data(self):
        """Fetches macro indices via yfinance."""
        now = time.time()
        if now - self.last_macro_update < 300 and self.macro_cache:
            return self.macro_cache
        
        tickers = {
            "DXY": "DX-Y.NYB",
            "VIX": "^VIX",
            "US30": "^DJI",
            "GOLD": "GC=F",
            "SILVER": "SI=F",
            "OIL": "CL=F"
        }
        
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: yf.download(list(tickers.values()), period="1mo", interval="1d", progress=False))
            
            if data.empty:
                return self.macro_cache

            results = {}
            for key, ticker in tickers.items():
                if ticker in data['Close']:
                    series = data['Close'][ticker].dropna()
                    if len(series) >= 2:
                        ltp = series.iloc[-1]
                        prev = series.iloc[-2]
                        chg = ((ltp - prev) / prev) * 100
                        results[key] = {
                            "current": ltp,
                            "change": chg,
                            "history": series.tolist()
                        }
            
            self.macro_cache = results
            self.last_macro_update = now
            return results
        except Exception as e:
            return self.macro_cache

    async def fetch_all_data(self):
        """Aggregates all data sources."""
        async with aiohttp.ClientSession() as session:
            binance_tasks = [self.fetch_binance(session, s) for s in self.symbols]
            option_tasks = [self.fetch_deribit_options(session, s) for s in self.symbols]
            
            depth_tasks = []
            for s in self.symbols:
                if s in ["XAU", "XAG"]:
                    depth_tasks.append(self.fetch_binance_futures_depth(session, s))
                else:
                    depth_tasks.append(self.fetch_binance_depth(session, s))
            
            # Gather everything at once to ensure all coroutines are awaited
            # even if one of them fails.
            results = await asyncio.gather(
                asyncio.gather(*binance_tasks),
                asyncio.gather(*option_tasks),
                asyncio.gather(*depth_tasks),
                self.fetch_macro_data(),
                return_exceptions=True
            )
            
            # Unpack results, handling potential exceptions
            binance_results = results[0] if not isinstance(results[0], Exception) else [ (None, None) for _ in self.symbols ]
            option_results = results[1] if not isinstance(results[1], Exception) else [ None for _ in self.symbols ]
            depth_results = results[2] if not isinstance(results[2], Exception) else [ None for _ in self.symbols ]
            macro_results = results[3] if not isinstance(results[3], Exception) else {}
            
            processed = {}
            for i, symbol in enumerate(self.symbols):
                processed[symbol] = {
                    "binance": binance_results[i] if i < len(binance_results) else (None, None),
                    "options": self.process_options(option_results[i] if i < len(option_results) else None),
                    "depth": self.process_depth(depth_results[i] if i < len(depth_results) else None, binance_results[i] if i < len(binance_results) else (None, None)),
                    "liq_map": self.generate_liquidation_map(depth_results[i] if i < len(depth_results) else None, symbol),
                    "macro_corr": self.calculate_macro_correlations(symbol, binance_results[i] if i < len(binance_results) else (None, None), macro_results)
                }
            
            processed["macro"] = macro_results
            return processed

    def generate_liquidation_map(self, depth_data, symbol):
        """Bins depth data for visual map."""
        if not depth_data: return []
        # Metals need smaller bins than BTC
        bin_size = 1.0 if symbol == "XAU" else (0.1 if symbol == "XAG" else 1.0)
        from collections import defaultdict
        bins = defaultdict(lambda: {"buy": 0.0, "sell": 0.0})
        for side in ["bids", "asks"]:
            key = "buy" if side == "bids" else "sell"
            for price_str, qty_str in depth_data.get(side, []):
                p, q = float(price_str), float(qty_str)
                bin_p = round(p / bin_size) * bin_size
                bins[bin_p][key] += (p * q)
        flattened = []
        for p, v in bins.items():
            total = v["buy"] + v["sell"]
            flattened.append((p, v["buy"], v["sell"], total))
        # Get top 15 by total volume
        top_vols = sorted(flattened, key=lambda x: x[3], reverse=True)[:15]
        return sorted(top_vols, key=lambda x: x[0], reverse=True)

    def process_options(self, data):
        """Calculates Max Pain, Max OI, PCR, and Skew from Deribit data."""
        if not data or 'result' not in data:
            return None
        
        results = data['result']
        calls = [r for r in results if r['instrument_name'].split('-')[-1] == 'C']
        puts = [r for r in results if r['instrument_name'].split('-')[-1] == 'P']
        
        call_oi = sum(r.get('open_interest', 0) for r in calls)
        put_oi = sum(r.get('open_interest', 0) for r in puts)
        pcr = put_oi / call_oi if call_oi > 0 else 0
        
        call_vol = sum(r.get('volume', 0) for r in calls)
        put_vol = sum(r.get('volume', 0) for r in puts)
        vol_pcr = put_vol / call_vol if call_vol > 0 else 0
        
        oi_skew = (put_oi - call_oi) / (put_oi + call_oi) if (put_oi + call_oi) > 0 else 0
        
        # Simple Max Pain estimation (strike with highest total OI for now as proxy)
        all_strikes = {}
        for r in results:
            try:
                strike = float(r['instrument_name'].split('-')[-2])
                oi = r.get('open_interest', 0)
                all_strikes[strike] = all_strikes.get(strike, 0) + oi
            except: continue
        
        max_oi_strike = max(all_strikes, key=all_strikes.get) if all_strikes else 0
        
        return {
            "pcr": pcr,
            "vol_pcr": vol_pcr,
            "oi_skew": oi_skew,
            "max_oi": max_oi_strike,
            "total_oi": call_oi + put_oi,
            "top_strikes": sorted(all_strikes.items(), key=lambda x: x[1], reverse=True)[:5]
        }

    def process_depth(self, depth, binance_data):
        """Detects Whale Walls (> $500k within 1% of price) and calculates book skew."""
        if not depth or not binance_data or not binance_data[1]:
            return None
        
        ltp = float(binance_data[1][0][4]) # Current close from futures kline
        
        bids = depth.get('bids', [])
        asks = depth.get('asks', [])
        
        whale_bids = []
        whale_asks = []
        
        total_bid_val = 0
        total_ask_val = 0
        
        threshold = 500000 # $500k USD
        
        for price, qty in bids:
            p, q = float(price), float(qty)
            val = p * q
            if p >= ltp * 0.99:
                total_bid_val += val
                if val >= threshold:
                    whale_bids.append({"p": p, "v": val})
                
        for price, qty in asks:
            p, q = float(price), float(qty)
            val = p * q
            if p <= ltp * 1.01:
                total_ask_val += val
                if val >= threshold:
                    whale_asks.append({"p": p, "v": val})
        
        skew = (total_bid_val - total_ask_val) / (total_bid_val + total_ask_val) if (total_bid_val + total_ask_val) > 0 else 0
        
        return {
            "bids": sorted(whale_bids, key=lambda x: x['v'], reverse=True),
            "asks": sorted(whale_asks, key=lambda x: x['v'], reverse=True),
            "skew": skew,
            "bid_depth": total_bid_val,
            "ask_depth": total_ask_val
        }

    def calculate_macro_correlations(self, symbol, binance_data, macro_data):
        """Pearson correlation with DXY, VIX, SPX over available overlap."""
        if not binance_data or not binance_data[0] or not macro_data:
            return {}
        
        # Use up to 30 days of spot closes
        btc_closes = [float(x[4]) for x in binance_data[0]][-30:]
        correlations = {}
        
        for key, mdata in macro_data.items():
            m_history = mdata.get('history', [])
            # Align lengths
            min_len = min(len(btc_closes), len(m_history))
            if min_len >= 5: # Need at least some data for meaningful correlation
                s1 = btc_closes[-min_len:]
                s2 = m_history[-min_len:]
                correlations[key] = self.calculate_correlation(s1, s2)
                
        return correlations

    # --- Existing methods ---
    async def fetch_all(self):
        """Backwards compatibility for previous version."""
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_binance(session, s) for s in self.symbols]
            results = await asyncio.gather(*tasks)
            return results

    def calculate_ema(self, data, period):
        """Standard EMA calculation matching collector.py."""
        if len(data) < period:
            return []
        # Initial SMA
        out = [sum(data[:period]) / period]
        k = 2 / (period + 1)
        for x in data[period:]:
            out.append(x * k + out[-1] * (1 - k))
        return out

    def calculate_rsi(self, closes, period=14):
        """RSI calculation matching collector.py."""
        if len(closes) < period + 2:
            return 50.0
        g = [max(closes[i] - closes[i - 1], 0) for i in range(1, len(closes))]
        l = [max(closes[i - 1] - closes[i], 0) for i in range(1, len(closes))]
        ag = sum(g[-period:]) / period
        al = sum(l[-period:]) / period
        return 100.0 if al == 0 else 100 - 100 / (1 + ag / al)

    def calculate_atr(self, candles, period=14):
        """Average True Range matching collector.py."""
        if len(candles) < 2:
            return 0
        trs = []
        for i in range(1, len(candles)):
            if len(candles[i]) < 5 or len(candles[i-1]) < 5:
                continue
            h, l, cp = candles[i][2], candles[i][3], candles[i-1][4]
            tr = max(float(h) - float(l), abs(float(h) - float(cp)), abs(float(l) - float(cp)))
            trs.append(tr)
        return sum(trs[-period:]) / min(period, len(trs)) if trs else 0

    def calculate_supertrend(self, candles, period=10, multiplier=3):
        """Supertrend calculation matching collector.py."""
        if len(candles) < period + 2:
            return None, 0
        atr = self.calculate_atr(candles, period)
        if atr == 0:
            return None, 0
        # Formula: HL2 +/- Multiplier * ATR
        if len(candles[-1]) < 4:
            return None, 0
        hl2 = (float(candles[-1][2]) + float(candles[-1][3])) / 2
        lo = hl2 - multiplier * atr
        direction = 1 if (len(candles[-1]) > 4 and float(candles[-1][4]) > lo) else -1
        return (lo if direction == 1 else hl2 + multiplier * atr), direction

    def calculate_vwap(self, candles, period=20):
        """VWAP calculation matching collector.py."""
        tv = vol = 0.0
        # candles: [t, o, h, l, c, v]
        for x in candles[-period:]:
            if len(x) < 6:
                continue
            v = float(x[5]) or 0
            tp = (float(x[2]) + float(x[3]) + float(x[4])) / 3
            tv += tp * v
            vol += v
        return tv / vol if vol > 0 else None

    def analyze_trend(self, candles):
        """Comprehensive trend analysis matching collector.py logic."""
        closes = [float(x[4]) for x in candles]
        if len(closes) < 20:
            return "N/A", 0, f"{len(closes)} bars"
        
        e20_l = self.calculate_ema(closes, 20)
        e50_l = self.calculate_ema(closes, min(50, len(closes)))
        e200_l = self.calculate_ema(closes, min(200, len(closes)))
        
        e20 = e20_l[-1] if e20_l else 0
        e50 = e50_l[-1] if e50_l else 0
        e200 = e200_l[-1] if e200_l else None
        
        cur = closes[-1]
        det = f"EMA20={e20:,.0f} | EMA50={e50:,.0f}"
        if e200:
            det += f" | EMA200={e200:,.0f}"
            if cur > e20 > e50 > e200: return "Strong Uptrend", 2, det
            if cur < e20 < e50 < e200: return "Strong Downtrend", -2, det
            
        if cur > e20 > e50: return "Uptrend", 1, det
        if cur < e20 < e50: return "Downtrend", -1, det
        if cur > e20: return "Mild Uptrend", 1, det
        if cur < e20: return "Mild Downtrend", -1, det
        
        return "Sideways", 0, det

    def calculate_correlation(self, series_a, series_b):
        """Pearson Correlation Coefficient."""
        if len(series_a) != len(series_b) or len(series_a) < 2:
            return 0
        n = len(series_a)
        sum_a = sum(series_a)
        sum_b = sum(series_b)
        sum_a_sq = sum(x*x for x in series_a)
        sum_b_sq = sum(x*x for x in series_b)
        p_sum = sum(series_a[i] * series_b[i] for i in range(n))
        
        num = p_sum - (sum_a * sum_b / n)
        den = ((sum_a_sq - pow(sum_a, 2) / n) * (sum_b_sq - pow(sum_b, 2) / n)) ** 0.5
        
        if den == 0:
            return 0
        return num / den
