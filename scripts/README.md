~/Desktop/Projects/                     # Monorepo — ~40 projects
├── scripts/                            # <<< CURRENT WORKSPACE
│   ├── 📈 AlphaEdge Market Intelligence
│   │   ├── collector.py                # Upstox + Yahoo → 10-factor signals → alphaedge.db
│   │   ├── alphaedge_db.py             # SQLite schema + CRUD
│   │   ├── api_server.py               # FastAPI REST :8765
│   │   ├── market_analysis_v3.py       # Legacy monolith + OI collector thread
│   │   ├── market_analysis_v2.py       # Older version
│   │   ├── market_engine.py            # Async engine for crypto (aiohttp)
│   │   ├── report_and_send.py          # Report + Telegram delivery
│   │   ├── run_analysis_headless.py    # Stdout-only analysis
│   │   └── frontend/
│   │       ├── dashboard.html          # Chart.js dashboard
│   │       ├── pixi_dashboard.html     # PixiJS options chain viz
│   │       ├── app.js                  # Dashboard logic
│   │       └── style.css
│   │
│   ├── 🪙 Crypto Intelligence
│   │   ├── crypto_dashboard.py         # BTC/ETH/SOL Rich dashboard (15s)
│   │   ├── crypto_market_dashboard_v2.py
│   │   └── crypto_market_dashboard.py
│   │
│   ├── 🔍 Exa AI Event Search
│   │   ├── exa_ai_search.py
│   │   ├── exa_ai_agents.py
│   │   └── ai_news_reporter.py         # Posts to Slack
│   │
│   ├── 📰 NotebookLM Pipelines
│   │   ├── telegram_to_notebooklm.py   # Telegram PDF → NotebookLM → all artifacts → Slack
│   │   ├── youtube_to_notebooklm.py   # YouTube channel monitor → NotebookLM → Slack
│   │   ├── youtube_channels.json       # Config: YouTube channel @handles
│   │   ├── toddle_notebooklm_sync.py   # Orchestrator: Toddle school notes → NotebookLM
│   │   ├── toddle_all_inventory.py     # Inventory all Toddle subject files
│   │   ├── toddle_bulk_download.py     # Download new/changed Toddle files
│   │   ├── toddle_bulk_convert.py      # Convert Toddle files to markdown
│   │   ├── sync_state.json             # Toddle sync state (per-subject timestamps)
│   │   └── cron_watchdog.py            # Cron failure monitor → Slack alerts
│   │
│   ├── 📊 PKScreener NSE Scanner
│   │   └── pkscreener_runner.py
│   │
│   ├── 🖥️ Terminal Dashboards
│   │   ├── options_cli.py             # Rich live option chain (5s, no flicker)
│   │   ├── live_market_dashboard.py
│   │   ├── alphaedge_pro.py
│   │   ├── metals_dashboard.py
│   │   └── fo_breakout_scanner.py
│   │
│   ├── 📂 Strategies
│   │   └── nifty200_momentum.py        # Nifty 200 momentum scanner (results via /api/strategies/)
│   │
│   ├── 🔧 Utilities
│   │   ├── send_slack.py / debug_telegram.py
│   │   ├── pnl_poller.py               # Multi-broker P&L aggregator (live + mock fallback)
│   │   ├── scaffold_agent.py           # Production AI agent scaffolder from templates/
│   │   ├── probe_pcr_pain.py / patch_market*.py
│   │   ├── report_and_summary.py / run_and_send_v2.py
│   │   └── youtube_video_search.py
│   │
│   ├── 📁 Config / Runtime
│   │   ├── AGENTS.md / CLAUDE.md / GEMINI.md / README.md / TODO.md
│   │   ├── alphaedge.db / intraday_oi.db / intraday_options_cli.db
│   │   ├── frontend/ / tests/ / logs/ / docs/ / scratch/
│   │   ├── venv/ / .env / .gitignore
│   │   └── alphaedge-api.service / multica-daemon.service
│   │
│   └── 🧪 Tests
│       ├── test_crypto_dashboard.py
│       └── test_indicators.py
│
├── AlphaEdge_Ticker/                   # tkinter desktop ticker (crypto + NSE)
├── AlphaEdge_NSE_Ticker/               # tkinter NSE options chain ticker
├── Alphaedge_Copy/                     # Multi-platform copy trading bot
├── btcusdt-futures-bot/                # Hyperliquid BTC paper trading
├── crypto-trending-oi/                 # Multi-factor crypto OI scoring
├── tradingview-mcp/                    # MCP server → TradingView CDP
├── open-codesign/                      # Electron AI design agent (pnpm/TS)
├── open-design/                        # Open-source Claude Design alt
├── crewai_testing/                     # CrewAI sandbox
├── hello-reasoner/                     # AgentField scaffold
├── daily_crypto_news/                  # CrewAI daily market reports
├── alphaedge-journal/                  # Next.js trading journal
├── pkscreener/                         # NSE stock screener (external)
├── Polymarket_Claude/                  # Polymarket prediction market agent
├── AI-Agentic-Security/                # Security research
├── Claude_Com_playbook/                # Claude playbook
├── ... 12 more dirs                    # misc: data, docs, pdf, etc.

# Scripts Repository

Comprehensive collection of scripts for Market Intelligence, AI Search, and automated reporting.

## 🚀 Script Index

### 📈 AlphaEdge Market Intelligence
*A decoupled, 10-factor market intelligence system for Indian Indices (NIFTY, SENSEX, BANKNIFTY).*

| Script | Description |
|:--- |:--- |
| `collector.py` | **Core Engine**. Fetches market data from Upstox/Yahoo, calculates 10-factor signals, and saves to DB. |
| `alphaedge_db.py` | **Database Manager**. Handles SQLite schema and data persistence for `alphaedge.db`. |
| `alert_dashboard_alive.py` | **Dashboard Uptime Monitor**. Cron-friendly uptime monitor — checks `/`, `/pixi`, `/api/latest`, `/api/gainers-losers` every 5 min. Silent when healthy; alerts Slack on 2+ consecutive failures plus recovery. State tracked in `/tmp/alert_dashboard_state.json`. |
| `api_server.py` | **API & Dashboard**. FastAPI backend serving market data and hosting the HTML dashboard on port 8765. Endpoints: `/api/latest`, `/api/history`, `/api/gainers-losers` (30s cache), `/api/portfolio/pnl` (multi-broker via `pnl_poller.py`), `/api/pixi/*` (options chain), `/api/strategies/nifty200-momentum`. |
| `market_engine.py` | Orchestrates the analysis flow for market signals. |
| `market_analysis_v3.py` | Latest version of core logic with **Auto-Refresh Terminal Dashboard**. |
| `run_analysis_headless.py` | CLI tool to run analysis and output results to console only. |
| `report_and_send.py` | Generates diagnostic reports and sends them to Telegram. |
| `options_cli.py` | **Advanced Options Dashboard**. Multi-index (Nifty, Sensex, BankNifty) Rich live terminal view. Shows Spot + Futures with OHLC (O/H/L/C) headers, strategy flags (OH/OL), human-readable OI (L/C), and ATM ± 300 strikes. **Lean, compressed layout (107 chars)** for small terminal windows. Zero-flicker rendering via `rich.live.Live` with alternate screen buffer. 5s polling, daily-reset SQLite. |

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

### 📰 Beat the Street — NotebookLM Daily Pipeline
*Automated daily pipeline: fetches PDFs from Telegram, uploads to NotebookLM, generates all artifact types, delivers to Slack, then cleans up.*

| Script | Description |
|:--- |:--- |
| `telegram_to_notebooklm.py` | **Daily Pipeline** (7 steps). Fetches PDFs from `@btsreports` (last 24h) → creates dated NotebookLM notebook → uploads sources → generates 5 artifacts (report, mind-map, infographic, quiz, podcast) → sends all to Slack via `format_file_for_slack()` → deletes notebook. Saves to `notebooklm_output/Beat-the-street-report-YYYY-MM-DD/`. Runs at **4PM IST** via cron. |
| `cron_watchdog.py` | **Cron Failure Monitor**. Parses cron logs via byte-offset tracking, detects tracebacks/ERROR/CRITICAL, alerts Slack. Runs at `:15` hourly. |

**Setup:**
```bash
# Install dependencies
venv/bin/pip install telethon python-dotenv
pipx install notebooklm-py

# Authenticate Telegram (one-time, interactive)
venv/bin/python - <<'EOF'
import asyncio
from telethon import TelegramClient
import os; from dotenv import load_dotenv; load_dotenv()
async def auth():
    client = TelegramClient('tg_session', int(os.environ['TELEGRAM_API_ID']), os.environ['TELEGRAM_API_HASH'])
    await client.start()
    await client.disconnect()
asyncio.run(auth())
EOF

# Authenticate NotebookLM (one-time, browser)
notebooklm login

# Run manually
PYTHONUNBUFFERED=1 venv/bin/python telegram_to_notebooklm.py
```

**Cron (already installed):**
```
30 10 * * *  cd /path/to/scripts && PYTHONUNBUFFERED=1 venv/bin/python telegram_to_notebooklm.py >> notebooklm_output/cron.log 2>&1
15 * * * *    cd /path/to/scripts && PYTHONUNBUFFERED=1 venv/bin/python cron_watchdog.py 2>&1
```

**Pipeline steps:**
1. Fetch PDFs from Telegram channel (last 24h)
2. Create NotebookLM notebook (`Beat-the-street-report-YYYY-MM-DD`)
3. Upload PDFs as notebook sources
4. Generate 5 artifacts: report (`.md`), mind-map (`.json`), infographic (`.png`), quiz (`.json`), podcast (`.mp3`)
5. Save artifacts to `notebooklm_output/` per-date directory
6. Send all artifacts to Slack (generic: `.md` = summary+full, `.json` = tree or raw, `.csv`, binary files noted)
7. Delete NotebookLM notebook from cloud

**Output:**
```
notebooklm_output/
├── pdfs/                                    # cached PDFs
├── Beat-the-street-report-YYYY-MM-DD/
│   ├── report.md                            # briefing-doc (full text)
│   ├── mindmap.json                         # mind-map (nested tree JSON)
│   ├── infographic.png                      # visual infographic
│   ├── quiz.json                            # quiz questions
│   └── podcast.mp3                          # audio podcast
└── cron.log                                 # daily run log
```

**Config (`.env`):**
```
TELEGRAM_API_ID=...
TELEGRAM_API_HASH=...
TELEGRAM_CHANNELS=@btsreports
DAYS_BACK=1
PDF_LIMIT=20
SLACK_WEBHOOK_URL=...
```

---

### 🎓 Toddle → NotebookLM
*Daily sync of school subject notes from Toddle LMS to NotebookLM study guides.*

| Script | Description |
|:--- |:--- |
| `toddle_notebooklm_sync.py` | **Orchestrator** (4 phases). Inventory → Download → Convert → Upload to NotebookLM + generate study guides. State tracked in `sync_state.json`. Skips subjects with no changes since last sync. |
| `toddle_all_inventory.py` | Inventories all subject files from Toddle LMS. |
| `toddle_bulk_download.py` | Downloads new/changed Toddle files. |
| `toddle_bulk_convert.py` | Converts files to markdown in `output/text/<subject>/`. |

**Subjects tracked:** Physics, Chemistry, Mathematics, English, Biology, History, Geography, Spanish, Design, Visual Arts

```bash
venv/bin/python toddle_notebooklm_sync.py
venv/bin/python toddle_notebooklm_sync.py --skip-inventory --skip-download  # convert + upload only
```

---

### 🤖 YouTube → NotebookLM
*Monitors YouTube channels for new videos, ingests each into NotebookLM, and delivers reports to Slack via Block Kit.*

| Script | Description |
|:--- |:--- |
| `youtube_to_notebooklm.py` | **Pipeline**. Checks tracked YouTube channels for videos published ≤24h ago, uploads each to a standalone NotebookLM notebook, generates `briefing-doc` report + mind-map, converts mind-map JSON to indented text tree, and sends a structured **Block Kit** Slack message. Safely deletes the notebook after successful Slack delivery. |
| `youtube_channels.json` | **Config**. JSON array of YouTube channel @handles to monitor. |

**Channels tracked (default):** `@DavidOndrej`, `@AkshatZayn`, `@TheNextNewThingAI`, `@LewisWJackson`

**CLI channel management:**
```bash
python3 youtube_to_notebooklm.py --add-channel @NewChannel
python3 youtube_to_notebooklm.py --remove-channel @OldChannel
python3 youtube_to_notebooklm.py --list-channels
```

**Slack output format (Block Kit):**
1. **Header** with pipeline name
2. **Fields** — channel handle + NotebookLM notebook link
3. **Video link**
4. **Divider**
5. **Mind-map** (indented text tree, ≤25 lines, in code block)
6. **Divider**
7. **Report** (first ~2,500 chars; remainder in continuation messages)

**Cron (already installed):**
```
30 11 * * * cd /path/to/scripts && python3 youtube_to_notebooklm.py >> logs/youtube_nlm_cron.log 2>&1
```

**Notebook safety:** Notebooks are deleted ONLY after successful Slack delivery. Deletion is regex-gated (`^[a-zA-Z0-9][a-zA-Z0-9_-]{19,}$`) and `_delete_notebook()` is the sole function authorized to call `notebooklm delete`.

---

### 💼 Portfolio P&L Dashboard
*Multi-broker portfolio aggregator with live/mock fallback.*

| Script | Description |
|:--- |:--- |
| `pnl_poller.py` | **P&L Aggregator**. Polls Upstox, Dhan, TradeSmart (Noren OMS), Fyers, Hyperliquid, Exness, and Binance APIs. Falls back to a dynamic mock (sinusoidal fluctuation) per broker when credentials are missing or return 401/403. Exposed at `GET /api/portfolio/pnl`. The endpoint never fails — always returns data. |

---

### 📂 Strategies
*Market scanning strategies with REST API exposure.*

| Script | Description |
|:--- |:--- |
| `strategies/nifty200_momentum.py` | **Nifty 200 Momentum Scanner**. Runs at 3:00 AM and 1:00 PM IST on weekdays. Results exposed at `GET /api/strategies/nifty200-momentum`. |

---

### 🛠️ Agent Scaffolder

| Script | Description |
|:--- |:--- |
| `scaffold_agent.py` | **Production Agent Scaffolder**. Copies `templates/production-agent/` to a new directory, substitutes `{{AGENT_NAME}}` placeholders in all files, and initialises a git repo. |

```bash
python3 scaffold_agent.py --name "Market Assistant"
python3 scaffold_agent.py --name "My Bot" --dest /path/to/dest
```

---

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
| `cron_watchdog.py` | Cron failure monitor — parses cron logs byte-offset, detects tracebacks, alerts Slack. State in `~/.opencode/cron_watchdog_state.json`. |
| `alert_dashboard_alive.py` | Dashboard uptime monitor — checks `/`, `/pixi`, `/api/latest`, `/api/gainers-losers` every 5 min, alerts Slack on outage. |
| `send_telegram.py` | Generic utility to send messages via Telegram Bot API. |
| `git-autosync.sh` | Shell script for automated git staging, committing, and pushing. |
| `patch_market.py` | Utility to apply specific logic patches to the market analysis scripts. |
| `clawdi` | **Environment Sync**. Cross-agent sync for sessions, skills, and secrets (Clawdi Cloud). |
| `crontab-viz` | **Crontab Visualizer**. Pretty-prints `crontab -l` with UTC→IST conversion, human-readable schedule, next run times, monthly calendar, and weekly grid. Run: `./crontab-viz` or alias `crons`. |

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

**Cron (every 5 min, already installed):**
```
*/5 * * * * cd /home/vreddy1/Desktop/Projects/scripts && PYTHONUNBUFFERED=1 venv/bin/python alert_dashboard_alive.py >> logs/alert_dashboard.log 2>&1
```

---

## 🏗️ AlphaEdge Architecture

1. **Data Collector**: Runs signals (Trend, VIX, OI Skew, PCR, Max Pain) and writes to `alphaedge.db`.
2. **Database**: SQLite storage for historical snapshots.
3. **API Server**: Connects to DB; serves `/api/latest`, `/api/history`, `/api/gainers-losers`, `/api/pixi/*`, `/api/portfolio/pnl` (multi-broker via `pnl_poller.py`), `/api/strategies/nifty200-momentum`. Macro data from Yahoo Finance with 5-min cache.
4. **Dashboard**: HTML/JS frontend in `frontend/` — main dashboard (`dashboard.html`) with portfolio, macro cards, gainers/losers, and Chart.js signal charts. PixiJS options chain viz at `/pixi`.
5. **P&L Poller** (`pnl_poller.py`): Aggregates 7 brokers (Upstox, Dhan, TradeSmart, Fyers, Hyperliquid, Exness, Binance). Live API → mock fallback per broker. Never errors.

---

## 🛠️ Setup

### Python Environments

Two separate venvs — use the correct one:

| Venv | Path | Used by |
|------|------|---------|
| Main | `venv/` (project root) | api_server, collector, telegram/youtube/toddle pipelines, watchdog, alert_dashboard |
| PKScreener | `/home/vreddy1/Desktop/Projects/pkscreener_venv` | `pkscreener_runner.py` only |

System Python 3.13/3.14 blocks global installs. Use venv or `--break-system-packages`:

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

### 🤖 Antigravity CLI — AI Agent IDE
*VS Code-based agent CLI with `chat` mode (ask/edit/agent). Replaces Gemini CLI.*

**Version:** v2.0.6 (Electron, `/usr/share/antigravity/`)
**Binary:** `/usr/bin/antigravity` → launcher → `antigravity` (ELF, 197MB)

**Usage:**
```bash
antigravity --version
antigravity chat "prompt"                        # agent mode
antigravity chat --mode ask "question"           # Q&A mode
antigravity chat --mode edit "change this"       # edit mode
```

**Upgrade:**
Download latest tar.gz, extract, then:
```bash
sudo cp extracted/Antigravity-x64/antigravity /usr/share/antigravity/
sudo cp extracted/Antigravity-x64/*.so /usr/share/antigravity/
sudo cp extracted/Antigravity-x64/*.pak /usr/share/antigravity/
sudo cp extracted/Antigravity-x64/*.bin /usr/share/antigravity/
sudo cp extracted/Antigravity-x64/icudtl.dat /usr/share/antigravity/
```

---

### 📡 Crypto Daily News — AI-Powered Crypto Briefing

*Daily crypto news summaries across 8 categories, delivered to Telegram at 8:00 AM IST.*

| Script | Description |
|:--- |:--- |
| `crypto_news_search.py` | Fetches top crypto stories via Exa API for BTC, ETH, SOL, RWA, Stablecoins, Onchain, Growth, and Price & Predictions. Each article gets an AI-generated 1-sentence summary. |
| `crypto_to_notebooklm.py` | Wraps `crypto_news_search.py --report` → creates NotebookLM notebook → generates infographic → sends to Telegram. Used by cron at 8AM IST. |

**Features:**
- 8 curated search topics with Exa's neural search (last 3 days)
- AI-generated summaries per article (no links to click)
- Rich terminal dashboard mode (`--report`)
- NotebookLM infographic pipeline: news → bento-grid PNG → Telegram

**Usage:**
```bash
# Terminal report
python3 crypto_news_search.py --report --num 10

# Full infographic pipeline (with Telegram delivery)
python3 crypto_to_notebooklm.py --telegram
```

**Cron (8:00 AM IST, already installed):**
```
0 8 * * * cd /home/vreddy1/Desktop/Projects/scripts && python3 crypto_to_notebooklm.py --telegram >> logs/crypto_news_cron.log 2>&1
```

**Config (`.env`):**
```
EXA_API_KEY=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

---

### 📈 PKScreener — NSE Automated Stock Scanner

Automated NSE stock screening using [PKScreener](https://github.com/pkjmesra/PKScreener) with Telegram delivery.

**Setup**
```bash
# Python 3.12 venv at:
/home/vreddy1/Desktop/Projects/pkscreener_venv

# PKScreener repo at:
/home/vreddy1/Desktop/Projects/pkscreener

# Wrapper script:
python3 pkscreener_runner.py
```

**Scan Strategies** (8 scans, runs on weekdays):
| Scan | Options |
|------|---------|
| Nifty50 — Probable Breakouts | X:1:1 |
| Nifty50 — Bullish RSI & MACD | X:1:13 |
| Nifty50 — Strong Buy Signals | X:1:44 |
| NiftyAll — Probable Breakouts | X:12:1 |
| NiftyAll — SuperTrend Uptrend | X:12:24 |
| NiftyAll — Strong Buy Signals | X:12:44 |
| NiftyAll — Breaking Out Now | X:12:23 |
| NiftyAll — Bullish RSI & MACD | X:12:13 |

**Cron Schedule** (IST, weekdays only):
```
55 3  * * 1-5   # 9:25 AM IST  — pre-open scan
5  10 * * 1-5   # 3:35 PM IST  — close-of-day scan
30 12 * * 1-5   # 6:00 PM IST  — evening review
```

**Lockfile**: `/tmp/pkscreener_runner.lock` — prevents overlapping cron runs via `fcntl.flock`. If a new cron fires while a previous run is in progress, it exits immediately.

**Orphan guard**: `run_scan()` uses `start_new_session=True` to isolate subprocesses in their own process group and kills the entire group (`os.killpg`) with `SIGTERM` → `SIGKILL` escalation. This prevents worker subprocesses from surviving as orphans when a scan times out or crashes. A `kill_orphan_pkscreener()` call at startup `pkill -9`s any leftover processes from prior crashed runs, preventing the 85-process / 12GB pileup issue.

**Output**: `pkscreener_output/` — per-scan `.txt` logs + Telegram delivery with LTP & % change

**Live LTP**: Each stock symbol is followed by its current price and change via Yahoo Finance (e.g. `ADANIENT  ₹2,345.67 (+1.23%)`). Uses `v8/finance/chart` with parallel `ThreadPoolExecutor` (max 10 workers) — 30 stocks resolve in ~1-2s. Gracefully falls back to bare symbol if Yahoo is unreachable. No new dependencies or env vars required.

## OpenCode `/pursue` Goal Plugin

Location: `~/.config/opencode/plugins/opencode-goal/`

Autonomous goal pursuit mode for OpenCode. Agent self-evaluates and iterates until verification condition is proven met.

**Usage in OpenCode TUI:**
```
/pursue <objective with verification condition>
```

**Components:**
| Component | Location |
|-----------|----------|
| Plugin (4 tools + 2 hooks) | `~/.config/opencode/plugins/opencode-goal/src/` |
| Config (agent + command) | `~/.config/opencode/opencode.jsonc` |
| State file | `~/.opencode/goals/state.json` |

**Tools:** `goal_define`, `goal_checkpoint`, `goal_status`, `goal_complete`

**Hooks:** `experimental.chat.system.transform` (injects evaluator prompt when goal active), `experimental.compaction.autocontinue` (re-enables agent loop while pursuing)

**Agent:** Claude Sonnet 4, 100 steps, unrestricted perms

See `~/.config/opencode/plugins/opencode-goal/src/index.js` for full implementation.

---
*Maintained by Antigravity CLI (formerly Gemini CLI).*
