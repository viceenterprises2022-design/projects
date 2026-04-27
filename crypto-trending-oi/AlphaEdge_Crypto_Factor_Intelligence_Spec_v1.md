# AlphaEdge — Crypto Price Driver Intelligence Spec
**Version:** 1.0 | **Author:** AlphaEdge Research | **For:** Engineering Team  
**Purpose:** Comprehensive factor map, correlation logic, API sourcing, and implementation instructions for the crypto signal engine.

---

## Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [Three-Layer Scoring Model](#2-three-layer-scoring-model)
3. [Macro Regime Factors](#3-macro-regime-factors)
4. [Monetary Policy Factors](#4-monetary-policy-factors)
5. [On-Chain & Crypto-Native Factors](#5-on-chain--crypto-native-factors)
6. [Intraday / Derivatives Factors](#6-intraday--derivatives-factors)
7. [Sentiment & Structural Factors](#7-sentiment--structural-factors)
8. [Regulatory & Event Layer](#8-regulatory--event-layer)
9. [Master API Source Catalog](#9-master-api-source-catalog)
10. [Internal Symbol Alias Map](#10-internal-symbol-alias-map)
11. [Relationship Cheat Sheet](#11-relationship-cheat-sheet)
12. [Regime Correlation Matrix](#12-regime-correlation-matrix)
13. [Minimal Production Feature Set](#13-minimal-production-feature-set)
14. [Implementation Notes for Developers](#14-implementation-notes-for-developers)

---

## 1. Architecture Overview

Crypto prices are driven by **three independent but interacting layers**. Treat them as separate scoring modules and combine with explicit weights.

```
┌─────────────────────────────────────────────────────────────────┐
│                    CRYPTO PRICE SIGNAL ENGINE                   │
├──────────────────┬──────────────────────┬───────────────────────┤
│  LAYER 1         │  LAYER 2             │  LAYER 3              │
│  Macro Regime    │  On-Chain / Native   │  Intraday / Micro     │
│  Score (MRS)     │  Score (OCS)         │  Score (IMS)          │
│                  │                      │                        │
│  Sets direction  │  Confirms structure  │  Timing & deviation   │
│  (days–weeks)    │  (days–weeks)        │  (minutes–hours)      │
│                  │                      │                        │
│  Weight: 0.45    │  Weight: 0.30        │  Weight: 0.25         │
└──────────────────┴──────────────────────┴───────────────────────┘
         │                   │                        │
         └───────────────────┴────────────────────────┘
                             │
                    Final Composite Score
                    [-1.0 bearish → +1.0 bullish]
```

**Core principle:** Macro sets the background trend. On-chain confirms capital structure. Intraday determines precision entry/exit and squeeze risk. Correlations are **state-dependent** — "inverse" or "direct" are defaults, not fixed rules. Always apply regime context before interpreting any single factor.

---

## 2. Three-Layer Scoring Model

### Macro Regime Score (MRS)
```python
# Pseudo-code for MRS computation
def compute_macro_regime_score(factors):
    scores = {
        'dxy':           normalize_inverse(factors['dxy_1d_pct_change']),
        'vix':           normalize_inverse(factors['vix_level']),
        'us10y_real':    normalize_inverse(factors['us10y_real']),
        'ndx':           normalize(factors['ndx_1d_pct_change']),
        'global_m2':     normalize(factors['global_m2_13w_change']),
        'fed_cut_prob':  normalize(factors['fed_cut_probability_1m']),
        'btc_etf_flow':  normalize(factors['btc_etf_net_flow_7d']),
        'credit_spread': normalize_inverse(factors['hy_spread_change']),
    }
    weights = [0.20, 0.18, 0.17, 0.12, 0.12, 0.10, 0.07, 0.04]
    return weighted_sum(scores, weights)  # Output: -1.0 to +1.0
```

### On-Chain Score (OCS)
```python
def compute_onchain_score(factors):
    scores = {
        'exchange_reserves':  normalize_inverse(factors['btc_exchange_netflow']),
        'stablecoin_supply':  normalize(factors['stablecoin_total_7d_change']),
        'mvrv':               normalize_cycle_position(factors['mvrv_z_score']),
        'miner_flow':         normalize_inverse(factors['miner_outflow_30d']),
        'whale_accumulation': normalize(factors['whale_wallet_change_7d']),
        'btc_dominance':      normalize(factors['btc_dominance_trend']),
    }
    weights = [0.25, 0.22, 0.20, 0.13, 0.12, 0.08]
    return weighted_sum(scores, weights)
```

### Intraday Micro Score (IMS)
```python
def compute_intraday_score(factors):
    scores = {
        'funding_rate':    normalize_contrarian(factors['perp_funding_rate']),
        'open_interest':   normalize_directional(factors['oi_change'], factors['price_change']),
        'liquidations':    normalize_directional(factors['liq_imbalance']),
        'options_skew':    normalize(factors['deribit_25d_skew']),
        'basis':           normalize(factors['futures_basis_annualized']),
    }
    weights = [0.30, 0.25, 0.22, 0.13, 0.10]
    return weighted_sum(scores, weights)
```

---

## 3. Macro Regime Factors

### Schema
Each factor has: `internal_key | group | relationship | strength | timeframe | logic | signal_to_watch | api_primary | api_backup | implementation_notes`

---

### 3.1 DXY — US Dollar Index

| Field | Value |
|---|---|
| **internal_key** | `dxy` |
| **group** | macro |
| **relationship** | **INVERSE** |
| **strength** | ★★★★★ Very High |
| **timeframe** | daily / swing |
| **preferred_symbols** | `DXY`, `DX-Y.NYB`, `ICE USDX` |

**Logic:**  
A stronger USD tightens global financial conditions. Dollar-denominated assets (BTC, ETH) become more expensive for non-USD buyers, reducing global demand. Capital flows back into dollar assets from risk assets. The DXY-crypto inverse relationship is the single most consistent macro correlation.

**Signal to watch:**  
- DXY breaking below key weekly support → crypto breakout signal (leading by 1–5 days)  
- DXY daily % change > +0.8% → intraday crypto headwind  
- DXY 20-day trend direction is the regime filter

**API sources:**
```
Primary:   Alpha Vantage — GET /query?function=FX_DAILY&from_symbol=USD&to_symbol=DXY
Backup:    Twelve Data — GET /time_series?symbol=DXY&interval=1day
Backup:    Polygon.io — GET /v2/aggs/ticker/C:USDX/range/1/day/{from}/{to}
Backup:    TradingEconomics — GET /api/markets/symbol/usdollarindex
```

**Implementation notes:**  
Use daily close + 1-day % change + 20-day trend direction. Track weekly high/low breakouts as leading signals. Normalize % change to z-score over 90-day rolling window.

---

### 3.2 VIX — CBOE Volatility Index

| Field | Value |
|---|---|
| **internal_key** | `vix` |
| **group** | macro |
| **relationship** | **INVERSE** |
| **strength** | ★★★★★ Very High |
| **timeframe** | daily / intraday |
| **preferred_symbols** | `VIX`, `^VIX` |

**Logic:**  
VIX measures implied volatility of S&P 500 options — it is the market's "fear gauge." When VIX spikes, institutional players de-risk across all asset classes simultaneously. Crypto sells off harder than equities because it carries no institutional floor. VIX compression (sustained low levels) creates the complacency environment where crypto trends can extend.

**Signal to watch:**  
- VIX > 30 → correlation between crypto and equities spikes to 0.80+; expect forced liquidations  
- VIX < 15 → ideal trending environment for crypto  
- VIX single-day spike > +25% → high probability of crypto flash sell-off within 2–4 hours  

**API sources:**
```
Primary:   Alpha Vantage — GET /query?function=TIME_SERIES_DAILY&symbol=^VIX
Backup:    Twelve Data — GET /time_series?symbol=VIX&interval=1day
Backup:    Polygon.io — GET /v2/aggs/ticker/I:VIX/range/1/day/{from}/{to}
Backup:    Financial Modeling Prep — GET /v3/historical-price-full/%5EVIX
```

**Implementation notes:**  
Use both level (absolute) and 1-day change. Regime thresholds: VIX < 15 = GREEN, 15–25 = YELLOW, 25–30 = ORANGE, > 30 = RED. Apply VIX regime as a multiplier on other signals, not just a standalone input.

---

### 3.3 US30 / SPX / NDX — US Equity Indices

| Field | Value |
|---|---|
| **internal_key** | `us30`, `spx`, `ndx` |
| **group** | macro |
| **relationship** | **DIRECT** (risk-on), **INVERSE** (panic) |
| **strength** | ★★★★ High (NDX strongest) |
| **timeframe** | daily / intraday |
| **preferred_symbols** | `DJIA`, `^GSPC`, `NDX`, `QQQ` |

**Logic:**  
Equities reflect general risk appetite. BTC and ETH trade as high-beta risk assets in risk-on phases, tracking NDX most tightly of all indices. During normal market conditions, the relationship is direct (equities up → crypto up). During panic/crash conditions, the relationship intensifies dramatically — crypto falls 2–4x more than equities as it is perceived as the highest-risk asset class.

**NDX > SPX > US30** in terms of correlation tightness with crypto. Use NDX as primary.

**Signal to watch:**  
- NDX holding 200-DMA = risk-on floor for crypto  
- NDX/SPX gap up at open → usually a tailwind for BTC/ETH in the following session  
- US30 used for broad sentiment confirmation only

**API sources:**
```
Primary:   Alpha Vantage — GET /query?function=TIME_SERIES_DAILY&symbol=QQQ
Backup:    Twelve Data — GET /time_series?symbol=NDX&interval=1day
Backup:    Polygon.io — GET /v2/aggs/ticker/QQQ/range/1/day/{from}/{to}
Backup:    Financial Modeling Prep — GET /v3/historical-price-full/QQQ
```

---

### 3.4 Gold (XAU)

| Field | Value |
|---|---|
| **internal_key** | `xau` |
| **group** | macro |
| **relationship** | **MIXED / REGIME-DEPENDENT** |
| **strength** | ★★★ Medium |
| **timeframe** | swing / daily |
| **preferred_symbols** | `XAUUSD`, `GC` |

**Logic:**  
Gold and BTC share the "store of value / inflation hedge" narrative, creating positive correlation during dollar debasement episodes and geopolitical risk. However, during acute risk-off events (crash days), gold holds or rises while BTC drops, because gold remains the institutional safe haven and BTC does not (yet). Gold ATH breakouts historically **precede** BTC breakouts by 2–6 weeks — use gold as a leading indicator.

**Regime rule:**  
- Gold ↑ + DXY ↓ = **bullish** for BTC (monetary debasement regime)  
- Gold ↑ + VIX ↑ = **ambiguous** — safe-haven demand, not risk-on; do not buy crypto on this  
- Gold ↑ + equities ↑ = **reflation regime** — bullish for crypto

**API sources:**
```
Primary:   Metals-API — GET /latest?base=USD&symbols=XAU (metals-api.com)
Backup:    Twelve Data — GET /time_series?symbol=XAU/USD&interval=1day
Backup:    Alpha Vantage — GET /query?function=FX_DAILY&from_symbol=XAU&to_symbol=USD
Backup:    Polygon.io — GET /v2/aggs/ticker/C:XAUUSD/range/1/day/{from}/{to}
```

---

### 3.5 Silver (XAG)

| Field | Value |
|---|---|
| **internal_key** | `xag` |
| **group** | macro |
| **relationship** | **MIXED / REGIME-DEPENDENT** |
| **strength** | ★★ Medium-Low |
| **timeframe** | swing / daily |
| **preferred_symbols** | `XAGUSD`, `SI` |

**Logic:**  
Silver is a hybrid of monetary metal and growth-sensitive industrial commodity. Less useful as a direct crypto signal, but valuable as a **confirmation signal** within the macro composite. The Gold/Silver ratio falling (silver outperforming gold) indicates aggressive reflation and risk-on appetite — a bullish backdrop for crypto.

**Signal to watch:**  
Gold/Silver ratio trending down over 20 days = risk-on confirmation

**API sources:**
```
Primary:   Metals-API — GET /latest?base=USD&symbols=XAG
Backup:    Twelve Data — GET /time_series?symbol=XAG/USD&interval=1day
Backup:    Alpha Vantage — GET /query?function=FX_DAILY&from_symbol=XAG&to_symbol=USD
```

---

### 3.6 US 10Y Nominal Yield

| Field | Value |
|---|---|
| **internal_key** | `us10y` |
| **group** | macro |
| **relationship** | **INVERSE** |
| **strength** | ★★★★ High |
| **timeframe** | daily |
| **preferred_symbols** | `^TNX`, `US10Y` |

**Logic:**  
Rising nominal yields increase the discount rate on all future cash flows and tighten financial conditions globally. As the "risk-free rate" rises, the opportunity cost of holding non-yielding assets (BTC, gold) increases. Capital rotates from crypto to bonds.

**Signal to watch:**  
- 10Y yield > 5.0% → historically triggers crypto risk-off  
- 1-day change in yield > +8bps = intraday headwind for crypto  
- 20-day downtrend in yields = tailwind

**API sources:**
```
Primary:   FRED API — GET /series/observations?series_id=DGS10&api_key={key}
Backup:    TradingEconomics — GET /api/markets/symbol/ust10y
Backup:    Nasdaq Data Link — GET /api/v3/datasets/USTREASURY/YIELD
```

---

### 3.7 US 10Y Real Yield (TIPS)

| Field | Value |
|---|---|
| **internal_key** | `us10y_real` |
| **group** | macro |
| **relationship** | **INVERSE** |
| **strength** | ★★★★★ Very High |
| **timeframe** | daily |
| **preferred_symbols** | `DFII10`, `10Y real yield` |

**Logic:**  
Real yields are the single best opportunity-cost measure for non-yielding assets like BTC. When real yields turn negative, cash loses purchasing power and investors are incentivized to seek alternatives (gold, BTC). When real yields rise sharply, holding BTC has a real opportunity cost. This is consistently one of the highest R² macro features for BTC trend direction.

**Signal to watch:**  
- Real yield turning negative → strong structural tailwind for BTC  
- Real yield rising above +2.0% → headwind for BTC positioning  

**API sources:**
```
Primary:   FRED API — GET /series/observations?series_id=DFII10&api_key={key}
Backup:    TradingEconomics — GET /api/markets/symbol/usrgdp (proxy)
```

---

### 3.8 Credit Spreads (HY / IG)

| Field | Value |
|---|---|
| **internal_key** | `hy_spread` |
| **group** | macro |
| **relationship** | **INVERSE** |
| **strength** | ★★★ Medium-High |
| **timeframe** | daily |
| **preferred_symbols** | `HY spreads`, `ICE BofA HY Index` |

**Logic:**  
Widening credit spreads signal stress in funding conditions and corporate credit. When HY spreads blow out, it indicates market-wide de-risking. This is a stronger stress filter than VIX alone during certain regimes (e.g., credit-driven crises). Crypto sells off sharply when HY spreads are rapidly widening.

**API sources:**
```
Primary:   FRED API — GET /series/observations?series_id=BAMLH0A0HYM2EY&api_key={key}
Backup:    TradingEconomics — GET /api/markets/symbol/us-high-yield
```

---

### 3.9 Oil / Energy (WTI)

| Field | Value |
|---|---|
| **internal_key** | `wti` |
| **group** | macro |
| **relationship** | **MIXED** |
| **strength** | ★★ Low-Medium |
| **timeframe** | swing / daily |
| **preferred_symbols** | `WTI`, `CL`, `Brent` |

**Logic:**  
Oil has an indirect, regime-dependent relationship with crypto. Moderate oil prices signal global growth (risk-on, positive for crypto). Oil shocks feed into inflation, which prompts Fed tightening, which hurts crypto. Best used as a macro context variable rather than a direct signal.

**API sources:**
```
Primary:   EIA API — GET /series/?api_key={key}&series_id=PET.RWTC.W (free, official)
Backup:    Alpha Vantage — GET /query?function=TIME_SERIES_DAILY&symbol=WTI
Backup:    Twelve Data — GET /time_series?symbol=WTI&interval=1day
```

---

### 3.10 USDJPY / JPY Carry Trade

| Field | Value |
|---|---|
| **internal_key** | `usdjpy` |
| **group** | macro |
| **relationship** | **REGIME-DEPENDENT** |
| **strength** | ★★★ Medium |
| **timeframe** | intraday / daily |
| **preferred_symbols** | `USDJPY`, `JPY crosses` |

**Logic:**  
The Japanese yen is a global funding currency. When USDJPY falls sharply (yen strengthens), it signals unwinding of yen-funded carry trades — investors liquidate risk assets globally to repay yen loans. The August 2024 crypto crash (-20% in 48 hours) was directly triggered by BOJ rate hike + yen carry unwind. Monitor USDJPY closely during BOJ policy windows.

**Signal to watch:**  
- USDJPY falling > 2% in a session = major carry unwind risk across all risk assets  

**API sources:**
```
Primary:   Oanda API — GET /v3/instruments/USD_JPY/candles
Backup:    Alpha Vantage — GET /query?function=FX_DAILY&from_symbol=USD&to_symbol=JPY
Backup:    Twelve Data — GET /time_series?symbol=USD/JPY&interval=1day
```

---

## 4. Monetary Policy Factors

### 4.1 Global M2 Money Supply

| Field | Value |
|---|---|
| **internal_key** | `global_m2` |
| **group** | monetary |
| **relationship** | **DIRECT** |
| **strength** | ★★★★★ Very High |
| **timeframe** | structural / swing |
| **lag** | BTC leads by ~3 months |

**Logic:**  
This is the most powerful macro leading indicator for BTC over medium-term horizons. When global central banks expand money supply, excess liquidity has to find a home — increasingly, crypto has become a recipient. BTC price trends have shown the highest long-horizon sensitivity to global M2 expansion/contraction of any macro variable. Use it as the primary regime setter, not a trading signal.

**Computation:**  
Aggregate US M2 + EU M2 (€ converted to $) + Japan M2 + China M2 + UK M2. Plot 13-week rate of change.

**API sources:**
```
Primary:   FRED API — series MABMM301USM189S (US M2), MABMM301EZM189S (EU M2)
           GET /series/observations?series_id=M2SL&api_key={key}
Backup:    TradingEconomics — Global M2 proxy via country endpoints
Backup:    IMF Data API — GET /data/IFS/{country}/FM_L_USD.PA_XDC_T_IX
```

**Implementation notes:**  
Use 13-week % change as the feature. Monthly data — not useful for intraday. Best for swing/structural regime classification. Lag BTC price reaction model by 8–12 weeks for best fit.

---

### 4.2 Fed Balance Sheet (QE / QT)

| Field | Value |
|---|---|
| **internal_key** | `fed_balance_sheet` |
| **group** | monetary |
| **relationship** | **DIRECT to QE / INVERSE to QT** |
| **strength** | ★★★★ High |
| **timeframe** | structural / daily |
| **preferred_symbols** | `WALCL`, `SOMA` |

**Logic:**  
QE (balance sheet expansion) floods the financial system with reserves, increases risk appetite, and compresses real yields — all bullish for crypto. QT (balance sheet contraction) drains reserves, tightens conditions, and reverses those effects. The 2022 crypto bear market perfectly coincided with the fastest QT in history.

**API sources:**
```
Primary:   FRED API — GET /series/observations?series_id=WALCL&api_key={key}
           (Weekly data, updated Thursdays)
```

---

### 4.3 Fed Funds Rate / Policy Path

| Field | Value |
|---|---|
| **internal_key** | `fed_cut_prob` |
| **group** | monetary |
| **relationship** | **INVERSE to hawkishness / DIRECT to easing** |
| **strength** | ★★★★★ Very High |
| **timeframe** | structural / daily (event-driven) |

**Logic:**  
The Fed's policy path is the single most important driver of the macro regime for crypto. Hawkish repricing (market pricing in more hikes or fewer cuts) compresses multiples and drains liquidity. Dovish pivots (market pricing in rate cuts) are jet fuel for crypto. Convert to probabilities — raw rates are less useful than the *change in expectations*.

**Signal to watch:**  
- CME FedWatch: probability of rate cut in next 3 meetings trending above 50% = structural tailwind  
- Hot CPI print → hawkish repricing → immediate crypto sell-off within hours  

**API sources:**
```
Primary:   CME FedWatch API — https://www.cmegroup.com/CmeWS/mvc/imagic/interest-rate-watch
           (Scrape or use CME data API for cut probability by meeting)
Backup:    FRED API — GET /series/observations?series_id=FEDFUNDS&api_key={key}
Backup:    TradingEconomics — GET /api/markets/symbol/federal-funds-rate
```

---

### 4.4 CPI / Inflation Surprise

| Field | Value |
|---|---|
| **internal_key** | `cpi_surprise` |
| **group** | monetary |
| **relationship** | **REGIME-DEPENDENT** |
| **strength** | ★★★ Medium-High |
| **timeframe** | event / daily |

**Logic:**  
Inflation matters primarily through the Fed reaction function. A hot CPI print → market reprices fewer rate cuts → crypto sells off. A soft CPI print → rate cuts back on the table → crypto rallies. Use surprise vs consensus (actual minus expected), not the raw CPI number.

**API sources:**
```
Primary:   BLS API — GET /timeseries/data/ with series CUUR0000SA0 (CPI-U)
           https://api.bls.gov/publicAPI/v2/timeseries/data/
Backup:    FRED API — GET /series/observations?series_id=CPIAUCSL
Backup:    TradingEconomics — GET /api/calendar (for consensus + actual)
```

**Implementation notes:**  
Model as event flags on release dates. Compute surprise = actual − Bloomberg/TE consensus. Apply decay function post-release (impact fades over 3–5 days unless triggers sustained repricing).

---

### 4.5 TGA / RRP / Treasury Liquidity

| Field | Value |
|---|---|
| **internal_key** | `tga`, `rrp` |
| **group** | monetary |
| **relationship** | **REGIME-DEPENDENT** |
| **strength** | ★★★ Medium-High |
| **timeframe** | daily / swing |

**Logic:**  
Treasury General Account (TGA) drawdowns inject liquidity into the financial system. Reverse Repo (RRP) usage declining means money is leaving the Fed's facility and entering markets. Both proxy for system-level liquidity beyond just Fed balance sheet. Advanced feature — useful for regime scoring when other signals are mixed.

**API sources:**
```
Primary:   FRED API — WTREGEN (TGA), RRPONTSYD (RRP)
Backup:    U.S. Treasury API — https://api.fiscaldata.treasury.gov/services/api/v1/
Backup:    New York Fed — https://www.newyorkfed.org/markets/desk-operations/repo
```

---

## 5. On-Chain & Crypto-Native Factors

### 5.1 BTC Exchange Reserves / Netflow

| Field | Value |
|---|---|
| **internal_key** | `btc_exchange_netflow` |
| **group** | on-chain |
| **relationship** | **INVERSE** (positive netflow = bearish) |
| **strength** | ★★★★ High |
| **timeframe** | daily / swing |

**Logic:**  
BTC flowing into exchanges signals holders are preparing to sell (increasing supply). BTC flowing out of exchanges to cold wallets signals accumulation and supply squeeze. Sustained negative netflow (withdrawals exceeding deposits) historically precedes bull moves.

**Signal to watch:**  
CryptoQuant exchange netflow turning consistently negative over 7 days = bullish accumulation signal

**API sources:**
```
Primary:   CryptoQuant API — GET /v1/btc/exchange-flows/netflow
           https://api.cryptoquant.com/v1/btc/exchange-flows/netflow?window=day
Backup:    Glassnode API — GET /v1/metrics/transactions/transfers_volume_to_exchanges
           https://api.glassnode.com/v1/metrics/transactions/transfers_volume_to_exchanges
```

---

### 5.2 Stablecoin Total Supply

| Field | Value |
|---|---|
| **internal_key** | `stablecoin_total` |
| **group** | on-chain / crypto-native |
| **relationship** | **DIRECT** |
| **strength** | ★★★★ High |
| **timeframe** | daily / swing |

**Logic:**  
Expanding stablecoin supply = rising deployable crypto liquidity. Stablecoins (USDT, USDC) are the "dry powder" of the crypto ecosystem. When supply grows, it represents fresh capital waiting to enter risk assets. Falling stablecoin supply (mass redemptions) signals capital exiting the ecosystem.

**Signal to watch:**  
Stablecoin dominance (USDT.D) falling sharply = capital rotating from stables into BTC/ETH = bullish

**API sources:**
```
Primary:   DefiLlama API — GET /stablecoins (free, comprehensive)
           https://stablecoins.llama.fi/stablecoins
Backup:    CoinGecko API — GET /api/v3/global (total stablecoin market cap)
Backup:    CoinMarketCap API — GET /v1/global-metrics/quotes/latest
```

---

### 5.3 MVRV Z-Score

| Field | Value |
|---|---|
| **internal_key** | `btc_mvrv` |
| **group** | on-chain |
| **relationship** | **MIXED** (cycle position tool) |
| **strength** | ★★★★ High |
| **timeframe** | swing |

**Logic:**  
MVRV = Market Value / Realized Value. The Z-score normalizes this ratio historically. MVRV < 0 (market below cost basis) = historically deep value, high-probability accumulation zone. MVRV Z > 7 = historically severe overheating, cycle top risk. Best for identifying macro-correlation breakdown zones (when internal valuation dominates).

**Signal to watch:**  
- MVRV Z-score < 0 → strong structural buy, regardless of macro headwinds  
- MVRV Z-score > 6 → reduce exposure even in bullish macro regime

**API sources:**
```
Primary:   Glassnode API — GET /v1/metrics/market/mvrv_z_score
           https://api.glassnode.com/v1/metrics/market/mvrv_z_score?a=BTC
Backup:    CryptoQuant API — GET /v1/btc/market-data/mvrv
```

---

### 5.4 BTC Spot ETF Net Flows

| Field | Value |
|---|---|
| **internal_key** | `btc_etf_flows` |
| **group** | crypto-native / structural |
| **relationship** | **DIRECT** |
| **strength** | ★★★★★ Very High |
| **timeframe** | daily |
| **note** | Post-Jan 2024 structural factor — now critical |

**Logic:**  
Post-SEC approval (Jan 2024), US Spot BTC ETFs (BlackRock IBIT, Fidelity FBTC, etc.) create persistent daily institutional demand. Unlike on-chain flows (peer-to-peer), ETF inflows represent regulated institutional money entering the space. Sustained ETF inflows over 5–7 days = sustained price support. ETF outflows are early warning of institutional position reduction.

**API sources:**
```
Primary:   SoSoValue — https://sosovalue.com/assets/etf/us-btc-spot (scrape/API)
           Check current API availability at: https://sosovalue.com
Backup:    Farside Investors — https://farside.co.uk/bitcoin-etf-flow-all-data/
Backup:    Issuer-direct (BlackRock IBIT): 
           https://www.ishares.com/us/products/333011/fund.json
```

**Implementation notes:**  
Pull daily. Use 7-day rolling sum for trend. Flag when daily flow > +$500M (strong institutional demand) or < -$300M (institutional retreat). This is now one of the most important daily signals for BTC.

---

### 5.5 BTC Halving Cycle Position

| Field | Value |
|---|---|
| **internal_key** | `halving_cycle_day` |
| **group** | structural / crypto-native |
| **relationship** | **DIRECT** |
| **strength** | ★★★★★ Very High |
| **timeframe** | structural (12–18 months) |

**Logic:**  
Every ~4 years, the BTC block reward halves, reducing new supply issuance by 50%. Post-halving supply shock historically triggers bull markets 12–18 months out (2013, 2017, 2021 all followed this pattern). Use cycle day as a structural regime feature — it doesn't help with intraday timing but fundamentally sets the multi-month backdrop.

**Last halving:** April 20, 2024 (Block 840,000). Current cycle peak window: ~Q4 2025.

**Implementation:**
```python
import datetime
LAST_HALVING = datetime.date(2024, 4, 20)
NEXT_HALVING_EST = datetime.date(2028, 4, 1)
cycle_day = (datetime.date.today() - LAST_HALVING).days
cycle_pct = cycle_day / (NEXT_HALVING_EST - LAST_HALVING).days
# cycle_pct 0.0–0.3 = early bull, 0.3–0.6 = mid bull, 0.6–0.8 = late bull, 0.8+ = bear/accumulation
```

---

### 5.6 BTC Miner Flows / Hash Ribbon

| Field | Value |
|---|---|
| **internal_key** | `miner_outflow` |
| **group** | on-chain |
| **relationship** | **INVERSE when selling heavily** |
| **strength** | ★★★ Medium |
| **timeframe** | daily / swing |

**Logic:**  
Miners receive BTC as block rewards and must sell some to cover operational costs. Heavy miner selling adds supply pressure, especially post-halving when revenue is halved. Miner capitulation (extended period of selling below cost) is often a bottom signal. The Hash Ribbon indicator (30D MA of hash rate crossing above 60D MA after capitulation) is historically a strong buy signal.

**API sources:**
```
Primary:   Glassnode API — GET /v1/metrics/mining/miners_unspent_supply
Backup:    CryptoQuant API — GET /v1/btc/miner-flows/reserve
```

---

### 5.7 Whale Wallet Activity

| Field | Value |
|---|---|
| **internal_key** | `whale_accumulation` |
| **group** | on-chain |
| **relationship** | **DIRECT** |
| **strength** | ★★★★ High |
| **timeframe** | daily |

**Logic:**  
Wallets holding > 1,000 BTC ("whales") represent the smart money layer of the market. Sustained whale accumulation (rising wallet balances) during price weakness is the strongest on-chain contrarian signal. Whale distribution during price strength is an early warning of cycle tops.

**API sources:**
```
Primary:   Glassnode API — GET /v1/metrics/distribution/balance_1k_to_10k
Backup:    CryptoQuant API — GET /v1/btc/network-data/whale-ratio
```

---

### 5.8 BTC Dominance

| Field | Value |
|---|---|
| **internal_key** | `btc_dominance` |
| **group** | crypto-native |
| **relationship** | **REGIME-DEPENDENT** |
| **strength** | ★★★ Medium |
| **timeframe** | daily |

**Logic:**  
Rising BTC dominance = capital flowing into BTC relative to alts (flight to relative safety within crypto). Falling BTC dominance = altcoin season / risk appetite expanding beyond BTC. Use for rotation models: when dominance falls fast, BTC signal is less useful as alts decouple.

**API sources:**
```
Primary:   CoinGecko API — GET /api/v3/global (returns btc_dominance)
Backup:    CoinMarketCap API — GET /v1/global-metrics/quotes/latest
```

---

## 6. Intraday / Derivatives Factors

### 6.1 Funding Rates (Perpetual Futures)

| Field | Value |
|---|---|
| **internal_key** | `perp_funding_rate` |
| **group** | intraday |
| **relationship** | **MIXED / CONTRARIAN AT EXTREMES** |
| **strength** | ★★★★ High |
| **timeframe** | intraday |

**Logic:**  
Perpetual swap funding rates represent the cost of holding leveraged positions. Positive funding = longs paying shorts (crowded long positioning). Extreme positive funding > +0.10% per 8 hours signals overleveraged longs ripe for a flush. Extreme negative funding signals crowded shorts that can squeeze violently upward. Use z-score or percentile rank, not the raw value.

**Signal to watch:**  
- Funding > +0.10% (8h) → deleveraging risk / contrarian bearish  
- Funding < -0.05% (8h) → short squeeze fuel / contrarian bullish

**API sources:**
```
Primary:   CoinGlass API — GET /api/pro/v1/futures/fundingRate
           https://open-api.coinglass.com/public/v2/funding
Backup:    Binance API — GET /fapi/v1/fundingRate?symbol=BTCUSDT
Backup:    Bybit API — GET /v5/market/funding/history?symbol=BTCUSDT&category=linear
```

---

### 6.2 Open Interest (OI)

| Field | Value |
|---|---|
| **internal_key** | `btc_oi` |
| **group** | intraday |
| **relationship** | **DIRECTIONAL (price + OI combined)** |
| **strength** | ★★★★ High |
| **timeframe** | intraday / daily |

**Logic:**  
OI alone is ambiguous — must be combined with price direction.  
- Rising OI + rising price = new money entering longs → trend confirmation  
- Rising OI + falling price = new money entering shorts → downtrend confirmation  
- Falling OI + price move = short/long squeeze (fast but less sustained)  
- Extreme OI relative to historical = elevated squeeze risk in either direction

**API sources:**
```
Primary:   CoinGlass API — GET /api/pro/v1/futures/openInterest
           https://open-api.coinglass.com/public/v2/open_interest_history
Backup:    Binance API — GET /fapi/v1/openInterest?symbol=BTCUSDT
Backup:    Bybit API — GET /v5/market/open-interest?symbol=BTCUSDT&category=linear
```

---

### 6.3 Liquidations

| Field | Value |
|---|---|
| **internal_key** | `btc_liquidations` |
| **group** | intraday |
| **relationship** | **MIXED** (amplification tool) |
| **strength** | ★★★★ High |
| **timeframe** | intraday |

**Logic:**  
Forced liquidations amplify price moves far beyond macro fair value. Large long liquidation cascades can produce -10% to -20% moves in hours. Large short liquidation squeezes produce equivalent upside. Liquidations are not directional signals — they explain *why* moves exceed macro drivers. Watch the imbalance: if long liquidations dominate, trend is down; if short liquidations dominate, trend is up.

**Signal to watch:**  
- $100M+ liquidation event → likely to see 1–3 additional legs of forced selling  
- Short liquidation cluster forming on the upside → squeeze fuel

**API sources:**
```
Primary:   CoinGlass API — GET /api/pro/v1/futures/liquidations_chart
           https://open-api.coinglass.com/public/v2/liquidation_history
Backup:    Binance API — GET /fapi/v1/allForceOrders?symbol=BTCUSDT
```

---

### 6.4 Options Implied Volatility & Skew

| Field | Value |
|---|---|
| **internal_key** | `btc_iv`, `btc_25d_skew` |
| **group** | intraday |
| **relationship** | **MIXED** |
| **strength** | ★★★ Medium-High |
| **timeframe** | intraday / daily |

**Logic:**  
BTC implied volatility reveals hedging demand and tail risk pricing. Rising IV before an event = market pricing in big move (directionally neutral but signals gamma risk). 25-delta skew: negative skew = puts more expensive than calls (downside hedging demand, bearish signal); positive skew = calls more expensive (upside positioning, bullish signal).

**API sources:**
```
Primary:   Deribit API — GET /api/v2/public/get_historical_volatility?currency=BTC
Backup:    Amberdata API — GET /markets/derivatives/analytics/volatility-surface
Backup:    Laevitas — https://laevitas.ch (API or data export)
```

---

### 6.5 Futures Basis / Calendar Spread

| Field | Value |
|---|---|
| **internal_key** | `futures_basis` |
| **group** | intraday |
| **relationship** | **MIXED** |
| **strength** | ★★★ Medium |
| **timeframe** | intraday / daily |

**Logic:**  
Basis = (futures price − spot price) / spot price × (365 / days to expiry). Elevated annualized basis (>15%) indicates bullish positioning and leverage. Collapsing basis signals deleveraging and risk reduction. Use as a sentiment and leverage proxy alongside funding.

**API sources:**
```
Primary:   Deribit API — GET /api/v2/public/get_instruments?currency=BTC&kind=future
Backup:    CME Group data API for regulated futures basis
Backup:    CoinGlass API — basis data available in dashboard
```

---

## 7. Sentiment & Structural Factors

### 7.1 Crypto Fear & Greed Index

| Field | Value |
|---|---|
| **internal_key** | `fear_greed` |
| **group** | sentiment |
| **relationship** | **CONTRARIAN at extremes** |
| **strength** | ★★★ Medium |
| **timeframe** | daily |

**Signal to watch:**  
- F&G < 15 (Extreme Fear) = historically excellent BTC accumulation zone  
- F&G > 80 (Extreme Greed) = late-stage signal, consider reducing

**API sources:**
```
Primary:   Alternative.me API — GET https://api.alternative.me/fng/
           (Free, no key required)
```

---

### 7.2 Google Trends

| Field | Value |
|---|---|
| **internal_key** | `google_trends_btc` |
| **group** | sentiment |
| **relationship** | **MIXED** (late-stage retail indicator) |
| **strength** | ★★ Low-Medium |
| **timeframe** | weekly |

**Logic:**  
Google Trends spike for "Bitcoin" or "crypto" = retail FOMO = late-cycle signal. Near-zero search interest = bear market bottom accumulation zone.

**API sources:**
```
Primary:   Google Trends Unofficial API via pytrends library
           pytrends.TrendReq().build_payload(['Bitcoin'], timeframe='today 3-m')
```

---

### 7.3 Network Fundamentals

| Field | Value |
|---|---|
| **internal_key** | `active_addresses`, `fees`, `tvl` |
| **group** | on-chain / structural |
| **relationship** | **DIRECT** |
| **strength** | ★★★ Medium |
| **timeframe** | daily / swing |

**Logic:**  
Active addresses, transaction fees, settlement volume, TVL (Total Value Locked in DeFi), and developer activity proxy for underlying network usage and adoption. More relevant to cross-asset relative value and altcoin selection than BTC macro timing.

**API sources:**
```
Primary:   Glassnode API — active addresses, fees, settlement volume
Backup:    DefiLlama API — GET /tvl (free, comprehensive DeFi TVL)
           https://api.llama.fi/tvl
Backup:    Artemis Terminal — developer + on-chain analytics
Backup:    Token Terminal API — protocol revenue and fees
```

---

## 8. Regulatory & Event Layer

**Implementation approach:** Model all items in this section as **categorical event flags** with impact scores, not as continuous correlations. Assign impact_score ∈ {-3, -2, -1, 0, +1, +2, +3} and apply decay function post-event.

```python
# Event flag schema
event = {
    "timestamp": "2024-01-10T16:00:00Z",
    "type": "etf_approval",            # etf_approval | sec_action | ban | macro_shock | hack | banking_stress
    "entity": "SEC / BlackRock IBIT",
    "impact_score": +3,                # -3 severe negative → +3 severe positive
    "impact_duration_days": 30,        # how long to apply decay
    "decay_function": "exponential",   # linear | exponential | step
    "notes": "Spot BTC ETF approved — structural bull catalyst"
}
```

### 8.1 Key Regulatory Events

| Event Type | Impact | Example | API Source |
|---|---|---|---|
| US ETF approval | +3 | Jan 2024 BTC ETF | SoSoValue, NewsAPI |
| SEC enforcement action | -2 to -3 | Exchange lawsuits | SEC EDGAR, NewsAPI |
| Pro-crypto legislation | +1 to +2 | FIT21 Act | Congress.gov, NewsAPI |
| China crypto ban | -2 to -3 | 2021 ban | GDELT, NewsAPI |
| Stablecoin depeg | -2 to -3 | USDC depeg Mar 2023 | CoinGecko API alerts |
| Exchange/protocol hack | -1 to -3 | FTX collapse | NewsAPI, official feeds |
| Banking sector stress | +1 to +2 | SVB crisis → BTC +40% | FRED, NewsAPI |
| Geopolitical escalation | -1 to -2 | Conflict outbreak | GDELT, Reuters |
| BOJ surprise rate hike | -2 | Aug 2024 carry unwind | BOJ, Reuters |

**API sources for event detection:**
```
NewsAPI:      GET https://newsapi.org/v2/everything?q=bitcoin+regulation
GDELT:        GET https://api.gdeltproject.org/api/v2/summary/summary?type=summary
SEC EDGAR:    GET https://efts.sec.gov/LATEST/search-index?q=%22bitcoin%22
FSB:          https://www.fsb.org/work-of-the-fsb/financial-innovation-and-structural-change/
```

---

## 9. Master API Source Catalog

| Source | Covers | Tier | Cost | Base URL |
|---|---|---|---|---|
| **FRED API** | US yields, real yields, M2, Fed balance sheet, CPI, TGA, RRP, credit spreads | Macro backbone | Free | `https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}` |
| **TradingEconomics** | Global macro, event calendar, consensus, country data | Macro + events | Paid | `https://api.tradingeconomics.com/` |
| **Alpha Vantage** | FX, equities, indices, commodities, crypto | Multi-asset starter | Free/Paid | `https://www.alphavantage.co/query` |
| **Twelve Data** | FX, indices, equities, commodities, crypto | Unified feeds | Paid tiers | `https://api.twelvedata.com/` |
| **Polygon.io** | Equities, indices, FX, options | Low-latency market data | Paid | `https://api.polygon.io/` |
| **Financial Modeling Prep** | Stocks, ETFs, indices, quotes | Easy REST market data | Free/Paid | `https://financialmodelingprep.com/api/` |
| **Metals-API** | Gold, silver, metals pricing | Precious metals | Paid | `https://metals-api.com/api/` |
| **EIA API** | Oil, gas, energy fundamentals | Energy context | Free (official) | `https://api.eia.gov/v2/` |
| **BLS API** | CPI, jobs, NFP, labor data | Inflation + employment | Free (official) | `https://api.bls.gov/publicAPI/v2/` |
| **U.S. Treasury API** | Issuance, auctions, TGA | Liquidity context | Free (official) | `https://api.fiscaldata.treasury.gov/services/api/v1/` |
| **CME FedWatch** | Rate cut probabilities | Policy path | Free (scrape) | `https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html` |
| **Oanda API** | FX rates, JPY crosses | FX | Free/Paid | `https://api-fxtrade.oanda.com/` |
| **CoinGecko API** | Spot crypto, market cap, dominance, global | Crypto broad coverage | Free/Paid | `https://api.coingecko.com/api/v3/` |
| **CoinMarketCap API** | Crypto prices, market cap, breadth | Crypto cross-section | Paid | `https://pro-api.coinmarketcap.com/v1/` |
| **DefiLlama API** | Stablecoin supply, TVL, DeFi metrics | DeFi + stablecoins | Free | `https://api.llama.fi/` / `https://stablecoins.llama.fi/` |
| **CoinGlass API** | OI, funding, liquidations, basis | Derivatives (best) | Paid | `https://open-api.coinglass.com/public/v2/` |
| **Glassnode API** | On-chain: MVRV, reserves, SOPR, whales | On-chain (institutional) | Paid | `https://api.glassnode.com/v1/` |
| **CryptoQuant API** | Exchange flows, miner flows, on-chain | Exchange analytics | Paid | `https://api.cryptoquant.com/v1/` |
| **Deribit API** | BTC/ETH options IV, skew, futures | Options/derivatives | Free | `https://www.deribit.com/api/v2/public/` |
| **Binance API** | Funding, OI, trades, order book, perps | Exchange intraday | Free | `https://fapi.binance.com/` |
| **Bybit API** | Funding, OI, perp data | Exchange intraday | Free | `https://api.bybit.com/v5/` |
| **Alternative.me** | Fear & Greed Index | Sentiment | Free | `https://api.alternative.me/fng/` |
| **SoSoValue** | BTC/ETH ETF flow summaries | ETF tracking | Free/check | `https://sosovalue.com/assets/etf/us-btc-spot` |
| **GDELT** | News flow, geopolitical events | Event detection | Free | `https://api.gdeltproject.org/api/v2/` |
| **NewsAPI** | News headlines, sentiment | Event flags | Paid | `https://newsapi.org/v2/` |
| **SEC EDGAR** | Regulatory filings, ETF docs | Regulatory | Free (official) | `https://efts.sec.gov/LATEST/search-index` |

---

## 10. Internal Symbol Alias Map

Always use internal aliases in code. Never hardcode provider-specific symbols — abstract them in a config layer.

```python
SYMBOL_MAP = {
    # Macro
    "dxy":                ("DXY",           "DX-Y.NYB",      "ICE USDX"),
    "vix":                ("^VIX",          "VIX",           "I:VIX"),
    "us30":               ("DJI",           "DJIA",          "US30"),
    "spx":                ("^GSPC",         "SPX",           "SPY"),
    "ndx":                ("NDX",           "QQQ",           "^NDX"),
    "xau":                ("XAUUSD",        "GC",            "C:XAUUSD"),
    "xag":                ("XAGUSD",        "SI",            "C:XAGUSD"),
    "wti":                ("WTI",           "CL",            "USOIL"),
    "usdjpy":             ("USD_JPY",       "USDJPY",        "C:USDJPY"),

    # Yields / Rates
    "us10y":              ("^TNX",          "DGS10",         "US10Y"),
    "us10y_real":         ("DFII10",        "TIPS10",        None),
    "fed_funds":          ("FEDFUNDS",      None,            None),
    "hy_spread":          ("BAMLH0A0HYM2EY", None,          None),

    # Monetary
    "fed_balance_sheet":  ("WALCL",         "SOMA",          None),
    "us_m2":              ("M2SL",          None,            None),
    "tga":                ("WTREGEN",       None,            None),
    "rrp":                ("RRPONTSYD",     None,            None),

    # Macro events
    "cpi":                ("CPIAUCSL",      "CUUR0000SA0",   None),
    "nfp":                ("PAYEMS",        None,            None),

    # Crypto
    "btc_etf_flows":      ("IBIT",          "FBTC",          "provider-specific"),
    "stablecoin_total":   ("USDT+USDC+all", "provider-specific", None),
    "btc_oi":             ("BTCUSDT",       "provider-specific", None),
    "btc_funding":        ("BTCUSDT perp",  "provider-specific", None),
    "btc_liquidations":   ("BTC",           "provider-specific", None),
    "btc_iv":             ("BTC-DVOL",      "provider-specific", None),
    "btc_mvrv":           ("BTC",           "provider-specific", None),
    "btc_exchange_netflow":("BTC",          "provider-specific", None),
    "btc_dominance":      ("BTC.D",         "provider-specific", None),
}
```

---

## 11. Relationship Cheat Sheet

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MOSTLY INVERSE TO CRYPTO (factor rises → crypto falls)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • DXY (US Dollar Index)
  • VIX (equity fear gauge)
  • US 10Y real yield (TIPS)
  • US 10Y nominal yield
  • Credit spreads (HY/IG widening)
  • Hawkish Fed repricing (fewer cuts priced)
  • BTC exchange inflows (net positive)
  • Stablecoin depeg / stress events
  • Heavy miner selling
  • Restrictive regulation events

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MOSTLY DIRECT TO CRYPTO (factor rises → crypto rises)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • Global M2 / money supply expansion
  • QE / Fed balance sheet growth
  • Equities rising (risk-on regime)
  • BTC Spot ETF net inflows
  • ETH / crypto ETF inflows
  • Stablecoin total supply growth
  • BTC exchange outflows (accumulation)
  • Whale wallet accumulation
  • Network fundamentals (active addrs, TVL)
  • Halving cycle (post-halving 12-18m window)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MIXED / REGIME-DEPENDENT (context required before using)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • Gold (XAU)              — use regime rule: Gold↑ + DXY↓ = bullish
  • Silver (XAG)            — confirmation of reflation only
  • CPI / inflation         — depends on Fed reaction
  • NFP / jobs data         — depends on rate reaction
  • Oil (WTI)               — macro context only
  • Geopolitics             — short-term panic then recovery
  • USDJPY                  — carry unwind events only
  • BTC dominance           — rotation model tool
  • Open interest           — combine with price direction
  • Funding rates           — contrarian at extremes
  • Futures basis           — sentiment + leverage proxy
  • BTC exchange netflows   — directional but regime-dependent
  • MVRV                    — cycle position tool
  • Banking sector stress   — BTC as "alternative banking" narrative
```

---

## 12. Regime Correlation Matrix

| Macro Condition | DXY | VIX | 10Y Real | Gold | NDX | Stablecoin | ETF Flow | Crypto Bias |
|---|---|---|---|---|---|---|---|---|
| **Risk-On Bull** | ↓ | ↓ | ↓ | Flat/↑ | ↑↑ | ↑ | ↑↑ | **Strong ↑↑** |
| **Dovish Fed Pivot** | ↓↓ | ↓ | ↓↓ | ↑ | ↑ | ↑ | ↑↑ | **Strong ↑↑** |
| **Dollar Debasement** | ↓↓ | Low | Negative | ↑↑ | ↑ | ↑ | ↑ | **↑↑** |
| **Liquidity Expansion (QE)** | ↓ | Low | ↓ | ↑ | ↑ | ↑ | ↑ | **↑↑** |
| **Post-Halving Window** | Neutral | Neutral | Neutral | Neutral | Neutral | ↑ | ↑ | **↑ (structural)** |
| **Stagflation** | ↑ | ↑ | ↑ | ↑ | ↓ | Mixed | Mixed | **Mixed/↓** |
| **QT / Rate Hike Cycle** | ↑ | ↑ | ↑↑ | ↓ | ↓ | ↓ | ↓ | **↓↓** |
| **Risk-Off Crash** | ↑↑ | ↑↑ | Flight | ↑ | ↓↓ | Redemption | ↓↓ | **↓↓↓** |
| **Carry Unwind (JPY)** | ↑ | ↑↑ | ↑ | ↑ | ↓↓ | ↓ | ↓ | **↓↓ (fast)** |
| **Regulatory Shock** | Neutral | ↑ | Neutral | Neutral | Neutral | ↓ | ↓↓ | **↓ (event)** |
| **Banking Stress (SVB-type)** | ↑ | ↑ | ↓ | ↑ | ↓ | Mixed | ↑ | **↑ (BTC safe haven narrative)** |

---

## 13. Minimal Production Feature Set

Start with this lean core before adding complexity. These 13 features cover ~80% of explainable crypto price variance.

```python
MINIMAL_FEATURE_SET = [
    # Macro regime (Layer 1)
    "dxy",              # USD strength — primary regime filter
    "vix",              # Fear gauge — volatility regime
    "ndx",              # Equity risk appetite proxy
    "us10y_real",       # Opportunity cost — best macro BTC feature
    "fed_cut_prob",     # Policy path probability
    "global_m2_13w",    # Global liquidity — leading indicator

    # On-chain / structural (Layer 2)
    "btc_etf_flows_7d", # Institutional demand — post-2024 critical
    "stablecoin_total", # Deployable crypto liquidity
    "btc_mvrv",         # Cycle position / valuation

    # Intraday / micro (Layer 3)
    "btc_oi",           # Open interest — positioning
    "btc_funding",      # Leverage crowding — contrarian signal
    "btc_liquidations", # Amplification signal
    "btc_iv",           # Implied vol — event risk
]
```

---

## 14. Implementation Notes for Developers

### 14.1 Data Pipeline Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    DATA INGESTION                       │
├──────────────┬───────────────────┬──────────────────────┤
│  Intraday    │  Daily            │  Weekly / Monthly    │
│  (1m – 1h)   │  (EOD)            │  (Structural)        │
│              │                   │                      │
│  Binance     │  FRED             │  FRED (M2, M/S data) │
│  Bybit       │  Alpha Vantage    │  TradingEconomics    │
│  CoinGlass   │  Twelve Data      │  IMF                 │
│  Deribit     │  CoinGecko        │  BLS (CPI, NFP)      │
│  Glassnode   │  DefiLlama        │  Halving cycle calc  │
└──────────────┴───────────────────┴──────────────────────┘
         │                │                   │
         └────────────────┴───────────────────┘
                          │
              ┌───────────────────────┐
              │  FEATURE STORE        │
              │  (normalized,         │
              │   z-scored,           │
              │   alias-mapped)       │
              └───────────────────────┘
                          │
              ┌───────────────────────┐
              │  THREE-LAYER SCORING  │
              │  MRS + OCS + IMS      │
              └───────────────────────┘
                          │
              ┌───────────────────────┐
              │  COMPOSITE SIGNAL     │
              │  + EVENT LAYER        │
              └───────────────────────┘
```

### 14.2 Normalization Rules

```python
def normalize_factor(series, method='zscore', window=90):
    """
    All factors must be normalized before scoring.
    method: 'zscore' | 'percentile' | 'minmax'
    window: rolling window in trading days
    """
    if method == 'zscore':
        return (series - series.rolling(window).mean()) / series.rolling(window).std()
    elif method == 'percentile':
        return series.rolling(window).rank(pct=True)  # 0 to 1

# Apply inverse flag where needed
def apply_relationship(normalized_value, relationship):
    if relationship == 'inverse':
        return -normalized_value
    elif relationship == 'direct':
        return normalized_value
    # For 'mixed' and 'regime-dependent': apply regime context before calling this
```

### 14.3 Correlation Regime Rules (Override Defaults)

```python
REGIME_OVERRIDES = {
    # When VIX > 30: all correlations compress — everything sells
    "vix_crisis": {
        "condition": lambda f: f['vix'] > 30,
        "override": "all inverse",
        "note": "Liquidation regime — macro correlations spike to 0.8+"
    },
    # When MVRV < 0: on-chain value dominates, buy regardless of macro
    "deep_value": {
        "condition": lambda f: f['btc_mvrv_zscore'] < 0,
        "override": "on-chain score weight increases to 0.50",
        "note": "Macro-correlation breakdown zone — internal value signal"
    },
    # When global M2 13W change > +3%: liquidity regime overrides yields
    "liquidity_surge": {
        "condition": lambda f: f['global_m2_13w_pct'] > 3.0,
        "override": "MRS weight increases to 0.55, liquidity factors amplified",
        "note": "Global liquidity surge regime"
    },
    # Post-halving 6-18 months: structural factor adds baseline +0.15 to composite
    "post_halving_bull": {
        "condition": lambda f: 180 < f['halving_cycle_day'] < 540,
        "override": "Add +0.15 to composite before thresholding",
        "note": "Historical post-halving structural bull window"
    }
}
```

### 14.4 Event Layer Integration

```python
def apply_event_decay(base_score, events, today):
    """
    Apply decaying event impact on top of factor scores.
    """
    event_impact = 0
    for event in events:
        days_elapsed = (today - event['timestamp']).days
        if days_elapsed <= event['impact_duration_days']:
            if event['decay_function'] == 'exponential':
                decay = math.exp(-0.1 * days_elapsed)
            elif event['decay_function'] == 'linear':
                decay = 1 - (days_elapsed / event['impact_duration_days'])
            event_impact += event['impact_score'] / 3.0 * decay  # normalize to [-1, +1]
    return base_score + event_impact
```

### 14.5 Update Frequency by Factor Group

| Group | Update Frequency | Method |
|---|---|---|
| Intraday factors (funding, OI, liquidations, IV) | Every 1–5 minutes | WebSocket / polling |
| Daily market factors (DXY, VIX, equities, gold) | End of day + intraday snapshot | REST API polling |
| On-chain factors (exchange flows, MVRV, miners) | Daily (some hourly) | REST API daily batch |
| ETF flows | Daily post-market (4:30 PM ET) | REST API + scrape |
| Macro indicators (CPI, NFP, M2) | Release calendar + monthly | Event-based fetch |
| Fed balance sheet | Weekly (Thursday 4:30 PM ET via FRED) | FRED API weekly |
| Global M2 | Monthly (lag 3–6 weeks) | FRED + central bank APIs |
| Event flags | Real-time | NewsAPI + GDELT webhooks |

### 14.6 Pre-Market Prep Dashboard Output (AlphaEdge Format)

For Vinod's daily 5:30 PM IST Pre-Market sessions, output the following composite view:

```
┌─────────────────────────────────────────────────────────┐
│  ALPHAEDGE PRE-MARKET SIGNAL BRIEF  [timestamp IST]    │
├─────────────────────────────────────────────────────────┤
│  MACRO REGIME SCORE:        +0.42  (BULLISH)           │
│  ON-CHAIN SCORE:            +0.28  (NEUTRAL-BULLISH)   │
│  INTRADAY MICRO SCORE:      -0.15  (SLIGHT CAUTION)    │
│  COMPOSITE SIGNAL:          +0.29  → LEAN LONG         │
├─────────────────────────────────────────────────────────┤
│  TOP BULLISH DRIVERS:                                   │
│    1. DXY -0.4% (2d trend) — macro tailwind            │
│    2. ETF flows +$480M (7d) — institutional demand      │
│    3. Stablecoin supply ↑ $2.1B (7d) — dry powder      │
├─────────────────────────────────────────────────────────┤
│  TOP RISK FLAGS:                                        │
│    1. Funding rate +0.08% — longs moderately crowded   │
│    2. VIX 18.2 — neutral (watch for spike)             │
│    3. CPI print Thursday — event risk                  │
├─────────────────────────────────────────────────────────┤
│  REGIME:  Risk-On Bull  |  CYCLE DAY: 372 post-halving │
└─────────────────────────────────────────────────────────┘
```

---

*Document version 1.0 — AlphaEdge Engineering Spec*  
*Merge of: AlphaEdge Research Matrix v1 + Perplexity Factor Map v1*  
*For internal use only. Review and update quarterly or on major structural market change.*
