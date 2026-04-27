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
  setInterval(loadLatest, REFRESH_MS);
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
}

function switchTab(sym) {
  SYMBOLS.forEach(s => {
    document.getElementById(`tab-${s}`)?.classList.toggle("active", s === sym);
    document.getElementById(`panel-${s}`)?.classList.toggle("active", s === sym);
  });
  // Trigger chart resize on tab show
  const inst = chartInstances[sym];
  if (inst) Object.values(inst).forEach(c => c?.resize());
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
