#!/usr/bin/env python3
import datetime
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.layout import Layout
from rich.rule import Rule

from fetchers import fetch_all_factors, get_event_flags
from engine import run_engine

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

def main():
    with console.status("[bold green]Fetching Crypto Factor Intelligence Data...[/bold green]", spinner="dots"):
        factors = fetch_all_factors(use_mock=True)
        events = get_event_flags()
        result = run_engine(factors, events)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
    
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
