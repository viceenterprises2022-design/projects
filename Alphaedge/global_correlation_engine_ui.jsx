import { useState, useEffect, useRef } from "react";

// ─── MOCK DATA ────────────────────────────────────────────────────────────────

const ASSETS = ["NIFTY", "S&P500", "CSI300", "FTSE", "DXY", "GOLD", "OIL", "UST10Y"];
const SECTORS = ["IT", "Banks", "Pharma", "Auto", "FMCG", "Metals", "Energy", "Infra"];

const corrMatrix = {
  NIFTY:   [1.00, 0.68, 0.45, 0.61, -0.58, -0.22, -0.42, -0.31],
  "S&P500":[0.68, 1.00, 0.54, 0.82, -0.62, -0.45, -0.31, -0.28],
  CSI300:  [0.45, 0.54, 1.00, 0.48, -0.41,  0.05,  0.12, -0.18],
  FTSE:    [0.61, 0.82, 0.48, 1.00, -0.71, -0.38, -0.18, -0.35],
  DXY:     [-0.58,-0.62,-0.41,-0.71, 1.00, -0.73,  0.45,  0.42],
  GOLD:    [-0.22,-0.45, 0.05,-0.38,-0.73,  1.00,  0.28,  0.15],
  OIL:     [-0.42,-0.31, 0.12,-0.18, 0.45,  0.28,  1.00,  0.22],
  UST10Y:  [-0.31,-0.28,-0.18,-0.35, 0.42,  0.15,  0.22,  1.00],
};

const transmissionChain = [
  { node: "Fed Hike +50bps", lag: "T+0", impact: "USD ↑ 0.4%", type: "trigger" },
  { node: "DXY Strengthens", lag: "T+0", impact: "+0.6%", type: "currency" },
  { node: "FII Outflows", lag: "T+1-2d", impact: "₹800-1200 Cr", type: "flow" },
  { node: "INR Weakens", lag: "T+2d", impact: "₹83.4 → ₹84.2", type: "currency" },
  { node: "Nifty 50", lag: "T+2-3d", impact: "-0.6% to -1.0%", type: "equity" },
  { node: "IT Stocks ↑", lag: "T+2d", impact: "+0.5-1.2%", type: "positive" },
  { node: "Banks ↓", lag: "T+2d", impact: "-1.0-1.5%", type: "negative" },
];

const leadLagData = [
  { leading: "US 10Y Yield", lagging: "India 10Y", lagDays: 2, strength: 0.85 },
  { leading: "Oil Price", lagging: "India CPI", lagDays: 30, strength: 0.78 },
  { leading: "China PMI", lagging: "EU Exporters", lagDays: 15, strength: 0.72 },
  { leading: "VIX Spikes", lagging: "EM Selloff", lagDays: 5, strength: 0.89 },
  { leading: "DXY Index", lagging: "INR/USD", lagDays: 0, strength: 0.91 },
  { leading: "S&P 500", lagging: "Nifty 50", lagDays: 1, strength: 0.82 },
];

const signals = [
  { name: "VIX Acceleration", activated: true, value: 0.18, threshold: 0.15, weight: 0.40, icon: "⚡" },
  { name: "Treasury Volatility", activated: true, value: 0.09, threshold: 0.08, weight: 0.25, icon: "📊" },
  { name: "FX Stress Index", activated: false, value: 2.1, threshold: 2.5, weight: 0.20, icon: "💱" },
  { name: "Credit Spreads", activated: false, value: 1.08, threshold: 1.15, weight: 0.10, icon: "📉" },
  { name: "Commodity Disloc.", activated: true, value: 0.07, threshold: 0.10, weight: 0.05, icon: "🛢️" },
];

const familyPortfolio = [
  { region: "US Holdings", aum: 355.9, pct: 42.0, change: -0.42, color: "#3b82f6" },
  { region: "India Holdings", aum: 237.2, pct: 28.0, change: -0.31, color: "#f59e0b" },
  { region: "Europe Holdings", aum: 127.1, pct: 15.0, change: -0.18, color: "#8b5cf6" },
  { region: "China Holdings", aum: 84.7,  pct: 10.0, change: -0.28, color: "#ef4444" },
  { region: "Alternatives",   aum: 42.4,  pct:  5.0, change: +0.12, color: "#10b981" },
];

const retailHoldings = [
  { symbol: "TCS",     sector: "IT",    value: 720000, pct: 15.2, chg: 0.8,  alert: "USD strength = Good" },
  { symbol: "HDFC Bk", sector: "Bank",  value: 842000, pct: 17.8, chg: 0.4,  alert: "Rate cycle peaking" },
  { symbol: "Infosys", sector: "IT",    value: 680000, chg: 0.6,  pct: 14.4, alert: "Nasdaq correlation 0.81" },
  { symbol: "Dr.Reddy",sector: "Pharma",value: 390000, chg: 1.2,  pct: 8.3,  alert: "FDA approval pending" },
  { symbol: "Maruti",  sector: "Auto",  value: 290000, chg: -0.5, pct: 6.1,  alert: "Oil ↑ → Margins pressure" },
  { symbol: "Wipro",   sector: "IT",    value: 312000, chg: -0.2, pct: 6.6,  alert: "" },
  { symbol: "DLF",     sector: "REIT",  value: 250000, chg: 0.2,  pct: 5.3,  alert: "Rate peak = Positive" },
  { symbol: "ITC",     sector: "FMCG",  value: 420000, chg: 0.3,  pct: 8.9,  alert: "Domestic demand strong" },
];

const pmsFactors = [
  { factor: "Beta", current: 0.98, target: 1.00, benchmark: 1.00, status: "ok" },
  { factor: "Size", current: 0.15, target: 0.20, benchmark: 0.00, status: "warn" },
  { factor: "Value", current: 0.42, target: 0.40, benchmark: 0.30, status: "ok" },
  { factor: "Momentum", current: 0.68, target: 0.70, benchmark: 0.50, status: "warn" },
  { factor: "Quality", current: 0.55, target: 0.60, benchmark: 0.40, status: "warn" },
  { factor: "Volatility", current: -0.32, target: -0.30, benchmark: -0.20, status: "ok" },
];

const regionCorrelation = [
  { region: "India", ticker: "NIFTY", corr: 0.68, oil: -0.42, usd: -0.58, china: 0.45 },
  { region: "China", ticker: "CSI300", corr: 0.54, oil: 0.12, usd: -0.41, china: 1.00 },
  { region: "Singapore", ticker: "STI", corr: 0.61, oil: 0.38, usd: -0.52, china: 0.58 },
  { region: "Europe", ticker: "FTSE", corr: 0.82, oil: -0.18, usd: -0.71, china: 0.48 },
  { region: "Africa (ZA)", ticker: "JSE", corr: 0.55, oil: 0.62, usd: -0.71, china: 0.44 },
];

// ─── HELPERS ─────────────────────────────────────────────────────────────────

const fmtINR = (n) => `₹${(n / 100000).toFixed(1)}L`;
const fmtCr = (n) => `₹${n.toFixed(1)} Cr`;
const fmtM  = (n) => `$${n.toFixed(1)}M`;

function corrColor(v) {
  if (v >= 0.7)  return "#ef4444";
  if (v >= 0.4)  return "#f59e0b";
  if (v >= 0.1)  return "#22c55e";
  if (v >= -0.1) return "#64748b";
  if (v >= -0.4) return "#22d3ee";
  if (v >= -0.7) return "#3b82f6";
  return "#8b5cf6";
}

function Bar({ value, max = 1, color = "#f59e0b", height = 6 }) {
  const w = Math.min(Math.abs(value) / max, 1) * 100;
  return (
    <div style={{ background: "#1e2533", borderRadius: 3, height, width: "100%", overflow: "hidden" }}>
      <div style={{ width: `${w}%`, height: "100%", background: color, borderRadius: 3, transition: "width 0.8s ease" }} />
    </div>
  );
}

function Sparkline({ data, color = "#f59e0b", width = 80, height = 32 }) {
  const max = Math.max(...data), min = Math.min(...data);
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((v - min) / (max - min || 1)) * height;
    return `${x},${y}`;
  }).join(" ");
  return (
    <svg width={width} height={height}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

const spark1 = [42, 45, 43, 48, 51, 49, 52, 55, 53, 58, 62, 60];
const spark2 = [60, 58, 62, 65, 63, 68, 66, 70, 68, 72, 71, 74];

// ─── CRISIS GAUGE ─────────────────────────────────────────────────────────────

function CrisisGauge({ probability = 0.63 }) {
  const pct = probability * 100;
  const r = 60, cx = 80, cy = 80;
  const circumference = Math.PI * r;
  const offset = circumference * (1 - probability);
  const color = probability > 0.7 ? "#ef4444" : probability > 0.5 ? "#f59e0b" : "#22c55e";
  const label = probability > 0.7 ? "CRITICAL" : probability > 0.5 ? "ELEVATED" : "NORMAL";

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
      <svg width={160} height={100} viewBox="0 0 160 100">
        <path d={`M${cx - r},${cy} A${r},${r} 0 0 1 ${cx + r},${cy}`} fill="none" stroke="#1e2533" strokeWidth={14} strokeLinecap="round" />
        <path d={`M${cx - r},${cy} A${r},${r} 0 0 1 ${cx + r},${cy}`} fill="none" stroke={color} strokeWidth={14} strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset} style={{ transition: "stroke-dashoffset 1s ease, stroke 0.5s" }} />
        <text x={cx} y={cy - 8} textAnchor="middle" fill="white" fontSize={26} fontWeight="700" fontFamily="'IBM Plex Mono', monospace">{pct.toFixed(0)}%</text>
        <text x={cx} y={cy + 14} textAnchor="middle" fill={color} fontSize={10} fontWeight="600" letterSpacing={2}>{label}</text>
      </svg>
    </div>
  );
}

// ─── CORRELATION CELL ─────────────────────────────────────────────────────────

function CorrCell({ value }) {
  if (value === 1) return <td style={{ background: "#0f172a", color: "#475569", textAlign: "center", fontFamily: "monospace", fontSize: 11, padding: "6px 4px", fontWeight: 700 }}>—</td>;
  const bg = corrColor(value);
  return (
    <td style={{ background: bg + "22", color: bg, textAlign: "center", fontFamily: "'IBM Plex Mono', monospace", fontSize: 11, padding: "6px 4px", fontWeight: 600, border: "1px solid #1e2533", transition: "background 0.3s" }}>
      {value.toFixed(2)}
    </td>
  );
}

// ─── MAIN APP ─────────────────────────────────────────────────────────────────

export default function App() {
  const [persona, setPersona] = useState("retail");
  const [activeTab, setActiveTab] = useState("overview");
  const [tick, setTick] = useState(0);
  const [crisisProb, setCrisisProb] = useState(0.63);

  useEffect(() => {
    const t = setInterval(() => {
      setTick(p => p + 1);
      setCrisisProb(p => Math.max(0.4, Math.min(0.85, p + (Math.random() - 0.5) * 0.02)));
    }, 2000);
    return () => clearInterval(t);
  }, []);

  const personas = [
    { id: "retail", label: "Retail Investor", icon: "👤", sub: "₹47L Portfolio" },
    { id: "family", label: "Family Office", icon: "🏛️", sub: "$847M AUM" },
    { id: "pms", label: "PMS Fund Manager", icon: "📊", sub: "₹847 Cr AUM" },
  ];

  return (
    <div style={{ background: "#080c14", color: "#e2e8f0", fontFamily: "'IBM Plex Sans', 'Helvetica Neue', sans-serif", minHeight: "100vh", fontSize: 13 }}>
      {/* GLOBAL HEADER */}
      <header style={{ background: "#0a0e1a", borderBottom: "1px solid #1e2a3d", padding: "0 24px", display: "flex", alignItems: "center", gap: 24, height: 56, position: "sticky", top: 0, zIndex: 100 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 28, height: 28, background: "linear-gradient(135deg, #f59e0b, #ef4444)", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14 }}>⬡</div>
          <span style={{ fontWeight: 800, fontSize: 15, letterSpacing: 1.5, color: "#f8fafc" }}>ALPHA<span style={{ color: "#f59e0b" }}>EDGE</span></span>
        </div>

        <div style={{ height: 28, width: 1, background: "#1e2a3d" }} />

        {/* LIVE TICKER */}
        <div style={{ display: "flex", gap: 20, fontSize: 11, fontFamily: "'IBM Plex Mono', monospace" }}>
          {[
            { l: "NIFTY", v: "21,345", c: "-0.31%", up: false },
            { l: "S&P", v: "4,892", c: "-0.45%", up: false },
            { l: "DXY", v: "104.2", c: "+0.38%", up: true },
            { l: "BRENT", v: "$87.2", c: "+1.8%", up: true },
            { l: "GOLD", v: "$2,042", c: "+0.8%", up: true },
            { l: "INR", v: "83.42", c: "-0.21%", up: false },
          ].map(t => (
            <div key={t.l} style={{ display: "flex", gap: 5, alignItems: "center" }}>
              <span style={{ color: "#64748b" }}>{t.l}</span>
              <span style={{ color: "#f8fafc", fontWeight: 600 }}>{t.v}</span>
              <span style={{ color: t.up ? "#22c55e" : "#ef4444" }}>{t.c}</span>
            </div>
          ))}
        </div>

        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ background: "#ef444422", border: "1px solid #ef4444", borderRadius: 4, padding: "3px 10px", fontSize: 11, color: "#ef4444", fontWeight: 700, letterSpacing: 1 }}>
            ⚠ CRISIS PROB: {(crisisProb * 100).toFixed(0)}%
          </div>
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#22c55e", boxShadow: "0 0 8px #22c55e" }} />
          <span style={{ fontSize: 11, color: "#64748b" }}>LIVE</span>
        </div>
      </header>

      {/* PERSONA SWITCHER */}
      <div style={{ background: "#0d1220", borderBottom: "1px solid #1e2a3d", padding: "12px 24px", display: "flex", gap: 12 }}>
        {personas.map(p => (
          <button key={p.id} onClick={() => { setPersona(p.id); setActiveTab("overview"); }}
            style={{ padding: "8px 20px", borderRadius: 8, border: "none", cursor: "pointer", transition: "all 0.2s", fontFamily: "inherit", fontSize: 13,
              background: persona === p.id ? "linear-gradient(135deg, #f59e0b22, #f59e0b11)" : "transparent",
              color: persona === p.id ? "#f59e0b" : "#64748b",
              borderLeft: persona === p.id ? "2px solid #f59e0b" : "2px solid transparent",
              fontWeight: persona === p.id ? 700 : 400,
            }}>
            <span style={{ marginRight: 6 }}>{p.icon}</span>
            <span>{p.label}</span>
            <div style={{ fontSize: 10, color: persona === p.id ? "#f59e0b88" : "#475569", marginTop: 2 }}>{p.sub}</div>
          </button>
        ))}

        <div style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center" }}>
          {["overview", "correlations", "crisis", "transmission", "portfolio"].map(t => (
            <button key={t} onClick={() => setActiveTab(t)}
              style={{ padding: "5px 14px", borderRadius: 6, border: "1px solid", cursor: "pointer", fontFamily: "inherit", fontSize: 11, textTransform: "uppercase", letterSpacing: 1, transition: "all 0.2s",
                borderColor: activeTab === t ? "#f59e0b" : "#1e2a3d",
                background: activeTab === t ? "#f59e0b11" : "transparent",
                color: activeTab === t ? "#f59e0b" : "#64748b",
              }}>
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div style={{ padding: "20px 24px" }}>
        {activeTab === "overview" && persona === "retail" && <RetailOverview tick={tick} holdings={retailHoldings} crisisProb={crisisProb} />}
        {activeTab === "overview" && persona === "family" && <FamilyOverview tick={tick} portfolio={familyPortfolio} crisisProb={crisisProb} />}
        {activeTab === "overview" && persona === "pms" && <PMSOverview tick={tick} factors={pmsFactors} crisisProb={crisisProb} />}
        {activeTab === "correlations" && <CorrelationDashboard tick={tick} />}
        {activeTab === "crisis" && <CrisisDashboard crisisProb={crisisProb} signals={signals} />}
        {activeTab === "transmission" && <TransmissionDashboard chain={transmissionChain} leadLag={leadLagData} regions={regionCorrelation} />}
        {activeTab === "portfolio" && persona === "retail" && <RetailPortfolioDeep holdings={retailHoldings} />}
        {activeTab === "portfolio" && persona === "family" && <FamilyPortfolioDeep portfolio={familyPortfolio} />}
        {activeTab === "portfolio" && persona === "pms" && <PMSPortfolioDeep factors={pmsFactors} />}
      </div>
    </div>
  );
}

// ─── RETAIL OVERVIEW ──────────────────────────────────────────────────────────

function RetailOverview({ tick, holdings, crisisProb }) {
  const totalValue = holdings.reduce((s, h) => s + h.value, 0);
  const dayPnl = 12340;
  const goalPct = 68;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gridTemplateRows: "auto auto auto", gap: 16 }}>
      {/* TOP BAR */}
      <div style={{ gridColumn: "1 / -1", background: "linear-gradient(135deg, #0d1220, #111827)", border: "1px solid #1e2a3d", borderRadius: 12, padding: "20px 28px", display: "flex", alignItems: "center", gap: 40 }}>
        <div>
          <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 4 }}>Portfolio Value</div>
          <div style={{ fontSize: 32, fontWeight: 800, fontFamily: "'IBM Plex Mono', monospace", color: "#f8fafc" }}>{fmtINR(totalValue)}</div>
        </div>
        <div style={{ height: 48, width: 1, background: "#1e2a3d" }} />
        <div>
          <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 4 }}>Today's P&L</div>
          <div style={{ fontSize: 24, fontWeight: 700, color: "#22c55e", fontFamily: "'IBM Plex Mono', monospace" }}>+{fmtINR(dayPnl)} <span style={{ fontSize: 14 }}>+0.26%</span></div>
        </div>
        <div style={{ height: 48, width: 1, background: "#1e2a3d" }} />
        <div>
          <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 4 }}>Retirement Goal 2045</div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ flex: 1, background: "#1e2533", borderRadius: 4, height: 8, width: 160 }}>
              <div style={{ width: `${goalPct}%`, height: "100%", background: "linear-gradient(90deg, #f59e0b, #22c55e)", borderRadius: 4 }} />
            </div>
            <span style={{ fontSize: 18, fontWeight: 700, color: "#22c55e" }}>{goalPct}% <span style={{ fontSize: 11, color: "#64748b" }}>ON TRACK</span></span>
          </div>
        </div>
        <div style={{ marginLeft: "auto", textAlign: "right" }}>
          <div style={{ fontSize: 11, color: "#64748b", marginBottom: 4 }}>US Correlation</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: "#f59e0b" }}>72%</div>
          <div style={{ fontSize: 10, color: "#64748b" }}>Because: TCS, Infosys, Wipro</div>
        </div>
      </div>

      {/* AI INSIGHT */}
      <div style={{ background: "#0d1220", border: "1px solid #f59e0b33", borderLeft: "3px solid #f59e0b", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11, color: "#f59e0b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
          <span>🤖</span> AI INSIGHT — TODAY
        </div>
        <p style={{ color: "#cbd5e1", lineHeight: 1.7, fontSize: 12 }}>
          Your portfolio fell <span style={{ color: "#ef4444", fontWeight: 600 }}>0.31%</span> because you hold{" "}
          <span style={{ color: "#f59e0b" }}>TCS, Infosys, Wipro</span> — all US-linked IT exporters with a{" "}
          <span style={{ color: "#f59e0b" }}>72% correlation to Nasdaq</span>.
        </p>
        <p style={{ color: "#94a3b8", lineHeight: 1.7, fontSize: 12, marginTop: 10 }}>
          💡 <strong style={{ color: "#f8fafc" }}>Add 15% in domestic-focused stocks</strong> (Banks, FMCG) to reduce US exposure from 72% → 55%.
        </p>
        <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
          {["Tell me more", "Suggest stocks", "Dismiss"].map(b => (
            <button key={b} style={{ padding: "5px 12px", background: b === "Tell me more" ? "#f59e0b22" : "transparent", border: `1px solid ${b === "Tell me more" ? "#f59e0b" : "#1e2a3d"}`, borderRadius: 6, color: b === "Tell me more" ? "#f59e0b" : "#64748b", fontSize: 11, cursor: "pointer", fontFamily: "inherit" }}>{b}</button>
          ))}
        </div>
      </div>

      {/* CRISIS WIDGET */}
      <div style={{ background: "#0d1220", border: `1px solid ${crisisProb > 0.6 ? "#ef444444" : "#1e2a3d"}`, borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11, color: crisisProb > 0.6 ? "#ef4444" : "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 8 }}>⚠ Correlation Risk</div>
        <CrisisGauge probability={crisisProb} />
        <div style={{ marginTop: 8 }}>
          {signals.slice(0, 3).map(s => (
            <div key={s.name} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
              <div style={{ width: 6, height: 6, borderRadius: "50%", background: s.activated ? "#ef4444" : "#22c55e", flexShrink: 0 }} />
              <span style={{ fontSize: 11, color: "#94a3b8", flex: 1 }}>{s.name}</span>
              <span style={{ fontSize: 10, fontFamily: "monospace", color: s.activated ? "#ef4444" : "#22c55e" }}>{s.activated ? "⚡ ACTIVE" : "✓ OK"}</span>
            </div>
          ))}
        </div>
        {crisisProb > 0.6 && <div style={{ background: "#ef444411", border: "1px solid #ef444444", borderRadius: 6, padding: "8px 12px", marginTop: 10, fontSize: 11, color: "#fca5a5" }}>Consider adding 5% Gold hedge</div>}
      </div>

      {/* MARKET SNAPSHOT */}
      <div style={{ background: "#0d1220", border: "1px solid #1e2a3d", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 14 }}>🌍 Market in 30 Seconds</div>
        {[
          { l: "Nifty 50", v: "21,345", c: -0.31, flag: "🇮🇳" },
          { l: "S&P 500",  v: "4,892",  c: -0.45, flag: "🇺🇸" },
          { l: "CSI 300",  v: "3,412",  c: -0.18, flag: "🇨🇳" },
          { l: "FTSE 100", v: "7,820",  c: -0.22, flag: "🇬🇧" },
          { l: "Brent Oil",v: "$87.2",  c:  1.82, flag: "🛢️" },
          { l: "Gold",     v: "$2,042", c:  0.82, flag: "🥇" },
        ].map(r => (
          <div key={r.l} style={{ display: "flex", alignItems: "center", gap: 8, padding: "5px 0", borderBottom: "1px solid #0f172a" }}>
            <span>{r.flag}</span>
            <span style={{ flex: 1, color: "#cbd5e1" }}>{r.l}</span>
            <span style={{ fontFamily: "monospace", color: "#f8fafc", fontWeight: 600 }}>{r.v}</span>
            <span style={{ fontFamily: "monospace", color: r.c > 0 ? "#22c55e" : "#ef4444", minWidth: 52, textAlign: "right" }}>{r.c > 0 ? "+" : ""}{r.c.toFixed(2)}%</span>
          </div>
        ))}
      </div>

      {/* HOLDINGS TABLE */}
      <div style={{ gridColumn: "1 / -1", background: "#0d1220", border: "1px solid #1e2a3d", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 14, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span>📁 My Holdings</span>
          <span style={{ color: "#f59e0b", fontSize: 10 }}>⚠ IT Overweight: 36.2% (Target: 30%)</span>
        </div>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #1e2a3d" }}>
              {["Stock", "Sector", "Value", "Weight", "Today", "AI Signal"].map(h => (
                <th key={h} style={{ padding: "6px 10px", textAlign: h === "Value" || h === "Today" ? "right" : "left", color: "#475569", fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 1 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {holdings.map(h => (
              <tr key={h.symbol} style={{ borderBottom: "1px solid #0f172a", transition: "background 0.2s" }}
                onMouseEnter={e => e.currentTarget.style.background = "#ffffff08"}
                onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                <td style={{ padding: "8px 10px", fontWeight: 700, color: "#f8fafc" }}>{h.symbol}</td>
                <td style={{ padding: "8px 10px" }}>
                  <span style={{ background: "#1e2533", color: "#94a3b8", padding: "2px 8px", borderRadius: 4, fontSize: 10 }}>{h.sector}</span>
                </td>
                <td style={{ padding: "8px 10px", textAlign: "right", fontFamily: "monospace", color: "#f8fafc" }}>{fmtINR(h.value)}</td>
                <td style={{ padding: "8px 10px", textAlign: "right" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, justifyContent: "flex-end" }}>
                    <Bar value={h.pct} max={20} color="#f59e0b" height={4} />
                    <span style={{ fontFamily: "monospace", color: "#94a3b8", minWidth: 36, textAlign: "right" }}>{h.pct}%</span>
                  </div>
                </td>
                <td style={{ padding: "8px 10px", textAlign: "right", fontFamily: "monospace", color: h.chg >= 0 ? "#22c55e" : "#ef4444", fontWeight: 600 }}>
                  {h.chg >= 0 ? "+" : ""}{h.chg}%
                </td>
                <td style={{ padding: "8px 10px", color: "#64748b", fontSize: 11 }}>
                  {h.alert && <span style={{ color: h.chg >= 0 ? "#22c55e88" : "#f59e0b88" }}>💡 {h.alert}</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── FAMILY OFFICE OVERVIEW ──────────────────────────────────────────────────

function FamilyOverview({ tick, portfolio, crisisProb }) {
  const totalAUM = portfolio.reduce((s, p) => s + p.aum, 0);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr", gap: 16 }}>
      {/* AUM HEADER */}
      <div style={{ gridColumn: "1 / -1", background: "linear-gradient(135deg, #0d1220, #111827)", border: "1px solid #1e2a3d", borderRadius: 12, padding: "20px 28px", display: "flex", gap: 48, alignItems: "center" }}>
        <div>
          <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 2, marginBottom: 4 }}>Total AUM</div>
          <div style={{ fontSize: 36, fontWeight: 800, fontFamily: "'IBM Plex Mono', monospace" }}>$847.3M</div>
        </div>
        <div style={{ height: 48, width: 1, background: "#1e2a3d" }} />
        <div>
          <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 2, marginBottom: 4 }}>YTD Return</div>
          <div style={{ fontSize: 28, fontWeight: 700, color: "#22c55e" }}>+12.4% <span style={{ fontSize: 13, color: "#64748b" }}>vs +8.2% benchmark</span></div>
        </div>
        <div style={{ height: 48, width: 1, background: "#1e2a3d" }} />
        <div>
          <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 2, marginBottom: 4 }}>Sharpe Ratio</div>
          <div style={{ fontSize: 28, fontWeight: 700, color: "#f59e0b" }}>1.34</div>
        </div>
        <div style={{ height: 48, width: 1, background: "#1e2a3d" }} />
        <div>
          <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 2, marginBottom: 4 }}>Preservation Score</div>
          <div style={{ fontSize: 28, fontWeight: 700, color: "#22c55e" }}>87<span style={{ fontSize: 14, color: "#64748b" }}>/100</span></div>
        </div>
        <div style={{ marginLeft: "auto", background: "#22c55e11", border: "1px solid #22c55e33", borderRadius: 8, padding: "10px 20px", textAlign: "center" }}>
          <div style={{ fontSize: 11, color: "#64748b", marginBottom: 4 }}>3-Gen Wealth Multiplier</div>
          <div style={{ fontSize: 22, fontWeight: 800, color: "#22c55e" }}>13.8x</div>
          <div style={{ fontSize: 10, color: "#22c55e88" }}>✓ ON TRACK</div>
        </div>
      </div>

      {/* GEO ALLOCATION */}
      <div style={{ background: "#0d1220", border: "1px solid #1e2a3d", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 16 }}>🌍 Geographic Allocation</div>
        {portfolio.map(p => (
          <div key={p.region} style={{ marginBottom: 14 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
              <span style={{ color: "#cbd5e1", fontSize: 12 }}>{p.region}</span>
              <div style={{ display: "flex", gap: 12 }}>
                <span style={{ fontFamily: "monospace", color: "#f8fafc", fontWeight: 600 }}>{fmtM(p.aum)}</span>
                <span style={{ fontFamily: "monospace", color: p.change >= 0 ? "#22c55e" : "#ef4444", minWidth: 48, textAlign: "right" }}>{p.change >= 0 ? "+" : ""}{p.change}%</span>
              </div>
            </div>
            <div style={{ background: "#1e2533", borderRadius: 4, height: 8, overflow: "hidden" }}>
              <div style={{ width: `${p.pct}%`, height: "100%", background: p.color, borderRadius: 4, transition: "width 0.8s" }} />
            </div>
            <div style={{ fontSize: 10, color: "#475569", marginTop: 3 }}>{p.pct}% of AUM</div>
          </div>
        ))}
      </div>

      {/* CORRELATION ALERT */}
      <div style={{ background: "#0d1220", border: `1px solid ${crisisProb > 0.6 ? "#f59e0b44" : "#1e2a3d"}`, borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11, color: "#f59e0b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 12 }}>⚡ Correlation Breakdown Alert</div>
        <CrisisGauge probability={crisisProb} />
        <div style={{ marginTop: 12, padding: "10px 14px", background: "#f59e0b11", borderRadius: 8, border: "1px solid #f59e0b22" }}>
          <div style={{ fontSize: 12, color: "#fcd34d", marginBottom: 6 }}>Portfolio Correlation: <strong>0.72</strong> ↑ from 0.64 last week</div>
          <div style={{ fontSize: 11, color: "#94a3b8" }}>If crisis hits: Expected drawdown risk +8% → Diversification benefit reduced 40%</div>
        </div>
        <div style={{ marginTop: 10 }}>
          {["Reduce equity 10-15%", "Add Gold +5%", "Hedge via Nifty Puts"].map(a => (
            <div key={a} style={{ display: "flex", alignItems: "center", gap: 6, padding: "4px 0", color: "#94a3b8", fontSize: 11 }}>
              <span style={{ color: "#f59e0b" }}>→</span> {a}
            </div>
          ))}
        </div>
      </div>

      {/* MACRO INTELLIGENCE */}
      <div style={{ background: "#0d1220", border: "1px solid #1e2a3d", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 14 }}>🏦 Central Bank Watch</div>
        {[
          { bank: "US Fed", rate: "5.25-5.50%", status: "Hold", color: "#f59e0b" },
          { bank: "RBI India", rate: "6.50%", color: "#22c55e", status: "Hold" },
          { bank: "PBOC China", rate: "3.45%", color: "#3b82f6", status: "Easing" },
          { bank: "ECB Europe", rate: "4.50%", color: "#8b5cf6", status: "Hold" },
          { bank: "BOJ Japan", rate: "0.10%", color: "#ef4444", status: "Hiking" },
        ].map(b => (
          <div key={b.bank} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0", borderBottom: "1px solid #0f172a" }}>
            <div style={{ width: 3, height: 28, background: b.color, borderRadius: 2, flexShrink: 0 }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 12, color: "#f8fafc", fontWeight: 600 }}>{b.bank}</div>
              <div style={{ fontSize: 10, color: "#64748b" }}>{b.rate}</div>
            </div>
            <span style={{ fontSize: 10, padding: "2px 8px", background: b.color + "22", color: b.color, borderRadius: 4, fontWeight: 600 }}>{b.status}</span>
          </div>
        ))}
      </div>

      {/* SCENARIO ANALYSIS */}
      <div style={{ gridColumn: "1 / -1", background: "#0d1220", border: "1px solid #1e2a3d", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 16 }}>🎯 Scenario Analysis</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14 }}>
          {[
            { title: "Fed Hikes 50bps", impact: -8.4, pct: -0.99, items: ["DXY +2.5%", "EM outflows", "Nifty -2.1%", "Gold +1.2%"], color: "#ef4444" },
            { title: "Oil → $100/barrel", impact: -12.1, pct: -1.43, items: ["INR -2.3%", "OMCs -5%", "Airlines -8%", "IT Exporters +3%"], color: "#f59e0b" },
            { title: "China Stimulus", impact: 15.2, pct: 1.79, items: ["Commodities +8%", "India Metals +6%", "Singapore REITs +3%", "BHP +8%"], color: "#22c55e" },
          ].map(s => (
            <div key={s.title} style={{ background: s.color + "0a", border: `1px solid ${s.color}33`, borderRadius: 10, padding: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#f8fafc", marginBottom: 8 }}>{s.title}</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: s.color, fontFamily: "monospace", marginBottom: 6 }}>
                {s.impact >= 0 ? "+" : ""}${Math.abs(s.impact).toFixed(1)}M ({s.pct >= 0 ? "+" : ""}{s.pct}%)
              </div>
              <div style={{ borderTop: "1px solid #1e2a3d", paddingTop: 10, marginTop: 4 }}>
                {s.items.map(item => (
                  <div key={item} style={{ fontSize: 11, color: "#94a3b8", padding: "2px 0" }}>• {item}</div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── PMS OVERVIEW ─────────────────────────────────────────────────────────────

function PMSOverview({ tick, factors, crisisProb }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 16 }}>
      {/* AUM STRIP */}
      <div style={{ gridColumn: "1 / -1", background: "linear-gradient(135deg, #0d1220, #111827)", border: "1px solid #1e2a3d", borderRadius: 12, padding: "16px 24px", display: "flex", gap: 32, alignItems: "center" }}>
        {[
          { l: "AUM", v: "₹847 Cr" },
          { l: "NAV", v: "₹184.23" },
          { l: "Today", v: "+0.18%", c: true },
          { l: "vs Nifty YTD", v: "+2.34%", c: true },
          { l: "Sharpe", v: "1.67" },
          { l: "Sortino", v: "2.14" },
          { l: "Max DD", v: "-8.2%", neg: true },
          { l: "Alpha", v: "3.2%", c: true },
          { l: "Info Ratio", v: "1.21" },
        ].map((m, i) => (
          <div key={m.l}>
            {i > 0 && <div style={{ position: "absolute" }} />}
            <div style={{ fontSize: 10, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 2 }}>{m.l}</div>
            <div style={{ fontSize: 16, fontWeight: 700, fontFamily: "monospace", color: m.c ? "#22c55e" : m.neg ? "#ef4444" : "#f8fafc" }}>{m.v}</div>
          </div>
        ))}
        <div style={{ marginLeft: "auto" }}>
          <CrisisGauge probability={crisisProb} />
        </div>
      </div>

      {/* ALPHA ATTRIBUTION */}
      <div style={{ gridColumn: "span 2", background: "#0d1220", border: "1px solid #1e2a3d", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 16 }}>📊 Today's Alpha Attribution</div>
        <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 16 }}>
          <span style={{ fontSize: 28, fontWeight: 800, color: "#22c55e", fontFamily: "monospace" }}>+0.23%</span>
          <span style={{ fontSize: 13, color: "#64748b" }}>vs Nifty today</span>
        </div>
        {[
          { source: "Stock Selection", value: 0.18, color: "#22c55e" },
          { source: "Sector Allocation", value: 0.03, color: "#3b82f6" },
          { source: "Market Timing", value: 0.02, color: "#8b5cf6" },
          { source: "Factor Exposure", value: 0.00, color: "#64748b" },
        ].map(a => (
          <div key={a.source} style={{ marginBottom: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <span style={{ fontSize: 12, color: "#94a3b8" }}>{a.source}</span>
              <span style={{ fontFamily: "monospace", color: a.value > 0 ? "#22c55e" : "#ef4444", fontWeight: 600 }}>
                {a.value >= 0 ? "+" : ""}{(a.value * 100).toFixed(2)} bps
              </span>
            </div>
            <div style={{ background: "#1e2533", borderRadius: 3, height: 5 }}>
              <div style={{ width: `${Math.abs(a.value) / 0.18 * 100}%`, height: "100%", background: a.color, borderRadius: 3 }} />
            </div>
          </div>
        ))}
      </div>

      {/* FACTOR EXPOSURE */}
      <div style={{ gridColumn: "span 2", background: "#0d1220", border: "1px solid #1e2a3d", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 14 }}>⚖ Factor Exposure</div>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #1e2a3d" }}>
              {["Factor", "Current", "Target", "Benchmark", "Status"].map(h => (
                <th key={h} style={{ padding: "4px 8px", textAlign: h === "Factor" ? "left" : "center", color: "#475569", fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: 1 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {factors.map(f => (
              <tr key={f.factor} style={{ borderBottom: "1px solid #0f172a" }}>
                <td style={{ padding: "7px 8px", color: "#cbd5e1", fontWeight: 600, fontSize: 12 }}>{f.factor}</td>
                <td style={{ padding: "7px 8px", textAlign: "center", fontFamily: "monospace", color: "#f8fafc", fontSize: 12 }}>{f.current.toFixed(2)}</td>
                <td style={{ padding: "7px 8px", textAlign: "center", fontFamily: "monospace", color: "#64748b", fontSize: 12 }}>{f.target.toFixed(2)}</td>
                <td style={{ padding: "7px 8px", textAlign: "center", fontFamily: "monospace", color: "#475569", fontSize: 12 }}>{f.benchmark.toFixed(2)}</td>
                <td style={{ padding: "7px 8px", textAlign: "center" }}>
                  <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 4, fontWeight: 600,
                    background: f.status === "ok" ? "#22c55e22" : "#f59e0b22",
                    color: f.status === "ok" ? "#22c55e" : "#f59e0b"
                  }}>{f.status === "ok" ? "✓ ON TARGET" : "⚠ ADJUST"}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* LIVE TRANSMISSION */}
      <div style={{ gridColumn: "span 2", background: "#0d1220", border: "1px solid #ef444433", borderLeft: "3px solid #ef4444", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11, color: "#ef4444", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 14 }}>🔴 LIVE: Oil Surge Impact</div>
        <div style={{ fontSize: 20, fontWeight: 700, color: "#f8fafc", marginBottom: 14 }}>Brent +1.8% → <span style={{ color: "#f59e0b" }}>$87.2</span></div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          <div>
            <div style={{ fontSize: 11, color: "#64748b", marginBottom: 6 }}>IMMEDIATE (T+0)</div>
            {[["OMCs (IOC, BPCL)", "-1.2% to -1.8%", "neg"], ["Airlines (IndiGo)", "-0.8% to -1.5%", "neg"], ["Logistics (VRL)", "-0.5%", "neg"]].map(([l, v, t]) => (
              <div key={l} style={{ display: "flex", justifyContent: "space-between", padding: "3px 0", fontSize: 11 }}>
                <span style={{ color: "#94a3b8" }}>{l}</span>
                <span style={{ color: "#ef4444", fontFamily: "monospace" }}>{v}</span>
              </div>
            ))}
          </div>
          <div>
            <div style={{ fontSize: 11, color: "#64748b", marginBottom: 6 }}>BENEFICIARIES</div>
            {[["IT Exporters", "+0.5-1.2%"], ["Pharma Exports", "+0.3-0.8%"]].map(([l, v]) => (
              <div key={l} style={{ display: "flex", justifyContent: "space-between", padding: "3px 0", fontSize: 11 }}>
                <span style={{ color: "#94a3b8" }}>{l}</span>
                <span style={{ color: "#22c55e", fontFamily: "monospace" }}>{v}</span>
              </div>
            ))}
            <div style={{ marginTop: 10, padding: 8, background: "#0f172a", borderRadius: 6 }}>
              <div style={{ fontSize: 10, color: "#64748b" }}>YOUR PORTFOLIO IMPACT</div>
              <div style={{ fontSize: 14, color: "#ef4444", fontFamily: "monospace", fontWeight: 700 }}>-₹2.8 Cr (-0.33%)</div>
            </div>
          </div>
        </div>
      </div>

      {/* TOP HOLDINGS */}
      <div style={{ gridColumn: "span 2", background: "#0d1220", border: "1px solid #1e2a3d", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 14 }}>📁 Top Positions</div>
        {[
          { sym: "HDFC Bank", wt: 8.2, alpha: 0.21, beta: 0.92, active: 3.2 },
          { sym: "TCS", wt: 7.1, alpha: 0.18, beta: 0.85, active: 2.1 },
          { sym: "Dr. Reddy's", wt: 6.4, alpha: 0.42, beta: 0.71, active: 1.4 },
          { sym: "Infosys", wt: 5.8, alpha: 0.15, beta: 0.88, active: 0.8 },
          { sym: "L&T", wt: 5.1, alpha: 0.31, beta: 1.10, active: 0.1 },
        ].map(p => (
          <div key={p.sym} style={{ display: "flex", gap: 10, alignItems: "center", padding: "6px 0", borderBottom: "1px solid #0f172a" }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 12, color: "#f8fafc", fontWeight: 700 }}>{p.sym}</div>
              <div style={{ fontSize: 10, color: "#64748b" }}>Wt: {p.wt}% | Beta: {p.beta}</div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 12, color: "#22c55e", fontFamily: "monospace" }}>α +{p.alpha}%</div>
              <div style={{ fontSize: 10, color: "#64748b" }}>Active: {p.active}%</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── CORRELATION DASHBOARD ────────────────────────────────────────────────────

function CorrelationDashboard({ tick }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16 }}>
      {/* MATRIX */}
      <div style={{ background: "#0d1220", border: "1px solid #1e2a3d", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 16, display: "flex", justifyContent: "space-between" }}>
          <span>🔗 Dynamic Correlation Matrix (30-Day Rolling)</span>
          <span style={{ color: "#22c55e", fontSize: 10 }}>● LIVE</span>
        </div>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ padding: "6px 10px", color: "#475569", fontSize: 10, textAlign: "left" }}></th>
              {ASSETS.map(a => <th key={a} style={{ padding: "6px 4px", color: "#64748b", fontSize: 10, textAlign: "center", fontFamily: "monospace" }}>{a}</th>)}
            </tr>
          </thead>
          <tbody>
            {ASSETS.map((rowAsset, i) => (
              <tr key={rowAsset}>
                <td style={{ padding: "6px 10px", color: "#94a3b8", fontSize: 11, fontWeight: 600, fontFamily: "monospace", borderRight: "1px solid #1e2a3d" }}>{rowAsset}</td>
                {ASSETS.map((colAsset, j) => (
                  <CorrCell key={colAsset} value={corrMatrix[rowAsset][j]} />
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ display: "flex", gap: 16, marginTop: 14, fontSize: 10 }}>
          {[[-1, "#8b5cf6", "Strong -ve"], [-0.5, "#3b82f6", "Weak -ve"], [0, "#64748b", "Neutral"], [0.5, "#f59e0b", "Weak +ve"], [0.9, "#ef4444", "Strong +ve"]].map(([v, c, l]) => (
            <div key={l} style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <div style={{ width: 12, height: 12, background: c + "44", border: `1px solid ${c}`, borderRadius: 2 }} />
              <span style={{ color: "#64748b" }}>{l}</span>
            </div>
          ))}
        </div>
      </div>

      {/* CORRELATION HIGHLIGHTS */}
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div style={{ background: "#0d1220", border: "1px solid #1e2a3d", borderRadius: 12, padding: 20 }}>
          <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 14 }}>⚠ Key Relationships</div>
          {[
            { pair: "NIFTY ↔ S&P 500", corr: 0.68, trend: "↑ from 0.62", alert: true },
            { pair: "DXY ↔ GOLD", corr: -0.73, trend: "Stable", alert: false },
            { pair: "OIL ↔ DXY", corr: 0.45, trend: "↑ from 0.38", alert: true },
            { pair: "NIFTY ↔ OIL", corr: -0.42, trend: "Stable", alert: false },
            { pair: "CSI300 ↔ FTSE", corr: 0.48, trend: "↓ from 0.55", alert: false },
            { pair: "DXY ↔ NIFTY", corr: -0.58, trend: "Deepening", alert: true },
          ].map(r => (
            <div key={r.pair} style={{ display: "flex", alignItems: "center", gap: 8, padding: "7px 0", borderBottom: "1px solid #0f172a" }}>
              <div style={{ width: 3, height: 28, background: corrColor(r.corr), borderRadius: 2, flexShrink: 0 }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, color: "#f8fafc", fontWeight: 600 }}>{r.pair}</div>
                <div style={{ fontSize: 10, color: "#475569" }}>{r.trend}</div>
              </div>
              <div style={{ fontFamily: "monospace", color: corrColor(r.corr), fontWeight: 700, fontSize: 14 }}>{r.corr.toFixed(2)}</div>
              {r.alert && <span style={{ fontSize: 10, color: "#f59e0b" }}>⚡</span>}
            </div>
          ))}
        </div>

        <div style={{ background: "#0d1220", border: "1px solid #1e2a3d", borderRadius: 12, padding: 20 }}>
          <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 14 }}>🌏 Regional vs US</div>
          {regionCorrelation.map(r => (
            <div key={r.region} style={{ marginBottom: 12 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ fontSize: 12, color: "#cbd5e1" }}>{r.region}</span>
                <span style={{ fontFamily: "monospace", color: corrColor(r.corr), fontWeight: 700 }}>{r.corr.toFixed(2)}</span>
              </div>
              <div style={{ background: "#1e2533", borderRadius: 3, height: 6 }}>
                <div style={{ width: `${r.corr * 100}%`, height: "100%", background: corrColor(r.corr), borderRadius: 3, transition: "width 0.8s" }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── CRISIS DASHBOARD ─────────────────────────────────────────────────────────

function CrisisDashboard({ crisisProb, signals }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
      <div style={{ gridColumn: "span 1", background: "#0d1220", border: `2px solid ${crisisProb > 0.6 ? "#ef4444" : "#f59e0b"}`, borderRadius: 12, padding: 24, textAlign: "center" }}>
        <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 2, marginBottom: 16 }}>Crisis Probability Index</div>
        <CrisisGauge probability={crisisProb} />
        <div style={{ marginTop: 12, fontSize: 12, color: "#94a3b8" }}>Correlation spike expected in <strong style={{ color: "#f8fafc" }}>5 days</strong></div>
        <div style={{ marginTop: 8, fontSize: 11, color: "#64748b" }}>If triggered: SPX-Nifty → <span style={{ color: "#ef4444" }}>0.85+</span></div>
        <div style={{ marginTop: 16, padding: "10px", background: "#ef444411", borderRadius: 8, border: "1px solid #ef444444" }}>
          <div style={{ fontSize: 11, color: "#fca5a5" }}>Model Accuracy: <strong>73%</strong> | False Positive: 27%</div>
        </div>
      </div>

      <div style={{ background: "#0d1220", border: "1px solid #1e2a3d", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 16 }}>⚡ Signal Breakdown</div>
        {signals.map(s => (
          <div key={s.name} style={{ marginBottom: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div style={{ width: 8, height: 8, borderRadius: "50%", background: s.activated ? "#ef4444" : "#22c55e", boxShadow: s.activated ? "0 0 8px #ef4444" : "none" }} />
                <span style={{ fontSize: 12, color: "#cbd5e1" }}>{s.icon} {s.name}</span>
              </div>
              <span style={{ fontSize: 10, fontFamily: "monospace", color: "#64748b" }}>Weight: {(s.weight * 100).toFixed(0)}%</span>
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <div style={{ flex: 1, background: "#1e2533", borderRadius: 3, height: 8 }}>
                <div style={{ width: `${Math.min(s.value / s.threshold, 1.5) / 1.5 * 100}%`, height: "100%", background: s.activated ? "#ef4444" : "#22c55e", borderRadius: 3, transition: "width 0.5s" }} />
              </div>
              <span style={{ fontFamily: "monospace", color: s.activated ? "#ef4444" : "#22c55e", fontSize: 11, minWidth: 60, textAlign: "right" }}>
                {s.value.toFixed(2)} / {s.threshold}
              </span>
            </div>
            <div style={{ fontSize: 10, color: "#475569", marginTop: 3 }}>
              {s.activated ? `🔴 TRIGGERED — ${(s.weight * 100).toFixed(0)}% contribution to risk` : `✅ Below threshold`}
            </div>
          </div>
        ))}
      </div>

      <div style={{ background: "#0d1220", border: "1px solid #1e2a3d", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 16 }}>🎯 Recommended Actions</div>
        {[
          { action: "Reduce equity by 10-15%", priority: "HIGH", detail: "Move to cash + gold" },
          { action: "Add Gold +5%", priority: "HIGH", detail: "Safe haven hedge" },
          { action: "Buy Nifty Put (21,500)", priority: "MEDIUM", detail: "1M expiry, at-the-money" },
          { action: "Reduce Leverage", priority: "MEDIUM", detail: "If margin used" },
          { action: "Prepare Buy List", priority: "LOW", detail: "Post-crisis opportunities" },
        ].map(a => (
          <div key={a.action} style={{ display: "flex", gap: 10, padding: "8px 0", borderBottom: "1px solid #0f172a" }}>
            <span style={{ fontSize: 10, padding: "2px 8px", height: 18, display: "flex", alignItems: "center", borderRadius: 4, fontWeight: 700, flexShrink: 0,
              background: a.priority === "HIGH" ? "#ef444422" : a.priority === "MEDIUM" ? "#f59e0b22" : "#22c55e22",
              color: a.priority === "HIGH" ? "#ef4444" : a.priority === "MEDIUM" ? "#f59e0b" : "#22c55e",
            }}>{a.priority}</span>
            <div>
              <div style={{ fontSize: 12, color: "#f8fafc", fontWeight: 600 }}>{a.action}</div>
              <div style={{ fontSize: 10, color: "#64748b" }}>{a.detail}</div>
            </div>
          </div>
        ))}

        <div style={{ marginTop: 14, padding: 12, background: "#0f172a", borderRadius: 8 }}>
          <div style={{ fontSize: 11, color: "#64748b", marginBottom: 6 }}>Historical Track Record</div>
          <div style={{ display: "flex", gap: 16 }}>
            <div><div style={{ fontSize: 16, fontWeight: 800, color: "#22c55e" }}>11/15</div><div style={{ fontSize: 10, color: "#64748b" }}>Correct</div></div>
            <div><div style={{ fontSize: 16, fontWeight: 800, color: "#f59e0b" }}>73%</div><div style={{ fontSize: 10, color: "#64748b" }}>Accuracy</div></div>
            <div><div style={{ fontSize: 16, fontWeight: 800, color: "#3b82f6" }}>5.2d</div><div style={{ fontSize: 10, color: "#64748b" }}>Avg Lead</div></div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── TRANSMISSION DASHBOARD ───────────────────────────────────────────────────

function TransmissionDashboard({ chain, leadLag, regions }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
      {/* TRANSMISSION CHAIN */}
      <div style={{ background: "#0d1220", border: "1px solid #1e2a3d", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 16 }}>🔗 US Fed Hike → India Transmission</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          {chain.map((step, i) => (
            <div key={i} style={{ display: "flex", gap: 12 }}>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 32 }}>
                <div style={{ width: 32, height: 32, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700, flexShrink: 0,
                  background: step.type === "trigger" ? "#ef444422" : step.type === "positive" ? "#22c55e22" : step.type === "negative" ? "#ef444411" : step.type === "currency" ? "#3b82f622" : "#f59e0b22",
                  border: `2px solid ${step.type === "trigger" ? "#ef4444" : step.type === "positive" ? "#22c55e" : step.type === "negative" ? "#ef4444" : step.type === "currency" ? "#3b82f6" : "#f59e0b"}`,
                }}>
                  {step.type === "trigger" ? "⚡" : step.type === "positive" ? "↑" : step.type === "negative" ? "↓" : step.type === "currency" ? "💱" : "→"}
                </div>
                {i < chain.length - 1 && <div style={{ width: 2, flex: 1, background: "#1e2a3d", margin: "2px 0", minHeight: 20 }} />}
              </div>
              <div style={{ paddingBottom: 16, flex: 1 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div style={{ fontSize: 13, color: "#f8fafc", fontWeight: 700 }}>{step.node}</div>
                  <span style={{ fontSize: 10, color: "#64748b", background: "#0f172a", padding: "2px 8px", borderRadius: 4 }}>{step.lag}</span>
                </div>
                <div style={{ fontSize: 11, color: step.type === "positive" ? "#22c55e" : step.type === "negative" ? "#ef4444" : "#f59e0b", marginTop: 2 }}>{step.impact}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* LEAD-LAG RELATIONSHIPS */}
      <div style={{ background: "#0d1220", border: "1px solid #1e2a3d", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 16 }}>⏱ Research-Backed Lead-Lag</div>
        {leadLag.map(r => (
          <div key={r.leading} style={{ marginBottom: 16, padding: 14, background: "#0f172a", borderRadius: 8, border: "1px solid #1e2a3d" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 13, color: "#f8fafc", fontWeight: 700 }}>{r.leading}</span>
                <span style={{ color: "#64748b", fontSize: 12 }}>→</span>
                <span style={{ fontSize: 13, color: "#f59e0b", fontWeight: 700 }}>{r.lagging}</span>
              </div>
              <span style={{ background: "#22c55e22", color: "#22c55e", fontSize: 10, padding: "2px 8px", borderRadius: 4, fontWeight: 600 }}>
                {(r.strength * 100).toFixed(0)}% strength
              </span>
            </div>
            <div style={{ display: "flex", gap: 16, fontSize: 11 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ color: "#64748b" }}>Lead Time:</span>
                <span style={{ color: "#f8fafc", fontFamily: "monospace", fontWeight: 700 }}>{r.lagDays === 0 ? "Same day" : `${r.lagDays}d`}</span>
              </div>
              <Bar value={r.strength} max={1} color="#22c55e" height={4} />
            </div>
          </div>
        ))}
      </div>

      {/* GLOBAL MACRO DEPENDENCIES */}
      <div style={{ gridColumn: "1 / -1", background: "#0d1220", border: "1px solid #1e2a3d", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 16 }}>🌐 Global Macro Dependency Map</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 12 }}>
          {[
            { country: "🇮🇳 India", drivers: [{ l: "S&P 500", v: 0.68 }, { l: "Oil", v: -0.42 }, { l: "DXY", v: -0.58 }, { l: "China PMI", v: 0.45 }], key: "Oil importer, IT exports" },
            { country: "🇨🇳 China", drivers: [{ l: "S&P 500", v: 0.54 }, { l: "Iron Ore", v: 0.89 }, { l: "USD/CNY", v: -0.71 }, { l: "Credit Imp", v: 0.82 }], key: "Commodity demand engine" },
            { country: "🇸🇬 Singapore", drivers: [{ l: "S&P 500", v: 0.61 }, { l: "NODX", v: 0.74 }, { l: "SGD/USD", v: -0.62 }, { l: "REIT yield", v: 0.58 }], key: "ASEAN trade barometer" },
            { country: "🇿🇦 Africa", drivers: [{ l: "Oil", v: 0.72 }, { l: "Gold", v: 0.65 }, { l: "China PMI", v: 0.58 }, { l: "DXY", v: -0.68 }], key: "Commodity-driven FX" },
            { country: "🇪🇺 Europe", drivers: [{ l: "S&P 500", v: 0.82 }, { l: "EUR/USD", v: 0.78 }, { l: "China PMI", v: 0.48 }, { l: "Energy", v: -0.55 }], key: "Highly US-correlated" },
          ].map(c => (
            <div key={c.country} style={{ background: "#0f172a", borderRadius: 10, padding: 14, border: "1px solid #1e2a3d" }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: "#f8fafc", marginBottom: 4 }}>{c.country}</div>
              <div style={{ fontSize: 10, color: "#64748b", marginBottom: 10, fontStyle: "italic" }}>{c.key}</div>
              {c.drivers.map(d => (
                <div key={d.l} style={{ display: "flex", justifyContent: "space-between", padding: "3px 0", fontSize: 11 }}>
                  <span style={{ color: "#94a3b8" }}>{d.l}</span>
                  <span style={{ fontFamily: "monospace", color: corrColor(d.v), fontWeight: 600 }}>{d.v.toFixed(2)}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── DEEP PORTFOLIO PAGES ─────────────────────────────────────────────────────

function RetailPortfolioDeep({ holdings }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
      <div style={{ background: "#0d1220", border: "1px solid #1e2a3d", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 14 }}>🔄 Smart Rebalancing Engine</div>
        <div style={{ padding: "10px 14px", background: "#f59e0b11", border: "1px solid #f59e0b33", borderRadius: 8, marginBottom: 16 }}>
          <div style={{ fontSize: 12, color: "#fcd34d", fontWeight: 600 }}>Deviation from target: 8.2% — REBALANCE RECOMMENDED</div>
        </div>
        {[
          { asset: "IT Stocks", current: 36.2, target: 30.0, action: "SELL", amount: "₹2.9L", color: "#ef4444" },
          { asset: "Banks", current: 17.8, target: 22.0, action: "BUY", amount: "₹2.0L", color: "#22c55e" },
          { asset: "Pharma", current: 8.3, target: 12.0, action: "BUY", amount: "₹1.8L", color: "#22c55e" },
          { asset: "Gold/ETF", current: 0.0, target: 5.0, action: "BUY", amount: "₹2.4L", color: "#22c55e" },
        ].map(r => (
          <div key={r.asset} style={{ display: "flex", gap: 10, alignItems: "center", padding: "8px 0", borderBottom: "1px solid #0f172a" }}>
            <span style={{ fontSize: 10, padding: "2px 8px", background: r.color + "22", color: r.color, borderRadius: 4, fontWeight: 700, minWidth: 36, textAlign: "center" }}>{r.action}</span>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 12, color: "#f8fafc" }}>{r.asset}</div>
              <div style={{ fontSize: 10, color: "#64748b" }}>{r.current}% → {r.target}%</div>
            </div>
            <span style={{ fontFamily: "monospace", color: r.color, fontWeight: 700 }}>{r.amount}</span>
          </div>
        ))}
        <div style={{ marginTop: 14, padding: 12, background: "#0f172a", borderRadius: 8 }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
            <span style={{ color: "#64748b" }}>Transaction Costs</span>
            <span style={{ color: "#f8fafc", fontFamily: "monospace" }}>₹12,400</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginTop: 4 }}>
            <span style={{ color: "#64748b" }}>Tax Savings (Harvest)</span>
            <span style={{ color: "#22c55e", fontFamily: "monospace" }}>₹9,000</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginTop: 8, paddingTop: 8, borderTop: "1px solid #1e2a3d", fontWeight: 700 }}>
            <span style={{ color: "#f8fafc" }}>Net Benefit</span>
            <span style={{ color: "#22c55e", fontFamily: "monospace" }}>+0.18% annually</span>
          </div>
        </div>
      </div>

      <div style={{ background: "#0d1220", border: "1px solid #1e2a3d", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 14 }}>📈 Goal Tracker</div>
        {[
          { goal: "Retirement 2045", current: 47.2, target: 180, pct: 26, color: "#22c55e", status: "ON TRACK" },
          { goal: "Child Education 2032", current: 12.1, target: 35, pct: 35, color: "#3b82f6", status: "ON TRACK" },
          { goal: "House Purchase 2028", current: 8.4, target: 40, pct: 21, color: "#f59e0b", status: "BEHIND" },
        ].map(g => (
          <div key={g.goal} style={{ marginBottom: 18 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
              <span style={{ fontSize: 13, color: "#f8fafc", fontWeight: 600 }}>{g.goal}</span>
              <span style={{ fontSize: 11, color: g.color, fontWeight: 700 }}>{g.status}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#64748b", marginBottom: 6 }}>
              <span>Current: {fmtINR(g.current * 100000)}</span>
              <span>Target: {fmtINR(g.target * 100000)}</span>
            </div>
            <div style={{ background: "#1e2533", borderRadius: 4, height: 10, overflow: "hidden" }}>
              <div style={{ width: `${g.pct}%`, height: "100%", background: g.color, borderRadius: 4, transition: "width 1s" }} />
            </div>
            <div style={{ fontSize: 10, color: "#475569", marginTop: 3 }}>{g.pct}% funded</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function FamilyPortfolioDeep({ portfolio }) {
  return (
    <div style={{ background: "#0d1220", border: "1px solid #1e2a3d", borderRadius: 12, padding: 20 }}>
      <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 16 }}>🏛️ Generational Wealth Dashboard</div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 20 }}>
        {[
          { label: "Real Return (1Y)", value: "+8.2%", sub: "After 4.5% inflation", color: "#22c55e" },
          { label: "Real Return (5Y)", value: "+9.1%", sub: "CAGR, after inflation", color: "#22c55e" },
          { label: "Drawdown (Max)", value: "-18.2%", sub: "2020 COVID, 8mo recovery", color: "#ef4444" },
          { label: "Wealth 3-Gen", value: "13.8x", sub: "At current trajectory", color: "#f59e0b" },
        ].map(m => (
          <div key={m.label} style={{ background: "#0f172a", borderRadius: 10, padding: 16, border: "1px solid #1e2a3d" }}>
            <div style={{ fontSize: 10, color: "#64748b", marginBottom: 6, textTransform: "uppercase", letterSpacing: 1 }}>{m.label}</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: m.color, fontFamily: "monospace" }}>{m.value}</div>
            <div style={{ fontSize: 10, color: "#475569", marginTop: 4 }}>{m.sub}</div>
          </div>
        ))}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        {portfolio.map(p => (
          <div key={p.region} style={{ background: "#0f172a", borderRadius: 8, padding: 14, border: `1px solid ${p.color}22`, display: "flex", gap: 12, alignItems: "center" }}>
            <div style={{ width: 4, height: 48, background: p.color, borderRadius: 2, flexShrink: 0 }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13, color: "#f8fafc", fontWeight: 700 }}>{p.region}</div>
              <div style={{ fontSize: 20, fontWeight: 800, color: p.color, fontFamily: "monospace" }}>{fmtM(p.aum)}</div>
              <Bar value={p.pct} max={50} color={p.color} height={5} />
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 18, fontWeight: 700, fontFamily: "monospace", color: p.change >= 0 ? "#22c55e" : "#ef4444" }}>{p.change >= 0 ? "+" : ""}{p.change}%</div>
              <div style={{ fontSize: 10, color: "#64748b" }}>{p.pct}% of AUM</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function PMSPortfolioDeep({ factors }) {
  return (
    <div style={{ background: "#0d1220", border: "1px solid #1e2a3d", borderRadius: 12, padding: 20 }}>
      <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 16 }}>📊 Multi-Factor Risk Model</div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 12 }}>
        {factors.map(f => (
          <div key={f.factor} style={{ background: "#0f172a", borderRadius: 10, padding: 14, border: `1px solid ${f.status === "ok" ? "#22c55e22" : "#f59e0b22"}` }}>
            <div style={{ fontSize: 11, color: "#64748b", marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>{f.factor}</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: "#f8fafc", fontFamily: "monospace" }}>{f.current.toFixed(2)}</div>
            <div style={{ fontSize: 10, color: "#475569", marginTop: 4 }}>Target: {f.target.toFixed(2)}</div>
            <div style={{ marginTop: 8 }}>
              <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 4, fontWeight: 600,
                background: f.status === "ok" ? "#22c55e22" : "#f59e0b22",
                color: f.status === "ok" ? "#22c55e" : "#f59e0b" }}>
                {f.status === "ok" ? "✓ OK" : "⚠ ADJUST"}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
