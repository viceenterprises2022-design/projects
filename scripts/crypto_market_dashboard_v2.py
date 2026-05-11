import time
from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich import box

def make_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="macro", size=5),
        Layout(name="body")
    )
    layout["body"].split_row(
        Layout(name="BTC"),
        Layout(name="ETH"),
        Layout(name="SOL")
    )
    return layout

def render_header(refresh_in: int) -> Panel:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return Panel(
        Align.center(f"[bold cyan]AlphaEdge Crypto Diagnostic 2.0[/] | [white]{now}[/] | Refresh in: [bold yellow]{refresh_in}s[/]", vertical="middle"),
        style="blue",
        box=box.ROUNDED
    )

def render_macro() -> Panel:
    table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE, expand=True)
    table.add_column("DXY", justify="center")
    table.add_column("VIX", justify="center")
    table.add_column("DOW_JONES", justify="center")
    table.add_column("CRUDE", justify="center")
    table.add_row("104.20", "14.50", "5120.30", "78.40")
    return Panel(table, title="[bold]Global Macro[/]", border_style="magenta")

def render_ticker(symbol: str) -> Panel:
    # Header: [SYM] | Spot: [price] | Fut: [price] ([change]%) | Sig: [NEUTRAL/BULL/BEAR] ([score]/10)
    data = {
        "BTC": {"spot": 98450.2, "fut": 98520.5, "chg": "+0.07", "sig": "[green]BULL[/]", "score": 8, "trend": "[green]UP[/]", "rsi": 62.5, "st": "[green]BUY[/]", "vwap": "+1.2%"},
        "ETH": {"spot": 2680.4, "fut": 2675.1, "chg": "-0.20", "sig": "[yellow]NEUTRAL[/]", "score": 5, "trend": "[yellow]SIDE[/]", "rsi": 48.2, "st": "[yellow]HOLD[/]", "vwap": "-0.1%"},
        "SOL": {"spot": 185.3, "fut": 186.1, "chg": "+0.43", "sig": "[green]BULL[/]", "score": 9, "trend": "[green]UP[/]", "rsi": 71.8, "st": "[green]BUY[/]", "vwap": "+2.5%"}
    }.get(symbol, {"spot": 0, "fut": 0, "chg": "0", "sig": "N/A", "score": 0, "trend": "N/A", "rsi": 0, "st": "N/A", "vwap": "0%"})

    summary = f"[bold yellow]{symbol}[/] | Spot: {data['spot']:,} | Fut: {data['fut']:,} ({data['chg']}%) | Sig: {data['sig']} ({data['score']}/10)"
    
    table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE, expand=True)
    table.add_column("INDICATOR", style="dim")
    table.add_column("VALUE", justify="right")
    table.add_row("TREND", data['trend'])
    table.add_row("RSI (14)", f"{data['rsi']:.1f}")
    table.add_row("SUPERTREND", data['st'])
    table.add_row("VWAP DIST", data['vwap'])
    
    return Panel(table, title=summary, border_style="cyan")

def main():
    console = Console()
    layout = make_layout()
    
    refresh_interval = 30
    counter = 0
    
    with Live(layout, console=console, screen=True, refresh_per_second=1) as live:
        try:
            while True:
                # Calculate countdown
                refresh_in = refresh_interval - (counter % refresh_interval)
                
                # Update header every second
                layout["header"].update(render_header(refresh_in))
                
                # Update data only every 30 seconds (or on first run)
                if counter % refresh_interval == 0:
                    layout["macro"].update(render_macro())
                    layout["BTC"].update(render_ticker("BTC"))
                    layout["ETH"].update(render_ticker("ETH"))
                    layout["SOL"].update(render_ticker("SOL"))
                
                time.sleep(1)
                counter += 1
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
