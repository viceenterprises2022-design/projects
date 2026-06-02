# Metals Intelligence Dashboard (MetalsIntel) Design Spec

## 1. Overview
A real-time CLI dashboard for Gold (XAU) and Silver (XAG) combining technical analysis, macro correlations, and order book depth. Built as a combination of `crypto_dashboard.py` and `crypto_market_dashboard_v2.py`.

## 2. Success Criteria
- [ ] Real-time price tracking for XAUUSDT and XAGUSDT via Binance Futures.
- [ ] Technical indicators (RSI, Supertrend, VWAP, EMA Trend) calculated on-the-fly.
- [ ] Liquidation Map / Whale Walls visualized for both assets.
- [ ] Macro correlation table (DXY, VIX, US30, GOLD/SILVER spot).
- [ ] Compact Rich-based terminal UI with auto-refresh (30s).

## 3. Architecture
- **Data Engine**: Modified `MarketEngine` to support Futures Depth and specialized Metals tickers.
- **UI Component**: `Live` display using Rich `Layout`.
- **Logic**:
    - **Price/OI/Depth**: Binance Futures REST API.
    - **Macro**: Yahoo Finance (`yfinance`).
    - **Technicals**: Custom logic in `MarketEngine`.

## 4. Components

### 4.1. Header
- Title: "Metals Intelligence Dashboard"
- Stats: Current time, Countdown to next poll.

### 4.2. Macro Section
- Displays: DXY, VIX, US30, OIL, GOLD (Spot), SILVER (Spot).
- Data: LTP, % Change, Correlation to XAU.

### 4.3. Asset Panels (Vertical Stack)
Each panel contains:
- **Header**: Asset Symbol, Spot Price, 24h Change, Volume.
- **Technicals Table**:
    - Trend (Strong/Mild/Side)
    - RSI (14)
    - Supertrend (Signal + Value)
    - VWAP Distance (%)
- **Orderbook Table**:
    - Top Buy/Sell Walls (> $500k threshold for metals).
    - Book Skew (Bids vs Asks).

## 5. Technical Details
- **Binance Symbols**: `XAUUSDT`, `XAGUSDT`.
- **Binance API**: `fapi.binance.com` for both Klines and Depth.
- **Refresh Rate**: 30 seconds for polling, 1 second for UI countdown.

## 6. Error Handling
- Timeout management for `yfinance` (slow).
- Empty response handling for Binance API.
- Fallback to "Loading..." states during first poll.

## 7. Future Scope
- Options data if a free source for COMEX/CME options is found.
- Multi-venue aggregation (Bybit).
