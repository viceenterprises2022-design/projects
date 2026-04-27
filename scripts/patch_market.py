import sys

with open('market_analysis_v3.py', 'r') as f:
    lines = f.readlines()

out = []
for line in lines:
    if line.startswith('def gen_html'):
        break
    out.append(line)

new_code = """# ── CLAUDE AI INTEGRATION ─────────────────────────────────────────────────────

def call_claude_for_diagnostics(sym, quote, res, final_signal, final_score):
    \"\"\"Pass the 10-factor technical breakdown to Claude for a targeted diagnostic.\"\"\"
    
    # Build a textual representation of the 10 factors
    factors_text = f"Instrument: {sym}\\n"
    factors_text += f"Price: {quote.get('ltp', 0):.2f} (Change: {quote.get('change_pct', 0):+.2f}%)\\n"
    factors_text += f"Technical Signal: {final_signal} ({final_score}/10)\\n\\n"
    factors_text += "10-Factor Breakdown:\\n"
    
    for key, val in res.items():
        factors_text += f"- {key.upper()}: {val['label']} | Score: {val['score']} | Detail: {val['detail']}\\n"
        
    prompt = f\"\"\"You are a professional quantitative analyst. 
Review the following 10-factor technical analysis for {sym}.

DATA:
{factors_text}

Provide a concise, sharp diagnostic summary. Focus on EXACTLY how these specific signals (e.g., VWAP, OI, VIX, Trend, PCR) interact to form the current picture.
Return your response as a valid JSON object with EXACTLY these fields (no markdown, no preamble):
- "bias": "Bullish" | "Bearish" | "Neutral"
- "summary": 2-3 sentences synthesizing the 10 factors into a cohesive market narrative.
- "key_level": A single price level to watch (number as string).
- "outlook": 1 forward-looking sentence based on the data.
- "risk_note": 1 caution note.
\"\"\"

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": prompt}],
    }
    
    try:
        import requests, json
        r = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=20)
        r.raise_for_status()
        raw = r.json()["content"][0]["text"].strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        return {
            "bias": "Error",
            "summary": f"Could not fetch AI analysis: {e}",
            "key_level": "N/A",
            "outlook": "N/A",
            "risk_note": "N/A"
        }

# ── CLI INTERFACE ─────────────────────────────────────────────────────────────

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

def print_diagnostic_report(sym, quote, oi_raw, res, final_signal, final_score, ai_analysis):
    console.clear()
    
    # 1. Header Panel
    ltp = quote.get("ltp", 0)
    chg = quote.get("change_pct", 0)
    chg_color = "green" if chg >= 0 else "red"
    
    pcr = res.get("pcr", {}).get("detail", "").replace("Ratio: ", "")
    max_pain = "N/A"
    if oi_raw:
        max_pain = f"{oi_raw.get('max_pain', 0):,}"
    
    header_text = (
        f"[bold white]LTP:[/bold white] [{chg_color}]{ltp:,.2f} ({chg:+.2f}%)[/{chg_color}]  |  "
        f"[bold white]PCR:[/bold white] {pcr}  |  "
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
    
    # 3. AI Analysis Panel
    ai_text = (
        f"[bold white]Bias:[/bold white] {ai_analysis.get('bias', 'N/A')}\\n\\n"
        f"[bold white]Synthesis:[/bold white] {ai_analysis.get('summary', 'N/A')}\\n\\n"
        f"[bold white]Key Level:[/bold white] [cyan]{ai_analysis.get('key_level', 'N/A')}[/cyan]\\n"
        f"[bold white]Outlook:[/bold white] {ai_analysis.get('outlook', 'N/A')}\\n"
        f"[bold red]Risk:[/bold red] {ai_analysis.get('risk_note', 'N/A')}"
    )
    console.print(Panel(ai_text, title="[bold purple]Claude AI Narrative[/bold purple]", border_style="purple"))

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
            if oi_key:
                exps = fetch_expiries(oi_key)
                if exps:
                    ch_data = fetch_option_chain(oi_key, exps[0])
                    if ch_data and q:
                        oi_raw = build_oi_data(ch_data, q["ltp"])

        with console.status(f"[cyan]Running 10-factor engine for {sym}...[/cyan]"):
            res, final_score, final_signal = analyze(sym, q, c, oi_raw, gd, yc)

        with console.status(f"[purple]Generating Claude AI narrative...[/purple]"):
            ai_analysis = call_claude_for_diagnostics(sym, q, res, final_signal, final_score)
            
        print_diagnostic_report(sym, q, oi_raw, res, final_signal, final_score, ai_analysis)
        
        input("\\nPress Enter to return to menu...")

if __name__ == '__main__':
    main()
"""

with open('market_analysis_v3.py', 'w') as f:
    f.writelines(out)
    f.write(new_code)
