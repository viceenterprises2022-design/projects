from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import feedparser
from bs4 import BeautifulSoup

from daily_market_report.models.snapshot import AssetConfig, AssetSnapshot, NewsItem


def strip_html(raw: str, max_len: int = 400) -> str:
    if not raw:
        return ""
    text = BeautifulSoup(raw, "lxml").get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text[:max_len]


def _pub_dt(entry, default_tz: ZoneInfo) -> datetime:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        return dt.astimezone(default_tz)
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        dt = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
        return dt.astimezone(default_tz)
    return datetime.now(default_tz)


def _feed_items(name: str, url: str, asset_tz: ZoneInfo, cutoff_date) -> list[NewsItem]:
    out: list[NewsItem] = []
    try:
        d = feedparser.parse(url)
        for e in getattr(d, "entries", [])[:40]:
            pub = _pub_dt(e, asset_tz)
            if pub.date() < cutoff_date:
                continue
            title = (e.title or "").strip()
            link = getattr(e, "link", "") or ""
            summ = strip_html(getattr(e, "summary", "") or "")
            out.append(
                NewsItem(
                    source=name,
                    title=title,
                    link=link,
                    published_ist=pub.strftime("%Y-%m-%d %H:%M %Z"),
                    summary_plain=summ,
                )
            )
    except Exception:  # noqa: BLE001
        return []
    return out


def keyword_relevant(item: NewsItem, keywords: list[str]) -> bool:
    if not keywords:
        return True
    blob = f"{item.title} {item.summary_plain}".lower()
    return any(k.lower() in blob for k in keywords)


def collect_news_for_asset(asset: AssetConfig, lookback_days: int = 2) -> list[NewsItem]:
    try:
        asset_tz = ZoneInfo(asset.timezone)
    except Exception:  # noqa: BLE001
        asset_tz = ZoneInfo("UTC")
    today = datetime.now(asset_tz).date()
    cutoff = today - timedelta(days=lookback_days - 1)
    acc: list[NewsItem] = []
    feeds = asset.rss_feeds or []
    with ThreadPoolExecutor(max_workers=min(6, max(1, len(feeds)))) as ex:
        futs = []
        for f in feeds:
            name = f.get("name") or "Feed"
            url = f.get("url") or ""
            if not url:
                continue
            futs.append(ex.submit(_feed_items, name, url, asset_tz, cutoff))
        for fut in as_completed(futs):
            acc.extend(fut.result())

    seen: set[str] = set()
    unique: list[NewsItem] = []
    for n in sorted(acc, key=lambda x: x.published_ist, reverse=True):
        if n.link in seen:
            continue
        seen.add(n.link)
        if keyword_relevant(n, asset.news_keywords):
            unique.append(n)
    return unique[:40]


def attach_news(assets: list[AssetConfig], snapshots: list[AssetSnapshot]) -> None:
    by_cfg = {a.id: a for a in assets}
    for snap in snapshots:
        cfg = by_cfg.get(snap.asset_id)
        if not cfg:
            continue
        snap.news_candidates = collect_news_for_asset(cfg)
