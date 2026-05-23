#!/usr/bin/env python3
"""
telegram_to_notebooklm.py

Pipeline:
  1. Read messages from selected Telegram channels (Telethon)
  2. Save as markdown files
  3. Upload to a new NotebookLM notebook
  4. Generate: briefing-doc report, mind-map, audio podcast
  5. Download all artifacts to ./notebooklm_output/

Config via .env:
  TELEGRAM_API_ID      - from my.telegram.org
  TELEGRAM_API_HASH    - from my.telegram.org
  TELEGRAM_CHANNELS    - comma-separated channel usernames, e.g. @durov,@telegram
  TELEGRAM_MSG_LIMIT   - messages per channel (default: 50)
  NOTEBOOKLM_NOTEBOOK_TITLE - notebook title (default: auto-generated)

Usage:
  venv/bin/python telegram_to_notebooklm.py
"""

import asyncio
import os
import sys
import subprocess
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
API_ID    = int(os.environ["TELEGRAM_API_ID"])
API_HASH  = os.environ["TELEGRAM_API_HASH"]
CHANNELS  = [c.strip() for c in os.environ.get("TELEGRAM_CHANNELS", "").split(",") if c.strip()]
MSG_LIMIT = int(os.environ.get("TELEGRAM_MSG_LIMIT", "50"))
NB_TITLE  = os.environ.get(
    "NOTEBOOKLM_NOTEBOOK_TITLE",
    f"Telegram Intel {datetime.now().strftime('%Y-%m-%d %H:%M')}"
)

OUTPUT_DIR = Path("notebooklm_output")
DOCS_DIR   = OUTPUT_DIR / "docs"
OUTPUT_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)

NLM = "notebooklm"  # CLI binary


# ── Helpers ───────────────────────────────────────────────────────────────────
def nlm(*args, capture=True):
    """Run notebooklm CLI command."""
    cmd = [NLM] + list(args)
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=capture, text=True)
    if result.returncode != 0 and capture:
        print(f"  [WARN] exit {result.returncode}: {result.stderr.strip()[:200]}")
    return result


def nlm_json(*args):
    """Run notebooklm CLI and return parsed JSON."""
    result = nlm(*args, "--json")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def strip_rich(text: str) -> str:
    return re.sub(r"\[/?[a-z0-9 _,=#\.]+\]", "", text)


# ── Step 1: Fetch Telegram messages via Telethon ───────────────────────────
async def fetch_channels(channels: list[str]) -> dict[str, list]:
    client = TelegramClient("tg_session", API_ID, API_HASH)
    await client.connect()
    results = {}
    for ch in channels:
        print(f"  Fetching {MSG_LIMIT} messages from {ch}...")
        msgs = []
        async for msg in client.iter_messages(ch, limit=MSG_LIMIT):
            if msg.text:
                msgs.append(msg)
        results[ch] = msgs
        print(f"    → {len(msgs)} messages")
    await client.disconnect()
    return results


# ── Step 2: Save as markdown ──────────────────────────────────────────────────
def save_channel_doc(channel: str, messages: list) -> Path:
    safe_name = channel.lstrip("@").replace("/", "_")
    path = DOCS_DIR / f"{safe_name}.md"
    lines = [f"# Telegram Channel: {channel}\n",
             f"_Fetched {len(messages)} messages on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_\n\n"]
    for msg in reversed(messages):  # chronological
        ts = msg.date.strftime("%Y-%m-%d %H:%M")
        text = msg.text.strip()
        lines.append(f"---\n**[{ts}]**\n\n{text}\n\n")
    path.write_text("".join(lines), encoding="utf-8")
    print(f"  Saved: {path} ({path.stat().st_size} bytes)")
    return path


# ── Step 3: NotebookLM — create + upload ──────────────────────────────────────
def create_notebook() -> str:
    print(f"\nCreating notebook: {NB_TITLE}")
    data = nlm_json("create", NB_TITLE)
    nb_id = data.get("notebook", {}).get("id", "")
    if not nb_id:
        print("ERROR: Failed to create notebook. Run 'notebooklm login' first.")
        sys.exit(1)
    print(f"  Notebook ID: {nb_id}")
    return nb_id


def add_sources(nb_id: str, doc_paths: list[Path]) -> list[str]:
    print("\nUploading sources to NotebookLM...")
    source_ids = []
    for p in doc_paths:
        data = nlm_json("source", "add", str(p), "--notebook", nb_id)
        sid = data.get("source", {}).get("id", "")
        if sid:
            source_ids.append(sid)
            print(f"  ✓ {p.name} → {sid[:8]}...")
        else:
            print(f"  ✗ Failed to add {p.name}")
    return source_ids


def wait_for_sources(nb_id: str, source_ids: list[str]):
    print("\nWaiting for sources to process...")
    for sid in source_ids:
        result = nlm("source", "wait", sid, "-n", nb_id, "--timeout", "300")
        status = "✓" if result.returncode == 0 else "✗"
        print(f"  {status} source {sid[:8]}...")


# ── Step 4: Generate artifacts ────────────────────────────────────────────────
def generate_artifacts(nb_id: str) -> dict:
    artifacts = {}

    print("\nGenerating briefing-doc report...")
    data = nlm_json("generate", "report", "--format", "briefing-doc", "--notebook", nb_id)
    artifacts["report"] = data.get("task_id") or data.get("artifact", {}).get("id", "")

    print("Generating mind-map...")
    data = nlm_json("generate", "mind-map", "--notebook", nb_id)
    artifacts["mind_map"] = data.get("task_id") or data.get("artifact", {}).get("id", "")

    print("Generating audio podcast (deep-dive)...")
    data = nlm_json("generate", "audio", "Comprehensive deep-dive covering all key insights",
                    "--format", "deep-dive", "--notebook", nb_id)
    artifacts["audio"] = data.get("task_id") or data.get("artifact", {}).get("id", "")

    for k, v in artifacts.items():
        print(f"  {k}: task_id={v}")
    return artifacts


# ── Step 5: Wait + Download ───────────────────────────────────────────────────
def wait_and_download(nb_id: str, artifacts: dict):
    print("\nWaiting for artifacts (this can take 5-20 min)...")

    # Report
    if artifacts.get("report"):
        aid = artifacts["report"]
        nlm("artifact", "wait", aid, "-n", nb_id, "--timeout", "900", capture=False)
        out = OUTPUT_DIR / "report.md"
        nlm("download", "report", str(out), "-a", aid, "-n", nb_id, capture=False)
        print(f"  ✓ Report → {out}")

    # Mind-map
    if artifacts.get("mind_map"):
        aid = artifacts["mind_map"]
        nlm("artifact", "wait", aid, "-n", nb_id, "--timeout", "300", capture=False)
        out = OUTPUT_DIR / "mindmap.json"
        nlm("download", "mind-map", str(out), "-a", aid, "-n", nb_id, capture=False)
        print(f"  ✓ Mind-map → {out}")

    # Audio
    if artifacts.get("audio"):
        aid = artifacts["audio"]
        print("  Audio generation takes 10-20 min...")
        nlm("artifact", "wait", aid, "-n", nb_id, "--timeout", "1200", capture=False)
        out = OUTPUT_DIR / "podcast.mp3"
        nlm("download", "audio", str(out), "-a", aid, "-n", nb_id, capture=False)
        print(f"  ✓ Audio → {out}")


# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    if not CHANNELS:
        print("ERROR: Set TELEGRAM_CHANNELS in .env, e.g.: TELEGRAM_CHANNELS=@channel1,@channel2")
        sys.exit(1)

    print(f"=== Telegram → NotebookLM Pipeline ===")
    print(f"Channels : {', '.join(CHANNELS)}")
    print(f"Msg limit: {MSG_LIMIT} per channel")
    print(f"Output   : {OUTPUT_DIR}/\n")

    # 1. Fetch
    print("[1/5] Fetching Telegram messages...")
    channel_msgs = await fetch_channels(CHANNELS)

    # 2. Save docs
    print("\n[2/5] Saving channel docs...")
    doc_paths = []
    for ch, msgs in channel_msgs.items():
        if msgs:
            doc_paths.append(save_channel_doc(ch, msgs))

    if not doc_paths:
        print("No messages fetched. Check channel names and Telegram auth.")
        sys.exit(1)

    # 3. Create notebook + upload
    print("\n[3/5] Creating NotebookLM notebook...")
    nb_id = create_notebook()
    source_ids = add_sources(nb_id, doc_paths)
    wait_for_sources(nb_id, source_ids)

    # 4. Generate
    print("\n[4/5] Generating artifacts...")
    artifacts = generate_artifacts(nb_id)

    # 5. Download
    print("\n[5/5] Downloading artifacts...")
    wait_and_download(nb_id, artifacts)

    print(f"\n=== DONE ===")
    print(f"Notebook ID : {nb_id}")
    print(f"Outputs in  : {OUTPUT_DIR}/")
    for f in sorted(OUTPUT_DIR.glob("*")):
        if f.is_file():
            print(f"  {f.name} ({f.stat().st_size:,} bytes)")


if __name__ == "__main__":
    asyncio.run(main())

