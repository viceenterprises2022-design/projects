"""Deep inventory: explore subfolders and capture file IDs for key subjects."""
import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright

CDP = "http://localhost:9222"
OUT = Path("output/toddle_inventory")

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(CDP)
        page = b.contexts[0].pages[0]

        targets = [
            ("Physics", "272491078354045998"),
            ("Chemistry", "272491078261771262"),
            ("Mathematics", "272491078446320765"),
            ("Biology", "272491078391794767"),
            ("English", "272491078215633905"),
        ]

        all_data = {}

        for subj_name, course_id in targets:
            print(f"\n{'='*50}\nExploring: {subj_name}")
            page.goto(f"https://web.toddleapp.com/platform/3777/courses/{course_id}/student-drive")
            time.sleep(3)
            page.wait_for_load_state("networkidle")
            time.sleep(2)

            folders = page.eval_on_selector_all(
                '[data-test-id*="resourceItemList-"][data-test-id*="folder"]',
                '''els => els.map(el => ({
                    testid: el.getAttribute("data-test-id"),
                    text: (el.textContent||"").trim().slice(0,80)
                }))'''
            )

            seen = set()
            unique_folders = []
            for f in folders:
                tid = f["testid"]
                parts = tid.split("-resourceItemList-")
                if len(parts) > 1:
                    fid = parts[1].split("-")[0]
                    if fid not in seen:
                        seen.add(fid)
                        name = f["text"].replace("Folder", "").strip()
                        unique_folders.append({"id": fid, "name": name})

            print(f"  Folders: {len(unique_folders)}")
            subject_data = {"folders": []}

            for folder in unique_folders:
                print(f"    {folder['name']}...", end=" ", flush=True)

                card = page.locator(f'[data-test-id*="resourceItemList-{folder["id"]}-resourceItem-mediacard"]')
                if card.count() == 0:
                    print("NO CARD")
                    continue

                card.dblclick()
                time.sleep(2)
                page.wait_for_load_state("networkidle")
                time.sleep(1)

                file_data = page.eval_on_selector_all(
                    '[data-test-id*="resourceItemList-"][data-test-id*="file"]',
                    '''els => els.map(el => ({
                        testid: el.getAttribute("data-test-id"),
                        text: (el.textContent||"").trim().slice(0,100)
                    }))'''
                )

                file_seen = set()
                folder_files = []
                for fe in file_data:
                    tid = fe["testid"]
                    if "mediacard" not in tid:
                        continue
                    parts = tid.split("-resourceItemList-")
                    if len(parts) > 1:
                        fid = parts[1].split("-")[0]
                        if fid not in file_seen:
                            file_seen.add(fid)
                            fname = fe["text"]
                            for suffix in ["Word Document", "Presentation", "Image", "Link"]:
                                fname = fname.replace(suffix, "")
                            fname = fname.strip().rstrip("(").strip()
                            folder_files.append({"id": fid, "name": fname})

                print(f"{len(folder_files)} files")
                subject_data["folders"].append({
                    "name": folder["name"],
                    "id": folder["id"],
                    "files": folder_files,
                })

                page.goto(f"https://web.toddleapp.com/platform/3777/courses/{course_id}/student-drive")
                time.sleep(2)
                page.wait_for_load_state("networkidle")
                time.sleep(1)

            all_data[subj_name] = subject_data

        path = OUT / "deep_inventory.json"
        path.write_text(json.dumps(all_data, indent=2))
        print(f"\nSaved: {path}")

        total = 0
        for subj, data in all_data.items():
            count = sum(len(f["files"]) for f in data["folders"])
            print(f"{subj}: {len(data['folders'])} folders, {count} files")
            total += count
        print(f"\nTotal: {total} files across {len(all_data)} subjects")

if __name__ == "__main__":
    main()
