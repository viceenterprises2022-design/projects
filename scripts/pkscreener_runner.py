#!/usr/bin/env python3
"""
PKScreener Runner — automated NSE stock screener with Telegram delivery.
Runs key scan strategies after market hours and sends results.
"""

import os
import re
import sys
import subprocess
import datetime
import requests
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
VENV_PYTHON = "/home/vreddy1/Desktop/Projects/pkscreener_venv/bin/python"
PKS_DIR = "/home/vreddy1/Desktop/Projects/pkscreener"
PKS_SCRIPT = os.path.join(PKS_DIR, "pkscreener", "pkscreenercli.py")
LOG_DIR = Path("/home/vreddy1/Desktop/Projects/scripts/pkscreener_output")
TOKEN = "8770565112:AAGy9q-BMWsgvU4RQUQDyeNXa282Vme9uG4"
CHAT_ID = "7246234100"
TIMEOUT_SEC = 300  # per scan

# ── Scan Strategies ──────────────────────────────────────────────────────────
# Format: (label, options_string)
SCANS = [
    ("Nifty50 — Probable Breakouts",        "X:1:1"),
    ("Nifty50 — Bullish RSI & MACD",        "X:1:13"),
    ("Nifty50 — Strong Buy Signals",        "X:1:44"),
    ("NiftyAll — Probable Breakouts",       "X:12:1"),
    ("NiftyAll — SuperTrend Uptrend",       "X:12:24"),
    ("NiftyAll — Strong Buy Signals",       "X:12:44"),
    ("NiftyAll — Breaking Out Now",         "X:12:23"),
    ("NiftyAll — Bullish RSI & MACD",       "X:12:13"),
]

# ── Helpers ───────────────────────────────────────────────────────────────────
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b[()][A-Za-z0-9]|\x1b[=>]|[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
RICH_RE = re.compile(r"\[/?[^\[\]]+\]")
SETTERM_RE = re.compile(r"^setterm:.*$", re.MULTILINE)


def strip_markup(text: str) -> str:
    text = ANSI_RE.sub("", text)
    text = RICH_RE.sub("", text)
    text = SETTERM_RE.sub("", text)
    # Remove blank lines
    lines = [l for l in text.splitlines() if l.strip()]
    return "\n".join(lines)


def send_telegram(text: str, parse_mode: str = "HTML") -> bool:
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    # Chunk into ≤4000 char messages
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    ok = True
    for chunk in chunks:
        try:
            r = requests.post(url, json={"chat_id": CHAT_ID, "text": chunk,
                                         "parse_mode": parse_mode}, timeout=15)
            if not r.json().get("ok"):
                ok = False
        except Exception as e:
            print(f"[Telegram] Error: {e}")
            ok = False
    return ok


def run_scan(label: str, options: str, log_file: Path) -> str:
    """Run a single PKScreener scan via PTY to capture rich terminal output."""
    import pty, select, termios

    cmd = [
        VENV_PYTHON,
        "-W", "ignore",
        PKS_SCRIPT,
        "-a", "Y",
        "-e",
        "-o", options,
    ]
    env = os.environ.copy()
    env["RUNNER"] = "1"
    env["PYTHONPATH"] = PKS_DIR
    env["PYTHONWARNINGS"] = "ignore"
    env["TF_CPP_MIN_LOG_LEVEL"] = "3"
    env["COLUMNS"] = "220"
    env["LINES"] = "50"

    output_bytes = b""
    try:
        master_fd, slave_fd = pty.openpty()
        proc = subprocess.Popen(
            cmd,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=PKS_DIR,
            env=env,
            close_fds=True,
        )
        os.close(slave_fd)
        import time
        deadline = time.time() + TIMEOUT_SEC
        while time.time() < deadline:
            try:
                r, _, _ = select.select([master_fd], [], [], 1.0)
                if r:
                    chunk = os.read(master_fd, 8192)
                    if not chunk:
                        break
                    output_bytes += chunk
                elif proc.poll() is not None:
                    # Drain remaining
                    try:
                        while True:
                            chunk = os.read(master_fd, 8192)
                            if not chunk:
                                break
                            output_bytes += chunk
                    except OSError:
                        pass
                    break
            except OSError:
                break
        os.close(master_fd)
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        output_bytes = b"[TIMEOUT]"
    except Exception as e:
        output_bytes = f"[ERROR: {e}]".encode()

    output = output_bytes.decode("utf-8", errors="replace")
    clean = strip_markup(output)
    log_file.write_text(clean, encoding="utf-8")
    return clean


def extract_stocks(output: str) -> list[str]:
    """Extract stock symbols from PKScreener tabular output."""
    lines = []
    for line in output.splitlines():
        # PKScreener rows typically start with stock symbol (2-20 caps)
        stripped = line.strip()
        if re.match(r'^[A-Z][A-Z0-9&\-]{1,19}\s', stripped):
            lines.append(stripped[:120])  # cap line length
    return lines


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    run_ts = now.strftime("%Y%m%d_%H%M")

    print(f"[PKScreener Runner] {date_str} {time_str} — starting {len(SCANS)} scans")

    header = f"<b>PKScreener NSE Scan — {date_str} {time_str} IST</b>\n"
    send_telegram(header)

    total_hits = 0

    for label, options in SCANS:
        print(f"  Running: {label} ({options}) ...")
        log_file = LOG_DIR / f"{run_ts}_{options.replace(':', '_')}.txt"
        output = run_scan(label, options, log_file)
        stocks = extract_stocks(output)

        if stocks:
            total_hits += len(stocks)
            lines = "\n".join(stocks[:30])  # max 30 stocks per scan
            msg = f"<b>{label}</b> [{options}] — {len(stocks)} hits\n<pre>{lines}</pre>"
        else:
            msg = f"<b>{label}</b> [{options}] — no results"

        print(f"    → {len(stocks)} stocks")
        send_telegram(msg)

    footer = f"\n<b>Done.</b> {total_hits} total hits across {len(SCANS)} scans."
    send_telegram(footer)
    print(f"[PKScreener Runner] complete — {total_hits} total hits")


if __name__ == "__main__":
    main()
