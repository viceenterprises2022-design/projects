# Crypto Options & Liquidation CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a real-time terminal dashboard tracking BTC/ETH/SOL Options (Deribit) and Liquidation Heatmaps (Binance/Bybit).

**Architecture:** A polling-based CLI tool. It fetches market data via REST APIs, calculates Max Pain/PCR and Liquidation density, and renders a split-panel dashboard in the terminal.

**Tech Stack:** Python 3.13, `requests`, `rich` (for UI), `pytest` (for TDD).

---

### Task 1: Project Scaffolding & Setup

**Files:**
- Create: `crypto_dashboard.py`
- Create: `tests/test_crypto_dashboard.py`

- [ ] **Step 1: Create the basic file structure**
- [ ] **Step 2: Add a placeholder main loop**
```python
import time
import sys

def main():
    while True:
        print("Fetching data...")
        time.sleep(5)

if __name__ == "__main__":
    main()
```
- [ ] **Step 3: Commit**
```bash
git add crypto_dashboard.py
git commit -m "chore: scaffold crypto dashboard script"
```

---

### Task 2: Deribit Options Data Fetcher

**Files:**
- Modify: `crypto_dashboard.py`
- Modify: `tests/test_crypto_dashboard.py`

- [ ] **Step 1: Write test for Deribit quote fetching**
```python
import pytest
from crypto_dashboard import fetch_deribit_quotes

def test_fetch_deribit_quotes_btc():
    data = fetch_deribit_quotes("BTC")
    assert "result" in data
    assert isinstance(data["result"], list)
```
- [ ] **Step 2: Implement `fetch_deribit_quotes`**
```python
import requests

def fetch_deribit_quotes(currency):
    url = f"https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency={currency}&kind=option"
    r = requests.get(url, timeout=10)
    return r.json()
```
- [ ] **Step 3: Run tests**
`pytest tests/test_crypto_dashboard.py::test_fetch_deribit_quotes_btc -v`
- [ ] **Step 4: Commit**
```bash
git commit -am "feat: add deribit options data fetcher"
```

---

### Task 3: Max Pain & PCR Calculation

**Files:**
- Modify: `crypto_dashboard.py`
- Modify: `tests/test_crypto_dashboard.py`

- [ ] **Step 1: Write test for Max Pain calculation**
- [ ] **Step 2: Implement `calculate_max_pain` and `calculate_pcr`**
```python
def calculate_max_pain(options_data):
    # Logic to find strike with minimum total loss for option buyers
    # (Simplified: find strike with highest total OI for now)
    pass

def calculate_pcr(options_data):
    # Sum(Put OI) / Sum(Call OI)
    pass
```
- [ ] **Step 3: Run tests and verify logic**
- [ ] **Step 4: Commit**
```bash
git commit -am "feat: implement max pain and pcr logic"
```

---

### Task 4: Binance/Bybit Liquidation Data Fetcher

**Files:**
- Modify: `crypto_dashboard.py`
- Modify: `tests/test_crypto_dashboard.py`

- [ ] **Step 1: Write test for Binance force orders**
- [ ] **Step 2: Implement `fetch_binance_liquidations`**
```python
def fetch_binance_liquidations(symbol):
    url = f"https://fapi.binance.com/fapi/v1/allForceOrders?symbol={symbol}USDT&limit=100"
    r = requests.get(url, timeout=10)
    return r.json()
```
- [ ] **Step 3: Implement `fetch_bybit_liquidations` (mocked or REST ticker)**
- [ ] **Step 4: Commit**
```bash
git commit -am "feat: add binance/bybit liquidation data fetchers"
```

---

### Task 5: Liquidation Binning & Heatmap Logic

**Files:**
- Modify: `crypto_dashboard.py`
- Modify: `tests/test_crypto_dashboard.py`

- [ ] **Step 1: Write test for price binning**
- [ ] **Step 2: Implement `aggregate_liquidation_bins`**
```python
def aggregate_liquidation_bins(liq_data, bin_size=100):
    bins = {}
    for liq in liq_data:
        price = float(liq['price'])
        vol = float(liq['origQty']) * price
        bin_price = round(price / bin_size) * bin_size
        bins[bin_price] = bins.get(bin_price, 0) + vol
    return sorted(bins.items(), key=lambda x: x[1], reverse=True)[:10]
```
- [ ] **Step 3: Run tests**
- [ ] **Step 4: Commit**
```bash
git commit -am "feat: implement liquidation binning logic"
```

---

### Task 6: Rich Terminal UI Implementation

**Files:**
- Modify: `crypto_dashboard.py`

- [ ] **Step 1: Setup `rich` Table and Layout**
- [ ] **Step 2: Implement `render_dashboard` function**
```python
from rich.console import Console
from rich.table import Table
from rich.live import Live

def render_dashboard(data):
    # Create Layout with 2 panels: Options and Liquidations
    pass
```
- [ ] **Step 3: Integrate with main loop to cycle BTC -> ETH -> SOL**
- [ ] **Step 4: Final verification and commit**
```bash
git commit -am "feat: implement rich terminal dashboard UI"
```
