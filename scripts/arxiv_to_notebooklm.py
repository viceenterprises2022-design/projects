#!/usr/bin/env python3
"""Arxiv → NotebookLM → Slack pipeline.

Scrapes recent research papers across selected categories, downloads the latest
interesting paper, uploads it to NotebookLM to generate a mindmap and report,
delivers structured block messages to Slack, and cleans up the notebook.

Runs daily but enforces a 48-hour cooldown interval (self-healing).
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# Import send_slack helpers
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from send_slack import send_to_slack, compose_blocks, build_header, build_payload, send_payload, resolve_color, chunk_blocks
except ImportError:
    send_to_slack = None

# ── Config ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
STATE_FILE = BASE_DIR / "arxiv_to_notebooklm_state.json"
ARXIV_DIR = Path("/home/vreddy1/Desktop/Projects/arxiv")
OUTPUT_DIR = ARXIV_DIR / "output"

SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK_RESEARCH") or os.environ.get("SLACK_WEBHOOK_URL")
NLM_CMD = "/home/vreddy1/.local/bin/notebooklm"

SLACK_USERNAME = "arXiv \u2192 NotebookLM"
SLACK_ICON = ":mortar_board:"

# arXiv Category URLs
CATEGORIES = {
    "cs.AI": "https://arxiv.org/list/cs.AI/recent",
    "cs": "https://arxiv.org/list/cs/new",
    "cs.NE": "https://arxiv.org/list/cs.NE/recent",
    "cs.RO": "https://arxiv.org/list/cs.RO/recent",
    "cs.CR": "https://arxiv.org/list/cs.CR/recent",
    "quant-ph": "https://arxiv.org/list/quant-ph/recent",
    "physics.space-ph": "https://arxiv.org/list/physics.space-ph/recent",
    "math": "https://arxiv.org/list/math/recent",
    "q-fin": "https://arxiv.org/list/q-fin/recent",
    "econ": "https://arxiv.org/list/econ/recent"
}

# Selection Priority order
PRIORITY = [
    "cs.AI", "cs", "cs.NE", "cs.RO", "cs.CR", 
    "quant-ph", "physics.space-ph", "math", "q-fin", "econ"
]

# ── Helpers ─────────────────────────────────────────────────────────────
def p(msg):
    print(msg, flush=True)

def nlm(*args, capture=True):
    cmd = [NLM_CMD] + [str(a) for a in args]
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

def sanitize_title(title: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9\s-]", "", title)
    s = re.sub(r"[\s-]+", "-", s)
    return s.strip("-")

def mindmap_to_text(data, indent=0) -> list[str]:
    prefix = "  " * indent
    lines = []
    if isinstance(data, dict):
        title = data.get("title") or data.get("label") or data.get("name", "")
        if title:
            marker = "•" if indent == 0 else "─"
            lines.append(f"{prefix}{marker} {title}")
        children = data.get("children") or data.get("items") or data.get("nodes") or []
        for child in children:
            lines.extend(mindmap_to_text(child, indent + 1))
    elif isinstance(data, list):
        for item in data:
            lines.extend(mindmap_to_text(item, indent))
    elif isinstance(data, str):
        lines.append(f"{prefix}  {data}")
    return lines

# ── State Management ────────────────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last_success_time": None, "processed_ids": []}

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str, ensure_ascii=False))
    p(f"State saved \u2192 {STATE_FILE.name}")

# ── Step 1: Scrape arXiv Category recent lists ──────────────────────────
def scrape_category(category_name: str, url: str) -> list[dict]:
    p(f"Scraping category '{category_name}'...")
    req = urllib.request.Request(
        url, 
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    )
    try:
        time.sleep(2)  # Polite delay to prevent rate limits
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read()
        soup = BeautifulSoup(html, "html.parser")
        
        dts = soup.find_all("dt")
        dds = soup.find_all("dd")
        
        papers = []
        for i in range(min(len(dts), len(dds))):
            dt = dts[i]
            dd = dds[i]
            
            # Find all <a> inside dt to extract ID and links
            links = dt.find_all("a")
            arxiv_id = ""
            abs_link = ""
            pdf_link = ""
            for link in links:
                href = link.get("href", "")
                if "/abs/" in href:
                    abs_link = "https://arxiv.org" + href
                    arxiv_id = href.split("/")[-1].split("v")[0]  # strip version e.g. v1
                elif "/pdf/" in href:
                    pdf_link = "https://arxiv.org" + href
            
            if not arxiv_id:
                continue
                
            # Title
            title_div = dd.find("div", class_="list-title")
            title = ""
            if title_div:
                title = title_div.get_text().replace("Title:", "").strip()
                title = " ".join(title.split())
            
            # Authors
            authors_div = dd.find("div", class_="list-authors")
            authors = ""
            if authors_div:
                authors = authors_div.get_text().replace("Authors:", "").strip()
                authors = " ".join(authors.split())
                
            papers.append({
                "id": arxiv_id,
                "title": title,
                "authors": authors,
                "abs_url": abs_link,
                "pdf_url": pdf_link,
                "category": category_name
            })
        p(f"  Found {len(papers)} papers in recent list.")
        return papers
    except Exception as e:
        p(f"  [ERROR] Scraping failed for {category_name}: {e}")
        return []

# ── Step 2: Candidates selection based on priority ───────────────────────
def select_candidate(state: dict) -> dict:
    processed_ids = set(state.get("processed_ids", []))
    
    # Scrape categories sequentially
    all_papers = {}
    for cat in PRIORITY:
        url = CATEGORIES[cat]
        papers = scrape_category(cat, url)
        if papers:
            all_papers[cat] = [p for p in papers if p["id"] not in processed_ids]
            
    # Iterate in priority order and select the absolute newest unprocessed candidate
    for cat in PRIORITY:
        candidates = all_papers.get(cat, [])
        if candidates:
            selected = candidates[0]  # Grab the first (most recent) candidate
            p(f"\nSelected Candidate:")
            p(f"  ID: {selected['id']}")
            p(f"  Title: {selected['title']}")
            p(f"  Category: {selected['category']}")
            return selected
            
    return {}

# ── Step 3: Download paper PDF ──────────────────────────────────────────
def download_pdf(paper: dict) -> Path:
    pdf_url = paper["pdf_url"]
    sanitized = sanitize_title(paper["title"])
    filename = f"{sanitized}.pdf"
    
    # Limit filename length
    if len(filename) > 100:
        filename = filename[:96] + ".pdf"
        
    dest_path = ARXIV_DIR / filename
    p(f"\nDownloading PDF: {pdf_url} \u2192 {dest_path}")
    
    req = urllib.request.Request(
        pdf_url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    
    ARXIV_DIR.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(req, timeout=30) as response, open(dest_path, "wb") as out_file:
        out_file.write(response.read())
        
    p(f"  ✓ Saved ({dest_path.stat().st_size:,} bytes)")
    return dest_path

# ── Step 4: Slack formatting and Block Kit delivery ────────────────────
def send_to_slack_blocks(paper: dict, nb_id: str, report_path: Path, mm_path: Path) -> bool:
    if not SLACK_WEBHOOK:
        p("  [SKIP] Slack webhook URL not set.")
        return False
        
    if send_to_slack is None:
        p("  [WARN] send_slack.py cannot be imported.")
        return False
        
    title = paper["title"]
    category = paper["category"]
    arxiv_id = paper["id"]
    abs_url = paper["abs_url"]
    pdf_url = paper["pdf_url"]
    nb_link = f"https://notebooklm.google.com/notebook/{nb_id}"
    
    fallback = f"\ud83c\udf93 New Arxiv Paper: {title}"
    
    # Msg 1: header + meta + links
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"\ud83c\udf93 Arxiv Daily Research", "emoji": True},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Title:*\n*{title}*"}
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*\ud83d\udcda Category*\n{category}"},
                {"type": "mrkdwn", "text": f"*\ud83d\udcd3 NotebookLM*\n<{nb_link}|Open Notebook>"},
            ],
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*\ud83c\udd94 arXiv ID*\n{arxiv_id}"},
                {"type": "mrkdwn", "text": f"*\ud83d\udd17 Links*\n<{abs_url}|Abstract> | <{pdf_url}|PDF>"},
            ],
        },
        {"type": "divider"},
    ]
    
    # Add Mind Map as tree structure
    if mm_path and mm_path.exists():
        try:
            mm_data = json.loads(mm_path.read_text())
            tree_lines = mindmap_to_text(mm_data)
            if tree_lines:
                mm_text = "\n".join(tree_lines)
                if len(mm_text) > 2800:
                    mm_text = mm_text[:2800] + "\n… (truncated)"
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*\ud83d\uddfa Mind Map (Concept Hierarchy)*\n```\n{mm_text}\n```"},
                })
                blocks.append({"type": "divider"})
        except Exception as e:
            p(f"  [WARN] Failed to parse mindmap JSON: {e}")
            
    # Add Briefing Report Blog Post Content
    report_chunks = []
    if report_path and report_path.exists():
        raw = report_path.read_text().strip()
        if raw:
            # First block cap
            MAX_FIRST = 2500
            if len(raw) <= MAX_FIRST:
                report_chunks = [raw]
            else:
                report_chunks = [raw[:MAX_FIRST]]
                remaining = raw[MAX_FIRST:]
                while remaining:
                    report_chunks.append(remaining[:3000])
                    remaining = remaining[3000:]
                    
    if report_chunks:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*\ud83d\udccb Detailed Briefing & Summary*\n\n{report_chunks[0]}"},
        })
        
    # Split blocks to fit within Slack's 50-block limit
    payloads_data = []
    color_hex = resolve_color("info")
    
    for blk_chunk in chunk_blocks(blocks):
        payload = build_payload(
            text=fallback,
            username=SLACK_USERNAME,
            icon_emoji=SLACK_ICON,
            blocks=blk_chunk
        )
        if color_hex:
            payload["attachments"] = [{"color": color_hex}]
        payloads_data.append(payload)
        
    # Send main parts
    ok = True
    for idx, pay in enumerate(payloads_data, start=1):
        res = send_payload(SLACK_WEBHOOK, pay)
        p(f"  Slack block part {idx}/{len(payloads_data)}: {res.get('ok')}")
        if not res.get("ok"):
            ok = False
            p(f"  [WARN] Slack send failed: {res.get('error')}")
            
    # Send continuation report chunks as secondary messages
    for i, chunk in enumerate(report_chunks[1:], start=2):
        cont_blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"\ud83d\udccb Report Continuation ({i - 1}/{len(report_chunks) - 1})", "emoji": True},
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": chunk}},
        ]
        payload = build_payload(
            text=f"{fallback} - Part {i}",
            username=SLACK_USERNAME,
            icon_emoji=SLACK_ICON,
            blocks=cont_blocks
        )
        if color_hex:
            payload["attachments"] = [{"color": color_hex}]
        res = send_payload(SLACK_WEBHOOK, payload)
        p(f"  Slack continuation part {i}: {res.get('ok')}")
        if not res.get("ok"):
            ok = False
            p(f"  [WARN] Slack continuation failed: {res.get('error')}")
            
    return ok

# ── Notebook Deletion (safety-gated) ─────────────────────────────────────
def delete_notebook(nb_id: str) -> bool:
    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{19,}$", nb_id):
        p(f"  [SAFETY BLOCKED] Notebook ID '{nb_id}' looks invalid, skipping delete.")
        return False

    p(f"  Cleaning up NotebookLM notebook {nb_id[:16]}...")
    for attempt in range(3):
        result = nlm("delete", "-n", nb_id, "-y", capture=True)
        if result.returncode != 0:
            p(f"  [WARN] delete exit {result.returncode}, retrying...")
            continue
        p(f"  Delete command completed. Verifying...")
        time.sleep(2)
        list_result = nlm("list", capture=True)
        if nb_id not in list_result.stdout:
            p(f"  ✓ Deleted notebook successfully.")
            return True
        time.sleep(3)
    p(f"  [WARN] Could not verify notebook deletion after 3 attempts.")
    return False

# ── Main Pipeline ───────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Arxiv → NotebookLM → Slack Daily Pipeline")
    parser.add_argument("--force", action="store_true", help="Override 48-hour cooldown lockout")
    parser.add_argument("--dry-run", action="store_true", help="Scrape and select candidate without running full pipeline")
    args = parser.parse_args()
    
    p("=" * 60)
    p("  Arxiv \u2192 NotebookLM Research Pipeline")
    p(f"  Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    p("=" * 60)
    
    state = load_state()
    
    # ── Interval Check (48 hours) ─────────────────────────────────────
    if not args.force and not args.dry_run:
        last_success = state.get("last_success_time")
        if last_success:
            last_dt = datetime.fromisoformat(last_success)
            diff = datetime.now(timezone.utc) - last_dt
            if diff < timedelta(hours=48):
                p(f"Lockout: Cooldown active. Last success was at {last_success} ({diff.total_seconds()/3600:.1f} hours ago).")
                p("Use --force to run pipeline immediately.")
                return
                
    # ── Step 1 & 2: Scrape & Select Candidate ────────────────────────
    candidate = select_candidate(state)
    if not candidate:
        p("\nNo new unprocessed research papers found across all priority categories.")
        return
        
    if args.dry_run:
        p("\n[DRY RUN] Selected candidate details:")
        p(json.dumps(candidate, indent=2))
        p("[DRY RUN] Done. Exiting without execution.")
        return
        
    # ── Step 3: Download PDF ──────────────────────────────────────────
    pdf_path = download_pdf(candidate)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / "briefing-report.md"
    mm_path = OUTPUT_DIR / "mindmap.json"
    restructured_path = OUTPUT_DIR / "restructured-report.md"
    
    # Clean previous output runs
    for path in [report_path, mm_path, restructured_path]:
        if path.exists():
            path.unlink()
            
    # ── Step 4: NotebookLM upload and artifact generation ─────────────
    nb_name = f"Arxiv: {candidate['title'][:60]}"
    p(f"\n[1/6] Creating NotebookLM notebook...")
    data = nlm_json("create", nb_name)
    nb_id = data.get("notebook", {}).get("id", "")
    if not nb_id:
        p("  [CRITICAL] Failed to create notebook. Run 'notebooklm login'.")
        sys.exit(1)
    p(f"  Notebook ID: {nb_id}")
    
    try:
        p(f"\n[2/6] Uploading research paper PDF...")
        data = nlm_json("source", "add", str(pdf_path), "--notebook", nb_id)
        sid = data.get("source", {}).get("id", "")
        if not sid:
            p("  [CRITICAL] Failed to add source.")
            delete_notebook(nb_id)
            sys.exit(1)
        p(f"  Source ID: {sid[:12]}")
        
        p(f"\n[3/6] Ingesting source PDF...")
        nlm("source", "wait", sid, "-n", nb_id, "--timeout", "600", capture=False)
        p("  Ready")
        
        p(f"\n[4/6] Generating comprehensive briefing report & blog-style post...")
        report_inst = (
            "You are a world-class AI researcher and academic. "
            "Generate an extremely comprehensive, exhaustive, and detailed briefing document "
            "and summary in a highly engaging, professional blog post format. "
            "Structure it with clear section headings, bullet points, tables for comparison, "
            "key mathematical or methodology summaries, main results/breakthroughs, and detailed context. "
            "Do not omit critical details."
        )
        data = nlm_json(
            "generate", "report",
            "--format", "briefing-doc",
            "--append", report_inst,
            "--notebook", nb_id
        )
        report_id = data.get("artifact", {}).get("id", "") or data.get("task_id", "")
        if not report_id:
            p("  [CRITICAL] Failed to start report generation.")
            delete_notebook(nb_id)
            sys.exit(1)
        p(f"  Report task: {report_id[:12]}")
        
        p(f"\n[4.5/6] Generating mind-map structure...")
        nlm_json("generate", "mind-map", "--notebook", nb_id)
        p("  Done.")
        
        p(f"\n[5/6] Downloading generated research artifacts...")
        nlm("artifact", "wait", report_id, "-n", nb_id, "--timeout", "900", capture=False)
        nlm("download", "report", str(report_path), "-a", report_id, "-n", nb_id, capture=False)
        nlm("download", "mind-map", str(mm_path), "--notebook", nb_id, capture=False)
        
        if report_path.exists():
            p(f"  ✓ Briefing Report saved ({report_path.stat().st_size:,} bytes)")
        if mm_path.exists():
            p(f"  ✓ Mind Map saved ({mm_path.stat().st_size:,} bytes)")
            
        # ── Save to Obsidian ─────────────────────────────────────────────
        p(f"\n[5.5/6] Saving to Obsidian vault...")
        try:
            from obsidian_integration import save_to_obsidian
            save_to_obsidian(
                source_type="arxiv",
                title=candidate["title"],
                source_id=candidate["id"],
                source_url=candidate["abs_url"],
                notebook_id=nb_id,
                report_path=report_path,
                mindmap_path=mm_path,
                additional_tags=[candidate["category"], candidate["authors"].split(",")[0]]
            )
        except Exception as obs_err:
            p(f"  [OBSIDIAN ERROR] Failed to integrate with Obsidian: {obs_err}")

        # ── Step 5: Deliver formatted message to Slack ──────────────────
        p(f"\n[6/6] Delivering structured research briefing to Slack...")
        slack_ok = send_to_slack_blocks(candidate, nb_id, report_path, mm_path)
        
        # ── Step 6: Delete notebook on success ──────────────────────────
        if slack_ok:
            delete_notebook(nb_id)
            
            # Save success to state
            state["last_success_time"] = datetime.now(timezone.utc).isoformat()
            if candidate["id"] not in state["processed_ids"]:
                state["processed_ids"].append(candidate["id"])
            save_state(state)
            
            p(f"\n✓ Pipeline successfully finished.")
        else:
            p("\n[ERROR] Slack delivery failed. Keeping notebook for debugging.")
            delete_notebook(nb_id)  # Clean up anyway to prevent clutter, or skip if wanted.
            
    except Exception as e:
        p(f"\n[CRITICAL ERROR] Run encountered error: {e}")
        delete_notebook(nb_id)
        sys.exit(1)

if __name__ == "__main__":
    main()
