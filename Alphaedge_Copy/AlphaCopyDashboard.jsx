import { useState, useEffect, useCallback, useRef } from "react";

// ─── Mock data (replace with real WebSocket/API calls) ─────────────────────
const MOCK_STATE = {
  hyperliquid: {
    allocated: 10000,
    equity: 10847.32,
    peak: 11200.0,
    positions: [
      { id: "hl-1", symbol: "BTC", side: "LONG", entry: 94210, ltp: 96540, size: 1250, sl: 89500, tp: 102000, source: "0xA3f1…", opened: "09:14", trailing: 91200 },
      { id: "hl-2", symbol: "ETH", side: "SHORT", entry: 3410, ltp: 3298, size: 820, sl: 3615, tp: 3100, source: "0xB7c2…", opened: "11:32", trailing: 3504 },
    ],
    total_trades: 47, wins: 31, halted: false,
  },
  binance: {
    allocated: 10000,
    equity: 9612.18,
    peak: 10100.0,
    positions: [
      { id: "bn-1", symbol: "SOL", side: "LONG", entry: 178.4, ltp: 182.1, size: 950, sl: 168.0, tp: 198.0, source: "UID:9A8F…", opened: "08:52", trailing: 175.2 },
    ],
    total_trades: 33, wins: 18, halted: false,
  },
  polymarket: {
    allocated: 10000,
    equity: 10291.55,
    peak: 10291.55,
    positions: [
      { id: "pm-1", symbol: "BTC>$100k Mar", side: "YES", entry: 0.61, ltp: 0.74, size: 400, sl: 0.30, tp: 0.92, source: "0xFr3n…", opened: "2d ago", trailing: null },
      { id: "pm-2", symbol: "Fed Cut Q1", side: "NO", entry: 0.38, ltp: 0.29, size: 250, sl: 0.65, tp: 0.10, source: "0xWhal…", opened: "3d ago", trailing: null },
    ],
    total_trades: 22, wins: 14, halted: false,
  }
};

const PLATFORM_META = {
  hyperliquid: { label: "Hyperliquid", short: "HL", accent: "#00d4ff", icon: "◈" },
  binance:     { label: "Binance",     short: "BN", accent: "#f0b90b", icon: "⬡" },
  polymarket:  { label: "Polymarket",  short: "PM", accent: "#9b59b6", icon: "◉" },
};

function calcPnl(pos) {
  if (pos.side === "LONG" || pos.side === "YES") {
    return ((pos.ltp - pos.entry) / pos.entry) * pos.size;
  }
  return ((pos.entry - pos.ltp) / pos.entry) * pos.size;
}

function calcRR(pos) {
  const risk   = Math.abs(pos.entry - pos.sl);
  const reward = Math.abs(pos.tp   - pos.entry);
  return risk > 0 ? (reward / risk).toFixed(2) : "—";
}

function calcPnlPct(pos) {
  if (pos.side === "LONG" || pos.side === "YES")
    return ((pos.ltp - pos.entry) / pos.entry * 100).toFixed(2);
  return ((pos.entry - pos.ltp) / pos.entry * 100).toFixed(2);
}

// ─── Sparkline component ──────────────────────────────────────────────────
function Spark({ values, color }) {
  if (!values || values.length < 2) return null;
  const max = Math.max(...values), min = Math.min(...values);
  const range = max - min || 1;
  const w = 80, h = 28;
  const pts = values.map((v, i) => {
    const x = (i / (values.length - 1)) * w;
    const y = h - ((v - min) / range) * h;
    return `${x},${y}`;
  }).join(" ");
  return (
    <svg width={w} height={h} style={{ overflow: "visible" }}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5"
        strokeLinejoin="round" strokeLinecap="round" opacity="0.9" />
    </svg>
  );
}

// ─── Animated number ──────────────────────────────────────────────────────
function AnimNum({ value, prefix = "", suffix = "", decimals = 2, color }) {
  const [disp, setDisp] = useState(value);
  const prev = useRef(value);
  useEffect(() => {
    if (prev.current === value) return;
    prev.current = value;
    setDisp(value);
  }, [value]);
  const fmt = typeof value === "number"
    ? `${prefix}${Math.abs(disp).toFixed(decimals)}${suffix}`
    : value;
  return (
    <span style={{ color: color || "inherit", fontVariantNumeric: "tabular-nums",
      transition: "color 0.3s" }}>
      {value < 0 ? "-" : ""}{fmt}
    </span>
  );
}

// ─── Confirm close modal ─────────────────────────────────────────────────
function ConfirmModal({ position, platform, onConfirm, onCancel }) {
  const pnl = calcPnl(position);
  const meta = PLATFORM_META[platform];
  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.82)",
      display: "flex", alignItems: "center", justifyContent: "center",
      zIndex: 9999, backdropFilter: "blur(4px)"
    }}>
      <div style={{
        background: "#141820", border: `1px solid ${meta.accent}44`,
        borderRadius: 12, padding: "32px 36px", minWidth: 360,
        boxShadow: `0 0 40px ${meta.accent}22`
      }}>
        <div style={{ fontSize: 13, color: meta.accent, letterSpacing: 2,
          textTransform: "uppercase", marginBottom: 8 }}>Close Position</div>
        <div style={{ fontSize: 22, fontWeight: 700, color: "#f0f4ff", marginBottom: 4 }}>
          {position.symbol}
        </div>
        <div style={{ fontSize: 13, color: "#8899aa", marginBottom: 20 }}>
          {position.side} · Entry {position.entry} · Current {position.ltp}
        </div>
        <div style={{ display: "flex", gap: 24, marginBottom: 24 }}>
          <div>
            <div style={{ fontSize: 11, color: "#556", marginBottom: 4 }}>EST. P&L</div>
            <div style={{ fontSize: 20, fontWeight: 700,
              color: pnl >= 0 ? "#00e676" : "#ff4444" }}>
              {pnl >= 0 ? "+" : ""}${pnl.toFixed(2)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 11, color: "#556", marginBottom: 4 }}>R:R</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "#f0f4ff" }}>
              {calcRR(position)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 11, color: "#556", marginBottom: 4 }}>SIZE</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "#f0f4ff" }}>
              ${position.size}
            </div>
          </div>
        </div>
        <div style={{ fontSize: 12, color: "#ff9800", background: "#ff980011",
          border: "1px solid #ff980033", borderRadius: 6, padding: "8px 12px",
          marginBottom: 20 }}>
          ⚠ This will send a MARKET close order immediately.
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <button onClick={onCancel} style={{
            flex: 1, padding: "11px 0", borderRadius: 8,
            background: "#1e2530", border: "1px solid #334",
            color: "#8899aa", fontSize: 14, cursor: "pointer",
            fontFamily: "inherit"
          }}>Cancel</button>
          <button onClick={() => onConfirm(position)} style={{
            flex: 1, padding: "11px 0", borderRadius: 8,
            background: "#c0392b", border: "none",
            color: "#fff", fontSize: 14, fontWeight: 700,
            cursor: "pointer", fontFamily: "inherit",
            letterSpacing: 0.5
          }}>Close Position</button>
        </div>
      </div>
    </div>
  );
}

// ─── Position row ─────────────────────────────────────────────────────────
function PositionRow({ pos, platform, onClose }) {
  const pnl    = calcPnl(pos);
  const pnlPct = calcPnlPct(pos);
  const rr     = calcRR(pos);
  const meta   = PLATFORM_META[platform];
  const isWin  = pnl >= 0;
  const slPct  = Math.abs((pos.ltp - pos.sl) / pos.ltp * 100).toFixed(1);

  // SL distance bar
  const slDist = Math.abs(pos.ltp - pos.sl);
  const totalRange = Math.abs(pos.tp - pos.sl);
  const progress = totalRange > 0
    ? Math.min(1, Math.abs(pos.ltp - pos.sl) / totalRange) : 0.5;

  return (
    <tr style={{ borderBottom: "1px solid #1a2030" }}>
      {/* Symbol */}
      <td style={{ padding: "10px 12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{
            fontSize: 10, padding: "2px 6px", borderRadius: 4,
            background: pos.side === "LONG" || pos.side === "YES"
              ? "#00e67622" : "#ff444422",
            color: pos.side === "LONG" || pos.side === "YES" ? "#00e676" : "#ff6060",
            fontWeight: 700, letterSpacing: 0.5
          }}>{pos.side}</span>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: "#e8eef8" }}>
              {pos.symbol}
            </div>
            <div style={{ fontSize: 10, color: "#445566" }}>{pos.source}</div>
          </div>
        </div>
      </td>

      {/* Entry / LTP */}
      <td style={{ padding: "10px 8px" }}>
        <div style={{ fontSize: 12, color: "#7788aa" }}>{pos.entry}</div>
        <div style={{ fontSize: 13, fontWeight: 600, color: "#e8eef8" }}>
          {pos.ltp}
        </div>
      </td>

      {/* Size */}
      <td style={{ padding: "10px 8px", fontSize: 13, color: "#aabbcc",
        textAlign: "right" }}>
        ${pos.size.toLocaleString()}
      </td>

      {/* SL / TP with bar */}
      <td style={{ padding: "10px 12px", minWidth: 120 }}>
        <div style={{ display: "flex", justifyContent: "space-between",
          fontSize: 10, color: "#445566", marginBottom: 3 }}>
          <span style={{ color: "#ff5555" }}>SL {pos.sl}</span>
          <span style={{ color: "#00cc88" }}>TP {pos.tp}</span>
        </div>
        <div style={{ height: 3, background: "#1e2530", borderRadius: 2,
          position: "relative", overflow: "visible" }}>
          <div style={{
            position: "absolute", left: 0, top: 0, height: "100%",
            width: `${progress * 100}%`,
            background: `linear-gradient(90deg, #ff5555, ${meta.accent})`,
            borderRadius: 2, transition: "width 0.5s"
          }} />
          <div style={{
            position: "absolute", top: -3, width: 8, height: 8,
            background: meta.accent, borderRadius: "50%",
            left: `calc(${progress * 100}% - 4px)`,
            boxShadow: `0 0 6px ${meta.accent}`,
            transition: "left 0.5s"
          }} />
        </div>
        <div style={{ fontSize: 10, color: "#445566", marginTop: 3 }}>
          {slPct}% from SL
        </div>
      </td>

      {/* R:R */}
      <td style={{ padding: "10px 8px", fontSize: 13, fontWeight: 600,
        color: "#aabbdd", textAlign: "center" }}>
        {rr}
      </td>

      {/* P&L */}
      <td style={{ padding: "10px 8px", textAlign: "right" }}>
        <div style={{ fontSize: 14, fontWeight: 700,
          color: isWin ? "#00e676" : "#ff5555" }}>
          {isWin ? "+" : ""}${pnl.toFixed(2)}
        </div>
        <div style={{ fontSize: 10,
          color: isWin ? "#00cc6688" : "#ff444488" }}>
          {isWin ? "+" : ""}{pnlPct}%
        </div>
      </td>

      {/* Opened */}
      <td style={{ padding: "10px 8px", fontSize: 11, color: "#445566",
        textAlign: "center" }}>
        {pos.opened}
      </td>

      {/* Close button */}
      <td style={{ padding: "10px 10px", textAlign: "center" }}>
        <button
          onClick={() => onClose(pos)}
          style={{
            padding: "5px 14px", borderRadius: 6,
            background: "transparent",
            border: "1px solid #c0392b88",
            color: "#ff6060", fontSize: 11, fontWeight: 700,
            cursor: "pointer", letterSpacing: 0.5,
            transition: "all 0.2s", fontFamily: "inherit"
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = "#c0392b";
            e.currentTarget.style.color = "#fff";
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = "transparent";
            e.currentTarget.style.color = "#ff6060";
          }}
        >CLOSE</button>
      </td>
    </tr>
  );
}

// ─── Bot card (summary) ───────────────────────────────────────────────────
function BotCard({ platform, state, sparkData, onSelectBot, isActive }) {
  const meta   = PLATFORM_META[platform];
  const pnl    = state.equity - state.allocated;
  const pnlPct = (pnl / state.allocated * 100);
  const dd     = ((state.peak - state.equity) / state.peak * 100);
  const wr     = state.total_trades > 0
    ? (state.wins / state.total_trades * 100).toFixed(0) : 0;
  const openPos = state.positions.length;

  return (
    <div
      onClick={() => onSelectBot(platform)}
      style={{
        background: isActive ? `${meta.accent}0a` : "#0f1318",
        border: `1px solid ${isActive ? meta.accent + "66" : "#1e2530"}`,
        borderRadius: 12, padding: "18px 20px", cursor: "pointer",
        transition: "all 0.25s", position: "relative", overflow: "hidden",
        minWidth: 200, flex: 1
      }}
    >
      {/* Glow effect when active */}
      {isActive && (
        <div style={{
          position: "absolute", top: 0, left: 0, right: 0, height: 2,
          background: `linear-gradient(90deg, transparent, ${meta.accent}, transparent)`,
        }} />
      )}

      <div style={{ display: "flex", justifyContent: "space-between",
        alignItems: "flex-start", marginBottom: 12 }}>
        <div>
          <span style={{ fontSize: 18, marginRight: 6, color: meta.accent }}>
            {meta.icon}
          </span>
          <span style={{ fontSize: 11, color: meta.accent, fontWeight: 700,
            letterSpacing: 2, textTransform: "uppercase" }}>{meta.short}</span>
        </div>
        <div style={{
          fontSize: 10, padding: "2px 8px", borderRadius: 4,
          background: state.halted ? "#ff444422" : "#00e67622",
          color: state.halted ? "#ff5555" : "#00cc88",
          border: `1px solid ${state.halted ? "#ff444444" : "#00cc8844"}`
        }}>
          {state.halted ? "HALTED" : `${openPos} OPEN`}
        </div>
      </div>

      <div style={{ fontSize: 26, fontWeight: 800, letterSpacing: -0.5,
        color: pnl >= 0 ? "#00e676" : "#ff5555", marginBottom: 2 }}>
        {pnl >= 0 ? "+" : ""}<AnimNum value={pnl} prefix="$" decimals={2} />
      </div>
      <div style={{ fontSize: 12, color: "#445566", marginBottom: 14 }}>
        ${state.equity.toFixed(2)} equity
        &nbsp;·&nbsp;
        <span style={{ color: pnlPct >= 0 ? "#00cc88" : "#ff5555" }}>
          {pnlPct >= 0 ? "+" : ""}{pnlPct.toFixed(1)}%
        </span>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between",
        alignItems: "flex-end" }}>
        <div style={{ display: "flex", gap: 16 }}>
          <div>
            <div style={{ fontSize: 10, color: "#334455" }}>DD</div>
            <div style={{ fontSize: 12, color: dd > 10 ? "#ff9800" : "#667788" }}>
              {dd.toFixed(1)}%
            </div>
          </div>
          <div>
            <div style={{ fontSize: 10, color: "#334455" }}>WR</div>
            <div style={{ fontSize: 12, color: "#667788" }}>{wr}%</div>
          </div>
          <div>
            <div style={{ fontSize: 10, color: "#334455" }}>TRADES</div>
            <div style={{ fontSize: 12, color: "#667788" }}>{state.total_trades}</div>
          </div>
        </div>
        <Spark values={sparkData} color={meta.accent} />
      </div>
    </div>
  );
}

// ─── Trade log panel ──────────────────────────────────────────────────────
const TRADE_LOG = [
  { id: 1, platform: "hl", symbol: "BTC", side: "LONG", entry: 92100, exit: 96540, size: 1250, rr: "2.8", pnl: 603.2, status: "OPEN",   ts: "09:14" },
  { id: 2, platform: "bn", symbol: "SOL", side: "LONG", entry: 174.2, exit: 182.1, size: 950,  rr: "3.1", pnl: 430.8, status: "OPEN",   ts: "08:52" },
  { id: 3, platform: "pm", symbol: "BTC>$100k", side: "YES", entry: 0.61, exit: 0.74, size: 400, rr: "2.1", pnl: 85.2, status: "OPEN",  ts: "2d ago" },
  { id: 4, platform: "hl", symbol: "ETH", side: "SHORT", entry: 3620, exit: 3298, size: 820, rr: "2.4", pnl: 72.8, status: "CLOSED", ts: "Yesterday" },
  { id: 5, platform: "bn", symbol: "BNB", side: "LONG", entry: 612, exit: 591, size: 600, rr: "2.0", pnl: -20.5, status: "STOPPED", ts: "Yesterday" },
  { id: 6, platform: "hl", symbol: "AVAX", side: "LONG", entry: 38.4, exit: 42.1, size: 500, rr: "3.0", pnl: 48.2, status: "CLOSED", ts: "2d ago" },
];

function TradeLog() {
  const [filter, setFilter] = useState("ALL");
  const filters = ["ALL", "OPEN", "CLOSED", "STOPPED"];
  const filtered = filter === "ALL" ? TRADE_LOG
    : TRADE_LOG.filter(t => t.status === filter);

  return (
    <div style={{ background: "#0b0f14", borderRadius: 10,
      border: "1px solid #1a2030" }}>
      <div style={{ padding: "14px 16px", borderBottom: "1px solid #1a2030",
        display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: 11, color: "#667788", letterSpacing: 2,
          textTransform: "uppercase" }}>Trade Journal</span>
        <div style={{ display: "flex", gap: 4 }}>
          {filters.map(f => (
            <button key={f} onClick={() => setFilter(f)} style={{
              padding: "3px 10px", borderRadius: 4, border: "none",
              background: filter === f ? "#1e2d40" : "transparent",
              color: filter === f ? "#5599ff" : "#445566",
              fontSize: 10, cursor: "pointer", fontFamily: "inherit",
              letterSpacing: 0.5
            }}>{f}</button>
          ))}
        </div>
      </div>
      <div style={{ maxHeight: 260, overflowY: "auto" }}>
        {filtered.map(t => {
          const meta = PLATFORM_META[
            t.platform === "hl" ? "hyperliquid"
            : t.platform === "bn" ? "binance" : "polymarket"
          ];
          return (
            <div key={t.id} style={{
              padding: "10px 16px", borderBottom: "1px solid #111820",
              display: "flex", alignItems: "center", gap: 12
            }}>
              <span style={{ fontSize: 10, color: meta.accent,
                minWidth: 24 }}>{meta.icon}</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: "#ccd6e8" }}>
                  {t.symbol}
                  <span style={{ marginLeft: 6, fontSize: 10, padding: "1px 5px",
                    borderRadius: 3,
                    background: t.side === "LONG" || t.side === "YES"
                      ? "#00e67611" : "#ff444411",
                    color: t.side === "LONG" || t.side === "YES"
                      ? "#00cc88" : "#ff6060"
                  }}>{t.side}</span>
                </div>
                <div style={{ fontSize: 10, color: "#334455", marginTop: 1 }}>
                  {t.entry} → {t.exit} · R:R {t.rr} · {t.ts}
                </div>
              </div>
              <div style={{
                fontSize: 13, fontWeight: 700, textAlign: "right",
                color: t.pnl >= 0 ? "#00e676" : "#ff5555"
              }}>
                {t.pnl >= 0 ? "+" : ""}${t.pnl.toFixed(2)}
              </div>
              <div style={{
                fontSize: 9, padding: "2px 7px", borderRadius: 3,
                background: t.status === "OPEN" ? "#00e67611"
                  : t.status === "CLOSED" ? "#5599ff11" : "#ff980011",
                color: t.status === "OPEN" ? "#00cc88"
                  : t.status === "CLOSED" ? "#5599ff" : "#ff9800",
                minWidth: 50, textAlign: "center", letterSpacing: 0.5
              }}>{t.status}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Main dashboard ───────────────────────────────────────────────────────
export default function AlphaCopyDashboard() {
  const [state, setState]     = useState(MOCK_STATE);
  const [activeBot, setActiveBot] = useState("hyperliquid");
  const [closing, setClosing] = useState(null);
  const [closedIds, setClosedIds] = useState([]);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [sparkData]           = useState({
    hyperliquid: [9800, 9950, 10100, 10400, 10250, 10600, 10847],
    binance:     [10100, 10050, 9900, 9700, 9800, 9650, 9612],
    polymarket:  [10000, 10050, 10200, 10100, 10280, 10310, 10291],
  });

  // Simulate live LTP updates
  useEffect(() => {
    const iv = setInterval(() => {
      setState(prev => {
        const next = { ...prev };
        ["hyperliquid", "binance", "polymarket"].forEach(bot => {
          next[bot] = {
            ...next[bot],
            positions: next[bot].positions.map(p => ({
              ...p,
              ltp: +(p.ltp * (1 + (Math.random() - 0.5) * 0.002)).toFixed(
                p.ltp > 100 ? 2 : 4
              )
            }))
          };
        });
        return next;
      });
      setLastUpdate(new Date());
    }, 2000);
    return () => clearInterval(iv);
  }, []);

  const handleCloseRequest = useCallback((pos) => {
    setClosing(pos);
  }, []);

  const handleConfirmClose = useCallback((pos) => {
    setClosedIds(prev => [...prev, pos.id]);
    setState(prev => {
      const next = { ...prev };
      next[activeBot] = {
        ...next[activeBot],
        positions: next[activeBot].positions.filter(p => p.id !== pos.id)
      };
      return next;
    });
    setClosing(null);
    // In real app: call API to close position + send Telegram alert
    console.log(`[CLOSE ORDER] ${pos.symbol} @ market | P&L: $${calcPnl(pos).toFixed(2)}`);
  }, [activeBot]);

  const totalEquity    = Object.values(state).reduce((a, b) => a + b.equity, 0);
  const totalAllocated = Object.values(state).reduce((a, b) => a + b.allocated, 0);
  const totalPnl       = totalEquity - totalAllocated;
  const totalPnlPct    = (totalPnl / totalAllocated * 100).toFixed(2);

  const botState    = state[activeBot];
  const openPositions = botState.positions;

  const fonts = `
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=DM+Sans:wght@300;400;500;600;700&display=swap');
    * { box-sizing: border-box; margin: 0; padding: 0; }
    ::-webkit-scrollbar { width: 4px; height: 4px; }
    ::-webkit-scrollbar-track { background: #0b0f14; }
    ::-webkit-scrollbar-thumb { background: #2a3540; border-radius: 2px; }
    body { background: #080c10; }
  `;

  return (
    <div style={{
      fontFamily: "'DM Sans', sans-serif",
      background: "#080c10", color: "#c8d6e8",
      minHeight: "100vh", padding: "0"
    }}>
      <style>{fonts}</style>

      {closing && (
        <ConfirmModal
          position={closing}
          platform={activeBot}
          onConfirm={handleConfirmClose}
          onCancel={() => setClosing(null)}
        />
      )}

      {/* ── Top bar ── */}
      <div style={{
        background: "#0b0f14",
        borderBottom: "1px solid #141c26",
        padding: "0 24px",
        display: "flex", alignItems: "center",
        justifyContent: "space-between", height: 52
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{
            fontFamily: "'Space Mono', monospace",
            fontSize: 15, fontWeight: 700,
            background: "linear-gradient(90deg, #00d4ff, #9b59b6)",
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent"
          }}>AlphaCopy</span>
          <span style={{ fontSize: 10, color: "#334455",
            border: "1px solid #1a2530", padding: "2px 8px", borderRadius: 4 }}>
            v2.0
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 10, color: "#334455" }}>PORTFOLIO</div>
            <div style={{ fontSize: 16, fontWeight: 700, fontFamily: "Space Mono, monospace",
              color: totalPnl >= 0 ? "#00e676" : "#ff5555" }}>
              {totalPnl >= 0 ? "+" : ""}${totalPnl.toFixed(2)}
              <span style={{ fontSize: 11, marginLeft: 6, opacity: 0.6 }}>
                ({totalPnl >= 0 ? "+" : ""}{totalPnlPct}%)
              </span>
            </div>
          </div>
          <div style={{ width: 1, height: 28, background: "#1a2530" }} />
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 10, color: "#334455" }}>LAST UPDATE</div>
            <div style={{ fontSize: 11, color: "#445566", fontFamily: "Space Mono, monospace" }}>
              {lastUpdate.toLocaleTimeString()}
            </div>
          </div>
          <div style={{
            width: 8, height: 8, borderRadius: "50%",
            background: "#00e676",
            boxShadow: "0 0 8px #00e67699",
            animation: "pulse 2s infinite"
          }} />
        </div>
      </div>

      <div style={{ padding: "20px 24px", maxWidth: 1400, margin: "0 auto" }}>

        {/* ── Bot cards ── */}
        <div style={{ display: "flex", gap: 14, marginBottom: 20 }}>
          {Object.entries(state).map(([platform, botData]) => (
            <BotCard
              key={platform}
              platform={platform}
              state={botData}
              sparkData={sparkData[platform]}
              onSelectBot={setActiveBot}
              isActive={activeBot === platform}
            />
          ))}
        </div>

        {/* ── Active bot positions table ── */}
        <div style={{
          background: "#0b0f14", borderRadius: 10,
          border: `1px solid ${PLATFORM_META[activeBot].accent}22`,
          marginBottom: 16, overflow: "hidden"
        }}>
          {/* Table header */}
          <div style={{
            padding: "12px 16px", borderBottom: "1px solid #141c26",
            display: "flex", alignItems: "center", justifyContent: "space-between"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span style={{ color: PLATFORM_META[activeBot].accent, fontSize: 16 }}>
                {PLATFORM_META[activeBot].icon}
              </span>
              <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: 2,
                color: PLATFORM_META[activeBot].accent, textTransform: "uppercase" }}>
                {PLATFORM_META[activeBot].label} Positions
              </span>
              <span style={{ fontSize: 10, color: "#334455",
                border: "1px solid #1a2530", padding: "1px 8px", borderRadius: 4 }}>
                {openPositions.length} OPEN
              </span>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button style={{
                padding: "5px 14px", borderRadius: 6,
                background: "transparent", border: "1px solid #c0392b44",
                color: "#ff6060", fontSize: 10, cursor: "pointer",
                letterSpacing: 0.5, fontFamily: "inherit"
              }}
                onClick={() => {
                  if (openPositions.length > 0) {
                    setClosing({ ...openPositions[0], _closeAll: true });
                  }
                }}
              >CLOSE ALL</button>
            </div>
          </div>

          {openPositions.length === 0 ? (
            <div style={{ padding: "40px 20px", textAlign: "center",
              color: "#334455", fontSize: 13 }}>
              No open positions
            </div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #141c26" }}>
                    {["Symbol / Source", "Entry / LTP", "Size", "SL → TP", "R:R", "P&L", "Opened", ""].map(h => (
                      <th key={h} style={{
                        padding: "8px 12px", fontSize: 9, color: "#334455",
                        textAlign: h === "P&L" || h === "Size" ? "right"
                          : h === "R:R" || h === "Opened" ? "center" : "left",
                        letterSpacing: 1, textTransform: "uppercase",
                        fontWeight: 600, whiteSpace: "nowrap"
                      }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {openPositions.map(pos => (
                    <PositionRow
                      key={pos.id}
                      pos={pos}
                      platform={activeBot}
                      onClose={handleCloseRequest}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* ── Bottom: Trade journal + Summary stats ── */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: 16 }}>
          <TradeLog />

          {/* Portfolio summary */}
          <div style={{ background: "#0b0f14", borderRadius: 10,
            border: "1px solid #1a2030", padding: "16px" }}>
            <div style={{ fontSize: 11, color: "#445566", letterSpacing: 2,
              textTransform: "uppercase", marginBottom: 16 }}>Portfolio Summary</div>

            {Object.entries(state).map(([platform, botData]) => {
              const meta = PLATFORM_META[platform];
              const pnl  = botData.equity - botData.allocated;
              return (
                <div key={platform} style={{
                  display: "flex", justifyContent: "space-between",
                  alignItems: "center", padding: "10px 0",
                  borderBottom: "1px solid #111820"
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ color: meta.accent }}>{meta.icon}</span>
                    <span style={{ fontSize: 12, color: "#889aaa" }}>{meta.short}</span>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: 13, fontWeight: 700,
                      color: pnl >= 0 ? "#00e676" : "#ff5555" }}>
                      {pnl >= 0 ? "+" : ""}${pnl.toFixed(2)}
                    </div>
                    <div style={{ fontSize: 10, color: "#334455" }}>
                      ${botData.equity.toFixed(2)}
                    </div>
                  </div>
                </div>
              );
            })}

            <div style={{ marginTop: 14, padding: "12px",
              background: "#0f1520", borderRadius: 8,
              border: "1px solid #1a2530" }}>
              <div style={{ fontSize: 10, color: "#334455", marginBottom: 6 }}>
                TOTAL PORTFOLIO
              </div>
              <div style={{ fontSize: 22, fontWeight: 800,
                color: totalPnl >= 0 ? "#00e676" : "#ff5555",
                fontFamily: "Space Mono, monospace" }}>
                {totalPnl >= 0 ? "+" : ""}${totalPnl.toFixed(2)}
              </div>
              <div style={{ fontSize: 12, color: "#445566", marginTop: 2 }}>
                of $30,000 allocated
              </div>
              <div style={{ marginTop: 10 }}>
                <div style={{ display: "flex", justifyContent: "space-between",
                  fontSize: 10, color: "#334455", marginBottom: 4 }}>
                  <span>Return</span>
                  <span style={{ color: totalPnl >= 0 ? "#00cc88" : "#ff5555" }}>
                    {totalPnl >= 0 ? "+" : ""}{totalPnlPct}%
                  </span>
                </div>
                <div style={{ height: 3, background: "#141c26", borderRadius: 2 }}>
                  <div style={{
                    width: `${Math.min(100, Math.abs(+totalPnlPct) * 5)}%`,
                    height: "100%",
                    background: totalPnl >= 0
                      ? "linear-gradient(90deg, #00e676, #00cc88)"
                      : "linear-gradient(90deg, #ff5555, #c0392b)",
                    borderRadius: 2
                  }} />
                </div>
              </div>
            </div>

            <div style={{ marginTop: 12, fontSize: 10, color: "#334455",
              padding: "8px", background: "#0a0e12",
              borderRadius: 6, lineHeight: 1.7 }}>
              📡 Telegram alerts: <span style={{ color: "#00cc8888" }}>Active</span><br />
              🔄 Dry Run: <span style={{ color: "#ff980088" }}>ON</span><br />
              ⏱ Poll interval: <span style={{ color: "#667788" }}>5s</span>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(0.85); }
        }
      `}</style>
    </div>
  );
}
