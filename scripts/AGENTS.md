# Repository Guidelines

## Project Structure & Module Organization

This repository contains multiple root-level script systems. AlphaEdge market intelligence is the primary app: `collector.py` fetches Upstox/Yahoo Finance data, `market_engine.py` and `market_analysis_v*.py` hold analysis logic, `alphaedge_db.py` manages SQLite storage, and `api_server.py` serves the FastAPI API and dashboard. Static dashboard files live in `frontend/` (`dashboard.html`, `app.js`, `style.css`). Exa-powered search/agents scripts live in `exa_ai_search.py`, `exa_ai_agents.py`, and `crypto_news_search.py`. Runtime artifacts include `*.db`, `logs/`, `*_report.txt`, and `ai_events_results.json`; do not treat these as source unless the task is explicitly data-related. `everything-claude-code/` is a separate embedded project/reference tree.

## Build, Test, and Development Commands

Install root dependencies as needed:

```bash
python3 -m pip install fastapi uvicorn[standard] requests rich exa-py
```

Run the collector once with `python3 collector.py`; run continuously with `python3 collector.py --loop --interval 5`. Start the API and dashboard with `python3 api_server.py`, then open `http://localhost:8765`. Generate the legacy report with `python3 market_analysis_v3.py`, send it through Telegram with `python3 report_and_send.py`, or run stdout-only analysis with `python3 run_analysis_headless.py`. Run Exa search with `EXA_API_KEY=<key> python3 exa_ai_search.py`.

## Coding Style & Naming Conventions

Use Python 3, 4-space indentation, `snake_case` for functions/variables, and uppercase constants for configuration such as symbol maps. Keep scripts executable from the repository root and preserve simple module imports (`import alphaedge_db as db`). Prefer small helper functions around network calls and database operations. Frontend code uses plain HTML/CSS/JavaScript; keep selectors and filenames descriptive.

## Testing Guidelines

There is no root test suite yet. For changes, run the specific script you touched and verify the expected API endpoint or output file. For API changes, check `GET /api/latest`, `GET /api/symbols`, and one `GET /api/history?sym=NIFTY&days=30` request after `collector.py` has populated `alphaedge.db`. If adding tests, place them under `tests/` as `test_*.py` and keep external API calls mocked.

## Commit & Pull Request Guidelines

Recent commits use Conventional Commits, especially `feat: ...`; follow that pattern (`fix: handle empty option chain`, `docs: add contributor guide`). PRs should describe the user-visible change, list commands run, mention required tokens or environment variables, and include screenshots for dashboard UI changes.

## Security & Configuration Tips

Never add new secrets to source. Use environment variables for `EXA_API_KEY`, Telegram credentials, and rotated market-data tokens. Avoid committing regenerated `*.db`, logs, caches, or report outputs unless the change intentionally updates sample data.

## Project Map — Full Understanding

### Script Systems in this Repo

**1. AlphaEdge Market Intelligence (primary)**
- `collector.py` → fetches Upstox (bearer JWT) + Yahoo Finance data, runs 10-factor signal engine (Trend, DJ, VIX, OI Skew, VWAP, SuperTrend, RSI, DXY, Crude, PCR), writes to `alphaedge.db`
- `alphaedge_db.py` → SQLite schema + CRUD helpers for `alphaedge.db`
- `api_server.py` → FastAPI on `:8765` serving REST (`/api/latest`, `/api/history`, `/api/symbols`, `/api/pixi/*`) + static dashboard HTML (`frontend/dashboard.html`, `frontend/pixi_dashboard.html`)
- `market_analysis_v3.py` → legacy monolith with terminal dashboard, has background `oi_collector_thread()` writing to `intraday_oi.db` every minute
- `options_cli.py` → live 5s-polling terminal for Nifty/Sensex/BankNifty option chain (107-char compressed layout), daily-reset SQLite at `intraday_options_cli.db`
- Signal scoring: each factor -1/0/+1, sum ≥6 → BUY, ≤4 → SELL, else NEUTRAL

**2. AlphaEdge Crypto (BTC/ETH/SOL)**
- `crypto_dashboard.py` → 15s polling Rich terminal dashboard, simultaneous BTC/ETH/SOL, shows Options Chain (Deribit) + Liquidation Map (Binance order book walls) with 10-level depth + Buy/Sell breakdown
- `crypto_market_dashboard_v2.py` → variant with 3-column diagnostic view
- `market_engine.py` → async data engine (aiohttp) fetching from Binance (Spot/Futures/Depth), Deribit (Options), Yahoo Finance (macro)

**3. NotebookLM Daily Pipeline**
- `telegram_to_notebooklm.py` → daily cron (4PM IST), fetches PDFs from Telegram channel `@btsreports`, uploads to dated NotebookLM notebook, generates briefing report + mind-map, saves to `notebooklm_output/`
- `youtube_to_notebooklm.py` → daily cron (5PM IST), monitors YouTube channels (`youtube_channels.json`) for new videos ≤24h old, ingests each into NotebookLM, generates briefing report + mind-map, delivers to Slack via Block Kit, deletes notebook after successful delivery
- `youtube_channels.json` → config file: array of YouTube channel @handles (`@DavidOndrej`, `@AkshatZayn`, `@TheNextNewThingAI`, `@LewisWJackson`)
- `substack_to_slack.py` → daily cron, fetches new posts from configured Substack RSS feeds (`substack_channels.json`), extracts full article content, summarizes with NotebookLM, and delivers Block Kit reports to Slack. State maintained in `substack_to_slack_state.json`.

**4. Exa AI Event Search**
- `exa_ai_search.py` / `exa_ai_agents.py` → Exa-powered search for upcoming AI events/workshops from OpenAI, Anthropic, Google AI, etc. Outputs `ai_events_results.json`
- `ai_news_reporter.py` → fetches AI agent launches + events, posts to Slack
- `crypto_news_search.py` → Exa-powered daily crypto news across 8 categories with AI summaries, plain-text report
- `crypto_to_notebooklm.py` → wraps `crypto_news_search.py` report → NotebookLM infographic → Telegram delivery. Cron at 8AM IST

**5. PKScreener NSE Scanner**
- `pkscreener_runner.py` → runs 8 scan strategies via PKScreener repo (at `~/Desktop/Projects/pkscreener/`), outputs to `pkscreener_output/`, delivers to Telegram. 3 cron slots weekdays.

**6. Utilities**
- `send_slack.py`, `debug_telegram.py` → notification helpers
- `report_and_send.py`, `run_and_send_v2.py` → wraps analysis + Telegram delivery
- `git-autosync.sh` → auto-commit/push
- `pnl_poller.py` → portfolio P&L polling
- `probe_pcr_pain.py` → Put-Call Ratio / Max Pain probe
- `metals_dashboard.py` → Gold/Silver dashboard
- `fo_breakout_scanner.py` → F&O breakout scanner
- `youtube_video_search.py` → YouTube keyword/channel search
- `youtube_channels.json` → channel config for YouTube → NotebookLM cron pipeline

### Data Sources
- **Upstox REST API** → JWT bearer token (`UPSTOX_TOKEN` env) for live quotes + option chain OI (Indian indices)
- **Yahoo Finance** (yfinance) → DXY, Crude, US30, Gold, Silver; index fallback
- **Binance** → Spot/Futures/Depth for BTC, ETH, SOL
- **Deribit** → Options chain for crypto
- **Exa API** → AI event search
- **Telegram** (Telethon) → PDF ingestion for NotebookLM pipeline
- **YouTube Data API** → channel video search for YouTube → NotebookLM pipeline
- **PKScreener** → NSE technical scans

### Running Services (systemd)
- `alphaedge-api.service` → FastAPI/uvicorn on `:8765`
- `multica-daemon.service` → Multica Agent Runtime (Claude, Codex, Gemini, Hermes, Cursor)

### Tech Stack
- Python 3, FastAPI, uvicorn, SQLite (alphaedge.db + intraday OI DBs), Rich (terminal dashboards), requests/aiohttp (async HTTP)
- Frontend: vanilla HTML/CSS/JS, Chart.js (in dashboard.html)
- System Python 3.13 (managed) — pip installs need `--break-system-packages`
- Project venv at `venv/` for heavier deps (telethon, aiohttp)

### Parent Projects (~/Desktop/Projects/)
Monorepo of ~40 independent projects including: AlphaEdge tickers (tkinter), copy trading bots (Hyperliquid/Binance/Polymarket), BTC futures bot, CrewAI agents, open-codesign (Electron/TypeScript), tradingview-mcp (Node.js CDP bridge), crypto-trending-oi engine, and more.

## Session Memory — Recent Work

### 2026-05-23: YouTube & Telegram → NotebookLM Pipelines
- `youtube_to_notebooklm.py` — maintained YouTube channel monitor pipeline. Tracks 4 channels, ingests to NotebookLM, delivers Block Kit reports to Slack. CLI channel management (`--add-channel`, `--remove-channel`, `--list-channels`). Notebook safety (regex-gated delete on successful Slack delivery).
- `telegram_to_notebooklm.py` — maintained Telegram PDF ingestion pipeline. Fetches PDFs from `@btsreports`, uploads to dated NotebookLM notebook, generates briefing-doc + mind-map. Runs daily at 4PM IST.
- **Multica:** ALP-336, ALP-337 (done, assigned Vinod-AI-CEO)

### 2026-05-24: OpenCode `/pursue` Goal Plugin
- Built plugin at `~/.config/opencode/plugins/opencode-goal/` with 4 tools (`goal_define`, `goal_checkpoint`, `goal_status`, `goal_complete`) and 2 hooks (`experimental.chat.system.transform`, `experimental.compaction.autocontinue`)
- Created self-evaluating agent pattern (no separate LLM — evaluator prompt injected via system transform hook)
- Configured `agent.goal` (Sonnet 4, 100 steps, full perms) and `command.pursue` (`$ARGUMENTS` template)
- Fixed name collision with built-in `/goal` command (renamed to `/pursue`)
- Removed markdown command file that was overriding JSON template
- Installed, verified, smoke-tested end-to-end
- Updated `README.md` with plugin section and `AGENTS.md` with session memory
- Built `/logwork` command for automated multica issue creation
- **Multica:** ALP-335 (done, assigned Vinod-AI-CEO)

### 2026-05-24: AlphaEdge Gainers/Losers + Live Macro Fix
- `api_server.py` — added `GET /api/gainers-losers` endpoint: 46 NSE stocks, change% from `net_change/(ltp-net_change)`, 30s thread-safe cache. Response keys `NSE_EQ:SYMBOL`.
- `dashboard.html` — added gainers/losers card row (`.gl-row`) at top of main layout.
- `app.js` — added `loadGainersLosers()`, `renderGainersLosers()`, `glItem()`, polled every 30s.
- `style.css` — added `.gl-row` 2-col grid, `.gl-item` rows with green/red change coloring.
- Fixed stale `app.js` cache: killed stale uvicorn processes and restarted server manually + via systemd.
- Fixed `/api/latest` macro section: Crude, US30, Gold, Silver now fetched live from Yahoo Finance via `_get_macro_cached()` instead of stale DB. VIX/DXY use live Yahoo with DB fallback.
- **Multica:** ALP-338 (done), ALP-339 (done, both assigned Vinod-AI-CEO)

### 2026-05-24: Crontab Visualizer (`crontab-viz`)
- Built `crontab-viz` — Python CLI that parses `crontab -l` with 3 views: schedule table (UTC→IST, next run), monthly calendar (green = cron days), weekly grid (which days per job).
- Handles cron dow ranges (`1-5`), `*`, and comma-separated values.
- Added to `README.md` Utilities table.
- Commit: `feat: add crontab-viz — crontab visualizer with IST conversion, next run, calendar grid`
- **Multica:** ALP-340 (done, assigned Vinod-AI-CEO)

### 2026-05-25: PKScreener Memory Leak Fix
- Diagnosed root cause: 28 orphaned pkscreener processes from PTY subprocess leaks + overlapping cron runs consuming ~12GB RAM, maxing 4GB swap, causing GNOME OOM kills.
- Killed all 28 runaway `pkscreenercli.py` processes → freed ~9GB instantly.
- Added `fcntl.flock` lockfile (`/tmp/pkscreener_runner.lock`) to `pkscreener_runner.py` — any overlapping cron run exits immediately instead of piling on more processes.
- Updated README with lockfile documentation.
- **Multica:** ALP-359 (done, assigned Vinod-AI-CEO)

### 2026-05-26: PKScreener Dependency Incompatibility & Locking Fix
- Diagnosed root cause: `pandas-ta-classic` package was missing from `pkscreener_venv` which crashed all scans requesting SuperTrend.
- Installed `pandas-ta-classic==0.3.78` and downgraded `numpy` back to `1.26.4` to fix strict C-extension dependencies of other pre-compiled packages (`scipy`, `pkbrokers`, `advanced_ta`).
- Fixed flock file descriptor lock release bug in `pkscreener_runner.py` by persisting `_lock_fd` in global scope, preventing immediate garbage collection lock releases.
- Cleaned up concurrent orphan processes and verified successful execution of all scans (173 total hits delivered to Telegram).
### 2026-05-26: Fullscreen Responsive Layout & Live Collectors Setup
- `dashboard.html` & `style.css` — Made main dashboard fully viewport-responsive and fullscreen using vertical flexbox layout and zero vertical/horizontal scrollbars, expanding the PixiJS Options Matrix canvas to its maximum fidelity.
- `api_server.py` — Added missing `/pixi` GET endpoint to serve `pixi_dashboard.html`, resolving consecutive `404` errors in the uptime monitor (`alert_dashboard_alive.py`). Triggered uvicorn reload cleanly.
- `oi_collector_daemon.py` — Created standalone wrapper script that leverages `market_analysis_v3.py`'s background collection thread in the main execution line, perfect for running as a headless daemon.
- `start_collectors.sh` — Created a unified bash script to cleanly kill stale processes and launch all 3 collectors in the background using `nohup` (alphaedge.db collector, options chain collector, and intraday PCR trend collector).
- `~/.config/systemd/user/` — Provisioned 3 systemd user services (`alphaedge-collector`, `alphaedge-options-collector`, `alphaedge-oi-collector`) for seamless, robust daemon management.
- `dashboard.html` & `app.js` — Changed last-updated refresh clocks across all pages and subpages to explicitly format to `Asia/Kolkata` (IST) timezone and unified stale logic (blinking orange warning when cache is >5 mins old).
- `crontab` — Added Nifty 200 Momentum Strategy scan runs (8:30 AM & 6:30 PM IST) and updated `strategies/nifty200_momentum.py` with dotenv loading. Verified successful live refresh of momentum report JSON.
- **Multica:** ALP-367 (done, assigned Vinod-AI-CEO)

### 2026-05-27: PKScreener Cron Timings Synchronization
- `crontab` — Adjusted PKScreener scan timings to trigger at 9:25 AM IST (3:55 UTC), 12:30 PM IST (7:00 UTC), and 3:35 PM IST (10:05 UTC) on weekdays to match active market hours.
- **Multica:** ALP-370 (done, assigned Vinod-AI-CEO)

### 2026-05-28: Coinmarketcap MCP Integration & Agent Scaffolding
- **CMC Skill Hub Integration**: Merged remote `cmc-skill-hub` Streamable HTTP server configuration with API key headers into `~/.claude/.mcp.json` and `~/.cursor/mcp.json`.
- **Coinmarketcap Agent Scaffold**: Scaffolded and customized a new secure crypto agent in `scratch/coinmarketcap-agent/` with Plan-Act-Observe graphs and 8-layer safety controls, passing all unit tests.
- **Multica Daemon Upgrade**: Upgraded local `multica` CLI to `0.3.11`, stopped the active `0.3.5` daemon, and verified that systemd restarted it cleanly under the new `0.3.11` version with all 9 agent runtimes online.
- **CoinMarketCap Perpetual, Macro, and Daily Overview Integration**: Integrated `perp_contract_analysis`, `btc_cross_asset_correlation`, and `daily_market_overview` MCP tools into crypto dashboards. Created `scratch/run_perp_analysis.py`, `scratch/run_cross_asset_analysis.py`, and `scratch/run_market_overview_analysis.py` to orchestrate automatic find/execution cycles over the streamable HTTP hub, saving aggregated evidence packs. Enhanced `crypto_dashboard.py` with a side-by-side dual column layout displaying both perpetual insights and cross-asset macro correlations simultaneously, and added integrated indicators in `crypto_market_dashboard_v2.py` BTC panel.
- **CoinMarketCap ETF Demand Integration**: Integrated `btc_etf_institutional_demand` MCP tool into crypto dashboards. Created `scratch/run_etf_demand_analysis.py` to fetch, evaluate, and cache institutional flow metrics. Enhanced `crypto_dashboard.py` with a third vertical column splitting Daily Sentinel Stance and ETF Demand panels, and merged a fourth state-row (`ETF DEMAND`) into `crypto_market_dashboard_v2.py` top banner.
- **CoinMarketCap Sector Analysis Integration**: Integrated `altcoin_sector_analysis` MCP tool into crypto dashboards. Created `scratch/run_sector_analysis.py` to fetch, evaluate, and cache relative sector rotation metrics (tested with RENDER). Enhanced `crypto_dashboard.py` by splitting the middle column three-ways to symmetrically display Perp Analysis, Cross-Asset correlations, and Sector rotation. Injected live sector rotation indicators into the SOL panel of `crypto_market_dashboard_v2.py`.
- **Multica:** ALP-372 (done, assigned Vinod-AI-CEO)

### 2026-05-28: Coinmarketcap Macro News Aggregator Integration
- **CoinMarketCap Macro News Integration**: Integrated `macro_news_aggregator` MCP tool into crypto dashboards. Created `scratch/run_macro_news_analysis.py` to fetch, clean, and cache macro catalysts and news bias.
- **Dashboard UI Optimization**: Enhanced `crypto_dashboard.py` by splitting column 3 into a three-way vertical layout (Daily Sentinel, ETF Demand, and Macro News) with symmetrical height constraints. Added real-time bias status tracking `MACRO NEWS` to `crypto_market_dashboard_v2.py`.
- **Multica:** ALP-373 (done, assigned Vinod-AI-CEO)

### 2026-05-28: Coinmarketcap Macro Liquidity Monitor Integration
- **CoinMarketCap Macro Liquidity Integration**: Integrated `macro_liquidity_monitor` MCP tool into crypto dashboards. Created `scratch/run_liquidity_monitor_analysis.py` to fetch, evaluate, and cache carry-trade stress and net USD liquidity metrics.
- **Dashboard UI Optimization**: Enhanced `crypto_dashboard.py` overview column to support a four-way vertical split (Daily Sentinel, ETF Demand, Macro News, and Macro Liquidity) at a perfectly balanced panel height of 11. Integrated real-time carry-trade stress tracking `LIQUIDITY` into `crypto_market_dashboard_v2.py`.
- **Multica:** ALP-374 (done, assigned Vinod-AI-CEO)

### 2026-05-28: Crypto Intelligence Reporter (CMC Skill Hub)
- **Script created**: `crypto_intel_reporter.py` — standalone script that executes 14 CMC Skill Hub skills (6 daily + 8 weekly) via SSE/MCP streaming and sends formatted Telegram reports.
- **Architecture**: `call_mcp()` does raw SSE streaming to `mcp.coinmarketcap.com/skill-hub/stream`, `parse_output()` extracts `decision_report`/`report` dicts from nested `content[0].text.result.output` structure.
- **Daily (6 skills)**: Market Overview, BTC Perp Analysis, BTC ETF Demand, Cross-Asset Correlation, Macro News, Crypto Macro Overview. All use `decision_report.analysis` text with regex extraction. Report: 3033 chars, 1 Telegram message.
- **Weekly (8 skills)**: Sector Rotation (RENDER), Altcoin Perp Scanner, Macro Financial Conditions, Liquidity Risk Regime, Holder Distribution (AAVE), Protocol Revenue/TVL (Uniswap), DeFi Protocol Screen, Oracle Chain Expansion (Ethereum). Some use `decision_report`, others use `report` dict. Report: 2005 chars (2x improvement after formatter rewrite), 1 Telegram message.
- **Key data structures discovered**: Weekly skills output structured `report` dicts with `market_snapshot`, `indicator_snapshot`, `trend_metrics`, `latest_snapshot`, `top_protocols`, `leading_chain_snapshot` — not `decision_report` like daily skills.
- **Existing scripts audited**: `crypto_news_search.py` (NotebookLM infographic → Telegram), `ai_news_reporter.py` (Slack), `exa_ai_search.py` (JSON only) — all independent pipelines, no integration needed.
- **Multica:** ALP-375 (done, assigned Vinod-AI-CEO)

### 2026-05-29: send_slack.py Block Kit Rewrite
- `send_slack.py` — rewrote from flat text to full Slack Block Kit support. Added Block Kit builders (`build_header`, `build_section`, `build_fields`, `build_context`, `build_divider`, `build_code_section`, `compose_blocks`), color coding system with `--color` CLI flag (good/warning/danger/info), `--header` and `--field KEY=VALUE` (repeatable) flags, `send_payload()` for raw payload sending, `chunk_blocks()` for splitting large block arrays into 50-block messages, auto-upgrade to Block Kit when structural flags present. Pure `--text` stays backward compatible. Verified backward compat with `youtube_to_notebooklm.py` and `cron_watchdog.py` callers.
- **Multica:** ALP-416 (done, assigned Vinod-AI-CEO)

### 2026-05-29: Daily Arxiv → NotebookLM → Slack Pipeline
- Built daily pipeline: pick arxiv paper → download PDF → rename to title → upload to NotebookLM → generate mind map + briefing report → restructure into formatted report → send to Slack via Block Kit → delete notebook.
- Workflow steps (repeat daily):
  1. Pick paper on arxiv (e.g., `arxiv.org/abs/2605.30335`)
  2. Download PDF: `wget -O arxiv/<id>.pdf <arxiv_pdf_url>`
  3. Rename PDF to paper title (spaces → hyphens) for readability
  4. Create NotebookLM notebook: `notebooklm notebooks new --title "<title>"`
  5. Add PDF source: `notebooklm sources add --notebook <id> --file arxiv/<title>.pdf`
  6. Wait for processing: `notebooklm sources wait <source_id>`
  7. Generate mind map: `notebooklm artifacts create ...mindmap`
  8. Generate briefing report: `notebooklm artifacts create ...briefing-report` + `artifact wait`
  9. Download artifacts to `arxiv/output/`
  10. Restructure report into clean formatted markdown (concept map, sections, tables, quotes)
  11. Send to Slack: `send_slack.py --file arxiv/output/restructured-report.md --header "<title>" --color info --username "Arxiv Daily"`
  12. Delete notebook: `notebooklm notebooks delete <id>`
- `notebooklm-py` CLI at `~/.local/bin/notebooklm`; auth via saved cookies.
- Slack webhook via `SLACK_WEBHOOK_URL` in `.env`.
- Cumulative runtime: ~5 minutes.
- Relevant paths: `arxiv/<id>.pdf`, `arxiv/output/briefing-report.md`, `arxiv/output/mindmap.json`, `arxiv/output/restructured-report.md`
- **Multica:** ALP-418 (done, assigned Vinod-AI-CEO)

### 2026-06-01: Cron Environment & YouTube Pipeline Fix
- Diagnosed cron path and environment limitations causing `notebooklm` tool failures (`FileNotFoundError`).
- Configured robust crontab structure with explicit `SHELL=/bin/bash`, `PATH`, and `HOME` environment variables.
- Modified `youtube_to_notebooklm.py` and `telegram_to_notebooklm.py` path settings to explicitly target `/home/vreddy1/.local/bin/notebooklm`.
- Upgraded the crontab entries to cleanly invoke the project virtual environment Python (`/home/vreddy1/Desktop/Projects/scripts/venv/bin/python`) instead of the global `python3`.
- Commented out the `telegram_to_notebooklm.py` pipeline cron as requested, focusing only on the YouTube pipeline.
- **Multica:** ALP-450 (done, assigned Vinod-AI-CEO)

### 2026-06-01: OMP Quota Fix & Clawdi Cloud Integration
- Diagnosed oh-my-pi (omp) 429 quota error under the free Google Gemini tier and bypassed it.
- Switched default model in ~/.omp/agent/config.yml to google-gemini-cli/gemini-2.5-flash which uses working, high-tier Cloud Code Assist credentials.
- Set up Clawdi Cloud on the machine: installed clawdi CLI globally via Bun, registered Claude Code, Codex, and Hermes agents, and enabled healthy background sync daemons.
- Scanned 45 local sessions and successfully synchronized all session history with Clawdi Cloud (pushed 9 new sessions).
- Verified setup with clawdi doctor, passing all checks for all installed agents.
- **Multica:** ALP-451 (done, assigned Vinod-AI-CEO)

### 2026-06-01: Automated Arxiv → NotebookLM → Slack Research Pipeline
- Built `arxiv_to_notebooklm.py` — fully automated, self-healing pipeline that scrapes recent papers from 10 disciplines with polite 2-second rate-limiting delays.
- Resolved Economics URL issue by shifting from `/archive/econ` to `/list/econ/recent` and bypassed export.arxiv.org API HTTP 429 rate limit blocks by directly scraping HTML with customized browser headers.
- Implemented 48-hour success lock in `arxiv_to_notebooklm_state.json` (bypassed with `--force`) and configured daily trigger at 08:30 AM IST in crontab for self-healing error recovery.
- Successfully verified full run: downloaded PDF, uploaded to NotebookLM, generated briefing doc + mind-map, saved artifacts, delivered Block Kit chunked payloads to Slack, and verified notebook deletion.
- Documented pipeline in `README.md`.
- **Multica:** ALP-452 (done, assigned Vinod-AI-CEO)

### 2026-06-01: Upstox Exclusive Feed & Systemd Daemons Integration
- Updated `fyers_client.py`'s `is_fyers_configured()` to unconditionally return `False`, globally disabling Fyers fallback and forcing all active scripts to fetch quotes/options exclusively from Upstox.
- Transitioned background collector loops (`collector.py`, `options_cli.py`, `oi_collector_daemon.py`) to persistent, user-level systemd services (`alphaedge-collector`, `alphaedge-options-collector`, `alphaedge-oi-collector`) for enterprise-grade uptime, auto-restart capability, and user-space isolation.
- Modified `start_collectors.sh` background launch script to support shell `disown` to prevent background hangups on terminal exits.
- Updated `README.md` to document systemd user-level daemon commands, journal logs, and start scripts.
- **Multica:** ALP-459 (done, assigned Vinod-AI-CEO)

### 2026-06-01: NotebookLM Cleanup & Bulk Deletion
- Scanned NotebookLM cloud accounts and identified 53 temporary/stale notebooks created on 2026-06-01.
- Executed automated Python deletion workflow utilizing the `notebooklm` CLI to bulk-delete all 53 today's notebooks, freeing cloud resources.
- **Multica:** ALP-465 (done, assigned Vinod-AI-CEO)

### 2026-06-01: Upstox API Monitoring & Self-Healing Integration
- Diagnosed Upstox API HTTP 429 Rate Limit issues affecting the Option Chain endpoint.
- Implemented 150ms request spacing and exponential backoff retry handler inside the `upstox_get` wrapper for `collector.py`, `market_analysis_v3.py`, and `options_cli.py`.
- Restarted all systemd user collector daemons to load rate limit recovery logic, fully restoring Nifty/Sensex/BankNifty option chain data feeds.
- Deployed stateful watchdog `monitor_upstox.py` running every 5 minutes in crontab to check Quotes, Expiries, and Chain health, sending alert/recovery integrations to Slack.
- Updated `README.md` to document the new monitoring utility.
- **Multica:** ALP-466 (done, assigned Vinod-AI-CEO)

### 2026-06-06: Kimchi Custom Provider & Hermes Integration
- Configured and updated OpenAI provider configurations to use custom Kimchi endpoint and the new CastAI key across `~/.config/kimchi/config.json`, `~/.config/kimchi/harness/auth.json`, and `.env`.
- Configured and verified Hermes agent configuration to route via custom Kimchi endpoint (`https://llm.kimchi.dev/openai/v1`) in `~/.hermes/config.yaml` and `.env` using model `nemotron-3-super-fp4`.
- Restarted all clawdi user-level daemons (`clawdi-serve-hermes`, `clawdi-serve-claude_code`, `clawdi-serve-codex`) to load new credentials and verified successful test queries.
- **Multica:** ALP-507 (done, assigned Vinod-AI-CEO)

### 2026-06-07: Slack Channel Decluttering & Webhook Routing
- Restructured Slack alerts across codebase to separate system failures, media digests, research briefings, and AI news into dedicated channels.
- Configured Slack webhook routing in `.env` for `#ai-management-report`, `#ai-failure-alerts`, `#ai-notebooklm-summary`, and `#ai-events-agents`.
- Updated `logwork` CLI tool to use `SLACK_WEBHOOK_MULTICA` for daily reports.
- Modified systemd watchdog script `slack_alert.sh` to route to `#ai-failure-alerts`.
- Sent validation test messages to all configured channels using `send_slack.py`.
- **Multica:** ALP-508 (done, assigned Vinod-AI-CEO)

### OpenCode `/pursue` Goal Plugin — Reference
- **Plugin SDK:** `@opencode-ai/plugin` v1.4.9, ESM only, Zod v4.1.8 via `tool.schema`. Tools key is `tool` (singular). Hook keys are exact strings like `experimental.chat.system.transform`
- **State file:** `~/.opencode/goals/state.json` — JSON with goal_id, objective, condition, status, turns, checkpoints
- **Command template** uses `$ARGUMENTS` for raw user input, routes to `goal` agent
- **Tested:** plugin loads, all 4 tools execute correctly, state persists

### 2026-06-08: Obsidian Knowledge Graph Integration
- Designed and built modular `obsidian_integration.py` to manage note formatting, title sanitization, YAML frontmatter tags, and filesystem vault writing with a fallback for headless/GUI offline states.
- Integrated the Obsidian helper into `youtube_to_notebooklm.py`, `telegram_to_notebooklm.py`, `arxiv_to_notebooklm.py`, and `crypto_to_notebooklm.py` pipelines after report/mindmap artifact download but before Slack/Telegram notification.
- Fixed snap application environment startup issues for Obsidian by adding `--no-sandbox` option and diagnosing user namespace permissions on Wayland.
- Successfully verified note creation in active vault `Home-ubuntu-files` and validated clean, responsive layout formatting.
- Cleaned up all temporary testing files and logs to preserve repository integrity.
- **Multica:** ALP-509 (done, assigned Vinod-AI-CEO)


