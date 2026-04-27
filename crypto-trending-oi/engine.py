import math
import datetime
import pandas as pd

# --- Normalization Helpers (Pandas) ---

def normalize_zscore(series, window=90):
    """
    Computes a rolling Z-Score over the specified window (Spec 14.2).
    Returns the full normalized series.
    """
    rolling_mean = series.rolling(window=window, min_periods=1).mean()
    rolling_std = series.rolling(window=window, min_periods=1).std()
    
    # Avoid division by zero
    rolling_std = rolling_std.replace(0, 1e-6)
    
    z_scores = (series - rolling_mean) / rolling_std
    # Clamp z-scores between -3 and 3 for stability, then map to [-1, 1]
    clamped = z_scores.clip(-3, 3)
    return clamped / 3.0

def apply_relationship(z_score, relationship):
    """
    Applies the inverse or direct relationship flag.
    z_score is a single float [-1, 1].
    """
    if relationship == 'inverse':
        return -z_score
    elif relationship == 'direct':
        return z_score
    return z_score

# --- Scoring Functions ---

def compute_macro_regime_score(df):
    latest = df.iloc[-1]
    
    # Normalize features using 90d z-score
    dxy_norm = apply_relationship(normalize_zscore(df['dxy_1d_pct_change']).iloc[-1], 'inverse')
    vix_norm = apply_relationship(normalize_zscore(df['vix_level']).iloc[-1], 'inverse')
    us10y_norm = apply_relationship(normalize_zscore(df['us10y_real']).iloc[-1], 'inverse')
    ndx_norm = apply_relationship(normalize_zscore(df['ndx_1d_pct_change']).iloc[-1], 'direct')
    m2_norm = apply_relationship(normalize_zscore(df['global_m2_13w_change']).iloc[-1], 'direct')
    fed_norm = apply_relationship(normalize_zscore(df['fed_cut_probability_1m']).iloc[-1], 'direct')
    
    scores = {
        'dxy': dxy_norm,
        'vix': vix_norm,
        'us10y_real': us10y_norm,
        'ndx': ndx_norm,
        'global_m2': m2_norm,
        'fed_cut_prob': fed_norm
    }
    
    weights = {
        'dxy': 0.25,
        'vix': 0.20,
        'us10y_real': 0.20,
        'ndx': 0.15,
        'global_m2': 0.10,
        'fed_cut_prob': 0.10
    }
    
    # Override: Liquidity Surge (raw M2 > 3.0%)
    if latest['global_m2_13w_change'] > 3.0:
        weights['global_m2'] = 0.30
        weights['us10y_real'] = 0.10
        weights['fed_cut_prob'] = 0.05
    
    return sum(s * weights[k] for k, s in scores.items()), scores

def compute_onchain_score(df):
    latest = df.iloc[-1]
    
    etf_norm = apply_relationship(normalize_zscore(df['btc_etf_net_flow_7d']).iloc[-1], 'direct')
    stablecoin_norm = apply_relationship(normalize_zscore(df['stablecoin_total_7d_change']).iloc[-1], 'direct')
    
    # MVRV uses absolute thresholds per spec
    mvrv_raw = latest['mvrv_z_score']
    if mvrv_raw < 0: mvrv_score = 1.0
    elif mvrv_raw > 6: mvrv_score = -1.0
    else: 
        # Map 0->6 to 1->-1
        mvrv_score = 1.0 - (mvrv_raw / 3.0)
        
    scores = {
        'btc_etf_flow': etf_norm,
        'stablecoin_supply': stablecoin_norm,
        'mvrv': mvrv_score
    }
    
    weights = {
        'btc_etf_flow': 0.40,
        'stablecoin_supply': 0.35,
        'mvrv': 0.25
    }
    
    # Override: Deep Value
    if mvrv_raw < 0:
        weights['mvrv'] = 0.60
        weights['btc_etf_flow'] = 0.20
        weights['stablecoin_supply'] = 0.20
    
    return sum(s * weights[k] for k, s in scores.items()), scores

def compute_intraday_score(df):
    latest = df.iloc[-1]
    
    funding_norm = apply_relationship(normalize_zscore(df['perp_funding_rate']).iloc[-1], 'inverse')
    
    # OI Directional Logic (raw values)
    oi_chg = latest['oi_change']
    px_chg = latest['price_change']
    if oi_chg > 0 and px_chg > 0: oi_score = 0.8
    elif oi_chg > 0 and px_chg < 0: oi_score = -0.8
    elif oi_chg < 0 and px_chg < 0: oi_score = -0.4
    elif oi_chg < 0 and px_chg > 0: oi_score = 0.4
    else: oi_score = 0.0
        
    liq_norm = apply_relationship(normalize_zscore(df['liq_imbalance']).iloc[-1], 'direct')
    iv_norm = apply_relationship(normalize_zscore(df['deribit_25d_skew']).iloc[-1], 'direct')
    
    scores = {
        'funding_rate': funding_norm,
        'open_interest': oi_score,
        'liquidations': liq_norm,
        'options_skew': iv_norm
    }
    
    weights = {
        'funding_rate': 0.35,
        'open_interest': 0.30,
        'liquidations': 0.20,
        'options_skew': 0.15
    }
    
    return sum(s * weights[k] for k, s in scores.items()), scores

def apply_event_decay(base_score, events, today):
    event_impact = 0
    for event in events:
        days_elapsed = (today - event['timestamp']).days
        if days_elapsed <= event['impact_duration_days'] and days_elapsed >= 0:
            if event['decay_function'] == 'exponential':
                decay = math.exp(-0.1 * days_elapsed)
            elif event['decay_function'] == 'linear':
                decay = 1 - (days_elapsed / event['impact_duration_days'])
            else:
                decay = 1.0
            event_impact += (event['impact_score'] / 3.0) * decay
    
    return max(-1.0, min(1.0, base_score + event_impact))

def run_engine(df, events):
    latest = df.iloc[-1]
    
    mrs, mrs_breakdown = compute_macro_regime_score(df)
    ocs, ocs_breakdown = compute_onchain_score(df)
    ims, ims_breakdown = compute_intraday_score(df)
    
    # Base weights
    w_mrs = 0.45
    w_ocs = 0.30
    w_ims = 0.25
    
    regime_name = "Normal"
    
    # Global Overrides (using raw latest values)
    if latest['vix_level'] > 30.0:
        regime_name = "VIX Crisis / Liquidation"
        mrs = -0.9
        ocs = -0.7
        ims = -0.8
        w_mrs = 0.70
        w_ocs = 0.15
        w_ims = 0.15
    elif latest['mvrv_z_score'] < 0:
        regime_name = "Deep Value Accumulation"
        w_mrs = 0.20
        w_ocs = 0.50
        w_ims = 0.30
    elif latest['global_m2_13w_change'] > 3.0:
        regime_name = "Liquidity Surge"
        w_mrs = 0.55
        w_ocs = 0.25
        w_ims = 0.20
    elif 180 < latest['halving_cycle_day'] < 540:
        regime_name = "Post-Halving Bull"
    
    base_composite = (mrs * w_mrs) + (ocs * w_ocs) + (ims * w_ims)
    
    if regime_name == "Post-Halving Bull":
        base_composite += 0.15
        
    final_composite = apply_event_decay(base_composite, events, datetime.date.today())
    final_composite = max(-1.0, min(1.0, final_composite))
    
    return {
        "mrs": mrs,
        "ocs": ocs,
        "ims": ims,
        "composite": final_composite,
        "regime": regime_name,
        "cycle_day": latest['halving_cycle_day'],
        "breakdown": {
            "macro": mrs_breakdown,
            "onchain": ocs_breakdown,
            "intraday": ims_breakdown
        }
    }
