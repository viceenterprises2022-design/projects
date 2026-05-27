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

### OpenCode `/pursue` Goal Plugin — Reference
- **Plugin SDK:** `@opencode-ai/plugin` v1.4.9, ESM only, Zod v4.1.8 via `tool.schema`. Tools key is `tool` (singular). Hook keys are exact strings like `experimental.chat.system.transform`
- **State file:** `~/.opencode/goals/state.json` — JSON with goal_id, objective, condition, status, turns, checkpoints
- **Command template** uses `$ARGUMENTS` for raw user input, routes to `goal` agent
- **Tested:** plugin loads, all 4 tools execute correctly, state persists
