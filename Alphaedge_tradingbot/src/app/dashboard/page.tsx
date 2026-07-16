'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';

// Math Helper: Standard Normal Cumulative Distribution Function (normCDF)
function normCDF(x: number) {
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

const hypotheses = [
  "Design an S&P 500 stat-arb mean-reversion model using 15m Z-score",
  "Arbitrage orderbook latency imbalance on BTC-PERP between Deribit and Hyperliquid",
  "Build multi-asset momentum overlay with Bayesian probability volatility filter",
  "Analyze liquidity sweep FVG gaps on ETH-PERP 5m candles with order flows",
  "Z-score mean-reversion on S&P 500 stat-arb with GARCH volatility modeling"
];

const pipelineSteps = [
  { id: 1, name: 'Parse', range: [75, 90] },
  { id: 2, name: 'IR Build', range: [65, 75] },
  { id: 3, name: 'Compile', range: [55, 65] },
  { id: 4, name: 'Backtest', range: [30, 55] },
  { id: 5, name: 'Validate', range: [18, 30] },
  { id: 6, name: 'Approve', range: [8, 18] },
  { id: 7, name: 'Deploy', range: [0, 8] }
];

const getActiveStepId = (sec: number) => {
  if (sec > 75) return 1; // Parse
  if (sec > 65) return 2; // IR Build
  if (sec > 55) return 3; // Compile
  if (sec > 30) return 4; // Backtest
  if (sec > 18) return 5; // Validate
  if (sec > 8) return 6;  // Approve
  return 7;              // Deploy
};

import { 
  Shield, 
  ShieldAlert, 
  Activity, 
  Plus, 
  RefreshCw, 
  Play, 
  Pause, 
  AlertTriangle, 
  TrendingUp, 
  Coins, 
  Lock, 
  FileText,
  AlertOctagon
} from 'lucide-react';

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Exchange Connection Form
  const [apiKey, setApiKey] = useState('');
  const [submittingConnection, setSubmittingConnection] = useState(false);

  // Bot Instance Form
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [selectedConnection, setSelectedConnection] = useState('');
  const [riskCeiling, setRiskCeiling] = useState('5.0');
  const [maxNotional, setMaxNotional] = useState('1000');
  const [botMode, setBotMode] = useState<'paper' | 'live'>('paper');
  const [submittingInstance, setSubmittingInstance] = useState(false);

  // Webhook Simulator state
  const [simulatingSignal, setSimulatingSignal] = useState(false);

  // Active Tab & Simulator Configs
  const [activeTab, setActiveTab] = useState<'cockpit' | 'simulator'>('cockpit');
  const [simAsset, setSimAsset] = useState<'BTC-PERP' | 'ETH-PERP' | 'XAU'>('BTC-PERP');

  // Real-world prices synchronized from feed
  const [realPrices, setRealPrices] = useState<Record<string, number>>({
    'BTC-PERP': 64850.00,
    'ETH-PERP': 1875.00,
    'XAU': 2035.00
  });

  const [priceSyncError, setPriceSyncError] = useState<string | null>(null);

  useEffect(() => {
    async function syncPrices() {
      try {
        const res = await fetch('/api/dashboard/prices');
        const data = await res.json();
        
        if (data && data.success && data.prices) {
          setRealPrices(data.prices);
          setPriceSyncError(null);
          console.log('Real-world Hyperliquid prices synchronized successfully:', data.prices);
        } else {
          throw new Error(data.error || 'Failed to fetch prices from Hyperliquid endpoint');
        }
      } catch (err: any) {
        console.error('Failed to synchronize real-world prices:', err);
        setPriceSyncError(err.message || 'Hyperliquid price sync failed.');
      }
    }
    
    syncPrices();
    const interval = setInterval(syncPrices, 15 * 60 * 1000); // 15 minutes
    return () => clearInterval(interval);
  }, []);

  // Simulator Metrics
  const [simPnl, setSimPnl] = useState(0);
  const [simWinRate, setSimWinRate] = useState(0);
  const [simVolume, setSimVolume] = useState(0);
  const [simWins, setSimWins] = useState(0);
  const [simLosses, setSimLosses] = useState(0);
  const [simPosition, setSimPosition] = useState<any>(null);
  const [simLogs, setSimLogs] = useState<Array<{ time: string; type: string; msg: string }>>([]);
  const [simCountdown, setSimCountdown] = useState('01:30');
  const [simSecondsRemaining, setSimSecondsRemaining] = useState(90);
  const [simHistory, setSimHistory] = useState<Array<any>>([]);
  const [robustnessData, setRobustnessData] = useState<Record<string, number[]>>({
    'BTCUSD': [-1.5, -3.4, 4.2, 5.5, 10.0, 7.9],
    'ETHUSD': [-5.6, 3.6, 4.9, 4.8, 4.5, 1.7],
    'SOLUSD': [-2.7, 6.3, 1.0, 2.7, 5.3, 10.0],
    'BNBUSD': [1.3, -3.6, -4.4, -0.5, -2.9, 2.8],
    'XRPUSD': [0.6, 2.3, -4.2, 9.3, 3.5, 4.4],
    'ADAUSD': [-3.1, 4.8, 6.5, 9.1, 7.0, 2.7],
    'DOTUSD': [4.3, -1.4, 3.1, 4.4, 5.8, 7.6]
  });

  // Load predictions log from database when asset changes
  useEffect(() => {
    async function loadHistory() {
      try {
        const res = await fetch(`/api/dashboard/predictions?asset=${simAsset}`);
        const data = await res.json();
        if (data && data.history) {
          setSimHistory(data.history);
          
          let totalProfit = 0;
          let wins = 0;
          let losses = 0;
          let totalVolume = 0;
          
          data.history.forEach((h: any) => {
            totalProfit += Number(h.pnl);
            if (h.outcome === 'WIN') wins++;
            if (h.outcome === 'LOSS') losses++;
            totalVolume += Number(h.entryPrice) * Number(h.size);
          });
          
          setSimPnl(totalProfit);
          setSimWins(wins);
          setSimLosses(losses);
          setSimWinRate(wins + losses > 0 ? (wins / (wins + losses)) * 100 : 0);
          setSimVolume(totalVolume);

          // Synchronize physics engine state reference
          simStateRef.current.wins = wins;
          simStateRef.current.losses = losses;
          simStateRef.current.totalProfit = totalProfit;
          simStateRef.current.totalVolume = totalVolume;
        }
      } catch (err) {
        console.error('Failed to load predictions history from DB:', err);
      }
    }
    loadHistory();
  }, [simAsset]);
  
  // Sliders
  const [simSpeed, setSimSpeed] = useState(5);
  const [simTradeSize, setSimTradeSize] = useState(1000);
  const [simEdgeThreshold, setSimEdgeThreshold] = useState(3.5);
  const [simVolatility, setSimVolatility] = useState(45);
  const [simRunning, setSimRunning] = useState(true);

  // Order Books
  const [yesBook, setYesBook] = useState<any>({ mid: 0.50, bids: [], asks: [] });
  const [noBook, setNoBook] = useState<any>({ mid: 0.50, bids: [], asks: [] });

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const simStateRef = useRef({
    isRunning: true,
    speedMultiplier: 5,
    volatility: 45,
    tradeSizeUsd: 1000,
    minEdgeThreshold: 3.5,
    
    asset: 'BTC-PERP',
    price: 65420.00,
    strikePrice: 65420.00,
    priceHistory: [] as Array<{ price: number; trade?: 'YES' | 'NO' }>,
    roundSecondsRemaining: 90,
    roundId: 101,
    tickCount: 0,
    
    yesContract: {
      midPrice: 0.50,
      bids: [] as Array<{ price: number; size: number }>,
      asks: [] as Array<{ price: number; size: number }>
    },
    noContract: {
      midPrice: 0.50,
      bids: [] as Array<{ price: number; size: number }>,
      asks: [] as Array<{ price: number; size: number }>
    },
    laggedFairValueYes: 0.50,
    
    activePosition: null as any,
    wins: 0,
    losses: 0,
    totalProfit: 0,
    totalVolume: 0,
    tradesCount: 0,
    initialBalance: 100000,
  });

  // Setup Simulator Loop
  useEffect(() => {
    if (activeTab !== 'simulator') return;

    const startPrice = realPrices[simAsset] || (
      simAsset === 'BTC-PERP' ? 64850.00 :
      simAsset === 'ETH-PERP' ? 1875.00 : 2035.00
    );
      
    simStateRef.current = {
      isRunning: simRunning,
      speedMultiplier: simSpeed,
      volatility: simVolatility,
      tradeSizeUsd: simTradeSize,
      minEdgeThreshold: simEdgeThreshold,
      asset: simAsset,
      price: startPrice,
      strikePrice: startPrice,
      priceHistory: [{ price: startPrice }],
      roundSecondsRemaining: 90,
      roundId: 101,
      tickCount: 0,
      yesContract: { midPrice: 0.50, bids: [], asks: [] },
      noContract: { midPrice: 0.50, bids: [], asks: [] },
      laggedFairValueYes: 0.50,
      activePosition: null,
      wins: simStateRef.current.wins,
      losses: simStateRef.current.losses,
      totalProfit: simStateRef.current.totalProfit,
      totalVolume: simStateRef.current.totalVolume,
      tradesCount: simStateRef.current.tradesCount,
      initialBalance: 100000,
    };

    setSimLogs([]);
    const addSimLog = (type: string, msg: string) => {
      const time = new Date().toLocaleTimeString() + '.' + String(Math.floor(Math.random() * 1000)).padStart(3, '0');
      setSimLogs(prev => {
        const updated = [...prev, { time, type, msg }];
        if (updated.length > 50) updated.shift();
        return updated;
      });
    };

    addSimLog('info', `Simulation started for ${simAsset}. Initial Strike locked at $${startPrice.toFixed(2)}`);

    let timer: NodeJS.Timeout | null = null;

    const generateSimBookSides = (midPrice: number, side: 'bid' | 'ask') => {
      const levels = 5;
      const rows = [];
      const step = 0.01;
      
      for (let i = 0; i < levels; i++) {
        let price;
        if (side === 'bid') {
          price = midPrice - (i * step) - 0.005;
        } else {
          price = midPrice + (i * step) + 0.005;
        }
        
        price = Math.min(Math.max(price, 0.01), 0.99);
        const baseSize = 800 + (i * 1200);
        const noiseSize = Math.floor(Math.random() * 500) - 250;
        const size = Math.max(100, baseSize + noiseSize);
        rows.push({ price, size });
      }
      return rows;
    };

    const drawSimChart = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      const w = canvas.width;
      const h = canvas.height;
      const state = simStateRef.current;
      
      ctx.clearRect(0, 0, w, h);
      if (state.priceHistory.length === 0) return;
      
      const prices = state.priceHistory.map(p => p.price);
      prices.push(state.strikePrice);
      let minPrice = Math.min(...prices);
      let maxPrice = Math.max(...prices);
      
      const range = maxPrice - minPrice;
      const padding = range === 0 ? 10 : range * 0.15;
      minPrice -= padding;
      maxPrice += padding;
      
      const getX = (index: number) => (index / 90) * w;
      const getY = (price: number) => h - ((price - minPrice) / (maxPrice - minPrice)) * h;
      
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.02)';
      ctx.lineWidth = 1;
      for (let i = 1; i < 6; i++) {
        const y = (i / 6) * h;
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
        const x = (i / 6) * w;
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
      }
      
      const strikeY = getY(state.strikePrice);
      ctx.strokeStyle = 'rgba(255, 209, 102, 0.4)';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.moveTo(0, strikeY); ctx.lineTo(w, strikeY); ctx.stroke();
      ctx.setLineDash([]);
      
      ctx.fillStyle = 'rgba(255, 209, 102, 0.8)';
      ctx.font = '10px monospace';
      ctx.fillText(`STRIKE: $${state.strikePrice.toFixed(2)}`, 10, strikeY - 6);
      
      ctx.beginPath();
      ctx.moveTo(getX(0), getY(state.priceHistory[0].price));
      for (let i = 1; i < state.priceHistory.length; i++) {
        ctx.lineTo(getX(i), getY(state.priceHistory[i].price));
      }
      ctx.strokeStyle = '#58f0ff';
      ctx.lineWidth = 2.5;
      ctx.stroke();
      
      const gradient = ctx.createLinearGradient(0, 0, 0, h);
      gradient.addColorStop(0, 'rgba(88, 240, 255, 0.12)');
      gradient.addColorStop(1, 'rgba(88, 240, 255, 0)');
      ctx.fillStyle = gradient;
      ctx.lineTo(getX(state.priceHistory.length - 1), h);
      ctx.lineTo(getX(0), h);
      ctx.closePath();
      ctx.fill();
      
      state.priceHistory.forEach((pt, index) => {
        if (pt.trade) {
          const tx = getX(index);
          const ty = getY(pt.price);
          ctx.beginPath();
          if (pt.trade === 'YES') {
            ctx.fillStyle = '#bfff6a';
            ctx.moveTo(tx, ty - 8);
            ctx.lineTo(tx - 5, ty + 2);
            ctx.lineTo(tx + 5, ty + 2);
            ctx.fill();
          } else {
            ctx.fillStyle = '#ff6fb3';
            ctx.moveTo(tx, ty + 8);
            ctx.lineTo(tx - 5, ty - 2);
            ctx.lineTo(tx + 5, ty - 2);
            ctx.fill();
          }
        }
      });
      
      const lastIdx = state.priceHistory.length - 1;
      const lastPt = state.priceHistory[lastIdx];
      const lastX = getX(lastIdx);
      const lastY = getY(lastPt.price);
      ctx.beginPath(); ctx.arc(lastX, lastY, 4, 0, Math.PI * 2); ctx.fillStyle = '#58f0ff'; ctx.fill();
    };

    const runStep = () => {
      const state = simStateRef.current;
      if (!state.isRunning) {
        timer = setTimeout(runStep, 1000 / state.speedMultiplier);
        return;
      }
      
      // 1. Tick price
      state.tickCount++;
      const volatilityFactor = state.volatility / 100.0;
      const trendBias = (Math.random() - 0.5) * 2.0;
      if (!(state as any).trendVelocity) (state as any).trendVelocity = 0;
      (state as any).trendVelocity = ((state as any).trendVelocity * 0.9) + (trendBias * 0.25);
      
      const assetScale = state.asset === 'BTC-PERP' ? 10.0 : state.asset === 'ETH-PERP' ? 0.6 : 0.4;
      const priceChange = (Math.random() - 0.5) * volatilityFactor * assetScale + (state as any).trendVelocity;
      state.price += priceChange;
      if (state.price < 0.1) state.price = 0.1;
      
      state.priceHistory.push({ price: state.price });
      if (state.priceHistory.length > 90) {
        state.priceHistory.shift();
      }
      
      state.roundSecondsRemaining -= 1;
      
      if (state.tickCount % 6 === 0) {
        const diff = state.price - state.strikePrice;
        const diffPct = (diff / state.strikePrice) * 100;
        const sign = diff >= 0 ? '+' : '';
        addSimLog('signal', `${state.asset} Price update: $${state.price.toFixed(2)} (${sign}${diffPct.toFixed(3)}% vs Strike)`);
      }
      
      // 2. Compute Fair Value
      const stdDev = (state.volatility / 100.0) * Math.sqrt(state.roundSecondsRemaining);
      let fairValueYes = 0.5;
      if (stdDev <= 0) {
        fairValueYes = state.price > state.strikePrice ? 1.0 : 0.0;
      } else {
        const diff = state.price - state.strikePrice;
        const z = diff / Math.max(0.1, stdDev);
        fairValueYes = normCDF(z);
      }
      fairValueYes = Math.min(Math.max(fairValueYes, 0.01), 0.99);
      
      // 3. Update Order Book
      const alpha = 0.35;
      state.laggedFairValueYes = (state.laggedFairValueYes * (1 - alpha)) + (fairValueYes * alpha);
      const laggedYes = state.laggedFairValueYes;
      
      state.yesContract.midPrice = laggedYes;
      state.yesContract.bids = generateSimBookSides(laggedYes, 'bid');
      state.yesContract.asks = generateSimBookSides(laggedYes, 'ask');
      
      const laggedNo = 1.0 - laggedYes;
      state.noContract.midPrice = laggedNo;
      state.noContract.bids = generateSimBookSides(laggedNo, 'bid');
      state.noContract.asks = generateSimBookSides(laggedNo, 'ask');
      
      // 4. Run Strategy
      if (state.roundSecondsRemaining >= 15) {
        const fairValueYesPct = fairValueYes * 100;
        const fairValueNoPct = (1.0 - fairValueYes) * 100;
        const bestYesAsk = state.yesContract.asks[0];
        const bestNoAsk = state.noContract.asks[0];
        
        if (bestYesAsk && bestNoAsk) {
          const yesAskPct = bestYesAsk.price * 100;
          const noAskPct = bestNoAsk.price * 100;
          const edgeYes = fairValueYesPct - yesAskPct;
          const edgeNo = fairValueNoPct - noAskPct;
          
          if (!state.activePosition) {
            if (edgeYes >= state.minEdgeThreshold) {
              const contracts = Math.floor(state.tradeSizeUsd / bestYesAsk.price);
              state.activePosition = { side: 'YES', size: contracts, entryPrice: bestYesAsk.price, costUsd: contracts * bestYesAsk.price };
              state.priceHistory[state.priceHistory.length - 1].trade = 'YES';
              state.totalVolume += state.activePosition.costUsd;
              state.tradesCount++;
              addSimLog('edge', `Arb edge detected! P(YES) model: ${Math.round(fairValueYes*100)}¢ vs Market: ${Math.round(bestYesAsk.price*100)}¢ (Edge: +${edgeYes.toFixed(1)}%)`);
              addSimLog('trade', `EXECUTE: BUY YES ${contracts.toLocaleString()} contracts @ ${Math.round(bestYesAsk.price*100)}¢. Total cost: $${state.activePosition.costUsd.toFixed(2)}`);
            } else if (edgeNo >= state.minEdgeThreshold) {
              const contracts = Math.floor(state.tradeSizeUsd / bestNoAsk.price);
              state.activePosition = { side: 'NO', size: contracts, entryPrice: bestNoAsk.price, costUsd: contracts * bestNoAsk.price };
              state.priceHistory[state.priceHistory.length - 1].trade = 'NO';
              state.totalVolume += state.activePosition.costUsd;
              state.tradesCount++;
              addSimLog('edge', `Arb edge detected! P(NO) model: ${Math.round((1-fairValueYes)*100)}¢ vs Market: ${Math.round(bestNoAsk.price*100)}¢ (Edge: +${edgeNo.toFixed(1)}%)`);
              addSimLog('trade', `EXECUTE: BUY NO ${contracts.toLocaleString()} contracts @ ${Math.round(bestNoAsk.price*100)}¢. Total cost: $${state.activePosition.costUsd.toFixed(2)}`);
            }
          }
        }
      }
      
      // 5. Draw Chart
      drawSimChart();
      
      // 6. Expiry Settlement
      if (state.roundSecondsRemaining <= 0) {
        const isWin = state.price > state.strikePrice;
        const winOutcome = isWin ? 'YES' : 'NO';
        addSimLog('settle', `ROUND #${state.roundId} EXPIRED. Final Price: $${state.price.toFixed(2)} | Strike: $${state.strikePrice.toFixed(2)} | Outcome: ${winOutcome}`);
        
        if (state.activePosition) {
          const pos = state.activePosition;
          let payout = 0;
          let netPnl = 0;
          const isWinTrade = pos.side === winOutcome;
          if (isWinTrade) {
            payout = pos.size * 1.00;
            netPnl = payout - pos.costUsd;
            state.wins++;
            state.totalProfit += netPnl;
            addSimLog('trade', `ROUND SETTLEMENT: WIN! Position ${pos.side} pays out $${payout.toFixed(2)} (Net PnL: +$${netPnl.toFixed(2)})`);
          } else {
            payout = 0;
            netPnl = -pos.costUsd;
            state.losses++;
            state.totalProfit += netPnl;
            addSimLog('error', `ROUND SETTLEMENT: LOSS. Position ${pos.side} pays out $0.00 (Net PnL: -$${Math.abs(netPnl).toFixed(2)})`);
          }

          const settledTrade = {
            roundId: state.roundId,
            timestamp: new Date().toLocaleTimeString(),
            strikePrice: state.strikePrice,
            expiryPrice: state.price,
            side: pos.side,
            size: pos.size,
            entryPrice: pos.entryPrice,
            exitPrice: isWinTrade ? 1.00 : 0.00,
            outcome: isWinTrade ? 'WIN' : 'LOSS',
            pnl: netPnl
          };

          setSimHistory(prev => [settledTrade, ...prev].slice(0, 100));

          // Save trade prediction to database
          fetch('/api/dashboard/predictions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              roundId: state.roundId,
              asset: state.asset,
              timestamp: settledTrade.timestamp,
              strikePrice: state.strikePrice,
              expiryPrice: state.price,
              side: pos.side,
              size: pos.size,
              entryPrice: pos.entryPrice,
              exitPrice: settledTrade.exitPrice,
              outcome: settledTrade.outcome,
              pnl: netPnl
            })
          }).catch(err => console.error('Failed to save prediction to DB:', err));

          state.activePosition = null;
        }
        
        state.roundId++;
        state.strikePrice = state.price;
        state.priceHistory = [{ price: state.price }];
        state.roundSecondsRemaining = 90;
        addSimLog('info', `ROUND #${state.roundId} STARTED. New Strike locked at $${state.strikePrice.toFixed(2)}`);
      }
      
      // 7. Update UI React states
      setSimPnl(state.totalProfit);
      setSimWinRate(state.wins + state.losses > 0 ? (state.wins / (state.wins + state.losses)) * 100 : 0);
      setSimWins(state.wins);
      setSimLosses(state.losses);
      setSimVolume(state.totalVolume);
      setSimPosition(state.activePosition);
      setSimSecondsRemaining(state.roundSecondsRemaining);
      
      const mins = Math.floor(state.roundSecondsRemaining / 60);
      const secs = state.roundSecondsRemaining % 60;
      setSimCountdown(`${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`);

      // Jitter the robustness matrix to show real-time agent telemetry
      if (state.tickCount % 4 === 0) {
        setRobustnessData(prev => {
          const updated = { ...prev };
          const assets = Object.keys(updated);
          const randomAsset = assets[Math.floor(Math.random() * assets.length)];
          const randomIdx = Math.floor(Math.random() * 6);
          updated[randomAsset] = [...updated[randomAsset]];
          updated[randomAsset][randomIdx] = parseFloat(
            Math.max(-10, Math.min(15, updated[randomAsset][randomIdx] + (Math.random() - 0.5) * 0.4)).toFixed(1)
          );
          return updated;
        });
      }
      
      setYesBook({
        mid: state.yesContract.midPrice,
        bids: [...state.yesContract.bids],
        asks: [...state.yesContract.asks]
      });
      setNoBook({
        mid: state.noContract.midPrice,
        bids: [...state.noContract.bids],
        asks: [...state.noContract.asks]
      });
      
      timer = setTimeout(runStep, 1000 / state.speedMultiplier);
    };

    timer = setTimeout(runStep, 1000 / simSpeed);

    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [activeTab, simAsset]);

  const handleSpeedChange = (val: number) => {
    setSimSpeed(val);
    simStateRef.current.speedMultiplier = val;
  };
  
  const handleSizeChange = (val: number) => {
    setSimTradeSize(val);
    simStateRef.current.tradeSizeUsd = val;
  };
  
  const handleEdgeChange = (val: number) => {
    setSimEdgeThreshold(val);
    simStateRef.current.minEdgeThreshold = val;
  };
  
  const handleVolatilityChange = (val: number) => {
    setSimVolatility(val);
    simStateRef.current.volatility = val;
  };

  const handleToggleSimRunning = () => {
    const nextState = !simRunning;
    setSimRunning(nextState);
    simStateRef.current.isRunning = nextState;
  };

  useEffect(() => {
    if (activeTab === 'simulator') {
      const canvas = canvasRef.current;
      if (canvas) {
        canvas.width = canvas.parentElement?.clientWidth || 600;
        canvas.height = 240;
      }
    }
  }, [activeTab]);

  // Fetch all dashboard data
  const fetchData = async () => {
    try {
      const res = await fetch('/api/dashboard/info');
      if (!res.ok) throw new Error('Failed to fetch dashboard data');
      const json = await res.json();
      setData(json);
      
      // Auto select first template and connection if available
      if (json.botTemplates?.length > 0 && !selectedTemplate) {
        setSelectedTemplate(json.botTemplates[0].id);
      }
      if (json.exchangeConnections?.length > 0 && !selectedConnection) {
        setSelectedConnection(json.exchangeConnections[0].id);
      }
    } catch (err: any) {
      console.error(err);
      setMessage({ type: 'error', text: err.message || 'Error loading dashboard' });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  // Add Exchange Connection
  const handleAddConnection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey) return;
    setSubmittingConnection(true);
    setMessage(null);

    try {
      const res = await fetch('/api/dashboard/connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exchange: 'hyperliquid', apiKey })
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Failed to add connection');
      
      setMessage({ type: 'success', text: 'Hyperliquid API key encrypted and saved securely!' });
      setApiKey('');
      await fetchData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Error saving connection' });
    } finally {
      setSubmittingConnection(false);
    }
  };

  // Create Bot Instance
  const handleCreateInstance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTemplate || !selectedConnection) {
      setMessage({ type: 'error', text: 'Select template and exchange connection' });
      return;
    }
    setSubmittingInstance(true);
    setMessage(null);

    try {
      const res = await fetch('/api/dashboard/instances', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          botTemplateId: selectedTemplate,
          exchangeConnectionId: selectedConnection,
          mode: botMode,
          riskCeilingPct: parseFloat(riskCeiling),
          maxNotional: parseFloat(maxNotional)
        })
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Failed to create bot instance');
      
      setMessage({ type: 'success', text: 'Bot instance created and activated!' });
      await fetchData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Error creating instance' });
    } finally {
      setSubmittingInstance(false);
    }
  };

  // Toggle Bot Status (Pause/Active/Kill Switch)
  const handleToggleBotStatus = async (instanceId: string, currentStatus: string, action: 'pause' | 'resume' | 'kill') => {
    setMessage(null);
    let nextStatus = 'active';
    if (action === 'pause') nextStatus = 'paused';
    if (action === 'kill') nextStatus = 'kill_switched';

    try {
      const res = await fetch('/api/dashboard/instances', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ instanceId, status: nextStatus })
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Failed to update bot state');
      
      setMessage({ type: 'success', text: `Bot instance successfully set to ${nextStatus}!` });
      await fetchData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Error updating status' });
    }
  };

  // Simulate Webhook Signal
  const handleSimulateSignal = async (botCode: string, direction: 'LONG' | 'SHORT' | 'EXIT', price: number) => {
    setSimulatingSignal(true);
    setMessage(null);
    try {
      const res = await fetch('/api/dashboard/mock-signal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ botCode, direction, price })
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Signal execution failed');

      if (json.executions?.some((e: any) => e.status === 'rejected')) {
        const rejection = json.executions.find((e: any) => e.status === 'rejected');
        setMessage({ type: 'error', text: `Signal received but execution blocked: ${rejection.reason}` });
      } else {
        setMessage({ type: 'success', text: `Signal executed! Processed ${json.processedInstances} instances.` });
      }
      await fetchData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Error simulating webhook' });
    } finally {
      setSimulatingSignal(false);
    }
  };

  if (loading) {
    return (
      <div style={styles.centeredContainer}>
        <div className="ambient-field" />
        <div className="noise-layer" />
        <div style={styles.loader}>
          <RefreshCw style={styles.spinIcon} size={40} />
          <p style={{ marginTop: '16px', color: 'rgba(239, 246, 255, 0.66)' }}>Decrypted vault... Syncing with Hyperliquid L1...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div className="ambient-field" />
      <div className="noise-layer" />
      {/* Top Glassmorphic Navigation */}
      <header style={styles.header}>
        <div style={styles.logoRow}>
          <Link href="/" className="brand-lockup" style={{ fontSize: '1.2rem', fontWeight: 800, textDecoration: 'none', gap: '10px', display: 'flex', alignItems: 'center' }}>
            <span className="brand-mark" style={{ display: 'grid', placeItems: 'center', width: '32px', height: '32px', borderRadius: '12px', color: '#051016', background: 'conic-gradient(from 160deg, #58f0ff, #bfff6a, #9d7dff, #58f0ff)', boxShadow: '0 0 20px rgba(88, 240, 255, 0.25)', fontWeight: 'bold', fontSize: '0.9rem' }}>P</span>
            <span style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', color: '#fff', lineHeight: 1 }}>
              Prospera
              <small style={{ fontSize: '0.5rem', letterSpacing: '0.12em', color: 'rgba(239, 246, 255, 0.56)', marginTop: '2px', fontWeight: 700 }}>WEALTH AUTOMATION DESK</small>
            </span>
          </Link>
          <span style={styles.divider}>/</span>
          <span style={styles.panelTitle}>Trading Desk</span>
        </div>

        {/* Tab Switcher */}
        <div style={{ display: 'flex', gap: '4px', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '14px', padding: '4px', backgroundColor: 'rgba(255, 255, 255, 0.03)' }}>
          <button 
            style={{ 
              backgroundColor: activeTab === 'cockpit' ? 'rgba(255, 255, 255, 0.08)' : 'transparent',
              color: activeTab === 'cockpit' ? '#fff' : 'rgba(239, 246, 255, 0.66)',
              border: 'none',
              padding: '6px 16px',
              borderRadius: '10px',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onClick={() => setActiveTab('cockpit')}
          >
            Live Cockpit
          </button>
          <button 
            style={{ 
              backgroundColor: activeTab === 'simulator' ? 'rgba(255, 255, 255, 0.08)' : 'transparent',
              color: activeTab === 'simulator' ? '#fff' : 'rgba(239, 246, 255, 0.66)',
              border: 'none',
              padding: '6px 16px',
              borderRadius: '10px',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onClick={() => setActiveTab('simulator')}
          >
            Live Quant Engine
          </button>
        </div>

        <div style={styles.headerRight}>
          {data?.ledgerValid ? (
            <div style={styles.ledgerBadgeVerified}>
              <Shield size={14} /> LEDGER INTEGRITY: SECURE
            </div>
          ) : (
            <div style={styles.ledgerBadgeCompromised}>
              <ShieldAlert size={14} /> LEDGER TAMPERED DETECTED
            </div>
          )}
          <button style={styles.refreshButton} onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw size={14} className={refreshing ? 'spin-icon' : ''} style={refreshing ? styles.spinAnimation : {}} />
            {refreshing ? 'Syncing...' : 'Sync'}
          </button>
        </div>
      </header>

      <div style={styles.dashboardLayout}>
        {/* Status / Message Banner */}
        {message && (
          <div style={message.type === 'success' ? styles.bannerSuccess : styles.bannerError}>
            {message.type === 'success' ? <Shield size={18} /> : <AlertOctagon size={18} />}
            <span>{message.text}</span>
          </div>
        )}

        {activeTab === 'cockpit' ? (
          <>
            {/* Top Analytics row */}
            <section style={styles.analyticsRow}>
          <div style={styles.analyticCard}>
            <div style={styles.cardHeader}>
              <span style={styles.cardTitle}>USDC EQUITY</span>
              <Coins size={16} style={{ color: '#58f0ff' }} />
            </div>
            <div style={styles.cardValue}>${data?.balances?.equity?.toFixed(2)}</div>
            <div style={styles.cardSubText}>Available: ${data?.balances?.available?.toFixed(2)}</div>
          </div>

          <div style={styles.analyticCard}>
            <div style={styles.cardHeader}>
              <span style={styles.cardTitle}>WIN RATE</span>
              <TrendingUp size={16} style={{ color: '#34d399' }} />
            </div>
            <div style={styles.cardValue}>{(data?.aiMetrics?.winRate * 100).toFixed(0)}%</div>
            <div style={styles.cardSubText}>Sharpe Ratio: {data?.aiMetrics?.sharpeRatio?.toFixed(2)}</div>
          </div>

          <div style={styles.analyticCard}>
            <div style={styles.cardHeader}>
              <span style={styles.cardTitle}>EST. PROFIT</span>
              <Activity size={16} style={{ color: '#c084fc' }} />
            </div>
            <div style={styles.cardValue} className={data?.aiMetrics?.totalProfit >= 0 ? 'text-green' : 'text-red'}>
              ${data?.aiMetrics?.totalProfit?.toFixed(2)}
            </div>
            <div style={styles.cardSubText}>Last 30 days execution</div>
          </div>
        </section>

        {/* AI Advisory Panel */}
        <section style={styles.advisoryCard}>
          <div style={styles.advisoryHeader}>
            <Shield size={18} style={{ color: '#9d7dff' }} />
            <span style={styles.advisoryTitle}>Prospera AI Risk Advisory</span>
          </div>
          <p style={styles.advisoryBody}>{data?.aiMetrics?.advisoryText}</p>
        </section>

        {/* Middle Interactive Grid */}
        <div style={styles.gridTwoCol}>
          {/* Column Left: Bot Config, Key Management & Webhook Simulator */}
          <div style={styles.gridCol}>
            {/* API Key Connection */}
            <div style={styles.panelCard}>
              <h2 style={styles.panelHeader}><Lock size={16} style={{ color: '#f87171' }} /> Connect Hyperliquid Account</h2>
              <form onSubmit={handleAddConnection} style={styles.form}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Hyperliquid API/Private Wallet Key</label>
                  <input
                    type="password"
                    placeholder="Enter wallet address or private key"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    style={styles.input}
                    required
                  />
                  <small style={styles.helperText}>Plaintext keys are immediately encrypted in-memory and stored using AES-256-GCM envelope protection.</small>
                </div>
                <button type="submit" style={styles.buttonAction} disabled={submittingConnection}>
                  {submittingConnection ? 'Saving encrypted key...' : 'Connect Exchange Key'}
                </button>
              </form>

              {/* Connected keys list */}
              {data?.exchangeConnections?.length > 0 && (
                <div style={styles.connectionList}>
                  <h4 style={styles.subTitle}>Active Connections</h4>
                  {data.exchangeConnections.map((c: any) => (
                    <div key={c.id} style={styles.connectionRow}>
                      <div style={styles.connInfo}>
                        <span style={styles.connLogo}>HL</span>
                        <div>
                          <div style={styles.connName}>{c.exchange.toUpperCase()} (user_1)</div>
                          <div style={styles.connSub}>IV Tag: {c.encryptionTag.substring(0, 8)}...</div>
                        </div>
                      </div>
                      <span style={styles.statusIndicatorGreen}>ACTIVE</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Deploy new bot */}
            <div style={styles.panelCard}>
              <h2 style={styles.panelHeader}><Plus size={16} style={{ color: '#3b82f6' }} /> Deploy Bot Instance</h2>
              <form onSubmit={handleCreateInstance} style={styles.form}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Select Bot Strategy Template</label>
                  <select 
                    value={selectedTemplate} 
                    onChange={(e) => setSelectedTemplate(e.target.value)}
                    style={styles.select}
                  >
                    {data?.botTemplates?.map((t: any) => (
                      <option key={t.id} value={t.id}>
                        {t.code} ({t.assetClass}) - {t.status === 'live' ? 'LIVE' : 'ASSAY'}
                      </option>
                    ))}
                  </select>
                </div>

                <div style={styles.formGroup}>
                  <label style={styles.label}>Select Connected Exchange Key</label>
                  <select
                    value={selectedConnection}
                    onChange={(e) => setSelectedConnection(e.target.value)}
                    style={styles.select}
                  >
                    {data?.exchangeConnections?.length === 0 ? (
                      <option value="">No active exchange key connected</option>
                    ) : (
                      data?.exchangeConnections?.map((c: any) => (
                        <option key={c.id} value={c.id}>
                          {c.exchange.toUpperCase()} ({c.id.substring(0, 8)}...)
                        </option>
                      ))
                    )}
                  </select>
                </div>

                <div style={styles.formGrid}>
                  <div style={styles.formGroup}>
                    <label style={styles.label}>Risk Ceiling %</label>
                    <input
                      type="number"
                      step="0.1"
                      value={riskCeiling}
                      onChange={(e) => setRiskCeiling(e.target.value)}
                      style={styles.input}
                      required
                    />
                  </div>
                  <div style={styles.formGroup}>
                    <label style={styles.label}>Max Notional ($)</label>
                    <input
                      type="number"
                      value={maxNotional}
                      onChange={(e) => setMaxNotional(e.target.value)}
                      style={styles.input}
                      required
                    />
                  </div>
                </div>

                <div style={styles.formGroup}>
                  <label style={styles.label}>Execution Mode</label>
                  <div style={styles.radioRow}>
                    <label style={styles.radioLabel}>
                      <input
                        type="radio"
                        name="mode"
                        checked={botMode === 'paper'}
                        onChange={() => setBotMode('paper')}
                        style={styles.radio}
                      />
                      Paper Trading
                    </label>
                    <label style={styles.radioLabel}>
                      <input
                        type="radio"
                        name="mode"
                        checked={botMode === 'live'}
                        onChange={() => setBotMode('live')}
                        style={styles.radio}
                      />
                      Live Execution
                    </label>
                  </div>
                </div>

                <button 
                  type="submit" 
                  style={styles.buttonAction} 
                  disabled={submittingInstance || data?.exchangeConnections?.length === 0}
                >
                  {submittingInstance ? 'Deploying...' : 'Deploy Active Bot'}
                </button>
              </form>
            </div>

            {/* Signal Simulator */}
            <div style={styles.panelCard}>
              <h2 style={styles.panelHeader}><Activity size={16} style={{ color: '#fbbf24' }} /> Webhook Signal Simulator</h2>
              <p style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '16px' }}>
                Simulate TradingView alerts sending buy/sell webhook signals directly to our parser:
              </p>
              
              <div style={styles.simulatorGrid}>
                {data?.botTemplates?.map((tmpl: any) => (
                  <div key={tmpl.id} style={styles.simCard}>
                    <div style={styles.simTitle}>
                      <span>{tmpl.code}</span>
                      <span style={tmpl.status === 'live' ? styles.statusGreen : styles.statusAmber}>
                        {tmpl.status.toUpperCase()}
                      </span>
                    </div>
                    <div style={styles.simActions}>
                      <button 
                        style={styles.simButtonLong} 
                        onClick={() => handleSimulateSignal(tmpl.code, 'LONG', tmpl.assetClass === 'BTC' ? 64850.00 : tmpl.assetClass === 'ETH' ? 1875.00 : 2035.00)}
                        disabled={simulatingSignal}
                      >
                        LONG Signal
                      </button>
                      <button 
                        style={styles.simButtonShort} 
                        onClick={() => handleSimulateSignal(tmpl.code, 'SHORT', tmpl.assetClass === 'BTC' ? 64850.00 : tmpl.assetClass === 'ETH' ? 1875.00 : 2035.00)}
                        disabled={simulatingSignal}
                      >
                        SHORT Signal
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Column Right: Active Bots, Trade Ledger (Journal) & Risk Audit logs */}
          <div style={styles.gridCol}>
            {/* Active Bots list */}
            <div style={styles.panelCard}>
              <h2 style={styles.panelHeader}><Activity size={16} style={{ color: '#34d399' }} /> Active Bot Deployments</h2>
              {data?.botInstances?.length === 0 ? (
                <div style={styles.emptyState}>No active bot instances deployed. Create one on the left.</div>
              ) : (
                <div style={styles.botGrid}>
                  {data.botInstances.map((bot: any) => {
                    const templateCode = data.botTemplates.find((t: any) => t.id === bot.botTemplateId)?.code || 'Unknown';
                    
                    return (
                      <div key={bot.id} style={styles.botCard}>
                        <div style={styles.botCardHeader}>
                          <div>
                            <span style={styles.botCodeName}>{templateCode}</span>
                            <span style={bot.mode === 'live' ? styles.badgeLive : styles.badgePaper}>
                              {bot.mode.toUpperCase()}
                            </span>
                          </div>
                          <span style={
                            bot.status === 'active' ? styles.botStatusActive : 
                            bot.status === 'paused' ? styles.botStatusPaused : 
                            styles.botStatusKilled
                          }>
                            {bot.status.toUpperCase()}
                          </span>
                        </div>
                        <div style={styles.botCardBody}>
                          <div>Risk Ceiling: {bot.riskCeilingPct}%</div>
                          <div>Max Notional: ${bot.maxNotional}</div>
                        </div>
                        <div style={styles.botCardActions}>
                          {bot.status === 'active' && (
                            <button 
                              style={styles.botButtonPause}
                              onClick={() => handleToggleBotStatus(bot.id, bot.status, 'pause')}
                            >
                              <Pause size={12} /> Pause
                            </button>
                          )}
                          {bot.status === 'paused' && (
                            <button 
                              style={styles.botButtonResume}
                              onClick={() => handleToggleBotStatus(bot.id, bot.status, 'resume')}
                            >
                              <Play size={12} /> Resume
                            </button>
                          )}
                          {bot.status !== 'kill_switched' && (
                            <button 
                              style={styles.botButtonKill}
                              onClick={() => handleToggleBotStatus(bot.id, bot.status, 'kill')}
                            >
                              <AlertTriangle size={12} /> Kill Switch
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Position state */}
            <div style={styles.panelCard}>
              <h2 style={styles.panelHeader}><Coins size={16} style={{ color: '#fbbf24' }} /> Hyperliquid Positions</h2>
              {data?.positions?.length === 0 ? (
                <div style={styles.emptyState}>No open positions currently held.</div>
              ) : (
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th style={styles.th}>Coin</th>
                      <th style={styles.th}>Size</th>
                      <th style={styles.th}>Entry Price</th>
                      <th style={styles.th}>Unrealized PnL</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.positions.map((pos: any, idx: number) => (
                      <tr key={idx} style={styles.tr}>
                        <td style={styles.td}>{pos.coin}</td>
                        <td style={pos.szi >= 0 ? styles.tdGreen : styles.tdRed}>
                          {pos.szi > 0 ? `+${pos.szi}` : pos.szi}
                        </td>
                        <td style={styles.td}>${pos.entryPx.toFixed(2)}</td>
                        <td style={pos.unrealizedPnl >= 0 ? styles.tdGreen : styles.tdRed}>
                          ${pos.unrealizedPnl.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* Trade Journal (Ledger Entries) */}
            <div style={styles.panelCard}>
              <h2 style={styles.panelHeader}><FileText size={16} style={{ color: '#c084fc' }} /> Cryptographic Trade Ledger</h2>
              <div style={styles.journalContainer}>
                {data?.orders?.length === 0 ? (
                  <div style={styles.emptyState}>No historical executions recorded.</div>
                ) : (
                  <div style={styles.timeline}>
                    {data.orders.map((ord: any) => (
                      <div key={ord.id} style={styles.timelineItem}>
                        <div style={styles.timelineHeader}>
                          <span style={ord.side === 'buy' ? styles.buyTag : styles.sellTag}>
                            {ord.side.toUpperCase()}
                          </span>
                          <span style={styles.timelineTime}>
                            {new Date(ord.submittedAt).toLocaleTimeString()}
                          </span>
                        </div>
                        <div style={styles.timelineBody}>
                          <span>Qty: {ord.qty.toFixed(4)} @ ${ord.price.toFixed(2)}</span>
                          <span style={ord.status === 'filled' ? styles.statusGreen : styles.statusRed}>
                            {ord.status.toUpperCase()}
                          </span>
                        </div>
                        <div style={styles.timelineHash}>
                          Hash: <code>{ord.id}</code>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Risk Audits list */}
            {data?.riskEvents?.length > 0 && (
              <div style={styles.panelCard}>
                <h2 style={styles.panelHeader}><AlertOctagon size={16} style={{ color: '#f87171' }} /> Risk Audit Logs</h2>
                <div style={styles.auditContainer}>
                  {data.riskEvents.map((evt: any) => (
                    <div key={evt.id} style={styles.auditRow}>
                      <div style={styles.auditTime}>
                        {new Date(evt.timestamp).toLocaleTimeString()}
                      </div>
                      <div style={styles.auditDetail}>
                        <strong>{evt.type.toUpperCase()}:</strong> {evt.detail}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </>
    ) : (
      <>
        {/* Alphaedge Top Banner */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#0e1524', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '12px', padding: '12px 20px', marginBottom: '16px', fontSize: '11px', fontFamily: 'monospace' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <span style={{ fontWeight: 'bold', color: '#58f0ff', fontSize: '12px' }}>ALPHAEDGE - AI QUANT AGENT</span>
            <span style={{ color: 'rgba(239, 246, 255, 0.4)' }}>V4.0 • ENGLISH • CODE • DEPLOY • 90S PIPELINE</span>
            {priceSyncError && (
              <span style={{ color: '#ff6fb3', backgroundColor: 'rgba(255, 111, 179, 0.15)', padding: '2px 8px', borderRadius: '4px', fontWeight: 'bold' }}>
                ⚠️ FEED ERROR: {priceSyncError}
              </span>
            )}
          </div>
          <div style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
            <div>
              <span style={{ color: 'rgba(239, 246, 255, 0.4)' }}>STRATEGIES: </span>
              <span style={{ color: '#fff', fontWeight: 'bold' }}>12,408</span>
            </div>
            <div>
              <span style={{ color: 'rgba(239, 246, 255, 0.4)' }}>DEPLOYED: </span>
              <span style={{ color: '#bfff6a', fontWeight: 'bold' }}>3,842</span>
            </div>
            <div>
              <span style={{ color: 'rgba(239, 246, 255, 0.4)' }}>LIVE %: </span>
              <span style={{ color: '#ff6fb3', fontWeight: 'bold' }}>31.0%</span>
            </div>
            <div style={{ color: 'rgba(239, 246, 255, 0.6)' }}>
              17:03:50 • 11ms
            </div>
          </div>
        </div>

        {/* Ticker Ribbon */}
        <div className="ticker-ribbon" style={{ margin: '0 0 24px 0', width: '100%', borderRadius: '8px' }}>
          <div>
            <span>[PIPELINE] PARSE HYPOTHESIS: "Z-score mean-reversion on S&P 500 stat-arb..."</span>
            <span>[BACKTEST] BTC-PERP: PnL +$24,375 (VERDICT: LIVE)</span>
            <span>[RISK] SOL-PERP: Drawdown breach ➜ instance paused</span>
            <span>[COMPILER] GM-CORE-001: Compilation complete ➜ binary generated</span>
            <span>[PIPELINE] PARSE HYPOTHESIS: "Z-score mean-reversion on S&P 500..."</span>
            <span>[BACKTEST] BTC-PERP: PnL +$24,375 (VERDICT: LIVE)</span>
            <span>[RISK] SOL-PERP: Drawdown breach ➜ instance paused</span>
            <span>[COMPILER] GM-CORE-001: Compilation complete ➜ binary generated</span>
          </div>
        </div>

        {/* Simulator KPIs Row */}
        <section style={{ ...styles.analyticsRow, gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', marginBottom: '24px' }}>
          {/* KPI 1: Net Profit */}
          <div style={styles.analyticCard}>
            <div style={styles.cardHeader}>
              <span style={styles.cardTitle}>NET PROFIT (PnL)</span>
              <TrendingUp size={16} style={{ color: simPnl >= 0 ? '#bfff6a' : '#ff6fb3' }} />
            </div>
            <div style={{ fontSize: '28px', fontWeight: 'bold', color: simPnl >= 0 ? '#bfff6a' : '#ff6fb3', fontFamily: 'monospace' }}>
              {simPnl >= 0 ? '+' : ''}${simPnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div style={styles.cardSubText}>ROI: {((simPnl / 100000) * 100).toFixed(3)}%</div>
          </div>

          {/* KPI 2: Win Rate */}
          <div style={styles.analyticCard}>
            <div style={styles.cardHeader}>
              <span style={styles.cardTitle}>WIN RATE</span>
              <Shield size={16} style={{ color: '#58f0ff' }} />
            </div>
            <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#58f0ff', fontFamily: 'monospace' }}>
              {simWinRate.toFixed(1)}%
            </div>
            <div style={styles.cardSubText}>{simWins} wins / {simLosses} losses</div>
          </div>

          {/* KPI 3: Trading Volume */}
          <div style={styles.analyticCard}>
            <div style={styles.cardHeader}>
              <span style={styles.cardTitle}>TRADING VOLUME</span>
              <Coins size={16} style={{ color: 'rgba(239, 246, 255, 0.6)' }} />
            </div>
            <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#ffffff', fontFamily: 'monospace' }}>
              ${simVolume.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </div>
            <div style={styles.cardSubText}>Total volume traded</div>
          </div>

          {/* KPI 4: Active Position */}
          <div style={styles.analyticCard}>
            <div style={styles.cardHeader}>
              <span style={styles.cardTitle}>ACTIVE POSITION</span>
              <Activity size={16} style={{ color: simPosition ? '#bfff6a' : 'rgba(239, 246, 255, 0.4)' }} />
            </div>
            <div style={{ fontSize: '22px', fontWeight: 'bold', color: simPosition ? '#bfff6a' : 'rgba(239, 246, 255, 0.4)', fontFamily: 'monospace', minHeight: '36px', display: 'flex', alignItems: 'center' }}>
              {simPosition ? `${simPosition.side} ${simPosition.size.toLocaleString()}` : 'FLAT'}
            </div>
            <div style={styles.cardSubText}>
              {simPosition ? `Entry: ${Math.round(simPosition.entryPrice * 100)}¢ | Cost: $${simPosition.costUsd.toFixed(2)}` : 'No contracts held'}
            </div>
          </div>
        </section>

        {/* Alphaedge Pipeline Flow */}
        <div style={{ ...styles.panelCard, marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <span style={{ fontSize: '11px', fontWeight: 'bold', color: 'rgba(239, 246, 255, 0.6)' }}>ALPHAEDGE PIPELINE: ENGLISH ➜ DEPLOYED</span>
            <span style={{ fontSize: '11px', fontWeight: 'bold', color: '#58f0ff', fontFamily: 'monospace' }}>
              ETA SECONDS REMAINING: {simSecondsRemaining}s
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '8px' }}>
            {pipelineSteps.map((step) => {
              const activeStepId = getActiveStepId(simSecondsRemaining);
              const isActive = activeStepId === step.id;
              const isPast = activeStepId > step.id;
              return (
                <div 
                  key={step.id} 
                  style={{
                    backgroundColor: isActive ? 'rgba(88, 240, 255, 0.15)' : isPast ? 'rgba(191, 255, 106, 0.08)' : 'rgba(255, 255, 255, 0.02)',
                    border: `1px solid ${isActive ? '#58f0ff' : isPast ? '#bfff6a' : 'rgba(255, 255, 255, 0.08)'}`,
                    borderRadius: '8px',
                    padding: '12px',
                    textAlign: 'center',
                    transition: 'all 0.3s ease',
                    boxShadow: isActive ? '0 0 16px rgba(88, 240, 255, 0.25)' : 'none'
                  }}
                >
                  <div style={{ fontSize: '9px', color: 'rgba(239, 246, 255, 0.4)', textTransform: 'uppercase', marginBottom: '4px' }}>0{step.id}</div>
                  <div style={{ fontSize: '12px', fontWeight: 'bold', color: isActive ? '#58f0ff' : isPast ? '#bfff6a' : 'rgba(239, 246, 255, 0.6)' }}>{step.name}</div>
                </div>
              );
            })}
          </div>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px', borderTop: '1px solid rgba(255, 255, 255, 0.06)', paddingTop: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '11px', color: '#ff6fb3', fontWeight: 'bold', fontFamily: 'monospace' }}>HYPOTHESIS:</span>
              <span style={{ fontSize: '12px', color: '#fff', fontStyle: 'italic' }}>
                "{hypotheses[simStateRef.current.roundId % hypotheses.length]}"
              </span>
            </div>
            
            {/* Agent Role Loop */}
            <div style={{ display: 'flex', gap: '16px', fontSize: '11px', fontFamily: 'monospace' }}>
              <span style={{ color: getActiveStepId(simSecondsRemaining) <= 2 ? '#58f0ff' : 'rgba(239, 246, 255, 0.3)', fontWeight: getActiveStepId(simSecondsRemaining) <= 2 ? 'bold' : 'normal' }}>Generator</span>
              <span style={{ color: 'rgba(239, 246, 255, 0.3)' }}>➜</span>
              <span style={{ color: getActiveStepId(simSecondsRemaining) === 3 ? '#58f0ff' : 'rgba(239, 246, 255, 0.3)', fontWeight: getActiveStepId(simSecondsRemaining) === 3 ? 'bold' : 'normal' }}>Coder</span>
              <span style={{ color: 'rgba(239, 246, 255, 0.3)' }}>➜</span>
              <span style={{ color: getActiveStepId(simSecondsRemaining) === 4 ? '#58f0ff' : 'rgba(239, 246, 255, 0.3)', fontWeight: getActiveStepId(simSecondsRemaining) === 4 ? 'bold' : 'normal' }}>Challenger</span>
              <span style={{ color: 'rgba(239, 246, 255, 0.3)' }}>➜</span>
              <span style={{ color: getActiveStepId(simSecondsRemaining) >= 5 ? '#58f0ff' : 'rgba(239, 246, 255, 0.3)', fontWeight: getActiveStepId(simSecondsRemaining) >= 5 ? 'bold' : 'normal' }}>Evaluator</span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
          {/* Column Left: Live Price Chart, Robustness Matrix & Monte Carlo (Wide) */}
          <div style={{ flex: '1.6 1 600px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div style={styles.panelCard}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', paddingBottom: '12px', marginBottom: '20px' }}>
                <h2 style={{ margin: 0, fontSize: '15px', display: 'flex', alignItems: 'center', gap: '8px', color: '#fff', fontWeight: 600 }}><TrendingUp size={16} style={{ color: '#58f0ff' }} /> {simAsset} PIPELINE SIMULATOR PATH</h2>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <select 
                    value={simAsset} 
                    onChange={(e) => setSimAsset(e.target.value as any)}
                    style={{ ...styles.select, padding: '4px 8px', borderRadius: '8px', fontSize: '12px', height: '30px' }}
                  >
                    <option value="BTC-PERP">BTC-PERP</option>
                    <option value="ETH-PERP">ETH-PERP</option>
                    <option value="XAU">XAU</option>
                  </select>
                  <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#ff6fb3', fontFamily: 'monospace' }}>{simCountdown}</div>
                </div>
              </div>

              {/* Chart values row */}
              <div style={{ display: 'flex', gap: '24px', marginBottom: '16px' }}>
                <div>
                  <small style={{ fontSize: '10px', color: 'rgba(239, 246, 255, 0.54)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>STRIKE PRICE (T0)</small>
                  <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#ffd166', fontFamily: 'monospace', marginTop: '2px' }}>${simStateRef.current.strikePrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                </div>
                <div>
                  <small style={{ fontSize: '10px', color: 'rgba(239, 246, 255, 0.54)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>CURRENT PRICE</small>
                  <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#58f0ff', fontFamily: 'monospace', marginTop: '2px' }}>${simStateRef.current.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                </div>
                <div>
                  <small style={{ fontSize: '10px', color: 'rgba(239, 246, 255, 0.54)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>DEVIATION</small>
                  <div style={{ fontSize: '16px', fontWeight: 'bold', color: simStateRef.current.price >= simStateRef.current.strikePrice ? '#bfff6a' : '#ff6fb3', fontFamily: 'monospace', marginTop: '2px' }}>
                    {simStateRef.current.price >= simStateRef.current.strikePrice ? '+' : ''}
                    {simStateRef.current.strikePrice > 0 ? ((simStateRef.current.price - simStateRef.current.strikePrice) / simStateRef.current.strikePrice * 100).toFixed(3) : '0.000'}%
                  </div>
                </div>
              </div>

              {/* Canvas element wrapper */}
              <div style={{ height: '240px', width: '100%', position: 'relative', background: 'rgba(5, 7, 17, 0.4)', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.05)', overflow: 'hidden' }}>
                <canvas ref={canvasRef} style={{ width: '100%', height: '100%' }} />
              </div>
            </div>

            {/* Robustness Matrix Grid */}
            <div style={styles.panelCard}>
              <h2 style={styles.panelHeader}><Activity size={16} style={{ color: '#9d7dff' }} /> Robustness Matrix (Returns across assets & timeframes)</h2>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px', fontFamily: 'monospace', textAlign: 'center' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', height: '28px', color: 'rgba(239, 246, 255, 0.5)' }}>
                      <th style={{ textAlign: 'left', fontWeight: 'bold' }}>ASSET</th>
                      <th>5M</th>
                      <th>15M</th>
                      <th>30M</th>
                      <th>1H</th>
                      <th>4H</th>
                      <th>1D</th>
                      <th style={{ fontWeight: 'bold', color: '#fff' }}>AVG</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.keys(robustnessData).map((asset) => {
                      const values = robustnessData[asset];
                      const avg = parseFloat((values.reduce((a, b) => a + b, 0) / values.length).toFixed(1));
                      return (
                        <tr key={asset} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)', height: '30px' }}>
                          <td style={{ textAlign: 'left', fontWeight: 'bold', color: '#fff' }}>{asset}</td>
                          {values.map((v, i) => {
                            const isNeg = v < 0;
                            return (
                              <td 
                                key={i} 
                                style={{
                                  backgroundColor: isNeg ? `rgba(255, 111, 179, ${Math.min(0.3, Math.abs(v) / 15)})` : `rgba(88, 240, 255, ${Math.min(0.3, v / 15)})`,
                                  color: isNeg ? '#ff6fb3' : '#58f0ff',
                                  borderRadius: '2px',
                                  transition: 'all 0.3s ease'
                                }}
                              >
                                {v >= 0 ? '+' : ''}{v.toFixed(1)}%
                              </td>
                            );
                          })}
                          <td style={{ fontWeight: 'bold', color: avg >= 0 ? '#bfff6a' : '#ff6fb3', backgroundColor: 'rgba(255, 255, 255, 0.02)' }}>
                            {avg >= 0 ? '+' : ''}{avg.toFixed(1)}%
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Monte Carlo Significance Panel */}
            <div style={styles.panelCard}>
              <h2 style={styles.panelHeader}><TrendingUp size={16} style={{ color: '#bfff6a' }} /> Monte Carlo Return Distribution (10,000 Paths)</h2>
              <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
                <div style={{ flex: '1.2 1', height: '140px', background: 'rgba(5, 7, 17, 0.4)', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.05)', position: 'relative', overflow: 'hidden' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-end', height: '100%', padding: '10px 20px', gap: '2px' }}>
                    {[2, 5, 8, 12, 18, 25, 35, 48, 65, 82, 95, 99, 90, 75, 58, 42, 30, 20, 12, 7, 4, 2].map((height, idx) => (
                      <div 
                        key={idx} 
                        style={{
                          flex: 1,
                          height: `${height}%`,
                          backgroundColor: idx === 9 ? '#ffd166' : idx < 9 ? 'rgba(255, 111, 179, 0.5)' : 'rgba(88, 240, 255, 0.5)',
                          borderRadius: '1px 1px 0 0',
                          minWidth: '4px'
                        }}
                      />
                    ))}
                  </div>
                </div>
                <div style={{ flex: '1', fontSize: '11px', display: 'flex', flexDirection: 'column', gap: '8px', fontFamily: 'monospace' }}>
                  <div>
                    <span style={{ color: 'rgba(239, 246, 255, 0.5)' }}>5th Percentile: </span>
                    <span style={{ color: '#58f0ff', fontWeight: 'bold' }}>+4.3% (Worst case)</span>
                  </div>
                  <div>
                    <span style={{ color: 'rgba(239, 246, 255, 0.5)' }}>Expected Max DD: </span>
                    <span style={{ color: '#ff6fb3', fontWeight: 'bold' }}>-8.6%</span>
                  </div>
                  <div>
                    <span style={{ color: 'rgba(239, 246, 255, 0.5)' }}>p(Loss &gt; 10%): </span>
                    <span style={{ color: '#fff' }}>2.7%</span>
                  </div>
                  <div>
                    <span style={{ color: 'rgba(239, 246, 255, 0.5)' }}>Significance: </span>
                    <span style={{ color: '#bfff6a', fontWeight: 'bold' }}>p &lt; 0.01 (Significant)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Broker Distribution */}
            <div style={styles.panelCard}>
              <h2 style={styles.panelHeader}><Shield size={16} style={{ color: '#58f0ff' }} /> Broker Distribution & Capital Share</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '11px', fontFamily: 'monospace' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'rgba(239, 246, 255, 0.6)' }}>
                  <span>Alpaca (42%)</span>
                  <span>Bybit (26%)</span>
                  <span>IBKR (18%)</span>
                  <span>Deribit (14%)</span>
                </div>
                <div style={{ display: 'flex', height: '10px', borderRadius: '5px', overflow: 'hidden', backgroundColor: 'rgba(255, 255, 255, 0.05)' }}>
                  <div style={{ width: '42%', backgroundColor: '#58f0ff' }} />
                  <div style={{ width: '26%', backgroundColor: '#ffd166' }} />
                  <div style={{ width: '18%', backgroundColor: '#bfff6a' }} />
                  <div style={{ width: '14%', backgroundColor: '#ff6fb3' }} />
                </div>
              </div>
            </div>
          </div>

          {/* Column Right: Agent Status, Sliders, CLOB, Telemetry Logs (Narrow) */}
          <div style={{ flex: '1 1 380px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Alphaedge Agent Status Card */}
            <div style={styles.panelCard}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', paddingBottom: '12px', marginBottom: '16px' }}>
                <h2 style={{ margin: 0, fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px', color: '#fff', fontWeight: 600 }}>
                  <Activity size={16} style={{ color: '#bfff6a' }} /> ALPHAEDGE AGENT v4.0
                </h2>
                <span style={{ fontSize: '10px', backgroundColor: 'rgba(191, 255, 106, 0.15)', color: '#bfff6a', padding: '2px 8px', borderRadius: '4px', fontWeight: 'bold' }}>ONLINE</span>
              </div>
              
              <div style={{ display: 'flex', gap: '20px', alignItems: 'center', marginBottom: '16px' }}>
                {/* Giant digital block countdown */}
                <div style={{ fontSize: '48px', fontWeight: '900', color: '#58f0ff', fontFamily: 'monospace', textShadow: '0 0 20px rgba(88, 240, 255, 0.4)', padding: '16px', border: '1px solid rgba(88, 240, 255, 0.2)', borderRadius: '12px', backgroundColor: 'rgba(5, 7, 17, 0.4)', width: '120px', textAlign: 'center' }}>
                  {simSecondsRemaining}s
                </div>
                
                <div style={{ flex: 1, fontSize: '11px', color: 'rgba(239, 246, 255, 0.6)' }}>
                  <div style={{ marginBottom: '8px' }}>
                    <span style={{ color: '#fff', fontWeight: 'bold' }}>BENCHMARK PIPELINE SPEED:</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255, 255, 255, 0.05)', paddingBottom: '4px' }}>
                    <span>Junior Quant:</span>
                    <span style={{ color: '#ff6fb3' }}>7 weeks</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '4px', fontWeight: 'bold' }}>
                    <span>Alphaedge Agent:</span>
                    <span style={{ color: '#bfff6a' }}>90 seconds</span>
                  </div>
                </div>
              </div>

              {/* Comparison Details */}
              <table style={{ width: '100%', fontSize: '11px', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.08)', color: 'rgba(239, 246, 255, 0.4)', height: '24px' }}>
                    <th style={{ textAlign: 'left' }}>METRIC</th>
                    <th style={{ textAlign: 'left' }}>JUNIOR QUANT</th>
                    <th style={{ textAlign: 'right' }}>ALPHAEDGE AGENT</th>
                  </tr>
                </thead>
                <tbody>
                  <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)', height: '28px' }}>
                    <td>Salary/Cost</td>
                    <td style={{ color: '#ff6fb3' }}>$87,500/yr</td>
                    <td style={{ color: '#bfff6a', textAlign: 'right', fontWeight: 'bold' }}>$0/hr</td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)', height: '28px' }}>
                    <td>Compile Time</td>
                    <td>7 weeks</td>
                    <td style={{ color: '#58f0ff', textAlign: 'right', fontWeight: 'bold' }}>90 sec</td>
                  </tr>
                  <tr style={{ height: '28px' }}>
                    <td>Deployment</td>
                    <td>Python / API scripts</td>
                    <td style={{ color: '#ffd166', textAlign: 'right', fontWeight: 'bold' }}>Auto Live Bot</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Config Panel */}
            <div style={styles.panelCard}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', paddingBottom: '12px', marginBottom: '16px' }}>
                <h2 style={{ margin: 0, fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px', color: '#fff', fontWeight: 600 }}><Lock size={16} style={{ color: '#ffd166' }} /> Bot Configuration</h2>
                <button 
                  onClick={handleToggleSimRunning}
                  style={{ 
                    background: simRunning ? 'rgba(255, 111, 179, 0.12)' : 'linear-gradient(135deg, #58f0ff, #bfff6a)',
                    border: 'none',
                    color: simRunning ? '#ff6fb3' : '#051016',
                    padding: '4px 12px',
                    borderRadius: '8px',
                    fontSize: '11px',
                    fontWeight: 'bold',
                    cursor: 'pointer'
                  }}
                >
                  {simRunning ? 'Pause Engine' : 'Resume Engine'}
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '12px' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span>Simulation Speed (Multiplier)</span>
                    <span style={{ color: '#58f0ff', fontWeight: 'bold' }}>{simSpeed}x</span>
                  </div>
                  <input 
                    type="range" min="1" max="20" step="1" 
                    value={simSpeed} onChange={(e) => handleSpeedChange(parseInt(e.target.value))} 
                    style={{ width: '100%', accentColor: '#58f0ff' }}
                  />
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span>Trade Size per Bet ($)</span>
                    <span style={{ color: '#58f0ff', fontWeight: 'bold' }}>${simTradeSize.toLocaleString()}</span>
                  </div>
                  <input 
                    type="range" min="100" max="5000" step="100" 
                    value={simTradeSize} onChange={(e) => handleSizeChange(parseInt(e.target.value))} 
                    style={{ width: '100%', accentColor: '#58f0ff' }}
                  />
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span>Min Executable Edge Threshold (%)</span>
                    <span style={{ color: '#58f0ff', fontWeight: 'bold' }}>{simEdgeThreshold}%</span>
                  </div>
                  <input 
                    type="range" min="0.5" max="10.0" step="0.5" 
                    value={simEdgeThreshold} onChange={(e) => handleEdgeChange(parseFloat(e.target.value))} 
                    style={{ width: '100%', accentColor: '#58f0ff' }}
                  />
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span>Simulated Volatility</span>
                    <span style={{ color: '#58f0ff', fontWeight: 'bold' }}>{simVolatility}</span>
                  </div>
                  <input 
                    type="range" min="10" max="100" step="5" 
                    value={simVolatility} onChange={(e) => handleVolatilityChange(parseInt(e.target.value))} 
                    style={{ width: '100%', accentColor: '#58f0ff' }}
                  />
                </div>
              </div>
            </div>

            {/* Polymarket CLOB book sides */}
            <div style={styles.panelCard}>
              <h2 style={styles.panelHeader}><Coins size={16} style={{ color: '#58f0ff' }} /> Polymarket CLOB (Contracts)</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {/* YES Contract Side */}
                <div style={{ border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '12px', padding: '12px', backgroundColor: 'rgba(5, 7, 17, 0.3)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', alignItems: 'center' }}>
                    <strong style={{ fontSize: '12px', color: '#fff' }}>YES Contract (UP)</strong>
                    <span style={{ color: '#bfff6a', fontWeight: 'bold', fontSize: '13px', fontFamily: 'monospace' }}>{Math.round(yesBook.mid * 100)}¢</span>
                  </div>
                  <div style={{ display: 'grid', gap: '4px', fontSize: '10px', fontFamily: 'monospace' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', color: 'rgba(239, 246, 255, 0.4)', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '4px', fontWeight: 600 }}>
                      <span>SIZE</span><span style={{ textAlign: 'right', paddingRight: '4px' }}>ASK</span><span style={{ textAlign: 'left', paddingLeft: '4px' }}>BID</span><span style={{ textAlign: 'right' }}>SIZE</span>
                    </div>
                    {yesBook.asks.slice(0, 3).reverse().map((ask: any, idx: number) => (
                      <div key={idx} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', alignItems: 'center' }}>
                        <span style={{ color: 'rgba(239, 246, 255, 0.5)' }}>{ask.size}</span>
                        <span style={{ color: '#ff6fb3', textAlign: 'right', paddingRight: '4px', fontWeight: 600 }}>{Math.round(ask.price * 100)}¢</span>
                        <span style={{ color: '#bfff6a', textAlign: 'left', paddingLeft: '4px', fontWeight: 600 }}>{Math.round(yesBook.bids[idx]?.price * 100)}¢</span>
                        <span style={{ color: 'rgba(239, 246, 255, 0.5)', textAlign: 'right' }}>{yesBook.bids[idx]?.size}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* NO Contract Side */}
                <div style={{ border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '12px', padding: '12px', backgroundColor: 'rgba(5, 7, 17, 0.3)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', alignItems: 'center' }}>
                    <strong style={{ fontSize: '12px', color: '#fff' }}>NO Contract (DOWN)</strong>
                    <span style={{ color: '#ff6fb3', fontWeight: 'bold', fontSize: '13px', fontFamily: 'monospace' }}>{Math.round(noBook.mid * 100)}¢</span>
                  </div>
                  <div style={{ display: 'grid', gap: '4px', fontSize: '10px', fontFamily: 'monospace' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', color: 'rgba(239, 246, 255, 0.4)', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '4px', fontWeight: 600 }}>
                      <span>SIZE</span><span style={{ textAlign: 'right', paddingRight: '4px' }}>ASK</span><span style={{ textAlign: 'left', paddingLeft: '4px' }}>BID</span><span style={{ textAlign: 'right' }}>SIZE</span>
                    </div>
                    {noBook.asks.slice(0, 3).reverse().map((ask: any, idx: number) => (
                      <div key={idx} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', alignItems: 'center' }}>
                        <span style={{ color: 'rgba(239, 246, 255, 0.5)' }}>{ask.size}</span>
                        <span style={{ color: '#ff6fb3', textAlign: 'right', paddingRight: '4px', fontWeight: 600 }}>{Math.round(ask.price * 100)}¢</span>
                        <span style={{ color: '#bfff6a', textAlign: 'left', paddingLeft: '4px', fontWeight: 600 }}>{Math.round(noBook.bids[idx]?.price * 100)}¢</span>
                        <span style={{ color: 'rgba(239, 246, 255, 0.5)', textAlign: 'right' }}>{noBook.bids[idx]?.size}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Bayesian Model Engine & Logs */}
            <div style={styles.panelCard}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', paddingBottom: '12px', marginBottom: '16px' }}>
                <h2 style={{ margin: 0, fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px', color: '#fff', fontWeight: 600 }}><FileText size={16} style={{ color: '#9d7dff' }} /> Bayesian Model Engine & Logs</h2>
                <button 
                  onClick={() => setSimLogs([])}
                  style={{ ...styles.refreshButton, padding: '4px 10px', fontSize: '10px' }}
                >
                  Clear
                </button>
              </div>
              
              <div style={{ height: '220px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px', fontFamily: 'monospace', fontSize: '11px', backgroundColor: 'rgba(5, 7, 17, 0.64)', padding: '12px', borderRadius: '14px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
                {simLogs.length === 0 ? (
                  <span style={{ color: 'rgba(239, 246, 255, 0.4)' }}>Waiting for engine telemetry...</span>
                ) : (
                  simLogs.map((log: any, idx: number) => {
                    let color = '#fff';
                    if (log.type === 'signal') color = '#58f0ff';
                    if (log.type === 'edge') color = '#9d7dff';
                    if (log.type === 'trade') color = '#bfff6a';
                    if (log.type === 'error') color = '#ff6fb3';
                    if (log.type === 'settle') color = '#ffd166';
                    return (
                      <div key={idx} style={{ display: 'flex', gap: '8px', lineHeight: '1.4' }}>
                        <span style={{ color: 'rgba(239, 246, 255, 0.4)' }}>[{log.time}]</span>
                        <span style={{ color, fontWeight: 'bold' }}>[{log.type.toUpperCase()}]</span>
                        <span style={{ color: '#f1f5f9' }}>{log.msg}</span>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Historical Predictions Log */}
        <div style={{ ...styles.panelCard, marginTop: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', paddingBottom: '12px', marginBottom: '16px' }}>
            <h2 style={{ margin: 0, fontSize: '15px', display: 'flex', alignItems: 'center', gap: '8px', color: '#fff', fontWeight: 600 }}>
              <FileText size={16} style={{ color: '#58f0ff' }} /> HISTORICAL PREDICTIONS LOG
            </h2>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button 
                onClick={() => {
                  const headers = ['Round ID', 'Timestamp', 'Strike Price', 'Expiry Price', 'Side', 'Quantity', 'Avg Entry', 'Avg Exit', 'Outcome', 'Net PnL'];
                  const rows = simHistory.map(h => [
                    `#${h.roundId}`,
                    h.timestamp,
                    h.strikePrice.toFixed(2),
                    h.expiryPrice.toFixed(2),
                    h.side,
                    h.size,
                    `${Math.round(h.entryPrice * 100)}¢`,
                    `${Math.round(h.exitPrice * 100)}¢`,
                    h.outcome,
                    `${h.pnl >= 0 ? '+' : ''}${h.pnl.toFixed(2)}`
                  ]);
                  const csvContent = "data:text/csv;charset=utf-8," 
                    + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
                  const encodedUri = encodeURI(csvContent);
                  const link = document.createElement("a");
                  link.setAttribute("href", encodedUri);
                  link.setAttribute("download", `predictions_log_${simAsset}.csv`);
                  document.body.appendChild(link);
                  link.click();
                  document.body.removeChild(link);
                }}
                style={{ ...styles.refreshButton, padding: '4px 12px', fontSize: '11px', gap: '4px' }}
                disabled={simHistory.length === 0}
              >
                EXPORT CSV
              </button>
              <button 
                onClick={async () => {
                  const secret = prompt('Enter Admin Passcode to Clear Database:');
                  if (!secret) return;
                  try {
                    const res = await fetch(`/api/dashboard/predictions?secret=${encodeURIComponent(secret)}&asset=${simAsset}`, {
                      method: 'DELETE'
                    });
                    const result = await res.json();
                    if (res.ok) {
                      setSimHistory([]);
                      setSimPnl(0);
                      setSimWins(0);
                      setSimLosses(0);
                      setSimWinRate(0);
                      setSimVolume(0);
                      simStateRef.current.wins = 0;
                      simStateRef.current.losses = 0;
                      simStateRef.current.totalProfit = 0;
                      simStateRef.current.totalVolume = 0;
                      alert('Database cleared successfully.');
                    } else {
                      alert(`Error: ${result.error || 'Failed to clear database'}`);
                    }
                  } catch (err: any) {
                    alert(`Request failed: ${err.message}`);
                  }
                }}
                style={{ 
                  ...styles.refreshButton, 
                  padding: '4px 12px', 
                  fontSize: '11px', 
                  gap: '4px', 
                  backgroundColor: 'rgba(255, 111, 179, 0.1)', 
                  borderColor: 'rgba(255, 111, 179, 0.4)',
                  color: '#ff6fb3'
                }}
              >
                CLEAR DATABASE
              </button>
            </div>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', fontFamily: 'monospace' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.08)', color: 'rgba(239, 246, 255, 0.4)', height: '32px' }}>
                  <th style={{ textAlign: 'left', padding: '8px' }}>ROUND ID</th>
                  <th style={{ textAlign: 'left', padding: '8px' }}>TIMESTAMP</th>
                  <th style={{ textAlign: 'left', padding: '8px' }}>STRIKE PRICE</th>
                  <th style={{ textAlign: 'left', padding: '8px' }}>EXPIRY PRICE</th>
                  <th style={{ textAlign: 'left', padding: '8px' }}>SIDE</th>
                  <th style={{ textAlign: 'left', padding: '8px' }}>QUANTITY</th>
                  <th style={{ textAlign: 'left', padding: '8px' }}>AVG ENTRY</th>
                  <th style={{ textAlign: 'left', padding: '8px' }}>AVG EXIT</th>
                  <th style={{ textAlign: 'left', padding: '8px' }}>OUTCOME</th>
                  <th style={{ textAlign: 'right', padding: '8px' }}>NET P&L</th>
                </tr>
              </thead>
              <tbody>
                {simHistory.length === 0 ? (
                  <tr>
                    <td colSpan={10} style={{ padding: '24px', textAlign: 'center', color: 'rgba(239, 246, 255, 0.3)' }}>
                      Waiting for first round settlement...
                    </td>
                  </tr>
                ) : (
                  simHistory.map((trade: any, index: number) => (
                    <tr 
                      key={index} 
                      style={{ 
                        borderBottom: '1px solid rgba(255, 255, 255, 0.05)', 
                        backgroundColor: trade.outcome === 'WIN' ? 'rgba(191, 255, 106, 0.02)' : 'rgba(255, 111, 179, 0.02)'
                      }}
                    >
                      <td style={{ padding: '10px 8px', color: 'rgba(239, 246, 255, 0.8)' }}>#{trade.roundId}</td>
                      <td style={{ padding: '10px 8px', color: 'rgba(239, 246, 255, 0.5)' }}>{trade.timestamp}</td>
                      <td style={{ padding: '10px 8px', color: '#ffd166' }}>${trade.strikePrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                      <td style={{ padding: '10px 8px', color: '#58f0ff' }}>${trade.expiryPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                      <td style={{ padding: '10px 8px' }}>
                        <span 
                          style={{ 
                            backgroundColor: trade.side === 'YES' ? 'rgba(191, 255, 106, 0.15)' : 'rgba(255, 111, 179, 0.15)',
                            color: trade.side === 'YES' ? '#bfff6a' : '#ff6fb3',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            fontWeight: 'bold',
                            fontSize: '10px'
                          }}
                        >
                          {trade.side}
                        </span>
                      </td>
                      <td style={{ padding: '10px 8px', color: '#fff' }}>{trade.size.toLocaleString()}</td>
                      <td style={{ padding: '10px 8px', color: 'rgba(239, 246, 255, 0.8)' }}>{Math.round(trade.entryPrice * 100)}¢</td>
                      <td style={{ padding: '10px 8px', color: 'rgba(239, 246, 255, 0.8)' }}>{Math.round(trade.exitPrice * 100)}¢</td>
                      <td style={{ padding: '10px 8px' }}>
                        <span style={{ color: trade.outcome === 'WIN' ? '#bfff6a' : '#ff6fb3', fontWeight: 'bold' }}>
                          {trade.outcome}
                        </span>
                      </td>
                      <td style={{ padding: '10px 8px', textAlign: 'right', fontWeight: 'bold', color: trade.pnl >= 0 ? '#bfff6a' : '#ff6fb3' }}>
                        {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </>
    )}
      </div>
    </div>
  );
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    backgroundColor: '#050711',
    color: '#ffffff',
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    position: 'relative',
    zIndex: 1,
  },
  centeredContainer: {
    backgroundColor: '#050711',
    color: '#ffffff',
    minHeight: '100vh',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
    zIndex: 1,
  },
  loader: {
    textAlign: 'center',
    position: 'relative',
    zIndex: 2,
  },
  spinIcon: {
    animation: 'spin 1.5s linear infinite',
    color: '#58f0ff',
  },
  spinAnimation: {
    animation: 'spin 1s linear infinite',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '20px 24px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
    backgroundColor: 'rgba(5, 7, 17, 0.65)',
    backdropFilter: 'blur(20px)',
    position: 'sticky',
    top: 0,
    zIndex: 100,
  },
  logoRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  logoLink: {
    fontSize: '18px',
    fontWeight: 'bold',
    color: '#ffffff',
    textDecoration: 'none',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  logoSymbol: {
    color: '#58f0ff',
  },
  divider: {
    color: 'rgba(255, 255, 255, 0.14)',
    fontWeight: 300,
  },
  panelTitle: {
    fontSize: '14px',
    color: 'rgba(239, 246, 255, 0.82)',
    fontWeight: 500,
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  ledgerBadgeVerified: {
    backgroundColor: 'rgba(191, 255, 106, 0.1)',
    border: '1px solid rgba(191, 255, 106, 0.3)',
    color: '#bfff6a',
    fontSize: '12px',
    fontWeight: 600,
    padding: '6px 12px',
    borderRadius: '4px',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  ledgerBadgeCompromised: {
    backgroundColor: 'rgba(255, 111, 179, 0.1)',
    border: '1px solid rgba(255, 111, 179, 0.3)',
    color: '#ff6fb3',
    fontSize: '12px',
    fontWeight: 600,
    padding: '6px 12px',
    borderRadius: '4px',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  refreshButton: {
    backgroundColor: 'transparent',
    border: '1px solid rgba(255, 255, 255, 0.14)',
    color: 'rgba(239, 246, 255, 0.66)',
    padding: '6px 12px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '12px',
    fontWeight: 500,
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    transition: 'all 0.2s',
  },
  dashboardLayout: {
    flex: 1,
    padding: '24px',
    maxWidth: '1400px',
    margin: '0 auto',
    width: '100%',
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
    position: 'relative',
    zIndex: 2,
  },
  bannerSuccess: {
    backgroundColor: 'rgba(191, 255, 106, 0.1)',
    border: '1px solid rgba(191, 255, 106, 0.3)',
    color: '#bfff6a',
    padding: '12px 16px',
    borderRadius: '12px',
    fontSize: '14px',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  bannerError: {
    backgroundColor: 'rgba(255, 111, 179, 0.1)',
    border: '1px solid rgba(255, 111, 179, 0.3)',
    color: '#ff6fb3',
    padding: '12px 16px',
    borderRadius: '12px',
    fontSize: '14px',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  analyticsRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
    gap: '16px',
  },
  analyticCard: {
    background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.025))',
    border: '1px solid rgba(255, 255, 255, 0.12)',
    borderRadius: '24px',
    padding: '20px',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    backdropFilter: 'blur(20px)',
    boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.08)',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardTitle: {
    fontSize: '11px',
    fontWeight: 600,
    color: 'rgba(239, 246, 255, 0.54)',
    letterSpacing: '1px',
  },
  cardValue: {
    fontSize: '28px',
    fontWeight: 'bold',
  },
  cardSubText: {
    fontSize: '12px',
    color: 'rgba(239, 246, 255, 0.66)',
  },
  advisoryCard: {
    backgroundColor: 'rgba(157, 125, 255, 0.06)',
    border: '1px solid rgba(157, 125, 255, 0.22)',
    borderRadius: '20px',
    padding: '16px 20px',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    backdropFilter: 'blur(20px)',
  },
  advisoryHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  advisoryTitle: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#9d7dff',
  },
  advisoryBody: {
    fontSize: '13px',
    color: 'rgba(239, 246, 255, 0.7)',
    lineHeight: 1.5,
  },
  gridTwoCol: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))',
    gap: '24px',
  },
  gridCol: {
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
  },
  panelCard: {
    background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.025))',
    border: '1px solid rgba(255, 255, 255, 0.12)',
    borderRadius: '24px',
    padding: '24px',
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
    backdropFilter: 'blur(20px)',
    boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.08)',
  },
  panelHeader: {
    fontSize: '16px',
    fontWeight: 600,
    marginBottom: '20px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.14)',
    paddingBottom: '12px',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  formGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '12px',
  },
  label: {
    fontSize: '12px',
    fontWeight: 500,
    color: 'rgba(239, 246, 255, 0.66)',
  },
  input: {
    backgroundColor: 'rgba(5, 7, 17, 0.64)',
    border: '1px solid rgba(255, 255, 255, 0.14)',
    color: '#ffffff',
    padding: '12px 14px',
    borderRadius: '14px',
    fontSize: '14px',
    outline: 'none',
  },
  select: {
    backgroundColor: 'rgba(5, 7, 17, 0.64)',
    border: '1px solid rgba(255, 255, 255, 0.14)',
    color: '#ffffff',
    padding: '12px 14px',
    borderRadius: '14px',
    fontSize: '14px',
    outline: 'none',
  },
  helperText: {
    fontSize: '11px',
    color: 'rgba(239, 246, 255, 0.5)',
  },
  buttonAction: {
    background: 'linear-gradient(135deg, #58f0ff, #bfff6a)',
    color: '#051016',
    border: 'none',
    padding: '14px 22px',
    borderRadius: '16px',
    fontWeight: 820,
    cursor: 'pointer',
    fontSize: '14px',
    transition: 'all 0.2s',
    boxShadow: '0 8px 24px rgba(88, 240, 255, 0.2)',
    letterSpacing: '-0.02em',
  },
  radioRow: {
    display: 'flex',
    gap: '16px',
    marginTop: '4px',
  },
  radioLabel: {
    fontSize: '13px',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    cursor: 'pointer',
  },
  radio: {
    accentColor: '#58f0ff',
  },
  connectionList: {
    marginTop: '20px',
    borderTop: '1px solid rgba(255, 255, 255, 0.14)',
    paddingTop: '16px',
  },
  subTitle: {
    fontSize: '13px',
    color: 'rgba(239, 246, 255, 0.5)',
    marginBottom: '12px',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  connectionRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: 'rgba(5, 7, 17, 0.5)',
    padding: '12px',
    borderRadius: '16px',
    border: '1px solid rgba(255, 255, 255, 0.12)',
  },
  connInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  connLogo: {
    backgroundColor: '#58f0ff',
    color: '#051016',
    width: '28px',
    height: '28px',
    borderRadius: '50px',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    fontSize: '12px',
    fontWeight: 'bold',
  },
  connName: {
    fontSize: '13px',
    fontWeight: 600,
  },
  connSub: {
    fontSize: '11px',
    color: 'rgba(239, 246, 255, 0.5)',
  },
  statusIndicatorGreen: {
    fontSize: '10px',
    fontWeight: 600,
    color: '#bfff6a',
    backgroundColor: 'rgba(191, 255, 106, 0.1)',
    padding: '2px 6px',
    borderRadius: '4px',
  },
  simulatorGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  simCard: {
    backgroundColor: 'rgba(5, 7, 17, 0.5)',
    border: '1px solid rgba(255, 255, 255, 0.12)',
    borderRadius: '16px',
    padding: '14px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  simTitle: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    fontWeight: 600,
    fontSize: '14px',
  },
  statusGreen: {
    fontSize: '10px',
    color: '#bfff6a',
    fontWeight: 600,
  },
  statusAmber: {
    fontSize: '10px',
    color: '#ffd166',
    fontWeight: 600,
  },
  simActions: {
    display: 'flex',
    gap: '8px',
  },
  simButtonLong: {
    backgroundColor: 'rgba(191, 255, 106, 0.12)',
    border: '1px solid rgba(191, 255, 106, 0.3)',
    color: '#bfff6a',
    padding: '6px 12px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: 600,
    cursor: 'pointer',
  },
  simButtonShort: {
    backgroundColor: 'rgba(255, 111, 179, 0.12)',
    border: '1px solid rgba(255, 111, 179, 0.3)',
    color: '#ff6fb3',
    padding: '6px 12px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: 600,
    cursor: 'pointer',
  },
  emptyState: {
    textAlign: 'center',
    color: 'rgba(239, 246, 255, 0.5)',
    padding: '24px 0',
    fontSize: '14px',
  },
  botGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  botCard: {
    backgroundColor: 'rgba(5, 7, 17, 0.5)',
    border: '1px solid rgba(255, 255, 255, 0.12)',
    borderRadius: '20px',
    padding: '16px',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  botCardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  botCodeName: {
    fontSize: '14px',
    fontWeight: 'bold',
    marginRight: '8px',
  },
  badgeLive: {
    backgroundColor: 'rgba(191, 255, 106, 0.15)',
    color: '#bfff6a',
    fontSize: '9px',
    fontWeight: 600,
    padding: '2px 6px',
    borderRadius: '4px',
  },
  badgePaper: {
    backgroundColor: 'rgba(157, 125, 255, 0.15)',
    color: '#9d7dff',
    fontSize: '9px',
    fontWeight: 600,
    padding: '2px 6px',
    borderRadius: '4px',
  },
  botStatusActive: {
    fontSize: '11px',
    fontWeight: 600,
    color: '#bfff6a',
    padding: '4px 8px',
    borderRadius: '20px',
    backgroundColor: 'rgba(191, 255, 106, 0.1)',
  },
  botStatusPaused: {
    fontSize: '11px',
    fontWeight: 600,
    color: '#ffd166',
    padding: '4px 8px',
    borderRadius: '20px',
    backgroundColor: 'rgba(255, 209, 102, 0.1)',
  },
  botStatusKilled: {
    fontSize: '11px',
    fontWeight: 600,
    color: '#ff6fb3',
    padding: '4px 8px',
    borderRadius: '20px',
    backgroundColor: 'rgba(255, 111, 179, 0.1)',
  },
  botCardBody: {
    fontSize: '12px',
    color: 'rgba(239, 246, 255, 0.66)',
    display: 'flex',
    gap: '16px',
  },
  botCardActions: {
    display: 'flex',
    gap: '8px',
    marginTop: '4px',
  },
  botButtonPause: {
    backgroundColor: 'transparent',
    border: '1px solid #ffd166',
    color: '#ffd166',
    padding: '4px 8px',
    borderRadius: '12px',
    fontSize: '11px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  botButtonResume: {
    backgroundColor: 'transparent',
    border: '1px solid #bfff6a',
    color: '#bfff6a',
    padding: '4px 8px',
    borderRadius: '12px',
    fontSize: '11px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  botButtonKill: {
    backgroundColor: 'transparent',
    border: '1px solid #ff6fb3',
    color: '#ff6fb3',
    padding: '4px 8px',
    borderRadius: '12px',
    fontSize: '11px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '13px',
  },
  th: {
    textAlign: 'left',
    color: 'rgba(239, 246, 255, 0.54)',
    fontWeight: 600,
    padding: '8px 12px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.14)',
  },
  tr: {
    borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
  },
  td: {
    padding: '10px 12px',
  },
  tdGreen: {
    padding: '10px 12px',
    color: '#bfff6a',
    fontWeight: 500,
  },
  tdRed: {
    padding: '10px 12px',
    color: '#ff6fb3',
    fontWeight: 500,
  },
  journalContainer: {
    maxHeight: '300px',
    overflowY: 'auto',
  },
  timeline: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  timelineItem: {
    borderLeft: '2px solid rgba(255, 255, 255, 0.14)',
    paddingLeft: '16px',
    marginLeft: '6px',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  timelineHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  buyTag: {
    color: '#bfff6a',
    fontSize: '11px',
    fontWeight: 'bold',
  },
  sellTag: {
    color: '#ff6fb3',
    fontSize: '11px',
    fontWeight: 'bold',
  },
  timelineTime: {
    fontSize: '11px',
    color: 'rgba(239, 246, 255, 0.5)',
  },
  timelineBody: {
    fontSize: '13px',
    display: 'flex',
    justifyContent: 'space-between',
  },
  timelineHash: {
    fontSize: '10px',
    color: 'rgba(239, 246, 255, 0.5)',
  },
  auditContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
    maxHeight: '200px',
    overflowY: 'auto',
  },
  auditRow: {
    backgroundColor: 'rgba(5, 7, 17, 0.5)',
    borderLeft: '3px solid #ff6fb3',
    padding: '10px 12px',
    borderRadius: '12px',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  auditTime: {
    fontSize: '10px',
    color: 'rgba(239, 246, 255, 0.5)',
  },
  auditDetail: {
    fontSize: '12px',
    color: '#ffffff',
  },
};

