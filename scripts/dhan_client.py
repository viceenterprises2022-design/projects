import os
import requests
import datetime
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("DhanClient")

# Base API Configuration
DHAN_BASE_URL = "https://api.dhan.co"

# Load Credentials
env_path = Path(__file__).parent / ".env"
DHAN_CLIENT_ID = os.environ.get("DHAN_CLIENT_ID")
DHAN_ACCESS_TOKEN = os.environ.get("DHAN_ACCESS_TOKEN")

if not DHAN_CLIENT_ID or not DHAN_ACCESS_TOKEN:
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("DHAN_CLIENT_ID="):
                    DHAN_CLIENT_ID = line.strip().split("=", 1)[1]
                elif line.startswith("DHAN_ACCESS_TOKEN="):
                    DHAN_ACCESS_TOKEN = line.strip().split("=", 1)[1]

DHAN_HEADERS = {
    "client-id": DHAN_CLIENT_ID if DHAN_CLIENT_ID else "",
    "access-token": DHAN_ACCESS_TOKEN if DHAN_ACCESS_TOKEN else "",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Dhan Security ID mappings for Indices
DHAN_INDICES = {
    "NIFTY": {"id": 13, "segment": "NSE_IDX", "seg_opt": "IDX_I", "exch": "NSE"},
    "BANKNIFTY": {"id": 25, "segment": "NSE_IDX", "seg_opt": "IDX_I", "exch": "NSE"},
    "SENSEX": {"id": 51, "segment": "BSE_IDX", "seg_opt": "IDX_I", "exch": "BSE"}
}

def is_dhan_configured():
    """Check if Dhan credentials are present."""
    return bool(DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN)

def dhan_post(endpoint, payload):
    """Generic wrapper for posting to Dhan REST API."""
    if not is_dhan_configured():
        logger.warning("Dhan API credentials are not configured.")
        return {}
    url = f"{DHAN_BASE_URL}{endpoint}"
    try:
        r = requests.post(url, headers=DHAN_HEADERS, json=payload, timeout=10)
        if r.status_code == 200:
            return r.json()
        else:
            logger.error(f"Dhan API Error {r.status_code} at {endpoint}: {r.text}")
    except Exception as e:
        logger.error(f"Dhan connection failed at {endpoint}: {str(e)}")
    return {}

def fetch_dhan_ltp(symbol):
    """
    Fetch Last Traded Price (LTP) for a symbol.
    Returns: float price or None
    """
    map_info = DHAN_INDICES.get(symbol)
    if not map_info:
        logger.error(f"Symbol {symbol} not mapped in Dhan indices.")
        return None
        
    segment = map_info["segment"]
    sec_id = map_info["id"]
    
    # Payload format: {"NSE_IDX": [13]}
    payload = {segment: [sec_id]}
    d = dhan_post("/v2/marketfeed/ltp", payload)
    
    if d.get("status") == "success" and d.get("data"):
        try:
            prices = d["data"].get(segment, {})
            ltp = prices.get(str(sec_id), {}).get("last_price")
            return float(ltp) if ltp is not None else None
        except Exception as e:
            logger.error(f"Failed to parse Dhan LTP response: {str(e)}")
    return None

def fetch_dhan_ohlc(symbol):
    """
    Fetch Daily OHLC for a symbol.
    Returns: dict with ohlc fields or None
    """
    map_info = DHAN_INDICES.get(symbol)
    if not map_info:
        return None
        
    segment = map_info["segment"]
    sec_id = map_info["id"]
    
    payload = {segment: [sec_id]}
    d = dhan_post("/v2/marketfeed/ohlc", payload)
    
    if d.get("status") == "success" and d.get("data"):
        try:
            ohlc_data = d["data"].get(segment, {}).get(str(sec_id), {})
            ohlc = ohlc_data.get("ohlc", {})
            return {
                "open": float(ohlc.get("open", 0)),
                "high": float(ohlc.get("high", 0)),
                "low": float(ohlc.get("low", 0)),
                "close": float(ohlc.get("close", 0)),
                "last_price": float(ohlc_data.get("last_price", 0))
            }
        except Exception as e:
            logger.error(f"Failed to parse Dhan OHLC response: {str(e)}")
    return None

def fetch_dhan_expiries(symbol):
    """
    Fetch available option expiry dates.
    Returns: list of expiry date strings (YYYY-MM-DD)
    """
    map_info = DHAN_INDICES.get(symbol)
    if not map_info:
        return []
        
    payload = {
        "UnderlyingScrip": map_info["id"],
        "UnderlyingSeg": map_info["seg_opt"]
    }
    d = dhan_post("/v2/optionchain/expirylist", payload)
    
    # Dhan typically returns a flat list of date strings or success status
    if isinstance(d, list):
        return sorted(d)
    elif isinstance(d, dict) and d.get("status") == "success":
        # Check standard data keys
        raw = d.get("data", [])
        return sorted(raw)
    return []

def fetch_dhan_option_chain(symbol, expiry):
    """
    Fetch Option Chain and convert to Upstox compatibility format.
    Returns: list of dicts matching Upstox option chain schema.
    """
    map_info = DHAN_INDICES.get(symbol)
    if not map_info:
        return []
        
    payload = {
        "UnderlyingScrip": map_info["id"],
        "UnderlyingSeg": map_info["seg_opt"],
        "Expiry": expiry
    }
    d = dhan_post("/v2/optionchain", payload)
    
    if not d or d.get("status") != "success":
        return []
        
    converted_chain = []
    oc = d.get("data", {}).get("oc", {})
    
    for strike_str, options in oc.items():
        try:
            strike_price = float(strike_str)
            ce_data = options.get("ce", {}) or {}
            pe_data = options.get("pe", {}) or {}
            
            converted_row = {
                "strike_price": strike_price,
                "call_options": {
                    "market_data": {
                        "oi": ce_data.get("oi") or ce_data.get("open_interest") or 0,
                        "change_in_oi": ce_data.get("oi_change") or ce_data.get("change_in_oi") or 0,
                        "ltp": ce_data.get("last_price") or ce_data.get("ltp") or 0
                    }
                },
                "put_options": {
                    "market_data": {
                        "oi": pe_data.get("oi") or pe_data.get("open_interest") or 0,
                        "change_in_oi": pe_data.get("oi_change") or pe_data.get("change_in_oi") or 0,
                        "ltp": pe_data.get("last_price") or pe_data.get("ltp") or 0
                    }
                }
            }
            converted_chain.append(converted_row)
        except Exception as e:
            logger.error(f"Failed parsing options strike row: {str(e)}")
            
    return converted_chain

def fetch_dhan_candles(symbol, days=90):
    """
    Fetch Daily Historical Candles and convert to Upstox compatibility format.
    Returns: list of lists [[timestamp, open, high, low, close, volume], ...]
    """
    map_info = DHAN_INDICES.get(symbol)
    if not map_info:
        return []
        
    today = datetime.date.today()
    from_date = (today - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")
    
    payload = {
        "securityId": str(map_info["id"]),
        "exchangeSegment": map_info["segment"],
        "instrument": "INDEX",
        "fromDate": from_date,
        "toDate": to_date,
        "interval": "D"
    }
    
    # Daily charts endpoint is v2/charts/historical
    d = dhan_post("/v2/charts/historical", payload)
    
    if not d or d.get("status") != "success":
        return []
        
    converted_candles = []
    data = d.get("data", {})
    opens = data.get("open", [])
    highs = data.get("high", [])
    lows = data.get("low", [])
    closes = data.get("close", [])
    volumes = data.get("volume", [])
    times = data.get("start_Time", []) or data.get("start_time", []) or data.get("timestamp", [])
    
    for i in range(len(times)):
        try:
            ts = times[i]
            # Convert epoch to datetime string matching Upstox format
            if isinstance(ts, (int, float)):
                dt = datetime.datetime.fromtimestamp(ts, datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
                ts_str = dt.strftime("%Y-%m-%dT%H:%M:%S+05:30")
            else:
                ts_str = str(ts)
                
            converted_candles.append([
                ts_str,
                float(opens[i]) if i < len(opens) else 0.0,
                float(highs[i]) if i < len(highs) else 0.0,
                float(lows[i]) if i < len(lows) else 0.0,
                float(closes[i]) if i < len(closes) else 0.0,
                float(volumes[i]) if i < len(volumes) else 0.0
            ])
        except Exception as e:
            logger.error(f"Error parsing candle bar {i}: {str(e)}")
            
    return converted_candles
