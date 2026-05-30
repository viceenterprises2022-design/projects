# Reverse Specification: ~/Desktop/Projects/scripts

## 1. Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.13+ |
| Web framework | FastAPI (uvicorn, port 8765) |
| Database | SQLite (4 DBs: `alphaedge.db`, `intraday_oi.db`, `intraday_options_cli.db`, `strategies/strategies.db`) |
| Terminal UI | Rich library |
| Frontend | Vanilla HTML/CSS/JS, Chart.js, PixiJS |
| Notifications | Slack (Incoming Webhook + Block Kit), Telegram Bot API |
| Async HTTP | aiohttp, requests |
| Finance APIs | Upstox REST (bearer JWT), Yahoo Finance (yfinance), Binance REST, Deribit |
| AI/LLM APIs | Exa API, NotebookLM CLI (`notebooklm-py`), OpenAI SDK |
| Pipelines | cron-driven, systemd services |

## 2. Module/Directory Structure

```
scripts/
├── collector.py                  # AlphaEdge: Upstox + Yahoo → 10-factor signals → alphaedge.db
├── alphaedge_db.py               # AlphaEdge: SQLite CRUD helpers for alphaedge.db
├── api_server.py                 # AlphaEdge: FastAPI REST server on :8765 (15 endpoints)
├── market_analysis_v3.py         # Legacy: terminal dashboard + background OI collector thread
├── market_analysis_v2.py         # Legacy: older version
├── market_engine.py              # Crypto: async engine (aiohttp) for Binance/Deribit/Yahoo data
├── crypto_dashboard.py           # scratch/ → Crypto: Rich live BTC/ETH/SOL dashboard (15s poll)
├── crypto_market_dashboard_v2.py # scratch/ → Crypto: 3-column diagnostic variant
├── crypto_intel_reporter.py      # CMC Skill Hub → Telegram daily/weekly crypto intel reports
├── crypto_news_search.py         # Exa-powered daily crypto news (8 categories) → Telegram
├── crypto_to_notebooklm.py       # Crypto news → NotebookLM infographic → Telegram
├── options_cli.py                # Live 5s-polling Rich terminal option chain
├── oi_collector_daemon.py        # Wrapper: market_analysis_v3 OI collector as standalone daemon
├── pkscreener_runner.py          # PKScreener: 8 NSE scans → Telegram (flock-guarded)
├── pnl_poller.py                 # Multi-broker P&L aggregator (Upstox/Dhan/TradeSmart/Fyers + crypto)
├── probe_pcr_pain.py             # Put-Call Ratio / Max Pain probe
├── fo_breakout_scanner.py        # F&O breakout scanner
├── metals_dashboard.py           # Gold/Silver terminal dashboard
├── live_market_dashboard.py      # Live market terminal dashboard
├── alphaedge_pro.py              # Enhanced AlphaEdge dashboard
├── scaffold_agent.py             # Production AI agent scaffolder from templates/
│
├── telegram_to_notebooklm.py     # Telegram PDFs → NotebookLM → briefing/mind-map → Slack
├── youtube_to_notebooklm.py      # YouTube channels → NotebookLM → briefing/mind-map → Slack
├── youtube_video_search.py       # YouTube keyword/channel search
├── youtube_channels.json         # Config: channel @handles for YouTube pipeline
│
├── exa_ai_search.py              # Exa-powered AI event search → JSON
├── exa_ai_agents.py              # Exa-powered agent search
├── ai_news_reporter.py           # AI news/events → Slack
│
├── send_slack.py                 # Slack Block Kit message sender
├── debug_telegram.py             # Telegram debug helper
├── send_telegram_msg.py          # Telegram message sender
├── report_and_send.py            # Analysis → Telegram
├── run_analysis_headless.py      # Stdout-only analysis
├── report_and_summary.py         # Analysis + summary report
├── run_and_send_v2.py            # Run + Telegram delivery v2
├── cron_watchdog.py              # Cron failure monitor → Slack alerts
├── alert_dashboard_alive.py      # Dashboard uptime monitor
│
├── frontend/                     # Static dashboard files
│   ├── dashboard.html            # Main Chart.js dashboard (GET /)
│   ├── pixi_dashboard.html       # PixiJS options chain (GET /pixi)
│   ├── market.html               # Market overview (GET /market)
│   ├── portfolio.html            # Portfolio P&L (GET /portfolio)
│   ├── holdings.html             # Holdings view (GET /holdings)
│   ├── positions.html            # Positions view (GET /positions)
│   ├── app.js                    # Dashboard logic
│   └── style.css
│
├── strategies/
│   ├── nifty200_momentum.py      # Nifty 200 momentum scanner
│   └── nifty200_momentum_report.json  # Scanner output
│
├── scratch/                      # CMC Skill Hub analysis scripts + outputs
│   ├── crypto_dashboard.py       # Full crypto dashboard with CMC integrations
│   ├── crypto_market_dashboard_v2.py
│   └── run_*.py                  # Per-skill analysis runners (perp, macro, etf, etc.)
│
├── tests/
│   ├── test_crypto_dashboard.py
│   └── test_indicators.py
│
├── templates/                    # Agent scaffold templates
├── docs/                         # Documentation files
├── specs/                        # Generated specs (this file)
│
├── AGENTS.md                     # Agent session memory & project map
├── CLAUDE.md                     # Claude Code guidance
├── GEMINI.md                     # Gemini Code Assist guidance
├── README.md                     # Project overview
├── TODO.md                       # Pending tasks
├── .env                          # Secrets (not committed)
│
├── alphaedge.db                  # Main market data DB
├── intraday_oi.db                # Intraday OI trend DB
├── intraday_options_cli.db       # Intraday option chain DB
│
├── alphaedge-api.service         # systemd unit for API server
├── multica-daemon.service        # systemd unit for Multica agents
│
└── logs/                         # Runtime logs
```

## 3. Observed Requirements (EARS Format)

### 3.1 AlphaEdge Market Intelligence

| ID | Type | Requirement |
|----|------|------------|
| AE-01 | Ubiquitous | The system shall collect market data for NIFTY, SENSEX, and BANKNIFTY via Upstox REST API. |
| AE-02 | Ubiquitous | The system shall fetch macro data (VIX, DXY, Crude, US30, Gold, Silver) via Yahoo Finance. |
| AE-03 | Ubiquitous | The system shall compute a 10-factor signal score (Trend, DJ, VIX, OI Skew, VWAP, SuperTrend, RSI, DXY, Crude, PCR). |
| AE-04 | Ubiquitous | Each factor shall be scored -1/0/+1. Score ≥6 → BUY, ≤4 → SELL, else NEUTRAL. |
| AE-05 | Ubiquitous | The system shall persist snapshots to `alphaedge.db` via `alphaedge_db.py`. |
| AE-06 | Event-driven | When `--loop` flag is provided, the system shall re-collect at `--interval N` minutes. |
| AE-07 | Ubiquitous | The API server shall expose endpoints on port 8765 via FastAPI. |
| AE-08 | Ubiquitous | The API shall serve static frontend files from `frontend/`. |
| AE-09 | Event-driven | When `/api/latest` is called, the system shall return the most recent snapshot with live macro data merged. |
| AE-10 | Event-driven | When `/api/history?sym=X&days=N` is called, the system shall return time-series rows for Chart.js. |
| AE-11 | Ubiquitous | The API shall expose 6 PixiJS endpoints for options chain data: `/api/pixi/chain`, `/api/pixi/oi-trend`, `/api/pixi/signal`, `/api/pixi/macro`, `/api/pixi/strike-history`, `/api/pixi/oi-surface`. |
| AE-12 | Ubiquitous | The system shall detect stale data (>5 min) and return `stale: true` in API responses. |

### 3.2 Crypto Intelligence

| ID | Type | Requirement |
|----|------|------------|
| CI-01 | Ubiquitous | The system shall fetch BTC, ETH, and SOL data from Binance (spot + futures + depth) and Deribit (options). |
| CI-02 | Ubiquitous | The crypto dashboard shall poll every 15 seconds and display via Rich terminal UI. |
| CI-03 | Ubiquitous | The dashboard shall show 10-level order book depth with buy/sell breakdown. |
| CI-04 | Ubiquitous | The dashboards shall integrate CMC Skill Hub outputs: perpetual analysis, cross-asset correlation, ETF demand, sector rotation, macro news, macro liquidity. |
| CI-05 | Ubiquitous | `crypto_intel_reporter.py` shall execute 14 CMC Skill Hub skills (6 daily + 8 weekly) and send formatted Telegram reports. |
| CI-06 | Ubiquitous | The crypto news pipeline shall search 8 news categories via Exa API daily. |

### 3.3 NotebookLM Pipelines

| ID | Type | Requirement |
|----|------|------------|
| NL-01 | Event-driven | When run daily, `telegram_to_notebooklm.py` shall fetch PDFs from `@btsreports` Telegram channel. |
| NL-02 | Ubiquitous | The pipeline shall upload PDFs to a dated NotebookLM notebook. |
| NL-03 | Ubiquitous | The pipeline shall generate a briefing report artifact and a mind-map artifact. |
| NL-04 | Ubiquitous | The pipeline shall save artifacts to `notebooklm_output/YYYY-MM-DD/`. |
| NL-05 | Ubiquitous | `youtube_to_notebooklm.py` shall monitor configured channels for videos ≤24h old. |
| NL-06 | Ubiquitous | YouTube pipeline shall deliver Block Kit reports to Slack and delete the notebook after successful delivery. |
| NL-07 | Ubiquitous | YouTube pipeline shall support CLI channel management (`--add-channel`, `--remove-channel`, `--list-channels`). |

### 3.4 PKScreener NSE Scanner

| ID | Type | Requirement |
|----|------|------------|
| PK-01 | Ubiquitous | The system shall execute 8 predefined NSE scan strategies via `pkscreenercli.py`. |
| PK-02 | Ubiquitous | The system shall run scans in parallel using `ThreadPoolExecutor`. |
| PK-03 | Ubiquitous | The system shall deliver aggregated scan results via Telegram. |
| PK-04 | Ubiquitous | The system shall enforce a `fcntl.flock` mutex to prevent overlapping cron runs. |
| PK-05 | Ubiquitous | Scans shall time out after 300 seconds per scan. |

### 3.5 P&L Portfolio

| ID | Type | Requirement |
|----|------|------------|
| PL-01 | Ubiquitous | The system shall aggregate P&L from Upstox, Dhan, TradeSmart, Fyers, Hyperliquid, Exness, and Binance. |
| PL-02 | Ubiquitous | The system shall fall back to mock data when live broker APIs are unavailable. |
| PL-03 | Ubiquitous | The `/api/portfolio/pnl` endpoint shall return aggregated portfolio data. |

### 3.6 Slack/Telegram Notifications

| ID | Type | Requirement |
|----|------|------------|
| SN-01 | Ubiquitous | `send_slack.py` shall support Slack Block Kit (header, section, fields, context, divider, code_section). |
| SN-02 | Ubiquitous | The system shall support color-coded messages (good/warning/danger/info). |
| SN-03 | Ubiquitous | Messages exceeding 50 blocks shall be chunked into multiple Slack messages. |
| SN-04 | Ubiquitous | Pure `--text` mode shall remain backward-compatible with flat text Slack messages. |

## 4. Non-Functional Observations

| Category | Observation | Evidence |
|----------|------------|----------|
| Data freshness | Macro data fetched live from Yahoo Finance on each `/api/latest` call; stale flag based on 5 min threshold | `api_server.py:156-157` |
| Concurrency | SQLite connections use WAL mode + `check_same_thread=False` for concurrent access | `options_cli.py:52-53`, `api_server.py:53` |
| Caching | Gainers/losers cached for 30s, live macro for 5 min | `api_server.py` |
| Systemd | Two user-level systemd services: alphaedge-api (uvicorn), multica-daemon | `.service` files |
| Secrets | Tokens sourced from `.env` file and environment variables — never committed | `.env`, `os.environ.get()` |
| Python envs | Two venvs: `venv/` (main), `pkscreener_venv` (PKScreener only) | `CLAUDE.md` |

## 5. Inferred Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-01 | Running `collector.py --loop --interval 5` shall produce new rows in `alphaedge.db` every 5 minutes. |
| AC-02 | Starting `api_server.py` shall make `http://localhost:8765/api/latest` return valid JSON with symbols + macro. |
| AC-03 | `GET /api/history?sym=NIFTY&days=30` shall return ≤30 days of intraday + daily rows. |
| AC-04 | Crypto dashboard shall display live BTC/ETH/SOL data with 15-second auto-refresh. |
| AC-05 | PKScreener runner shall complete all 8 scans and deliver a single Telegram summary message. |
| AC-06 | NotebookLM pipelines shall create notebooks, generate artifacts, and deliver results without manual intervention. |
| AC-07 | `send_slack.py --header "Test" --field "Status: OK" --color good` shall produce a green Slack message. |

## 6. Uncertainties and Questions

1. **Toddle scripts** — 12 `toddle_*.py` files for school management system. Not explored in depth; appear to be a separate NotebookLM sub-pipeline for Toddle (school) content. Need to verify integration with main NotebookLM pipeline.

2. **`patch_market*.py`** — Three scripts (`patch_market_no_claude.py`, `patch_market_trending.py`, `patch_market.py`). Purpose unclear from directory listing — likely DB patch/data migration scripts.

3. **`everything-claude-code/`** — Referenced as embedded project/reference tree. Not explored.

4. **`astro_report.py`** — Purpose unclear from filename.

5. **`live_market_dashboard.py` vs `alphaedge_pro.py`** — Overlap with crypto/AlphaEdge functionality unclear.

6. **Scratch agent scaffold** — `scratch/coinmarketcap-agent/` appears as an agent scaffold project. Relationship to main pipeline unclear.

7. **`graphify-out/`** — Output from graphify knowledge graph tool; not a source file.

8. **`logs/` monitoring** — No log rotation or retention policy observed.

## 7. Recommendations

1. **Unify test framework** — Move from ad-hoc `tests/test_*.py` to `pytest` with proper conftest and fixtures.
2. **Add logging** — Several scripts lack structured logging; rely on `print()` statements.
3. **Document DB schemas** — `intraday_oi.db` and `intraday_options_cli.db` schemas are only defined at point of use.
4. **Consolidate dashboards** — `crypto_dashboard.py` lives in `scratch/` while `crypto_market_dashboard_v2.py` is at root — relocate.
5. **Secrets audit** — Hardcoded tokens found in `options_cli.py:13`, `pkscreener_runner.py:28`, `crypto_intel_reporter.py:11`, `youtube_to_notebooklm.py:31` — should be moved to `.env`.
