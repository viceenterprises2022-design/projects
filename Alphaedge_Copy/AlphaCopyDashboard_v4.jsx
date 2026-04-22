import { useState, useEffect, useRef, useCallback } from "react";

const TOTAL_ALLOCATED = 30000;

const INITIAL_BOTS = {
  HL: {
    id:"HL", label:"HYPERLIQUID", accent:"#00c8ff", dim:"#001f2e",
    equity:10847.32, allocated:10000, peak:11200,
    wins:31, losses:16, totalTrades:47,
    dailyTrades:8, maxDailyTrades:50,
    consecLosses:1, maxConsec:5,
    drawdown:3.2, maxDD:20, dailyLoss:0.4, maxDailyLoss:7,
    halted:false,
    spark:[9800,9950,10200,10050,10600,10750,10847],
    positions:[
      { id:"hl1", sym:"BTC-PERP",  side:"LONG",  entry:94210, ltp:96540, size:893, sl:89499, tp:108341, risk:0.97, rr:2.8, source:"0xA3f1…", age:"2h 14m", group:"BTC_CORE",  leverage:3 },
      { id:"hl2", sym:"ETH-PERP",  side:"SHORT", entry:3410,  ltp:3298,  size:307, sl:3614,  tp:2996,   risk:0.82, rr:2.0, source:"0xB7c2…", age:"4h 32m", group:"ETH_CORE",  leverage:2 },
    ],
  },
  BN: {
    id:"BN", label:"BINANCE", accent:"#f0b90b", dim:"#1e1800",
    equity:9612.18, allocated:10000, peak:10100,
    wins:18, losses:15, totalTrades:33,
    dailyTrades:5, maxDailyTrades:50,
    consecLosses:2, maxConsec:5,
    drawdown:4.1, maxDD:20, dailyLoss:1.2, maxDailyLoss:7,
    halted:false,
    spark:[10100,10050,9900,9750,9800,9650,9612],
    positions:[
      { id:"bn1", sym:"SOLUSDT", side:"LONG", entry:178.4, ltp:182.1, size:308, sl:168.0, tp:198.0, risk:0.93, rr:1.9, source:"UID:9A8F…", age:"6h 08m", group:"LARGE_CAP", leverage:2 },
    ],
  },
  PM: {
    id:"PM", label:"POLYMARKET", accent:"#b06aff", dim:"#1a0028",
    equity:10291.55, allocated:10000, peak:10291.55,
    wins:14, losses:8, totalTrades:22,
    dailyTrades:3, maxDailyTrades:50,
    consecLosses:0, maxConsec:5,
    drawdown:0, maxDD:20, dailyLoss:0, maxDailyLoss:7,
    halted:false,
    spark:[10000,10050,10200,10150,10290,10305,10291],
    positions:[
      { id:"pm1", sym:"BTC>$100k",  side:"YES", entry:0.61, ltp:0.74, size:400, sl:0.31, tp:0.92, risk:1.07, rr:2.1, source:"0xFr3n…", age:"2d", group:"PREDICTION", leverage:1 },
      { id:"pm2", sym:"Fed Cut Q1", side:"NO",  entry:0.38, ltp:0.29, size:250, sl:0.65, tp:0.10, risk:0.72, rr:2.0, source:"0xWhal…", age:"3d", group:"MACRO_POLY",  leverage:1 },
    ],
  },
};

const JOURNAL = [
  { id:1, bot:"HL", sym:"BTC-PERP",   side:"LONG",  entry:94210, exit:96540, size:893, pnl:431.2, rr:"2.8R", risk:"0.97%", status:"OPEN",    ts:"09:14" },
  { id:2, bot:"BN", sym:"SOLUSDT",    side:"LONG",  entry:174.2, exit:182.1, size:308, pnl:138.6, rr:"1.9R", risk:"0.93%", status:"OPEN",    ts:"08:52" },
  { id:3, bot:"PM", sym:"BTC>$100k",  side:"YES",   entry:0.61,  exit:0.74,  size:400, pnl:85.2,  rr:"2.1R", risk:"1.07%", status:"OPEN",    ts:"2d ago" },
  { id:4, bot:"HL", sym:"AVAX-PERP",  side:"LONG",  entry:38.4,  exit:42.1,  size:500, pnl:48.2,  rr:"2.4R", risk:"0.88%", status:"CLOSED",  ts:"Yesterday" },
  { id:5, bot:"BN", sym:"BNBUSDT",    side:"LONG",  entry:612,   exit:591,   size:600, pnl:-20.5, rr:"-1.0R",risk:"0.90%", status:"STOPPED", ts:"Yesterday" },
  { id:6, bot:"HL", sym:"SOL-PERP",   side:"SHORT", entry:185,   exit:179.2, size:420, pnl:13.2,  rr:"0.7R", risk:"0.75%", status:"CLOSED",  ts:"2d ago" },
];

const CORR_GROUPS = [
  { name:"BTC_CORE",   pct:12.5, limit:25 },
  { name:"ETH_CORE",   pct:6.1,  limit:25 },
  { name:"LARGE_CAP",  pct:3.2,  limit:25 },
  { name:"PREDICTION", pct:2.7,  limit:25 },
  { name:"MACRO_POLY", pct:1.9,  limit:25 },
];

// ── utils ─────────────────────────────────────────────────────────────────
function calcPnl(p) {
  return ((p.side==="LONG"||p.side==="YES")?1:-1) * (p.ltp-p.entry)/p.entry * p.size;
}
function fmtD(v,dec=2){ return (v>=0?"+":"-")+"$"+Math.abs(v).toFixed(dec).replace(/\B(?=(\d{3})+(?!\d))/g,","); }
function fmtP(v){ return (v>=0?"+":"")+v.toFixed(2)+"%" }

// ── Sparkline ─────────────────────────────────────────────────────────────
function Spark({vals,color,w=72,h=28}){
  if(!vals||vals.length<2) return null;
  const mx=Math.max(...vals),mn=Math.min(...vals),rng=mx-mn||1;
  const pts=vals.map((v,i)=>`${i/(vals.length-1)*w},${h-(v-mn)/rng*h}`).join(" ");
  const gid="g"+color.replace(/[^a-z0-9]/gi,"");
  return(
    <svg width={w} height={h} style={{display:"block",overflow:"visible"}}>
      <defs><linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor={color} stopOpacity="0.3"/>
        <stop offset="100%" stopColor={color} stopOpacity="0"/>
      </linearGradient></defs>
      <polygon points={pts+` ${w},${h} 0,${h}`} fill={`url(#${gid})`}/>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round"/>
    </svg>
  );
}

// ── Live animated number ───────────────────────────────────────────────────
function Live({val,dec=2,prefix="$",color="#c8d8e8"}){
  const [v,setV]=useState(val);
  const [flash,setFlash]=useState(0);
  const prev=useRef(val);
  useEffect(()=>{
    if(prev.current===val) return;
    setFlash(val>prev.current?1:-1);
    prev.current=val; setV(val);
    const t=setTimeout(()=>setFlash(0),500);
    return()=>clearTimeout(t);
  },[val]);
  const c=flash===1?"#00ff99":flash===-1?"#ff3355":color;
  return <span style={{color:c,transition:"color .3s",fontVariantNumeric:"tabular-nums"}}>{prefix}{Math.abs(v).toFixed(dec)}</span>;
}

// ── Progress bar ──────────────────────────────────────────────────────────
function Bar({pct,color,h=5,bg="#0e1420"}){
  return(
    <div style={{height:h,background:bg,borderRadius:h,overflow:"hidden"}}>
      <div style={{width:`${Math.min(100,pct)}%`,height:"100%",background:color,borderRadius:h,transition:"width .5s"}}/>
    </div>
  );
}

// ── Risk donut gauge ──────────────────────────────────────────────────────
function RiskGauge({val,max=2,size=40}){
  const pct=Math.min(1,val/max);
  const c=val>1.8?"#ff3355":val>1.2?"#ff9800":"#00cc88";
  const r=15,cx=size/2,cy=size/2,circ=2*Math.PI*r;
  return(
    <svg width={size} height={size}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#0f1620" strokeWidth="4"/>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={c} strokeWidth="4"
        strokeDasharray={`${pct*circ} ${circ}`} strokeLinecap="round"
        transform={`rotate(-90 ${cx} ${cy})`}/>
      <text x={cx} y={cy+1} textAnchor="middle" dominantBaseline="middle"
        fontSize="10" fontWeight="700" fill={c} fontFamily="monospace">{val}</text>
    </svg>
  );
}

// ── Close modal ───────────────────────────────────────────────────────────
function CloseModal({pos,accent,onConfirm,onCancel}){
  const p=calcPnl(pos);
  return(
    <div style={{position:"fixed",inset:0,background:"rgba(0,0,0,.9)",display:"flex",alignItems:"center",justifyContent:"center",zIndex:9999,backdropFilter:"blur(8px)"}}>
      <div style={{background:"#0c1018",border:`1px solid ${accent}50`,borderRadius:14,padding:"32px 36px",minWidth:400,boxShadow:`0 0 80px ${accent}18`}}>
        <div style={{fontSize:12,color:accent,letterSpacing:3,marginBottom:12,fontFamily:"monospace",textTransform:"uppercase"}}>Close Position</div>
        <div style={{fontFamily:"monospace",fontSize:26,fontWeight:700,color:"#e0ecff",marginBottom:6}}>{pos.sym}</div>
        <div style={{fontSize:15,color:"#5a6e82",marginBottom:22}}>{pos.side} · Entry {pos.entry} · Current {pos.ltp.toFixed(pos.ltp>10?2:4)}</div>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr 1fr",gap:14,marginBottom:22}}>
          {[{l:"EST. P&L",v:fmtD(p,2),c:p>=0?"#00cc88":"#ff4455"},{l:"RISK",v:pos.risk+"%",c:"#8a9aaa"},{l:"R:R",v:""+pos.rr,c:"#8a9aaa"},{l:"SIZE",v:"$"+pos.size,c:"#8a9aaa"}].map(x=>(
            <div key={x.l}>
              <div style={{fontSize:12,color:"#3a4e62",letterSpacing:1,marginBottom:6}}>{x.l}</div>
              <div style={{fontFamily:"monospace",fontSize:19,fontWeight:700,color:x.c}}>{x.v}</div>
            </div>
          ))}
        </div>
        <div style={{fontSize:14,color:"#e08020",background:"#e0802012",border:"1px solid #e0802030",borderRadius:7,padding:"10px 14px",marginBottom:22}}>
          ⚠ MARKET ORDER — executes immediately. Slippage risk applies.
        </div>
        <div style={{display:"flex",gap:12}}>
          <button onClick={onCancel} style={{flex:1,padding:"12px 0",borderRadius:8,background:"#0f1520",border:"1px solid #1a2535",color:"#5a7090",fontSize:15,cursor:"pointer",fontFamily:"inherit"}}>Cancel</button>
          <button onClick={()=>onConfirm(pos)} style={{flex:1,padding:"12px 0",borderRadius:8,background:"#b91c1c",border:"none",color:"#fff",fontSize:15,fontWeight:700,cursor:"pointer",fontFamily:"inherit"}}>CLOSE POSITION</button>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// ROOT DASHBOARD
// ═══════════════════════════════════════════════════════════════════════════
export default function Dashboard(){
  const [bots,setBots]             = useState(INITIAL_BOTS);
  const [activeBot,setActiveBot]   = useState("HL");
  const [tab,setTab]               = useState("positions");
  const [closing,setClosing]       = useState(null);
  const [killConfirm,setKillConfirm] = useState(false);
  const [globalHalt,setGlobalHalt] = useState(false);
  const [jFilter,setJFilter]       = useState("ALL");
  const [time,setTime]             = useState(new Date());

  // live price simulation
  useEffect(()=>{
    const iv=setInterval(()=>{
      setBots(prev=>{
        const n={...prev};
        Object.keys(n).forEach(k=>{
          n[k]={...n[k],positions:n[k].positions.map(p=>({...p,
            ltp:p.ltp>10?+(p.ltp*(1+(Math.random()-.5)*.001)).toFixed(2):+(p.ltp*(1+(Math.random()-.5)*.003)).toFixed(4)
          }))};
        });
        return n;
      });
      setTime(new Date());
    },1800);
    return()=>clearInterval(iv);
  },[]);

  const totalEquity = Object.values(bots).reduce((a,b)=>a+b.equity,0);
  const totalPnl    = totalEquity - TOTAL_ALLOCATED;
  const totalPnlPct = totalPnl/TOTAL_ALLOCATED*100;
  const allOpen     = Object.values(bots).flatMap(b=>b.positions);
  const maxRisk1    = totalEquity*0.01;
  const maxRisk2    = totalEquity*0.02;
  const portDD      = ((Object.values(bots).reduce((a,b)=>a+b.peak,0)-totalEquity)/TOTAL_ALLOCATED*100).toFixed(1);
  const bot         = bots[activeBot];

  const confirmClose=useCallback(pos=>{
    setBots(prev=>{
      const n={...prev};
      Object.keys(n).forEach(k=>{n[k]={...n[k],positions:n[k].positions.filter(p=>p.id!==pos.id)};});
      return n;
    });
    setClosing(null);
  },[]);

  const RULES=[
    {num:"①",key:"r1",label:"1% – 2% Risk Rule",   sc:"OK",   detail:`Avg ${(allOpen.reduce((a,p)=>a+p.risk,0)/Math.max(allOpen.length,1)).toFixed(2)}% / trade · Max $${maxRisk1.toFixed(0)}`},
    {num:"②",key:"r2",label:"Mandatory Stop-Loss",  sc:"OK",   detail:`${allOpen.length} of ${allOpen.length} positions protected`},
    {num:"③",key:"r3",label:"Min R:R  1 : 2",       sc:"WARN", detail:"SOL at 1.9 — approaching minimum"},
    {num:"④",key:"r4",label:"Diversification",       sc:"WARN", detail:"BTC_CORE 12.5% of 25% limit"},
    {num:"⑤",key:"r5",label:"Kill Switches",         sc:globalHalt?"HALT":"OK", detail:globalHalt?"PORTFOLIO HALT ACTIVE":"All thresholds clear"},
    {num:"⑥",key:"r6",label:"Algo Validated",        sc:"FAIL", detail:"Paper trading: Day 9 of 14"},
  ];
  const SC={OK:{bg:"#001a0e",bd:"#00cc8830",tx:"#00cc88"},WARN:{bg:"#1a1000",bd:"#ff980030",tx:"#ff9800"},FAIL:{bg:"#1a0008",bd:"#ff445530",tx:"#ff4455"},HALT:{bg:"#220000",bd:"#ff223350",tx:"#ff2233"}};

  const CSS=`
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Sora:wght@400;500;600;700;800&display=swap');
    *{box-sizing:border-box;margin:0;padding:0}
    ::-webkit-scrollbar{width:4px;height:4px}
    ::-webkit-scrollbar-track{background:#060910}
    ::-webkit-scrollbar-thumb{background:#1a2535;border-radius:2px}
    @keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
    @keyframes fadeUp{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:translateY(0)}}
    .fade{animation:fadeUp .22s ease forwards}
    .row:hover{background:#0d1525!important}
    button:focus{outline:none}
  `;

  // ── POSITIONS TAB ──────────────────────────────────────────────────────
  function TabPositions(){
    if(!bot.positions.length)
      return <div style={{padding:60,textAlign:"center",fontSize:17,color:"#2a3848",fontFamily:"monospace",letterSpacing:2}}>NO OPEN POSITIONS</div>;
    return(
      <div className="fade" style={{overflowX:"auto"}}>
        <table style={{width:"100%",borderCollapse:"collapse",minWidth:1000}}>
          <thead>
            <tr style={{borderBottom:"1px solid #0f1828"}}>
              {["Symbol","Side","Entry / LTP","Size","Stop-Loss ②","Take-Profit","Risk % ①","R:R ③","SL → TP","Corr Group ④","Held","P&L",""].map(h=>(
                <th key={h} style={{padding:"11px 13px",fontSize:13,fontFamily:"'Sora',sans-serif",
                  color:h.includes("①")||h.includes("②")||h.includes("③")||h.includes("④")?"#4a90b8":"#3a5060",
                  fontWeight:600,textAlign:"left",whiteSpace:"nowrap",letterSpacing:.3}}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {bot.positions.map(p=>{
              const P=calcPnl(p);
              const isLong=p.side==="LONG"||p.side==="YES";
              const rrNum=+p.rr;
              const rrCol=rrNum>=2?"#00cc88":rrNum>=1.5?"#ff9800":"#ff4455";
              const riskCol=p.risk>1.8?"#ff4455":p.risk>1.2?"#ff9800":"#00c8ff";
              const slDist=Math.abs(p.ltp-p.sl)/p.ltp*100;
              const prog=Math.abs(p.tp-p.sl)>0?Math.min(100,Math.abs(p.ltp-p.sl)/Math.abs(p.tp-p.sl)*100):50;
              return(
                <tr key={p.id} className="row" style={{borderBottom:"1px solid #090d14",transition:"background .15s"}}>
                  {/* Symbol */}
                  <td style={{padding:"13px 13px"}}>
                    <div style={{fontFamily:"monospace",fontWeight:700,fontSize:16,color:"#cce0f8"}}>{p.sym}</div>
                    <div style={{fontSize:13,color:"#2a3e52",marginTop:3}}>{p.source} · {p.leverage}×</div>
                  </td>
                  {/* Side badge */}
                  <td style={{padding:"13px 13px"}}>
                    <span style={{fontSize:13,fontWeight:700,padding:"4px 12px",borderRadius:5,
                      background:isLong?"#00cc8818":"#ff445518",color:isLong?"#00cc88":"#ff6677",
                      border:`1px solid ${isLong?"#00cc8845":"#ff445545"}`}}>{p.side}</span>
                  </td>
                  {/* Entry / LTP */}
                  <td style={{padding:"13px 13px"}}>
                    <div style={{fontSize:14,color:"#4a6278",fontFamily:"monospace",marginBottom:3}}>{p.entry}</div>
                    <div style={{fontSize:17,fontWeight:700,fontFamily:"monospace",color:P>=0?"#00cc88":"#ff5566"}}>
                      <Live val={p.ltp} dec={p.ltp>10?2:4} prefix="" color={P>=0?"#00cc88":"#ff5566"}/>
                    </div>
                  </td>
                  {/* Size */}
                  <td style={{padding:"13px 13px",fontFamily:"monospace",fontSize:15,color:"#7a8a9a"}}>${p.size}</td>
                  {/* SL */}
                  <td style={{padding:"13px 13px",fontFamily:"monospace",fontSize:15,color:"#cc4455",fontWeight:600}}>{p.sl}</td>
                  {/* TP */}
                  <td style={{padding:"13px 13px",fontFamily:"monospace",fontSize:15,color:"#33aa77",fontWeight:600}}>{p.tp}</td>
                  {/* Risk gauge */}
                  <td style={{padding:"13px 13px"}}>
                    <div style={{display:"flex",alignItems:"center",gap:8}}>
                      <RiskGauge val={p.risk} max={2} size={40}/>
                      <div>
                        <div style={{fontFamily:"monospace",fontSize:15,fontWeight:700,color:riskCol}}>{p.risk}%</div>
                        <div style={{fontSize:12,color:"#2a3e52",marginTop:2}}>${(p.risk/100*totalEquity).toFixed(0)} risked</div>
                      </div>
                    </div>
                  </td>
                  {/* R:R */}
                  <td style={{padding:"13px 13px"}}>
                    <div style={{fontFamily:"monospace",fontSize:20,fontWeight:700,color:rrCol}}>{p.rr}</div>
                    <div style={{fontSize:12,marginTop:3,color:rrNum>=2?"#00884466":"#ff440066"}}>{rrNum>=2?"✓ Min met":"⚠ Below 2:1"}</div>
                  </td>
                  {/* SL→TP bar */}
                  <td style={{padding:"13px 13px",minWidth:130}}>
                    <div style={{display:"flex",justifyContent:"space-between",fontSize:12,color:"#2a3e52",marginBottom:5}}>
                      <span style={{color:"#cc4455"}}>SL</span>
                      <span>{slDist.toFixed(1)}% away</span>
                      <span style={{color:"#33aa77"}}>TP</span>
                    </div>
                    <div style={{height:7,background:"#0a0f1a",borderRadius:4,position:"relative",overflow:"hidden"}}>
                      <div style={{height:"100%",borderRadius:4,background:`linear-gradient(90deg,#cc4455,${bot.accent},#33aa77)`,width:`${prog}%`,transition:"width .4s"}}/>
                    </div>
                    <div style={{fontSize:12,color:"#1e2d3e",marginTop:4,textAlign:"center"}}>{prog.toFixed(0)}% of range</div>
                  </td>
                  {/* Corr group */}
                  <td style={{padding:"13px 13px"}}>
                    <span style={{fontSize:13,padding:"4px 10px",borderRadius:5,background:"#0a1020",border:"1px solid #1a2535",color:"#4a6080"}}>{p.group}</span>
                  </td>
                  {/* Age */}
                  <td style={{padding:"13px 13px",fontFamily:"monospace",fontSize:14,color:"#2a3e52",textAlign:"center"}}>{p.age}</td>
                  {/* P&L */}
                  <td style={{padding:"13px 13px",textAlign:"right"}}>
                    <div style={{fontFamily:"monospace",fontSize:18,fontWeight:700,color:P>=0?"#00cc88":"#ff5566"}}>{fmtD(P)}</div>
                    <div style={{fontSize:13,marginTop:3,color:P>=0?"#008844":"#ff4444"}}>{fmtP(P/p.size*100)}</div>
                  </td>
                  {/* Close */}
                  <td style={{padding:"13px 10px"}}>
                    <button onClick={()=>setClosing(p)}
                      style={{padding:"7px 16px",borderRadius:6,background:"transparent",border:"1px solid #aa1c1c80",color:"#ee5566",fontSize:13,fontWeight:700,cursor:"pointer",fontFamily:"inherit",transition:"all .2s"}}
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
      </div>
    );
  }

  // ── RISK RULES TAB ──────────────────────────────────────────────────────
  function TabRules(){
    return(
      <div className="fade" style={{padding:20,display:"flex",flexDirection:"column",gap:16}}>
        {/* 6 rule cards */}
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:12}}>
          {RULES.map(r=>{
            const s=SC[r.sc];
            return(
              <div key={r.key} style={{background:s.bg,border:`1px solid ${s.bd}`,borderRadius:10,padding:"20px 22px",position:"relative",overflow:"hidden"}}>
                <div style={{position:"absolute",top:0,left:0,right:0,height:2,background:`linear-gradient(90deg,transparent,${s.tx}80,transparent)`}}/>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:12}}>
                  <span style={{fontFamily:"monospace",fontSize:26,color:s.tx,opacity:.5,lineHeight:1}}>{r.num}</span>
                  <span style={{fontSize:12,padding:"4px 12px",borderRadius:4,color:s.tx,border:`1px solid ${s.bd}`,fontWeight:700,letterSpacing:1}}>{r.sc}</span>
                </div>
                <div style={{fontFamily:"'Sora',sans-serif",fontSize:16,fontWeight:700,color:"#c8d8e8",marginBottom:6}}>{r.label}</div>
                <div style={{fontSize:14,color:s.tx,fontFamily:"monospace",lineHeight:1.5}}>{r.detail}</div>
              </div>
            );
          })}
        </div>

        {/* 1% sizing calculator */}
        <div style={{background:"#06090f",border:"1px solid #0e1828",borderRadius:10,padding:"20px 22px"}}>
          <div style={{fontSize:14,color:"#2a5070",letterSpacing:1,marginBottom:16,fontFamily:"'Sora',sans-serif",fontWeight:700}}>① POSITION SIZING — 1% RISK RULE</div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:12,marginBottom:16}}>
            {[
              {l:"Portfolio Equity",  v:`$${totalEquity.toFixed(0)}`,                       c:"#7a9aaa"},
              {l:"1% Max Risk/Trade", v:`$${maxRisk1.toFixed(0)}`,                           c:"#00cc88"},
              {l:"2% Hard Cap",       v:`$${maxRisk2.toFixed(0)}`,                           c:"#ff9800"},
              {l:"Max Position Size", v:`$${Math.min(totalEquity*.15,5000).toFixed(0)}`,     c:"#b06aff"},
            ].map(x=>(
              <div key={x.l} style={{background:"#09101a",border:"1px solid #0f1a28",borderRadius:8,padding:"16px 18px"}}>
                <div style={{fontSize:13,color:"#2a3e52",letterSpacing:.3,marginBottom:8}}>{x.l}</div>
                <div style={{fontFamily:"monospace",fontSize:24,fontWeight:700,color:x.c}}>{x.v}</div>
              </div>
            ))}
          </div>
          <div style={{background:"#040810",border:"1px solid #0a1020",borderRadius:7,padding:"13px 16px",fontFamily:"monospace",fontSize:14,color:"#3a5070",lineHeight:1.9}}>
            <span style={{color:"#4a7090"}}>Example: </span>
            BTC @ $95,000 · SL $90,250 (−5%) → Size = ${(maxRisk1/0.05).toFixed(0)} · Risk at stake = ${maxRisk1.toFixed(0)}
            <span style={{color:"#00cc8899"}}> · R:R 2:1 → TP $104,750  ✓</span>
          </div>
        </div>

        {/* Kill switch monitors */}
        <div style={{background:"#06090f",border:"1px solid #0e1828",borderRadius:10,padding:"20px 22px"}}>
          <div style={{fontSize:14,color:"#2a5070",letterSpacing:1,marginBottom:16,fontFamily:"'Sora',sans-serif",fontWeight:700}}>⑤ KILL SWITCH THRESHOLDS — LIVE</div>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr 1fr",gap:12}}>
            {[
              {l:"Portfolio DD",        used:parseFloat(portDD),     limit:15, col:"#b06aff"},
              {l:"Daily Loss (Port.)",  used:0,                      limit:5,  col:"#ff4455"},
              {l:"HL  Consec. Losses",  used:bots.HL.consecLosses,  limit:5,  col:"#00c8ff",isCount:true},
              {l:"BN  Consec. Losses",  used:bots.BN.consecLosses,  limit:5,  col:"#f0b90b",isCount:true},
              {l:"HL  Daily Loss %",    used:bots.HL.dailyLoss,     limit:7,  col:"#00c8ff"},
              {l:"BN  Daily Loss %",    used:bots.BN.dailyLoss,     limit:7,  col:"#f0b90b"},
              {l:"HL  Trades Today",    used:bots.HL.dailyTrades,   limit:50, col:"#00c8ff",isCount:true},
              {l:"BN  Trades Today",    used:bots.BN.dailyTrades,   limit:50, col:"#f0b90b",isCount:true},
            ].map(t=>{
              const pct=t.used/t.limit*100;
              const c=pct>75?t.col:pct>45?"#ff9800":"#1e3040";
              return(
                <div key={t.l} style={{background:"#09101a",border:"1px solid #0f1a28",borderRadius:8,padding:"14px 16px"}}>
                  <div style={{fontSize:13,color:"#3a5070",marginBottom:10}}>{t.l}</div>
                  <div style={{display:"flex",justifyContent:"space-between",fontSize:16,fontFamily:"monospace",fontWeight:700,marginBottom:10}}>
                    <span style={{color:c}}>{t.used}{t.isCount?"":"%"}</span>
                    <span style={{color:"#2a3e52",fontWeight:400}}>/ {t.limit}{t.isCount?"":"%"}</span>
                  </div>
                  <Bar pct={pct} color={c} h={6}/>
                  {pct>75&&<div style={{fontSize:13,color:t.col+"aa",marginTop:6}}>⚠ approaching limit</div>}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  // ── EXPOSURE TAB ────────────────────────────────────────────────────────
  function TabExposure(){
    const botExp=Object.values(bots).map(b=>({id:b.id,accent:b.accent,pct:b.positions.reduce((a,p)=>a+p.size,0)/totalEquity*100}));
    const totalExp=allOpen.reduce((a,p)=>a+p.size,0);
    return(
      <div className="fade" style={{padding:20,display:"flex",flexDirection:"column",gap:14}}>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
          {/* Corr groups */}
          <div style={{background:"#06090f",border:"1px solid #0e1828",borderRadius:10,padding:"20px 22px"}}>
            <div style={{fontSize:14,color:"#2a5070",letterSpacing:1,marginBottom:18,fontFamily:"'Sora',sans-serif",fontWeight:700}}>④ CORRELATION GROUP EXPOSURE · MAX 25%</div>
            {CORR_GROUPS.map(g=>{
              const c=g.pct>g.limit*.8?"#ff9800":g.pct>g.limit*.5?"#00c8ff":"#00cc88";
              return(
                <div key={g.name} style={{marginBottom:18}}>
                  <div style={{display:"flex",justifyContent:"space-between",fontSize:15,marginBottom:7}}>
                    <span style={{fontFamily:"monospace",color:"#6a8a9a",fontWeight:600}}>{g.name}</span>
                    <span style={{fontFamily:"monospace",fontWeight:700,color:c}}>{g.pct}%{g.pct>g.limit*.75&&"  ⚠"}</span>
                  </div>
                  <Bar pct={g.pct/g.limit*100} color={c} h={7}/>
                  <div style={{fontSize:13,color:"#1e2d3e",marginTop:5,textAlign:"right"}}>{g.pct} of {g.limit}% limit</div>
                </div>
              );
            })}
          </div>
          <div style={{display:"flex",flexDirection:"column",gap:14}}>
            {/* Bot allocation */}
            <div style={{background:"#06090f",border:"1px solid #0e1828",borderRadius:10,padding:"20px 22px"}}>
              <div style={{fontSize:14,color:"#2a5070",letterSpacing:1,marginBottom:16,fontFamily:"'Sora',sans-serif",fontWeight:700}}>BOT ALLOCATION · MAX 40% EACH</div>
              {botExp.map(b=>(
                <div key={b.id} style={{marginBottom:16}}>
                  <div style={{display:"flex",justifyContent:"space-between",fontSize:15,marginBottom:7}}>
                    <span style={{color:b.accent,fontWeight:700,fontFamily:"monospace"}}>{b.id}</span>
                    <span style={{fontFamily:"monospace",color:b.pct>32?"#ff9800":"#4a6080"}}>{b.pct.toFixed(1)}% / 40%</span>
                  </div>
                  <Bar pct={b.pct/40*100} color={b.accent} h={7}/>
                </div>
              ))}
            </div>
            {/* Stats */}
            <div style={{background:"#06090f",border:"1px solid #0e1828",borderRadius:10,padding:"20px 22px"}}>
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
                {[
                  {l:"Open Positions",  v:allOpen.length,                                                    note:"of 15 max",       c:"#00c8ff"},
                  {l:"Asset Classes",   v:3,                                                                 note:"≥ 3 required  ✓", c:"#00cc88"},
                  {l:"Total Exposure",  v:`${(totalExp/totalEquity*100).toFixed(1)}%`,                       note:"of equity",       c:"#b06aff"},
                  {l:"Open Risk $",     v:`$${allOpen.reduce((a,p)=>a+p.risk/100*totalEquity,0).toFixed(0)}`,note:"total at stake",  c:"#ff9800"},
                ].map(x=>(
                  <div key={x.l} style={{background:"#09101a",border:"1px solid #0f1a28",borderRadius:8,padding:"16px 18px"}}>
                    <div style={{fontSize:13,color:"#2a3e52",marginBottom:8}}>{x.l}</div>
                    <div style={{fontFamily:"monospace",fontSize:24,fontWeight:700,color:x.c}}>{x.v}</div>
                    <div style={{fontSize:13,color:"#2a4050",marginTop:5}}>{x.note}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
        {/* Breakdown table */}
        <div style={{background:"#06090f",border:"1px solid #0e1828",borderRadius:10,overflow:"hidden"}}>
          <div style={{padding:"14px 22px",borderBottom:"1px solid #0e1828",fontSize:14,color:"#2a5070",fontFamily:"'Sora',sans-serif",fontWeight:700}}>ALL OPEN POSITIONS — RISK BREAKDOWN</div>
          <table style={{width:"100%",borderCollapse:"collapse"}}>
            <thead>
              <tr style={{borderBottom:"1px solid #0e1828"}}>
                {["Bot","Symbol","Group","Size","Risk %","$ at Risk","R:R","Status"].map(h=>(
                  <th key={h} style={{padding:"11px 16px",fontSize:13,color:"#2a3e52",fontFamily:"'Sora',sans-serif",textAlign:"left",fontWeight:600}}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {allOpen.map(p=>{
                const b2=Object.values(bots).find(b=>b.positions.some(x=>x.id===p.id));
                const rrN=+p.rr;
                return(
                  <tr key={p.id} className="row" style={{borderBottom:"1px solid #080d14"}}>
                    <td style={{padding:"11px 16px"}}><span style={{fontFamily:"monospace",fontSize:15,fontWeight:700,color:b2?.accent}}>{b2?.id}</span></td>
                    <td style={{padding:"11px 16px",fontFamily:"monospace",fontSize:15,color:"#7a9aaa",fontWeight:600}}>{p.sym}</td>
                    <td style={{padding:"11px 16px"}}><span style={{fontSize:13,padding:"4px 10px",borderRadius:5,background:"#0a1020",border:"1px solid #1a2535",color:"#4a6080"}}>{p.group}</span></td>
                    <td style={{padding:"11px 16px",fontFamily:"monospace",fontSize:15,color:"#5a7090"}}>${p.size}</td>
                    <td style={{padding:"11px 16px",fontFamily:"monospace",fontSize:15,fontWeight:700,color:p.risk>1.8?"#ff4455":p.risk>1.2?"#ff9800":"#00c8ff"}}>{p.risk}%</td>
                    <td style={{padding:"11px 16px",fontFamily:"monospace",fontSize:15,color:"#ff9800"}}>${(p.risk/100*totalEquity).toFixed(0)}</td>
                    <td style={{padding:"11px 16px",fontFamily:"monospace",fontSize:16,fontWeight:700,color:rrN>=2?"#00cc88":rrN>=1.5?"#ff9800":"#ff4455"}}>{p.rr}</td>
                    <td style={{padding:"11px 16px"}}><span style={{fontSize:13,padding:"4px 10px",borderRadius:5,background:"#00cc8812",border:"1px solid #00cc8828",color:"#00cc88"}}>OPEN</span></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  // ── JOURNAL TAB ─────────────────────────────────────────────────────────
  function TabJournal(){
    const BC={HL:"#00c8ff",BN:"#f0b90b",PM:"#b06aff"};
    const rows=jFilter==="ALL"?JOURNAL:JOURNAL.filter(t=>t.status===jFilter);
    return(
      <div className="fade">
        <div style={{padding:"12px 18px",borderBottom:"1px solid #0a0e18",display:"flex",alignItems:"center",gap:8,background:"#03050a"}}>
          {["ALL","OPEN","CLOSED","STOPPED"].map(f=>(
            <button key={f} onClick={()=>setJFilter(f)} style={{padding:"6px 16px",borderRadius:5,border:"none",background:jFilter===f?"#0f1828":"transparent",color:jFilter===f?"#6090b0":"#2a3e52",fontSize:14,cursor:"pointer",fontFamily:"inherit",fontWeight:600}}>
              {f}
            </button>
          ))}
          <div style={{marginLeft:"auto",display:"flex",alignItems:"center",gap:8,fontSize:14,color:"#1e3028"}}>
            <div style={{width:9,height:9,borderRadius:"50%",background:"#00cc88",boxShadow:"0 0 6px #00cc88",animation:"blink 2s infinite"}}/>
            Telegram alerts active
          </div>
        </div>
        <div style={{overflowX:"auto"}}>
          <table style={{width:"100%",borderCollapse:"collapse",minWidth:860}}>
            <thead>
              <tr style={{borderBottom:"1px solid #0e1828",background:"#03050a"}}>
                {["Bot","Symbol","Side","Entry","Exit","Size","Risk","P&L","R Achieved","Status","Time"].map(h=>(
                  <th key={h} style={{padding:"11px 14px",fontSize:13,color:"#2a3e52",fontFamily:"'Sora',sans-serif",textAlign:"left",fontWeight:600}}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map(t=>{
                const isLong=t.side==="LONG"||t.side==="YES";
                const rrN=parseFloat(t.rr);
                const stCol=t.status==="OPEN"?"#00cc88":t.status==="CLOSED"?"#00c8ff":"#ff9800";
                return(
                  <tr key={t.id} className="row" style={{borderBottom:"1px solid #070b12"}}>
                    <td style={{padding:"12px 14px"}}><span style={{fontFamily:"monospace",fontSize:15,fontWeight:700,color:BC[t.bot]}}>{t.bot}</span></td>
                    <td style={{padding:"12px 14px",fontFamily:"monospace",fontSize:15,color:"#7a8a9a",fontWeight:600}}>{t.sym}</td>
                    <td style={{padding:"12px 14px"}}>
                      <span style={{fontSize:13,padding:"4px 10px",borderRadius:5,fontWeight:700,background:isLong?"#00cc8812":"#ff445512",color:isLong?"#00aa66":"#ff5566",border:`1px solid ${isLong?"#00cc8830":"#ff445530"}`}}>{t.side}</span>
                    </td>
                    <td style={{padding:"12px 14px",fontFamily:"monospace",fontSize:14,color:"#4a6278"}}>{t.entry}</td>
                    <td style={{padding:"12px 14px",fontFamily:"monospace",fontSize:14,color:"#5a6a78"}}>{t.exit}</td>
                    <td style={{padding:"12px 14px",fontFamily:"monospace",fontSize:14,color:"#5a7090"}}>${t.size}</td>
                    <td style={{padding:"12px 14px",fontFamily:"monospace",fontSize:14,color:"#00c8ffaa"}}>{t.risk}</td>
                    <td style={{padding:"12px 14px",fontFamily:"monospace",fontSize:17,fontWeight:700,color:t.pnl>=0?"#00cc88":"#ff5566"}}>{t.pnl>=0?"+":""}{t.pnl.toFixed(2)}</td>
                    <td style={{padding:"12px 14px",fontFamily:"monospace",fontSize:15,fontWeight:700,color:rrN>=2?"#00cc88":rrN>=0?"#ff9800":"#ff4455"}}>{t.rr}</td>
                    <td style={{padding:"12px 14px"}}>
                      <span style={{fontSize:13,padding:"4px 10px",borderRadius:5,fontWeight:700,background:`${stCol}12`,border:`1px solid ${stCol}28`,color:stCol}}>{t.status}</span>
                    </td>
                    <td style={{padding:"12px 14px",fontFamily:"monospace",fontSize:14,color:"#2a3e52"}}>{t.ts}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  // ═════════════════════════════════════════════════════════════════════════
  return(
    <div style={{fontFamily:"'Sora',sans-serif",background:"#060910",color:"#c8d8e8",minHeight:"100vh",display:"flex",flexDirection:"column"}}>
      <style>{CSS}</style>

      {/* Modals */}
      {closing&&<CloseModal pos={closing} accent={bot.accent} onConfirm={confirmClose} onCancel={()=>setClosing(null)}/>}
      {killConfirm&&(
        <div style={{position:"fixed",inset:0,background:"rgba(0,0,0,.92)",display:"flex",alignItems:"center",justifyContent:"center",zIndex:9999,backdropFilter:"blur(10px)"}}>
          <div style={{background:"#0a0205",border:"1px solid #ff000055",borderRadius:14,padding:"36px 40px",maxWidth:420,textAlign:"center",boxShadow:"0 0 100px #ff00001a"}}>
            <div style={{fontSize:48,marginBottom:14}}>🚨</div>
            <div style={{fontFamily:"'Sora',sans-serif",fontSize:26,fontWeight:800,color:"#ff4455",marginBottom:10}}>Emergency Kill Switch</div>
            <div style={{fontSize:16,color:"#6a7a8a",lineHeight:1.7,marginBottom:28}}>
              Halts <strong style={{color:"#ffaaaa"}}>all three bots</strong> immediately.<br/>
              No new trades will be placed.<br/>Existing positions remain open.
            </div>
            <div style={{display:"flex",gap:12}}>
              <button onClick={()=>setKillConfirm(false)} style={{flex:1,padding:"13px 0",borderRadius:8,background:"#111820",border:"1px solid #1a2535",color:"#5a7090",fontSize:16,cursor:"pointer",fontFamily:"inherit"}}>Cancel</button>
              <button onClick={()=>{setGlobalHalt(true);setKillConfirm(false)}} style={{flex:1,padding:"13px 0",borderRadius:8,background:"#b91c1c",border:"none",color:"#fff",fontSize:16,fontWeight:800,cursor:"pointer",fontFamily:"inherit"}}>⚡ Kill All Bots</button>
            </div>
          </div>
        </div>
      )}

      {/* ── TOPBAR ── */}
      <div style={{height:62,background:"#03050a",borderBottom:"1px solid #0c1522",display:"flex",alignItems:"center",padding:"0 20px",gap:0,position:"sticky",top:0,zIndex:100,flexShrink:0}}>
        {/* Logo */}
        <div style={{display:"flex",alignItems:"center",gap:10,paddingRight:22,borderRight:"1px solid #0c1522"}}>
          <div style={{width:30,height:30,borderRadius:6,background:"linear-gradient(135deg,#00c8ff,#b06aff)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:16,fontWeight:900,color:"#fff"}}>α</div>
          <span style={{fontWeight:800,fontSize:18,letterSpacing:2,color:"#c8d8e8"}}>ALPHACOPY</span>
          <span style={{fontSize:12,color:"#1a2535",border:"1px solid #0f1a28",padding:"2px 8px",borderRadius:4}}>v4</span>
        </div>
        {/* P&L */}
        <div style={{padding:"0 22px",borderRight:"1px solid #0c1522"}}>
          <div style={{fontSize:12,color:"#2a3e52",letterSpacing:1,marginBottom:2}}>PORTFOLIO P&L</div>
          <div style={{fontFamily:"monospace",fontSize:22,fontWeight:700,color:totalPnl>=0?"#00cc88":"#ff5566"}}>
            {totalPnl>=0?"+":"-"}<Live val={totalPnl} dec={2} prefix="$" color={totalPnl>=0?"#00cc88":"#ff5566"}/>
            <span style={{fontSize:15,marginLeft:8,opacity:.5}}>({fmtP(totalPnlPct)})</span>
          </div>
        </div>
        {/* Equity */}
        <div style={{padding:"0 22px",borderRight:"1px solid #0c1522"}}>
          <div style={{fontSize:12,color:"#2a3e52",letterSpacing:1,marginBottom:2}}>EQUITY</div>
          <div style={{fontFamily:"monospace",fontSize:17,fontWeight:600,color:"#6a8aaa"}}>${totalEquity.toFixed(2)}</div>
        </div>
        {/* Rule pills */}
        <div style={{padding:"0 22px",borderRight:"1px solid #0c1522",display:"flex",gap:8,alignItems:"center"}}>
          {RULES.map(r=>{
            const c=SC[r.sc].tx;
            return(
              <div key={r.key} onClick={()=>setTab("rules")} title={r.label}
                style={{display:"flex",alignItems:"center",gap:6,cursor:"pointer",padding:"4px 10px",borderRadius:5,border:`1px solid ${c}30`,background:`${c}0a`,transition:"all .2s"}}
                onMouseEnter={e=>e.currentTarget.style.border=`1px solid ${c}70`}
                onMouseLeave={e=>e.currentTarget.style.border=`1px solid ${c}30`}>
                <div style={{width:8,height:8,borderRadius:"50%",background:c,boxShadow:`0 0 5px ${c}`}}/>
                <span style={{fontSize:14,color:c,fontFamily:"monospace"}}>{r.num}</span>
              </div>
            );
          })}
        </div>
        <div style={{flex:1}}/>
        {/* Clock */}
        <div style={{fontFamily:"monospace",fontSize:15,color:"#2a3e52",paddingRight:16}}>{time.toISOString().slice(11,19)} UTC</div>
        {/* Live dot */}
        <div style={{display:"flex",alignItems:"center",gap:7,paddingRight:16}}>
          <div style={{width:9,height:9,borderRadius:"50%",background:"#00cc88",boxShadow:"0 0 7px #00cc88",animation:"blink 2s infinite"}}/>
          <span style={{fontSize:14,color:"#1a4a2a"}}>LIVE</span>
        </div>
        {/* Kill */}
        {globalHalt?(
          <button onClick={()=>setGlobalHalt(false)} style={{padding:"8px 20px",borderRadius:7,border:"1px solid #00cc8840",background:"#00cc8810",color:"#00cc88",fontSize:14,fontWeight:700,cursor:"pointer",fontFamily:"inherit"}}>↺ Resume All</button>
        ):(
          <button onClick={()=>setKillConfirm(true)}
            style={{padding:"8px 20px",borderRadius:7,border:"1px solid #ff444440",background:"transparent",color:"#ff5566",fontSize:14,fontWeight:700,cursor:"pointer",fontFamily:"inherit",transition:"all .2s"}}
            onMouseEnter={e=>{e.currentTarget.style.background="#b91c1c";e.currentTarget.style.color="#fff"}}
            onMouseLeave={e=>{e.currentTarget.style.background="transparent";e.currentTarget.style.color="#ff5566"}}>
            ⚡ Kill All
          </button>
        )}
      </div>

      {globalHalt&&(
        <div style={{background:"#1a0005",borderBottom:"2px solid #ff000040",padding:"10px 20px",textAlign:"center",fontFamily:"monospace",fontSize:15,color:"#ff4455",letterSpacing:1,animation:"blink 1.5s infinite"}}>
          🚨  KILL SWITCH ACTIVE — ALL BOTS HALTED — NO NEW TRADES
        </div>
      )}

      <div style={{display:"flex",flex:1,overflow:"hidden",minHeight:0}}>
        {/* ── SIDEBAR ── */}
        <div style={{width:230,background:"#03050a",borderRight:"1px solid #0c1522",display:"flex",flexDirection:"column",overflowY:"auto",flexShrink:0}}>
          {/* Risk rules list */}
          <div style={{padding:"16px 12px 8px"}}>
            <div style={{fontSize:12,color:"#1a2535",letterSpacing:2,marginBottom:10,padding:"0 6px",fontWeight:700}}>RISK RULES</div>
            {RULES.map(r=>{
              const c=SC[r.sc].tx;
              return(
                <div key={r.key} onClick={()=>setTab("rules")}
                  style={{display:"flex",alignItems:"flex-start",gap:9,padding:"9px 10px",borderRadius:7,cursor:"pointer",marginBottom:2,transition:"background .15s"}}
                  onMouseEnter={e=>e.currentTarget.style.background="#0a1020"}
                  onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
                  <div style={{width:8,height:8,borderRadius:"50%",background:c,boxShadow:`0 0 5px ${c}`,flexShrink:0,marginTop:5}}/>
                  <div style={{flex:1,minWidth:0}}>
                    <div style={{fontSize:14,fontWeight:600,color:"#5a7090",whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{r.label}</div>
                    <div style={{fontSize:12,color:c,marginTop:2,fontFamily:"monospace"}}>{r.sc}</div>
                  </div>
                </div>
              );
            })}
          </div>
          <div style={{height:1,background:"#0c1522",margin:"4px 0"}}/>
          {/* Bots */}
          <div style={{padding:"8px 12px"}}>
            <div style={{fontSize:12,color:"#1a2535",letterSpacing:2,marginBottom:10,padding:"0 6px",fontWeight:700}}>BOTS</div>
            {Object.values(bots).map(b=>{
              const p=b.equity-b.allocated;
              const isA=activeBot===b.id;
              return(
                <div key={b.id} onClick={()=>{setActiveBot(b.id);setTab("positions")}}
                  style={{padding:"13px 12px",borderRadius:8,cursor:"pointer",marginBottom:6,
                    border:`1px solid ${isA?b.accent+"50":"transparent"}`,
                    background:isA?b.dim+"80":"transparent",transition:"all .2s"}}>
                  <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:6}}>
                    <span style={{fontSize:15,fontWeight:800,color:b.accent,letterSpacing:1}}>{b.id}</span>
                    <span style={{fontSize:12,padding:"2px 8px",borderRadius:4,
                      background:b.halted||globalHalt?"#ff000018":"#00cc8812",
                      color:b.halted||globalHalt?"#ff4455":"#00cc88",
                      border:`1px solid ${b.halted||globalHalt?"#ff000030":"#00cc8828"}`}}>
                      {b.halted||globalHalt?"HALTED":`${b.positions.length} pos`}
                    </span>
                  </div>
                  <div style={{fontFamily:"monospace",fontSize:17,fontWeight:700,color:p>=0?"#00cc88":"#ff5566",marginBottom:8}}>
                    <Live val={p} dec={2} prefix={p>=0?"+$":"-$"} color={p>=0?"#00cc88":"#ff5566"}/>
                  </div>
                  <Spark vals={b.spark} color={b.accent} w={198} h={26}/>
                  <div style={{marginTop:8}}>
                    <div style={{display:"flex",justifyContent:"space-between",fontSize:13,color:"#2a3e52",marginBottom:4}}>
                      <span>Drawdown</span>
                      <span style={{color:b.drawdown>10?"#ff9800":"#3a5060"}}>{b.drawdown}%</span>
                    </div>
                    <Bar pct={b.drawdown/b.maxDD*100} color={b.accent} h={5}/>
                  </div>
                </div>
              );
            })}
          </div>
          <div style={{height:1,background:"#0c1522",margin:"4px 0"}}/>
          {/* Portfolio totals */}
          <div style={{padding:"14px 16px",margin:"6px 10px 10px",background:"#080c14",borderRadius:8,border:"1px solid #0f1a28"}}>
            <div style={{fontSize:12,color:"#1a2535",letterSpacing:2,marginBottom:10,fontWeight:700}}>PORTFOLIO</div>
            {[
              {l:"Equity",   v:`$${totalEquity.toFixed(0)}`, c:"#5a7a8a"},
              {l:"Net P&L",  v:fmtD(totalPnl,0),             c:totalPnl>=0?"#00cc88":"#ff5566"},
              {l:"Open pos", v:`${allOpen.length}`,           c:"#3a5060"},
              {l:"Port. DD", v:`${portDD}%`,                  c:parseFloat(portDD)>5?"#ff9800":"#2a4050"},
            ].map(x=>(
              <div key={x.l} style={{display:"flex",justifyContent:"space-between",marginBottom:8}}>
                <span style={{fontSize:14,color:"#2a3e52"}}>{x.l}</span>
                <span style={{fontSize:14,fontFamily:"monospace",fontWeight:600,color:x.c}}>{x.v}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── MAIN PANEL ── */}
        <div style={{flex:1,display:"flex",flexDirection:"column",overflow:"hidden"}}>
          {/* Bot header strip */}
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",borderBottom:"1px solid #0c1522",flexShrink:0}}>
            {Object.values(bots).map((b,i)=>{
              const p=b.equity-b.allocated;
              const isA=activeBot===b.id;
              return(
                <div key={b.id} onClick={()=>{setActiveBot(b.id);setTab("positions")}}
                  style={{padding:"16px 22px",cursor:"pointer",borderRight:i<2?"1px solid #0c1522":"none",
                    background:isA?`${b.dim}60`:"transparent",
                    borderBottom:isA?`2px solid ${b.accent}`:"2px solid transparent",transition:"all .2s"}}>
                  <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:8}}>
                    <div style={{fontSize:14,fontWeight:800,color:b.accent,letterSpacing:1.5}}>{b.id} — {b.label}</div>
                    <Spark vals={b.spark} color={b.accent} w={62} h={24}/>
                  </div>
                  <div style={{fontFamily:"monospace",fontSize:24,fontWeight:700,color:p>=0?"#00cc88":"#ff5566",marginBottom:8}}>
                    <Live val={p} dec={2} prefix={p>=0?"+$":"-$"} color={p>=0?"#00cc88":"#ff5566"}/>
                    <span style={{fontSize:15,marginLeft:8,opacity:.5}}>({fmtP(p/b.allocated*100)})</span>
                  </div>
                  <div style={{display:"flex",gap:22}}>
                    {[
                      {l:"Equity",v:`$${b.equity.toFixed(0)}`,  c:"#4a6080"},
                      {l:"DD",    v:`${b.drawdown.toFixed(1)}%`, c:b.drawdown>10?"#ff9800":"#2a4050"},
                      {l:"W / L", v:`${b.wins} / ${b.losses}`,  c:"#2a3a4a"},
                    ].map(x=>(
                      <div key={x.l}>
                        <div style={{fontSize:12,color:"#1a2535"}}>{x.l}</div>
                        <div style={{fontSize:15,fontFamily:"monospace",fontWeight:600,color:x.c}}>{x.v}</div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Tab bar */}
          <div style={{display:"flex",alignItems:"center",borderBottom:"1px solid #080d14",background:"#03050a",flexShrink:0}}>
            <div style={{display:"flex",padding:"0 16px",gap:2}}>
              {[
                {id:"positions",label:`Positions  ${bot.positions.length}`},
                {id:"rules",    label:"Risk Rules  6"},
                {id:"exposure", label:"Exposure"},
                {id:"journal",  label:"Journal"},
              ].map(t=>(
                <button key={t.id} onClick={()=>setTab(t.id)}
                  style={{padding:"13px 20px",border:"none",borderBottom:tab===t.id?`2px solid ${bot.accent}`:"2px solid transparent",background:"transparent",color:tab===t.id?bot.accent:"#3a5060",fontSize:15,fontWeight:600,cursor:"pointer",fontFamily:"inherit",transition:"color .2s",marginBottom:-1}}>
                  {t.label}
                </button>
              ))}
            </div>
            {tab==="positions"&&bot.positions.length>0&&(
              <button onClick={()=>setClosing(bot.positions[0])}
                style={{marginLeft:"auto",marginRight:16,padding:"7px 18px",borderRadius:6,background:"transparent",border:"1px solid #aa1c1c50",color:"#ff5566",fontSize:14,fontWeight:700,cursor:"pointer",fontFamily:"inherit"}}>
                Close All {bot.id}
              </button>
            )}
          </div>

          {/* Content */}
          <div style={{flex:1,overflowY:"auto"}}>
            {tab==="positions"&&<TabPositions/>}
            {tab==="rules"    &&<TabRules/>}
            {tab==="exposure" &&<TabExposure/>}
            {tab==="journal"  &&<TabJournal/>}
          </div>

          {/* Status bar */}
          <div style={{borderTop:"1px solid #080d14",background:"#03050a",padding:"9px 20px",display:"flex",alignItems:"center",gap:0,flexShrink:0,flexWrap:"wrap"}}>
            {[
              `① Max $${maxRisk1.toFixed(0)} / trade`,
              `② SL on all ${allOpen.length} positions`,
              "③ Min R:R 2:1 enforced",
              "④ 5 groups monitored",
              `⑤ Kill switch: ${globalHalt?"ACTIVE":"clear"}`,
              "⑥ Paper: day 9 / 14",
            ].map((s,i)=>(
              <div key={i} style={{display:"flex",alignItems:"center",gap:6}}>
                {i>0&&<div style={{width:1,height:14,background:"#0c1522",margin:"0 12px"}}/>}
                <span style={{fontSize:14,color:s.includes("ACTIVE")?"#ff4455":s.includes("9 / 14")?"#ff9800":"#2a3e52",fontFamily:"monospace"}}>{s}</span>
              </div>
            ))}
            <div style={{flex:1}}/>
            <span style={{fontSize:14,color:"#1a2535",fontFamily:"monospace"}}>
              Open risk: ${allOpen.reduce((a,p)=>a+p.risk/100*totalEquity,0).toFixed(0)} · Port. DD: {portDD}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
