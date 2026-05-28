import sys
import os
import html

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the original script
import market_analysis_v3 as ma
import send_telegram_msg as tg

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
        # Clean labels and details of potential Rich tags if any
        report += f"• {key.upper().replace('_', ' ')}: {label}\n  <i>{detail}</i>\n"
    
    if oi:
        report += f"\n<b>INTEL:</b>\n"
        report += f"PCR: {oi['total_pcr']:.2f} | Max Pain: {oi['max_pain']:,.0f}\n"
        report += f"Expiry: {oi['expiry']}\n"
        
    return report

def run():
    ma.init_db()

    print("ALPHAEDGE MARKET INTELLIGENCE REPORT")
    
    for sym in ["NIFTY", "BANKNIFTY"]:
        try:
            print(f"Analyzing {sym}...")
            result = ma.run_analysis(sym)
            if result:
                # result is (sym, q, fq, oi, a_res)
                _, q, fq, oi, a_res = result
                report_text = format_report(sym, q, fq, oi, a_res)
                
                res = tg.send_text(report_text)
                print(f"Sent {sym} report: {res.get('ok')}")
        except Exception as e:
            print(f"Error analyzing {sym}: {e}")

if __name__ == "__main__":
    run()
