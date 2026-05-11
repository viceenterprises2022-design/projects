import requests
import sys

def send_to_telegram(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error sending to Telegram: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 send_telegram.py <token> <chat_id> <text>")
        sys.exit(1)
    
    token = sys.argv[1]
    chat_id = sys.argv[2]
    text = sys.argv[3]
    
    res = send_to_telegram(token, chat_id, text)
    if res and res.get("ok"):
        print("Successfully sent to Telegram")
    else:
        print(f"Failed to send: {res}")
