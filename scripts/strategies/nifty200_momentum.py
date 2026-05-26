import csv, io, json, os, sqlite3, time, datetime
import requests
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR.parent / ".env")

LOOKBACK_DAYS = 365
API_THROTTLE = 0.2
NIFTY200_URL = "https://archives.nseindia.com/content/indices/ind_nifty200list.csv"
UPSTOX_TOKEN = os.environ.get("UPSTOX_TOKEN")
UH = {"Authorization": f"Bearer {UPSTOX_TOKEN}", "Accept": "application/json"}
DB_PATH = BASE_DIR / "strategies.db"
REPORT_PATH = BASE_DIR / "nifty200_momentum_report.json"


def upstox_get(url, params):
    try:
        r = requests.get(url, headers=UH, params=params, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  [W] {url.split('/')[-1]} {params}: {e}")
    return {}


def fetch_nifty200():
    print("[1/6] Fetching Nifty 200 constituents...")
    r = requests.get(NIFTY200_URL, timeout=15)
    r.raise_for_status()
    reader = csv.DictReader(io.StringIO(r.text))
    stocks = []
    for row in reader:
        isin = row["ISIN Code"].strip()
        if not isin:
            continue
        stocks.append({
            "symbol": row["Symbol"].strip(),
            "name": row["Company Name"].strip(),
            "isin": isin,
            "instrument_key": f"NSE_EQ|{isin}",
        })
    print(f"       {len(stocks)} stocks fetched")
    return stocks


def fetch_candles(key, days=LOOKBACK_DAYS):
    today = datetime.date.today()
    f = (today - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    t = today.strftime("%Y-%m-%d")
    d = upstox_get(f"https://api.upstox.com/v2/historical-candle/{key}/day/{t}/{f}", {})
    candles = d.get("data", {}).get("candles", [])
    candles = candles[::-1]
    result = []
    for c in candles:
        result.append({
            "timestamp": c[0],
            "open": float(c[1]),
            "high": float(c[2]),
            "low": float(c[3]),
            "close": float(c[4]),
            "volume": int(c[5]),
        })
    return result


def fetch_live_quotes(keys):
    joined = ",".join(keys)
    d = upstox_get("https://api.upstox.com/v2/market-quote/quotes", {"instrument_key": joined})
    items = d.get("data", {})
    result = {}
    for k, v in items.items():
        symbol = k.split(":", 1)[-1] if ":" in k else k
        ltp = v.get("last_price", 0)
        net_chg = v.get("net_change", 0)
        prev_close = ltp - net_chg
        chg_pct = (net_chg / prev_close * 100) if prev_close else 0
        result[symbol] = {"ltp": ltp, "chg": chg_pct}
    return result


def compute_rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(diff if diff > 0 else 0)
        losses.append(-diff if diff < 0 else 0)
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def compute_ema(closes, period):
    if len(closes) < period:
        return None
    k = 2.0 / (period + 1)
    ema = sum(closes[:period]) / period
    for c in closes[period:]:
        ema = c * k + ema * (1 - k)
    return ema


def count_consecutive_highs(candles):
    if len(candles) < 21:
        return 0
    highs = [c["high"] for c in candles]
    count = 0
    for i in range(len(highs) - 1, 0, -1):
        window = highs[max(0, i - 20):i]
        if not window:
            break
        if highs[i] > max(window):
            count += 1
        else:
            break
    return count


def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stock_universe (
            symbol TEXT PRIMARY KEY,
            name TEXT,
            isin TEXT,
            instrument_key TEXT UNIQUE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            ltp REAL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            high_52w REAL,
            low_52w REAL,
            pct_from_52wh REAL,
            pct_from_52wl REAL,
            rsi_14 REAL,
            ema_20 REAL,
            ema_50 REAL,
            ema_100 REAL,
            ema_200 REAL,
            consecutive_high_days INTEGER,
            FOREIGN KEY (symbol) REFERENCES stock_universe(symbol)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_daily_date ON daily_snapshots(recorded_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_daily_sym ON daily_snapshots(symbol)")
    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    deleted = conn.execute("DELETE FROM daily_snapshots WHERE recorded_at < ?", (week_ago,)).rowcount
    conn.commit()
    if deleted:
        print(f"       Purged {deleted} stale rows (>7 days old)")
    return conn


def save_universe(conn, stocks):
    for s in stocks:
        conn.execute("""
            INSERT OR REPLACE INTO stock_universe (symbol, name, isin, instrument_key)
            VALUES (?, ?, ?, ?)
        """, (s["symbol"], s["name"], s["isin"], s["instrument_key"]))
    conn.commit()


def save_snapshot(conn, symbol, recorded_at, data):
    conn.execute("""
        INSERT INTO daily_snapshots (
            symbol, recorded_at, ltp, open, high, low, close, volume,
            high_52w, low_52w, pct_from_52wh, pct_from_52wl,
            rsi_14, ema_20, ema_50, ema_100, ema_200, consecutive_high_days
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        symbol, recorded_at,
        data.get("ltp"), data.get("open"), data.get("high"),
        data.get("low"), data.get("close"), data.get("volume"),
        data.get("high_52w"), data.get("low_52w"),
        data.get("pct_from_52wh"), data.get("pct_from_52wl"),
        data.get("rsi_14"), data.get("ema_20"), data.get("ema_50"),
        data.get("ema_100"), data.get("ema_200"),
        data.get("consecutive_high_days"),
    ))


def main():
    t0 = time.time()

    recorded_at = datetime.datetime.now(datetime.UTC).isoformat()

    if not UPSTOX_TOKEN:
        print("[!] UPSTOX_TOKEN not set")
        return

    conn = init_db()

    stocks = fetch_nifty200()
    save_universe(conn, stocks)

    print("[2/6] Fetching historical candles (365d)...")
    instrument_keys = [s["instrument_key"] for s in stocks]
    all_candles = {}
    for i, (stock, key) in enumerate(zip(stocks, instrument_keys)):
        sym = stock["symbol"]
        candles = fetch_candles(key)
        if candles:
            all_candles[sym] = candles
        if (i + 1) % 20 == 0:
            print(f"       {i+1}/{len(stocks)} done")
        time.sleep(API_THROTTLE)
    print(f"       {len(all_candles)}/{len(stocks)} had candle data")

    print("[3/6] Fetching live quotes...")
    live = fetch_live_quotes(instrument_keys)
    print(f"       {len(live)} quotes received")

    print("[4/6] Computing indicators...")
    results = []
    for stock in stocks:
        sym = stock["symbol"]
        candles = all_candles.get(sym, [])
        if len(candles) < 50:
            continue
        closes = [c["close"] for c in candles]
        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]
        high_52w = max(highs[-252:]) if len(highs) >= 252 else max(highs)
        low_52w = min(lows[-252:]) if len(lows) >= 252 else min(lows)
        last = candles[-1]
        pct_from_52wh = ((last["close"] - high_52w) / high_52w) * 100 if high_52w else 0
        pct_from_52wl = ((last["close"] - low_52w) / low_52w) * 100 if low_52w else 0
        rsi = compute_rsi(closes)
        ema_20 = compute_ema(closes, 20)
        ema_50 = compute_ema(closes, 50)
        ema_100 = compute_ema(closes, 100)
        ema_200 = compute_ema(closes, 200)
        streak = count_consecutive_highs(candles)
        ltp = live.get(sym, {}).get("ltp", last["close"])
        data = {
            "symbol": sym,
            "name": stock["name"],
            "ltp": ltp,
            "open": last["open"],
            "high": last["high"],
            "low": last["low"],
            "close": last["close"],
            "volume": last["volume"],
            "high_52w": high_52w,
            "low_52w": low_52w,
            "pct_from_52wh": round(pct_from_52wh, 2),
            "pct_from_52wl": round(pct_from_52wl, 2),
            "rsi_14": round(rsi, 2),
            "ema_20": round(ema_20, 2) if ema_20 else None,
            "ema_50": round(ema_50, 2) if ema_50 else None,
            "ema_100": round(ema_100, 2) if ema_100 else None,
            "ema_200": round(ema_200, 2) if ema_200 else None,
            "consecutive_high_days": streak,
        }
        results.append(data)
        save_snapshot(conn, sym, recorded_at, data)

    conn.commit()
    conn.close()

    print("[5/6] Shortlisting...")
    bullish = [
        r for r in results
        if r["pct_from_52wh"] >= -2
        and r["rsi_14"] > 55
        and r["ema_50"] is not None and r["ema_200"] is not None
        and r["close"] > r["ema_50"]
        and r["close"] > r["ema_200"]
    ]
    bearish = [
        r for r in results
        if r["pct_from_52wl"] <= 2
        and r["rsi_14"] < 45
        and r["ema_50"] is not None and r["ema_200"] is not None
        and r["close"] < r["ema_50"]
        and r["close"] < r["ema_200"]
    ]
    streak = [
        r for r in results
        if r["consecutive_high_days"] >= 3
    ]
    bullish.sort(key=lambda x: x["pct_from_52wh"], reverse=True)
    bearish.sort(key=lambda x: x["pct_from_52wl"])
    streak.sort(key=lambda x: x["consecutive_high_days"], reverse=True)

    report = {
        "updated_at": recorded_at,
        "total_scanned": len(results),
        "bullish": bullish[:20],
        "bearish": bearish[:20],
        "streak": streak[:20],
        "all_stocks": results,
    }

    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str))
    print(f"       Report written to {REPORT_PATH.name}")

    print("[6/6] Terminal output:")
    print()
    print_table(bullish, bearish, streak, recorded_at)

    elapsed = time.time() - t0
    print(f"\n       Done in {elapsed:.1f}s")


def print_table(bullish, bearish, streak, recorded_at):
    try:
        from rich.console import Console
        from rich.table import Table
        from rich import box
        console = Console()
    except ImportError:
        print("[!] rich not installed — skipping formatted output")
        return

    dt = recorded_at[:19].replace("T", " ")
    console.print(f"\n[bold cyan]NIFTY 200 MOMENTUM SCANNER[/bold cyan] · {dt} IST", style="bold")

    if bullish:
        t = Table(title=f"[green]BULLISH — {len(bullish)} stocks at 52wH proximity[/green]", box=box.SIMPLE, header_style="bold green")
        t.add_column("Symbol", style="cyan", no_wrap=True)
        t.add_column("LTP", justify="right")
        t.add_column("52wH%", justify="right")
        t.add_column("RSI", justify="right")
        t.add_column("EMA50", justify="center")
        t.add_column("EMA200", justify="center")
        t.add_column("Streak", justify="right")
        for r in bullish[:10]:
            ema50 = "↑" if r["close"] > r["ema_50"] else "↓"
            ema200 = "↑" if r["close"] > r["ema_200"] else "↓"
            t.add_row(
                r["symbol"],
                f"{r['ltp']:.2f}",
                f"{r['pct_from_52wh']:.1f}%",
                f"{r['rsi_14']:.1f}",
                ema50,
                ema200,
                f"{r['consecutive_high_days']}d" if r["consecutive_high_days"] else "—",
            )
        console.print(t)

    if bearish:
        t = Table(title=f"[red]BEARISH — {len(bearish)} stocks at 52wL proximity[/red]", box=box.SIMPLE, header_style="bold red")
        t.add_column("Symbol", style="cyan", no_wrap=True)
        t.add_column("LTP", justify="right")
        t.add_column("52wL%", justify="right")
        t.add_column("RSI", justify="right")
        for r in bearish[:10]:
            t.add_row(r["symbol"], f"{r['ltp']:.2f}", f"{r['pct_from_52wl']:.1f}%", f"{r['rsi_14']:.1f}")
        console.print(t)

    if streak:
        t = Table(title=f"[yellow]STREAK — {len(streak)} stocks making consecutive highs[/yellow]", box=box.SIMPLE, header_style="bold yellow")
        t.add_column("Symbol", style="cyan", no_wrap=True)
        t.add_column("LTP", justify="right")
        t.add_column("Streak", justify="right")
        t.add_column("52wH%", justify="right")
        t.add_column("RSI", justify="right")
        for r in streak[:10]:
            t.add_row(r["symbol"], f"{r['ltp']:.2f}", f"{r['consecutive_high_days']}d", f"{r['pct_from_52wh']:.1f}%", f"{r['rsi_14']:.1f}")
        console.print(t)

    if not bullish and not bearish and not streak:
        console.print("[dim]No stocks qualified in any shortlist tier[/dim]")

    console.print(f"\n[dim]Scanned {len(bullish) + len(bearish) + len(streak) if bullish or bearish or streak else 'all'} stocks.[/dim]")


if __name__ == "__main__":
    main()
