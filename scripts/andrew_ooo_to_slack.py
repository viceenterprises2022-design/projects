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
DEFAULT_FEED_URL = "https://andrew.ooo/rss.xml"
STATE_FILE = Path(__file__).parent / "andrew_ooo_state.json"
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_ANDREW_OOO") or os.environ.get("SLACK_WEBHOOK_URL")

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
    # Fallback to current time if no date is found
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
        
        # Remove scripts, styles, metadata
        for s in soup(["script", "style", "meta", "link", "noscript", "header", "footer", "nav"]):
            s.decompose()
            
        # Target main content area
        content_area = soup.find("article") or soup.find("main") or soup.find("body")
        if not content_area:
            return ""
            
        # Extract text elements
        text_elements = []
        for elem in content_area.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
            text_elements.append(elem.get_text().strip())
            
        # Join elements with newlines
        article_text = "\n".join([t for t in text_elements if t])
        return article_text.strip()
    except Exception as e:
        log(f"Error fetching article text from {url}: {e}")
        return ""

def get_ai_summary(text: str) -> str:
    """Uses the agy CLI to generate a bulleted summary of the text."""
    if not text:
        return ""
    
    # Truncate text to avoid excessively long prompts
    max_char_len = 15000
    if len(text) > max_char_len:
        text = text[:max_char_len] + "..."
        
    prompt = (
        "You are a technical assistant. Summarize the following blog post in 3-5 concise, high-value bullet points "
        "appropriate for a Slack notification. Output ONLY the bullet points. Use standard Slack markdown format (e.g. *bold*, * bullet points). "
        "Do not include intro/outro text.\n\n"
        f"Article Content:\n{text}"
    )
    
    cmd = [
        "/home/vreddy1/.local/bin/agy",
        "--dangerously-skip-permissions",
        "--print",
        prompt
    ]
    
    log("Running agy CLI for summarization...")
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

def build_slack_payload(entry, title: str, link: str, pub_date: datetime, description: str, summary: str = "") -> dict:
    """Builds a beautiful Slack Block Kit message for a post."""
    # Format categories/tags if present safely
    categories = []
    if "tags" in entry:
        for cat in entry.tags:
            if hasattr(cat, "term") and cat.term:
                categories.append(cat.term)
            elif isinstance(cat, dict) and cat.get("term"):
                categories.append(cat["term"])
            elif isinstance(cat, str):
                categories.append(cat)
                
    if not categories and "category" in entry:
        categories = [entry.category]
        
    tags_str = ", ".join(categories) if categories else "None"
    
    # Format date
    pub_date_str = pub_date.strftime("%B %d, %Y")
    
    # Clean up description (limit length, remove html tags if any)
    desc_clean = " ".join(description.split())
    if len(desc_clean) > 300:
        desc_clean = desc_clean[:297] + "..."

    # Block Kit blocks
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "New post from andrew.ooo 📝",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*<{link}|{title}>*"
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
    elif desc_clean:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": desc_clean
            }
        })
        
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"📅 *Published:* {pub_date_str}   |   🏷️ *Tags:* {tags_str}"
            }
        ]
    })
    
    # Use attachments to add sidebar color (info/blue: #3b82f6)
    payload = {
        "text": f"New post: {title} - {link}", # Fallback notification text
        "attachments": [
            {
                "color": "#3b82f6",
                "blocks": blocks
            }
        ]
    }
    return payload

def send_to_slack(webhook_url: str, payload: dict) -> bool:
    try:
        res = requests.post(webhook_url, json=payload, timeout=15)
        res.raise_for_status()
        log("Successfully sent notification to Slack.")
        return True
    except Exception as e:
        log(f"Error sending to Slack: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Monitor andrew.ooo RSS and send new posts to Slack.")
    parser.add_argument("--dry-run", action="store_true", help="Print actions and payloads without sending/updating state.")
    parser.add_argument("--force", action="store_true", help="Ignore state and send the latest post anyway.")
    parser.add_argument("--limit", type=int, default=5, help="Max number of new posts to send at once.")
    parser.add_argument("--webhook", help="Override Slack Webhook URL.")
    
    args = parser.parse_args()
    
    webhook_url = args.webhook or SLACK_WEBHOOK_URL
    if not webhook_url:
        log("Error: Slack Webhook URL not configured. Set SLACK_WEBHOOK_ANDREW_OOO in .env or pass --webhook.")
        sys.exit(1)
        
    log("Fetching feed...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    try:
        response = requests.get(DEFAULT_FEED_URL, headers=headers, timeout=20)
        response.raise_for_status()
        feed = feedparser.parse(response.text)
    except Exception as e:
        log(f"Failed to fetch RSS feed: {e}")
        sys.exit(1)
        
    if not feed.entries:
        log("No entries found in feed.")
        return

    # Sort entries oldest to newest
    entries = []
    for entry in feed.entries:
        pub_dt = parse_pubdate(entry)
        entries.append((pub_dt, entry))
    entries.sort(key=lambda x: x[0])
    
    state = load_state()
    last_processed_str = state.get("last_processed_pubdate")
    
    if last_processed_str:
        try:
            last_processed_dt = datetime.fromisoformat(last_processed_str)
        except Exception:
            last_processed_dt = None
    else:
        last_processed_dt = None

    new_entries = []
    
    if last_processed_dt is None:
        # Initial run: state is empty
        # Initialize state with the latest entry to avoid spamming the channel
        latest_dt, latest_entry = entries[-1]
        log(f"No existing state. Initializing state with the latest post: '{latest_entry.title}' ({latest_dt.isoformat()})")
        
        # To verify the integration, let's send the single latest post
        new_entries.append((latest_dt, latest_entry))
    else:
        for pub_dt, entry in entries:
            if pub_dt > last_processed_dt:
                new_entries.append((pub_dt, entry))

    if args.force and not new_entries:
        # If forced and no new entries, send the latest one anyway
        latest_dt, latest_entry = entries[-1]
        log(f"Forced execution. Adding latest entry: '{latest_entry.title}'")
        new_entries.append((latest_dt, latest_entry))

    if not new_entries:
        log("No new posts found since last check.")
        return

    log(f"Found {len(new_entries)} post(s) to process.")
    
    # Apply limit
    if len(new_entries) > args.limit:
        log(f"Limiting posts sent in this run to the first {args.limit} out of {len(new_entries)} (avoids spam).")
        new_entries = new_entries[:args.limit]

    # Process and send
    success_count = 0
    new_last_processed_dt = last_processed_dt
    
    for pub_dt, entry in new_entries:
        title = entry.get("title", "Untitled Post")
        link = entry.get("link", "")
        description = entry.get("description", "")
        
        log(f"Processing post: '{title}' ({pub_dt.isoformat()})")
        
        # 1. Fetch full article text
        article_text = ""
        if link:
            log(f"Fetching full content for {link}...")
            article_text = get_article_text(link)
            
        # 2. Summarize using agy CLI
        summary = ""
        if article_text:
            summary = get_ai_summary(article_text)
            if summary:
                log("Successfully generated summary.")
            else:
                log("Failed to generate summary, falling back to excerpt.")
        else:
            log("No full content fetched, falling back to excerpt.")
            
        # 3. Build payload with summary
        payload = build_slack_payload(entry, title, link, pub_dt, description, summary=summary)
        
        if args.dry_run:
            log(f"[DRY-RUN] Would send Slack payload for: '{title}'")
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            success = True
        else:
            success = send_to_slack(webhook_url, payload)
            
        if success:
            success_count += 1
            if new_last_processed_dt is None or pub_dt > new_last_processed_dt:
                new_last_processed_dt = pub_dt
        else:
            # Stop if one fails to keep state aligned and retry later
            log("Stopping execution due to Slack sending failure.")
            break

    if not args.dry_run and new_last_processed_dt and new_last_processed_dt != last_processed_dt:
        state["last_processed_pubdate"] = new_last_processed_dt.isoformat()
        save_state(state)
        
    log(f"Completed run. Sent {success_count} post(s).")

if __name__ == "__main__":
    main()
