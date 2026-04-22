from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup

from daily_market_report.models.snapshot import QuotePayload

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _finite(x: float | None) -> bool:
    return x is not None and not math.isnan(x) and not math.isinf(x)


def _parse_money(text: str) -> float | None:
    if not text:
        return None
    t = re.sub(r"[^\d,.\-]", "", text.replace(",", ""))
    try:
        v = float(t)
        return v if _finite(v) else None
    except ValueError:
        return None


def fetch_google_finance(quote_path: str) -> QuotePayload:
    q = QuotePayload(source="google_finance", session_label="Google Finance")
    url = f"https://www.google.com/finance/quote/{quote_path}"
    try:
        r = httpx.get(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}, timeout=25.0)
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, "lxml")

        # Primary price: common Google Finance class
        price_el = soup.select_one(".YMlKec.fxKbKc") or soup.select_one(".YMlKec")
        if price_el:
            q.last = _parse_money(price_el.get_text(" ", strip=True))

        # Percent change chip
        chp = soup.select_one(".JwB6zf") or soup.select_one("[class*='VORqKc']")
        if chp:
            pct_text = chp.get_text(" ", strip=True)
            m = re.search(r"([+\-]?\d+[.,]?\d*)\s*%", pct_text)
            if m:
                q.change_pct = float(m.group(1).replace(",", "."))

        # Fallback: ld+json
        if q.last is None:
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string or "")
                except json.JSONDecodeError:
                    continue
                items = data if isinstance(data, list) else [data]
                for it in items:
                    if not isinstance(it, dict):
                        continue
                    offers = it.get("offers")
                    if isinstance(offers, dict) and "price" in offers:
                        q.last = _parse_money(str(offers["price"]))
                        break
                if q.last is not None:
                    break

        if q.last is None:
            q.raw_error = "parse_failed"

        q.as_of_utc = datetime.now(timezone.utc)
    except Exception as ex:  # noqa: BLE001
        q.raw_error = str(ex)
    return q
