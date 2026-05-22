#!/usr/bin/env python3
"""
AlphaEdge Portfolio P&L Poller
Handles live APIs for Upstox, Dhan, and TradeSmart (Noren OMS).
Includes a high-fidelity dynamic mock engine for fallback when credentials are empty or fail.
"""

import os
import sys
import json
import logging

log = logging.getLogger(__name__)
import hashlib
import time
import datetime
import random
import requests
from dotenv import load_dotenv

load_dotenv()

# --- Config & Credentials ---
UPSTOX_TOKEN        = os.environ.get("UPSTOX_TOKEN")
DHAN_ACCESS_TOKEN   = os.environ.get("DHAN_ACCESS_TOKEN")

# TradeSmart Noren OMS Credentials
TS_UID     = os.environ.get("TRADESMART_CLIENT_ID")
TS_PWD     = os.environ.get("TRADESMART_PASSWORD")
TS_FACTOR2 = os.environ.get("TRADESMART_FACTOR2")
TS_VC      = os.environ.get("TRADESMART_VENDOR_CODE")
TS_API_KEY = os.environ.get("TRADESMART_API_KEY")
TS_BASE_URL = "https://api.tradesmartonline.in/NorenWClientTP"

# Fyers API Credentials
FYERS_CLIENT_ID   = os.environ.get("FYERS_CLIENT_ID")
FYERS_ACCESS_TOKEN = os.environ.get("FYERS_ACCESS_TOKEN")

# Hyperliquid API Credentials (public address)
HL_WALLET_ADDRESS = os.environ.get("HYPERLIQUID_WALLET_ADDRESS")

# Exness (FTMO-style REST) — no standard public API; will always use mock
EXNESS_API_KEY    = os.environ.get("EXNESS_API_KEY")

# Binance API Credentials
BINANCE_API_KEY    = os.environ.get("BINANCE_API_KEY")
BINANCE_API_SECRET = os.environ.get("BINANCE_API_SECRET")

# --- Helper function for dynamic fluctuation ---
def get_fluctuation_factor():
    """Generates a small time-based fluctuation to make mock data feel alive and real-time."""
    # Use current second to create a deterministic but changing small float
    current_sec = time.time()
    # Sinusoidal swing between -0.4% and +0.4% based on time
    swing = 0.004 * (time.sin(current_sec / 15.0) if hasattr(time, 'sin') else (int(current_sec) % 30 - 15) / 15.0)
    return 1.0 + swing

# Inject simple sine calculation
if not hasattr(time, 'sin'):
    import math
    time.sin = math.sin

# --- Mock Data Generator ---
def get_mock_portfolio(broker):
    """Generates realistic holdings and positions based on the broker name."""
    fluc = get_fluctuation_factor()
    
    if broker == "upstox":
        # Upstox mock portfolio (focused on large cap shares)
        holdings = [
            {"scrip": "RELIANCE", "qty": 120, "avg_price": 2450.0, "ltp": round(2520.0 * fluc, 2), "close": 2510.0},
            {"scrip": "TCS", "qty": 45, "avg_price": 3580.0, "ltp": round(3690.0 * fluc, 2), "close": 3660.0},
            {"scrip": "HDFCBANK", "qty": 210, "avg_price": 1520.0, "ltp": round(1495.0 * fluc, 2), "close": 1500.0},
        ]
        positions = [
            {"scrip": "SBIN", "qty": 300, "avg_price": 725.5, "ltp": round(734.20 * fluc, 2), "product": "MIS", "status": "OPEN"},
            {"scrip": "NIFTY28MAY22000CE", "qty": 75, "avg_price": 145.0, "ltp": round(162.50 * fluc, 2), "product": "NRML", "status": "OPEN"},
        ]
    elif broker == "dhan":
        # Dhan mock portfolio (focused on mid cap and tech)
        holdings = [
            {"scrip": "INFY", "qty": 80, "avg_price": 1420.0, "ltp": round(1475.0 * fluc, 2), "close": 1465.0},
            {"scrip": "TATAMOTORS", "qty": 150, "avg_price": 610.0, "ltp": round(935.0 * fluc, 2), "close": 928.0},
            {"scrip": "IREDA", "qty": 1000, "avg_price": 60.0, "ltp": round(178.50 * fluc, 2), "close": 172.0},
        ]
        positions = [
            {"scrip": "ZOMATO", "qty": 500, "avg_price": 185.0, "ltp": round(189.40 * fluc, 2), "product": "MIS", "status": "OPEN"},
        ]
    elif broker == "tradesmart":
        # TradeSmart mock portfolio (defensive / commodities / FMCG)
        holdings = [
            {"scrip": "ITC",       "qty": 350, "avg_price": 410.0,  "ltp": round(430.50 * fluc, 2), "close": 428.50},
            {"scrip": "LICI",      "qty": 75,  "avg_price": 940.0,  "ltp": round(995.0  * fluc, 2), "close": 985.0},
            {"scrip": "GOLD_BEES", "qty": 500, "avg_price": 54.2,   "ltp": round(61.80  * fluc, 2), "close": 61.50},
        ]
        positions = [
            {"scrip": "CRUDEOIL26MAY", "qty": 100, "avg_price": 6550.0, "ltp": round(6510.0 * fluc, 2), "product": "NRML", "status": "OPEN"},
        ]

    elif broker == "fyers":
        # Fyers mock portfolio (Indian equities CNC + short F&O)
        holdings = [
            {"scrip": "NSE:TATASTEEL-EQ", "qty": 400, "avg_price": 142.0, "ltp": round(156.80 * fluc, 2), "close": 155.0},
            {"scrip": "NSE:ADANIENT-EQ",  "qty": 60,  "avg_price": 2480.0, "ltp": round(2850.0 * fluc, 2), "close": 2830.0},
            {"scrip": "NSE:WIPRO-EQ",     "qty": 200, "avg_price": 420.0,  "ltp": round(468.50 * fluc, 2), "close": 465.0},
        ]
        positions = [
            {"scrip": "NSE:NIFTY28MAY22100PE", "qty": -50,  "avg_price": 92.0,   "ltp": round(67.50 * fluc, 2), "product": "NRML", "status": "OPEN"},
            {"scrip": "NSE:MIDCPNIFTY28MAY",   "qty":  25,  "avg_price": 1140.0,  "ltp": round(1185.0 * fluc, 2), "product": "MIS",  "status": "OPEN"},
        ]

    elif broker == "hyperliquid":
        # Hyperliquid mock (spot + decentralised perpetuals in USD)
        holdings = [
            {"scrip": "HYPE", "qty": 1200, "avg_price": 8.40,   "ltp": round(14.20 * fluc, 2),    "close": 14.05},
        ]
        positions = [
            {"scrip": "BTC-PERP",  "qty": 0.15,  "avg_price": 62000.0, "ltp": round(68400.0 * fluc, 2), "product": "PERP", "status": "OPEN"},
            {"scrip": "SOL-PERP",  "qty": 12.0,  "avg_price": 148.0,   "ltp": round(172.0  * fluc, 2), "product": "PERP", "status": "OPEN"},
            {"scrip": "HYPE-PERP", "qty": 500.0, "avg_price": 10.20,   "ltp": round(14.30  * fluc, 2), "product": "PERP", "status": "OPEN"},
        ]

    elif broker == "exness":
        # Exness mock (FX majors + metals, CFD platform — no equity holdings)
        holdings = []
        positions = [
            {"scrip": "EURUSD", "qty":  100000, "avg_price": 1.0812, "ltp": round(1.0874 * fluc, 5), "product": "CFD", "status": "OPEN"},
            {"scrip": "XAUUSD", "qty":  5,      "avg_price": 2300.0, "ltp": round(2385.0 * fluc, 2), "product": "CFD", "status": "OPEN"},
            {"scrip": "GBPJPY", "qty": -50000, "avg_price": 196.80, "ltp": round(198.50 * fluc, 2), "product": "CFD", "status": "OPEN"},
        ]

    elif broker == "binance":
        # Binance mock (spot token holdings + leveraged futures)
        holdings = [
            {"scrip": "BTC",  "qty": 0.42,  "avg_price": 55000.0, "ltp": round(68200.0 * fluc, 2), "close": 67500.0},
            {"scrip": "ETH",  "qty": 5.8,   "avg_price": 2800.0,  "ltp": round(3550.0  * fluc, 2), "close": 3480.0},
            {"scrip": "SOL",  "qty": 38.0,  "avg_price": 105.0,   "ltp": round(172.0   * fluc, 2), "close": 168.0},
        ]
        positions = [
            {"scrip": "DOGEUSDT", "qty": 50000, "avg_price": 0.098, "ltp": round(0.165 * fluc, 4), "product": "FUTURES", "status": "OPEN"},
        ]

    else:
        holdings  = []
        positions = []

    # Process holdings metrics
    processed_holdings = []
    for h in holdings:
        invested = h["qty"] * h["avg_price"]
        curr_val = h["qty"] * h["ltp"]
        pnl = curr_val - invested
        pnl_pct = (pnl / invested) * 100 if invested > 0 else 0.0
        # Today P&L = qty * (ltp - close)
        today_pnl = h["qty"] * (h["ltp"] - h["close"])
        
        processed_holdings.append({
            "scrip": h["scrip"],
            "broker": broker,
            "qty": h["qty"],
            "avg_price": h["avg_price"],
            "ltp": h["ltp"],
            "invested": round(invested, 2),
            "current_value": round(curr_val, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "today_pnl": round(today_pnl, 2),
        })

    # Process positions metrics
    processed_positions = []
    for p in positions:
        invested = abs(p["qty"]) * p["avg_price"]
        # Standard directional calculation: positive qty is long, negative is short
        pnl = p["qty"] * (p["ltp"] - p["avg_price"])
        today_pnl = p["qty"] * (p["ltp"] - p["avg_price"]) * 0.8 # Simulated today's action
        
        processed_positions.append({
            "scrip": p["scrip"],
            "broker": broker,
            "qty": p["qty"],
            "avg_price": p["avg_price"],
            "ltp": p["ltp"],
            "pnl": round(pnl, 2),
            "today_pnl": round(today_pnl, 2),
            "product": p["product"],
            "status": p["status"],
        })

    return processed_holdings, processed_positions

# --- Live Fetchers ---

def fetch_live_upstox():
    """Fetches holdings and positions from Upstox API."""
    if not UPSTOX_TOKEN:
        return None
        
    headers = {
        "Authorization": f"Bearer {UPSTOX_TOKEN}",
        "Accept": "application/json"
    }
    
    try:
        # 1. Fetch Holdings
        h_res = requests.get("https://api.upstox.com/v2/portfolio/long-term-holdings", headers=headers, timeout=8)
        # 2. Fetch Positions
        p_res = requests.get("https://api.upstox.com/v2/portfolio/short-term-positions", headers=headers, timeout=8)
        
        if h_res.status_code in (401, 403) or p_res.status_code in (401, 403):
            log.warning("[Upstox API] Unauthorized (%s/%s) - falling back to mock", h_res.status_code, p_res.status_code)
            return None

        holdings = []
        positions = []
        
        if h_res.status_code == 200:
            h_data = h_res.json().get("data", [])
            for item in h_data:
                qty = item.get("quantity", 0)
                avg_price = item.get("average_price", 0.0)
                ltp = item.get("last_price", 0.0)
                close = item.get("close_price", ltp)
                
                invested = qty * avg_price
                curr_val = qty * ltp
                pnl = curr_val - invested
                pnl_pct = (pnl / invested) * 100 if invested > 0 else 0.0
                today_pnl = qty * (ltp - close)
                
                holdings.append({
                    "scrip": item.get("trading_symbol", "UNKNOWN"),
                    "broker": "upstox",
                    "qty": qty,
                    "avg_price": avg_price,
                    "ltp": ltp,
                    "invested": round(invested, 2),
                    "current_value": round(curr_val, 2),
                    "pnl": round(pnl, 2),
                    "pnl_pct": round(pnl_pct, 2),
                    "today_pnl": round(today_pnl, 2)
                })
                
        if p_res.status_code == 200:
            p_data = p_res.json().get("data", [])
            for item in p_data:
                # Buy qty - Sell qty
                buy_qty = item.get("buy_quantity", 0)
                sell_qty = item.get("sell_quantity", 0)
                net_qty = buy_qty - sell_qty
                
                avg_price = item.get("average_price", 0.0)
                ltp = item.get("last_price", 0.0)
                pnl = item.get("pnl", 0.0)
                today_pnl = pnl # Upstox returns net pnl for positions
                
                positions.append({
                    "scrip": item.get("trading_symbol", "UNKNOWN"),
                    "broker": "upstox",
                    "qty": net_qty,
                    "avg_price": avg_price,
                    "ltp": ltp,
                    "pnl": round(pnl, 2),
                    "today_pnl": round(today_pnl, 2),
                    "product": item.get("product", "MIS"),
                    "status": "OPEN" if net_qty != 0 else "CLOSED"
                })
                
        return holdings, positions
    except Exception as e:
        log.error("[Upstox API Error] %s", e)
        return None

def fetch_live_dhan():
    """Fetches holdings and positions from Dhan API."""
    if not DHAN_ACCESS_TOKEN:
        return None
        
    headers = {
        "access-token": DHAN_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    
    try:
        # 1. Fetch Holdings
        h_res = requests.get("https://api.dhan.co/v2/holdings", headers=headers, timeout=8)
        # 2. Fetch Positions
        p_res = requests.get("https://api.dhan.co/v2/positions", headers=headers, timeout=8)
        
        if h_res.status_code in (401, 403) or p_res.status_code in (401, 403):
            log.warning("[Dhan API] Unauthorized (%s/%s) - falling back to mock", h_res.status_code, p_res.status_code)
            return None

        holdings = []
        positions = []
        
        if h_res.status_code == 200:
            h_data = h_res.json()
            # Dhan can return list directly or in a nested field
            h_list = h_data.get("data", h_data) if isinstance(h_data, dict) else h_data
            for item in h_list:
                qty = item.get("holdingQty", item.get("quantity", 0))
                avg_price = item.get("avgCostPrice", item.get("averagePrice", 0.0))
                ltp = item.get("lastTradedPrice", item.get("ltp", 0.0))
                close = item.get("prevClosePrice", ltp)
                
                invested = qty * avg_price
                curr_val = qty * ltp
                pnl = curr_val - invested
                pnl_pct = (pnl / invested) * 100 if invested > 0 else 0.0
                today_pnl = qty * (ltp - close)
                
                holdings.append({
                    "scrip": item.get("tradingSymbol", "UNKNOWN"),
                    "broker": "dhan",
                    "qty": qty,
                    "avg_price": avg_price,
                    "ltp": ltp,
                    "invested": round(invested, 2),
                    "current_value": round(curr_val, 2),
                    "pnl": round(pnl, 2),
                    "pnl_pct": round(pnl_pct, 2),
                    "today_pnl": round(today_pnl, 2)
                })
                
        if p_res.status_code == 200:
            p_data = p_res.json()
            p_list = p_data.get("data", p_data) if isinstance(p_data, dict) else p_data
            for item in p_list:
                net_qty = item.get("netQty", 0)
                avg_price = item.get("buyAvgPrice", 0.0)
                ltp = item.get("lastTradedPrice", 0.0)
                # Dhan direct P&L
                pnl = item.get("realizedProfitLoss", 0.0) + item.get("unrealizedProfitLoss", 0.0)
                
                positions.append({
                    "scrip": item.get("tradingSymbol", "UNKNOWN"),
                    "broker": "dhan",
                    "qty": net_qty,
                    "avg_price": avg_price,
                    "ltp": ltp,
                    "pnl": round(pnl, 2),
                    "today_pnl": round(pnl, 2), # Using current P&L as today P&L proxy
                    "product": item.get("productType", "MIS"),
                    "status": "OPEN" if net_qty != 0 else "CLOSED"
                })
                
        return holdings, positions
    except Exception as e:
        log.error("[Dhan API Error] %s", e)
        return None

def fetch_live_tradesmart():
    """Fetches holdings and positions from TradeSmart API (Noren OMS)."""
    if not all([TS_UID, TS_PWD, TS_FACTOR2, TS_VC, TS_API_KEY]):
        return None
        
    try:
        # Step 1: QuickAuth to get susertoken
        pwd_hash = hashlib.sha256(TS_PWD.encode()).hexdigest()
        appkey_src = TS_UID + TS_API_KEY
        appkey_hash = hashlib.sha256(appkey_src.encode()).hexdigest()
        
        j_data = {
            "apkversion": "1.0.0",
            "uid": TS_UID,
            "pwd": pwd_hash,
            "factor2": TS_FACTOR2,
            "vc": TS_VC,
            "appkey": appkey_hash,
            "imei": "12-34-56-78-90-AB",
            "source": "API"
        }
        
        auth_res = requests.post(
            f"{TS_BASE_URL}/QuickAuth", 
            data={"jData": json.dumps(j_data)}, 
            timeout=8
        )
        
        if auth_res.status_code != 200:
            return None
            
        auth_json = auth_res.json()
        if auth_json.get("stat") != "Ok":
            log.warning("[TradeSmart Auth Fail] %s", auth_json.get('emsg'))
            return None
            
        susertoken = auth_json.get("susertoken")
        
        # Step 2: Query Holdings
        h_payload = {"jData": json.dumps({"uid": TS_UID}), "jKey": susertoken}
        h_res = requests.post(f"{TS_BASE_URL}/Holdings", data=h_payload, timeout=8)
        
        # Step 3: Query Position Book
        p_payload = {"jData": json.dumps({"uid": TS_UID}), "jKey": susertoken}
        p_res = requests.post(f"{TS_BASE_URL}/PositionBook", data=p_payload, timeout=8)
        
        holdings = []
        positions = []
        
        if h_res.status_code == 200:
            h_data = h_res.json()
            if isinstance(h_data, list):
                for item in h_data:
                    # Noren returns holdings fields:
                    # prd: product, exch: exchange, tsym: trading symbol
                    # holdqty: quantity, upldprc: average upload price, ltp: last price
                    qty = int(item.get("holdqty", 0))
                    avg_price = float(item.get("upldprc", 0.0))
                    ltp = float(item.get("ltp", 0.0))
                    
                    invested = qty * avg_price
                    curr_val = qty * ltp
                    pnl = curr_val - invested
                    pnl_pct = (pnl / invested) * 100 if invested > 0 else 0.0
                    
                    holdings.append({
                        "scrip": item.get("tsym", "UNKNOWN"),
                        "broker": "tradesmart",
                        "qty": qty,
                        "avg_price": avg_price,
                        "ltp": ltp,
                        "invested": round(invested, 2),
                        "current_value": round(curr_val, 2),
                        "pnl": round(pnl, 2),
                        "pnl_pct": round(pnl_pct, 2),
                        "today_pnl": round(pnl * 0.1, 2) # Simulated daily share
                    })
                    
        if p_res.status_code == 200:
            p_data = p_res.json()
            if isinstance(p_data, list):
                for item in p_data:
                    # Noren position fields:
                    # netqty: net quantity, netavgprc: average price, urmtom: unrealized pnl, rpnl: realized pnl
                    net_qty = int(item.get("netqty", 0))
                    avg_price = float(item.get("netavgprc", 0.0))
                    ltp = float(item.get("ltp", 0.0))
                    pnl = float(item.get("urmtom", 0.0)) + float(item.get("rpnl", 0.0))
                    
                    positions.append({
                        "scrip": item.get("tsym", "UNKNOWN"),
                        "broker": "tradesmart",
                        "qty": net_qty,
                        "avg_price": avg_price,
                        "ltp": ltp,
                        "pnl": round(pnl, 2),
                        "today_pnl": round(pnl, 2),
                        "product": item.get("prd", "MIS"),
                        "status": "OPEN" if net_qty != 0 else "CLOSED"
                    })
                    
        return holdings, positions
    except Exception as e:
        log.error("[TradeSmart API Error] %s", e)
        return None

# --- Main Polling & Aggregation Core ---

def get_aggregated_portfolio():
    """Aggregates portfolio data from all brokers using dual live/mock channels."""
    brokers_data = {}
    all_holdings = []
    all_positions = []
    
    # 1. Poll Upstox
    upstox_res = fetch_live_upstox()
    if upstox_res is not None:
        h, p = upstox_res
        brokers_data["upstox"] = {"status": "active", "is_mock": False}
        all_holdings.extend(h)
        all_positions.extend(p)
    else:
        # Fallback to Mock
        h, p = get_mock_portfolio("upstox")
        brokers_data["upstox"] = {"status": "active", "is_mock": True}
        all_holdings.extend(h)
        all_positions.extend(p)
        
    # 2. Poll Dhan
    dhan_res = fetch_live_dhan()
    if dhan_res is not None:
        h, p = dhan_res
        brokers_data["dhan"] = {"status": "active", "is_mock": False}
        all_holdings.extend(h)
        all_positions.extend(p)
    else:
        # Fallback to Mock
        h, p = get_mock_portfolio("dhan")
        brokers_data["dhan"] = {"status": "active", "is_mock": True}
        all_holdings.extend(h)
        all_positions.extend(p)
        
    # 3. Poll TradeSmart
    ts_res = fetch_live_tradesmart()
    if ts_res is not None:
        h, p = ts_res
        brokers_data["tradesmart"] = {"status": "active", "is_mock": False}
        all_holdings.extend(h)
        all_positions.extend(p)
    else:
        h, p = get_mock_portfolio("tradesmart")
        brokers_data["tradesmart"] = {"status": "active", "is_mock": True}
        all_holdings.extend(h)
        all_positions.extend(p)

    # 4. Poll Fyers (always mock until live token provided)
    if FYERS_CLIENT_ID and FYERS_ACCESS_TOKEN:
        # Live Fyers integration placeholder — falls through to mock for now
        log.info("[Fyers] Credentials detected but live integration pending; using mock.")
    h, p = get_mock_portfolio("fyers")
    brokers_data["fyers"] = {"status": "active", "is_mock": True}
    all_holdings.extend(h)
    all_positions.extend(p)

    # 5. Poll Hyperliquid (public address based; always mock until address provided)
    if HL_WALLET_ADDRESS:
        log.info("[Hyperliquid] Wallet address detected but live integration pending; using mock.")
    h, p = get_mock_portfolio("hyperliquid")
    brokers_data["hyperliquid"] = {"status": "active", "is_mock": True}
    all_holdings.extend(h)
    all_positions.extend(p)

    # 6. Poll Exness (always mock — no standard public REST API)
    h, p = get_mock_portfolio("exness")
    brokers_data["exness"] = {"status": "active", "is_mock": True}
    all_holdings.extend(h)
    all_positions.extend(p)

    # 7. Poll Binance
    if BINANCE_API_KEY and BINANCE_API_SECRET:
        log.info("[Binance] Credentials detected but live integration pending; using mock.")
    h, p = get_mock_portfolio("binance")
    brokers_data["binance"] = {"status": "active", "is_mock": True}
    all_holdings.extend(h)
    all_positions.extend(p)

    # 4. Compute broker-level aggregates and overall metrics
    total_invested = 0.0
    current_value = 0.0
    today_pnl = 0.0
    
    # Initialize broker metrics
    for b in brokers_data:
        brokers_data[b].update({
            "invested": 0.0,
            "value": 0.0,
            "total_pnl": 0.0,
            "today_pnl": 0.0,
            "holdings_count": 0,
            "positions_count": 0
        })

    for h in all_holdings:
        b = h["broker"]
        brokers_data[b]["invested"] += h["invested"]
        brokers_data[b]["value"] += h["current_value"]
        brokers_data[b]["total_pnl"] += h["pnl"]
        brokers_data[b]["today_pnl"] += h["today_pnl"]
        brokers_data[b]["holdings_count"] += 1
        
        total_invested += h["invested"]
        current_value += h["current_value"]
        today_pnl += h["today_pnl"]

    for p in all_positions:
        b = p["broker"]
        # Add open position P&L to broker summaries
        brokers_data[b]["total_pnl"] += p["pnl"]
        brokers_data[b]["today_pnl"] += p["today_pnl"]
        brokers_data[b]["positions_count"] += 1
        
        current_value += p["pnl"] # P&L contributes directly to net portfolio value
        today_pnl += p["today_pnl"]

    # Round all broker numbers
    for b in brokers_data:
        brokers_data[b]["invested"] = round(brokers_data[b]["invested"], 2)
        brokers_data[b]["value"] = round(brokers_data[b]["value"], 2)
        brokers_data[b]["total_pnl"] = round(brokers_data[b]["total_pnl"], 2)
        brokers_data[b]["today_pnl"] = round(brokers_data[b]["today_pnl"], 2)

    total_pnl = current_value - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0
    today_pnl_pct = (today_pnl / total_invested * 100) if total_invested > 0 else 0.0

    return {
        "summary": {
            "total_invested": round(total_invested, 2),
            "current_value": round(current_value, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round(total_pnl_pct, 2),
            "today_pnl": round(today_pnl, 2),
            "today_pnl_pct": round(today_pnl_pct, 2),
            "updated_at": datetime.datetime.utcnow().isoformat()
        },
        "brokers": brokers_data,
        "holdings": all_holdings,
        "positions": all_positions
    }

if __name__ == "__main__":
    print("[Poller Test] Gathering aggregated portfolio...")
    res = get_aggregated_portfolio()
    print(json.dumps(res["summary"], indent=2))
    print(f"Total holdings fetched: {len(res['holdings'])}")
    print(f"Total positions fetched: {len(res['positions'])}")
