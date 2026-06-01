#!/usr/bin/env python3
"""
monitor_upstox.py — Monitor Upstox API endpoints for health, rate limits, and outages.
Alerts Slack when endpoints fail or return 429 Too Many Requests.
"""

import json
import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
import requests

# Load dotenv to get UPSTOX_TOKEN and SLACK_WEBHOOK_URL
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
UPSTOX_TOKEN = os.environ.get("UPSTOX_TOKEN")

STATE_FILE = Path("/tmp/monitor_upstox_state.json")
ALERT_THRESHOLD = 2

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}

def save_state(state: dict):
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2))
    except OSError as e:
        print(f"[WARN] Failed to write state file: {e}")

def slack_alert(text: str, is_recovery: bool = False):
    if not SLACK_WEBHOOK_URL:
        print("[WARN] SLACK_WEBHOOK_URL not configured")
        return
    try:
        color = "#36a64f" if is_recovery else "#dc3545"
        emoji = "✅" if is_recovery else "🚨"
        payload = {
            "username": "Upstox API Monitor",
            "icon_emoji": ":bar_chart:",
            "attachments": [
                {
                    "color": color,
                    "title": f"{emoji} Upstox API Status Alert",
                    "text": text,
                    "mrkdwn_in": ["text"]
                }
            ]
        }
        r = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"[WARN] Slack alert failed: {e}")

def probe_upstox() -> dict:
    results = {}
    if not UPSTOX_TOKEN:
        return {"error": "UPSTOX_TOKEN missing in .env"}

    headers = {
        "Authorization": f"Bearer {UPSTOX_TOKEN}",
        "Accept": "application/json"
    }

    # 1. Probe Quotes API
    try:
        r = requests.get(
            "https://api.upstox.com/v2/market-quote/quotes",
            headers=headers,
            params={"instrument_key": "NSE_INDEX|Nifty 50"},
            timeout=10
        )
        if r.status_code == 200:
            results["quotes"] = {"ok": True, "code": r.status_code, "msg": "OK"}
        else:
            results["quotes"] = {"ok": False, "code": r.status_code, "msg": r.text[:200]}
    except Exception as e:
        results["quotes"] = {"ok": False, "code": 0, "msg": str(e)}

    # 2. Probe Expiries (Option Contract) API
    try:
        r = requests.get(
            "https://api.upstox.com/v2/option/contract",
            headers=headers,
            params={"instrument_key": "NSE_INDEX|Nifty 50"},
            timeout=10
        )
        if r.status_code == 200:
            results["contract"] = {"ok": True, "code": r.status_code, "msg": "OK"}
            # Extract nearest expiry if successful
            data = r.json().get("data", [])
            nearest_expiry = None
            if data and isinstance(data, list):
                if isinstance(data[0], str):
                    nearest_expiry = sorted(data)[0]
                elif isinstance(data[0], dict):
                    nearest_expiry = sorted([x.get("expiry", "") for x in data if x.get("expiry")])[0]
            results["nearest_expiry"] = nearest_expiry
        else:
            results["contract"] = {"ok": False, "code": r.status_code, "msg": r.text[:200]}
            results["nearest_expiry"] = None
    except Exception as e:
        results["contract"] = {"ok": False, "code": 0, "msg": str(e)}
        results["nearest_expiry"] = None

    # 3. Probe Option Chain API (only if nearest_expiry is found)
    expiry = results.get("nearest_expiry")
    if expiry:
        try:
            r = requests.get(
                "https://api.upstox.com/v2/option/chain",
                headers=headers,
                params={"instrument_key": "NSE_INDEX|Nifty 50", "expiry_date": expiry},
                timeout=10
            )
            if r.status_code == 200:
                results["chain"] = {"ok": True, "code": r.status_code, "msg": "OK"}
            else:
                results["chain"] = {"ok": False, "code": r.status_code, "msg": r.text[:200]}
        except Exception as e:
            results["chain"] = {"ok": False, "code": 0, "msg": str(e)}
    else:
        results["chain"] = {"ok": False, "code": 0, "msg": "Skipped (no expiry available)"}

    return results

def main():
    parser = argparse.ArgumentParser(description="Monitor Upstox API")
    parser.add_argument("--dry-run", action="store_true", help="Print status only, skip alerts")
    parser.add_argument("--force-alert", action="store_true", help="Force send alert regardless of state")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%d %H:%M:%S UTC")

    print(f"[{ts}] Running Upstox API Monitor...")
    probes = probe_upstox()

    if "error" in probes:
        print(f"[CRITICAL] {probes['error']}")
        sys.exit(1)

    # Determine overall status
    endpoints = ["quotes", "contract", "chain"]
    all_ok = True
    failed_details = []

    for ep in endpoints:
        p = probes.get(ep, {"ok": False, "code": 0, "msg": "Not run"})
        status_char = "✓" if p["ok"] else "✗"
        code_str = f"HTTP {p['code']}" if p["code"] else "Error"
        print(f"  {status_char} {ep:<10} ({code_str}): {p['msg']}")
        if not p["ok"]:
            all_ok = False
            failed_details.append(f"`{ep}` -> *{code_str}* ({p['msg']})")

    # State management
    state = load_state()
    prev_failures = state.get("failures", 0)
    alerted_down = state.get("alerted_down", False)

    if all_ok:
        failures = 0
        state["failures"] = 0
        if alerted_down and not args.dry_run:
            slack_alert("*Recovered* — Upstox API is responding correctly again across all endpoints.", is_recovery=True)
            state["alerted_down"] = False
        print(f"[{ts}] Overall: OK")
    else:
        failures = prev_failures + 1
        state["failures"] = failures
        print(f"[{ts}] Overall: FAIL (Consecutive failures: {failures})")

        if (failures >= ALERT_THRESHOLD and not alerted_down) or args.force_alert:
            if not args.dry_run:
                error_msg = "\n".join(failed_details)
                alert_text = (
                    f"*Outage Detected* — Upstox API is failing ({failures} consecutive check failures)\n\n"
                    f"*Failing Endpoints:*\n{error_msg}\n\n"
                    f"*Time:* `{ts}`"
                )
                slack_alert(alert_text, is_recovery=False)
                state["alerted_down"] = True

    if not args.dry_run:
        save_state(state)

    if not all_ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
