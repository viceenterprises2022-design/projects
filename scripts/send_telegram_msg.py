import os
import sys
import argparse
import re

import requests

TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN",
    "8770565112:AAGy9q-BMWsgvU4RQUQDyeNXa282Vme9uG4",
)
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7246234100")

def detect_format(text):
    """Detect if text is HTML or Markdown."""
    has_markdown = False
    if re.search(r"^\s*(?:#+\s|\-\s|\*\s|\+\s|\d+\.\s|\|.*?\|)", text, re.M):
        has_markdown = True
    elif re.search(r"\*\*.*?\*\*|__.*?__|\[.*?\]\(.*?\)", text):
        has_markdown = True
        
    if has_markdown:
        return "markdown"
        
    # Check for HTML tags
    if re.search(r"<[a-z/]+[^>]*>", text, re.I):
        return "html"
        
    return "html"

def send_text(text, parse_mode="HTML", mode="auto"):
    """Send a text message to the pre-configured Telegram chat.
    Uses sendRichMessage for rich formatting support if HTML or Markdown is requested."""
    # Determine formatting mode
    if mode == "auto":
        fmt = detect_format(text)
    else:
        fmt = mode.lower()

    if parse_mode in ["Markdown", "MarkdownV2"]:
        fmt = "markdown"

    url = f"https://api.telegram.org/bot{TOKEN}/sendRichMessage"
    rich_payload = {
        "chat_id": CHAT_ID,
        "rich_message": {
            fmt: text
        }
    }
    
    try:
        r = requests.post(url, json=rich_payload, timeout=15)
        res = r.json()
        if res.get("ok"):
            return res
        sys.stderr.write(f"sendRichMessage failed: {res.get('description')}\n")
    except Exception as e:
        sys.stderr.write(f"sendRichMessage error: {e}\n")
        
    # Fallback to standard sendMessage
    fallback_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": parse_mode
    }
    try:
        r = requests.post(fallback_url, json=payload, timeout=15)
        return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

def send_file(file_path, caption=None):
    """Send a file (document) to the pre-configured Telegram chat."""
    if not os.path.exists(file_path):
        return {"ok": False, "error": f"File not found: {file_path}"}
        
    url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
    files = {"document": open(file_path, "rb")}
    data = {"chat_id": CHAT_ID}
    if caption:
        data["caption"] = caption
        data["parse_mode"] = "HTML"
        
    try:
        r = requests.post(url, data=data, files=files, timeout=30)
        return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

if __name__ == "__main__":
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

    if args.token:
        TOKEN = args.token
    if args.chat_id:
        CHAT_ID = args.chat_id

    res = send_text(msg, parse_mode=args.parse_mode, mode=args.mode)
    print(f"Sent: {res.get('ok')}")
