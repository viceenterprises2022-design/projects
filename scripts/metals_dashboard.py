import asyncio
import time
from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich import box
from market_engine import MarketEngine

def make_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="macro", size=7),
        Layout(name="body")
    )
    layout["body"].split_row(
        Layout(name="XAU", ratio=2),
        Layout(name="XAG", ratio=1)
    )
    return layout

def render_header(refresh_in: int, macro_data: dict = None) -> Panel:
    now = datetime.now().strftime("%H:%M:%S")
    return Panel(
        Align.center(f"[bold yellow]AlphaEdge Metals Intelligence[/] | [white]{now}[/] | Sync: [bold cyan]{refresh_in}s[/]", vertical="middle"),
        style="yellow",
        box=box.ROUNDED
    )

def render_macro(macro_data, correlations) -> Panel:
    table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE, expand=True, padding=(0, 1))
    table.add_column("IDX", justify="left", width=10)
    table.add_column("PRICE", justify="right")
    table.add_column("CHG", justify="right")
    table.add_column("CORR (XAU)", justify="right")
    
    if not macro_data:
        table.add_row("...", "---", "---", "---")
    else:
        # Focus on relevant macros for metals
        for key in ["DXY", "VIX", "GOLD", "SILVER", "US30"]:
            if key in macro_data:
                mdata = macro_data[key]
                val = f"{mdata['current']:,.2f}"
                chg = mdata.get('change', 0)
                chg_color = "green" if chg >= 0 else "red"
                corr = correlations.get(key, 0)
                corr_color = "green" if corr > 0.5 else "red" if corr < -0.5 else "white"
                table.add_row(key, val, f"[{chg_color}]{chg:+.2f}%[/]", f"[{corr_color}]{corr:+.2f}[/]")
            
    return Panel(table, title="[bold]Macro Environment & Gold Correlation[/]", border_style="magenta")

def render_metal_panel(symbol: str, data, engine, detailed: bool = True) -> Panel:
    if not data or not data.get('binance'):
        return Panel(Align.center("[yellow]Loading...[/]"), title=f"[bold yellow]{symbol}[/]")

    binance = data['binance']
    depth = data.get('depth')
    
    # Binance data: [spot_klines, fut_klines]
    # Metals on Binance are usually USDT pairs, check MarketEngine for exact logic if needed
    # spot_klines[-1][4] is close
    spot_close = float(binance[0][-1][4])
    change = ((spot_close - float(binance[0][-2][4])) / float(binance[0][-2][4])) * 100
    
    # Analyze trend
    trend_str, trend_score, trend_det = engine.analyze_trend(binance[0])
    rsi = engine.calculate_rsi([float(x[4]) for x in binance[0]])
    st_val, st_dir = engine.calculate_supertrend(binance[0])
    vwap = engine.calculate_vwap(binance[0])
    vwap_dist = ((spot_close - vwap) / vwap) * 100 if vwap else 0

    sig_color = "green" if trend_score > 0 else "red" if trend_score < 0 else "yellow"
    summary = f"[bold yellow]{symbol}[/] | [white]{spot_close:,.2f}[/] ([{sig_color}]{change:+.2f}%[/])"
    
    table = Table(show_header=False, box=box.SIMPLE, expand=True, padding=(0, 0))
    table.add_column("K", style="dim", width=12)
    table.add_column("V", justify="right")
    
    # Technicals
    table.add_row("TREND", f"[{sig_color}]{trend_str}[/]")
    table.add_row("RSI (14)", f"{rsi:.1f}")
    st_color = "green" if st_dir == 1 else "red"
    table.add_row("SUPERTREND", f"[{st_color}]{'BUY' if st_dir == 1 else 'SELL'}[/]")
    vwap_color = "green" if vwap_dist > 0 else "red"
    table.add_row("VWAP DIST", f"[{vwap_color}]{vwap_dist:+.2f}%[/]")
    
    if detailed and depth:
        table.add_row("", "") # Spacer
        table.add_row("[bold cyan]ORDERBOOK (Whales)[/]", "")
        book_skew = depth['skew']
        bs_color = "green" if book_skew > 0.1 else "red" if book_skew < -0.1 else "white"
        table.add_row("BOOK SKEW", f"[{bs_color}]{book_skew:+.2f}[/]")
        
        # Filter walls for better display
        whale_bids = depth['bids'][:2]
        whale_asks = depth['asks'][:2]
        
        for bid in whale_bids:
            table.add_row("SUPPORT", f"[green]{bid['p']:,.2f}[/] (${bid['v']/1e6:.1f}M)")
        for ask in whale_asks:
            table.add_row("RESISTANCE", f"[red]{ask['p']:,.2f}[/] (${ask['v']/1e6:.1f}M)")
            
        if not whale_bids and not whale_asks:
            table.add_row("WALLS", "[dim]None > $500k[/]")

    return Panel(table, title=summary, border_style="yellow" if symbol == "XAU" else "white")

async def update_data(engine, layout, state):
    while True:
        try:
            data = await engine.fetch_all_data()
            state["macro"] = data["macro"]
            # XAU correlations are in data["XAU"]["macro_corr"]
            layout["macro"].update(render_macro(data["macro"], data["XAU"]["macro_corr"]))
            layout["XAU"].update(render_metal_panel("XAU", data["XAU"], engine, detailed=True))
            layout["XAG"].update(render_metal_panel("XAG", data["XAG"], engine, detailed=False))
        except Exception as e:
            # layout["header"].update(Panel(f"[red]Error: {e}[/]"))
            pass
        await asyncio.sleep(30)

async def run_dashboard():
    console = Console()
    layout = make_layout()
    # MarketEngine symbols for metals
    engine = MarketEngine(symbols=["XAU", "XAG"])
    
    state = {"macro": None}
    refresh_interval = 30
    
    # Start background data update
    asyncio.create_task(update_data(engine, layout, state))
    
    with Live(layout, console=console, screen=True, refresh_per_second=1) as live:
        counter = 0
        while True:
            refresh_in = refresh_interval - (counter % refresh_interval)
            layout["header"].update(render_header(refresh_in, state["macro"]))
            await asyncio.sleep(1)
            counter += 1

if __name__ == "__main__":
    try:
        asyncio.run(run_dashboard())
    except KeyboardInterrupt:
        pass
