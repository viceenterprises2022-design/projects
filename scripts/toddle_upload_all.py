"""Upload each subject to dedicated NotebookLM notebook."""
import json, subprocess, sys
from pathlib import Path

TEXT_DIR = Path("output/text")
NBLM = "notebooklm"
STATE = Path("sync_state.json")

def run(*args, timeout=120):
    cmd = [NBLM] + list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            print(f"  WARN: {' '.join(args)[:60]} exited {r.returncode}")
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT: {' '.join(args)[:60]}")
        return ""

def merge_subject(subj):
    sd = TEXT_DIR / subj
    if not sd.exists():
        return None
    mds = sorted(sd.rglob("*.md"))
    if not mds:
        return None
    
    merged = TEXT_DIR / f"{subj}_merged.md"
    parts = []
    for f in mds:
        rel = f.relative_to(sd)
        parts.append(f"\n\n## {rel}\n\n")
        parts.append(f.read_text())
    merged.write_text("".join(parts))
    size = merged.stat().st_size
    print(f"  Merged: {len(mds)} files → {size:,} bytes")
    return merged

def find_or_create_nb(subj):
    nb_name = f"{subj} Notes Grade 7"
    out = run("list", "--json", timeout=30)
    if out:
        try:
            data = json.loads(out)
            for nb in data.get("notebooks", []):
                if nb.get("title") == nb_name:
                    print(f"  Found existing: {nb_name}")
                    return nb["id"]
        except (json.JSONDecodeError, KeyError):
            pass
    
    print(f"  Creating: {nb_name}")
    out = run("create", nb_name, "--json", timeout=30)
    if out:
        try:
            nb = json.loads(out)
            nid = nb["notebook"]["id"]
            link = nb["notebook"].get("notebooklm_url", "")
            if link: print(f"  URL: {link}")
            return nid
        except (json.JSONDecodeError, KeyError):
            pass
    return None

def main():
    subjects = ["Physics", "Chemistry", "Mathematics", "English", "Biology", "History", "Geography", "Spanish", "Design", "Visual Arts"]
    state = {}
    if STATE.exists():
        state = json.loads(STATE.read_text())
    
    for subj in subjects:
        print(f"\n{'='*50}\n{subj}")
        
        # Skip if already synced
        if subj in state and state[subj].get("status") == "synced":
            print(f"  SKIP (already synced at {state[subj].get('last_synced','?')})")
            continue
        
        merged = merge_subject(subj)
        if merged is None:
            print(f"  SKIP: no text files")
            state[subj] = {"status": "empty"}
            STATE.write_text(json.dumps(state, indent=2))
            continue
        
        nb_id = find_or_create_nb(subj)
        if not nb_id:
            print(f"  FAIL: could not get notebook")
            continue
        
        print(f"  Uploading source...")
        out = run("source", "add", str(merged), "--notebook", nb_id, "--json", timeout=120)
        
        state[subj] = {
            "status": "synced",
            "notebook_id": nb_id,
            "file_count": len(list(TEXT_DIR.joinpath(subj).rglob("*.md"))),
            "size_bytes": merged.stat().st_size,
            "last_synced": subprocess.run(["date", "+%Y-%m-%dT%H:%M:%S"], capture_output=True, text=True).stdout.strip(),
        }
        STATE.write_text(json.dumps(state, indent=2))
        print(f"  DONE: {subj} → notebook {nb_id[:8]}")
    
    print(f"\n{'='*50}")
    synced = sum(1 for v in state.values() if v.get("status") == "synced")
    print(f"Synced: {synced}/{len(subjects)} subjects")

if __name__ == "__main__":
    main()
