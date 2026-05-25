# Task 3: 3-Column Diagnostic UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a 3-column side-by-side crypto diagnostic dashboard using `rich`.

**Architecture:** Split screen into Header (Macro) and Body (Ticker Tiles). Body has 3 columns for BTC, ETH, SOL. Live update loop @ 30s.

**Tech Stack:** Python 3.13, `rich`.

---

### Task 1: Project Scaffolding & Layout Definition

**Files:**
- Create: `crypto_market_dashboard_v2.py`

- [ ] **Step 1: Create file with imports and layout function**

```python
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
```

- [ ] **Step 2: Implement mock renderers**

```python
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
```

- [ ] **Step 3: Implement main loop**

```python
def main():
    console = Console()
    layout = make_layout()
    
    with Live(layout, console=console, screen=True, refresh_per_second=1) as live:
        while True:
            layout["header"].update(render_header())
            layout["macro"].update(render_macro())
            layout["BTC"].update(render_ticker("BTC"))
            layout["ETH"].update(render_ticker("ETH"))
            layout["SOL"].update(render_ticker("SOL"))
            time.sleep(1) # Fast update for clock, data would be 30s
            
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
```

- [ ] **Step 4: Verify UI locally**
Run: `python3 crypto_market_dashboard_v2.py`
Expected: Fullscreen 3-column UI with mock data. Clock updates every second.

- [ ] **Step 5: Commit**

```bash
git add crypto_market_dashboard_v2.py
git commit -m "feat: 3-column diagnostic UI layout"
```
