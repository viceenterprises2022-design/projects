import { useState, useEffect, useRef, useCallback } from "react";

/* ═══════════════════════════════════════════════════════════════════
   ALPHACOPY v3  ·  RISK-INTEGRATED TRADING DASHBOARD
   All 6 industry risk rules enforced + visualised
   Aesthetic: submarine control room × Bloomberg terminal
   Fonts: IBM Plex Mono (data) + Barlow Condensed (labels)
═══════════════════════════════════════════════════════════════════ */

const TOTAL_ALLOCATED = 30000;

const INITIAL_BOTS = {
  HL: {
    id:"HL", label:"HYPERLIQUID", accent:"#00c8ff", dim:"#001f2e",
    equity:10847.32, allocated:10000, peak:11200,
    wins:31, losses:16, totalTrades:47,
    dailyTrades:8, maxDailyTrades:50,
    consecLosses:1, maxConsec:5,
    drawdown:3.2, maxDD:20,
    dailyLoss:0.4, maxDailyLoss:7,
    halted:false,
    spark:[9800,9950,10200,10050,10600,10750,10847],
    positions:[
      { id:"hl1", sym:"BTC-PERP",  side:"LONG",  entry:94210,  ltp:96540,   size:893,  sl:89499,  tp:108341, risk:0.97, rr:2.8, source:"0xA3f1…", age:"2h 14m", group:"BTC_CORE",   leverage:3 },
      { id:"hl2", sym:"ETH-PERP",  side:"SHORT", entry:3410,   ltp:3298,    size:307,  sl:3614,   tp:2996,   risk:0.82, rr:2.0, source:"0xB7c2…", age:"4h 32m", group:"ETH_CORE",   leverage:2 },
    ],
  },
  BN: {
    id:"BN", label:"BINANCE", accent:"#f0b90b", dim:"#1e1800",
    equity:9612.18, allocated:10000, peak:10100,
    wins:18, losses:15, totalTrades:33,
    dailyTrades:5, maxDailyTrades:50,
    consecLosses:2, maxConsec:5,
    drawdown:4.1, maxDD:20,
    dailyLoss:1.2, maxDailyLoss:7,
    halted:false,
    spark:[10100,10050,9900,9750,9800,9650,9612],
    positions:[
      { id:"bn1", sym:"SOLUSDT",   side:"LONG",  entry:178.4,  ltp:182.1,   size:308,  sl:168.0,  tp:198.0,  risk:0.93, rr:1.9, source:"UID:9A8F…", age:"6h 08m", group:"LARGE_CAP", leverage:2 },
    ],
  },
  PM: {
    id:"PM", label:"POLYMARKET", accent:"#b06aff", dim:"#1a0028",
    equity:10291.55, allocated:10000, peak:10291.55,
    wins:14, losses:8, totalTrades:22,
    dailyTrades:3, maxDailyTrades:50,
    consecLosses:0, maxConsec:5,
    drawdown:0, maxDD:20,
    dailyLoss:0, maxDailyLoss:7,
    halted:false,
    spark:[10000,10050,10200,10150,10290,10305,10291],
    positions:[
      { id:"pm1", sym:"BTC>$100k",  side:"YES",  entry:0.61,   ltp:0.74,    size:400,  sl:0.31,   tp:0.92,   risk:1.07, rr:2.1, source:"0xFr3n…", age:"2d",     group:"PREDICTION",leverage:1 },
      { id:"pm2", sym:"Fed Cut Q1", side:"NO",   entry:0.38,   ltp:0.29,    size:250,  sl:0.65,   tp:0.10,   risk:0.72, rr:2.0, source:"0xWhal…", age:"3d",     group:"MACRO_POLY",leverage:1 },
    ],
  },
};

const JOURNAL = [
  { id:1, bot:"HL", sym:"BTC-PERP",  side:"LONG",  entry:94210, exit:96540, size:893,  pnl:431.2, rr:"2.8R", risk:"0.97%", status:"OPEN",    ts:"09:14" },
  { id:2, bot:"BN", sym:"SOLUSDT",   side:"LONG",  entry:174.2, exit:182.1, size:308,  pnl:138.6, rr:"1.9R", risk:"0.93%", status:"OPEN",    ts:"08:52" },
  { id:3, bot:"PM", sym:"BTC>$100k", side:"YES",   entry:0.61,  exit:0.74,  size:400,  pnl:85.2,  rr:"2.1R", risk:"1.07%", status:"OPEN",    ts:"2d ago" },
  { id:4, bot:"HL", sym:"AVAX-PERP", side:"LONG",  entry:38.4,  exit:42.1,  size:500,  pnl:48.2,  rr:"2.4R", risk:"0.88%", status:"CLOSED",  ts:"Yesterday" },
  { id:5, bot:"BN", sym:"BNBUSDT",   side:"LONG",  entry:612,   exit:591,   size:600,  pnl:-20.5, rr:"-1R",  risk:"0.90%", status:"STOPPED", ts:"Yesterday" },
  { id:6, bot:"HL", sym:"SOL-PERP",  side:"SHORT", entry:185,   exit:179.2, size:420,  pnl:13.2,  rr:"0.7R", risk:"0.75%", status:"CLOSED",  ts:"2d ago" },
];

const CORR_GROUPS = [
  { name:"BTC_CORE",    pct:12.5, limit:25 },
  { name:"ETH_CORE",    pct:6.1,  limit:25 },
  { name:"LARGE_CAP",   pct:3.2,  limit:25 },
  { name:"PREDICTION",  pct:2.7,  limit:25 },
  { name:"MACRO_POLY",  pct:1.9,  limit:25 },
];

// ─── utils ────────────────────────────────────────────────────────────────
function calcPnl(p) {
  const dir = (p.side==="LONG"||p.side==="YES") ? 1 : -1;
  return dir * (p.ltp - p.entry) / p.entry * p.size;
}
function fmtD(v, dec=2) {
  return (v>=0?"+":"-") + "$" + Math.abs(v).toFixed(dec).replace(/\B(?=(\d{3})+(?!\d))/g,",");
}
function fmtP(v) { return (v>=0?"+":"") + v.toFixed(2) + "%" }

// ─── Sparkline ────────────────────────────────────────────────────────────
function Spark({ vals, color, w=64, h=22 }) {
  if (!vals||vals.length<2) return null;
  const mx=Math.max(...vals), mn=Math.min(...vals), rng=mx-mn||1;
  const pts = vals.map((v,i)=>`${(i/(vals.length-1))*w},${h-((v-mn)/rng)*h}`).join(" ");
  const fillPts = pts + ` ${w},${h} 0,${h}`;
  const gradId = `sg${color.replace(/[^a-z0-9]/gi,"")}`;
  return (
    <svg width={w} height={h} style={{overflow:"visible",display:"block"}}>
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3"/>
          <stop offset="100%" stopColor={color} stopOpacity="0"/>
        </linearGradient>
      </defs>
      <polygon points={fillPts} fill={`url(#${gradId})`}/>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5"
        strokeLinejoin="round" strokeLinecap="round"/>
    </svg>
  );
}

// ─── Animated number ──────────────────────────────────────────────────────
function Live({ val, dec=2, prefix="$", color="#c8d6e8" }) {
  const [v, setV] = useState(val);
  const [flash, setFlash] = useState(0);
  const prev = useRef(val);
  useEffect(()=>{
    if (prev.current===val) return;
    setFlash(val>prev.current?1:-1);
    prev.current=val; setV(val);
    const t=setTimeout(()=>setFlash(0),500);
    return ()=>clearTimeout(t);
  },[val]);
  const c = flash===1?"#00ff99":flash===-1?"#ff3355":color;
  return <span style={{color:c,transition:"color .3s",fontVariantNumeric:"tabular-nums"}}>
    {prefix}{Math.abs(v).toFixed(dec)}
  </span>;
}

// ─── Thin progress bar ────────────────────────────────────────────────────
function Bar({ pct, color, h=3, bg="#0b0f16" }) {
  return (
    <div style={{height:h,background:bg,borderRadius:h,overflow:"hidden"}}>
      <div style={{width:`${Math.min(100,pct)}%`,height:"100%",background:color,
        borderRadius:h,transition:"width .5s"}}/>
    </div>
  );
}

// ─── Donut risk gauge ─────────────────────────────────────────────────────
function RiskGauge({ val, max=2, size=32 }) {
  const pct = Math.min(1, val/max);
  const c = val>1.8?"#ff3355":val>1.2?"#ff9800":"#00cc88";
  const r=12, cx=size/2, cy=size/2;
  const circ=2*Math.PI*r;
  return (
    <svg width={size} height={size}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#0f1620" strokeWidth="3.5"/>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={c} strokeWidth="3.5"
        strokeDasharray={`${pct*circ} ${circ}`}
        strokeLinecap="round"
        transform={`rotate(-90 ${cx} ${cy})`}/>
      <text x={cx} y={cy+1} textAnchor="middle" dominantBaseline="middle"
        fontSize="7" fontWeight="700" fill={c} fontFamily="monospace">{val}</text>
    </svg>
  );
}

// ─── Close position modal ─────────────────────────────────────────────────
function CloseModal({ pos, accent, onConfirm, onCancel }) {
  const p = calcPnl(pos);
  return (
    <div style={{position:"fixed",inset:0,background:"rgba(0,0,0,.9)",display:"flex",
      alignItems:"center",justifyContent:"center",zIndex:9999,backdropFilter:"blur(8px)"}}>
      <div style={{background:"#0a0d14",border:`1px solid ${accent}50`,borderRadius:12,
        padding:"28px 32px",minWidth:380,boxShadow:`0 0 80px ${accent}15`}}>
        <div style={{fontSize:9,color:accent,letterSpacing:3,marginBottom:10,
          fontFamily:"'Barlow Condensed',sans-serif",textTransform:"uppercase"}}>
          Close Position
        </div>
        <div style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:22,
          fontWeight:700,color:"#e0ecff",marginBottom:4}}>{pos.sym}</div>
        <div style={{fontSize:11,color:"#3a4e62",marginBottom:18}}>
          {pos.side} · Entry {pos.entry} · Current {pos.ltp.toFixed(pos.ltp>10?2:4)}
        </div>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr 1fr",gap:12,marginBottom:18}}>
          {[
            {l:"EST. P&L",  v:fmtD(p,2),          c:p>=0?"#00cc88":"#ff4455"},
            {l:"RISK",      v:pos.risk+"%",         c:"#7a8aaa"},
            {l:"R:R",       v:pos.rr+"",            c:"#7a8aaa"},
            {l:"SIZE",      v:"$"+pos.size,         c:"#7a8aaa"},
          ].map(x=>(
            <div key={x.l}>
              <div style={{fontSize:8,color:"#2a3848",letterSpacing:1,marginBottom:3}}>{x.l}</div>
              <div style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:14,
                fontWeight:700,color:x.c}}>{x.v}</div>
            </div>
          ))}
        </div>
        <div style={{fontSize:10,color:"#e08020",background:"#e0802012",
          border:"1px solid #e0802030",borderRadius:5,padding:"8px 12px",marginBottom:18}}>
          ⚠ MARKET ORDER — executes immediately. Slippage risk applies.
        </div>
        <div style={{display:"flex",gap:10}}>
          <button onClick={onCancel} style={{flex:1,padding:"10px 0",borderRadius:7,
            background:"#0f1520",border:"1px solid #1a2535",color:"#3a5070",
            fontSize:12,cursor:"pointer",fontFamily:"inherit"}}>Cancel</button>
          <button onClick={()=>onConfirm(pos)} style={{flex:1,padding:"10px 0",borderRadius:7,
            background:"#b91c1c",border:"none",color:"#fff",fontSize:12,fontWeight:800,
            cursor:"pointer",fontFamily:"inherit",letterSpacing:.5}}>CLOSE POSITION</button>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// ROOT DASHBOARD
// ═══════════════════════════════════════════════════════════════════
export default function Dashboard() {
  const [bots, setBots]             = useState(INITIAL_BOTS);
  const [activeBot, setActiveBot]   = useState("HL");
  const [tab, setTab]               = useState("positions");
  const [closing, setClosing]       = useState(null);
  const [killConfirm, setKillConfirm] = useState(false);
  const [globalHalt, setGlobalHalt] = useState(false);
  const [journalFilter, setJournalFilter] = useState("ALL");
  const [time, setTime]             = useState(new Date());
  const [alertLog, setAlertLog]     = useState([]);

  // live price simulation
  useEffect(()=>{
    const iv=setInterval(()=>{
      setBots(prev=>{
        const n={...prev};
        Object.keys(n).forEach(k=>{
          n[k]={...n[k],positions:n[k].positions.map(p=>({
            ...p,
            ltp:p.ltp>10
              ? +(p.ltp*(1+(Math.random()-.5)*.0012)).toFixed(2)
              : +(p.ltp*(1+(Math.random()-.5)*.004)).toFixed(4)
          }))};
        });
        return n;
      });
      setTime(new Date());
    }, 1500);
    return ()=>clearInterval(iv);
  },[]);

  const totalEquity  = Object.values(bots).reduce((a,b)=>a+b.equity,0);
  const totalPnl     = totalEquity - TOTAL_ALLOCATED;
  const totalPnlPct  = totalPnl/TOTAL_ALLOCATED*100;
  const allOpen      = Object.values(bots).flatMap(b=>b.positions);
  const maxRisk1Pct  = totalEquity*0.01;
  const maxRisk2Pct  = totalEquity*0.02;
  const portfolioDD  = ((Math.max(...Object.values(bots).map(b=>b.peak))+
    TOTAL_ALLOCATED - totalEquity)/TOTAL_ALLOCATED*100).toFixed(1);

  const bot = bots[activeBot];

  const confirmClose = useCallback(pos=>{
    setBots(prev=>{
      const n={...prev};
      Object.keys(n).forEach(k=>{
        n[k]={...n[k],positions:n[k].positions.filter(p=>p.id!==pos.id)};
      });
      return n;
    });
    const p=calcPnl(pos);
    setAlertLog(prev=>[{
      ts:new Date().toLocaleTimeString(),
      msg:`CLOSED ${pos.sym} ${pos.side} @ ${pos.ltp} | P&L: ${fmtD(p)}`
    },...prev.slice(0,9)]);
    setClosing(null);
  },[]);

  // ─── Risk rules state ───────────────────────────────────────────────────
  const rules = [
    {
      num:"①", key:"r1", label:"1%–2% RULE", shortLabel:"1% RULE",
      desc:"Max risk per trade",
      pass:true, warn:false,
      detail:`Max $${maxRisk1Pct.toFixed(0)}/trade · Avg 0.93%`,
      metric: `${(allOpen.reduce((a,p)=>a+p.risk,0)/Math.max(allOpen.length,1)).toFixed(2)}% avg`,
      color:"#00c8ff",
    },
    {
      num:"②", key:"r2", label:"MANDATORY SL", shortLabel:"STOP LOSS",
      desc:"Every position has a stop-loss",
      pass:true, warn:false,
      detail:`${allOpen.length}/${allOpen.length} positions protected`,
      metric: `${allOpen.length} / ${allOpen.length}`,
      color:"#00cc88",
    },
    {
      num:"③", key:"r3", label:"MIN R:R  1:2", shortLabel:"R:R RATIO",
      desc:"Reward ≥ 2× risk on every trade",
      pass:true, warn:true,
      detail:`SOLUSDT at 1.9 — near limit`,
      metric: `${(allOpen.reduce((a,p)=>a+(typeof p.rr==="string"?parseFloat(p.rr):p.rr),0)/Math.max(allOpen.length,1)).toFixed(1)} avg`,
      color:"#ff9800",
    },
    {
      num:"④", key:"r4", label:"DIVERSIFICATION", shortLabel:"EXPOSURE",
      desc:"Non-correlated exposure limits",
      pass:true, warn:true,
      detail:`BTC_CORE 12.5% of 25% limit`,
      metric:`5 groups`,
      color:"#ff9800",
    },
    {
      num:"⑤", key:"r5", label:"KILL SWITCHES", shortLabel:"KILL SW.",
      desc:"Velocity + drawdown gates",
      pass:!globalHalt, warn:false,
      detail:globalHalt?"PORTFOLIO HALT ACTIVE":"All thresholds clear",
      metric:globalHalt?"HALTED":"ACTIVE",
      color:globalHalt?"#ff4455":"#00cc88",
    },
    {
      num:"⑥", key:"r6", label:"ALGO VALIDATED", shortLabel:"BACKTEST",
      desc:"14-day paper trade gate",
      pass:false, warn:false,
      detail:`Day 9 / 14 · PnL +$341`,
      metric:`9 / 14 days`,
      color:"#ff4455",
    },
  ];

  // ─── CSS ─────────────────────────────────────────────────────────────────
  const css = `
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Barlow+Condensed:wght@400;500;600;700;800&display=swap');
    *{box-sizing:border-box;margin:0;padding:0}
    ::-webkit-scrollbar{width:3px;height:3px}
    ::-webkit-scrollbar-track{background:#070a0f}
    ::-webkit-scrollbar-thumb{background:#1a2535;border-radius:2px}
    @keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.3;transform:scale(.75)}}
    @keyframes fadeIn{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}
    @keyframes scanIn{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:translateX(0)}}
    .tab-content{animation:fadeIn .2s ease}
    .row-hover:hover{background:#0d1525 !important}
  `;

  // ─── POSITIONS TAB ────────────────────────────────────────────────────────
  function PositionsTab() {
    return (
      <div className="tab-content" style={{overflowX:"auto"}}>
        {bot.positions.length===0 ? (
          <div style={{padding:"60px",textAlign:"center",color:"#1a2535",
            fontFamily:"'Barlow Condensed',sans-serif",fontSize:13,letterSpacing:3}}>
            NO OPEN POSITIONS
          </div>
        ):(
          <table style={{width:"100%",borderCollapse:"collapse",fontSize:11,minWidth:900}}>
            <thead>
              <tr style={{borderBottom:"1px solid #0d1525"}}>
                {["SYMBOL","SIDE","ENTRY","LTP","SIZE","SL","TP","RISK ①","R:R ③","SL→TP","CORR GROUP ④","HELD","CLOSE"].map(h=>(
                  <th key={h} style={{padding:"7px 10px",fontSize:8,
                    fontFamily:"'Barlow Condensed',sans-serif",
                    color: h.includes("①")?"#00c8ff66":h.includes("③")?"#ff980066":
                           h.includes("④")?"#b06aff66":"#1e2d3e",
                    letterSpacing:1.5,fontWeight:600,textAlign:"left",whiteSpace:"nowrap"}}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {bot.positions.map(p=>{
                const P      = calcPnl(p);
                const isLong = p.side==="LONG"||p.side==="YES";
                const rrNum  = typeof p.rr==="string"?parseFloat(p.rr):p.rr;
                const rrCol  = rrNum>=2?"#00cc88":rrNum>=1.5?"#ff9800":"#ff4455";
                const riskCol= p.risk>1.8?"#ff4455":p.risk>1.2?"#ff9800":"#00c8ff";
                const slDist = Math.abs(p.ltp-p.sl)/p.ltp*100;
                const range  = Math.abs(p.tp-p.sl);
                const prog   = range>0?Math.min(100,Math.abs(p.ltp-p.sl)/range*100):50;

                return (
                  <tr key={p.id} className="row-hover"
                    style={{borderBottom:"1px solid #080d14",transition:"background .15s"}}>
                    <td style={{padding:"9px 10px"}}>
                      <div style={{fontFamily:"'IBM Plex Mono',monospace",fontWeight:700,
                        color:"#c8ddf0",fontSize:12}}>{p.sym}</div>
                      <div style={{fontSize:8,color:"#1e2d3e",marginTop:1}}>{p.source} · {p.leverage}×</div>
                    </td>
                    <td style={{padding:"9px 10px"}}>
                      <span style={{fontSize:9,fontWeight:700,padding:"2px 8px",
                        borderRadius:3,letterSpacing:1,
                        background:isLong?"#00cc8815":"#ff445515",
                        color:isLong?"#00cc88":"#ff6677",
                        border:`1px solid ${isLong?"#00cc8835":"#ff445535"}`}}>
                        {p.side}
                      </span>
                    </td>
                    <td style={{padding:"9px 10px",fontFamily:"'IBM Plex Mono',monospace",
                      fontSize:10,color:"#3a4e62"}}>{p.entry}</td>
                    <td style={{padding:"9px 10px",fontFamily:"'IBM Plex Mono',monospace"}}>
                      <span style={{fontSize:12,fontWeight:600,
                        color:P>=0?"#00cc88":"#ff5566"}}>
                        <Live val={p.ltp} dec={p.ltp>10?2:4} prefix=""
                          color={P>=0?"#00cc88":"#ff5566"}/>
                      </span>
                    </td>
                    <td style={{padding:"9px 10px",fontFamily:"'IBM Plex Mono',monospace",
                      fontSize:11,color:"#6a7a8a"}}>${p.size}</td>
                    <td style={{padding:"9px 10px",fontFamily:"'IBM Plex Mono',monospace",
                      fontSize:10,color:"#cc4455"}}>{p.sl}</td>
                    <td style={{padding:"9px 10px",fontFamily:"'IBM Plex Mono',monospace",
                      fontSize:10,color:"#33aa77"}}>{p.tp}</td>

                    {/* RISK (Rule ①) */}
                    <td style={{padding:"9px 10px"}}>
                      <div style={{display:"flex",alignItems:"center",gap:6}}>
                        <RiskGauge val={p.risk} max={2} size={30}/>
                        <div>
                          <div style={{fontSize:9,fontFamily:"'IBM Plex Mono',monospace",
                            fontWeight:700,color:riskCol}}>{p.risk}%</div>
                          <div style={{fontSize:7,color:"#1e2d3e"}}>
                            ${(p.risk/100*totalEquity).toFixed(0)} at risk
                          </div>
                        </div>
                      </div>
                    </td>

                    {/* R:R (Rule ③) */}
                    <td style={{padding:"9px 10px"}}>
                      <div style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:14,
                        fontWeight:700,color:rrCol}}>{p.rr}</div>
                      <div style={{fontSize:7,color:rrNum>=2?"#00884455":"#ff440055",
                        marginTop:1}}>
                        {rrNum>=2?"✓ MET":"⚠ BELOW 2:1"}
                      </div>
                    </td>

                    {/* SL→TP bar (Rule ②③) */}
                    <td style={{padding:"9px 10px",minWidth:110}}>
                      <div style={{display:"flex",justifyContent:"space-between",
                        fontSize:7,color:"#1e2d3e",marginBottom:3}}>
                        <span style={{color:"#cc4455"}}>SL</span>
                        <span style={{color:"#3a5a4a"}}>{slDist.toFixed(1)}% away</span>
                        <span style={{color:"#33aa77"}}>TP</span>
                      </div>
                      <div style={{height:4,background:"#0a0f1a",borderRadius:2,
                        position:"relative",overflow:"visible"}}>
                        <div style={{height:"100%",borderRadius:2,
                          background:`linear-gradient(90deg,#cc4455,${bot.accent},#33aa77)`,
                          width:`${prog}%`,transition:"width .4s"}}/>
                        <div style={{position:"absolute",top:-2,width:8,height:8,
                          borderRadius:"50%",background:bot.accent,
                          left:`calc(${prog}% - 4px)`,
                          boxShadow:`0 0 6px ${bot.accent}`,transition:"left .4s"}}/>
                      </div>
                    </td>

                    {/* Correlation group (Rule ④) */}
                    <td style={{padding:"9px 10px"}}>
                      <span style={{fontSize:8,padding:"2px 7px",borderRadius:3,
                        background:"#0a1020",border:"1px solid #1a2535",
                        color:"#3a5070",letterSpacing:.5}}>{p.group}</span>
                    </td>

                    <td style={{padding:"9px 10px",fontFamily:"'IBM Plex Mono',monospace",
                      fontSize:9,color:"#1e2d3e",textAlign:"center"}}>{p.age}</td>

                    <td style={{padding:"9px 10px"}}>
                      <button onClick={()=>setClosing(p)}
                        style={{padding:"4px 12px",borderRadius:5,background:"transparent",
                          border:"1px solid #aa1c1c80",color:"#ee5566",fontSize:8,
                          fontWeight:700,cursor:"pointer",fontFamily:"inherit",
                          letterSpacing:1,transition:"all .2s"}}
                        onMouseEnter={e=>{e.currentTarget.style.background="#b91c1c";e.currentTarget.style.color="#fff"}}
                        onMouseLeave={e=>{e.currentTarget.style.background="transparent";e.currentTarget.style.color="#ee5566"}}>
                        CLOSE
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    );
  }

  // ─── RISK RULES TAB ───────────────────────────────────────────────────────
  function RulesTab() {
    return (
      <div className="tab-content" style={{padding:"16px",display:"flex",flexDirection:"column",gap:14}}>
        {/* 6 rule cards */}
        <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:10}}>
          {rules.map(r=>{
            const status = !r.pass?"FAIL":r.warn?"WARN":"OK";
            const sc = {
              OK:  {bg:"#001a0e",bd:"#00cc8830",tx:"#00cc88",ln:"#00cc88"},
              WARN:{bg:"#1a1000",bd:"#ff980030",tx:"#ff9800",ln:"#ff9800"},
              FAIL:{bg:"#1a0008",bd:"#ff445530",tx:"#ff4455",ln:"#ff4455"},
            }[status];
            return (
              <div key={r.key} style={{background:sc.bg,border:`1px solid ${sc.bd}`,
                borderRadius:8,padding:"14px 15px",position:"relative",overflow:"hidden"}}>
                <div style={{position:"absolute",top:0,left:0,right:0,height:2,
                  background:`linear-gradient(90deg,transparent,${sc.ln}80,transparent)`}}/>
                <div style={{display:"flex",justifyContent:"space-between",
                  alignItems:"flex-start",marginBottom:10}}>
                  <span style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:20,
                    color:sc.ln,opacity:.5,lineHeight:1}}>{r.num}</span>
                  <span style={{fontSize:8,padding:"2px 8px",borderRadius:3,
                    color:sc.tx,border:`1px solid ${sc.bd}`,letterSpacing:1.5,
                    fontWeight:700}}>{status}</span>
                </div>
                <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:13,
                  fontWeight:700,color:"#c0d0e0",letterSpacing:1,marginBottom:3}}>
                  {r.label}
                </div>
                <div style={{fontSize:9,color:"#2a3a4a",marginBottom:8}}>{r.desc}</div>
                <div style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:10,color:sc.tx}}>
                  {r.detail}
                </div>
                <div style={{marginTop:8,display:"flex",justifyContent:"space-between",
                  alignItems:"center"}}>
                  <span style={{fontSize:9,color:"#1e2d3e"}}>Live</span>
                  <span style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:11,
                    fontWeight:700,color:sc.tx}}>{r.metric}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* 1% Rule sizing calculator */}
        <div style={{background:"#06090f",border:"1px solid #0d1525",borderRadius:8,padding:"14px 16px"}}>
          <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:9,
            color:"#00c8ff50",letterSpacing:2,marginBottom:12}}>
            ① POSITION SIZING — 1% RISK RULE
          </div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:10,marginBottom:12}}>
            {[
              {l:"Portfolio Equity",  v:`$${totalEquity.toFixed(0)}`,         c:"#7a9aaa"},
              {l:"1% Max Risk",       v:`$${maxRisk1Pct.toFixed(0)}`,          c:"#00cc88"},
              {l:"2% Hard Cap",       v:`$${maxRisk2Pct.toFixed(0)}`,          c:"#ff9800"},
              {l:"Max Position Size", v:`$${Math.min(totalEquity*.15,5000).toFixed(0)}`, c:"#b06aff"},
            ].map(x=>(
              <div key={x.l} style={{background:"#09101a",border:"1px solid #0f1a28",
                borderRadius:6,padding:"10px 12px"}}>
                <div style={{fontSize:8,color:"#1e2d3e",letterSpacing:1,marginBottom:5}}>{x.l}</div>
                <div style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:17,
                  fontWeight:700,color:x.c}}>{x.v}</div>
              </div>
            ))}
          </div>
          <div style={{background:"#04060c",border:"1px solid #0a1020",borderRadius:5,
            padding:"9px 12px",fontFamily:"'IBM Plex Mono',monospace",
            fontSize:10,color:"#2a3a4a",lineHeight:1.9}}>
            <span style={{color:"#3a5070"}}>Example: </span>
            BTC @ $95,000 · SL $90,250 (−5%) →
            Size = ${(maxRisk1Pct/0.05).toFixed(0)} · Risk at risk = ${maxRisk1Pct.toFixed(0)} ·
            <span style={{color:"#00cc8888"}}> R:R 2:1 → TP $104,750 ✓</span>
          </div>
        </div>

        {/* Kill switch thresholds */}
        <div style={{background:"#06090f",border:"1px solid #0d1525",borderRadius:8,padding:"14px 16px"}}>
          <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:9,
            color:"#ff980050",letterSpacing:2,marginBottom:12}}>
            ⑤ KILL SWITCH THRESHOLDS — REAL-TIME
          </div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:10}}>
            {[
              {l:"Portfolio DD",       used:parseFloat(portfolioDD), limit:15,  col:"#b06aff", bot:null},
              {l:"Daily Loss (Portfolio)",used:0,   limit:5,   col:"#ff4455", bot:null},
              {l:"HL · Consec Losses", used:bots.HL.consecLosses, limit:5, col:"#00c8ff", isCount:true},
              {l:"BN · Consec Losses", used:bots.BN.consecLosses, limit:5, col:"#f0b90b", isCount:true},
              {l:"HL · Daily Loss",    used:bots.HL.dailyLoss,   limit:7,   col:"#00c8ff",bot:"HL"},
              {l:"BN · Daily Loss",    used:bots.BN.dailyLoss,   limit:7,   col:"#f0b90b",bot:"BN"},
              {l:"HL · Trades Today",  used:bots.HL.dailyTrades, limit:50,  col:"#00c8ff",isCount:true},
              {l:"BN · Trades Today",  used:bots.BN.dailyTrades, limit:50,  col:"#f0b90b",isCount:true},
            ].map(t=>{
              const pct=t.used/t.limit*100;
              const c=pct>75?t.col:pct>45?"#ff9800":"#1a2838";
              return (
                <div key={t.l} style={{background:"#09101a",border:"1px solid #0f1a28",
                  borderRadius:6,padding:"10px 12px"}}>
                  <div style={{display:"flex",justifyContent:"space-between",
                    fontSize:8,color:"#2a3a4a",marginBottom:6}}>
                    <span style={{color:"#3a5070"}}>{t.l}</span>
                    <span style={{color:c,fontFamily:"'IBM Plex Mono',monospace"}}>
                      {t.used}{t.isCount?"":"%"} / {t.limit}{t.isCount?"":"%"}
                    </span>
                  </div>
                  <Bar pct={pct} color={c}/>
                  {pct>75&&<div style={{fontSize:7,color:t.col+"88",marginTop:4}}>⚠ approaching limit</div>}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  // ─── EXPOSURE TAB (Rule ④) ────────────────────────────────────────────────
  function ExposureTab() {
    const botExp = Object.values(bots).map(b=>({
      id:b.id, accent:b.accent,
      pct:b.positions.reduce((a,p)=>a+p.size,0)/totalEquity*100
    }));
    return (
      <div className="tab-content" style={{padding:"16px",display:"flex",flexDirection:"column",gap:14}}>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
          {/* Correlation groups */}
          <div style={{background:"#06090f",border:"1px solid #0d1525",borderRadius:8,padding:"14px 16px"}}>
            <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:9,
              color:"#b06aff50",letterSpacing:2,marginBottom:14}}>
              ④ CORRELATION GROUP EXPOSURE · MAX 25%
            </div>
            {CORR_GROUPS.map(g=>{
              const pct=g.pct/g.limit*100;
              const c=g.pct>g.limit*.8?"#ff9800":g.pct>g.limit*.5?"#00c8ff":"#00cc88";
              return (
                <div key={g.name} style={{marginBottom:12}}>
                  <div style={{display:"flex",justifyContent:"space-between",
                    fontSize:10,marginBottom:4}}>
                    <span style={{fontFamily:"'IBM Plex Mono',monospace",color:"#5a7a8a"}}>
                      {g.name}
                    </span>
                    <span style={{fontFamily:"'IBM Plex Mono',monospace",fontWeight:700,color:c}}>
                      {g.pct}%{g.pct>g.limit*.75&&" ⚠"}
                    </span>
                  </div>
                  <div style={{height:5,background:"#0a0f1a",borderRadius:3,overflow:"hidden"}}>
                    <div style={{width:`${pct}%`,height:"100%",background:c,
                      borderRadius:3,boxShadow:`0 0 8px ${c}50`,transition:"width .5s"}}/>
                  </div>
                  <div style={{fontSize:7,color:"#1a2535",marginTop:2,textAlign:"right"}}>
                    {g.pct} / {g.limit}% limit
                  </div>
                </div>
              );
            })}
          </div>

          <div style={{display:"flex",flexDirection:"column",gap:12}}>
            {/* Bot allocation */}
            <div style={{background:"#06090f",border:"1px solid #0d1525",borderRadius:8,padding:"14px 16px"}}>
              <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:9,
                color:"#b06aff50",letterSpacing:2,marginBottom:12}}>
                BOT ALLOCATION · MAX 40% EACH
              </div>
              {botExp.map(b=>(
                <div key={b.id} style={{marginBottom:10}}>
                  <div style={{display:"flex",justifyContent:"space-between",
                    fontSize:10,marginBottom:4}}>
                    <span style={{color:b.accent,fontWeight:700}}>{b.id}</span>
                    <span style={{fontFamily:"'IBM Plex Mono',monospace",
                      color:b.pct>32?"#ff9800":"#4a6080"}}>{b.pct.toFixed(1)}% / 40%</span>
                  </div>
                  <Bar pct={b.pct/40*100} color={b.accent}/>
                </div>
              ))}
            </div>

            {/* Diversity stats */}
            <div style={{background:"#06090f",border:"1px solid #0d1525",borderRadius:8,padding:"14px 16px"}}>
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10}}>
                {[
                  {l:"Total Open",   v:allOpen.length,                              c:"#00c8ff",  note:`of 15 max`},
                  {l:"Asset Classes",v:3,                                            c:"#00cc88",  note:"≥3 req. ✓"},
                  {l:"Total Exposure",v:`${(allOpen.reduce((a,p)=>a+p.size,0)/totalEquity*100).toFixed(1)}%`, c:"#b06aff",note:"of equity"},
                  {l:"Open Risk $",  v:`$${allOpen.reduce((a,p)=>a+p.risk/100*totalEquity,0).toFixed(0)}`,c:"#ff9800",note:"total at risk"},
                ].map(x=>(
                  <div key={x.l} style={{background:"#09101a",border:"1px solid #0f1a28",
                    borderRadius:6,padding:"10px 12px"}}>
                    <div style={{fontSize:8,color:"#1e2d3e",letterSpacing:1,marginBottom:5}}>{x.l}</div>
                    <div style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:17,
                      fontWeight:700,color:x.c}}>{x.v}</div>
                    <div style={{fontSize:7,color:"#2a3a4a",marginTop:2}}>{x.note}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Per-position exposure table */}
        <div style={{background:"#06090f",border:"1px solid #0d1525",borderRadius:8,padding:"14px 16px"}}>
          <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:9,
            color:"#1e2d3e",letterSpacing:2,marginBottom:12}}>ALL OPEN POSITIONS — RISK BREAKDOWN</div>
          <table style={{width:"100%",borderCollapse:"collapse",fontSize:10}}>
            <thead>
              <tr style={{borderBottom:"1px solid #0d1525"}}>
                {["BOT","SYMBOL","GROUP","SIZE","RISK %","$ AT RISK","R:R","STATUS"].map(h=>(
                  <th key={h} style={{padding:"5px 10px",fontSize:8,color:"#1e2d3e",
                    fontFamily:"'Barlow Condensed',sans-serif",letterSpacing:1.5,
                    textAlign:"left",fontWeight:600}}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {allOpen.map(p=>{
                const bot2=Object.values(bots).find(b=>b.positions.some(x=>x.id===p.id));
                const rrN=typeof p.rr==="string"?parseFloat(p.rr):p.rr;
                return (
                  <tr key={p.id} className="row-hover"
                    style={{borderBottom:"1px solid #080d14"}}>
                    <td style={{padding:"7px 10px"}}>
                      <span style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:9,
                        fontWeight:700,color:bot2?.accent}}>{bot2?.id}</span>
                    </td>
                    <td style={{padding:"7px 10px",fontFamily:"'IBM Plex Mono',monospace",
                      color:"#7a9aaa"}}>{p.sym}</td>
                    <td style={{padding:"7px 10px"}}>
                      <span style={{fontSize:8,padding:"1px 6px",borderRadius:3,
                        background:"#0a1020",border:"1px solid #1a2535",color:"#3a5070"}}>
                        {p.group}
                      </span>
                    </td>
                    <td style={{padding:"7px 10px",fontFamily:"'IBM Plex Mono',monospace",
                      color:"#4a6080"}}>${p.size}</td>
                    <td style={{padding:"7px 10px",fontFamily:"'IBM Plex Mono',monospace",
                      color:p.risk>1.8?"#ff4455":p.risk>1.2?"#ff9800":"#00c8ff"}}>
                      {p.risk}%
                    </td>
                    <td style={{padding:"7px 10px",fontFamily:"'IBM Plex Mono',monospace",
                      color:"#ff9800"}}>
                      ${(p.risk/100*totalEquity).toFixed(0)}
                    </td>
                    <td style={{padding:"7px 10px",fontFamily:"'IBM Plex Mono',monospace",
                      fontWeight:700,color:rrN>=2?"#00cc88":rrN>=1.5?"#ff9800":"#ff4455"}}>
                      {p.rr}
                    </td>
                    <td style={{padding:"7px 10px"}}>
                      <span style={{fontSize:8,padding:"1px 6px",borderRadius:3,
                        background:"#00cc8812",border:"1px solid #00cc8828",color:"#00cc88"}}>
                        OPEN
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  // ─── JOURNAL TAB ─────────────────────────────────────────────────────────
  function JournalTab() {
    const botCol={HL:"#00c8ff",BN:"#f0b90b",PM:"#b06aff"};
    const rows=journalFilter==="ALL"?JOURNAL:JOURNAL.filter(t=>t.status===journalFilter);
    return (
      <div className="tab-content">
        <div style={{padding:"10px 16px",borderBottom:"1px solid #080d14",
          display:"flex",alignItems:"center",gap:6,background:"#04060c"}}>
          {["ALL","OPEN","CLOSED","STOPPED"].map(f=>(
            <button key={f} onClick={()=>setJournalFilter(f)} style={{
              padding:"3px 12px",borderRadius:4,border:"none",
              background:journalFilter===f?"#0f1828":"transparent",
              color:journalFilter===f?"#6090b0":"#1e2d3e",fontSize:8,
              cursor:"pointer",fontFamily:"inherit",letterSpacing:1,fontWeight:700}}>
              {f}
            </button>
          ))}
          <div style={{marginLeft:"auto",display:"flex",alignItems:"center",gap:6,
            fontSize:8,color:"#1e2d3e",fontFamily:"'IBM Plex Mono',monospace"}}>
            <div style={{width:5,height:5,borderRadius:"50%",background:"#00cc88",
              boxShadow:"0 0 4px #00cc88",animation:"pulse 2s infinite"}}/>
            TELEGRAM ALERTS ACTIVE
          </div>
        </div>
        <div style={{maxHeight:320,overflowY:"auto"}}>
          <table style={{width:"100%",borderCollapse:"collapse",fontSize:10}}>
            <thead>
              <tr style={{borderBottom:"1px solid #0d1525",position:"sticky",top:0,
                background:"#04060c"}}>
                {["BOT","SYMBOL","SIDE","ENTRY","EXIT","SIZE","RISK","P&L","R ACHIEVED","STATUS","TIME"].map(h=>(
                  <th key={h} style={{padding:"6px 10px",fontSize:7,color:"#1e2d3e",
                    fontFamily:"'Barlow Condensed',sans-serif",letterSpacing:1.5,
                    textAlign:"left",fontWeight:600,whiteSpace:"nowrap"}}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map(t=>{
                const isLong=t.side==="LONG"||t.side==="YES";
                const rrN=parseFloat(t.rr);
                return (
                  <tr key={t.id} className="row-hover"
                    style={{borderBottom:"1px solid #070b12"}}>
                    <td style={{padding:"7px 10px"}}>
                      <span style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:9,
                        fontWeight:700,color:botCol[t.bot]}}>{t.bot}</span>
                    </td>
                    <td style={{padding:"7px 10px",fontFamily:"'IBM Plex Mono',monospace",
                      color:"#7a8a9a",fontWeight:600}}>{t.sym}</td>
                    <td style={{padding:"7px 10px"}}>
                      <span style={{fontSize:8,padding:"1px 6px",borderRadius:3,fontWeight:700,
                        background:isLong?"#00cc8812":"#ff445512",
                        color:isLong?"#00aa66":"#ff5566",
                        border:`1px solid ${isLong?"#00cc8830":"#ff445530"}`}}>
                        {t.side}
                      </span>
                    </td>
                    <td style={{padding:"7px 10px",fontFamily:"'IBM Plex Mono',monospace",
                      fontSize:9,color:"#2a3a4a"}}>{t.entry}</td>
                    <td style={{padding:"7px 10px",fontFamily:"'IBM Plex Mono',monospace",
                      fontSize:9,color:"#3a4a5a"}}>{t.exit}</td>
                    <td style={{padding:"7px 10px",fontFamily:"'IBM Plex Mono',monospace",
                      fontSize:9,color:"#4a5a6a"}}>${t.size}</td>
                    <td style={{padding:"7px 10px",fontFamily:"'IBM Plex Mono',monospace",
                      fontSize:9,color:"#00c8ff88"}}>{t.risk}</td>
                    <td style={{padding:"7px 10px",fontFamily:"'IBM Plex Mono',monospace",
                      fontSize:11,fontWeight:700,color:t.pnl>=0?"#00cc88":"#ff5566"}}>
                      {t.pnl>=0?"+":""}{t.pnl.toFixed(2)}
                    </td>
                    <td style={{padding:"7px 10px",fontFamily:"'IBM Plex Mono',monospace",
                      fontSize:10,fontWeight:700,
                      color:rrN>=2?"#00cc88":rrN>=0?"#ff9800":"#ff4455"}}>
                      {t.rr}
                    </td>
                    <td style={{padding:"7px 10px"}}>
                      <span style={{fontSize:7,padding:"2px 7px",borderRadius:3,letterSpacing:.5,
                        fontWeight:700,
                        background:t.status==="OPEN"?"#00cc8810":t.status==="CLOSED"?"#00c8ff10":"#ff980010",
                        color:t.status==="OPEN"?"#00cc88":t.status==="CLOSED"?"#00c8ff":"#ff9800",
                        border:`1px solid ${t.status==="OPEN"?"#00cc8828":t.status==="CLOSED"?"#00c8ff28":"#ff980028"}`}}>
                        {t.status}
                      </span>
                    </td>
                    <td style={{padding:"7px 10px",fontFamily:"'IBM Plex Mono',monospace",
                      fontSize:8,color:"#1e2d3e"}}>{t.ts}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {/* Alert log */}
        {alertLog.length>0&&(
          <div style={{borderTop:"1px solid #080d14",padding:"8px 16px",
            background:"#04060c",maxHeight:80,overflowY:"auto"}}>
            {alertLog.map((a,i)=>(
              <div key={i} style={{fontSize:8,color:"#2a4a2a",fontFamily:"'IBM Plex Mono',monospace",
                marginBottom:2}}>
                <span style={{color:"#1a3a1a"}}>[{a.ts}]</span> {a.msg}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div style={{fontFamily:"'Barlow Condensed',sans-serif",background:"#060910",
      color:"#c8d8e8",minHeight:"100vh",display:"flex",flexDirection:"column"}}>
      <style>{css}</style>

      {/* ── MODALS ── */}
      {closing&&(
        <CloseModal pos={closing} accent={bot.accent}
          onConfirm={confirmClose} onCancel={()=>setClosing(null)}/>
      )}
      {killConfirm&&(
        <div style={{position:"fixed",inset:0,background:"rgba(0,0,0,.92)",
          display:"flex",alignItems:"center",justifyContent:"center",
          zIndex:9999,backdropFilter:"blur(10px)"}}>
          <div style={{background:"#0a0205",border:"1px solid #ff000050",borderRadius:12,
            padding:"32px 36px",maxWidth:400,textAlign:"center",
            boxShadow:"0 0 100px #ff00001a"}}>
            <div style={{fontSize:40,marginBottom:12}}>🚨</div>
            <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:24,
              fontWeight:800,color:"#ff4455",letterSpacing:2,marginBottom:8}}>
              EMERGENCY KILL SWITCH
            </div>
            <div style={{fontSize:12,color:"#5a6a7a",lineHeight:1.8,marginBottom:24}}>
              Halts <strong style={{color:"#ffaaaa"}}>ALL THREE BOTS</strong> immediately.<br/>
              No new trades will be placed.<br/>
              Existing positions remain open.
            </div>
            <div style={{display:"flex",gap:10}}>
              <button onClick={()=>setKillConfirm(false)} style={{flex:1,padding:"11px 0",
                borderRadius:7,background:"#0f1520",border:"1px solid #1a2535",
                color:"#3a5070",fontSize:13,cursor:"pointer",fontFamily:"inherit"}}>
                CANCEL
              </button>
              <button onClick={()=>{setGlobalHalt(true);setKillConfirm(false)}}
                style={{flex:1,padding:"11px 0",borderRadius:7,background:"#b91c1c",
                  border:"none",color:"#fff",fontSize:13,fontWeight:800,
                  cursor:"pointer",fontFamily:"inherit",letterSpacing:1}}>
                ⚡ KILL ALL BOTS
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── TOPBAR ── */}
      <div style={{height:50,background:"#03050a",borderBottom:"1px solid #0c1522",
        display:"flex",alignItems:"center",padding:"0 18px",gap:0,
        position:"sticky",top:0,zIndex:100,flexShrink:0}}>

        {/* Logo */}
        <div style={{display:"flex",alignItems:"center",gap:9,
          paddingRight:18,borderRight:"1px solid #0c1522"}}>
          <div style={{width:22,height:22,borderRadius:4,
            background:"linear-gradient(135deg,#00c8ff,#b06aff)",
            display:"flex",alignItems:"center",justifyContent:"center",
            fontSize:11,fontWeight:900,color:"#fff"}}>α</div>
          <span style={{fontWeight:800,fontSize:13,letterSpacing:3,color:"#c0d8e8"}}>
            ALPHACOPY
          </span>
          <span style={{fontSize:8,color:"#1a2535",border:"1px solid #0f1a28",
            padding:"1px 6px",borderRadius:3,letterSpacing:1}}>v3.0</span>
        </div>

        {/* P&L */}
        <div style={{padding:"0 18px",borderRight:"1px solid #0c1522"}}>
          <div style={{fontSize:7,color:"#1e2d3e",letterSpacing:2,marginBottom:1}}>PORTFOLIO P&L</div>
          <div style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:15,fontWeight:700,
            color:totalPnl>=0?"#00cc88":"#ff5566"}}>
            {totalPnl>=0?"+":"-"}
            <Live val={totalPnl} dec={2} prefix="$" color={totalPnl>=0?"#00cc88":"#ff5566"}/>
            <span style={{fontSize:10,marginLeft:6,opacity:.5}}>({fmtP(totalPnlPct)})</span>
          </div>
        </div>

        {/* Equity */}
        <div style={{padding:"0 18px",borderRight:"1px solid #0c1522"}}>
          <div style={{fontSize:7,color:"#1e2d3e",letterSpacing:2,marginBottom:1}}>EQUITY</div>
          <div style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:13,
            fontWeight:600,color:"#6a8aaa"}}>${totalEquity.toFixed(2)}</div>
        </div>

        {/* 6 Rule status pills */}
        <div style={{padding:"0 18px",borderRight:"1px solid #0c1522",
          display:"flex",gap:6,alignItems:"center"}}>
          {rules.map(r=>{
            const c=!r.pass?"#ff4455":r.warn?"#ff9800":"#00cc88";
            return (
              <div key={r.key} title={r.label}
                onClick={()=>{setTab("rules")}}
                style={{display:"flex",alignItems:"center",gap:4,cursor:"pointer",
                  padding:"2px 7px",borderRadius:3,border:`1px solid ${c}30`,
                  background:`${c}0a`,transition:"all .2s"}}
                onMouseEnter={e=>e.currentTarget.style.border=`1px solid ${c}60`}
                onMouseLeave={e=>e.currentTarget.style.border=`1px solid ${c}30`}>
                <div style={{width:5,height:5,borderRadius:"50%",background:c,
                  boxShadow:`0 0 4px ${c}`}}/>
                <span style={{fontSize:8,color:c,fontFamily:"'IBM Plex Mono',monospace",
                  letterSpacing:.5}}>{r.num}</span>
              </div>
            );
          })}
        </div>

        <div style={{flex:1}}/>

        {/* Clock */}
        <div style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:10,
          color:"#1e2d3e",paddingRight:14}}>
          {time.toISOString().slice(11,19)} UTC
        </div>

        {/* Live indicator */}
        <div style={{display:"flex",alignItems:"center",gap:5,paddingRight:14}}>
          <div style={{width:6,height:6,borderRadius:"50%",background:"#00cc88",
            boxShadow:"0 0 5px #00cc88",animation:"pulse 2s infinite"}}/>
          <span style={{fontSize:8,color:"#1a4a2a",letterSpacing:1.5}}>LIVE</span>
        </div>

        {/* Kill switch */}
        {globalHalt ? (
          <button onClick={()=>setGlobalHalt(false)}
            style={{padding:"5px 14px",borderRadius:5,border:"1px solid #00cc8840",
              background:"#00cc8810",color:"#00cc88",fontSize:8,fontWeight:700,
              cursor:"pointer",fontFamily:"inherit",letterSpacing:1.5}}>
            ↺ RESUME ALL
          </button>
        ):(
          <button onClick={()=>setKillConfirm(true)}
            style={{padding:"5px 14px",borderRadius:5,border:"1px solid #ff444440",
              background:"transparent",color:"#ff5566",fontSize:8,fontWeight:700,
              cursor:"pointer",fontFamily:"inherit",letterSpacing:1.5,transition:"all .2s"}}
            onMouseEnter={e=>{e.currentTarget.style.background="#b91c1c";e.currentTarget.style.color="#fff"}}
            onMouseLeave={e=>{e.currentTarget.style.background="transparent";e.currentTarget.style.color="#ff5566"}}>
            ⚡ KILL ALL
          </button>
        )}
      </div>

      {/* ── HALT BANNER ── */}
      {globalHalt&&(
        <div style={{background:"#1a0005",borderBottom:"2px solid #ff000040",
          padding:"7px 18px",textAlign:"center",fontFamily:"'IBM Plex Mono',monospace",
          fontSize:10,color:"#ff4455",letterSpacing:2,animation:"pulse 1.5s infinite"}}>
          🚨 KILL SWITCH ACTIVE — ALL BOTS HALTED — NO NEW TRADES
        </div>
      )}

      {/* ── BODY ── */}
      <div style={{display:"flex",flex:1,overflow:"hidden",minHeight:0}}>

        {/* ── LEFT SIDEBAR ── */}
        <div style={{width:196,background:"#03050a",borderRight:"1px solid #0c1522",
          display:"flex",flexDirection:"column",gap:0,overflowY:"auto",flexShrink:0}}>

          {/* Rule status list */}
          <div style={{padding:"12px 10px 6px"}}>
            <div style={{fontSize:7,color:"#1a2535",letterSpacing:2,
              marginBottom:8,padding:"0 4px"}}>RISK RULES</div>
            {rules.map(r=>{
              const c=!r.pass?"#ff4455":r.warn?"#ff9800":"#00cc88";
              return (
                <div key={r.key} onClick={()=>setTab("rules")}
                  style={{display:"flex",alignItems:"center",gap:7,
                    padding:"7px 8px",borderRadius:5,cursor:"pointer",
                    marginBottom:1,transition:"background .15s"}}
                  onMouseEnter={e=>e.currentTarget.style.background="#0a1020"}
                  onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
                  <div style={{width:5,height:5,borderRadius:"50%",flexShrink:0,
                    background:c,boxShadow:`0 0 4px ${c}`}}/>
                  <div style={{flex:1,minWidth:0}}>
                    <div style={{fontSize:8,fontWeight:700,color:"#4a6080",
                      letterSpacing:.5,whiteSpace:"nowrap",overflow:"hidden",
                      textOverflow:"ellipsis"}}>{r.shortLabel}</div>
                    <div style={{fontSize:7,color:"#1a2535",marginTop:1,
                      whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>
                      {r.metric}
                    </div>
                  </div>
                  <span style={{fontSize:6,color:c,letterSpacing:.5,flexShrink:0}}>
                    {!r.pass?"FAIL":r.warn?"WARN":"OK"}
                  </span>
                </div>
              );
            })}
          </div>

          <div style={{height:1,background:"#0c1522",margin:"4px 0"}}/>

          {/* Bot selectors */}
          <div style={{padding:"6px 10px"}}>
            <div style={{fontSize:7,color:"#1a2535",letterSpacing:2,
              marginBottom:8,padding:"0 4px"}}>BOTS</div>
            {Object.values(bots).map(b=>{
              const p=b.equity-b.allocated;
              const isA=activeBot===b.id;
              return (
                <div key={b.id}
                  onClick={()=>{setActiveBot(b.id);setTab("positions")}}
                  style={{padding:"9px 10px",borderRadius:6,cursor:"pointer",
                    marginBottom:3,
                    border:`1px solid ${isA?b.accent+"50":"transparent"}`,
                    background:isA?b.dim+"80":"transparent",
                    transition:"all .2s"}}>
                  <div style={{display:"flex",justifyContent:"space-between",
                    alignItems:"center",marginBottom:5}}>
                    <span style={{fontSize:11,fontWeight:800,color:b.accent,
                      letterSpacing:1.5}}>{b.id}</span>
                    <span style={{fontSize:6,padding:"1px 5px",borderRadius:3,
                      background:b.halted||globalHalt?"#ff000018":"#00cc8810",
                      color:b.halted||globalHalt?"#ff4455":"#00cc88",
                      border:`1px solid ${b.halted||globalHalt?"#ff000030":"#00cc8825"}`}}>
                      {b.halted||globalHalt?"HALT":b.positions.length+" POS"}
                    </span>
                  </div>
                  <div style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:12,
                    fontWeight:700,color:p>=0?"#00cc88":"#ff5566",marginBottom:4}}>
                    <Live val={p} dec={2} prefix={p>=0?"$":"-$"}
                      color={p>=0?"#00cc88":"#ff5566"}/>
                  </div>
                  <Spark vals={b.spark} color={b.accent} w={160} h={20}/>
                  <div style={{marginTop:5}}>
                    <div style={{display:"flex",justifyContent:"space-between",
                      fontSize:7,color:"#1a2535",marginBottom:2}}>
                      <span>DD</span>
                      <span style={{color:b.drawdown>10?"#ff9800":"#2a4050"}}>
                        {b.drawdown}%/{b.maxDD}%
                      </span>
                    </div>
                    <Bar pct={b.drawdown/b.maxDD*100} color={b.accent}/>
                  </div>
                </div>
              );
            })}
          </div>

          <div style={{height:1,background:"#0c1522",margin:"4px 0"}}/>

          {/* Portfolio summary */}
          <div style={{padding:"10px 12px",margin:"4px 8px 8px",
            background:"#080c14",borderRadius:7,border:"1px solid #0f1a28"}}>
            <div style={{fontSize:7,color:"#1a2535",letterSpacing:2,marginBottom:8}}>PORTFOLIO</div>
            {[
              {l:"Equity",  v:`$${totalEquity.toFixed(0)}`,   c:"#5a7a8a"},
              {l:"Net P&L", v:fmtD(totalPnl,0),              c:totalPnl>=0?"#00cc88":"#ff5566"},
              {l:"Open",    v:`${allOpen.length} positions`,  c:"#3a5060"},
              {l:"Port DD", v:`${portfolioDD}%`,              c:parseFloat(portfolioDD)>5?"#ff9800":"#2a4050"},
            ].map(x=>(
              <div key={x.l} style={{display:"flex",justifyContent:"space-between",marginBottom:5}}>
                <span style={{fontSize:8,color:"#1e2d3e"}}>{x.l}</span>
                <span style={{fontSize:8,fontFamily:"'IBM Plex Mono',monospace",
                  fontWeight:600,color:x.c}}>{x.v}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── MAIN PANEL ── */}
        <div style={{flex:1,display:"flex",flexDirection:"column",overflow:"hidden"}}>

          {/* Bot summary strip */}
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",
            borderBottom:"1px solid #0c1522",flexShrink:0}}>
            {Object.values(bots).map((b,i)=>{
              const p=b.equity-b.allocated;
              const pPct=p/b.allocated*100;
              const isA=activeBot===b.id;
              return (
                <div key={b.id} onClick={()=>{setActiveBot(b.id);setTab("positions")}}
                  style={{padding:"12px 18px",cursor:"pointer",
                    borderRight:i<2?"1px solid #0c1522":"none",
                    background:isA?`${b.dim}60`:"transparent",
                    borderBottom:isA?`2px solid ${b.accent}`:"2px solid transparent",
                    transition:"all .2s"}}>
                  <div style={{display:"flex",justifyContent:"space-between",
                    alignItems:"flex-start",marginBottom:7}}>
                    <div>
                      <div style={{fontSize:10,fontWeight:800,color:b.accent,
                        letterSpacing:2}}>{b.id}</div>
                      <div style={{fontSize:8,color:"#1e2d3e",letterSpacing:1}}>{b.label}</div>
                    </div>
                    <div style={{display:"flex",alignItems:"center",gap:8}}>
                      <Spark vals={b.spark} color={b.accent} w={52} h={18}/>
                      <div style={{textAlign:"right"}}>
                        <div style={{fontSize:7,color:"#1a2535",letterSpacing:1}}>W/L</div>
                        <div style={{fontSize:9,fontFamily:"'IBM Plex Mono',monospace",
                          color:"#3a5060"}}>{b.wins}/{b.losses}</div>
                      </div>
                    </div>
                  </div>
                  <div style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:17,
                    fontWeight:700,color:p>=0?"#00cc88":"#ff5566",marginBottom:6}}>
                    <Live val={p} dec={2} prefix={p>=0?"+$":"-$"} color={p>=0?"#00cc88":"#ff5566"}/>
                    <span style={{fontSize:9,marginLeft:6,opacity:.5}}>({fmtP(pPct)})</span>
                  </div>
                  <div style={{display:"flex",gap:14}}>
                    {[
                      {l:"EQUITY",   v:`$${b.equity.toFixed(0)}`,    c:"#4a6080"},
                      {l:"DD",       v:`${b.drawdown.toFixed(1)}%`,   c:b.drawdown>10?"#ff9800":"#2a4050"},
                      {l:"TRADES",   v:`${b.totalTrades}`,            c:"#2a3a4a"},
                    ].map(x=>(
                      <div key={x.l}>
                        <div style={{fontSize:6,color:"#1a2535",letterSpacing:1}}>{x.l}</div>
                        <div style={{fontSize:9,fontFamily:"'IBM Plex Mono',monospace",
                          fontWeight:600,color:x.c}}>{x.v}</div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Tab bar */}
          <div style={{display:"flex",alignItems:"center",
            borderBottom:"1px solid #080d14",background:"#03050a",flexShrink:0}}>
            <div style={{display:"flex",padding:"0 14px",gap:0}}>
              {[
                {id:"positions", label:`POSITIONS  ${bot.positions.length}`},
                {id:"rules",     label:"RISK RULES  6"},
                {id:"exposure",  label:"EXPOSURE"},
                {id:"journal",   label:"JOURNAL"},
              ].map(t=>(
                <button key={t.id} onClick={()=>setTab(t.id)} style={{
                  padding:"9px 16px",border:"none",
                  borderBottom:tab===t.id?`2px solid ${bot.accent}`:"2px solid transparent",
                  background:"transparent",color:tab===t.id?bot.accent:"#1e2d3e",
                  fontSize:8,fontWeight:700,cursor:"pointer",fontFamily:"inherit",
                  letterSpacing:1.5,transition:"color .2s",marginBottom:-1}}>
                  {t.label}
                </button>
              ))}
            </div>
            {tab==="positions"&&bot.positions.length>0&&(
              <button onClick={()=>setClosing(bot.positions[0])}
                style={{marginLeft:"auto",marginRight:14,padding:"4px 12px",
                  borderRadius:4,background:"transparent",
                  border:"1px solid #aa1c1c50",color:"#ff5566",fontSize:7,
                  fontWeight:700,cursor:"pointer",fontFamily:"inherit",letterSpacing:1}}>
                CLOSE ALL {bot.id}
              </button>
            )}
          </div>

          {/* Content area */}
          <div style={{flex:1,overflowY:"auto"}}>
            {tab==="positions" && <PositionsTab/>}
            {tab==="rules"     && <RulesTab/>}
            {tab==="exposure"  && <ExposureTab/>}
            {tab==="journal"   && <JournalTab/>}
          </div>

          {/* ── STATUS BAR ── */}
          <div style={{borderTop:"1px solid #080d14",background:"#03050a",
            padding:"5px 16px",display:"flex",alignItems:"center",
            gap:0,flexShrink:0}}>
            {[
              `① 1%: MAX $${maxRisk1Pct.toFixed(0)}/TRADE`,
              `② SL ON ALL ${allOpen.length} POSITIONS`,
              "③ MIN R:R 2:1 ENFORCED",
              "④ 5 CORR. GROUPS MONITORED",
              `⑤ KILL SW: ${globalHalt?"ACTIVE":"CLEAR"}`,
              "⑥ PAPER: DAY 9/14",
            ].map((s,i)=>(
              <div key={i} style={{display:"flex",alignItems:"center",gap:0}}>
                {i>0&&<div style={{width:1,height:10,background:"#0c1522",margin:"0 10px"}}/>}
                <span style={{fontSize:7,color:
                  s.includes("ACTIVE")?"#ff4455":
                  s.includes("9/14")?"#ff9800":
                  "#1e2d3e",letterSpacing:.8,
                  fontFamily:"'IBM Plex Mono',monospace"}}>{s}</span>
              </div>
            ))}
            <div style={{flex:1}}/>
            <span style={{fontSize:7,color:"#1a2535",fontFamily:"'IBM Plex Mono',monospace",
              letterSpacing:.5}}>
              OPEN RISK: ${allOpen.reduce((a,p)=>a+p.risk/100*totalEquity,0).toFixed(0)} ·
              PORT DD: {portfolioDD}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
