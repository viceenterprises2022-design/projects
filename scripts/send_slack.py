#!/usr/bin/env python3
"""Send structured Slack messages via Incoming Webhook using Block Kit.

CLI examples:
  send_slack.py --text "Hello world"
  send_slack.py --header "Deploy Complete" --field "Status: OK" --color good
  send_slack.py --file log.txt --color danger --header "Crash Report"
  echo "alert" | send_slack.py --color warning

Python import:
  from send_slack import send_to_slack, build_header, build_fields, compose_blocks
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

import requests
from dotenv import load_dotenv
load_dotenv()


MAX_SLACK_TEXT_CHARS = 3500
MAX_BLOCK_TEXT_CHARS = 2900

COLOR_MAP: dict[str, str] = {
    "good": "#36a64f", "success": "#36a64f", "green": "#36a64f",
    "warning": "#daa038", "warn": "#daa038", "yellow": "#daa038",
    "danger": "#dc3545", "error": "#dc3545", "red": "#dc3545", "critical": "#dc3545",
    "info": "#3b82f6", "blue": "#3b82f6",
}


# ── Block Kit builders ─────────────────────────────────────────────

def build_header(text: str, emoji: bool = True) -> dict:
    return {"type": "header", "text": {"type": "plain_text", "text": text, "emoji": emoji}}


def build_section(mrkdwn: str) -> dict:
    return {"type": "section", "text": {"type": "mrkdwn", "text": mrkdwn}}


def build_fields(pairs: dict[str, str]) -> dict:
    return {
        "type": "section",
        "fields": [{"type": "mrkdwn", "text": f"*{k}:*\n{v}"} for k, v in pairs.items()],
    }


def build_context(texts: list[str]) -> dict:
    return {"type": "context", "elements": [{"type": "mrkdwn", "text": t} for t in texts]}


def build_divider() -> dict:
    return {"type": "divider"}


def build_code_section(text: str, label: str = "") -> dict:
    body = f"*{label}*\n```\n{text}\n```" if label else f"```\n{text}\n```"
    return {"type": "section", "text": {"type": "mrkdwn", "text": body}}


# ── Color helpers ──────────────────────────────────────────────────

def resolve_color(color: str) -> Optional[str]:
    if not color:
        return None
    c = color.lower().strip("#")
    if c in COLOR_MAP:
        return COLOR_MAP[c]
    if len(c) == 6 and all(ch in "0123456789abcdef" for ch in c):
        return f"#{c}"
    return None


# ── Payload builder ────────────────────────────────────────────────

def build_payload(
    text: str,
    *,
    username: Optional[str] = None,
    channel: Optional[str] = None,
    icon_emoji: Optional[str] = None,
    blocks: Optional[list[dict]] = None,
    attachments: Optional[list[dict]] = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"text": text}
    if blocks:
        payload["blocks"] = blocks
    if attachments:
        payload["attachments"] = attachments
    if username:
        payload["username"] = username
    if channel:
        payload["channel"] = channel
    if icon_emoji:
        payload["icon_emoji"] = icon_emoji
    return payload


def compose_blocks(
    *,
    header: Optional[str] = None,
    body: Optional[str] = None,
    fields: Optional[dict[str, str]] = None,
    code: Optional[str] = None,
    context: Optional[list[str]] = None,
) -> list[dict]:
    blocks: list[dict] = []
    if header:
        blocks.append(build_header(header))
    if fields:
        blocks.append(build_fields(fields))
    if body:
        for ch in chunk_text(body, MAX_BLOCK_TEXT_CHARS):
            blocks.append(build_section(ch))
    if code:
        if blocks:
            blocks.append(build_divider())
        for ch in chunk_text(code, MAX_BLOCK_TEXT_CHARS - 200):
            blocks.append(build_code_section(ch))
    if context:
        if blocks:
            blocks.append(build_divider())
        blocks.append(build_context(context))
    return blocks


# ── Chunking ───────────────────────────────────────────────────────

def chunk_text(text: str, size: int = MAX_SLACK_TEXT_CHARS) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)] or [""]


def chunk_blocks(blocks: list[dict], max_blocks: int = 50) -> list[list[dict]]:
    if len(blocks) <= max_blocks:
        return [blocks]
    result = []
    for i in range(0, len(blocks), max_blocks):
        chunk = blocks[i : i + max_blocks]
        if i > 0 and chunk and chunk[0].get("type") != "header":
            chunk = [build_header("Continued")] + chunk
        result.append(chunk)
    return result


# ── Sending ────────────────────────────────────────────────────────

def send_payload(webhook_url: str, payload: dict, *, timeout: float = 15.0) -> dict[str, Any]:
    try:
        response = requests.post(webhook_url, json=payload, timeout=timeout)
        response.raise_for_status()
        return {"ok": True, "status_code": response.status_code, "response": response.text}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def send_to_slack(
    webhook_url: str,
    text: str,
    *,
    username: Optional[str] = None,
    channel: Optional[str] = None,
    icon_emoji: Optional[str] = None,
    blocks: Optional[list[dict]] = None,
    color: Optional[str] = None,
    attachments: Optional[list[dict]] = None,
    timeout: float = 15.0,
) -> dict[str, Any]:
    if color and not attachments:
        hex_c = resolve_color(color)
        if hex_c:
            attachments = [{"color": hex_c}]
    payload = build_payload(
        text,
        username=username,
        channel=channel,
        icon_emoji=icon_emoji,
        blocks=blocks,
        attachments=attachments,
    )
    return send_payload(webhook_url, payload, timeout=timeout)


# ── CLI helpers ────────────────────────────────────────────────────

def read_message(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    if args.file:
        return Path(args.file).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("No message provided. Use --text, --file, or pipe stdin.")


def parse_fields(raw: list[str]) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for item in raw:
        if "=" not in item:
            print(f"Warning: ignoring field '{item}' (missing '=')", file=sys.stderr)
            continue
        key, _, value = item.partition("=")
        pairs[key.strip()] = value.strip()
    return pairs


# ── CLI entrypoint ─────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Send structured Slack messages via Incoming Webhook using Block Kit."
    )
    parser.add_argument("--webhook-url", default=os.getenv("SLACK_WEBHOOK_URL"))
    parser.add_argument("--text", help="Message text to send.")
    parser.add_argument("--file", help="Read message text from file.")
    parser.add_argument("--header", help="Header block text (appears bold at top).")
    parser.add_argument("--color", choices=list(COLOR_MAP), help="Sidebar color bar. Values: good, warning, danger, info")
    parser.add_argument("--field", action="append", default=[], metavar="KEY=VALUE", help="Key-value field (repeatable).")
    parser.add_argument("--username", default=os.getenv("SLACK_USERNAME"))
    parser.add_argument("--channel", default=os.getenv("SLACK_CHANNEL"))
    parser.add_argument("--icon-emoji", default=os.getenv("SLACK_ICON_EMOJI"))
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without sending.")
    args = parser.parse_args()

    if not args.webhook_url and not args.dry_run:
        raise SystemExit("Missing Slack webhook. Set SLACK_WEBHOOK_URL or pass --webhook-url.")

    message = read_message(args).strip()
    use_blocks = bool(args.header or args.field or args.color)

    if use_blocks:
        fields = parse_fields(args.field)
        blocks = compose_blocks(
            header=args.header,
            body=message if not args.header and not args.field else message if not args.header else None,
            fields=fields if fields else None,
        )
        hex_color = resolve_color(args.color) if args.color else None
        payloads_data = []
        for blk_chunk in chunk_blocks(blocks):
            p = build_payload(
                text=message[:300] if len(message) > 300 else message,
                username=args.username,
                channel=args.channel,
                icon_emoji=args.icon_emoji,
                blocks=blk_chunk,
            )
            if hex_color:
                p["attachments"] = [{"color": hex_color}]
            payloads_data.append(p)
    else:
        payloads_data = [
            build_payload(chunk, username=args.username, channel=args.channel, icon_emoji=args.icon_emoji)
            for chunk in chunk_text(message)
        ]

    if args.dry_run:
        print(json.dumps(payloads_data, indent=2, ensure_ascii=False))
        return 0

    ok = True
    for idx, payload in enumerate(payloads_data, start=1):
        res = send_payload(args.webhook_url, payload)
        print(f"Slack part {idx}/{len(payloads_data)}: {res}")
        ok = ok and bool(res.get("ok"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
