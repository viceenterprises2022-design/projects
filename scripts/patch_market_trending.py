import sys, re

with open('market_analysis_v3.py', 'r') as f:
    content = f.read()

# 1. Add imports
content = content.replace(
    "import requests, datetime, os, webbrowser, time, json",
    "import requests, datetime, os, webbrowser, time, json, sqlite3, threading"
)

# 2. Add Database & Thread logic
db_code = """
# ── INTRADAY OI COLLECTOR ────────────────────────────────────────────────────

DB_PATH = "intraday_oi.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS trending_oi 
                 (timestamp TEXT, symbol TEXT, ltp REAL, call_oi REAL, put_oi REAL)''')
    # Clean previous day's data
    c.execute("DELETE FROM trending_oi WHERE date(timestamp) < date('now', 'localtime')")
    conn.commit()
    conn.close()

def oi_collector_thread():
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:00")
            
            for sym in ["NIFTY", "BANKNIFTY", "SENSEX"]:
                key = INSTRUMENTS.get(sym)
                oi_key = OI_INSTRUMENTS.get(sym)
                if not key or not oi_key: continue
                
                q = fetch_quote(key)
                if not q: continue
                ltp = q.get("ltp", 0)
                oi_raw = build_oi_data(sym, ltp)
                if not oi_raw: continue
                
                c_oi = oi_raw.get("total_call_oi", 0)
                p_oi = oi_raw.get("total_put_oi", 0)
                
                c.execute("INSERT INTO trending_oi VALUES (?, ?, ?, ?, ?)", (ts, sym, ltp, c_oi, p_oi))
                
            conn.commit()
            conn.close()
        except Exception as e:
            pass # Silent fail for background daemon
            
        time.sleep(300) # 5 minutes

# ─────────────────────────────────────────────────────────────────────────────
"""
content = content.replace("# ── Upstox Fetchers", db_code + "\n# ── Upstox Fetchers")

# 3. Add print_trending_oi function
trending_oi_code = """
# ─────────────────────────────────────────────────────────────────────────────
# PHASE 4 — TRENDING OI TABLE
# ─────────────────────────────────────────────────────────────────────────────

def print_trending_oi(sym):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT timestamp, ltp, call_oi, put_oi FROM trending_oi WHERE symbol=? ORDER BY timestamp ASC", (sym,))
        rows = c.fetchall()
        conn.close()
    except Exception:
        return
        
    if not rows:
        console.print("[dim]  Trending OI data is collecting... Please wait for the first 5-min interval.[/dim]")
        return
        
    console.print(Rule("[bold cyan]Trending OI (Intraday Pulse)[/bold cyan]", style="cyan"))
    
    t_table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold dim")
    t_table.add_column("Time", justify="left")
    t_table.add_column("LTP", justify="right")
    t_table.add_column("Chng Call OI", justify="right", style="green")
    t_table.add_column("Chng Put OI", justify="right", style="red")
    t_table.add_column("Diff in OI", justify="right", style="bold")
    t_table.add_column("Dir.", justify="center")
    t_table.add_column("Chng in Dir", justify="right")
    t_table.add_column("Net PCR", justify="right")
    t_table.add_column("Sentiment", justify="center")
    
    base_c_oi = rows[0][2]
    base_p_oi = rows[0][3]
    prev_diff = None
    
    # Render reverse chronological
    display_rows = []
    
    for r in rows:
        ts_str, ltp, c_oi, p_oi = r
        time_str = ts_str.split(" ")[1][:5]
        
        chng_c = c_oi - base_c_oi
        chng_p = p_oi - base_p_oi
        diff = p_oi - c_oi
        
        pcr = p_oi / c_oi if c_oi > 0 else 0
        
        chng_dir = diff - prev_diff if prev_diff is not None else 0
        
        # Format strings
        dir_char = "[green]↑[/green]" if chng_dir > 0 else "[red]↓[/red]" if chng_dir < 0 else "—"
        
        sent = "[bold green]Bullish[/bold green]" if (diff > 0 and chng_dir >= 0) else \
               "[bold red]Bearish[/bold red]" if (diff < 0 and chng_dir <= 0) else \
               "[yellow]Neutral[/yellow]"
               
        chng_dir_str = f"[green]{chng_dir:,.0f}[/green]" if chng_dir > 0 else f"[red]{chng_dir:,.0f}[/red]"
        diff_str = f"{diff:,.0f}"
        
        display_rows.insert(0, (
            time_str, f"{ltp:,.2f}", f"{chng_c:,.0f}", f"{chng_p:,.0f}", 
            diff_str, dir_char, chng_dir_str, f"{pcr:.2f}", sent
        ))
        
        prev_diff = diff
        
    for dr in display_rows:
        t_table.add_row(*dr)
        
    console.print(t_table)

"""
content = content.replace("# ─────────────────────────────────────────────────────────────────────────────\n# FULL DIAGNOSTIC REPORT", trending_oi_code + "\n# ─────────────────────────────────────────────────────────────────────────────\n# FULL DIAGNOSTIC REPORT")


# 4. Inject print_trending_oi into print_diagnostic_report
content = content.replace(
    "    # Phase 2 — Intelligence Panel\n    if oi_raw:\n        print_intelligence_panel(sym, quote, oi_raw)\n",
    "    # Phase 2 — Intelligence Panel\n    if oi_raw:\n        print_intelligence_panel(sym, quote, oi_raw)\n\n    # Phase 4 — Trending OI\n    if oi_raw:\n        print_trending_oi(sym)\n"
)

# 5. Start thread and init DB in main()
content = content.replace(
    "def main():\n    while True:",
    "def main():\n    init_db()\n    threading.Thread(target=oi_collector_thread, daemon=True).start()\n\n    while True:"
)

with open('market_analysis_v3.py', 'w') as f:
    f.write(content)

