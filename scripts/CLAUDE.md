---
type: Reference
title: Claude Code Assistant Rules
description: Developer guidelines, system commands, and environment setups for the Claude Code agent.
tags: [rules, agent, claude, run-commands]
timestamp: 2026-06-17T23:45:00Z
---

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communication Style

Always use **caveman ultra** mode (`/caveman ultra`), always enable **wozcode** and **rtk** at the start of every session. Never revert unless user says "stop caveman" or "normal mode".

---

## Python Environments

Two separate venvs — use the right one:

| Venv | Path | Used by |
|------|------|--------|
| Main | `venv/` (project root) | api_server, collector, telegram/youtube pipelines, watchdog, alert_dashboard |
| PKScreener | `/home/vreddy1/Desktop/Projects/pkscreener_venv` | pkscreener_runner.py only |

System Python 3.13/3.14 blocks global installs — use `--break-system-packages` or install into venv.

```bash
# Install into main venv
venv/bin/pip install <pkg>

# Install into pkscreener venv
/home/vreddy1/Desktop/Projects/pkscreener_venv/bin/pip install <pkg>

# System-level fallback (avoid)
python3 -m pip install <pkg> --break-system-packages
```

---

## Repository Overview

1. **AlphaEdge Market Intelligence** — 10-factor signal engine for Indian indices (NIFTY, SENSEX, BANKNIFTY)
2. **AlphaEdge Crypto Diagnostic 2.0** — High-density async dashboard for BTC, ETH, SOL
3. **Exa AI Event Search** — upcoming online AI events/classes finder via Exa API
4. **Crypto Daily News** (`crypto_news_search.py` + `crypto_to_notebooklm.py`) — 8-category crypto briefing via Exa, AI summaries, NotebookLM infographic → Telegram at 8AM IST daily
5. **Beat the Street / YouTube / Toddle → NotebookLM Pipelines** — automated document ingestion and report generation
6. **PKScreener NSE Scanner** — 8 NSE stock scans with Telegram delivery
7. **Portfolio P&L Dashboard** — multi-broker aggregator (Upstox, Dhan, TradeSmart, Fyers, Hyperliquid, Exness, Binance) with live/mock fallback

---

## AlphaEdge: 3-Tier Architecture (Indian Indices)

**Data flow:** `collector.py` → `alphaedge.db` → `api_server.py` → `frontend/`

**Signal engine** — 10 factors, each scored -1/0/+1: Trend, Dow Jones, India VIX, OI skew, VWAP, SuperTrend, RSI, DXY, Crude Oil, PCR. Sum = final score; ≥6 → BUY, ≤4 → SELL, else NEUTRAL.

**Data sources:**
- Upstox REST API (bearer token `UPSTOX_TOKEN`) → live quotes + option chain OI
- Yahoo Finance (no auth) → DXY, Crude, US30, Gold, Silver, index fallback

**API server endpoints** (`api_server.py` on `:8765`):
- `GET /` — DVR Portfolio dashboard (Chart.js)
- `GET /pixi` — PixiJS Options Intelligence dashboard
- `GET /api/latest` — latest snapshot (all symbols + macro)
- `GET /api/history?sym=NIFTY&days=30` — time-series for Chart.js
- `GET /api/portfolio/pnl` — multi-broker portfolio P&L (via `pnl_poller.py`)
- `GET /api/pixi/chain?symbol=NIFTY` — live options chain (all strikes)
- `GET /api/pixi/oi-trend?symbol=NIFTY` — intraday total Call/Put OI trend
- `GET /api/pixi/signal?symbol=NIFTY` — signal, score, all 10 factor values
- `GET /api/strategies/nifty200-momentum` — Nifty 200 scanner results

**market_analysis_v3.py** — legacy monolith; generates self-contained HTML report with embedded PixiJS/sparklines. Still used by `report_and_send.py` for Telegram delivery. Has background `oi_collector_thread()` writing to `intraday_oi.db` every minute — do not block main thread.

### Run Commands

```bash
# Populate DB once
python3 collector.py

# Continuous collection (every 5 min)
python3 collector.py --loop --interval 5

# Start API server (or use systemd: alphaedge-api.service)
venv/bin/python api_server.py
# → http://localhost:8765

# Legacy standalone HTML report
python3 market_analysis_v3.py

# Send analysis to Telegram
python3 report_and_send.py

# Headless stdout only
python3 run_analysis_headless.py
```

### Install Dependencies

```bash
venv/bin/pip install fastapi "uvicorn[standard]" requests rich python-dotenv aiohttp
```

---

## Portfolio P&L Poller (`pnl_poller.py`)

Aggregates live portfolio data from 7 brokers. Pattern: try live API → fall back to dynamic mock (sinusoidal fluctuation to simulate real-time feel). Used by `api_server.py` at `GET /api/portfolio/pnl`.

**Brokers:** Upstox, Dhan, TradeSmart (Noren OMS), Fyers, Hyperliquid, Exness, Binance.

All credentials via `.env`. If a broker credential is missing or returns 401/403, mock data is used silently — the endpoint never fails.

---

## AlphaEdge Crypto Diagnostic 2.0

**`crypto_market_dashboard_v2.py`** — `rich.live` 3-column diagnostic for BTC, ETH, SOL.
**`market_engine.py`** — async data engine: Binance (Spot/Futures/Depth), Deribit (Options), Yahoo Finance (Macro). Exposes `MarketEngine` class with `calculate_rsi`, `calculate_ema`, `calculate_vwap`, `calculate_supertrend`, `analyze_trend`, `calculate_correlation`.

```bash
python3 crypto_market_dashboard_v2.py
```

---

## NotebookLM Pipelines

Three independent pipelines sharing the same `notebooklm` CLI tool and Slack delivery pattern:

### 1. Beat the Street (Telegram PDFs → NotebookLM)

**`telegram_to_notebooklm.py`** — 7-step daily pipeline:
1. Fetch PDFs from `@btsreports` (last 24h via Telethon)
2. Create dated NotebookLM notebook
3. Upload PDFs as sources
4. Generate 5 artifacts: report (`.md`), mind-map (`.json`), infographic (`.png`), quiz (`.json`), podcast (`.mp3`)
5. Save to `notebooklm_output/Beat-the-street-report-YYYY-MM-DD/`
6. Send all artifacts to Slack
7. Delete NotebookLM notebook from cloud

```bash
# One-time auth (interactive)
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

notebooklm login   # one-time browser auth

# Manual run
PYTHONUNBUFFERED=1 venv/bin/python telegram_to_notebooklm.py
```

### 2. YouTube → NotebookLM

**`youtube_to_notebooklm.py`** — monitors channels in `youtube_channels.json` for videos ≤24h old → NotebookLM notebook → briefing-doc + mind-map → Slack Block Kit message → deletes notebook.

**Safety:** Notebook deleted ONLY after successful Slack delivery. Deletion is regex-gated (`^[a-zA-Z0-9][a-zA-Z0-9_-]{19,}$`).

```bash
python3 youtube_to_notebooklm.py --add-channel @NewChannel
python3 youtube_to_notebooklm.py --remove-channel @OldChannel
python3 youtube_to_notebooklm.py --list-channels
python3 youtube_to_notebooklm.py   # run pipeline
```

### 3. Toddle → NotebookLM

**`toddle_notebooklm_sync.py`** — orchestrates 4-phase daily sync for school subjects (Physics, Chemistry, Maths, etc.):
1. `toddle_all_inventory.py` — inventory all subject files from Toddle
2. `toddle_bulk_download.py` — download new/changed files
3. `toddle_bulk_convert.py` — convert to markdown (`output/text/<subject>/`)
4. Upload merged markdown + generate study guides via `notebooklm` CLI

State tracked in `sync_state.json`. Skip phases with `--skip-inventory`, `--skip-download`, `--skip-convert`.

```bash
venv/bin/python toddle_notebooklm_sync.py
venv/bin/python toddle_notebooklm_sync.py --skip-inventory --skip-download  # convert + upload only
```

---

## Exa AI Event Search

**`exa_ai_search.py`** — searches for upcoming online AI events from OpenAI, Anthropic, Google AI, Meta, DeepMind, HuggingFace.

Key design: `start_published_date` set to 60 days ago (Exa server-side filter); `is_future_event()` post-filters past-event language. Runs broad search + domain-targeted search per query.

```bash
EXA_API_KEY=<key> python3 exa_ai_search.py
python3 exa_ai_search.py --query "Anthropic online course 2025"
python3 exa_ai_search.py --no-broad     # domain-targeted only
python3 exa_ai_search.py --all          # include non-online results
```

---

## Crypto Daily News (`crypto_news_search.py` + `crypto_to_notebooklm.py`)

8 search topics (BTC, ETH, SOL, RWA, Stablecoins, Onchain, Growth, Price & Predictions) via Exa neural search. Per-article AI summary. `crypto_to_notebooklm.py` wraps search → NotebookLM infographic → Telegram.

```bash
python3 crypto_news_search.py --report --num 10          # terminal report
python3 crypto_to_notebooklm.py --telegram               # full pipeline → Telegram
```

---

## PKScreener NSE Scanner (`pkscreener_runner.py`)

Uses separate venv at `/home/vreddy1/Desktop/Projects/pkscreener_venv` and PKScreener repo at `/home/vreddy1/Desktop/Projects/pkscreener`. Runs 8 scans (Nifty50 + NiftyAll breakouts, RSI/MACD, SuperTrend, strong buy). Results sent to Telegram.

```bash
/home/vreddy1/Desktop/Projects/pkscreener_venv/bin/python pkscreener_runner.py
```

---

## Monitoring & Alerting

**`cron_watchdog.py`** — parses cron log files via byte-offset tracking (state in `~/.opencode/cron_watchdog_state.json`); detects Python tracebacks, ERROR/CRITICAL entries, nonzero exit codes; alerts Slack.

```bash
venv/bin/python cron_watchdog.py          # check + alert
venv/bin/python cron_watchdog.py --dry-run # report only, no Slack
venv/bin/python cron_watchdog.py --reset   # reset state, recheck all logs
```

**`alert_dashboard_alive.py`** — checks `/`, `/pixi`, `/api/latest`, `/api/gainers-losers` every 5 min; alerts Slack on 2+ consecutive failures + recovery. State in `/tmp/alert_dashboard_state.json`.

**`send_slack.py`** — generic utility; call with `python3 send_slack.py "message"` or import and call `send_slack(text)` / `send_file_to_slack(path)`.

---

## Strategies

**`strategies/nifty200_momentum.py`** — Nifty 200 momentum scanner; results served at `GET /api/strategies/nifty200-momentum`.

---

## Scaffolding

**`scaffold_agent.py`** — copies `templates/production-agent/` to a new directory, substitutes `{{AGENT_NAME}}` / `{{AGENT_NAME_SNAKE}}` / `{{AGENT_NAME_CAMEL}}` placeholders, inits git.

```bash
python3 scaffold_agent.py --name "Market Assistant"
python3 scaffold_agent.py --name "My Bot" --dest /path/to/dest
```

---

## Tests

```bash
# Run all tests
python3 -m pytest tests/

# Run a single test file
python3 -m pytest tests/test_indicators.py

# Run a single test
python3 -m pytest tests/test_indicators.py::test_rsi_calculation
```

`tests/test_indicators.py` tests `MarketEngine` from `market_engine.py`.
`tests/test_crypto_dashboard.py` tests `crypto_dashboard.py` (Deribit fetcher, PCR, max pain, liquidation bins).

---

## Cron Schedule (actual installed)

| Time (IST) | Script | Venv |
|-----------|--------|------|
| 1:30 AM daily | `market_engine.py` | system python3 |
| 3:00 AM weekdays | `strategies/nifty200_momentum.py` | venv |
| 3:55 AM weekdays | `pkscreener_runner.py` (pre-market) | pkscreener_venv |
| 7:00 AM weekdays | `pkscreener_runner.py` (morning) | pkscreener_venv |
| 8:00 AM daily | `crypto_to_notebooklm.py --telegram` | system python3 |
| 10:05 AM weekdays | `pkscreener_runner.py` (noon) | pkscreener_venv |
| 10:30 AM daily | `telegram_to_notebooklm.py` | venv |
| 11:30 AM daily | `youtube_to_notebooklm.py` | system python3 |
| 1:00 PM weekdays | `strategies/nifty200_momentum.py` | venv |
| every 5 min | `alert_dashboard_alive.py` | venv |
| every hour :15 | `cron_watchdog.py` | venv |

Logs: `logs/` directory (per-script log files).

---

## Systemd Services

```bash
sudo systemctl status alphaedge-api     # FastAPI on :8765
sudo systemctl restart alphaedge-api
journalctl -u alphaedge-api -f
```

---

## Key File Index

| File | Role |
|------|------|
| `collector.py` | Data fetch + signal engine + DB writes |
| `alphaedge_db.py` | SQLite schema + query helpers |
| `api_server.py` | FastAPI REST on :8765; imports `pnl_poller` |
| `pnl_poller.py` | Multi-broker P&L aggregator (live + mock fallback) |
| `market_analysis_v3.py` | Legacy monolith — generates self-contained HTML |
| `market_engine.py` | Async crypto data engine + indicator calculations |
| `report_and_send.py` | Wraps v3, captures output, sends to Telegram |
| `telegram_to_notebooklm.py` | Telegram PDF → NotebookLM → Slack (daily 10:30AM) |
| `youtube_to_notebooklm.py` | YouTube channels → NotebookLM → Slack (daily 11:30AM) |
| `toddle_notebooklm_sync.py` | Toddle school notes → NotebookLM orchestrator |
| `exa_ai_search.py` | Exa API upcoming AI event search |
| `crypto_news_search.py` | Exa API crypto daily news with AI summaries |
| `crypto_to_notebooklm.py` | Crypto news → NotebookLM infographic → Telegram |
| `pkscreener_runner.py` | NSE stock scanner wrapper → Telegram |
| `cron_watchdog.py` | Cron failure monitor → Slack |
| `alert_dashboard_alive.py` | Dashboard uptime monitor → Slack |
| `send_slack.py` | Generic Slack delivery utility |
| `scaffold_agent.py` | Production AI agent scaffolder from templates/ |
| `sync_state.json` | Toddle sync state (per-subject last-synced timestamp) |
| `alphaedge.db` | SQLite for 3-tier market intelligence metrics |
| `intraday_oi.db` | SQLite for intraday OI snapshots (written by v3 background thread) |
| `git-autosync.sh` | Auto-commit + push to origin/main |

---

## Important Constraints

- **Upstox token** in `collector.py` and `market_analysis_v3.py` is a hardcoded JWT — expires and must be rotated manually.
- `api_server.py` calls `db.init_db()` on every request — safe (CREATE IF NOT EXISTS), not a performance concern.
- `pnl_poller.py` always returns data (mock fallback) — `GET /api/portfolio/pnl` never errors due to missing broker credentials.
- `cron_watchdog.py` state file is at `~/.opencode/cron_watchdog_state.json` (not inside this repo).
- NotebookLM notebook deletion in YouTube/Telegram pipelines is gated on successful Slack delivery — partial failures leave notebooks in cloud.
- PKScreener uses its own isolated venv; never run `pkscreener_runner.py` with the main venv.
