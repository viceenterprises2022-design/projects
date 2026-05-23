#!/usr/bin/env python3
"""
telegram_to_notebooklm.py

Pipeline:
  1. Fetch PDF documents from Telegram channel (Telethon)
  2. Download PDFs locally
  3. Upload each PDF to a new NotebookLM notebook
  4. Generate: briefing-doc report, mind-map, audio podcast
  5. Download all artifacts to ./notebooklm_output/

Config via .env:
  TELEGRAM_API_ID      - from my.telegram.org
  TELEGRAM_API_HASH    - from my.telegram.org
  TELEGRAM_CHANNELS    - comma-separated channel usernames, e.g. @btsreports
  TELEGRAM_MSG_LIMIT   - messages to scan per channel (default: 100)
  NOTEBOOKLM_NOTEBOOK_TITLE - notebook title (default: auto-generated)

Usage:
  venv/bin/python telegram_to_notebooklm.py
"""

import asyncio
import os
import sys
import subprocess
import json
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import DocumentAttributeFilename, MessageMediaDocument

load_dotenv()

# ── Config ─────────────────────────────────────────────────────────────────
API_ID    = int(os.environ["TELEGRAM_API_ID"])
API_HASH  = os.environ["TELEGRAM_API_HASH"]
CHANNELS  = [c.strip() for c in os.environ.get("TELEGRAM_CHANNELS", "").split(",") if c.strip()]
MSG_LIMIT = int(os.environ.get("TELEGRAM_MSG_LIMIT", "100"))
PDF_LIMIT = int(os.environ.get("PDF_LIMIT", "30"))
NB_TITLE  = os.environ.get(
    "NOTEBOOKLM_NOTEBOOK_TITLE",
    f"Telegram Intel {datetime.now().strftime('%Y-%m-%d %H:%M')}"
)

OUTPUT_DIR = Path("notebooklm_output")
PDFS_DIR   = OUTPUT_DIR / "pdfs"
OUTPUT_DIR.mkdir(exist_ok=True)
PDFS_DIR.mkdir(exist_ok=True)

NLM = "notebooklm"


# ── Helpers ───────────────────────────────────────────────────────────────────
def p(msg):
    print(msg, flush=True)


def nlm(*args, capture=True):
    cmd = [NLM] + list(str(a) for a in args)
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


# ── Step 1: Download PDFs from Telegram ──────────────────────────────────────
async def download_pdfs(channels: list[str]) -> list[Path]:
    client = TelegramClient("tg_session", API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        await client.disconnect()
        p("ERROR: Not authorized. Run: venv/bin/python -c \"import asyncio; from telethon import TelegramClient; asyncio.run(TelegramClient('tg_session', API_ID, API_HASH).start())\"")
        sys.exit(1)

    all_pdfs = []
    for ch in channels:
        p(f"  Scanning {MSG_LIMIT} messages from {ch}...")
        pdf_count = 0
        async for msg in client.iter_messages(ch, limit=MSG_LIMIT):
            if not msg.media or not isinstance(msg.media, MessageMediaDocument):
                continue
            doc = msg.media.document
            # Check if PDF
            mime = getattr(doc, "mime_type", "")
            if mime != "application/pdf":
                continue
            # Get filename
            fname = None
            for attr in doc.attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    fname = attr.file_name
                    break
            if not fname:
                fname = f"doc_{msg.id}.pdf"
            # Sanitize
            safe = fname.replace("/", "_").replace("\\", "_")
            dest = PDFS_DIR / safe
            if dest.exists():
                p(f"    skip (exists): {safe}")
                all_pdfs.append(dest)
                pdf_count += 1
            else:
                p(f"    Downloading: {safe}")
                await client.download_media(msg, file=str(dest))
                all_pdfs.append(dest)
                pdf_count += 1
            if len(all_pdfs) >= PDF_LIMIT:
                p(f"    PDF_LIMIT {PDF_LIMIT} reached, stopping")
                break
        p(f"    → {pdf_count} PDFs from {ch}")

    await client.disconnect()
    return all_pdfs


# ── Step 2: NotebookLM — create notebook ─────────────────────────────────────────
def create_notebook() -> str:
    p(f"\nCreating notebook: {NB_TITLE}")
    data = nlm_json("create", NB_TITLE)
    nb_id = data.get("notebook", {}).get("id", "")
    if not nb_id:
        p("ERROR: Failed to create notebook. Run 'notebooklm login' first.")
        sys.exit(1)
    p(f"  Notebook ID: {nb_id}")
    return nb_id


# ── Step 3: Upload PDFs as sources ───────────────────────────────────────────────
def upload_pdfs(nb_id: str, pdf_paths: list[Path]) -> list[str]:
    p(f"\nUploading {len(pdf_paths)} PDFs to NotebookLM...")
    source_ids = []
    for pdf in pdf_paths:
        data = nlm_json("source", "add", str(pdf), "--notebook", nb_id)
        sid = data.get("source", {}).get("id", "")
        if sid:
            source_ids.append(sid)
            p(f"  ✓ {pdf.name[:60]} → {sid[:8]}...")
        else:
            p(f"  ✗ Failed: {pdf.name}")
    return source_ids


# ── Step 4: Wait for sources ─────────────────────────────────────────────────────
def wait_for_sources(nb_id: str, source_ids: list[str]):
    p(f"\nWaiting for {len(source_ids)} sources to process...")
    for sid in source_ids:
        result = nlm("source", "wait", sid, "-n", nb_id, "--timeout", "600")
        status = "✓" if result.returncode == 0 else "✗"
        p(f"  {status} {sid[:8]}...")


# ── Step 5: Generate artifacts ───────────────────────────────────────────────────
def generate_artifacts(nb_id: str) -> dict:
    artifacts = {}

    p("\nGenerating briefing-doc report...")
    data = nlm_json("generate", "report", "--format", "briefing-doc", "--notebook", nb_id)
    artifacts["report"] = data.get("task_id", "")

    p("Generating mind-map...")
    data = nlm_json("generate", "mind-map", "--notebook", nb_id)
    artifacts["mind_map"] = data.get("task_id", "")

    p("Generating audio podcast (deep-dive)...")
    data = nlm_json("generate", "audio",
                    "Comprehensive deep-dive covering all key market insights from these reports",
                    "--format", "deep-dive", "--notebook", nb_id)
    artifacts["audio"] = data.get("task_id", "")

    for k, v in artifacts.items():
        p(f"  {k}: {v or '(no task_id)'}")
    return artifacts


# ── Step 6: Wait + Download ───────────────────────────────────────────────────
def wait_and_download(nb_id: str, artifacts: dict):
    p("\nWaiting for artifacts (5-20 min for audio)...")

    if artifacts.get("report"):
        aid = artifacts["report"]
        nlm("artifact", "wait", aid, "-n", nb_id, "--timeout", "900", capture=False)
        out = OUTPUT_DIR / "report.md"
        nlm("download", "report", str(out), "-a", aid, "-n", nb_id, capture=False)
        p(f"  ✓ Report → {out}")

    if artifacts.get("mind_map"):
        aid = artifacts["mind_map"]
        nlm("artifact", "wait", aid, "-n", nb_id, "--timeout", "300", capture=False)
        out = OUTPUT_DIR / "mindmap.json"
        nlm("download", "mind-map", str(out), "-a", aid, "-n", nb_id, capture=False)
        p(f"  ✓ Mind-map → {out}")

    if artifacts.get("audio"):
        aid = artifacts["audio"]
        p("  Audio takes 10-20 min...")
        nlm("artifact", "wait", aid, "-n", nb_id, "--timeout", "1200", capture=False)
        out = OUTPUT_DIR / "podcast.mp3"
        nlm("download", "audio", str(out), "-a", aid, "-n", nb_id, capture=False)
        p(f"  ✓ Audio → {out}")


# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    if not CHANNELS:
        p("ERROR: Set TELEGRAM_CHANNELS in .env")
        sys.exit(1)

    p(f"=== Telegram PDF → NotebookLM Pipeline ===")
    p(f"Channels  : {', '.join(CHANNELS)}")
    p(f"Scan limit: {MSG_LIMIT} messages per channel")
    p(f"PDF limit : {PDF_LIMIT}")
    p(f"PDFs dir  : {PDFS_DIR}/")
    p(f"Output    : {OUTPUT_DIR}/\n")

    # 1. Download PDFs
    p("[1/6] Downloading PDFs from Telegram...")
    pdf_paths = await download_pdfs(CHANNELS)

    if not pdf_paths:
        p("No PDFs found. Check channel name and that channel has PDF documents.")
        sys.exit(1)
    p(f"\n  Total PDFs: {len(pdf_paths)}")

    # 2. Create notebook
    p("\n[2/6] Creating NotebookLM notebook...")
    nb_id = create_notebook()

    # 3. Upload PDFs
    p("\n[3/6] Uploading PDFs as sources...")
    source_ids = upload_pdfs(nb_id, pdf_paths)
    p(f"  Uploaded: {len(source_ids)}/{len(pdf_paths)}")

    if not source_ids:
        p("No sources uploaded. Exiting.")
        sys.exit(1)

    # 4. Wait for processing
    p("\n[4/6] Waiting for source processing...")
    wait_for_sources(nb_id, source_ids)

    # 5. Generate
    p("\n[5/6] Generating artifacts...")
    artifacts = generate_artifacts(nb_id)

    # 6. Download
    p("\n[6/6] Downloading artifacts...")
    wait_and_download(nb_id, artifacts)

    p(f"\n=== DONE ===")
    p(f"Notebook ID : {nb_id}")
    p(f"PDFs used   : {len(pdf_paths)}")
    p(f"Sources     : {len(source_ids)}")
    p(f"\nOutputs in {OUTPUT_DIR}/")
    for f in sorted(OUTPUT_DIR.glob("*")):
        if f.is_file():
            p(f"  {f.name} ({f.stat().st_size:,} bytes)")


if __name__ == "__main__":
    asyncio.run(main())
