#!/usr/bin/env python3
"""Crypto news → NotebookLM infographic pipeline."""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

NLM = ["/home/vreddy1/Desktop/Projects/scripts/venv/bin/notebooklm"]
OUTPUT_DIR = Path("notebooklm_output/crypto_news")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TODAY = datetime.now().strftime("%Y-%m-%d")
NB_TITLE = f"Crypto Daily Brief — {TODAY}"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8770565112:AAGy9q-BMWsgvU4RQUQDyeNXa282Vme9uG4")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7246234100")


def p(msg):
    print(msg, flush=True)


def nlm(*args, capture=True):
    cmd = NLM + list(str(a) for a in args)
    p(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=capture, text=True)
    if result.returncode != 0 and capture:
        p(f"  [WARN] exit {result.returncode}: {result.stderr.strip()[:300]}")
    return result


def nlm_json(*args):
    result = nlm(*args, "--json")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def step_run_search() -> str:
    p("\n[1] Fetching crypto news...")
    result = subprocess.run(
        [sys.executable, "crypto_news_search.py", "--report", "--num", "10"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        p(f"  Search failed: {result.stderr.strip()[:200]}")
        sys.exit(1)
    report = result.stdout.strip()
    src_path = OUTPUT_DIR / f"crypto_report_{TODAY}.txt"
    src_path.write_text(report)
    p(f"  Report saved → {src_path} ({len(report)} chars)")
    return str(src_path)


def step_create_notebook() -> str:
    p(f"\n[2] Creating notebook: {NB_TITLE}")
    data = nlm_json("create", NB_TITLE)
    nb_id = data.get("notebook", {}).get("id", "")
    if not nb_id:
        p("  FAILED. Run 'notebooklm login' first.")
        sys.exit(1)
    p(f"  ID: {nb_id}")
    return nb_id


def step_upload_source(nb_id: str, src_path: str) -> str:
    p(f"\n[3] Uploading source...")
    data = nlm_json("source", "add", src_path, "--notebook", nb_id)
    sid = data.get("source", {}).get("id", "")
    if not sid:
        p("  FAILED to upload source.")
        sys.exit(1)
    p(f"  Source ID: {sid[:8]}")
    return sid


def step_wait_for_source(nb_id: str, sid: str):
    p(f"\n[4] Waiting for source processing...")
    nlm("source", "wait", sid, "-n", nb_id, "--timeout", "600", capture=False)


def step_generate_infographic(nb_id: str) -> str:
    p(f"\n[5] Generating infographic...")
    desc = "Visual summary of today's crypto news across Bitcoin, Ethereum, Solana, RWA, stablecoins, onchain milestones, growth, and price predictions."
    data = nlm_json("generate", "infographic", desc,
                    "--orientation", "landscape",
                    "--detail", "detailed",
                    "--style", "bento-grid",
                    "--notebook", nb_id,
                    "--wait", "--retry", "3")
    p(f"  Response: {json.dumps(data)[:200]}")
    infographic_id = data.get("artifact", {}).get("id", "") or data.get("task_id", "")
    if infographic_id:
        p(f"  Infographic task: {infographic_id[:12]}")
    else:
        if isinstance(data, dict):
            for k in data:
                p(f"  Key '{k}': {str(data[k])[:120]}")
    return infographic_id


def step_download_infographic(nb_id: str) -> str:
    p(f"\n[6] Downloading infographic...")
    out_path = str(OUTPUT_DIR / f"crypto_daily_{TODAY}.png")
    result = nlm("download", "infographic", out_path, "--notebook", nb_id)
    if result.returncode == 0:
        size = Path(out_path).stat().st_size if Path(out_path).exists() else 0
        p(f"  Downloaded → {out_path} ({size:,} bytes)")
        return out_path
    fallback = OUTPUT_DIR / f"crypto_daily_{TODAY}.png"
    if fallback.exists():
        p(f"  Found → {fallback} ({fallback.stat().st_size:,} bytes)")
        return str(fallback)
    p("  No infographic file found.")
    return ""


def step_send_telegram(info_path: str, nb_id: str):
    if not info_path or not Path(info_path).exists():
        p("\n[TG] No infographic to send.")
        return

    p(f"\n[TG] Sending to Telegram...")
    import requests
    caption = f"📡 Crypto Daily Brief — {TODAY}\nNotebookLM Infographic"
    for attempt in range(2):
        try:
            with open(info_path, "rb") as f:
                r = requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument",
                    data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
                    files={"document": f},
                    timeout=120
                )
                r.raise_for_status()
            p("  ✓ Telegram sent")
            return
        except Exception as e:
            p(f"  ✗ Attempt {attempt+1}: {e}")
    p("  ✗ Telegram delivery failed after 2 attempts")


def step_delete_notebook(nb_id: str):
    p(f"\n[7] Cleaning up notebook...")
    nlm("delete", "-n", nb_id, "-y", capture=False)
    p(f"  ✓ Deleted notebook {nb_id[:12]}")


def main():
    p("=" * 50)
    p(f"Crypto News → NotebookLM Infographic  [{TODAY}]")
    p("=" * 50)

    src_path = step_run_search()
    nb_id = step_create_notebook()
    sid = step_upload_source(nb_id, src_path)
    step_wait_for_source(nb_id, sid)
    aid = step_generate_infographic(nb_id)
    info_path = step_download_infographic(nb_id)

    # ── Save to Obsidian ─────────────────────────────────────────────
    p("\n[6.5] Saving to Obsidian vault...")
    try:
        from obsidian_integration import save_to_obsidian
        save_to_obsidian(
            source_type="other",
            title=f"Crypto Daily Brief — {TODAY}",
            source_id=f"crypto_report_{TODAY}",
            source_url="crypto_news_search.py",
            notebook_id=nb_id,
            report_path=Path(src_path),
            mindmap_path=None,
            infographic_path=Path(info_path) if info_path and Path(info_path).exists() else None,
            additional_tags=["crypto", "bitcoin", "solana", "news"]
        )
    except Exception as obs_err:
        p(f"  [OBSIDIAN ERROR] Failed to integrate with Obsidian: {obs_err}")

    step_delete_notebook(nb_id)

    if not info_path:
        p("\n✗ Infographic generation failed. Not proceeding to Telegram/cron.")
        sys.exit(1)

    p(f"\n✓ Infographic ready: {info_path}")

    if "--telegram" in sys.argv:
        step_send_telegram(info_path, nb_id)

    p(f"\nAll done.")


if __name__ == "__main__":
    nb_id = main()
