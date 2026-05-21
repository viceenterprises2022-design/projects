/**
 * AlphaEdge Dashboard — app.js (Portfolio-Only Edition)
 * Fetches from FastAPI on localhost:8765
 * Renders portfolio stats, asset allocation, broker accounts, holdings/positions tables, macros, and combined ticker
 */

const API_BASE = "http://localhost:8765";
const REFRESH_MS = 30_000; // re-poll every 30 seconds for dynamic feel

let latestPortfolioData = null;
let latestMacroData = null;

// ── Bootstrap ────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  // First load
  refreshAll();

  // Polling loop
  setInterval(refreshAll, REFRESH_MS);
});

async function refreshAll() {
  await Promise.allSettled([
    loadLatest(),
    loadPortfolio()
  ]);
}

// ── Data Fetch ───────────────────────────────────────────────────────────────

async function loadLatest() {
  try {
    const res = await fetch(`${API_BASE}/api/latest`);
    if (!res.ok) throw new Error(`/api/latest → ${res.status}`);
    const latest = await res.json();

    renderTimestamp(latest.recorded_at);
    latestMacroData = latest.macro;
    updateTicker();
    renderMacro(latest.macro);
    
    // Hide error banner if success
    const errBanner = document.getElementById("error-banner");
    if (errBanner) errBanner.style.display = "none";
  } catch (err) {
    showError("Macro data update failed: " + err.message);
  }
}

async function loadPortfolio() {
  try {
    const res = await fetch(`${API_BASE}/api/portfolio/pnl`);
    if (!res.ok) throw new Error(`/api/portfolio/pnl → ${res.status}`);
    const data = await res.json();

    latestPortfolioData = data;
    updateTicker();
    renderPortfolio(data);
  } catch (err) {
    console.error("Failed to load portfolio:", err);
    showError("Portfolio P&L update failed: " + err.message);
    const container = document.getElementById("portfolio-container");
    if (container && !latestPortfolioData) {
      container.innerHTML = `
        <div class="error-banner" style="display:block">
          ⚠ Failed to load Portfolio data: ${err.message}. Please verify the backend is running.
        </div>`;
    }
  }
}

// ── Ticker & Macro ───────────────────────────────────────────────────────────

function updateTicker() {
  const items = [];

  // 1. Add Portfolio Stats if available
  if (latestPortfolioData && latestPortfolioData.summary) {
    const s = latestPortfolioData.summary;
    items.push({
      name: "PORTFOLIO VALUE",
      val: `₹${fmtIN(s.current_value)}`,
      chg: s.total_pnl_pct,
      isPortfolio: true
    });
    items.push({
      name: "TODAY'S P&L",
      val: `${s.today_pnl >= 0 ? "+" : "-"}₹${fmtIN(Math.abs(s.today_pnl))}`,
      chg: s.today_pnl_pct,
      isPortfolio: true
    });
  } else {
    items.push({
      name: "PORTFOLIO",
      val: "Loading...",
      chg: 0,
      isPortfolio: true
    });
  }

  // 2. Add Macro Stats if available
  if (latestMacroData) {
    items.push(
      { name: "VIX",    val: fmt(latestMacroData.vix?.ltp, 2),    chg: latestMacroData.vix?.chg },
      { name: "DXY",    val: fmt(latestMacroData.dxy?.ltp, 3),    chg: latestMacroData.dxy?.chg },
      { name: "CRUDE",  val: "$" + fmt(latestMacroData.crude?.ltp, 2), chg: latestMacroData.crude?.chg },
      { name: "US30",   val: fmt(latestMacroData.us30?.ltp, 0),   chg: latestMacroData.us30?.chg },
      { name: "GOLD",   val: "$" + fmt(latestMacroData.gold?.ltp, 1), chg: latestMacroData.gold?.chg },
      { name: "SILVER", val: "$" + fmt(latestMacroData.silver?.ltp, 2), chg: latestMacroData.silver?.chg }
    );
  }

  const tickerEl = document.getElementById("ticker");
  if (!tickerEl) return;

  tickerEl.innerHTML = [...items, ...items].map(({ name, val, chg, isPortfolio }) => {
    const cv = parseFloat(chg) || 0;
    const cls = cv > 0 ? "up" : cv < 0 ? "dn" : "flat";
    const arrow = cv >= 0 ? "▲" : "▼";
    const highlightClass = isPortfolio ? "portfolio-ticker-highlight" : "";
    return `<div class="ticker-item ${highlightClass}">
      <span class="ticker-name">${name}</span>
      <span class="ticker-val">${val ?? "—"}</span>
      <span class="ticker-chg ${cls}">${arrow} ${Math.abs(cv).toFixed(2)}%</span>
    </div>`;
  }).join("");
}

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

// ── Timestamp ────────────────────────────────────────────────────────────────

function renderTimestamp(ts) {
  const el = document.getElementById("last-updated");
  if (!el || !ts) return;
  const d = new Date(ts + "Z");
  el.innerHTML = `<span class="live-dot"></span>Updated: ${d.toLocaleTimeString("en-IN", { hour12: false })} UTC`;
}

// ── Portfolio Render ─────────────────────────────────────────────────────────

function renderPortfolio(data) {
  const container = document.getElementById("portfolio-container");
  if (!container) return;

  const s = data.summary;
  const brokers = data.brokers;
  const holdings = data.holdings;
  const positions = data.positions;

  const totalPnlCls = s.total_pnl > 0 ? "up" : s.total_pnl < 0 ? "dn" : "flat";
  const todayPnlCls = s.today_pnl > 0 ? "up" : s.today_pnl < 0 ? "dn" : "flat";
  const totalArrow = s.total_pnl >= 0 ? "▲" : "▼";
  const todayArrow = s.today_pnl >= 0 ? "▲" : "▼";

  // Remember search query and broker filter state
  const prevQuery = document.getElementById("portfolio-search")?.value || "";
  const prevBroker = document.getElementById("portfolio-broker-filter")?.value || "ALL";

  container.innerHTML = `
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

  // Restore input values
  if (prevQuery) {
    const searchEl = document.getElementById("portfolio-search");
    if (searchEl) searchEl.value = prevQuery;
  }
  if (prevBroker) {
    const brokerEl = document.getElementById("portfolio-broker-filter");
    if (brokerEl) brokerEl.value = prevBroker;
  }

  // Draw chart
  renderAllocationChart(brokers);
  
  // Re-apply filters
  filterPortfolioTables();
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
  const today = new Date();
  if (d.toDateString() === today.toDateString()) {
    return d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false });
  }
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
}

// Loading state HTML helper
function loadingHTML() {
  return `<div class="loading"><div class="spinner"></div><span>Fetching data…</span></div>`;
}

function showError(msg) {
  const el = document.getElementById("error-banner");
  if (el) { el.textContent = `⚠ ${msg}`; el.style.display = "block"; }
  console.error("[AlphaEdge]", msg);
}
