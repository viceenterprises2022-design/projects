#!/usr/bin/env python3
"""
Multi-Asset SaaS Web API (FastAPI)
Accepts TradingView alerts for Gold, BTC, and ETH.
Enforces subscription tier constraints, decrypts credentials,
runs orders on exchanges, and schedules Gemini risk reviews.
"""

import os
import hmac
import hashlib
import base64
import json
import time
import asyncio
import logging
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, Depends, BackgroundTasks, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv

import saas_multi_db as db
from multi_executor import MultiAssetExecutor

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

load_dotenv()

# Webhook secret token
WEBHOOK_SECRET_TOKEN = os.environ.get("WEBHOOK_SECRET_TOKEN", "supersecret_webhook_token")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
JWT_SECRET = os.environ.get("SaaS_JWT_SECRET", "supersecret_jwt_sign_key")

app = FastAPI(title="Hyperliquid & Gold Multi-Asset SaaS Portal API")
executor = MultiAssetExecutor(use_testnet=True)
security = HTTPBearer()

# Mount frontend directory
FRONTEND_DIR = Path(__file__).parent / "frontend"
app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")

# --- JWT Token Helper Functions ---

def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').replace('=', '')

def base64url_decode(data: str) -> bytes:
    padding = '=' * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)

def encode_jwt(payload: dict) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_enc = base64url_encode(json.dumps(header).encode('utf-8'))
    payload_enc = base64url_encode(json.dumps(payload).encode('utf-8'))
    signature = hmac.new(JWT_SECRET.encode('utf-8'), f"{header_enc}.{payload_enc}".encode('utf-8'), hashlib.sha256).digest()
    sig_enc = base64url_encode(signature)
    return f"{header_enc}.{payload_enc}.{sig_enc}"

def decode_jwt(token: str) -> dict:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid format")
        header_enc, payload_enc, sig_enc = parts
        expected_sig = hmac.new(JWT_SECRET.encode('utf-8'), f"{header_enc}.{payload_enc}".encode('utf-8'), hashlib.sha256).digest()
        if base64url_encode(expected_sig) != sig_enc:
            raise ValueError("Signature mismatch")
        payload = json.loads(base64url_decode(payload_enc).decode('utf-8'))
        if payload.get("exp") and payload["exp"] < time.time():
            raise ValueError("Expired token")
        return payload
    except Exception:
        return None

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    payload = decode_jwt(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired JWT token")
    return int(payload["user_id"])

# --- Pydantic Schemas ---

class LoginPayload(BaseModel):
    email: str
    password: str

class RegisterUserPayload(BaseModel):
    email: str
    password: str
    tier: str = "free" # free, pro, enterprise

class CredentialPayload(BaseModel):
    broker_name: str # hyperliquid, upstox, mock
    api_key: str
    api_secret: str
    wallet_address: Optional[str] = None

class StrategyPayload(BaseModel):
    symbol: str
    asset_type: str # crypto, commodity
    active: bool
    leverage: int
    size_pct: float
    stop_loss: float
    take_profit: float

class TVWebhookPayload(BaseModel):
    symbol: str
    action: str # BUY, SELL, CLOSE
    price: float
    size: float
    token: str

# --- HTML Serving ---

@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    dashboard_path = FRONTEND_DIR / "saas_multi_dashboard.html"
    return HTMLResponse(content=dashboard_path.read_text(), status_code=200)

# --- Authentication Endpoints ---

@app.post("/api/auth/register")
def register_user(payload: RegisterUserPayload):
    try:
        # Simple insecure hash for testing, upgrade to bcrypt in production
        hashed_password = hashlib.sha256(payload.password.encode()).hexdigest()
        uid = db.add_user(payload.email, hashed_password, role="user", tier=payload.tier)
        return {"success": True, "user_id": uid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registration failed: {e}")

@app.post("/api/auth/login")
def login_user(payload: LoginPayload):
    hashed_password = hashlib.sha256(payload.password.encode()).hexdigest()
    with db.get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (payload.email,)).fetchone()
        if not row or row["password_hash"] != hashed_password:
            raise HTTPException(status_code=401, detail="Invalid email or password")
            
        token = encode_jwt({"user_id": row["id"], "email": row["email"], "exp": time.time() + 86400})
        return {"token": token, "email": row["email"], "tier": row["tier"]}

# --- User Strategy & Credentials Configuration ---

@app.post("/api/user/credentials")
def save_credentials(payload: CredentialPayload, user_id: int = Depends(get_current_user_id)):
    try:
        db.add_user_credential(
            user_id=user_id,
            broker_name=payload.broker_name,
            api_key=payload.api_key,
            api_secret=payload.api_secret,
            wallet_address=payload.wallet_address
        )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to save credentials: {e}")

@app.post("/api/user/strategy")
def configure_strategy(payload: StrategyPayload, user_id: int = Depends(get_current_user_id)):
    # 1. Enforce Subscription Tier constraints
    user = db.get_user(user_id)
    tier = user["tier"]
    
    # Enforce maximum leverage constraints per tier
    if tier == "free" and payload.leverage > 5:
        raise HTTPException(status_code=403, detail="Leverage limited to 5x on Free subscription tier. Upgrade to Pro.")
    elif tier == "pro" and payload.leverage > 15:
        raise HTTPException(status_code=403, detail="Leverage limited to 15x on Pro subscription tier. Upgrade to Enterprise.")
        
    # Enforce strategy sizing constraints
    if tier == "free" and payload.size_pct > 5.0:
        raise HTTPException(status_code=403, detail="Order size limited to max 5.0% on Free tier.")
    elif tier == "pro" and payload.size_pct > 25.0:
        raise HTTPException(status_code=403, detail="Order size limited to max 25.0% on Pro tier.")
        
    # Enforce max position count limits on Free tier
    if tier == "free":
        positions = db.get_active_positions(user_id)
        if len(positions) >= 3 and payload.active:
            raise HTTPException(status_code=403, detail="Position count limit (3) exceeded on Free tier.")
            
    try:
        db.upsert_strategy_config(
            user_id=user_id,
            symbol=payload.symbol,
            asset_type=payload.asset_type,
            active=payload.active,
            leverage=payload.leverage,
            size_pct=payload.size_pct,
            stop_loss=payload.stop_loss,
            take_profit=payload.take_profit
        )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to map strategy: {e}")

# --- Webhook Processing gateway ---

def verify_webhook_token(payload: TVWebhookPayload):
    if payload.token != WEBHOOK_SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid webhook verification token")
    return payload

@app.post("/api/webhook/tradingview")
async def handle_webhook(payload: TVWebhookPayload = Depends(verify_webhook_token), background_tasks: BackgroundTasks = BackgroundTasks()):
    symbol = payload.symbol.upper()
    action = payload.action.upper()
    
    # 1. Fetch active user strategy maps for the asset
    configs = db.get_strategy_configs_for_symbol(symbol)
    if not configs:
        return {"status": "ignored", "reason": f"No active maps for {symbol}"}
        
    execution_list = []
    
    for cfg in configs:
        user_id = cfg["user_id"]
        broker = "hyperliquid" if "GOLD" not in symbol and "XAU" not in symbol else "mock"
        
        # Load decrypted keys from db
        creds = db.get_user_credentials(user_id, broker)
        if not creds:
            # Fallback to mock broker configuration
            creds = {"api_key": "mock_dev_key", "api_secret": "secret_xyz", "wallet_address": "0xmock"}
            
        # Dispatch order asynchronously
        background_tasks.add_task(
            execute_client_trade_task,
            user_id=user_id,
            creds=creds,
            symbol=symbol,
            side=action,
            size=payload.size,
            price=payload.price,
            cfg=cfg
        )
        execution_list.append({"user_id": user_id, "status": "queued"})
        
    return {"status": "enqueued", "executions": execution_list}

async def execute_client_trade_task(user_id: int, creds: dict, symbol: str, side: str, size: float, price: float, cfg: dict):
    try:
        res = executor.execute_trade(
            credential_cfg=creds,
            symbol=symbol,
            side=side,
            size=size,
            price=price
        )
        
        if res.get("success"):
            exec_price = res.get("price", price)
            tx_hash = res.get("tx_hash", "0xmock")
            
            # Log successful trade execution
            db.add_trade_log(
                user_id=user_id,
                symbol=symbol,
                side="LONG" if side == "BUY" else "SHORT",
                price=exec_price,
                size=size,
                pnl=0.0,
                trigger_type="TV_SIGNAL"
            )
            
            # Update positions tracking
            margin = (size * exec_price) / cfg["leverage"]
            tp_px = exec_price * (1.0 + cfg["hard_take_profit_pct"]/100.0) if side == "BUY" else exec_price * (1.0 - cfg["hard_take_profit_pct"]/100.0)
            sl_px = exec_price * (1.0 - cfg["hard_stop_loss_pct"]/100.0) if side == "BUY" else exec_price * (1.0 + cfg["hard_stop_loss_pct"]/100.0)
            
            db.upsert_active_position(
                user_id=user_id,
                symbol=symbol,
                side="LONG" if side == "BUY" else "SHORT",
                size=size,
                entry_price=exec_price,
                leverage=cfg["leverage"],
                margin=margin,
                tp_price=tp_px,
                sl_price=sl_px
            )
            log.info(f"[SaaS Multi-API] Successfully routed {side} trade for user {user_id} on {symbol}")
        else:
            log.error(f"[SaaS Multi-API] Order execution failed for user {user_id} on {symbol}: {res.get('error')}")
            
    except Exception as e:
        log.exception(f"[SaaS Multi-API] Task exception for user {user_id}: {e}")

# --- User API Dashboard ---

@app.get("/api/user/dashboard")
def get_user_dashboard(user_id: int = Depends(get_current_user_id)):
    user = db.get_user(user_id)
    positions = db.get_active_positions(user_id)
    trades = db.get_trade_logs(user_id, limit=20)
    latest_audit = db.get_latest_risk_audit()
    return {
        "user": {"id": user["id"], "email": user["email"], "tier": user["tier"], "role": user["role"]},
        "positions": positions,
        "recent_trades": trades,
        "latest_audit": latest_audit
    }

# --- Admin API Dashboard & AI Compliance ---

@app.get("/api/admin/dashboard")
def get_admin_metrics(user_id: int = Depends(get_current_user_id)):
    # Check admin role
    user = db.get_user(user_id)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required")
        
    users = db.get_active_users()
    positions = db.get_active_positions()
    trades = db.get_trade_logs(limit=30)
    latest_audit = db.get_latest_risk_audit()
    
    return {
        "users": [{"id": u["id"], "email": u["email"], "tier": u["tier"]} for u in users],
        "positions": positions,
        "recent_trades": trades,
        "latest_audit": latest_audit
    }

@app.post("/api/admin/audit")
async def trigger_ai_audit(background_tasks: BackgroundTasks, user_id: int = Depends(get_current_user_id)):
    user = db.get_user(user_id)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required")
        
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY env variable not set")
        
    background_tasks.add_task(run_offline_risk_audit)
    return {"status": "triggered"}

async def run_offline_risk_audit():
    """Gemini 3.5 Flash offline trade performance log analysis."""
    log.info("[SaaS Multi-API] Initiating multi-asset AI risk audit...")
    try:
        trades = db.get_trade_logs(limit=20)
        trade_logs = json.dumps(trades, indent=2)
        
        prompt = f"""
        Analyze these recent multi-asset client trade logs (Gold, BTC, ETH):
        {trade_logs}

        Tasks:
        1. Compile compliance report detailing metrics and leverage safety levels.
        2. Set recommended leverage ceilings and volatility multiplier.

        Your output must be structured exactly in JSON:
        {{
            "audit_report": "<detailed compliance review string>",
            "suggested_leverage_limit": <integer>,
            "daily_volatility_multiplier": <float>
        }}
        Output ONLY raw JSON. No markdown wrappers.
        """
        
        from google.antigravity import Agent, LocalAgentConfig
        config = LocalAgentConfig(api_key=GEMINI_API_KEY)
        async with Agent(config=config) as agent:
            response = await agent.chat(prompt)
            raw_text = await response.text()
            
        audit_data = json.loads(raw_text.strip())
        db.add_risk_audit(
            report=audit_data.get("audit_report", "Review completed successfully."),
            leverage_limit=int(audit_data.get("suggested_leverage_limit", 10)),
            volatility_mult=float(audit_data.get("daily_volatility_multiplier", 1.0))
        )
        log.info("[SaaS Multi-API] Risk audit log created successfully.")
    except Exception as e:
        log.exception(f"[SaaS Multi-API] Offline audit failed: {e}")

@app.on_event("startup")
def startup():
    db.init_db()
    # Add a default admin account if table is empty
    with db.get_conn() as conn:
        row = conn.execute("SELECT id FROM users WHERE role='admin'").fetchone()
        if not row:
            admin_pwd = hashlib.sha256("adminpassword".encode()).hexdigest()
            db.add_user("admin@alphaedge.com", admin_pwd, role="admin", tier="enterprise")
            log.info("[SaaS Multi-API] Seeded default admin account: admin@alphaedge.com / adminpassword")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("saas_multi_api:app", host="127.0.0.1", port=8900, reload=True)
