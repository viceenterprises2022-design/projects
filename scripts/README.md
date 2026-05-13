# Scripts Repository

Comprehensive collection of scripts for Market Intelligence, AI Search, and automated reporting.

## 🚀 Script Index

### 📈 AlphaEdge Market Intelligence
*A decoupled, 10-factor market intelligence system for Indian Indices (NIFTY, SENSEX, BANKNIFTY).*

| Script | Description |
|:--- |:--- |
| `collector.py` | **Core Engine**. Fetches market data from Upstox/Yahoo, calculates 10-factor signals, and saves to DB. |
| `alphaedge_db.py` | **Database Manager**. Handles SQLite schema and data persistence for `alphaedge.db`. |
| `api_server.py` | **API & Dashboard**. FastAPI backend serving market data and hosting the HTML dashboard on port 8765. |
| `market_engine.py` | Orchestrates the analysis flow for market signals. |
| `market_analysis_v3.py` | Latest version of core logic with **Auto-Refresh Terminal Dashboard**. |
| `run_analysis_headless.py` | CLI tool to run analysis and output results to console only. |
| `report_and_send.py` | Generates diagnostic reports and sends them to Telegram. |
| `options_cli.py` | **Advanced Options Dashboard**. Multi-index (Nifty, Sensex, BankNifty) live terminal view. Shows Spot vs. Futures, human-readable OI (L/C), and ATM ± 300 strikes. **Lean, compressed layout (107 chars)** for small terminal windows. 5s polling, daily-reset SQLite. |

### 🤖 AI Search & Discovery
*Tools for tracking AI agent launches, events, and research using Exa AI.*

| Script | Description |
|:--- |:--- |
| `ai_news_reporter.py` | **Daily Reporter**. Fetches latest AI agent launches and upcoming events; posts to Slack. |
| `astro_report.py` | **Personal Horoscope**. Fetches astro insights via Exa AI and generates a report via Gemini AI. |
| `exa_ai_agents.py` | Tracks new AI agent framework and tool launches from the last 24 hours. |
| `exa_ai_search.py` | Searches for upcoming online AI workshops, webinars, and classes. |

### 🪙 Crypto Intelligence
*Real-time predictive mapping for Crypto markets (BTC, ETH, SOL).*

| Script | Description |
|:--- |:--- |
| `crypto_dashboard.py` | **Crypto Depth Map**. Multi-asset terminal dashboard. Shows real-time Options Chain (Deribit) and Liquidation Map (Binance Order Book Walls). Displays Buy vs Sell liquidity breakdown for high-resolution market structure analysis. 15s parallel polling. |

### 🛠️ Utilities & Helpers
| Script | Description |
|:--- |:--- |
| `send_slack.py` | Generic utility to send text or file content to any Slack webhook. |
| `send_telegram.py` | Generic utility to send messages via Telegram Bot API. |
| `git-autosync.sh` | Shell script for automated git staging, committing, and pushing. |
| `patch_market.py` | Utility to apply specific logic patches to the market analysis scripts. |
| `clawdi` | **Environment Sync**. Cross-agent sync for sessions, skills, and secrets (Clawdi Cloud). |

---

## 🌩️ Clawdi Sync Status
*Current environment is integrated with Clawdi Cloud for session continuity.*

- **Dashboard**: [cloud.clawdi.ai](https://cloud.clawdi.ai/)
- **Active Agents**: Claude Code, Codex, Hermes.
- **Live Sync**: Daemons managed via `systemd` (`clawdi serve`).
- **Known Issue**: Gemini CLI sync in `clawdi` v0.5.7 is currently mapped to Hermes logic (Bug). Actual Gemini sessions do not sync to cloud yet.

---

## 🏗️ AlphaEdge Architecture

1. **Data Collector**: Runs signals (Trend, VIX, OI Skew, PCR, Max Pain) and writes to `alphaedge.db`.
2. **Database**: SQLite storage for historical snapshots.
3. **API Server**: Connects to DB and serves REST endpoints (`/api/latest`, `/api/history`).
4. **Dashboard**: HTML/JS frontend in `frontend/` visualizing trends via Chart.js.

---

## 🛠️ Setup

Install dependencies:
```bash
python3 -m pip install fastapi uvicorn[standard] requests rich exa-py python-dotenv
```

### Usage Examples

**Run AI News Reporter:**
```bash
python3 ai_news_reporter.py
```

**Run Astro Report:**
```bash
python3 astro_report.py
```

**Run AlphaEdge Dashboard:**
```bash
python3 api_server.py  # Server
python3 collector.py --loop --interval 5 # Data collector
```

**Run AI Agent Search:**
```bash
python3 exa_ai_agents.py
```

**Run YouTube Search:**
```bash
# Keyword Search
python3 youtube_video_search.py "AI Agentic Security"

# Channel Search
python3 youtube_video_search.py @mkbhd
```

**Run Options CLI Dashboard:**
```bash
python3 options_cli.py
```

**Run Crypto Depth Map Dashboard:**
```bash
python3 crypto_dashboard.py
```

---
*Maintained by Gemini CLI.*
ned by Gemini CLI.*
ity"

# Channel Search
python3 youtube_video_search.py @mkbhd
```

---
*Maintained by Gemini CLI.*
ned by Gemini CLI.*
