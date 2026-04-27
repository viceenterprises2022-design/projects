import asyncio
import aiohttp
from pprint import pprint

COIN_API_KEY = "136d0f86-7ba2-439e-a118-751c6417ef4b"
HEADERS = {'X-CoinAPI-Key': COIN_API_KEY}

async def fetch_coinapi_exchanges(session):
    url = "https://rest.coinapi.io/v1/exchanges"
    async with session.get(url, headers=HEADERS) as response:
        print("Exchanges Status:", response.status)
        if response.status == 200:
            data = await response.json()
            print("First 2 exchanges:")
            pprint(data[:2])
        else:
            print("Response:", await response.text())

async def main():
    async with aiohttp.ClientSession() as session:
        await fetch_coinapi_exchanges(session)

if __name__ == "__main__":
    asyncio.run(main())
