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
