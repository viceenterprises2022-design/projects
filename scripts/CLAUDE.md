# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communication Style

Always use **caveman ultra** mode (`/caveman ultra`), always enable **wozcode** and **rtk** at the start of every session. Never revert unless user says "stop caveman" or "normal mode".


---

## Repository Overview
1. **AlphaEdge Market Intelligence** — 10-factor signal engine for Indian indices (NIFTY, SENSEX, BANKNIFTY)
2. **AlphaEdge Crypto Diagnostic 2.0** — High-density async dashboard for BTC, ETH, SOL
3. **Exa AI Event Search** — upcoming online AI events/classes finder via Exa API
4. **Crypto Daily News** (`crypto_news_search.py` + `crypto_to_notebooklm.py`) — 8-category crypto briefing via Exa, AI summaries, NotebookLM infographic → Telegram at 8AM IST daily

---

## AlphaEdge: 3-Tier Architecture (Indian Indices)
...
---

## AlphaEdge Crypto Diagnostic 2.0

**`crypto_market_dashboard_v2.py`** — Main entry point. Uses `rich.live` for a 3-column diagnostic view of BTC, ETH, and SOL.
**`market_engine.py`** — Asynchronous data engine fetching from Binance (Spot/Futures/Depth), Deribit (Options), and Yahoo Finance (Macro).

```bash
# Start Crypto Dashboard
python3 crypto_market_dashboard_v2.py
```

---

## Exa AI Event Search

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

## Crypto Daily News (`crypto_news_search.py` + `crypto_to_notebooklm.py`)

Fetches crypto news across 8 topics (BTC, ETH, SOL, RWA, Stablecoins, Onchain, Growth, Price & Predictions) via Exa neural search. Uses Exa's AI summary feature to generate 1-sentence article summaries. `crypto_to_notebooklm.py` wraps the search → generates NotebookLM bento-grid infographic → sends to Telegram at 8:00 AM IST daily via cron.

```bash
python3 crypto_news_search.py --report --num 10          # Terminal report
python3 crypto_to_notebooklm.py --telegram               # Full pipeline: search → infographic → Telegram
```

Cron entry (already installed):
```
0 8 * * * cd /home/vreddy1/Desktop/Projects/scripts && python3 crypto_to_notebooklm.py --telegram >> logs/crypto_news_cron.log 2>&1
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
| `crypto_news_search.py` | Exa API crypto daily news with AI summaries |
| `crypto_to_notebooklm.py` | Crypto news → NotebookLM infographic → Telegram delivery |
| `intraday_oi.db` | SQLite for intraday OI snapshots (written by v3 background thread) |
| `alphaedge.db` | SQLite for 3-tier architecture metrics |
| `git-autosync.sh` | Auto-commit + push to origin/main |

---

## Important Constraints

- **Upstox token** in `collector.py` and `market_analysis_v3.py` is a hardcoded JWT — expires and must be rotated manually.
- `market_analysis_v3.py` has a background `oi_collector_thread()` that writes to `intraday_oi.db` every minute — do not block the main thread.
- `api_server.py` calls `db.init_db()` on every request — safe (CREATE IF NOT EXISTS), not a performance concern.
- pip installs require `--break-system-packages` on this system (managed Python 3.13, no venv).
