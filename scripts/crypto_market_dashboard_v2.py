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
        Layout(name="macro", size=8),
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
    return Panel(
        Align.center(f"[bold cyan]AlphaEdge Crypto 2.0[/] | [white]{now}[/] | Sync: [bold yellow]{refresh_in}s[/]", vertical="middle"),
        style="blue",
        box=box.ROUNDED
    )

def render_macro(macro_data, correlations) -> Panel:
    table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE, expand=True, padding=(0, 1))
    table.add_column("IDX", justify="left", width=5)
    table.add_column("PRICE", justify="right")
    table.add_column("CHG", justify="right")
    table.add_column("CORR", justify="right")
    
    if not macro_data:
        table.add_row("...", "---", "---", "---")
    else:
        for key in ["DXY", "VIX", "US30", "GOLD", "OIL"]:
            if key in macro_data:
                mdata = macro_data[key]
                val = f"{mdata['current']:,.1f}"
                chg = mdata.get('change', 0)
                chg_color = "green" if chg >= 0 else "red"
                corr = correlations.get(key, 0)
                corr_color = "green" if corr > 0.5 else "red" if corr < -0.5 else "white"
                table.add_row(key, val, f"[{chg_color}]{chg:+.2f}%[/]", f"[{corr_color}]{corr:+.2f}[/]")
            
    return Panel(table, title="[bold]Macro & Corr[/]", border_style="magenta")

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
    summary = f"[bold yellow]{symbol}[/] | [white]{spot_close:,.1f}[/] ([{sig_color}]{change:+.1f}%[/])"
    
    table = Table(show_header=False, box=box.SIMPLE, expand=True, padding=(0, 0))
    table.add_column("K", style="dim", width=8)
    table.add_column("V", justify="right")
    
    # Technicals
    table.add_row("TREND", f"[{sig_color}]{trend_str[:12]}[/]")
    table.add_row("RSI", f"{rsi:.1f}")
    st_color = "green" if st_dir == 1 else "red"
    table.add_row("SUPERTREND", f"[{st_color}]{'BUY' if st_dir == 1 else 'SELL'}[/]")
    vwap_color = "green" if vwap_dist > 0 else "red"
    table.add_row("VWAP DIST", f"[{vwap_color}]{vwap_dist:+.1f}%[/]")
    
    table.add_row("", "") # Spacer
    
    # Options
    if options:
        table.add_row("[bold cyan]OPTIONS[/]", "")
        table.add_row("PCR O/V", f"{options['pcr']:.2f}/{options['vol_pcr']:.2f}")
        skew_color = "red" if options['oi_skew'] < -0.1 else "green" if options['oi_skew'] > 0.1 else "white"
        table.add_row("OI SKEW", f"[{skew_color}]{options['oi_skew']:+.2f}[/]")
        table.add_row("MAXPAIN", f"{options['max_oi']:,.0f}")
    
    table.add_row("", "") # Spacer
    
    # Whale Walls
    if depth:
        table.add_row("[bold cyan]ORDERBOOK[/]", "")
        book_skew = depth['skew']
        bs_color = "green" if book_skew > 0.1 else "red" if book_skew < -0.1 else "white"
        table.add_row("BK SKEW", f"[{bs_color}]{book_skew:+.2f}[/]")
        for bid in depth['bids'][:1]:
            table.add_row("BID", f"[green]{bid['p']:,.0f}[/] (${bid['v']/1e6:.1f}M)")
        for ask in depth['asks'][:1]:
            table.add_row("ASK", f"[red]{ask['p']:,.0f}[/] (${ask['v']/1e6:.1f}M)")
        if not depth['bids'] and not depth['asks']:
            table.add_row("WALLS", "[dim]None[/]")

    # CMC Perpetual & Macro Intelligence (BTC specific)
    if symbol == "BTC":
        import os
        import json
        
        # 1. Perp Intel
        perp_path = "scratch/perp_analysis_output.json"
        if os.path.exists(perp_path):
            try:
                with open(perp_path, "r") as f:
                    raw = json.load(f)
                text = raw["content"][0]["text"]
                cmc_data = json.loads(text)["result"]["data"]
                rep = cmc_data.get("decision_report", {})
                action = rep.get("action_guidance", {})
                
                bias = action.get("bias", "neutral").upper()
                bias_color = "green" if bias == "BULLISH" else "red" if bias == "BEARISH" else "yellow"
                
                table.add_row("", "") # Spacer
                table.add_row("[bold cyan]CMC PERP INTEL[/]", "")
                table.add_row("CMC BIAS", f"[{bias_color}]{bias}[/]")
                table.add_row("CMC SETUP", f"[white]{action.get('preferred_setup', 'N/A')[:18]}[/]")
            except:
                pass
                
        # 2. Macro Corr
        macro_path = "scratch/cross_asset_analysis_output.json"
        if os.path.exists(macro_path):
            try:
                with open(macro_path, "r") as f:
                    raw = json.load(f)
                text = raw["content"][0]["text"]
                res_data = json.loads(text)["result"]["data"]
                if "data" in res_data:
                    cmc_macro = res_data["data"]
                else:
                    cmc_macro = res_data
                rep = cmc_macro.get("decision_report", {})
                action = rep.get("action_guidance", {})
                
                table.add_row("", "") # Spacer
                table.add_row("[bold magenta]CMC MACRO CORR[/]", "")
                table.add_row("MACRO BIAS", f"[yellow]{action.get('bias', 'neutral').upper()}[/]")
                table.add_row("REGIME", f"[white]{rep.get('title', 'N/A')[:18]}[/]")
            except:
                pass

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
