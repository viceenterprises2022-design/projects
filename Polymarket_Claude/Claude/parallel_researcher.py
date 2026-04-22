"""
parallel_researcher.py — Run N domain-specialist strategy variants concurrently.
Equivalent to Karpathy's multi-GPU factorial grid.

Usage:
    python parallel_researcher.py              # run all variants
    python parallel_researcher.py --promote    # auto-promote winner
    python parallel_researcher.py --list       # list variants
"""
import asyncio, copy, sys, tempfile, yaml, argparse, subprocess
from pathlib import Path

BASE = yaml.safe_load(Path("strategy.yaml").read_text()) if Path("strategy.yaml").exists() else {}

VARIANTS = {
    "baseline": BASE,
    "politics_specialist": {**copy.deepcopy(BASE),
        "whale_filters": {**BASE.get("whale_filters",{}), "consensus_threshold":2, "min_trade_size_usd":1000},
        "exit": {**BASE.get("exit",{}), "max_hold_days":60, "follow_whale_exit":True},
        "market_filters": {**BASE.get("market_filters",{}), "min_days_to_resolution":7, "max_days_to_resolution":90}},
    "crypto_specialist": {**copy.deepcopy(BASE),
        "risk": {**BASE.get("risk",{}), "stop_loss_pct":0.30, "take_profit_pct":1.50},
        "whale_filters": {**BASE.get("whale_filters",{}), "consensus_threshold":1, "min_trade_size_usd":200},
        "exit": {**BASE.get("exit",{}), "max_hold_days":7, "follow_whale_exit":False}},
    "sports_specialist": {**copy.deepcopy(BASE),
        "risk": {**BASE.get("risk",{}), "stop_loss_pct":0.40, "take_profit_pct":0.80},
        "exit": {**BASE.get("exit",{}), "max_hold_days":3, "follow_whale_exit":False},
        "market_filters": {**BASE.get("market_filters",{}), "min_days_to_resolution":1, "max_days_to_resolution":14}},
    "aggressive_tp": {**copy.deepcopy(BASE),
        "risk": {**BASE.get("risk",{}), "take_profit_pct":2.00, "stop_loss_pct":0.25},
        "position_sizing": {"mode":"tiered","fixed_amount_usd":25,"tiers":{"high":{"min_score":0.80,"amount_usd":75},"medium":{"min_score":0.60,"amount_usd":35},"low":{"min_score":0.00,"amount_usd":10}}}},
    "conservative": {**copy.deepcopy(BASE),
        "risk": {**BASE.get("risk",{}), "stop_loss_pct":0.25, "take_profit_pct":0.60},
        "whale_filters": {**BASE.get("whale_filters",{}), "consensus_threshold":3, "min_win_rate":0.65}},
}

async def eval_variant(name, cfg, sem):
    async with sem:
        print(f"  Starting: {name}")
        with tempfile.NamedTemporaryFile(mode="w",suffix=".yaml",prefix=f"v_{name}_",delete=False) as f:
            yaml.dump(cfg,f); tmp=f.name
        try:
            proc = await asyncio.create_subprocess_exec(sys.executable,"evaluate.py","--config",tmp,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            out,_ = await asyncio.wait_for(proc.communicate(), timeout=120)
            m = {"variant":name,"config":cfg}
            for line in out.decode().splitlines():
                if ":" in line:
                    k,_,v=line.partition(":"); k=k.strip(); v=v.strip()
                    try: m[k]=float(v)
                    except ValueError: pass
            if "sharpe" not in m: m["sharpe"]=0.0
        except Exception as e:
            m = {"variant":name,"sharpe":0.0,"error":str(e),"config":cfg}
        finally:
            Path(tmp).unlink(missing_ok=True)
        print(f"  Done: {name:<26} Sharpe={m.get('sharpe',0):.4f} WR={m.get('win_rate',0):.1%}")
        return m

async def run(variant_names=None, concurrent=4):
    variants = {k:v for k,v in VARIANTS.items() if not variant_names or k in variant_names}
    print(f"\n{'='*65}\n  PARALLEL COMPARISON | Variants: {list(variants.keys())}\n{'='*65}\n")
    sem = asyncio.Semaphore(concurrent)
    results = await asyncio.gather(*[eval_variant(n,c,sem) for n,c in variants.items()])
    ranked = sorted([r for r in results if "sharpe" in r], key=lambda x:x["sharpe"], reverse=True)
    print(f"\n  {'Rank':<5} {'Variant':<28} {'Sharpe':>8} {'WinRate':>8} {'MaxDD':>8}")
    print(f"  {'-'*60}")
    for i,r in enumerate(ranked,1):
        print(f"  {i:<5} {r['variant']:<28} {r.get('sharpe',0):>8.4f} {r.get('win_rate',0):>8.1%} {r.get('max_drawdown',0):>8.1%}")
    if ranked: print(f"\n  Winner: {ranked[0]['variant']} (Sharpe={ranked[0]['sharpe']:.4f})")
    return ranked

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--variants",type=str); parser.add_argument("--concurrent",type=int,default=4)
    parser.add_argument("--promote",action="store_true"); parser.add_argument("--list",action="store_true")
    args = parser.parse_args()
    if args.list: print("Variants:", list(VARIANTS.keys())); sys.exit(0)
    names = args.variants.split(",") if args.variants else None
    ranked = asyncio.run(run(names, args.concurrent))
    if args.promote and ranked:
        winner = ranked[0]
        Path("strategy.yaml").rename("strategy.yaml.pre_parallel_bak")
        yaml.dump(winner["config"], open("strategy.yaml","w"))
        subprocess.run(["git","add","strategy.yaml"])
        subprocess.run(["git","commit","-m",f"promote: {winner['variant']} sharpe={winner['sharpe']:.4f}"])
        print(f"\nPromoted {winner['variant']} to strategy.yaml")
