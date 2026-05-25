"""Toddle inventory: discover all subjects and their class drive contents."""
import json, time
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

CDP = "http://localhost:9222"
OUT = Path("output/toddle_inventory")
COURSES_URL = "https://web.toddleapp.com/platform/3777/courses"

def get_drive_text(page):
    return (page.locator("body").text_content() or "")

def parse_drive_text(text):
    """Parse the flat text into structured folders and files."""
    folders = []; files = []
    for line in text.split("\n"):
        line = line.strip()
        if line.endswith("Folder") and "Folders" not in line and "folder selected" not in line:
            folders.append(line.replace("Folder", "").strip())
        elif any(ext in line for ext in [".docx", ".pptx", ".jpg", ".png", ".pdf", "Link"]):
            files.append(line)
    return folders, files

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("=== Toddle Full Inventory ===\n")
    
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP)
        context = browser.contexts[0]
        page = context.pages[0]
        page.bring_to_front()
        
        # Go to courses page
        page.goto(COURSES_URL)
        time.sleep(3)
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Get all unique courses
        buttons = page.eval_on_selector_all('[data-test-id^="button-course-"]',
            'els => els.map(el => ({testid: el.getAttribute("data-test-id"), text: el.textContent.trim()}))')
        
        seen = set(); courses = []
        for b in buttons:
            cid = b["testid"].replace("button-course-", "")
            if cid not in seen:
                seen.add(cid)
                parts = b["text"].split("Grade")
                courses.append({"id": cid, "name": parts[0].strip()})
        
        print(f"Courses: {len(courses)}")
        
        inventory = {}
        
        for i, course in enumerate(courses):
            name, cid = course["name"], course["id"]
            print(f"\n[{i+1}/{len(courses)}] {name}")
            
            card = page.locator(f'[data-test-id="button-course-{cid}"]')
            if card.count() == 0: continue
            card.click()
            time.sleep(3); page.wait_for_load_state("networkidle"); time.sleep(1)
            
            drive_btn = page.locator('[data-test-id="course-sidebar-menu-item-STUDENT_DRIVE"]')
            if drive_btn.count() == 0:
                inventory[name] = {"id": cid, "note": "no drive"}
                page.goto(COURSES_URL); time.sleep(3)
                continue
            
            drive_btn.click()
            time.sleep(3); page.wait_for_load_state("networkidle"); time.sleep(1)
            
            drive_url = page.url
            text = get_drive_text(page)
            top_folders, top_files = parse_drive_text(text)
            inventory[name] = {"id": cid, "drive_url": drive_url, "folders": [], "files": top_files}
            print(f"  Folders: {len(top_folders)}, Files: {len(top_files)}")
            
            # Explore each folder via double-click
            for fname in top_folders:
                try:
                    page.goto(drive_url)
                    time.sleep(2); page.wait_for_load_state("networkidle"); time.sleep(1)
                    
                    folder_el = page.get_by_text(fname, exact=True).first
                    if folder_el.count() == 0: continue
                    folder_el.dblclick()
                    time.sleep(2); page.wait_for_load_state("networkidle"); time.sleep(1)
                    
                    folder_url = page.url
                    ftext = get_drive_text(page)
                    sub_folders, sub_files = parse_drive_text(ftext)
                    
                    # Remove items that are in the parent
                    parent_items = set(top_folders + top_files)
                    sub_files = [f for f in sub_files if f not in parent_items]
                    
                    inventory[name]["folders"].append({
                        "name": fname,
                        "url": folder_url,
                        "subfolders": sub_folders,
                        "files": sub_files
                    })
                    print(f"    {fname}: {len(sub_files)} files, {len(sub_folders)} subfolders")
                except Exception as e:
                    print(f"    {fname}: ERROR {e}")
            
            page.goto(COURSES_URL); time.sleep(3)
        
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = OUT / f"inventory_{ts}.json"
        path.write_text(json.dumps(inventory, indent=2, default=str))
        print(f"\nSaved: {path}")

if __name__ == "__main__":
    main()
