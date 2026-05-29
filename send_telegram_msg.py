import requests
import os
import sys

# Credentials from report_and_send.py
TOKEN = "8770565112:AAGy9q-BMWsgvU4RQUQDyeNXa282Vme9uG4"
CHAT_ID = "7246234100"

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
    # If run directly from CLI, treat arguments as message
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
        res = send_text(msg)
        print(f"Sent: {res.get('ok')}")
    else:
        print("Usage: python3 send_telegram_msg.py 'your message here'")
