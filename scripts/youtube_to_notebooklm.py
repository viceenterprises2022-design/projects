#!/usr/bin/env python3
"""YouTube → NotebookLM synthesis pipeline.

Monitors configured channels for new videos (within 24h),
sends each to NotebookLM, generates a briefing report + mind-map,
and delivers results to Slack.

Config: youtube_channels.json  (list of @handles)
State:  youtube_to_notebooklm_state.json  (auto-managed)

Cron (once daily at 09:00):
  0 9 * * * cd /path/to/scripts && python3 youtube_to_notebooklm.py >> logs/youtube_nlm_cron.log 2>&1
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

# ── YouTube API helpers (adapted from youtube_video_search.py) ──────────
YT_API_KEY = "AIzaSyBTywdvYzEJlu1Q0782hI0iM22zBZIWCcc"


def get_channel_id(api_key, handle):
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {"part": "id", "forHandle": handle, "key": api_key}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("items"):
        raise ValueError(f"No channel found for handle @{handle}")
    return data["items"][0]["id"]


def get_uploads_playlist_id(api_key, channel_id):
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {"part": "contentDetails", "id": channel_id, "key": api_key}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    return data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


def fetch_all_from_playlist(api_key, playlist_id):
    videos = []
    next_page_token = None
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    while True:
        params = {
            "part": "snippet,contentDetails",
            "maxResults": 50,
            "playlistId": playlist_id,
            "key": api_key,
        }
        if next_page_token:
            params["pageToken"] = next_page_token
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        video_ids = [item["contentDetails"]["videoId"] for item in data["items"]]
        stats_params = {
            "part": "statistics,contentDetails,snippet",
            "id": ",".join(video_ids),
            "key": api_key,
        }
        stats_resp = requests.get("https://www.googleapis.com/youtube/v3/videos", params=stats_params)
        stats_resp.raise_for_status()
        stats_data = stats_resp.json()
        stats_lookup = {vid["id"]: vid for vid in stats_data["items"]}
        for item in data["items"]:
            vid = item["contentDetails"]["videoId"]
            snippet = item["snippet"]
            stats = stats_lookup.get(vid, {})
            content = stats.get("contentDetails", {})
            stats_detail = stats.get("statistics", {})
            videos.append({
                "id": vid,
                "title": snippet.get("title", ""),
                "publishedAt": snippet.get("publishedAt", ""),
                "views": int(stats_detail.get("viewCount", 0)),
                "duration": content.get("duration", ""),
                "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                "url": f"https://www.youtube.com/watch?v={vid}",
            })
        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break
    return videos


# ── Config ──────────────────────────────────────────────────────────────
CONFIG_DIR = Path(__file__).parent
CHANNELS_FILE = CONFIG_DIR / "youtube_channels.json"
STATE_FILE = CONFIG_DIR / "youtube_to_notebooklm_state.json"
OUTPUT_BASE = CONFIG_DIR / "notebooklm_output" / "youtube"

SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK_URL")
NLM_CMD = "notebooklm"
MAX_SLACK_CHARS = 3500

# Non-None values only if slack is configured
SLACK_USERNAME = "YouTube \u2192 NotebookLM"
SLACK_ICON = ":movie_camera:"


# ── Helpers ─────────────────────────────────────────────────────────────
def p(msg):
    print(msg, flush=True)


def nlm(*args, capture=True):
    cmd = [NLM_CMD] + [str(a) for a in args]
    p(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=capture, text=True)
    if result.returncode != 0 and capture:
        p(f"  [WARN] exit {result.returncode}: {result.stderr.strip()[:300]}")
    return result


def nlm_json(*args):
    result = nlm(*args, "--json")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def extract_video_id(url: str) -> str:
    m = re.search(r"v=([a-zA-Z0-9_-]+)", url)
    return m.group(1) if m else url


def mindmap_to_text(data, indent=0) -> list[str]:
    prefix = "  " * indent
    lines = []

    if isinstance(data, dict):
        title = data.get("title") or data.get("label") or data.get("name", "")
        if title:
            marker = "•" if indent == 0 else "─"
            lines.append(f"{prefix}{marker} {title}")
        children = data.get("children") or data.get("items") or data.get("nodes") or []
        for i, child in enumerate(children):
            lines.extend(mindmap_to_text(child, indent + 1))
    elif isinstance(data, list):
        for item in data:
            lines.extend(mindmap_to_text(item, indent))
    elif isinstance(data, str):
        lines.append(f"{prefix}  {data}")

    return lines


# ── State Management ────────────────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str, ensure_ascii=False))
    p(f"  State saved \u2192 {STATE_FILE.name}")


# ── Step 1: Load channels ───────────────────────────────────────────────
def load_channels() -> list[str]:
    if not CHANNELS_FILE.exists():
        p(f"ERROR: {CHANNELS_FILE} not found.")
        sys.exit(1)
    return json.loads(CHANNELS_FILE.read_text()).get("channels", [])


# ── Step 2: Fetch new videos (last 24h) ────────────────────────────────
def fetch_new_videos(channels: list[str], state: dict) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    new_videos = []

    for handle in channels:
        p(f"\n  {handle}")
        try:
            chan = handle.lstrip("@")
            channel_id = get_channel_id(YT_API_KEY, chan)
            playlist_id = get_uploads_playlist_id(YT_API_KEY, channel_id)
            all_videos = fetch_all_from_playlist(YT_API_KEY, playlist_id)
        except Exception as e:
            p(f"    FAIL: {e}")
            continue

        known = set(state.get(handle, {}).get("known_ids", []))
        fresh = []
        for v in all_videos:
            pub = v.get("publishedAt", "")
            if not pub:
                continue
            pub_dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            if pub_dt >= cutoff:
                vid = extract_video_id(v["url"])
                if vid not in known and vid not in [f["id"] for f in fresh]:
                    v["id"] = vid
                    v["channel_handle"] = handle
                    fresh.append(v)
            else:
                break

        if fresh:
            p(f"    \u2192 {len(fresh)} new video(s)")
            for v in fresh:
                p(f"      {v['id'][:12]}  {v['title'][:70]}")
        else:
            p("    No new videos in last 24h")

        new_videos.extend(fresh)

    return new_videos


# ── Step 3: Process a single video through NotebookLM \u2192 Slack ─────────
def process_video(video: dict, state: dict):
    title = video["title"]
    channel = video["channel_handle"]
    vid_id = video["id"]
    url = video["url"]
    day = datetime.now().strftime("%Y-%m-%d")

    p(f"\n{'='*55}")
    p(f"  {title}")
    p(f"  {channel}  |  {url}")
    p(f"{'='*55}")

    out_dir = OUTPUT_BASE / day / vid_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Create notebook ─────────────────────────────────────────────
    nb_name = f"YT: {channel.lstrip('@')} \u2014 {title[:60]}"
    p(f"\n[1/7] Creating notebook...")
    data = nlm_json("create", nb_name)
    nb_id = data.get("notebook", {}).get("id", "")
    if not nb_id:
        p("  FAILED. Run 'notebooklm login'.")
        return False
    p(f"  ID: {nb_id}")

    # ── Add YouTube source ──────────────────────────────────────────
    p(f"\n[2/7] Adding YouTube source...")
    data = nlm_json("source", "add", url, "--notebook", nb_id)
    sid = data.get("source", {}).get("id", "")
    if not sid:
        p("  FAILED to add source.")
        return False
    p(f"  Source: {sid[:12]}")

    # ── Wait for processing ─────────────────────────────────────────
    p(f"\n[3/7] Waiting for source processing...")
    nlm("source", "wait", sid, "-n", nb_id, "--timeout", "600", capture=False)
    p("  Ready")

    # ── Generate briefing report ────────────────────────────────────
    p(f"\n[4/7] Generating briefing report (detailed)...")
    data = nlm_json(
        "generate", "report",
        "--format", "briefing-doc",
        "--append",
        "Be extremely detailed and comprehensive. Include every key point, "
        "evidence, example, and actionable insight from the video. "
        "Structure with clear section headings and bullet points.",
        "--notebook", nb_id,
    )
    report_id = data.get("artifact", {}).get("id", "") or data.get("task_id", "")
    if not report_id:
        p("  Could not start report generation — continuing for mind-map.")
    else:
        p(f"  Task: {report_id[:12]}")

    # ── Generate mind-map ───────────────────────────────────────────
    p(f"\n[5/7] Generating mind-map...")
    nlm_json("generate", "mind-map", "--notebook", nb_id)
    p("  Done (sync)")

    # ── Wait + download ─────────────────────────────────────────────
    p(f"\n[6/7] Downloading artifacts...")

    report_path = out_dir / "report.md"
    mm_path = out_dir / "mindmap.json"

    if report_id:
        nlm("artifact", "wait", report_id, "-n", nb_id, "--timeout", "900", capture=False)
        nlm("download", "report", str(report_path), "-a", report_id, "-n", nb_id, capture=False)

    nlm("download", "mind-map", str(mm_path), "--notebook", nb_id, capture=False)

    for path in [report_path, mm_path]:
        if path.exists():
            p(f"  {path.name} ({path.stat().st_size:,} bytes)")
        else:
            p(f"  {path.name} — not available")

    # ── Send to Slack ───────────────────────────────────────────────
    p(f"\n[7/7] Sending to Slack...")
    slack_ok = _send_slack(video, nb_id, report_path, mm_path)
    p(f"  {'OK' if slack_ok else 'FAILED'}")

    # ── Delete notebook (only after Slack confirms OK) ──────────────
    if slack_ok:
        _delete_notebook(nb_id)
    else:
        p("  Slack failed — keeping notebook (will retry next run).")

    # ── Mark processed in state ─────────────────────────────────────
    ch_state = state.setdefault(channel, {"known_ids": []})
    if vid_id not in ch_state["known_ids"]:
        ch_state["known_ids"].append(vid_id)
    save_state(state)

    nb_link = f"https://notebooklm.google.com/notebook/{nb_id}"
    p(f"\n  Done \u2192 {nb_link}")
    return True


def _send_slack(video: dict, nb_id: str, report_path: Path, mm_path: Path) -> bool:
    if not SLACK_WEBHOOK:
        p("  SLACK_WEBHOOK_URL not set, skipping.")
        return False

    title = video["title"]
    channel_handle = video["channel_handle"]
    url = video["url"]
    nb_link = f"https://notebooklm.google.com/notebook/{nb_id}"
    channel_display = channel_handle.lstrip("@")

    fallback = f"\U0001f3ac New video from {channel_handle}"

    from send_slack import send_to_slack

    # ── Message 1: header + summary + mind-map + report ────────────
    blocks: list[dict] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"\U0001f3ac {title}", "emoji": True},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*\U0001f4fa Channel*\n{channel_handle}"},
                {"type": "mrkdwn", "text": f"*\U0001f4d3 NotebookLM*\n<{nb_link}|Open>"},
            ],
        },
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*\U0001f517 Link*\n{url}"}},
        {"type": "divider"},
    ]

    # Mind-map as text tree (cap at 25 lines)
    if mm_path and mm_path.exists():
        mm_data = json.loads(mm_path.read_text())
        tree_lines = mindmap_to_text(mm_data)
        if tree_lines:
            clipped = tree_lines[:25]
            mm_text = "\n".join(clipped)
            if len(tree_lines) > 25:
                mm_text += f"\n… and {len(tree_lines) - 25} more"
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*\U0001f5fa Mind Map*\n```\n{mm_text}\n```"},
            })
            blocks.append({"type": "divider"})

    # Report: include first ~2500 chars in msg 1
    report_chunks: list[str] = []
    if report_path and report_path.exists():
        raw = report_path.read_text().strip()
        if raw:
            MAX_FIRST = 2500
            if len(raw) <= MAX_FIRST:
                report_chunks = [raw]
            else:
                report_chunks = [raw[:MAX_FIRST]]
                remaining = raw[MAX_FIRST:]
                while remaining:
                    report_chunks.append(remaining[:3000])
                    remaining = remaining[3000:]

    if report_chunks:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*\U0001f4cb Briefing Report*\n\n{report_chunks[0]}"},
        })

    ok = True
    res = send_to_slack(
        SLACK_WEBHOOK,
        fallback,
        username=SLACK_USERNAME,
        icon_emoji=SLACK_ICON,
        blocks=blocks,
    )
    if not res.get("ok"):
        ok = False
        p(f"  Slack error (msg 1): {res.get('error')}")

    # ── Messages 2+: report continuation chunks ──────────────────
    for i, chunk in enumerate(report_chunks[1:], start=2):
        cont_blocks: list[dict] = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"\U0001f4cb Report (continued {i - 1}/{len(report_chunks) - 1})", "emoji": True},
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": chunk}},
        ]
        res = send_to_slack(
            SLACK_WEBHOOK,
            f"{fallback} — report continuation {i-1}",
            username=SLACK_USERNAME,
            icon_emoji=SLACK_ICON,
            blocks=cont_blocks,
        )
        if not res.get("ok"):
            ok = False
            p(f"  Slack error (msg {i}): {res.get('error')}")

    return ok


# ── Notebook Deletion (safety-gated) ─────────────────────────────────────
def _delete_notebook(nb_id: str) -> bool:
    """Delete a NotebookLM notebook.

    SAFETY: This is the ONLY function in this file that can delete notebooks.
    - Only proceeds if nb_id matches expected format (UUID-like: 20+ alphanumeric/hyphen chars)
    - Only called after Slack delivery confirms OK (see process_video)
    - Every nb_id passed here was freshly created in the same process_video call
    """
    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{19,}$", nb_id):
        p(f"  SAFETY BLOCKED: notebook ID '{nb_id}' looks invalid, skipping delete.")
        return False

    p(f"  Cleaning up notebook {nb_id[:16]}...")
    result = nlm("delete", "-n", nb_id, capture=True)
    if result.returncode == 0:
        p(f"  Deleted \u2713")
        return True
    p(f"  WARN: could not delete notebook {nb_id} (exit {result.returncode})")
    return False


# ── Channel Management ───────────────────────────────────────────────────
def _add_channel(handle: str):
    data = json.loads(CHANNELS_FILE.read_text())
    existing = [h.lower() for h in data["channels"]]
    h = handle if handle.startswith("@") else f"@{handle}"
    if h.lower() in existing:
        p(f"Already present: {h}")
        return
    data["channels"].append(h)
    data["channels"].sort(key=str.casefold)
    CHANNELS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    p(f"Added: {h}")


def _remove_channel(handle: str):
    data = json.loads(CHANNELS_FILE.read_text())
    h = handle if handle.startswith("@") else f"@{handle}"
    matches = [c for c in data["channels"] if c.lower() == h.lower()]
    if not matches:
        p(f"Not found: {h}")
        return
    for m in matches:
        data["channels"].remove(m)
    CHANNELS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    p(f"Removed: {h}")


def _list_channels():
    data = json.loads(CHANNELS_FILE.read_text())
    p(f"Configured channels ({len(data['channels'])}):")
    for c in data["channels"]:
        p(f"  {c}")


# ── Main ─────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="YouTube → NotebookLM synthesis pipeline",
    )
    group = parser.add_argument_group("channel management")
    group.add_argument("--add-channel", metavar="@handle", help="Add a YouTube channel to monitor")
    group.add_argument("--remove-channel", metavar="@handle", help="Remove a YouTube channel")
    group.add_argument("--list-channels", action="store_true", help="List configured channels")
    args = parser.parse_args()

    if args.add_channel:
        _add_channel(args.add_channel)
        return
    if args.remove_channel:
        _remove_channel(args.remove_channel)
        return
    if args.list_channels:
        _list_channels()
        return

    p("=" * 55)
    p("  YouTube \u2192 NotebookLM Synthesis")
    p(f"  {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    p("=" * 55)

    channels = load_channels()
    p(f"\nChannels ({len(channels)}): {', '.join(channels)}")

    state = load_state()
    p(f"State loaded: {len(state)} channel(s) tracked")

    new_videos = fetch_new_videos(channels, state)
    if not new_videos:
        p("\nNo new videos found. Nothing to do.")
        return

    p(f"\n{'='*55}")
    p(f"Processing {len(new_videos)} new video(s)...")
    p(f"{'='*55}")

    processed = 0
    for v in new_videos:
        if process_video(v, state):
            processed += 1

    p(f"\n{'='*55}")
    p(f"Done. {processed}/{len(new_videos)} videos processed.")
    p(f"{'='*55}")


if __name__ == "__main__":
    main()
