#!/usr/bin/env python3
"""
telegram_to_notebooklm.py

Daily pipeline (runs at 4PM IST via cron):
  1. Fetch PDFs posted in the last DAYS_BACK days from Telegram channel
  2. Download PDFs locally to notebooklm_output/pdfs/
  3. Upload each PDF to a new dated NotebookLM notebook
  4. Generate: briefing-doc report + mind-map
  5. Download artifacts to notebooklm_output/YYYY-MM-DD/

Config via .env:
  TELEGRAM_API_ID      - from my.telegram.org
  TELEGRAM_API_HASH    - from my.telegram.org
  TELEGRAM_CHANNELS    - comma-separated, e.g. @btsreports
  TELEGRAM_MSG_LIMIT   - max messages to scan (default: 200)
  PDF_LIMIT            - max PDFs to process (default: 20)
  DAYS_BACK            - how many days back to fetch (default: 1)

Usage:
  venv/bin/python telegram_to_notebooklm.py
"""

import asyncio
import os
import sys
import subprocess
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import DocumentAttributeFilename, MessageMediaDocument

load_dotenv()

# ── Config ─────────────────────────────────────────────────────────────────
API_ID    = int(os.environ["TELEGRAM_API_ID"])
API_HASH  = os.environ["TELEGRAM_API_HASH"]
CHANNELS  = [c.strip() for c in os.environ.get("TELEGRAM_CHANNELS", "").split(",") if c.strip()]
MSG_LIMIT = int(os.environ.get("TELEGRAM_MSG_LIMIT", "200"))
PDF_LIMIT = int(os.environ.get("PDF_LIMIT", "20"))
DAYS_BACK = float(os.environ.get("DAYS_BACK", "1"))

TODAY     = datetime.now().strftime("%Y-%m-%d")
NB_TITLE  = f"@btsreports Daily Intel {TODAY}"

OUTPUT_DIR = Path("notebooklm_output")
PDFS_DIR   = OUTPUT_DIR / "pdfs"
DAILY_DIR  = OUTPUT_DIR / TODAY
for d in [OUTPUT_DIR, PDFS_DIR, DAILY_DIR]:
    d.mkdir(exist_ok=True)

NLM = "notebooklm"


# ── Helpers ──────────────────────────────────────────────────────────────────
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


# ── Step 1: Download new PDFs from Telegram ──────────────────────────────────
async def download_pdfs(channels: list[str]) -> list[Path]:
    client = TelegramClient("tg_session", API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        await client.disconnect()
        p("ERROR: Not authorized. Re-auth with: venv/bin/python -c \"from telethon.sync import TelegramClient; TelegramClient('tg_session', API_ID, API_HASH).start()\"")
        sys.exit(1)

    cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)
    all_pdfs = []

    for ch in channels:
        p(f"  Channel {ch} — last {DAYS_BACK}d (since {cutoff.strftime('%Y-%m-%d %H:%M UTC')})")
        pdf_count = 0
        async for msg in client.iter_messages(ch, limit=MSG_LIMIT, reverse=False):
            if not msg.date:
                continue
            msg_dt = msg.date if msg.date.tzinfo else msg.date.replace(tzinfo=timezone.utc)
            if msg_dt < cutoff:
                break  # messages are newest-first; once older than cutoff, stop
            if not msg.media or not isinstance(msg.media, MessageMediaDocument):
                continue
            doc = msg.media.document
            if getattr(doc, "mime_type", "") != "application/pdf":
                continue
            # Filename
            fname = next(
                (a.file_name for a in doc.attributes if isinstance(a, DocumentAttributeFilename)),
                f"doc_{msg.id}.pdf"
            )
            safe = fname.replace("/", "_").replace("\\", "_")
            dest = PDFS_DIR / safe
            if dest.exists():
                p(f"    [cached] {safe}")
            else:
                p(f"    [download] {safe}")
                await client.download_media(msg, file=str(dest))
            all_pdfs.append(dest)
            pdf_count += 1
            if len(all_pdfs) >= PDF_LIMIT:
                p(f"    PDF_LIMIT {PDF_LIMIT} reached")
                break
        p(f"    → {pdf_count} PDFs")

    await client.disconnect()
    return all_pdfs


# ── Step 2: Create notebook ───────────────────────────────────────────────────
def create_notebook() -> str:
    p(f"\nNotebook: {NB_TITLE}")
    data = nlm_json("create", NB_TITLE)
    nb_id = data.get("notebook", {}).get("id", "")
    if not nb_id:
        p("ERROR: Failed to create notebook. Run 'notebooklm login'.")
        sys.exit(1)
    p(f"  ID: {nb_id}")
    return nb_id


# ── Step 3: Upload PDFs ───────────────────────────────────────────────────────
def upload_pdfs(nb_id: str, pdf_paths: list[Path]) -> list[str]:
    p(f"\nUploading {len(pdf_paths)} PDFs...")
    source_ids = []
    for pdf in pdf_paths:
        data = nlm_json("source", "add", str(pdf), "--notebook", nb_id)
        sid = data.get("source", {}).get("id", "")
        if sid:
            source_ids.append(sid)
            p(f"  ✓ {pdf.name[:60]} → {sid[:8]}")
        else:
            p(f"  ✗ Failed: {pdf.name}")
    return source_ids


# ── Step 4: Wait for sources ──────────────────────────────────────────────────
def wait_for_sources(nb_id: str, source_ids: list[str]):
    p(f"\nWaiting for {len(source_ids)} sources...")
    for sid in source_ids:
        result = nlm("source", "wait", sid, "-n", nb_id, "--timeout", "600")
        p(f"  {'✓' if result.returncode == 0 else '✗'} {sid[:8]}")


# ── Step 5: Generate + Download artifacts ─────────────────────────────────────
def generate_and_download(nb_id: str):
    # ── Briefing-doc report (async)
    p("\nGenerating briefing-doc report...")
    data = nlm_json("generate", "report", "--format", "briefing-doc", "--notebook", nb_id)
    report_id = data.get("task_id", "")
    p(f"  report task: {report_id or '(none)'}")

    # ── Mind-map (sync — available immediately)
    p("Generating mind-map...")
    nlm_json("generate", "mind-map", "--notebook", nb_id)
    out_mm = DAILY_DIR / "mindmap.json"
    nlm("download", "mind-map", str(out_mm), "--notebook", nb_id, capture=False)
    p(f"  ✓ Mind-map → {out_mm}")

    # ── Wait + download report
    if report_id:
        p("Waiting for report (1-5 min)...")
        nlm("artifact", "wait", report_id, "-n", nb_id, "--timeout", "600", capture=False)
        out_r = DAILY_DIR / "report.md"
        nlm("download", "report", str(out_r), "-a", report_id, "-n", nb_id, capture=False)
        p(f"  ✓ Report → {out_r}")
    else:
        p("  [WARN] No report task_id — skipping download")


# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    if not CHANNELS:
        p("ERROR: Set TELEGRAM_CHANNELS in .env")
        sys.exit(1)

    p("=" * 50)
    p(f"Telegram PDF → NotebookLM  [{TODAY}]")
    p(f"Channels : {', '.join(CHANNELS)}")
    p(f"Days back: {DAYS_BACK}  |  PDF limit: {PDF_LIMIT}")
    p(f"Output   : {DAILY_DIR}/")
    p("=" * 50)

    p("\n[1/5] Downloading PDFs from Telegram...")
    pdf_paths = await download_pdfs(CHANNELS)
    if not pdf_paths:
        p("No new PDFs today. Exiting.")
        sys.exit(0)
    p(f"  Total: {len(pdf_paths)} PDFs")

    p("\n[2/5] Creating NotebookLM notebook...")
    nb_id = create_notebook()

    p("\n[3/5] Uploading PDFs...")
    source_ids = upload_pdfs(nb_id, pdf_paths)
    p(f"  Uploaded: {len(source_ids)}/{len(pdf_paths)}")
    if not source_ids:
        p("No sources uploaded. Exiting.")
        sys.exit(1)

    p("\n[4/5] Waiting for source processing...")
    wait_for_sources(nb_id, source_ids)

    p("\n[5/5] Generating report + mind-map...")
    generate_and_download(nb_id)

    p(f"\n{'=' * 50}")
    p(f"DONE — Notebook: {nb_id}")
    p(f"PDFs: {len(pdf_paths)}  Sources: {len(source_ids)}")
    p(f"\nOutputs in {DAILY_DIR}/")
    for f in sorted(DAILY_DIR.glob("*")):
        if f.is_file():
            p(f"  {f.name} ({f.stat().st_size:,} bytes)")


if __name__ == "__main__":
    asyncio.run(main())
