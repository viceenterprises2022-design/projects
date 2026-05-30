import os
import sys
import argparse

import requests

TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN",
    "8770565112:AAGy9q-BMWsgvU4RQUQDyeNXa282Vme9uG4",
)
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7246234100")

def send_text(text, parse_mode="HTML"):
    """Send a text message to the pre-configured Telegram chat."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": parse_mode
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
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

    res = send_text(msg)
    print(f"Sent: {res.get('ok')}")
