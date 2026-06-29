"""Unified channel abstraction for Slack and Telegram delivery.

Usage:
  from channels import slack, telegram

  # Slack
  slack.send_to_slack(webhook_url, "Hello", blocks=[...])

  # Telegram
  telegram.send_text("Hello")
  telegram.send_file("report.pdf")

  # Unified dispatcher
  from channels import send
  send("slack", webhook_url="...", text="Hello")
"""
from . import slack, telegram

PLATFORMS = {"slack": slack, "telegram": telegram}


def send(platform: str, **kwargs):
    mod = PLATFORMS.get(platform)
    if mod is None:
        raise ValueError(f"Unknown channel platform: {platform!r}. Choose: {list(PLATFORMS)}")
    if platform == "slack":
        return mod.send_to_slack(kwargs.pop("webhook_url"), **kwargs)
    return mod.send_text(**kwargs)
