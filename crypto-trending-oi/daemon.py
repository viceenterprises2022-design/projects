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
    except:
        pass
    return 65000.0

def generate_initial_history():
    """Generates the last 1 hour of data to bootstrap the table if empty"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT count(*) FROM trending_oi")
    count = c.fetchone()[0]
    
    if count == 0:
        now = datetime.datetime.now()
        base_price = get_real_btc_price()
        base_call_oi = 50000
        base_put_oi = 45000
        
        for i in range(12, 0, -1):
            ts = (now - datetime.timedelta(minutes=i*5)).strftime("%Y-%m-%d %H:%M:00")
            base_price += random.uniform(-50, 50)
            base_call_oi += random.uniform(-500, 800)
            base_put_oi += random.uniform(-300, 1000)
            c.execute("INSERT INTO trending_oi VALUES (?, ?, ?, ?, ?)", 
                      (ts, "BTC", base_price, base_call_oi, base_put_oi))
        conn.commit()
    conn.close()

def fetch_and_log_oi():
    """
    Fetches real price from Binance.
    Mocks Call/Put OI because Options APIs (CoinGlass/Deribit) require paid keys.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT call_oi, put_oi FROM trending_oi ORDER BY timestamp DESC LIMIT 1")
    row = c.fetchone()
    
    if row:
        base_call_oi, base_put_oi = row
    else:
        base_call_oi, base_put_oi = 50000, 45000
        
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:00")
    
    # Real Price
    new_price = get_real_btc_price()
    
    # Mocked OI (Requires Coinglass/Deribit to be real)
    new_call_oi = base_call_oi + random.uniform(-500, 800)
    new_put_oi = base_put_oi + random.uniform(-300, 1000)
    
    c.execute("INSERT INTO trending_oi VALUES (?, ?, ?, ?, ?)", 
              (ts, "BTC", new_price, new_call_oi, new_put_oi))
              
    # Prune old data (keep last 24 hours = 288 rows of 5m intervals)
    c.execute("DELETE FROM trending_oi WHERE timestamp NOT IN (SELECT timestamp FROM trending_oi ORDER BY timestamp DESC LIMIT 288)")
    
    conn.commit()
    conn.close()
    print(f"[{ts}] Logged BTC OI -> Price: {new_price:.2f}, Call OI: {new_call_oi:.0f}, Put OI: {new_put_oi:.0f}")

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
