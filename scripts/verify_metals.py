import asyncio
from market_engine import MarketEngine

async def verify():
    engine = MarketEngine(symbols=["XAU", "XAG"])
    print("Fetching metals data...")
    data = await engine.fetch_all_data()
    
    # Check Macro
    print("Macro Data:", list(data["macro"].keys()))
    assert "DXY" in data["macro"], "DXY missing"
    assert "VIX" in data["macro"], "VIX missing"
    
    # Check XAU
    xau = data["XAU"]
    print("XAU Data Keys:", list(xau.keys()))
    assert xau["binance"] is not None, "XAU Binance data missing"
    assert xau["depth"] is not None, "XAU Depth missing"
    assert "macro_corr" in xau, "XAU Macro correlation missing"
    
    print("XAU Correlations:", xau["macro_corr"])
    
    # Check Whale Wall Detection
    depth = xau["depth"]
    print(f"XAU Book Skew: {depth['skew']:.4f}")
    print(f"XAU Whale Bids: {len(depth['bids'])}")
    print(f"XAU Whale Asks: {len(depth['asks'])}")
    
    print("\nVerification SUCCESS")

if __name__ == "__main__":
    asyncio.run(verify())
