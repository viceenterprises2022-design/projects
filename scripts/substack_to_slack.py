import feedparser
import requests
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import argparse
from bs4 import BeautifulSoup
import time
import subprocess

# Configuration
SUBSTACK_CHANNELS_FILE = Path(__file__).parent / "substack_channels.json"
STATE_FILE = Path(__file__).parent / "substack_to_slack_state.json"
OUTPUT_DIR = Path(__file__).parent / "notebooklm_output" / "substack"
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
NLM_CMD = "/home/vreddy1/.local/bin/notebooklm" # Consistent with youtube_to_notebooklm.py
SLACK_USERNAME = "Substack Summaries"
SLACK_ICON = ":notebook:"

def p(msg):
    """Simple print helper."""
    print(f"[{datetime.now().isoformat()}] {msg}")

def nlm(*args, capture=True):
    """Wrapper for NotebookLM CLI commands."""
    cmd = [NLM_CMD] + list(args)
    p(f"Executing NLM command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        p(f"NLM command failed: {result.stderr}")
        raise RuntimeError(f"NLM command failed: {result.stderr}")
    if capture:
        return result.stdout
    return None

def nlm_json(*args):
    """Wrapper for NotebookLM CLI commands returning JSON."""
    output = nlm(*args)
    if output:
        return json.loads(output)
    return None

def load_channels():
    """Loads channels from substack_channels.json."""
    if not SUBSTACK_CHANNELS_FILE.exists():
        p(f"Error: {SUBSTACK_CHANNELS_FILE} not found. Please create it.")
        return {}
    with open(SUBSTACK_CHANNELS_FILE, 'r') as f:
        return json.load(f)

def load_state():
    """Loads state from substack_to_slack_state.json."""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            # Convert ISO strings back to datetime objects
            for channel_url, data in state.items():
                if 'last_processed_pubdate' in data and data['last_processed_pubdate'] is not None:
                    state[channel_url]['last_processed_pubdate'] = datetime.fromisoformat(data['last_processed_pubdate'])
            return state
    return {}

def save_state(state):
    """Saves state to substack_to_slack_state.json."""
    # Convert datetime objects to ISO strings for JSON serialization
    serializable_state = {}
    for channel_url, data in state.items():
        serializable_state[channel_url] = data.copy()
        if 'last_processed_pubdate' in data and data['last_processed_pubdate'] is not None:
            serializable_state[channel_url]['last_processed_pubdate'] = data['last_processed_pubdate'].isoformat()
    
    with open(STATE_FILE, 'w') as f:
        json.dump(serializable_state, f, indent=4)

def fetch_new_posts(channel_url, last_pubdate):
    """Fetches new RSS entries and converts pubdate to datetime objects."""
    p(f"Fetching RSS feed for {channel_url}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'} # Mimic a browser
    feed = feedparser.parse(channel_url, request_headers=headers)
    new_posts = []
    for entry in feed.entries:
        try:
            # Parse publication date. feedparser usually provides a parsed_struct
            if hasattr(entry, 'published_parsed'):
                pub_dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, 'updated_parsed'): # Fallback to updated if published is missing
                pub_dt = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            else:
                p(f"Warning: Could not find publication date for entry '{entry.title}'. Skipping.")
                continue

            if last_pubdate is None or pub_dt > last_pubdate:
                new_posts.append({
                    'title': entry.title,
                    'link': entry.link,
                    'published': pub_dt
                })
        except Exception as e:
            p(f"Error processing entry '{entry.title}': {e}")
            continue
    
    # Sort posts by publication date in ascending order so oldest are processed first
    new_posts.sort(key=lambda x: x['published'])
    return new_posts

def get_article_content(url):
    """Fetches and cleans article content from a URL."""
    p(f"Fetching article content from: {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        content_source = None

        # Prioritized selectors
        if not content_source:
            content_source = soup.find('div', {'data-component': 'ArticleBody'})
        if not content_source:
            content_source = soup.find('div', class_='duet--article--body-page')
        if not content_source:
            content_source = soup.find('article')
        if not content_source:
            content_source = soup.find('main')
        if not content_source:
            content_source = soup.find('div', class_='body prose')

        if not content_source:
            # Fallback for Substack specific structure or common article containers
            content_source = soup.find('div', class_='available-content') or \
                             soup.find('div', class_='markup') or \
                             soup.find('div', class_=lambda x: x and ('post-content' in x or 'entry-content' in x))

        if not content_source:
            p(f"Warning: Could not find a specific primary content area for {url}. Extracting all paragraph text from body.")
            content_source = soup
        
        # Remove script, style, and other unwanted elements from the content source
        for script_or_style in content_source(['script', 'style', 'noscript', 'aside', 'footer', 'nav', '.caption']):
            script_or_style.decompose()

        # Get text and clean up
        content_text = content_source.get_text(separator='\n', strip=True)
        
        # Further cleanup: remove multiple newlines, excessive whitespace
        content_text = os.linesep.join([s for s in content_text.splitlines() if s.strip()])

        return content_text.strip()

    except requests.exceptions.RequestException as e:
        p(f"Error fetching article content from {url}: {e}")
        return None
def process_with_notebooklm(title, content_text):
    """
    Creates a NotebookLM notebook, uploads content, generates a briefing report,
    downloads it, extracts summary, and cleans up.
    """
    p(f"Processing '{title}' with NotebookLM...")
    notebook_id = None
    temp_file_path = None
    try:
        # 1. Create a temporary text file with content_text
        temp_file_name = f"substack_{int(time.time())}.txt"
        temp_file_path = Path(OUTPUT_DIR) / temp_file_name
        temp_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_file_path, 'w') as f:
            f.write(content_text)
        p(f"Created temporary content file: {temp_file_path}")

        # 2. Create a new NotebookLM notebook
        notebook_id = nlm("create", title).strip()
        p(f"Created NotebookLM notebook: {title} (ID: {notebook_id})")

        # 3. Add the temporary file as a source
        source_id = nlm("source", "add", "--notebook", notebook_id, "--file", str(temp_file_path)).strip()
        p(f"Added source '{temp_file_name}' (ID: {source_id}) to notebook {notebook_id}")

        # 4. Wait for NotebookLM source processing to complete
        nlm("source", "wait", source_id)
        p(f"NotebookLM source processing completed for {source_id}")

        # 5. Generate a "briefing-report" artifact
        artifact_id = nlm("artifact", "generate", "report", "--notebook", notebook_id).strip()
        p(f"Generating briefing report artifact (ID: {artifact_id})...")

        # Wait for artifact generation to complete
        nlm("artifact", "wait", artifact_id)
        p(f"Briefing report artifact generation completed for {artifact_id}")

        # 6. Download the briefing report artifact
        report_output_path = Path(OUTPUT_DIR) / f"briefing_report_{artifact_id}.md"
        nlm("artifact", "download", artifact_id, "--output", str(report_output_path))
        p(f"Downloaded briefing report to {report_output_path}")

        # 7. Parse the downloaded report to extract the summary
        summary = "Summary not found."
        if report_output_path.exists():
            with open(report_output_path, 'r') as f:
                report_content = f.read()
                # Assuming the summary is in the first section or clearly marked
                # This might need refinement based on actual NLM briefing report format
                summary_start = report_content.find("## Briefing Report")
                if summary_start != -1:
                    summary_content = report_content[summary_start + len("## Briefing Report"):].strip()
                    first_section_end = summary_content.find("\n## ") # Find next section header
                    if first_section_end != -1:
                        summary = summary_content[:first_section_end].strip()
                    else:
                        summary = summary_content.strip()
                elif report_content.strip():
                    summary = report_content.strip() # Fallback if specific header not found
        else:
            p(f"Warning: Briefing report not found at {report_output_path}")

        return summary

    except Exception as e:
        p(f"Error during NotebookLM processing for '{title}': {e}")
        return None
    finally:
        # 8. Clean up temporary files and NotebookLM notebook
        if temp_file_path and temp_file_path.exists():
            os.remove(temp_file_path)
            p(f"Deleted temporary file: {temp_file_path}")
        if notebook_id:
            try:
                nlm("delete", notebook_id)
                p(f"Deleted NotebookLM notebook: {notebook_id}")
            except Exception as e:
                p(f"Error deleting NotebookLM notebook {notebook_id}: {e}")

def process_with_notebooklm(title, content_text):
    """
    Creates a NotebookLM notebook, uploads content, generates a briefing report,
    downloads it, extracts summary, and cleans up.
    """
    p(f"Processing '{title}' with NotebookLM...")
    notebook_id = None
    temp_file_path = None
    try:
        # 1. Create a temporary text file with content_text
        temp_file_name = f"substack_{int(time.time())}.txt"
        temp_file_path = Path(OUTPUT_DIR) / temp_file_name
        temp_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_file_path, 'w') as f:
            f.write(content_text)
        p(f"Created temporary content file: {temp_file_path}")

        # 2. Create a new NotebookLM notebook
        notebook_info = nlm_json("notebooks", "new", "--title", title)
        notebook_id = notebook_info['id']
        p(f"Created NotebookLM notebook: {title} (ID: {notebook_id})")

        # 3. Add the temporary file as a source
        source_info = nlm_json("sources", "add", "--notebook", notebook_id, "--file", str(temp_file_path))
        source_id = source_info['id']
        p(f"Added source '{temp_file_name}' (ID: {source_id}) to notebook {notebook_id}")

        # 4. Wait for NotebookLM source processing to complete
        nlm("sources", "wait", source_id)
        p(f"NotebookLM source processing completed for {source_id}")

        # 5. Generate a "briefing-report" artifact
        artifact_info = nlm_json("artifacts", "create", "--notebook", notebook_id, "--type", "briefing-report")
        artifact_id = artifact_info['id']
        p(f"Generating briefing report artifact (ID: {artifact_id})...")

        # Wait for artifact generation to complete
        nlm("artifacts", "wait", artifact_id)
        p(f"Briefing report artifact generation completed for {artifact_id}")

        # 6. Download the briefing report artifact
        report_output_path = Path(OUTPUT_DIR) / f"briefing_report_{artifact_id}.md"
        nlm("artifacts", "download", artifact_id, "--output", str(report_output_path))
        p(f"Downloaded briefing report to {report_output_path}")

        # 7. Parse the downloaded report to extract the summary
        summary = "Summary not found."
        if report_output_path.exists():
            with open(report_output_path, 'r') as f:
                report_content = f.read()
                # Assuming the summary is in the first section or clearly marked
                # This might need refinement based on actual NLM briefing report format
                summary_start = report_content.find("## Briefing Report")
                if summary_start != -1:
                    summary_content = report_content[summary_start + len("## Briefing Report"):].strip()
                    first_section_end = summary_content.find("\n## ") # Find next section header
                    if first_section_end != -1:
                        summary = summary_content[:first_section_end].strip()
                    else:
                        summary = summary_content.strip()
                elif report_content.strip():
                    summary = report_content.strip() # Fallback if specific header not found
        else:
            p(f"Warning: Briefing report not found at {report_output_path}")

        return summary

    except Exception as e:
        p(f"Error during NotebookLM processing for '{title}': {e}")
        return None
    finally:
        # 8. Clean up temporary files and NotebookLM notebook
        if temp_file_path and temp_file_path.exists():
            os.remove(temp_file_path)
            p(f"Deleted temporary file: {temp_file_path}")
        if notebook_id:
            try:
                nlm("notebooks", "delete", notebook_id)
                p(f"Deleted NotebookLM notebook: {notebook_id}")
            except Exception as e:
                p(f"Error deleting NotebookLM notebook {notebook_id}: {e}")

def send_summary_to_slack(channel_name, post_title, summary, post_url):
    """
    Constructs and sends Slack Block Kit messages using send_slack.py.
    """
    if not SLACK_WEBHOOK_URL:
        p("Skipping Slack notification: SLACK_WEBHOOK_URL not set.")
        return

    p(f"Sending summary to Slack for '{post_title}' from {channel_name}")
    try:
        # Use subprocess to call send_slack.py
        # Need to ensure send_slack.py is importable or callable as a script
        # For now, let's assume it's in the same directory and callable
        send_slack_script = Path(__file__).parent / "send_slack.py"
        
        # Prepare blocks for Slack message
        blocks = []

        # Header section with channel name and post title
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"New Post from {channel_name}: {post_title}",
                "emoji": True
            }
        })
        blocks.append({"type": "divider"})

        # Summary section
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": summary
            }
        })

        # Link to original post
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"<{post_url}|Read the full article>"
                }
            ]
        })
        blocks.append({"type": "divider"})

        # Construct the command for send_slack.py
        cmd = [
            "python3", str(send_slack_script),
            "--webhook", SLACK_WEBHOOK_URL,
            "--username", SLACK_USERNAME,
            "--icon", SLACK_ICON,
            "--color", "info", # Can be 'good', 'warning', 'danger', 'info'
            "--blocks", json.dumps(blocks)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            p(f"send_slack.py failed: {result.stderr}")
            raise RuntimeError(f"send_slack.py failed: {result.stderr}")
        else:
            p(f"Slack message sent successfully: {result.stdout.strip()}")

    except Exception as e:
        p(f"Error sending Slack message for '{post_title}': {e}")


def main():
    parser = argparse.ArgumentParser(description="Summarize Substack posts and send to Slack via NotebookLM.")
    parser.add_argument("--init-state", action="store_true", help="Initialize state file without processing posts.")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    channels = load_channels()
    if not channels:
        p("No channels configured. Exiting.")
        return

    state = load_state()

    if args.init_state:
        p("Initializing state file...")
        for channel_name, channel_config in channels.items():
            channel_url = channel_config['feed_url']
            state[channel_url] = {"last_processed_pubdate": None, "channel_name": channel_name}
        save_state(state)
        p("State file initialized. Please run the script again without --init-state to process posts.")
        return

    p("Starting Substack summarization and Slack integration...")

    for channel_name, channel_config in channels.items():
        feed_url = channel_config['feed_url']
        display_name = channel_config.get('display_name', channel_name)
        
        # Initialize state for this channel if not present
        if feed_url not in state:
            state[feed_url] = {"last_processed_pubdate": None, "channel_name": display_name}
        
        last_processed_pubdate = state[feed_url]['last_processed_pubdate']
        p(f"Processing channel: {display_name} (Feed: {feed_url}). Last processed: {last_processed_pubdate}")

        new_posts = fetch_new_posts(feed_url, last_processed_pubdate)

        if not new_posts:
            p(f"No new posts found for {display_name}.")
            continue

        p(f"Found {len(new_posts)} new posts for {display_name}. Processing...")

        for post in new_posts:
            post_title = post['title']
            post_link = post['link']
            post_pubdate = post['published']

            p(f"  -> Processing post: '{post_title}' (Published: {post_pubdate})")
            
            article_content = get_article_content(post_link)

            if article_content:
                summary = process_with_notebooklm(post_title, article_content)
                if summary:
                    send_summary_to_slack(display_name, post_title, summary, post_link)
                else:
                    p(f"Warning: Could not generate summary for '{post_title}'. Skipping Slack notification.")
            else:
                p(f"Warning: Could not retrieve article content for '{post_title}'. Skipping NotebookLM and Slack notification.")
            
            # Update last processed date after successful attempt, even if summary/slack failed for this specific post
            # This prevents reprocessing failed posts on next run and moving forward with newer posts
            state[feed_url]['last_processed_pubdate'] = post_pubdate
            save_state(state) # Save state after each post to be robust against crashes

        p(f"Finished processing {len(new_posts)} posts for {display_name}. Updated last_processed_pubdate to {state[feed_url]['last_processed_pubdate']}.")

    p("Substack summarization and Slack integration complete.")

if __name__ == "__main__":
    main()
