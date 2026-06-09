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
import re # Import re for regex parsing of NLM output

# Load env variables from crewai_testing/.env for API keys
def load_crewai_env():
    env_path = Path(__file__).parent.parent / "crewai_testing" / ".env"
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

load_crewai_env()

from crewai import Agent, Task, Crew, LLM

# Configuration
SUBSTACK_CHANNELS_FILE = Path(__file__).parent / "substack_channels.json"
STATE_FILE = Path(__file__).parent / "substack_to_slack_state.json"
OUTPUT_DIR = Path(__file__).parent / "notebooklm_output" / "substack"
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_SUBSTACK") or os.environ.get("SLACK_WEBHOOK_URL")
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
    else: # Always print stderr for debugging, even if returncode is 0
        if result.stderr:
            p(f"NLM command stderr: {result.stderr.strip()}")
    if capture:
        return result.stdout
    return None

def nlm_json(*args):
    """Wrapper for NotebookLM CLI commands returning JSON."""
    output = nlm(*args)
    if output:
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            p(f"Warning: NLM output is not JSON: {output[:200]}...") # Log snippet
            return None # Or raise an error, depending on desired behavior
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

def match_filters(text: str, filters: list[str]) -> bool:
    """Checks if the text contains any of the keywords in the filters (case-insensitive)."""
    if not filters:
        return True  # No filters defined, so all text matches
    text_lower = text.lower()
    for f in filters:
        if f.lower() in text_lower:
            return True
    return False

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

        # Prioritized selectors for NPR
        if not content_source:
            content_source = soup.find('div', class_='storytext')
        if not content_source:
            content_source = soup.find('div', id='storytext')
        # General selectors
        if not content_source:
            content_source = soup.find('article')
        if not content_source:
            content_source = soup.find('main')
        if not content_source:
            content_source = soup.find('div', class_='body prose')

        if not content_source:
            # Fallback for other structures or common article containers
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
    except Exception as e:
        p(f"Error parsing article content from {url}: {e}")
        return None

def process_with_crewai(title, content_text):
    """
    Summarize Substack post content using CrewAI.
    """
    p(f"Processing '{title}' with CrewAI...")
    try:
        # Define LLM using the loaded environment variables
        model_name = os.environ.get("MODEL", "anthropic/claude-3-5-sonnet-20241022")
        llm = LLM(
            model=model_name,
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            verbose=True
        )

        # Define Agent
        summarizer = Agent(
            role="Senior Content Curator",
            goal="Synthesize complex long-form articles into concise, high-impact summaries.",
            backstory="An expert newsletter editor who extracts core arguments, key insights, and actionable takeaways from technical and macro articles.",
            llm=llm,
            verbose=True
        )

        # Define Task
        task_desc = f"""Read the article content and write an engaging, structured summary.
Focus on:
1. Core thesis / Main argument
2. Key insights and data points
3. Three main takeaways/action points

Format the output cleanly in Markdown with bold headers and bullet points.

Article Title: {title}
Article Content:
{content_text}"""

        summarization_task = Task(
            description=task_desc,
            expected_output="Structured Markdown summary with bullet points and bold sections.",
            agent=summarizer
        )

        # Create Crew
        crew = Crew(
            agents=[summarizer],
            tasks=[summarization_task],
            verbose=True
        )

        # Kickoff
        result = crew.kickoff()
        summary = str(result.raw)
        return summary
    except Exception as e:
        p(f"Error during CrewAI processing for '{title}': {e}")
        return None

def send_summary_to_slack(channel_name, post_title, summary, post_url):
    """
    Constructs and sends Slack messages using send_slack.py.
    """
    if not SLACK_WEBHOOK_URL:
        p("Skipping Slack notification: SLACK_WEBHOOK_URL not set.")
        return

    p(f"Sending summary to Slack for '{post_title}' from {channel_name}")
    try:
        send_slack_script = Path(__file__).parent / "send_slack.py"
        
        # Construct the command for send_slack.py using header and text
        cmd = [
            "python3", str(send_slack_script),
            "--webhook", SLACK_WEBHOOK_URL,
            "--username", SLACK_USERNAME,
            "--icon", SLACK_ICON,
            "--color", "info", # Use 'info' color for general summaries
            "--header", f"New Post from {channel_name}: {post_title}",
            "--text", f"{summary}\n\nRead the full article: <{post_url}|{post_title}>"
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
        filters = channel_config.get('filters', []) # Get filters for the channel
        
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

            # Apply filters
            if not match_filters(post_title, filters):
                p(f"  -> Skipping post '{post_title}' due to filters.")
                continue

            p(f"  -> Processing post: '{post_title}' (Published: {post_pubdate})")
            
            article_content = get_article_content(post_link)

            if article_content:
                summary = process_with_crewai(post_title, article_content)
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