#!/usr/bin/env python3
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


def chunk_text(text: str, size: int = MAX_SLACK_TEXT_CHARS) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)] or [""]


def build_payload(
    text: str,
    *,
    username: Optional[str] = None,
    channel: Optional[str] = None,
    icon_emoji: Optional[str] = None,
    blocks: Optional[list[dict]] = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"text": text}
    if blocks:
        payload["blocks"] = blocks
    if username:
        payload["username"] = username
    if channel:
        payload["channel"] = channel
    if icon_emoji:
        payload["icon_emoji"] = icon_emoji
    return payload


def send_to_slack(
    webhook_url: str,
    text: str,
    *,
    username: Optional[str] = None,
    channel: Optional[str] = None,
    icon_emoji: Optional[str] = None,
    blocks: Optional[list[dict]] = None,
    timeout: float = 15.0,
) -> dict[str, Any]:
    payload = build_payload(text, username=username, channel=channel, icon_emoji=icon_emoji, blocks=blocks)
    try:
        response = requests.post(webhook_url, json=payload, timeout=timeout)
        response.raise_for_status()
        return {"ok": True, "status_code": response.status_code, "response": response.text}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def read_message(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    if args.file:
        return Path(args.file).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("No message provided. Use --text, --file, or pipe stdin.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a standalone message to Slack via Incoming Webhook.")
    parser.add_argument("--webhook-url", default=os.getenv("SLACK_WEBHOOK_URL"), help="Slack webhook URL. Defaults to SLACK_WEBHOOK_URL.")
    parser.add_argument("--text", help="Message text to send.")
    parser.add_argument("--file", help="Read message text from file.")
    parser.add_argument("--title", help="Optional title prepended in bold.")
    parser.add_argument("--username", default=os.getenv("SLACK_USERNAME"), help="Optional bot display name.")
    parser.add_argument("--channel", default=os.getenv("SLACK_CHANNEL"), help="Optional channel override if webhook allows it.")
    parser.add_argument("--icon-emoji", default=os.getenv("SLACK_ICON_EMOJI"), help="Optional icon emoji, e.g. :chart_with_upwards_trend:.")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without sending.")
    args = parser.parse_args()

    if not args.webhook_url and not args.dry_run:
        raise SystemExit("Missing Slack webhook. Set SLACK_WEBHOOK_URL or pass --webhook-url.")

    message = read_message(args).strip()
    if args.title:
        message = f"*{args.title}*\n{message}"

    payloads = [
        build_payload(chunk, username=args.username, channel=args.channel, icon_emoji=args.icon_emoji)
        for chunk in chunk_text(message)
    ]

    if args.dry_run:
        print(json.dumps(payloads, indent=2, ensure_ascii=False))
        return 0

    ok = True
    for idx, payload in enumerate(payloads, start=1):
        res = send_to_slack(
            args.webhook_url,
            payload["text"],
            username=args.username,
            channel=args.channel,
            icon_emoji=args.icon_emoji,
        )
        print(f"Slack part {idx}/{len(payloads)}: {res}")
        ok = ok and bool(res.get("ok"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
