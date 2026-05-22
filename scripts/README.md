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
| `crypto_dashboard.py` | **Unified Crypto Depth Map**. Simultaneous BTC, ETH, and SOL dashboard. Shows real-time Options Chain (Deribit) and Liquidation Map (Binance Order Book Walls) with 10-level depth. Displays Buy vs Sell breakdown to identify Support/Resistance. Features a live poll countdown and 15s parallel updates. |

### 📊 Live Market Dashboards
*Async real-time dashboards requiring venv python.*

| Script | Description |
|:--- |:--- |
| `alphaedge_pro.py` | **AlphaEdge Pro**. Advanced async market dashboard. |
| `live_market_dashboard.py` | **Live Market Dashboard**. Real-time async market view. |

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
- **Active Agents**: Claude Code, Codex, Hermes, Gemini, Cursor.
- **Live Sync**: Daemons managed via `systemd` (`clawdi serve`).
- **Known Issue**: Gemini CLI and Antigravity CLI sync in `clawdi` v0.5.7 is currently mapped to Hermes logic (Bug). Actual sessions do not sync to cloud yet.

## ⚙️ Systemd Services

| Service | Description | Port |
|:--- |:--- |:--- |
| `alphaedge-api.service` | AlphaEdge Market Intelligence API (FastAPI + uvicorn) | `:8765` |
| `multica-daemon.service` | Multica Agent Runtime (Claude, Codex, Gemini, Hermes, Cursor) | — |

```bash
# Check status
sudo systemctl status alphaedge-api
sudo systemctl status multica-daemon

# Restart
sudo systemctl restart alphaedge-api
sudo systemctl restart multica-daemon

# Logs
journalctl -u alphaedge-api -f
journalctl -u multica-daemon -f
```

---

## 🏗️ AlphaEdge Architecture

1. **Data Collector**: Runs signals (Trend, VIX, OI Skew, PCR, Max Pain) and writes to `alphaedge.db`.
2. **Database**: SQLite storage for historical snapshots.
3. **API Server**: Connects to DB and serves REST endpoints (`/api/latest`, `/api/history`).
4. **Dashboard**: HTML/JS frontend in `frontend/` visualizing trends via Chart.js.

---

## 🛠️ Setup

### Python Environment

System Python 3.14 blocks global pip installs. Use the project venv:

```bash
python3 -m venv venv
venv/bin/pip install fastapi "uvicorn[standard]" requests rich exa-py python-dotenv aiohttp
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
venv/bin/python api_server.py  # Server (or managed by systemd: alphaedge-api.service)
python3 collector.py --loop --interval 5 # Data collector
```

**Run AlphaEdge Pro / Live Market Dashboard:**
```bash
venv/bin/python alphaedge_pro.py
venv/bin/python live_market_dashboard.py
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

**Run Metals Intelligence Dashboard:**
```bash
python3 metals_dashboard.py
```

---

## 🛠️ Troubleshooting & Database Recovery (GBrain / PGlite)

If `gbrain-autopilot.service` crashes or fails to start with the following WASM runtime abort error:
```
PGLite failed to initialize its WASM runtime.
Original error: Aborted()
...
PANIC: could not locate a valid checkpoint record at ...
```
This is caused by an unclean shutdown leaving the PGlite (embedded WASM Postgres) Write-Ahead Log (WAL) in an inconsistent/corrupted state.

### Recovery Procedure
To repair the database without losing your stored data (avoiding database deletion):

1. **Download PostgreSQL Utilities**:
   Download the PostgreSQL package matching your major version (e.g., PostgreSQL 17 for Ubuntu/Debian) to extract administrative tools without needing system-wide installation or `sudo`:
   ```bash
   apt-get download postgresql-17
   dpkg -x postgresql-17_*.deb ./extracted_pg
   ```

2. **Clean up Stale Locks**:
   Ensure `gbrain-autopilot` is stopped and remove any stale postmaster PID lock file:
   ```bash
   systemctl --user stop gbrain-autopilot.service
   rm -f ~/.gbrain/brain.pglite/postmaster.pid
   ```

3. **Verify control file**:
   Check the current system state using `pg_controldata`:
   ```bash
   ./extracted_pg/usr/lib/postgresql/17/bin/pg_controldata -D ~/.gbrain/brain.pglite
   ```

4. **Reset Write-Ahead Log (WAL)**:
   Force a reset of the WAL using `pg_resetwal` to bypass the corrupted checkpoint record and return the database to a clean, runnable state:
   ```bash
   ./extracted_pg/usr/lib/postgresql/17/bin/pg_resetwal -f -D ~/.gbrain/brain.pglite
   ```

5. **Clean Up & Restart Daemon**:
   Delete the extracted utility directory and restart the autopilot service:
   ```bash
   rm -rf ./extracted_pg postgresql-17_*.deb
   systemctl --user start gbrain-autopilot.service
   ```

---

### ⚠️ Migration Note: Gemini CLI to Antigravity CLI
Gemini CLI is being sunset on June 18, 2026. This project has been migrated to support the new Go-based **Antigravity CLI**. Legacy `.gemini` configurations are deprecated; please use the new `.agent` configurations. System-level extensions must be manually ported to the Antigravity Plugin format.

---
*Maintained by Antigravity CLI (formerly Gemini CLI).*
