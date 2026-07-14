#!/usr/bin/env python3
"""
Multi-Asset Execution Manager (BTC, ETH, Gold)
Handles cryptographic execution via Hyperliquid for crypto assets,
market-hours checking and broker integration for Gold,
and simulated paper-trading fallbacks.
"""

import time
import datetime
import logging
import requests
from hl_executor import HyperliquidExecutor

log = logging.getLogger(__name__)

# Target timezone for MCX Gold is Indian Standard Time (IST, GMT+5:30)
class MultiAssetExecutor:
    def __init__(self, use_testnet=True):
        self.hl_executor = HyperliquidExecutor(use_testnet=use_testnet)
        
    def is_gold_market_open(self, now: datetime.datetime = None) -> bool:
        """
        Gold (MCX) trades weekdays: Monday-Friday from 9:00 AM to 11:30 PM IST.
        Returns True if market is currently open.
        """
        if now is None:
            # Get current time in UTC
            now = datetime.datetime.now(datetime.timezone.utc)
            
        # Convert UTC to IST (UTC + 5:30)
        ist_offset = datetime.timedelta(hours=5, minutes=30)
        ist_time = now + ist_offset
        
        weekday = ist_time.weekday() # 0 = Monday, 6 = Sunday
        hour = ist_time.hour
        minute = ist_time.minute
        
        # Weekends closed
        if weekday >= 5:
            return False
            
        # Monday - Friday trading windows: 09:00 to 23:30 IST
        time_in_minutes = hour * 60 + minute
        start_minutes = 9 * 60       # 09:00
        end_minutes = 23 * 60 + 30   # 23:30
        
        return start_minutes <= time_in_minutes <= end_minutes

    def execute_trade(self, credential_cfg: dict, symbol: str, side: str, size: float, price: float = None) -> dict:
        """
        Main execution router.
        Identifies asset class from symbol and executes via appropriate adapter.
        """
        symbol = symbol.upper()
        side = side.upper()
        
        # Route Gold (Commodity)
        if "GOLD" in symbol or "XAU" in symbol:
            # 1. Market hours guard
            if not self.is_gold_market_open():
                log.warning(f"[EXECUTOR] Gold trade rejected: Market is currently closed.")
                return {
                    "success": False, 
                    "error": "Gold commodity market is closed. Orders are only accepted Mon-Fri 09:00 - 23:30 IST."
                }
                
            return self._execute_gold(credential_cfg, symbol, side, size, price)
            
        # Route Crypto (BTC, ETH) via Hyperliquid
        else:
            return self.hl_executor.execute_order(
                user_cfg=credential_cfg,
                symbol=symbol,
                side=side,
                sz=size,
                price=price
            )

    def _execute_gold(self, creds: dict, symbol: str, side: str, size: float, price: float) -> dict:
        """Executes commodity orders via Upstox MCX API or Mock fallback."""
        api_key = creds.get("api_key")
        api_secret = creds.get("api_secret")
        
        is_mock = (
            not api_key or 
            not api_secret or 
            api_key.startswith("test") or 
            api_secret == "secret_xyz"
        )
        
        if is_mock:
            log.info(f"[MOCK BROKER] Gold Order: {side} {size} contracts of {symbol} at {price or 2400.0}")
            return {
                "success": True,
                "is_mock": True,
                "tx_hash": f"0xmock_gold_tx_{int(time.time())}",
                "price": price or 2400.0,
                "size": size
            }
            
        # Live Upstox MCX Order submission implementation outline
        # Endpoint: POST https://api.upstox.com/v2/order/place
        try:
            # Headers: Authorization: Bearer <api_secret> (which holds OAuth access token)
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {api_secret}"
            }
            
            # Construct standard order payload
            payload = {
                "quantity": int(size),
                "product": "I", # Intraday (or D for Delivery/Carry)
                "validity": "DAY",
                "price": price,
                "tag": "saas_bot",
                "instrument_token": "MCX_FO|251341", # Example token for Gold Futures
                "order_type": "LIMIT" if price else "MARKET",
                "transaction_type": side.upper() # BUY or SELL
            }
            
            # Post order request to broker API
            res = requests.post("https://api.upstox.com/v2/order/place", json=payload, headers=headers, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                if data.get("status") == "success":
                    return {
                        "success": True,
                        "is_mock": False,
                        "tx_hash": data.get("data", {}).get("order_id"),
                        "price": price or 2400.0,
                        "size": size
                    }
                else:
                    return {"success": False, "error": data.get("errors", [{}])[0].get("message", "Upstox execution error")}
            else:
                return {"success": False, "error": f"Broker HTTP {res.status_code}: {res.text}"}
                
        except Exception as e:
            log.exception(f"Live Upstox execution failed: {e}")
            return {"success": False, "error": str(e)}

if __name__ == "__main__":
    executor = MultiAssetExecutor()
    # Test market hours helper
    test_weekend = datetime.datetime(2026, 7, 12, 12, 0, 0, tzinfo=datetime.timezone.utc) # Sunday
    test_weekday_open = datetime.datetime(2026, 7, 13, 8, 0, 0, tzinfo=datetime.timezone.utc) # Monday 1:30 PM IST (GMT+5:30)
    
    print("Market open check (Sunday UTC):", executor.is_gold_market_open(test_weekend)) # Should be False
    print("Market open check (Monday 08:00 UTC = 13:30 IST):", executor.is_gold_market_open(test_weekday_open)) # Should be True
