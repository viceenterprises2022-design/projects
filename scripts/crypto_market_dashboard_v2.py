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
        Layout(name="BTC"),
        Layout(name="ETH"),
        Layout(name="SOL")
    )
    return layout

def render_header(refresh_in: int, macro_data: dict = None) -> Panel:
    now = datetime.now().strftime("%H:%M:%S")
    ticker = ""
    if macro_data:
        parts = []
        for key in ["DXY", "VIX"]:
            if key in macro_data:
                val = macro_data[key]['current']
                parts.append(f"{key}: [bold cyan]{val:,.1f}[/]")
        ticker = " | ".join(parts)
        ticker = f" | {ticker}"

    return Panel(
        Align.center(f"[bold cyan]AlphaEdge Crypto 2.0[/] | [white]{now}[/]{ticker} | Refresh: [bold yellow]{refresh_in}s[/]", vertical="middle"),
        style="blue",
        box=box.ROUNDED
    )

def render_macro(macro_data, correlations) -> Panel:
    table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE, expand=True)
    table.add_column("INDEX", justify="left")
    table.add_column("VALUE", justify="right")
    table.add_column("CORR (BTC)", justify="right")
    
    if not macro_data:
        table.add_row("Loading...", "---", "---")
    else:
        for key, mdata in macro_data.items():
            val = f"{mdata['current']:,.2f}"
            corr = correlations.get(key, 0)
            color = "green" if corr > 0.5 else "red" if corr < -0.5 else "white"
            table.add_row(key, val, f"[{color}]{corr:+.2f}[/]")
            
    return Panel(table, title="[bold]Global Macro & Correlations[/]", border_style="magenta")

def render_ticker(symbol: str, data, engine) -> Panel:
    if not data or not data.get('binance'):
        return Panel(Align.center("[yellow]Loading...[/]"), title=f"[bold yellow]{symbol}[/]")

    binance = data['binance']
    options = data.get('options')
    depth = data.get('depth')
    
    # Binance data: [spot_klines, fut_klines]
    spot_close = float(binance[0][-1][4])
    fut_close = float(binance[1][0][4])
    change = ((spot_close - float(binance[0][-2][4])) / float(binance[0][-2][4])) * 100
    
    # Analyze trend
    trend_str, trend_score, trend_det = engine.analyze_trend(binance[0])
    rsi = engine.calculate_rsi([float(x[4]) for x in binance[0]])
    st_val, st_dir = engine.calculate_supertrend(binance[0])
    vwap = engine.calculate_vwap(binance[0])
    vwap_dist = ((spot_close - vwap) / vwap) * 100 if vwap else 0

    sig_color = "green" if trend_score > 0 else "red" if trend_score < 0 else "yellow"
    summary = f"[bold yellow]{symbol}[/] | Spot: [white]{spot_close:,.2f}[/] | Fut: [dim]{fut_close:,.2f}[/] ([{sig_color}]{change:+.2f}%[/])"
    
    table = Table(show_header=False, box=box.SIMPLE, expand=True)
    table.add_column("K", style="dim")
    table.add_column("V", justify="right")
    
    # Technicals
    table.add_row("TREND", f"[{sig_color}]{trend_str}[/]")
    table.add_row("RSI", f"{rsi:.1f}")
    st_color = "green" if st_dir == 1 else "red"
    table.add_row("SUPERTREND", f"[{st_color}]{'BUY' if st_dir == 1 else 'SELL'}[/]")
    vwap_color = "green" if vwap_dist > 0 else "red"
    table.add_row("VWAP DIST", f"[{vwap_color}]{vwap_dist:+.2f}%[/]")
    
    table.add_row("", "") # Spacer
    
    # Options
    if options:
        table.add_row("[bold cyan]OPTIONS (DERIBIT)[/]", "")
        table.add_row("PCR (OI/VOL)", f"{options['pcr']:.2f} / {options['vol_pcr']:.2f}")
        skew_color = "red" if options['oi_skew'] < -0.1 else "green" if options['oi_skew'] > 0.1 else "white"
        table.add_row("OI SKEW", f"[{skew_color}]{options['oi_skew']:+.2f}[/]")
        table.add_row("MAX PAIN", f"{options['max_oi']:,.0f}")
    
    table.add_row("", "") # Spacer
    
    # Whale Walls
    if depth:
        table.add_row("[bold cyan]ORDER BOOK (1%)[/]", "")
        book_skew = depth['skew']
        bs_color = "green" if book_skew > 0.1 else "red" if book_skew < -0.1 else "white"
        table.add_row("BOOK SKEW", f"[{bs_color}]{book_skew:+.2f}[/]")
        for bid in depth['bids'][:1]:
            table.add_row("WHALE BID", f"[green]{bid['p']:,.0f}[/] (${bid['v']/1e6:.1f}M)")
        for ask in depth['asks'][:1]:
            table.add_row("WHALE ASK", f"[red]{ask['p']:,.0f}[/] (${ask['v']/1e6:.1f}M)")
        if not depth['bids'] and not depth['asks']:
            table.add_row("WALLS", "[dim]None >$1M[/]")

    return Panel(table, title=summary, border_style="cyan")

async def update_data(engine, layout, state):
    while True:
        try:
            data = await engine.fetch_all_data()
            state["macro"] = data["macro"]
            layout["macro"].update(render_macro(data["macro"], data["BTC"]["macro_corr"]))
            layout["BTC"].update(render_ticker("BTC", data["BTC"], engine))
            layout["ETH"].update(render_ticker("ETH", data["ETH"], engine))
            layout["SOL"].update(render_ticker("SOL", data["SOL"], engine))
        except Exception as e:
            print(f"Update error: {e}")
        await asyncio.sleep(30)

async def run_dashboard():
    console = Console()
    layout = make_layout()
    engine = MarketEngine(symbols=["BTC", "ETH", "SOL"])
    
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
