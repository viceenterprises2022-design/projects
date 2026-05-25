"""Download all Physics files from Toddle."""
import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright

CDP = "http://localhost:9222"
INV = Path("output/toddle_inventory/physics_inventory.json")
DL = Path("output/downloads/physics")

DL.mkdir(parents=True, exist_ok=True)
data = json.loads(INV.read_text())
course_id = "272491078354045998"

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(CDP)
    page = b.contexts[0].pages[0]

    total = 0
    errors = 0

    for folder in data["folders"]:
        fname = folder["name"]
        fdir = fname.replace("/", "_").replace(":", "_")
        (DL / fdir).mkdir(exist_ok=True)

        print(f"\nFolder: {fname} ({len(folder['files'])} files)")
        page.goto(f"https://web.toddleapp.com/platform/3777/courses/{course_id}/student-drive/{folder['id']}")
        page.wait_for_load_state("networkidle")
        time.sleep(1.5)

        for f in folder["files"]:
            fid = f["id"]
            fpath = DL / fdir / (f["name"] or fid)

            if fpath.exists() and fpath.stat().st_size > 0:
                print(f"  SKIP {f['name']} (exists)")
                continue

            try:
                card = page.locator(f'[data-test-id*="resourceItemList-{fid}-resourceItem-mediacard"]')
                if card.count() == 0:
                    print(f"  MISS {f['name']} (no card)")
                    continue

                card.click()
                time.sleep(0.5)

                dl_btn = page.get_by_text("Download", exact=True)
                if dl_btn.count() == 0:
                    print(f"  NOBTN {f['name']}")
                    continue

                with page.expect_download(timeout=15000) as dl_info:
                    dl_btn.first.click()
                    time.sleep(1)

                dl = dl_info.value
                suggested = dl.suggested_filename or f["name"]
                ext = Path(suggested).suffix or ""
                save_name = f"{f['name']}{ext}".replace("/", "_")
                dl.save_as(str(DL / fdir / save_name))
                print(f"  OK {save_name} ({Path(suggested).suffix})")
                total += 1
                time.sleep(0.5)

            except Exception as e:
                print(f"  ERR {f['name']}: {e}")
                errors += 1
                time.sleep(1)

    # Root files
    if data.get("root_files"):
        print(f"\nRoot files ({len(data['root_files'])})")
        page.goto(f"https://web.toddleapp.com/platform/3777/courses/{course_id}/student-drive")
        page.wait_for_load_state("networkidle")
        time.sleep(1.5)

        for f in data["root_files"]:
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
                ext = Path(dl.suggested_filename).suffix or ""
                save_name = f"{f['name']}{ext}".replace("/", "_")
                dl.save_as(str(DL / save_name))
                print(f"  OK {save_name}")
                total += 1
                time.sleep(0.5)
            except Exception as e:
                print(f"  ERR {f['name']}: {e}")
                errors += 1

    print(f"\nDone: {total} downloaded, {errors} errors")
