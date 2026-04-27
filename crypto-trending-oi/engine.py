import math
import datetime

# --- Normalization Helpers ---

def normalize_inverse(val, min_val, max_val):
    """Normalize such that higher raw value = lower score [-1 to 1]"""
    # Clamp
    val = max(min_val, min(val, max_val))
    # Map to 0-1
    pct = (val - min_val) / (max_val - min_val)
    # Map to +1 to -1 (inverse)
    return 1.0 - (pct * 2.0)

def normalize_direct(val, min_val, max_val):
    """Normalize such that higher raw value = higher score [-1 to 1]"""
    # Clamp
    val = max(min_val, min(val, max_val))
    # Map to 0-1
    pct = (val - min_val) / (max_val - min_val)
    # Map to -1 to +1
    return (pct * 2.0) - 1.0

# --- Scoring Functions ---

def compute_macro_regime_score(f):
    # DXY: inverse (-1.0% to +1.0% daily change)
    dxy_score = normalize_inverse(f['dxy_1d_pct_change'], -1.0, 1.0)
    
    # VIX: inverse (10 to 35)
    vix_score = normalize_inverse(f['vix_level'], 10.0, 35.0)
    
    # US10Y Real: inverse (-1.0 to 3.0)
    us10y_score = normalize_inverse(f['us10y_real'], -1.0, 3.0)
    
    # NDX: direct (-3.0% to +3.0%)
    ndx_score = normalize_direct(f['ndx_1d_pct_change'], -3.0, 3.0)
    
    # Global M2: direct (-2.0% to 5.0%)
    m2_score = normalize_direct(f['global_m2_13w_change'], -2.0, 5.0)
    
    # Fed cut prob: direct (0% to 100%)
    fed_score = normalize_direct(f['fed_cut_probability_1m'], 0.0, 100.0)
    
    scores = {
        'dxy': dxy_score,
        'vix': vix_score,
        'us10y_real': us10y_score,
        'ndx': ndx_score,
        'global_m2': m2_score,
        'fed_cut_prob': fed_score
    }
    
    # Base weights
    weights = {
        'dxy': 0.25,
        'vix': 0.20,
        'us10y_real': 0.20,
        'ndx': 0.15,
        'global_m2': 0.10,
        'fed_cut_prob': 0.10
    }
    
    # Override: Liquidity Surge (M2 > 3.0)
    if f['global_m2_13w_change'] > 3.0:
        weights['global_m2'] = 0.30
        weights['us10y_real'] = 0.10
        weights['fed_cut_prob'] = 0.05
    
    return sum(s * weights[k] for k, s in scores.items()), scores

def compute_onchain_score(f):
    # ETF Flows: direct (-500M to +1000M)
    etf_score = normalize_direct(f['btc_etf_net_flow_7d'], -500_000_000, 1_000_000_000)
    
    # Stablecoin: direct (-2B to +3B)
    stablecoin_score = normalize_direct(f['stablecoin_total_7d_change'], -2_000_000_000, 3_000_000_000)
    
    # MVRV Z-score: mixed (-1 to 7)
    # < 0 is strong buy (+1), > 6 is strong sell (-1), 1-3 is neutral (0)
    mvrv = f['mvrv_z_score']
    if mvrv < 0: mvrv_score = 1.0
    elif mvrv > 6: mvrv_score = -1.0
    else: mvrv_score = normalize_inverse(mvrv, 0.0, 6.0) # 0 maps to 1, 6 maps to -1
        
    scores = {
        'btc_etf_flow': etf_score,
        'stablecoin_supply': stablecoin_score,
        'mvrv': mvrv_score
    }
    
    weights = {
        'btc_etf_flow': 0.40,
        'stablecoin_supply': 0.35,
        'mvrv': 0.25
    }
    
    # Override: Deep Value (MVRV < 0)
    if f['mvrv_z_score'] < 0:
        weights['mvrv'] = 0.60
        weights['btc_etf_flow'] = 0.20
        weights['stablecoin_supply'] = 0.20
    
    return sum(s * weights[k] for k, s in scores.items()), scores

def compute_intraday_score(f):
    # Funding rate: contrarian (-0.05 to +0.10)
    # High funding = overleveraged longs = bearish (-1)
    # Low/negative funding = short squeeze fuel = bullish (+1)
    funding_score = normalize_inverse(f['perp_funding_rate'], -0.05, 0.10)
    
    # Open interest: directional with price
    oi_chg = f['oi_change']
    px_chg = f['price_change']
    if oi_chg > 0 and px_chg > 0: oi_score = 0.8  # Long buildup
    elif oi_chg > 0 and px_chg < 0: oi_score = -0.8 # Short buildup
    elif oi_chg < 0 and px_chg < 0: oi_score = -0.4 # Long unwinding
    elif oi_chg < 0 and px_chg > 0: oi_score = 0.4  # Short covering
    else: oi_score = 0.0
        
    # Liquidations: directional imbalance
    # Positive means shorts liquidated (bullish push), Negative means longs liquidated (bearish dump)
    liq_score = normalize_direct(f['liq_imbalance'], -50_000_000, 50_000_000)
    
    # Options skew: negative = put premium (bearish), positive = call premium (bullish)
    iv_score = normalize_direct(f['deribit_25d_skew'], -10.0, 10.0)
    
    scores = {
        'funding_rate': funding_score,
        'open_interest': oi_score,
        'liquidations': liq_score,
        'options_skew': iv_score
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
            # Normalize impact to [-1, 1] relative to a max impact of 3
            event_impact += (event['impact_score'] / 3.0) * decay
    
    return max(-1.0, min(1.0, base_score + event_impact))

def run_engine(f, events):
    mrs, mrs_breakdown = compute_macro_regime_score(f)
    ocs, ocs_breakdown = compute_onchain_score(f)
    ims, ims_breakdown = compute_intraday_score(f)
    
    # Base weights
    w_mrs = 0.45
    w_ocs = 0.30
    w_ims = 0.25
    
    regime_name = "Normal"
    
    # Global Overrides
    if f['vix_level'] > 30.0:
        regime_name = "VIX Crisis / Liquidation"
        # Everything sells, correlations go to 1
        mrs = -0.9
        ocs = -0.7
        ims = -0.8
        w_mrs = 0.70
        w_ocs = 0.15
        w_ims = 0.15
    elif f['mvrv_z_score'] < 0:
        regime_name = "Deep Value Accumulation"
        w_mrs = 0.20
        w_ocs = 0.50
        w_ims = 0.30
    elif f['global_m2_13w_change'] > 3.0:
        regime_name = "Liquidity Surge"
        w_mrs = 0.55
        w_ocs = 0.25
        w_ims = 0.20
    elif 180 < f['halving_cycle_day'] < 540:
        regime_name = "Post-Halving Bull"
    
    base_composite = (mrs * w_mrs) + (ocs * w_ocs) + (ims * w_ims)
    
    # Apply structural halving boost if applicable
    if regime_name == "Post-Halving Bull":
        base_composite += 0.15
        
    final_composite = apply_event_decay(base_composite, events, datetime.date.today())
    
    # Clamp to [-1, 1]
    final_composite = max(-1.0, min(1.0, final_composite))
    
    return {
        "mrs": mrs,
        "ocs": ocs,
        "ims": ims,
        "composite": final_composite,
        "regime": regime_name,
        "cycle_day": f['halving_cycle_day'],
        "breakdown": {
            "macro": mrs_breakdown,
            "onchain": ocs_breakdown,
            "intraday": ims_breakdown
        }
    }
