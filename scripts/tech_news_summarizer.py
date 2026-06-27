#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
import bs4
import feedparser
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
FEEDS = {
    "Anthropic": "https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/main/feeds/anthropic-news.xml",
    "OpenAI": "https://openai.com/news/rss.xml",
    "Latent Space": "https://www.latent.space/feed",
    "Ahead of AI": "https://magazine.sebastianraschka.com/feed",
    "The Pragmatic Engineer": "https://newsletter.pragmaticengineer.com/feed"
}

STATE_FILE = Path(__file__).parent / "tech_news_state.json"
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_TECH_NEWS") or os.environ.get("SLACK_WEBHOOK_URL")

def log(msg: str):
    print(f"[{datetime.now(timezone.utc).isoformat()}] {msg}")

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            log(f"Error loading state file: {e}")
    return {}

def save_state(state: dict):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=4)
        log("State saved successfully.")
    except Exception as e:
        log(f"Error saving state: {e}")

def parse_pubdate(entry) -> datetime:
    """Extracts publication date from a feed entry and returns a timezone-aware datetime."""
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
    return datetime.now(timezone.utc)

def get_article_text(url: str) -> str:
    """Fetches article HTML and extracts body text for summarization."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    try:
        response = requests.get(url, headers=headers, timeout=25)
        response.raise_for_status()
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        
        # Remove scripts, styles, metadata, headers, footers
        for s in soup(["script", "style", "meta", "link", "noscript", "header", "footer", "nav"]):
            s.decompose()
            
        content_area = soup.find("article") or soup.find("main") or soup.find("body")
        if not content_area:
            return ""
            
        # Extract text elements
        text_elements = []
        for elem in content_area.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
            text_elements.append(elem.get_text().strip())
            
        article_text = "\n".join([t for t in text_elements if t])
        return article_text.strip()
    except Exception as e:
        log(f"Error fetching article text from {url}: {e}")
        return ""

def get_ai_summary(title: str, text: str) -> str:
    """Uses the agy CLI to generate a bulleted summary of the text."""
    if not text:
        return ""
    
    # Truncate text to avoid excessively long prompts
    max_char_len = 15000
    if len(text) > max_char_len:
        text = text[:max_char_len] + "..."
        
    prompt = (
        f"You are a technical assistant. Summarize the following article in 3-5 concise, high-value bullet points "
        f"appropriate for a Slack notification. Output ONLY the bullet points. Use standard Slack markdown format (e.g. *bold*, * bullet points). "
        f"Do not include intro/outro text.\n\n"
        f"Article Title: {title}\n"
        f"Article Content:\n{text}"
    )
    
    cmd = [
        "/home/vreddy1/.local/bin/agy",
        "--dangerously-skip-permissions",
        "--print",
        prompt
    ]
    
    log(f"Running agy CLI for summarizing '{title}'...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90, check=True)
        summary = result.stdout.strip()
        if not summary:
            log(f"Warning: agy returned empty output. Stderr: {result.stderr}")
        return summary
    except subprocess.TimeoutExpired:
        log("Error: agy execution timed out.")
        return ""
    except Exception as e:
        log(f"Error running agy CLI: {e}")
        return ""

def send_to_slack(webhook_url: str, url: str, title: str, summary: str, feed_name: str) -> bool:
    # Set fallback tags based on source
    tags = f"{feed_name}, Tech Insights"
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Technical Insight 📝",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*<{url}|{title}>*"
            }
        }
    ]
    
    if summary:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": summary
            }
        })
        
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"🏷️ *Source:* {feed_name}   |   🏷️ *Tags:* {tags}"
            }
        ]
    })
    
    payload = {
        "text": f"New article from {feed_name}: {title} - {url}",
        "attachments": [
            {
                "color": "#36a64f",
                "blocks": blocks
            }
        ]
    }
    
    try:
        res = requests.post(webhook_url, json=payload, timeout=15)
        res.raise_for_status()
        log(f"Successfully sent notification for '{title}' to Slack.")
        return True
    except Exception as e:
        log(f"Error sending to Slack: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Monitor tech blogs RSS and send new summaries to Slack.")
    parser.add_argument("--dry-run", action="store_true", help="Print actions and payloads without sending/updating state.")
    parser.add_argument("--force", action="store_true", help="Ignore state and send the latest post from each feed anyway.")
    parser.add_argument("--limit", type=int, default=3, help="Max number of new posts to send per feed in this run.")
    parser.add_argument("--webhook", help="Override Slack Webhook URL.")
    
    args = parser.parse_args()
    
    webhook_url = args.webhook or SLACK_WEBHOOK_URL
    if not webhook_url:
        log("Error: Slack Webhook URL not configured. Set SLACK_WEBHOOK_TECH_NEWS in .env or pass --webhook.")
        sys.exit(1)
        
    state = load_state()
    last_processed_dates = state.setdefault("last_processed_dates", {})
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    
    for feed_name, feed_url in FEEDS.items():
        log(f"Processing feed '{feed_name}': {feed_url}...")
        try:
            response = requests.get(feed_url, headers=headers, timeout=25)
            response.raise_for_status()
            feed = feedparser.parse(response.text)
        except Exception as e:
            log(f"Failed to fetch feed '{feed_name}': {e}")
            continue
            
        if not feed.entries:
            log(f"No entries found in feed '{feed_name}'.")
            continue

        # Sort entries oldest to newest
        entries = []
        for entry in feed.entries:
            pub_dt = parse_pubdate(entry)
            entries.append((pub_dt, entry))
        entries.sort(key=lambda x: x[0])
        
        # Filter entries to only keep posts from the last 5 days
        now = datetime.now(timezone.utc)
        recent_entries = []
        for pub_dt, entry in entries:
            diff = now - pub_dt
            if diff.days <= 5:
                recent_entries.append((pub_dt, entry))
        
        last_processed_str = last_processed_dates.get(feed_name)
        if last_processed_str:
            try:
                last_processed_dt = datetime.fromisoformat(last_processed_str)
            except Exception:
                last_processed_dt = None
        else:
            last_processed_dt = None
            
        new_entries = []
        if last_processed_dt is None:
            if recent_entries:
                latest_dt, latest_entry = recent_entries[-1]
                log(f"No existing state for '{feed_name}'. Initializing with latest recent post: '{latest_entry.title}' ({latest_dt.isoformat()})")
                new_entries.append((latest_dt, latest_entry))
            else:
                log(f"No existing state and no recent posts (<= 5 days) found for '{feed_name}'. Initializing state to current time.")
                last_processed_dates[feed_name] = now.isoformat()
                save_state(state)
        else:
            for pub_dt, entry in recent_entries:
                if pub_dt > last_processed_dt:
                    new_entries.append((pub_dt, entry))
                    
        if args.force and not new_entries:
            if recent_entries:
                latest_dt, latest_entry = recent_entries[-1]
                log(f"Forced run for '{feed_name}'. Adding latest recent post: '{latest_entry.title}'")
                new_entries.append((latest_dt, latest_entry))
            elif entries:
                latest_dt, latest_entry = entries[-1]
                log(f"Forced run for '{feed_name}' but no recent posts found. Adding latest post anyway: '{latest_entry.title}'")
                new_entries.append((latest_dt, latest_entry))
            
        if not new_entries:
            log(f"No new posts found for '{feed_name}' since last check.")
            continue
            
        log(f"Found {len(new_entries)} new post(s) for '{feed_name}'.")
        if len(new_entries) > args.limit:
            log(f"Limiting to first {args.limit} new post(s).")
            new_entries = new_entries[:args.limit]
            
        new_last_processed_dt = last_processed_dt
        for pub_dt, entry in new_entries:
            title = entry.get("title", "Untitled Post")
            link = entry.get("link", "")
            
            # Clean title suffix
            if " — Anthropic" in title:
                title = title.replace(" — Anthropic", "")
            if " — andrew.ooo" in title:
                title = title.replace(" — andrew.ooo", "")
                
            log(f"Processing entry: '{title}' ({pub_dt.isoformat()})")
            
            # 1. Fetch text content
            text = ""
            if link:
                text = get_article_text(link)
            if not text:
                text = entry.get("description") or entry.get("summary") or ""
                if text:
                    try:
                        text = bs4.BeautifulSoup(text, "html.parser").get_text()
                    except Exception:
                        pass
                
            # 2. Get AI summary
            summary = ""
            if text:
                summary = get_ai_summary(title, text)
                
            # 3. Send to Slack
            if args.dry_run:
                log(f"[DRY-RUN] Would send Slack block for '{title}'")
                print(summary)
                success = True
            else:
                success = send_to_slack(webhook_url, link, title, summary, feed_name)
                
            if success:
                if new_last_processed_dt is None or pub_dt > new_last_processed_dt:
                    new_last_processed_dt = pub_dt
            else:
                log(f"Failed to process '{title}'. Stopping this feed's run.")
                break
                
        if not args.dry_run and new_last_processed_dt and new_last_processed_dt != last_processed_dt:
            last_processed_dates[feed_name] = new_last_processed_dt.isoformat()
            save_state(state)
            
    log("Feed monitoring completed.")

if __name__ == "__main__":
    main()
