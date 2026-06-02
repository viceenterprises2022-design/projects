# Usage Tracker — Design Spec

## Purpose
CLI tool that tracks desktop window activity + agent/daemon/systemd uptime, stores to SQLite, and produces per-app/per-agent daily/weekly reports.

## Architecture

Single Python file: `usage_tracker.py`. Two modes:
- **Daemon mode** (`start`/`stop`) — background loop polling every 5s
- **Query mode** (`status`/`report`) — reads DB, prints reports

## Database Schema (`~/.usage_tracker.db`)

```sql
CREATE TABLE window_events (
    id INTEGER PRIMARY KEY,
    app TEXT NOT NULL,
    title TEXT NOT NULL,
    started_at INTEGER NOT NULL,
    ended_at INTEGER,
    duration_seconds INTEGER
);

CREATE TABLE process_snapshots (
    id INTEGER PRIMARY KEY,
    ts INTEGER NOT NULL,
    pid INTEGER NOT NULL,
    name TEXT NOT NULL,
    cmdline TEXT,
    cpu REAL,
    rss_mb REAL
);

CREATE TABLE systemd_events (
    id INTEGER PRIMARY KEY,
    ts INTEGER NOT NULL,
    unit TEXT NOT NULL,
    state TEXT NOT NULL,
    duration_seconds INTEGER
);

CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

## Wayland Window Detection
Use `gdbus` call to `org.gnome.Shell.Eval` — extracts `get_wm_class()` and `get_title()`. Single subprocess, ~3ms. X11 fallback via `xdotool getactivewindow getwindowname`.

## Process Monitoring
Scan `/proc` every 30s for target process names (multica, python scripts). Read `/proc/<pid>/status` and `/proc/<pid>/cmdline`. Systemd units via `systemctl --user list-units`.

## Resource Budget
- CPU: ~0.15% of one core
- Memory: ~12MB RSS
- Disk: ~3MB/day

## CLI Interface

```
usage-tracker start              Start daemon
usage-tracker stop               Stop daemon
usage-tracker status             Show daemon status + live window + agents
usage-tracker report             Today's report
usage-tracker report --period week
usage-tracker report --app <name>
usage-tracker report --agent     Focus on agents only
```

## Reporting
- ASCII bar charts using filled blocks (██)
- Daily: app breakdown with percentages, agent uptime
- Weekly: day-by-day bar summary, top apps
- Per-app drill-down: top window titles within that app
- Idle detection: screen lock or >5min no input
