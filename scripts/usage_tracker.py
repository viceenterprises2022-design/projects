#!/usr/bin/env python3
"""usage_tracker.py — Track window/app activity + agent/daemon/systemd uptime.

Usage:
  usage-tracker start              Start daemon
  usage-tracker stop               Stop daemon
  usage-tracker status             Show daemon status + live window + agents
  usage-tracker report             Today's report
  usage-tracker report --period week
  usage-tracker report --app <name>
  usage-tracker report --agent     Focus on agents only
"""

import argparse
import json
import logging
import os
import pwd
import signal
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path.home() / ".usage_tracker.db"
PID_PATH = Path.home() / ".usage_tracker.pid"
LOG_PATH = Path.home() / ".usage_tracker.log"

AGENT_NAMES = {"multica", "codex", "claude", "opencode"}
DAEMON_INTERVAL = 5
PROCESS_SCAN_INTERVAL = 30
SYSTEMD_SCAN_INTERVAL = 60

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("usage_tracker")


# ─── Database ───────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS window_events (
            id INTEGER PRIMARY KEY,
            app TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            started_at INTEGER NOT NULL,
            ended_at INTEGER,
            duration_seconds INTEGER
        );
        CREATE TABLE IF NOT EXISTS process_snapshots (
            id INTEGER PRIMARY KEY,
            ts INTEGER NOT NULL,
            pid INTEGER NOT NULL,
            name TEXT NOT NULL,
            cmdline TEXT,
            cpu REAL,
            rss_mb REAL
        );
        CREATE TABLE IF NOT EXISTS systemd_events (
            id INTEGER PRIMARY KEY,
            ts INTEGER NOT NULL,
            unit TEXT NOT NULL,
            state TEXT NOT NULL,
            duration_seconds INTEGER
        );
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_window_app ON window_events(app);
        CREATE INDEX IF NOT EXISTS idx_window_started ON window_events(started_at);
        CREATE INDEX IF NOT EXISTS idx_systemd_unit ON systemd_events(unit);
    """)
    conn.commit()
    return conn


def get_conn():
    return sqlite3.connect(DB_PATH)


def get_config():
    conn = get_conn()
    cur = conn.execute("SELECT key, value FROM metadata")
    cfg = dict(cur.fetchall())
    conn.close()
    return cfg


def set_config(key, value):
    conn = get_conn()
    conn.execute(
        "INSERT INTO metadata (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=?",
        (key, value, value),
    )
    conn.commit()
    conn.close()


# ─── Display Server Detection ───────────────────────────────────

def detect_display_server():
    session_type = os.environ.get("XDG_SESSION_TYPE", "")
    if session_type == "x11":
        return "x11"
    return "wayland"


# ─── Window Detection ────────────────────────────────────────────

def get_active_window_x11():
    try:
        title = subprocess.run(
            ["xdotool", "getactivewindow", "getwindowname"],
            capture_output=True, text=True, timeout=3
        ).stdout.strip()
        pid_out = subprocess.run(
            ["xdotool", "getactivewindow", "getwindowpid"],
            capture_output=True, text=True, timeout=3
        ).stdout.strip()
        if not title:
            return None
        app = _app_from_pid(pid_out) if pid_out else _app_from_title(title)
        return (app, title)
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        return None


def _app_from_title(title):
    title_lower = title.lower()
    known = {
        "firefox": "Firefox", "mozilla": "Firefox",
        "chromium": "Chromium", "chrome": "Chrome",
        "code": "Code", "vscode": "Code",
        "terminal": "Terminal", "gnome-terminal": "Terminal",
        "slack": "Slack", "discord": "Discord",
        "spotify": "Spotify", "thunderbird": "Thunderbird",
        "libreoffice": "LibreOffice", "writer": "LibreOffice",
        "nautilus": "Files", "files": "Files",
        "settings": "Settings",
        "brave": "Brave", "edge": "Edge",
        "obsidian": "Obsidian",
        "telegram": "Telegram",
    }
    for key, val in known.items():
        if key in title_lower:
            return val
    return title.split(" - ")[0].split(" — ")[0].strip() or title


def _app_from_pid(pid_str):
    try:
        pid = int(pid_str)
        with open(f"/proc/{pid}/comm") as f:
            comm = f.read().strip()
        return comm.capitalize()
    except (ValueError, FileNotFoundError, OSError):
        return "Unknown"


def get_active_window_wayland():
    known_apps = _scan_interactive_processes()
    if known_apps:
        app = known_apps[0]
        # Try to get more detail from cmdline
        if app.get("cmdline"):
            return (app["name"], app["cmdline"][:120])
        return (app["name"], "")
    return ("Unknown", "")


def _scan_interactive_processes():
    uid = os.getuid()
    results = []
    for pid_dir in Path("/proc").iterdir():
        if not pid_dir.name.isdigit():
            continue
        try:
            status = (pid_dir / "status").read_text().split("\n")
            status_map = {}
            for line in status:
                if ":" in line:
                    k, v = line.split(":", 1)
                    status_map[k.strip()] = v.strip()
            proc_uid = int(status_map.get("Uid", "-1").split("\t")[0])
            if proc_uid != uid:
                continue
            state = status_map.get("State", "?")[0]
            if state not in ("S", "D", "R"):
                continue
            name = status_map.get("Name", "")
            comm = (pid_dir / "comm").read_text().strip()
            cmdline = (pid_dir / "cmdline").read_text().replace("\0", " ").strip() if (pid_dir / "cmdline").exists() else ""
            if not name or name.startswith("kworker"):
                continue
            # Focus on interactive apps
            if comm in ("gnome-shell", "Xorg", "systemd", "sd-pam"):
                continue
            env = (pid_dir / "environ").read_bytes() if (pid_dir / "environ").exists() else b""
            # Check for wayland display or XDG session
            if b"WAYLAND_DISPLAY" not in env and b"DISPLAY" not in env and b"QT_QPA_PLATFORM" not in env:
                continue
            pid = int(pid_dir.name)
            tty_nr = status_map.get("Tgid", "0")
            results.append({
                "pid": pid,
                "name": name,
                "comm": comm,
                "cmdline": cmdline[:200],
            })
        except (FileNotFoundError, PermissionError, ValueError, OSError):
            continue
    return results


def get_active_window():
    display = detect_display_server()
    if display == "x11":
        result = get_active_window_x11()
        if result:
            return result
    return get_active_window_wayland()


# ─── Process Scanning ────────────────────────────────────────────

def scan_processes():
    uid = os.getuid()
    results = []
    now = int(time.time())
    for pid_dir in Path("/proc").iterdir():
        if not pid_dir.name.isdigit():
            continue
        try:
            pid = int(pid_dir.name)
            status = (pid_dir / "status").read_text().split("\n")
            status_map = {}
            for line in status:
                if ":" in line:
                    k, v = line.split(":", 1)
                    status_map[k.strip()] = v.strip()
            proc_uid = int(status_map.get("Uid", "-1").split("\t")[0])
            if proc_uid != uid:
                continue
            name = status_map.get("Name", "")
            if not name or name == "":
                continue
            if name in ("gnome-shell", "systemd", "(sd-pam)"):
                continue
            cmdline = (pid_dir / "cmdline").read_text().replace("\0", " ").strip()[:300] if (pid_dir / "cmdline").exists() else ""
            vm_rss = int(status_map.get("VmRSS", "0 kB").split()[0])
            rss_mb = round(vm_rss / 1024, 1) if vm_rss else 0.0
            results.append({
                "pid": pid,
                "name": name,
                "cmdline": cmdline,
                "rss_mb": rss_mb,
            })
        except (FileNotFoundError, PermissionError, ValueError, OSError):
            continue
    return results


# ─── Systemd Monitoring ──────────────────────────────────────────

def get_systemd_units():
    try:
        result = subprocess.run(
            ["systemctl", "--user", "list-units", "--all", "--no-legend", "--no-pager"],
            capture_output=True, text=True, timeout=10
        )
        units = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split(None, 4)
            if len(parts) >= 3:
                units.append({
                    "unit": parts[0],
                    "load": parts[1],
                    "state": parts[2],
                })
        return units
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


# ─── Agent Detection ─────────────────────────────────────────────

def detect_agents(processes):
    agents = []
    for proc in processes:
        name = proc["name"].lower()
        cmdline_lower = proc["cmdline"].lower()
        for agent_name in AGENT_NAMES:
            if agent_name in name or agent_name in cmdline_lower:
                agents.append(proc)
                break
        # Also detect long-running python scripts
        if name == "python3" and any(
            kw in cmdline_lower for kw in ("collector", "daemon", "agent", "bot", "tracker")
        ):
            agents.append(proc)
    return agents


# ─── Idle Detection ──────────────────────────────────────────────

def is_user_idle():
    try:
        result = subprocess.run(
            ["loginctl", "show-session", "$(loginctl | grep $(whoami) | awk '{print $1}')", "-p", "IdleHint"],
            capture_output=True, text=True, timeout=5, shell=True
        )
        return "yes" in result.stdout.lower()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_idle_seconds():
    try:
        result = subprocess.run(
            ["loginctl", "show-session", "$(loginctl | grep $(whoami) | awk '{print $1}')", "-p", "IdleSinceHint"],
            capture_output=True, text=True, timeout=5, shell=True
        )
        if "=" in result.stdout:
            val = result.stdout.split("=", 1)[1].strip()
            if val and val != "0":
                idle_since = int(val) // 1000000
                return int(time.time()) - idle_since
        return 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 0


# ─── Daemon ──────────────────────────────────────────────────────

def is_daemon_running():
    if not PID_PATH.exists():
        return False
    try:
        pid = int(PID_PATH.read_text().strip())
        os.kill(pid, 0)
        return True
    except (ValueError, ProcessLookupError, OSError):
        PID_PATH.unlink(missing_ok=True)
        return False


def start_daemon():
    if is_daemon_running():
        print("Daemon already running")
        return
    init_db()
    pid = os.fork()
    if pid > 0:
        print(f"Daemon started (pid {pid})")
        sys.exit(0)
    os.setsid()
    pid2 = os.fork()
    if pid2 > 0:
        sys.exit(0)
    PID_PATH.write_text(str(os.getpid()))
    _run_daemon()


def stop_daemon():
    if not is_daemon_running():
        print("Daemon not running")
        return
    pid = int(PID_PATH.read_text().strip())
    os.kill(pid, signal.SIGTERM)
    PID_PATH.unlink(missing_ok=True)
    print("Daemon stopped")


def _run_daemon():
    sys.stdin.close()
    conn = init_db()
    last_process_scan = 0
    last_systemd_scan = 0
    current_event_id = None
    running = True
    idle_accumulated = 0

    def handle_sigterm(sig, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)

    log.info("Daemon started")
    dbg_fd = os.open("/tmp/usage_dbg.txt", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    os.write(dbg_fd, f"[{int(time.time())}] _run_daemon started\n".encode())
    os.close(dbg_fd)

    while running:
        now = int(time.time())
        try:
            # Window tracking
            window = get_active_window()
            app = window[0] if window else "Unknown"
            title = window[1] if window else ""

            # Idle detection
            idle = get_idle_seconds()
            if idle > 300:
                idle_accumulated += DAEMON_INTERVAL
                if current_event_id is not None:
                    conn.execute(
                        "UPDATE window_events SET ended_at=?, duration_seconds=? WHERE id=?",
                        (now, now - (conn.execute(
                            "SELECT started_at FROM window_events WHERE id=?",
                            (current_event_id,)
                        ).fetchone() or [now])[0], current_event_id)
                    )
                    conn.commit()
                    current_event_id = None
                time.sleep(DAEMON_INTERVAL)
                continue

            idle_accumulated = 0

            # Check if app changed
            if current_event_id is not None:
                cur = conn.execute(
                    "SELECT app FROM window_events WHERE id=?",
                    (current_event_id,)
                )
                row = cur.fetchone()
                if row and row[0] == app:
                    # Update title if changed
                    conn.execute(
                        "UPDATE window_events SET title=?, ended_at=?, duration_seconds=? WHERE id=?",
                        (title, now, now - (conn.execute(
                            "SELECT started_at FROM window_events WHERE id=?",
                            (current_event_id,)
                        ).fetchone() or [now])[0], current_event_id)
                    )
                    conn.commit()
                    time.sleep(DAEMON_INTERVAL)
                    continue

                # Close current event
                conn.execute(
                    "UPDATE window_events SET ended_at=?, duration_seconds=? WHERE id=?",
                    (now, now - (conn.execute(
                        "SELECT started_at FROM window_events WHERE id=?",
                        (current_event_id,)
                    ).fetchone() or [now])[0], current_event_id)
                )
                conn.commit()

            # Start new event
            cur = conn.execute(
                "INSERT INTO window_events (app, title, started_at) VALUES (?, ?, ?)",
                (app, title, now)
            )
            current_event_id = cur.lastrowid
            conn.commit()

            # Process scan (every 30s)
            if now - last_process_scan >= PROCESS_SCAN_INTERVAL:
                procs = scan_processes()
                for proc in procs:
                    conn.execute(
                        "INSERT INTO process_snapshots (ts, pid, name, cmdline, rss_mb) VALUES (?, ?, ?, ?, ?)",
                        (now, proc["pid"], proc["name"], proc["cmdline"], proc["rss_mb"])
                    )
                conn.commit()
                last_process_scan = now

            # Systemd scan (every 60s)
            if now - last_systemd_scan >= SYSTEMD_SCAN_INTERVAL:
                units = get_systemd_units()
                for unit in units:
                    conn.execute(
                        "INSERT INTO systemd_events (ts, unit, state) VALUES (?, ?, ?)",
                        (now, unit["unit"], unit["state"])
                    )
                conn.commit()
                last_systemd_scan = now

        except Exception as e:
            log.error("Daemon loop error: %s", e)

        time.sleep(DAEMON_INTERVAL)

    # Clean shutdown
    if current_event_id is not None:
        now = int(time.time())
        conn.execute(
            "UPDATE window_events SET ended_at=?, duration_seconds=? WHERE id=?",
            (now, now - (conn.execute(
                "SELECT started_at FROM window_events WHERE id=?",
                (current_event_id,)
            ).fetchone() or [now])[0], current_event_id)
        )
        conn.commit()

    conn.close()
    log.info("Daemon stopped")


# ─── Status Command ──────────────────────────────────────────────

def cmd_status():
    if not is_daemon_running():
        print("Daemon: STOPPED")
        return
    pid = PID_PATH.read_text().strip()
    print(f"Daemon: RUNNING (pid {pid})")
    print()
    window = get_active_window()
    if window:
        print(f"Active Window: {window[0]} - {window[1]}")
    else:
        print("Active Window: Unknown")
    print()
    procs = scan_processes()
    agents = detect_agents(procs)
    if agents:
        print("Detected Agents:")
        for a in agents:
            print(f"  {a['pid']:>7}  {a['name']:<16}  {a['rss_mb']:>6.1f} MB")
    else:
        print("No agents detected")
    print()
    try:
        idle = get_idle_seconds()
        if idle > 60:
            print(f"Idle: {idle // 60}m {idle % 60}s")
        else:
            print("Idle: active")
    except Exception:
        pass


# ─── Report Command ──────────────────────────────────────────────

BAR_WIDTH = 40

def ascii_bar(pct, width=BAR_WIDTH):
    filled = int((pct / 100) * width)
    return "\u2588" * filled + "\u2591" * (width - filled)


def format_seconds(s):
    h, r = divmod(int(s), 3600)
    m, s = divmod(r, 60)
    if h:
        return f"{h}h {m}m"
    return f"{m}m {s}s"


def cmd_report(args):
    period = args.period or "day"
    app_filter = args.app
    agent_only = args.agent
    conn = get_conn()

    if period == "day":
        cutoff = int(time.time()) - 86400
        label = "Today"
    elif period == "week":
        cutoff = int(time.time()) - 604800
        label = "Past 7 Days"
    else:
        cutoff = int(time.time()) - 86400
        label = "Today"

    print(f"{'=' * 60}")
    print(f"  USAGE TRACKER REPORT — {label}")
    print(f"{'=' * 60}")
    print()

    if agent_only:
        _print_agent_report(conn, cutoff)
    else:
        _print_window_report(conn, cutoff, app_filter)
        print()
        _print_agent_report(conn, cutoff)

    conn.close()


def _print_window_report(conn, cutoff, app_filter=None):
    if app_filter:
        rows = conn.execute(
            """SELECT app, title, SUM(duration_seconds) as total
               FROM window_events
               WHERE started_at >= ? AND app = ?
               GROUP BY app, title ORDER BY total DESC""",
            (cutoff, app_filter)
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT app, SUM(duration_seconds) as total
               FROM window_events
               WHERE started_at >= ? AND duration_seconds IS NOT NULL
               GROUP BY app ORDER BY total DESC""",
            (cutoff,)
        ).fetchall()

    if not rows:
        print("  No window activity tracked")
        return

    total = sum(r[-1] for r in rows)
    if total == 0:
        print("  No duration data")
        return

    print("  APP ACTIVITY")
    print(f"  {'App':<30} {'Time':>10} {'%':>5}  Bar")
    print(f"  {'-'*30} {'-'*10} {'-'*5}  {'-'*40}")

    for row in rows:
        if app_filter:
            app, title, secs = row
            label = f"  {title[:28]:<30}"
        else:
            app, secs = row
            label = f"  {app[:28]:<30}"
        pct = (secs / total) * 100
        time_str = format_seconds(secs)
        print(f"{label} {time_str:>10} {pct:>4.0f}%  {ascii_bar(pct)}")

    print(f"\n  Total tracked: {format_seconds(total)}")


def _print_agent_report(conn, cutoff):
    rows = conn.execute(
        """SELECT name, COUNT(*) as samples, ROUND(AVG(rss_mb), 1) as avg_rss,
                  SUM(rss_mb) as total_rss
           FROM process_snapshots
           WHERE ts >= ? AND (
               LOWER(name) IN ('multica', 'codex', 'claude', 'opencode')
               OR LOWER(cmdline) LIKE '%collector%'
               OR LOWER(cmdline) LIKE '%daemon%'
               OR LOWER(cmdline) LIKE '%market%'
               OR LOWER(cmdline) LIKE '%agent%'
           )
           GROUP BY name ORDER BY samples DESC""",
        (cutoff,)
    ).fetchall()

    if not rows:
        print("  No agent/daemon activity tracked")
        return

    print("  AGENTS & DAEMONS")
    print(f"  {'Process':<30} {'Samples':>8} {'Avg RSS':>10}")
    print(f"  {'-'*30} {'-'*8} {'-'*10}")
    for name, samples, avg_rss, total_rss in rows:
        print(f"  {name[:28]:<30} {samples:>8} {avg_rss:>6.1f} MB")

    unit_rows = conn.execute(
        """SELECT unit, COUNT(*) as samples
           FROM systemd_events
           WHERE ts >= ?
           GROUP BY unit ORDER BY samples DESC LIMIT 15""",
        (cutoff,)
    ).fetchall()

    if unit_rows:
        print(f"\n  SYSTEMD UNITS")
        print(f"  {'Unit':<45} {'Samples':>8}")
        print(f"  {'-'*45} {'-'*8}")
        for unit, samples in unit_rows:
            print(f"  {unit[:43]:<45} {samples:>8}")


# ─── CLI ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Desktop usage tracker")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("start", help="Start daemon")
    sub.add_parser("stop", help="Stop daemon")
    sub.add_parser("status", help="Show daemon status")

    report_parser = sub.add_parser("report", help="Show usage report")
    report_parser.add_argument("--period", choices=["day", "week"], default="day")
    report_parser.add_argument("--app", type=str, help="Filter by app name")
    report_parser.add_argument("--agent", action="store_true", help="Focus on agents only")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == "start":
        start_daemon()
    elif args.command == "stop":
        stop_daemon()
    elif args.command == "status":
        cmd_status()
    elif args.command == "report":
        init_db()
        cmd_report(args)


if __name__ == "__main__":
    main()
