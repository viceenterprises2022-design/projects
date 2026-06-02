# 📈 AlphaEdge Market Intelligence

> Section group: **🚀 Script Index**

*A decoupled, 10-factor market intelligence system for Indian Indices (NIFTY, SENSEX, BANKNIFTY).*

| Script | Description |
|:--- |:--- |
| `collector.py` | **Core Engine**. Fetches market data from Upstox/Yahoo, calculates 10-factor signals, and saves to DB. |
| `alphaedge_db.py` | **Database Manager**. Handles SQLite schema and data persistence for `alphaedge.db`. |
| `alert_dashboard_alive.py` | **Dashboard Uptime Monitor**. Cron-friendly uptime monitor — checks `/`, `/pixi`, `/api/latest`, `/api/gainers-losers` every 5 min. Silent when healthy; alerts Slack on 2+ consecutive failures plus recovery. State tracked in `/tmp/alert_dashboard_state.json`. |
| `monitor_upstox.py` | **Upstox API Monitor**. Stateful health and rate-limit watchdog. Probes Quotes, Expiries, and Option Chain endpoints every 5 min. Automatically sends Slack alerts on HTTP 429/401/outages and handles recovery. State in `/tmp/monitor_upstox_state.json`. |
| `api_server.py` | **API & Dashboard**. FastAPI backend serving market data and hosting the HTML dashboard on port 8765. Endpoints: `/api/latest`, `/api/history`, `/api/gainers-losers` (30s cache), `/api/portfolio/pnl` (multi-broker via `pnl_poller.py`), `/api/pixi/*` (options chain), `/api/strategies/nifty200-momentum`. |
| `market_engine.py` | Orchestrates the analysis flow for market signals. |
| `market_analysis_v3.py` | Latest version of core logic with **Auto-Refresh Terminal Dashboard**. |
| `run_analysis_headless.py` | CLI tool to run analysis and output results to console only. |
| `report_and_send.py` | **Clean Text Reporter**. Generates 10-factor analysis reports as clean HTML text (no terminal boxes) and sends to Telegram via `send_telegram_msg.py`. |
| `send_telegram_msg.py` | **Telegram Utility**. Dedicated script to send text messages or files to the pre-configured bot. Used by `report_and_send.py` and other automated tasks. |
| `options_cli.py` | **Advanced Options Dashboard**. Multi-index (Nifty, Sensex, BankNifty) Rich live terminal view. Shows Spot + Futures with OHLC (O/H/L/C) headers, strategy flags (OH/OL), human-readable OI (L/C), and ATM ± 300 strikes. **Lean, compressed layout (107 chars)** for small terminal windows. Zero-flicker rendering via `rich.live.Live` with alternate screen buffer. 5s polling, daily-reset SQLite. |
