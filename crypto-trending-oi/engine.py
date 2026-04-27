import math
import datetime
import pandas as pd

# ─── Normalization Helpers ────────────────────────────────────────────────────

def normalize_zscore(series, window=90):
    """
    Computes rolling Z-Score over the specified window (Spec §14.2).
    Output clamped to [-3,+3] then mapped to [-1,+1].
    """
    rolling_mean = series.rolling(window=window, min_periods=1).mean()
    rolling_std  = series.rolling(window=window, min_periods=1).std()
    rolling_std  = rolling_std.replace(0, 1e-6)
    z = (series - rolling_mean) / rolling_std
    return z.clip(-3, 3) / 3.0

def apply_relationship(z_score, relationship):
    """Flip sign for inverse-correlated factors."""
    return -z_score if relationship == 'inverse' else z_score

def safe_norm(df, col, rel='direct'):
    """Normalize a column if it exists, else return 0."""
    if col not in df.columns:
        return 0.0
    return apply_relationship(normalize_zscore(df[col]).iloc[-1], rel)

# ─── Macro Regime Score ───────────────────────────────────────────────────────

def compute_macro_regime_score(df):
    """
    Spec §2 MRS weights:
    DXY=0.20, VIX=0.18, US10Y_real=0.17, NDX=0.12, M2=0.12, FedCut=0.10,
    ETFFlow=0.07, HYSpread=0.04
    """
    latest = df.iloc[-1]

    dxy_norm   = safe_norm(df, 'dxy_1d_pct_change',    'inverse')
    vix_norm   = safe_norm(df, 'vix_level',             'inverse')
    us10y_norm = safe_norm(df, 'us10y_real',            'inverse')
    ndx_norm   = safe_norm(df, 'ndx_1d_pct_change',    'direct')
    m2_norm    = safe_norm(df, 'global_m2_13w_change',  'direct')
    fed_norm   = safe_norm(df, 'fed_cut_probability_1m','direct')
    etf_norm   = safe_norm(df, 'btc_etf_net_flow_7d',  'direct')
    hy_norm    = safe_norm(df, 'hy_spread_change',      'inverse')

    scores = {
        'dxy':          dxy_norm,
        'vix':          vix_norm,
        'us10y_real':   us10y_norm,
        'ndx':          ndx_norm,
        'global_m2':    m2_norm,
        'fed_cut_prob': fed_norm,
        'btc_etf_flow': etf_norm,
        'hy_spread':    hy_norm,
    }

    weights = {
        'dxy':          0.20,
        'vix':          0.18,
        'us10y_real':   0.17,
        'ndx':          0.12,
        'global_m2':    0.12,
        'fed_cut_prob': 0.10,
        'btc_etf_flow': 0.07,
        'hy_spread':    0.04,
    }

    # Override: Liquidity Surge regime (raw M2 > 3.0%)
    if latest.get('global_m2_13w_change', 0) > 3.0:
        weights['global_m2']    = 0.30
        weights['us10y_real']   = 0.10
        weights['fed_cut_prob'] = 0.05
        # Renormalize remaining
        total = sum(weights.values())
        weights = {k: v/total for k, v in weights.items()}

    return sum(s * weights[k] for k, s in scores.items()), scores

# ─── On-Chain Score ───────────────────────────────────────────────────────────

def compute_onchain_score(df):
    """
    Spec §2 OCS weights:
    ExchReserves=0.25, Stablecoin=0.22, MVRV=0.20, MinerFlow=0.13,
    Whale=0.12, Dominance=0.08
    """
    latest = df.iloc[-1]

    exch_norm     = safe_norm(df, 'btc_exchange_netflow',    'inverse')
    stablecoin_norm = safe_norm(df, 'stablecoin_total_7d_change', 'direct')
    miner_norm    = safe_norm(df, 'miner_outflow_30d',       'inverse')
    whale_norm    = safe_norm(df, 'whale_wallet_change_7d',  'direct')
    dom_norm      = safe_norm(df, 'btc_dominance_trend',     'direct')

    # MVRV uses absolute cycle thresholds (spec §5)
    mvrv_raw = latest.get('mvrv_z_score', 1.5)
    if mvrv_raw < 0:    mvrv_score =  1.0
    elif mvrv_raw > 6:  mvrv_score = -1.0
    else:               mvrv_score =  1.0 - (mvrv_raw / 3.0)

    scores = {
        'exchange_reserves':  exch_norm,
        'stablecoin_supply':  stablecoin_norm,
        'mvrv':               mvrv_score,
        'miner_flow':         miner_norm,
        'whale_accumulation': whale_norm,
        'btc_dominance':      dom_norm,
    }

    weights = {
        'exchange_reserves':  0.25,
        'stablecoin_supply':  0.22,
        'mvrv':               0.20,
        'miner_flow':         0.13,
        'whale_accumulation': 0.12,
        'btc_dominance':      0.08,
    }

    # Override: Deep Value Accumulation
    if mvrv_raw < 0:
        weights['mvrv']              = 0.50
        weights['exchange_reserves'] = 0.20
        weights['stablecoin_supply'] = 0.15
        weights['miner_flow']        = 0.08
        weights['whale_accumulation']= 0.05
        weights['btc_dominance']     = 0.02

    return sum(s * weights[k] for k, s in scores.items()), scores

# ─── Intraday Micro Score ─────────────────────────────────────────────────────

def compute_intraday_score(df):
    """
    Spec §2 IMS weights:
    Funding=0.30, OI=0.25, Liquidations=0.22, Skew=0.13, Basis=0.10
    """
    latest = df.iloc[-1]

    funding_norm = safe_norm(df, 'perp_funding_rate', 'inverse')
    liq_norm     = safe_norm(df, 'liq_imbalance',     'direct')
    iv_norm      = safe_norm(df, 'deribit_25d_skew',  'direct')

    # OI directional logic (spec §6)
    oi_chg = latest.get('oi_change', 0)
    px_chg = latest.get('price_change', 0)
    if   oi_chg > 0 and px_chg > 0: oi_score =  0.8   # OI up + price up = genuine long build
    elif oi_chg > 0 and px_chg < 0: oi_score = -0.8   # OI up + price down = short build
    elif oi_chg < 0 and px_chg < 0: oi_score = -0.4   # deleveraging
    elif oi_chg < 0 and px_chg > 0: oi_score =  0.4   # short squeeze
    else:                            oi_score =  0.0

    scores = {
        'funding_rate':   funding_norm,
        'open_interest':  oi_score,
        'liquidations':   liq_norm,
        'options_skew':   iv_norm,
        'basis':          0.0,       # Basis not fetched yet; neutral placeholder
    }

    weights = {
        'funding_rate':  0.30,
        'open_interest': 0.25,
        'liquidations':  0.22,
        'options_skew':  0.13,
        'basis':         0.10,
    }

    return sum(s * weights[k] for k, s in scores.items()), scores

# ─── Event Decay ─────────────────────────────────────────────────────────────

def apply_event_decay(base_score, events, today):
    event_impact = 0
    for event in events:
        days_elapsed = (today - event['timestamp']).days
        if 0 <= days_elapsed <= event['impact_duration_days']:
            if event['decay_function'] == 'exponential':
                decay = math.exp(-0.1 * days_elapsed)
            elif event['decay_function'] == 'linear':
                decay = 1 - (days_elapsed / event['impact_duration_days'])
            else:
                decay = 1.0
            event_impact += (event['impact_score'] / 3.0) * decay
    return max(-1.0, min(1.0, base_score + event_impact))

# ─── Main Engine ──────────────────────────────────────────────────────────────

def run_engine(df, events):
    latest = df.iloc[-1]

    mrs, mrs_breakdown = compute_macro_regime_score(df)
    ocs, ocs_breakdown = compute_onchain_score(df)
    ims, ims_breakdown = compute_intraday_score(df)

    # Spec §2 composite weights
    w_mrs, w_ocs, w_ims = 0.45, 0.30, 0.25

    regime_name = "Normal"

    # Regime overrides
    if latest.get('vix_level', 0) > 30.0:
        regime_name = "VIX Crisis / Liquidation"
        mrs, ocs, ims = -0.9, -0.7, -0.8
        w_mrs, w_ocs, w_ims = 0.70, 0.15, 0.15

    elif latest.get('mvrv_z_score', 1.5) < 0:
        regime_name = "Deep Value Accumulation"
        w_mrs, w_ocs, w_ims = 0.20, 0.50, 0.30

    elif latest.get('global_m2_13w_change', 0) > 3.0:
        regime_name = "Liquidity Surge"
        w_mrs, w_ocs, w_ims = 0.55, 0.25, 0.20

    elif 180 < latest.get('halving_cycle_day', 0) < 540:
        regime_name = "Post-Halving Bull"

    base_composite = (mrs * w_mrs) + (ocs * w_ocs) + (ims * w_ims)

    if regime_name == "Post-Halving Bull":
        base_composite += 0.15

    final_composite = apply_event_decay(base_composite, events, datetime.date.today())
    final_composite = max(-1.0, min(1.0, final_composite))

    return {
        "mrs":       mrs,
        "ocs":       ocs,
        "ims":       ims,
        "composite": final_composite,
        "regime":    regime_name,
        "cycle_day": latest.get('halving_cycle_day', 0),
        "breakdown": {
            "macro":    mrs_breakdown,
            "onchain":  ocs_breakdown,
            "intraday": ims_breakdown,
        }
    }
