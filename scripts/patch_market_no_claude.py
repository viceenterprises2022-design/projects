import sys

with open('market_analysis_v3.py', 'r') as f:
    lines = f.readlines()

out = []
for line in lines:
    if line.startswith('def gen_html'):
        break
    out.append(line)

new_code = """
# ── CLI INTERFACE ─────────────────────────────────────────────────────────────

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

def print_diagnostic_report(sym, quote, oi_raw, res, final_signal, final_score):
    console.clear()
    
    # 1. Header Panel
    ltp = quote.get("ltp", 0)
    chg = quote.get("change_pct", 0)
    chg_color = "green" if chg >= 0 else "red"
    
    pcr_detail = res.get("pcr", {}).get("detail", "")
    pcr_val = "N/A"
    if "Total PCR: " in pcr_detail:
        pcr_val = pcr_detail.split("Total PCR: ")[1]
        
    max_pain = "N/A"
    if oi_raw:
        max_pain = f"{oi_raw.get('max_pain', 0):,}"
    
    header_text = (
        f"[bold white]LTP:[/bold white] [{chg_color}]{ltp:,.2f} ({chg:+.2f}%)[/{chg_color}]  |  "
        f"[bold white]PCR:[/bold white] {pcr_val}  |  "
        f"[bold white]Max Pain:[/bold white] {max_pain}  |  "
        f"[bold white]Technical Signal:[/bold white] [bold cyan]{final_signal} ({final_score}/10)[/bold cyan]"
    )
    console.print(Panel(header_text, title=f"[bold yellow]AlphaEdge Diagnostics: {sym}[/bold yellow]", border_style="cyan"))
    
    # 2. Factor Table
    table = Table(box=box.SIMPLE, show_lines=True)
    table.add_column("Indicator", style="cyan", no_wrap=True)
    table.add_column("Status / Label", style="white")
    table.add_column("Detail", style="dim")
    table.add_column("Score", justify="right")

    indicator_names = {
        "trend": "1. Trend (EMA)",
        "dow_jones": "2. Dow Jones (US30)",
        "india_vix": "3. India VIX",
        "oi": "4. Open Interest",
        "vwap": "5. VWAP",
        "supertrend": "6. Supertrend",
        "rsi": "7. RSI (14)",
        "dxy": "8. US Dollar (DXY)",
        "crude": "9. Crude Oil (WTI)",
        "pcr": "10. Put-Call Ratio",
    }
    
    for key, name in indicator_names.items():
        if key not in res: continue
        data = res[key]
        
        score = data["score"]
        score_str = f"[green]+1[/green]" if score > 0 else f"[red]-1[/red]" if score < 0 else "[yellow] 0[/yellow]"
        
        table.add_row(name, data["label"], data["detail"], score_str)

    console.print(table)


def main():
    while True:
        console.clear()
        console.print("[bold cyan]======================================[/bold cyan]")
        console.print("[bold yellow] ALPHAEDGE DIAGNOSTICS (CLI)[/bold yellow]")
        console.print("[bold cyan]======================================[/bold cyan]")
        console.print("\\n[1] NIFTY 50")
        console.print("[2] BANKNIFTY")
        console.print("[3] SENSEX")
        console.print("[q] Quit\\n")
        
        choice = input("Select instrument to analyze: ").strip().lower()
        if choice == 'q':
            import sys
            sys.exit(0)
            
        sym_map = {"1": "NIFTY", "2": "BANKNIFTY", "3": "SENSEX"}
        if choice not in sym_map:
            continue
            
        sym = sym_map[choice]
        key = INSTRUMENTS.get(sym)
        oi_key = OI_INSTRUMENTS.get(sym)
        
        with console.status(f"[cyan]Fetching real-time data for {sym}...[/cyan]"):
            q = fetch_quote(key)
            if not q:
                console.print(f"[red]Failed to fetch Upstox quote for {sym}[/red]")
                time.sleep(2)
                continue
                
            c = fetch_candles(key)
            yc = fetch_yahoo({"NIFTY":"^NSEI", "SENSEX":"^BSESN", "BANKNIFTY":"^NSEBANK"}.get(sym, "^NSEI"))
            
            gd = {
                "US30": fetch_yahoo("^DJI", days=5),
                "VIX":  {"ltp": fetch_quote(INSTRUMENTS["INDIA_VIX"]).get("ltp", 15)} if fetch_quote(INSTRUMENTS["INDIA_VIX"]) else None,
                "DXY":  fetch_yahoo("DX-Y.NYB", days=5),
                "CRUDE":fetch_yahoo("CL=F", days=5)
            }
            if gd["VIX"]: gd["VIX"]["change_pct"] = 0 
                
            oi_raw = None
            if oi_key and q:
                oi_raw = build_oi_data(sym, q["ltp"])

        with console.status(f"[cyan]Running 10-factor engine for {sym}...[/cyan]"):
            a_res = analyze(sym, q, c, oi_raw, gd, yc)
            res = a_res["indicators"]
            final_score = a_res["score"]
            final_signal = a_res["signal"]

        print_diagnostic_report(sym, q, oi_raw, res, final_signal, final_score)
        
        try:
            input("\\nPress Enter to return to menu...")
        except EOFError:
            break

if __name__ == '__main__':
    main()
"""

with open('market_analysis_v3.py', 'w') as f:
    f.writelines(out)
    f.write(new_code)
