#!/usr/bin/env python3
"""
alert_dashboard_alive.py

Cron-friendly dashboard uptime monitor. Runs every 5 minutes via cron.
Checks AlphaEdge dashboard, pixi page, and key API endpoints.
Silent when healthy — alerts Slack on outage and recovery.

State file: /tmp/alert_dashboard_state.json (tracks consecutive failures per check)
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE_URL = "http://localhost:8765"
SLACK_WEBHOOK_URL = os.environ.get(
    "SLACK_WEBHOOK_URL",
    subprocess.run(
        [sys.executable, "-c", "from dotenv import load_dotenv; load_dotenv(); import os; print(os.environ.get('SLACK_WEBHOOK_URL', ''))"],
        capture_output=True, text=True, cwd=Path(__file__).parent
    ).stdout.strip()
)
ALERT_THRESHOLD = 2
STATE_FILE = Path("/tmp/alert_dashboard_state.json")

CHECKS = {
    "dashboard":      ("/",               "text/html",        lambda r: True),
    "pixi":           ("/pixi",           "text/html",        lambda r: True),
    "api-latest":     ("/api/latest",     "application/json", lambda r: r.status_code == 200 and bool(r.json())),
    "api-gainers":    ("/api/gainers-losers", "application/json", lambda r: r.status_code == 200),
}


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def slack_alert(text: str):
    if not SLACK_WEBHOOK_URL:
        return
    try:
        payload = {
            "text": f"⚠️ *AlphaEdge Monitor*\n{text}",
            "username": "AlphaEdge Monitor",
            "icon_emoji": ":robot_face:",
        }
        requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=15)
    except Exception as e:
        print(f"  [WARN] Slack send failed: {e}", flush=True)


def check_endpoint(name: str, path: str, expect_type: str, validator) -> tuple[bool, str]:
    url = f"{BASE_URL}{path}"
    try:
        r = requests.get(url, timeout=10)
        ct = r.headers.get("content-type", "")
        if r.status_code == 200 and expect_type in ct and validator(r):
            return True, "ok"
        detail = f"HTTP {r.status_code} type={ct[:30]}"
        return False, detail
    except requests.ConnectionError:
        return False, "connection refused"
    except requests.Timeout:
        return False, "timeout"
    except Exception as e:
        return False, str(e)


def main():
    state = load_state()
    now = datetime.now(timezone.utc)
    any_failure = False
    results = []

    for name, (path, expect_type, validator) in CHECKS.items():
        ok, detail = check_endpoint(name, path, expect_type, validator)
        prev = state.get(name, {"failures": 0, "alerted_down": False})
        failures = prev["failures"] + (0 if ok else 1)
        alerted_down = prev.get("alerted_down", False)
        alerted_up = prev.get("alerted_up", True)

        if ok:
            if failures > 0:
                failures = 0
            if alerted_down:
                slack_alert(f"✅ *Recovered* — `{name}` is responding again (`{path}`)")
                alerted_down = False
                alerted_up = True
        else:
            any_failure = True
            if failures >= ALERT_THRESHOLD and not alerted_down:
                slack_alert(
                    f"🚨 *Outage* — `{name}` down ({failures} checks failed)\n"
                    f"  Endpoint: `{path}`\n"
                    f"  Error: `{detail}`\n"
                    f"  Time: `{now.strftime('%Y-%m-%d %H:%M:%S UTC')}`"
                )
                alerted_down = True
                alerted_up = False

        state[name] = {"failures": failures, "alerted_down": alerted_down, "alerted_up": alerted_up}
        results.append(f"  {'✓' if ok else '✗'} {name:20s} {detail}")

    save_state(state)
    ts = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    status = "FAIL" if any_failure else "OK"
    print(f"[{ts}] {status}", flush=True)
    for r in results:
        print(r, flush=True)

    if any_failure:
        sys.exit(1)


if __name__ == "__main__":
    main()
