"""
dgm_h_loop.py — DGM-Hyperagents self-improvement loop for Polybot.
Run overnight. Never stop. Wake up to results.tsv.

Usage:
    python dgm_h_loop.py                  # run forever
    python dgm_h_loop.py --max-iter 50    # 50 experiments
    python dgm_h_loop.py --dry-run        # print proposals only
"""
import argparse, csv, json, math, os, random, shutil, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

HYPERAGENT_FILE = "hyperagent.py"
STRATEGY_FILE   = "strategy.yaml"
EVALUATE_SCRIPT = "evaluate.py"
RESULTS_FILE    = "results.tsv"
ARCHIVE_DIR     = "archive"
LOG_FILE        = "run.log"

parser = argparse.ArgumentParser()
parser.add_argument("--max-iter", type=int, default=10000)
parser.add_argument("--dry-run", action="store_true")
args = parser.parse_args()


# ── Git ───────────────────────────────────────────────────────────────────────
def git(*a) -> str:
    return subprocess.run(["git"]+list(a), capture_output=True, text=True).stdout.strip()

def git_commit(msg: str) -> bool:
    subprocess.run(["git","add", HYPERAGENT_FILE, STRATEGY_FILE])
    return subprocess.run(["git","commit","-m",f"exp: {msg[:80]}"], capture_output=True).returncode==0

def git_revert(target: str) -> bool:
    r1 = subprocess.run(["git","reset","HEAD~1","--",target], capture_output=True)
    r2 = subprocess.run(["git","checkout","--",target], capture_output=True)
    return r1.returncode==0 and r2.returncode==0


# ── Archive ───────────────────────────────────────────────────────────────────
class Archive:
    def __init__(self):
        Path(ARCHIVE_DIR).mkdir(exist_ok=True)
        idx = Path(f"{ARCHIVE_DIR}/index.json")
        self.agents = json.loads(idx.read_text()) if idx.exists() else []

    def _save(self):
        Path(f"{ARCHIVE_DIR}/index.json").write_text(json.dumps(self.agents, indent=2))

    def add(self, agent_id, sharpe, win_rate, max_dd, trades, hypothesis, ha_snap, strat_snap):
        d = Path(f"{ARCHIVE_DIR}/agent_{agent_id:04d}"); d.mkdir(exist_ok=True)
        (d/"hyperagent.py").write_text(ha_snap); (d/"strategy.yaml").write_text(strat_snap)
        self.agents.append({"id":agent_id,"sharpe":sharpe,"win_rate":win_rate,
            "max_drawdown":max_dd,"trade_count":trades,"hypothesis":hypothesis,
            "children":0,"compiled_children":0,"timestamp":time.time()})
        self._save()

    def select_parent(self) -> dict:
        if len(self.agents) == 1: return self.agents[0]
        top3  = sorted(self.agents, key=lambda x:x["sharpe"], reverse=True)[:3]
        mid   = sum(a["sharpe"] for a in top3) / len(top3)
        weights = [1/(1+math.exp(-10*(a["sharpe"]-mid))) * 1/(1+a["compiled_children"]) for a in self.agents]
        total = sum(weights) or 1; weights = [w/total for w in weights]
        r = random.random(); cum = 0
        for i, w in enumerate(weights):
            cum += w
            if r <= cum: return self.agents[i]
        return self.agents[-1]

    def load_snapshot(self, agent_id) -> tuple:
        d = Path(f"{ARCHIVE_DIR}/agent_{agent_id:04d}")
        return (d/"hyperagent.py").read_text(), (d/"strategy.yaml").read_text()

    def inc_children(self, agent_id, compiled=True):
        for a in self.agents:
            if a["id"] == agent_id:
                a["children"] += 1
                if compiled: a["compiled_children"] += 1
        self._save()

    def best(self): return max(self.agents, key=lambda x:x["sharpe"]) if self.agents else None


# ── Evaluation ────────────────────────────────────────────────────────────────
def run_eval() -> dict:
    with open(LOG_FILE,"w") as log:
        subprocess.run([sys.executable, EVALUATE_SCRIPT,"--config",STRATEGY_FILE],
                       stdout=log, stderr=log, timeout=120)
    content = Path(LOG_FILE).read_text(); metrics = {}
    for line in content.splitlines():
        if ":" in line:
            k,_,v = line.partition(":"); k=k.strip(); v=v.strip()
            if k in ("sharpe","win_rate","max_drawdown","pnl_7d","pnl_30d","mean_return","avg_hold_hours","total_pnl"):
                try: metrics[k]=float(v)
                except ValueError: pass
            elif k in ("trade_count","filtered_signals","sl_hits","tp_hits"):
                try: metrics[k]=int(v)
                except ValueError: pass
            elif k=="insufficient_data": metrics["insufficient_data"]=True
    if "sharpe" not in metrics and "insufficient_data" not in metrics:
        return {"crashed":True,"trace":"\n".join(content.splitlines()[-20:])}
    return metrics


# ── Decision ──────────────────────────────────────────────────────────────────
def decide(before, after) -> tuple:
    if after.get("crashed"):     return False,"CRASH"
    if after.get("insufficient_data"): return False,"INSUFFICIENT_DATA"
    s_delta  = after.get("sharpe",0) - before.get("sharpe",0)
    win_rate = after.get("win_rate",0); max_dd = after.get("max_drawdown",1); tc = after.get("trade_count",0)
    if tc < 5:        return False,f"TOO_FEW_TRADES ({tc})"
    if win_rate<0.50: return False,f"WIN_RATE_LOW ({win_rate:.1%})"
    if max_dd>=0.35:  return False,f"DRAWDOWN_HIGH ({max_dd:.1%})"
    if s_delta>=0 and max_dd<before.get("max_drawdown",1): return True,"SIMPLIFICATION_WIN"
    if s_delta>0: return True,f"IMPROVED (+{s_delta:.4f})"
    return False,f"NO_IMPROVEMENT ({s_delta:.4f})"


# ── Results log ───────────────────────────────────────────────────────────────
HEADERS = ["iter","timestamp","target","hypothesis","sharpe_before","sharpe_after","delta","win_rate","max_dd","trades","kept","notes"]

def init_results():
    if not Path(RESULTS_FILE).exists():
        with open(RESULTS_FILE,"w",newline="") as f:
            csv.DictWriter(f,fieldnames=HEADERS,delimiter="\t").writeheader()

def log_result(row):
    with open(RESULTS_FILE,"a",newline="") as f:
        csv.DictWriter(f,fieldnames=HEADERS,delimiter="\t",extrasaction="ignore").writerow(row)


# ── Telegram ──────────────────────────────────────────────────────────────────
def tg(text):
    import urllib.request
    tok=os.environ.get("TELEGRAM_BOT_TOKEN",""); cid=os.environ.get("TELEGRAM_CHAT_ID","")
    if not tok or not cid: return
    try:
        import json as j
        p=j.dumps({"chat_id":cid,"text":text,"parse_mode":"Markdown"}).encode()
        urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{tok}/sendMessage",data=p,headers={"Content-Type":"application/json"}),timeout=5)
    except Exception: pass


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("="*65); print("  POLYBOT DGM-H — Autonomous Self-Improvement")
    print(f"  Mode: {'DRY RUN' if args.dry_run else 'LIVE'} | Max: {args.max_iter}")
    print("="*65)

    init_results(); archive = Archive()
    print("\nEstablishing baseline...")
    baseline = run_eval()
    if baseline.get("crashed"):
        print("Baseline crashed:"); print(baseline.get("trace","")); sys.exit(1)
    if baseline.get("insufficient_data"):
        print("Insufficient data. Run: python main.py for 7+ days first."); sys.exit(1)
    baseline_sharpe = baseline.get("sharpe",0.0); current = baseline; best_sharpe = baseline_sharpe
    print(f"  Sharpe={baseline_sharpe:.4f} | WR={baseline.get('win_rate',0):.1%} | Trades={baseline.get('trade_count',0)}")
    archive.add(0,baseline_sharpe,baseline.get("win_rate",0),baseline.get("max_drawdown",0),
                baseline.get("trade_count",0),"BASELINE",Path(HYPERAGENT_FILE).read_text(),Path(STRATEGY_FILE).read_text())
    log_result({"iter":0,"timestamp":datetime.now(timezone.utc).isoformat(),"target":"—","hypothesis":"BASELINE",
                "sharpe_before":baseline_sharpe,"sharpe_after":baseline_sharpe,"delta":0,
                "win_rate":baseline.get("win_rate"),"max_dd":baseline.get("max_drawdown"),
                "trades":baseline.get("trade_count"),"kept":"BASELINE","notes":""})
    tg(f"*Polybot DGM-H Started*\nBaseline Sharpe: `{baseline_sharpe:.4f}`\nTrades: `{baseline.get('trade_count',0)}`\nMax iters: `{args.max_iter}`")

    t = 0; consecutive_crashes = 0
    while t < args.max_iter:
        t += 1; iterations_left = args.max_iter - t
        print(f"\n{'═'*65}\n  Iter {t:04d} | Best Sharpe: {best_sharpe:.4f} | Archive: {len(archive.agents)}\n{'═'*65}")
        parent = archive.select_parent()
        parent_ha, parent_strat = archive.load_snapshot(parent["id"])
        Path(HYPERAGENT_FILE).write_text(parent_ha); Path(STRATEGY_FILE).write_text(parent_strat)
        print("  Calling meta agent...")
        try:
            import importlib, sys as _sys
            if "hyperagent" in _sys.modules: del _sys.modules["hyperagent"]
            ha = importlib.import_module("hyperagent")
            target, new_content = ha.hyperagent.modify(archive.agents, iterations_left)
        except Exception as e:
            print(f"  Meta agent failed: {e}"); consecutive_crashes += 1
            if consecutive_crashes >= 5:
                tg("*DGM-H Alert*: 5 consecutive meta failures. Check hyperagent.py."); break
            continue
        print(f"  Target: {target}")
        if args.dry_run:
            print(f"  [DRY] Would modify {target}"); continue
        shutil.copy(target, target+".bak")
        Path(target).write_text(new_content)
        is_valid = True
        if target == HYPERAGENT_FILE:
            r = subprocess.run([sys.executable,"-c",f"import py_compile; py_compile.compile('{target}')"], capture_output=True)
            is_valid = r.returncode == 0
        if not is_valid:
            print("  Syntax error — reverting"); shutil.copy(target+".bak", target)
            archive.inc_children(parent["id"], compiled=False); consecutive_crashes += 1; continue
        consecutive_crashes = 0
        hyp_line = [l for l in new_content.split("\n") if "HYPOTHESIS:" in l]
        hypothesis = hyp_line[0].replace("HYPOTHESIS:","").strip() if hyp_line else "unknown"
        git_commit(hypothesis)
        print("  Running backtest...")
        t0 = time.time(); new_metrics = run_eval(); elapsed = time.time()-t0
        print(f"  Done in {elapsed:.1f}s")
        keep, reason = decide(current, new_metrics)
        new_sharpe = new_metrics.get("sharpe",0.0); delta = new_sharpe - current.get("sharpe",0.0)
        if keep:
            current = new_metrics; best_sharpe = max(best_sharpe, new_sharpe); kept_str="KEPT"; icon="✅"
            archive.add(t,new_sharpe,new_metrics.get("win_rate",0),new_metrics.get("max_drawdown",1),
                        new_metrics.get("trade_count",0),hypothesis,Path(HYPERAGENT_FILE).read_text(),Path(STRATEGY_FILE).read_text())
            archive.inc_children(parent["id"], compiled=True)
        else:
            git_revert(target); Path(HYPERAGENT_FILE).write_text(parent_ha); Path(STRATEGY_FILE).write_text(parent_strat)
            kept_str="DISCARDED"; icon="❌"; archive.inc_children(parent["id"], compiled=False)
        print(f"  {icon} {kept_str}: {current.get('sharpe',0):.4f}→{new_sharpe:.4f} ({delta:+.4f}) | {reason}")
        log_result({"iter":t,"timestamp":datetime.now(timezone.utc).isoformat(),"target":target,
                    "hypothesis":hypothesis[:60],"sharpe_before":round(current.get("sharpe",0),4) if kept_str=="DISCARDED" else round(current.get("sharpe",0)-delta,4),
                    "sharpe_after":round(new_sharpe,4),"delta":round(delta,4),"win_rate":new_metrics.get("win_rate"),
                    "max_dd":new_metrics.get("max_drawdown"),"trades":new_metrics.get("trade_count"),"kept":kept_str,"notes":reason})
        if t % 10 == 0:
            tg(f"*DGM-H Update — Iter {t}*\nBest: `{best_sharpe:.4f}` (base: `{baseline_sharpe:.4f}`)\nArchive: `{len(archive.agents)}`\nLast: `{icon} {delta:+.4f}`")
        time.sleep(1)

    total_kept = sum(1 for a in archive.agents if a.get("sharpe",0) > baseline_sharpe)
    print(f"\n{'═'*65}\n  COMPLETE: {t} iters | Baseline {baseline_sharpe:.4f} → Best {best_sharpe:.4f}\n  Archive: {len(archive.agents)} | Improved: {total_kept}\n{'═'*65}")
    tg(f"*DGM-H Complete*\nIters: `{t}` | Baseline→Best: `{baseline_sharpe:.4f}`→`{best_sharpe:.4f}`\nArchive: `{len(archive.agents)}`")

if __name__ == "__main__": main()
