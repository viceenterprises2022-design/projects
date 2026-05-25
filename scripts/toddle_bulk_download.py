"""Bulk download all subjects' files from Toddle inventory."""
import json, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

CDP = "http://localhost:9222"
INV = Path("output/toddle_inventory/all_subjects_inventory.json")
DL = Path("output/downloads")

def download_subject(page, subj, data):
    cid = data["course_id"]
    sdir = DL / subj
    sdir.mkdir(parents=True, exist_ok=True)
    total = 0
    errors = 0
    skipped = 0

    for folder in data["folders"]:
        fname = folder["name"].replace("/", "_").replace(":", "_").strip() or "Unnamed"
        fdir = sdir / fname
        fdir.mkdir(exist_ok=True)

        print(f"  [{subj}] Folder: {fname} ({len(folder['files'])} files)")
        page.goto(f"https://web.toddleapp.com/platform/3777/courses/{cid}/student-drive/{folder['id']}")
        page.wait_for_load_state("networkidle")
        time.sleep(1.5)

        for f in folder["files"]:
            fid = f["id"]
            fname_clean = f["name"].replace("/", "_").replace(":", "_")[:100] or fid
            fpath = fdir / fname_clean

            # Check if any file with same name exists
            existing = list(fdir.glob(f"{fname_clean}.*"))
            if existing:
                skipped += 1
                continue

            try:
                card = page.locator(f'[data-test-id*="resourceItemList-{fid}-resourceItem-mediacard"]')
                if card.count() == 0:
                    print(f"    MISS {f['name'][:50]}")
                    continue

                card.click()
                time.sleep(0.5)

                dl_btn = page.get_by_text("Download", exact=True)
                if dl_btn.count() == 0:
                    print(f"    LINK {f['name'][:50]}")
                    continue

                with page.expect_download(timeout=15000) as dl_info:
                    dl_btn.first.click()
                    time.sleep(1)

                dl = dl_info.value
                suggested = dl.suggested_filename
                ext = Path(suggested).suffix if suggested else ""
                save_name = f"{fname_clean}{ext}"
                dl.save_as(str(fdir / save_name))
                total += 1
                time.sleep(0.5)

            except Exception as e:
                print(f"    ERR {f['name'][:40]}: {str(e)[:60]}")
                errors += 1
                time.sleep(1)

    # Root files
    root_files = data.get("root_files", [])
    if root_files:
        print(f"  [{subj}] Root: {len(root_files)} files")
        page.goto(f"https://web.toddleapp.com/platform/3777/courses/{cid}/student-drive")
        page.wait_for_load_state("networkidle")
        time.sleep(1.5)

        for f in root_files:
            try:
                card = page.locator(f'[data-test-id*="resourceItemList-{f["id"]}-resourceItem-mediacard"]')
                if card.count() == 0: continue
                card.click()
                time.sleep(0.5)
                dl_btn = page.get_by_text("Download", exact=True)
                if dl_btn.count() == 0: continue
                with page.expect_download(timeout=15000) as dl_info:
                    dl_btn.first.click()
                    time.sleep(1)
                dl = dl_info.value
                ext = Path(dl.suggested_filename).suffix if dl.suggested_filename else ""
                save_name = f"{f['name'][:100]}{ext}"
                dl.save_as(str(sdir / save_name))
                total += 1
                time.sleep(0.5)
            except Exception as e:
                print(f"    ERR root {f['name'][:40]}: {str(e)[:60]}")
                errors += 1

    return total, errors, skipped

def main():
    data = json.loads(INV.read_text())
    DL.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(CDP)
        page = b.contexts[0].pages[0]

        grand_total = 0
        grand_errors = 0
        grand_skipped = 0

        for subj in ["Chemistry", "Mathematics", "English", "Biology", "History", "Geography", "Spanish", "Design", "Visual Arts"]:
            if subj not in data:
                print(f"\nSKIP {subj} (no inventory)")
                continue
            print(f"\n{'='*50}\nDownloading: {subj}")
            t, e, s = download_subject(page, subj, data[subj])
            grand_total += t
            grand_errors += e
            grand_skipped += s
            print(f"  [{subj}] Downloaded: {t}, Errors: {e}, Skipped: {s}")

        print(f"\n{'='*50}")
        print(f"Total: {grand_total} new files, {grand_skipped} skipped, {grand_errors} errors")

if __name__ == "__main__":
    main()
