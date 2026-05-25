# Metals Intelligence Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a real-time CLI dashboard for Gold (XAU) and Silver (XAG) using Binance Futures data and Yahoo Finance macro indicators.

**Architecture:** Monolithic script `metals_dashboard.py` powered by an enhanced `MarketEngine` backend. Uses `rich` for terminal UI.

**Tech Stack:** Python, `aiohttp`, `rich`, `yfinance`, `pandas`.

---

### Task 1: Update `MarketEngine` for Metals Support

**Files:**
- Modify: `market_engine.py`

- [ ] **Step 1: Add Silver to macro tickers**
Update `fetch_macro_data` to include `SILVER`.

- [ ] **Step 2: Enhance `fetch_binance` for Futures-only symbols**
Modify `fetch_binance` to handle cases where spot data is missing or invalid.

- [ ] **Step 3: Add Futures Depth support**
Add `fetch_binance_futures_depth` and update `fetch_all_data` to use it for Metals.

- [ ] **Step 4: Verify with `test_fetch_metals.py`**
Run a quick test to ensure XAU/XAG prices and depth are flowing.

---

### Task 2: Implement `metals_dashboard.py`

**Files:**
- Create: `metals_dashboard.py`

- [ ] **Step 1: Scaffold layout and header**
Setup `rich.layout` and `render_header`.

- [ ] **Step 2: Port Macro rendering logic**
Implement `render_macro` with DXY, VIX, GOLD, SILVER.

- [ ] **Step 3: Create Asset Panels**
Implement `render_metal_panel` for XAU (Detailed) and XAG (Summary).

- [ ] **Step 4: Implement Async Loop**
Wire up `asyncio` and `Live` with 30s polling.

---

### Task 3: Final Verification

- [ ] **Step 1: Run dashboard**
- [ ] **Step 2: Verify XAU Whale Walls (> $500k)**
- [ ] **Step 3: Verify Macro correlations**
