import re
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime

from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PwTimeout

import toddle_config as cfg

class ToddleExtractor:
    def __init__(self):
        self.results = {}
        self.browser = None
        self.context = None
        self.page = None

    def run(self):
        try:
            with sync_playwright() as p:
                self.browser = p.chromium.launch(
                    channel="chrome",
                    headless=cfg.HEADLESS,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                self.context = self.browser.new_context(
                    viewport={"width": 1280, "height": 900},
                    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
                )
                self.page = self.context.new_page()
                self._login()
                self._select_child()
                self._extract_all_subjects()
                return self.results
        except Exception as e:
            raise RuntimeError(f"Extraction failed: {e}") from e
        finally:
            if self.browser:
                self.browser.close()

    def _login(self):
        p = self.page
        p.goto(cfg.TODDLE_URL, wait_until="networkidle")
        p.wait_for_timeout(1500)

        login_btn = p.locator("text=Family account").first
        if login_btn.is_visible(timeout=5000):
            login_btn.click()
        else:
            login_btn = p.locator('[data-testid*="family"]').first
            if login_btn.is_visible(timeout=3000):
                login_btn.click()
            else:
                for btn_text in ["Family", "family", "Parent", "parent"]:
                    el = p.locator(f"text={btn_text}").first
                    if el.is_visible(timeout=2000):
                        el.click()
                        break

        p.wait_for_timeout(2000)

        if p.url.startswith("https://accounts.google.com") or p.locator("text=Sign in with Google").is_visible(timeout=3000):
            self._login_google()
        else:
            if p.locator('input[type="email"]').is_visible(timeout=3000):
                self._login_google()
            else:
                p.wait_for_timeout(2000)
                if "accounts.google" in p.url:
                    self._login_google()

        p.wait_for_load_state("networkidle")
        p.wait_for_timeout(3000)
        self._save_snapshot("after_login")

    def _login_google(self):
        p = self.page
        email = cfg.TODDLE_GOOGLE_EMAIL or cfg.TODDLE_EMAIL
        password = cfg.TODDLE_GOOGLE_PASSWORD or cfg.TODDLE_PASSWORD

        email_input = p.locator('input[type="email"]').first
        if email_input.is_visible(timeout=3000):
            email_input.fill(email)
            p.locator("text=Next").first.click()
            p.wait_for_timeout(2000)
            pwd_input = p.locator('input[type="password"]').first
            if pwd_input.is_visible(timeout=5000):
                pwd_input.fill(password)
                p.locator("text=Next").first.click()
                p.wait_for_timeout(3000)
                return

        google_btn = p.locator("text=Sign in with Google").first
        if google_btn.is_visible(timeout=3000):
            with p.expect_popup() as popup_info:
                google_btn.click()
            google_popup = popup_info.value
            google_popup.wait_for_load_state("networkidle")
            google_popup.wait_for_timeout(2000)
            email_input = google_popup.locator('input[type="email"]').first
            if email_input.is_visible(timeout=5000):
                email_input.fill(email)
                google_popup.locator("text=Next").first.click()
                google_popup.wait_for_timeout(2000)
                pwd_input = google_popup.locator('input[type="password"]').first
                if pwd_input.is_visible(timeout=5000):
                    pwd_input.fill(password)
                    google_popup.locator("text=Next").first.click()
                    google_popup.wait_for_timeout(3000)
            google_popup.close()
            p.wait_for_timeout(3000)

    def _select_child(self):
        p = self.page
        child_selectors = [
            '[class*="child"]', '[class*="student"]', '[class*="profile"]',
            '[class*="avatar"]', "text=View Profile", "text=Switch Child",
            "text=Switch Student", '[data-testid*="child"]',
        ]
        for sel in child_selectors:
            el = p.locator(sel).first
            if el.is_visible(timeout=2000):
                el.click()
                p.wait_for_timeout(1500)
                break

        p.wait_for_timeout(1000)
        self._save_snapshot("after_child_select")

    def _extract_all_subjects(self):
        p = self.page
        p.wait_for_timeout(2000)

        subject_labels = self._find_subject_folders()
        if not subject_labels:
            self._save_snapshot("no_subjects_found")
            raise RuntimeError("No subject folders found. DOM snapshot saved.")

        for subj in subject_labels:
            if cfg.ALLOWED_SUBJECTS and subj not in cfg.ALLOWED_SUBJECTS:
                continue
            text = self._extract_single_subject(subj)
            if text and len(text.strip()) > 20:
                content_hash = hashlib.sha256(text.encode()).hexdigest()
                filepath = self._save_subject_file(subj, text)
                self.results[subj] = {
                    "filepath": str(filepath),
                    "content_hash": content_hash,
                    "char_count": len(text),
                    "extracted_at": datetime.now().isoformat(),
                }
                print(f"  ✓ {subj}: {len(text)} chars -> {filepath.name}")

        if not self.results:
            self._save_snapshot("extraction_empty")
            print("WARNING: No subjects extracted. DOM snapshots saved for debugging.")

    def _find_subject_folders(self):
        p = self.page
        labels = set()
        known_subjects = [
            "Physics", "Chemistry", "Biology", "Mathematics", "Math",
            "English", "Hindi", "History", "Geography", "Science",
            "Computer", "Social Studies", "Social Science", "SST",
            "Economics", "Accountancy", "Business", "Civics",
            "Political Science", "Art", "Music", "Physical Education",
            "French", "Sanskrit", "Environmental Science", "EVS",
            "General Knowledge", "GK", "Value Education", "Moral Science",
            "Language", "Literature", "Grammar",
        ]
        pattern = "|".join(known_subjects)

        for tag in ["h1", "h2", "h3", "h4", "h5", "h6", "span", "div", "a", "button", "p", "li"]:
            elements = p.locator(tag).all()
            for el in elements:
                try:
                    text = el.text_content()
                    if text and re.search(pattern, text, re.IGNORECASE):
                        labels.add(text.strip())
                except Exception:
                    continue

        links = p.locator("a").all()
        for a in links:
            try:
                text = a.text_content()
                if text and re.search(pattern, text, re.IGNORECASE):
                    labels.add(text.strip())
            except Exception:
                continue

        if cfg.DEBUG:
            all_text = p.locator("body").text_content()
            found = set(re.findall(r'\b(?:' + pattern + r')\b', all_text, re.IGNORECASE))
            print(f"  [DEBUG] Subject keywords found in body: {found}")

        return list(labels)

    def _extract_single_subject(self, subject_label):
        p = self.page
        print(f"  Extracting: {subject_label}")

        link = p.locator(f"text={subject_label}").first
        if link.is_visible(timeout=3000):
            link.click()
        else:
            return self._extract_current_page_text(subject_label)

        p.wait_for_timeout(3000)
        p.wait_for_load_state("networkidle")
        self._save_snapshot(f"subject_{subject_label}")

        text = self._extract_current_page_text(subject_label)
        back_btn = p.locator("text=Back").or_(p.locator('[aria-label="Back"]')).or_(p.locator('[class*="back"]')).first
        if back_btn.is_visible(timeout=2000):
            back_btn.click()
            p.wait_for_timeout(1500)

        return text

    def _extract_current_page_text(self, label=""):
        p = self.page
        text_parts = []
        seen = set()

        content_selectors = [
            "main", "article", '[class*="content"]', '[class*="portfolio"]',
            '[class*="class-flow"]', '[class*="resource"]', '[class*="material"]',
            '[role="main"]', '[class*="note"]', '[class*="description"]',
            '[class*="body"]', '[class*="text"]', "body",
        ]

        combined = p.locator(", ".join(content_selectors)).all()
        for el in combined:
            try:
                text = el.text_content()
                if text and text.strip():
                    cleaned = text.strip()
                    if cleaned not in seen:
                        seen.add(cleaned)
                        text_parts.append(cleaned)
            except Exception:
                continue

        return "\n\n".join(text_parts) if text_parts else ""

    def _save_subject_file(self, subject, text):
        cfg.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", subject.lower()).strip("_")
        date_str = datetime.now().strftime("%Y%m%d")
        filepath = cfg.OUTPUT_DIR / f"{slug}_{date_str}.md"
        header = f"# {subject} Notes\nExtracted: {datetime.now().isoformat()}\n\n---\n\n"
        filepath.write_text(header + text, encoding="utf-8")
        return filepath

    def _save_snapshot(self, name):
        if not cfg.DEBUG:
            return
        snap_dir = cfg.OUTPUT_DIR / "snapshots"
        snap_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%H%M%S")
        try:
            self.page.screenshot(path=str(snap_dir / f"{name}_{ts}.png"))
            with open(snap_dir / f"{name}_{ts}.html", "w") as f:
                f.write(self.page.content())
        except Exception:
            pass


def extract():
    extractor = ToddleExtractor()
    return extractor.run()


if __name__ == "__main__":
    import sys
    cfg.HEADLESS = "--headed" not in sys.argv and "-h" not in sys.argv
    if cfg.HEADLESS:
        print("Running headless. Use --headed to see the browser.")
    else:
        print("Running in visible mode (headed).")
    cfg.DEBUG = True
    results = extract()
    print(f"\nExtracted {len(results)} subjects:")
    for subj, info in results.items():
        print(f"  {subj}: {info['char_count']} chars -> {info['filepath']}")
