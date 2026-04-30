import sys
import os
import requests
import datetime
import time
import html

# Add script directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import market_analysis_v3 as ma

TELEGRAM_BOT_TOKEN = "8777670827:AAFJpLDZCHLrnAOV4ygA1AqTXGubE9H22RI"
TELEGRAM_CHANNEL = "@dvr_market_snippet"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, json=payload, timeout=20)
        if r.status_code == 200:
            return True
        print(f"Telegram error {r.status_code}: {r.text}")
    except Exception as e:
        print(f"Telegram exception: {e}")
    return False

def main():
    symbols = ["NIFTY", "BANKNIFTY", "SENSEX"]
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    header = f"<b>⚡ AlphaEdge V3 Diagnostic Report</b>\n🗓 <i>{now}</i>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for sym in symbols:
        print(f"Analyzing {sym}...")
        try:
            res = ma.run_analysis(sym)
        except Exception as e:
            print(f"Error analyzing {sym}: {e}")
            continue
            
        if not res:
            continue
            
        sym, quote, oi_raw, indicators, signal, score = res
        
        ltp = quote.get("ltp", 0)
        chg = quote.get("change_pct", 0)
        chg_sign = "+" if chg >= 0 else ""
        sig_emoji = "🚀" if signal == "BUY" and score >= 5 else "📈" if signal == "BUY" else \
                    "🔻" if signal == "SELL" and score <= -5 else "📉" if signal == "SELL" else "⚖️"
        
        msg = f"<b>{sym}</b>  |  <code>{ltp:,.2f}</code> ({chg_sign}{chg:.2f}%)\n"
        msg += f"Signal: <b>{signal}</b> (<code>{score}/10</code>) {sig_emoji}\n"
        
        if oi_raw:
            msg += f"PCR: <code>{oi_raw['total_pcr']:.2f}</code>  |  Max Pain: <code>{oi_raw['max_pain']:,}</code>\n"
        
        # Key Factors
        msg += "Key Factors:\n"
        # Sort factors by impact (absolute score)
        sorted_factors = sorted(indicators.items(), key=lambda x: (abs(x[1]['score']), x[1]['score']), reverse=True)
        for i in range(min(5, len(sorted_factors))):
            k, v = sorted_factors[i]
            s_icon = "🟢" if v['score'] > 0 else "🔴" if v['score'] < 0 else "⚪"
            label = html.escape(v['label'].split('(')[0].strip())
            msg += f"• {s_icon} {k.upper()}: {label}\n"
            
        header += msg + "━━━━━━━━━━━━━━━━━━━━\n"
        
    header += "\n<i>AlphaEdge Financial Intelligence</i>"
    
    if send_telegram(header):
        print("Report sent to Telegram successfully!")
    else:
        print("Failed to send report.")

if __name__ == "__main__":
    main()
