"""Get file inventory for Physics only - fast version."""
import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright

CDP = "http://localhost:9222"
OUT = Path("output/toddle_inventory")

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(CDP)
    page = b.contexts[0].pages[0]

    course_id = "272491078354045998"
    page.goto(f"https://web.toddleapp.com/platform/3777/courses/{course_id}/student-drive")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # Get all folder mediacards at root
    folder_cards = page.eval_on_selector_all(
        '[data-test-id*="folder"][data-test-id*="mediacard"]',
        '''els => els.map(el => ({
            testid: el.getAttribute("data-test-id"),
            text: (el.textContent||"").trim().slice(0,80)
        }))'''
    )

    folders = []
    seen = set()
    for fc in folder_cards:
        tid = fc["testid"]
        parts = tid.split("-resourceItemList-")
        if len(parts) > 1:
            fid = parts[1].split("-")[0]
            if fid not in seen:
                seen.add(fid)
                name = fc["text"].replace("Folder", "").strip()
                folders.append({"id": fid, "name": name})

    print(f"Physics folders ({len(folders)}):")
    physics_data = {"folders": []}

    for f in folders:
        print(f"  {f['name']} (id: {f['id']})...", end=" ", flush=True)
        
        # Use URL-based navigation instead of double-click
        page.goto(f"https://web.toddleapp.com/platform/3777/courses/{course_id}/student-drive/{f['id']}")
        page.wait_for_load_state("networkidle")
        time.sleep(1.5)
        
        # Get files in this folder
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
        physics_data["folders"].append({"name": f["name"], "id": f["id"], "files": files})
    
    # Also save root-level files
    page.goto(f"https://web.toddleapp.com/platform/3777/courses/{course_id}/student-drive")
    page.wait_for_load_state("networkidle")
    time.sleep(1.5)
    
    root_files = page.eval_on_selector_all(
        '[data-test-id*="file"][data-test-id*="mediacard"]',
        '''els => els.map(el => ({
            testid: el.getAttribute("data-test-id"),
            text: (el.textContent||"").trim().slice(0,120)
        }))'''
    )
    
    root_seen = set()
    root_file_list = []
    for fc in root_files:
        tid = fc["testid"]
        parts = tid.split("-resourceItemList-")
        if len(parts) > 1:
            fid = parts[1].split("-")[0]
            if fid not in root_seen:
                root_seen.add(fid)
                fname = fc["text"]
                for s in ["Word Document", "Presentation", "Image", "Link", "("]:
                    idx = fname.find(s)
                    if idx > 0: fname = fname[:idx]
                fname = fname.strip()
                root_file_list.append({"id": fid, "name": fname})
    
    physics_data["root_files"] = root_file_list
    print(f"  Root files: {len(root_file_list)}")
    
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "physics_inventory.json").write_text(json.dumps(physics_data, indent=2))
    
    total = sum(len(f["files"]) for f in physics_data["folders"]) + len(root_file_list)
    print(f"\nTotal: {total} files in Physics")
