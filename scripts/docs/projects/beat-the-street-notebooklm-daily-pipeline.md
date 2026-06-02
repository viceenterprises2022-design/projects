# 📰 Beat the Street — NotebookLM Daily Pipeline

> Section group: **🚀 Script Index**

*Automated daily pipeline: fetches PDFs from Telegram, uploads to NotebookLM, generates all artifact types, delivers to Slack, then cleans up.*

| Script | Description |
|:--- |:--- |
| `telegram_to_notebooklm.py` | **Daily Pipeline** (7 steps). Fetches PDFs from `@btsreports` (last 24h) → creates dated NotebookLM notebook → uploads sources → generates 5 artifacts (report, mind-map, infographic, quiz, podcast) → sends all to Slack via `format_file_for_slack()` → deletes notebook. Saves to `notebooklm_output/Beat-the-street-report-YYYY-MM-DD/`. Runs at **4PM IST** via cron. |
| `cron_watchdog.py` | **Cron Failure Monitor**. Parses cron logs via byte-offset tracking, detects tracebacks/ERROR/CRITICAL, alerts Slack. Runs at `:15` hourly. |

**Setup:**
```bash
# Install dependencies
venv/bin/pip install telethon python-dotenv
pipx install notebooklm-py

# Authenticate Telegram (one-time, interactive)
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

# Authenticate NotebookLM (one-time, browser)
notebooklm login

# Run manually
PYTHONUNBUFFERED=1 venv/bin/python telegram_to_notebooklm.py
```

**Cron (already installed):**
```
30 10 * * *  cd /path/to/scripts && PYTHONUNBUFFERED=1 venv/bin/python telegram_to_notebooklm.py >> notebooklm_output/cron.log 2>&1
15 * * * *    cd /path/to/scripts && PYTHONUNBUFFERED=1 venv/bin/python cron_watchdog.py 2>&1
```

**Pipeline steps:**
1. Fetch PDFs from Telegram channel (last 24h)
2. Create NotebookLM notebook (`Beat-the-street-report-YYYY-MM-DD`)
3. Upload PDFs as notebook sources
4. Generate 5 artifacts: report (`.md`), mind-map (`.json`), infographic (`.png`), quiz (`.json`), podcast (`.mp3`)
5. Save artifacts to `notebooklm_output/` per-date directory
6. Send all artifacts to Slack (generic: `.md` = summary+full, `.json` = tree or raw, `.csv`, binary files noted)
7. Delete NotebookLM notebook from cloud

**Output:**
```
notebooklm_output/
├── pdfs/                                    # cached PDFs
├── Beat-the-street-report-YYYY-MM-DD/
│   ├── report.md                            # briefing-doc (full text)
│   ├── mindmap.json                         # mind-map (nested tree JSON)
│   ├── infographic.png                      # visual infographic
│   ├── quiz.json                            # quiz questions
│   └── podcast.mp3                          # audio podcast
└── cron.log                                 # daily run log
```

**Config (`.env`):**
```
TELEGRAM_API_ID=...
TELEGRAM_API_HASH=...
TELEGRAM_CHANNELS=@btsreports
DAYS_BACK=1
PDF_LIMIT=20
SLACK_WEBHOOK_URL=...
```

---
