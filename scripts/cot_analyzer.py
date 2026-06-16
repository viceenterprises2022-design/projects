#!/usr/bin/env python3
"""
Commit of Traders (COT) Commodity and Index Positioning Analyzer
Sourced from CFTC Legacy Futures-Only Socrata dataset (6dca-aqww).
"""

import sys
import os
import argparse
import requests
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Add current directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

try:
    import send_telegram_msg as tg
except ImportError:
    tg = None

# Rich UI imports
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text

# Constants
CFTC_API_URL = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"
STATE_FILE = os.path.join(script_dir, "cot_analyzer_state.json")

# 8 target contracts to watch
CODES = {
    "Gold": "088691",
    "Silver": "084691",
    "Copper": "085692",
    "Oil": "067651",
    "SP500": "13874A",
    "Nasdaq": "209742",
    "Dow Jones": "124603",
    "UST Bond": "020601"
}

# Preserve exact ordering for visual presentation
ORDER = ["Gold", "Silver", "Copper", "Oil", "SP500", "Nasdaq", "Dow Jones", "UST Bond"]

code_to_name = {v: k for k, v in CODES.items()}

# HSL-based or vibrant styling constants
COLOR_BULL = "bold green"
COLOR_BEAR = "bold red"
COLOR_UP = "bold green"
COLOR_DOWN = "bold red"
COLOR_NEUTRAL = "grey70"

console = Console()

def load_state():
    """Load the state tracking file."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_sent_date": None}

def save_state(state):
    """Save the state tracking file."""
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        console.print(f"[yellow]Warning: Could not save state file: {e}[/yellow]")

def fetch_cot_data():
    """Fetch CFTC COT legacy futures-only records for target contracts."""
    codes_str = ", ".join([f"'{c}'" for c in CODES.values()])
    params = {
        "$where": f"cftc_contract_market_code in ({codes_str})",
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$limit": 150
    }
    
    r = requests.get(CFTC_API_URL, params=params)
    r.raise_for_status()
    return r.json()

def process_data(raw_data):
    """Process raw Socrata JSON records into structured dataframes."""
    # Group by code
    groups = {}
    for record in raw_data:
        code = record.get("cftc_contract_market_code")
        if code not in groups:
            groups[code] = []
        groups[code].append(record)
        
    rows = []
    report_date = None
    
    for name in ORDER:
        code = CODES[name]
        records = groups.get(code, [])
        if len(records) < 2:
            console.print(f"[yellow]Warning: Insufficient historical data for {name}[/yellow]")
            continue
            
        latest = records[0]
        prev = records[1]
        
        if not report_date:
            report_date = latest.get("report_date_as_yyyy_mm_dd")[:10]
            
        # Extract and parse numeric fields
        nc_long = int(float(latest.get("noncomm_positions_long_all", 0)))
        nc_short = int(float(latest.get("noncomm_positions_short_all", 0)))
        com_long = int(float(latest.get("comm_positions_long_all", 0)))
        com_short = int(float(latest.get("comm_positions_short_all", 0)))
        
        nc_net = nc_long - nc_short
        com_net = com_long - com_short
        divergence = nc_net - com_net
        
        nc_total = nc_long + nc_short
        nc_pct = int(round(nc_long / nc_total * 100)) if nc_total > 0 else 0
        
        com_total = com_long + com_short
        com_pct = int(round(com_long / com_total * 100)) if com_total > 0 else 0
        
        # Previous Week
        prev_nc_long = int(float(prev.get("noncomm_positions_long_all", 0)))
        prev_nc_short = int(float(prev.get("noncomm_positions_short_all", 0)))
        prev_com_long = int(float(prev.get("comm_positions_long_all", 0)))
        prev_com_short = int(float(prev.get("comm_positions_short_all", 0)))
        
        prev_nc_net = prev_nc_long - prev_nc_short
        prev_com_net = prev_com_long - prev_com_short
        prev_divergence = prev_nc_net - prev_com_net
        
        # WoW Changes
        div_change = divergence - prev_divergence
        div_pct_change = int(round(div_change / abs(prev_divergence) * 100)) if prev_divergence != 0 else 0
        
        signal = "Bullish" if nc_net > 0 else "Bearish"
        
        rows.append({
            "Contract": name,
            "NC Long": nc_long,
            "NC Short": nc_short,
            "NC Net": nc_net,
            "NC %Long": nc_pct,
            "Com Long": com_long,
            "Com Short": com_short,
            "Com Net": com_net,
            "Com %Long": com_pct,
            "Divergence": divergence,
            "Prev Divergence": prev_divergence,
            "Div Change": div_change,
            "Div %Chg": div_pct_change,
            "Signal": signal
        })
        
    return rows, report_date

def render_cli(rows, report_date):
    """Render a premium CLI terminal dashboard using Rich."""
    console.print()
    
    # 1. Main Title Header Panel
    title = Text("COMMITMENTS OF TRADERS (COT) WEEKLY INTELLIGENCE\n", style="bold cyan")
    subtitle = Text(f"Report Date: {report_date} | Sourced from CFTC Legacy Futures-Only\n\n", style="italic grey70")
    legend = Text(
        "Definitions:\n"
        "• Spec  = Non-Commercial (Hedge Funds, Banks & Institutions)\n"
        "• Hedg  = Commercial (Corporations Hedging)\n"
        "• WoW ± = Week-over-Week Change (Divergence net positioning shift)",
        style="dim white"
    )
    header_panel = Panel(
        Text.assemble(title, subtitle, legend),
        border_style="cyan",
        expand=True,
        padding=(1, 2)
    )
    console.print(header_panel)
    
    # 2. KPI Cards Row
    kpi_panels = []
    # We display a selection of top commodities + bonds + equities
    kpis_to_show = ["Gold", "Silver", "Oil", "SP500", "Nasdaq", "UST Bond"]
    for row in rows:
        name = row["Contract"]
        if name not in kpis_to_show:
            continue
            
        nc_net = row["NC Net"]
        pct_chg = row["Div %Chg"]
        signal = row["Signal"]
        
        # Color coding
        val_str = f"{nc_net/1000:+.1f}K"
        val_style = COLOR_BULL if nc_net > 0 else COLOR_BEAR
        
        chg_arrow = "▲" if pct_chg >= 0 else "▼"
        chg_str = f"{chg_arrow} {abs(pct_chg)}%"
        chg_style = COLOR_UP if pct_chg >= 0 else COLOR_DOWN
        
        sig_str = "BULL" if signal == "Bullish" else "BEAR"
        sig_style = "on green bold black" if signal == "Bullish" else "on red bold white"
        
        kpi_text = Text()
        kpi_text.append(f"{name}\n", style="bold white")
        kpi_text.append(f"{val_str}\n", style=val_style)
        kpi_text.append(f"{chg_str} WoW  ", style=chg_style)
        kpi_text.append(f" {sig_str} ", style=sig_style)
        
        kpi_panels.append(
            Panel(kpi_text, border_style="grey37", padding=(0, 1))
        )
        
    console.print(Columns(kpi_panels, expand=True))
    console.print()
    
    # 3. Main Data Table
    table = Table(
        title="Commitment of Traders — Detailed Positioning Matrix",
        title_style="bold underline cyan",
        expand=False,
        border_style="grey37",
        header_style="bold cyan"
    )
    
    table.add_column("Contract", style="bold white", width=11)
    table.add_column("Spec L", justify="right")
    table.add_column("Spec S", justify="right")
    table.add_column("Spec Net", justify="right")
    table.add_column("Spec %L", justify="right")
    table.add_column("Hedg L", justify="right")
    table.add_column("Hedg S", justify="right")
    table.add_column("Hedg Net", justify="right")
    table.add_column("Hedg %L", justify="right")
    table.add_column("Div Net", justify="right")
    table.add_column("Prev Div", justify="right")
    table.add_column("WoW ±", justify="right")
    table.add_column("% WoW", justify="right")
    table.add_column("Signal", justify="center")

    
    for row in rows:
        nc_net = row["NC Net"]
        com_net = row["Com Net"]
        div = row["Divergence"]
        p_div = row["Prev Divergence"]
        chg = row["Div Change"]
        pct = row["Div %Chg"]
        sig = row["Signal"]
        
        # Color mappings
        nc_net_str = f"{nc_net:+,.0f}"
        nc_net_style = COLOR_BULL if nc_net > 0 else COLOR_BEAR
        
        com_net_str = f"{com_net:+,.0f}"
        com_net_style = COLOR_BULL if com_net > 0 else COLOR_BEAR
        
        div_str = f"{div:+,.0f}"
        div_style = "bold cyan" if div > 0 else "bold magenta"
        
        chg_str = f"{chg:+,.0f}"
        chg_style = COLOR_UP if chg >= 0 else COLOR_DOWN
        
        pct_arrow = "▲" if pct >= 0 else "▼"
        pct_str = f"{pct_arrow} {abs(pct)}%"
        pct_style = COLOR_UP if pct >= 0 else COLOR_DOWN
        
        sig_str = f"[bold green]Bullish[/bold green]" if sig == "Bullish" else f"[bold red]Bearish[/bold red]"
        
        table.add_row(
            row["Contract"],
            f"{row['NC Long']:,}",
            f"{row['NC Short']:,}",
            f"[{nc_net_style}]{nc_net_str}[/{nc_net_style}]",
            f"{row['NC %Long']}%",
            f"{row['Com Long']:,}",
            f"{row['Com Short']:,}",
            f"[{com_net_style}]{com_net_str}[/{com_net_style}]",
            f"{row['Com %Long']}%",
            f"[{div_style}]{div_str}[/{div_style}]",
            f"{p_div:+,.0f}",
            f"[{chg_style}]{chg_str}[/{chg_style}]",
            f"[{pct_style}]{pct_str}[/{pct_style}]",
            sig_str
        )
        
    console.print(table)
    console.print()

def generate_ascii_table(rows):
    """Generate a clean ASCII text table for Telegram monospace formatting."""
    lines = [
        "Contract  | Spec Net  | WoW Net  | Signal  | % L",
        "----------+-----------+----------+---------+----"
    ]
    for row in rows:
        name = row["Contract"].upper().ljust(10)
        nc_net = f"{row['NC Net']/1000:+.1f}K".ljust(10)
        chg = f"{row['Div Change']/1000:+.1f}K".ljust(9)
        sig = ("BULLISH" if row["Signal"] == "Bullish" else "BEARISH").ljust(8)
        pct_l = f"{row['NC %Long']}%"
        lines.append(f"{name}| {nc_net}| {chg}| {sig}| {pct_l}")
    return "\n".join(lines)

def generate_markdown_table(rows):
    """Generate a GFM Markdown table for rich Telegram table rendering."""
    lines = [
        "| Contract | Spec Net | WoW Net | Signal | % L |",
        "| :--- | :---: | :---: | :---: | :---: |"
    ]
    for row in rows:
        name = f"**{row['Contract'].upper()}**"
        nc_net = f"`{row['NC Net']/1000:+.1f}K`"
        chg = f"`{row['Div Change']/1000:+.1f}K`"
        emoji = "🟢" if row["Signal"] == "Bullish" else "🔴"
        sig = f"{emoji} {row['Signal'].upper()}"
        pct_l = f"{row['NC %Long']}%"
        lines.append(f"| {name} | {nc_net} | {chg} | {sig} | {pct_l} |")
    return "\n".join(lines)

def get_ai_analysis(rows, report_date):
    """Generate professional analyst insights using Google Gemini API."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        console.print("[yellow]Warning: GEMINI_API_KEY missing from environment. Skipping AI analysis.[/yellow]")
        return "_AI Analysis unavailable (GEMINI_API_KEY not set)._"
        
    console.print("[cyan]Generating AI Analysis via Gemini...[/cyan]")
    
    # Prepare clean markdown representation of the data for prompt context
    headers = ["Contract", "NC Net", "Com Net", "Divergence", "WoW Change", "WoW % Chg", "Signal"]
    md_rows = []
    for r in rows:
        md_rows.append(f"| {r['Contract']} | {r['NC Net']:+,.0f} | {r['Com Net']:+,.0f} | {r['Divergence']:+,.0f} | {r['Div Change']:+,.0f} | {r['Div %Chg']}% | {r['Signal']} |")
    data_md = "| " + " | ".join(headers) + " |\n| " + " | ".join(["---"]*len(headers)) + " |\n" + "\n".join(md_rows)
    
    prompt = f"""You are a senior global macro hedge fund strategist and commodity portfolio manager.
Analyze this Commitments of Traders (COT) report for the week ending {report_date}:

{data_md}

Generate a high-impact, professional market intelligence summary for our trading desk.
Focus on:
1. Significant Speculator (Non-Commercial) Positioning Extremes (e.g., crowded longs/shorts, extreme percentages).
2. Large Weekly Shifts (aggressive long addition or short covering).
3. The Divergence Trend (NC Net vs Com Net) and what it signals about upcoming price action and supply/demand dynamics.
4. Specific sub-analyses:
   - Precious Metals (Gold, Silver, Copper)
   - Energy (WTI Crude Oil)
   - Equities (S&P 500, Nasdaq, Dow Jones)
   - Rates/Bonds (UST Bond)
5. Tactical takeaways (key reversal zones, trade confirmation signals, supply/demand interactions).

Keep the report extremely professional, structured, and concise. Avoid generic introductions or meta-commentary.
Use Telegram-compatible Markdown (V1/V2 style, like *bold*, _italic_, `inline code`) for beautiful structural formatting. Do NOT use HTML tags.
"""
    
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        analysis = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return analysis.strip()
    except Exception as e:
        console.print(f"[red]Error calling Gemini API: {e}[/red]")
        return f"_Error generating AI analysis: {e}_"

def send_telegram_report(rows, report_date, analysis):
    """Send the structured GFM table + AI analysis to Telegram."""
    if not tg:
        console.print("[red]Error: send_telegram_msg.py utility not found. Cannot send report.[/red]")
        return False
        
    table_str = generate_markdown_table(rows)
    
    message = f"📊 *CFTC Commitments of Traders (COT) Intelligence*\n"
    message += f"_Report Date: {report_date} (Futures-Only Legacy)_\n\n"
    message += f"{table_str}\n\n"
    message += f"🧠 *AI Positioning Analysis & Market Intel*\n\n"
    message += f"{analysis}"
    
    console.print("[cyan]Sending report to Telegram...[/cyan]")
    res = tg.send_text(message, mode="markdown")
    
    if res and res.get("ok"):
        console.print("[green]Report sent successfully to Telegram![/green]")
        return True
    else:
        console.print(f"[red]Failed to send Telegram message: {res.get('description', 'Unknown error')}[/red]")
        return False

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Commitments of Traders (COT) Commodity Positioning Intelligence")
    parser.add_argument("--send-telegram", action="store_true", help="Generate AI analysis and send to Telegram")
    parser.add_argument("--cron", action="store_true", help="Run in cron mode (checks if latest report date has already been processed)")
    parser.add_argument("--force", action="store_true", help="Force processing/sending even if already completed for the week")
    args = parser.parse_args()
    
    try:
        # 1. Fetch & process
        raw_data = fetch_cot_data()
        rows, report_date = process_data(raw_data)
        
        # 2. Render CLI Dashboard
        render_cli(rows, report_date)
        
        # 3. Check state for cron mode
        state = load_state()
        if args.cron and not args.force:
            if state.get("last_sent_date") == report_date:
                console.print(f"[green]Cron check: Report for {report_date} already sent. Skipping.[/green]")
                return
                
        # 4. Trigger Telegram alert with AI Analysis
        if args.send_telegram or args.cron:
            analysis = get_ai_analysis(rows, report_date)
            success = send_telegram_report(rows, report_date, analysis)
            
            if success:
                state["last_sent_date"] = report_date
                save_state(state)
                
    except Exception as e:
        console.print(f"[bold red]Execution failed: {e}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
