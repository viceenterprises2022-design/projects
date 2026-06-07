#!/usr/bin/env python3
"""
cron_watchdog.py — Scans crontab log files for failures and alerts Slack.

Detection: Python tracebacks, ERROR/CRITICAL entries, nonzero exit codes.
State: Tracks last-checked byte offset per log to avoid re-alerting.
Usage:
  venv/bin/python cron_watchdog.py          # check + alert on failures
  venv/bin/python cron_watchdog.py --dry-run # report only, no Slack
  venv/bin/python cron_watchdog.py --reset   # reset state, recheck all logs
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

STATE_FILE = Path.home() / ".opencode" / "cron_watchdog_state.json"
LOG_DIR = Path.home() / "Desktop" / "Projects" / "scripts" / "logs"
SCRIPTS_DIR = LOG_DIR.parent
SLACK_SCRIPT = SCRIPTS_DIR / "send_slack.py"
VENV_PYTHON = SCRIPTS_DIR / "venv" / "bin" / "python"

ERROR_PATTERNS = re.compile(
    r"(Traceback \(most recent call last\)|"
    r"ModuleNotFoundError|ImportError|FileNotFoundError|"
    r"PermissionError|KeyError|IndexError|TypeError|ValueError|"
    r"subprocess\.CalledProcessError|ConnectionError|TimeoutError|"
    r"\[ERROR\]|\[CRITICAL\]|CRITICAL|"
    r"exit code \d+|[Ee]rror:|FAILED)"
)

IGNORE_PATTERNS = re.compile(
    r"(using local fallback|"
    r"\[WARN\]|"
    r"Warning:|"
    r"Retrying|"
    r"attempt \d+/\d+)"
)


def get_crontab_jobs() -> list[dict]:
    result = subprocess.run(
        ["crontab", "-l"], capture_output=True, text=True, timeout=10
    )
    if result.returncode != 0:
        print(f"WARN: crontab -l failed: {result.stderr.strip()}")
        return []

    jobs = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split()
        if len(parts) < 6:
            continue

        cmd_part = " ".join(parts[5:])

        log_match = re.search(r">>\s*(\S+)", cmd_part)
        log_file = log_match.group(1) if log_match else None

        name_match = re.search(r"(?:^|\s|/)(\w+)\.py", cmd_part)
        job_name = name_match.group(1) if name_match else "cronjob"

        schedule = " ".join(parts[:5])
        jobs.append({
            "name": job_name,
            "schedule": schedule,
            "cmd": cmd_part[:120],
            "log_file": log_file,
        })
    return jobs


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def resolve_log_path(log_path: str) -> Path | None:
    p = Path(log_path)
    if p.is_absolute():
        return p if p.exists() else None
    candidates = [SCRIPTS_DIR / p, Path.cwd() / p]
    if not p.parts[0] == "logs":
        candidates.insert(0, LOG_DIR / p)
    for c in candidates:
        if c.exists():
            return c.resolve()
    return None


def scan_log(
    log_path: Path, last_offset: int = 0
) -> tuple[list[dict], int]:
    if not log_path.exists():
        return [], 0

    current_size = log_path.stat().st_size

    if current_size <= last_offset:
        return [], current_size

    with open(log_path, "r", errors="replace") as f:
        f.seek(last_offset)
        new_content = f.read()

    errors = []
    lines = new_content.splitlines()

    error_block = []
    in_traceback = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        if "Traceback (most recent call last)" in stripped:
            in_traceback = True
            error_block = [stripped]
            continue

        if in_traceback:
            error_block.append(stripped)
            if stripped and not stripped.startswith(" ") and not stripped.startswith("\t"):
                if error_block:
                    context_start = max(0, i - len(error_block) - 3)
                    context = "\n".join(
                        lines[context_start : i + 1]
                    )
                    errors.append({
                        "line": context_start + last_offset + 1,
                        "type": "traceback",
                        "excerpt": context[-500:],
                    })
                error_block = []
                in_traceback = False
            continue

        if ERROR_PATTERNS.search(stripped):
            if IGNORE_PATTERNS.search(stripped):
                continue
            context_start = max(0, i - 2)
            context = "\n".join(lines[context_start : i + 1])
            errors.append({
                "line": context_start + last_offset + 1,
                "type": "error",
                "excerpt": context[-300:],
            })

    if error_block:
        errors.append({
            "line": last_offset + len(lines) - len(error_block) + 1,
            "type": "traceback",
            "excerpt": "\n".join(error_block)[-500:],
        })

    return errors, current_size


def send_slack_alert(job_errors: list[dict]):
    total_errors = sum(len(e["errors"]) for e in job_errors)
    if total_errors == 0:
        return

    lines = [
        f":warning: *Cron Watchdog* — {total_errors} failure(s) detected",
        f"Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    for job in job_errors:
        lines.append(f"*{job['name']}* ({job['log_file'] or 'no log'}):")
        for err in job["errors"][:3]:
            excerpt = err["excerpt"].replace("```", "'''")
            lines.append(f"```\n{excerpt}\n```")
        if len(job["errors"]) > 3:
            lines.append(f"  ... +{len(job['errors']) - 3} more errors")

    message = "\n".join(lines)

    webhook_url = os.environ.get("SLACK_WEBHOOK_SYSTEM_ALERTS") or os.environ.get("SLACK_WEBHOOK_URL")
    cmd = [str(VENV_PYTHON), str(SLACK_SCRIPT), "--text", message]
    if webhook_url:
        cmd += ["--webhook-url", webhook_url]

    result = subprocess.run(
        cmd,
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        print(f"Slack send failed: {result.stderr.strip()}")
    else:
        print(f"Slack alert sent ({total_errors} failures)")


def main():
    dry_run = "--dry-run" in sys.argv
    do_reset = "--reset" in sys.argv

    jobs = get_crontab_jobs()
    if not jobs:
        print("No crontab jobs found.")
        return 1

    state = {} if do_reset else load_state()
    job_errors = []

    print(f"Cron Watchdog — {len(jobs)} jobs, {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'Job':<30} {'Log':<35} {'Errors':>8}")
    print("-" * 75)

    for job in jobs:
        log_file = job["log_file"]
        if not log_file:
            print(f"{job['name']:<30} {'<no log>':<35} {'N/A':>8}")
            continue

        log_path = resolve_log_path(log_file)
        if not log_path:
            print(f"{job['name']:<30} {log_file:<35} {'MISSING':>8}")
            continue

        last_offset = state.get(str(log_path), 0)
        errors, new_size = scan_log(log_path, last_offset)
        state[str(log_path)] = new_size

        if errors:
            job_errors.append({
                "name": job["name"],
                "log_file": str(log_path),
                "errors": errors,
            })
        print(
            f"{job['name']:<30} {str(log_path)[-34:]:<35} {len(errors):>8}"
        )

    save_state(state)

    if job_errors:
        print(f"\n{sum(len(e['errors']) for e in job_errors)} total failures")
        if not dry_run:
            send_slack_alert(job_errors)
        else:
            print("DRY-RUN — would send Slack alert")
            for job in job_errors:
                for err in job["errors"][:1]:
                    print(f"  {job['name']}: {err['excerpt'][:150]}")
    else:
        print("\nNo failures detected.")

    return 1 if job_errors else 0


if __name__ == "__main__":
    sys.exit(main())
