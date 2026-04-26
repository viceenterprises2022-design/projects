#!/usr/bin/env python3
"""
AlphaEdge Market Intelligence Dashboard v2
PixiJS-powered ultra-modern UI with particle canvas, animated gauges,
sparklines, and glassmorphism design.

Usage:  python market_analysis_v2.py
Output: alphaedge_<timestamp>.html  (auto-opens in browser)
"""

import requests, datetime, os, webbrowser, time, json

UPSTOX_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJGVzY0MDYiLCJqdGkiOiI2OWVjZDE1NTU0ZTdlMzBhNmY0NTZkODYiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaXNFeHRlbmRlZCI6dHJ1ZSwiaWF0IjoxNzc3MTI3NzY1LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE4MDg2OTA0MDB9.lxl6fYYoKH1_2AItX-XN40eNsYhbAzbjnwbvyopgSUo"
UPSTOX_HEADERS = {"Authorization": f"Bearer {UPSTOX_TOKEN}", "Accept": "application/json"}
UPSTOX_INSTRUMENTS = {
    "NIFTY": "NSE_INDEX|Nifty 50", "SENSEX": "BSE_INDEX|SENSEX",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank", "INDIA_VIX": "NSE_INDEX|India VIX"
}
YAHOO_SYMBOLS = {"DXY":"DX-Y.NYB","CRUDE_OIL":"CL=F","US30":"YM=F","GOLD":"GC=F","SILVER":"SI=F"}
YAHOO_INDEX = {"NIFTY":"^NSEI","SENSEX":"^BSESN","BANKNIFTY":"^NSEBANK"}
YAHOO_HEADERS = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def fetch_upstox_quote(k):
    try:
        r = requests.get("https://api.upstox.com/v2/market-quote/quotes",
                         headers=UPSTOX_HEADERS, params={"instrument_key":k}, timeout=10)
        d = r.json()
        if d.get("status")=="success" and d.get("data"):
            key=list(d["data"].keys())[0]; q=d["data"][key]; ohlc=q.get("ohlc",{})
            prev=ohlc.get("close",0) or 1; ltp=q.get("last_price",0); chg=ltp-prev
            return {"ltp":ltp,"open":ohlc.get("open",0),"high":ohlc.get("high",0),
                    "low":ohlc.get("low",0),"close":prev,"volume":q.get("volume",0),
                    "change":chg,"change_pct":chg/prev*100}
    except Exception as e: print(f"    [W] {k[:20]}: {e}")
    return None

def fetch_upstox_candles(k, days=90):
    today=datetime.date.today()
    f=(today-datetime.timedelta(days=days)).strftime("%Y-%m-%d"); t=today.strftime("%Y-%m-%d")
    try:
        r=requests.get(f"https://api.upstox.com/v2/historical-candle/{k}/day/{t}/{f}",
                       headers=UPSTOX_HEADERS,timeout=15)
        d=r.json()
        if d.get("status")=="success":
            raw=d.get("data",{}).get("candles",[])
            return [[c[0],float(c[1]),float(c[2]),float(c[3]),float(c[4]),
                     float(c[5]) if len(c)>5 else 0] for c in raw]
    except Exception as e: print(f"    [W] candles {k[:20]}: {e}")
    return []

def fetch_upstox_oi(symbol):
    key_map={"NIFTY":"NSE_INDEX|Nifty 50","BANKNIFTY":"NSE_INDEX|Nifty Bank"}
    k=key_map.get(symbol)
    if not k: return None
    try:
        r=requests.get("https://api.upstox.com/v2/option/contract",
                       headers=UPSTOX_HEADERS,params={"instrument_key":k},timeout=10)
        d=r.json()
        if d.get("status")=="success" and d.get("data"):
            raw=d["data"]
            nearest=(sorted(raw)[0] if isinstance(raw[0],str)
                     else sorted(raw,key=lambda x:str(x.get("expiry",x)))[0].get("expiry",""))
            r2=requests.get("https://api.upstox.com/v2/option/chain",headers=UPSTOX_HEADERS,
                            params={"instrument_key":k,"expiry_date":nearest},timeout=15)
            oc=r2.json()
            if oc.get("status")=="success" and oc.get("data"):
                chain=oc["data"]
                coi=sum((d.get("call_options")or{}).get("market_data",{}).get("oi",0)
                        for d in chain if isinstance(d,dict))
                poi=sum((d.get("put_options")or{}).get("market_data",{}).get("oi",0)
                        for d in chain if isinstance(d,dict))
                return {"call_oi":coi,"put_oi":poi,"pcr":poi/max(coi,1),"expiry":nearest}
    except Exception as e: print(f"    [W] OI {symbol}: {e}")
    return None

def fetch_yahoo(symbol,days=60,interval="1d"):
    end=int(time.time()); start=end-days*86400
    try:
        r=requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                       params={"period1":start,"period2":end,"interval":interval},
                       headers=YAHOO_HEADERS,timeout=12)
        res=(r.json().get("chart",{}).get("result") or [None])[0]
        if not res: return None
        q=res["indicators"]["quote"][0]; ts=res.get("timestamp",[])
        valid=[(t,o,h,l,c,v) for t,o,h,l,c,v in zip(ts,q.get("open",[]),q.get("high",[]),
               q.get("low",[]),q.get("close",[]),q.get("volume",[]))
               if c is not None and o is not None]
        if not valid: return None
        last=valid[-1]; prev=valid[-2][4] if len(valid)>1 else last[4]
        chg=last[4]-prev
        return {"ltp":last[4],"open":last[1],"high":last[2],"low":last[3],"close":prev,
                "volume":last[5] or 0,"change":chg,"change_pct":chg/prev*100 if prev else 0,
                "candles":[[t,o,h,l,c,v or 0] for t,o,h,l,c,v in valid]}
    except Exception as e: print(f"    [W] Yahoo {symbol}: {e}")
    return None

def ema(v,n):
    if len(v)<n: return []
    out=[sum(v[:n])/n]; k=2/(n+1)
    for x in v[n:]: out.append(x*k+out[-1]*(1-k))
    return out

def rsi_val(closes,n=14):
    if len(closes)<n+2: return 50.0
    g=[max(closes[i]-closes[i-1],0) for i in range(1,len(closes))]
    l=[max(closes[i-1]-closes[i],0) for i in range(1,len(closes))]
    ag=sum(g[-n:])/n; al=sum(l[-n:])/n
    return 100.0 if al==0 else 100-100/(1+ag/al)

def atr_val(c,n=14):
    trs=[max(c[i][2]-c[i][3],abs(c[i][2]-c[i-1][4]),abs(c[i][3]-c[i-1][4]))
         for i in range(1,len(c))]
    return sum(trs[-n:])/min(n,len(trs)) if trs else 0

def supertrend(c,n=10,m=3):
    if len(c)<n+2: return None,0
    a=atr_val(c,n)
    if a==0: return None,0
    hl2=(c[-1][2]+c[-1][3])/2; lo=hl2-m*a; hi=hl2+m*a
    d=1 if c[-1][4]>lo else -1
    return (lo if d==1 else hi),d

def vwap_val(c,bars=20):
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

def signal(sc,fa):
    r=sc/max(fa,1)
    if r>=0.35: return "BUY","#00e5b0"
    if r<=-0.35: return "SELL","#ff3d5a"
    return "NEUTRAL","#ffb020"

def analyze(sym,quote,uc,oi,gd,yc):
    res={}; sc=fa=0
    c=uc if len(uc)>=10 else yc
    ltp=(quote or {}).get("ltp",0)

    # 1 TREND
    if len(c)>=20:
        lb,s,dt=trend_analysis(c); res["trend"]={"label":lb,"score":s,"detail":dt}
        sc+=s; fa+=2
    else: res["trend"]={"label":"N/A","score":0,"detail":f"{len(c)} bars"}

    # 2 DOW
    u=gd.get("US30")
    if u:
        ch=u["change_pct"]; s=1 if ch>0.3 else(-1 if ch<-0.3 else 0)
        res["dow_jones"]={"label":f"{'BULLISH' if s>0 else 'BEARISH' if s<0 else 'FLAT'} ({ch:+.2f}%)",
                          "score":s,"detail":f"DJIA Fut: {u['ltp']:,.0f}"}
        sc+=s; fa+=1
    else: res["dow_jones"]={"label":"N/A","score":0,"detail":"Unavailable"}

    # 3 VIX
    v=gd.get("VIX")
    if v:
        vv=v["ltp"]
        if vv<13: s,lb=1,f"LOW ({vv:.2f}) — Calm"
        elif vv<=17: s,lb=1,f"NORMAL ({vv:.2f}) — Stable"
        elif vv<=21: s,lb=0,f"ELEVATED ({vv:.2f}) — Caution"
        else: s,lb=-1,f"HIGH ({vv:.2f}) — Fear"
        res["india_vix"]={"label":lb,"score":s,"detail":f"Chg: {v.get('change_pct',0):+.2f}%"}
        sc+=s; fa+=1
    else: res["india_vix"]={"label":"N/A","score":0,"detail":"Unavailable"}

    # 4 OI
    if oi:
        pcr=oi["pcr"]
        if pcr>1.3: s,lb=1,f"BULLISH — PCR {pcr:.2f}"
        elif pcr>1.1: s,lb=1,f"MILDLY BULLISH — PCR {pcr:.2f}"
        elif pcr<0.7: s,lb=-1,f"BEARISH — PCR {pcr:.2f}"
        elif pcr<0.9: s,lb=-1,f"MILDLY BEARISH — PCR {pcr:.2f}"
        else: s,lb=0,f"NEUTRAL — PCR {pcr:.2f}"
        res["oi"]={"label":lb,"score":s,
                   "detail":f"Call:{oi['call_oi']/1e5:.1f}L | Put:{oi['put_oi']/1e5:.1f}L | {oi['expiry']}"}
        sc+=s; fa+=1
    else: res["oi"]={"label":"N/A","score":0,"detail":"Market closed / index"}

    # 5 VWAP
    if c and ltp:
        vw=vwap_val(c)
        if vw:
            dp=(ltp-vw)/vw*100
            if ltp>vw*1.002: s,lb=1,f"ABOVE (+{dp:.2f}%)"
            elif ltp<vw*0.998: s,lb=-1,f"BELOW ({dp:.2f}%)"
            else: s,lb=0,f"AT VWAP ({dp:+.2f}%)"
            res["vwap"]={"label":lb,"score":s,"detail":f"VWAP:{vw:,.2f} | LTP:{ltp:,.2f}"}
            sc+=s; fa+=1
        else: res["vwap"]={"label":"N/A","score":0,"detail":"No volume"}
    else: res["vwap"]={"label":"N/A","score":0,"detail":"No candles"}

    # 6 SUPERTREND
    if len(c)>=12:
        stv,std=supertrend(c)
        if std==1: lb=f"BULLISH (Sup≈{stv:,.0f})" if stv else "BULLISH"
        elif std==-1: lb=f"BEARISH (Res≈{stv:,.0f})" if stv else "BEARISH"
        else: lb="NEUTRAL"
        res["supertrend"]={"label":lb,"score":std,"detail":"ATR(10) × 3"}
        sc+=std; fa+=1
    else: res["supertrend"]={"label":"N/A","score":0,"detail":"Need ≥12 bars"}

    # 7 RSI
    if len(c)>=16:
        rv=rsi_val([x[4] for x in c])
        if rv>=75: s,lb=-1,f"OVERBOUGHT ({rv:.1f})"
        elif rv>=60: s,lb=1,f"BULLISH ZONE ({rv:.1f})"
        elif rv<=25: s,lb=1,f"OVERSOLD ({rv:.1f})"
        elif rv<=40: s,lb=-1,f"BEARISH ZONE ({rv:.1f})"
        else: s,lb=0,f"NEUTRAL ({rv:.1f})"
        res["rsi"]={"label":lb,"score":s,"detail":"RSI(14) Daily"}
        sc+=s; fa+=1
    else: res["rsi"]={"label":"N/A","score":0,"detail":"Need ≥16 bars"}

    # 8 DXY
    dx=gd.get("DXY")
    if dx:
        ch=dx["change_pct"]
        if ch>0.5: s,lb=-1,f"SURGING ({ch:+.2f}%) — EM risk"
        elif ch>0.2: s,lb=-1,f"STRENGTHENING ({ch:+.2f}%)"
        elif ch<-0.5: s,lb=1,f"WEAKENING ({ch:+.2f}%) — EM positive"
        elif ch<-0.2: s,lb=1,f"SOFTENING ({ch:+.2f}%)"
        else: s,lb=0,f"STABLE ({ch:+.2f}%)"
        res["dxy"]={"label":lb,"score":s,"detail":f"DXY: {dx['ltp']:.3f}"}
        sc+=s; fa+=1
    else: res["dxy"]={"label":"N/A","score":0,"detail":"Unavailable"}

    # 9 CRUDE
    cr=gd.get("CRUDE_OIL")
    if cr:
        ch=cr["change_pct"]
        if ch>2.0: s,lb=-1,f"SURGING ({ch:+.2f}%) — Inflation risk"
        elif ch>0.8: s,lb=-1,f"RISING ({ch:+.2f}%)"
        elif ch<-2.0: s,lb=1,f"CRASHING ({ch:+.2f}%)"
        elif ch<-0.8: s,lb=1,f"FALLING ({ch:+.2f}%)"
        else: s,lb=0,f"STABLE ({ch:+.2f}%)"
        res["crude"]={"label":lb,"score":s,"detail":f"WTI: ${cr['ltp']:.2f}"}
        sc+=s; fa+=1
    else: res["crude"]={"label":"N/A","score":0,"detail":"Unavailable"}

    sg,sgc=signal(sc,fa)
    return {"indicators":res,"score":sc,"factors":fa,"signal":sg,"signal_color":sgc,
            "candles":c[-30:] if c else []}

# ── HTML ─────────────────────────────────────────────────────────────────────────

def gen_html(analyses, quotes, gdata, ts):
    NAMES = {
        "trend":"Trend","dow_jones":"Dow Jones","india_vix":"India VIX",
        "oi":"Open Interest","vwap":"VWAP","supertrend":"Supertrend",
        "rsi":"RSI (14)","dxy":"USD Index","crude":"Crude Oil"
    }
    ICONS = {
        "trend":"T","dow_jones":"D","india_vix":"V","oi":"OI",
        "vwap":"VW","supertrend":"ST","rsi":"RS","dxy":"$","crude":"C"
    }

    def f(v,d=2):
        try: return f"{float(v):,.{d}f}"
        except: return "—"

    def serialize_candles(clist):
        return json.dumps([[x[1],x[2],x[3],x[4]] for x in clist])

    # Build per-symbol JSON for JS
    sym_data = {}
    for sym in ["NIFTY","SENSEX","BANKNIFTY"]:
        a = analyses[sym]
        q = quotes.get(sym,{})
        inds = []
        for k,d in a["indicators"].items():
            inds.append({
                "key": k,
                "name": NAMES.get(k,k),
                "abbr": ICONS.get(k,"•"),
                "label": d.get("label","—"),
                "detail": d.get("detail",""),
                "score": d.get("score",0)
            })
        sym_data[sym] = {
            "ltp": q.get("ltp",0),
            "open": q.get("open",0),
            "high": q.get("high",0),
            "low": q.get("low",0),
            "change_pct": q.get("change_pct",0),
            "signal": a["signal"],
            "signal_color": a["signal_color"],
            "score": a["score"],
            "factors": a["factors"],
            "indicators": inds,
            "candles": [[x[1],x[2],x[3],x[4]] for x in a["candles"]]
        }

    global_data = {
        "VIX":   {"ltp": gdata.get("VIX",{}).get("ltp","—"),  "chg": gdata.get("VIX",{}).get("change_pct",0)},
        "DXY":   {"ltp": gdata.get("DXY",{}).get("ltp","—"),  "chg": gdata.get("DXY",{}).get("change_pct",0)},
        "CRUDE": {"ltp": gdata.get("CRUDE_OIL",{}).get("ltp","—"), "chg": gdata.get("CRUDE_OIL",{}).get("change_pct",0)},
        "US30":  {"ltp": gdata.get("US30",{}).get("ltp","—"), "chg": gdata.get("US30",{}).get("change_pct",0)},
        "GOLD":  {"ltp": gdata.get("GOLD",{}).get("ltp","—"), "chg": gdata.get("GOLD",{}).get("change_pct",0)},
        "SILVER":{"ltp": gdata.get("SILVER",{}).get("ltp","—"),"chg": gdata.get("SILVER",{}).get("change_pct",0)},
    }

    sym_json   = json.dumps(sym_data)
    global_json= json.dumps(global_data)
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
/* ── RESET & ROOT ── */
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{
  --bg:#03030a;
  --glass:rgba(255,255,255,0.035);
  --glass2:rgba(255,255,255,0.06);
  --border:rgba(255,255,255,0.07);
  --border2:rgba(255,255,255,0.12);
  --tx:#e8eaf6;
  --tx2:#8890b8;
  --tx3:#50547a;
  --buy:#00e5b0;
  --sell:#ff3d5a;
  --neutral:#ffb020;
  --buy-glow:rgba(0,229,176,0.15);
  --sell-glow:rgba(255,61,90,0.15);
  --neu-glow:rgba(255,176,32,0.15);
  --sans:'Clash Display',system-ui,sans-serif;
  --mono:'DM Mono',monospace;
  --r:14px;
}}
html{{scroll-behavior:smooth}}
body{{
  background:var(--bg);
  color:var(--tx);
  font-family:var(--sans);
  min-height:100vh;
  overflow-x:hidden;
}}

/* ── PIXI CANVAS ── */
#pixi-canvas{{
  position:fixed;top:0;left:0;width:100%;height:100%;
  z-index:0;pointer-events:none;opacity:0.6;
}}

/* ── LAYOUT ── */
#app{{position:relative;z-index:1}}

/* ── HEADER ── */
.header{{
  display:flex;align-items:center;justify-content:space-between;
  padding:18px 32px;
  background:rgba(3,3,10,0.85);
  backdrop-filter:blur(24px);
  border-bottom:1px solid var(--border);
  position:sticky;top:0;z-index:100;
}}
.logo{{display:flex;align-items:center;gap:14px}}
.logo-mark{{
  width:42px;height:42px;
  background:linear-gradient(135deg,#6366f1,#00e5b0);
  border-radius:12px;
  display:flex;align-items:center;justify-content:center;
  font-size:20px;font-weight:700;color:#fff;
  box-shadow:0 0 24px rgba(99,102,241,0.4);
  position:relative;overflow:hidden;
}}
.logo-mark::after{{
  content:'';position:absolute;inset:0;
  background:linear-gradient(135deg,transparent 40%,rgba(255,255,255,0.15));
}}
.logo-text{{font-size:20px;font-weight:700;letter-spacing:-0.5px}}
.logo-sub{{font-size:10px;color:var(--tx2);font-family:var(--mono);margin-top:2px;letter-spacing:0.5px}}
.header-right{{text-align:right}}
.header-ts{{font-family:var(--mono);font-size:11px;color:var(--tx2)}}
.pulse-dot{{
  display:inline-block;width:7px;height:7px;
  background:var(--buy);border-radius:50%;margin-right:6px;
  animation:pulse-anim 2s infinite;
  box-shadow:0 0 6px var(--buy);
}}
@keyframes pulse-anim{{
  0%,100%{{opacity:1;transform:scale(1)}}
  50%{{opacity:0.3;transform:scale(0.6)}}
}}

/* ── TICKER BAR ── */
.ticker-bar{{
  background:rgba(255,255,255,0.02);
  border-bottom:1px solid var(--border);
  overflow:hidden;height:44px;display:flex;align-items:center;
}}
.ticker-track{{
  display:flex;gap:0;
  animation:ticker 30s linear infinite;
  white-space:nowrap;
}}
.ticker-track:hover{{animation-play-state:paused}}
.t-item{{
  display:inline-flex;align-items:center;gap:10px;
  padding:0 28px;border-right:1px solid var(--border);
  height:44px;
}}
.t-name{{font-size:10px;color:var(--tx3);font-family:var(--mono);letter-spacing:1px;text-transform:uppercase}}
.t-val{{font-family:var(--mono);font-size:13px;font-weight:500;color:var(--tx)}}
.t-chg{{font-family:var(--mono);font-size:11px;font-weight:500}}
.up{{color:var(--buy)}}
.dn{{color:var(--sell)}}
@keyframes ticker{{from{{transform:translateX(0)}}to{{transform:translateX(-50%)}}}}

/* ── MAIN GRID ── */
.main{{
  padding:28px 24px 60px;
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:20px;
  max-width:1520px;margin:0 auto;
}}
@media(max-width:1100px){{.main{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:700px){{.main{{grid-template-columns:1fr;padding:16px 12px 40px}}}}

/* ── CARD ── */
.card{{
  background:var(--glass);
  border:1px solid var(--border);
  border-radius:20px;
  overflow:hidden;
  backdrop-filter:blur(20px);
  transition:transform 0.3s cubic-bezier(.34,1.56,.64,1),
             border-color 0.3s,box-shadow 0.3s;
  animation:cardIn 0.6s cubic-bezier(.34,1.56,.64,1) both;
}}
.card:nth-child(1){{animation-delay:0.1s}}
.card:nth-child(2){{animation-delay:0.2s}}
.card:nth-child(3){{animation-delay:0.3s}}
@keyframes cardIn{{
  from{{opacity:0;transform:translateY(40px) scale(0.95)}}
  to{{opacity:1;transform:translateY(0) scale(1)}}
}}
.card:hover{{
  transform:translateY(-4px) scale(1.01);
  border-color:var(--border2);
}}

/* ── CARD HEADER ── */
.card-head{{
  padding:22px 24px 16px;
  position:relative;
  background:var(--glass2);
  border-bottom:1px solid var(--border);
}}
.card-head::before{{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:var(--sig-color);
  box-shadow:0 0 20px var(--sig-color);
}}
.sym-row{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px}}
.sym-name{{font-size:26px;font-weight:700;letter-spacing:-1px;color:#fff}}
.sig-badge{{
  display:inline-flex;align-items:center;gap:6px;
  padding:6px 16px;border-radius:100px;
  font-size:12px;font-weight:600;letter-spacing:0.5px;
  background:var(--sig-color);color:#000;
  box-shadow:0 0 20px var(--sig-glow);
  animation:badgePop 0.5s cubic-bezier(.34,1.56,.64,1) 0.4s both;
}}
@keyframes badgePop{{
  from{{opacity:0;transform:scale(0.7)}}
  to{{opacity:1;transform:scale(1)}}
}}
.sig-icon{{font-size:10px}}
.price-row{{display:flex;align-items:baseline;gap:10px}}
.ltp{{font-family:var(--mono);font-size:28px;font-weight:500;letter-spacing:-1px}}
.change{{font-family:var(--mono);font-size:13px;font-weight:400}}
.ohlc{{
  display:flex;gap:14px;margin-top:8px;
  font-family:var(--mono);font-size:10px;color:var(--tx3);
}}
.ohlc span{{display:flex;flex-direction:column;gap:2px}}
.ohlc .ol{{font-size:8px;text-transform:uppercase;letter-spacing:0.5px}}
.ohlc .ov{{color:var(--tx2);font-size:11px}}

/* ── SPARKLINE ── */
.sparkline-wrap{{margin:0 24px 16px;height:50px;position:relative}}
canvas.spark{{width:100%;height:50px;border-radius:8px}}

/* ── GAUGE ── */
.gauge-section{{
  display:flex;flex-direction:column;align-items:center;
  padding:16px 24px;border-bottom:1px solid var(--border);
}}
.gauge-wrap{{position:relative;width:140px;height:75px;margin-bottom:8px}}
.gauge-svg{{width:140px;height:75px}}
.gauge-score{{
  position:absolute;bottom:0;left:50%;transform:translateX(-50%);
  text-align:center;
}}
.gauge-num{{font-family:var(--mono);font-size:22px;font-weight:500;line-height:1}}
.gauge-lbl{{font-size:9px;color:var(--tx3);font-family:var(--mono);letter-spacing:0.5px;margin-top:2px}}

/* ── INDICATORS ── */
.ind-list{{padding:0 0 8px}}
.ind-row{{
  display:grid;
  grid-template-columns:32px 1fr auto;
  align-items:center;
  gap:10px;
  padding:10px 24px;
  border-bottom:1px solid rgba(255,255,255,0.03);
  transition:background 0.15s;
  animation:rowIn 0.4s ease both;
}}
.ind-row:hover{{background:rgba(255,255,255,0.03)}}
.ind-row:last-child{{border-bottom:none}}
.ind-num{{
  width:28px;height:28px;border-radius:8px;
  display:flex;align-items:center;justify-content:center;
  font-size:9px;font-weight:600;font-family:var(--mono);
  letter-spacing:0;color:#000;flex-shrink:0;
}}
.ind-body{{min-width:0}}
.ind-name{{font-size:11px;font-weight:600;color:var(--tx);letter-spacing:0.2px;margin-bottom:2px}}
.ind-label{{font-size:10px;color:var(--tx2);font-family:var(--mono);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.ind-detail{{font-size:9px;color:var(--tx3);font-family:var(--mono);white-space:nowrap}}
.ind-pip{{width:6px;height:6px;border-radius:50%;flex-shrink:0}}
@keyframes rowIn{{from{{opacity:0;transform:translateX(-8px)}}to{{opacity:1;transform:translateX(0)}}}}

/* ── FOOTER ── */
.footer{{
  text-align:center;
  padding:24px;
  border-top:1px solid var(--border);
  font-family:var(--mono);font-size:10px;color:var(--tx3);
  line-height:2;
  background:rgba(255,255,255,0.01);
}}

/* ── SCROLLBAR ── */
::-webkit-scrollbar{{width:4px;height:4px}}
::-webkit-scrollbar-track{{background:transparent}}
::-webkit-scrollbar-thumb{{background:rgba(255,255,255,0.1);border-radius:4px}}
</style>
</head>
<body>

<canvas id="pixi-canvas"></canvas>

<div id="app">

<!-- HEADER -->
<header class="header">
  <div class="logo">
    <div class="logo-mark">α</div>
    <div>
      <div class="logo-text">AlphaEdge</div>
      <div class="logo-sub">FINANCIAL INTELLIGENCE · PINAKA.AI</div>
    </div>
  </div>
  <div class="header-right">
    <div class="header-ts"><span class="pulse-dot"></span>{ts} IST</div>
    <div class="header-ts" style="margin-top:3px;color:var(--tx3)">9-FACTOR SIGNAL ENGINE</div>
  </div>
</header>

<!-- TICKER -->
<div class="ticker-bar">
  <div class="ticker-track" id="ticker"></div>
</div>

<!-- MAIN -->
<main class="main" id="cards-container"></main>

<!-- FOOTER -->
<footer class="footer">
  <div>⚠ For informational purposes only &nbsp;·&nbsp; Not financial advice &nbsp;·&nbsp; Always conduct your own due diligence</div>
  <div>AlphaEdge © {yr} &nbsp;·&nbsp; Data: Upstox API + Yahoo Finance &nbsp;·&nbsp; Signals regenerate on each run</div>
</footer>

</div><!-- #app -->

<script>
// ── DATA ────────────────────────────────────────────────────────────────────────
const SYM_DATA    = {sym_json};
const GLOBAL_DATA = {global_json};

// ── PIXI PARTICLE BACKGROUND ────────────────────────────────────────────────────
(async () => {{
  try {{
    const canvas = document.getElementById('pixi-canvas');
    const app = new PIXI.Application({{
      view: canvas,
      width: window.innerWidth,
      height: window.innerHeight,
      backgroundColor: 0x03030a,
      resolution: Math.min(window.devicePixelRatio || 1, 2),
      autoDensity: true,
      antialias: true,
    }});

    const particles = [];
    const N = 80;
    const container = new PIXI.Container();
    app.stage.addChild(container);

    // Color palette
    const COLS = [0x6366f1, 0x00e5b0, 0xff3d5a, 0xffb020, 0x818cf8];

    for (let i = 0; i < N; i++) {{
      const g = new PIXI.Graphics();
      const r = Math.random() * 2 + 0.5;
      const col = COLS[Math.floor(Math.random() * COLS.length)];
      g.beginFill(col, 0.7);
      g.drawCircle(0, 0, r);
      g.endFill();
      g.x = Math.random() * app.screen.width;
      g.y = Math.random() * app.screen.height;
      const speed = Math.random() * 0.4 + 0.1;
      const angle = Math.random() * Math.PI * 2;
      particles.push({{ g, vx: Math.cos(angle)*speed, vy: Math.sin(angle)*speed,
                        r, life: Math.random(), lifeSpeed: Math.random()*0.005+0.002 }});
      container.addChild(g);
    }}

    // Connection lines container
    const linesCont = new PIXI.Graphics();
    app.stage.addChildAt(linesCont, 0);

    app.ticker.add(() => {{
      linesCont.clear();
      const W = app.screen.width, H = app.screen.height;
      for (let i = 0; i < particles.length; i++) {{
        const p = particles[i];
        p.x = (p.g.x += p.vx);
        p.y = (p.g.y += p.vy);
        p.life += p.lifeSpeed;
        p.g.alpha = (Math.sin(p.life) * 0.5 + 0.5) * 0.8 + 0.1;
        if (p.g.x < -10) p.g.x = W + 10;
        if (p.g.x > W + 10) p.g.x = -10;
        if (p.g.y < -10) p.g.y = H + 10;
        if (p.g.y > H + 10) p.g.y = -10;

        for (let j = i+1; j < particles.length; j++) {{
          const q = particles[j];
          const dx = p.g.x - q.g.x, dy = p.g.y - q.g.y;
          const dist = Math.sqrt(dx*dx + dy*dy);
          if (dist < 120) {{
            const alpha = (1 - dist/120) * 0.15;
            linesCont.lineStyle(0.5, 0x6366f1, alpha);
            linesCont.moveTo(p.g.x, p.g.y);
            linesCont.lineTo(q.g.x, q.g.y);
          }}
        }}
      }}
    }});

    window.addEventListener('resize', () => {{
      app.renderer.resize(window.innerWidth, window.innerHeight);
    }});
  }} catch(e) {{
    console.warn('PixiJS init failed:', e);
  }}
}})();

// ── TICKER ──────────────────────────────────────────────────────────────────────
function buildTicker() {{
  const items = [
    ['NIFTY',    SYM_DATA.NIFTY.ltp,    SYM_DATA.NIFTY.change_pct,    2, ''],
    ['SENSEX',   SYM_DATA.SENSEX.ltp,   SYM_DATA.SENSEX.change_pct,   2, ''],
    ['BANKNIFTY',SYM_DATA.BANKNIFTY.ltp,SYM_DATA.BANKNIFTY.change_pct,2, ''],
    ['VIX',  GLOBAL_DATA.VIX.ltp,   GLOBAL_DATA.VIX.chg,   2, ''],
    ['DXY',  GLOBAL_DATA.DXY.ltp,   GLOBAL_DATA.DXY.chg,   3, ''],
    ['CRUDE',GLOBAL_DATA.CRUDE.ltp,  GLOBAL_DATA.CRUDE.chg, 2, '$'],
    ['US30', GLOBAL_DATA.US30.ltp,   GLOBAL_DATA.US30.chg,  0, ''],
    ['GOLD', GLOBAL_DATA.GOLD.ltp,   GLOBAL_DATA.GOLD.chg,  1, '$'],
    ['SILVER',GLOBAL_DATA.SILVER.ltp,GLOBAL_DATA.SILVER.chg,2, '$'],
  ];
  const html = [...items, ...items].map(([n,v,c,d,pre]) => {{
    const cv = parseFloat(c)||0;
    const cls = cv>=0 ? 'up' : 'dn';
    const arr = cv>=0 ? '▲' : '▼';
    const val = typeof v === 'number' ? (pre+v.toLocaleString('en-IN',{{minimumFractionDigits:d,maximumFractionDigits:d}})) : v;
    return `<div class="t-item">
      <span class="t-name">${{n}}</span>
      <span class="t-val">${{val}}</span>
      <span class="t-chg ${{cls}}">${{arr}} ${{Math.abs(cv).toFixed(2)}}%</span>
    </div>`;
  }}).join('');
  document.getElementById('ticker').innerHTML = html;
}}

// ── SPARKLINE ───────────────────────────────────────────────────────────────────
function drawSparkline(canvas, candles, sigColor) {{
  if (!candles || candles.length < 2) return;
  const closes = candles.map(c => c[3]);
  const W = canvas.offsetWidth || 300, H = 50;
  canvas.width = W * (window.devicePixelRatio||1);
  canvas.height = H * (window.devicePixelRatio||1);
  const ctx = canvas.getContext('2d');
  ctx.scale(window.devicePixelRatio||1, window.devicePixelRatio||1);
  const mn = Math.min(...closes), mx = Math.max(...closes);
  const rng = mx - mn || 1;
  const xStep = W / (closes.length - 1);
  const pts = closes.map((v,i) => [i*xStep, H - ((v-mn)/rng)*(H-8) - 4]);
  
  // Gradient fill
  const grad = ctx.createLinearGradient(0,0,0,H);
  grad.addColorStop(0, sigColor + '40');
  grad.addColorStop(1, sigColor + '00');
  ctx.beginPath();
  ctx.moveTo(pts[0][0], H);
  pts.forEach(([x,y]) => ctx.lineTo(x,y));
  ctx.lineTo(pts[pts.length-1][0], H);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();

  // Line
  ctx.beginPath();
  pts.forEach(([x,y],i) => i===0 ? ctx.moveTo(x,y) : ctx.lineTo(x,y));
  ctx.strokeStyle = sigColor;
  ctx.lineWidth = 1.5;
  ctx.lineJoin = 'round';
  ctx.stroke();

  // Last dot
  const [lx,ly] = pts[pts.length-1];
  ctx.beginPath();
  ctx.arc(lx,ly,3,0,Math.PI*2);
  ctx.fillStyle = sigColor;
  ctx.fill();
  ctx.beginPath();
  ctx.arc(lx,ly,6,0,Math.PI*2);
  ctx.fillStyle = sigColor+'30';
  ctx.fill();
}}

// ── GAUGE ────────────────────────────────────────────────────────────────────────
function drawGauge(svgEl, score, factors, sigColor) {{
  const pct = Math.max(0, Math.min(1, (score/Math.max(factors,1) + 1) / 2));
  const R = 56, cx = 70, cy = 68;
  const startAngle = Math.PI, endAngle = Math.PI * 2;
  const angle = startAngle + pct * Math.PI;

  function polarToXY(ang, r) {{
    return [cx + r*Math.cos(ang), cy + r*Math.sin(ang)];
  }}

  const trackPath = `M ${{cx-R}} ${{cy}} A ${{R}} ${{R}} 0 0 1 ${{cx+R}} ${{cy}}`;
  const [ex,ey] = polarToXY(angle, R);
  const largeArc = pct > 0.5 ? 1 : 0;
  const fillPath = `M ${{cx-R}} ${{cy}} A ${{R}} ${{R}} 0 ${{largeArc}} 1 ${{ex}} ${{ey}}`;

  svgEl.innerHTML = `
    <defs>
      <linearGradient id="ggrad-${{Math.random().toString(36).slice(2)}}" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="${{score<0?'#ff3d5a':'#ffb020'}}"/>
        <stop offset="100%" stop-color="${{sigColor}}"/>
      </linearGradient>
      <filter id="glow"><feGaussianBlur stdDeviation="2" result="blur"/>
        <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    </defs>
    <path d="${{trackPath}}" fill="none" stroke="rgba(255,255,255,0.07)" stroke-width="8" stroke-linecap="round"/>
    <path d="${{fillPath}}" fill="none" stroke="${{sigColor}}" stroke-width="8" stroke-linecap="round"
          filter="url(#glow)" style="transition:stroke-dashoffset 1s ease"/>
    <circle cx="${{ex}}" cy="${{ey}}" r="5" fill="${{sigColor}}" filter="url(#glow)"/>
    <text x="${{cx}}" y="${{cy-10}}" text-anchor="middle" fill="rgba(255,255,255,0.3)"
          font-family="DM Mono,monospace" font-size="8">BEARISH ◄ ► BULLISH</text>
  `;
}}

// ── CARDS ────────────────────────────────────────────────────────────────────────
function sigGlow(sc) {{
  if(sc==="BUY") return "rgba(0,229,176,0.3)";
  if(sc==="SELL") return "rgba(255,61,90,0.3)";
  return "rgba(255,176,32,0.3)";
}}
function sigIcon(sc) {{
  return sc==="BUY" ? "▲" : sc==="SELL" ? "▼" : "◆";
}}
function fmtNum(v,d=2,pre='') {{
  if(typeof v!=='number') return '—';
  return pre + v.toLocaleString('en-IN',{{minimumFractionDigits:d,maximumFractionDigits:d}});
}}
function scoreColor(s) {{
  if(s>0) return "#00e5b0"; if(s<0) return "#ff3d5a"; return "#ffb020";
}}

function buildCards() {{
  const container = document.getElementById('cards-container');
  const syms = ['NIFTY','SENSEX','BANKNIFTY'];

  syms.forEach((sym, si) => {{
    const d = SYM_DATA[sym];
    const sc = d.signal_color;
    const glow = sigGlow(d.signal);
    const chg = d.change_pct;
    const chgCls = chg>=0 ? 'up' : 'dn';
    const chgArr = chg>=0 ? '▲' : '▼';
    const q = d;

    const card = document.createElement('div');
    card.className = 'card';
    card.style.cssText = `--sig-color:${{sc}};--sig-glow:${{glow}};box-shadow:0 0 60px ${{glow}},0 20px 60px rgba(0,0,0,0.4)`;

    const indRows = d.indicators.map((ind, ii) => {{
      const ic = scoreColor(ind.score);
      return `<div class="ind-row" style="animation-delay:${{0.05*ii + 0.5}}s">
        <div class="ind-num" style="background:${{ic}}22;color:${{ic}};border:1px solid ${{ic}}44">
          ${{ii+1}}
        </div>
        <div class="ind-body">
          <div class="ind-name">${{ind.name}}</div>
          <div class="ind-label">${{ind.label}}</div>
          <div class="ind-detail">${{ind.detail}}</div>
        </div>
        <div class="ind-pip" style="background:${{ic}};box-shadow:0 0 6px ${{ic}}"></div>
      </div>`;
    }}).join('');

    card.innerHTML = `
      <div class="card-head">
        <div class="sym-row">
          <div class="sym-name">${{sym}}</div>
          <div class="sig-badge">${{sigIcon(d.signal)}} ${{d.signal}}</div>
        </div>
        <div class="price-row">
          <div class="ltp" style="color:${{chg>=0?'var(--buy)':'var(--sell)'}}">${{fmtNum(d.ltp,2)}}</div>
          <div class="change ${{chgCls}}">${{chgArr}} ${{Math.abs(chg).toFixed(2)}}%</div>
        </div>
        <div class="ohlc">
          <span><span class="ol">OPEN</span><span class="ov">${{fmtNum(q.open,2)}}</span></span>
          <span><span class="ol">HIGH</span><span class="ov" style="color:var(--buy)">${{fmtNum(q.high,2)}}</span></span>
          <span><span class="ol">LOW</span><span class="ov" style="color:var(--sell)">${{fmtNum(q.low,2)}}</span></span>
        </div>
      </div>

      <div class="sparkline-wrap">
        <canvas class="spark" id="spark-${{sym}}"></canvas>
      </div>

      <div class="gauge-section">
        <div class="gauge-wrap">
          <svg class="gauge-svg" id="gauge-${{sym}}" viewBox="0 0 140 75"></svg>
          <div class="gauge-score">
            <div class="gauge-num" style="color:${{sc}}">${{d.score>0?'+':''}}${{d.score}}</div>
            <div class="gauge-lbl">${{d.score>0?'BULLISH':d.score<0?'BEARISH':'NEUTRAL'}} / ${{d.factors}} SIGNALS</div>
          </div>
        </div>
      </div>

      <div class="ind-list">${{indRows}}</div>
    `;

    container.appendChild(card);

    // Draw after DOM insertion
    requestAnimationFrame(() => {{
      const sparkCanvas = document.getElementById(`spark-${{sym}}`);
      if (sparkCanvas) drawSparkline(sparkCanvas, d.candles, sc);
      const gaugeSvg = document.getElementById(`gauge-${{sym}}`);
      if (gaugeSvg) drawGauge(gaugeSvg, d.score, d.factors, sc);
    }});
  }});
}}

// ── INIT ─────────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {{
  buildTicker();
  buildCards();
}});
</script>
</body>
</html>"""

# ── MAIN ─────────────────────────────────────────────────────────────────────────

def main():
    ts = datetime.datetime.now().strftime("%d %b %Y, %H:%M")
    print("=" * 62)
    print("  AlphaEdge Market Intelligence Engine  v2")
    print(f"  {ts} IST")
    print("=" * 62)

    print("\n[1/4] Global market data...")
    gdata = {}
    vq = fetch_upstox_quote(UPSTOX_INSTRUMENTS["INDIA_VIX"])
    if vq: gdata["VIX"]=vq; print(f"  ✓ VIX {vq['ltp']:.2f}")
    else: print("  ✗ VIX unavailable")
    for key,ytick in YAHOO_SYMBOLS.items():
        d=fetch_yahoo(ytick,days=5,interval="1h")
        if d: gdata[key]=d; print(f"  ✓ {key:<15} {d['ltp']:.3f} ({d['change_pct']:+.2f}%)")
        else: print(f"  ✗ {key} unavailable")

    print("\n[2/4] Index quotes...")
    quotes = {}
    for sym,key in {k:v for k,v in UPSTOX_INSTRUMENTS.items() if k!="INDIA_VIX"}.items():
        q=fetch_upstox_quote(key); quotes[sym]=q or {}
        if q: print(f"  ✓ {sym:<12} {q['ltp']:>12,.2f} ({q['change_pct']:+.2f}%)")
        else: print(f"  ✗ {sym} unavailable")

    print("\n[3/4] Candles + OI...")
    uc,yc,oi_map={},{},{}
    for sym,key in {k:v for k,v in UPSTOX_INSTRUMENTS.items() if k!="INDIA_VIX"}.items():
        c=fetch_upstox_candles(key,days=90); uc[sym]=c
        print(f"  Upstox {sym:<12} {len(c)} bars")
    for sym,ytick in YAHOO_INDEX.items():
        d=fetch_yahoo(ytick,days=90,interval="1d")
        if d and "candles" in d:
            yc[sym]=d["candles"]; print(f"  Yahoo  {sym:<12} {len(d['candles'])} bars")
            if not quotes.get(sym,{}).get("ltp"): quotes[sym]=d
        else: yc[sym]=[]
    for sym in ["NIFTY","BANKNIFTY"]:
        oi=fetch_upstox_oi(sym)
        if oi: oi_map[sym]=oi; print(f"  OI {sym} PCR={oi['pcr']:.2f} Exp={oi['expiry']}")
        else: print(f"  OI {sym} unavailable")

    print("\n[4/4] Computing signals...")
    analyses={}
    EMOJ={"BUY":"🟢","SELL":"🔴","NEUTRAL":"🟡"}
    for sym in ["NIFTY","SENSEX","BANKNIFTY"]:
        a=analyze(sym,quotes.get(sym,{}),uc.get(sym,[]),oi_map.get(sym),gdata,yc.get(sym,[]))
        analyses[sym]=a
        print(f"  {EMOJ[a['signal']]} {sym:<12} {a['signal']:<8} Score:{a['score']:+d}/{a['factors']}")

    html=gen_html(analyses,quotes,gdata,ts)
    fname=f"alphaedge_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(fname,"w",encoding="utf-8") as f: f.write(html)

    print(f"\n{'='*62}")
    for sym,a in analyses.items(): print(f"  {sym:<12} ── {a['signal']}")
    print(f"{'='*62}")
    print(f"\n  ✅  {fname}")
    try: webbrowser.open(f"file://{os.path.abspath(fname)}")
    except: pass
    return fname

if __name__=="__main__":
    main()
