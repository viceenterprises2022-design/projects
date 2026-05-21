/**
 * AlphaEdge Dashboard — app.js
 * Fetches from FastAPI on localhost:8765
 * Renders signal cards, Chart.js history charts, macro cells, and ticker
 */

const API_BASE = "http://localhost:8765";
const SYMBOLS  = ["NIFTY", "SENSEX", "BANKNIFTY"];
const REFRESH_MS = 60_000; // re-poll every 60 seconds

// Chart instances (keyed by sym)
const chartInstances = {};

// ── Bootstrap ────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  buildTabs();
  loadLatest();
  setInterval(() => {
    loadLatest();
    if (document.getElementById("tab-PORTFOLIO")?.classList.contains("active")) {
      loadPortfolio();
    }
  }, REFRESH_MS);
});

// ── Tab Logic ────────────────────────────────────────────────────────────────

function buildTabs() {
  const tabBar  = document.getElementById("sym-tabs");
  const panels  = document.getElementById("sym-panels");

  SYMBOLS.forEach((sym, i) => {
    // Tab button
    const btn = document.createElement("button");
    btn.className = "sym-tab" + (i === 0 ? " active" : "");
    btn.id = `tab-${sym}`;
    btn.textContent = sym;
    btn.addEventListener("click", () => switchTab(sym));
    tabBar.appendChild(btn);

    // Panel
    const panel = document.createElement("div");
    panel.className = "sym-panel" + (i === 0 ? " active" : "");
    panel.id = `panel-${sym}`;
    panel.innerHTML = loadingHTML();
    panels.appendChild(panel);
  });

  // Build Portfolio Tab
  const pBtn = document.createElement("button");
  pBtn.className = "sym-tab";
  pBtn.id = "tab-PORTFOLIO";
  pBtn.textContent = "PORTFOLIO";
  pBtn.addEventListener("click", () => switchTab("PORTFOLIO"));
  tabBar.appendChild(pBtn);

  // Build Portfolio Panel
  const pPanel = document.createElement("div");
  pPanel.className = "sym-panel";
  pPanel.id = "panel-PORTFOLIO";
  pPanel.innerHTML = loadingHTML();
  panels.appendChild(pPanel);
}

function switchTab(sym) {
  SYMBOLS.forEach(s => {
    document.getElementById(`tab-${s}`)?.classList.toggle("active", s === sym);
    document.getElementById(`panel-${s}`)?.classList.toggle("active", s === sym);
  });

  document.getElementById("tab-PORTFOLIO")?.classList.toggle("active", sym === "PORTFOLIO");
  document.getElementById("panel-PORTFOLIO")?.classList.toggle("active", sym === "PORTFOLIO");

  if (sym === "PORTFOLIO") {
    loadPortfolio();
  } else {
    // Trigger chart resize on tab show
    const inst = chartInstances[sym];
    if (inst) Object.values(inst).forEach(c => c?.resize());
  }
}

// ── Data Fetch ───────────────────────────────────────────────────────────────

async function loadLatest() {
  try {
    const [latest] = await Promise.all([
      fetch(`${API_BASE}/api/latest`).then(r => {
        if (!r.ok) throw new Error(`/api/latest → ${r.status}`);
        return r.json();
      }),
    ]);

    renderTimestamp(latest.recorded_at);
    renderTicker(latest.symbols, latest.macro);
    renderMacro(latest.macro);

    for (const sym of SYMBOLS) {
      const data = latest.symbols[sym];
      if (data) {
        renderSignalCard(sym, data);
        loadHistory(sym, "30");
      }
    }
  } catch (err) {
    showError(err.message);
  }
}

async function loadHistory(sym, days) {
  try {
    const res = await fetch(`${API_BASE}/api/history?sym=${sym}&days=${days}`);
    if (!res.ok) throw new Error(`/api/history → ${res.status}`);
    const data = await res.json();
    renderChartCard(sym, data.rows);
  } catch (err) {
    console.warn(`History fetch failed for ${sym}:`, err);
  }
}

// ── Ticker ───────────────────────────────────────────────────────────────────

function renderTicker(symbols, macro) {
  const items = [
    ...SYMBOLS.map(sym => {
      const d = symbols[sym] || {};
      return { name: sym, val: fmt(d.ltp, 2), chg: d.change_pct };
    }),
    { name: "VIX",    val: fmt(macro.vix?.ltp, 2),    chg: macro.vix?.chg },
    { name: "DXY",    val: fmt(macro.dxy?.ltp, 3),    chg: macro.dxy?.chg },
    { name: "CRUDE",  val: "$" + fmt(macro.crude?.ltp, 2), chg: macro.crude?.chg },
    { name: "US30",   val: fmt(macro.us30?.ltp, 0),   chg: macro.us30?.chg },
    { name: "GOLD",   val: "$" + fmt(macro.gold?.ltp, 1), chg: macro.gold?.chg },
    { name: "SILVER", val: "$" + fmt(macro.silver?.ltp, 2), chg: macro.silver?.chg },
  ];

  const html = [...items, ...items].map(({ name, val, chg }) => {
    const cv = parseFloat(chg) || 0;
    const cls = cv > 0 ? "up" : cv < 0 ? "dn" : "flat";
    const arrow = cv >= 0 ? "▲" : "▼";
    return `<div class="ticker-item">
      <span class="ticker-name">${name}</span>
      <span class="ticker-val">${val ?? "—"}</span>
      <span class="ticker-chg ${cls}">${arrow} ${Math.abs(cv).toFixed(2)}%</span>
    </div>`;
  }).join("");

  document.getElementById("ticker").innerHTML = html;
}

// ── Timestamp ────────────────────────────────────────────────────────────────

function renderTimestamp(ts) {
  const el = document.getElementById("last-updated");
  if (!el || !ts) return;
  const d = new Date(ts + "Z");
  el.textContent = `Updated: ${d.toLocaleTimeString("en-IN", { hour12: false })} UTC`;
}

// ── Signal Card ───────────────────────────────────────────────────────────────

function renderSignalCard(sym, data) {
  const panel = document.getElementById(`panel-${sym}`);
  if (!panel) return;

  // Find or create the signal card slot
  let slot = panel.querySelector(".signal-card");
  if (!slot) {
    // First render: build full panel structure
    panel.innerHTML = `
      <div class="panel-grid">
        <div class="signal-card card"></div>
        <div class="chart-card card">
          <div class="card-header">
            <h3>Price &amp; Signal Score History</h3>
            <div class="chart-tabs">
              <button class="chart-tab active" data-days="7"  data-sym="${sym}">7d</button>
              <button class="chart-tab"        data-days="30" data-sym="${sym}">30d</button>
            </div>
          </div>
          <div class="chart-wrap">
            <canvas id="chart-${sym}"></canvas>
          </div>
        </div>
      </div>`;

    // Attach tab listeners
    panel.querySelectorAll(".chart-tab").forEach(btn => {
      btn.addEventListener("click", () => {
        panel.querySelectorAll(".chart-tab").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        loadHistory(btn.dataset.sym, btn.dataset.days);
      });
    });

    slot = panel.querySelector(".signal-card");
  }

  const sig   = data.signal || "NEUTRAL";
  const chg   = data.change_pct ?? 0;
  const ltpColor = sig === "BUY" ? "var(--primary)" : sig === "SELL" ? "var(--error)" : "var(--warning)";
  const scoreColor = sig === "BUY" ? "#10B981" : sig === "SELL" ? "#EF4444" : "#F59E0B";
  const scorePct = data.factors ? Math.round(((data.score / data.factors) + 1) / 2 * 100) : 50;

  const indRows = Object.entries(data.indicators || {}).map(([key, ind], i) => {
    const ic = ind.score > 0 ? "#10B981" : ind.score < 0 ? "#EF4444" : "#F59E0B";
    return `<div class="ind-row">
      <div class="ind-num" style="background:${ic}22;color:${ic};border:1px solid ${ic}33">${i + 1}</div>
      <div class="ind-body">
        <div class="ind-name">${indName(key)}</div>
        <div class="ind-label">${ind.label ?? "—"}</div>
        <div class="ind-detail">${ind.detail ?? ""}</div>
      </div>
      <div class="ind-pip" style="background:${ic};box-shadow:0 0 4px ${ic}"></div>
    </div>`;
  }).join("");

  slot.innerHTML = `
    <div class="card-header signal-card-head">
      <div>
        <div class="sym-label">${sym}</div>
        <div class="price-row">
          <div class="ltp" style="color:${ltpColor}">${fmtIN(data.ltp, 2)}</div>
          <div class="chg-pct ${chg >= 0 ? "up" : "dn"}">${chg >= 0 ? "▲" : "▼"} ${Math.abs(chg).toFixed(2)}%</div>
        </div>
        <div class="ohlc-row">
          <div class="ohlc-cell"><span class="ohlc-label">OPEN</span><span class="ohlc-val">${fmtIN(data.open, 2)}</span></div>
          <div class="ohlc-cell"><span class="ohlc-label">HIGH</span><span class="ohlc-val up">${fmtIN(data.high, 2)}</span></div>
          <div class="ohlc-cell"><span class="ohlc-label">LOW</span><span class="ohlc-val dn">${fmtIN(data.low, 2)}</span></div>
        </div>
      </div>
      <div class="signal-badge ${sig}">${sigIcon(sig)} ${sig}</div>
    </div>
    <div class="score-row">
      <span class="score-label text-xs text-muted">Score</span>
      <div class="score-bar-wrap">
        <div class="score-bar" style="width:${scorePct}%;background:${scoreColor}"></div>
      </div>
      <span class="score-num">${data.score > 0 ? "+" : ""}${data.score}/${data.factors}</span>
    </div>
    <div class="ind-list">${indRows}</div>
    ${data.pcr ? `
    <div class="card-body" style="padding-top:8px;border-top:1px solid var(--border)">
      <div style="display:flex;gap:16px;font-family:var(--mono);font-size:0.7rem;color:var(--muted)">
        <span>PCR <strong style="color:var(--text)">${(data.pcr).toFixed(2)}</strong></span>
        <span>Max Pain <strong style="color:#a78bfa">${fmtIN(data.max_pain, 0)}</strong></span>
        <span>Expiry <strong style="color:var(--text)">${data.expiry ?? "—"}</strong></span>
      </div>
    </div>` : ""}`;
}

// ── Chart.js ─────────────────────────────────────────────────────────────────

function renderChartCard(sym, rows) {
  const canvas = document.getElementById(`chart-${sym}`);
  if (!canvas || !rows?.length) return;

  const labels    = rows.map(r => fmtTime(r.recorded_at));
  const ltpData   = rows.map(r => r.ltp);
  const scoreData = rows.map(r => r.score);

  if (chartInstances[sym]) {
    chartInstances[sym].destroy();
  }

  const ctx = canvas.getContext("2d");

  chartInstances[sym] = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Price (LTP)",
          data: ltpData,
          borderColor: "#10B981",
          backgroundColor: "rgba(16,185,129,0.08)",
          borderWidth: 1.5,
          pointRadius: 0,
          pointHoverRadius: 4,
          tension: 0.3,
          fill: true,
          yAxisID: "yPrice",
        },
        {
          label: "Signal Score",
          data: scoreData,
          borderColor: "#3B82F6",
          backgroundColor: "rgba(59,130,246,0.08)",
          borderWidth: 1.5,
          pointRadius: 0,
          pointHoverRadius: 4,
          tension: 0.3,
          fill: false,
          yAxisID: "yScore",
          borderDash: [4, 2],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      animation: { duration: 300 },
      plugins: {
        legend: {
          labels: {
            color: "#94A3B8",
            font: { family: "JetBrains Mono, monospace", size: 11 },
            boxWidth: 12,
            padding: 16,
          },
        },
        tooltip: {
          backgroundColor: "#0F172A",
          borderColor: "#1E293B",
          borderWidth: 1,
          titleColor: "#FFFFFF",
          bodyColor: "#94A3B8",
          titleFont: { family: "JetBrains Mono, monospace", size: 11 },
          bodyFont:  { family: "JetBrains Mono, monospace", size: 11 },
          callbacks: {
            label: ctx => {
              const v = ctx.parsed.y;
              if (ctx.datasetIndex === 0) return ` Price: ${fmtIN(v, 2)}`;
              return ` Score: ${v > 0 ? "+" : ""}${v}`;
            },
          },
        },
      },
      scales: {
        x: {
          ticks: {
            color: "#94A3B8",
            font: { family: "JetBrains Mono, monospace", size: 10 },
            maxTicksLimit: 8,
            maxRotation: 0,
          },
          grid: { color: "rgba(30,41,59,0.8)" },
          border: { color: "#1E293B" },
        },
        yPrice: {
          position: "left",
          ticks: {
            color: "#94A3B8",
            font: { family: "JetBrains Mono, monospace", size: 10 },
            callback: v => fmtIN(v, 0),
          },
          grid: { color: "rgba(30,41,59,0.8)" },
          border: { color: "#1E293B" },
        },
        yScore: {
          position: "right",
          min: -10, max: 10,
          ticks: {
            color: "#3B82F6",
            font: { family: "JetBrains Mono, monospace", size: 10 },
            stepSize: 2,
          },
          grid: { drawOnChartArea: false },
          border: { color: "#1E293B" },
        },
      },
    },
  });
}

// ── Macro Cells ───────────────────────────────────────────────────────────────

function renderMacro(macro) {
  const items = [
    { name: "India VIX", key: "vix",    pre: "" },
    { name: "DXY",       key: "dxy",    pre: "" },
    { name: "Crude Oil", key: "crude",  pre: "$" },
    { name: "US30",      key: "us30",   pre: "" },
    { name: "Gold",      key: "gold",   pre: "$" },
    { name: "Silver",    key: "silver", pre: "$" },
  ];
  const container = document.getElementById("macro-row");
  if (!container) return;

  container.innerHTML = items.map(({ name, key, pre }) => {
    const d = macro[key] || {};
    const chg = d.chg ?? 0;
    const cls = chg > 0 ? "up" : chg < 0 ? "dn" : "flat";
    const arrow = chg >= 0 ? "▲" : "▼";
    return `<div class="macro-cell">
      <div class="macro-name">${name}</div>
      <div class="macro-val">${pre}${d.ltp != null ? fmtIN(d.ltp, key === "dxy" ? 3 : 2) : "—"}</div>
      <div class="macro-chg ${cls}">${arrow} ${Math.abs(chg).toFixed(2)}%</div>
    </div>`;
  }).join("");
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

function fmtTime(ts) {
  if (!ts) return "";
  const d = new Date(ts + (ts.endsWith("Z") ? "" : "Z"));
  // If same day, show time only; else show date
  const today = new Date();
  if (d.toDateString() === today.toDateString()) {
    return d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false });
  }
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
}

function sigIcon(sig) {
  return sig === "BUY" ? "▲" : sig === "SELL" ? "▼" : "◆";
}

const IND_NAMES = {
  trend: "Trend", dow_jones: "Dow Jones", india_vix: "India VIX",
  oi: "Open Interest", vwap: "VWAP", supertrend: "Supertrend",
  rsi: "RSI (14)", dxy: "USD Index", crude: "Crude Oil", pcr: "Put-Call Ratio",
};
function indName(k) { return IND_NAMES[k] || k; }

function loadingHTML() {
  return `<div class="loading"><div class="spinner"></div><span>Fetching data…</span></div>`;
}

function showError(msg) {
  const el = document.getElementById("error-banner");
  if (el) { el.textContent = `⚠ ${msg}`; el.style.display = "block"; }
  console.error("[AlphaEdge]", msg);
}

// ── Portfolio Logic ──────────────────────────────────────────────────────────

async function loadPortfolio() {
  try {
    const res = await fetch(`${API_BASE}/api/portfolio/pnl`);
    if (!res.ok) throw new Error(`/api/portfolio/pnl → ${res.status}`);
    const data = await res.json();
    renderPortfolio(data);
  } catch (err) {
    console.error("Failed to load portfolio:", err);
    const panel = document.getElementById("panel-PORTFOLIO");
    if (panel) {
      panel.innerHTML = `<div class="error-banner">Failed to fetch Portfolio P&L: ${err.message}</div>`;
    }
  }
}

function renderPortfolio(data) {
  const panel = document.getElementById("panel-PORTFOLIO");
  if (!panel) return;

  const s = data.summary;
  const brokers = data.brokers;
  const holdings = data.holdings;
  const positions = data.positions;

  const totalPnlCls = s.total_pnl > 0 ? "up" : s.total_pnl < 0 ? "dn" : "flat";
  const todayPnlCls = s.today_pnl > 0 ? "up" : s.today_pnl < 0 ? "dn" : "flat";
  const totalArrow = s.total_pnl >= 0 ? "▲" : "▼";
  const todayArrow = s.today_pnl >= 0 ? "▲" : "▼";

  panel.innerHTML = `
    <!-- Top Summary Cards -->
    <div class="portfolio-summary-grid">
      <div class="port-card glass">
        <div class="port-card-label">Net Portfolio Value</div>
        <div class="port-card-val primary-glow">₹${fmtIN(s.current_value)}</div>
        <div class="port-card-sub ${totalPnlCls}">${totalArrow} ₹${fmtIN(Math.abs(s.total_pnl))} (${s.total_pnl_pct.toFixed(2)}%)</div>
      </div>
      
      <div class="port-card glass">
        <div class="port-card-label">Invested Capital</div>
        <div class="port-card-val">₹${fmtIN(s.total_invested)}</div>
        <div class="port-card-sub text-muted">All active brokers</div>
      </div>

      <div class="port-card glass">
        <div class="port-card-label">Total Returns</div>
        <div class="port-card-val ${totalPnlCls}">${totalArrow} ₹${fmtIN(Math.abs(s.total_pnl))}</div>
        <div class="port-card-sub ${totalPnlCls}">${s.total_pnl_pct.toFixed(2)}% Cumulative</div>
      </div>

      <div class="port-card glass">
        <div class="port-card-label">Today's Returns</div>
        <div class="port-card-val ${todayPnlCls}">${todayArrow} ₹${fmtIN(Math.abs(s.today_pnl))}</div>
        <div class="port-card-sub ${todayPnlCls}">${s.today_pnl_pct.toFixed(2)}% Daily</div>
      </div>
    </div>

    <!-- Mid Section: Broker Cards + Allocation Chart -->
    <div class="portfolio-mid-grid">
      <div class="broker-cards-wrap">
        <h3 class="section-title">Broker Accounts</h3>
        <div class="broker-cards-list">
          ${Object.entries(brokers).map(([name, b]) => {
            const bPnlCls = b.total_pnl > 0 ? "up" : b.total_pnl < 0 ? "dn" : "flat";
            const statusLabel = b.is_mock ? "Mocked" : "Live";
            const statusClass = b.is_mock ? "badge-mock" : "badge-live";
            return `
              <div class="broker-card glass">
                <div class="broker-card-header">
                  <div class="broker-logo-wrap">
                    <span class="broker-logo logo-${name}">${name[0].toUpperCase()}</span>
                    <div>
                      <div class="broker-name">${name.toUpperCase()}</div>
                      <span class="broker-badge ${statusClass}">${statusLabel}</span>
                    </div>
                  </div>
                  <div class="broker-pnl ${bPnlCls}">${b.total_pnl >= 0 ? "+" : ""}${fmtIN(b.total_pnl)}</div>
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
              </div>
            `;
          }).join("")}
        </div>
      </div>

      <div class="allocation-wrap card glass">
        <div class="card-header">
          <h3>Asset Allocation</h3>
        </div>
        <div class="allocation-body">
          <div class="chart-container">
            <canvas id="portfolio-allocation-chart"></canvas>
          </div>
          <div class="allocation-legend" id="allocation-legend"></div>
        </div>
      </div>
    </div>

    <!-- Filter & Search Controls -->
    <div class="portfolio-controls glass">
      <div class="search-input-wrap">
        <span class="search-icon">🔍</span>
        <input type="text" id="portfolio-search" placeholder="Search scrip (e.g. RELIANCE, TCS)..." oninput="filterPortfolioTables()">
      </div>
      <div class="filter-select-wrap">
        <label for="portfolio-broker-filter" class="text-xs text-muted">Broker:</label>
        <select id="portfolio-broker-filter" onchange="filterPortfolioTables()">
          <option value="ALL">All Brokers</option>
          <option value="upstox">Upstox</option>
          <option value="dhan">Dhan</option>
          <option value="tradesmart">TradeSmart</option>
        </select>
      </div>
    </div>

    <!-- Bottom Section: Holdings & Positions Tables -->
    <div class="portfolio-tables-grid">
      <!-- Holdings Section -->
      <div class="table-card card glass">
        <div class="card-header table-card-header">
          <h3>Long-Term Holdings</h3>
          <span class="badge-count" id="holdings-count">${holdings.length} scrips</span>
        </div>
        <div class="table-wrap">
          <table class="port-table" id="holdings-table">
            <thead>
              <tr>
                <th>Scrip</th>
                <th>Broker</th>
                <th class="num">Qty</th>
                <th class="num">Avg. Price</th>
                <th class="num">LTP</th>
                <th class="num">Market Value</th>
                <th class="num">P&L (%)</th>
              </tr>
            </thead>
            <tbody>
              ${holdings.map(h => {
                const hPnlCls = h.pnl > 0 ? "up" : h.pnl < 0 ? "dn" : "flat";
                return `
                  <tr class="table-row" data-scrip="${h.scrip}" data-broker="${h.broker}">
                    <td class="bold">${h.scrip}</td>
                    <td><span class="broker-pill pill-${h.broker}">${h.broker.toUpperCase()}</span></td>
                    <td class="num mono">${h.qty}</td>
                    <td class="num mono">₹${fmtIN(h.avg_price)}</td>
                    <td class="num mono">₹${fmtIN(h.ltp)}</td>
                    <td class="num mono">₹${fmtIN(h.current_value)}</td>
                    <td class="num mono ${hPnlCls} bold">
                      ${h.pnl >= 0 ? "+" : ""}${fmtIN(h.pnl)}
                      <div class="text-xxs">${h.pnl_pct >= 0 ? "+" : ""}${h.pnl_pct.toFixed(2)}%</div>
                    </td>
                  </tr>
                `;
              }).join("")}
            </tbody>
          </table>
        </div>
      </div>

      <!-- Positions Section -->
      <div class="table-card card glass">
        <div class="card-header table-card-header">
          <h3>Intraday Positions</h3>
          <span class="badge-count" id="positions-count">${positions.length} active</span>
        </div>
        <div class="table-wrap">
          <table class="port-table" id="positions-table">
            <thead>
              <tr>
                <th>Scrip</th>
                <th>Broker</th>
                <th>Product</th>
                <th class="num">Net Qty</th>
                <th class="num">Avg. Price</th>
                <th class="num">LTP</th>
                <th class="num">P&L</th>
              </tr>
            </thead>
            <tbody>
              ${positions.map(p => {
                const pPnlCls = p.pnl > 0 ? "up" : p.pnl < 0 ? "dn" : "flat";
                const statusClass = p.qty !== 0 ? "open-pos" : "closed-pos";
                return `
                  <tr class="table-row" data-scrip="${p.scrip}" data-broker="${p.broker}">
                    <td class="bold">
                      ${p.scrip}
                      <span class="status-dot ${statusClass}"></span>
                    </td>
                    <td><span class="broker-pill pill-${p.broker}">${p.broker.toUpperCase()}</span></td>
                    <td><span class="product-badge">${p.product}</span></td>
                    <td class="num mono">${p.qty > 0 ? "+" : ""}${p.qty}</td>
                    <td class="num mono">₹${fmtIN(p.avg_price)}</td>
                    <td class="num mono">₹${fmtIN(p.ltp)}</td>
                    <td class="num mono ${pPnlCls} bold">${p.pnl >= 0 ? "+" : ""}${fmtIN(p.pnl)}</td>
                  </tr>
                `;
              }).join("")}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;

  renderAllocationChart(brokers);
}

let allocationChartInstance = null;

function renderAllocationChart(brokers) {
  const canvas = document.getElementById("portfolio-allocation-chart");
  if (!canvas) return;

  const labels = Object.keys(brokers).map(b => b.toUpperCase());
  const dataValues = Object.values(brokers).map(b => b.value);
  const colors = ["#10B981", "#3B82F6", "#F59E0B"]; // Emerald, Blue, Gold

  if (allocationChartInstance) {
    allocationChartInstance.destroy();
  }

  const ctx = canvas.getContext("2d");
  allocationChartInstance = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{
        data: dataValues,
        backgroundColor: colors,
        borderWidth: 2,
        borderColor: "#0F172A",
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#0F172A",
          borderColor: "#1E293B",
          borderWidth: 1,
          titleColor: "#FFFFFF",
          bodyColor: "#94A3B8",
          callbacks: {
            label: (ctx) => {
              const val = ctx.parsed;
              const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
              const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
              return ` ${ctx.label}: ₹${fmtIN(val)} (${pct}%)`;
            }
          }
        }
      },
      cutout: "70%"
    }
  });

  const legend = document.getElementById("allocation-legend");
  if (legend) {
    const total = dataValues.reduce((a, b) => a + b, 0);
    legend.innerHTML = Object.entries(brokers).map(([name, b], i) => {
      const pct = total > 0 ? ((b.value / total) * 100).toFixed(1) : 0;
      return `
        <div class="legend-item">
          <span class="legend-color-dot" style="background:${colors[i]}"></span>
          <span class="legend-name">${name.toUpperCase()}</span>
          <span class="legend-val mono">${pct}%</span>
        </div>
      `;
    }).join("");
  }
}

function filterPortfolioTables() {
  const query = document.getElementById("portfolio-search")?.value.toLowerCase().trim() || "";
  const broker = document.getElementById("portfolio-broker-filter")?.value || "ALL";

  let visibleHoldings = 0;
  const holdingsRows = document.querySelectorAll("#holdings-table tbody tr");
  holdingsRows.forEach(row => {
    const scrip = row.getAttribute("data-scrip").toLowerCase();
    const rowBroker = row.getAttribute("data-broker");
    const matchesSearch = scrip.includes(query);
    const matchesBroker = broker === "ALL" || rowBroker === broker;

    if (matchesSearch && matchesBroker) {
      row.style.display = "";
      visibleHoldings++;
    } else {
      row.style.display = "none";
    }
  });
  const holdingsCountEl = document.getElementById("holdings-count");
  if (holdingsCountEl) holdingsCountEl.textContent = `${visibleHoldings} scrips`;

  let visiblePositions = 0;
  const positionsRows = document.querySelectorAll("#positions-table tbody tr");
  positionsRows.forEach(row => {
    const scrip = row.getAttribute("data-scrip").toLowerCase();
    const rowBroker = row.getAttribute("data-broker");
    const matchesSearch = scrip.includes(query);
    const matchesBroker = broker === "ALL" || rowBroker === broker;

    if (matchesSearch && matchesBroker) {
      row.style.display = "";
      visiblePositions++;
    } else {
      row.style.display = "none";
    }
  });
  const positionsCountEl = document.getElementById("positions-count");
  if (positionsCountEl) positionsCountEl.textContent = `${visiblePositions} active`;
}
