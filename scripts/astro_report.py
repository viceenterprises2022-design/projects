import os
import requests
import json
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

class SlackNotifier:
    def __init__(self, webhook_url="", username="AstroBot"):
        self.webhook_url = webhook_url
        self.username = username

    def send(self, title, text):
        message = f"*{title}*\n{text}"
        if not self.webhook_url:
            print(message)
            return False
        payload = json.dumps({"text": message, "username": self.username}).encode("utf-8")
        req = urllib.request.Request(
            self.webhook_url,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "AstroBot/1.0"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return 200 <= resp.status < 300
        except Exception as e:
            print(f"Slack error: {e}")
            return False

def fetch_exa_context():
    api_key = os.getenv("EXA_API_KEY")
    if not api_key: raise ValueError("EXA_API_KEY missing")
    url = "https://api.exa.ai/search"
    headers = {"x-api-key": api_key, "content-type": "application/json"}
    payload = {
        "query": "Taurus sun Cancer moon daily horoscope Indian Vedic astrology today finance family business health lucky day numbers remediation",
        "numResults": 5,
        "useAutoprompt": True,
        "contents": {"text": True}
    }
    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return "\n\n".join([r.get("text", "")[:2000] for r in results])

def generate_report(context):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: raise ValueError("GEMINI_API_KEY missing")
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
    prompt = f"Expert Indian Vedic astrologer. Daily report for Taurus Sun, Cancer Moon (DOB: June 30, 1981). Sections: This Week, Today, Finance, Family, Business, Health, Lucky Day & Numbers, Remediation (Gods to pray, Mantras). Use Slack Markdown. Context:\n{context}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

def main():
    load_dotenv()
    
    slack_url = os.getenv("SLACK_WEBHOOK_ASTRO") or os.getenv("SLACK_WEBHOOK_URL")
    if not slack_url:
        print("SLACK_WEBHOOK_ASTRO/SLACK_WEBHOOK_URL missing. Defaulting to console.")
        slack_url = ""

    print("Fetching data...")
    try:
        context = fetch_exa_context()
        report = generate_report(context)
        notifier = SlackNotifier(slack_url, "Astro Insight")
        notifier.send("Daily Astro Report: Taurus ☀️ / Cancer 🌙", report)
        print("Success!")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    main()
