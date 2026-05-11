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

def render_header() -> Panel:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return Panel(
        Align.center(f"[bold cyan]AlphaEdge Crypto Diagnostic 2.0[/] | [white]{now}[/]", vertical="middle"),
        style="blue",
        box=box.ROUNDED
    )

def render_macro() -> Panel:
    table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE, expand=True)
    table.add_column("DXY", justify="center")
    table.add_column("VIX", justify="center")
    table.add_column("SPX", justify="center")
    table.add_column("CRUDE", justify="center")
    table.add_row("104.20", "14.50", "5120.30", "78.40")
    return Panel(table, title="[bold]Global Macro[/]", border_style="magenta")

def render_ticker(symbol: str) -> Panel:
    # Header: [SYM] | S: [price] | F: [price] ([change]%) | Sig: [NEUTRAL/BULL/BEAR] ([score]/10)
    summary = f"[bold yellow]{symbol}[/] | S: 65200 | F: 65150 (-0.05%) | Sig: [green]BULL[/] (7/10)"
    
    table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE, expand=True)
    table.add_column("INDICATOR", style="dim")
    table.add_column("VALUE", justify="right")
    table.add_row("TREND", "[green]UP[/]")
    table.add_row("RSI (14)", "58.2")
    table.add_row("SUPERTREND", "[green]BUY[/]")
    table.add_row("VWAP DIST", "+0.45%")
    
    return Panel(table, title=summary, border_style="cyan")

def main():
    console = Console()
    layout = make_layout()
    
    with Live(layout, console=console, screen=True, refresh_per_second=1) as live:
        try:
            while True:
                layout["header"].update(render_header())
                layout["macro"].update(render_macro())
                layout["BTC"].update(render_ticker("BTC"))
                layout["ETH"].update(render_ticker("ETH"))
                layout["SOL"].update(render_ticker("SOL"))
                time.sleep(1)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
