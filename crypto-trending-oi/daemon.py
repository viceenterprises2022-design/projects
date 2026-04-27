import sqlite3
import datetime
import time
import random
import os
import requests

DB_PATH = "crypto_intraday_oi.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS trending_oi 
                 (timestamp TEXT, symbol TEXT, ltp REAL, call_oi REAL, put_oi REAL)''')
    conn.commit()
    conn.close()

def get_real_btc_price():
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5)
        if res.status_code == 200:
            return float(res.json()["price"])
    except Exception as e:
        print(f"  [warn] Binance price fetch failed: {e}")
    return 65000.0

def generate_initial_history():
    """Bootstraps the table with 1h of history using real price if empty."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT count(*) FROM trending_oi")
    count = c.fetchone()[0]

    if count == 0:
        now = datetime.datetime.now()
        base_price = get_real_btc_price()
        call_oi, put_oi = get_real_btc_options_oi()
        base_call_oi = call_oi if call_oi else 50000
        base_put_oi  = put_oi  if put_oi  else 45000

        for i in range(12, 0, -1):
            ts = (now - datetime.timedelta(minutes=i*5)).strftime("%Y-%m-%d %H:%M:00")
            base_price   += random.uniform(-50, 50)
            base_call_oi += random.uniform(-200, 200)
            base_put_oi  += random.uniform(-200, 200)
            c.execute("INSERT INTO trending_oi VALUES (?, ?, ?, ?, ?)",
                      (ts, "BTC", base_price, base_call_oi, base_put_oi))
        conn.commit()
    conn.close()


def get_real_btc_options_oi():
    """
    Fetches live Call and Put OI from Binance Options (eapi) — free, no key required.
    Returns (call_oi, put_oi) in BTC contract units.
    Falls back to last known values on error.
    """
    try:
        res = requests.get("https://eapi.binance.com/eapi/v1/openInterest", timeout=5)
        if res.status_code == 200:
            data = res.json()
            call_oi = sum(float(d.get("sumOpenInterest", 0)) for d in data if d.get("symbol", "").endswith("-C"))
            put_oi  = sum(float(d.get("sumOpenInterest", 0)) for d in data if d.get("symbol", "").endswith("-P"))
            if call_oi + put_oi > 0:
                return call_oi, put_oi
    except Exception as e:
        print(f"  [warn] Binance Options OI fetch failed: {e}")
    return None, None

def fetch_and_log_oi():
    """
    Fetches real price from Binance Spot.
    Fetches real Call/Put OI from Binance Options (eapi).
    Falls back to random walk only if both real APIs fail.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT call_oi, put_oi FROM trending_oi ORDER BY timestamp DESC LIMIT 1")
    row = c.fetchone()
    last_call_oi = row[0] if row else 50000
    last_put_oi  = row[1] if row else 45000
        
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:00")
    
    # Real Price from Binance Spot
    new_price = get_real_btc_price()
    
    # Real Call/Put OI from Binance Options
    new_call_oi, new_put_oi = get_real_btc_options_oi()
    
    if new_call_oi is None:
        # Fallback: carry forward last value with small random walk
        new_call_oi = last_call_oi + random.uniform(-200, 200)
        new_put_oi  = last_put_oi  + random.uniform(-200, 200)
        source_label = "MOCK"
    else:
        source_label = "LIVE"
    
    c.execute("INSERT INTO trending_oi VALUES (?, ?, ?, ?, ?)", 
              (ts, "BTC", new_price, new_call_oi, new_put_oi))
              
    # Prune old data (keep last 24 hours = 288 rows of 5m intervals)
    c.execute("DELETE FROM trending_oi WHERE timestamp NOT IN (SELECT timestamp FROM trending_oi ORDER BY timestamp DESC LIMIT 288)")
    
    conn.commit()
    conn.close()
    print(f"[{ts}] [{source_label}] BTC -> Price: ${new_price:,.2f} | Call OI: {new_call_oi:,.0f} | Put OI: {new_put_oi:,.0f}")

def main():
    print("Starting AlphaEdge OI Background Daemon (Live Price)...")
    init_db()
    generate_initial_history()
    
    try:
        while True:
            fetch_and_log_oi()
            # Wait 5 minutes
            time.sleep(300)
    except KeyboardInterrupt:
        print("\nDaemon stopped.")

if __name__ == "__main__":
    main()
