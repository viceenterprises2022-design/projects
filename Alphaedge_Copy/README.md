# AlphaCopy — Multi-Platform Copy Trading Framework
### Hyperliquid · Binance Futures · Polymarket

> **⚠️ Start in DRY_RUN mode. Validate for 2+ weeks before going live.**

---

## Architecture Overview

```
alphacopy/
├── main.py                    # Orchestrator — runs all bots
├── config/
│   └── settings.py            # All tunable parameters
├── core/
│   ├── risk_manager.py        # Unified SL/TP/drawdown engine
│   └── trader_selector.py     # Alpha scoring & leaderboard filtering
├── bots/
│   ├── hyperliquid_bot.py     # HL WebSocket fill mirroring
│   ├── binance_bot.py         # BN leaderboard polling
│   └── polymarket_bot.py      # POLY whale wallet monitoring
└── utils/
    ├── notifier.py            # Telegram + Discord alerts
    └── dashboard.py           # Console performance view
```

---

## Platform Deep-Dive

### 1. Hyperliquid (`$10k`)
| Feature | Detail |
|---------|--------|
| **Data source** | Official REST + WebSocket (`api.hyperliquid.xyz`) |
| **Leaderboard** | `/info` → `{"type": "leaderboard"}` |
| **Fill monitoring** | WS subscription: `userFills` per wallet |
| **Execution** | `hyperliquid-python-sdk` → signed EIP-712 orders |
| **Auth** | API wallet (separate from main — no withdrawal rights) |
| **SL/TP** | Managed by risk engine in WS price feed |
| **Latency** | ~50ms fill detection |

**Trader selection filter:**
- 30d PnL > $50k
- 30d ROI > 30%
- Max drawdown < 25%
- Alpha score > 60 (our composite metric)

### 2. Binance Futures (`$10k`)
| Feature | Detail |
|---------|--------|
| **Data source** | Unofficial leaderboard endpoints (public, no auth) |
| **Leaderboard** | `POST /bapi/futures/v3/public/future/leaderboard/getLeaderboardRank` |
| **Position check** | `POST /bapi/futures/v1/public/future/leaderboard/getOtherPosition` |
| **Execution** | `python-binance` → official Futures API |
| **Polling interval** | 5 seconds |
| **SL/TP** | Native Binance STOP_MARKET + TAKE_PROFIT_MARKET orders |

> **Note:** Binance no longer offers new portfolios in official copy trading for many regions. We mirror via Futures API directly using public position data.

**Anti-detection:** The leaderboard endpoints are public but rate-limited. Use reasonable polling intervals (≥5s).

### 3. Polymarket (`$10k`)
| Feature | Detail |
|---------|--------|
| **Data source** | CLOB API + Gamma API + PolymarketAnalytics |
| **Execution** | `py_clob_client` on Polygon (Chain ID 137) |
| **Currency** | USDC on Polygon |
| **Key difference** | NO leverage, binary outcomes (0 or $1), no traditional SL |
| **"Stop loss"** | Exit if market price drops 50% from entry |
| **Consensus filter** | Enter only if 2+ whales buy same market |

**Unique risks on Polymarket:**
- Thin order books → severe slippage on large orders
- Resolution risk (oracle manipulation)
- ~25% of volume may be wash trading (airdrop farming)
- Markets can trade at wrong prices during breaking news

---

## Risk Management Architecture

### Position Sizing
```
Max size per trade = MIN(
    current_equity × max_position_pct (15%),
    max_copy_size_usd ($2,000)
)

Risk-based size = (equity × 1%) / stop_loss_distance_pct
Final size = MIN(proportional_copy, risk_based_size)
```

### Stop Loss Structure
```
Entry price: $100
Stop loss:   $95   (-5%)      ← Hard floor
Trailing:    trails up 3%     ← Locks in profits
Take profit: $115  (+15%)     ← Primary exit
```

### Portfolio Guardrails
| Rule | Value |
|------|-------|
| Max drawdown per bot | 20% → auto-halt |
| Max open positions per bot | 5 |
| Max size per position | 15% of equity |
| Copy ratio | 10% of trader's size |

### Alpha Scoring Formula
```
Score (0-100) = 
  30% × Sharpe ratio (normalized)
  20% × 30d ROI
  20% × Win rate (40-80% range)
  15% × Drawdown safety (inverted)
  10% × Consistency (7d vs 30d)
   5% × Experience (trade count)
```

---

## Setup Guide

### Step 1: Install
```bash
git clone <repo>
cd alphacopy
pip install -r requirements.txt
cp .env.example .env
```

### Step 2: Configure keys
```bash
# Edit .env with your credentials
# Hyperliquid: Create API wallet at https://app.hyperliquid.xyz/API
# Binance: API Management → Enable Futures, disable withdrawals
# Polymarket: Polygon wallet with USDC
```

### Step 3: Dry run (mandatory first step)
```bash
python main.py --bot hl      # Test Hyperliquid only
python main.py --bot bn      # Test Binance only  
python main.py --bot poly    # Test Polymarket only
python main.py               # All three simultaneously
```

### Step 4: Monitor for 2 weeks
```bash
python main.py --dashboard   # Check performance anytime
```

### Step 5: Go live (only after validation)
```bash
# Edit config/settings.py: dry_run = False
# OR use flag:
python main.py --live --bot hl   # Go live one bot at a time
```

---

## Scaling Plan

| Phase | Capital | Condition |
|-------|---------|-----------|
| **Phase 1 (now)** | $10k × 3 = $30k | Dry-run 2 weeks |
| **Phase 2** | $25k × 3 = $75k | 2 weeks live, Sharpe > 1.5 |
| **Phase 3** | $50k × 3 = $150k | 1 month live, drawdown < 10% |
| **Phase 4** | Custom | Hire quant, add more wallets |

---

## Key Risks

1. **Slippage**: Your copy arrives after the trader — you get a worse price. Worst on Polymarket thin books.
2. **Front-running**: Other bots watching the same traders. HL has ~50ms latency advantage.
3. **Leaderboard gaming**: Traders pump metrics then blow up. Use our wash-trader filter.
4. **Binance ToS**: Scraping their public endpoints is a grey area. Use reasonable intervals.
5. **Smart contract risk**: Polymarket runs on Polygon — bridge/contract exploits possible.
6. **Key security**: Never store private keys in code. Use `.env`, never commit to git.

---

## Monitoring Commands

```bash
# Live dashboard
python main.py --dashboard

# Follow logs
tail -f logs/alphacopy.log

# Check specific bot
grep "\[HL\]" logs/alphacopy.log | tail -50
grep "\[BN\]" logs/alphacopy.log | tail -50
grep "\[POLY\]" logs/alphacopy.log | tail -50
```

---

*Built for AlphaEdge infrastructure. Not financial advice.*
