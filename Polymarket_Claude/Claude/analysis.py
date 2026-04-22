"""
analysis.py — Read results.tsv and surface insights.
Usage:
    python analysis.py              # terminal report
    python analysis.py --telegram   # send to Telegram too
"""
import argparse, csv, json, os, sys, urllib.request
from collections import defaultdict
from pathlib import Path

RESULTS_FILE = "results.tsv"

def load():
    if not Path(RESULTS_FILE).exists():
        print(f"No {RESULTS_FILE}. Run dgm_h_loop.py first."); sys.exit(1)
    with open(RESULTS_FILE, newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    for row in rows:
        for field in ("sharpe_before","sharpe_after","delta","win_rate","max_dd"):
            try: row[field] = float(row[field]) if row.get(field) else None
            except (ValueError,TypeError): row[field] = None
    return rows

def analyze(rows):
    exps   = [r for r in rows if r.get("kept") not in ("BASELINE",)]
    kept   = [r for r in exps if r.get("kept")=="KEPT"]
    discard= [r for r in exps if r.get("kept")=="DISCARDED"]
    crashes= [r for r in exps if r.get("kept")=="CRASH"]
    base_row = next((r for r in rows if r.get("kept")=="BASELINE"), None)
    base_sharpe = float(base_row["sharpe_after"]) if base_row and base_row.get("sharpe_after") else 0.0
    best_sharpe = max((float(r["sharpe_after"]) for r in kept if r.get("sharpe_after")), default=base_sharpe)
    near_misses = sorted([r for r in discard if r.get("delta") and r["delta"] > -0.10], key=lambda x:x["delta"] or -99, reverse=True)
    top_kept    = sorted(kept, key=lambda x:x.get("delta") or 0, reverse=True)[:5]
    stop_words  = {"the","a","an","to","of","and","in","is","it","this","that","for","with","should","will","may","improve","increase","decrease","reduce","higher","lower","change","adjust","modify","update"}
    keeper_words= defaultdict(int); discard_words=defaultdict(int)
    for r in kept:
        for w in (r.get("hypothesis","") or "").lower().split():
            w=w.strip(".,;:"); keeper_words[w]+=1 if len(w)>3 and w not in stop_words else 0
    for r in discard:
        for w in (r.get("hypothesis","") or "").lower().split():
            w=w.strip(".,;:"); discard_words[w]+=1 if len(w)>3 and w not in stop_words else 0
    signal_words = sorted([(w, keeper_words[w]-discard_words.get(w,0)) for w in keeper_words if keeper_words[w]>=2], key=lambda x:x[1], reverse=True)[:8]
    overall_kr = len(kept)/max(len(exps),1)
    last20 = exps[-20:]; last20_kr = sum(1 for r in last20 if r.get("kept")=="KEPT")/max(len(last20),1)
    return {"total":len(exps),"kept":len(kept),"discarded":len(discard),"crashes":len(crashes),
            "overall_kr":overall_kr,"base":base_sharpe,"best":best_sharpe,"improvement":best_sharpe-base_sharpe,
            "near_misses":near_misses[:5],"top_kept":top_kept,"signal_words":signal_words,
            "last20_kr":last20_kr,"diminishing":last20_kr<(overall_kr*0.5) and len(exps)>30}

def print_report(a):
    print(f"\n{'═'*65}\n  AUTORESEARCH ANALYSIS\n{'═'*65}")
    print(f"\n  Experiments: {a['total']} | Kept: {a['kept']} | Discarded: {a['discarded']} | Crashes: {a['crashes']}")
    print(f"  Keep rate: {a['overall_kr']:.1%} | Last 20: {a['last20_kr']:.1%}" + (" ⚠️  DIMINISHING" if a['diminishing'] else ""))
    print(f"\n  Sharpe: {a['base']:.4f} → {a['best']:.4f} (+{a['improvement']:.4f})")
    if a['top_kept']:
        print(f"\n  Top Improvements:")
        for r in a['top_kept']:
            print(f"    Exp #{r.get('iter',0):>3}: {(r.get('hypothesis') or '')[:55]}")
            print(f"             Δ={float(r.get('delta') or 0):+.4f}")
    if a['near_misses']:
        print(f"\n  Near-Misses (try combining):")
        for r in a['near_misses']:
            print(f"    Exp #{r.get('iter',0):>3}: {(r.get('hypothesis') or '')[:55]} Δ={float(r.get('delta') or 0):+.4f}")
    if a['signal_words']:
        print(f"\n  Winning directions:")
        for w,s in a['signal_words'][:6]:
            print(f"    {w:<20} (score: {s})")
    if a['diminishing']:
        print(f"\n  ⚠️  Diminishing returns: try parallel_researcher.py or accumulate more signal data")
    print("="*65+"\n")

def fmt_telegram(a) -> str:
    lines = [f"📊 *AutoResearch Report*","",f"Experiments: `{a['total']}` | Kept: `{a['kept']}`",
             f"Keep rate: `{a['overall_kr']:.0%}` (last 20: `{a['last20_kr']:.0%}`)",
             f"Sharpe: `{a['base']:.4f}` → `{a['best']:.4f}` (+`{a['improvement']:.4f}`)"]
    if a['near_misses']:
        lines += ["","*Near-misses to combine:*"]
        for r in a['near_misses'][:3]:
            lines.append(f"  • `{(r.get('hypothesis') or '')[:45]}` Δ`{float(r.get('delta') or 0):+.4f}`")
    if a['top_kept']:
        lines += ["","*Best improvements:*"]
        for r in a['top_kept'][:3]:
            lines.append(f"  • `{(r.get('hypothesis') or '')[:45]}` Δ`{float(r.get('delta') or 0):+.4f}`")
    if a['diminishing']: lines += ["","⚠️ *Diminishing returns — expand data or try new directions*"]
    return "\n".join(lines)

def send_tg(text):
    tok=os.environ.get("TELEGRAM_BOT_TOKEN",""); cid=os.environ.get("TELEGRAM_CHAT_ID","")
    if not tok or not cid: print("Telegram not configured"); return
    p=json.dumps({"chat_id":cid,"text":text,"parse_mode":"Markdown"}).encode()
    urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{tok}/sendMessage",data=p,headers={"Content-Type":"application/json"}),timeout=10)
    print("Report sent to Telegram")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--telegram",action="store_true")
    a_args = parser.parse_args()
    rows = load(); result = analyze(rows); print_report(result)
    if a_args.telegram: send_tg(fmt_telegram(result))
