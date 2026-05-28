import sys
import os
import requests
import html

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the original script
import market_analysis_v3 as ma

def send_to_telegram(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

def format_report(sym, q, fq, oi, a_res):
    ltp = q['ltp']
    chg = q['change_pct']
    signal = a_res['signal']
    score = a_res['score']
    
    report = f"<b>{sym} | Spot: {ltp:,.2f} ({chg:+.2f}%)</b>\n"
    report += f"<b>Signal: {signal} ({score}/10)</b>\n\n"
    
    report += "<b>INDICATORS:</b>\n"
    for key, data in a_res['indicators'].items():
        label = data['label']
        detail = data['detail']
        # Clean labels and details of potential Rich tags if any (though a_res shouldn't have them)
        report += f"• {key.upper().replace('_', ' ')}: {label}\n  <i>{detail}</i>\n"
    
    if oi:
        report += f"\n<b>INTEL:</b>\n"
        report += f"PCR: {oi['total_pcr']:.2f} | Max Pain: {oi['max_pain']:,.0f}\n"
        report += f"Expiry: {oi['expiry']}\n"
        
    return report

def run():
    ma.init_db()
    TOKEN = "8770565112:AAGy9q-BMWsgvU4RQUQDyeNXa282Vme9uG4"
    CHAT_ID = "7246234100"

    print("ALPHAEDGE MARKET INTELLIGENCE REPORT")
    
    for sym in ["NIFTY", "BANKNIFTY"]:
        try:
            print(f"Analyzing {sym}...")
            result = ma.run_analysis(sym)
            if result:
                # result is (sym, q, fq, oi, a_res)
                _, q, fq, oi, a_res = result
                report_text = format_report(sym, q, fq, oi, a_res)
                
                res = send_to_telegram(TOKEN, CHAT_ID, report_text)
                print(f"Sent {sym} report: {res.get('ok')}")
        except Exception as e:
            print(f"Error analyzing {sym}: {e}")

if __name__ == "__main__":
    run()
