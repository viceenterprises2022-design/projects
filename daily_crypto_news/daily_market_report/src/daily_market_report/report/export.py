from __future__ import annotations

from pathlib import Path

from weasyprint import HTML

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


def write_pdf(html: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html, base_url=str(path.parent)).write_pdf(str(path))


def write_png(html: str, path: Path, viewport_width: int = 1100, viewport_height: int = 1600) -> None:
    if sync_playwright is None:
        raise RuntimeError("playwright not available")
    path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": viewport_width, "height": viewport_height})
        page.set_content(html, wait_until="load")
        page.screenshot(path=str(path), full_page=True)
        browser.close()
