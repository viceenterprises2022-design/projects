#!/usr/bin/env python3
"""
AlphaEdge Market Intelligence Dashboard v3
- 10-factor signal engine (added PCR as standalone #10)
- Option Chain OI chart: spot ±1000pts, Call/Put OI bars, Change OI, PCR, Max Pain
- PixiJS particle canvas, sparklines, animated gauges
- All symbols: NIFTY, SENSEX, BANKNIFTY

Usage:  python market_analysis_v3.py
Output: alphaedge_<timestamp>.html  (auto-opens in browser)
"""

import requests, datetime, os, webbrowser, time, json

# ── Config ────────────────────────────────────────────────────────────────────
UPSTOX_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJGVzY0MDYiLCJqdGkiOiI2OWVjZDE1NTU0ZTdlMzBhNmY0NTZkODYiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaXNFeHRlbmRlZCI6dHJ1ZSwiaWF0IjoxNzc3MTI3NzY1LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE4MDg2OTA0MDB9.lxl6fYYoKH1_2AItX-XN40eNsYhbAzbjnwbvyopgSUo"
UH = {"Authorization": f"Bearer {UPSTOX_TOKEN}", "Accept": "application/json"}

INSTRUMENTS = {
    "NIFTY":     "NSE_INDEX|Nifty 50",
    "SENSEX":    "BSE_INDEX|SENSEX",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "INDIA_VIX": "NSE_INDEX|India VIX"
}
# OI chain available for these only (NSE F&O)
OI_INSTRUMENTS = {
    "NIFTY":     "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "SENSEX":    "BSE_INDEX|SENSEX",   # BSE Sensex options (limited but available)
}
LOT_SIZE = {"NIFTY": 75, "BANKNIFTY": 30, "SENSEX": 20}
OI_RANGE  = 1000   # spot ± 1000 pts
YAHOO_SYM = {"DXY":"DX-Y.NYB","CRUDE_OIL":"CL=F","US30":"YM=F","GOLD":"GC=F","SILVER":"SI=F"}
YAHOO_IDX = {"NIFTY":"^NSEI","SENSEX":"^BSESN","BANKNIFTY":"^NSEBANK"}
YH = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# ── Upstox Fetchers ───────────────────────────────────────────────────────────

def upstox_get(url, params):
    try:
        r = requests.get(url, headers=UH, params=params, timeout=12)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"    [W] {url.split('/')[-1]} {params}: {e}")
    return {}

def fetch_quote(key):
    d = upstox_get("https://api.upstox.com/v2/market-quote/quotes", {"instrument_key": key})
    if d.get("status") == "success" and d.get("data"):
        q = list(d["data"].values())[0]
        ohlc = q.get("ohlc", {}); prev = ohlc.get("close", 0) or 1
        ltp = q.get("last_price", 0); chg = ltp - prev
        return {"ltp":ltp,"open":ohlc.get("open",0),"high":ohlc.get("high",0),
                "low":ohlc.get("low",0),"close":prev,"volume":q.get("volume",0),
                "change":chg,"change_pct":chg/prev*100}
    return None

def fetch_candles(key, days=90):
    today = datetime.date.today()
    f = (today - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    t = today.strftime("%Y-%m-%d")
    d = upstox_get(f"https://api.upstox.com/v2/historical-candle/{key}/day/{t}/{f}", {})
    if d.get("status") == "success":
        raw = d.get("data", {}).get("candles", [])
        return [[c[0],float(c[1]),float(c[2]),float(c[3]),float(c[4]),
                 float(c[5]) if len(c)>5 else 0] for c in raw]
    return []

def fetch_expiries(key):
    """Return sorted list of expiry date strings."""
    d = upstox_get("https://api.upstox.com/v2/option/contract", {"instrument_key": key})
    if d.get("status") == "success" and d.get("data"):
        raw = d["data"]
        if raw and isinstance(raw[0], str):
            return sorted(raw)
        elif raw and isinstance(raw[0], dict):
            return sorted([x.get("expiry","") for x in raw if x.get("expiry")])
    return []

def fetch_option_chain(key, expiry):
    """Fetch full option chain for a given expiry."""
    d = upstox_get("https://api.upstox.com/v2/option/chain",
                   {"instrument_key": key, "expiry_date": expiry})
    if d.get("status") == "success":
        return d.get("data", [])
    return []

def build_oi_data(symbol, spot):
    """
    Fetch option chain, filter to spot ±1000, compute:
    - OI bars (call_oi, put_oi per strike)
    - Change OI (change_in_oi per strike)
    - PCR per strike + total PCR
    - Max Pain strike
    Returns dict with all tabs data.
    """
    key = OI_INSTRUMENTS.get(symbol)
    if not key:
        return None

    expiries = fetch_expiries(key)
    if not expiries:
        print(f"    [W] No expiries for {symbol}")
        return None

    nearest = expiries[0]
    print(f"    {symbol} expiry: {nearest}")
    chain = fetch_option_chain(key, nearest)
    if not chain:
        print(f"    [W] Empty chain for {symbol}")
        return None

    lo = spot - OI_RANGE
    hi = spot + OI_RANGE

    strikes = []
    total_call_oi = 0
    total_put_oi  = 0

    for row in chain:
        if not isinstance(row, dict):
            continue
        strike = row.get("strike_price", 0)
        if not (lo <= strike <= hi):
            continue

        cmd = (row.get("call_options") or {}).get("market_data") or {}
        pmd = (row.get("put_options")  or {}).get("market_data") or {}

        c_oi  = cmd.get("oi", 0) or 0
        p_oi  = pmd.get("oi", 0) or 0
        c_doi = cmd.get("change_in_oi", 0) or 0
        p_doi = pmd.get("change_in_oi", 0) or 0
        c_ltp = cmd.get("ltp", 0) or 0
        p_ltp = pmd.get("ltp", 0) or 0
        c_iv  = cmd.get("iv", 0) or 0
        p_iv  = pmd.get("iv", 0) or 0

        total_call_oi += c_oi
        total_put_oi  += p_oi

        strikes.append({
            "strike":  strike,
            "call_oi": c_oi,
            "put_oi":  p_oi,
            "call_doi": c_doi,
            "put_doi":  p_doi,
            "call_ltp": c_ltp,
            "put_ltp":  p_ltp,
            "call_iv":  c_iv,
            "put_iv":   p_iv,
            "pcr": round(p_oi / max(c_oi, 1), 3),
        })

    if not strikes:
        return None

    strikes.sort(key=lambda x: x["strike"])

    # Max Pain: strike where total loss for option writers is minimized
    def max_pain_loss(target_strike):
        loss = 0
        for s in strikes:
            k = s["strike"]
            # Call writers lose when spot > strike
            if target_strike > k:
                loss += s["call_oi"] * (target_strike - k)
            # Put writers lose when spot < strike
            if target_strike < k:
                loss += s["put_oi"] * (k - target_strike)
        return loss

    min_loss = None
    max_pain_strike = strikes[0]["strike"]
    for s in strikes:
        loss = max_pain_loss(s["strike"])
        if min_loss is None or loss < min_loss:
            min_loss = loss
            max_pain_strike = s["strike"]

    total_pcr = round(total_put_oi / max(total_call_oi, 1), 3)

    return {
        "expiry":         nearest,
        "spot":           spot,
        "strikes":        strikes,
        "total_call_oi":  total_call_oi,
        "total_put_oi":   total_put_oi,
        "total_pcr":      total_pcr,
        "max_pain":       max_pain_strike,
    }

# ── Yahoo Fetcher ─────────────────────────────────────────────────────────────

def fetch_yahoo(symbol, days=60, interval="1d"):
    end = int(time.time()); start = end - days * 86400
    try:
        r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                         params={"period1":start,"period2":end,"interval":interval},
                         headers=YH, timeout=12)
        res = (r.json().get("chart",{}).get("result") or [None])[0]
        if not res: return None
        q = res["indicators"]["quote"][0]; ts = res.get("timestamp",[])
        valid = [(t,o,h,l,c,v) for t,o,h,l,c,v in
                 zip(ts,q.get("open",[]),q.get("high",[]),q.get("low",[]),
                     q.get("close",[]),q.get("volume",[]))
                 if c is not None and o is not None]
        if not valid: return None
        last=valid[-1]; prev=valid[-2][4] if len(valid)>1 else last[4]; chg=last[4]-prev
        return {"ltp":last[4],"open":last[1],"high":last[2],"low":last[3],"close":prev,
                "volume":last[5] or 0,"change":chg,
                "change_pct":chg/prev*100 if prev else 0,
                "candles":[[t,o,h,l,c,v or 0] for t,o,h,l,c,v in valid]}
    except Exception as e:
        print(f"    [W] Yahoo {symbol}: {e}")
    return None

# ── Indicators ────────────────────────────────────────────────────────────────

def ema(v, n):
    if len(v) < n: return []
    out = [sum(v[:n])/n]; k = 2/(n+1)
    for x in v[n:]: out.append(x*k + out[-1]*(1-k))
    return out

def rsi_val(closes, n=14):
    if len(closes) < n+2: return 50.0
    g=[max(closes[i]-closes[i-1],0) for i in range(1,len(closes))]
    l=[max(closes[i-1]-closes[i],0) for i in range(1,len(closes))]
    ag=sum(g[-n:])/n; al=sum(l[-n:])/n
    return 100.0 if al==0 else 100-100/(1+ag/al)

def atr_val(c, n=14):
    trs=[max(c[i][2]-c[i][3],abs(c[i][2]-c[i-1][4]),abs(c[i][3]-c[i-1][4]))
         for i in range(1,len(c))]
    return sum(trs[-n:])/min(n,len(trs)) if trs else 0

def supertrend(c, n=10, m=3):
    if len(c)<n+2: return None,0
    a=atr_val(c,n)
    if a==0: return None,0
    hl2=(c[-1][2]+c[-1][3])/2; lo=hl2-m*a
    d=1 if c[-1][4]>lo else -1
    return (lo if d==1 else hl2+m*a), d

def vwap_val(c, bars=20):
    tv=vol=0.0
    for x in c[-bars:]:
        v=x[5] or 0; tp=(x[2]+x[3]+x[4])/3; tv+=tp*v; vol+=v
    return tv/vol if vol>0 else None

def trend_analysis(c):
    cl=[x[4] for x in c]
    if len(cl)<20: return "N/A",0,""
    e20=ema(cl,20)[-1]; e50=ema(cl,min(50,len(cl)))[-1]
    e200l=ema(cl,min(200,len(cl))); e200=e200l[-1] if e200l else None
    cur=cl[-1]; det=f"EMA20={e20:,.0f} | EMA50={e50:,.0f}"
    if e200: det+=f" | EMA200={e200:,.0f}"
    if e200:
        if cur>e20>e50>e200: return "STRONG UPTREND",2,det
        if cur<e20<e50<e200: return "STRONG DOWNTREND",-2,det
    if cur>e20>e50: return "UPTREND",1,det
    if cur<e20<e50: return "DOWNTREND",-1,det
    if cur>e20: return "MILD UPTREND",1,det
    if cur<e20: return "MILD DOWNTREND",-1,det
    return "SIDEWAYS",0,det

def sig_color(sc, fa):
    r = sc/max(fa,1)
    if r>=0.35:  return "BUY","#00e5b0"
    if r<=-0.35: return "SELL","#ff3d5a"
    return "NEUTRAL","#ffb020"

# ── 10-Factor Analyzer ────────────────────────────────────────────────────────

def analyze(sym, quote, uc, oi_raw, gd, yc):
    """
    Factors:
     1. Trend      (EMA 20/50/200)           weight ±2
     2. Dow Jones  (US30)                    weight ±1
     3. India VIX                            weight ±1
     4. Open Interest (total OI skew)        weight ±1
     5. VWAP                                 weight ±1
     6. Supertrend                           weight ±1
     7. RSI (14)                             weight ±1
     8. US Dollar Index (DXY)               weight ±1
     9. Crude Oil                            weight ±1
    10. PCR  (Put-Call Ratio standalone)     weight ±1
    """
    res={}; sc=fa=0
    c = uc if len(uc)>=10 else yc
    ltp = (quote or {}).get("ltp", 0)

    # 1 TREND
    if len(c)>=20:
        lb,s,dt = trend_analysis(c)
        res["trend"]={"label":lb,"score":s,"detail":dt}
        sc+=s; fa+=2
    else:
        res["trend"]={"label":"N/A","score":0,"detail":f"{len(c)} bars"}

    # 2 DOW JONES
    u=gd.get("US30")
    if u:
        ch=u["change_pct"]; s=1 if ch>0.3 else(-1 if ch<-0.3 else 0)
        res["dow_jones"]={"label":f"{'BULLISH' if s>0 else 'BEARISH' if s<0 else 'FLAT'} ({ch:+.2f}%)",
                          "score":s,"detail":f"DJIA Fut: {u['ltp']:,.0f}"}
        sc+=s; fa+=1
    else: res["dow_jones"]={"label":"N/A","score":0,"detail":"Unavailable"}

    # 3 INDIA VIX
    v=gd.get("VIX")
    if v:
        vv=v["ltp"]
        if vv<13:    s,lb=1, f"LOW ({vv:.2f}) — Calm"
        elif vv<=17: s,lb=1, f"NORMAL ({vv:.2f}) — Stable"
        elif vv<=21: s,lb=0, f"ELEVATED ({vv:.2f}) — Caution"
        else:        s,lb=-1,f"HIGH ({vv:.2f}) — Fear"
        res["india_vix"]={"label":lb,"score":s,"detail":f"Chg: {v.get('change_pct',0):+.2f}%"}
        sc+=s; fa+=1
    else: res["india_vix"]={"label":"N/A","score":0,"detail":"Unavailable"}

    # 4 OPEN INTEREST (total OI skew — separate from PCR)
    if oi_raw:
        total_c = oi_raw["total_call_oi"]; total_p = oi_raw["total_put_oi"]
        # OI skew: if more put OI piled at lower strikes = support = bullish
        # If more call OI at upper strikes = resistance = bearish
        # Simple: compare total call vs put OI magnitude
        oi_ratio = total_c / max(total_p, 1)  # >1 = more calls = bearish (resistance heavy)
        if oi_ratio > 1.3:   s,lb=-1,f"CALL HEAVY — Resistance strong"
        elif oi_ratio > 1.1: s,lb=-1,f"MILD CALL HEAVY"
        elif oi_ratio < 0.7: s,lb=1, f"PUT HEAVY — Support strong"
        elif oi_ratio < 0.9: s,lb=1, f"MILD PUT HEAVY"
        else:                 s,lb=0, f"BALANCED OI"
        cL=total_c/1e5; pL=total_p/1e5
        res["oi"]={"label":lb,"score":s,
                   "detail":f"Calls:{cL:.1f}L | Puts:{pL:.1f}L | Exp:{oi_raw['expiry']}"}
        sc+=s; fa+=1
    else:
        res["oi"]={"label":"N/A","score":0,"detail":"Market closed / BSE chain"}

    # 5 VWAP
    if c and ltp:
        vw=vwap_val(c)
        if vw:
            dp=(ltp-vw)/vw*100
            if ltp>vw*1.002:    s,lb=1, f"ABOVE (+{dp:.2f}%)"
            elif ltp<vw*0.998:  s,lb=-1,f"BELOW ({dp:.2f}%)"
            else:                s,lb=0, f"AT VWAP ({dp:+.2f}%)"
            res["vwap"]={"label":lb,"score":s,"detail":f"VWAP:{vw:,.2f} | LTP:{ltp:,.2f}"}
            sc+=s; fa+=1
        else: res["vwap"]={"label":"N/A","score":0,"detail":"No volume data"}
    else: res["vwap"]={"label":"N/A","score":0,"detail":"No candles"}

    # 6 SUPERTREND
    if len(c)>=12:
        stv,std=supertrend(c)
        if std==1:    lb=f"BULLISH (Sup≈{stv:,.0f})" if stv else "BULLISH"
        elif std==-1: lb=f"BEARISH (Res≈{stv:,.0f})" if stv else "BEARISH"
        else:          lb="NEUTRAL"
        res["supertrend"]={"label":lb,"score":std,"detail":"ATR(10) × 3"}
        sc+=std; fa+=1
    else: res["supertrend"]={"label":"N/A","score":0,"detail":"Need ≥12 bars"}

    # 7 RSI
    if len(c)>=16:
        rv=rsi_val([x[4] for x in c])
        if rv>=75:    s,lb=-1,f"OVERBOUGHT ({rv:.1f})"
        elif rv>=60:  s,lb=1, f"BULLISH ZONE ({rv:.1f})"
        elif rv<=25:  s,lb=1, f"OVERSOLD ({rv:.1f})"
        elif rv<=40:  s,lb=-1,f"BEARISH ZONE ({rv:.1f})"
        else:          s,lb=0, f"NEUTRAL ({rv:.1f})"
        res["rsi"]={"label":lb,"score":s,"detail":"RSI(14) Daily"}
        sc+=s; fa+=1
    else: res["rsi"]={"label":"N/A","score":0,"detail":"Need ≥16 bars"}

    # 8 DXY
    dx=gd.get("DXY")
    if dx:
        ch=dx["change_pct"]
        if ch>0.5:    s,lb=-1,f"SURGING ({ch:+.2f}%) — EM risk"
        elif ch>0.2:  s,lb=-1,f"STRENGTHENING ({ch:+.2f}%)"
        elif ch<-0.5: s,lb=1, f"WEAKENING ({ch:+.2f}%) — EM positive"
        elif ch<-0.2: s,lb=1, f"SOFTENING ({ch:+.2f}%)"
        else:          s,lb=0, f"STABLE ({ch:+.2f}%)"
        res["dxy"]={"label":lb,"score":s,"detail":f"DXY: {dx['ltp']:.3f}"}
        sc+=s; fa+=1
    else: res["dxy"]={"label":"N/A","score":0,"detail":"Unavailable"}

    # 9 CRUDE OIL
    cr=gd.get("CRUDE_OIL")
    if cr:
        ch=cr["change_pct"]
        if ch>2.0:    s,lb=-1,f"SURGING ({ch:+.2f}%) — Inflation risk"
        elif ch>0.8:  s,lb=-1,f"RISING ({ch:+.2f}%)"
        elif ch<-2.0: s,lb=1, f"CRASHING ({ch:+.2f}%)"
        elif ch<-0.8: s,lb=1, f"FALLING ({ch:+.2f}%)"
        else:          s,lb=0, f"STABLE ({ch:+.2f}%)"
        res["crude"]={"label":lb,"score":s,"detail":f"WTI: ${cr['ltp']:.2f}"}
        sc+=s; fa+=1
    else: res["crude"]={"label":"N/A","score":0,"detail":"Unavailable"}

    # 10 PCR (standalone)
    if oi_raw:
        pcr=oi_raw["total_pcr"]; mp=oi_raw["max_pain"]
        if pcr>1.3:    s,lb=1, f"BULLISH — PCR {pcr:.2f} (above 1.3)"
        elif pcr>1.1:  s,lb=1, f"MILDLY BULLISH — PCR {pcr:.2f}"
        elif pcr<0.7:  s,lb=-1,f"BEARISH — PCR {pcr:.2f} (below 0.7)"
        elif pcr<0.9:  s,lb=-1,f"MILDLY BEARISH — PCR {pcr:.2f}"
        else:           s,lb=0, f"NEUTRAL — PCR {pcr:.2f}"
        res["pcr"]={"label":lb,"score":s,
                    "detail":f"Max Pain: {mp:,.0f} | Total PCR: {pcr:.2f}"}
        sc+=s; fa+=1
    else:
        res["pcr"]={"label":"N/A","score":0,"detail":"Requires option chain data"}

    sg,sgc=sig_color(sc,fa)
    return {"indicators":res,"score":sc,"factors":fa,"signal":sg,"signal_color":sgc,
            "candles":c[-30:] if c else []}

# ── HTML Generator ────────────────────────────────────────────────────────────

def gen_html(analyses, quotes, gdata, oi_map, ts):
    NAMES={
        "trend":"Trend","dow_jones":"Dow Jones","india_vix":"India VIX",
        "oi":"Open Interest","vwap":"VWAP","supertrend":"Supertrend",
        "rsi":"RSI (14)","dxy":"USD Index","crude":"Crude Oil","pcr":"Put-Call Ratio"
    }

    # Build symbol JSON for JS
    sym_data={}
    for sym in ["NIFTY","SENSEX","BANKNIFTY"]:
        a=analyses[sym]; q=quotes.get(sym,{})
        inds=[{"key":k,"name":NAMES.get(k,k),"label":d.get("label","—"),
               "detail":d.get("detail",""),"score":d.get("score",0)}
              for k,d in a["indicators"].items()]
        oi=oi_map.get(sym)
        sym_data[sym]={
            "ltp":q.get("ltp",0),"open":q.get("open",0),
            "high":q.get("high",0),"low":q.get("low",0),
            "change_pct":q.get("change_pct",0),
            "signal":a["signal"],"signal_color":a["signal_color"],
            "score":a["score"],"factors":a["factors"],
            "indicators":inds,
            "candles":[[x[1],x[2],x[3],x[4]] for x in a["candles"]],
            "oi_chain": oi if oi else None,
        }

    global_data={
        "VIX":   {"ltp":gdata.get("VIX",{}).get("ltp","—"),   "chg":gdata.get("VIX",{}).get("change_pct",0)},
        "DXY":   {"ltp":gdata.get("DXY",{}).get("ltp","—"),   "chg":gdata.get("DXY",{}).get("change_pct",0)},
        "CRUDE": {"ltp":gdata.get("CRUDE_OIL",{}).get("ltp","—"),"chg":gdata.get("CRUDE_OIL",{}).get("change_pct",0)},
        "US30":  {"ltp":gdata.get("US30",{}).get("ltp","—"),  "chg":gdata.get("US30",{}).get("change_pct",0)},
        "GOLD":  {"ltp":gdata.get("GOLD",{}).get("ltp","—"),  "chg":gdata.get("GOLD",{}).get("change_pct",0)},
        "SILVER":{"ltp":gdata.get("SILVER",{}).get("ltp","—"),"chg":gdata.get("SILVER",{}).get("change_pct",0)},
    }

    sym_json    = json.dumps(sym_data)
    global_json = json.dumps(global_data)
    yr = datetime.date.today().year

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AlphaEdge · Market Intelligence · {ts}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Clash+Display:wght@400;500;600;700&family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/pixi.js/7.3.2/pixi.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{
  --bg:#03030a;--glass:rgba(255,255,255,0.033);--glass2:rgba(255,255,255,0.055);
  --bdr:rgba(255,255,255,0.07);--bdr2:rgba(255,255,255,0.13);
  --tx:#e8eaf6;--tx2:#8890b8;--tx3:#50547a;
  --buy:#00e5b0;--sell:#ff3d5a;--neu:#ffb020;
  --sans:'Clash Display',system-ui,sans-serif;--mono:'DM Mono',monospace;
}}
html{{scroll-behavior:smooth}}
body{{background:var(--bg);color:var(--tx);font-family:var(--sans);overflow-x:hidden}}
#pixi-canvas{{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none;opacity:0.55}}
#app{{position:relative;z-index:1}}

/* HEADER */
.header{{display:flex;align-items:center;justify-content:space-between;
  padding:16px 32px;background:rgba(3,3,10,0.9);backdrop-filter:blur(24px);
  border-bottom:1px solid var(--bdr);position:sticky;top:0;z-index:100}}
.logo{{display:flex;align-items:center;gap:14px}}
.logo-mark{{width:40px;height:40px;background:linear-gradient(135deg,#6366f1,#00e5b0);
  border-radius:11px;display:flex;align-items:center;justify-content:center;
  font-size:18px;font-weight:700;color:#fff;box-shadow:0 0 24px rgba(99,102,241,0.35)}}
.logo-text{{font-size:19px;font-weight:700;letter-spacing:-.5px}}
.logo-sub{{font-size:10px;color:var(--tx2);font-family:var(--mono);margin-top:2px;letter-spacing:.5px}}
.hdr-r{{text-align:right}}
.hdr-ts{{font-family:var(--mono);font-size:11px;color:var(--tx2)}}
.pulse{{display:inline-block;width:7px;height:7px;background:var(--buy);border-radius:50%;
  margin-right:6px;animation:pulse 2s infinite;box-shadow:0 0 6px var(--buy)}}
@keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:.3;transform:scale(.6)}}}}

/* TICKER */
.ticker-bar{{background:rgba(255,255,255,0.018);border-bottom:1px solid var(--bdr);
  overflow:hidden;height:42px;display:flex;align-items:center}}
.ticker-track{{display:flex;animation:ticker 35s linear infinite;white-space:nowrap}}
.ticker-track:hover{{animation-play-state:paused}}
.t-item{{display:inline-flex;align-items:center;gap:10px;padding:0 24px;
  border-right:1px solid var(--bdr);height:42px}}
.t-name{{font-size:10px;color:var(--tx3);font-family:var(--mono);letter-spacing:1px}}
.t-val{{font-family:var(--mono);font-size:13px;font-weight:500}}
.t-chg{{font-family:var(--mono);font-size:11px;font-weight:500}}
.up{{color:var(--buy)}}.dn{{color:var(--sell)}}
@keyframes ticker{{from{{transform:translateX(0)}}to{{transform:translateX(-50%)}}}}

/* MAIN LAYOUT: Signal cards on left, OI chart on right per symbol */
.sym-section{{max-width:1520px;margin:0 auto;padding:24px 20px 10px}}
.sym-section:last-child{{padding-bottom:60px}}
.sym-divider{{
  display:flex;align-items:center;gap:16px;margin-bottom:18px;
  font-size:11px;font-family:var(--mono);color:var(--tx3);letter-spacing:1px
}}
.sym-divider::after{{content:'';flex:1;height:1px;background:var(--bdr)}}

.sym-grid{{display:grid;grid-template-columns:380px 1fr;gap:20px;align-items:start}}
@media(max-width:900px){{.sym-grid{{grid-template-columns:1fr}}}}

/* SIGNAL CARD */
.card{{
  background:var(--glass);border:1px solid var(--bdr);border-radius:18px;
  overflow:hidden;backdrop-filter:blur(20px);
  border-top:2px solid var(--sc);
  box-shadow:0 0 50px var(--sg),0 16px 40px rgba(0,0,0,0.35);
  animation:cardIn .5s cubic-bezier(.34,1.56,.64,1) both;
}}
@keyframes cardIn{{from{{opacity:0;transform:translateY(30px)}}to{{opacity:1;transform:translateY(0)}}}}
.card:hover{{border-color:var(--bdr2)}}

.card-head{{padding:20px 22px 14px;background:var(--glass2);border-bottom:1px solid var(--bdr);position:relative}}
.sym-row{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px}}
.sym-name{{font-size:24px;font-weight:700;letter-spacing:-1px;color:#fff}}
.sig-badge{{display:inline-flex;align-items:center;gap:5px;padding:5px 14px;
  border-radius:100px;font-size:12px;font-weight:600;letter-spacing:.5px;
  background:var(--sc);color:#000;box-shadow:0 0 18px var(--sg)}}
.price-row{{display:flex;align-items:baseline;gap:10px;margin-bottom:6px}}
.ltp{{font-family:var(--mono);font-size:26px;font-weight:500;letter-spacing:-1px}}
.chg{{font-family:var(--mono);font-size:13px}}
.ohlc{{display:flex;gap:16px;font-family:var(--mono);font-size:10px;color:var(--tx3)}}
.ohlc span{{display:flex;flex-direction:column;gap:1px}}
.ohlc .ol{{font-size:8px;text-transform:uppercase;letter-spacing:.5px}}
.ohlc .ov{{color:var(--tx2);font-size:11px}}

/* SPARKLINE */
.spark-wrap{{margin:0 22px 14px;height:48px}}
canvas.spark{{width:100%;height:48px;border-radius:6px}}

/* GAUGE */
.gauge-sec{{display:flex;flex-direction:column;align-items:center;
  padding:12px 22px;border-bottom:1px solid var(--bdr)}}
.gauge-wrap{{position:relative;width:130px;height:70px;margin-bottom:6px}}
.gauge-svg{{width:130px;height:70px}}
.gauge-score{{position:absolute;bottom:0;left:50%;transform:translateX(-50%);text-align:center}}
.gauge-num{{font-family:var(--mono);font-size:20px;font-weight:500;line-height:1}}
.gauge-lbl{{font-size:9px;color:var(--tx3);font-family:var(--mono);letter-spacing:.5px;margin-top:2px}}

/* INDICATOR ROWS */
.ind-list{{padding:0 0 6px}}
.ind-row{{display:grid;grid-template-columns:30px 1fr auto;align-items:center;
  gap:10px;padding:9px 22px;border-bottom:1px solid rgba(255,255,255,0.03);
  transition:background .15s;animation:rowIn .4s ease both}}
.ind-row:hover{{background:rgba(255,255,255,0.025)}}
.ind-row:last-child{{border-bottom:none}}
.ind-num{{width:26px;height:26px;border-radius:7px;display:flex;align-items:center;
  justify-content:center;font-size:9px;font-weight:600;font-family:var(--mono);
  color:#000;flex-shrink:0}}
.ind-body{{min-width:0}}
.ind-name{{font-size:11px;font-weight:600;color:var(--tx);margin-bottom:1px}}
.ind-label{{font-size:10px;color:var(--tx2);font-family:var(--mono);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.ind-detail{{font-size:9px;color:var(--tx3);font-family:var(--mono)}}
.ind-pip{{width:6px;height:6px;border-radius:50%;flex-shrink:0}}
@keyframes rowIn{{from{{opacity:0;transform:translateX(-8px)}}to{{opacity:1;transform:translateX(0)}}}}

/* OI CHART PANEL */
.oi-panel{{
  background:var(--glass);border:1px solid var(--bdr);border-radius:18px;
  overflow:hidden;backdrop-filter:blur(20px);
  animation:cardIn .5s cubic-bezier(.34,1.56,.64,1) .15s both;
}}
.oi-head{{
  padding:16px 22px 12px;background:var(--glass2);
  border-bottom:1px solid var(--bdr);
  display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px
}}
.oi-title{{font-size:14px;font-weight:600;color:var(--tx)}}
.oi-meta{{display:flex;gap:20px;font-family:var(--mono);font-size:11px;color:var(--tx2)}}
.oi-meta span{{display:flex;flex-direction:column;gap:2px}}
.oi-meta .ml{{font-size:9px;color:var(--tx3);text-transform:uppercase;letter-spacing:.5px}}
.oi-meta .mv{{color:var(--tx)}}

/* TABS */
.oi-tabs{{display:flex;gap:6px;padding:14px 22px 0;border-bottom:1px solid var(--bdr)}}
.tab-btn{{
  padding:6px 16px;border-radius:100px;font-size:11px;font-weight:600;
  font-family:var(--sans);cursor:pointer;border:1px solid var(--bdr);
  background:transparent;color:var(--tx2);transition:all .2s;letter-spacing:.3px
}}
.tab-btn:hover{{background:var(--glass2);color:var(--tx);border-color:var(--bdr2)}}
.tab-btn.active{{background:linear-gradient(135deg,#6366f1,#818cf8);
  color:#fff;border-color:transparent;box-shadow:0 0 14px rgba(99,102,241,.35)}}

/* CHART AREA */
.oi-chart-wrap{{padding:18px 22px 14px;position:relative}}
.oi-stats{{display:flex;gap:20px;margin-bottom:14px;flex-wrap:wrap}}
.oi-stat{{display:flex;align-items:center;gap:7px;font-family:var(--mono);font-size:11px}}
.oi-stat-dot{{width:10px;height:10px;border-radius:3px;flex-shrink:0}}
.oi-chart-canvas{{width:100%;height:220px;cursor:crosshair}}
.oi-tooltip{{
  position:absolute;background:rgba(10,10,25,0.95);border:1px solid var(--bdr2);
  border-radius:10px;padding:10px 14px;pointer-events:none;
  font-family:var(--mono);font-size:11px;display:none;z-index:10;
  backdrop-filter:blur(8px);min-width:160px
}}
.oi-tooltip .tt-strike{{font-size:14px;font-weight:500;color:#fff;margin-bottom:6px}}
.oi-tooltip .tt-row{{display:flex;justify-content:space-between;gap:16px;margin-bottom:2px}}
.oi-tooltip .tt-lbl{{color:var(--tx3)}}

/* MAX PAIN marker */
.mp-label{{position:absolute;font-family:var(--mono);font-size:10px;
  color:#a78bfa;background:rgba(167,139,250,.12);
  padding:2px 8px;border-radius:4px;border:1px solid rgba(167,139,250,.25);pointer-events:none}}

/* FOOTER */
.footer{{text-align:center;padding:22px;border-top:1px solid var(--bdr);
  font-family:var(--mono);font-size:10px;color:var(--tx3);line-height:2;
  background:rgba(255,255,255,0.01)}}
::-webkit-scrollbar{{width:4px;height:4px}}
::-webkit-scrollbar-track{{background:transparent}}
::-webkit-scrollbar-thumb{{background:rgba(255,255,255,0.1);border-radius:4px}}
</style>
</head>
<body>
<canvas id="pixi-canvas"></canvas>
<div id="app">

<header class="header">
  <div class="logo">
    <div class="logo-mark">α</div>
    <div>
      <div class="logo-text">AlphaEdge</div>
      <div class="logo-sub">FINANCIAL INTELLIGENCE · PINAKA.AI</div>
    </div>
  </div>
  <div class="hdr-r">
    <div class="hdr-ts"><span class="pulse"></span>{ts} IST</div>
    <div class="hdr-ts" style="margin-top:3px;color:var(--tx3)">10-FACTOR SIGNAL ENGINE</div>
  </div>
</header>

<div class="ticker-bar"><div class="ticker-track" id="ticker"></div></div>

<div id="main-content"></div>

<footer class="footer">
  <div>⚠ For informational purposes only · Not financial advice · Always conduct your own due diligence</div>
  <div>AlphaEdge © {yr} · Data: Upstox API + Yahoo Finance · Signals regenerate on each run</div>
</footer>
</div>

<script>
const SYM_DATA    = {sym_json};
const GLOBAL_DATA = {global_json};

// ── PIXI BACKGROUND ──────────────────────────────────────────────────────────
(async () => {{
  try {{
    const app = new PIXI.Application({{
      view: document.getElementById('pixi-canvas'),
      width: window.innerWidth, height: window.innerHeight,
      backgroundColor: 0x03030a,
      resolution: Math.min(window.devicePixelRatio||1, 2),
      autoDensity: true, antialias: true,
    }});
    const COLS=[0x6366f1,0x00e5b0,0xff3d5a,0xffb020,0x818cf8];
    const ps=[]; const N=70;
    const cont=new PIXI.Container(); app.stage.addChild(cont);
    const lines=new PIXI.Graphics(); app.stage.addChildAt(lines,0);
    for(let i=0;i<N;i++){{
      const g=new PIXI.Graphics();
      g.beginFill(COLS[i%COLS.length],0.75).drawCircle(0,0,Math.random()*1.8+0.4).endFill();
      g.x=Math.random()*app.screen.width; g.y=Math.random()*app.screen.height;
      const a=Math.random()*Math.PI*2, sp=Math.random()*0.35+0.08;
      ps.push({{g,vx:Math.cos(a)*sp,vy:Math.sin(a)*sp,life:Math.random(),ls:Math.random()*.004+.002}});
      cont.addChild(g);
    }}
    app.ticker.add(()=>{{
      lines.clear();
      const W=app.screen.width,H=app.screen.height;
      for(let i=0;i<ps.length;i++){{
        const p=ps[i];
        p.g.x+=p.vx; p.g.y+=p.vy; p.life+=p.ls;
        p.g.alpha=(Math.sin(p.life)*.5+.5)*.7+.1;
        if(p.g.x<-10)p.g.x=W+10; if(p.g.x>W+10)p.g.x=-10;
        if(p.g.y<-10)p.g.y=H+10; if(p.g.y>H+10)p.g.y=-10;
        for(let j=i+1;j<ps.length;j++){{
          const q=ps[j],dx=p.g.x-q.g.x,dy=p.g.y-q.g.y,d=Math.sqrt(dx*dx+dy*dy);
          if(d<110){{lines.lineStyle(.4,0x6366f1,(1-d/110)*.12);lines.moveTo(p.g.x,p.g.y);lines.lineTo(q.g.x,q.g.y);}}
        }}
      }}
    }});
    window.addEventListener('resize',()=>app.renderer.resize(window.innerWidth,window.innerHeight));
  }}catch(e){{console.warn('Pixi:',e)}}
}})();

// ── UTILS ────────────────────────────────────────────────────────────────────
const fmtL=(v,d=2)=>typeof v==='number'?v.toLocaleString('en-IN',{{minimumFractionDigits:d,maximumFractionDigits:d}}):'—';
const fmtK=(v)=>{{if(!v)return'0';const l=v/1e5;return l>=1?l.toFixed(1)+'L':(v/1e3).toFixed(1)+'K';}};
const sc=(s)=>s>0?'#00e5b0':s<0?'#ff3d5a':'#ffb020';
const sigIcon=(s)=>s==='BUY'?'▲':s==='SELL'?'▼':'◆';
const sigGlow=(s)=>s==='BUY'?'rgba(0,229,176,0.25)':s==='SELL'?'rgba(255,61,90,0.25)':'rgba(255,176,32,0.25)';

// ── TICKER ───────────────────────────────────────────────────────────────────
function buildTicker(){{
  const items=[
    ['NIFTY',SYM_DATA.NIFTY.ltp,SYM_DATA.NIFTY.change_pct,2,''],
    ['SENSEX',SYM_DATA.SENSEX.ltp,SYM_DATA.SENSEX.change_pct,2,''],
    ['BANKNIFTY',SYM_DATA.BANKNIFTY.ltp,SYM_DATA.BANKNIFTY.change_pct,2,''],
    ['VIX',GLOBAL_DATA.VIX.ltp,GLOBAL_DATA.VIX.chg,2,''],
    ['DXY',GLOBAL_DATA.DXY.ltp,GLOBAL_DATA.DXY.chg,3,''],
    ['CRUDE',GLOBAL_DATA.CRUDE.ltp,GLOBAL_DATA.CRUDE.chg,2,'$'],
    ['US30',GLOBAL_DATA.US30.ltp,GLOBAL_DATA.US30.chg,0,''],
    ['GOLD',GLOBAL_DATA.GOLD.ltp,GLOBAL_DATA.GOLD.chg,1,'$'],
    ['SILVER',GLOBAL_DATA.SILVER.ltp,GLOBAL_DATA.SILVER.chg,2,'$'],
  ];
  const html=[...items,...items].map(([n,v,c,d,pre])=>{{
    const cv=parseFloat(c)||0,cls=cv>=0?'up':'dn',arr=cv>=0?'▲':'▼';
    const val=typeof v==='number'?pre+fmtL(v,d):v;
    return `<div class="t-item"><span class="t-name">${{n}}</span><span class="t-val">${{val}}</span><span class="t-chg ${{cls}}">${{arr}} ${{Math.abs(cv).toFixed(2)}}%</span></div>`;
  }}).join('');
  document.getElementById('ticker').innerHTML=html;
}}

// ── SPARKLINE ────────────────────────────────────────────────────────────────
function drawSpark(canvas,candles,color){{
  if(!candles||candles.length<2)return;
  const closes=candles.map(c=>c[3]);
  const W=canvas.offsetWidth||320,H=48,dpr=window.devicePixelRatio||1;
  canvas.width=W*dpr;canvas.height=H*dpr;
  const ctx=canvas.getContext('2d'); ctx.scale(dpr,dpr);
  const mn=Math.min(...closes),mx=Math.max(...closes),rng=mx-mn||1;
  const xs=W/(closes.length-1);
  const pts=closes.map((v,i)=>[i*xs,H-((v-mn)/rng)*(H-8)-4]);
  const grad=ctx.createLinearGradient(0,0,0,H);
  grad.addColorStop(0,color+'44');grad.addColorStop(1,color+'00');
  ctx.beginPath();ctx.moveTo(pts[0][0],H);
  pts.forEach(([x,y])=>ctx.lineTo(x,y));
  ctx.lineTo(pts[pts.length-1][0],H);ctx.closePath();
  ctx.fillStyle=grad;ctx.fill();
  ctx.beginPath();pts.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));
  ctx.strokeStyle=color;ctx.lineWidth=1.5;ctx.lineJoin='round';ctx.stroke();
  const[lx,ly]=pts[pts.length-1];
  ctx.beginPath();ctx.arc(lx,ly,2.5,0,Math.PI*2);ctx.fillStyle=color;ctx.fill();
  ctx.beginPath();ctx.arc(lx,ly,5,0,Math.PI*2);ctx.fillStyle=color+'30';ctx.fill();
}}

// ── GAUGE ────────────────────────────────────────────────────────────────────
function drawGauge(svg,score,factors,color){{
  const pct=Math.max(0,Math.min(1,(score/Math.max(factors,1)+1)/2));
  const R=52,cx=65,cy=64;
  const [ex,ey]=[cx+R*Math.cos(Math.PI+pct*Math.PI),cy+R*Math.sin(Math.PI+pct*Math.PI)];
  const la=pct>.5?1:0;
  const uid='g'+Math.random().toString(36).slice(2,7);
  svg.innerHTML=`<defs>
    <linearGradient id="${{uid}}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="${{score<0?'#ff3d5a':'#ffb020'}}"/>
      <stop offset="100%" stop-color="${{color}}"/>
    </linearGradient>
    <filter id="gl${{uid}}"><feGaussianBlur stdDeviation="2.5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <path d="M ${{cx-R}} ${{cy}} A ${{R}} ${{R}} 0 0 1 ${{cx+R}} ${{cy}}" fill="none"
        stroke="rgba(255,255,255,0.06)" stroke-width="7" stroke-linecap="round"/>
  <path d="M ${{cx-R}} ${{cy}} A ${{R}} ${{R}} 0 ${{la}} 1 ${{ex}} ${{ey}}" fill="none"
        stroke="url(#${{uid}})" stroke-width="7" stroke-linecap="round" filter="url(#gl${{uid}})"/>
  <circle cx="${{ex}}" cy="${{ey}}" r="4.5" fill="${{color}}" filter="url(#gl${{uid}})"/>`;
}}

// ── OI CHART ─────────────────────────────────────────────────────────────────
const CALL_COL='#00e5b0', PUT_COL='#ff6b6b';
const CALL_DOI_COL='#6366f1', PUT_DOI_COL='#f97316';

function renderOIChart(canvas,tooltip,strikes,spot,maxPainStrike,activeTab){{
  if(!strikes||!strikes.length)return;
  const W=canvas.offsetWidth||600,H=canvas.offsetHeight||220,dpr=window.devicePixelRatio||1;
  canvas.width=W*dpr;canvas.height=H*dpr;
  const ctx=canvas.getContext('2d'); ctx.scale(dpr,dpr);
  ctx.clearRect(0,0,W,H);

  // Determine values by tab
  let vals;
  if(activeTab==='oi'){{
    vals=strikes.map(s=>([s.call_oi,s.put_oi]));
  }}else if(activeTab==='doi'){{
    vals=strikes.map(s=>([s.call_doi,s.put_doi]));
  }}else if(activeTab==='pcr'){{
    // PCR bar chart: single bar per strike
    vals=strikes.map(s=>([s.pcr,0]));
  }}else{{
    // Max Pain — show call+put OI with max pain highlighted
    vals=strikes.map(s=>([s.call_oi,s.put_oi]));
  }}

  const isPCR=activeTab==='pcr';
  const isDOI=activeTab==='doi';
  const n=strikes.length;
  const PAD_L=52,PAD_R=16,PAD_T=20,PAD_B=48;
  const chartW=W-PAD_L-PAD_R, chartH=H-PAD_T-PAD_B;
  const barW=Math.max(4,(chartW/n)*0.38);
  const xStep=chartW/n;

  // Y scale
  let allVals=[];
  if(isPCR){{
    allVals=strikes.map(s=>s.pcr);
  }}else if(isDOI){{
    strikes.forEach(s=>{{allVals.push(Math.abs(s.call_doi),Math.abs(s.put_doi))}});
  }}else{{
    strikes.forEach(s=>{{allVals.push(s.call_oi,s.put_oi)}});
  }}
  const maxV=Math.max(...allVals)*1.12||1;
  const minV=isDOI?-maxV:0;
  const totalRange=maxV-minV;

  function yPos(v){{return PAD_T+chartH*(1-(v-minV)/totalRange);}}

  // Grid lines
  const gridN=4;
  ctx.strokeStyle='rgba(255,255,255,0.05)';ctx.lineWidth=1;
  for(let i=0;i<=gridN;i++){{
    const v=minV+(totalRange/gridN)*i;
    const y=yPos(v);
    ctx.beginPath();ctx.moveTo(PAD_L,y);ctx.lineTo(W-PAD_R,y);ctx.stroke();
    // Y label
    ctx.fillStyle='rgba(255,255,255,0.3)';ctx.font=`${{9*dpr/dpr}}px DM Mono,monospace`;
    ctx.textAlign='right';
    const lbl=isPCR?v.toFixed(2):(Math.abs(v)>=1e5?(v/1e5).toFixed(1)+'L':(v/1e3).toFixed(0)+'K');
    ctx.fillText(lbl,PAD_L-6,y+3);
  }}

  // Zero line for DOI
  if(isDOI){{
    const zy=yPos(0);
    ctx.strokeStyle='rgba(255,255,255,0.15)';ctx.lineWidth=1;
    ctx.beginPath();ctx.moveTo(PAD_L,zy);ctx.lineTo(W-PAD_R,zy);ctx.stroke();
  }}

  // Bars
  strikes.forEach((s,i)=>{{
    const cx=PAD_L+xStep*i+xStep/2;
    if(isPCR){{
      // Single PCR bar, colored by bullish/bearish
      const v=s.pcr;
      const col=v>1.2?PUT_COL:v<0.8?CALL_COL:'#ffb020';
      const top=yPos(v),bot=yPos(0);
      ctx.fillStyle=col+'cc';
      ctx.fillRect(cx-barW/2,top,barW,bot-top);
    }}else{{
      const cv=vals[i][0],pv=vals[i][1];
      // Call bar (left of center)
      if(cv!==0){{
        const col=isDOI?CALL_DOI_COL:CALL_COL;
        const top=cv>=0?yPos(cv):yPos(0);
        const bot=cv>=0?yPos(0):yPos(cv);
        const grad=ctx.createLinearGradient(0,top,0,bot);
        grad.addColorStop(0,col+'ee');grad.addColorStop(1,col+'66');
        ctx.fillStyle=grad;
        ctx.fillRect(cx-barW-2,top,barW,bot-top);
      }}
      // Put bar (right of center)
      if(pv!==0){{
        const col=isDOI?PUT_DOI_COL:PUT_COL;
        const top=pv>=0?yPos(pv):yPos(0);
        const bot=pv>=0?yPos(0):yPos(pv);
        const grad=ctx.createLinearGradient(0,top,0,bot);
        grad.addColorStop(0,col+'ee');grad.addColorStop(1,col+'66');
        ctx.fillStyle=grad;
        ctx.fillRect(cx+2,top,barW,bot-top);
      }}
    }}

    // X label (every 2nd strike to avoid clutter)
    if(i%2===0||n<=12){{
      ctx.fillStyle='rgba(255,255,255,0.3)';ctx.font=`9px DM Mono,monospace`;
      ctx.textAlign='center';
      const lbl=s.strike>=1000?(s.strike/1000).toFixed(0)+'k':s.strike.toString();
      ctx.fillText(lbl,cx,H-PAD_B+16);
    }}
  }});

  // Spot price dashed vertical line
  const spotIdx=strikes.findIndex(s=>s.strike>=spot);
  if(spotIdx>=0){{
    const spotX=PAD_L+xStep*spotIdx+xStep/2;
    ctx.strokeStyle='rgba(255,255,255,0.5)';ctx.lineWidth=1;
    ctx.setLineDash([4,4]);ctx.beginPath();
    ctx.moveTo(spotX,PAD_T);ctx.lineTo(spotX,H-PAD_B);ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle='rgba(255,255,255,0.7)';ctx.font='bold 10px DM Mono,monospace';
    ctx.textAlign='center';
    ctx.fillText('Spot '+fmtL(spot,0),spotX,PAD_T-6);
  }}

  // Max Pain line
  if(activeTab==='maxpain'||activeTab==='oi'){{
    const mpIdx=strikes.findIndex(s=>s.strike>=maxPainStrike);
    if(mpIdx>=0){{
      const mpX=PAD_L+xStep*mpIdx+xStep/2;
      ctx.strokeStyle='rgba(167,139,250,0.7)';ctx.lineWidth=1.5;
      ctx.setLineDash([3,3]);ctx.beginPath();
      ctx.moveTo(mpX,PAD_T);ctx.lineTo(mpX,H-PAD_B);ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle='rgba(167,139,250,0.9)';ctx.font='9px DM Mono,monospace';
      ctx.textAlign='center';
      ctx.fillText('MaxPain',mpX,PAD_T+10);
    }}
  }}

  // Hover tooltip
  canvas._strikes=strikes;canvas._spot=spot;canvas._tab=activeTab;
  canvas._PAD_L=PAD_L;canvas._xStep=xStep;canvas._n=n;
  canvas._tooltip=tooltip;canvas._maxPain=maxPainStrike;
}}

function attachOIHover(canvas){{
  canvas.addEventListener('mousemove',(e)=>{{
    const rect=canvas.getBoundingClientRect();
    const x=e.clientX-rect.left;
    const i=Math.floor((x-canvas._PAD_L)/canvas._xStep);
    const strikes=canvas._strikes; const tt=canvas._tooltip;
    if(!strikes||i<0||i>=strikes.length){{tt.style.display='none';return;}}
    const s=strikes[i]; const tab=canvas._tab;
    let rows='';
    if(tab==='pcr'){{
      rows=`<div class="tt-row"><span class="tt-lbl">PCR</span><span style="color:#ffb020">${{s.pcr.toFixed(2)}}</span></div>
            <div class="tt-row"><span class="tt-lbl">Call OI</span><span style="color:#00e5b0">${{fmtK(s.call_oi)}}</span></div>
            <div class="tt-row"><span class="tt-lbl">Put OI</span><span style="color:#ff6b6b">${{fmtK(s.put_oi)}}</span></div>`;
    }}else if(tab==='doi'){{
      rows=`<div class="tt-row"><span class="tt-lbl">Call Δ OI</span><span style="color:#6366f1">${{fmtK(s.call_doi)}}</span></div>
            <div class="tt-row"><span class="tt-lbl">Put Δ OI</span><span style="color:#f97316">${{fmtK(s.put_doi)}}</span></div>`;
    }}else{{
      rows=`<div class="tt-row"><span class="tt-lbl">Call OI</span><span style="color:#00e5b0">${{fmtK(s.call_oi)}}</span></div>
            <div class="tt-row"><span class="tt-lbl">Put OI</span><span style="color:#ff6b6b">${{fmtK(s.put_oi)}}</span></div>
            <div class="tt-row"><span class="tt-lbl">PCR</span><span>${{s.pcr.toFixed(2)}}</span></div>`;
    }}
    tt.innerHTML=`<div class="tt-strike">Strike: ${{fmtL(s.strike,0)}}</div>${{rows}}`;
    tt.style.display='block';
    const left=Math.min(e.clientX-rect.left+12, rect.width-180);
    tt.style.left=left+'px';tt.style.top=(e.clientY-rect.top-10)+'px';
  }});
  canvas.addEventListener('mouseleave',()=>{{if(canvas._tooltip)canvas._tooltip.style.display='none';}});
}}

// ── SIGNAL CARD ──────────────────────────────────────────────────────────────
function buildSignalCard(sym){{
  const d=SYM_DATA[sym];
  const chg=d.change_pct,chgCls=chg>=0?'up':'dn',chgArr=chg>=0?'▲':'▼';
  const ltpCol=chg>=0?'var(--buy)':'var(--sell)';
  const indRows=d.indicators.map((ind,ii)=>{{
    const ic=sc(ind.score);
    return `<div class="ind-row" style="animation-delay:${{0.05*ii+0.4}}s">
      <div class="ind-num" style="background:${{ic}}22;color:${{ic}};border:1px solid ${{ic}}33">${{ii+1}}</div>
      <div class="ind-body">
        <div class="ind-name">${{ind.name}}</div>
        <div class="ind-label">${{ind.label}}</div>
        <div class="ind-detail">${{ind.detail}}</div>
      </div>
      <div class="ind-pip" style="background:${{ic}};box-shadow:0 0 5px ${{ic}}"></div>
    </div>`;
  }}).join('');

  const div=document.createElement('div');
  div.className='card';
  div.style.cssText=`--sc:${{d.signal_color}};--sg:${{sigGlow(d.signal)}}`;
  div.innerHTML=`
    <div class="card-head">
      <div class="sym-row">
        <div class="sym-name">${{sym}}</div>
        <div class="sig-badge" style="--sc:${{d.signal_color}};--sg:${{sigGlow(d.signal)}}">${{sigIcon(d.signal)}} ${{d.signal}}</div>
      </div>
      <div class="price-row">
        <div class="ltp" style="color:${{ltpCol}}">${{fmtL(d.ltp,2)}}</div>
        <div class="chg ${{chgCls}}">${{chgArr}} ${{Math.abs(chg).toFixed(2)}}%</div>
      </div>
      <div class="ohlc">
        <span><span class="ol">OPEN</span><span class="ov">${{fmtL(d.open,2)}}</span></span>
        <span><span class="ol">HIGH</span><span class="ov" style="color:var(--buy)">${{fmtL(d.high,2)}}</span></span>
        <span><span class="ol">LOW</span><span class="ov" style="color:var(--sell)">${{fmtL(d.low,2)}}</span></span>
        <span><span class="ol">SCORE</span><span class="ov" style="color:${{d.signal_color}}">${{d.score>0?'+':''}}${{d.score}}/${{d.factors}}</span></span>
      </div>
    </div>
    <div class="spark-wrap"><canvas class="spark" id="spark-${{sym}}"></canvas></div>
    <div class="gauge-sec">
      <div class="gauge-wrap">
        <svg class="gauge-svg" id="gauge-${{sym}}" viewBox="0 0 130 70"></svg>
        <div class="gauge-score">
          <div class="gauge-num" style="color:${{d.signal_color}}">${{d.score>0?'+':''}}${{d.score}}</div>
          <div class="gauge-lbl">${{d.signal}} · ${{d.factors}} SIGNALS</div>
        </div>
      </div>
    </div>
    <div class="ind-list">${{indRows}}</div>`;
  return div;
}}

// ── OI CHART PANEL ───────────────────────────────────────────────────────────
function buildOIPanel(sym){{
  const d=SYM_DATA[sym]; const oi=d.oi_chain;
  const panel=document.createElement('div');
  panel.className='oi-panel';

  if(!oi||!oi.strikes||!oi.strikes.length){{
    panel.innerHTML=`<div class="oi-head"><div class="oi-title">Option Chain — ${{sym}}</div></div>
      <div style="padding:60px 22px;text-align:center;font-family:var(--mono);font-size:12px;color:var(--tx3)">
        Option chain data unavailable<br>
        <span style="font-size:10px;margin-top:6px;display:block">(BSE options may be limited outside market hours)</span>
      </div>`;
    return panel;
  }}

  const totalCL=fmtK(oi.total_call_oi), totalPL=fmtK(oi.total_put_oi);
  const pcr=oi.total_pcr.toFixed(2), mp=fmtL(oi.max_pain,0);
  const pcrCol=oi.total_pcr>1.2?'var(--buy)':oi.total_pcr<0.8?'var(--sell)':'var(--neu)';

  panel.innerHTML=`
    <div class="oi-head">
      <div>
        <div class="oi-title">Option Chain OI — ${{sym}}</div>
        <div style="font-family:var(--mono);font-size:10px;color:var(--tx3);margin-top:3px">Expiry: ${{oi.expiry}} · Spot: ${{fmtL(oi.spot,2)}} · Range ±1000 pts</div>
      </div>
      <div class="oi-meta">
        <span><span class="ml">Total Calls</span><span class="mv" style="color:${{CALL_COL}}">${{totalCL}}</span></span>
        <span><span class="ml">Total Puts</span><span class="mv" style="color:${{PUT_COL}}">${{totalPL}}</span></span>
        <span><span class="ml">PCR</span><span class="mv" style="color:${{pcrCol}}">${{pcr}}</span></span>
        <span><span class="ml">Max Pain</span><span class="mv" style="color:#a78bfa">${{mp}}</span></span>
      </div>
    </div>
    <div class="oi-tabs">
      <button class="tab-btn active" data-tab="oi">OI</button>
      <button class="tab-btn" data-tab="doi">Change OI</button>
      <button class="tab-btn" data-tab="pcr">PCR</button>
      <button class="tab-btn" data-tab="maxpain">Max Pain</button>
    </div>
    <div class="oi-chart-wrap" style="position:relative">
      <div class="oi-stats">
        <div class="oi-stat"><div class="oi-stat-dot" style="background:${{CALL_COL}}"></div><span style="font-family:var(--mono);font-size:11px;color:var(--tx2)">Call OI</span></div>
        <div class="oi-stat"><div class="oi-stat-dot" style="background:${{PUT_COL}}"></div><span style="font-family:var(--mono);font-size:11px;color:var(--tx2)">Put OI</span></div>
        <div class="oi-stat" style="margin-left:auto">
          <span style="font-family:var(--mono);font-size:10px;color:var(--tx3)">Viewing: ${{new Date().toLocaleDateString('en-IN')}}</span>
        </div>
      </div>
      <canvas class="oi-chart-canvas" id="oi-${{sym}}"></canvas>
      <div class="oi-tooltip" id="tt-${{sym}}"></div>
    </div>`;

  // Tab switching
  let activeTab='oi';
  panel.querySelectorAll('.tab-btn').forEach(btn=>{{
    btn.addEventListener('click',()=>{{
      panel.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
      btn.classList.add('active');
      activeTab=btn.dataset.tab;
      // Update legend
      const statDots=panel.querySelectorAll('.oi-stat-dot');
      const statLabels=panel.querySelectorAll('.oi-stat span');
      if(activeTab==='doi'){{
        statDots[0].style.background=CALL_DOI_COL;statLabels[0].textContent='Call Δ OI';
        statDots[1].style.background=PUT_DOI_COL;statLabels[1].textContent='Put Δ OI';
      }}else if(activeTab==='pcr'){{
        statDots[0].style.background='#ffb020';statLabels[0].textContent='PCR (bull>1)';
        statDots[1].style.background='transparent';statLabels[1].textContent='';
      }}else{{
        statDots[0].style.background=CALL_COL;statLabels[0].textContent='Call OI';
        statDots[1].style.background=PUT_COL;statLabels[1].textContent='Put OI';
      }}
      const canvas=document.getElementById('oi-'+sym);
      if(canvas)renderOIChart(canvas,document.getElementById('tt-'+sym),oi.strikes,oi.spot,oi.max_pain,activeTab);
    }});
  }});

  return panel;
}}

// ── MAIN BUILD ───────────────────────────────────────────────────────────────
function buildAll(){{
  const container=document.getElementById('main-content');
  ['NIFTY','SENSEX','BANKNIFTY'].forEach((sym,si)=>{{
    const section=document.createElement('div');
    section.className='sym-section';
    const divider=document.createElement('div');
    divider.className='sym-divider';
    divider.textContent=sym+' ANALYSIS';
    section.appendChild(divider);
    const grid=document.createElement('div');
    grid.className='sym-grid';
    grid.appendChild(buildSignalCard(sym));
    grid.appendChild(buildOIPanel(sym));
    section.appendChild(grid);
    container.appendChild(section);
  }});

  // Render charts after DOM is ready
  requestAnimationFrame(()=>{{
    ['NIFTY','SENSEX','BANKNIFTY'].forEach(sym=>{{
      const d=SYM_DATA[sym];
      const spark=document.getElementById('spark-'+sym);
      if(spark)drawSpark(spark,d.candles,d.signal_color);
      const gauge=document.getElementById('gauge-'+sym);
      if(gauge)drawGauge(gauge,d.score,d.factors,d.signal_color);
      const oiCanvas=document.getElementById('oi-'+sym);
      const tt=document.getElementById('tt-'+sym);
      if(oiCanvas&&d.oi_chain&&d.oi_chain.strikes){{
        renderOIChart(oiCanvas,tt,d.oi_chain.strikes,d.oi_chain.spot,d.oi_chain.max_pain,'oi');
        attachOIHover(oiCanvas);
      }}
    }});
  }});
}}

document.addEventListener('DOMContentLoaded',()=>{{buildTicker();buildAll();}});
window.addEventListener('resize',()=>{{
  ['NIFTY','SENSEX','BANKNIFTY'].forEach(sym=>{{
    const d=SYM_DATA[sym];
    const spark=document.getElementById('spark-'+sym);
    if(spark)drawSpark(spark,d.candles,d.signal_color);
    const oiCanvas=document.getElementById('oi-'+sym);
    const tt=document.getElementById('tt-'+sym);
    if(oiCanvas&&d.oi_chain&&d.oi_chain.strikes){{
      renderOIChart(oiCanvas,tt,d.oi_chain.strikes,d.oi_chain.spot,d.oi_chain.max_pain,oiCanvas._tab||'oi');
    }}
  }});
}});

const CALL_COL='#00e5b0',PUT_COL='#ff6b6b',CALL_DOI_COL='#6366f1',PUT_DOI_COL='#f97316';
</script>
</body>
</html>"""

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    ts = datetime.datetime.now().strftime("%d %b %Y, %H:%M")
    print("="*62)
    print("  AlphaEdge Market Intelligence Engine  v3")
    print(f"  {ts} IST")
    print("="*62)

    print("\n[1/4] Global market data...")
    gdata={}
    vq=fetch_quote(INSTRUMENTS["INDIA_VIX"])
    if vq: gdata["VIX"]=vq; print(f"  ✓ VIX {vq['ltp']:.2f}")
    else: print("  ✗ VIX unavailable")
    for key,ytick in YAHOO_SYM.items():
        d=fetch_yahoo(ytick,days=5,interval="1h")
        if d: gdata[key]=d; print(f"  ✓ {key:<15} {d['ltp']:.3f} ({d['change_pct']:+.2f}%)")
        else: print(f"  ✗ {key} unavailable")

    print("\n[2/4] Index quotes...")
    quotes={}
    for sym,key in {k:v for k,v in INSTRUMENTS.items() if k!="INDIA_VIX"}.items():
        q=fetch_quote(key); quotes[sym]=q or {}
        if q: print(f"  ✓ {sym:<12} {q['ltp']:>12,.2f} ({q['change_pct']:+.2f}%)")
        else: print(f"  ✗ {sym} unavailable")

    print("\n[3/4] Candles + Option Chain OI...")
    uc,yc,oi_map={},{},{}
    for sym,key in {k:v for k,v in INSTRUMENTS.items() if k!="INDIA_VIX"}.items():
        c=fetch_candles(key,days=90); uc[sym]=c
        print(f"  Upstox {sym:<12} {len(c)} bars")
    for sym,ytick in YAHOO_IDX.items():
        d=fetch_yahoo(ytick,days=90,interval="1d")
        if d and "candles" in d:
            yc[sym]=d["candles"]
            print(f"  Yahoo  {sym:<12} {len(d['candles'])} bars")
            if not quotes.get(sym,{}).get("ltp"): quotes[sym]=d
        else: yc[sym]=[]

    # Option chain for all 3 symbols
    for sym in ["NIFTY","SENSEX","BANKNIFTY"]:
        spot=quotes.get(sym,{}).get("ltp",0)
        if spot:
            print(f"  OI chain {sym} (spot={spot:,.0f}, range ±{OI_RANGE})...")
            oi=build_oi_data(sym,spot)
            if oi:
                oi_map[sym]=oi
                print(f"    ✓ {len(oi['strikes'])} strikes | PCR={oi['total_pcr']:.2f} | MaxPain={oi['max_pain']:,.0f}")
            else:
                print(f"    ✗ Chain unavailable")
        else:
            print(f"  OI chain {sym}: no spot price, skipping")

    print("\n[4/4] Computing 10-factor signals...")
    analyses={}
    EMOJ={"BUY":"🟢","SELL":"🔴","NEUTRAL":"🟡"}
    for sym in ["NIFTY","SENSEX","BANKNIFTY"]:
        a=analyze(sym,quotes.get(sym,{}),uc.get(sym,[]),
                  oi_map.get(sym),gdata,yc.get(sym,[]))
        analyses[sym]=a
        print(f"  {EMOJ[a['signal']]} {sym:<12} {a['signal']:<8} Score:{a['score']:+d}/{a['factors']}")

    html=gen_html(analyses,quotes,gdata,oi_map,ts)
    fname=f"alphaedge_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(fname,"w",encoding="utf-8") as f: f.write(html)

    print(f"\n{'='*62}")
    for sym,a in analyses.items(): print(f"  {sym:<12} ── {a['signal']}")
    print(f"{'='*62}")
    print(f"\n  ✅  {fname}")
    try: webbrowser.open(f"file://{os.path.abspath(fname)}")
    except: pass

if __name__=="__main__":
    main()
