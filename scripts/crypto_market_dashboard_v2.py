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
        Layout(name="macro", size=9),
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
    import os
    import json
    
    # 1. Standard Macro Table
    macro_table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE, expand=True, padding=(0, 1))
    macro_table.add_column("IDX", justify="left", width=6)
    macro_table.add_column("PRICE", justify="right")
    macro_table.add_column("CHG", justify="right")
    macro_table.add_column("CORR", justify="right")
    
    for key in ["DXY", "VIX", "US30", "GOLD", "OIL"]:
        if macro_data and key in macro_data:
            mdata = macro_data[key]
            val = f"{mdata['current']:,.1f}"
            chg = mdata.get('change', 0)
            chg_color = "green" if chg >= 0 else "red"
            corr = correlations.get(key, 0) if correlations else 0
            corr_color = "green" if corr > 0.5 else "red" if corr < -0.5 else "white"
            macro_table.add_row(key, val, f"[{chg_color}]{chg:+.2f}%[/]", f"[{corr_color}]{corr:+.2f}[/]")
        else:
            macro_table.add_row(key, "---", "---", "---")
                
    # 2. CMC Daily Sentiment Stance Table
    cmc_table = Table(show_header=False, box=None, expand=True, padding=(0,1))
    cmc_table.add_column("Label", style="bold cyan", width=14)
    cmc_table.add_column("Value", style="white")
    
    cmc_path = "scratch/market_overview_analysis_output.json"
    has_cmc = False
    if os.path.exists(cmc_path):
        try:
            with open(cmc_path, "r") as f:
                raw = json.load(f)
            text = raw["content"][0]["text"]
            cmc_data = json.loads(text)["result"]["data"]
            rep = cmc_data.get("decision_report", {})
            assessment = cmc_data.get("trader_assessment", {})
            action = cmc_data.get("action_guidance", {})
            
            regime = assessment.get("market_regime", "N/A").upper()
            bias = assessment.get("risk_bias", "N/A").upper()
            stance = action.get("bias", "N/A").upper()
            
            bias_color = "red" if "bear" in bias.lower() or "defensive" in bias.lower() else "green" if "bull" in bias.lower() else "yellow"
            
            cmc_table.add_row("CMC REGIME", f"[red]{regime[:15]}[/]")
            cmc_table.add_row("RISK BIAS", f"[{bias_color}]{bias[:18]}[/]")
            cmc_table.add_row("CMC STANCE", f"[bold white]{stance[:18]}[/]")
            
            # Load ETF demand context
            etf_path = "scratch/etf_demand_analysis_output.json"
            if os.path.exists(etf_path):
                try:
                    with open(etf_path, "r") as f_etf:
                        raw_etf = json.load(f_etf)
                    text_etf = raw_etf["content"][0]["text"]
                    etf_data = json.loads(text_etf)["result"]["data"]
                    etf_bias = etf_data.get("decision_report", {}).get("action_guidance", {}).get("bias", "N/A").upper()
                    cmc_table.add_row("ETF DEMAND", f"[bold yellow]{etf_bias[:15]}[/]")
                except:
                    pass

            # Load Macro News context
            news_path = "scratch/macro_news_analysis_output.json"
            if os.path.exists(news_path):
                try:
                    with open(news_path, "r") as f_news:
                        raw_news = json.load(f_news)
                    text_news = raw_news["content"][0]["text"]
                    news_data = json.loads(text_news)["result"]["data"]
                    news_bias = news_data.get("decision_report", {}).get("action_guidance", {}).get("bias", "N/A").upper()
                    cmc_table.add_row("MACRO NEWS", f"[bold yellow]{news_bias[:15]}[/]")
                except:
                    pass
            has_cmc = True
        except:
            pass
            
    if not has_cmc:
        cmc_table.add_row("CMC SENTINEL", "[dim]No Overview Data[/]")
        cmc_table.add_row("STATUS", "[dim]Run overview script[/]")
        cmc_table.add_row("STANCE", "[dim]To display here[/]")
        
    # Combine side-by-side using an outer Table
    outer_table = Table.grid(expand=True)
    outer_table.add_column("Left", ratio=1)
    outer_table.add_column("Right", ratio=1)
    outer_table.add_row(macro_table, cmc_table)
    
    return Panel(outer_table, title="[bold]Macro Correlation & CMC Global Sentiment[/]", border_style="magenta")

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

    # CMC Sector Rotation (SOL/Altcoin specific)
    if symbol == "SOL":
        import os
        import json
        path = "scratch/sector_analysis_output.json"
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    raw = json.load(f)
                text = raw["content"][0]["text"]
                res_data = json.loads(text)["result"]["data"]
                if "data" in res_data:
                    cmc_data = res_data["data"]
                else:
                    cmc_data = res_data
                rep = cmc_data.get("report", {})
                action = cmc_data.get("action_guidance", {})
                identity = rep.get("token_identity", {})
                
                table.add_row("", "") # Spacer
                table.add_row("[bold cyan]CMC SECTOR ROT[/]", "")
                table.add_row("PRIMARY SEC", f"[white]{rep.get('primary_sector', 'N/A')[:18]}[/]")
                mom = rep.get("sector_momentum", "N/A").upper()
                mom_color = "red" if "decline" in mom.lower() or "bear" in mom.lower() else "green" if "bull" in mom.lower() else "yellow"
                table.add_row("MOMENTUM", f"[{mom_color}]{mom}[/]")
                table.add_row("ROT SIGNAL", f"[red]{rep.get('rotation_signal', 'N/A').upper()[:18]}[/]")
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
