/**
 * DVR Portfolio Dashboard — app.js
 * Fetches from FastAPI on localhost:8765
 * Renders 7-broker portfolio with interactive deepdive modals
 */

const API_BASE   = "http://localhost:8765";
const REFRESH_MS = 30_000;

// Broker metadata: display name, logo letter, category label, accent color
const BROKER_META = {
  upstox:      { name: "Upstox",      letter: "U", category: "Indian Equities & F&O",       accent: "#c084fc" },
  dhan:        { name: "Dhan",        letter: "D", category: "Indian Equities & Futures",    accent: "#34d399" },
  tradesmart:  { name: "TradeSmart",  letter: "T", category: "Indian Equities & Commodities",accent: "#60a5fa" },
  fyers:       { name: "Fyers",       letter: "F", category: "Indian Equities & Options",    accent: "#06b6d4" },
  hyperliquid: { name: "Hyperliquid", letter: "H", category: "DeFi Perps & Spot Crypto",    accent: "#84cc16" },
  exness:      { name: "Exness",      letter: "E", category: "FX & CFD",                     accent: "#fbbf24" },
  binance:     { name: "Binance",     letter: "B", category: "Spot & Futures Crypto",        accent: "#f59e0b" },
};

// Chart color palette (per-scrip allocation inside deepdive)
const SCRIP_COLORS = [
  "#10B981","#3B82F6","#F59E0B","#EF4444","#8B5CF6",
  "#06B6D4","#84CC16","#F97316","#EC4899","#14B8A6",
];

let latestPortfolioData = null;
let latestMacroData     = null;
let deepdiveChartInst   = null;
let allocChartInstance  = null;

// ── Bootstrap ────────────────────────────────────────────────────────────────

function getPage() {
  const p = window.location.pathname;
  if (p === "/portfolio") return "portfolio";
  if (p === "/holdings")  return "holdings";
  if (p === "/positions") return "positions";
  return "dashboard";
}

document.addEventListener("DOMContentLoaded", () => {
  refreshAll();
  setInterval(refreshAll, REFRESH_MS);
});

async function refreshAll() {
  const page = getPage();
  const jobs = [loadLatest()];
  if (page === "dashboard") {
    jobs.push(loadGainersLosers(), loadStrategyNifty200());
  } else {
    jobs.push(loadPortfolio());
  }
  await Promise.allSettled(jobs);
}

// ── Data Fetch ───────────────────────────────────────────────────────────────

async function loadLatest() {
  try {
    const res    = await fetch(`${API_BASE}/api/latest`);
    if (!res.ok) throw new Error(`/api/latest → ${res.status}`);
    const latest = await res.json();
    renderTimestamp(latest.recorded_at);
    latestMacroData = latest.macro;
    latestMacroData._stale = latest.stale;
    updateTicker();
    renderMacro(latest.macro);
    const el = document.getElementById("error-banner");
    if (el) el.style.display = "none";
  } catch (err) {
    showError("Macro data update failed: " + err.message);
  }
}

async function loadPortfolio() {
  try {
    const res  = await fetch(`${API_BASE}/api/portfolio/pnl`);
    if (!res.ok) throw new Error(`/api/portfolio/pnl → ${res.status}`);
    const data = await res.json();
    latestPortfolioData = data;
    updateTicker();
    const page = getPage();
    if (page === "portfolio") {
      renderSummaryCards(data);
      renderBrokerCards(data);
      renderPortfolioTables(data, "both");
    } else if (page === "holdings") {
      renderPortfolioTables(data, "holdings");
    } else {
      renderPortfolioTables(data, "positions");
    }
  } catch (err) {
    console.error("Failed to load portfolio:", err);
    showError("Portfolio P&L update failed: " + err.message);
  }
}

// ── Ticker ───────────────────────────────────────────────────────────────────

function updateTicker() {
  const items = [];

  if (latestPortfolioData?.summary) {
    const s = latestPortfolioData.summary;
    items.push({ name: "PORTFOLIO VALUE", val: `₹${fmtIN(s.current_value)}`,
                 chg: s.total_pnl_pct, isPortfolio: true });
    items.push({ name: "TODAY'S P&L",
                 val: `${s.today_pnl >= 0 ? "+" : "-"}₹${fmtIN(Math.abs(s.today_pnl))}`,
                 chg: s.today_pnl_pct, isPortfolio: true });
  } else {
    items.push({ name: "PORTFOLIO", val: "Loading...", chg: 0, isPortfolio: true });
  }

  if (latestMacroData) {
    const m = latestMacroData;
    items.push(
      { name: "VIX",    val: fmt(m.vix?.ltp, 2),        chg: m.vix?.chg },
      { name: "DXY",    val: fmt(m.dxy?.ltp, 3),        chg: m.dxy?.chg },
      { name: "CRUDE",  val: "$" + fmt(m.crude?.ltp, 2), chg: m.crude?.chg },
      { name: "US30",   val: fmt(m.us30?.ltp, 0),       chg: m.us30?.chg },
      { name: "GOLD",   val: "$" + fmt(m.gold?.ltp, 1), chg: m.gold?.chg },
      { name: "SILVER", val: "$" + fmt(m.silver?.ltp, 2), chg: m.silver?.chg },
    );
  }

  const el = document.getElementById("ticker");
  if (!el) return;
  el.innerHTML = [...items, ...items].map(({ name, val, chg, isPortfolio }) => {
    const cv  = parseFloat(chg) || 0;
    const cls = cv > 0 ? "up" : cv < 0 ? "dn" : "flat";
    const arr = cv >= 0 ? "▲" : "▼";
    return `<div class="ticker-item ${isPortfolio ? "portfolio-ticker-highlight" : ""}">
      <span class="ticker-name">${name}</span>
      <span class="ticker-val">${val ?? "—"}</span>
      <span class="ticker-chg ${cls}">${arr} ${Math.abs(cv).toFixed(2)}%</span>
    </div>`;
  }).join("");
}

// ── Macro Row ────────────────────────────────────────────────────────────────

function renderMacro(macro) {
  const items = [
    { name: "India VIX", key: "vix",   pre: "" },
    { name: "DXY",       key: "dxy",   pre: "" },
    { name: "Crude Oil", key: "crude", pre: "$" },
    { name: "US30",      key: "us30",  pre: "" },
    { name: "Gold",      key: "gold",  pre: "$" },
    { name: "Silver",    key: "silver",pre: "$" },
  ];
  const container = document.getElementById("macro-row");
  if (!container) return;
  container.innerHTML = items.map(({ name, key, pre }) => {
    const d   = macro[key] || {};
    const chg = d.chg ?? 0;
    const cls = chg > 0 ? "up" : chg < 0 ? "dn" : "flat";
    const arr = chg >= 0 ? "▲" : "▼";
    return `<div class="macro-cell">
      <div class="macro-name">${name}</div>
      <div class="macro-val">${pre}${d.ltp != null ? fmtIN(d.ltp, key === "dxy" ? 3 : 2) : "—"}</div>
      <div class="macro-chg ${cls}">${arr} ${Math.abs(chg).toFixed(2)}%</div>
    </div>`;
  }).join("");
}

// ── Gainers / Losers ───────────────────────────────────────────────────────────

async function loadGainersLosers() {
  try {
    const res = await fetch(`${API_BASE}/api/gainers-losers`);
    if (!res.ok) throw new Error(`/api/gainers-losers → ${res.status}`);
    const data = await res.json();
    renderGainersLosers(data);
  } catch (err) {
    console.error("Gainers/Losers fetch failed:", err);
  }
}

function renderGainersLosers(data) {
  const gList = document.getElementById("gainers-list");
  const lList = document.getElementById("losers-list");
  if (!gList || !lList) return;

  gList.innerHTML = data.gainers.map(s => glItem(s, true)).join("");
  lList.innerHTML = data.losers.map(s => glItem(s, false)).join("");

  const gCount = document.getElementById("gainers-count");
  const lCount = document.getElementById("losers-count");
  if (gCount) gCount.textContent = data.gainers.length;
  if (lCount) lCount.textContent = data.losers.length;
}

function glItem(s, isGainer) {
  const cls = isGainer ? "up" : "dn";
  const arrow = isGainer ? "▲" : "▼";
  return `<div class="gl-item">
    <div class="gl-sym">${s.symbol}</div>
    <div class="gl-ltp">${fmtIN(s.ltp)}</div>
    <div class="gl-chg ${cls}">${arrow} ${Math.abs(s.change_pct).toFixed(2)}%</div>
  </div>`;
}

// ── Strategy: Nifty 200 Momentum Scanner ────────────────────────────────────

async function loadStrategyNifty200() {
  try {
    const res = await fetch(`${API_BASE}/api/strategies/nifty200-momentum`);
    if (!res.ok) throw new Error(`/api/strategies/nifty200-momentum → ${res.status}`);
    const data = await res.json();
    renderStrategyNifty200(data);
  } catch (err) {
    console.error("Strategy fetch failed:", err);
    const el = document.getElementById("strat-row");
    if (el && !el.querySelector(".strat-card")) {
      el.innerHTML = `<div class="card strat-card" style="grid-column:1/-1;padding:16px;text-align:center;color:var(--muted)">
        ⚠ Strategy report not yet available. Run scanner first.</div>`;
    }
  }
}

function renderStrategyNifty200(data) {
  const container = document.getElementById("strat-row");
  if (!container) return;

  const dt = data.updated_at ? new Date(data.updated_at).toLocaleString("en-IN", { hour12: false }) : "—";

  const sections = [
    { title: "Bullish (52wH)", key: "bullish", cls: "bullish", empty: "No stocks qualify", cols: ["Sym", "LTP", "52wH%", "RSI", "Strk"] },
    { title: "Bearish (52wL)", key: "bearish", cls: "bearish", empty: "No stocks qualify", cols: ["Sym", "LTP", "52wL%", "RSI", "Strk"] },
    { title: "Streak (3+d)", key: "streak", cls: "streak", empty: "No streaks", cols: ["Sym", "LTP", "52wH%", "RSI", "Days"] },
  ];

  container.innerHTML = sections.map(s => {
    const items = data[s.key] || [];
    const color = s.cls === "bullish" ? "var(--green)" : s.cls === "bearish" ? "var(--red)" : "var(--yellow)";
    return `<div class="card strat-card">
      <div class="strat-header" style="border-bottom-color:${color}">${s.title}
        <span class="strat-count" style="background:${color}">${items.length}</span>
      </div>
      <div class="strat-updated">${dt}</div>
      <div class="strat-list">
        <div class="strat-item strat-hdr">${s.cols.map(c => `<div class="strat-val mono">${c}</div>`).join("")}</div>
        ${items.length ? items.slice(0, 8).map(r => {
          const pctKey = s.key === "bullish" ? "pct_from_52wh" : s.key === "bearish" ? "pct_from_52wl" : "pct_from_52wh";
          const pctVal = r[pctKey];
          const pctCls = s.key === "bullish" ? (pctVal >= -1 ? "up" : "flat") : s.key === "bearish" ? (pctVal <= 1 ? "dn" : "flat") : "flat";
          const dayStr = s.key === "streak" ? `${r.consecutive_high_days}d` : r.consecutive_high_days ? `${r.consecutive_high_days}d` : "—";
          return `<div class="strat-item">
            <div class="strat-sym">${r.symbol}</div>
            <div class="strat-val mono">${fmtIN(r.ltp)}</div>
            <div class="strat-val ${pctCls} mono">${pctVal >= 0 ? "+" : ""}${pctVal.toFixed(1)}%</div>
            <div class="strat-val mono">${r.rsi_14.toFixed(1)}</div>
            <div class="strat-val mono">${dayStr}</div>
          </div>`;
        }).join("") : `<div class="strat-empty">${s.empty}</div>`}
      </div>
    </div>`;
  }).join("");
}

// ── Timestamp ────────────────────────────────────────────────────────────────

function renderTimestamp(ts) {
  if (document.getElementById("pixi-status")) return;
  const el = document.getElementById("last-updated");
  if (!el || !ts) return;
  const d = new Date(ts + "Z");
  el.innerHTML = `<span class="live-dot"></span>Updated: ${d.toLocaleTimeString("en-IN", { hour12: false })} UTC`;
}

// ── Portfolio Render ─────────────────────────────────────────────────────────

function renderSummaryCards(data) {
  const container = document.getElementById("portfolio-summary-container");
  if (!container) return;
  const s         = data.summary;
  const brokers   = data.brokers;
  const brokerKeys = Object.keys(brokers);
  const totalPnlCls = s.total_pnl > 0 ? "up" : s.total_pnl < 0 ? "dn" : "flat";
  const todayPnlCls = s.today_pnl > 0 ? "up" : s.today_pnl < 0 ? "dn" : "flat";
  const totalArr    = s.total_pnl >= 0 ? "▲" : "▼";
  const todayArr    = s.today_pnl >= 0 ? "▲" : "▼";
  container.innerHTML = `
    <div class="portfolio-summary-grid">
      <div class="port-card glass">
        <div class="port-card-label">Net Portfolio Value</div>
        <div class="port-card-val primary-glow">₹${fmtIN(s.current_value)}</div>
        <div class="port-card-sub ${totalPnlCls}">${totalArr} ₹${fmtIN(Math.abs(s.total_pnl))} (${s.total_pnl_pct.toFixed(2)}%)</div>
      </div>
      <div class="port-card glass">
        <div class="port-card-label">Invested Capital</div>
        <div class="port-card-val">₹${fmtIN(s.total_invested)}</div>
        <div class="port-card-sub text-muted">Across ${brokerKeys.length} platforms</div>
      </div>
      <div class="port-card glass">
        <div class="port-card-label">Total Returns</div>
        <div class="port-card-val ${totalPnlCls}">${totalArr} ₹${fmtIN(Math.abs(s.total_pnl))}</div>
        <div class="port-card-sub ${totalPnlCls}">${s.total_pnl_pct.toFixed(2)}% Cumulative</div>
      </div>
      <div class="port-card glass">
        <div class="port-card-label">Today's Returns</div>
        <div class="port-card-val ${todayPnlCls}">${todayArr} ₹${fmtIN(Math.abs(s.today_pnl))}</div>
        <div class="port-card-sub ${todayPnlCls}">${s.today_pnl_pct.toFixed(2)}% Daily</div>
      </div>
    </div>`;
}

function renderBrokerCards(data) {
  const container = document.getElementById("portfolio-broker-container");
  if (!container) return;
  const brokers   = data.brokers;
  const brokerKeys = Object.keys(brokers);
  container.innerHTML = `
    <div class="portfolio-mid-grid">
      <div class="broker-cards-wrap">
        <h3 class="section-title">Broker &amp; Exchange Accounts <span style="font-size:0.65rem;font-family:var(--mono);color:var(--muted);font-weight:400;margin-left:8px;">Click any tile to deepdive</span></h3>
        <div class="broker-cards-list">
          ${brokerKeys.map(name => {
            const b    = brokers[name];
            const meta = BROKER_META[name] || { name: name, letter: name[0].toUpperCase(), category: "Platform", accent: "#94a3b8" };
            const pnlCls = b.total_pnl > 0 ? "up" : b.total_pnl < 0 ? "dn" : "flat";
            return `
              <div class="broker-card glass" onclick="openBrokerDeepdive('${name}')" title="Click for ${meta.name} deepdive">
                <div class="broker-card-header">
                  <div class="broker-logo-wrap">
                    <span class="broker-logo logo-${name}">${meta.letter}</span>
                    <div>
                      <div class="broker-name">${meta.name}</div>
                      <span class="broker-badge ${b.is_mock ? "badge-mock" : "badge-live"}">${b.is_mock ? "Mocked" : "Live"}</span>
                    </div>
                  </div>
                  <div class="broker-pnl ${pnlCls}">${b.total_pnl >= 0 ? "+" : ""}${fmtIN(b.total_pnl)}</div>
                </div>
                <div class="broker-details">
                  <div class="broker-detail-row">
                    <span class="text-xs text-muted">Invested</span>
                    <span class="mono text-sm">₹${fmtIN(b.invested)}</span>
                  </div>
                  <div class="broker-detail-row">
                    <span class="text-xs text-muted">Current Value</span>
                    <span class="mono text-sm">₹${fmtIN(b.value)}</span>
                  </div>
                  <div class="broker-detail-row">
                    <span class="text-xs text-muted">Today's P&L</span>
                    <span class="mono text-sm ${b.today_pnl >= 0 ? "up" : "dn"}">${b.today_pnl >= 0 ? "+" : ""}${fmtIN(b.today_pnl)}</span>
                  </div>
                </div>
              </div>`;
          }).join("")}
        </div>
      </div>
      <div class="allocation-wrap card glass">
        <div class="card-header"><h3>Asset Allocation by Platform</h3></div>
        <div class="allocation-body">
          <div class="chart-container">
            <canvas id="portfolio-allocation-chart"></canvas>
          </div>
          <div class="allocation-legend" id="allocation-legend"></div>
        </div>
      </div>
    </div>`;
  renderAllocationChart(brokers);
}

function renderPortfolioTables(data, mode) {
  const container = document.getElementById("portfolio-tables-container");
  if (!container) return;

  mode = mode || "both";

  const holdings  = data.holdings;
  const positions = data.positions;
  const brokers   = data.brokers;

  // Remember filter state
  const prevQuery  = document.getElementById("portfolio-search")?.value || "";
  const prevBroker = document.getElementById("portfolio-broker-filter")?.value || "ALL";

  const brokerKeys = Object.keys(brokers);
  const brokerFilterOptions = brokerKeys.map(b => {
    const meta = BROKER_META[b] || { name: b };
    return `<option value="${b}">${meta.name}</option>`;
  }).join("");

  function holdingsTable() {
    return `<div class="table-card card glass">
      <div class="card-header table-card-header">
        <h3>Holdings</h3>
        <span class="badge-count" id="holdings-count">${holdings.length} scrips</span>
      </div>
      <div class="table-wrap">
        <table class="port-table" id="holdings-table">
          <thead><tr>
            <th>Scrip</th><th>Platform</th>
            <th class="num">Qty</th><th class="num">Avg. Price</th>
            <th class="num">LTP</th><th class="num">Market Value</th>
            <th class="num">P&amp;L (%)</th>
          </tr></thead>
          <tbody>
            ${holdings.map(h => {
              const cls = h.pnl > 0 ? "up" : h.pnl < 0 ? "dn" : "flat";
              return `<tr class="table-row" data-scrip="${h.scrip}" data-broker="${h.broker}">
                <td class="bold">${h.scrip}</td>
                <td><span class="broker-pill pill-${h.broker}">${(BROKER_META[h.broker]?.name || h.broker).toUpperCase()}</span></td>
                <td class="num mono">${h.qty}</td>
                <td class="num mono">${fmtPrice(h.avg_price, h.broker)}</td>
                <td class="num mono">${fmtPrice(h.ltp, h.broker)}</td>
                <td class="num mono">${fmtPrice(h.current_value, h.broker)}</td>
                <td class="num mono ${cls} bold">
                  ${h.pnl >= 0 ? "+" : ""}${fmtIN(h.pnl)}
                  <div class="text-xxs">${h.pnl_pct >= 0 ? "+" : ""}${h.pnl_pct.toFixed(2)}%</div>
                </td>
              </tr>`;
            }).join("")}
          </tbody>
        </table>
      </div>
    </div>`;
  }

  function positionsTable() {
    return `<div class="table-card card glass">
      <div class="card-header table-card-header">
        <h3>Open Positions</h3>
        <span class="badge-count" id="positions-count">${positions.length} active</span>
      </div>
      <div class="table-wrap">
        <table class="port-table" id="positions-table">
          <thead><tr>
            <th>Scrip</th><th>Platform</th><th>Product</th>
            <th class="num">Net Qty</th><th class="num">Avg. Price</th>
            <th class="num">LTP</th><th class="num">P&amp;L</th>
          </tr></thead>
          <tbody>
            ${positions.map(p => {
              const cls = p.pnl > 0 ? "up" : p.pnl < 0 ? "dn" : "flat";
              const sDot = p.qty !== 0 ? "open-pos" : "closed-pos";
              return `<tr class="table-row" data-scrip="${p.scrip}" data-broker="${p.broker}">
                <td class="bold">${p.scrip}<span class="status-dot ${sDot}"></span></td>
                <td><span class="broker-pill pill-${p.broker}">${(BROKER_META[p.broker]?.name || p.broker).toUpperCase()}</span></td>
                <td><span class="product-badge">${p.product}</span></td>
                <td class="num mono">${p.qty > 0 ? "+" : ""}${p.qty}</td>
                <td class="num mono">${fmtPrice(p.avg_price, p.broker)}</td>
                <td class="num mono">${fmtPrice(p.ltp, p.broker)}</td>
                <td class="num mono ${cls} bold">${p.pnl >= 0 ? "+" : ""}${fmtIN(p.pnl)}</td>
              </tr>`;
            }).join("")}
          </tbody>
        </table>
      </div>
    </div>`;
  }

  const gridClass = mode === "both" ? "portfolio-tables-grid" : "portfolio-tables-single";

  container.innerHTML = `
    <div class="portfolio-controls glass">
      <div class="search-input-wrap">
        <span class="search-icon">🔍</span>
        <input type="text" id="portfolio-search" placeholder="Search scrip (e.g. RELIANCE, BTC, EURUSD)..." oninput="filterPortfolioTables()">
      </div>
      <div class="filter-select-wrap">
        <label for="portfolio-broker-filter" class="text-xs text-muted">Platform:</label>
        <select id="portfolio-broker-filter" onchange="filterPortfolioTables()">
          <option value="ALL">All Platforms</option>
          ${brokerFilterOptions}
        </select>
      </div>
    </div>
    <div class="${gridClass}">
      ${mode === "positions" ? "" : holdingsTable()}
      ${mode === "holdings" ? "" : positionsTable()}
    </div>`;

  // Restore filter state
  if (prevQuery)  { const el = document.getElementById("portfolio-search");        if (el) el.value = prevQuery; }
  if (prevBroker) { const el = document.getElementById("portfolio-broker-filter"); if (el) el.value = prevBroker; }

  filterPortfolioTables();
}

// ── Allocation Chart ─────────────────────────────────────────────────────────

function renderAllocationChart(brokers) {
  const canvas = document.getElementById("portfolio-allocation-chart");
  if (!canvas) return;
  const keys   = Object.keys(brokers);
  const labels = keys.map(b => BROKER_META[b]?.name || b.toUpperCase());
  const values = keys.map(b => brokers[b].value || 0);
  const colors = keys.map((_, i) => SCRIP_COLORS[i % SCRIP_COLORS.length]);

  if (allocChartInstance) { allocChartInstance.destroy(); allocChartInstance = null; }
  const ctx = canvas.getContext("2d");
  allocChartInstance = new Chart(ctx, {
    type: "doughnut",
    data: { labels, datasets: [{ data: values, backgroundColor: colors, borderWidth: 2, borderColor: "#0F172A" }] },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#0F172A", borderColor: "#1E293B", borderWidth: 1,
          titleColor: "#FFF", bodyColor: "#94A3B8",
          callbacks: { label: ctx => {
            const val = ctx.parsed;
            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
            const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
            return ` ${ctx.label}: ₹${fmtIN(val)} (${pct}%)`;
          }}
        }
      },
      cutout: "70%"
    }
  });

  const legend = document.getElementById("allocation-legend");
  if (legend) {
    const total = values.reduce((a, b) => a + b, 0);
    legend.innerHTML = keys.map((b, i) => {
      const pct = total > 0 ? ((brokers[b].value / total) * 100).toFixed(1) : 0;
      return `<div class="legend-item">
        <span class="legend-color-dot" style="background:${colors[i]}"></span>
        <span class="legend-name">${labels[i]}</span>
        <span class="legend-val mono">${pct}%</span>
      </div>`;
    }).join("");
  }
}

// ── Broker Deepdive Modal ────────────────────────────────────────────────────

function openBrokerDeepdive(brokerName) {
  if (!latestPortfolioData) return;
  const data   = latestPortfolioData;
  const meta   = BROKER_META[brokerName] || { name: brokerName, letter: brokerName[0].toUpperCase(), category: "Platform", accent: "#94a3b8" };
  const b      = data.brokers[brokerName];
  if (!b) return;

  const bHoldings  = data.holdings.filter(h => h.broker === brokerName);
  const bPositions = data.positions.filter(p => p.broker === brokerName);

  const totalPnlCls = b.total_pnl > 0 ? "up" : b.total_pnl < 0 ? "dn" : "flat";
  const todayPnlCls = b.today_pnl > 0 ? "up" : b.today_pnl < 0 ? "dn" : "flat";

  // Win Rate metrics
  const winningHoldings  = bHoldings.filter(h => h.pnl > 0).length;
  const winningPositions = bPositions.filter(p => p.pnl > 0).length;
  const totalScrips      = bHoldings.length + bPositions.length;
  const winCount         = winningHoldings + winningPositions;
  const winRatePct       = totalScrips > 0 ? Math.round((winCount / totalScrips) * 100) : 0;
  const holdingsWinPct   = bHoldings.length > 0 ? Math.round((winningHoldings / bHoldings.length) * 100) : 0;
  const positionsWinPct  = bPositions.length > 0 ? Math.round((winningPositions / bPositions.length) * 100) : 0;
  const winColor         = winRatePct >= 60 ? "#10B981" : winRatePct >= 40 ? "#F59E0B" : "#EF4444";

  // Return on invested
  const roi = b.invested > 0 ? ((b.total_pnl / b.invested) * 100).toFixed(2) : "0.00";

  // Build modal HTML
  const overlay = document.createElement("div");
  overlay.className = "deepdive-overlay";
  overlay.id = "deepdive-overlay";

  overlay.innerHTML = `
    <div class="deepdive-modal" id="deepdive-modal">
      <!-- Header -->
      <div class="deepdive-header">
        <div class="deepdive-broker-identity">
          <div class="deepdive-logo logo-${brokerName}">${meta.letter}</div>
          <div>
            <div class="deepdive-broker-name">${meta.name}</div>
            <div class="deepdive-broker-type">${meta.category} &nbsp;·&nbsp; <span class="${b.is_mock ? "badge-mock" : "badge-live"}">${b.is_mock ? "Mocked Data" : "Live Feed"}</span></div>
          </div>
        </div>
        <button class="deepdive-close" onclick="closeDeepdive()" title="Close">✕</button>
      </div>

      <!-- Body -->
      <div class="deepdive-body">

        <!-- Stats Row -->
        <div class="deepdive-stats-row">
          <div class="deepdive-stat">
            <div class="deepdive-stat-label">Invested Capital</div>
            <div class="deepdive-stat-val">₹${fmtIN(b.invested)}</div>
            <div class="deepdive-stat-sub text-muted">${bHoldings.length} holdings · ${bPositions.length} positions</div>
          </div>
          <div class="deepdive-stat">
            <div class="deepdive-stat-label">Current Value</div>
            <div class="deepdive-stat-val">₹${fmtIN(b.value)}</div>
            <div class="deepdive-stat-sub text-muted">Market-to-market</div>
          </div>
          <div class="deepdive-stat">
            <div class="deepdive-stat-label">Total Returns</div>
            <div class="deepdive-stat-val ${totalPnlCls}">${b.total_pnl >= 0 ? "+" : ""}${fmtIN(b.total_pnl)}</div>
            <div class="deepdive-stat-sub ${totalPnlCls}">ROI ${b.total_pnl >= 0 ? "+" : ""}${roi}%</div>
          </div>
          <div class="deepdive-stat">
            <div class="deepdive-stat-label">Today's P&L</div>
            <div class="deepdive-stat-val ${todayPnlCls}">${b.today_pnl >= 0 ? "+" : ""}${fmtIN(b.today_pnl)}</div>
            <div class="deepdive-stat-sub ${todayPnlCls}">Intraday movement</div>
          </div>
        </div>

        <!-- Mid: scrip allocation donut + win-rate metrics -->
        <div class="deepdive-mid">
          <div class="deepdive-chart-wrap">
            <h4>Scrip Allocation</h4>
            <div class="deepdive-donut-container">
              <canvas id="deepdive-donut-chart"></canvas>
            </div>
            <div class="deepdive-legend" id="deepdive-donut-legend"></div>
          </div>

          <div class="deepdive-win-rate-wrap">
            <h4>Performance Analytics</h4>

            <div class="win-rate-metric">
              <span class="win-rate-label">Overall Win Rate</span>
              <div class="win-rate-bar-wrap">
                <div class="win-rate-bar" style="width:${winRatePct}%;background:${winColor}"></div>
              </div>
              <span class="win-rate-val" style="color:${winColor}">${winRatePct}%</span>
            </div>

            <div class="win-rate-metric">
              <span class="win-rate-label">Holdings Win Rate</span>
              <div class="win-rate-bar-wrap">
                <div class="win-rate-bar" style="width:${holdingsWinPct}%;background:#10B981"></div>
              </div>
              <span class="win-rate-val up">${holdingsWinPct}%</span>
            </div>

            <div class="win-rate-metric">
              <span class="win-rate-label">Positions Win Rate</span>
              <div class="win-rate-bar-wrap">
                <div class="win-rate-bar" style="width:${positionsWinPct}%;background:#3B82F6"></div>
              </div>
              <span class="win-rate-val" style="color:#93c5fd">${positionsWinPct}%</span>
            </div>

            <div style="margin-top:18px;border-top:1px solid rgba(255,255,255,0.05);padding-top:14px;">
              <div class="win-rate-metric">
                <span class="win-rate-label">Winning Positions</span>
                <div class="win-rate-bar-wrap"></div>
                <span class="win-rate-val up">${winCount} / ${totalScrips}</span>
              </div>
              <div class="win-rate-metric">
                <span class="win-rate-label">Total P&L Contribution</span>
                <div class="win-rate-bar-wrap"></div>
                <span class="win-rate-val ${totalPnlCls}">${b.total_pnl >= 0 ? "+" : ""}${roi}%</span>
              </div>
              <div class="win-rate-metric">
                <span class="win-rate-label">Unrealised Gain/Loss</span>
                <div class="win-rate-bar-wrap"></div>
                <span class="win-rate-val ${totalPnlCls}">${b.total_pnl >= 0 ? "+" : ""}${fmtIN(b.total_pnl)}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Holdings Table -->
        ${bHoldings.length > 0 ? `
        <div class="deepdive-section-title">Holdings (${bHoldings.length})</div>
        <div class="table-wrap" style="margin-bottom:20px">
          <table class="port-table">
            <thead><tr>
              <th>Scrip</th><th class="num">Qty</th><th class="num">Avg Price</th>
              <th class="num">LTP</th><th class="num">Market Value</th><th class="num">P&L</th><th class="num">Return %</th>
            </tr></thead>
            <tbody>
              ${bHoldings.map(h => {
                const cls = h.pnl > 0 ? "up" : h.pnl < 0 ? "dn" : "flat";
                return `<tr>
                  <td class="bold">${h.scrip}</td>
                  <td class="num mono">${h.qty}</td>
                  <td class="num mono">${fmtPrice(h.avg_price, brokerName)}</td>
                  <td class="num mono">${fmtPrice(h.ltp, brokerName)}</td>
                  <td class="num mono">${fmtPrice(h.current_value, brokerName)}</td>
                  <td class="num mono ${cls} bold">${h.pnl >= 0 ? "+" : ""}${fmtIN(h.pnl)}</td>
                  <td class="num mono ${cls}">${h.pnl_pct >= 0 ? "+" : ""}${h.pnl_pct.toFixed(2)}%</td>
                </tr>`;
              }).join("")}
            </tbody>
          </table>
        </div>` : `<div class="deepdive-empty">No holdings for this account.</div>`}

        <!-- Positions Table -->
        ${bPositions.length > 0 ? `
        <div class="deepdive-section-title">Open Positions (${bPositions.length})</div>
        <div class="table-wrap">
          <table class="port-table">
            <thead><tr>
              <th>Scrip</th><th>Product</th>
              <th class="num">Net Qty</th><th class="num">Avg Price</th>
              <th class="num">LTP</th><th class="num">P&L</th>
            </tr></thead>
            <tbody>
              ${bPositions.map(p => {
                const cls  = p.pnl > 0 ? "up" : p.pnl < 0 ? "dn" : "flat";
                const sDot = p.qty !== 0 ? "open-pos" : "closed-pos";
                return `<tr>
                  <td class="bold">${p.scrip}<span class="status-dot ${sDot}"></span></td>
                  <td><span class="product-badge">${p.product}</span></td>
                  <td class="num mono">${p.qty > 0 ? "+" : ""}${p.qty}</td>
                  <td class="num mono">${fmtPrice(p.avg_price, brokerName)}</td>
                  <td class="num mono">${fmtPrice(p.ltp, brokerName)}</td>
                  <td class="num mono ${cls} bold">${p.pnl >= 0 ? "+" : ""}${fmtIN(p.pnl)}</td>
                </tr>`;
              }).join("")}
            </tbody>
          </table>
        </div>` : `<div class="deepdive-empty">No open positions.</div>`}

      </div>
    </div>
  `;

  document.body.appendChild(overlay);
  document.body.style.overflow = "hidden";

  // Close on overlay background click
  overlay.addEventListener("click", e => { if (e.target === overlay) closeDeepdive(); });

  // Close on Escape key
  document.addEventListener("keydown", _escHandler);

  // Render scrip-level allocation doughnut
  renderDeepdiveDonut(bHoldings, bPositions, meta.accent);
}

function _escHandler(e) {
  if (e.key === "Escape") closeDeepdive();
}

function closeDeepdive() {
  if (deepdiveChartInst) { deepdiveChartInst.destroy(); deepdiveChartInst = null; }
  const overlay = document.getElementById("deepdive-overlay");
  if (overlay) overlay.remove();
  document.body.style.overflow = "";
  document.removeEventListener("keydown", _escHandler);
}

function renderDeepdiveDonut(holdings, positions, accentColor) {
  const canvas = document.getElementById("deepdive-donut-chart");
  if (!canvas) return;

  // Build scrip → value mapping (holdings use current_value; positions use abs pnl contribution)
  const scripMap = {};
  holdings.forEach(h  => { scripMap[h.scrip] = (scripMap[h.scrip] || 0) + Math.abs(h.current_value || 0); });
  positions.forEach(p => { scripMap[p.scrip] = (scripMap[p.scrip] || 0) + Math.abs(p.pnl || 0) + 100; });

  const entries = Object.entries(scripMap).filter(([, v]) => v > 0);
  if (!entries.length) return;

  const labels = entries.map(([s]) => s);
  const values = entries.map(([, v]) => v);
  const colors = labels.map((_, i) => SCRIP_COLORS[i % SCRIP_COLORS.length]);

  const ctx = canvas.getContext("2d");
  deepdiveChartInst = new Chart(ctx, {
    type: "doughnut",
    data: { labels, datasets: [{ data: values, backgroundColor: colors, borderWidth: 1.5, borderColor: "#0A1120" }] },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#0F172A", borderColor: "#1E293B", borderWidth: 1,
          titleColor: "#FFF", bodyColor: "#94A3B8",
          callbacks: { label: ctx => {
            const val   = ctx.parsed;
            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
            const pct   = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
            return ` ${ctx.label}: ${pct}%`;
          }}
        }
      },
      cutout: "65%"
    }
  });

  const legend = document.getElementById("deepdive-donut-legend");
  if (legend) {
    const total = values.reduce((a, b) => a + b, 0);
    legend.innerHTML = entries.map(([scrip, val], i) => {
      const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
      return `<div class="deepdive-legend-item">
        <span class="deepdive-legend-dot" style="background:${colors[i]}"></span>
        <span style="flex:1;color:var(--text)">${scrip}</span>
        <span style="color:var(--muted)">${pct}%</span>
      </div>`;
    }).join("");
  }
}

// ── Table Filtering ───────────────────────────────────────────────────────────

function filterPortfolioTables() {
  const query  = document.getElementById("portfolio-search")?.value.toLowerCase().trim() || "";
  const broker = document.getElementById("portfolio-broker-filter")?.value || "ALL";

  let vh = 0;
  document.querySelectorAll("#holdings-table tbody tr").forEach(row => {
    const scrip   = row.getAttribute("data-scrip").toLowerCase();
    const rb      = row.getAttribute("data-broker");
    const show    = scrip.includes(query) && (broker === "ALL" || rb === broker);
    row.style.display = show ? "" : "none";
    if (show) vh++;
  });
  const hc = document.getElementById("holdings-count");
  if (hc) hc.textContent = `${vh} scrips`;

  let vp = 0;
  document.querySelectorAll("#positions-table tbody tr").forEach(row => {
    const scrip   = row.getAttribute("data-scrip").toLowerCase();
    const rb      = row.getAttribute("data-broker");
    const show    = scrip.includes(query) && (broker === "ALL" || rb === broker);
    row.style.display = show ? "" : "none";
    if (show) vp++;
  });
  const pc = document.getElementById("positions-count");
  if (pc) pc.textContent = `${vp} active`;
}

// ── Price Formatting (platform-aware) ────────────────────────────────────────

function fmtPrice(v, broker) {
  if (v == null) return "—";
  // Crypto / FX brokers show USD values without ₹
  const fxBrokers = ["hyperliquid", "exness", "binance"];
  if (fxBrokers.includes(broker)) {
    // For very small prices (DOGE, EURUSD decimals) use more decimal places
    const decimals = Math.abs(v) < 1 ? 4 : 2;
    return "$" + Number(v).toLocaleString("en-US", {
      minimumFractionDigits: decimals, maximumFractionDigits: decimals,
    });
  }
  return "₹" + fmtIN(v, 2);
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmt(v, d = 2) {
  if (v == null) return "—";
  return Number(v).toFixed(d);
}

function fmtIN(v, d = 2) {
  if (v == null) return "—";
  return Number(v).toLocaleString("en-IN", {
    minimumFractionDigits: d, maximumFractionDigits: d,
  });
}

function showError(msg) {
  const el = document.getElementById("error-banner");
  if (el) { el.textContent = `⚠ ${msg}`; el.style.display = "block"; }
  console.error("[DVR Portfolio]", msg);
}

function loadingHTML() {
  return `<div class="loading"><div class="spinner"></div><span>Fetching data…</span></div>`;
}
