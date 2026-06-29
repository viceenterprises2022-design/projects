"""Slack Block Kit messaging — shared library for all scripts.

Import:
  from channels.slack import send_to_slack, build_header, compose_blocks
"""
import json
from pathlib import Path
from typing import Any, Optional

import requests

MAX_SLACK_TEXT_CHARS = 3500
MAX_BLOCK_TEXT_CHARS = 2900

COLOR_MAP: dict[str, str] = {
    "good": "#36a64f", "success": "#36a64f", "green": "#36a64f",
    "warning": "#daa038", "warn": "#daa038", "yellow": "#daa038",
    "danger": "#dc3545", "error": "#dc3545", "red": "#dc3545", "critical": "#dc3545",
    "info": "#3b82f6", "blue": "#3b82f6",
}


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


def resolve_color(color: str) -> Optional[str]:
    if not color:
        return None
    c = color.lower().strip("#")
    if c in COLOR_MAP:
        return COLOR_MAP[c]
    if len(c) == 6 and all(ch in "0123456789abcdef" for ch in c):
        return f"#{c}"
    return None


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


def send_payload(webhook_url: str, payload: dict, *, timeout: float = 15.0) -> dict[str, Any]:
    try:
        resp = requests.post(webhook_url, json=payload, timeout=timeout)
        resp.raise_for_status()
        return {"ok": True, "status_code": resp.status_code, "response": resp.text}
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
