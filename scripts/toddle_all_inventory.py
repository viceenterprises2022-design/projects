"""Inventory all remaining subjects - get folder/file IDs."""
import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright

CDP = "http://localhost:9222"
OUT = Path("output/toddle_inventory")

subjects = [
    ("English", "272491078215633905"),
    ("Biology", "272491078391794767"),
    ("History", "272491078920818849"),
    ("Geography", "272491078975894096"),
    ("Spanish", "272620157786304607"),
    ("Design", "272491078815653780"),
    ("Assembly", "272491078890115225"),
    ("Visual Arts", "272491078744215539"),
]

OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(CDP)
    page = b.contexts[0].pages[0]
    all_data = {}
    existing = OUT / "all_subjects_inventory.json"
    if existing.exists():
        all_data = json.loads(existing.read_text())
        print(f"Loaded existing: {len(all_data)} subjects already saved")

    for subj, cid in subjects:
        if subj in all_data:
            print(f"\nSKIP {subj} (already saved)")
            continue
        print(f"\n{'-'*50}\n{subj}")
        page.goto(f"https://web.toddleapp.com/platform/3777/courses/{cid}/student-drive")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        folder_cards = page.eval_on_selector_all(
            '[data-test-id*="folder"][data-test-id*="mediacard"]',
            '''els => els.map(el => ({
                testid: el.getAttribute("data-test-id"),
                text: (el.textContent||"").trim().slice(0,80)
            }))'''
        )

        seen = set()
        folders = []
        for fc in folder_cards:
            tid = fc["testid"]
            parts = tid.split("-resourceItemList-")
            if len(parts) > 1:
                fid = parts[1].split("-")[0]
                if fid not in seen:
                    seen.add(fid)
                    name = fc["text"].replace("Folder", "").strip()
                    folders.append({"id": fid, "name": name})

        print(f"  Folders: {len(folders)}")
        subject_data = {"course_id": cid, "folders": [], "root_files": []}

        for f in folders:
            print(f"    {f['name']}...", end=" ", flush=True)
            page.goto(f"https://web.toddleapp.com/platform/3777/courses/{cid}/student-drive/{f['id']}")
            page.wait_for_load_state("networkidle")
            time.sleep(1.5)

            file_cards = page.eval_on_selector_all(
                '[data-test-id*="file"][data-test-id*="mediacard"]',
                '''els => els.map(el => ({
                    testid: el.getAttribute("data-test-id"),
                    text: (el.textContent||"").trim().slice(0,120)
                }))'''
            )

            file_seen = set()
            files = []
            for fc in file_cards:
                tid = fc["testid"]
                parts = tid.split("-resourceItemList-")
                if len(parts) > 1:
                    fid = parts[1].split("-")[0]
                    if fid not in file_seen:
                        file_seen.add(fid)
                        fname = fc["text"]
                        for s in ["Word Document", "Presentation", "Image", "Link", "("]:
                            idx = fname.find(s)
                            if idx > 0: fname = fname[:idx]
                        fname = fname.strip()
                        files.append({"id": fid, "name": fname})

            print(f"{len(files)} files")
            subject_data["folders"].append({"name": f["name"], "id": f["id"], "files": files})

        # Root files
        page.goto(f"https://web.toddleapp.com/platform/3777/courses/{cid}/student-drive")
        page.wait_for_load_state("networkidle")
        time.sleep(1.5)

        root_cards = page.eval_on_selector_all(
            '[data-test-id*="file"][data-test-id*="mediacard"]',
            '''els => els.map(el => ({
                testid: el.getAttribute("data-test-id"),
                text: (el.textContent||"").trim().slice(0,120)
            }))'''
        )
        root_seen = set()
        for fc in root_cards:
            parts = fc["testid"].split("-resourceItemList-")
            if len(parts) > 1:
                fid = parts[1].split("-")[0]
                if fid not in root_seen:
                    root_seen.add(fid)
                    fname = fc["text"]
                    for s in ["Word Document", "Presentation", "Image", "Link", "("]:
                        idx = fname.find(s)
                        if idx > 0: fname = fname[:idx]
                    fname = fname.strip()
                    subject_data["root_files"].append({"id": fid, "name": fname})

        print(f"  Root files: {len(subject_data['root_files'])}")
        all_data[subj] = subject_data
        (OUT / "all_subjects_inventory.json").write_text(json.dumps(all_data, indent=2))
        print(f"  [saved: {subj}]")
        if len(all_data) >= 4:  # Save every 4 to manage timeout
            print("  [break for timeout safety]")
            break

    path = OUT / "all_subjects_inventory.json"
    path.write_text(json.dumps(all_data, indent=2))
    print(f"  [saved interim: {len(all_data)} subjects]")

    total_files = 0
    for subj, data in all_data.items():
        count = sum(len(f["files"]) for f in data["folders"]) + len(data["root_files"])
        total_files += count
        print(f"\n{subj}: {count} total files")
    print(f"\nGrand total: {total_files} files")
