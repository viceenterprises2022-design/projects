# Runbook

## 🖥️ System-Level Services (Requires sudo)
_(was: ⚙️ Systemd Services)_


| Service | Description | Port |
|:--- |:--- |:--- |
| `alphaedge-api.service` | AlphaEdge Market Intelligence API (FastAPI + uvicorn) | `:8765` |
| `multica-daemon.service` | Multica Agent Runtime (Claude, Codex, Antigravity, Hermes, Cursor) | — |

```bash
# Check status
sudo systemctl status alphaedge-api
sudo systemctl status multica-daemon

# Restart
sudo systemctl restart alphaedge-api
sudo systemctl restart multica-daemon

# Logs
journalctl -u alphaedge-api -f
journalctl -u multica-daemon -f
```


## 👤 User-Level Services (AlphaEdge Collectors, No sudo required)
_(was: ⚙️ Systemd Services)_


These services manage persistent, real-time index quotes, option chains, and intraday PCR data.

| Service | Script / Daemon | Description |
|:--- |:--- |:--- |
| `alphaedge-collector.service` | `collector.py --loop --interval 1` | Main signal engine (Trend, VIX, etc.) writing to `alphaedge.db`. |
| `alphaedge-options-collector.service` | `options_cli.py` | Live 5-second Options Matrix builder for `intraday_options_cli.db`. |
| `alphaedge-oi-collector.service` | `oi_collector_daemon.py` | Intraday PCR/OI trend collector writing to `intraday_oi.db`. |

```bash
# Enable to start automatically on system boot
systemctl --user enable alphaedge-collector alphaedge-options-collector alphaedge-oi-collector

# Start or Restart
systemctl --user restart alphaedge-collector alphaedge-options-collector alphaedge-oi-collector

# Check status
systemctl --user status alphaedge-collector alphaedge-options-collector alphaedge-oi-collector

# Live Logs
journalctl --user -u alphaedge-collector -f
journalctl --user -u alphaedge-options-collector -f
journalctl --user -u alphaedge-oi-collector -f
```

> [!TIP]
> You can also run the local backup shell script `bash start_collectors.sh` which cleanly restarts all of them in a completely disowned background environment.

---


## Recovery Procedure
_(was: 🛠️ Troubleshooting & Database Recovery (GBrain / PGlite))_

To repair the database without losing your stored data (avoiding database deletion):

1. **Download PostgreSQL Utilities**:
   Download the PostgreSQL package matching your major version (e.g., PostgreSQL 17 for Ubuntu/Debian) to extract administrative tools without needing system-wide installation or `sudo`:
   ```bash
   apt-get download postgresql-17
   dpkg -x postgresql-17_*.deb ./extracted_pg
   ```

2. **Clean up Stale Locks**:
   Ensure `gbrain-autopilot` is stopped and remove any stale postmaster PID lock file:
   ```bash
   systemctl --user stop gbrain-autopilot.service
   rm -f ~/.gbrain/brain.pglite/postmaster.pid
   ```

3. **Verify control file**:
   Check the current system state using `pg_controldata`:
   ```bash
   ./extracted_pg/usr/lib/postgresql/17/bin/pg_controldata -D ~/.gbrain/brain.pglite
   ```

4. **Reset Write-Ahead Log (WAL)**:
   Force a reset of the WAL using `pg_resetwal` to bypass the corrupted checkpoint record and return the database to a clean, runnable state:
   ```bash
   ./extracted_pg/usr/lib/postgresql/17/bin/pg_resetwal -f -D ~/.gbrain/brain.pglite
   ```

5. **Clean Up & Restart Daemon**:
   Delete the extracted utility directory and restart the autopilot service:
   ```bash
   rm -rf ./extracted_pg postgresql-17_*.deb
   systemctl --user start gbrain-autopilot.service
   ```

---


## 🤖 Antigravity CLI — AI Agent IDE
_(was: 🛠️ Troubleshooting & Database Recovery (GBrain / PGlite))_

*VS Code-based agent CLI with `chat` mode (ask/edit/agent). Replaces Gemini CLI.*

**Version:** v2.0.6 (Electron, `/usr/share/antigravity/`)
**Binary:** `/usr/bin/antigravity` → launcher → `antigravity` (ELF, 197MB)

**Usage:**
```bash
antigravity --version
antigravity chat "prompt"                        # agent mode
antigravity chat --mode ask "question"           # Q&A mode
antigravity chat --mode edit "change this"       # edit mode
```

**Upgrade:**
Download latest tar.gz, extract, then:
```bash
sudo cp extracted/Antigravity-x64/antigravity /usr/share/antigravity/
sudo cp extracted/Antigravity-x64/*.so /usr/share/antigravity/
sudo cp extracted/Antigravity-x64/*.pak /usr/share/antigravity/
sudo cp extracted/Antigravity-x64/*.bin /usr/share/antigravity/
sudo cp extracted/Antigravity-x64/icudtl.dat /usr/share/antigravity/
```

---


## 📡 Crypto Daily News — AI-Powered Crypto Briefing
_(was: 🛠️ Troubleshooting & Database Recovery (GBrain / PGlite))_


*Daily crypto news summaries across 8 categories, delivered to Telegram at 8:00 AM IST.*

| Script | Description |
|:--- |:--- |
| `crypto_news_search.py` | Fetches top crypto stories via Exa API for BTC, ETH, SOL, RWA, Stablecoins, Onchain, Growth, and Price & Predictions. Each article gets an AI-generated 1-sentence summary. |
| `crypto_to_notebooklm.py` | Wraps `crypto_news_search.py --report` → creates NotebookLM notebook → generates infographic → sends to Telegram. Used by cron at 8AM IST. |

**Features:**
- 8 curated search topics with Exa's neural search (last 3 days)
- AI-generated summaries per article (no links to click)
- Rich terminal dashboard mode (`--report`)
- NotebookLM infographic pipeline: news → bento-grid PNG → Telegram

**Usage:**
```bash
# Terminal report
python3 crypto_news_search.py --report --num 10

# Full infographic pipeline (with Telegram delivery)
python3 crypto_to_notebooklm.py --telegram
```

**Cron (8:00 AM IST, already installed):**
```
0 8 * * * cd /home/vreddy1/Desktop/Projects/scripts && python3 crypto_to_notebooklm.py --telegram >> logs/crypto_news_cron.log 2>&1
```

**Config (`.env`):**
```
EXA_API_KEY=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

---


## 📈 PKScreener — NSE Automated Stock Scanner
_(was: 🛠️ Troubleshooting & Database Recovery (GBrain / PGlite))_


Automated NSE stock screening using [PKScreener](https://github.com/pkjmesra/PKScreener) with Telegram delivery.

**Setup**
```bash
# Python 3.12 venv at:
/home/vreddy1/Desktop/Projects/pkscreener_venv

# PKScreener repo at:
/home/vreddy1/Desktop/Projects/pkscreener

# Wrapper script:
python3 pkscreener_runner.py
```

**Scan Strategies** (8 scans, runs on weekdays):
| Scan | Options |
|------|---------|
| Nifty50 — Probable Breakouts | X:1:1 |
| Nifty50 — Bullish RSI & MACD | X:1:13 |
| Nifty50 — Strong Buy Signals | X:1:44 |
| NiftyAll — Probable Breakouts | X:12:1 |
| NiftyAll — SuperTrend Uptrend | X:12:24 |
| NiftyAll — Strong Buy Signals | X:12:44 |
| NiftyAll — Breaking Out Now | X:12:23 |
| NiftyAll — Bullish RSI & MACD | X:12:13 |

**Cron Schedule** (IST, weekdays only):
```
55 3  * * 1-5   # 9:25 AM IST  — pre-open scan
5  10 * * 1-5   # 3:35 PM IST  — close-of-day scan
30 12 * * 1-5   # 6:00 PM IST  — evening review
```

**Lockfile**: `/tmp/pkscreener_runner.lock` — prevents overlapping cron runs via `fcntl.flock`. If a new cron fires while a previous run is in progress, it exits immediately.

**Orphan guard**: `run_scan()` uses `start_new_session=True` to isolate subprocesses in their own process group and kills the entire group (`os.killpg`) with `SIGTERM` → `SIGKILL` escalation. This prevents worker subprocesses from surviving as orphans when a scan times out or crashes. A `kill_orphan_pkscreener()` call at startup `pkill -9`s any leftover processes from prior crashed runs, preventing the 85-process / 12GB pileup issue.

**Output**: `pkscreener_output/` — per-scan `.txt` logs + Telegram delivery with LTP & % change

**Live LTP**: Each stock symbol is followed by its current price and change via Yahoo Finance (e.g. `ADANIENT  ₹2,345.67 (+1.23%)`). Uses `v8/finance/chart` with parallel `ThreadPoolExecutor` (max 10 workers) — 30 stocks resolve in ~1-2s. Gracefully falls back to bare symbol if Yahoo is unreachable. No new dependencies or env vars required.
