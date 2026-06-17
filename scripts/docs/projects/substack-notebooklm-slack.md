---
type: Pipeline
title: Substack to NotebookLM & Slack Pipeline
description: Monitors Substack RSS feeds, filters articles by keywords, summarizes using NotebookLM, and pushes alerts to Slack.
tags: [rss, substack, notebooklm, pipeline]
timestamp: 2026-06-17T23:30:00Z
---

# ✉️ Substack → NotebookLM → Slack

> Section group: **🚀 Script Index**

*Monitors subscribed Substack RSS feeds, filters articles by keywords, summarizes each via NotebookLM, and delivers briefings to Slack.*

| Script | Description |
|:--- |:--- |
| `substack_to_slack.py` | **Pipeline**. Checks configured Substack RSS feeds for new posts, applies keyword filters to article titles, uploads the full article content to a standalone NotebookLM notebook, generates a `briefing-doc` report, downloads the report, extracts a summary, and sends a structured Slack message. Safely deletes the notebook after successful processing. |
| `substack_channels.json` | **Config**. JSON object mapping channel names to their `feed_url` and an optional `filters` array (list of keywords for case-insensitive matching). |
| `substack_to_slack_state.json` | **State**. Tracks `last_processed_pubdate` for each channel to prevent reprocessing. |

**Configuration (`substack_channels.json` example):**
```json
{
    "my_filtered_substack": {
        "feed_url": "https://<publication-name>.substack.com/feed",
        "display_name": "My Filtered Substack",
        "filters": ["AI", "Crypto", "Economy", "Trump"] // Optional: articles must contain any of these keywords
    },
    "another_substack_all_posts": {
        "feed_url": "https://<another-publication>.substack.com/feed",
        "display_name": "Another Substack (All Posts)"
        // No "filters" key means all posts are processed
    }
}
```

**Usage:**
```bash
# Initialize the state file (resets last processed dates)
python3 substack_to_slack.py --init-state

# Run the processing pipeline
python3 substack_to_slack.py
```

**Cron (example - daily at 9:00 AM IST):**
```
0 9 * * * cd /home/vreddy1/Desktop/Projects/scripts && python3 substack_to_slack.py >> logs/substack_nlm_cron.log 2>&1
```

---
