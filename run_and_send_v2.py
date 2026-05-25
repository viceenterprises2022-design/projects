import sys
import os
import json
import requests
import io
import html
import re
import time

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the original script
import market_analysis_v3 as ma
from rich.console import Console

class CapturingConsole(Console):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.captured_text = ""
    
    def print(self, *args, **kwargs):
        f = io.StringIO()
        temp_console = Console(file=f, force_terminal=False, width=80)
        temp_console.print(*args, **kwargs)
        self.captured_text += f.getvalue()

capturing_console = CapturingConsole()
ma.console = capturing_console

def send_to_telegram(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        response = requests.post(url, json=payload, timeout=20)
        print(f"Telegram response: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"Telegram error: {e}")
        return {"ok": False, "error": str(e)}

def run():
    ma.init_db()
    TOKEN = "8770565112:AAGy9q-BMWsgvU4RQUQDyeNXa282Vme9uG4"
    CHAT_ID = "7246234100"

    print("Starting market analysis execution...")
    
    for sym in ["NIFTY", "BANKNIFTY"]:
        try:
            print(f"Running analysis for {sym}...")
            result = ma.run_analysis(sym)
            if result:
                capturing_console.captured_text = ""
                ma.display_dashboard(*result)
                content = capturing_console.captured_text
                
                # Strip rich tags and clean up
                clean_content = re.sub(r'\[/?[a-zA-Z ]+\]', '', content)
                clean_content = clean_content.replace("Auto-refreshing every 30s... [Ctrl+C] to return to menu", "")
                
                header = f"{sym} ANALYSIS REPORT - MAY 11, 2026\n"
                full_text = header + clean_content
                
                # Split into chunks of 4000 chars to be safe
                chunks = [full_text[i:i+4000] for i in range(0, len(full_text), 4000)]
                for i, chunk in enumerate(chunks):
                    send_to_telegram(TOKEN, CHAT_ID, chunk)
            else:
                print(f"Failed to run analysis for {sym}")
        except Exception as e:
            print(f"Error analyzing {sym}: {e}")

if __name__ == "__main__":
    run()
