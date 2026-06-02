# Design Document: Crypto Options & Liquidation CLI Dashboard

## 1. Overview
A real-time terminal dashboard for tracking BTC, ETH, and SOL market intelligence. It combines Options Chain data (Deribit) with Liquidation Heatmaps (Binance/Bybit) to identify key support/resistance zones and leverage concentrations.

## 2. Goals & Success Criteria
- **Multi-Asset Support:** Track BTC, ETH, and SOL.
- **Unified View:** Combine options OI with perpetual futures liquidation clusters.
- **Lightweight:** Polling-based architecture (REST) for simplicity and stability.
- **Visual Clarity:** Clear terminal tables with ASCII density bars.

## 3. Data Sources & Integration
### Options Chain (Deribit)
- **API:** `https://www.deribit.com/api/v2/public/`
- **Endpoints:**
    - `get_instruments`: Filter for `kind=option` and `currency` (BTC/ETH/SOL).
    - `get_book_summary_by_currency`: Batch fetch LTP and OI for all options.
- **Logic:**
    - Calculate **Max Pain** and **PCR** (Put-Call Ratio) per asset.
    - Identify ATM (At-The-Money) strikes based on spot price.

### Liquidation Heatmap (Binance + Bybit)
- **Binance API:** `https://fapi.binance.com/fapi/v1/`
    - `openInterest`: Get current Perp OI.
    - `allForceOrders`: Poll for recent liquidation events (24h window).
- **Bybit API:** `https://api.bybit.com/v5/market/`
    - `tickers`: Get mark price and 24h stats.
    - `recent-trade`: Sample for liquidation-style large trades (if public stream is restricted).
- **Aggregation:**
    - Bin prices into 50/100/500 point buckets (asset dependent).
    - Sum liquidation volume per bucket.
    - Select top 10 buckets by volume for the heatmap.

## 4. UI/UX Design
### Layout (107-char width)
1. **Header:** Asset name, Spot, Max Pain, Time.
2. **Options Chain Table:**
   `LTP | OI | STRIKE | OI | LTP`
3. **Liquidation Map Table:**
   `PRICE | VOL (24H) | OI (PERP) | DENSITY [BAR]`

### Interaction
- Cycle through BTC -> ETH -> SOL every N seconds or via user input (if interactive).
- Refresh all data every 10-20 seconds.

## 5. Architecture (Approach 1: Polling)
- **Language:** Python 3.13
- **Libraries:** `requests`, `datetime`, `time`, `json`, `rich` (or custom ANSI for consistency).
- **Main Loop:**
    - `fetch_spot()`
    - `fetch_deribit_options()` -> `calculate_max_pain()`
    - `fetch_liquidations()` -> `aggregate_bins()`
    - `render_ui()`
    - `sleep(15)`

## 6. Testing Strategy
- **Mock Responses:** Test UI rendering with sample JSON from Deribit/Binance.
- **Bucket Logic:** Verify price binning for different asset price scales (e.g., $60k BTC vs $150 SOL).
- **API Resilience:** Handle 429 (Rate Limit) and timeouts gracefully.
