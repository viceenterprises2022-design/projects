#!/usr/bin/env python3
"""Send structured Slack messages via Incoming Webhook using Block Kit.

CLI examples:
  send_slack.py --text "Hello world"
  send_slack.py --header "Deploy Complete" --field "Status: OK" --color good
  send_slack.py --file log.txt --color danger --header "Crash Report"
  echo "alert" | send_slack.py --color warning

Python import (backward compat — functions now live in channels.slack):
  from channels.slack import send_to_slack, build_header, build_fields, compose_blocks
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

from channels.slack import (  # noqa: F401 — re-exported for backward compat
    COLOR_MAP,
    build_code_section,
    build_context,
    build_divider,
    build_fields,
    build_header,
    build_payload,
    build_section,
    chunk_blocks,
    chunk_text,
    compose_blocks,
    MAX_BLOCK_TEXT_CHARS,
    MAX_SLACK_TEXT_CHARS,
    resolve_color,
    send_payload,
    send_to_slack,
)


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
    parser.add_argument("--blocks", help="JSON string of Block Kit blocks (bypasses header/field/text construction).")
    parser.add_argument("--username", default=os.getenv("SLACK_USERNAME"))
    parser.add_argument("--channel", default=os.getenv("SLACK_CHANNEL"))
    parser.add_argument("--icon-emoji", default=os.getenv("SLACK_ICON_EMOJI"))
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without sending.")
    args = parser.parse_args()

    if not args.webhook_url and not args.dry_run:
        raise SystemExit("Missing Slack webhook. Set SLACK_WEBHOOK_URL or pass --webhook-url.")

    message = _read_message(args).strip()
    use_blocks = bool(args.header or args.field or args.color or args.blocks)

    if use_blocks:
        blocks = []
        if args.blocks:
            try:
                blocks = json.loads(args.blocks)
            except json.JSONDecodeError as e:
                raise SystemExit(f"Error parsing --blocks JSON: {e}")
        else:
            fields = _parse_fields(args.field)
            blocks = compose_blocks(
                header=args.header,
                body=message or None,
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


def _read_message(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    if args.file:
        return Path(args.file).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("No message provided. Use --text, --file, or pipe stdin.")


def _parse_fields(raw: list[str]) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for item in raw:
        if "=" not in item:
            print(f"Warning: ignoring field '{item}' (missing '=')", file=sys.stderr)
            continue
        key, _, value = item.partition("=")
        pairs[key.strip()] = value.strip()
    return pairs


if __name__ == "__main__":
    raise SystemExit(main())
