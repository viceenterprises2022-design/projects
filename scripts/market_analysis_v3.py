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
import requests, datetime, os, webbrowser, time, json, sqlite3, threading, sys
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
YAHOO_SYM = {"DXY":"DX-Y.NYB","VIX":"^VIX"}
YAHOO_IDX = {"NIFTY":"^NSEI","SENSEX":"^BSESN","BANKNIFTY":"^NSEBANK"}
YH = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


# ── INTRADAY OI COLLECTOR ────────────────────────────────────────────────────

DB_PATH = "intraday_oi.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS trending_oi 
                 (timestamp TEXT, symbol TEXT, ltp REAL, call_oi REAL, put_oi REAL)''')
    # Clean previous day's data
    c.execute("DELETE FROM trending_oi WHERE date(timestamp) < date('now', 'localtime')")
    conn.commit()
    conn.close()

def oi_collector_thread():
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:00")
            
            # Prevent duplicate for same minute
            c.execute("SELECT 1 FROM trending_oi WHERE timestamp=? AND symbol='NIFTY' LIMIT 1", (ts,))
            if c.fetchone():
                conn.close()
                time.sleep(10)
                continue

            for sym in ["NIFTY", "BANKNIFTY", "SENSEX"]:
                key = INSTRUMENTS.get(sym)
                oi_key = OI_INSTRUMENTS.get(sym)
                if not key or not oi_key: continue
                
                q = fetch_quote(key)
                if not q: continue
                ltp = q.get("ltp", 0)
                oi_raw = build_oi_data(sym, ltp)
                if not oi_raw: continue
                
                c_oi = oi_raw.get("total_call_oi", 0)
                p_oi = oi_raw.get("total_put_oi", 0)
                
                c.execute("INSERT INTO trending_oi VALUES (?, ?, ?, ?, ?)", (ts, sym, ltp, c_oi, p_oi))
                
            conn.commit()
            conn.close()
        except Exception:
            pass
            
        time.sleep(60) # 1 minute

# ─────────────────────────────────────────────────────────────────────────────

# ── Upstox Fetchers ───────────────────────────────────────────────────────────

def upstox_get(url, params):
    try:
        r = requests.get(url, headers=UH, params=params, timeout=12)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
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
        return None

    nearest = expiries[0]
    chain = fetch_option_chain(key, nearest)
    if not chain:
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
    except Exception:
        pass
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

    # 4 OPEN INTEREST (total OI skew)
    if oi_raw:
        total_c = oi_raw["total_call_oi"]; total_p = oi_raw["total_put_oi"]
        oi_ratio = total_c / max(total_p, 1)
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
        res["oi"]={"label":"N/A","score":0,"detail":"Market closed"}

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

    # 10 PCR
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
        res["pcr"]={"label":"N/A","score":0,"detail":"Option chain req."}

    sg,sgc=sig_color(sc,fa)
    total_score = min(abs(sc), 10)
    return {"indicators":res,"score":total_score,"factors":fa,"signal":sg,"signal_color":sgc}

# ── CLI INTERFACE ─────────────────────────────────────────────────────────────

from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.rule import Rule
from rich import box

console = Console()

def fmt_oi(v):
    if not v: return "—"
    l = v / 100000
    if l >= 100: return f"{l:,.0f}L"
    return f"{l:.1f}L"

def days_to_expiry(expiry_str):
    try:
        exp = datetime.datetime.strptime(expiry_str, "%Y-%m-%d").date()
        return (exp - datetime.date.today()).days
    except Exception: return "?"

def get_option_chain_table(oi_raw, spot):
    if not oi_raw: return Text("Option chain unavailable", style="dim")
    expiry  = oi_raw.get("expiry", "?")
    dte     = days_to_expiry(expiry)
    strikes = oi_raw.get("strikes", [])
    max_p   = oi_raw.get("max_pain", 0)
    lo, hi  = spot - 500, spot + 500
    visible = [s for s in strikes if lo <= s["strike"] <= hi] or strikes
    
    oc_table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold", padding=(0, 0))
    oc_table.add_column("C.LTP", justify="right", style="green", width=7)
    oc_table.add_column("C.OI", justify="right", style="green", width=7)
    oc_table.add_column("STRIKE", justify="center", style="bold white", width=14)
    oc_table.add_column("P.OI", justify="right", style="red", width=7)
    oc_table.add_column("P.LTP", justify="right", style="red", width=7)
    for s in visible:
        k=s["strike"]; is_atm = abs(k-spot)<=50
        c_ltp=f"{s['call_ltp']:.1f}" if s['call_ltp'] else "—"
        c_oi=fmt_oi(s['call_oi'])
        p_ltp=f"{s['put_ltp']:.1f}" if s['put_ltp'] else "—"
        p_oi=fmt_oi(s['put_oi'])
        strike_str = f"[bold yellow]►{k:,.1f}◄[/bold yellow]" if is_atm else f"{k:,.1f}"
        if k == max_p: strike_str += " [magenta]MP[/magenta]"
        oc_table.add_row(c_ltp, c_oi, strike_str, p_oi, p_ltp)
    
    header_text = Text(f"Option Chain — Exp: {expiry}\nDTE: {dte}d | MP: {max_p:,.1f}", style="bold yellow", justify="center")
    return Panel(Group(header_text, oc_table), border_style="yellow", padding=(0, 1))

def get_intelligence_panel(sym, quote, oi_raw):
    if not oi_raw: return Text("")
    strikes=oi_raw.get("strikes", []); spot=oi_raw.get("spot", 0)
    total_pcr=oi_raw.get("total_pcr", 0); max_pain=oi_raw.get("max_pain", 0)
    total_c_oi=oi_raw.get("total_call_oi", 0); total_p_oi=oi_raw.get("total_put_oi", 0)
    price_chg=quote.get("change_pct", 0)
    total_oi_chg=sum(s.get("call_doi", 0) + s.get("put_doi", 0) for s in strikes)
    top_call=sorted(strikes, key=lambda x: x["call_oi"], reverse=True)[:3]
    top_put=sorted(strikes, key=lambda x: x["put_oi"], reverse=True)[:3]
    pcr_color = "green" if total_pcr>=1.0 else "yellow" if total_pcr>=0.7 else "red"
    buildup_sig = "[green]Long[/green]" if price_chg>0 and total_oi_chg>0 else "[cyan]Cov[/cyan]" if price_chg>0 and total_oi_chg<0 else "[red]Short[/red]" if price_chg<0 and total_oi_chg>0 else "[yellow]Unwnd[/yellow]" if price_chg<0 and total_oi_chg<0 else "[dim]Neut[/dim]"
    
    intel = Table(box=None, show_header=False, padding=(0, 1), expand=True)
    intel.add_column("L", justify="left")
    intel.add_column("V", justify="right")
    intel.add_row("PCR", f"[{pcr_color}]{total_pcr:.2f}[/{pcr_color}]")
    intel.add_row("Max Pain", f"[magenta]{max_pain:,}[/magenta]")
    intel.add_row("OI Build", buildup_sig)
    intel.add_row("C.OI", f"[green]{fmt_oi(total_c_oi)}[/green]")
    intel.add_row("P.OI", f"[red]{fmt_oi(total_p_oi)}[/red]")
    intel.add_row("R", f"[red]{top_call[0]['strike']:,}[/red]")
    intel.add_row("S", f"[green]{top_put[0]['strike']:,}[/green]")
    return Panel(intel, title=Text("Intel", style="bold magenta"), border_style="magenta", padding=(0, 1))

def print_summary_ticker(quotes_all):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    console.print(Rule(f"[bold cyan]Live Market Snapshot ({now})[/bold cyan]", style="cyan"))
    parts = []
    for s, q in quotes_all.items():
        if not q: continue
        ltp, chg = q["ltp"], q["change_pct"]
        color = "green" if chg>=0 else "red"
        parts.append(f"[bold white]{s}[/bold white] [{color}]{ltp:,.2f} ({chg:+.2f}%)[/{color}]")
    console.print("  " + "   │   ".join(parts) + "\n")

def print_trending_oi(sym):
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT timestamp, ltp, call_oi, put_oi FROM trending_oi WHERE symbol=? ORDER BY timestamp DESC LIMIT 15", (sym,)).fetchall()
        conn.close()
    except Exception: return
    if not rows: return
    console.print(Rule("[bold cyan]Trending OI (Intraday)[/bold cyan]", style="cyan"))
    t = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold dim", padding=(0, 1))
    t.add_column("Time", justify="center")
    t.add_column("LTP", justify="right")
    t.add_column("ΔCall OI", justify="right")
    t.add_column("ΔPut OI", justify="right")
    t.add_column("Diff", justify="right")
    t.add_column("PCR", justify="right")
    t.add_column("Sentiment", justify="center")
    
    base_c, base_p = rows[-1][2], rows[-1][3]
    for r in rows:
        ts, ltp, c_oi, p_oi = r
        d_c, d_p = c_oi-base_c, p_oi-base_p; diff = p_oi-c_oi
        pcr = p_oi/c_oi if c_oi>0 else 0
        sent = "[green]Bullish[/green]" if diff>0 else "[red]Bearish[/red]"
        t.add_row(
            ts.split(" ")[1][:5], 
            f"{ltp:,.2f}", 
            f"{d_c:,.0f}", 
            f"{d_p:,.0f}", 
            f"{diff:,.0f}", 
            f"{pcr:.2f}", 
            sent
        )
    console.print(t)

def get_futures_key(sym, next_month=False):
    now = datetime.datetime.now()
    if next_month:
        m = now.month + 1
        y = now.year
        if m > 12: m = 1; y += 1
        now = datetime.datetime(y, m, 1)
    year, mon = now.strftime("%y"), now.strftime("%b").upper()
    if sym == "SENSEX": return f"BSE_FO|SENSEX{year}{mon}FUT"
    return f"NSE_FO|{sym}{year}{mon}FUT"

def run_analysis(sym):
    q = fetch_quote(INSTRUMENTS[sym])
    if not q: return None
    fq = fetch_quote(get_futures_key(sym))
    if not fq: fq = fetch_quote(get_futures_key(sym, True))
    
    c = fetch_candles(INSTRUMENTS[sym])
    yc = fetch_yahoo(YAHOO_IDX.get(sym, "^NSEI"))
    gd = {"DXY":fetch_yahoo(YAHOO_SYM["DXY"], 5), 
          "VIX":fetch_yahoo(YAHOO_SYM["VIX"], 5),
          "US30":fetch_yahoo("^DJI", 5)}
    vix = fetch_quote(INSTRUMENTS["INDIA_VIX"])
    if vix: gd["VIX"] = {"ltp":vix.get("ltp",15), "change_pct":0}
    oi = build_oi_data(sym, q["ltp"])
    return (sym, q, fq, oi, analyze(sym, q, c, oi, gd, yc))

def display_dashboard(sym, q, fq, oi, a_res):
    console.clear()
    ltp, chg = q["ltp"], q["change_pct"]
    color = "green" if chg>=0 else "red"
    sig_c = {"BUY":"green", "SELL":"red", "NEUTRAL":"yellow"}.get(a_res["signal"], "white")
    
    header = f"[bold white]{sym}[/bold white] | Spot: [{color}]{ltp:,.2f} ({chg:+.2f}%)[/{color}]"
    if fq:
        fltp, fchg = fq["ltp"], fq["change_pct"]
        fcolor = "green" if fchg>=0 else "red"
        header += f" | Fut: [{fcolor}]{fltp:,.2f} ({fchg:+.2f}%)[/{fcolor}]"
    
    header += f" | Signal: [{sig_c}]{a_res['signal']} ({a_res['score']}/10)[/{sig_c}]"
    console.print(Panel(header, border_style="cyan"))
    
    # 1. Indicator Table (Condensed)
    ind_table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold dim", padding=(0,0), expand=True)
    ind_table.add_column("Ind", style="cyan", justify="left"); ind_table.add_column("Status", justify="left"); ind_table.add_column("S", justify="center")
    for k, v in a_res["indicators"].items():
        score_val = v["score"]
        score_str = f"[green]+{score_val}[/green]" if score_val>0 else f"[red]{score_val}[/red]" if score_val<0 else "[yellow]0[/yellow]"
        short_k = k.upper().replace("INDIA_VIX", "VIX").replace("SUPERTREND", "S-TREND").replace("DOW_JONES", "DOW")
        ind_table.add_row(short_k, v["label"][:32], score_str)
    
    # 2. Layout Structure (Grid Table for compact height)
    if oi:
        grid = Table.grid(expand=True)
        grid.add_column(ratio=4) # Indicators
        grid.add_column(ratio=6) # OC
        grid.add_column(ratio=3) # Intel
        grid.add_row(
            Panel(ind_table, title=Text("Indicators", style="bold cyan"), border_style="cyan", padding=(0,0)),
            get_option_chain_table(oi, ltp),
            get_intelligence_panel(sym, q, oi)
        )
        console.print(grid)
        print_trending_oi(sym)
    else:
        console.print(Panel(ind_table, title=Text("Indicators", style="bold cyan"), border_style="cyan"))

    console.print(f"[dim]  Refresh 30s | {datetime.datetime.now().strftime('%H:%M:%S')} | Ctrl+C Exit[/dim]")


def main():
    init_db()
    threading.Thread(target=oi_collector_thread, daemon=True).start()
    while True:
        console.clear()
        console.print(Panel("[bold yellow]⚡ ALPHAEDGE MARKET DIAGNOSTICS[/bold yellow]", border_style="cyan"))
        quotes = {s: fetch_quote(INSTRUMENTS[s]) for s in ["NIFTY", "BANKNIFTY", "SENSEX"]}
        print_summary_ticker(quotes)
        console.print("  [1] NIFTY 50\n  [2] BANKNIFTY\n  [3] SENSEX\n  [q] Quit\n")
        choice = input("  Select: ").strip().lower()
        if choice == 'q': sys.exit(0)
        sym = {"1":"NIFTY", "2":"BANKNIFTY", "3":"SENSEX"}.get(choice)
        if not sym: continue
        while True:
            try:
                res = run_analysis(sym)
                if res: display_dashboard(*res)
                for _ in range(30): time.sleep(1) # Simple sleep loop
            except KeyboardInterrupt: break

if __name__ == "__main__": main()
