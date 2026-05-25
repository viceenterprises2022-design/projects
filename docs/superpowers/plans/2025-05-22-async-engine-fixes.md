# Asynchronous Data Engine Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve reliability and performance of `market_engine.py` through error handling, parallelization, and documentation.

**Architecture:** Use `asyncio.gather` for parallel JSON parsing and `try/except` for network/JSON robustness.

**Tech Stack:** Python 3.13, `aiohttp`, `asyncio`.

---

### Task 1: Add Docstrings and Parallel JSON Parsing in `fetch_binance`

**Files:**
- Modify: `market_engine.py`

- [ ] **Step 1: Update `fetch_binance` with docstring and parallel JSON**

```python
    async def fetch_binance(self, session, symbol):
        """
        Fetches spot and futures kline data for a given symbol from Binance.

        Args:
            session (aiohttp.ClientSession): The async HTTP session.
            symbol (str): The symbol to fetch (e.g., 'BTC').

        Returns:
            tuple: (spot_data, futures_data)
        """
        url_spot = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1d&limit=100"
        url_fut = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}USDT&interval=1d&limit=1"
        async with session.get(url_spot) as r1, session.get(url_fut) as r2:
            return await asyncio.gather(r1.json(), r2.json())
```

- [ ] **Step 2: Run verification**

Run: `python3 test_fetch.py`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add market_engine.py
git commit -m "feat(market_engine): add docstrings and parallelize JSON parsing"
```

---

### Task 2: Add Error Handling in `fetch_binance`

**Files:**
- Modify: `market_engine.py`

- [ ] **Step 1: Add try/except blocks to `fetch_binance`**

```python
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
```

- [ ] **Step 2: Run verification**

Run: `python3 test_fetch.py`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add market_engine.py
git commit -m "fix(market_engine): add network and JSON error handling"
```

---

### Task 3: Add Docstrings to `MarketEngine` and `fetch_all`

**Files:**
- Modify: `market_engine.py`

- [ ] **Step 1: Add docstrings to class and `fetch_all`**

```python
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
```

- [ ] **Step 2: Run verification**

Run: `python3 test_fetch.py`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add market_engine.py
git commit -m "docs(market_engine): add docstrings to MarketEngine and fetch_all"
```
