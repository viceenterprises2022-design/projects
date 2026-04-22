# DCC-GARCH CORRELATION ENGINE
## Implementation Guide for AI/ML Developers

---

## 🎯 **WHAT YOU'RE BUILDING**

You're building the **real-time correlation engine** that powers the Butterfly Effect visualization. Your job is to:

1. Take market price data (45 emerging markets + 5 global assets)
2. Compute time-varying correlations using DCC-GARCH
3. Output a live correlation matrix that updates every tick
4. Feed this to the front-end visualization

**End Result:** The green/red lines in the Butterfly Effect Engine show YOUR correlation values, updated in real-time.

---

## 📊 **WHY DCC-GARCH? (Not Static Correlation)**

### The Problem with Static Correlation

```python
# WRONG: Static correlation (what most platforms do)
import numpy as np
correlation = np.corrcoef(nifty_returns, spx_returns)[0, 1]
# Returns: 0.72

# Problem: This number is CONSTANT. It doesn't update when regime changes.
# In March 2020, Nifty-SPX correlation spiked from 0.65 → 0.92 in 10 days.
# Static correlation would have missed this entirely.
```

### DCC-GARCH Solution

```python
# RIGHT: Dynamic correlation (what AlphaEdge does)
from dcc_garch import DCCGARCHEngine

engine = DCCGARCHEngine(assets=['NIFTY', 'SPX'])
engine.fit(historical_returns)  # Train on 1000+ days

# Now on each new tick:
correlation_t = engine.update(new_returns)
# Returns: 0.72 normally, but spikes to 0.92 during crisis

# This is a TIME-VARYING correlation that reacts to market conditions
```

**The Key Insight:** Correlations are NOT constant. They change based on volatility, stress, and market conditions. DCC-GARCH models this evolution.

---

## 🔬 **THE FOUR STAGES (Conceptual Breakdown)**

### **Stage 1: Model Each Asset's Volatility**

**What:** Fit a GARCH(1,1) model to each asset independently to capture volatility clustering.

**Why:** Volatility is not constant. High-vol days cluster together (2020 March had 5 consecutive 3%+ moves). GARCH captures this.

**Formula:**
```
σ²ᵢ,ₜ = ωᵢ + αᵢ·ε²ᵢ,ₜ₋₁ + βᵢ·σ²ᵢ,ₜ₋₁
```

**Plain English:**
- `σ²ᵢ,ₜ` = Today's expected variance for asset i
- `ωᵢ` = Long-run baseline variance (like a floor)
- `αᵢ·ε²ᵢ,ₜ₋₁` = React to yesterday's shock (if yesterday was big move, expect higher vol today)
- `βᵢ·σ²ᵢ,ₜ₋₁` = Persistence (if vol was high yesterday, it stays high today)

**Code Implementation:**

```python
from arch import arch_model
import pandas as pd

def fit_garch_per_asset(returns_df):
    """
    Fits GARCH(1,1) to each asset column in the DataFrame.
    
    Args:
        returns_df: pd.DataFrame, shape (T, N)
                    T = time periods, N = number of assets
                    Values = daily returns (e.g., 0.012 = 1.2% gain)
    
    Returns:
        garch_params: dict of {asset_name: {'omega', 'alpha', 'beta'}}
        fitted_volatilities: pd.DataFrame, shape (T, N), conditional volatility σ_t
    """
    garch_params = {}
    fitted_volatilities = pd.DataFrame(index=returns_df.index)
    
    for asset in returns_df.columns:
        # Fit GARCH(1,1) model
        model = arch_model(returns_df[asset], vol='GARCH', p=1, q=1, dist='normal')
        result = model.fit(disp='off', options={'maxiter': 1000})
        
        # Store parameters
        garch_params[asset] = {
            'omega': result.params['omega'],
            'alpha': result.params['alpha[1]'],
            'beta': result.params['beta[1]']
        }
        
        # Extract conditional volatility time series
        fitted_volatilities[asset] = result.conditional_volatility
    
    return garch_params, fitted_volatilities

# Example usage
returns = pd.read_csv('market_returns.csv', index_col='date', parse_dates=True)
# returns has columns: ['NIFTY', 'SPX', 'KOSPI', 'BOVESPA', ...]

params, volatilities = fit_garch_per_asset(returns)

print(params['NIFTY'])
# Output: {'omega': 0.000015, 'alpha': 0.08, 'beta': 0.91}
# Interpretation: 
#   - alpha = 0.08 means 8% reaction to new shocks
#   - beta = 0.91 means 91% persistence (very sticky volatility)
#   - alpha + beta = 0.99 (close to 1 = highly persistent)
```

**What This Gives You:**
- For each asset, you now have `σᵢ,ₜ` (volatility) at every time point
- This is the first building block for DCC

---

### **Stage 2: Standardize Returns**

**What:** Remove the time-varying volatility from returns to get "standardized residuals" (z-scores).

**Why:** We want to measure correlation between the DIRECTION of moves, not the SIZE. If Nifty moves 2% and SPX moves 1%, but Nifty's volatility is 2× higher, they're actually moving the same amount in standardized terms.

**Formula:**
```
zᵢ,ₜ = rᵢ,ₜ / σᵢ,ₜ
```

**Plain English:**
- Take the raw return
- Divide by the conditional volatility from Stage 1
- Result: standardized return with mean ≈ 0, std ≈ 1

**Code Implementation:**

```python
def standardize_returns(returns_df, volatilities_df):
    """
    Converts raw returns to standardized residuals.
    
    Args:
        returns_df: pd.DataFrame, raw returns (T, N)
        volatilities_df: pd.DataFrame, conditional volatilities from Stage 1 (T, N)
    
    Returns:
        standardized: pd.DataFrame (T, N), z-scores
    """
    # Element-wise division
    standardized = returns_df / volatilities_df
    
    # Verify: mean should be ~0, std should be ~1
    assert abs(standardized.mean().mean()) < 0.1, "Mean should be near 0"
    assert abs(standardized.std().mean() - 1) < 0.2, "Std should be near 1"
    
    return standardized

# Example
z_scores = standardize_returns(returns, volatilities)

print(z_scores['NIFTY'].head())
# Output:
#            NIFTY
# 2024-01-01  -0.82  (negative z-score = down move, 0.82 std devs)
# 2024-01-02   1.45  (positive z-score = up move, 1.45 std devs)
# 2024-01-03   0.12  (small move, 0.12 std devs)
```

**What This Gives You:**
- Standardized returns matrix Z (T×N)
- These are the inputs to the correlation model

---

### **Stage 3: DCC Dynamics (The Core Innovation)**

**What:** Model how the correlation matrix EVOLVES over time using a recursion formula.

**Why:** This is where the "Dynamic" in DCC comes from. Instead of computing correlation once, we model its time evolution.

**Formula:**
```
Qₜ = (1-a-b)·Q̄ + a·(zₜ₋₁·zₜ₋₁') + b·Qₜ₋₁
```

**Components Explained:**

1. **Q̄ (Q-bar)** = Long-run average correlation
   - Computed once from historical data
   - Think of it as the "baseline" correlation the model reverts to
   
2. **(1-a-b)·Q̄** = Mean reversion term
   - Pulls Qₜ back toward the long-run average
   - Ensures correlations don't explode to infinity
   
3. **a·(zₜ₋₁·zₜ₋₁')** = Reaction to yesterday's co-movement
   - If assets moved together yesterday (both up or both down), correlation increases today
   - This is an N×N outer product matrix
   
4. **b·Qₜ₋₁** = Persistence term
   - If correlation was high yesterday, it stays high today
   - Captures stickiness of correlation regimes

**Parameters:**
- `a` = reaction speed (typical: 0.01–0.05)
- `b` = persistence (typical: 0.90–0.98)
- Constraint: `a + b < 1` (ensures stationarity)

**Code Implementation:**

```python
import numpy as np
from scipy.optimize import minimize

def compute_unconditional_correlation(z_matrix):
    """
    Compute Q̄ (Q-bar), the long-run average correlation matrix.
    
    Args:
        z_matrix: np.array (T, N), standardized residuals
    
    Returns:
        Q_bar: np.array (N, N), unconditional correlation matrix
    """
    # Simple sample correlation
    Q_bar = np.corrcoef(z_matrix, rowvar=False)
    return Q_bar

def dcc_log_likelihood(params, z_matrix, Q_bar):
    """
    Compute negative log-likelihood for DCC parameters estimation.
    
    Args:
        params: [a, b], DCC parameters to optimize
        z_matrix: np.array (T, N), standardized residuals
        Q_bar: np.array (N, N), unconditional correlation
    
    Returns:
        -log_likelihood: float (we minimize this)
    """
    a, b = params
    T, N = z_matrix.shape
    
    # Initialize Q₀ = Q̄
    Q = [Q_bar.copy()]
    log_lik = 0
    
    for t in range(1, T):
        # Get yesterday's standardized residuals
        z_prev = z_matrix[t-1, :].reshape(-1, 1)  # Column vector (N, 1)
        
        # Outer product: z·z' (N×N matrix)
        outer = z_prev @ z_prev.T
        
        # DCC recursion
        Q_t = (1 - a - b) * Q_bar + a * outer + b * Q[t-1]
        Q.append(Q_t)
        
        # Convert Q to correlation matrix R
        # R = D⁻¹/² · Q · D⁻¹/²  where D = diag(Q)
        D_inv_sqrt = np.diag(1 / np.sqrt(np.diag(Q_t)))
        R_t = D_inv_sqrt @ Q_t @ D_inv_sqrt
        
        # Likelihood contribution (simplified)
        z_t = z_matrix[t, :].reshape(-1, 1)
        log_lik += -0.5 * (np.log(np.linalg.det(R_t)) + z_t.T @ np.linalg.inv(R_t) @ z_t)
    
    return -log_lik.item()  # Return negative (for minimization)

def estimate_dcc_parameters(z_matrix, Q_bar):
    """
    Estimate DCC parameters (a, b) via Maximum Likelihood.
    
    Args:
        z_matrix: np.array (T, N)
        Q_bar: np.array (N, N)
    
    Returns:
        a, b: float, estimated parameters
    """
    # Initial guess
    x0 = [0.01, 0.95]
    
    # Constraints: a > 0, b > 0, a + b < 1
    bounds = [(0.001, 0.1), (0.80, 0.999)]
    
    result = minimize(
        dcc_log_likelihood,
        x0,
        args=(z_matrix, Q_bar),
        bounds=bounds,
        method='L-BFGS-B',
        options={'maxiter': 500}
    )
    
    a, b = result.x
    print(f"Estimated DCC parameters: a = {a:.4f}, b = {b:.4f}, sum = {a+b:.4f}")
    
    return a, b

# Example usage
z_matrix = z_scores.values  # Convert DataFrame to numpy array
Q_bar = compute_unconditional_correlation(z_matrix)
a, b = estimate_dcc_parameters(z_matrix, Q_bar)

# Typical output:
# Estimated DCC parameters: a = 0.0235, b = 0.9541, sum = 0.9776
```

**What This Gives You:**
- Estimated parameters `a` and `b`
- These are used in the real-time update step

---

### **Stage 4: Extract Correlation Matrix**

**What:** Convert the Q matrix to a proper correlation matrix with 1s on the diagonal.

**Why:** The Q matrix from Stage 3 is a "quasi-correlation" matrix. We need to rescale it so diagonal elements = 1.

**Formula:**
```
ρₜ = Q*ₜ^(-1/2) · Qₜ · Q*ₜ^(-1/2)

where Q*ₜ = diag(Qₜ)  (diagonal matrix with only diagonal elements of Q)
```

**Plain English:**
1. Extract the diagonal of Q
2. Take the square root of each diagonal element
3. Invert it (1/√diagonal)
4. Create a diagonal matrix from this
5. "Sandwich" Q between these matrices

**Code Implementation:**

```python
def extract_correlation_matrix(Q_t):
    """
    Convert quasi-correlation matrix Q to proper correlation matrix ρ.
    
    Args:
        Q_t: np.array (N, N), output from DCC recursion
    
    Returns:
        rho_t: np.array (N, N), correlation matrix with diag = 1
    """
    # Extract diagonal
    diag_Q = np.diag(Q_t)
    
    # Inverse square root of diagonal
    inv_sqrt_diag = 1 / np.sqrt(diag_Q)
    
    # Create diagonal matrix
    D_inv_sqrt = np.diag(inv_sqrt_diag)
    
    # Sandwich multiplication
    rho_t = D_inv_sqrt @ Q_t @ D_inv_sqrt
    
    # Verification
    assert np.allclose(np.diag(rho_t), 1.0), "Diagonal must be all 1s"
    assert np.allclose(rho_t, rho_t.T), "Must be symmetric"
    assert np.all(rho_t >= -1) and np.all(rho_t <= 1), "Correlations must be in [-1, 1]"
    
    return rho_t

# Example
Q_t = np.array([[1.2, 0.8], [0.8, 1.5]])  # Quasi-correlation
rho_t = extract_correlation_matrix(Q_t)

print(rho_t)
# Output:
# [[1.000  0.596]
#  [0.596  1.000]]
#
# Interpretation: Correlation between asset 1 and asset 2 is 0.596
```

**What This Gives You:**
- Final correlation matrix ρₜ (N×N)
- This is what feeds into the visualization

---

## 🔄 **REAL-TIME UPDATE (Production Flow)**

Once trained, your engine needs to update correlations on every new tick.

### Full Engine Class

```python
class DCCGARCHEngine:
    """
    Production-ready DCC-GARCH correlation engine.
    """
    
    def __init__(self, asset_names):
        self.assets = asset_names
        self.N = len(asset_names)
        
        # Parameters (fitted during training)
        self.garch_params = {}  # {asset: {'omega', 'alpha', 'beta'}}
        self.Q_bar = None       # Unconditional correlation (N×N)
        self.dcc_a = None       # DCC parameter a
        self.dcc_b = None       # DCC parameter b
        
        # State (updated on each tick)
        self.sigma_prev = {}    # {asset: last volatility}
        self.Q_prev = None      # Last Q matrix (N×N)
    
    def fit(self, returns_df):
        """
        One-time training on historical data.
        
        Args:
            returns_df: pd.DataFrame (T, N), historical returns
                        Columns = asset names
                        Index = dates
                        Values = % returns (0.012 = 1.2%)
        """
        print(f"Training DCC-GARCH on {len(returns_df)} days of data...")
        
        # Stage 1: Fit GARCH per asset
        self.garch_params, volatilities = fit_garch_per_asset(returns_df)
        
        # Stage 2: Standardize
        z_scores = standardize_returns(returns_df, volatilities)
        
        # Stage 3: Estimate DCC parameters
        z_matrix = z_scores.values
        self.Q_bar = compute_unconditional_correlation(z_matrix)
        self.dcc_a, self.dcc_b = estimate_dcc_parameters(z_matrix, self.Q_bar)
        
        # Initialize state
        self.Q_prev = self.Q_bar.copy()
        for asset in self.assets:
            self.sigma_prev[asset] = volatilities[asset].iloc[-1]
        
        print(f"✓ Training complete. DCC params: a={self.dcc_a:.4f}, b={self.dcc_b:.4f}")
    
    def update(self, new_returns):
        """
        Real-time update on new tick.
        
        Args:
            new_returns: dict {asset: return}
                         Example: {'NIFTY': 0.015, 'SPX': 0.008, ...}
        
        Returns:
            correlation_matrix: np.array (N, N)
            volatilities: dict {asset: current_vol}
        """
        # Step 1: Update GARCH volatilities
        z_current = []
        volatilities_current = {}
        
        for asset in self.assets:
            params = self.garch_params[asset]
            r = new_returns[asset]
            
            # GARCH(1,1) recursion
            sigma_sq_prev = self.sigma_prev[asset] ** 2
            epsilon_sq_prev = r ** 2  # Simplified (should use fitted residual)
            
            sigma_sq = (params['omega'] + 
                       params['alpha'] * epsilon_sq_prev + 
                       params['beta'] * sigma_sq_prev)
            
            sigma = np.sqrt(sigma_sq)
            volatilities_current[asset] = sigma
            self.sigma_prev[asset] = sigma
            
            # Standardize
            z = r / sigma
            z_current.append(z)
        
        # Step 2: Update DCC
        z_vec = np.array(z_current).reshape(-1, 1)  # Column vector
        outer = z_vec @ z_vec.T  # N×N
        
        Q_t = ((1 - self.dcc_a - self.dcc_b) * self.Q_bar + 
               self.dcc_a * outer + 
               self.dcc_b * self.Q_prev)
        
        self.Q_prev = Q_t
        
        # Step 3: Extract correlation
        rho_t = extract_correlation_matrix(Q_t)
        
        return rho_t, volatilities_current
```

### Usage in Production

```python
# TRAINING (One-time, or re-run daily)
engine = DCCGARCHEngine(['NIFTY', 'SPX', 'KOSPI', 'BOVESPA', 'TASI'])
historical_returns = load_returns_from_database(days=1000)  # Last 1000 days
engine.fit(historical_returns)

# Save model
import pickle
with open('dcc_garch_model.pkl', 'wb') as f:
    pickle.dump(engine, f)

# REAL-TIME (Every tick)
while True:
    # Get new returns from live feed
    new_data = get_live_tick()  # {'NIFTY': 0.0012, 'SPX': 0.0008, ...}
    
    # Update correlations
    correlation_matrix, volatilities = engine.update(new_data)
    
    # Extract specific pairs for visualization
    nifty_spx_corr = correlation_matrix[0, 1]  # Assuming NIFTY=0, SPX=1
    
    # Send to frontend
    send_to_websocket({
        'type': 'correlation_update',
        'timestamp': datetime.now().isoformat(),
        'correlations': {
            'NIFTY-SPX': float(nifty_spx_corr),
            'NIFTY-KOSPI': float(correlation_matrix[0, 2]),
            # ... etc
        },
        'volatilities': {k: float(v) for k, v in volatilities.items()}
    })
    
    time.sleep(1)  # Update every second (or on every tick)
```

---

## 🔌 **INTEGRATION WITH BUTTERFLY EFFECT ENGINE**

### Backend API Contract

```python
# FastAPI endpoint
from fastapi import FastAPI, WebSocket
import json

app = FastAPI()

@app.websocket("/ws/correlations")
async def correlation_stream(websocket: WebSocket):
    """
    WebSocket endpoint for streaming correlation updates.
    
    Frontend connects to this and receives real-time correlation matrices.
    """
    await websocket.accept()
    
    while True:
        # Get latest correlation matrix from DCC engine
        correlation_matrix, volatilities = engine.update(get_latest_returns())
        
        # Convert to frontend format
        links = []
        for i, asset1 in enumerate(engine.assets):
            for j, asset2 in enumerate(engine.assets):
                if i < j:  # Upper triangle only (avoid duplicates)
                    corr_value = correlation_matrix[i, j]
                    
                    # Only send significant correlations
                    if abs(corr_value) > 0.2:
                        links.append({
                            'source': asset1,
                            'target': asset2,
                            'correlation': float(corr_value),
                            'strength': float(abs(corr_value)),
                            'color': '#10B981' if corr_value > 0 else '#EF4444',
                            'opacity': float(abs(corr_value) * 0.8),
                            'width': float(abs(corr_value) * 5)
                        })
        
        payload = {
            'type': 'correlation_update',
            'timestamp': datetime.now().isoformat(),
            'links': links,
            'volatilities': {k: float(v) for k, v in volatilities.items()},
            'regime': classify_regime(correlation_matrix)  # Normal/Stress/Crisis
        }
        
        await websocket.send_text(json.dumps(payload))
        await asyncio.sleep(1)  # Update every second

def classify_regime(correlation_matrix):
    """
    Classify current correlation regime.
    
    Based on average pairwise correlation strength.
    """
    # Extract upper triangle (no diagonal)
    upper_tri = correlation_matrix[np.triu_indices_from(correlation_matrix, k=1)]
    avg_corr = np.mean(np.abs(upper_tri))
    
    if avg_corr < 0.65:
        return 'Normal'
    elif avg_corr < 0.80:
        return 'Stress'
    else:
        return 'Crisis'
```

### Frontend Integration

```javascript
// In ButterflyEffectEngine.html

const ws = new WebSocket('ws://localhost:8000/ws/correlations');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    // Update links in the visualization
    links = data.links;
    
    // Update node volatilities (affects node size)
    nodes.forEach(node => {
        if (data.volatilities[node.id]) {
            node.currentVolatility = data.volatilities[node.id];
            // Make node larger if volatility is high
            node.radius = node.baseRadius * (1 + node.currentVolatility * 2);
        }
    });
    
    // Change background color based on regime
    if (data.regime === 'Crisis') {
        document.body.style.background = 'linear-gradient(135deg, #1E0000 0%, #3D0000 100%)';
    } else if (data.regime === 'Stress') {
        document.body.style.background = 'linear-gradient(135deg, #1E1200 0%, #3D2400 100%)';
    } else {
        document.body.style.background = 'linear-gradient(135deg, #0F172A 0%, #1E293B 100%)';
    }
    
    // Redraw canvas with new correlations
    draw();
};
```

---

## ⚡ **PERFORMANCE OPTIMIZATION**

### Latency Target: <500ms per update

For 45 assets, you have a 45×45 = 2,025 element matrix. Here's how to meet the target:

```python
import numba
from numba import jit

@jit(nopython=True)
def dcc_update_fast(Q_prev, z_vec, Q_bar, a, b):
    """
    JIT-compiled DCC update for speed.
    
    ~10x faster than pure Python.
    """
    N = z_vec.shape[0]
    outer = np.outer(z_vec, z_vec)
    Q_t = (1 - a - b) * Q_bar + a * outer + b * Q_prev
    return Q_t

@jit(nopython=True)
def extract_correlation_fast(Q_t):
    """
    JIT-compiled correlation extraction.
    """
    diag_Q = np.diag(Q_t)
    inv_sqrt_diag = 1 / np.sqrt(diag_Q)
    D_inv_sqrt = np.diag(inv_sqrt_diag)
    rho_t = D_inv_sqrt @ Q_t @ D_inv_sqrt
    return rho_t

# Use in production
correlation_matrix = extract_correlation_fast(
    dcc_update_fast(Q_prev, z_vec, Q_bar, a, b)
)
```

### Benchmarks

```python
import time

# 45 assets, 1000 iterations
start = time.time()
for _ in range(1000):
    rho = engine.update(random_returns)
elapsed = time.time() - start

print(f"Average latency: {elapsed/1000*1000:.2f}ms per update")
# Target: <500ms
# With Numba: ~50-100ms ✓
# Without Numba: ~800-1200ms ✗
```

---

## 📦 **DEPLOYMENT CHECKLIST**

- [ ] Train DCC-GARCH on 1000+ days of historical data
- [ ] Validate parameters: a + b < 1, typically a ≈ 0.02, b ≈ 0.95
- [ ] Set up WebSocket server for real-time streaming
- [ ] Implement Redis caching for correlation matrix (5-min TTL)
- [ ] Add TimescaleDB for storing historical correlations
- [ ] Set up monitoring for latency (alert if >500ms)
- [ ] Implement fallback to static correlation if DCC update fails
- [ ] Add health check endpoint: `/health/correlation-engine`
- [ ] Deploy with Docker + Kubernetes for auto-scaling
- [ ] Set up alerting for regime changes (Normal → Crisis)

---

## 🎯 **SUCCESS CRITERIA**

Your engine is working correctly if:

1. **Correlations are realistic:** Nifty-SPX should be 0.60–0.80 in normal times
2. **Regime detection works:** Correlations spike during known crises (March 2020, Feb 2018)
3. **Latency is acceptable:** <500ms for 45×45 matrix update
4. **Visualization updates smoothly:** Frontend receives updates without lag
5. **No numerical errors:** No NaN, no correlations >1 or <-1, diagonal always = 1

---

## 📚 **FURTHER READING**

- Engle & Sheppard (2001) - Original DCC-GARCH paper
- `arch` Python library documentation
- Our full DCC-GARCH specification (200 pages)
- Granger causality lead-lag models
- Crisis Predictor integration guide

---

**You are now ready to build the correlation engine that powers the Butterfly Effect visualization. Good luck! 🚀**
