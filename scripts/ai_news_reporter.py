#!/usr/bin/env python3
import os
from dotenv import load_dotenv
load_dotenv()
import json
import argparse
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import requests
from exa_py import Exa

# Slack settings
NEW_SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_AI_NEWS") or os.getenv("SLACK_WEBHOOK_URL")
EXA_API_KEY = os.environ.get("EXA_API_KEY")

MAX_SLACK_TEXT_CHARS = 3500

# Exa search configs
AGENT_SEARCHES = [
    {"label": "GitHub", "query": "new AI agent framework tool launch release", "include_domains": ["github.com"]},
    {"label": "News", "query": "AI agent product launch release announcement 2025", "category": "news"},
    {"label": "HuggingFace", "query": "AI agent release launch model agent system", "include_domains": ["huggingface.co", "blog.langchain.dev", "openai.com", "anthropic.com"]},
]

EVENT_SEARCHES = [
    {"label": "Events", "query": "upcoming AI online workshop webinar register 2025", "include_domains": ["lu.ma", "eventbrite.com", "meetup.com"]},
    {"label": "Research", "query": "AI agent autonomous LLM agent system paper", "category": "research paper"},
]

def chunk_text(text: str, size: int = MAX_SLACK_TEXT_CHARS) -> list:
    return [text[i : i + size] for i in range(0, len(text), size)] or [""]

def send_to_slack(webhook_url: str, text: str) -> bool:
    payload = {"text": text}
    try:
        response = requests.post(webhook_url, json=payload, timeout=15)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error sending to Slack: {e}")
        return False

def run_search(exa: Exa, cfg: dict, since: str) -> list:
    kwargs = dict(
        type="auto",
        num_results=5,
        start_published_date=since,
    )
    if cfg.get("include_domains"):
        kwargs["include_domains"] = cfg["include_domains"]
    if cfg.get("category"):
        kwargs["category"] = cfg["category"]

    try:
        resp = exa.search(cfg["query"], **kwargs)
        return [{
            "source": cfg["label"],
            "title": (r.title or "").strip() or "(no title)",
            "url": r.url
        } for r in resp.results]
    except Exception as e:
        print(f"Error searching {cfg['label']}: {e}")
        return []

def load_events_from_json(path: str = "/home/vreddy1/Desktop/Projects/scripts/ai_events_results.json") -> list:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return []

def fetch_ai_news() -> str:
    exa = Exa(api_key=EXA_API_KEY)
    now = datetime.now(timezone.utc)
    since = (now - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    report = [f"📅 *AI News & Events Report - {now.strftime('%Y-%m-%d')}*"]
    
    # 1. Agents Search (Fresh from Exa)
    report.append("\n🚀 *Latest AI Agent Launches (Last 24h)*")
    agent_found = False
    for cfg in AGENT_SEARCHES:
        results = run_search(exa, cfg, since)
        if results:
            agent_found = True
            for r in results[:3]:
                report.append(f"• *{r['title']}* ({r['source']})\n  {r['url']}")
    
    if not agent_found:
        report.append("• No new agent launches detected in last 24h.")
            
    # 2. Events (From JSON file primarily)
    report.append("\n📅 *Upcoming AI Online Events & Classes*")
    json_events = load_events_from_json()
    
    if json_events:
        print(f"Loading {len(json_events)} events from JSON...")
        for i, r in enumerate(json_events, 1):
            date_str = r.get("published_date", "")[:10] if r.get("published_date") else "Upcoming"
            report.append(f"{i}. *{r['title']}* ({date_str})\n   {r['url']}")
    else:
        # Fallback to fresh search if JSON missing
        print("JSON file not found, falling back to fresh search...")
        for cfg in EVENT_SEARCHES:
            results = run_search(exa, cfg, since)
            if results:
                for r in results[:3]:
                    report.append(f"• *{r['title']}* ({r['source']})\n  {r['url']}")
            else:
                report.append(f"• No new results for {cfg['label']}")
            
    return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description="Fetch daily AI news and send to Slack.")
    parser.add_argument("--webhook", default=NEW_SLACK_WEBHOOK_URL, help="Slack webhook URL")
    parser.add_argument("--dry-run", action="store_true", help="Print the report without sending to Slack")
    args = parser.parse_args()
    
    print("Fetching AI news...")
    report_text = fetch_ai_news()
    
    if args.dry_run:
        print("\n--- REPORT PREVIEW ---")
        print(report_text)
        print("----------------------")
        return
        
    chunks = chunk_text(report_text)
    for i, chunk in enumerate(chunks, 1):
        if send_to_slack(args.webhook, chunk):
            print(f"Part {i}/{len(chunks)} sent to Slack.")
        else:
            print(f"Failed to send Part {i}/{len(chunks)} to Slack.")

if __name__ == "__main__":
    main()
