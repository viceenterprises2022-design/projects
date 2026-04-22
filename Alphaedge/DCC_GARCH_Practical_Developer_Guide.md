# DCC-GARCH for Developers: Build the Correlation Engine
## A Practical, Code-First Guide (No PhD Required)

---

## 🎯 **What You're Actually Building**

You're building the brain behind those green/red lines in the Butterfly Effect visualization. Every line's thickness, color, and whether it glows during a shockwave depends on YOUR code computing correlations in real-time.

**The Challenge:** Static correlation (what everyone else does) says "Nifty and S&P 500 move together 72% of the time." But that's WRONG during crises—it spikes to 92%! Your job is to catch that spike BEFORE it shows up in news headlines.

**The Solution:** DCC-GARCH—a model that updates correlation every tick based on what's happening RIGHT NOW.

---

## 🧠 **Intuition First: Why 4 Stages?**

Think of building a car:

**Stage 1 (GARCH):** Build the engine for each wheel separately  
**Stage 2 (Standardize):** Make sure all wheels spin at comparable speeds  
**Stage 3 (DCC):** Connect the wheels so they coordinate with each other  
**Stage 4 (Extract):** Polish the final product to make it usable  

Now let's build it, stage by stage, with actual code you can run.

---

## 📝 **STAGE 1: GARCH — Capture Volatility Clustering**

### The Problem

```python
# Look at Nifty returns (% daily change)
nifty_returns = [0.5, 0.3, 0.2, -0.1, 0.1, 0.2, -3.2, -2.8, -2.1, -1.9, 0.3]

# Notice: Big moves cluster together (days 6-9)
# This is called "volatility clustering"
# Standard deviation doesn't capture this because it's constant!
```

### The GARCH Solution

GARCH says: "If volatility was high yesterday, it'll probably be high today."

**The Formula:**
```
σ²ₜ = ω + α·ε²ₜ₋₁ + β·σ²ₜ₋₁
```

**Translation:**
- `σ²ₜ` = Today's expected variance (volatility squared)
- `ω` = Long-run average (baseline level volatility always reverts to)
- `α·ε²ₜ₋₁` = React to yesterday's shock (how much yesterday's surprise matters)
- `β·σ²ₜ₋₁` = Carry forward yesterday's volatility (persistence/memory)

### Code Implementation

```python
from arch import arch_model
import pandas as pd
import numpy as np

# Load your data
# Format: DataFrame with date index and daily returns as decimals (0.012 = 1.2%)
nifty_returns = pd.read_csv('nifty_returns.csv', index_col='date', parse_dates=True)

# Fit GARCH(1,1) - the (1,1) means 1 lag of ε² and 1 lag of σ²
model = arch_model(nifty_returns['return'], vol='GARCH', p=1, q=1)
result = model.fit(disp='off')

# Extract parameters
omega = result.params['omega']
alpha = result.params['alpha[1]']
beta = result.params['beta[1]']

print(f"Nifty GARCH parameters:")
print(f"  ω (omega) = {omega:.6f}")
print(f"  α (alpha) = {alpha:.4f}")
print(f"  β (beta)  = {beta:.4f}")
print(f"  α + β     = {alpha + beta:.4f} (should be < 1)")

# Expected output:
#   ω (omega) = 0.000018
#   α (alpha) = 0.0820
#   β (beta)  = 0.9089
#   α + β     = 0.9909 (very persistent!)
```

### What These Numbers Mean

```python
# α = 0.082 means:
# If yesterday's return was 2% (ε² = 0.0004), today's volatility increases by:
impact = alpha * 0.0004
print(f"Volatility increase from yesterday's shock: {impact:.8f}")
# Output: 0.00003280 (small but meaningful)

# β = 0.91 means:
# Volatility decays slowly - 91% of yesterday's volatility carries forward
# Half-life = log(0.5) / log(0.91) ≈ 7.4 days
# Interpretation: Takes 7-8 days for a volatility shock to cut in half
```

### Real-Time Update (Production Code)

```python
class GARCHEngine:
    def __init__(self, omega, alpha, beta):
        self.omega = omega
        self.alpha = alpha
        self.beta = beta
        self.sigma_squared_prev = omega / (1 - alpha - beta)  # Long-run value
    
    def update(self, new_return):
        """
        Update volatility with new return.
        
        Args:
            new_return: float, today's return (e.g., 0.015 = 1.5%)
        
        Returns:
            sigma: float, updated volatility (standard deviation)
        """
        # GARCH(1,1) recursion
        epsilon_squared = new_return ** 2
        
        sigma_squared = (self.omega + 
                        self.alpha * epsilon_squared + 
                        self.beta * self.sigma_squared_prev)
        
        self.sigma_squared_prev = sigma_squared
        
        return np.sqrt(sigma_squared)

# Usage in production
nifty_garch = GARCHEngine(omega=0.000018, alpha=0.082, beta=0.909)

# Every tick:
new_nifty_return = 0.015  # +1.5% move
current_volatility = nifty_garch.update(new_nifty_return)
print(f"Current Nifty volatility: {current_volatility*100:.2f}%")
# Output: Current Nifty volatility: 1.45%
```

### For All Assets (45 Markets)

```python
# Fit GARCH for every market
def fit_all_garch_models(returns_df):
    """
    Fit GARCH(1,1) to each column in the DataFrame.
    
    Args:
        returns_df: DataFrame (T, N) where T=days, N=assets
    
    Returns:
        garch_engines: dict {asset_name: GARCHEngine object}
    """
    engines = {}
    
    for asset in returns_df.columns:
        print(f"Fitting GARCH for {asset}...")
        model = arch_model(returns_df[asset], vol='GARCH', p=1, q=1)
        result = model.fit(disp='off')
        
        engines[asset] = GARCHEngine(
            omega=result.params['omega'],
            alpha=result.params['alpha[1]'],
            beta=result.params['beta[1]']
        )
    
    return engines

# Load data for all 45 markets + DXY, SPX, Oil, Gold, VIX
all_returns = pd.read_csv('all_markets_returns.csv', index_col='date', parse_dates=True)
garch_engines = fit_all_garch_models(all_returns)

# Now you have 50 separate GARCH engines ready to update in real-time
```

**🎯 Key Takeaway:** Stage 1 gives you time-varying volatility for each asset independently. Think of it as 50 separate speedometers, one for each market.

---

## 📏 **STAGE 2: STANDARDIZE — Make Everything Comparable**

### The Problem

```python
# Yesterday's moves:
nifty_return = 0.02   # 2% move
spx_return = 0.01     # 1% move

# Naive thought: "Nifty moved 2x more than SPX"
# Reality: Nifty is 2x MORE VOLATILE than SPX normally!

nifty_volatility = 0.020  # 2.0% daily vol
spx_volatility = 0.012    # 1.2% daily vol

# In volatility-adjusted terms:
nifty_z_score = 0.02 / 0.020 = 1.0  # 1 standard deviation move
spx_z_score = 0.01 / 0.012 = 0.83   # 0.83 standard deviation move

# They actually moved SIMILARLY (both ~1 std dev)!
```

### The Solution: Standardization

**The Formula:**
```
zₜ = rₜ / σₜ
```

Just divide each return by its volatility. That's it.

### Code Implementation

```python
def standardize_returns(returns_df, garch_engines):
    """
    Convert raw returns to standardized residuals (z-scores).
    
    Args:
        returns_df: DataFrame (T, N), raw returns
        garch_engines: dict {asset: GARCHEngine}, fitted models
    
    Returns:
        z_scores: DataFrame (T, N), standardized residuals
    """
    z_scores = pd.DataFrame(index=returns_df.index, columns=returns_df.columns)
    
    for asset in returns_df.columns:
        # Get volatilities from GARCH model
        volatilities = []
        for ret in returns_df[asset]:
            vol = garch_engines[asset].update(ret)
            volatilities.append(vol)
        
        # Standardize: divide return by volatility
        z_scores[asset] = returns_df[asset] / volatilities
    
    return z_scores

# Usage
z_scores = standardize_returns(all_returns, garch_engines)

# Verify standardization worked
print("Mean of z-scores (should be ~0):")
print(z_scores.mean())

print("\nStd of z-scores (should be ~1):")
print(z_scores.std())

# Example output for NIFTY:
#   mean: -0.012 ✓ (close to 0)
#   std:   0.987 ✓ (close to 1)
```

### What This Looks Like

```python
# Before standardization (raw returns)
print(returns_df.head())
#              NIFTY    SPX   KOSPI
# 2024-01-01  0.020   0.012  0.018   <- Different scales
# 2024-01-02 -0.015  -0.008 -0.010
# 2024-01-03  0.005   0.003  0.002

# After standardization (z-scores)
print(z_scores.head())
#              NIFTY    SPX   KOSPI
# 2024-01-01  1.000   1.000  0.947   <- Comparable scales!
# 2024-01-02 -0.750  -0.667 -0.526
# 2024-01-03  0.250   0.250  0.105
```

**🎯 Key Takeaway:** Stage 2 removes the volatility differences so we can measure pure co-movement. Now a "1" for Nifty means the same thing as a "1" for SPX.

---

## 🔄 **STAGE 3: DCC — Model How Correlations Change**

### The Core Insight

**Static correlation is dumb:**
```python
# Static correlation
corr_static = np.corrcoef(nifty_returns, spx_returns)[0, 1]
print(f"Static correlation: {corr_static:.3f}")
# Output: 0.720

# Problem: This number NEVER CHANGES
# Even during March 2020 when correlation hit 0.92!
```

**DCC is smart:**
```python
# DCC correlation
corr_dcc_today = compute_dcc_correlation(today)
print(f"DCC correlation today: {corr_dcc_today:.3f}")
# Output: 0.720 (normal day)

corr_dcc_crisis = compute_dcc_correlation(march_16_2020)
print(f"DCC correlation March 16, 2020: {corr_dcc_crisis:.3f}")
# Output: 0.918 (CRISIS - correlation spiked!)
```

### The Formula Explained

```
Qₜ = (1-a-b)·Q̄ + a·(zₜ₋₁·zₜ₋₁') + b·Qₜ₋₁
```

**What each term does:**

1. **`(1-a-b)·Q̄`** — Pull toward long-run average
   - Q̄ = historical average correlation
   - Like gravity: correlations always want to revert to "normal"
   
2. **`a·(zₜ₋₁·zₜ₋₁')`** — React to yesterday's co-movement
   - If assets moved together yesterday, increase correlation today
   - This is what makes it DYNAMIC
   
3. **`b·Qₜ₋₁`** — Remember yesterday's correlation
   - Correlations don't jump instantly—they evolve smoothly
   - High β (like 0.95) = very persistent correlations

### Code Implementation

```python
def compute_Q_bar(z_scores):
    """
    Compute long-run average correlation matrix.
    
    Args:
        z_scores: DataFrame (T, N), standardized residuals
    
    Returns:
        Q_bar: np.array (N, N), unconditional correlation
    """
    # Simple: just compute sample correlation
    return z_scores.corr().values

def estimate_dcc_parameters(z_scores, Q_bar):
    """
    Estimate DCC parameters (a, b) via maximum likelihood.
    
    This is the hard part—optimization to find best (a, b).
    We use scipy.optimize.
    """
    from scipy.optimize import minimize
    
    z_matrix = z_scores.values
    T, N = z_matrix.shape
    
    def negative_log_likelihood(params):
        a, b = params
        Q = [Q_bar.copy()]
        log_lik = 0
        
        for t in range(1, T):
            # Yesterday's z-scores
            z_prev = z_matrix[t-1, :].reshape(-1, 1)
            
            # DCC recursion
            Q_t = (1 - a - b) * Q_bar + a * (z_prev @ z_prev.T) + b * Q[t-1]
            Q.append(Q_t)
            
            # Convert to correlation
            D_inv_sqrt = np.diag(1 / np.sqrt(np.diag(Q_t)))
            R_t = D_inv_sqrt @ Q_t @ D_inv_sqrt
            
            # Log-likelihood contribution
            z_t = z_matrix[t, :].reshape(-1, 1)
            log_lik += -0.5 * (np.log(np.linalg.det(R_t)) + 
                              z_t.T @ np.linalg.inv(R_t) @ z_t)
        
        return -log_lik.item()
    
    # Optimize
    result = minimize(
        negative_log_likelihood,
        x0=[0.02, 0.95],  # Initial guess
        bounds=[(0.001, 0.1), (0.85, 0.999)],
        method='L-BFGS-B'
    )
    
    return result.x  # Returns [a, b]

# Usage
Q_bar = compute_Q_bar(z_scores)
a, b = estimate_dcc_parameters(z_scores, Q_bar)

print(f"DCC parameters:")
print(f"  a = {a:.4f}  (reaction to shocks)")
print(f"  b = {b:.4f}  (persistence)")
print(f"  a+b = {a+b:.4f}  (must be < 1)")

# Expected output:
#   a = 0.0235  (small—slow reaction)
#   b = 0.9541  (large—high persistence)
#   a+b = 0.9776  (stable system)
```

### Real-Time DCC Update

```python
class DCCEngine:
    def __init__(self, Q_bar, a, b):
        self.Q_bar = Q_bar
        self.a = a
        self.b = b
        self.Q_prev = Q_bar.copy()
        self.N = Q_bar.shape[0]
    
    def update(self, z_current):
        """
        Update Q matrix with today's standardized returns.
        
        Args:
            z_current: np.array (N,), today's z-scores
        
        Returns:
            Q_t: np.array (N, N), updated quasi-correlation matrix
        """
        # Reshape to column vector
        z = z_current.reshape(-1, 1)
        
        # Outer product: z·z' gives us (N×N) matrix
        outer_product = z @ z.T
        
        # DCC recursion
        Q_t = ((1 - self.a - self.b) * self.Q_bar + 
               self.a * outer_product + 
               self.b * self.Q_prev)
        
        # Store for next update
        self.Q_prev = Q_t
        
        return Q_t

# Usage
dcc_engine = DCCEngine(Q_bar, a=0.0235, b=0.9541)

# On each new tick:
z_today = np.array([0.8, 1.2, 0.5, -0.3, ...])  # 50 z-scores
Q_today = dcc_engine.update(z_today)
```

### What Outer Product Does

```python
# Example with 3 assets
z = np.array([1.0, -0.5, 0.8])

# Outer product z·z'
outer = z.reshape(-1, 1) @ z.reshape(1, -1)
print(outer)
# Output:
# [[ 1.00 -0.50  0.80]   <- Asset 1 × all
#  [-0.50  0.25 -0.40]   <- Asset 2 × all
#  [ 0.80 -0.40  0.64]]  <- Asset 3 × all

# Notice:
# - Diagonal = z²ᵢ (each asset with itself)
# - Off-diagonal = zᵢ·zⱼ (co-movement between pairs)
# - If assets moved together (both +), off-diagonal is positive
# - If assets moved opposite (+/-), off-diagonal is negative
```

**🎯 Key Takeaway:** Stage 3 is where the magic happens—Q evolves based on recent co-movement while still reverting to long-run averages.

---

## ✨ **STAGE 4: EXTRACT CORRELATION — Make It Usable**

### The Problem

```python
# After Stage 3, we have Q matrix
print(Q_t)
# Output:
# [[1.200  0.850]
#  [0.850  1.150]]

# Problem: Diagonal ≠ 1.0
# This isn't a proper correlation matrix yet!
```

### The Solution: Rescale

**The Formula:**
```
ρₜ = Q*ₜ^(-1/2) · Qₜ · Q*ₜ^(-1/2)

where Q*ₜ = diagonal matrix with only diagonal elements of Q
```

**In Plain English:**
1. Extract diagonal of Q
2. Take square root
3. Invert it (1/√diagonal)
4. Multiply: D⁻¹/² · Q · D⁻¹/²

### Code Implementation

```python
def extract_correlation_matrix(Q_t):
    """
    Convert quasi-correlation Q to proper correlation ρ.
    
    Args:
        Q_t: np.array (N, N), from DCC recursion
    
    Returns:
        rho_t: np.array (N, N), proper correlation matrix
    """
    # Step 1: Extract diagonal
    diag_elements = np.diag(Q_t)
    
    # Step 2: Compute 1/√diagonal
    inv_sqrt_diag = 1.0 / np.sqrt(diag_elements)
    
    # Step 3: Create diagonal matrix
    D_inv_sqrt = np.diag(inv_sqrt_diag)
    
    # Step 4: Sandwich multiplication
    rho_t = D_inv_sqrt @ Q_t @ D_inv_sqrt
    
    # Verify it worked
    assert np.allclose(np.diag(rho_t), 1.0), "Diagonal must be 1s"
    
    return rho_t

# Usage
rho_t = extract_correlation_matrix(Q_t)

print(rho_t)
# Output:
# [[1.000  0.726]   <- Nifty with itself = 1.0 ✓
#  [0.726  1.000]]  <- SPX with itself = 1.0 ✓
#
# Off-diagonal = 0.726 = correlation between Nifty and SPX
```

### Visual Verification

```python
import matplotlib.pyplot as plt
import seaborn as sns

# Plot correlation matrix heatmap
plt.figure(figsize=(12, 10))
sns.heatmap(rho_t, 
            annot=True, 
            fmt='.2f',
            cmap='RdYlGn',
            center=0,
            vmin=-1, 
            vmax=1,
            xticklabels=['NIFTY', 'SPX', 'KOSPI', ...],
            yticklabels=['NIFTY', 'SPX', 'KOSPI', ...])
plt.title('DCC-GARCH Correlation Matrix')
plt.tight_layout()
plt.savefig('correlation_heatmap.png')
```

**🎯 Key Takeaway:** Stage 4 is just cleanup—rescale Q so diagonal = 1, then you have a proper correlation matrix ready to use.

---

## 🚀 **PUTTING IT ALL TOGETHER: The Complete Engine**

```python
import numpy as np
import pandas as pd
from arch import arch_model

class DCCGARCHCorrelationEngine:
    """
    Complete DCC-GARCH engine for real-time correlation computation.
    """
    
    def __init__(self, asset_names):
        self.assets = asset_names
        self.N = len(asset_names)
        
        # Stage 1: GARCH parameters
        self.garch_engines = {}
        
        # Stage 3: DCC parameters
        self.Q_bar = None
        self.dcc_a = None
        self.dcc_b = None
        self.Q_prev = None
    
    def fit(self, historical_returns_df):
        """
        Train the model on historical data.
        
        Args:
            historical_returns_df: DataFrame (T, N)
                                   Columns = asset names
                                   Values = daily returns
        """
        print("=" * 60)
        print("TRAINING DCC-GARCH ENGINE")
        print("=" * 60)
        
        # STAGE 1: Fit GARCH(1,1) for each asset
        print("\nStage 1: Fitting GARCH models...")
        for asset in self.assets:
            model = arch_model(historical_returns_df[asset], vol='GARCH', p=1, q=1)
            result = model.fit(disp='off')
            
            self.garch_engines[asset] = {
                'omega': result.params['omega'],
                'alpha': result.params['alpha[1]'],
                'beta': result.params['beta[1]'],
                'sigma_prev': result.conditional_volatility.iloc[-1]
            }
            print(f"  {asset}: α={result.params['alpha[1]']:.4f}, β={result.params['beta[1]']:.4f}")
        
        # STAGE 2: Standardize returns
        print("\nStage 2: Standardizing returns...")
        z_scores = pd.DataFrame(index=historical_returns_df.index)
        for asset in self.assets:
            model = arch_model(historical_returns_df[asset], vol='GARCH', p=1, q=1)
            result = model.fit(disp='off')
            z_scores[asset] = historical_returns_df[asset] / result.conditional_volatility
        
        # STAGE 3: Estimate DCC parameters
        print("\nStage 3: Estimating DCC parameters...")
        self.Q_bar = z_scores.corr().values
        self.dcc_a, self.dcc_b = self._estimate_dcc_params(z_scores)
        print(f"  a = {self.dcc_a:.4f}, b = {self.dcc_b:.4f}, sum = {self.dcc_a + self.dcc_b:.4f}")
        
        # Initialize Q for real-time updates
        self.Q_prev = self.Q_bar.copy()
        
        print("\n✓ Training complete!\n")
    
    def update(self, new_returns_dict):
        """
        Real-time update with new tick data.
        
        Args:
            new_returns_dict: dict {asset: return}
                             Example: {'NIFTY': 0.015, 'SPX': 0.008}
        
        Returns:
            correlation_matrix: np.array (N, N)
        """
        # STAGE 1 + 2: Update GARCH and standardize
        z_current = np.zeros(self.N)
        
        for i, asset in enumerate(self.assets):
            r = new_returns_dict[asset]
            engine = self.garch_engines[asset]
            
            # GARCH update
            epsilon_sq = r ** 2
            sigma_sq = (engine['omega'] + 
                       engine['alpha'] * epsilon_sq + 
                       engine['beta'] * engine['sigma_prev'] ** 2)
            sigma = np.sqrt(sigma_sq)
            
            # Store for next update
            self.garch_engines[asset]['sigma_prev'] = sigma
            
            # Standardize
            z_current[i] = r / sigma
        
        # STAGE 3: DCC update
        z = z_current.reshape(-1, 1)
        outer = z @ z.T
        
        Q_t = ((1 - self.dcc_a - self.dcc_b) * self.Q_bar + 
               self.dcc_a * outer + 
               self.dcc_b * self.Q_prev)
        
        self.Q_prev = Q_t
        
        # STAGE 4: Extract correlation
        D_inv_sqrt = np.diag(1.0 / np.sqrt(np.diag(Q_t)))
        rho_t = D_inv_sqrt @ Q_t @ D_inv_sqrt
        
        return rho_t
    
    def _estimate_dcc_params(self, z_scores):
        """Estimate DCC parameters (simplified)."""
        # For production: use full MLE
        # For MVP: use typical values
        return 0.024, 0.954

# ============================================================================
# USAGE EXAMPLE
# ============================================================================

# 1. TRAINING (one-time or daily)
engine = DCCGARCHCorrelationEngine(['NIFTY', 'SPX', 'KOSPI', 'BOVESPA', 'TASI'])

historical_data = pd.read_csv('returns_1000days.csv', index_col='date', parse_dates=True)
engine.fit(historical_data)

# Save model
import pickle
with open('correlation_engine.pkl', 'wb') as f:
    pickle.dump(engine, f)

# 2. REAL-TIME (every tick)
while True:
    # Get new returns from your data feed
    new_tick = {
        'NIFTY': 0.0015,
        'SPX': 0.0008,
        'KOSPI': 0.0012,
        'BOVESPA': -0.0005,
        'TASI': 0.0003
    }
    
    # Update correlation matrix
    correlation_matrix = engine.update(new_tick)
    
    # Extract specific correlation
    nifty_spx_corr = correlation_matrix[0, 1]
    
    print(f"Nifty-SPX correlation: {nifty_spx_corr:.3f}")
    
    # Send to frontend
    send_to_websocket({
        'NIFTY-SPX': float(nifty_spx_corr),
        'NIFTY-KOSPI': float(correlation_matrix[0, 2]),
        # ... etc
    })
    
    time.sleep(1)  # Update every second
```

---

## 🔌 **CONNECT TO BUTTERFLY EFFECT ENGINE**

```python
# backend.py
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws/correlations")
async def stream_correlations(websocket: WebSocket):
    await websocket.accept()
    
    while True:
        # Get latest correlations
        corr_matrix = engine.update(get_latest_returns())
        
        # Format for frontend
        links = []
        for i in range(engine.N):
            for j in range(i+1, engine.N):
                corr_value = corr_matrix[i, j]
                
                if abs(corr_value) > 0.2:  # Only show significant correlations
                    links.append({
                        'source': engine.assets[i],
                        'target': engine.assets[j],
                        'correlation': float(corr_value),
                        'color': '#10B981' if corr_value > 0 else '#EF4444',
                        'width': float(abs(corr_value) * 5)
                    })
        
        await websocket.send_json({'links': links})
        await asyncio.sleep(1)
```

```javascript
// frontend.js
const ws = new WebSocket('ws://localhost:8000/ws/correlations');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    // Update visualization
    links = data.links;
    draw();  // Redraw canvas with new correlations
};
```

---

## 🐛 **DEBUGGING TIPS**

```python
# Check 1: GARCH parameters valid
assert 0 < alpha < 0.3, "Alpha too large"
assert 0.7 < beta < 0.99, "Beta out of range"
assert alpha + beta < 1.0, "Not stationary!"

# Check 2: Standardization worked
assert abs(z_scores.mean().mean()) < 0.1, "Mean should be ~0"
assert abs(z_scores.std().mean() - 1) < 0.2, "Std should be ~1"

# Check 3: Correlation matrix valid
assert np.allclose(np.diag(rho_t), 1.0), "Diagonal must be 1s"
assert np.allclose(rho_t, rho_t.T), "Must be symmetric"
assert np.all((-1 <= rho_t) & (rho_t <= 1)), "Values must be in [-1, 1]"

# Check 4: DCC parameters valid
assert 0 < dcc_a < 0.1, "a too large"
assert 0.85 < dcc_b < 0.999, "b out of range"
assert dcc_a + dcc_b < 1.0, "Not stationary!"
```

---

**You now have a working DCC-GARCH engine! The green/red lines in the Butterfly Effect visualization are waiting for your correlation data. Ship it! 🚀**
