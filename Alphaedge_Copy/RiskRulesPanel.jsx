import { useState, useEffect } from "react";

// ─── Mock risk engine state ───────────────────────────────────────────────
const INITIAL_RISK_STATE = {
  kill_switch: {
    portfolio_halted: false,
    bot_halted: { hyperliquid: false, binance: false, polymarket: false },
    consecutive_losses: { hyperliquid: 1, binance: 2, polymarket: 0 },
    daily_trade_counts: { hyperliquid: 8, binance: 5, polymarket: 3 },
    events_today: 0,
    last_event: null,
  },
  exposure: {
    total_exposure_pct: 18.4,
    by_group: { BTC_CORE: 12.5, LARGE_CAP: 3.2, PREDICTION: 2.7 },
    by_bot: { hyperliquid: 8.2, binance: 4.1, polymarket: 6.1 },
    open_count: 5,
  },
  rules: {
    one_pct_rule:    { name: "1% Risk Rule",          status: "OK",  detail: "Current risk: 0.82%/trade avg" },
    stop_loss:       { name: "Mandatory Stop-Loss",   status: "OK",  detail: "All 5 positions have SL set" },
    rr_ratio:        { name: "Min R:R ≥ 1:2",         status: "OK",  detail: "Avg R:R: 2.7 across open trades" },
    diversification: { name: "Diversification",       status: "WARN",detail: "BTC_CORE at 12.5% (max 25%)" },
    kill_switch:     { name: "Kill Switches",         status: "OK",  detail: "No triggers active" },
    algo_validation: { name: "Algo Validated",        status: "WARN",detail: "14-day paper trade window: Day 9/14" },
  },
  portfolio: {
    total_equity: 30751.05,
    allocated: 30000,
    peak: 31200,
    daily_pnl: 412.30,
    weekly_pnl: 1180.50,
    drawdown_pct: 1.44,
    daily_loss_limit_pct: 5.0,
    weekly_loss_limit_pct: 10.0,
    daily_used_pct: 0,
    weekly_used_pct: 0,
  },
  bots: {
    hyperliquid: { equity: 10847, allocated: 10000, drawdown: 3.2, consec_loss: 1, daily_trades: 8, max_daily_trades: 50, halted: false },
    binance:     { equity: 9612,  allocated: 10000, drawdown: 4.1, consec_loss: 2, daily_trades: 5, max_daily_trades: 50, halted: false },
    polymarket:  { equity: 10291, allocated: 10000, drawdown: 0.8, consec_loss: 0, daily_trades: 3, max_daily_trades: 50, halted: false },
  }
};

const PLATFORM_META = {
  hyperliquid: { label: "Hyperliquid", short: "HL", accent: "#00d4ff" },
  binance:     { label: "Binance",     short: "BN", accent: "#f0b90b" },
  polymarket:  { label: "Polymarket",  short: "PM", accent: "#9b59b6" },
};

const RULE_ICONS = {
  one_pct_rule:    "①",
  stop_loss:       "🛑",
  rr_ratio:        "⚖️",
  diversification: "🔀",
  kill_switch:     "⚡",
  algo_validation: "🧪",
};

const STATUS_STYLE = {
  OK:   { bg: "#00e67611", border: "#00e67644", text: "#00cc88", dot: "#00e676" },
  WARN: { bg: "#ff980011", border: "#ff980044", text: "#ff9800", dot: "#ff9800" },
  FAIL: { bg: "#ff444411", border: "#ff444444", text: "#ff5555", dot: "#ff4444" },
  HALT: { bg: "#ff000022", border: "#ff000066", text: "#ff2222", dot: "#ff0000" },
};

function StatusDot({ status, pulse = false }) {
  const s = STATUS_STYLE[status] || STATUS_STYLE.OK;
  return (
    <span style={{
      display: "inline-block", width: 8, height: 8,
      borderRadius: "50%", background: s.dot,
      boxShadow: `0 0 6px ${s.dot}`,
      ...(pulse ? { animation: "pulse 1.5s infinite" } : {})
    }} />
  );
}

function RuleCard({ ruleKey, rule }) {
  const s = STATUS_STYLE[rule.status] || STATUS_STYLE.OK;
  return (
    <div style={{
      background: s.bg, border: `1px solid ${s.border}`,
      borderRadius: 8, padding: "12px 14px",
      display: "flex", gap: 12, alignItems: "flex-start"
    }}>
      <div style={{ fontSize: 18, lineHeight: 1 }}>{RULE_ICONS[ruleKey]}</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", justifyContent: "space-between",
          alignItems: "center", marginBottom: 4 }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: "#ccd6e8" }}>
            {rule.name}
          </span>
          <span style={{
            fontSize: 9, padding: "2px 8px", borderRadius: 3,
            background: s.bg, border: `1px solid ${s.border}`,
            color: s.text, fontWeight: 700, letterSpacing: 1
          }}>{rule.status}</span>
        </div>
        <div style={{ fontSize: 11, color: "#556677", lineHeight: 1.4 }}>
          {rule.detail}
        </div>
      </div>
    </div>
  );
}

function KillSwitchPanel({ state, onManualKill, onReset }) {
  const s = state.kill_switch;
  const isAnyHalted = s.portfolio_halted || Object.values(s.bot_halted).some(Boolean);

  return (
    <div style={{
      background: isAnyHalted ? "#200008" : "#0b0f14",
      border: `1px solid ${isAnyHalted ? "#ff003366" : "#1e2530"}`,
      borderRadius: 10, overflow: "hidden"
    }}>
      <div style={{
        padding: "12px 16px",
        borderBottom: `1px solid ${isAnyHalted ? "#ff003333" : "#141c26"}`,
        display: "flex", justifyContent: "space-between", alignItems: "center",
        background: isAnyHalted ? "#ff00001a" : "transparent"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <StatusDot status={isAnyHalted ? "HALT" : "OK"} pulse={isAnyHalted} />
          <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: 2,
            color: isAnyHalted ? "#ff4444" : "#667788",
            textTransform: "uppercase" }}>
            Kill Switch Control
          </span>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            onClick={() => onManualKill("ALL")}
            style={{
              padding: "5px 14px", borderRadius: 6,
              background: "#c0392b22", border: "1px solid #c0392b88",
              color: "#ff6060", fontSize: 10, fontWeight: 700,
              cursor: "pointer", fontFamily: "inherit", letterSpacing: 1
            }}>
            ⚡ KILL ALL
          </button>
          {isAnyHalted && (
            <button onClick={onReset} style={{
              padding: "5px 14px", borderRadius: 6,
              background: "#00e67622", border: "1px solid #00e67644",
              color: "#00cc88", fontSize: 10, fontWeight: 700,
              cursor: "pointer", fontFamily: "inherit", letterSpacing: 1
            }}>
              ↺ RESET
            </button>
          )}
        </div>
      </div>

      <div style={{ padding: "14px 16px" }}>
        {/* Per-bot kill switch status */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr",
          gap: 10, marginBottom: 14 }}>
          {Object.entries(PLATFORM_META).map(([bot, meta]) => {
            const botData   = state.bots[bot];
            const halted    = s.bot_halted[bot];
            const consec    = s.consecutive_losses[bot] || 0;
            const consecLim = 5;
            const ddPct     = botData.drawdown;
            const ddLim     = 20;
            const tradePct  = (botData.daily_trades / botData.max_daily_trades) * 100;
            return (
              <div key={bot} style={{
                background: halted ? "#ff000022" : "#0f1520",
                border: `1px solid ${halted ? "#ff004466" : meta.accent + "33"}`,
                borderRadius: 8, padding: "10px 12px"
              }}>
                <div style={{ display: "flex", justifyContent: "space-between",
                  alignItems: "center", marginBottom: 8 }}>
                  <span style={{ fontSize: 10, fontWeight: 700,
                    color: meta.accent, letterSpacing: 1 }}>{meta.short}</span>
                  <span style={{
                    fontSize: 9, padding: "1px 6px", borderRadius: 3,
                    background: halted ? "#ff000033" : "#00e67611",
                    color: halted ? "#ff4444" : "#00cc88",
                    fontWeight: 700
                  }}>{halted ? "HALTED" : "ACTIVE"}</span>
                </div>

                {/* Drawdown bar */}
                <div style={{ marginBottom: 6 }}>
                  <div style={{ display: "flex", justifyContent: "space-between",
                    fontSize: 9, color: "#445566", marginBottom: 2 }}>
                    <span>DD</span>
                    <span style={{
                      color: ddPct > ddLim * 0.7 ? "#ff9800" : "#556677"
                    }}>{ddPct.toFixed(1)}% / {ddLim}%</span>
                  </div>
                  <div style={{ height: 3, background: "#1a2030", borderRadius: 2 }}>
                    <div style={{
                      width: `${Math.min(100, ddPct / ddLim * 100)}%`,
                      height: "100%", borderRadius: 2,
                      background: ddPct > ddLim * 0.7 ? "#ff9800" : meta.accent
                    }} />
                  </div>
                </div>

                {/* Trade velocity bar */}
                <div style={{ marginBottom: 6 }}>
                  <div style={{ display: "flex", justifyContent: "space-between",
                    fontSize: 9, color: "#445566", marginBottom: 2 }}>
                    <span>Trades/day</span>
                    <span>{botData.daily_trades}/{botData.max_daily_trades}</span>
                  </div>
                  <div style={{ height: 3, background: "#1a2030", borderRadius: 2 }}>
                    <div style={{
                      width: `${tradePct}%`, height: "100%", borderRadius: 2,
                      background: tradePct > 70 ? "#ff9800" : "#334455"
                    }} />
                  </div>
                </div>

                <div style={{ fontSize: 9, color: "#445566" }}>
                  Consec. losses: {" "}
                  <span style={{ color: consec >= 3 ? "#ff9800" : "#556677" }}>
                    {consec}/{consecLim}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Portfolio thresholds */}
        <div style={{ background: "#080c10", borderRadius: 8,
          padding: "12px 14px", border: "1px solid #141c26" }}>
          <div style={{ fontSize: 10, color: "#445566", letterSpacing: 1,
            textTransform: "uppercase", marginBottom: 10 }}>
            Portfolio Threshold Monitors
          </div>
          {[
            { label: "Daily Loss", used: state.portfolio.daily_used_pct,
              limit: state.portfolio.daily_loss_limit_pct, color: "#ff5555" },
            { label: "Weekly Loss", used: state.portfolio.weekly_used_pct,
              limit: state.portfolio.weekly_loss_limit_pct, color: "#ff9800" },
            { label: "Portfolio DD", used: state.portfolio.drawdown_pct,
              limit: 15, color: "#9b59b6" },
          ].map(t => (
            <div key={t.label} style={{ marginBottom: 10 }}>
              <div style={{ display: "flex", justifyContent: "space-between",
                fontSize: 10, color: "#556677", marginBottom: 4 }}>
                <span>{t.label}</span>
                <span style={{
                  color: t.used / t.limit > 0.7 ? t.color : "#445566"
                }}>
                  {t.used.toFixed(1)}% / {t.limit.toFixed(0)}%
                  {t.used / t.limit > 0.7 && " ⚠"}
                </span>
              </div>
              <div style={{ height: 4, background: "#141c26", borderRadius: 2 }}>
                <div style={{
                  width: `${Math.min(100, t.used / t.limit * 100)}%`,
                  height: "100%", borderRadius: 2,
                  background: t.used / t.limit > 0.7 ? t.color : "#2a3a4a",
                  transition: "width 0.5s"
                }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ExposureMap({ exposure }) {
  const MAX_PCT = 25;
  const entries = Object.entries(exposure.by_group);
  return (
    <div style={{
      background: "#0b0f14", borderRadius: 10,
      border: "1px solid #1e2530", padding: "14px 16px"
    }}>
      <div style={{ fontSize: 11, color: "#556677", letterSpacing: 2,
        textTransform: "uppercase", marginBottom: 12 }}>
        Correlation Group Exposure
      </div>
      {entries.length === 0 ? (
        <div style={{ fontSize: 12, color: "#334455", textAlign: "center",
          padding: "20px 0" }}>No open positions</div>
      ) : (
        entries.map(([group, pct]) => {
          const danger = pct > MAX_PCT * 0.8;
          const fill   = pct > MAX_PCT ? "#ff5555" : danger ? "#ff9800" : "#00cc88";
          return (
            <div key={group} style={{ marginBottom: 10 }}>
              <div style={{ display: "flex", justifyContent: "space-between",
                fontSize: 11, marginBottom: 4 }}>
                <span style={{ color: "#8899aa" }}>{group}</span>
                <span style={{ color: fill, fontWeight: 600 }}>
                  {pct}%
                  {danger && <span style={{ marginLeft: 6, fontSize: 9,
                    color: "#ff9800" }}>⚠ near limit</span>}
                </span>
              </div>
              <div style={{ height: 6, background: "#141c26",
                borderRadius: 3, overflow: "hidden" }}>
                <div style={{
                  width: `${Math.min(100, pct / MAX_PCT * 100)}%`,
                  height: "100%", background: fill,
                  borderRadius: 3, transition: "width 0.5s",
                  opacity: 0.85
                }} />
              </div>
            </div>
          );
        })
      )}
      <div style={{ marginTop: 12, fontSize: 10, color: "#334455",
        borderTop: "1px solid #141c26", paddingTop: 10,
        display: "flex", justifyContent: "space-between" }}>
        <span>Total exposure</span>
        <span style={{ color: "#8899aa" }}>{exposure.total_exposure_pct}% of portfolio</span>
      </div>
    </div>
  );
}

export default function RiskRulesPanel() {
  const [riskState, setRiskState] = useState(INITIAL_RISK_STATE);
  const [killConfirm, setKillConfirm] = useState(null);

  // Simulate live risk updates
  useEffect(() => {
    const iv = setInterval(() => {
      setRiskState(prev => ({
        ...prev,
        portfolio: {
          ...prev.portfolio,
          daily_pnl: prev.portfolio.daily_pnl + (Math.random() - 0.45) * 20
        }
      }));
    }, 3000);
    return () => clearInterval(iv);
  }, []);

  const handleManualKill = (target) => setKillConfirm(target);

  const handleConfirmKill = () => {
    if (killConfirm === "ALL") {
      setRiskState(prev => ({
        ...prev,
        kill_switch: {
          ...prev.kill_switch,
          portfolio_halted: true,
          bot_halted: { hyperliquid: true, binance: true, polymarket: true }
        },
        rules: {
          ...prev.rules,
          kill_switch: { name: "Kill Switches", status: "HALT",
            detail: "MANUAL KILL — All bots halted" }
        }
      }));
    }
    setKillConfirm(null);
  };

  const handleReset = () => {
    setRiskState(prev => ({
      ...prev,
      kill_switch: {
        ...prev.kill_switch,
        portfolio_halted: false,
        bot_halted: { hyperliquid: false, binance: false, polymarket: false }
      },
      rules: {
        ...prev.rules,
        kill_switch: { name: "Kill Switches", status: "OK", detail: "No triggers active" }
      }
    }));
  };

  const fonts = `
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600;700&display=swap');
    * { box-sizing: border-box; margin: 0; padding: 0; }
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: #0b0f14; }
    ::-webkit-scrollbar-thumb { background: #2a3540; border-radius: 2px; }
    @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.3; } }
  `;

  return (
    <div style={{
      fontFamily: "'DM Sans', sans-serif",
      background: "#080c10", color: "#c8d6e8",
      minHeight: "100vh", padding: "0"
    }}>
      <style>{fonts}</style>

      {/* Kill confirm modal */}
      {killConfirm && (
        <div style={{
          position: "fixed", inset: 0, background: "rgba(0,0,0,0.9)",
          display: "flex", alignItems: "center", justifyContent: "center",
          zIndex: 9999, backdropFilter: "blur(4px)"
        }}>
          <div style={{
            background: "#120008", border: "1px solid #ff000066",
            borderRadius: 12, padding: "28px 32px", maxWidth: 380,
            boxShadow: "0 0 60px #ff000033"
          }}>
            <div style={{ fontSize: 24, marginBottom: 8 }}>🚨</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: "#ff4444",
              marginBottom: 8 }}>Emergency Kill Switch</div>
            <div style={{ fontSize: 13, color: "#889aaa", marginBottom: 20,
              lineHeight: 1.6 }}>
              This will immediately halt <b style={{color:"#ff8888"}}>ALL THREE BOTS</b> and
              prevent any new trades. Existing positions will remain open until manually closed.
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <button onClick={() => setKillConfirm(null)} style={{
                flex: 1, padding: "10px 0", borderRadius: 8,
                background: "#1a2030", border: "1px solid #334",
                color: "#8899aa", fontSize: 13, cursor: "pointer",
                fontFamily: "inherit"
              }}>Cancel</button>
              <button onClick={handleConfirmKill} style={{
                flex: 1, padding: "10px 0", borderRadius: 8,
                background: "#c0392b", border: "none",
                color: "#fff", fontSize: 13, fontWeight: 700,
                cursor: "pointer", fontFamily: "inherit",
                letterSpacing: 0.5
              }}>⚡ KILL ALL BOTS</button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div style={{
        background: "#0b0f14", borderBottom: "1px solid #141c26",
        padding: "0 24px", height: 52,
        display: "flex", alignItems: "center", justifyContent: "space-between"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{
            fontFamily: "'Space Mono', monospace", fontSize: 15, fontWeight: 700,
            background: "linear-gradient(90deg, #00d4ff, #9b59b6)",
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent"
          }}>AlphaCopy</span>
          <span style={{ fontSize: 11, color: "#445566",
            border: "1px solid #1a2530", padding: "2px 10px", borderRadius: 4 }}>
            Risk Rules Dashboard
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 10, color: "#334455" }}>Portfolio Equity</span>
          <span style={{
            fontFamily: "Space Mono, monospace", fontSize: 15, fontWeight: 700,
            color: riskState.portfolio.total_equity > riskState.portfolio.allocated
              ? "#00e676" : "#ff5555"
          }}>
            ${riskState.portfolio.total_equity.toFixed(2)}
          </span>
        </div>
      </div>

      <div style={{ padding: "20px 24px", maxWidth: 1400, margin: "0 auto" }}>

        {/* ── Row 1: 6 Rule Cards ─────────────────────────────────────── */}
        <div style={{ marginBottom: 6 }}>
          <div style={{ fontSize: 11, color: "#445566", letterSpacing: 2,
            textTransform: "uppercase", marginBottom: 12 }}>
            Industry Risk Rules — System-Wide Enforcement
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)",
            gap: 10, marginBottom: 20 }}>
            {Object.entries(riskState.rules).map(([key, rule]) => (
              <RuleCard key={key} ruleKey={key} rule={rule} />
            ))}
          </div>
        </div>

        {/* ── Row 2: Kill Switch + Exposure ──────────────────────────── */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 340px",
          gap: 16, marginBottom: 16 }}>
          <KillSwitchPanel
            state={riskState}
            onManualKill={handleManualKill}
            onReset={handleReset}
          />
          <ExposureMap exposure={riskState.exposure} />
        </div>

        {/* ── Row 3: Position Sizing Reference ──────────────────────── */}
        <div style={{
          background: "#0b0f14", borderRadius: 10,
          border: "1px solid #1e2530", padding: "16px 20px"
        }}>
          <div style={{ fontSize: 11, color: "#445566", letterSpacing: 2,
            textTransform: "uppercase", marginBottom: 14 }}>
            1% Rule — Position Sizing Calculator (Live Reference)
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)",
            gap: 14 }}>
            {[
              { label: "Portfolio Equity",   value: `$${riskState.portfolio.total_equity.toFixed(0)}`,       color: "#8899cc" },
              { label: "Max Risk / Trade (1%)", value: `$${(riskState.portfolio.total_equity * 0.01).toFixed(0)}`, color: "#00cc88" },
              { label: "Hard Cap / Trade (2%)", value: `$${(riskState.portfolio.total_equity * 0.02).toFixed(0)}`, color: "#ff9800" },
              { label: "Max Single Position", value: `$${Math.min(riskState.portfolio.total_equity * 0.15, 5000).toFixed(0)}`, color: "#9b59b6" },
            ].map(item => (
              <div key={item.label} style={{
                background: "#0f1520", borderRadius: 8,
                padding: "12px 14px", border: "1px solid #1a2530"
              }}>
                <div style={{ fontSize: 10, color: "#445566", marginBottom: 6 }}>
                  {item.label}
                </div>
                <div style={{ fontSize: 22, fontWeight: 800,
                  fontFamily: "Space Mono, monospace", color: item.color }}>
                  {item.value}
                </div>
              </div>
            ))}
          </div>

          {/* Trade example */}
          <div style={{
            marginTop: 14, padding: "12px 14px",
            background: "#080c10", borderRadius: 8,
            border: "1px solid #141c26", fontSize: 11,
            color: "#556677", lineHeight: 2
          }}>
            <span style={{ color: "#8899aa", fontWeight: 600 }}>
              Example sizing:
            </span>{" "}
            BTC @ $95,000 · SL at $90,250 (−5%) →
            Risk distance = 5% →
            Position = $
            {((riskState.portfolio.total_equity * 0.01) / 0.05).toFixed(0)}{" "}
            (1% ÷ 5% SL) ·{" "}
            <span style={{ color: "#00cc88" }}>
              Risk: ${(riskState.portfolio.total_equity * 0.01).toFixed(0)} ✓
            </span>
            {" · R:R 2:1 → TP at $104,500"}
          </div>
        </div>
      </div>
    </div>
  );
}
