---
type: Reference
title: System Architecture
description: Overview of Python environments, dependencies, and subsystem usage commands.
tags: [setup, environment, dependencies, architecture]
timestamp: 2026-06-17T23:30:00Z
---

# Architecture

## Python Environments
_(was: 🛠️ Setup)_


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


## Usage Examples
_(was: 🛠️ Setup)_


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
