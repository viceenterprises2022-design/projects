import sqlite3
import datetime
import time
import random
import os

DB_PATH = "crypto_intraday_oi.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS trending_oi 
                 (timestamp TEXT, symbol TEXT, ltp REAL, call_oi REAL, put_oi REAL)''')
    conn.commit()
    conn.close()

def generate_initial_history():
    """Generates the last 1 hour of data to bootstrap the table if empty"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT count(*) FROM trending_oi")
    count = c.fetchone()[0]
    
    if count == 0:
        now = datetime.datetime.now()
        base_price = 65000
        base_call_oi = 50000
        base_put_oi = 45000
        
        for i in range(12, 0, -1):
            ts = (now - datetime.timedelta(minutes=i*5)).strftime("%Y-%m-%d %H:%M:00")
            base_price += random.uniform(-100, 150)
            base_call_oi += random.uniform(-500, 800)
            base_put_oi += random.uniform(-300, 1000)
            c.execute("INSERT INTO trending_oi VALUES (?, ?, ?, ?, ?)", 
                      (ts, "BTC", base_price, base_call_oi, base_put_oi))
        conn.commit()
    conn.close()

def fetch_and_log_oi():
    """
    In production, this would make an async API call to CoinGlass to get
    the current BTC price, Call OI, and Put OI.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get last known to continue the random walk for smooth dummy data
    c.execute("SELECT ltp, call_oi, put_oi FROM trending_oi ORDER BY timestamp DESC LIMIT 1")
    row = c.fetchone()
    
    if row:
        base_price, base_call_oi, base_put_oi = row
    else:
        base_price, base_call_oi, base_put_oi = 65000, 50000, 45000
        
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:00")
    new_price = base_price + random.uniform(-100, 150)
    new_call_oi = base_call_oi + random.uniform(-500, 800)
    new_put_oi = base_put_oi + random.uniform(-300, 1000)
    
    c.execute("INSERT INTO trending_oi VALUES (?, ?, ?, ?, ?)", 
              (ts, "BTC", new_price, new_call_oi, new_put_oi))
              
    # Optional: Prune old data (e.g., keep last 24 hours = 288 rows of 5m intervals)
    c.execute("DELETE FROM trending_oi WHERE timestamp NOT IN (SELECT timestamp FROM trending_oi ORDER BY timestamp DESC LIMIT 288)")
    
    conn.commit()
    conn.close()
    print(f"[{ts}] Logged BTC OI -> Price: {new_price:.2f}, Call OI: {new_call_oi:.0f}, Put OI: {new_put_oi:.0f}")

def main():
    print("Starting AlphaEdge OI Background Daemon...")
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
