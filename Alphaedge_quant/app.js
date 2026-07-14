/**
 * ALPHAEDGE QUANT - POLYMARKET QUANT BOT SIMULATOR
 * Core logic, math, rendering, and simulation loops.
 */

// Math Helper: Standard Normal Cumulative Distribution Function (normCDF)
// Used to compute the theoretical "Fair Value" of the prediction contracts
function normCDF(x) {
    const a1 =  0.254829592;
    const a2 = -0.284496736;
    const a3 =  1.421413741;
    const a4 = -1.453152027;
    const a5 =  1.061405429;
    const p  =  0.3275911;

    const sign = x < 0 ? -1 : 1;
    const absX = Math.abs(x) / Math.sqrt(2.0);

    const t = 1.0 / (1.0 + p * absX);
    const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-absX * absX);

    return 0.5 * (1.0 + sign * y);
}

// Main Application State
const state = {
    // Simulation Configs
    isRunning: true,
    speedMultiplier: 5,        // Speed up the simulation
    volatility: 45,            // Simulated standard deviation (ticks)
    tradeSizeUsd: 1000,        // USD amount per trade
    minEdgeThreshold: 3.5,     // in percentage points (e.g. 3.5%)
    
    // Market & Asset State
    btcPrice: 65420.00,
    strikePrice: 65420.00,
    priceHistory: [],          // [{ time: number, price: number }]
    roundSecondsRemaining: 300,// 5-minute round = 300 seconds
    roundId: 101,
    tickCount: 0,
    
    // Polymarket Order Book State
    // Stored in cents (0 to 100)
    yesContract: {
        midPrice: 0.50,
        bids: [], // [{ price, size }]
        asks: []  // [{ price, size }]
    },
    noContract: {
        midPrice: 0.50,
        bids: [],
        asks: []
    },
    laggedFairValueYes: 0.50,  // Simulates market maker lag

    // Quant Bot Trade State
    activePosition: null,      // { side: 'YES'|'NO', size: number, entryPrice: number, costUsd: number }
    allPositions: [],          // Array of closed positions for stats/table
    
    // Performance Statistics
    totalProfit: 0.0,
    totalVolume: 0.0,
    tradesCount: 0,
    wins: 0,
    losses: 0,
    initialBalance: 100000,    // Start with $100k simulated balance
    
    // Chart References
    canvas: null,
    ctx: null,
    
    // Simulation Timer Ref
    loopTimer: null
};

// UI Element Bindings
const UI = {
    // Stats
    statPnl: document.getElementById('stat-pnl'),
    statPnlPct: document.getElementById('stat-pnl-pct'),
    statWinrate: document.getElementById('stat-winrate'),
    statWinrateRatio: document.getElementById('stat-winrate-ratio'),
    statVolume: document.getElementById('stat-volume'),
    statTradesPerHour: document.getElementById('stat-trades-per-hour'),
    statPosition: document.getElementById('stat-position'),
    statPositionDetails: document.getElementById('stat-position-details'),
    
    // Chart info
    chartStrikePrice: document.getElementById('chart-strike-price'),
    chartCurrentPrice: document.getElementById('chart-current-price'),
    chartPriceDeviation: document.getElementById('chart-price-deviation'),
    roundCountdown: document.getElementById('round-countdown'),
    
    // Book
    yesContractMid: document.getElementById('yes-contract-mid'),
    yesBookRows: document.getElementById('yes-book-rows'),
    noContractMid: document.getElementById('no-contract-mid'),
    noBookRows: document.getElementById('no-book-rows'),
    bookLatency: document.getElementById('book-latency'),
    
    // Console & Configs
    consoleStream: document.getElementById('console-stream'),
    btnClearConsole: document.getElementById('btn-clear-console'),
    sliderSpeed: document.getElementById('slider-speed'),
    valSpeed: document.getElementById('val-speed'),
    sliderSize: document.getElementById('slider-size'),
    valSize: document.getElementById('val-size'),
    sliderEdge: document.getElementById('slider-edge'),
    valEdge: document.getElementById('val-edge'),
    sliderVolatility: document.getElementById('slider-volatility'),
    valVolatility: document.getElementById('val-volatility'),
    btnToggleEngine: document.getElementById('btn-toggle-engine'),
    btnResetSim: document.getElementById('btn-reset-sim'),
    btnExportCsv: document.getElementById('btn-export-csv'),
    tradeHistoryBody: document.getElementById('trade-history-body'),
    liveTime: document.getElementById('live-time')
};

// ==========================================================================
// 1. LOG SYSTEM
// ==========================================================================
function addLog(type, message) {
    const row = document.createElement('div');
    row.className = `console-row ${type}`;
    
    // microsecond timestamp formatting
    const now = new Date();
    const hrs = String(now.getHours()).padStart(2, '0');
    const mins = String(now.getMinutes()).padStart(2, '0');
    const secs = String(now.getSeconds()).padStart(2, '0');
    const ms = String(now.getMilliseconds()).padStart(3, '0');
    const us = String(Math.floor(Math.random() * 1000)).padStart(3, '0');
    
    row.innerHTML = `
        <span class="log-time">${hrs}:${mins}:${secs}.${ms}${us}</span>
        <span class="log-tag">${type.toUpperCase()}</span>
        <span class="log-msg">${message}</span>
    `;
    
    UI.consoleStream.appendChild(row);
    UI.consoleStream.scrollTop = UI.consoleStream.scrollHeight;
    
    // Keep console trimmed to 200 elements for performance
    if (UI.consoleStream.children.length > 200) {
        UI.consoleStream.removeChild(UI.consoleStream.firstChild);
    }
}

// ==========================================================================
// 2. MATH & PRICING MODELS
// ==========================================================================
function calculateFairValue() {
    // Standard deviation scaling factor (annualized volatility to 5-min step)
    // Adjust scaling so the probability moves dynamically but is well-behaved
    const stdDev = (state.volatility / 100.0) * Math.sqrt(state.roundSecondsRemaining);
    
    if (stdDev <= 0) {
        return state.btcPrice > state.strikePrice ? 1.0 : 0.0;
    }
    
    const diff = state.btcPrice - state.strikePrice;
    const z = diff / Math.max(0.1, stdDev);
    
    const probYes = normCDF(z);
    return Math.min(Math.max(probYes, 0.01), 0.99);
}

// ==========================================================================
// 3. POLYMARKET CLOB ORDER BOOK SIMULATOR
// ==========================================================================
function simulateOrderBook(fairValueYes) {
    // Simulates lag in the market makers' prices.
    // The book doesn't instantly snap to fair value. It drifts.
    const alpha = 0.35; // speed of order book adjustment
    state.laggedFairValueYes = (state.laggedFairValueYes * (1 - alpha)) + (fairValueYes * alpha);
    
    const laggedYes = state.laggedFairValueYes;
    const laggedNo = 1.0 - laggedYes;
    
    // Generate Bid/Ask books based on lagged values
    state.yesContract.midPrice = laggedYes;
    state.yesContract.bids = generateBookSides(laggedYes, 'bid');
    state.yesContract.asks = generateBookSides(laggedYes, 'ask');
    
    state.noContract.midPrice = laggedNo;
    state.noContract.bids = generateBookSides(laggedNo, 'bid');
    state.noContract.asks = generateBookSides(laggedNo, 'ask');
}

function generateBookSides(midPrice, side) {
    const levels = 5;
    const rows = [];
    const step = 0.01; // 1 cent intervals
    
    for (let i = 0; i < levels; i++) {
        let price;
        if (side === 'bid') {
            price = midPrice - (i * step) - 0.005;
        } else {
            price = midPrice + (i * step) + 0.005;
        }
        
        // Boundaries
        price = Math.min(Math.max(price, 0.01), 0.99);
        
        // Size gets larger deeper in the book
        const baseSize = 800 + (i * 1200);
        const noiseSize = Math.floor(Math.random() * 500) - 250;
        const size = Math.max(100, baseSize + noiseSize);
        
        rows.push({ price: price, size: size });
    }
    
    return rows;
}

// Render Order Book UI
function renderOrderBookUI(actualFairValueYes) {
    // YES Contract Mid Price
    UI.yesContractMid.textContent = `${Math.round(state.yesContract.midPrice * 100)}¢`;
    UI.noContractMid.textContent = `${Math.round(state.noContract.midPrice * 100)}¢`;
    
    // Feed Latency simulation UI
    const latency = Math.floor(10 + Math.random() * 20);
    UI.bookLatency.textContent = `FEED LATENCY: ${latency}ms`;
    
    // Render YES side
    UI.yesBookRows.innerHTML = '';
    const yesBids = state.yesContract.bids;
    const yesAsks = state.yesContract.asks;
    
    // Show top 4 levels
    for (let i = 3; i >= 0; i--) {
        const ask = yesAsks[i];
        const bid = yesBids[i];
        if (!ask || !bid) continue;
        
        const askCents = Math.round(ask.price * 100);
        const bidCents = Math.round(bid.price * 100);
        
        // Edge check: is the theoretical Fair Value higher than this ask price?
        // If actualFairValue > Ask, we buy YES cheap.
        const actualCents = actualFairValueYes * 100;
        const edgeHigh = (actualCents - askCents) >= state.minEdgeThreshold;
        
        const row = document.createElement('div');
        row.className = `book-row ask-side ${edgeHigh ? 'edge-high' : ''}`;
        row.innerHTML = `
            <span class="size">${ask.size}</span>
            <span class="ask">${askCents}¢</span>
            <span class="bid">${bidCents}¢</span>
            <span class="size">${bid.size}</span>
        `;
        UI.yesBookRows.appendChild(row);
    }
    
    // Render NO side
    UI.noBookRows.innerHTML = '';
    const noBids = state.noContract.bids;
    const noAsks = state.noContract.asks;
    
    for (let i = 3; i >= 0; i--) {
        const ask = noAsks[i];
        const bid = noBids[i];
        if (!ask || !bid) continue;
        
        const askCents = Math.round(ask.price * 100);
        const bidCents = Math.round(bid.price * 100);
        
        // Edge check: is theoretical NO Fair Value higher than this ask price?
        const actualNoCents = (1.0 - actualFairValueYes) * 100;
        const edgeHigh = (actualNoCents - askCents) >= state.minEdgeThreshold;
        
        const row = document.createElement('div');
        row.className = `book-row ask-side ${edgeHigh ? 'edge-high' : ''}`;
        row.innerHTML = `
            <span class="size">${ask.size}</span>
            <span class="ask">${askCents}¢</span>
            <span class="bid">${bidCents}¢</span>
            <span class="size">${bid.size}</span>
        `;
        UI.noBookRows.appendChild(row);
    }
}

// ==========================================================================
// 4. CHART RENDERING ENGINE (HTML5 Canvas)
// ==========================================================================
function initChart() {
    state.canvas = document.getElementById('live-btc-chart');
    state.ctx = state.canvas.getContext('2d');
    resizeChartCanvas();
    window.addEventListener('resize', resizeChartCanvas);
}

function resizeChartCanvas() {
    if (!state.canvas) return;
    const rect = state.canvas.parentElement.getBoundingClientRect();
    state.canvas.width = rect.width;
    state.canvas.height = rect.height - 60; // leave room for overlays
}

function drawChart() {
    if (!state.ctx || state.priceHistory.length === 0) return;
    
    const ctx = state.ctx;
    const w = state.canvas.width;
    const h = state.canvas.height;
    
    ctx.clearRect(0, 0, w, h);
    
    // Get min and max prices for auto-scaling
    const prices = state.priceHistory.map(p => p.price);
    prices.push(state.strikePrice); // Include strike price in scale
    let minPrice = Math.min(...prices);
    let maxPrice = Math.max(...prices);
    
    // Add padding to y-scale
    const range = maxPrice - minPrice;
    const padding = range === 0 ? 10 : range * 0.15;
    minPrice -= padding;
    maxPrice += padding;
    
    const getX = (index) => {
        // Draw across the entire chart length (300 ticks max per round)
        return (index / 300) * w;
    };
    
    const getY = (price) => {
        return h - ((price - minPrice) / (maxPrice - minPrice)) * h;
    };
    
    // Draw Grid Lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.02)';
    ctx.lineWidth = 1;
    for (let i = 1; i < 6; i++) {
        // Horizontal lines
        const y = (i / 6) * h;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
        
        // Vertical lines
        const x = (i / 6) * w;
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
    }
    
    // Draw Strike Price Line (Strike is locked at T0)
    const strikeY = getY(state.strikePrice);
    ctx.strokeStyle = 'rgba(255, 184, 0, 0.5)';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(0, strikeY);
    ctx.lineTo(w, strikeY);
    ctx.stroke();
    ctx.setLineDash([]); // Reset
    
    // Strike Price Label
    ctx.fillStyle = 'rgba(255, 184, 0, 0.85)';
    ctx.font = '9px "JetBrains Mono"';
    ctx.fillText(`STRIKE: $${state.strikePrice.toFixed(2)}`, 10, strikeY - 6);
    
    // Draw Price Path
    ctx.beginPath();
    ctx.moveTo(getX(0), getY(state.priceHistory[0].price));
    
    for (let i = 1; i < state.priceHistory.length; i++) {
        ctx.lineTo(getX(i), getY(state.priceHistory[i].price));
    }
    
    // Main price line styling
    ctx.strokeStyle = '#00f2fe';
    ctx.lineWidth = 2.5;
    ctx.shadowBlur = 8;
    ctx.shadowColor = '#00f2fe';
    ctx.stroke();
    ctx.shadowBlur = 0; // Reset shadow
    
    // Gradient fill under curve
    const gradient = ctx.createLinearGradient(0, 0, 0, h);
    gradient.addColorStop(0, 'rgba(0, 242, 254, 0.15)');
    gradient.addColorStop(1, 'rgba(0, 242, 254, 0)');
    ctx.fillStyle = gradient;
    ctx.lineTo(getX(state.priceHistory.length - 1), h);
    ctx.lineTo(getX(0), h);
    ctx.closePath();
    ctx.fill();
    
    // Draw Active trades / Entries
    state.priceHistory.forEach((pt, index) => {
        if (pt.trade) {
            const tx = getX(index);
            const ty = getY(pt.price);
            
            ctx.beginPath();
            if (pt.trade === 'YES') {
                // Green triangle pointing up
                ctx.fillStyle = '#00f29c';
                ctx.moveTo(tx, ty - 10);
                ctx.lineTo(tx - 6, ty + 2);
                ctx.lineTo(tx + 6, ty + 2);
                ctx.fill();
            } else {
                // Pink triangle pointing down
                ctx.fillStyle = '#ff3366';
                ctx.moveTo(tx, ty + 10);
                ctx.lineTo(tx - 6, ty - 2);
                ctx.lineTo(tx + 6, ty - 2);
                ctx.fill();
            }
        }
    });
    
    // Pulsing current price dot
    const lastIdx = state.priceHistory.length - 1;
    const lastPt = state.priceHistory[lastIdx];
    const lastX = getX(lastIdx);
    const lastY = getY(lastPt.price);
    
    ctx.beginPath();
    ctx.arc(lastX, lastY, 5, 0, Math.PI * 2);
    ctx.fillStyle = '#00f2fe';
    ctx.fill();
    
    ctx.beginPath();
    ctx.arc(lastX, lastY, 10 + (Math.sin(Date.now() / 150) * 3), 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(0, 242, 254, 0.3)';
    ctx.lineWidth = 1.5;
    ctx.stroke();
}

// ==========================================================================
// 5. QUANT BOT DECISION ENGINE & STRATEGY
// ==========================================================================
function runQuantStrategy(fairValueYes) {
    if (!state.isRunning) return;
    
    const timeRemaining = state.roundSecondsRemaining;
    
    // Don't open new positions in the last 15 seconds to avoid extreme tail risk
    if (timeRemaining < 15) {
        if (timeRemaining === 14) {
            addLog('info', `Entering lockout window (15s remaining). Arbitrage orders halted.`);
        }
        return;
    }
    
    // Quant pricing updates
    const fairValueYesPct = fairValueYes * 100;
    const fairValueNoPct = (1.0 - fairValueYes) * 100;
    
    // Get best asks from Simulated Order book
    const bestYesAsk = state.yesContract.asks[0];
    const bestNoAsk = state.noContract.asks[0];
    
    if (!bestYesAsk || !bestNoAsk) return;
    
    const yesAskPct = bestYesAsk.price * 100;
    const noAskPct = bestNoAsk.price * 100;
    
    // 1. Calculate Edge for YES Contract
    const edgeYes = fairValueYesPct - yesAskPct;
    
    // 2. Calculate Edge for NO Contract
    const edgeNo = fairValueNoPct - noAskPct;
    
    // Bot logic: Only holds one active direction at a time during a round
    if (!state.activePosition) {
        if (edgeYes >= state.minEdgeThreshold) {
            // Found statistical edge buying YES
            executeOrder('YES', bestYesAsk.price, edgeYes);
        } else if (edgeNo >= state.minEdgeThreshold) {
            // Found statistical edge buying NO
            executeOrder('NO', bestNoAsk.price, edgeNo);
        }
    } else {
        // If we are already in a position, we can accumulate up to risk limit
        // For simplicity, we execute 1 trade per side per round
    }
}

function executeOrder(side, askPrice, edge) {
    const tradeSize = state.tradeSizeUsd;
    const contracts = Math.floor(tradeSize / askPrice);
    
    state.activePosition = {
        side: side,
        size: contracts,
        entryPrice: askPrice,
        costUsd: contracts * askPrice
    };
    
    // Mark trade point on the chart history
    if (state.priceHistory.length > 0) {
        state.priceHistory[state.priceHistory.length - 1].trade = side;
    }
    
    // Accumulate total volume
    state.totalVolume += state.activePosition.costUsd;
    state.tradesCount++;
    
    // Log details
    addLog('edge', `Arb edge detected! P(${side}) model: ${side === 'YES' ? Math.round(calculateFairValue()*100) : Math.round((1-calculateFairValue())*100)}¢ vs Market: ${Math.round(askPrice*100)}¢ (Edge: +${edge.toFixed(1)}%)`);
    addLog('trade', `EXECUTE: BUY ${side} ${contracts.toLocaleString()} contracts @ ${Math.round(askPrice*100)}¢. Total cost: $${state.activePosition.costUsd.toFixed(2)}`);
    
    // Update Stats Display
    updateStatsUI();
}

// Settlement of Prediction Round
function settleRound() {
    const isWin = (state.btcPrice > state.strikePrice);
    const winOutcome = isWin ? 'YES' : 'NO';
    
    addLog('settle', `ROUND #${state.roundId} EXPIRED. Final BTC: $${state.btcPrice.toFixed(2)} | Strike: $${state.strikePrice.toFixed(2)} | Outcome: ${winOutcome}`);
    
    let payout = 0;
    let netPnl = 0;
    
    if (state.activePosition) {
        const pos = state.activePosition;
        if (pos.side === winOutcome) {
            // Payout is $1.00 per contract
            payout = pos.size * 1.00;
            netPnl = payout - pos.costUsd;
            state.wins++;
            state.totalProfit += netPnl;
            addLog('trade', `ROUND SETTLEMENT: WIN! Position ${pos.side} pays out $${payout.toFixed(2)} (Net PnL: +$${netPnl.toFixed(2)})`);
        } else {
            payout = 0;
            netPnl = -pos.costUsd;
            state.losses++;
            state.totalProfit += netPnl;
            addLog('error', `ROUND SETTLEMENT: LOSS. Position ${pos.side} pays out $0.00 (Net PnL: -$${Math.abs(netPnl).toFixed(2)})`);
        }
        
        // Save to historic logs array
        const settledTrade = {
            roundId: state.roundId,
            timestamp: new Date().toLocaleTimeString(),
            strikePrice: state.strikePrice,
            expiryPrice: state.btcPrice,
            side: pos.side,
            size: pos.size,
            entryPrice: pos.entryPrice,
            exitPrice: pos.side === winOutcome ? 1.00 : 0.00,
            outcome: pos.side === winOutcome ? 'WIN' : 'LOSS',
            pnl: netPnl
        };
        state.allPositions.unshift(settledTrade); // Add to front of logs
        
        // Reset active position
        state.activePosition = null;
    } else {
        // No trade taken in this round
        addLog('info', `No trade executed in Round #${state.roundId}.`);
    }
    
    // Build a fresh round
    state.roundId++;
    state.strikePrice = state.btcPrice;
    state.priceHistory = [{ time: Date.now(), price: state.btcPrice }];
    state.roundSecondsRemaining = 300;
    
    addLog('info', `ROUND #${state.roundId} STARTED. New Strike Price locked at $${state.strikePrice.toFixed(2)}`);
    
    updateStatsUI();
    renderHistoryTable();
}

// ==========================================================================
// 6. SIMULATION ENGINE TICK LOOP
// ==========================================================================
function generatePriceTick() {
    state.tickCount++;
    
    // Simulate Random Walk of BTC price with minor trending bias
    const volatilityFactor = state.volatility / 100.0;
    const trendBias = (Math.random() - 0.5) * 2.0; // Random shift
    
    // Slow trending factor to mimic momentum
    if (!state.trendVelocity) state.trendVelocity = 0;
    state.trendVelocity = (state.trendVelocity * 0.9) + (trendBias * 0.25);
    
    const priceChange = (Math.random() - 0.5) * volatilityFactor * 10 + state.trendVelocity;
    state.btcPrice += priceChange;
    
    // Store price history
    state.priceHistory.push({
        time: Date.now(),
        price: state.btcPrice
    });
    
    // Maintain maximum ticks limit
    if (state.priceHistory.length > 300) {
        state.priceHistory.shift();
    }
    
    // Decrement round remaining seconds (scaled by speed multiplier)
    // Speed multiplier scales down real clock seconds per loop step
    const stepSeconds = 1; 
    state.roundSecondsRemaining -= stepSeconds;
    
    // Console log updates for price change events
    if (state.tickCount % 6 === 0) {
        const diff = state.btcPrice - state.strikePrice;
        const diffPct = (diff / state.strikePrice) * 100;
        const sign = diff >= 0 ? '+' : '';
        addLog('signal', `BTC Price update: $${state.btcPrice.toFixed(2)} (${sign}${diffPct.toFixed(3)}% vs Strike)`);
    }
}

// Main update execution frame
function simLoopStep() {
    if (!state.isRunning) return;
    
    // 1. Generate BTC Price movement
    generatePriceTick();
    
    // 2. Perform Bayesian calculation
    const fairValueYes = calculateFairValue();
    
    // 3. Update Polymarket Order Book Order lines
    simulateOrderBook(fairValueYes);
    
    // 4. Run Quantitative trading agent logic
    runQuantStrategy(fairValueYes);
    
    // 5. Render UI changes
    renderLiveUI(fairValueYes);
    
    // 6. Expiry Resolution Check
    if (state.roundSecondsRemaining <= 0) {
        settleRound();
    }
    
    // Queue next step based on Speed Multiplier
    const baseIntervalMs = 1000;
    const nextInterval = baseIntervalMs / state.speedMultiplier;
    
    state.loopTimer = setTimeout(simLoopStep, nextInterval);
}

// ==========================================================================
// 7. UI PRESENTATION BINDINGS
// ==========================================================================
function renderLiveUI(fairValueYes) {
    // Current Price overlays
    UI.chartCurrentPrice.textContent = `$${state.btcPrice.toFixed(2)}`;
    UI.chartStrikePrice.textContent = `$${state.strikePrice.toFixed(2)}`;
    
    const diff = state.btcPrice - state.strikePrice;
    const diffPct = (diff / state.strikePrice) * 100;
    const sign = diff >= 0 ? '+' : '';
    
    UI.chartPriceDeviation.textContent = `${sign}${diffPct.toFixed(2)}%`;
    if (diff >= 0) {
        UI.chartPriceDeviation.className = 'overlay-value positive';
    } else {
        UI.chartPriceDeviation.className = 'overlay-value negative';
    }
    
    // Format Round countdown timer
    const mins = Math.floor(state.roundSecondsRemaining / 60);
    const secs = state.roundSecondsRemaining % 60;
    UI.roundCountdown.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    
    // Warn styling on expiry countdown
    if (state.roundSecondsRemaining <= 30) {
        UI.roundCountdown.className = 'countdown-timer critical';
    } else if (state.roundSecondsRemaining <= 90) {
        UI.roundCountdown.className = 'countdown-timer warning';
    } else {
        UI.roundCountdown.className = 'countdown-timer';
    }
    
    // Render order book columns
    renderOrderBookUI(fairValueYes);
    
    // Render Canvas chart
    drawChart();
}

function updateStatsUI() {
    // Net profit (PnL)
    UI.statPnl.textContent = `${state.totalProfit >= 0 ? '+' : ''}$${state.totalProfit.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    if (state.totalProfit >= 0) {
        UI.statPnl.className = 'kpi-value positive';
    } else {
        UI.statPnl.className = 'kpi-value negative';
    }
    
    const roiPct = (state.totalProfit / state.initialBalance) * 100;
    UI.statPnlPct.textContent = `${roiPct >= 0 ? '+' : ''}${roiPct.toFixed(2)}% ROI`;
    
    // Winrate
    const totalTrades = state.wins + state.losses;
    const wr = totalTrades > 0 ? (state.wins / totalTrades) * 100 : 0.0;
    UI.statWinrate.textContent = `${wr.toFixed(1)}%`;
    UI.statWinrateRatio.textContent = `${state.wins} wins / ${state.losses} losses`;
    
    // Volume & Trades per Hour
    UI.statVolume.textContent = `$${state.totalVolume.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})}`;
    
    // Calculate trades per hour based on round length (5-min speed scaled)
    const activeHrs = (state.tickCount / 300) * (5 / 60); // simulated hours
    const tph = activeHrs > 0 ? state.tradesCount / activeHrs : 0.0;
    // Cap trades per hour calculation at reasonable rate
    const displaysTph = state.tradesCount > 0 ? Math.min(60, Math.max(12, tph)) : 0.0;
    UI.statTradesPerHour.textContent = `${displaysTph.toFixed(1)} trades / hr`;
    
    // Active Position Card
    if (state.activePosition) {
        const pos = state.activePosition;
        UI.statPosition.textContent = `${pos.side} ${pos.size.toLocaleString()}`;
        UI.statPosition.className = 'kpi-value in-position';
        UI.statPositionDetails.textContent = `Entry: ${Math.round(pos.entryPrice*100)}¢ | Cost: $${pos.costUsd.toFixed(2)}`;
    } else {
        UI.statPosition.textContent = 'FLAT';
        UI.statPosition.className = 'kpi-value flat';
        UI.statPositionDetails.textContent = 'No contracts held';
    }
}

function renderHistoryTable() {
    if (state.allPositions.length === 0) {
        UI.tradeHistoryBody.innerHTML = `
            <tr class="empty-row-placeholder">
                <td colspan="10">Waiting for first round settlement...</td>
            </tr>
        `;
        return;
    }
    
    UI.tradeHistoryBody.innerHTML = '';
    
    state.allPositions.forEach(trade => {
        const row = document.createElement('tr');
        row.className = trade.outcome === 'WIN' ? 'outcome-win' : 'outcome-loss';
        
        row.innerHTML = `
            <td>#${trade.roundId}</td>
            <td>${trade.timestamp}</td>
            <td>$${trade.strikePrice.toFixed(2)}</td>
            <td>$${trade.expiryPrice.toFixed(2)}</td>
            <td><span class="badge-${trade.side.toLowerCase()}">${trade.side}</span></td>
            <td>${trade.size.toLocaleString()}</td>
            <td>${Math.round(trade.entryPrice * 100)}¢</td>
            <td>${Math.round(trade.exitPrice * 100)}¢</td>
            <td><span class="outcome-${trade.outcome.toLowerCase()}-text">${trade.outcome}</span></td>
            <td class="${trade.pnl >= 0 ? 'pnl-pos' : 'pnl-neg'}">${trade.pnl >= 0 ? '+' : ''}$${trade.pnl.toFixed(2)}</td>
        `;
        
        UI.tradeHistoryBody.appendChild(row);
    });
}

// Update Local clock indicator
function startClock() {
    setInterval(() => {
        const date = new Date();
        UI.liveTime.textContent = date.toLocaleTimeString() + ' UTC';
    }, 1000);
}

// ==========================================================================
// 8. INTERACTIVE BINDINGS & LISTENERS
// ==========================================================================
function setupEventListeners() {
    // Clear Console
    UI.btnClearConsole.addEventListener('click', () => {
        UI.consoleStream.innerHTML = '';
        addLog('info', 'Console logs cleared.');
    });
    
    // Speed Slider
    UI.sliderSpeed.addEventListener('input', (e) => {
        state.speedMultiplier = parseInt(e.target.value);
        UI.valSpeed.textContent = `${state.speedMultiplier}x`;
        addLog('info', `Simulation speed multiplier changed to ${state.speedMultiplier}x`);
    });
    
    // Size Slider
    UI.sliderSize.addEventListener('input', (e) => {
        state.tradeSizeUsd = parseInt(e.target.value);
        UI.valSize.textContent = `$${state.tradeSizeUsd.toLocaleString()}`;
    });
    
    // Edge Slider
    UI.sliderEdge.addEventListener('input', (e) => {
        state.minEdgeThreshold = parseFloat(e.target.value);
        UI.valEdge.textContent = `${state.minEdgeThreshold}%`;
    });
    
    // Volatility Slider
    UI.sliderVolatility.addEventListener('input', (e) => {
        const val = parseInt(e.target.value);
        state.volatility = val;
        let label = 'Medium';
        if (val < 25) label = 'Low';
        else if (val > 70) label = 'High';
        
        UI.valVolatility.textContent = label;
        addLog('info', `Simulated asset volatility updated to ${val} (${label})`);
    });
    
    // Pause/Resume engine button
    UI.btnToggleEngine.addEventListener('click', () => {
        state.isRunning = !state.isRunning;
        if (state.isRunning) {
            UI.btnToggleEngine.textContent = 'PAUSE ENGINE';
            UI.btnToggleEngine.classList.remove('paused');
            addLog('info', 'Quant engine simulation RESUMED.');
            // Restart step loop
            simLoopStep();
        } else {
            UI.btnToggleEngine.textContent = 'RESUME ENGINE';
            UI.btnToggleEngine.classList.add('paused');
            addLog('info', 'Quant engine simulation PAUSED.');
            clearTimeout(state.loopTimer);
        }
    });
    
    // Reset simulation parameters
    UI.btnResetSim.addEventListener('click', () => {
        const confirmReset = confirm("Are you sure you want to reset all simulation stats?");
        if (confirmReset) {
            state.totalProfit = 0.0;
            state.totalVolume = 0.0;
            state.tradesCount = 0;
            state.wins = 0;
            state.losses = 0;
            state.activePosition = null;
            state.allPositions = [];
            state.roundId = 101;
            state.roundSecondsRemaining = 300;
            state.strikePrice = state.btcPrice;
            state.priceHistory = [{ time: Date.now(), price: state.btcPrice }];
            
            addLog('info', 'Simulation stats reset to default. Restarting...');
            updateStatsUI();
            renderHistoryTable();
        }
    });
    
    // Export CSV
    UI.btnExportCsv.addEventListener('click', () => {
        if (state.allPositions.length === 0) {
            alert("No trade log entries to export.");
            return;
        }
        
        let csvContent = "data:text/csv;charset=utf-8,";
        csvContent += "ROUND_ID,TIMESTAMP,STRIKE_PRICE,EXPIRY_PRICE,SIDE,QUANTITY,ENTRY_PRICE,EXIT_PRICE,OUTCOME,NET_PNL\n";
        
        state.allPositions.forEach(trade => {
            csvContent += `${trade.roundId},${trade.timestamp},${trade.strikePrice},${trade.expiryPrice},${trade.side},${trade.size},${trade.entryPrice},${trade.exitPrice},${trade.outcome},${trade.pnl}\n`;
        });
        
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `alphaedge_predictions_round_${state.roundId}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        addLog('info', `Trade history CSV successfully compiled and downloaded.`);
    });
}

// ==========================================================================
// 9. BOOTSTRAP INITIALIZATION
// ==========================================================================
function init() {
    addLog('info', 'Initializing Alphaedge Bayesian Arbitrage Engine...');
    
    // 1. Setup local clock widgets
    startClock();
    
    // 2. Load settings listeners
    setupEventListeners();
    
    // 3. Setup canvas size & drawing contexts
    initChart();
    
    // 4. Lock initial round strike price
    state.strikePrice = state.btcPrice;
    state.priceHistory.push({ time: Date.now(), price: state.btcPrice });
    
    addLog('info', `Engine core activated. Strike locked at $${state.strikePrice.toFixed(2)}`);
    addLog('info', `Waiting for Polymarket feed validation...`);
    
    // 5. Start main simulation tick loop
    updateStatsUI();
    simLoopStep();
}

// Start everything on script load
window.onload = init;
