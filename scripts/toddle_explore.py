"""Toddle DOM discovery — automates Google SSO login, then waits for user to navigate.

Usage:
  1. Set TODDLE_GOOGLE_EMAIL / TODDLE_GOOGLE_PASSWORD in .env
  2. Run: python3 toddle_explore.py
  3. Log in is automated via Google SSO
  4. After login, manually navigate in the browser
  5. When ready for snapshot, create signal file

Signals (run in another terminal):
  echo done > /tmp/toddle_signal       # snapshots current page (re-triggerable)
  echo stop > /tmp/toddle_signal       # end session
"""

import sys
import time
import re
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

import toddle_config as cfg

SIGNAL = Path("/tmp/toddle_signal")
SNAP_DIR = Path("output/snapshots")

def clear_signal():
    SIGNAL.unlink(missing_ok=True)

def wait_or_signal(label, timeout=600):
    print(f"\n=== {label} ===")
    print(f"Signals: echo done > {SIGNAL} | echo stop > {SIGNAL}")
    print(f"Waiting up to {timeout}s...")
    clear_signal()
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(1)
        if SIGNAL.exists():
            cmd = SIGNAL.read_text().strip()
            clear_signal()
            if cmd == "stop":
                print("  Stop signal. Exiting.")
                return "stop"
            print("  Signal received. Proceeding.")
            return "done"
    print("  Timeout.")
    return "timeout"

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
    return ts

def login(page):
    print("- Navigating to Toddle...")
    page.goto(cfg.TODDLE_URL, wait_until="networkidle")
    page.wait_for_timeout(2000)

    body = page.locator("body").text_content() or ""
    if "Family account" in body or "family" in body.lower():
        print("- Clicking 'Family account'...")
        for btn_text in ["Family account", "Family", "family"]:
            btn = page.locator(f"text={btn_text}").first
            if btn.is_visible(timeout=2000):
                btn.click()
                break
        page.wait_for_timeout(2000)

    page.wait_for_timeout(2000)
    body2 = page.locator("body").text_content() or ""

    if page.url.startswith("https://accounts.google.com") or "Sign in with Google" in body2 or "accounts.google" in page.url:
        print("- Google SSO page detected. Automating login...")
        google_login(page)
    else:
        print("- Checking for email/password fields...")
        email_el = page.locator('input[type="email"]').first
        if email_el.is_visible(timeout=3000):
            google_login(page)
        else:
            print("- No login form detected. May already be logged in.")

def google_login(page):
    email = cfg.TODDLE_GOOGLE_EMAIL or cfg.TODDLE_EMAIL
    pwd = cfg.TODDLE_GOOGLE_PASSWORD or cfg.TODDLE_PASSWORD
    if not email or not pwd:
        print("  WARNING: No Google credentials found in .env. Please log in manually.")
        return

    email_input = page.locator('input[type="email"]').first
    if email_input.is_visible(timeout=3000):
        print("  Filling email field...")
        email_input.fill(email)
        page.locator("#identifierNext, #next, button:has-text('Next')").first.click()
        page.wait_for_timeout(3000)

        try:
            page.wait_for_selector('input[type="password"]', timeout=10000)
            print("  Filling password field...")
            page.locator('input[type="password"]').first.fill(pwd)
            page.locator("#passwordNext, button:has-text('Next')").first.click()
            page.wait_for_timeout(5000)
        except PwTimeout:
            pass

        if "challenge" in page.url or "2fa" in page.url or page.locator("text=Enter code").is_visible(timeout=2000):
            print("  2FA detected! Check browser, enter code manually.")
            try:
                page.wait_for_url("**/toddleapp.com/**", timeout=120000)
            except PwTimeout:
                print("  2FA wait timed out.")
        else:
            page.wait_for_timeout(5000)
    else:
        print("  No email input found. May already be logged in.")

def explore():
    print("=== Toddle DOM Discovery ===")
    print(f"Browser: {'headed' if not cfg.HEADLESS else 'headless'}")
    print(f"Credentials: {'found' if (cfg.TODDLE_GOOGLE_EMAIL or cfg.TODDLE_EMAIL) else 'MISSING'}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        login(page)

        print("\n✔ Browser open. Navigate manually now.")
        print("  Signal commands: echo done > /tmp/toddle_signal  |  echo stop > /tmp/toddle_signal")

        while True:
            result = wait_or_signal("Waiting for signal...")
            if result == "stop":
                break
            save_snapshot(page, "explore")
            print("  Ready for next snapshot. Signal again or 'stop' to quit.")

        print("\nClosing browser.")
        browser.close()

    print("\nDone. Check output/snapshots/")

if __name__ == "__main__":
    explore()
