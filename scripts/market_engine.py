import asyncio
import aiohttp
import time

class MarketEngine:
    def __init__(self, symbols=["BTC", "ETH", "SOL"]):
        self.symbols = symbols
        self.macro_cache = {}
        self.last_macro_update = 0

    async def fetch_binance(self, session, symbol):
        # Fetch Spot and Futures in parallel
        url_spot = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1d&limit=100"
        url_fut = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}USDT&interval=1d&limit=1"
        async with session.get(url_spot) as r1, session.get(url_fut) as r2:
            return await r1.json(), await r2.json()

    async def fetch_all(self):
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_binance(session, s) for s in self.symbols]
            results = await asyncio.gather(*tasks)
            return results
