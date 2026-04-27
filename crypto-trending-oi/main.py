import datetime
import asyncio
import sqlite3
from rich.console import Console
from rich.table import Table
from rich import box
from rich.layout import Layout
from rich.rule import Rule
from rich.panel import Panel

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

def identify_drivers(df, result):
    latest = df.iloc[-1]
    bullish = []
    bearish = []
    
    # Macro
    if latest['dxy_1d_pct_change'] < -0.3: bullish.append(f"DXY {latest['dxy_1d_pct_change']:.1f}% — macro tailwind")
    if latest['dxy_1d_pct_change'] > 0.5: bearish.append(f"DXY +{latest['dxy_1d_pct_change']:.1f}% — macro headwind")
    
    if latest['vix_level'] > 25: bearish.append(f"VIX {latest['vix_level']:.1f} — elevated fear/de-risking")
    elif latest['vix_level'] < 15: bullish.append(f"VIX {latest['vix_level']:.1f} — calm/complacency")
    
    if latest['global_m2_13w_change'] > 2.0: bullish.append(f"Global M2 +{latest['global_m2_13w_change']:.1f}% — liquidity expansion")
    
    # Onchain
    if latest['btc_etf_net_flow_7d'] > 200_000_000: bullish.append(f"ETF flows +${latest['btc_etf_net_flow_7d']/1e6:.0f}M (7d) — inst demand")
    elif latest['btc_etf_net_flow_7d'] < -100_000_000: bearish.append(f"ETF flows -${abs(latest['btc_etf_net_flow_7d'])/1e6:.0f}M (7d) — inst retreat")
    
    if latest['stablecoin_total_7d_change'] > 500_000_000: bullish.append(f"Stablecoin supply ↑ ${latest['stablecoin_total_7d_change']/1e9:.1f}B (7d) — dry powder")
    
    if latest['mvrv_z_score'] < 0: bullish.append(f"MVRV Z {latest['mvrv_z_score']:.2f} — deep value accumulation")
    elif latest['mvrv_z_score'] > 6: bearish.append(f"MVRV Z {latest['mvrv_z_score']:.2f} — overheating/top risk")
    
    # Intraday
    if latest['perp_funding_rate'] > 0.05: bearish.append(f"Funding rate +{latest['perp_funding_rate']:.3f}% — longs crowded")
    elif latest['perp_funding_rate'] < -0.01: bullish.append(f"Funding rate {latest['perp_funding_rate']:.3f}% — short squeeze fuel")
    
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

def print_oi_intelligence(df):
    latest = df.iloc[-1]
    console.print(Rule("[bold magenta]Market Intelligence - Option Chain Pulse[/bold magenta]", style="magenta"))
    
    c_oi = latest['btc_call_oi_total']
    p_oi = latest['btc_put_oi_total']
    pcr = p_oi / c_oi if c_oi > 0 else 0
    
    left = Table(box=None, show_header=False, padding=(0,1))
    left.add_column("k", style="dim", no_wrap=True)
    left.add_column("v", style="bold white", no_wrap=True)
    
    pcr_color = "green" if pcr >= 1.0 else "yellow" if pcr >= 0.7 else "red"
    pcr_label = "Bullish" if pcr >= 1.0 else "Neutral" if pcr >= 0.7 else "Bearish"
    
    left.add_row("Total Call OI", f"[green]{c_oi:,.0f} BTC[/green]")
    left.add_row("Total Put OI", f"[red]{p_oi:,.0f} BTC[/red]")
    left.add_row("Net PCR", f"[{pcr_color}]{pcr:.2f} ({pcr_label})[/{pcr_color}]")
    left.add_row("Funding Rate", f"{latest['perp_funding_rate']:.3f}% (8h)")
    left.add_row("Deribit Skew", f"{latest['deribit_25d_skew']:+.2f}%")
    
    console.print(Panel(left, border_style="magenta"))
    console.print("\n")

async def main():
    with console.status("[bold green]Fetching Async Crypto Factor Intelligence Data...[/bold green]", spinner="dots"):
        df_factors = await fetch_all_factors(use_mock=True)
        events = get_event_flags()
        result = run_engine(df_factors, events)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
    
    console.clear()
    print_trending_oi()
    print_oi_intelligence(df_factors)
    
    bullish_drivers, risk_flags = identify_drivers(df_factors, result)
    
    # Build Panel
    table = Table(box=None, show_header=False, padding=(0,2))
    table.add_column("Metric", style="bold cyan")
    table.add_column("Score", style="bold")
    
    table.add_row("MACRO REGIME SCORE:", format_score(result['mrs']))
    table.add_row("ON-CHAIN SCORE:", format_score(result['ocs']))
    table.add_row("INTRADAY MICRO SCORE:", format_score(result['ims']))
    table.add_row("COMPOSITE SIGNAL:", format_composite(result['composite']))
    
    drivers_str = ""
    if bullish_drivers:
        drivers_str = "\n".join([f"  {i+1}. {d}" for i, d in enumerate(bullish_drivers)])
    else:
        drivers_str = "  None"
        
    risks_str = ""
    if risk_flags:
        risks_str = "\n".join([f"  {i+1}. {r}" for i, r in enumerate(risk_flags)])
    else:
        risks_str = "  None"

    from rich.console import Group
    from rich.text import Text
    
    content_group = Group(
        table,
        Rule(style="dim"),
        Text("TOP BULLISH DRIVERS:\n", style="bold"),
        Text(f"{drivers_str}\n", style="green"),
        Rule(style="dim"),
        Text("TOP RISK FLAGS:\n", style="bold"),
        Text(f"{risks_str}\n", style="red"),
        Rule(style="dim"),
        Text(f"REGIME: ", style="bold").append(result['regime']).append("  |  ").append(f"CYCLE DAY: ", style="bold").append(f"{int(result['cycle_day'])} post-halving")
    )
    
    panel = Panel(
        content_group,
        title=f"[bold]ALPHAEDGE PRE-MARKET SIGNAL BRIEF  [{timestamp}][/bold]",
        border_style="cyan",
        padding=(1, 2)
    )
    
    console.print(panel)
    console.print("\n")

if __name__ == "__main__":
    asyncio.run(main())
