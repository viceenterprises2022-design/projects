# AlphaEdge Crypto Diagnostic 2.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a high-density, flicker-free terminal diagnostic dashboard for BTC, ETH, and SOL using parallel data fetching and a 3-column AlphaEdge UI.

**Architecture:** An asynchronous `asyncio` data engine fetches Spot/Futures (Binance), Options (Deribit), and Macro (Yahoo) data in parallel. The UI uses `rich.live` to render a shared macro header and ticker-specific diagnostic columns every 30 seconds.

**Tech Stack:** Python 3.13, `asyncio`, `aiohttp`, `rich`, `yfinance` (or direct Yahoo API).

---

## File Mapping

- `crypto_market_dashboard_v2.py`: The main entry point and UI orchestration.
- `market_engine.py`: The asynchronous data fetching and calculation logic (Technical indicators, correlations).
- `tests/test_indicators.py`: Unit tests for technical indicators (RSI, Supertrend, etc.).

---

## Tasks

### Task 1: Asynchronous Data Engine (MarketEngine)

**Files:**
- Create: `market_engine.py`

- [ ] **Step 1: Implement the MarketEngine class with aiohttp**
```python
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
```

- [ ] **Step 2: Create a dummy test script to verify parallel fetching**
```python
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
```

- [ ] **Step 3: Run the test**
Run: `python3 test_fetch.py`
Expected: "Fetched data for 3 symbols"

- [ ] **Step 4: Commit**
```bash
git add market_engine.py
git commit -m "feat: initial async market engine"
```

### Task 2: Technical Indicators & Macro Correlations

**Files:**
- Modify: `market_engine.py`
- Create: `tests/test_indicators.py`

- [ ] **Step 1: Implement RSI, Supertrend, and Correlation logic**
Add these methods to `MarketEngine`:
```python
def calculate_rsi(self, closes, period=14):
    # RSI implementation logic
    pass

def calculate_correlation(self, btc_prices, macro_prices):
    # Pearson correlation logic
    pass
```

- [ ] **Step 2: Write unit tests for indicators**
```python
# tests/test_indicators.py
import pytest
from market_engine import MarketEngine

def test_rsi_calculation():
    me = MarketEngine()
    data = [10, 12, 11, 13, 15, 14, 16, 18, 17, 19, 21, 20, 22, 24, 23]
    rsi = me.calculate_rsi(data)
    assert 0 <= rsi <= 100
```

- [ ] **Step 3: Run tests**
Run: `pytest tests/test_indicators.py`
Expected: PASS

- [ ] **Step 4: Commit**
```bash
git add market_engine.py tests/test_indicators.py
git commit -m "feat: technical indicators and correlations"
```

### Task 3: 3-Column Diagnostic UI (Multi-Ticker)

**Files:**
- Create: `crypto_market_dashboard_v2.py`

- [ ] **Step 1: Implement the Rich Layout with 3 columns**
```python
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="macro", size=5),
        Layout(name="tickers")
    )
    layout["tickers"].split_row(
        Layout(name="BTC"),
        Layout(name="ETH"),
        Layout(name="SOL")
    )
    return layout
```

- [ ] **Step 2: Implement the update loop with rich.live**
Ensure `live.update()` is called with the new layout every 30s.

- [ ] **Step 3: Mock the UI data and verify layout**
Run the script with hardcoded dummy data to ensure no overlap in columns.

- [ ] **Step 4: Commit**
```bash
git add crypto_market_dashboard_v2.py
git commit -m "feat: 3-column diagnostic UI layout"
```

### Task 4: Option Chain and Whale Wall Integration

**Files:**
- Modify: `market_engine.py`
- Modify: `crypto_market_dashboard_v2.py`

- [ ] **Step 1: Implement Deribit option fetching and Binance order book scan**
- [ ] **Step 2: Format the condensed Option Chain in UI**
- [ ] **Step 3: Implement Whale Wall detection logic**
- [ ] **Step 4: Final Integration and End-to-End verification**
- [ ] **Step 5: Commit**
```bash
git add .
git commit -m "feat: finalize option chain and whale walls"
```
