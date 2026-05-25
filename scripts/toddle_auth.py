"""Open Toddle, let user login manually, save auth state after 120s."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

AUTH_FILE = Path("toddle_auth.json")

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()
    page.goto("https://web.toddleapp.com", wait_until="domcontentloaded")
    print("Browser open. Log in to Toddle manually in the browser.")
    print(f"Saving auth state to {AUTH_FILE} after 120s...")
    time.sleep(120)
    context.storage_state(path=str(AUTH_FILE))
    print(f"Saved! File size: {AUTH_FILE.stat().st_size} bytes")
    print("Browser stays open. Closing in 10s...")
    time.sleep(10)
    browser.close()
    print("Done.")
