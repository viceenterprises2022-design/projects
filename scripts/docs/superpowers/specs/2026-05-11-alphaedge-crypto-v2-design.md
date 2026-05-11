# Design Spec: AlphaEdge Crypto Diagnostic 2.0

**Date**: 2026-05-11
**Topic**: AlphaEdge Crypto Diagnostic 2.0
**Status**: Draft

## 1. Goal
A high-density, "sleek" terminal-based diagnostic dashboard for cryptocurrencies (BTC, ETH, SOL). It prioritizes actionable signals (Macro, Derivatives, Whale Walls) over raw commodity data.

## 2. Success Criteria
- **Multi-Ticker Display**: BTC, ETH, and SOL technicals shown simultaneously in a single window.
- **Shared Macro Context**: One global macro panel (VIX, DXY, SPX, etc.) at the top, shared by all tickers.
- **Diagnostic Signal**: Clear LTP and aggregated signal score (X/10) for each ticker.
- **Derivative Gravity**: Concentrated strike analysis (Call OI vs. Put OI) and Max Pain for each ticker.
- **Whale Footprints**: Detection of significant order book walls for each ticker.
- **Performance**: 30-second refresh with zero flicker using `rich.live`.

## 3. Architecture

### 3.1 Data Engine (Parallel Fetcher)
- **Framework**: Python `asyncio`.
- **Sources**:
  - **Binance (Spot/Futures)**: LTP, Order Book (top 1% for walls), Klines (for Technicals).
  - **Deribit**: Option chain summary (OI per strike).
  - **Yahoo Finance**: Macro indices (VIX, DXY, SPX, GOLD).
- **Refresh Policy**:
  - Market data (Binance/Deribit): 30 seconds for all three tickers.
  - Macro data (Yahoo): Every 5 minutes (cached) shared across all tickers.

### 3.2 UI Components (Rich Library)
1.  **Global Macro Panel**: Shared at the top (DOW_JONES, DXY, CRUDE, VIX US).
2.  **Ticker Columns (3-Column Layout)**: One column per ticker (BTC, ETH, SOL).
    - **Header**: `[SYM] | Spot: [price] | Fut: [price] ([change]%) | Sig: [NEUTRAL/BULL/BEAR] ([score]/10)`.
    - **Technical Indicators Table**: TREND, RSI, SUPERTREND, VWAP.
    - **Intelligence Blocks**:
        - **Left**: PCR, Max Pain, OI Build, Total Calls/Puts.
        - **Right**: Top 3 Resistance/Support Strikes.
    - **Positioning Chain**: Condensed Option Chain: `CALL OI | STRIKE | PUT OI`.


## 4. Implementation Strategy
- **Flicker-Free**: Use `rich.live.Live` with a layout-based redraw.
- **Concurrency**: `aiohttp` for non-blocking API calls.
- **State Management**: A central `TickerState` object to store data across refresh cycles and compute deltas.

## 5. Testing
- **Unit Tests**: Technical indicator logic (EMA, RSI, Supertrend).
- **Integration Tests**: Mocked API responses for Binance and Deribit.
- **Dry Run**: Verify UI layout on various terminal widths.
