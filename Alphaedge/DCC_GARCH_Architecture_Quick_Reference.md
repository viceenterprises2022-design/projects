# DCC-GARCH → BUTTERFLY EFFECT ENGINE
## System Architecture & Quick Reference

---

## 🏗️ **SYSTEM ARCHITECTURE**

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA INGESTION LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Market Data Feeds (Real-time)                                 │
│  ├─ NSE (India): Nifty 50, Nifty Bank, Nifty IT               │
│  ├─ NYSE: S&P 500                                              │
│  ├─ KOSPI (Korea), TAIEX (Taiwan), HSI (Hong Kong)            │
│  ├─ Bovespa (Brazil), IPC (Mexico), JSE (South Africa)        │
│  └─ Commodities: Brent Oil, Gold, DXY, VIX                    │
│                                                                 │
│  Apache Kafka Topics:                                          │
│  • market.prices.tick    (every tick)                          │
│  • market.returns.daily  (EOD aggregation)                     │
│                                                                 │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   │ Raw price data
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│              DCC-GARCH CORRELATION ENGINE                       │
│                 (Your Implementation)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📊 Stage 1: GARCH(1,1) Volatility Models                      │
│     ├─ Fit per asset: σ²ₜ = ω + α·ε²ₜ₋₁ + β·σ²ₜ₋₁             │
│     ├─ Library: Python `arch` package                          │
│     └─ Output: {asset: {'omega', 'alpha', 'beta'}}            │
│                                                                 │
│  📐 Stage 2: Standardization                                   │
│     ├─ Compute: zₜ = rₜ / σₜ                                   │
│     └─ Output: Standardized residuals matrix (T × N)          │
│                                                                 │
│  🔄 Stage 3: DCC Recursion                                     │
│     ├─ Q̄ = unconditional correlation (fitted once)            │
│     ├─ Qₜ = (1-a-b)·Q̄ + a·(zₜ₋₁·zₜ₋₁') + b·Qₜ₋₁              │
│     ├─ Estimate (a, b) via MLE                                 │
│     └─ Update on every tick (real-time)                        │
│                                                                 │
│  ✨ Stage 4: Extract Correlation                               │
│     ├─ ρₜ = Q*ₜ^(-1/2) · Qₜ · Q*ₜ^(-1/2)                      │
│     ├─ Enforce: diag(ρₜ) = 1, ρₜ ∈ [-1, 1]                    │
│     └─ Output: 45×45 correlation matrix                        │
│                                                                 │
│  ⚡ Performance:                                                │
│     • Latency: <500ms per update (45 assets)                   │
│     • Optimization: Numba JIT compilation                       │
│     • Caching: Redis (5-min TTL)                               │
│                                                                 │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   │ Correlation matrix + volatilities
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API / STREAMING LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FastAPI Server (Python)                                       │
│  • REST: GET /correlations/current                             │
│  • WebSocket: ws://host/ws/correlations                        │
│                                                                 │
│  Payload Format (JSON):                                        │
│  {                                                              │
│    "timestamp": "2026-02-19T10:30:00Z",                        │
│    "links": [                                                   │
│      {                                                          │
│        "source": "NIFTY", "target": "SPX",                     │
│        "correlation": 0.72, "strength": 0.72,                  │
│        "color": "#10B981", "width": 3.6                        │
│      },                                                         │
│      { ... }                                                    │
│    ],                                                           │
│    "volatilities": {"NIFTY": 0.015, "SPX": 0.012, ...},       │
│    "regime": "Normal"  // or "Stress" or "Crisis"             │
│  }                                                              │
│                                                                 │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   │ WebSocket stream (1 update/sec)
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│            BUTTERFLY EFFECT ENGINE (Frontend)                   │
│                   (HTML5 Canvas + JavaScript)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📍 Nodes (Markets):                                           │
│     • Center: DXY, US 10Y (Epicenter)                          │
│     • Inner Ring: SPX, VIX, Oil, Gold (Primary)                │
│     • Outer: 45 EM markets organized by region                 │
│                                                                 │
│  🔗 Links (Correlations):                                      │
│     • Green: Positive correlation                              │
│     • Red: Inverse correlation                                 │
│     • Thickness: |ρ| × 5                                       │
│     • Opacity: |ρ| × 0.8                                       │
│                                                                 │
│  🌊 Shockwave Animation:                                       │
│     • Fed Hike → DXY pulse → ripple to EM (1.5s delay)        │
│     • Timing: transmissionTiming[node_id] from Granger model   │
│                                                                 │
│  🎨 Regime Visualization:                                      │
│     • Normal: Blue/Navy background                             │
│     • Stress: Amber tint                                       │
│     • Crisis: Red gradient + all nodes shake                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚡ **QUICK REFERENCE CARD**

### DCC-GARCH in 60 Seconds

| Stage | Formula | Output | Code Entry Point |
|-------|---------|--------|------------------|
| **1. GARCH** | σ²ᵢ,ₜ = ω + α·ε²ₜ₋₁ + β·σ²ₜ₋₁ | Volatility per asset | `arch_model(returns, vol='GARCH', p=1, q=1).fit()` |
| **2. Standardize** | zᵢ,ₜ = rᵢ,ₜ / σᵢ,ₜ | Z-scores (T×N) | `returns / volatilities` |
| **3. DCC** | Qₜ = (1-a-b)·Q̄ + a·(zₜ₋₁·zₜ₋₁') + b·Qₜ₋₁ | Q matrix (N×N) | `dcc_update_fast(Q_prev, z, Q_bar, a, b)` |
| **4. Correlation** | ρₜ = Q*ₜ^(-½) · Qₜ · Q*ₜ^(-½) | Correlation matrix | `extract_correlation_fast(Q_t)` |

### Typical Parameter Values

```python
# GARCH parameters (equity markets)
alpha = 0.05 - 0.15  # Reaction to shocks
beta  = 0.80 - 0.95  # Persistence
omega = 0.00001 - 0.0001  # Long-run variance

# DCC parameters
a = 0.01 - 0.05  # Correlation reaction speed
b = 0.90 - 0.98  # Correlation persistence
# Constraint: a + b < 1.0

# Nifty 50 example (India)
NIFTY_PARAMS = {
    'omega': 0.000018,
    'alpha': 0.082,
    'beta': 0.909,
    'a': 0.024,
    'b': 0.954
}
```

### Key Correlations (Normal Regime)

```
High Correlation (ρ > 0.70):
  • Nifty-SPX: 0.72
  • KOSPI-TAIEX: 0.74
  • Mexico-SPX: 0.82
  • Nifty Bank-DXY: -0.72 (inverse)

Medium Correlation (0.50 < ρ < 0.70):
  • Brazil-Oil: 0.68
  • Saudi-Oil: 0.89 (commodity exporter)
  • China-Nifty: 0.61

Low Correlation (ρ < 0.50):
  • Pakistan-SPX: 0.45
  • Vietnam-SPX: 0.52
  • Nigeria-SPX: 0.41
```

---

## 🔌 **INTEGRATION ENDPOINTS**

### Backend (FastAPI)

```python
# main.py

from fastapi import FastAPI, WebSocket
from dcc_garch_engine import DCCGARCHEngine

app = FastAPI()
engine = DCCGARCHEngine.load('model.pkl')

@app.get("/api/correlations/current")
async def get_current_correlations():
    """REST endpoint for latest correlation matrix."""
    return {
        "timestamp": datetime.now().isoformat(),
        "matrix": engine.get_latest_matrix().tolist(),
        "regime": engine.classify_regime()
    }

@app.websocket("/ws/correlations")
async def stream_correlations(websocket: WebSocket):
    """WebSocket for real-time streaming."""
    await websocket.accept()
    while True:
        correlation_matrix, vols = engine.update(get_latest_returns())
        await websocket.send_json(format_for_frontend(correlation_matrix, vols))
        await asyncio.sleep(1)  # 1 update/second
```

### Frontend (JavaScript)

```javascript
// butterfly-effect-engine.js

const ws = new WebSocket('ws://api.alphaedge.com/ws/correlations');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    // Update correlation links
    updateLinks(data.links);
    
    // Update node volatilities
    updateVolatilities(data.volatilities);
    
    // Change regime colors
    if (data.regime === 'Crisis') {
        canvas.style.background = CRISIS_GRADIENT;
        triggerShakeAnimation();
    }
    
    // Redraw
    requestAnimationFrame(draw);
};
```

---

## 📊 **DATA FLOW EXAMPLE**

### New Tick Arrives

```
Time: 10:30:00 AM IST

INPUT:
{
  "NIFTY": 0.0015,   // +0.15% move
  "SPX": 0.0008,     // +0.08% move
  "KOSPI": 0.0012,   // +0.12% move
  "BOVESPA": -0.0005,// -0.05% move
  ...
}

STAGE 1: Update GARCH volatilities
  NIFTY: σₜ = 0.0145 (1.45% daily vol)
  SPX: σₜ = 0.0118 (1.18% daily vol)

STAGE 2: Standardize
  NIFTY: zₜ = 0.0015 / 0.0145 = 0.103
  SPX: zₜ = 0.0008 / 0.0118 = 0.068

STAGE 3: DCC update
  Qₜ = 0.0224·Q̄ + 0.024·(zₜ₋₁·zₜ₋₁') + 0.954·Qₜ₋₁
  (45×45 matrix multiplication)

STAGE 4: Extract correlation
  ρ(NIFTY, SPX) = 0.726  (slightly up from 0.720 yesterday)

OUTPUT (to WebSocket):
{
  "timestamp": "2026-02-19T10:30:00Z",
  "links": [
    {
      "source": "NIFTY",
      "target": "SPX",
      "correlation": 0.726,
      "color": "#10B981",  // Green (positive)
      "width": 3.63        // 0.726 × 5
    },
    ...
  ],
  "regime": "Normal"
}

VISUALIZATION:
  Green line between Nifty and SPX nodes
  Thickness: 3.63px
  Opacity: 0.58 (0.726 × 0.8)
  No regime change (still Normal)
```

---

## 🎯 **TESTING CHECKLIST**

### Unit Tests

```python
def test_garch_parameters():
    """GARCH parameters should be in valid ranges."""
    assert 0 < alpha < 0.3
    assert 0.7 < beta < 0.99
    assert alpha + beta < 1.0

def test_correlation_bounds():
    """Correlations must be in [-1, 1]."""
    rho = engine.update(test_returns)
    assert np.all(rho >= -1) and np.all(rho <= 1)
    assert np.allclose(np.diag(rho), 1.0)

def test_regime_detection():
    """Test crisis detection."""
    # Simulate crisis (all correlations → 0.90+)
    crisis_returns = generate_crisis_scenario()
    rho = engine.update(crisis_returns)
    regime = classify_regime(rho)
    assert regime == 'Crisis'

def test_update_latency():
    """Update must be <500ms."""
    start = time.time()
    rho = engine.update(random_returns)
    latency = (time.time() - start) * 1000
    assert latency < 500
```

### Integration Tests

```python
def test_websocket_stream():
    """Test WebSocket data format."""
    async with websockets.connect('ws://localhost:8000/ws/correlations') as ws:
        msg = await ws.recv()
        data = json.loads(msg)
        
        assert 'timestamp' in data
        assert 'links' in data
        assert 'regime' in data
        assert all(abs(link['correlation']) <= 1 for link in data['links'])

def test_frontend_rendering():
    """Test canvas renders without errors."""
    selenium.get('http://localhost:3000')
    canvas = selenium.find_element_by_id('graph-canvas')
    
    # Trigger shockwave
    selenium.find_element_by_class('btn-fed').click()
    time.sleep(2)
    
    # Verify nodes animated
    assert canvas.is_displayed()
    assert no_js_errors()
```

---

## 🚨 **COMMON PITFALLS**

### 1. Forgetting to Standardize

```python
# ❌ WRONG: Using raw returns in DCC
Q_t = (1-a-b)*Q_bar + a*(returns @ returns.T) + b*Q_prev

# ✅ CORRECT: Use standardized residuals
z = returns / volatilities
Q_t = (1-a-b)*Q_bar + a*(z @ z.T) + b*Q_prev
```

### 2. Not Enforcing Stationarity

```python
# ❌ WRONG: No constraint on a+b
a, b = 0.05, 0.98  # Sum = 1.03 > 1 (unstable!)

# ✅ CORRECT: Enforce a+b < 1
bounds = [(0.001, 0.1), (0.80, 0.999)]
constraints = {'type': 'ineq', 'fun': lambda x: 0.999 - (x[0] + x[1])}
```

### 3. Integer Division Bug

```python
# ❌ WRONG: Integer division
inv_sqrt = 1 / np.sqrt(diag_Q)  # Works
D = np.diag(inv_sqrt)  # Also works
rho = D @ Q @ D  # Correct result

# But watch out for:
rho = np.diag(1/np.sqrt(diag_Q)) @ Q @ np.diag(1/np.sqrt(diag_Q))
# This works BUT is slower (creates diag matrix twice)
```

### 4. Not Handling NaN

```python
# ❌ WRONG: No NaN handling
if returns[asset] == 0:
    z = 0  # Wrong! Division by zero later

# ✅ CORRECT: Handle edge cases
if np.isnan(returns[asset]) or volatilities[asset] < 1e-8:
    z = 0  # Safe fallback
else:
    z = returns[asset] / volatilities[asset]
```

---

## 📦 **DEPLOYMENT**

### Docker Setup

```dockerfile
# Dockerfile

FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    libopenblas-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
WORKDIR /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml

version: '3.8'
services:
  correlation-engine:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - KAFKA_BROKER=kafka:9092
    depends_on:
      - redis
      - kafka
    restart: always
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    
  frontend:
    image: nginx:alpine
    volumes:
      - ./dist:/usr/share/nginx/html
    ports:
      - "80:80"
```

---

## 🎓 **LEARNING PATH**

1. ✅ **Read this guide** (you are here)
2. 📖 **Study original paper:** Engle & Sheppard (2001)
3. 💻 **Run example code:** Test with 2-asset system first
4. 🧪 **Validate on historical crisis:** March 2020 data
5. ⚡ **Optimize performance:** Add Numba JIT
6. 🔌 **Build API:** FastAPI + WebSocket
7. 🎨 **Connect to viz:** Butterfly Effect Engine
8. 🚀 **Deploy to production:** Docker + K8s

---

**You now have everything needed to implement the DCC-GARCH correlation engine. The Butterfly Effect visualization is waiting for your real-time correlation data! 🦋**
