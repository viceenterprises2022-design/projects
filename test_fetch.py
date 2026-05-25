# test_fetch.py
import asyncio
from market_engine import MarketEngine

async def test():
    me = MarketEngine()
    data = await me.fetch_all()
    print(f"Fetched data for {len(data)} symbols")
    assert len(data) == 3

if __name__ == "__main__":
    asyncio.run(test())
