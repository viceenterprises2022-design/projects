# Nifty 200 Momentum Scanner — Implementation Plan

## Overview
Periodic scanner (2x daily) that analyses Nifty 200 stocks for 52-week high/low proximity, RSI, EMAs, and consecutive-high streaks. Results stored in SQLite, served via FastAPI endpoint, displayed on dashboard.

## Files to Create

### 1. `strategies/__init__.py`
Empty package marker.

### 2. `strategies/nifty200_momentum.py` (~350 lines)
Main scanner script. Sections:

**Config:**
- `LOOKBACK_DAYS = 365`
- `API_THROTTLE = 0.2` seconds
- Nifty 200 CSV URL: `https://archives.nseindia.com/content/indices/ind_nifty200list.csv`
- Upstox token from `UPSTOX_TOKEN` env var
- DB at `strategies/strategies.db`
- Report at `strategies/nifty200_momentum_report.json`

**Functions:**
- `upstox_get(url, params)` — wrapped GET with auth header, timeout 15s, returns {} on error
- `fetch_nifty200()` — GET CSV → parse → list of {symbol, name, isin, instrument_key}
- `fetch_candles(key, days=365)` — Upstox historical-candle/day endpoint → parsed candle list
- `fetch_live_quotes(keys)` — batch quote call for LTPs
- `compute_rsi(closes, period=14)` — Wilder's RSI
- `compute_ema(closes, period)` — standard EMA with SMA seed
- `count_consecutive_highs(candles)` — count how many recent days high > prev 20d max
- `init_db()` — create tables + 7-day TTL cleanup
- `save_universe(conn, stocks)` — upsert stock list
- `save_snapshot(conn, symbol, date, data)` — insert one day's snapshot

**DB Schema (`strategies.db`):**
```sql
CREATE TABLE stock_universe (
    symbol TEXT PRIMARY KEY,
    name TEXT, isin TEXT, instrument_key TEXT UNIQUE
);
CREATE TABLE daily_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    ltp REAL, open REAL, high REAL, low REAL, close REAL, volume INTEGER,
    high_52w REAL, low_52w REAL,
    pct_from_52wh REAL, pct_from_52wl REAL,
    rsi_14 REAL, ema_20 REAL, ema_50 REAL, ema_100 REAL, ema_200 REAL,
    consecutive_high_days INTEGER,
    FOREIGN KEY (symbol) REFERENCES stock_universe(symbol)
);
```

**Shortlist Tiers:**
1. **Bullish**: pct_from_52wh >= -2 AND rsi > 55 AND close > ema_50 AND close > ema_200
2. **Bearish**: pct_from_52wl <= 2 AND rsi < 45 AND close < ema_50 AND close < ema_200
3. **Streak**: consecutive_high_days >= 3

**Output:**
- Insert into `daily_snapshots`
- Write `nifty200_momentum_report.json` with keys: `updated_at`, `bullish`[], `bearish`[], `streak`[], `all_stocks`[]
- Print Rich table to stdout

**Main flow:**
```
fetch_nifty200() → save_universe()
for each stock (200ms throttle):
    fetch_candles() → compute RSI, EMAs, 52wH/L, streak
fetch_live_quotes() → merge LTPs
shortlist → save_snapshot → write_report → print_table
```

## Files to Modify

### 3. `api_server.py` — Add endpoint
```python
@app.get("/api/strategies/nifty200-momentum")
def api_nifty200_momentum():
    report_path = Path("strategies/nifty200_momentum_report.json")
    if report_path.exists():
        return json.loads(report_path.read_text())
    raise HTTPException(status_code=404, detail="Report not yet generated")
```

### 4. `frontend/app.js` — Add strategy loader
- Add `loadStrategyNifty200()` → fetches `/api/strategies/nifty200-momentum`
- Add `renderStrategyNifty200(data)` → renders 3-column Bullish/Bearish/Streak
- Add to `refreshAll()` parallel call
- Each item shows: symbol, LTP, % from 52wH/L, RSI, streak count

### 5. `frontend/dashboard.html` — Add section
After gl-row container:
```html
<div class="container" style="margin-bottom:24px">
  <div class="strat-row" id="strat-row"></div>
</div>
```

### 6. `frontend/style.css` — Add strategy styles
`.strat-row` — 3-col grid for Bullish/Bearish/Streak cards
`.strat-card` — glass card with header + list
`.strat-item` — per-stock row with symbol, ltp, indicator badges

## Execution Order (for dev)
1. mkdir -p strategies/
2. Write strategies/__init__.py (empty)
3. Write strategies/nifty200_momentum.py (main scanner)
4. Modify api_server.py (add endpoint)
5. Modify frontend/app.js (add fetch/render)
6. Modify frontend/dashboard.html (add container)
7. Modify frontend/style.css (add styles)
8. Run once: `python3 strategies/nifty200_momentum.py`
9. Verify: DB has rows, report.json exists, API returns data
10. Restart api_server.py and check dashboard

## Cron Setup (2x daily)
```
30 8 * * 1-5 cd /home/vreddy1/Desktop/Projects/scripts && python3 strategies/nifty200_momentum.py
30 18 * * 1-5 cd /home/vreddy1/Desktop/Projects/scripts && python3 strategies/nifty200_momentum.py
```
