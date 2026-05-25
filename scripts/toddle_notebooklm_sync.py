#!/usr/bin/env python3
"""Toddle → NotebookLM daily sync orchestrator.

1. Extracts subject notes from Toddle via Playwright
2. Diffs content hashes against sync_state.json
3. Uploads changed/new subjects to NotebookLM
4. Generates study-guide reports for updated notebooks
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import toddle_config as cfg
from toddle_extractor import extract

NBLM = "notebooklm"


def run_nblm(*args, timeout=120):
    cmd = [NBLM] + list(args)
    if cfg.NOTEBOOKLM_PROFILE != "default":
        cmd = [NBLM, "-p", cfg.NOTEBOOKLM_PROFILE] + list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0 and r.returncode != 2:
            print(f"  [WARN] notebooklm {' '.join(args)} exited {r.returncode}: {r.stderr.strip()}")
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"  [WARN] notebooklm {' '.join(args)} timed out after {timeout}s")
        return ""
    except FileNotFoundError:
        print("  [FATAL] notebooklm CLI not found. Install: pip install notebooklm-py")
        sys.exit(1)


def load_state():
    if cfg.STATE_FILE.exists():
        return json.loads(cfg.STATE_FILE.read_text())
    return {"subjects": {}}


def save_state(state):
    cfg.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    cfg.STATE_FILE.write_text(json.dumps(state, indent=2, default=str))


def find_notebook_id(subject_name):
    nb_name = f"{cfg.NOTEBOOK_PREFIX}{subject_name} Notes"
    out = run_nblm("list", "--json", timeout=30)
    if not out:
        return None
    try:
        data = json.loads(out)
        for nb in data.get("notebooks", []):
            if nb.get("title") == nb_name:
                return nb["id"]
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def create_notebook(subject_name):
    nb_name = f"{cfg.NOTEBOOK_PREFIX}{subject_name} Notes"
    print(f"  Creating notebook: {nb_name}")
    out = run_nblm("create", nb_name, "--json", timeout=30)
    if out:
        try:
            return json.loads(out)["notebook"]["id"]
        except (json.JSONDecodeError, KeyError):
            return None
    return None


def sync_subject(subject, info, state):
    subj_state = state["subjects"].get(subject, {})
    prev_hash = subj_state.get("content_hash", "")
    cur_hash = info["content_hash"]

    if cur_hash == prev_hash and subj_state.get("notebook_id"):
        print(f"  SKIP {subject}: unchanged (hash: {cur_hash[:12]}...)")
        return

    notebook_id = subj_state.get("notebook_id") or find_notebook_id(subject)
    if not notebook_id:
        notebook_id = create_notebook(subject)
        if not notebook_id:
            print(f"  FAIL {subject}: could not create notebook")
            return

    filepath = info["filepath"]
    print(f"  Uploading {subject} -> notebook {notebook_id[:8]}...")
    run_nblm("source", "add", filepath, "--notebook", notebook_id, "--json", timeout=60)
    print(f"  Generating study guide for {subject}...")
    run_nblm("generate", "report", "--format", "study-guide", "--notebook", notebook_id, "--json", timeout=300)

    state["subjects"][subject] = {
        "notebook_id": notebook_id,
        "notebook_name": f"{cfg.NOTEBOOK_PREFIX}{subject} Notes",
        "content_hash": cur_hash,
        "last_synced": datetime.now().isoformat(),
        "char_count": info.get("char_count", 0),
    }
    save_state(state)


def sync():
    print(f"=== Toddle → NotebookLM Sync: {datetime.now().isoformat()} ===")
    cfg.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    state = load_state()
    print("\n[Phase 1] Extracting Toddle content...")
    results = extract()

    if not results:
        print("\nNo subjects extracted. Check Toddle credentials or DOM structure.")
        print("Run with: python3 toddle_extractor.py --headed")
        sys.exit(1)

    print(f"\n[Phase 2] Syncing {len(results)} subjects to NotebookLM...")
    for subject, info in results.items():
        sync_subject(subject, info, state)

    print(f"\nDone. Synced {len(results)} subjects.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sync Toddle notes to NotebookLM")
    parser.add_argument("--headed", action="store_true", help="Show browser window")
    parser.add_argument("--subject", "-s", help="Sync only one subject")
    args = parser.parse_args()

    if args.headed:
        cfg.HEADLESS = False

    if args.subject:
        cfg.ALLOWED_SUBJECTS = [args.subject]

    sync()
