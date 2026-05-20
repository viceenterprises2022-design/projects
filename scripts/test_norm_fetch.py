import asyncio
import aiohttp
import sys

sys.path.insert(0, "/home/vreddy1/Desktop/Projects/scripts")
import live_market_dashboard as ld

async def main():
    async with aiohttp.ClientSession() as session:
        quotes_res = await ld.safe_get(session, "https://api.upstox.com/v2/market-quote/quotes", {"instrument_key": ",".join(ld.ALL_SYMBOLS_LIST)})
        if isinstance(quotes_res, dict) and quotes_res.get("status") == "success":
            raw_data = quotes_res.get("data", {})
            normalized = {}
            for k, v in raw_data.items():
                symbol_name = v.get("symbol")
                if symbol_name:
                    normalized[symbol_name.upper()] = v
                else:
                    normalized[k.split(":")[-1].upper()] = v
            
            print("Normalized keys in quotes cache:")
            print(list(normalized.keys()))
            
            print("\nTesting lookups:")
            for name in ld.INDICES:
                q = normalized.get(name.upper())
                print(f"  Index: {name} -> LTP = {q.get('last_price') if q else 'MISSING'}")
                
            for name in ld.WATCHLIST:
                q = normalized.get(name.upper())
                print(f"  Stock: {name} -> LTP = {q.get('last_price') if q else 'MISSING'}")

if __name__ == "__main__":
    asyncio.run(main())
