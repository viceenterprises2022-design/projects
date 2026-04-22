import feedparser
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import json
from concurrent.futures import ThreadPoolExecutor

# --- config ---
IST = ZoneInfo("Asia/Kolkata")
TODAY = datetime.now(IST).date()

FEEDS = {
    "Yahoo Finance": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=yhoo&region=US&lang=en-US",
    "MarketWatch Top": "http://feeds.marketwatch.com/marketwatch/topstories/",
    "Reuters Business": "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best",
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "Cointelegraph": "https://cointelegraph.com/rss",
    "Decrypt": "https://decrypt.co/feed"
}

def parse_feed(name, url):
    try:
        d = feedparser.parse(url)
        items = []
        for e in d.entries[:25]:
            if hasattr(e, 'published_parsed') and e.published_parsed:
                pub_dt = datetime(*e.published_parsed[:6], tzinfo=timezone.utc).astimezone(IST)
            elif hasattr(e, 'updated_parsed') and e.updated_parsed:
                pub_dt = datetime(*e.updated_parsed[:6], tzinfo=timezone.utc).astimezone(IST)
            else:
                pub_dt = datetime.now(IST)

            if pub_dt.date() != TODAY:
                continue

            items.append({
                "source": name,
                "title": e.title.strip(),
                "link": e.link,
                "published_ist": pub_dt.strftime("%Y-%m-%d %H:%M IST"),
                "summary": getattr(e, 'summary', '')[:200]
            })
        return items
    except Exception as ex:
        print(f"[{name}] error: {ex}")
        return []

def main():
    all_news = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = [ex.submit(parse_feed, n, u) for n, u in FEEDS.items()]
        for f in futures:
            all_news.extend(f.result())

    seen = set()
    unique = []
    for n in sorted(all_news, key=lambda x: x["published_ist"], reverse=True):
        if n["link"] not in seen:
            seen.add(n["link"])
            unique.append(n)

    print(f"\n=== Finance & Crypto News — {TODAY.strftime('%d %b %Y')} ===\n")
    for i, n in enumerate(unique, 1):
        print(f"{i}. [{n['source']}] {n['title']}")
        print(f"   {n['published_ist']} | {n['link']}\n")

    with open("news_today.json", "w", encoding="utf-8") as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(unique)} items to news_today.json")

if __name__ == "__main__":
    main()