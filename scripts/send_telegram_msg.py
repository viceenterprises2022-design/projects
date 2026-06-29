"""Send a Telegram message — thin CLI wrapper over channels.telegram.

Python import (backward compat — functions now live in channels.telegram):
  from channels.telegram import send_text, send_file
"""
import argparse
import os
import sys

from channels.telegram import (  # noqa: F401 — re-exported for backward compat
    CHAT_ID as _TG_CHAT_ID_GLOBAL,
    TOKEN as _TG_TOKEN_GLOBAL,
    auto_format_content,
    detect_format,
    is_raw_report,
    send_file,
    send_text,
)


def main():
    parser = argparse.ArgumentParser(description="Send a Telegram message")
    parser.add_argument("--message", "-m", type=str, help="Message text to send")
    parser.add_argument("--token", type=str, help="Bot token override")
    parser.add_argument("--chat-id", type=str, help="Chat ID override")
    parser.add_argument(
        "--mode",
        choices=["html", "markdown", "auto"],
        default="auto",
        help="Formatting mode for rich messages (html, markdown, or auto)",
    )
    parser.add_argument(
        "--parse-mode",
        type=str,
        default="HTML",
        help="Parse mode fallback (HTML or Markdown)",
    )
    parser.add_argument(
        "rest", nargs=argparse.REMAINDER, help="Message text (fallback)"
    )
    args = parser.parse_args()

    msg = args.message or (" ".join(args.rest) if args.rest else None)
    if not msg:
        parser.print_help()
        sys.exit(1)

    token = args.token or _TG_TOKEN_GLOBAL
    chat_id = args.chat_id or _TG_CHAT_ID_GLOBAL

    res = send_text(msg, parse_mode=args.parse_mode, mode=args.mode, token=token, chat_id=chat_id)
    print(f"Sent: {res.get('ok')}")


if __name__ == "__main__":
    main()
