/* AlphaEdge - Crypto Matrix Dashboard Javascript */

'use strict';

const API_BASE = window.location.origin;
let activeSymbol = "ETH";
let accountState = null;
let pollTimer = null;

// --- Canvas Configuration & Isometric Projection ---
const canvas = document.getElementById("matrix-canvas");
const ctx = canvas.getContext("2d");

let scale = window.devicePixelRatio || 1;
let width = 0;
let height = 0;

// Camera offset for panning
let panX = 0;
let panY = 0;
let isDragging = false;
let startDragX = 0;
let startDragY = 0;

// Isometric map setup
const TILE_W = 60;
const TILE_H = 30;
const GRID_SIZE = 10;

// Entities for visual simulation
let characters = [
  { id: 1, x: 1, y: 1, targetX: 6, targetY: 1, progress: 0, speed: 0.008, color: '#f59e0b', name: 'Trainee Bot' },
  { id: 2, x: 1, y: 1, targetX: 1, targetY: 6, progress: 0, speed: 0.006, color: '#10b981', name: 'Prophet Bot' },
  { id: 3, x: 1, y: 1, targetX: 6, targetY: 6, progress: 0, speed: 0.012, color: '#3b82f6', name: 'Battler Bot' },
  { id: 4, x: 1, y: 1, targetX: 1, targetY: 1, progress: 0, speed: 0.004, color: '#a855f7', name: 'Chief Bot' }
];

let particles = [];
let animFrameId = null;

// Locations defining the isometric map zones
const LOCATIONS = {
  village: { name: "Village", cx: 1, cy: 1, r: 2, color: "#a855f7" },
  training: { name: "Training Camp", cx: 6, cy: 1, r: 2, color: "#14b8a6" },
  forest: { name: "Prediction Forest", cx: 1, cy: 6, r: 2, color: "#22c55e" },
  battlefield: { name: "Battlefield", cx: 6, cy: 6, r: 3, color: "#ef4444" }
};

// --- Bootstrap ---
document.addEventListener("DOMContentLoaded", () => {
  initLayout();
  initFormControls();
  startPolling();
  startCanvasLoop();
  
  // Drag/Pan handlers for Isometric Canvas
  canvas.addEventListener("mousedown", e => {
    isDragging = true;
    startDragX = e.clientX - panX;
    startDragY = e.clientY - panY;
  });
  
  window.addEventListener("mousemove", e => {
    if (!isDragging) return;
    panX = e.clientX - startDragX;
    panY = e.clientY - startDragY;
  });
  
  window.addEventListener("mouseup", () => {
    isDragging = false;
  });
});

function initLayout() {
  // Set dimensions
  resizeCanvas();
  window.addEventListener("resize", () => {
    resizeCanvas();
  });
  
  // Setup camera start offset
  panX = width / 2;
  panY = height / 3;
}

function resizeCanvas() {
  const wrap = canvas.parentElement;
  width = wrap.clientWidth;
  height = wrap.clientHeight;
  
  canvas.width = width * scale;
  canvas.height = height * scale;
  canvas.style.width = width + "px";
  canvas.style.height = height + "px";
  ctx.scale(scale, scale);
}

function initFormControls() {
  // Order Side buttons
  const sideButtons = document.querySelectorAll(".order-btn-side");
  sideButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      sideButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
    });
  });

  // Limit Price input toggle on Order Type change
  const typeSelect = document.getElementById("order-type");
  const priceGroup = document.getElementById("limit-price-group");
  typeSelect.addEventListener("change", () => {
    if (typeSelect.value === "LIMIT") {
      priceGroup.style.display = "block";
    } else {
      priceGroup.style.display = "none";
    }
  });
}

// --- API Polling & Rendering ---
function startPolling() {
  fetchState();
  pollTimer = setInterval(fetchState, 3000);
}

async function fetchState() {
  try {
    const res = await fetch(`${API_BASE}/api/paper/state?symbol=${activeSymbol}`);
    if (!res.ok) throw new Error("API request failed");
    const data = await res.json();
    accountState = data;
    
    // Set dynamic form limit price input if empty
    const priceInput = document.getElementById("order-price");
    if (!priceInput.value) {
      priceInput.value = data.ltp.toFixed(2);
    }
    
    renderUI(data);
  } catch (err) {
    console.error("[Polling] Error fetching state:", err);
  }
}

function renderUI(data) {
  const acc = data.account;
  const ltp = data.ltp;
  
  // 1. Update Today's PnL card
  const todayVal = document.getElementById("today-pnl-val");
  const todayChg = document.getElementById("today-pnl-chg");
  if (todayVal) {
    todayVal.className = "pnl-value " + (acc.today_pnl >= 0 ? "up" : "dn");
    todayVal.textContent = (acc.today_pnl >= 0 ? "+" : "") + formatUSDT(acc.today_pnl);
  }
  if (todayChg) {
    const totalInvested = acc.equity - acc.today_pnl;
    const todayPct = totalInvested > 0 ? (acc.today_pnl / totalInvested * 100) : 0.0;
    todayChg.textContent = `${todayPct >= 0 ? "▲" : "▼"} ${Math.abs(todayPct).toFixed(2)}% Today`;
  }

  // 2. Render This Month PnL card with Mini-Chart
  const monthVal = document.getElementById("month-pnl-val");
  if (monthVal) {
    monthVal.className = "pnl-value " + (acc.total_pnl >= 0 ? "up" : "dn");
    monthVal.textContent = (acc.total_pnl >= 0 ? "+" : "") + formatUSDT(acc.total_pnl);
  }
  renderMiniChart(data.daily_pnls);

  // 3. Render Total PnL card
  const totalVal = document.getElementById("total-pnl-val");
  const totalSub = document.getElementById("total-pnl-sub");
  if (totalVal) {
    totalVal.className = "pnl-value " + (acc.total_pnl >= 0 ? "up" : "dn");
    totalVal.textContent = (acc.total_pnl >= 0 ? "+" : "") + formatUSDT(acc.total_pnl);
  }
  if (totalSub) {
    const totalPct = 100000.0 > 0 ? (acc.total_pnl / 100000.0 * 100) : 0.0;
    totalSub.textContent = `ROI: ${totalPct.toFixed(2)}% Cumulative`;
  }

  // 4. Update Position Count Badge & Summary sub-cards
  const activePositions = data.position ? [data.position] : [];
  const openPosCount = document.getElementById("open-pos-count");
  if (openPosCount) {
    openPosCount.textContent = `${activePositions.length} POS`;
  }
  
  const longSizeEl = document.getElementById("long-size-val");
  const shortSizeEl = document.getElementById("short-size-val");
  if (longSizeEl && shortSizeEl) {
    if (data.position && data.position.side === "LONG") {
      longSizeEl.textContent = `${data.position.size} ${data.symbol}`;
      shortSizeEl.textContent = "-";
    } else if (data.position && data.position.side === "SHORT") {
      shortSizeEl.textContent = `${data.position.size} ${data.symbol}`;
      longSizeEl.textContent = "-";
    } else {
      longSizeEl.textContent = "-";
      shortSizeEl.textContent = "-";
    }
  }

  // 5. Update Position Ratios and Gauges
  updateGauge("binance-long-gauge", data.ratios.global_long_pct);
  const binanceLongVal = document.getElementById("binance-long-val");
  if (binanceLongVal) {
    binanceLongVal.textContent = `${data.ratios.global_long_pct}%`;
  }
  
  updateGauge("toptrader-long-gauge", data.ratios.top_long_pct);
  const toptraderLongVal = document.getElementById("toptrader-long-val");
  if (toptraderLongVal) {
    toptraderLongVal.textContent = `${data.ratios.top_long_pct}%`;
  }

  // 6. Update Open Positions List
  const posList = document.getElementById("open-positions-list");
  if (posList) {
    if (activePositions.length === 0) {
      posList.innerHTML = `<div style="text-align:center;padding:12px;color:var(--muted);font-size:0.7rem;">No open positions active.</div>`;
    } else {
      posList.innerHTML = activePositions.map(p => {
        const pnlCls = p.unrealized_pnl >= 0 ? "up" : "dn";
        const liqPrice = p.liq_price ? p.liq_price.toFixed(2) : "—";
        return `
          <div class="open-pos-item">
            <div class="pos-item-header">
              <div class="open-pos-sym-side">
                ${p.symbol} 
                <span class="side-badge ${p.side.toLowerCase()}">${p.side} ${p.leverage}x</span>
              </div>
              <div class="open-pos-pnl ${pnlCls}">
                ${p.unrealized_pnl >= 0 ? "+" : ""}${p.unrealized_pnl.toFixed(2)} USDT
              </div>
            </div>
            
            <div class="pos-item-grid">
              <div class="grid-cell">
                <span class="cell-lbl">Size</span>
                <span class="cell-val">${p.size} ${p.symbol}</span>
              </div>
              <div class="grid-cell">
                <span class="cell-lbl">Margin</span>
                <span class="cell-val">${p.margin.toFixed(1)} USDT</span>
              </div>
              <div class="grid-cell">
                <span class="cell-lbl">Entry Price</span>
                <span class="cell-val">${p.entry_price.toFixed(2)}</span>
              </div>
              <div class="grid-cell">
                <span class="cell-lbl">Mark Price</span>
                <span class="cell-val">${ltp.toFixed(2)}</span>
              </div>
              <div class="grid-cell liq-cell">
                <span class="cell-lbl">Liquidation Price</span>
                <span class="cell-val liq-color">${liqPrice}</span>
              </div>
            </div>
            
            <div class="pos-sltp-row">
              <div class="pos-sltp-col">
                <span class="sltp-lbl">TP Price</span>
                <input type="number" class="pos-sltp-input" id="pos-tp-${p.symbol}-${p.side}" value="${p.tp_price ? p.tp_price.toFixed(2) : ''}" placeholder="None" step="0.01">
              </div>
              <div class="pos-sltp-col">
                <span class="sltp-lbl">SL Price</span>
                <input type="number" class="pos-sltp-input" id="pos-sl-${p.symbol}-${p.side}" value="${p.sl_price ? p.sl_price.toFixed(2) : ''}" placeholder="None" step="0.01">
              </div>
              <button class="btn-save-sltp" onclick="savePositionSLTP('${p.symbol}', '${p.side}')">Save</button>
            </div>
            
            <button class="btn-close-pos-full" onclick="closePosition('${p.symbol}', '${p.side}')">CLOSE POSITION</button>
          </div>
        `;
      }).join("");
    }
  }

  // 7. Update Position execution strength bar
  const strengthFill = document.getElementById("execution-strength-fill");
  const executionVal = document.getElementById("execution-strength-val");
  let longWeight = 50;
  if (data.indicators) {
    const rsi = data.indicators.rsi;
    longWeight = Math.min(Math.max(Math.round(rsi), 10), 90);
  }
  if (strengthFill) {
    strengthFill.style.width = `${longWeight}%`;
  }
  if (executionVal) {
    executionVal.textContent = `LONG ${longWeight}% / SHORT ${100 - longWeight}%`;
  }

  // 8. Update AI Gate breakdown
  const gateList = document.getElementById("gate-breakdown-list");
  if (gateList) {
    gateList.innerHTML = data.gate_breakdown.map(g => {
      return `
        <div class="checklist-item">
          <div class="checklist-hdr">
            <span>${g.name}</span>
            <span style="font-family:var(--mono)">${g.val.toFixed(1)}%</span>
          </div>
          <div class="checklist-bar-bg">
            <div class="checklist-bar-fill ${g.color}" style="width: ${g.val}%"></div>
          </div>
        </div>
      `;
    }).join("");
  }

  // 9. Update AI Advisor
  const advisorEl = document.getElementById("advisor-text-content");
  if (advisorEl) {
    advisorEl.textContent = data.advisor;
  }
  
  const thoughtsEl = document.getElementById("agent-thoughts-log");
  if (thoughtsEl && data.agent_logs) {
    if (data.agent_logs.length === 0) {
      thoughtsEl.innerHTML = `<div style="color:var(--muted);text-align:center;padding:10px;font-size:0.7rem;">No agent thoughts recorded yet.</div>`;
    } else {
      thoughtsEl.innerHTML = data.agent_logs.map(log => {
        let color = "#38bdf8";
        if (log.includes("[CHIEF]")) color = "#a855f7";
        else if (log.includes("[TRAINEE]")) color = "#f59e0b";
        else if (log.includes("[PROPHET]")) color = "#10b981";
        else if (log.includes("[FIGHTER]")) color = "#ef4444";
        return `<div style="color:${color}">${escapeHtml(log)}</div>`;
      }).join("");
      thoughtsEl.scrollTop = thoughtsEl.scrollHeight;
    }
  }

  // 10. Update position ratio grid detail
  const pcrEl = document.getElementById("stat-overall-pcr");
  if (pcrEl) pcrEl.textContent = data.indicators.pcr.toFixed(2);
  
  const painEl = document.getElementById("stat-max-pain");
  if (painEl) painEl.textContent = data.indicators.max_pain.toFixed(0);
  
  const expiryEl = document.getElementById("stat-expiry");
  if (expiryEl) expiryEl.textContent = "PERPETUAL";

  // 11. Update bottom ticker
  const ticksWrap = document.getElementById("ticks-wrap");
  if (ticksWrap) {
    ticksWrap.innerHTML = data.trades.map(t => {
      const isUp = t.pnl >= 0;
      return `<div class="tick-square ${isUp ? 'up' : 'dn'}" title="Trade ${t.symbol} ${t.side}: ${t.pnl >= 0 ? '+' : ''}${t.pnl.toFixed(2)} USDT"></div>`;
    }).join("");
  }
}

function updateGauge(id, percent) {
  const circle = document.getElementById(id);
  if (!circle) return;
  // Circumference = 2 * PI * r = 2 * PI * 35 = ~220
  const offset = 220 - (percent / 100 * 220);
  circle.style.strokeDashoffset = offset;
}

function renderMiniChart(dailyPnLs) {
  const container = document.getElementById("mini-chart-container");
  if (!container || !dailyPnLs.length) return;
  
  const maxAbs = Math.max(...dailyPnLs.map(d => Math.abs(d.pnl))) || 1;
  container.innerHTML = dailyPnLs.map(d => {
    const isUp = d.pnl >= 0;
    const h = Math.max(Math.round((Math.abs(d.pnl) / maxAbs) * 32), 4);
    return `<div class="mini-bar ${isUp ? 'up' : 'dn'}" style="height:${h}px" title="${d.date}: ${d.pnl >= 0 ? '+' : ''}${d.pnl.toFixed(0)}"></div>`;
  }).join("");
}

// --- Submit Order ---
async function submitOrder() {
  const activeSideBtn = document.querySelector(".order-btn-side.active");
  if (!activeSideBtn) {
    alert("Please select LONG or SHORT side");
    return;
  }
  
  const side = activeSideBtn.textContent.trim();
  const type = document.getElementById("order-type").value;
  const size = parseFloat(document.getElementById("order-size").value);
  const leverage = parseFloat(document.getElementById("order-leverage").value);
  const limitPrice = parseFloat(document.getElementById("order-price").value);
  
  const tpPriceRaw = document.getElementById("order-tp").value;
  const slPriceRaw = document.getElementById("order-sl").value;
  const tpPrice = tpPriceRaw ? parseFloat(tpPriceRaw) : null;
  const slPrice = slPriceRaw ? parseFloat(slPriceRaw) : null;
  
  if (isNaN(size) || size <= 0) {
    alert("Please enter a valid order size");
    return;
  }
  
  const payload = {
    symbol: activeSymbol,
    side: side,
    type: type,
    size: size,
    leverage: leverage,
    limit_price: type === "LIMIT" ? limitPrice : null,
    tp_price: isNaN(tpPrice) || tpPrice === null ? null : tpPrice,
    sl_price: isNaN(slPrice) || slPrice === null ? null : slPrice
  };

  try {
    const res = await fetch(`${API_BASE}/api/paper/order`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    
    const data = await res.json();
    if (!res.ok) {
      alert(data.detail || "Order execution failed");
    } else {
      // Clear inputs
      document.getElementById("order-tp").value = "";
      document.getElementById("order-sl").value = "";
      
      // Trigger order feedback visual indicators
      spawnTradeFlashParticles();
      fetchState();
    }
  } catch (err) {
    console.error("[Order] Request failed:", err);
  }
}

window.savePositionSLTP = async function(symbol, side) {
  const tpEl = document.getElementById(`pos-tp-${symbol}-${side}`);
  const slEl = document.getElementById(`pos-sl-${symbol}-${side}`);
  
  const tpVal = tpEl && tpEl.value ? parseFloat(tpEl.value) : null;
  const slVal = slEl && slEl.value ? parseFloat(slEl.value) : null;
  
  try {
    const res = await fetch(`${API_BASE}/api/paper/update_sltp`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symbol: symbol,
        side: side,
        tp_price: isNaN(tpVal) || tpVal === null ? null : tpVal,
        sl_price: isNaN(slVal) || slVal === null ? null : slVal
      })
    });
    
    const data = await res.json();
    if (!res.ok) {
      alert(data.detail || "Failed to update SL/TP");
    } else {
      fetchState();
    }
  } catch (err) {
    console.error("[SLTP Update] Request failed:", err);
  }
};

async function closePosition(symbol, side) {
  try {
    const res = await fetch(`${API_BASE}/api/paper/close`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol, side })
    });
    const data = await res.json();
    if (!res.ok) {
      alert(data.detail || "Close execution failed");
    } else {
      fetchState();
    }
  } catch (err) {
    console.error("[Close] Request failed:", err);
  }
}

async function resetAccount() {
  if (!confirm("Are you sure you want to reset your paper account balance to 100,000 USDT? This will close all open positions and clear trade history.")) {
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/api/paper/reset`, { method: "POST" });
    if (res.ok) {
      fetchState();
    }
  } catch (err) {
    console.error("[Reset] Request failed:", err);
  }
}

// --- Active Symbol Tabs ---
window.switchSymbol = function(sym) {
  activeSymbol = sym.toUpperCase();
  document.querySelectorAll(".sym-tab").forEach(tab => {
    tab.classList.remove("active");
  });
  const tabEl = document.getElementById(`tab-${activeSymbol.toLowerCase()}`);
  if (tabEl) tabEl.classList.add("active");
  
  // Clear price input to let state updater fetch active price
  const priceInput = document.getElementById("order-price");
  if (priceInput) priceInput.value = "";
  
  // Update TradingView widget if present
  updateTradingViewWidget();
  
  fetchState();
};

function updateTradingViewWidget() {
  const container = document.getElementById("tv-widget-wrap");
  if (!container) return;
  
  const symLabel = activeSymbol === "BTC" ? "BINANCE:BTCUSDT" : "BINANCE:ETHUSDT";
  
  container.innerHTML = `
    <iframe src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_chart&symbol=${symLabel}&interval=5&hidesidetoolbar=1&symboledit=0&saveimage=0&toolbarbg=f1f3f6&studies=%5B%5D&theme=dark&style=1&timezone=Asia%2FKolkata&studies_overrides=%7B%7D&overrides=%7B%7D&enabled_features=%5B%5D&disabled_features=%5B%5D&locale=en" 
            style="width: 100%; height: 100%; border: none;"></iframe>
  `;
}

// --- Canvas Game-Like Isometric Battlefield Renderer ---

function isoToScreen(x, y, z = 0) {
  // Rotate grid 45 deg and stretch vertically by 0.5
  const sx = (x - y) * (TILE_W / 2) + panX;
  const sy = (x + y) * (TILE_H / 2) - z + panY;
  return { x: sx, y: sy };
}

function screenToIso(sx, sy) {
  // Inverse mapping matrices
  const dx = sx - panX;
  const dy = sy - panY;
  const x = (dx / (TILE_W / 2) + dy / (TILE_H / 2)) / 2;
  const y = (dy / (TILE_H / 2) - dx / (TILE_W / 2)) / 2;
  return { x, y };
}

function startCanvasLoop() {
  updateTradingViewWidget();
  
  // Initialize particles
  for (let i = 0; i < 15; i++) {
    particles.push({
      x: Math.random() * GRID_SIZE,
      y: Math.random() * GRID_SIZE,
      z: Math.random() * 20,
      vy: 0.1 + Math.random() * 0.3,
      size: 1 + Math.random() * 2,
      opacity: 0.2 + Math.random() * 0.5
    });
  }

  function loop() {
    updateEntities();
    drawScene();
    animFrameId = requestAnimationFrame(loop);
  }
  loop();
}

function updateEntities() {
  // Update characters paths
  characters.forEach(char => {
    if (char.progress >= 1) {
      char.x = char.targetX;
      char.y = char.targetY;
      char.progress = 0;
      
      const isAtVillage = (char.x <= 2 && char.y <= 2);
      
      if (isAtVillage) {
        // Go to their respective zones
        if (char.name === 'Trainee Bot') { char.targetX = 6; char.targetY = 1; }
        else if (char.name === 'Prophet Bot') { char.targetX = 1; char.targetY = 6; }
        else if (char.name === 'Battler Bot') { char.targetX = 6; char.targetY = 6; }
        else { 
          // Chief Bot wanders around the Village
          char.targetX = Math.max(0, Math.min(2, char.x + (Math.random() > 0.5 ? 1 : -1)));
          char.targetY = Math.max(0, Math.min(2, char.y + (Math.random() > 0.5 ? 1 : -1)));
        }
      } else {
        // Return to Village
        char.targetX = 1;
        char.targetY = 1;
      }
    } else {
      char.progress += char.speed;
    }
  });

  // Update particles
  particles.forEach(p => {
    p.z += p.vy;
    if (p.z > 50) {
      p.z = 0;
      p.x = Math.random() * GRID_SIZE;
      p.y = Math.random() * GRID_SIZE;
    }
  });
}

function drawScene() {
  ctx.clearRect(0, 0, width, height);
  
  // Draw background grid highlights
  drawMapGrids();
  
  // Draw locations outlines
  drawLocations();
  
  // Draw isometric characters & elements sorted by depth (Z-ordering)
  drawDepthSortedEntities();
  
  // Draw HUD overlays
  drawHUD();
}

function drawMapGrids() {
  ctx.strokeStyle = "rgba(30, 45, 74, 0.4)";
  ctx.lineWidth = 1;
  
  for (let x = 0; x <= GRID_SIZE; x++) {
    let p1 = isoToScreen(x, 0);
    let p2 = isoToScreen(x, GRID_SIZE);
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.stroke();
  }
  
  for (let y = 0; y <= GRID_SIZE; y++) {
    let p1 = isoToScreen(0, y);
    let p2 = isoToScreen(GRID_SIZE, y);
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.stroke();
  }
}

function drawLocations() {
  Object.values(LOCATIONS).forEach(loc => {
    // Render location zones
    ctx.fillStyle = loc.color + "12";
    ctx.strokeStyle = loc.color + "55";
    ctx.lineWidth = 1.5;
    
    // Draw polygon for the bounding circle/zone
    ctx.beginPath();
    for (let angle = 0; angle <= Math.PI*2; angle += 0.4) {
      const rx = loc.cx + Math.cos(angle) * loc.r;
      const ry = loc.cy + Math.sin(angle) * loc.r;
      const screen = isoToScreen(rx, ry);
      if (angle === 0) ctx.moveTo(screen.x, screen.y);
      else ctx.lineTo(screen.x, screen.y);
    }
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    
    // Label
    const textScreen = isoToScreen(loc.cx, loc.cy, 12);
    ctx.fillStyle = "#94a3b8";
    ctx.font = "bold 9px 'JetBrains Mono', monospace";
    ctx.textAlign = "center";
    ctx.fillText(loc.name, textScreen.x, textScreen.y);
  });
}

function drawDepthSortedEntities() {
  let list = [];
  
  // 1. Add characters
  characters.forEach(c => {
    // Linear interpolation of coordinate
    const curX = c.x + (c.targetX - c.x) * c.progress;
    const curY = c.y + (c.targetY - c.y) * c.progress;
    list.push({
      type: 'character',
      depth: curX + curY,
      x: curX,
      y: curY,
      raw: c
    });
  });
  
  // 2. Add particles
  particles.forEach(p => {
    list.push({
      type: 'particle',
      depth: p.x + p.y,
      x: p.x,
      y: p.y,
      z: p.z,
      raw: p
    });
  });

  // 3. Add battlefield ETH Boss
  const bf = LOCATIONS.battlefield;
  list.push({
    type: 'boss',
    depth: bf.cx + bf.cy,
    x: bf.cx,
    y: bf.cy,
    color: bf.color
  });

  // 4. Add Village Houses
  list.push({ type: 'house', depth: 1.5 + 0.8, x: 1.5, y: 0.8 });
  list.push({ type: 'house', depth: 0.8 + 1.5, x: 0.8, y: 1.5 });
  
  // 5. Add Forest Trees
  const trees = [
    { x: 0.8, y: 6.2 }, { x: 1.5, y: 5.5 }, { x: 2.2, y: 6.8 },
    { x: 1.0, y: 7.2 }, { x: 1.8, y: 7.8 }
  ];
  trees.forEach(t => {
    list.push({ type: 'tree', depth: t.x + t.y, x: t.x, y: t.y });
  });
  
  // 6. Add Training Target Boards
  list.push({ type: 'target', depth: 6.5 + 1.2, x: 6.5, y: 1.2 });
  list.push({ type: 'target', depth: 5.8 + 1.8, x: 5.8, y: 1.8 });

  // Sort by depth (painters algorithm)
  list.sort((a, b) => a.depth - b.depth);

  // Render sorted
  list.forEach(ent => {
    if (ent.type === 'character') {
      const screen = isoToScreen(ent.x, ent.y);
      ctx.fillStyle = ent.raw.color;
      ctx.beginPath();
      ctx.arc(screen.x, screen.y - 6, 4, 0, Math.PI * 2);
      ctx.fill();
      // Draw label
      ctx.fillStyle = "#ffffff";
      ctx.font = "7px 'JetBrains Mono', monospace";
      ctx.fillText(ent.raw.name, screen.x, screen.y - 12);
    } else if (ent.type === 'particle') {
      const screen = isoToScreen(ent.x, ent.y, ent.z);
      ctx.fillStyle = `rgba(16, 185, 129, ${ent.raw.opacity})`;
      ctx.beginPath();
      ctx.arc(screen.x, screen.y, ent.raw.size, 0, Math.PI * 2);
      ctx.fill();
    } else if (ent.type === 'boss') {
      // Draw ETH/BTC Boss monolith
      const floatOffset = Math.sin(Date.now() * 0.003) * 6;
      const screen = isoToScreen(ent.x, ent.y, 8 + floatOffset);
      
      // Combat ring glow on grid ground
      const groundScreen = isoToScreen(ent.x, ent.y);
      ctx.strokeStyle = ent.color + "88";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.ellipse(groundScreen.x, groundScreen.y, 16, 8, 0, 0, Math.PI * 2);
      ctx.stroke();
      
      // Draw diamond crystal
      ctx.fillStyle = "rgba(10, 20, 40, 0.9)";
      ctx.strokeStyle = ent.color;
      ctx.lineWidth = 2;
      
      const h = 26;
      ctx.beginPath();
      ctx.moveTo(screen.x, screen.y - h); // top
      ctx.lineTo(screen.x + 8, screen.y - h/2); // right
      ctx.lineTo(screen.x, screen.y); // bottom
      ctx.lineTo(screen.x - 8, screen.y - h/2); // left
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      
      // Floating boss name overlay
      ctx.fillStyle = "#ef4444";
      ctx.font = "bold 9px 'JetBrains Mono', monospace";
      ctx.fillText(`${activeSymbol} BOSS`, screen.x, screen.y - h - 6);
    } else if (ent.type === 'house') {
      const screen = isoToScreen(ent.x, ent.y);
      const w = 12;
      const h = 16;
      
      // Left wall
      ctx.fillStyle = "rgba(23, 37, 66, 0.95)";
      ctx.strokeStyle = "rgba(59, 130, 246, 0.4)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(screen.x, screen.y);
      ctx.lineTo(screen.x - w, screen.y - w/2);
      ctx.lineTo(screen.x - w, screen.y - w/2 - h);
      ctx.lineTo(screen.x, screen.y - h);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // Right wall
      ctx.fillStyle = "rgba(15, 23, 42, 0.95)";
      ctx.beginPath();
      ctx.moveTo(screen.x, screen.y);
      ctx.lineTo(screen.x + w, screen.y - w/2);
      ctx.lineTo(screen.x + w, screen.y - w/2 - h);
      ctx.lineTo(screen.x, screen.y - h);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // Roof left
      ctx.fillStyle = "rgba(168, 85, 247, 0.8)";
      ctx.beginPath();
      ctx.moveTo(screen.x, screen.y - h);
      ctx.lineTo(screen.x - w, screen.y - w/2 - h);
      ctx.lineTo(screen.x - w/2, screen.y - w/4 - h - 8);
      ctx.lineTo(screen.x, screen.y - h - 8);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // Roof right
      ctx.fillStyle = "rgba(139, 92, 246, 0.8)";
      ctx.beginPath();
      ctx.moveTo(screen.x, screen.y - h);
      ctx.lineTo(screen.x + w, screen.y - w/2 - h);
      ctx.lineTo(screen.x + w/2, screen.y - w/4 - h - 8);
      ctx.lineTo(screen.x, screen.y - h - 8);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    } else if (ent.type === 'tree') {
      const screen = isoToScreen(ent.x, ent.y);
      // Trunk
      ctx.fillStyle = "#78350f";
      ctx.fillRect(screen.x - 2, screen.y - 4, 4, 4);
      
      // Pine leaves layers
      ctx.fillStyle = "rgba(16, 185, 129, 0.85)";
      ctx.strokeStyle = "rgba(16, 185, 129, 0.3)";
      ctx.lineWidth = 1;
      
      const drawLayer = (cx, cy, r, layerH) => {
        ctx.beginPath();
        ctx.moveTo(cx, cy - layerH);
        ctx.lineTo(cx - r, cy);
        ctx.lineTo(cx + r, cy);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
      };
      
      drawLayer(screen.x, screen.y - 3, 8, 6);
      drawLayer(screen.x, screen.y - 6, 6, 6);
      drawLayer(screen.x, screen.y - 9, 4, 6);
    } else if (ent.type === 'target') {
      const screen = isoToScreen(ent.x, ent.y);
      // Leg stands
      ctx.strokeStyle = "#b45309";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(screen.x - 4, screen.y);
      ctx.lineTo(screen.x - 1, screen.y - 8);
      ctx.moveTo(screen.x + 4, screen.y);
      ctx.lineTo(screen.x + 1, screen.y - 8);
      ctx.stroke();
      
      // Face
      ctx.fillStyle = "#ffffff";
      ctx.strokeStyle = "#ef4444";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(screen.x, screen.y - 10, 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      
      // Red Bullseye
      ctx.fillStyle = "#ef4444";
      ctx.beginPath();
      ctx.arc(screen.x, screen.y - 10, 2.5, 0, Math.PI * 2);
      ctx.fill();
    }
  });
}

function drawHUD() {
  // Draw floating indicators
  const tvScreen = isoToScreen(2, 8, 15);
  ctx.fillStyle = "rgba(7, 13, 25, 0.8)";
  ctx.strokeStyle = "rgba(59, 130, 246, 0.4)";
  ctx.lineWidth = 1;
  
  // Box
  ctx.fillRect(tvScreen.x - 50, tvScreen.y - 10, 100, 18);
  ctx.strokeRect(tvScreen.x - 50, tvScreen.y - 10, 100, 18);
  
  ctx.fillStyle = "#3b82f6";
  ctx.font = "bold 8px 'JetBrains Mono', monospace";
  ctx.textAlign = "center";
  ctx.fillText("TrendLine 5m: BUY", tvScreen.x, tvScreen.y + 2);
}

function spawnTradeFlashParticles() {
  const bf = LOCATIONS.battlefield;
  for (let i = 0; i < 20; i++) {
    particles.push({
      x: bf.cx + (Math.random() - 0.5) * 2,
      y: bf.cy + (Math.random() - 0.5) * 2,
      z: 0,
      vy: 1.0 + Math.random() * 2.0,
      size: 2 + Math.random() * 3,
      opacity: 1.0
    });
  }
}

// --- Utility Formatters ---
function formatUSDT(value) {
  if (value == null) return "—";
  return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " USDT";
}

window.switchAdvisorTab = function(tab) {
  const briefTab = document.getElementById("adv-tab-commentary");
  const logsTab = document.getElementById("adv-tab-logs");
  const contentEl = document.getElementById("advisor-text-content");
  const logsEl = document.getElementById("agent-thoughts-log");
  
  if (tab === "commentary") {
    if (briefTab) briefTab.classList.add("active");
    if (logsTab) logsTab.classList.remove("active");
    if (contentEl) contentEl.style.display = "block";
    if (logsEl) logsEl.style.display = "none";
  } else {
    if (briefTab) briefTab.classList.remove("active");
    if (logsTab) logsTab.classList.add("active");
    if (contentEl) contentEl.style.display = "none";
    if (logsEl) logsEl.style.display = "flex";
  }
};

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
