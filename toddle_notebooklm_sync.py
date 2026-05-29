#!/usr/bin/env python3
"""Toddle → NotebookLM daily sync orchestrator.

Full pipeline:
  1. Inventory all subject files from Toddle
  2. Download new/changed files
  3. Convert to markdown
  4. Upload merged text to NotebookLM
  5. Generate study guides
"""
import importlib.util
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

NBLM = "notebooklm"
SCRIPTS_DIR = Path(__file__).parent
STATE_FILE = SCRIPTS_DIR / "sync_state.json"
INVENTORY_FILE = SCRIPTS_DIR / "output" / "toddle_inventory" / "all_subjects_inventory.json"
OUTPUT_DIR = SCRIPTS_DIR / "output"
DOWNLOADS_DIR = OUTPUT_DIR / "downloads"
TEXT_DIR = OUTPUT_DIR / "text"
SUBJECTS = ["Physics", "Chemistry", "Mathematics", "English", "Biology", "History", "Geography", "Spanish", "Design", "Visual Arts"]
SUBJECT_DIR_MAP = {"Physics": "physics"}
PHYSICS_NOTEBOOK_ID = "cbfa891c-b27d-4964-aaac-9c0b70c31605"


def run_script(name, *args, timeout=300):
    script = SCRIPTS_DIR / name
    cmd = [sys.executable, str(script)] + list(args)
    print(f"  Running: {name} {' '.join(args)}")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    for line in r.stdout.splitlines():
        print(f"    {line}")
    if r.returncode != 0:
        print(f"    [ERROR] exited {r.returncode}: {r.stderr.strip()[:200]}")
    return r.returncode == 0


def run_nblm(*args, timeout=120):
    cmd = [NBLM] + list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] notebooklm {' '.join(args)}")
        return ""
    except FileNotFoundError:
        print("  [FATAL] notebooklm CLI not found.")
        sys.exit(1)


def get_subject_dir(subject):
    return SUBJECT_DIR_MAP.get(subject, subject)


def get_merged_path(subject):
    return TEXT_DIR / f"{get_subject_dir(subject)}_merged.md"


def merge_subject(subject):
    sd = TEXT_DIR / get_subject_dir(subject)
    if not sd.exists():
        return None
    mds = sorted(sd.rglob("*.md"))
    if not mds:
        return None
    merged = get_merged_path(subject)
    parts = []
    for f in mds:
        rel = f.relative_to(sd)
        parts.append(f"\n\n## {rel}\n\n")
        parts.append(f.read_text())
    merged.write_text("".join(parts))
    return merged


def needs_sync(subject, state):
    subj_state = state.get(subject, {})
    # Check if any files are newer than last sync
    sd = TEXT_DIR / get_subject_dir(subject)
    if not sd.exists():
        return True
    last = subj_state.get("last_synced", "")
    if not last:
        return True
    last_ts = datetime.fromisoformat(last).timestamp()
    for f in sd.rglob("*.md"):
        if f.stat().st_mtime > last_ts:
            return True
    return False


def sync_routine(state_file=STATE_FILE, skip_inventory=False, skip_download=False, skip_convert=False):
    state = {}
    if state_file.exists():
        state = json.loads(state_file.read_text())

    print(f"=== Toddle → NotebookLM Sync: {datetime.now().isoformat()} ===")

    # Phase 1: Inventory
    print("\n[Phase 1] Inventorying subject files from Toddle...")
    if not skip_inventory:
        if not run_script("toddle_all_inventory.py", timeout=600):
            print("  Inventory failed, continuing with existing data...")
    else:
        print("  (skipped)")

    # Phase 2: Download
    print("\n[Phase 2] Downloading subject files...")
    if not skip_download:
        run_script("toddle_bulk_download.py", timeout=600)
    else:
        print("  (skipped)")

    # Phase 3: Convert
    print("\n[Phase 3] Converting to markdown...")
    if not skip_convert:
        run_script("toddle_bulk_convert.py", timeout=600)
    else:
        print("  (skipped)")

    # Phase 4: Upload to NotebookLM
    print("\n[Phase 4] Uploading to NotebookLM...")
    for subject in SUBJECTS:
        if not needs_sync(subject, state):
            print(f"  SKIP {subject}: no changes since last sync")
            continue

        merged = merge_subject(subject)
        if merged is None:
            print(f"  SKIP {subject}: no text files")
            state[subject] = {"status": "empty"}
            state_file.write_text(json.dumps(state, indent=2))
            continue

        # Get notebook ID
        nb_id = state.get(subject, {}).get("notebook_id")
        if not nb_id:
            nb_name = f"{subject} Notes Grade 7"
            out = run_nblm("list", "--json", timeout=30)
            if out:
                try:
                    data = json.loads(out)
                    for nb in data.get("notebooks", []):
                        if nb.get("title") == nb_name:
                            nb_id = nb["id"]
                            break
                except (json.JSONDecodeError, KeyError):
                    pass
            if not nb_id:
                if subject == "Physics":
                    nb_id = PHYSICS_NOTEBOOK_ID
                else:
                    out = run_nblm("create", nb_name, "--json", timeout=30)
                    if out:
                        try:
                            nb_id = json.loads(out)["notebook"]["id"]
                        except (json.JSONDecodeError, KeyError):
                            pass
            if not nb_id:
                print(f"  FAIL {subject}: could not get notebook")
                continue

        # Upload
        file_size = merged.stat().st_size
        print(f"  Uploading {subject} ({file_size:,} bytes) → {nb_id[:8]}...")
        run_nblm("source", "add", str(merged), "--notebook", nb_id, timeout=120)

        # Generate study guide (background)
        print(f"  Launching study guide for {subject}...")
        run_nblm("generate", "report", "--format", "study-guide", "--notebook", nb_id, timeout=10)

        file_count = len(list(TEXT_DIR.joinpath(get_subject_dir(subject)).rglob("*.md")))
        state[subject] = {
            "status": "synced",
            "notebook_id": nb_id,
            "file_count": file_count,
            "size_bytes": file_size,
            "last_synced": datetime.now().isoformat(),
        }
        state_file.write_text(json.dumps(state, indent=2))
        print(f"  DONE {subject}")

    # Summary
    synced = sum(1 for v in state.values() if v.get("status") == "synced")
    print(f"\n=== Sync complete: {synced}/{len(SUBJECTS)} subjects ===")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sync Toddle notes to NotebookLM daily")
    parser.add_argument("--state", default=str(STATE_FILE), help="Path to sync state JSON")
    parser.add_argument("--skip-inventory", action="store_true", help="Skip Phase 1")
    parser.add_argument("--skip-download", action="store_true", help="Skip Phase 2")
    parser.add_argument("--skip-convert", action="store_true", help="Skip Phase 3")
    args = parser.parse_args()

    state_file = Path(args.state)
    sync_routine(state_file, skip_inventory=args.skip_inventory, skip_download=args.skip_download, skip_convert=args.skip_convert)
