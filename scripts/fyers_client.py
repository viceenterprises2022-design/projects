import os
import hashlib
import requests
import datetime
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("FyersClient")

# Base API Configuration
FYERS_BASE_URL = "https://api-t1.fyers.in"  # V3 Data Domain
FYERS_AUTH_URL = "https://api.fyers.in"    # V3 Auth Domain

# Load Credentials
env_path = Path(__file__).parent / ".env"
FYERS_CLIENT_ID = os.environ.get("FYERS_CLIENT_ID")
FYERS_SECRET_KEY = os.environ.get("FYERS_SECRET_KEY")
FYERS_PIN = os.environ.get("FYERS_PIN")
FYERS_REFRESH_TOKEN = os.environ.get("FYERS_REFRESH_TOKEN")
FYERS_ACCESS_TOKEN = os.environ.get("FYERS_ACCESS_TOKEN")

if not FYERS_CLIENT_ID or not FYERS_SECRET_KEY or not FYERS_REFRESH_TOKEN:
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("FYERS_CLIENT_ID="):
                    FYERS_CLIENT_ID = line.strip().split("=", 1)[1]
                elif line.startswith("FYERS_SECRET_KEY="):
                    FYERS_SECRET_KEY = line.strip().split("=", 1)[1]
                elif line.startswith("FYERS_PIN="):
                    FYERS_PIN = line.strip().split("=", 1)[1]
                elif line.startswith("FYERS_REFRESH_TOKEN="):
                    FYERS_REFRESH_TOKEN = line.strip().split("=", 1)[1]
                elif line.startswith("FYERS_ACCESS_TOKEN="):
                    FYERS_ACCESS_TOKEN = line.strip().split("=", 1)[1]

# Fyers Symbol Mappings for Indices
FYERS_SYMBOLS = {
    "NIFTY": "NSE:NIFTY50-INDEX",
    "BANKNIFTY": "NSE:NIFTYBANK-INDEX",
    "SENSEX": "BSE:SENSEX-INDEX"
}

def update_env_var(key, val):
    """Safely writes/updates a key-value pair in .env file."""
    lines = []
    replaced = False
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith(f"{key}="):
                    lines.append(f"{key}={val}\n")
                    replaced = True
                else:
                    lines.append(line)
    if not replaced:
        lines.append(f"{key}={val}\n")
        
    with open(env_path, "w") as f:
        f.writelines(lines)
    logger.info(f"Updated {key} in .env file.")

def is_fyers_configured():
    """Disabled by request - force all feeds exclusively from Upstox."""
    return False

def refresh_fyers_access_token():
    """
    Exchanges the 15-day refresh token for a fresh 24h daily access token.
    Saves the new token to .env and updates the global variable.
    """
    if not is_fyers_configured():
        logger.warning("Fyers credentials not configured for refresh token exchange.")
        return None
        
    # Calculate app ID hash as sha256(client_id + ":" + secret_key)
    app_id_hash = hashlib.sha256(f"{FYERS_CLIENT_ID}:{FYERS_SECRET_KEY}".encode()).hexdigest()
    
    url = f"{FYERS_AUTH_URL}/api/v3/validate-refresh-token"
    payload = {
        "grant_type": "refresh_token",
        "appIdHash": app_id_hash,
        "refresh_token": FYERS_REFRESH_TOKEN,
        "pin": FYERS_PIN
    }
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            d = r.json()
            if d.get("s") == "ok" and d.get("access_token"):
                new_token = d["access_token"]
                global FYERS_ACCESS_TOKEN
                FYERS_ACCESS_TOKEN = new_token
                update_env_var("FYERS_ACCESS_TOKEN", new_token)
                logger.info("Successfully refreshed daily Fyers access token!")
                return new_token
            else:
                logger.error(f"Fyers refresh token exchange failed: {d}")
        else:
            logger.error(f"Fyers refresh failed with status {r.status_code}: {r.text}")
    except Exception as e:
        logger.error(f"Fyers refresh connection failed: {str(e)}")
    return None

def get_auth_headers():
    """Generates standard V3 authorization headers."""
    # Fyers V3 uses: "app_id:access_token" in Authorization header
    token = FYERS_ACCESS_TOKEN if FYERS_ACCESS_TOKEN else ""
    return {
        "Authorization": f"{FYERS_CLIENT_ID}:{token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def fyers_request(method, endpoint, params=None, json_data=None, retry_on_auth_err=True):
    """
    Generic wrapper for Fyers requests. Handlers authentication,
    detects expired tokens (401), automatically triggers token refresh,
    and retries the query once.
    """
    if not is_fyers_configured():
        return {}
        
    url = f"{FYERS_BASE_URL}{endpoint}"
    headers = get_auth_headers()
    
    try:
        if method == "GET":
            r = requests.get(url, headers=headers, params=params, timeout=10)
        else:
            r = requests.post(url, headers=headers, json=json_data, timeout=10)
            
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 401 and retry_on_auth_err:
            logger.warning("Fyers access token expired (401). Attempting background refresh...")
            new_token = refresh_fyers_access_token()
            if new_token:
                # Retry once with fresh token
                return fyers_request(method, endpoint, params, json_data, retry_on_auth_err=False)
        else:
            logger.error(f"Fyers HTTP Error {r.status_code} at {endpoint}: {r.text}")
    except Exception as e:
        logger.error(f"Fyers connection failed at {endpoint}: {str(e)}")
    return {}

def fetch_fyers_ltp(symbol):
    """
    Fetch Last Traded Price (LTP) for an index symbol.
    Returns: float price or None
    """
    fyers_sym = FYERS_SYMBOLS.get(symbol)
    if not fyers_sym:
        return None
        
    d = fyers_request("GET", "/data/quotes", params={"symbols": fyers_sym})
    if d.get("s") == "ok" and d.get("d"):
        try:
            val = d["d"][0].get("v", {})
            ltp = val.get("lp")
            return float(ltp) if ltp is not None else None
        except Exception as e:
            logger.error(f"Failed parsing Fyers quotes LTP: {str(e)}")
    return None

def fetch_fyers_ohlc(symbol):
    """
    Fetch Daily OHLC for an index symbol.
    Returns: dict with ohlc fields or None
    """
    fyers_sym = FYERS_SYMBOLS.get(symbol)
    if not fyers_sym:
        return None
        
    d = fyers_request("GET", "/data/quotes", params={"symbols": fyers_sym})
    if d.get("s") == "ok" and d.get("d"):
        try:
            val = d["d"][0].get("v", {})
            ltp = val.get("lp", 0)
            open_p = val.get("open_price", 0)
            high_p = val.get("high_price", 0)
            low_p = val.get("low_price", 0)
            prev_c = val.get("prev_close_price", 0)
            return {
                "open": float(open_p),
                "high": float(high_p),
                "low": float(low_p),
                "close": float(prev_c),
                "last_price": float(ltp)
            }
        except Exception as e:
            logger.error(f"Failed parsing Fyers quotes OHLC: {str(e)}")
    return None

def fetch_fyers_expiries(symbol):
    """
    Dummy/Fallback expiries list. Since Fyers Option Chain API returns the expiry dates
    directly within its standard option chain, we can fetch the option chain for the
    symbol and extract the available expiry list dynamically, or fall back to empty.
    """
    fyers_sym = FYERS_SYMBOLS.get(symbol)
    if not fyers_sym:
        return []
        
    # We can fetch the nearest 5 expiries via the option chain API or standard Fyers F&O contracts
    # For now, return empty or mock-fetch expiry from options chain which handles this cleanly
    return []

def fetch_fyers_option_chain(symbol, expiry):
    """
    Fetch Option Chain for a symbol and expiry, and convert to Upstox format.
    Returns: list of dicts matching Upstox option chain schema.
    """
    fyers_sym = FYERS_SYMBOLS.get(symbol)
    if not fyers_sym:
        return []
        
    # Expiry format: YYYY-MM-DD
    # We query the fyers option chain REST API
    params = {
        "symbol": fyers_sym,
        "strikecount": 50
    }
    d = fyers_request("GET", "/data/options-chain-v3", params=params)
    if d.get("s") != "ok" or not d.get("optionsChain"):
        return []
        
    converted_chain = []
    chain_list = d.get("optionsChain", [])
    
    # Filter only matching expiry if provided
    # Upstox returns expiry format as YYYY-MM-DD. Fyers typically returns string dates
    for item in chain_list:
        try:
            # Check if expiry match
            strike_price = float(item.get("strikePrice", 0))
            
            # Handle call/put structures safely checking all keys (call, ce, call_options)
            ce_data = item.get("call_options") or item.get("call") or item.get("ce") or {}
            pe_data = item.get("put_options") or item.get("put") or item.get("pe") or {}
            
            converted_row = {
                "strike_price": strike_price,
                "call_options": {
                    "market_data": {
                        "oi": ce_data.get("oi") or ce_data.get("open_interest") or 0,
                        "change_in_oi": ce_data.get("oi_change") or ce_data.get("change_in_oi") or ce_data.get("oich") or 0,
                        "ltp": ce_data.get("last_price") or ce_data.get("ltp") or 0
                    }
                },
                "put_options": {
                    "market_data": {
                        "oi": pe_data.get("oi") or pe_data.get("open_interest") or 0,
                        "change_in_oi": pe_data.get("oi_change") or pe_data.get("change_in_oi") or pe_data.get("oich") or 0,
                        "ltp": pe_data.get("last_price") or pe_data.get("ltp") or 0
                    }
                }
            }
            converted_chain.append(converted_row)
        except Exception as e:
            logger.error(f"Error converting Fyers options row: {str(e)}")
            
    return converted_chain

def fetch_fyers_candles(symbol, days=90):
    """
    Fetch Daily Historical Candles and convert to Upstox format.
    Returns: list of lists [[timestamp, open, high, low, close, volume], ...]
    """
    fyers_sym = FYERS_SYMBOLS.get(symbol)
    if not fyers_sym:
        return []
        
    today = datetime.date.today()
    from_date = (today - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")
    
    params = {
        "symbol": fyers_sym,
        "resolution": "D",
        "date_format": "1",
        "range_from": from_date,
        "range_to": to_date,
        "cont_flag": "0"
    }
    
    d = fyers_request("GET", "/data/history", params=params)
    if d.get("s") != "ok" or not d.get("candles"):
        return []
        
    converted_candles = []
    raw_candles = d.get("candles", [])
    
    # Fyers returns candles as lists: [epoch, open, high, low, close, volume]
    for c in raw_candles:
        try:
            ts = c[0]
            # Convert epoch to datetime string matching Upstox format
            if isinstance(ts, (int, float)):
                dt = datetime.datetime.fromtimestamp(ts, datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
                ts_str = dt.strftime("%Y-%m-%dT%H:%M:%S+05:30")
            else:
                ts_str = str(ts)
                
            converted_candles.append([
                ts_str,
                float(c[1]), # Open
                float(c[2]), # High
                float(c[3]), # Low
                float(c[4]), # Close
                float(c[5])  # Volume
            ])
        except Exception as e:
            logger.error(f"Error parsing Fyers candle bar: {str(e)}")
            
    return converted_candles
