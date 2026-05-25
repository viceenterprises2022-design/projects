"""Upload Physics content to NotebookLM."""
import json, subprocess, sys
from pathlib import Path

TEXT_DIR = Path("output/text/physics")
NBLM = "notebooklm"

def run(*args, timeout=120):
    cmd = [NBLM] + list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            print(f"  WARN: {' '.join(args)} exited {r.returncode}: {r.stderr.strip()[:200]}")
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT: {' '.join(args)}")
        return ""

# 1. Create merged markdown per folder
merged = Path("output/text/physics_merged.md")
parts = []
for fpath in sorted(TEXT_DIR.rglob("*.md")):
    rel = fpath.relative_to(TEXT_DIR)
    parts.append(f"\n\n## Source: {rel}\n\n")
    parts.append(fpath.read_text())

merged.parent.mkdir(parents=True, exist_ok=True)
merged.write_text("".join(parts))
print(f"Merged: {merged.stat().st_size:,} bytes from {len(list(TEXT_DIR.rglob('*.md')))} files")

# 2. Create notebook
NB_NAME = "Physics Notes Grade 7"
print(f"\nCreating notebook: {NB_NAME}")
out = run("create", NB_NAME, "--json", timeout=30)
if not out:
    print("FAILED to create notebook!")
    sys.exit(1)

try:
    nb = json.loads(out)
    nb_id = nb["notebook"]["id"]
    nb_link = nb["notebook"].get("notebooklm_url", "")
    print(f"Created: {nb_id}")
    if nb_link:
        print(f"URL: {nb_link}")
except (json.JSONDecodeError, KeyError) as e:
    print(f"Parse error: {e}")
    print(f"Raw: {out[:200]}")
    sys.exit(1)

# 3. Upload file
print(f"\nUploading source...")
out = run("source", "add", str(merged), "--notebook", nb_id, "--json", timeout=120)
if out:
    try:
        src = json.loads(out)
        print(f"Uploaded: {src.get('source', {}).get('display_name', 'ok')}")
    except json.JSONDecodeError:
        print(f"Upload done: {out[:100]}")
else:
    print("Upload may have failed")

# 4. Generate study guide
print(f"\nGenerating study guide...")
out = run("generate", "report", "--format", "study-guide", "--notebook", nb_id, "--json", timeout=300)
if out:
    print(f"Study guide generated ({len(out)} chars)")
else:
    print("Study guide generation timed out or failed (can retry manually)")

print(f"\nDone! Notebook: {NB_NAME}")
print(f"https://notebooklm.google.com/notebook/{nb_id}")
