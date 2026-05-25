"""Connect to real Chrome via CDP, navigate to Toddle, save DOM snapshots.

Usage:
  1. Start Chrome with remote debugging:
     google-chrome --remote-debugging-port=9222
  
  2. Navigate to https://web.toddleapp.com manually in that Chrome
     Log into Family account → Google SSO should work
  
  3. Run this script to connect and take DOM snapshots
  
  Signals:
     echo done > /tmp/toddle_signal    # take snapshot
     echo stop > /tmp/toddle_signal    # exit
"""

import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

SIGNAL = Path("/tmp/toddle_signal")
SNAP_DIR = Path("output/snapshots")

def save_snapshot(page, name):
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%H%M%S")
    page.screenshot(path=str(SNAP_DIR / f"{name}_{ts}.png"))
    html = page.content()
    (SNAP_DIR / f"{name}_{ts}.html").write_text(html, encoding="utf-8")
    body = page.locator("body").text_content() or ""
    (SNAP_DIR / f"{name}_{ts}_text.txt").write_text(body, encoding="utf-8")
    clickable = page.evaluate("""() =>
        [...document.querySelectorAll('a, button, [role=button]')]
          .map(e => e.textContent.trim()).filter(Boolean)
    """) or []
    (SNAP_DIR / f"{name}_{ts}_links.txt").write_text("\n".join(clickable), encoding="utf-8")
    print(f"  Saved {name}_{ts}_* ({len(clickable)} links)")

def explore():
    print("=== Toddle CDP Discovery ===")
    print("Connecting to Chrome on port 9222...")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        print(f"Connected! Contexts: {len(browser.contexts)}")
        
        if browser.contexts:
            context = browser.contexts[0]
        else:
            context = browser.new_context()
        
        pages = context.pages
        print(f"Open tabs: {len(pages)}")
        for i, pg in enumerate(pages):
            print(f"  [{i}] {pg.url[:80]}")

        page = pages[0] if pages else context.new_page()

        save_snapshot(page, "initial")

        print("\n✔ Connected. Navigate Toddle in your Chrome browser.")
        print("  Signal: echo done > /tmp/toddle_signal")
        print("  Stop:   echo stop > /tmp/toddle_signal")

        SIGNAL.unlink(missing_ok=True)
        while True:
            time.sleep(2)
            if SIGNAL.exists():
                cmd = SIGNAL.read_text().strip()
                SIGNAL.unlink(missing_ok=True)
                if cmd == "stop":
                    break
                if pages:
                    page = pages[0]
                save_snapshot(page, "explore")

    print("\nDone. Check output/snapshots/")

if __name__ == "__main__":
    explore()
