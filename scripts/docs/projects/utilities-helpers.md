---
type: Reference
title: Utilities & Helpers
description: Shared standalone scripts, daemon status monitors, and notification utility helpers.
tags: [utilities, monitors, watchdog, notifications, scripts]
timestamp: 2026-06-17T23:30:00Z
---

# 🛠️ Utilities & Helpers

> Section group: **🚀 Script Index**

| Script | Description |
|:--- |:--- |
| `send_slack.py` | Generic utility to send text or file content to any Slack webhook. |
| `cron_watchdog.py` | Cron failure monitor — parses cron logs byte-offset, detects tracebacks, alerts Slack. State in `~/.opencode/cron_watchdog_state.json`. |
| `alert_dashboard_alive.py` | Dashboard uptime monitor — checks `/`, `/pixi`, `/api/latest`, `/api/gainers-losers` every 5 min, alerts Slack on outage. |
| `monitor_upstox.py` | Upstox API Monitor — checks health, rate limits, and outages of Upstox endpoints every 5 min, alerts Slack. State in `/tmp/monitor_upstox_state.json`. |
| `send_telegram.py` | Generic utility to send messages via Telegram Bot API. |
| `git-autosync.sh` | Shell script for automated git staging, committing, and pushing. |
| `patch_market.py` | Utility to apply specific logic patches to the market analysis scripts. |
| `clawdi` | **Environment Sync**. Cross-agent sync for sessions, skills, and secrets (Clawdi Cloud). |
| `crontab-viz` | **Crontab Visualizer**. Pretty-prints `crontab -l` with UTC→IST conversion, human-readable schedule, next run times, monthly calendar, and weekly grid. Run: `./crontab-viz` or alias `crons`. |

---
