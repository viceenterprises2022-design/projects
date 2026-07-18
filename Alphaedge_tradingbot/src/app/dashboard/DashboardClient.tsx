'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import './dashboard.css';

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
  AlertOctagon,
  Radio,
  Scale,
} from 'lucide-react';

import { handleSignOut } from '@/app/auth-actions';

// ---------------------------------------------------------------------------
// Model math
// ---------------------------------------------------------------------------

// Standard normal CDF (Abramowitz & Stegun 7.1.26 approximation)
function normCDF(x: number) {
  const a1 = 0.254829592, a2 = -0.284496736, a3 = 1.421413741;
  const a4 = -1.453152027, a5 = 1.061405429, p = 0.3275911;
  const sign = x < 0 ? -1 : 1;
  const absX = Math.abs(x) / Math.sqrt(2.0);
  const t = 1.0 / (1.0 + p * absX);
  const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-absX * absX);
  return 0.5 * (1.0 + sign * y);
}

const SECONDS_PER_YEAR = 31_536_000;

// Binary fair value under driftless GBM: sigma in USD over remaining round time.
function binaryFairValue(price: number, strike: number, annualVolPct: number, secondsRemaining: number) {
  const sigmaUsd = price * (annualVolPct / 100) * Math.sqrt(Math.max(secondsRemaining, 0.001) / SECONDS_PER_YEAR);
  const z = (price - strike) / Math.max(sigmaUsd, 1e-9);
  return { pYes: Math.min(Math.max(normCDF(z), 0.01), 0.99), z, sigmaUsd };
}

// ---------------------------------------------------------------------------
// Desk constants
// ---------------------------------------------------------------------------

const DESK_ASSETS = ['XAU', 'BTC-PERP', 'ETH-PERP'] as const;
type DeskAsset = typeof DESK_ASSETS[number];

const ASSET_LABEL: Record<DeskAsset, string> = {
  'XAU': 'XAU · GOLD (PAXG)',
  'BTC-PERP': 'BTC · PERPETUAL',
  'ETH-PERP': 'ETH · PERPETUAL',
};

// Maps bot template asset classes to live feed keys
function feedKeyForAssetClass(assetClass: string): DeskAsset | null {
  const a = (assetClass || '').toUpperCase();
  if (a.startsWith('BTC')) return 'BTC-PERP';
  if (a.startsWith('ETH')) return 'ETH-PERP';
  if (a.startsWith('XAU') || a.startsWith('GOLD') || a.startsWith('PAXG')) return 'XAU';
  return null;
}

const hypotheses = [
  'Gold regime filter over BTC-PERP breakout with funding-rate confirmation',
  'Z-score mean reversion on XAU/BTC ratio, 15m lookback, vol-scaled entries',
  'ETH-PERP order-flow imbalance against Hyperliquid oracle basis',
  'Cross-asset momentum overlay: XAU, BTC, ETH with Bayesian vol filter',
  'Latency arbitrage on binary round pricing vs continuous mark drift',
];

const pipelineSteps = [
  { id: 1, name: 'Parse' },
  { id: 2, name: 'IR Build' },
  { id: 3, name: 'Compile' },
  { id: 4, name: 'Backtest' },
  { id: 5, name: 'Validate' },
  { id: 6, name: 'Approve' },
  { id: 7, name: 'Deploy' },
];

const getActiveStepId = (sec: number) => {
  if (sec > 75) return 1;
  if (sec > 65) return 2;
  if (sec > 55) return 3;
  if (sec > 30) return 4;
  if (sec > 18) return 5;
  if (sec > 8) return 6;
  return 7;
};

interface FeedContext {
  mark: number;
  prevDay: number;
  change24hPct: number;
  fundingRate: number;
  openInterest: number;
  dayVolumeUsd: number;
  oracle: number;
}

function fmtUsd(n: number | undefined | null, dp = 2) {
  if (n === undefined || n === null || !Number.isFinite(n)) return '—';
  return '$' + n.toLocaleString(undefined, { minimumFractionDigits: dp, maximumFractionDigits: dp });
}

function fmtSignedUsd(n: number | undefined | null) {
  if (n === undefined || n === null || !Number.isFinite(n)) return '—';
  const sign = n > 0 ? '+' : n < 0 ? '−' : '';
  return sign + '$' + Math.abs(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtCompact(n: number | undefined | null) {
  if (n === undefined || n === null || !Number.isFinite(n)) return '—';
  if (n >= 1e9) return (n / 1e9).toFixed(2) + 'B';
  if (n >= 1e6) return (n / 1e6).toFixed(2) + 'M';
  if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K';
  return n.toFixed(0);
}

function fmtTime(epochMs: number) {
  if (!Number.isFinite(epochMs)) return '—';
  return new Date(epochMs).toLocaleString(undefined, {
    month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
  });
}

// ---------------------------------------------------------------------------

export default function DashboardClient({ user }: { user: any }) {
  // ---- Cockpit state ----
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const [apiKey, setApiKey] = useState('');
  const [submittingConnection, setSubmittingConnection] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [selectedConnection, setSelectedConnection] = useState('');
  const [riskCeiling, setRiskCeiling] = useState('5.0');
  const [maxNotional, setMaxNotional] = useState('1000');
  const [botMode, setBotMode] = useState<'paper' | 'live'>('paper');
  const [submittingInstance, setSubmittingInstance] = useState(false);
  const [simulatingSignal, setSimulatingSignal] = useState(false);

  const [activeTab, setActiveTab] = useState<'cockpit' | 'simulator'>('cockpit');
  const [simAsset, setSimAsset] = useState<DeskAsset>('BTC-PERP');

  const [clock, setClock] = useState('');

  // ---- Live feed state ----
  const [prices, setPrices] = useState<Record<string, number>>({});
  const [contexts, setContexts] = useState<Record<string, FeedContext>>({});
  const [tickDir, setTickDir] = useState<Record<string, 'up' | 'down' | null>>({});
  const [feedError, setFeedError] = useState<string | null>(null);
  const [feedTs, setFeedTs] = useState<number>(0);
  const pricesRef = useRef<Record<string, number>>({});
  const feedTsRef = useRef<number>(0);

  // ---- Simulator state ----
  const [dbStats, setDbStats] = useState<any>(null);
  const [simHistory, setSimHistory] = useState<Array<any>>([]);
  const [simLogs, setSimLogs] = useState<Array<{ time: string; type: string; msg: string }>>([]);
  const [simCountdown, setSimCountdown] = useState('01:30');
  const [simSecondsRemaining, setSimSecondsRemaining] = useState(90);
  const [simPosition, setSimPosition] = useState<any>(null);
  const [modelReadout, setModelReadout] = useState<{ pYes: number; z: number; sigmaUsd: number } | null>(null);
  const [yesBook, setYesBook] = useState<any>({ mid: 0.5, bids: [], asks: [] });
  const [noBook, setNoBook] = useState<any>({ mid: 0.5, bids: [], asks: [] });
  const [robustnessData, setRobustnessData] = useState<Record<string, number[]>>({
    'XAU': [0.8, 1.9, -0.6, 2.4, 3.1, 1.2],
    'BTC': [-1.5, 3.4, 4.2, 5.5, 7.9, 6.1],
    'ETH': [-2.7, 1.6, 4.9, 3.8, 4.5, 2.2],
  });

  const [simSpeed, setSimSpeed] = useState(5);
  const [simTradeSize, setSimTradeSize] = useState(1000);
  const [simEdgeThreshold, setSimEdgeThreshold] = useState(3.5);
  const [simVolatility, setSimVolatility] = useState(45);
  const [simRunning, setSimRunning] = useState(true);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const simStateRef = useRef({
    isRunning: true,
    speedMultiplier: 5,
    volatility: 45,
    tradeSizeUsd: 1000,
    minEdgeThreshold: 3.5,
    asset: 'BTC-PERP' as DeskAsset,
    price: 0,
    strikePrice: 0,
    strikeLocked: false,
    priceHistory: [] as Array<{ price: number; trade?: 'YES' | 'NO' }>,
    roundSecondsRemaining: 90,
    roundId: 101,
    tickCount: 0,
    yesContract: { midPrice: 0.5, bids: [] as any[], asks: [] as any[] },
    noContract: { midPrice: 0.5, bids: [] as any[], asks: [] as any[] },
    laggedFairValueYes: 0.5,
    activePosition: null as any,
    settling: false,
    staleWarned: false,
  });

  // ---- Wall clock ----
  useEffect(() => {
    const t = setInterval(() => {
      setClock(new Date().toLocaleTimeString(undefined, { hour12: false }));
    }, 1000);
    return () => clearInterval(t);
  }, []);

  // ---- Live price feed (Hyperliquid via server route, 2s poll) ----
  useEffect(() => {
    let cancelled = false;
    async function syncPrices() {
      try {
        const res = await fetch('/api/dashboard/prices');
        const json = await res.json();
        if (cancelled) return;
        if (json && json.success && json.prices) {
          setPrices(prev => {
            const dirs: Record<string, 'up' | 'down' | null> = {};
            for (const k of Object.keys(json.prices)) {
              if (prev[k] !== undefined && json.prices[k] !== prev[k]) {
                dirs[k] = json.prices[k] > prev[k] ? 'up' : 'down';
              }
            }
            if (Object.keys(dirs).length) {
              setTickDir(d => ({ ...d, ...dirs }));
              setTimeout(() => { if (!cancelled) setTickDir({}); }, 750);
            }
            return json.prices;
          });
          setContexts(json.contexts || {});
          setFeedError(null);
          setFeedTs(json.ts || Date.now());
          pricesRef.current = json.prices;
          feedTsRef.current = json.ts || Date.now();
          const st = simStateRef.current;
          if (json.prices[st.asset]) {
            st.price = json.prices[st.asset];
            st.staleWarned = false;
          }
        } else {
          throw new Error(json.error || 'Feed returned no prices');
        }
      } catch (err: any) {
        if (!cancelled) setFeedError(err.message || 'Hyperliquid feed unreachable');
      }
    }
    syncPrices();
    const interval = setInterval(syncPrices, 2000);
    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  // ---- Predictions history (server-verified) ----
  const loadHistory = useCallback(async (asset: string) => {
    try {
      const res = await fetch(`/api/dashboard/predictions?asset=${encodeURIComponent(asset)}`);
      const json = await res.json();
      if (json && json.history) {
        setSimHistory(json.history);
        setDbStats(json.stats || null);
        if (json.nextRoundId && json.nextRoundId > simStateRef.current.roundId) {
          simStateRef.current.roundId = json.nextRoundId;
        }
      }
    } catch (err) {
      console.error('Failed to load predictions history:', err);
    }
  }, []);

  useEffect(() => { loadHistory(simAsset); }, [simAsset, loadHistory]);

  // ---- Cockpit data ----
  const fetchData = useCallback(async () => {
    try {
      const res = await fetch('/api/dashboard/info');
      if (!res.ok) throw new Error('Failed to fetch dashboard data');
      const json = await res.json();
      setData(json);
      if (json.botTemplates?.length > 0) {
        setSelectedTemplate(prev => prev || json.botTemplates[0].id);
      }
      if (json.exchangeConnections?.length > 0) {
        setSelectedConnection(prev => prev || json.exchangeConnections[0].id);
      }
    } catch (err: any) {
      console.error(err);
      setMessage({ type: 'error', text: err.message || 'Error loading dashboard' });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  // ---- Simulator engine ----
  useEffect(() => {
    if (activeTab !== 'simulator') return;

    const st = simStateRef.current;
    st.isRunning = simRunning;
    st.speedMultiplier = simSpeed;
    st.volatility = simVolatility;
    st.tradeSizeUsd = simTradeSize;
    st.minEdgeThreshold = simEdgeThreshold;
    st.asset = simAsset;
    st.strikeLocked = false;
    st.price = pricesRef.current[simAsset] || 0;
    st.strikePrice = 0;
    st.priceHistory = [];
    st.roundSecondsRemaining = 90;
    st.tickCount = 0;
    st.yesContract = { midPrice: 0.5, bids: [], asks: [] };
    st.noContract = { midPrice: 0.5, bids: [], asks: [] };
    st.laggedFairValueYes = 0.5;
    st.activePosition = null;
    st.settling = false;

    setSimLogs([]);
    setSimPosition(null);

    const addSimLog = (type: string, msg: string) => {
      const time = new Date().toLocaleTimeString(undefined, { hour12: false });
      setSimLogs(prev => {
        const updated = [...prev, { time, type, msg }];
        if (updated.length > 60) updated.shift();
        return updated;
      });
    };

    addSimLog('info', `Engine armed for ${simAsset}. Awaiting live Hyperliquid mark to lock strike…`);

    let timer: NodeJS.Timeout | null = null;
    let disposed = false;

    const generateBookSides = (midPrice: number, side: 'bid' | 'ask') => {
      const rows = [];
      const step = 0.01;
      for (let i = 0; i < 5; i++) {
        let price = side === 'bid' ? midPrice - i * step - 0.005 : midPrice + i * step + 0.005;
        price = Math.min(Math.max(price, 0.01), 0.99);
        const size = Math.max(100, 800 + i * 1200 + Math.floor(Math.random() * 500) - 250);
        rows.push({ price, size });
      }
      return rows;
    };

    const drawChart = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      const w = canvas.width, h = canvas.height;
      ctx.clearRect(0, 0, w, h);
      if (st.priceHistory.length === 0) return;

      const prices = st.priceHistory.map(p => p.price);
      prices.push(st.strikePrice);
      let minPrice = Math.min(...prices), maxPrice = Math.max(...prices);
      const range = maxPrice - minPrice;
      const padding = range === 0 ? Math.max(minPrice * 0.0004, 0.5) : range * 0.2;
      minPrice -= padding; maxPrice += padding;

      const getX = (i: number) => (i / 90) * w;
      const getY = (p: number) => h - ((p - minPrice) / (maxPrice - minPrice)) * h;

      // hairline grid
      ctx.strokeStyle = 'rgba(216, 222, 240, 0.05)';
      ctx.lineWidth = 1;
      for (let i = 1; i < 6; i++) {
        const y = (i / 6) * h;
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
        const x = (i / 6) * w;
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
      }

      // strike line — gold
      const strikeY = getY(st.strikePrice);
      ctx.strokeStyle = 'rgba(217, 169, 78, 0.55)';
      ctx.lineWidth = 1.2;
      ctx.setLineDash([5, 5]);
      ctx.beginPath(); ctx.moveTo(0, strikeY); ctx.lineTo(w, strikeY); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = 'rgba(245, 199, 106, 0.9)';
      ctx.font = '10px monospace';
      ctx.fillText(`STRIKE ${st.strikePrice.toFixed(2)}`, 8, strikeY - 6);

      // price path — azure
      ctx.beginPath();
      ctx.moveTo(getX(0), getY(st.priceHistory[0].price));
      for (let i = 1; i < st.priceHistory.length; i++) {
        ctx.lineTo(getX(i), getY(st.priceHistory[i].price));
      }
      ctx.strokeStyle = '#6fb3e0';
      ctx.lineWidth = 2;
      ctx.stroke();

      const gradient = ctx.createLinearGradient(0, 0, 0, h);
      gradient.addColorStop(0, 'rgba(111, 179, 224, 0.14)');
      gradient.addColorStop(1, 'rgba(111, 179, 224, 0)');
      ctx.fillStyle = gradient;
      ctx.lineTo(getX(st.priceHistory.length - 1), h);
      ctx.lineTo(getX(0), h);
      ctx.closePath();
      ctx.fill();

      // trade markers
      st.priceHistory.forEach((pt, index) => {
        if (!pt.trade) return;
        const tx = getX(index), ty = getY(pt.price);
        ctx.beginPath();
        if (pt.trade === 'YES') {
          ctx.fillStyle = '#7fce9b';
          ctx.moveTo(tx, ty - 8); ctx.lineTo(tx - 5, ty + 2); ctx.lineTo(tx + 5, ty + 2);
        } else {
          ctx.fillStyle = '#e0706f';
          ctx.moveTo(tx, ty + 8); ctx.lineTo(tx - 5, ty - 2); ctx.lineTo(tx + 5, ty - 2);
        }
        ctx.fill();
      });

      const lastIdx = st.priceHistory.length - 1;
      ctx.beginPath();
      ctx.arc(getX(lastIdx), getY(st.priceHistory[lastIdx].price), 3.5, 0, Math.PI * 2);
      ctx.fillStyle = '#f5c76a';
      ctx.fill();
    };

    const settleRound = async () => {
      const pos = st.activePosition;
      const payload = {
        roundId: st.roundId,
        asset: st.asset,
        strikePrice: st.strikePrice,
        expiryPrice: st.price,
        side: pos.side,
        size: pos.size,
        entryPrice: pos.entryPrice,
      };
      st.settling = true;
      try {
        const res = await fetch('/api/dashboard/predictions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const json = await res.json();
        if (res.ok) {
          addSimLog(json.outcome === 'WIN' ? 'trade' : 'error',
            `SETTLED (server-verified): ${pos.side} → ${json.outcome} · Net PnL ${json.pnl >= 0 ? '+' : ''}$${Number(json.pnl).toFixed(2)}`);
        } else if (res.status === 409) {
          addSimLog('error', `Round #${st.roundId} already settled on server — skipping duplicate.`);
        } else {
          addSimLog('error', `Settlement rejected: ${json.error || res.status}`);
        }
      } catch (err: any) {
        addSimLog('error', `Settlement request failed: ${err.message}`);
      } finally {
        st.settling = false;
        // Re-sync log + stats from the persisted DB so the display never drifts
        loadHistory(st.asset);
      }
    };

    const runStep = () => {
      if (disposed) return;
      if (!st.isRunning) {
        timer = setTimeout(runStep, 1000 / st.speedMultiplier);
        return;
      }

      const livePrice = pricesRef.current[st.asset];
      const feedFresh = Date.now() - feedTsRef.current < 15000;

      // No strike yet: wait for a live tick before starting the round.
      if (!st.strikeLocked) {
        if (livePrice && feedFresh) {
          st.price = livePrice;
          st.strikePrice = livePrice;
          st.strikeLocked = true;
          st.priceHistory = [{ price: livePrice }];
          st.roundSecondsRemaining = 90;
          addSimLog('info', `ROUND #${st.roundId} OPEN — strike locked at ${fmtUsd(livePrice)} (Hyperliquid mark)`);
        } else {
          timer = setTimeout(runStep, 500);
          return;
        }
      }

      // Stale feed guard: freeze the round clock rather than settling on dead data.
      if (!feedFresh) {
        if (!st.staleWarned) {
          st.staleWarned = true;
          addSimLog('error', 'Feed stale >15s — round clock frozen until live data resumes.');
        }
        timer = setTimeout(runStep, 1000);
        return;
      }

      st.tickCount++;
      st.price = livePrice || st.price;
      st.priceHistory.push({ price: st.price });
      if (st.priceHistory.length > 90) st.priceHistory.shift();
      st.roundSecondsRemaining -= 1;

      if (st.tickCount % 6 === 0) {
        const diffPct = ((st.price - st.strikePrice) / st.strikePrice) * 100;
        addSimLog('signal', `${st.asset} mark ${fmtUsd(st.price)} (${diffPct >= 0 ? '+' : ''}${diffPct.toFixed(3)}% vs strike)`);
      }

      // Fair value via annualized-vol binary pricing
      const fv = binaryFairValue(st.price, st.strikePrice, st.volatility, st.roundSecondsRemaining);
      setModelReadout(fv);

      const alpha = 0.35;
      st.laggedFairValueYes = st.laggedFairValueYes * (1 - alpha) + fv.pYes * alpha;
      const laggedYes = st.laggedFairValueYes;

      st.yesContract.midPrice = laggedYes;
      st.yesContract.bids = generateBookSides(laggedYes, 'bid');
      st.yesContract.asks = generateBookSides(laggedYes, 'ask');
      const laggedNo = 1.0 - laggedYes;
      st.noContract.midPrice = laggedNo;
      st.noContract.bids = generateBookSides(laggedNo, 'bid');
      st.noContract.asks = generateBookSides(laggedNo, 'ask');

      // Strategy: buy modeled edge over synthetic market
      if (st.roundSecondsRemaining >= 15 && !st.activePosition) {
        const bestYesAsk = st.yesContract.asks[0];
        const bestNoAsk = st.noContract.asks[0];
        if (bestYesAsk && bestNoAsk) {
          const edgeYes = fv.pYes * 100 - bestYesAsk.price * 100;
          const edgeNo = (1 - fv.pYes) * 100 - bestNoAsk.price * 100;
          if (edgeYes >= st.minEdgeThreshold) {
            const contracts = Math.floor(st.tradeSizeUsd / bestYesAsk.price);
            st.activePosition = { side: 'YES', size: contracts, entryPrice: bestYesAsk.price, costUsd: contracts * bestYesAsk.price };
            st.priceHistory[st.priceHistory.length - 1].trade = 'YES';
            addSimLog('edge', `Edge +${edgeYes.toFixed(1)}% — model P(YES) ${Math.round(fv.pYes * 100)}¢ vs market ${Math.round(bestYesAsk.price * 100)}¢`);
            addSimLog('trade', `BUY YES ${contracts.toLocaleString()} @ ${Math.round(bestYesAsk.price * 100)}¢ · cost ${fmtUsd(st.activePosition.costUsd)}`);
          } else if (edgeNo >= st.minEdgeThreshold) {
            const contracts = Math.floor(st.tradeSizeUsd / bestNoAsk.price);
            st.activePosition = { side: 'NO', size: contracts, entryPrice: bestNoAsk.price, costUsd: contracts * bestNoAsk.price };
            st.priceHistory[st.priceHistory.length - 1].trade = 'NO';
            addSimLog('edge', `Edge +${edgeNo.toFixed(1)}% — model P(NO) ${Math.round((1 - fv.pYes) * 100)}¢ vs market ${Math.round(bestNoAsk.price * 100)}¢`);
            addSimLog('trade', `BUY NO ${contracts.toLocaleString()} @ ${Math.round(bestNoAsk.price * 100)}¢ · cost ${fmtUsd(st.activePosition.costUsd)}`);
          }
        }
      }

      drawChart();

      // Round expiry
      if (st.roundSecondsRemaining <= 0) {
        const winOutcome = st.price > st.strikePrice ? 'YES' : 'NO';
        addSimLog('settle', `ROUND #${st.roundId} EXPIRED — final ${fmtUsd(st.price)} vs strike ${fmtUsd(st.strikePrice)} → ${winOutcome}`);

        if (st.activePosition && !st.settling) {
          settleRound();
        }
        st.activePosition = null;
        st.roundId++;
        st.strikePrice = st.price;
        st.priceHistory = [{ price: st.price }];
        st.roundSecondsRemaining = 90;
        addSimLog('info', `ROUND #${st.roundId} OPEN — strike relocked at ${fmtUsd(st.strikePrice)}`);
      }

      setSimPosition(st.activePosition);
      setSimSecondsRemaining(st.roundSecondsRemaining);
      const mins = Math.floor(st.roundSecondsRemaining / 60);
      const secs = st.roundSecondsRemaining % 60;
      setSimCountdown(`${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`);

      if (st.tickCount % 4 === 0) {
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

      setYesBook({ mid: st.yesContract.midPrice, bids: [...st.yesContract.bids], asks: [...st.yesContract.asks] });
      setNoBook({ mid: st.noContract.midPrice, bids: [...st.noContract.bids], asks: [...st.noContract.asks] });

      timer = setTimeout(runStep, 1000 / st.speedMultiplier);
    };

    timer = setTimeout(runStep, 300);

    return () => {
      disposed = true;
      if (timer) clearTimeout(timer);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, simAsset]);

  useEffect(() => {
    if (activeTab !== 'simulator') return;
    const canvas = canvasRef.current;
    const size = () => {
      if (!canvas) return;
      canvas.width = canvas.parentElement?.clientWidth || 600;
      canvas.height = 248;
    };
    size();
    window.addEventListener('resize', size);
    return () => window.removeEventListener('resize', size);
  }, [activeTab]);

  // ---- Slider handlers ----
  const handleSpeedChange = (v: number) => { setSimSpeed(v); simStateRef.current.speedMultiplier = v; };
  const handleSizeChange = (v: number) => { setSimTradeSize(v); simStateRef.current.tradeSizeUsd = v; };
  const handleEdgeChange = (v: number) => { setSimEdgeThreshold(v); simStateRef.current.minEdgeThreshold = v; };
  const handleVolatilityChange = (v: number) => { setSimVolatility(v); simStateRef.current.volatility = v; };
  const handleToggleSimRunning = () => {
    const next = !simRunning;
    setSimRunning(next);
    simStateRef.current.isRunning = next;
  };

  // ---- Cockpit handlers ----
  const handleRefresh = () => { setRefreshing(true); fetchData(); };

  const handleAddConnection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey) return;
    setSubmittingConnection(true);
    setMessage(null);
    try {
      const res = await fetch('/api/dashboard/connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exchange: 'hyperliquid', apiKey }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Failed to add connection');
      setMessage({ type: 'success', text: 'Hyperliquid key encrypted (AES-256-GCM) and vaulted.' });
      setApiKey('');
      await fetchData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Error saving connection' });
    } finally {
      setSubmittingConnection(false);
    }
  };

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
          maxNotional: parseFloat(maxNotional),
        }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Failed to create bot instance');
      setMessage({ type: 'success', text: 'Bot instance deployed and activated.' });
      await fetchData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Error creating instance' });
    } finally {
      setSubmittingInstance(false);
    }
  };

  const handleToggleBotStatus = async (instanceId: string, _current: string, action: 'pause' | 'resume' | 'kill') => {
    setMessage(null);
    let nextStatus = 'active';
    if (action === 'pause') nextStatus = 'paused';
    if (action === 'kill') nextStatus = 'kill_switched';
    try {
      const res = await fetch('/api/dashboard/instances', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ instanceId, status: nextStatus }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Failed to update bot state');
      setMessage({ type: 'success', text: `Bot instance set to ${nextStatus}.` });
      await fetchData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Error updating status' });
    }
  };

  // Live-price webhook simulation — fires at the current Hyperliquid mark.
  const handleSimulateSignal = async (botCode: string, direction: 'LONG' | 'SHORT', assetClass: string) => {
    const feedKey = feedKeyForAssetClass(assetClass);
    const livePrice = feedKey ? prices[feedKey] : undefined;
    if (!livePrice) {
      setMessage({ type: 'error', text: `No live price for ${assetClass} yet — feed still syncing.` });
      return;
    }
    setSimulatingSignal(true);
    setMessage(null);
    try {
      const res = await fetch('/api/dashboard/mock-signal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ botCode, direction, price: livePrice }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Signal execution failed');
      if (json.executions?.some((e: any) => e.status === 'rejected')) {
        const rejection = json.executions.find((e: any) => e.status === 'rejected');
        setMessage({ type: 'error', text: `Signal blocked: ${rejection.reason}` });
      } else {
        setMessage({ type: 'success', text: `${direction} @ ${fmtUsd(livePrice)} executed across ${json.processedInstances} instance(s).` });
      }
      await fetchData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Error simulating webhook' });
    } finally {
      setSimulatingSignal(false);
    }
  };

  const handleExportCsv = () => {
    const headers = ['Round', 'Timestamp (UTC)', 'Asset', 'Strike', 'Expiry', 'Side', 'Qty', 'Entry', 'Exit', 'Outcome', 'Net PnL'];
    const rows = simHistory.map(h => [
      `#${h.roundId}`,
      new Date(h.createdAt).toISOString(),
      h.asset,
      h.strikePrice.toFixed(2),
      h.expiryPrice.toFixed(2),
      h.side,
      h.size,
      h.entryPrice.toFixed(2),
      h.exitPrice.toFixed(2),
      h.outcome,
      `${h.pnl >= 0 ? '+' : ''}${h.pnl.toFixed(2)}`,
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const link = document.createElement('a');
    link.setAttribute('href', encodeURI(csvContent));
    link.setAttribute('download', `predictions_log_${simAsset}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleClearDb = async () => {
    const secret = prompt('Enter admin passcode to clear this asset\'s log:');
    if (!secret) return;
    try {
      const res = await fetch(`/api/dashboard/predictions?secret=${encodeURIComponent(secret)}&asset=${simAsset}`, { method: 'DELETE' });
      const result = await res.json();
      if (res.ok) {
        await loadHistory(simAsset);
        setMessage({ type: 'success', text: 'Predictions log cleared for ' + simAsset });
      } else {
        setMessage({ type: 'error', text: result.error || 'Failed to clear database' });
      }
    } catch (err: any) {
      setMessage({ type: 'error', text: `Request failed: ${err.message}` });
    }
  };

  // -------------------------------------------------------------------------

  if (loading) {
    return (
      <div className="fable">
        <div className="f-loading-shell">
          <RefreshCw className="f-spin" size={34} color="#d9a94e" />
          <span className="f-kicker">Decrypting vault · syncing Hyperliquid L1</span>
        </div>
      </div>
    );
  }

  const feedAge = feedTs ? Math.max(0, Math.round((Date.now() - feedTs) / 1000)) : null;
  const feedLive = !feedError && feedAge !== null && feedAge < 15;

  return (
    <div className="fable">
      <div className="f-shell">

        {/* ---------- Masthead ---------- */}
        <header className="f-masthead">
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <Link href="/" className="f-brand">
              <span className="f-brand-name">Prospera</span>
            </Link>
            <span className="f-brand-rule" />
            <div>
              <div className="f-kicker">AlphaEdge Desk</div>
              <div className="f-serif" style={{ fontSize: 13, color: 'var(--ivory-dim)' }}>the wealth automation ledger</div>
            </div>
          </div>

          <div className="f-tabs">
            <button className={`f-tab ${activeTab === 'cockpit' ? 'active' : ''}`} onClick={() => setActiveTab('cockpit')}>
              Live Cockpit
            </button>
            <button className={`f-tab ${activeTab === 'simulator' ? 'active' : ''}`} onClick={() => setActiveTab('simulator')}>
              Quant Engine
            </button>
          </div>

          <div className="f-masthead-meta">
            <span className={`f-led ${feedLive ? 'ok' : 'bad'}`}>
              {feedLive ? `FEED LIVE · ${feedAge}s` : 'FEED DOWN'}
            </span>
            {data?.ledgerValid ? (
              <span className="f-led warm">LEDGER SEALED</span>
            ) : (
              <span className="f-led bad">LEDGER TAMPERED</span>
            )}
            <span className="f-clock f-mono">{clock} LOCAL</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: 11, color: 'var(--ivory-dim)' }}>{user?.name || user?.email}</span>
              <button className="f-btn" style={{ padding: '4px 10px', fontSize: 9.5 }} onClick={() => handleSignOut()}>
                SIGN OUT
              </button>
            </div>
          </div>
        </header>

        {/* ---------- Wire ribbon ---------- */}
        <div className="f-wire">
          <div className="f-wire-inner">
            {[0, 1].map(dup => (
              <span key={`wire-${dup}`} style={{ display: 'inline' }}>
                {DESK_ASSETS.map(a => {
                  const ctx = contexts[a];
                  return (
                    <span key={`${a}-${dup}`}>
                      {ASSET_LABEL[a].split(' · ')[0]} {fmtUsd(prices[a])}
                      {ctx ? ` (${ctx.change24hPct >= 0 ? '+' : ''}${ctx.change24hPct.toFixed(2)}% 24H · FUNDING ${(ctx.fundingRate * 100).toFixed(4)}% · OI ${fmtCompact(ctx.openInterest)})` : ''}
                    </span>
                  );
                })}
                <span>SOURCE HYPERLIQUID L1 · METAANDASSETCTXS · POLL 2S</span>
                {feedError && <span style={{ color: 'var(--oxide)' }}>FEED ERROR: {feedError}</span>}
              </span>
            ))}
          </div>
        </div>

        {/* ---------- Ticker tape ---------- */}
        <div className="f-tape">
          {DESK_ASSETS.map(asset => {
            const ctx = contexts[asset];
            const price = prices[asset];
            const dir = tickDir[asset];
            return (
              <div
                key={asset}
                className={`f-tape-cell ${activeTab === 'simulator' && simAsset === asset ? 'selected' : ''}`}
                onClick={() => { setSimAsset(asset); setActiveTab('simulator'); }}
                title={`Open ${asset} in Quant Engine`}
              >
                <div className="f-tape-head">
                  <span className="f-kicker">{ASSET_LABEL[asset]}</span>
                  {ctx && (
                    <span className={`f-mono ${ctx.change24hPct >= 0 ? 'f-pos' : 'f-neg'}`} style={{ fontSize: 11, fontWeight: 700 }}>
                      {ctx.change24hPct >= 0 ? '▲' : '▼'} {Math.abs(ctx.change24hPct).toFixed(2)}%
                    </span>
                  )}
                </div>
                <div className={`f-tape-price ${dir === 'up' ? 'tick-up' : dir === 'down' ? 'tick-down' : ''}`}>
                  {price ? fmtUsd(price) : '— syncing —'}
                </div>
                <div className="f-tape-row">
                  <span><b>FUND</b> {ctx ? `${(ctx.fundingRate * 100).toFixed(4)}%` : '—'}</span>
                  <span><b>OI</b> {ctx ? fmtCompact(ctx.openInterest) : '—'}</span>
                  <span><b>VOL24H</b> {ctx ? '$' + fmtCompact(ctx.dayVolumeUsd) : '—'}</span>
                  <span><b>ORACLE</b> {ctx ? fmtUsd(ctx.oracle) : '—'}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* ---------- Message banner ---------- */}
        {message && (
          <div className={`f-banner ${message.type === 'success' ? 'ok' : 'err'}`}>
            {message.type === 'success' ? <Shield size={15} /> : <AlertOctagon size={15} />}
            <span>{message.text}</span>
            <button className="f-btn" style={{ marginLeft: 'auto', padding: '2px 8px', fontSize: 9 }} onClick={() => setMessage(null)}>DISMISS</button>
          </div>
        )}

        {activeTab === 'cockpit' ? (
          <>
            {/* ============ COCKPIT ============ */}
            <div className="f-stat-grid">
              <div className="f-stat">
                <span className="f-kicker">USDC Equity</span>
                <div className="f-stat-value f-gold">{fmtUsd(data?.balances?.equity)}</div>
                <div className="f-stat-sub">Available {fmtUsd(data?.balances?.available)}</div>
              </div>
              <div className="f-stat">
                <span className="f-kicker">Win Rate</span>
                <div className="f-stat-value f-azure">{data?.aiMetrics ? (data.aiMetrics.winRate * 100).toFixed(0) + '%' : '—'}</div>
                <div className="f-stat-sub">Sharpe {data?.aiMetrics?.sharpeRatio?.toFixed(2)}</div>
              </div>
              <div className="f-stat">
                <span className="f-kicker">Est. Profit / 30d</span>
                <div className={`f-stat-value ${(data?.aiMetrics?.totalProfit ?? 0) >= 0 ? 'f-pos' : 'f-neg'}`}>
                  {fmtUsd(data?.aiMetrics?.totalProfit)}
                </div>
                <div className="f-stat-sub">Execution attribution</div>
              </div>
              <div className="f-stat">
                <span className="f-kicker">Active Deployments</span>
                <div className="f-stat-value">{data?.botInstances?.filter((b: any) => b.status === 'active').length ?? 0}</div>
                <div className="f-stat-sub">{data?.botInstances?.length ?? 0} total instances</div>
              </div>
            </div>

            {/* Advisory */}
            <div className="f-panel" style={{ marginBottom: 22 }}>
              <div className="f-panel-head">
                <h2 className="f-panel-title"><Shield size={14} color="#a58fdd" /> <span className="f-serif">Risk Advisory</span></h2>
                <span className="f-tag violet">MODEL PLANE</span>
              </div>
              <p style={{ margin: 0, fontSize: 13, lineHeight: 1.7, color: 'var(--ivory-dim)' }}>{data?.aiMetrics?.advisoryText}</p>
            </div>

            <div className="f-grid-main">
              {/* Left column */}
              <div className="f-col">
                {/* Connect exchange */}
                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Lock size={14} color="#e0706f" /> <span className="f-serif">Connect Hyperliquid</span></h2>
                    <span className="f-tag gold">AES-256-GCM</span>
                  </div>
                  <form onSubmit={handleAddConnection}>
                    <label className="f-label">Hyperliquid API / Private Wallet Key</label>
                    <input
                      type="password"
                      className="f-input"
                      placeholder="wallet address or private key"
                      value={apiKey}
                      onChange={e => setApiKey(e.target.value)}
                      required
                    />
                    <small className="f-help">Keys are encrypted in-memory with AES-256-GCM envelope protection before persistence. Plaintext never touches the ledger.</small>
                    <div style={{ marginTop: 12 }}>
                      <button type="submit" className="f-btn primary" disabled={submittingConnection}>
                        {submittingConnection ? 'VAULTING…' : 'CONNECT EXCHANGE KEY'}
                      </button>
                    </div>
                  </form>

                  {data?.exchangeConnections?.length > 0 && (
                    <>
                      <hr className="f-divider" />
                      <span className="f-kicker">Active Connections</span>
                      <table className="f-table" style={{ marginTop: 8 }}>
                        <tbody>
                          {data.exchangeConnections.map((c: any) => (
                            <tr key={c.id}>
                              <td style={{ color: 'var(--ivory)' }}>{c.exchange.toUpperCase()}</td>
                              <td className="f-faint">IV {c.encryptionTag.substring(0, 8)}…</td>
                              <td className="num"><span className="f-tag win">ACTIVE</span></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </>
                  )}
                </div>

                {/* Deploy instance */}
                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Plus size={14} color="#6fb3e0" /> <span className="f-serif">Deploy Bot Instance</span></h2>
                  </div>
                  <form onSubmit={handleCreateInstance} style={{ display: 'flex', flexDirection: 'column', gap: 13 }}>
                    <div>
                      <label className="f-label">Strategy Template</label>
                      <select className="f-select" value={selectedTemplate} onChange={e => setSelectedTemplate(e.target.value)}>
                        {data?.botTemplates?.map((t: any) => (
                          <option key={t.id} value={t.id}>
                            {t.code} ({t.assetClass}) — {t.status === 'live' ? 'LIVE' : 'ASSAY'}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="f-label">Exchange Key</label>
                      <select className="f-select" value={selectedConnection} onChange={e => setSelectedConnection(e.target.value)}>
                        {data?.exchangeConnections?.length === 0 ? (
                          <option value="">No active exchange key connected</option>
                        ) : (
                          data?.exchangeConnections?.map((c: any) => (
                            <option key={c.id} value={c.id}>{c.exchange.toUpperCase()} ({c.id.substring(0, 8)}…)</option>
                          ))
                        )}
                      </select>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                      <div>
                        <label className="f-label">Risk Ceiling %</label>
                        <input type="number" step="0.1" className="f-input" value={riskCeiling} onChange={e => setRiskCeiling(e.target.value)} required />
                      </div>
                      <div>
                        <label className="f-label">Max Notional ($)</label>
                        <input type="number" className="f-input" value={maxNotional} onChange={e => setMaxNotional(e.target.value)} required />
                      </div>
                    </div>
                    <div>
                      <label className="f-label">Execution Mode</label>
                      <div style={{ display: 'flex', gap: 18, fontSize: 12 }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                          <input type="radio" name="mode" checked={botMode === 'paper'} onChange={() => setBotMode('paper')} style={{ accentColor: '#d9a94e' }} />
                          Paper
                        </label>
                        <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                          <input type="radio" name="mode" checked={botMode === 'live'} onChange={() => setBotMode('live')} style={{ accentColor: '#d9a94e' }} />
                          Live Execution
                        </label>
                      </div>
                    </div>
                    <button type="submit" className="f-btn primary" disabled={submittingInstance || data?.exchangeConnections?.length === 0}>
                      {submittingInstance ? 'DEPLOYING…' : 'DEPLOY ACTIVE BOT'}
                    </button>
                  </form>
                </div>

                {/* Webhook simulator — live prices */}
                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Radio size={14} color="#d9a94e" /> <span className="f-serif">Webhook Signal Desk</span></h2>
                    <span className={`f-led ${feedLive ? 'ok' : 'bad'}`}>{feedLive ? 'MARK SYNCED' : 'AWAITING FEED'}</span>
                  </div>
                  <p style={{ margin: '0 0 12px', fontSize: 11.5, color: 'var(--ivory-faint)', lineHeight: 1.6 }}>
                    Fire a TradingView-style webhook into the dispatcher at the <b style={{ color: 'var(--gold-bright)' }}>live Hyperliquid mark</b> for the template's asset.
                  </p>
                  <table className="f-table">
                    <thead>
                      <tr>
                        <th>Template</th>
                        <th>Status</th>
                        <th className="num">Live Mark</th>
                        <th className="num">Fire</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data?.botTemplates?.map((tmpl: any) => {
                        const feedKey = feedKeyForAssetClass(tmpl.assetClass);
                        const livePrice = feedKey ? prices[feedKey] : undefined;
                        return (
                          <tr key={tmpl.id}>
                            <td style={{ color: 'var(--ivory)' }}>{tmpl.code}</td>
                            <td><span className={`f-tag ${tmpl.status === 'live' ? 'win' : 'gold'}`}>{tmpl.status.toUpperCase()}</span></td>
                            <td className="num f-gold">{livePrice ? fmtUsd(livePrice) : 'syncing…'}</td>
                            <td className="num">
                              <div style={{ display: 'inline-flex', gap: 6 }}>
                                <button className="f-btn long" style={{ padding: '3px 10px', fontSize: 9 }}
                                  disabled={simulatingSignal || !livePrice}
                                  onClick={() => handleSimulateSignal(tmpl.code, 'LONG', tmpl.assetClass)}>
                                  LONG
                                </button>
                                <button className="f-btn short" style={{ padding: '3px 10px', fontSize: 9 }}
                                  disabled={simulatingSignal || !livePrice}
                                  onClick={() => handleSimulateSignal(tmpl.code, 'SHORT', tmpl.assetClass)}>
                                  SHORT
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Right column */}
              <div className="f-col">
                {/* Active bots */}
                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Activity size={14} color="#7fce9b" /> <span className="f-serif">Active Deployments</span></h2>
                    <button className="f-btn" style={{ padding: '3px 10px', fontSize: 9 }} onClick={handleRefresh} disabled={refreshing}>
                      <RefreshCw size={10} className={refreshing ? 'f-spin' : ''} style={{ marginRight: 4, verticalAlign: '-1px' }} />
                      {refreshing ? 'SYNCING' : 'SYNC'}
                    </button>
                  </div>
                  {data?.botInstances?.length === 0 ? (
                    <div className="f-empty">No bot instances deployed — configure one on the left.</div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                      {data.botInstances.map((bot: any) => {
                        const templateCode = data.botTemplates.find((t: any) => t.id === bot.botTemplateId)?.code || 'Unknown';
                        return (
                          <div key={bot.id} style={{ border: '1px solid var(--hairline)', padding: '10px 12px', background: 'var(--ink-0)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                                <span className="f-mono" style={{ fontSize: 12, fontWeight: 700 }}>{templateCode}</span>
                                <span className={`f-tag ${bot.mode === 'live' ? 'loss' : 'dim'}`}>{bot.mode.toUpperCase()}</span>
                              </div>
                              <span className={`f-tag ${bot.status === 'active' ? 'win' : bot.status === 'paused' ? 'gold' : 'loss'}`}>
                                {bot.status.toUpperCase()}
                              </span>
                            </div>
                            <div className="f-mono f-faint" style={{ fontSize: 10.5, display: 'flex', gap: 16 }}>
                              <span>CEILING {bot.riskCeilingPct}%</span>
                              <span>MAX NOTIONAL {fmtUsd(bot.maxNotional, 0)}</span>
                            </div>
                            <div style={{ display: 'flex', gap: 6, marginTop: 9 }}>
                              {bot.status === 'active' && (
                                <button className="f-btn" style={{ padding: '3px 10px', fontSize: 9 }} onClick={() => handleToggleBotStatus(bot.id, bot.status, 'pause')}>
                                  <Pause size={9} style={{ marginRight: 4, verticalAlign: '-1px' }} />PAUSE
                                </button>
                              )}
                              {bot.status === 'paused' && (
                                <button className="f-btn long" style={{ padding: '3px 10px', fontSize: 9 }} onClick={() => handleToggleBotStatus(bot.id, bot.status, 'resume')}>
                                  <Play size={9} style={{ marginRight: 4, verticalAlign: '-1px' }} />RESUME
                                </button>
                              )}
                              {bot.status !== 'kill_switched' && (
                                <button className="f-btn danger" style={{ padding: '3px 10px', fontSize: 9 }} onClick={() => handleToggleBotStatus(bot.id, bot.status, 'kill')}>
                                  <AlertTriangle size={9} style={{ marginRight: 4, verticalAlign: '-1px' }} />KILL
                                </button>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Positions */}
                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Coins size={14} color="#d9a94e" /> <span className="f-serif">Hyperliquid Positions</span></h2>
                  </div>
                  {data?.positions?.length === 0 ? (
                    <div className="f-empty">No open positions currently held.</div>
                  ) : (
                    <table className="f-table">
                      <thead>
                        <tr><th>Coin</th><th className="num">Size</th><th className="num">Entry</th><th className="num">uPnL</th></tr>
                      </thead>
                      <tbody>
                        {data.positions.map((pos: any, idx: number) => (
                          <tr key={idx}>
                            <td style={{ color: 'var(--ivory)' }}>{pos.coin}</td>
                            <td className={`num ${pos.szi >= 0 ? 'f-pos' : 'f-neg'}`}>{pos.szi > 0 ? `+${pos.szi}` : pos.szi}</td>
                            <td className="num">{fmtUsd(pos.entryPx)}</td>
                            <td className={`num ${pos.unrealizedPnl >= 0 ? 'f-pos' : 'f-neg'}`}>{fmtUsd(pos.unrealizedPnl)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>

                {/* Ledger journal */}
                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><FileText size={14} color="#a58fdd" /> <span className="f-serif">Cryptographic Trade Ledger</span></h2>
                    <span className="f-tag gold">HASH-CHAINED</span>
                  </div>
                  <div style={{ maxHeight: 300, overflowY: 'auto' }}>
                    {data?.orders?.length === 0 ? (
                      <div className="f-empty">No historical executions recorded.</div>
                    ) : (
                      <table className="f-table">
                        <thead>
                          <tr><th>Side</th><th>Time</th><th className="num">Qty</th><th className="num">Price</th><th className="num">Status</th></tr>
                        </thead>
                        <tbody>
                          {data.orders.map((ord: any) => (
                            <tr key={ord.id}>
                              <td><span className={`f-tag ${ord.side === 'buy' ? 'win' : 'loss'}`}>{ord.side.toUpperCase()}</span></td>
                              <td className="f-faint">{fmtTime(ord.submittedAt)}</td>
                              <td className="num">{ord.qty.toFixed(4)}</td>
                              <td className="num f-gold">{fmtUsd(ord.price)}</td>
                              <td className="num">
                                <span className={`f-tag ${ord.status === 'filled' ? 'win' : 'dim'}`}>{ord.status.toUpperCase()}</span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                </div>

                {/* Risk audit */}
                {data?.riskEvents?.length > 0 && (
                  <div className="f-panel">
                    <div className="f-panel-head">
                      <h2 className="f-panel-title"><AlertOctagon size={14} color="#e0706f" /> <span className="f-serif">Risk Audit Log</span></h2>
                    </div>
                    <div style={{ maxHeight: 220, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 7 }}>
                      {data.riskEvents.map((evt: any) => (
                        <div key={evt.id} className="f-mono" style={{ fontSize: 10.5, display: 'flex', gap: 10, lineHeight: 1.5 }}>
                          <span className="f-faint" style={{ whiteSpace: 'nowrap' }}>{fmtTime(evt.timestamp)}</span>
                          <span><b className="f-neg">{evt.type.toUpperCase()}</b> <span className="f-dim">{evt.detail}</span></span>
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
            {/* ============ QUANT ENGINE ============ */}

            {/* KPIs from server-verified DB stats */}
            <div className="f-stat-grid">
              <div className="f-stat">
                <span className="f-kicker">Net PnL · {simAsset}</span>
                <div className={`f-stat-value ${(dbStats?.totalPnl ?? 0) >= 0 ? 'f-pos' : 'f-neg'}`}>
                  {dbStats ? fmtSignedUsd(dbStats.totalPnl) : '—'}
                </div>
                <div className="f-stat-sub">DB-verified · {dbStats?.settled ?? 0} settled rounds</div>
              </div>
              <div className="f-stat">
                <span className="f-kicker">Hit Rate</span>
                <div className="f-stat-value f-azure">{dbStats ? dbStats.hitRate.toFixed(1) + '%' : '—'}</div>
                <div className="f-stat-sub">{dbStats?.wins ?? 0} W / {dbStats?.losses ?? 0} L</div>
              </div>
              <div className="f-stat">
                <span className="f-kicker">Expectancy / Round</span>
                <div className={`f-stat-value ${(dbStats?.expectancy ?? 0) >= 0 ? 'f-pos' : 'f-neg'}`}>
                  {dbStats ? fmtUsd(dbStats.expectancy) : '—'}
                </div>
                <div className="f-stat-sub">Profit factor {dbStats?.profitFactor === Infinity ? '∞' : dbStats?.profitFactor ?? '—'}</div>
              </div>
              <div className="f-stat">
                <span className="f-kicker">Volume Deployed</span>
                <div className="f-stat-value f-gold">{dbStats ? '$' + fmtCompact(dbStats.totalVolume) : '—'}</div>
                <div className="f-stat-sub">Cumulative contract cost</div>
              </div>
              <div className="f-stat">
                <span className="f-kicker">Active Position</span>
                <div className="f-stat-value" style={{ color: simPosition ? 'var(--sage)' : 'var(--ivory-faint)' }}>
                  {simPosition ? `${simPosition.side} ${simPosition.size.toLocaleString()}` : 'FLAT'}
                </div>
                <div className="f-stat-sub">
                  {simPosition ? `Entry ${Math.round(simPosition.entryPrice * 100)}¢ · cost ${fmtUsd(simPosition.costUsd)}` : 'No contracts held'}
                </div>
              </div>
            </div>

            {/* Pipeline strip */}
            <div className="f-panel" style={{ marginBottom: 22 }}>
              <div className="f-panel-head">
                <h2 className="f-panel-title"><Activity size={14} color="#6fb3e0" /> <span className="f-serif">Strategy Pipeline</span> <span className="f-kicker" style={{ marginLeft: 6 }}>ENGLISH → DEPLOYED</span></h2>
                <span className="f-mono f-gold" style={{ fontSize: 13, fontWeight: 700 }}>{simCountdown}</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 6 }}>
                {pipelineSteps.map(step => {
                  const activeStepId = getActiveStepId(simSecondsRemaining);
                  const isActive = activeStepId === step.id;
                  const isPast = activeStepId > step.id;
                  return (
                    <div key={step.id} style={{
                      border: `1px solid ${isActive ? 'var(--gold)' : isPast ? 'rgba(127, 206, 155, 0.4)' : 'var(--hairline)'}`,
                      background: isActive ? 'rgba(217, 169, 78, 0.1)' : isPast ? 'rgba(127, 206, 155, 0.05)' : 'transparent',
                      padding: '9px 6px',
                      textAlign: 'center',
                      transition: 'all 300ms ease',
                    }}>
                      <div className="f-kicker" style={{ marginBottom: 3 }}>0{step.id}</div>
                      <div className="f-mono" style={{
                        fontSize: 11, fontWeight: 700,
                        color: isActive ? 'var(--gold-bright)' : isPast ? 'var(--sage)' : 'var(--ivory-faint)',
                      }}>{step.name}</div>
                    </div>
                  );
                })}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--hairline)', flexWrap: 'wrap', gap: 10 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span className="f-kicker" style={{ color: 'var(--oxide)' }}>Hypothesis</span>
                  <span className="f-serif" style={{ fontSize: 13, color: 'var(--ivory-dim)' }}>
                    "{hypotheses[simStateRef.current.roundId % hypotheses.length]}"
                  </span>
                </div>
                <div className="f-mono" style={{ display: 'flex', gap: 12, fontSize: 10 }}>
                  {['Generator', 'Coder', 'Challenger', 'Evaluator'].map((role, i) => {
                    const stepId = getActiveStepId(simSecondsRemaining);
                    const active = (i === 0 && stepId <= 2) || (i === 1 && stepId === 3) || (i === 2 && stepId === 4) || (i === 3 && stepId >= 5);
                    return (
                      <span key={role} style={{ color: active ? 'var(--gold-bright)' : 'var(--ivory-faint)', fontWeight: active ? 700 : 400 }}>
                        {role}{i < 3 ? ' →' : ''}
                      </span>
                    );
                  })}
                </div>
              </div>
            </div>

            <div className="f-grid-main">
              {/* Left: chart + matrix */}
              <div className="f-col">
                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title">
                      <TrendingUp size={14} color="#6fb3e0" />
                      <span className="f-serif">{ASSET_LABEL[simAsset]}</span>
                      <span className="f-kicker" style={{ marginLeft: 4 }}>90S BINARY ROUND</span>
                    </h2>
                    <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                      <select className="f-select" style={{ width: 'auto', padding: '4px 8px', fontSize: 11 }}
                        value={simAsset} onChange={e => setSimAsset(e.target.value as DeskAsset)}>
                        {DESK_ASSETS.map(a => <option key={a} value={a}>{a}</option>)}
                      </select>
                      <button className="f-btn" style={{ padding: '4px 10px', fontSize: 9.5 }} onClick={handleToggleSimRunning}>
                        {simRunning ? 'PAUSE ENGINE' : 'RESUME ENGINE'}
                      </button>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: 26, marginBottom: 12, flexWrap: 'wrap' }}>
                    <div>
                      <span className="f-kicker">Strike (T₀)</span>
                      <div className="f-mono f-gold" style={{ fontSize: 15, fontWeight: 700, marginTop: 2 }}>
                        {simStateRef.current.strikeLocked ? fmtUsd(simStateRef.current.strikePrice) : 'awaiting feed'}
                      </div>
                    </div>
                    <div>
                      <span className="f-kicker">Live Mark</span>
                      <div className="f-mono f-azure" style={{ fontSize: 15, fontWeight: 700, marginTop: 2 }}>
                        {prices[simAsset] ? fmtUsd(prices[simAsset]) : '—'}
                      </div>
                    </div>
                    <div>
                      <span className="f-kicker">Deviation</span>
                      <div className={`f-mono ${simStateRef.current.price >= simStateRef.current.strikePrice ? 'f-pos' : 'f-neg'}`}
                        style={{ fontSize: 15, fontWeight: 700, marginTop: 2 }}>
                        {simStateRef.current.strikeLocked && simStateRef.current.strikePrice > 0
                          ? `${simStateRef.current.price >= simStateRef.current.strikePrice ? '+' : ''}${((simStateRef.current.price - simStateRef.current.strikePrice) / simStateRef.current.strikePrice * 100).toFixed(4)}%`
                          : '—'}
                      </div>
                    </div>
                    <div>
                      <span className="f-kicker">Round Clock</span>
                      <div className="f-mono" style={{ fontSize: 15, fontWeight: 700, marginTop: 2, color: 'var(--oxide)' }}>{simCountdown}</div>
                    </div>
                  </div>

                  <div className="f-chart-frame">
                    <canvas ref={canvasRef} style={{ width: '100%', height: '100%' }} />
                  </div>
                </div>

                {/* Model readout — real quant telemetry */}
                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Scale size={14} color="#a58fdd" /> <span className="f-serif">Model Readout</span> <span className="f-kicker" style={{ marginLeft: 4 }}>GBM BINARY PRICER</span></h2>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 14 }}>
                    <div>
                      <span className="f-kicker">P(YES) Model</span>
                      <div className="f-mono f-violet" style={{ fontSize: 19, fontWeight: 700 }}>{modelReadout ? Math.round(modelReadout.pYes * 100) + '¢' : '—'}</div>
                    </div>
                    <div>
                      <span className="f-kicker">Z-Score</span>
                      <div className="f-mono" style={{ fontSize: 19, fontWeight: 700 }}>{modelReadout ? modelReadout.z.toFixed(3) : '—'}</div>
                    </div>
                    <div>
                      <span className="f-kicker">σ (USD, remaining)</span>
                      <div className="f-mono" style={{ fontSize: 19, fontWeight: 700 }}>{modelReadout ? fmtUsd(modelReadout.sigmaUsd) : '—'}</div>
                    </div>
                    <div>
                      <span className="f-kicker">Market YES Mid</span>
                      <div className="f-mono f-azure" style={{ fontSize: 19, fontWeight: 700 }}>{Math.round(yesBook.mid * 100)}¢</div>
                    </div>
                    <div>
                      <span className="f-kicker">Model Edge</span>
                      <div className={`f-mono ${modelReadout && (modelReadout.pYes - yesBook.mid) >= 0 ? 'f-pos' : 'f-neg'}`} style={{ fontSize: 19, fontWeight: 700 }}>
                        {modelReadout ? `${((modelReadout.pYes - yesBook.mid) * 100).toFixed(1)}%` : '—'}
                      </div>
                    </div>
                    <div>
                      <span className="f-kicker">Ann. Vol Input</span>
                      <div className="f-mono f-gold" style={{ fontSize: 19, fontWeight: 700 }}>{simVolatility}%</div>
                    </div>
                  </div>
                </div>

                {/* Robustness matrix — desk assets only */}
                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Activity size={14} color="#a58fdd" /> <span className="f-serif">Robustness Matrix</span> <span className="f-kicker" style={{ marginLeft: 4 }}>RETURNS × TIMEFRAME</span></h2>
                  </div>
                  <div style={{ overflowX: 'auto' }}>
                    <table className="f-table" style={{ textAlign: 'center' }}>
                      <thead>
                        <tr>
                          <th>Asset</th><th className="num">5M</th><th className="num">15M</th><th className="num">30M</th>
                          <th className="num">1H</th><th className="num">4H</th><th className="num">1D</th><th className="num">AVG</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.keys(robustnessData).map(asset => {
                          const values = robustnessData[asset];
                          const avg = values.reduce((a, b) => a + b, 0) / values.length;
                          return (
                            <tr key={asset}>
                              <td style={{ color: 'var(--ivory)', fontWeight: 700 }}>{asset}</td>
                              {values.map((v, i) => (
                                <td key={i} className={`num ${v < 0 ? 'f-neg' : 'f-pos'}`}
                                  style={{ background: v < 0 ? `rgba(224, 112, 111, ${Math.min(0.22, Math.abs(v) / 30)})` : `rgba(127, 206, 155, ${Math.min(0.22, v / 30)})` }}>
                                  {v >= 0 ? '+' : ''}{v.toFixed(1)}%
                                </td>
                              ))}
                              <td className={`num ${avg >= 0 ? 'f-pos' : 'f-neg'}`} style={{ fontWeight: 700 }}>
                                {avg >= 0 ? '+' : ''}{avg.toFixed(1)}%
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              {/* Right: config, books, console */}
              <div className="f-col">
                {/* Engine config */}
                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Lock size={14} color="#d9a94e" /> <span className="f-serif">Engine Configuration</span></h2>
                    <span className={`f-led ${simRunning ? 'ok' : 'warm'}`}>{simRunning ? 'RUNNING' : 'PAUSED'}</span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    {[
                      { label: 'Simulation Speed', value: `${simSpeed}×`, min: 1, max: 20, step: 1, cur: simSpeed, onChange: handleSpeedChange },
                      { label: 'Trade Size per Round', value: `$${simTradeSize.toLocaleString()}`, min: 100, max: 5000, step: 100, cur: simTradeSize, onChange: handleSizeChange },
                      { label: 'Min Executable Edge', value: `${simEdgeThreshold}%`, min: 0.5, max: 10, step: 0.5, cur: simEdgeThreshold, onChange: handleEdgeChange },
                      { label: 'Annualized Vol Input', value: `${simVolatility}%`, min: 10, max: 150, step: 5, cur: simVolatility, onChange: handleVolatilityChange },
                    ].map(s => (
                      <div key={s.label}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                          <span className="f-kicker">{s.label}</span>
                          <span className="f-mono f-gold" style={{ fontSize: 11, fontWeight: 700 }}>{s.value}</span>
                        </div>
                        <input type="range" className="f-slider" min={s.min} max={s.max} step={s.step}
                          value={s.cur} onChange={e => s.onChange(parseFloat(e.target.value))} />
                      </div>
                    ))}
                  </div>
                </div>

                {/* Order books */}
                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Coins size={14} color="#6fb3e0" /> <span className="f-serif">Round Contract Book</span> <span className="f-kicker" style={{ marginLeft: 4 }}>SYNTHETIC CLOB</span></h2>
                  </div>
                  {[
                    { name: 'YES · SETTLES ABOVE STRIKE', book: yesBook, color: 'var(--sage)' },
                    { name: 'NO · SETTLES AT/BELOW STRIKE', book: noBook, color: 'var(--oxide)' },
                  ].map(({ name, book, color }) => (
                    <div key={name} style={{ border: '1px solid var(--hairline)', background: 'var(--ink-0)', padding: '10px 12px', marginBottom: 10 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 7 }}>
                        <span className="f-kicker">{name}</span>
                        <span className="f-mono" style={{ color, fontSize: 12, fontWeight: 700 }}>{Math.round(book.mid * 100)}¢</span>
                      </div>
                      <table className="f-table" style={{ fontSize: 10 }}>
                        <thead>
                          <tr><th className="num">Size</th><th className="num">Ask</th><th>Bid</th><th>Size</th></tr>
                        </thead>
                        <tbody>
                          {book.asks.slice(0, 3).reverse().map((ask: any, idx: number) => (
                            <tr key={idx}>
                              <td className="num f-faint">{ask.size}</td>
                              <td className="num f-neg" style={{ fontWeight: 700 }}>{Math.round(ask.price * 100)}¢</td>
                              <td className="f-pos" style={{ fontWeight: 700 }}>{book.bids[idx] ? Math.round(book.bids[idx].price * 100) + '¢' : '—'}</td>
                              <td className="f-faint">{book.bids[idx]?.size ?? '—'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ))}
                </div>

                {/* Console */}
                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><FileText size={14} color="#a58fdd" /> <span className="f-serif">Engine Telemetry</span></h2>
                    <button className="f-btn" style={{ padding: '3px 10px', fontSize: 9 }} onClick={() => setSimLogs([])}>CLEAR</button>
                  </div>
                  <div className="f-console">
                    {simLogs.length === 0 ? (
                      <span className="f-faint">Awaiting engine telemetry…</span>
                    ) : (
                      simLogs.map((log, idx) => {
                        let color = 'var(--ivory)';
                        if (log.type === 'signal') color = 'var(--azure)';
                        if (log.type === 'edge') color = 'var(--violet)';
                        if (log.type === 'trade') color = 'var(--sage)';
                        if (log.type === 'error') color = 'var(--oxide)';
                        if (log.type === 'settle') color = 'var(--gold-bright)';
                        return (
                          <div key={idx}>
                            <span className="f-faint">[{log.time}]</span>{' '}
                            <span style={{ color, fontWeight: 700 }}>[{log.type.toUpperCase()}]</span>{' '}
                            <span className="f-dim">{log.msg}</span>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Historical predictions — server-verified */}
            <div className="f-section-head">
              <span className="f-serif">Historical Predictions Log</span>
              <span className="f-tag gold">SERVER-VERIFIED</span>
            </div>
            <div className="f-panel">
              <div className="f-panel-head">
                <div className="f-mono f-faint" style={{ fontSize: 10 }}>
                  {dbStats ? `${dbStats.settled} settled · hit rate ${dbStats.hitRate.toFixed(1)}% · expectancy ${fmtUsd(dbStats.expectancy)}/round` : 'Loading…'}
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="f-btn" style={{ padding: '4px 12px', fontSize: 9.5 }} onClick={handleExportCsv} disabled={simHistory.length === 0}>
                    EXPORT CSV
                  </button>
                  <button className="f-btn danger" style={{ padding: '4px 12px', fontSize: 9.5 }} onClick={handleClearDb}>
                    CLEAR LOG
                  </button>
                </div>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table className="f-table">
                  <thead>
                    <tr>
                      <th>Round</th>
                      <th>Settled At</th>
                      <th className="num">Strike</th>
                      <th className="num">Expiry</th>
                      <th>Side</th>
                      <th className="num">Qty</th>
                      <th className="num">Entry</th>
                      <th className="num">Exit</th>
                      <th>Outcome</th>
                      <th className="num">Net PnL</th>
                    </tr>
                  </thead>
                  <tbody>
                    {simHistory.length === 0 ? (
                      <tr><td colSpan={10}><div className="f-empty">No settled rounds recorded yet — engine writes here after each round expiry.</div></td></tr>
                    ) : (
                      simHistory.map((trade: any) => (
                        <tr key={trade.id || `${trade.asset}-${trade.roundId}-${trade.createdAt}`}>
                          <td style={{ color: 'var(--ivory)' }}>#{trade.roundId}</td>
                          <td className="f-faint">{fmtTime(trade.createdAt)}</td>
                          <td className="num f-gold">{fmtUsd(trade.strikePrice)}</td>
                          <td className="num f-azure">{fmtUsd(trade.expiryPrice)}</td>
                          <td><span className={`f-tag ${trade.side === 'YES' ? 'win' : 'loss'}`}>{trade.side}</span></td>
                          <td className="num">{trade.size.toLocaleString()}</td>
                          <td className="num">{Math.round(trade.entryPrice * 100)}¢</td>
                          <td className="num">{Math.round(trade.exitPrice * 100)}¢</td>
                          <td><span className={`f-tag ${trade.outcome === 'WIN' ? 'win' : 'loss'}`}>{trade.outcome}</span></td>
                          <td className={`num ${trade.pnl >= 0 ? 'f-pos' : 'f-neg'}`} style={{ fontWeight: 700 }}>
                            {fmtSignedUsd(trade.pnl)}
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

        {/* Footer colophon */}
        <div style={{ marginTop: 34, paddingTop: 14, borderTop: '1px solid var(--hairline)', display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
          <span className="f-kicker">Prospera · AlphaEdge Desk · XAU / BTC / ETH</span>
          <span className="f-kicker">Feed: Hyperliquid L1 · Ledger: hash-chained · Predictions: server-verified</span>
        </div>
      </div>
    </div>
  );
}
