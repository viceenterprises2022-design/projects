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
from rich.text import Text
from market_engine import MarketEngine

def make_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(
            Panel(Align.center("[yellow]Loading Macro & Correlation...[/]"), title="Macro Intelligence", border_style="magenta"),
            name="macro", size=8
        ),
        Layout(name="body")
    )
    layout["body"].split_row(
        Layout(
            Panel(Align.center("[yellow]Loading XAU Data...[/]"), title="XAU | Gold", border_style="yellow"),
            name="XAU", ratio=1
        ),
        Layout(
            Panel(Align.center("[yellow]Loading XAG Data...[/]"), title="XAG | Silver", border_style="white"),
            name="XAG", ratio=1
        )
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
        for key in ["DXY", "VIX", "GOLD", "SILVER", "OIL", "US30"]:
            if key in macro_data:
                mdata = macro_data[key]
                val = f"{mdata['current']:,.2f}"
                chg = mdata.get('change', 0)
                chg_color = "green" if chg >= 0 else "red"
                corr = correlations.get(key, 0)
                corr_color = "green" if corr > 0.5 else "red" if corr < -0.5 else "white"
                table.add_row(key, val, f"[{chg_color}]{chg:+.2f}%[/]", f"[{corr_color}]{corr:+.2f}[/]")
            
    return Panel(table, title="[bold]Macro Environment & Gold Correlation[/]", border_style="magenta")

def make_liquidation_map_table(liq_map):
    """Shows Buy Liquidity | Zone | Sell Liquidity depth."""
    table = Table(expand=True, box=None, padding=(0,0))
    table.add_column("BUY", justify="right", style="green", width=10)
    table.add_column("ZONE", justify="center", style="yellow", width=10)
    table.add_column("SELL", justify="left", style="red", width=10)
    
    if not liq_map:
        table.add_row("-", "-", "-")
        return table
        
    for price, buy, sell, total in liq_map:
        buy_str = f"${buy/1e6:,.1f}M" if buy > 1e5 else f"${buy/1e3:,.0f}K"
        sell_str = f"${sell/1e6:,.1f}M" if sell > 1e5 else f"${sell/1e3:,.0f}K"
        table.add_row(buy_str, f"{price:,.1f}", sell_str)
    return table

def render_metal_panel(symbol: str, data, engine) -> Panel:
    if not data or not data.get('binance'):
        return Panel(Align.center("[yellow]Loading...[/]"), title=f"[bold yellow]{symbol}[/]")

    binance = data['binance']
    depth = data.get('depth')
    liq_map = data.get('liq_map', [])
    
    # Binance data: [spot_klines, fut_klines]
    if not binance[0] or len(binance[0]) < 2:
        return Panel(Align.center("[red]No Price Data[/]"), title=f"[bold yellow]{symbol}[/]")
        
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
    
    # Create content layout
    content_layout = Layout()
    
    # Left: Technicals
    tech_table = Table(show_header=False, box=box.SIMPLE, expand=True, padding=(0, 0))
    tech_table.add_column("K", style="dim", width=12)
    tech_table.add_column("V", justify="right")
    tech_table.add_row("TREND", f"[{sig_color}]{trend_str}[/]")
    tech_table.add_row("RSI (14)", f"{rsi:.1f}")
    st_color = "green" if st_dir == 1 else "red"
    tech_table.add_row("SUPERTREND", f"[{st_color}]{'BUY' if st_dir == 1 else 'SELL'}[/]")
    vwap_color = "green" if vwap_dist > 0 else "red"
    tech_table.add_row("VWAP DIST", f"[{vwap_color}]{vwap_dist:+.2f}%[/]")
    
    if depth:
        tech_table.add_row("", "")
        tech_table.add_row("[cyan]BOOK SKEW[/]", f"{depth['skew']:+.2f}")
        for bid in depth['bids'][:1]:
            tech_table.add_row("SUPPORT", f"[green]{bid['p']:,.1f}[/]")
        for ask in depth['asks'][:1]:
            tech_table.add_row("RESISTANCE", f"[red]{ask['p']:,.1f}[/]")

    # Right: Depth Map
    map_table = make_liquidation_map_table(liq_map)
    
    # Stack Technicals and Depth Map vertically
    content_layout.split_column(
        Layout(tech_table, ratio=1),
        Layout(Panel(map_table, title="[dim]Depth Map[/]", border_style="dim"), ratio=2)
    )
    
    return Panel(content_layout, title=summary, border_style="yellow" if symbol == "XAU" else "white")

async def update_data(engine, layout, state):
    while True:
        try:
            data = await engine.fetch_all_data()
            state["macro"] = data["macro"]
            layout["macro"].update(render_macro(data["macro"], data["XAU"]["macro_corr"]))
            layout["XAU"].update(render_metal_panel("XAU", data["XAU"], engine))
            layout["XAG"].update(render_metal_panel("XAG", data["XAG"], engine))
        except Exception:
            pass
        await asyncio.sleep(30)

async def run_dashboard():
    console = Console()
    layout = make_layout()
    engine = MarketEngine(symbols=["XAU", "XAG"])
    
    state = {"macro": None}
    refresh_interval = 30
    
    # Fetch initial data before entering Live loop
    console.print("[yellow]Initializing data...[/]")
    try:
        data = await engine.fetch_all_data()
        state["macro"] = data["macro"]
        layout["macro"].update(render_macro(data["macro"], data["XAU"]["macro_corr"]))
        layout["XAU"].update(render_metal_panel("XAU", data["XAU"], engine))
        layout["XAG"].update(render_metal_panel("XAG", data["XAG"], engine))
    except Exception as e:
        console.print(f"[red]Initialization error: {e}[/]")
    
    # Start background task for updates
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

        pass
