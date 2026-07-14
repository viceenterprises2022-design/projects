#!/usr/bin/env python3
"""
Hyperliquid SaaS Bot Web API
FastAPI backend that accepts TradingView alerts, executes trades via hl_executor,
and performs offline risk reviews using Gemini.
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Header, Depends, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

import saas_db as db
from hl_executor import HyperliquidExecutor

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

load_dotenv()

# Webhook verification token
WEBHOOK_SECRET_TOKEN = os.environ.get("WEBHOOK_SECRET_TOKEN", "supersecret_webhook_token")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

app = FastAPI(title="Hyperliquid Commercial SaaS Trading Bot API")
executor = HyperliquidExecutor(use_testnet=True)

# Mount frontend directory
FRONTEND_DIR = Path(__file__).parent / "frontend"
app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")

@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    dashboard_path = FRONTEND_DIR / "saas_dashboard.html"
    return HTMLResponse(content=dashboard_path.read_text(), status_code=200)

# --- Pydantic Schemas ---

class TVWebhookPayload(BaseModel):
    symbol: str
    action: str  # BUY or SELL or CLOSE
    price: float
    size: float  # Base size (can be multiplied by user risk multiplier)
    token: str

class UserConfigPayload(BaseModel):
    email: str
    hl_wallet: str
    hl_api_key: str
    hl_api_secret: str
    risk_multiplier: float = 1.0
    max_leverage: int = 10

class StrategyConfigPayload(BaseModel):
    user_id: int
    symbol: str
    active: bool
    size_pct: float
    stop_loss: float
    take_profit: float

# --- Middleware / Helper Dependancy ---

def verify_token(payload: TVWebhookPayload):
    if payload.token != WEBHOOK_SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid webhook authentication token")
    return payload

# --- Startup Tasks ---

@app.on_event("startup")
def startup_event():
    db.init_db()
    log.info("[SaaS API] Database checked and initialized.")

# --- API Endpoints ---

@app.post("/api/webhook/tradingview")
async def handle_tradingview_webhook(payload: TVWebhookPayload = Depends(verify_token), background_tasks: BackgroundTasks = BackgroundTasks()):
    """
    Receives alerts from TradingView or a master signals engine,
    validates active configs, and triggers execution in parallel.
    """
    symbol = payload.symbol.upper()
    action = payload.action.upper()
    
    # 1. Fetch all active user strategies for this symbol
    configs = db.get_strategy_configs_for_symbol(symbol)
    if not configs:
        log.info(f"[SaaS API] No active strategies configured for {symbol}")
        return {"status": "ignored", "reason": f"No active user strategies for {symbol}"}
        
    # 2. Iterate and enqueue executions to avoid blocking incoming requests
    execution_results = []
    for cfg in configs:
        user_id = cfg["user_id"]
        # Calculate scaled order size based on user risk multiplier
        scaled_size = payload.size * cfg["risk_multiplier"]
        
        # Execute asynchronously in background
        background_tasks.add_task(
            execute_user_order_task,
            user_id=user_id,
            user_cfg=cfg,
            symbol=symbol,
            side=action,
            size=scaled_size,
            price=payload.price
        )
        execution_results.append({
            "user_id": user_id,
            "email": cfg.get("email"),
            "scaled_size": scaled_size,
            "status": "queued"
        })
        
    return {"status": "enqueued", "executions": execution_results}

async def execute_user_order_task(user_id: int, user_cfg: dict, symbol: str, side: str, size: float, price: float):
    """Execution helper running in the background thread."""
    try:
        # Call the Hyperliquid executor
        res = executor.execute_order(
            user_cfg=user_cfg,
            symbol=symbol,
            side=side,
            sz=size,
            price=price
        )
        
        if res.get("success"):
            exec_price = res.get("price", price)
            tx_hash = res.get("tx_hash", "0xmock")
            
            # Record trade in local DB log
            db.add_client_trade(
                user_id=user_id,
                symbol=symbol,
                side=side,
                price=exec_price,
                size=size,
                pnl=0.0,  # Zero for entry, calculated on exit
                trigger_type="TV_SIGNAL"
            )
            
            # Update local position tracking
            margin = (size * exec_price) / user_cfg["max_leverage"]
            
            # Simple take profit / stop loss levels calculation based on user config
            tp_px = exec_price * (1.0 + user_cfg["hard_take_profit_pct"]/100.0) if side == "BUY" else exec_price * (1.0 - user_cfg["hard_take_profit_pct"]/100.0)
            sl_px = exec_price * (1.0 - user_cfg["hard_stop_loss_pct"]/100.0) if side == "BUY" else exec_price * (1.0 + user_cfg["hard_stop_loss_pct"]/100.0)
            
            if side in ["BUY", "LONG"]:
                db.upsert_client_position(
                    user_id=user_id,
                    symbol=symbol,
                    side="LONG",
                    size=size,
                    entry_price=exec_price,
                    leverage=user_cfg["max_leverage"],
                    margin=margin,
                    tp_price=tp_px,
                    sl_price=sl_px
                )
            else:
                db.upsert_client_position(
                    user_id=user_id,
                    symbol=symbol,
                    side="SHORT",
                    size=size,
                    entry_price=exec_price,
                    leverage=user_cfg["max_leverage"],
                    margin=margin,
                    tp_price=tp_px,
                    sl_price=sl_px
                )
            log.info(f"[SaaS API] Executed order for user {user_id}: {side} {size} {symbol} at {exec_price}")
        else:
            log.error(f"[SaaS API] Execution failed for user {user_id}: {res.get('error')}")
            
    except Exception as e:
        log.exception(f"[SaaS API] Error executing trade task for user {user_id}: {e}")

# --- Dashboard & User Configurations ---

@app.get("/api/dashboard")
def get_dashboard_summary():
    """Aggregated stats for the global SaaS administrator dashboard."""
    users = db.get_active_users()
    latest_audit = db.get_latest_risk_audit()
    
    # Compile global metrics
    positions = []
    trades = []
    
    for u in users:
        uid = u["id"]
        positions.extend(db.get_client_positions(uid))
        trades.extend(db.get_client_trades(uid, limit=10))
        
    return {
        "active_users_count": len(users),
        "positions": positions,
        "recent_trades": sorted(trades, key=lambda x: x.get("id"), reverse=True)[:20],
        "latest_audit": latest_audit
    }

@app.post("/api/user/register")
def register_user(payload: UserConfigPayload):
    try:
        uid = db.add_user(
            email=payload.email,
            hl_wallet=payload.hl_wallet,
            hl_api_key=payload.hl_api_key,
            hl_api_secret=payload.hl_api_secret,
            risk_mult=payload.risk_multiplier,
            max_lev=payload.max_leverage
        )
        return {"success": True, "user_id": uid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registration failed: {e}")

@app.post("/api/user/strategy")
def set_strategy_config(payload: StrategyConfigPayload):
    try:
        db.upsert_strategy_config(
            user_id=payload.user_id,
            symbol=payload.symbol,
            active=payload.active,
            size_pct=payload.size_pct,
            stop_loss=payload.stop_loss,
            take_profit=payload.take_profit
        )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Configuration failed: {e}")

# --- Offline AI Risk Assessment task (Triggered via cron/backend task) ---

@app.post("/api/admin/audit")
async def trigger_ai_risk_audit(background_tasks: BackgroundTasks):
    """Admin endpoint to manually trigger the offline Gemini risk analysis."""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY environment variable not configured")
        
    background_tasks.add_task(run_offline_risk_audit)
    return {"status": "triggered"}

async def run_offline_risk_audit():
    """Offline background task querying Gemini 3.5 Flash for trade safety & parameter updates."""
    log.info("[SaaS API] Starting offline risk audit...")
    try:
        # Retrieve recent trades across all users
        users = db.get_active_users()
        recent_trades = []
        for u in users:
            recent_trades.extend(db.get_client_trades(u["id"], limit=5))
            
        trade_logs = json.dumps(recent_trades, indent=2)
        
        # Ask Gemini to review the trades safety
        prompt = f"""
        You are a Senior Risk Compliance System reviewing the trading logs of our multi-user Hyperliquid SaaS platform.
        Review the following executed trades:
        {trade_logs}

        Tasks:
        1. Compile a structured trade journal summary of the trades.
        2. Identify risk exposure concerns (e.g. position sizing, market regimes).
        3. Output a new max leverage limit recommendation (integer between 1 and 20) and a daily volatility multiplier adjustment (float between 0.5 and 1.5).

        Your output must be structured exactly in JSON format:
        {{
            "audit_report": "<Summary analysis and recommendations>",
            "suggested_leverage_limit": <integer>,
            "daily_volatility_multiplier": <float>
        }}
        Output ONLY the JSON object. Do not include markdown wraps like ```json.
        """
        
        from google.antigravity import Agent, LocalAgentConfig
        
        config = LocalAgentConfig(api_key=GEMINI_API_KEY)
        async with Agent(config=config) as agent:
            response = await agent.chat(prompt)
            raw_text = await response.text()
            
        # Parse JSON from Gemini
        audit_data = json.loads(raw_text.strip())
        
        # Save to database
        db.add_risk_audit(
            report=audit_data.get("audit_report", "No issues identified."),
            leverage_limit=int(audit_data.get("suggested_leverage_limit", 10)),
            volatility_mult=float(audit_data.get("daily_volatility_multiplier", 1.0))
        )
        log.info("[SaaS API] Offline risk audit saved successfully.")
        
    except Exception as e:
        log.exception(f"[SaaS API] Offline risk audit failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("saas_api:app", host="127.0.0.1", port=8899, reload=True)
