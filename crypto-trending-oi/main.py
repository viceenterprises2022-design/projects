#!/usr/bin/env python3
import datetime
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.layout import Layout
from rich.rule import Rule

from fetchers import fetch_all_factors, get_event_flags, generate_mock_oi_db
from engine import run_engine
import sqlite3
from rich.rule import Rule

console = Console()

def format_score(score):
    if score >= 0.5: return f"[bold green]+{score:.2f}  (STRONG BULLISH)[/bold green]"
    if score >= 0.15: return f"[green]+{score:.2f}  (BULLISH)[/green]"
    if score > -0.15: return f"[yellow]{score:+.2f}  (NEUTRAL)[/yellow]"
    if score > -0.5: return f"[red]{score:+.2f}  (BEARISH)[/red]"
    return f"[bold red]{score:+.2f}  (STRONG BEARISH)[/bold red]"

def format_composite(score):
    if score >= 0.4: return f"[bold green]+{score:.2f}  → LEAN LONG[/bold green]"
    if score <= -0.4: return f"[bold red]{score:+.2f}  → LEAN SHORT[/bold red]"
    return f"[yellow]{score:+.2f}  → CHOP / NEUTRAL[/yellow]"

def identify_drivers(f, result):
    bullish = []
    bearish = []
    
    # Macro
    if f['dxy_1d_pct_change'] < -0.3: bullish.append(f"DXY {f['dxy_1d_pct_change']:.1f}% — macro tailwind")
    if f['dxy_1d_pct_change'] > 0.5: bearish.append(f"DXY +{f['dxy_1d_pct_change']:.1f}% — macro headwind")
    
    if f['vix_level'] > 25: bearish.append(f"VIX {f['vix_level']:.1f} — elevated fear/de-risking")
    elif f['vix_level'] < 15: bullish.append(f"VIX {f['vix_level']:.1f} — calm/complacency")
    
    if f['global_m2_13w_change'] > 2.0: bullish.append(f"Global M2 +{f['global_m2_13w_change']:.1f}% — liquidity expansion")
    
    # Onchain
    if f['btc_etf_net_flow_7d'] > 200_000_000: bullish.append(f"ETF flows +${f['btc_etf_net_flow_7d']/1e6:.0f}M (7d) — inst demand")
    elif f['btc_etf_net_flow_7d'] < -100_000_000: bearish.append(f"ETF flows -${abs(f['btc_etf_net_flow_7d'])/1e6:.0f}M (7d) — inst retreat")
    
    if f['stablecoin_total_7d_change'] > 500_000_000: bullish.append(f"Stablecoin supply ↑ ${f['stablecoin_total_7d_change']/1e9:.1f}B (7d) — dry powder")
    
    if f['mvrv_z_score'] < 0: bullish.append(f"MVRV Z {f['mvrv_z_score']:.2f} — deep value accumulation")
    elif f['mvrv_z_score'] > 6: bearish.append(f"MVRV Z {f['mvrv_z_score']:.2f} — overheating/top risk")
    
    # Intraday
    if f['perp_funding_rate'] > 0.05: bearish.append(f"Funding rate +{f['perp_funding_rate']:.3f}% — longs crowded")
    elif f['perp_funding_rate'] < -0.01: bullish.append(f"Funding rate {f['perp_funding_rate']:.3f}% — short squeeze fuel")
    
    return bullish[:3], bearish[:3]

def print_trending_oi():
    try:
        conn = sqlite3.connect("crypto_intraday_oi.db")
        c = conn.cursor()
        c.execute("SELECT timestamp, ltp, call_oi, put_oi FROM trending_oi ORDER BY timestamp ASC")
        rows = c.fetchall()
        conn.close()
    except Exception:
        return
        
    if not rows:
        return
        
    console.print(Rule("[bold cyan]Trending OI (Intraday Pulse) - BTC[/bold cyan]", style="cyan"))
    
    t_table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold dim")
    t_table.add_column("Time", justify="left", no_wrap=True)
    t_table.add_column("LTP", justify="right", no_wrap=True)
    t_table.add_column("Call OI (BTC)", justify="right", style="green", no_wrap=True)
    t_table.add_column("Put OI (BTC)", justify="right", style="red", no_wrap=True)
    t_table.add_column("Diff in OI", justify="right", style="bold", no_wrap=True)
    t_table.add_column("Dir.", justify="center", no_wrap=True)
    t_table.add_column("Net PCR", justify="right", no_wrap=True)
    t_table.add_column("Sentiment", justify="center", no_wrap=True)
    
    prev_diff = None
    
    display_rows = []
    
    for r in rows:
        ts_str, ltp, c_oi, p_oi = r
        time_str = ts_str.split(" ")[1][:5]
        
        diff = p_oi - c_oi
        pcr = p_oi / c_oi if c_oi > 0 else 0
        chng_dir = diff - prev_diff if prev_diff is not None else 0
        
        dir_char = "[green]↑[/green]" if chng_dir > 0 else "[red]↓[/red]" if chng_dir < 0 else "—"
        sent = "[bold green]Bullish[/bold green]" if (diff > 0 and chng_dir >= 0) else \
               "[bold red]Bearish[/bold red]" if (diff < 0 and chng_dir <= 0) else \
               "[yellow]Neutral[/yellow]"
               
        diff_str = f"{diff:,.0f}"
        
        display_rows.insert(0, (
            time_str, f"{ltp:,.2f}", f"{c_oi:,.0f}", f"{p_oi:,.0f}", 
            diff_str, dir_char, f"{pcr:.2f}", sent
        ))
        
        prev_diff = diff
        
    for dr in display_rows:
        t_table.add_row(*dr)
        
    console.print(t_table)
    console.print("\n")

def print_oi_intelligence(f):
    console.print(Rule("[bold magenta]Market Intelligence - Option Chain Pulse[/bold magenta]", style="magenta"))
    
    c_oi = f['btc_call_oi_total']
    p_oi = f['btc_put_oi_total']
    pcr = p_oi / c_oi if c_oi > 0 else 0
    
    left = Table(box=None, show_header=False, padding=(0,1))
    left.add_column("k", style="dim", no_wrap=True)
    left.add_column("v", style="bold white", no_wrap=True)
    
    pcr_color = "green" if pcr >= 1.0 else "yellow" if pcr >= 0.7 else "red"
    pcr_label = "Bullish" if pcr >= 1.0 else "Neutral" if pcr >= 0.7 else "Bearish"
    
    left.add_row("Total Call OI", f"[green]{c_oi:,.0f} BTC[/green]")
    left.add_row("Total Put OI", f"[red]{p_oi:,.0f} BTC[/red]")
    left.add_row("Net PCR", f"[{pcr_color}]{pcr:.2f} ({pcr_label})[/{pcr_color}]")
    left.add_row("Funding Rate", f"{f['perp_funding_rate']:.3f}% (8h)")
    left.add_row("Deribit Skew", f"{f['deribit_25d_skew']:+.2f}%")
    
    console.print(Panel(left, border_style="magenta"))
    console.print("\n")

def main():
    with console.status("[bold green]Fetching Crypto Factor Intelligence Data...[/bold green]", spinner="dots"):
        generate_mock_oi_db()
        factors = fetch_all_factors(use_mock=True)
        events = get_event_flags()
        result = run_engine(factors, events)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
    
    console.clear()
    print_trending_oi()
    print_oi_intelligence(factors)
    
    bullish_drivers, risk_flags = identify_drivers(factors, result)
    
    # Build Panel
    output = f"""
[bold cyan]MACRO REGIME SCORE:[/bold cyan]        {format_score(result['mrs'])}
[bold cyan]ON-CHAIN SCORE:[/bold cyan]            {format_score(result['ocs'])}
[bold cyan]INTRADAY MICRO SCORE:[/bold cyan]      {format_score(result['ims'])}
[bold cyan]COMPOSITE SIGNAL:[/bold cyan]          {format_composite(result['composite'])}
"""
    
    table_bullish = Table(box=box.SIMPLE, show_header=False, pad_edge=False)
    for i, d in enumerate(bullish_drivers, 1):
        table_bullish.add_row(f"  [green]{i}. {d}[/green]")
    if not bullish_drivers: table_bullish.add_row("  [dim]None[/dim]")
    
    table_bearish = Table(box=box.SIMPLE, show_header=False, pad_edge=False)
    for i, d in enumerate(risk_flags, 1):
        table_bearish.add_row(f"  [red]{i}. {d}[/red]")
    if not risk_flags: table_bearish.add_row("  [dim]None[/dim]")

    # Compose final display using tables to mimic the requested UI
    
    grid = Table.grid(expand=True)
    grid.add_column()
    
    grid.add_row(output)
    grid.add_row(Rule(style="dim"))
    grid.add_row("[bold]TOP BULLISH DRIVERS:[/bold]")
    grid.add_row(table_bullish)
    grid.add_row(Rule(style="dim"))
    grid.add_row("[bold]TOP RISK FLAGS:[/bold]")
    grid.add_row(table_bearish)
    grid.add_row(Rule(style="dim"))
    
    regime_str = f"[bold white]REGIME:[/bold white] {result['regime']}  |  [bold white]CYCLE DAY:[/bold white] {result['cycle_day']} post-halving"
    grid.add_row(regime_str)
    
    panel = Panel(
        grid,
        title=f"[bold]ALPHAEDGE PRE-MARKET SIGNAL BRIEF  [{timestamp}][/bold]",
        border_style="cyan",
        padding=(1, 2)
    )
    
    console.print("\n")
    console.print(panel)
    console.print("\n")

if __name__ == "__main__":
    main()
