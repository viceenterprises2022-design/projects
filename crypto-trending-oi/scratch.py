import asyncio
import aiohttp
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
FRED_API_KEY = os.getenv("FRED_API_KEY", "")

async def test_binance_oi(session):
    print("Testing Binance OI...")
    urls = [
        "https://fapi.binance.com/futures/data/openInterestHist?symbol=BTCUSDT&period=1d&limit=90",
        "https://fapi.binance.com/fapi/v1/openInterestHist?symbol=BTCUSDT&period=1d&limit=90"
    ]
    for url in urls:
        async with session.get(url) as response:
            print(f"URL: {url} -> Status: {response.status}")
            if response.status == 200:
                data = await response.json()
                print(f"Success! First item keys: {data[0].keys() if data else 'Empty'}")
                return

async def test_defillama(session):
    print("Testing DefiLlama...")
    url = "https://stablecoins.llama.fi/stablecoincharts/all"
    async with session.get(url) as response:
        print(f"Status: {response.status}")
        data = await response.json()
        print(f"First item: {data[0]}")
        try:
            date = pd.to_datetime(int(data[0]['date']), unit='s')
            print(f"Parsed Date: {date}")
        except Exception as e:
            print(f"Date parse error: {e}")

async def test_fred(session):
    print("Testing FRED for VIX, NDX, DXY...")
    series = ["VIXCLS", "NASDAQ100", "DTWEXBGS"]
    for s in series:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id={s}&api_key={FRED_API_KEY}&file_type=json"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                print(f"FRED {s}: Found {len(data.get('observations', []))} records.")
            else:
                print(f"FRED {s}: Failed with status {response.status}")

async def main():
    async with aiohttp.ClientSession() as session:
        await test_binance_oi(session)
        await test_defillama(session)
        await test_fred(session)

if __name__ == "__main__":
    asyncio.run(main())
