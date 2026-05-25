import sys
import os
import json
import requests
import io
import html
import re

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the original script
import market_analysis_v3 as ma
from rich.console import Console

class CapturingConsole(Console):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output = []
    
    def print(self, *args, **kwargs):
        f = io.StringIO()
        temp_console = Console(file=f, force_terminal=False, width=80) # Narrower
        temp_console.print(*args, **kwargs)
        self.output.append(f.getvalue())

capturing_console = CapturingConsole()
ma.console = capturing_console

def send_to_telegram(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

def run():
    ma.init_db()
    TOKEN = "8770565112:AAGy9q-BMWsgvU4RQUQDyeNXa282Vme9uG4"
    CHAT_ID = "7246234100"

    print("<b>ALPHAEDGE MARKET INTELLIGENCE REPORT</b>")
    
    for sym in ["NIFTY", "BANKNIFTY"]:
        try:
            result = ma.run_analysis(sym)
            if result:
                ma.display_dashboard(*result)
                content = "".join(capturing_console.output)
                capturing_console.output = []
                
                # Strip rich tags
                clean_content = re.sub(r'\[/?[a-z ]+\]', '', content)
                # Escape HTML
                escaped = html.escape(clean_content)
                
                # Split into chunks of 4000 chars
                chunks = [escaped[i:i+3500] for i in range(0, len(escaped), 3500)]
                for i, chunk in enumerate(chunks):
                    prefix = f"<b>{sym} Analysis (Part {i+1})</b>\n"
                    res = send_to_telegram(TOKEN, CHAT_ID, f"{prefix}<pre>{chunk}</pre>")
                    print(f"Sent {sym} part {i+1}: {res.get('ok')}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run()
