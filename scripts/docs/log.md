# Directory Update Log

## 2026-06-17
* **Update**: Migrated Daily Crypto Brief pipeline (`crypto_to_notebooklm.py`) notification and file delivery system from Telegram to Slack using Slack Block Kit Webhooks and File Upload APIs.
* **Update**: Migrated PKScreener scan reporter (`pkscreener_runner.py`) from Telegram alerts to Slack webhook alerts, parsing HTML tags to Slack mrkdwn.

## 2026-06-01
* **Update**: Cleaned up crontab execution environment; fixed path issues by targeting local `notebooklm` binary explicitly and routing runners through python virtual environment.

## 2026-05-29
* **Creation**: Established the Arxiv → NotebookLM → Slack Pipeline (`arxiv_to_notebooklm.py`) to scrape, process, and summarize academic papers via Slack.
* **Update**: Rewrote `send_slack.py` utility to support Slack Block Kit payloads, custom fields, color headers, and auto-chunking.

## 2026-05-28
* **Update**: Integrated CoinMarketCap perp, macro, ETF demand, sector rotation, and liquidity indicators into `crypto_dashboard.py` layout.
* **Creation**: Developed `crypto_intel_reporter.py` to fetch, format, and report 14 Daily/Weekly CMC Skill Hub analyses.

## 2026-05-26
* **Creation**: Created `oi_collector_daemon.py` and provisioned three systemd user services for AlphaEdge collection pipelines.
* **Update**: Unified timezone calculations in AlphaEdge dashboard clocks to `Asia/Kolkata` (IST).

## 2026-05-25
* **Update**: Added flock-based locking to `pkscreener_runner.py` to resolve duplicate run cron memory leaks and GNOME crashes.

## 2026-05-24
* **Creation**: Created the `crontab-viz` visualizer tool to map and audit scheduled script intervals.
* **Update**: Integrated gainers/losers card row and live Yahoo Finance macro tracking in AlphaEdge dashboard.
