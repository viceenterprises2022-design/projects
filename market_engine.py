import asyncio
import aiohttp
import time

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

    async def fetch_binance(self, session, symbol):
        """
        Fetches spot and futures kline data for a given symbol from Binance.

        Args:
            session (aiohttp.ClientSession): The async HTTP session.
            symbol (str): The symbol to fetch (e.g., 'BTC').

        Returns:
            tuple: (spot_data, futures_data) or (None, None) on error.
        """
        url_spot = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1d&limit=100"
        url_fut = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}USDT&interval=1d&limit=1"
        try:
            async with session.get(url_spot) as r1, session.get(url_fut) as r2:
                try:
                    return await asyncio.gather(r1.json(), r2.json())
                except (ValueError, aiohttp.ContentTypeError) as e:
                    print(f"JSON error for {symbol}: {e}")
                    return None, None
        except aiohttp.ClientError as e:
            print(f"Network error for {symbol}: {e}")
            return None, None

    async def fetch_all(self):
        """
        Fetches data for all configured symbols in parallel.

        Returns:
            list: List of results from fetch_binance for each symbol.
        """
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_binance(session, s) for s in self.symbols]
            results = await asyncio.gather(*tasks)
            return results

    # --- Technical Indicators ---

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
            tr = max(h - l, abs(h - cp), abs(l - cp))
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
        hl2 = (candles[-1][2] + candles[-1][3]) / 2
        lo = hl2 - multiplier * atr
        direction = 1 if (len(candles[-1]) > 4 and candles[-1][4] > lo) else -1
        return (lo if direction == 1 else hl2 + multiplier * atr), direction

    def calculate_vwap(self, candles, period=20):
        """VWAP calculation matching collector.py."""
        tv = vol = 0.0
        # candles: [t, o, h, l, c, v]
        for x in candles[-period:]:
            if len(x) < 6:
                continue
            v = x[5] or 0
            tp = (x[2] + x[3] + x[4]) / 3
            tv += tp * v
            vol += v
        return tv / vol if vol > 0 else None

    def analyze_trend(self, candles):
        """Comprehensive trend analysis matching collector.py logic."""
        closes = [x[4] for x in candles]
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
