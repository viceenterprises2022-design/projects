#!/usr/bin/env python3
"""
telegram_to_notebooklm.py

Daily pipeline (runs at 4PM IST via cron):
  1. Fetch PDFs posted in the last DAYS_BACK days from Telegram channel
  2. Download PDFs locally to notebooklm_output/pdfs/
  3. Upload each PDF to a new dated NotebookLM notebook
  4. Inject 6 Q&A coverage notes into notebook
  5. Generate: custom comprehensive report + mind-map
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
import textwrap
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import DocumentAttributeFilename, MessageMediaDocument

load_dotenv()

# ── CLI args ────────────────────────────────────────────────────────────────
def parse_args():
    import argparse
    ap = argparse.ArgumentParser(description="Telegram PDF → NotebookLM pipeline")
    ap.add_argument("--channel", action="append", dest="extra_channels",
                    help="Additional Telegram channel(s) to fetch from (can be repeated)")
    return ap.parse_args()

ARGS = parse_args()

# ── Config ─────────────────────────────────────────────────────────────────
API_ID    = int(os.environ["TELEGRAM_API_ID"])
API_HASH  = os.environ["TELEGRAM_API_HASH"]
CHANNELS  = [c.strip() for c in os.environ.get("TELEGRAM_CHANNELS", "").split(",") if c.strip()]
if ARGS.extra_channels:
    CHANNELS.extend(c.strip().lstrip("@") for c in ARGS.extra_channels)
    CHANNELS = [f"@{c}" if not c.startswith("@") else c for c in CHANNELS]
MSG_LIMIT = int(os.environ.get("TELEGRAM_MSG_LIMIT", "200"))
PDF_LIMIT = int(os.environ.get("PDF_LIMIT", "20"))
DAYS_BACK = float(os.environ.get("DAYS_BACK", "1"))

TODAY     = datetime.now().strftime("%Y-%m-%d")
NB_TITLE  = f"Beat-the-street-report-{TODAY}"

OUTPUT_DIR = Path("notebooklm_output")
PDFS_DIR   = OUTPUT_DIR / "pdfs"
DAILY_DIR  = OUTPUT_DIR / f"Beat-the-street-report-{TODAY}"
for d in [OUTPUT_DIR, PDFS_DIR, DAILY_DIR]:
    d.mkdir(exist_ok=True)

NLM = os.path.join(os.path.dirname(__file__), "venv", "bin", "notebooklm")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
SLACK_TOKEN = os.environ.get("SLACK_TOKEN", "")
SLACK_USERNAME = "Beat-the-Street"
SLACK_ICON = ":newspaper:"


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


# ── Mindmap → tree renderer ───────────────────────────────────────────────────
def render_mindmap_tree(data, prefix="", is_last=True, is_root=True):
    if is_root:
        lines = [f"🌳 *Mind Map: {data.get('name', 'Untitled')}*"]
        children = data.get("children", [])
        for i, child in enumerate(children):
            lines.append(render_mindmap_tree(child, "", i == len(children) - 1, False))
        return "\n".join(lines)

    connector = "└── " if is_last else "├── "
    lines = [f"{prefix}{connector}{data.get('name', '')}"]
    children = data.get("children", [])
    extension = "    " if is_last else "│   "
    for i, child in enumerate(children):
        lines.append(render_mindmap_tree(child, prefix + extension, i == len(children) - 1, False))
    return lines[-1] if len(lines) == 1 else "\n".join(lines)


# ── Slack helpers ─────────────────────────────────────────────────────────────
MAX_SLACK_CHARS = 3900


def slack_send(text, title=None):
    if not SLACK_WEBHOOK_URL:
        p("  [SKIP] No SLACK_WEBHOOK_URL set")
        return False
    header = f"*{title}*\n" if title else ""
    payload = {"text": f"{header}{text}", "username": SLACK_USERNAME, "icon_emoji": SLACK_ICON}
    try:
        resp = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=20)
        resp.raise_for_status()
        return True
    except Exception as e:
        p(f"  [WARN] Slack send failed: {e}")
        return False


def slack_send_chunks(text, title=None):
    for i in range(0, len(text), MAX_SLACK_CHARS):
        chunk = text[i:i + MAX_SLACK_CHARS]
        ok = slack_send(chunk, title if i == 0 else None)
        if not ok:
            return False
    return True


SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL", "#general")


def slack_upload_file(file_path: Path, title: str = None):
    if not SLACK_TOKEN:
        p("  [SKIP] No SLACK_TOKEN set — cannot upload files")
        return False
    try:
        fname = title or file_path.name
        fsize = file_path.stat().st_size
        headers = {"Authorization": f"Bearer {SLACK_TOKEN}", "Content-Type": "application/json"}

        # Step 1: get upload URL
        r1 = requests.post(
            "https://slack.com/api/files.getUploadURLExternal",
            headers=headers,
            json={"filename": fname, "length": fsize, "alt_text": fname},
            timeout=30,
        )
        d1 = r1.json()
        if not d1.get("ok"):
            p(f"  [WARN] getUploadURL failed: {d1.get('error', 'unknown')}")
            return False
        upload_url = d1["upload_url"]
        file_id = d1["file_id"]

        # Step 2: PUT file bytes to upload_url
        with open(file_path, "rb") as f:
            r2 = requests.put(upload_url, data=f, timeout=120)
        if r2.status_code != 200:
            p(f"  [WARN] file PUT failed: HTTP {r2.status_code}")
            return False

        # Step 3: complete upload
        r3 = requests.post(
            "https://slack.com/api/files.completeUploadExternal",
            headers=headers,
            json={"files": [{"id": file_id, "title": fname}], "channel_id": SLACK_CHANNEL},
            timeout=30,
        )
        d3 = r3.json()
        if d3.get("ok"):
            p(f"  ✓ Uploaded {fname}")
            return True
        p(f"  [WARN] completeUpload failed: {d3.get('error', 'unknown')}")
        return False
    except Exception as e:
        p(f"  [WARN] Slack upload exception: {e}")
        return False


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

# Targeted questions — answers saved as notes before report generation.
# Notes become notebook sources, giving the report generator richer content to draw from.
COVERAGE_QUESTIONS = [
    ("stock-picks",
     "List ALL specific stock recommendations, buy/sell calls, price targets, and entry/exit levels "
     "mentioned across ALL reports. Be exhaustive — include every ticker and level."),
    ("technical-analysis",
     "Summarize ALL technical analysis across ALL reports: chart patterns, support/resistance levels, "
     "moving averages, RSI, volume signals, and breakout/breakdown setups."),
    ("sector-themes",
     "What sector rotations, thematic plays, and macro trends are discussed across ALL reports? "
     "Include every sector-specific insight and relative strength observation."),
    ("risk-warnings",
     "List ALL risk factors, stop-loss levels, cautionary notes, and downside scenarios mentioned "
     "across ALL reports."),
    ("macro-outlook",
     "Summarize the macro and market outlook from ALL reports: index targets, FII/DII activity, "
     "global cues, options data (PCR, OI, max pain), and derivative signals."),
    ("high-conviction-plays",
     "What are the most unique, contrarian, or high-conviction trade setups and insights across "
     "ALL reports? Include specific reasoning for each."),
]

REPORT_PROMPT = (
    "Generate a comprehensive, exhaustive daily market intelligence briefing covering ALL sources "
    "and notes. Required sections: "
    "1) Market Overview & Index Targets "
    "2) Top Stock Picks — full reasoning, price targets, entry/exit for every call "
    "3) Technical Analysis Highlights "
    "4) Sector Analysis & Themes "
    "5) Macro & Global Cues "
    "6) Options & Derivatives Data "
    "7) Risk Factors & Stop-Losses "
    "8) High-Conviction & Contrarian Plays. "
    "Include specific numbers, levels, and tickers from every source. "
    "Do NOT omit any report's key calls or analysis."
)


GEN_ARTIFACTS = [
    ("report",     {"args": ["generate", "report", "--format", "custom", REPORT_PROMPT],
                     "ext": ".md", "wait_id": True, "desc": "Report"}),
    ("mind-map",   {"args": ["generate", "mind-map"],
                     "ext": ".json", "wait_id": False, "desc": "Mind-map"}),
    ("infographic",{"args": ["generate", "infographic",
                              "Visual summary of today's market intelligence briefing across all sources.",
                              "--orientation", "landscape", "--detail", "detailed", "--style", "bento-grid"],
                     "ext": ".png", "wait_id": True, "desc": "Infographic"}),
]


def _gen_one(nb_id: str, kind: str, cfg: dict) -> Path | None:
    p(f"\n  Generating {cfg['desc']}...")
    if cfg.get("wait_id"):
        data = nlm_json(*cfg["args"], "--notebook", nb_id)
        task_id = data.get("task_id", "")
        p(f"    task: {task_id or '(none)'}")
        if not task_id:
            return None
        if "report" in kind:
            nlm("artifact", "wait", task_id, "-n", nb_id, "--timeout", "900", capture=False)
        else:
            nlm("artifact", "wait", task_id, "-n", nb_id, "--timeout", "300", capture=False)
    else:
        nlm_json(*cfg["args"], "--notebook", nb_id)

    out = DAILY_DIR / f"{kind}{cfg['ext']}"
    # download uses different subcommands per kind
    dl_cmd = cfg.get("download_args", [kind])
    nlm("download", *dl_cmd, str(out), "--notebook", nb_id, capture=False)
    if out.exists():
        p(f"    ✓ {out.name} ({out.stat().st_size:,} bytes)")
        return out
    p(f"    [WARN] {out.name} not found after download")
    return None


def generate_and_download(nb_id: str) -> list[Path]:
    generated = []

    p("\nPhase 1: Injecting coverage notes (Q&A → notes)...")
    for note_title, question in COVERAGE_QUESTIONS:
        p(f"  Q: {note_title}...")
        result = nlm("ask", question, "--save-as-note", "--note-title", note_title, "--notebook", nb_id)
        if result.returncode != 0:
            p(f"    [WARN] failed: {result.stderr.strip()[:120]}")
        else:
            p(f"    ✓ note saved: {note_title}")

    for kind, cfg in GEN_ARTIFACTS:
        out = _gen_one(nb_id, kind, cfg)
        if out:
            generated.append(out)

    return generated


# ── Step 6: Send to Slack ─────────────────────────────────────────────────────
FILE_LABELS = {
    ".md":    ("📄", "Report"),
    ".json":  ("🗃", "Data"),
    ".png":   ("🖼", "Infographic"),
    ".jpg":   ("🖼", "Image"),
    ".jpeg":  ("🖼", "Image"),
    ".mp3":   ("🎧", "Podcast"),
    ".mp4":   ("🎬", "Video"),
    ".csv":   ("📊", "Table"),
    ".pdf":   ("📕", "Slides"),
    ".pptx":  ("📕", "Presentation"),
    ".txt":   ("📝", "Notes"),
}


def format_file_for_slack(file_path: Path) -> list[dict]:
    """Return list of {title, text} payloads for a given file."""
    ext = file_path.suffix.lower()
    base = file_path.stem
    emoji, label = FILE_LABELS.get(ext, ("📎", "File"))

    if ext == ".json" and base == "mind-map":
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            tree = render_mindmap_tree(data)
            title = f"{emoji} Topic Map"
            return [{"title": title, "text": f"```\n{tree[:MAX_SLACK_CHARS]}\n```"}]
        except Exception as e:
            return [{"title": f"{emoji} {label}: {file_path.name}", "text": f"_(failed to parse: {e})_"}]

    if ext in (".json", ".csv", ".txt"):
        text = file_path.read_text(encoding="utf-8", errors="replace").strip()
        if not text:
            return []
        title = f"{emoji} {label}: {file_path.name}"
        if ext == ".json":
            try:
                parsed = json.loads(text)
                text = json.dumps(parsed, indent=2)[:3000]
            except json.JSONDecodeError:
                text = text[:2000]
        if ext == ".csv":
            text = text[:2000]
        chunks = []
        for i in range(0, len(text), MAX_SLACK_CHARS):
            chunk_title = title if i == 0 else None
            chunks.append({"title": chunk_title, "text": f"```\n{text[i:i+MAX_SLACK_CHARS]}\n```"})
        return chunks

    if ext == ".md":
        full = file_path.read_text(encoding="utf-8")
        # First send summary of key sections
        sections = full.split("\n### ")
        summary_parts = []
        for sec in sections[:6]:
            lines = sec.strip().split("\n")
            heading = lines[0].replace("#", "").strip()
            body = "\n".join(lines[1:8]).strip()
            body = textwrap.shorten(body, width=300, placeholder="...")
            if body:
                summary_parts.append(f"*{heading}*\n{body}")
        summary = "\n\n".join(summary_parts)
        chunks = [{"title": f"{emoji} Report Summary", "text": summary}]
        # Then full report if it fits
        if len(full) <= MAX_SLACK_CHARS * 3:
            for i in range(0, len(full), MAX_SLACK_CHARS):
                chunk_title = f"{emoji} Full Report" if i == 0 else None
                chunks.append({"title": chunk_title, "text": full[i:i+MAX_SLACK_CHARS]})
        else:
            chunks.append({"title": f"{emoji} Full Report", "text": f"📄 *Full report saved locally* — too large for Slack ({len(full):,} bytes). Check `{file_path.name}`"})
        return chunks

    # Image files — upload as file attachment
    if ext in (".png", ".jpg", ".jpeg", ".gif"):
        return [{"_upload": str(file_path), "title": f"{emoji} {label}", "text": ""}]

    # Other binary files — just note them
    size = file_path.stat().st_size
    return [{"title": f"{emoji} {label}: {file_path.name}", "text": f"• Size: {size:,} bytes\n• Saved locally at `{file_path}`"}]


def send_artifacts_to_slack(nb_id: str, source_ids: list[str], pdf_paths: list[Path]):
    p("\n[6/7] Delivering to Slack...")

    slack_send(
        f"📊 *Beat-the-Street Report — {TODAY}*\n"
        f"• Notebook: `{nb_id[:8]}…`\n"
        f"• PDFs processed: {len(pdf_paths)}\n"
        f"• Sources uploaded: {len(source_ids)}"
    )

    files = sorted(DAILY_DIR.iterdir())
    text_files = [f for f in files if f.is_file()]
    if not text_files:
        slack_send("No artifact files found in output directory.")
        p("  No files to send.")
        return

    for fp in text_files:
        if fp.name.startswith("."):
            continue
        p(f"  Sending {fp.name}...")
        payloads = format_file_for_slack(fp)
        for payload in payloads:
            if "_upload" in payload:
                slack_upload_file(Path(payload["_upload"]), payload.get("title"))
            else:
                slack_send(payload["text"], payload.get("title"))

    p("  ✓ Slack delivery complete")


# ── Step 7: Cleanup notebook ──────────────────────────────────────────────────
def delete_notebook(nb_id: str):
    p(f"\n[Cleanup] Deleting notebook {nb_id[:8]}…...")
    result = nlm("delete", "-n", nb_id, "-y", capture=True)
    if result.returncode == 0:
        p("  ✓ Notebook deleted")
    else:
        p(f"  [WARN] Delete may have failed: {result.stderr.strip()[:200]}")




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

    p("\n[1/7] Downloading PDFs from Telegram...")
    pdf_paths = await download_pdfs(CHANNELS)
    if not pdf_paths:
        p("No new PDFs today. Exiting.")
        sys.exit(0)
    p(f"  Total: {len(pdf_paths)} PDFs")

    p("\n[2/7] Creating NotebookLM notebook...")
    nb_id = create_notebook()

    p("\n[3/7] Uploading PDFs...")
    source_ids = upload_pdfs(nb_id, pdf_paths)
    p(f"  Uploaded: {len(source_ids)}/{len(pdf_paths)}")
    if not source_ids:
        p("No sources uploaded. Exiting.")
        sys.exit(1)

    p("\n[4/7] Waiting for source processing...")
    wait_for_sources(nb_id, source_ids)

    p("\n[5/7] Generating artifacts (report + mind-map + infographic)...")
    generated = generate_and_download(nb_id)

    p(f"\n{'=' * 50}")
    p(f"GENERATED — Notebook: {nb_id}")
    p(f"PDFs: {len(pdf_paths)}  Sources: {len(source_ids)}  Artifacts: {len(generated)}")
    p(f"\nOutputs in {DAILY_DIR}/")
    for f in sorted(DAILY_DIR.glob("*")):
        if f.is_file():
            p(f"  {f.name} ({f.stat().st_size:,} bytes)")

    # ── Step 6: Slack delivery
    p("\n" + "=" * 50)
    send_artifacts_to_slack(nb_id, source_ids, pdf_paths)

    # ── Step 7: Delete notebook to save space
    p("\n" + "=" * 50)
    delete_notebook(nb_id)

    p(f"\n{'=' * 50}")
    p(f"✓ COMPLETE — {TODAY}")
    p(f"Slack sent · Notebook deleted · Outputs in {DAILY_DIR}/")


if __name__ == "__main__":
    asyncio.run(main())
