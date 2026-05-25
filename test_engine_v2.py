# test_engine_v2.py
import asyncio
import json
from market_engine import MarketEngine

async def test():
    me = MarketEngine(symbols=["BTC", "ETH"])
    print("Fetching all data (Binance, Deribit, Depth, Macro)...")
    data = await me.fetch_all_data()
    
    print(f"\nKeys in results: {list(data.keys())}")
    
    for symbol in ["BTC", "ETH"]:
        print(f"\n--- {symbol} ---")
        s_data = data.get(symbol)
        if not s_data:
            print(f"No data for {symbol}")
            continue
            
        print(f"Binance: {'OK' if s_data['binance'] else 'FAILED'}")
        print(f"Options: {'OK' if s_data['options'] else 'FAILED'}")
        if s_data['options']:
            print(f"  PCR (OI/VOL): {s_data['options']['pcr']:.2f} / {s_data['options']['vol_pcr']:.2f}")
            print(f"  OI Skew: {s_data['options']['oi_skew']:+.2f}")
            print(f"  Max OI Strike: {s_data['options']['max_oi']}")
            
        print(f"Depth: {'OK' if s_data['depth'] else 'FAILED'}")
        if s_data['depth']:
            print(f"  Book Skew: {s_data['depth']['skew']:+.2f}")
            print(f"  Bid Walls: {len(s_data['depth']['bids'])}")
            print(f"  Ask Walls: {len(s_data['depth']['asks'])}")
            
        print(f"Macro Corr: {s_data['macro_corr']}")
        if not s_data['macro_corr'] and s_data['binance'] and data.get('macro'):
            binance_len = len(s_data['binance'][0])
            print(f"  DEBUG: Binance history len: {binance_len}")
            for k, m in data['macro'].items():
                print(f"  DEBUG: Macro {k} history len: {len(m.get('history', []))}")

    print(f"\nMacro Data: {'OK' if data.get('macro') else 'FAILED'}")
    if data.get('macro'):
        print(f"  Indices: {list(data['macro'].keys())}")

if __name__ == "__main__":
    asyncio.run(test())
