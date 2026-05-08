# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communication Style

Always use **caveman ultra** mode (`/caveman ultra`). Never revert unless user says "stop caveman" or "normal mode".

---

## Repository Overview

Two independent systems in one directory:

1. **AlphaEdge Market Intelligence** — 10-factor signal engine for Indian indices (NIFTY, SENSEX, BANKNIFTY)
2. **Exa AI Event Search** — upcoming online AI events/classes finder via Exa API

---

## AlphaEdge: 3-Tier Architecture

```
collector.py          # Fetches data (Upstox + Yahoo Finance), runs signal engine, writes to SQLite
    └─► alphaedge.db  # SQLite: metrics_history + macro_history tables
alphaedge_db.py       # DB layer: init_db(), insert_metric(), insert_macro(), query_latest(), query_history()
api_server.py         # FastAPI on :8765 — /api/latest, /api/history, /api/symbols + serves frontend/
frontend/             # HTML/JS dashboard polling the API every 60s, Chart.js visualizations
```

**market_analysis_v3.py** — monolithic legacy script (pre-decoupling). Generates a self-contained HTML report with embedded PixiJS/sparklines. Still used by `report_and_send.py` for Telegram delivery. The patched versions (`patch_market*.py`) injected Claude AI diagnostics into it.

**Signal engine** — 10 factors, each scored -1/0/+1: Trend, Dow Jones, India VIX, OI skew, VWAP, SuperTrend, RSI, DXY, Crude Oil, PCR. Sum = final score; ≥6 → BUY, ≤4 → SELL, else NEUTRAL.

**Data sources:**
- Upstox REST API (bearer token in `UPSTOX_TOKEN`) → live quotes + option chain OI
- Yahoo Finance (no auth) → DXY, Crude, US30, Gold, Silver, index fallback

**Telegram delivery** (`report_and_send.py`): swaps `market_analysis_v3.console` with a `CapturingConsole`, runs analysis, strips rich tags, sends HTML chunks ≤3500 chars to Telegram bot.

### Run Commands

```bash
# Populate DB once
python3 collector.py

# Continuous collection (every 5 min)
python3 collector.py --loop --interval 5

# Start API + dashboard
python3 api_server.py
# → http://localhost:8765

# Legacy: generate standalone HTML report
python3 market_analysis_v3.py

# Send analysis to Telegram
python3 report_and_send.py

# Headless analysis (stdout only)
python3 run_analysis_headless.py
```

### Install Dependencies

```bash
python3 -m pip install fastapi uvicorn[standard] requests rich --break-system-packages
```

---

## Exa AI Event Search

**`exa_ai_search.py`** — searches for upcoming online AI events/classes from OpenAI, Anthropic, Google AI, Meta, DeepMind, HuggingFace.

Key design decisions:
- `start_published_date` set to 60 days ago (server-side Exa filter)
- `is_future_event()` post-filters: drops pages with past-event language or age >60 days
- Runs broad search + domain-targeted search per query for coverage
- Output: rich table + `ai_events_results.json`

```bash
# Full run
EXA_API_KEY=<key> python3 exa_ai_search.py

# Custom query
python3 exa_ai_search.py --query "Anthropic online course 2025"

# Domain-targeted only (fewer API calls)
python3 exa_ai_search.py --no-broad

# Include non-online results
python3 exa_ai_search.py --all
```

```bash
python3 -m pip install exa-py rich --break-system-packages
```

---

## Key File Index

| File | Role |
|------|------|
| `collector.py` | Data fetch + signal engine + DB writes |
| `alphaedge_db.py` | SQLite schema + query helpers |
| `api_server.py` | FastAPI REST on :8765 |
| `market_analysis_v3.py` | Legacy monolith — generates self-contained HTML |
| `report_and_send.py` | Wraps v3, captures output, sends to Telegram |
| `exa_ai_search.py` | Exa API upcoming AI event search |
| `intraday_oi.db` | SQLite for intraday OI snapshots (written by v3 background thread) |
| `alphaedge.db` | SQLite for 3-tier architecture metrics |
| `git-autosync.sh` | Auto-commit + push to origin/main |

---

## Important Constraints

- **Upstox token** in `collector.py` and `market_analysis_v3.py` is a hardcoded JWT — expires and must be rotated manually.
- `market_analysis_v3.py` has a background `oi_collector_thread()` that writes to `intraday_oi.db` every minute — do not block the main thread.
- `api_server.py` calls `db.init_db()` on every request — safe (CREATE IF NOT EXISTS), not a performance concern.
- pip installs require `--break-system-packages` on this system (managed Python 3.13, no venv).
