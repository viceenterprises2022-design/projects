import asyncio
from market_engine import MarketEngine

async def test():
    engine = MarketEngine(symbols=["BTC", "ETH", "SOL"])
    print("Fetching data...")
    data = await engine.fetch_all_data()
    print("Data keys:", data.keys())
    print("Macro keys:", data['macro'].keys())
    for s in ["BTC", "ETH", "SOL"]:
        print(f"\n--- {s} ---")
        print("Options:", data[s]['options'])
        print("Depth Bids:", len(data[s]['depth']['bids']))
        print("Depth Asks:", len(data[s]['depth']['asks']))
        print("Macro Correlation:", data[s]['macro_corr'])

if __name__ == "__main__":
    asyncio.run(test())
