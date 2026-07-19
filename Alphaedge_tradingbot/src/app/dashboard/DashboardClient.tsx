'use client';

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import Link from 'next/link';
import './dashboard.css';

import {
  Shield,
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
  Network,
  Waves,
  Grid3x3,
  CandlestickChart,
  Dices,
} from 'lucide-react';

import { handleSignOut } from '@/app/auth-actions';

// ---------------------------------------------------------------------------
// Model math (all readouts derive from these — no invented numbers)
// ---------------------------------------------------------------------------

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

function binaryFairValue(price: number, strike: number, annualVolPct: number, secondsRemaining: number) {
  const sigmaUsd = price * (annualVolPct / 100) * Math.sqrt(Math.max(secondsRemaining, 0.001) / SECONDS_PER_YEAR);
  const z = (price - strike) / Math.max(sigmaUsd, 1e-9);
  return { pYes: Math.min(Math.max(normCDF(z), 0.01), 0.99), z, sigmaUsd };
}

function std(xs: number[]) {
  if (xs.length < 2) return 0;
  const m = xs.reduce((a, b) => a + b, 0) / xs.length;
  return Math.sqrt(xs.reduce((a, b) => a + (b - m) ** 2, 0) / (xs.length - 1));
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

function feedKeyForAssetClass(assetClass: string): DeskAsset | null {
  const a = (assetClass || '').toUpperCase();
  if (a.startsWith('BTC')) return 'BTC-PERP';
  if (a.startsWith('ETH')) return 'ETH-PERP';
  if (a.startsWith('XAU') || a.startsWith('GOLD') || a.startsWith('PAXG')) return 'XAU';
  return null;
}

const CYCLE_STEPS = ['Scan', 'Detect', 'Validate', 'Size', 'Fill', 'Settle'];
const DEFAULT_ROUND_S = 300;

const cycleStep = (sec: number, total: number) => {
  const f = sec / Math.max(total, 1);
  if (f > 0.83) return 0;
  if (f > 0.66) return 1;
  if (f > 0.5) return 2;
  if (f > 0.33) return 3;
  if (f > 0.13) return 4;
  return 5;
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

function levelLabel(l: number | undefined) {
  return l === 4 ? 'DEMO' : `LEVEL ${l ?? '—'}`;
}

function fmtTime(epochMs: number) {
  if (!Number.isFinite(epochMs)) return '—';
  return new Date(epochMs).toLocaleString(undefined, {
    month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
  });
}

// Canvas palette (matches dashboard.css tokens)
const C = {
  azure: '#58f0ff', lime: '#bfff6a', rose: '#ff6fb3', violet: '#9d7dff', amber: '#ffd166',
  grid: 'rgba(255,255,255,0.05)', faint: 'rgba(239,246,255,0.4)',
};

function fitCanvas(canvas: HTMLCanvasElement | null, height: number) {
  if (!canvas) return null;
  const w = canvas.parentElement?.clientWidth || 600;
  if (canvas.width !== w || canvas.height !== height) {
    canvas.width = w;
    canvas.height = height;
  }
  return canvas.getContext('2d');
}

// Circular quota gauge: ring fills with usage; red when the day's quota is
// spent; unlimited tiers show a decorative sliver with the infinity mark.
function QuotaRing({ used, limit }: { used: number | undefined; limit: number | null | undefined }) {
  const R = 30, C = 2 * Math.PI * R;
  const unlimited = limit === null;
  const pct = used === undefined ? 0 : unlimited ? 0.1 : Math.min(1, used / (limit as number));
  const exhausted = !unlimited && limit !== undefined && used !== undefined && used >= (limit as number);
  // Green = day's quota fully captured (completed); blue + soft blur = ongoing
  const stroke = exhausted ? '#bfff6a' : '#58f0ff';
  return (
    <div style={{ position: 'relative', width: 76, height: 76, flexShrink: 0 }}>
      <svg width="76" height="76" viewBox="0 0 76 76" style={{ transform: 'rotate(-90deg)' }}>
        <circle cx="38" cy="38" r={R} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="6" />
        <circle cx="38" cy="38" r={R} fill="none" stroke={stroke} strokeWidth="6" strokeLinecap="round"
          strokeDasharray={`${pct * C} ${C}`}
          style={{ transition: 'stroke-dasharray 500ms ease, stroke 300ms ease', filter: `drop-shadow(0 0 ${exhausted ? 5 : 10}px ${stroke})` }} />
      </svg>
      <div style={{
        position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', lineHeight: 1.15,
      }}>
        <span className="f-mono" style={{ fontSize: 15, fontWeight: 700 }}>{used ?? '—'}</span>
        <span className="f-mono" style={{ fontSize: 8.5, color: 'var(--ivory-faint)', letterSpacing: '0.08em' }}>
          / {unlimited ? '∞' : limit ?? '—'}
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------

export default function DashboardClient({ user, isOwner }: { user: any; isOwner: boolean }) {
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
  const [adminUsers, setAdminUsers] = useState<Array<any>>([]);
  const [ledgerScope, setLedgerScope] = useState<'demo' | 'archive'>('demo');
  const ledgerScopeRef = useRef<'demo' | 'archive'>('demo');
  const [levelView, setLevelView] = useState<1 | 2 | 3 | 4>(4);
  const levelViewRef = useRef<1 | 2 | 3 | 4>(4);
  const [logAllLevels, setLogAllLevels] = useState(false);
  const logAllLevelsRef = useRef(false);
  const [simAsset, setSimAsset] = useState<DeskAsset>('BTC-PERP');
  const [clock, setClock] = useState('');

  // ---- Live feed state ----
  const [prices, setPrices] = useState<Record<string, number>>({});
  const [contexts, setContexts] = useState<Record<string, FeedContext>>({});
  const [tickDir, setTickDir] = useState<Record<string, 'up' | 'down' | null>>({});
  const [feedError, setFeedError] = useState<string | null>(null);
  const [feedTs, setFeedTs] = useState<number>(0);
  const pricesRef = useRef<Record<string, number>>({});
  const contextsRef = useRef<Record<string, FeedContext>>({});
  const feedTsRef = useRef<number>(0);

  // ---- Market candle history (real Hyperliquid candles, 60s poll) ----
  const [markets, setMarkets] = useState<any>(null);
  const marketsRef = useRef<any>(null);

  // ---- Canonical server engine state (3s poll; every poll also ticks the engine) ----
  const [engineState, setEngineState] = useState<any>(null);
  const engineStateRef = useRef<any>(null);
  const prevRoundsRef = useRef<Record<string, any>>({});

  // ---- Simulator state ----
  const [dbStats, setDbStats] = useState<any>(null);
  const [simHistory, setSimHistory] = useState<Array<any>>([]);
  const [simLogs, setSimLogs] = useState<Array<{ time: string; type: string; msg: string }>>([]);
  const [simCountdown, setSimCountdown] = useState('05:00');
  const [simSecondsRemaining, setSimSecondsRemaining] = useState(DEFAULT_ROUND_S);
  const [simPosition, setSimPosition] = useState<any>(null);
  const [modelReadout, setModelReadout] = useState<{ pYes: number; z: number; sigmaUsd: number } | null>(null);
  const [regimeReadout, setRegimeReadout] = useState<{ trend: number; chop: number; panic: number } | null>(null);
  const [yesBook, setYesBook] = useState<any>({ mid: 0.5, bids: [], asks: [] });
  const [noBook, setNoBook] = useState<any>({ mid: 0.5, bids: [], asks: [] });

  const [simSpeed, setSimSpeed] = useState(1);
  const [simVolatility, setSimVolatility] = useState(45);
  const [simRunning, setSimRunning] = useState(true);

  const roundCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const meshCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const regimeCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const envelopeCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const equityCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const hitrateCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const candleCanvasRef = useRef<HTMLCanvasElement | null>(null);

  const simStateRef = useRef({
    isRunning: true,
    speedMultiplier: 1,
    volatility: 45,
    asset: 'BTC-PERP' as DeskAsset,
    price: 0,
    strikePrice: 0,
    strikeLocked: false,
    priceHistory: [] as Array<{ price: number; trade?: 'YES' | 'NO' }>,
    pYesHistory: [] as Array<{ p: number; lo: number; hi: number }>,
    roundSeconds: DEFAULT_ROUND_S,
    roundSecondsRemaining: DEFAULT_ROUND_S,
    roundId: 101,
    tickCount: 0,
    yesContract: { midPrice: 0.5, bids: [] as any[], asks: [] as any[] },
    noContract: { midPrice: 0.5, bids: [] as any[], asks: [] as any[] },
    laggedFairValueYes: 0.5,
    activePosition: null as any,
    settling: false,
    staleWarned: false,
    // regime engine buffers (built from live 2s feed samples)
    feedBuf: [] as Array<{ t: number; p: number }>,
    regimeHist: [] as Array<{ trend: number; chop: number; panic: number }>,
  });

  // ---- Wall clock ----
  useEffect(() => {
    const t = setInterval(() => setClock(new Date().toLocaleTimeString(undefined, { hour12: false })), 1000);
    return () => clearInterval(t);
  }, []);

  // ---- Live price feed (2s poll) ----
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
          contextsRef.current = json.contexts || {};
          feedTsRef.current = json.ts || Date.now();
          const st = simStateRef.current;
          if (json.prices[st.asset]) {
            st.price = json.prices[st.asset];
            st.staleWarned = false;
            // feed the regime buffer with the real sample
            st.feedBuf.push({ t: Date.now(), p: json.prices[st.asset] });
            if (st.feedBuf.length > 300) st.feedBuf.shift();
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
    // Browsers throttle timers in background tabs (down to 1/min) — force an
    // instant resync the moment the tab is foregrounded so prices are never stale.
    const onVisible = () => { if (document.visibilityState === 'visible') syncPrices(); };
    document.addEventListener('visibilitychange', onVisible);
    return () => { cancelled = true; clearInterval(interval); document.removeEventListener('visibilitychange', onVisible); };
  }, []);

  // ---- Market candle history (60s poll) ----
  useEffect(() => {
    let cancelled = false;
    async function syncMarkets() {
      try {
        const res = await fetch('/api/dashboard/markets');
        const json = await res.json();
        if (!cancelled && json?.success) {
          setMarkets(json);
          marketsRef.current = json;
        }
      } catch { /* transient — next poll retries */ }
    }
    syncMarkets();
    const interval = setInterval(syncMarkets, 60_000);
    const onVisible = () => { if (document.visibilityState === 'visible') syncMarkets(); };
    document.addEventListener('visibilitychange', onVisible);
    return () => { cancelled = true; clearInterval(interval); document.removeEventListener('visibilitychange', onVisible); };
  }, []);


  // ---- Predictions history (server-verified, Turso-backed) ----
  const loadHistory = useCallback(async (asset: string) => {
    try {
      const scope = ledgerScopeRef.current;
      const lvl = logAllLevelsRef.current ? 'all' : String(levelViewRef.current);
      const res = await fetch(`/api/dashboard/predictions?asset=${encodeURIComponent(asset)}&scope=${scope}&level=${lvl}`);
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

  // ---- Canonical engine sync: the server trades; viewers observe ----
  const pushEngineLog = useCallback((type: string, msg: string) => {
    const time = new Date().toLocaleTimeString(undefined, { hour12: false });
    setSimLogs(prev => {
      const updated = [...prev, { time, type, msg }];
      if (updated.length > 60) updated.shift();
      return updated;
    });
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function syncEngine() {
      try {
        const res = await fetch('/api/engine/state');
        const json = await res.json();
        if (cancelled || !json?.success) return;
        setEngineState(json);
        engineStateRef.current = json;

        // Telemetry from canonical transitions
        for (const round of json.rounds || []) {
          const prev = prevRoundsRef.current[round.id];
          if (!prev) {
            pushEngineLog('info', `ROUND #${round.epoch} OPEN — ${round.asset} strike locked at ${fmtUsd(round.strikePrice)} (server engine)`);
          } else if (!prev.side && round.side) {
            pushEngineLog('trade', `ENGINE ENTRY — ${round.asset} ${round.side} ${round.size?.toLocaleString()} @ ${Math.round((round.entryPrice || 0) * 100)}¢`);
            const st = simStateRef.current;
            if (round.asset === st.asset && st.priceHistory.length) {
              st.priceHistory[st.priceHistory.length - 1].trade = round.side;
            }
          }
          prevRoundsRef.current[round.id] = round;
        }
        if (json.settledThisTick > 0) {
          pushEngineLog('settle', `${json.settledThisTick} round(s) settled server-side — ledger updated`);
          loadHistory(simStateRef.current.asset);
        }

        // Current-asset position display comes from the canonical round
        const cur = (json.rounds || []).find((r: any) => r.asset === simStateRef.current.asset && r.status === 'open');
        let lvlSize = 0;
        if (cur?.side) {
          try { lvlSize = JSON.parse(cur.levelSizes || '{}')[String(levelViewRef.current)] || 0; } catch { lvlSize = cur.size || 0; }
        }
        setSimPosition(cur?.side && lvlSize > 0 ? {
          side: cur.side,
          size: lvlSize,
          entryPrice: cur.entryPrice,
          costUsd: lvlSize * (cur.entryPrice || 0),
        } : null);
      } catch { /* transient — next poll retries */ }
    }
    syncEngine();
    const interval = setInterval(syncEngine, 3000);
    const onVisible = () => { if (document.visibilityState === 'visible') syncEngine(); };
    document.addEventListener('visibilitychange', onVisible);
    return () => { cancelled = true; clearInterval(interval); document.removeEventListener('visibilitychange', onVisible); };
  }, [pushEngineLog, loadHistory]);

  // ---- Cockpit data ----
  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(`/api/dashboard/info?level=${levelViewRef.current}`);
      if (!res.ok) throw new Error('Failed to fetch dashboard data');
      const json = await res.json();
      setData(json);
      if (json.botTemplates?.length > 0) setSelectedTemplate(prev => prev || json.botTemplates[0].id);
      if (json.exchangeConnections?.length > 0) setSelectedConnection(prev => prev || json.exchangeConnections[0].id);
    } catch (err: any) {
      console.error(err);
      setMessage({ type: 'error', text: err.message || 'Error loading dashboard' });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60_000); // keep cockpit metrics fresh
    return () => clearInterval(interval);
  }, [fetchData]);

  // -------------------------------------------------------------------------
  // DB-derived series — equity curve, rolling hit rate, Markov transition
  // matrix, Monte Carlo bootstrap. All computed from the persisted,
  // server-verified round history in Turso.
  // -------------------------------------------------------------------------

  const chrono = useMemo(() => [...simHistory].sort((a, b) => a.createdAt - b.createdAt), [simHistory]);

  const equitySeries = useMemo(() => {
    let cum = 0;
    return chrono.map(h => { cum += h.pnl; return cum; });
  }, [chrono]);

  const hitrateSeries = useMemo(() => {
    const win = 20;
    const out: number[] = [];
    for (let i = 0; i < chrono.length; i++) {
      const slice = chrono.slice(Math.max(0, i - win + 1), i + 1);
      const wins = slice.filter(h => h.outcome === 'WIN').length;
      out.push((wins / slice.length) * 100);
    }
    return out;
  }, [chrono]);

  const transitionMatrix = useMemo(() => {
    const counts = { WW: 0, WL: 0, LW: 0, LL: 0 };
    for (let i = 1; i < chrono.length; i++) {
      const prev = chrono[i - 1].outcome === 'WIN' ? 'W' : 'L';
      const cur = chrono[i].outcome === 'WIN' ? 'W' : 'L';
      counts[(prev + cur) as keyof typeof counts]++;
    }
    const wTotal = counts.WW + counts.WL;
    const lTotal = counts.LW + counts.LL;
    return {
      counts,
      pWW: wTotal ? counts.WW / wTotal : null,
      pWL: wTotal ? counts.WL / wTotal : null,
      pLW: lTotal ? counts.LW / lTotal : null,
      pLL: lTotal ? counts.LL / lTotal : null,
      transitions: chrono.length > 1 ? chrono.length - 1 : 0,
    };
  }, [chrono]);

  const bootstrap = useMemo(() => {
    // Monte Carlo: 10,000 paths resampled from the REAL settled per-round PnLs
    const pnls = chrono.map(h => h.pnl);
    if (pnls.length < 5) return null;
    const PATHS = 10_000;
    const HORIZON = Math.min(60, pnls.length * 2);
    const terminals: number[] = new Array(PATHS);
    let ddSum = 0;
    for (let p = 0; p < PATHS; p++) {
      let cum = 0, peak = 0, maxDD = 0;
      for (let s = 0; s < HORIZON; s++) {
        cum += pnls[(Math.random() * pnls.length) | 0];
        if (cum > peak) peak = cum;
        const dd = peak - cum;
        if (dd > maxDD) maxDD = dd;
      }
      terminals[p] = cum;
      ddSum += maxDD;
    }
    terminals.sort((a, b) => a - b);
    const q = (f: number) => terminals[Math.min(PATHS - 1, Math.max(0, Math.floor(f * PATHS)))];
    const lo = terminals[0], hi = terminals[PATHS - 1];
    const BINS = 24;
    const bins = new Array(BINS).fill(0);
    const span = Math.max(hi - lo, 1e-9);
    for (const t of terminals) bins[Math.min(BINS - 1, Math.floor(((t - lo) / span) * BINS))]++;
    const maxBin = Math.max(...bins);
    return {
      horizon: HORIZON,
      p5: q(0.05), p50: q(0.5), p95: q(0.95),
      pLoss: terminals.filter(t => t < 0).length / PATHS,
      avgMaxDD: ddSum / PATHS,
      bins: bins.map(b => b / maxBin),
      zeroBin: Math.min(BINS - 1, Math.max(0, Math.floor(((0 - lo) / span) * BINS))),
    };
  }, [chrono]);

  // -------------------------------------------------------------------------
  // Canvas painters
  // -------------------------------------------------------------------------

  const drawRoundChart = useCallback(() => {
    const st = simStateRef.current;
    const ctx = fitCanvas(roundCanvasRef.current, 250);
    if (!ctx) return;
    const w = roundCanvasRef.current!.width, h = 250;
    ctx.clearRect(0, 0, w, h);
    if (st.priceHistory.length === 0) return;

    const ps = st.priceHistory.map(p => p.price);
    ps.push(st.strikePrice);
    let min = Math.min(...ps), max = Math.max(...ps);
    const pad = (max - min) === 0 ? Math.max(min * 0.0004, 0.5) : (max - min) * 0.2;
    min -= pad; max += pad;
    const X = (i: number) => (i / Math.max(st.roundSeconds, 1)) * w;
    const Y = (p: number) => h - ((p - min) / (max - min)) * h;

    ctx.strokeStyle = C.grid;
    ctx.lineWidth = 1;
    for (let i = 1; i < 6; i++) {
      const y = (i / 6) * h, x = (i / 6) * w;
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
    }

    const sy = Y(st.strikePrice);
    ctx.strokeStyle = 'rgba(255,209,102,0.6)';
    ctx.lineWidth = 1.2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath(); ctx.moveTo(0, sy); ctx.lineTo(w, sy); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = C.amber;
    ctx.font = '10px monospace';
    ctx.fillText(`STRIKE ${st.strikePrice.toFixed(2)}`, 8, sy - 6);

    ctx.beginPath();
    ctx.moveTo(X(0), Y(st.priceHistory[0].price));
    for (let i = 1; i < st.priceHistory.length; i++) ctx.lineTo(X(i), Y(st.priceHistory[i].price));
    ctx.strokeStyle = C.azure;
    ctx.lineWidth = 2;
    ctx.stroke();

    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, 'rgba(88,240,255,0.15)');
    grad.addColorStop(1, 'rgba(88,240,255,0)');
    ctx.fillStyle = grad;
    ctx.lineTo(X(st.priceHistory.length - 1), h); ctx.lineTo(X(0), h);
    ctx.closePath(); ctx.fill();

    st.priceHistory.forEach((pt, i) => {
      if (!pt.trade) return;
      const tx = X(i), ty = Y(pt.price);
      ctx.beginPath();
      ctx.fillStyle = pt.trade === 'YES' ? C.lime : C.rose;
      if (pt.trade === 'YES') { ctx.moveTo(tx, ty - 8); ctx.lineTo(tx - 5, ty + 2); ctx.lineTo(tx + 5, ty + 2); }
      else { ctx.moveTo(tx, ty + 8); ctx.lineTo(tx - 5, ty - 2); ctx.lineTo(tx + 5, ty - 2); }
      ctx.fill();
    });

    const li = st.priceHistory.length - 1;
    ctx.beginPath(); ctx.arc(X(li), Y(st.priceHistory[li].price), 3.5, 0, Math.PI * 2);
    ctx.fillStyle = C.amber; ctx.fill();
  }, []);

  const drawEnvelope = useCallback(() => {
    const st = simStateRef.current;
    const ctx = fitCanvas(envelopeCanvasRef.current, 150);
    if (!ctx) return;
    const w = envelopeCanvasRef.current!.width, h = 150;
    ctx.clearRect(0, 0, w, h);
    const hist = st.pYesHistory;
    if (hist.length < 2) {
      ctx.fillStyle = C.faint; ctx.font = '10px monospace'; ctx.textAlign = 'left';
      ctx.fillText('accumulating model path…', 10, h / 2);
      return;
    }
    const X = (i: number) => (i / Math.max(st.roundSeconds, 1)) * w;
    const Y = (p: number) => h - p * h;

    ctx.strokeStyle = C.grid;
    [0.25, 0.75].forEach(g => { ctx.beginPath(); ctx.moveTo(0, Y(g)); ctx.lineTo(w, Y(g)); ctx.stroke(); });
    ctx.strokeStyle = 'rgba(239,246,255,0.2)';
    ctx.setLineDash([3, 4]);
    ctx.beginPath(); ctx.moveTo(0, Y(0.5)); ctx.lineTo(w, Y(0.5)); ctx.stroke();
    ctx.setLineDash([]);

    // ±1σ confidence band from the pricer
    ctx.beginPath();
    hist.forEach((pt, i) => { i === 0 ? ctx.moveTo(X(i), Y(pt.hi)) : ctx.lineTo(X(i), Y(pt.hi)); });
    for (let i = hist.length - 1; i >= 0; i--) ctx.lineTo(X(i), Y(hist[i].lo));
    ctx.closePath();
    ctx.fillStyle = 'rgba(157,125,255,0.13)';
    ctx.fill();

    ctx.beginPath();
    hist.forEach((pt, i) => { i === 0 ? ctx.moveTo(X(i), Y(pt.p)) : ctx.lineTo(X(i), Y(pt.p)); });
    ctx.strokeStyle = C.violet;
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.fillStyle = C.faint; ctx.font = '9px monospace'; ctx.textAlign = 'left';
    ctx.fillText('P=1', 6, 12); ctx.fillText('P=0', 6, h - 5);
  }, []);

  const drawMesh = useCallback(() => {
    const st = simStateRef.current;
    const ctx = fitCanvas(meshCanvasRef.current, 240);
    if (!ctx) return;
    const w = meshCanvasRef.current!.width, h = 240;
    ctx.clearRect(0, 0, w, h);

    const fv = st.pYesHistory.length ? st.pYesHistory[st.pYesHistory.length - 1] : null;
    const asset = st.asset;
    const cx = contextsRef.current[asset];
    const mkt = marketsRef.current?.markets?.[asset];
    const bidSum = st.yesContract.bids.reduce((a: number, r: any) => a + r.size, 0);
    const askSum = st.yesContract.asks.reduce((a: number, r: any) => a + r.size, 0);
    const bookImb = bidSum + askSum > 0 ? (bidSum - askSum) / (bidSum + askSum) : 0;
    const drift = st.strikeLocked && st.strikePrice > 0 ? (st.price - st.strikePrice) / st.strikePrice : 0;
    const pYes = fv ? fv.p : 0.5;
    const edge = pYes - st.yesContract.midPrice;

    // Real inputs: [label, displayed value, normalized weight -1..1]
    const inputs: Array<[string, string, number]> = [
      ['MARK DRIFT', `${drift >= 0 ? '+' : ''}${(drift * 100).toFixed(3)}%`, Math.max(-1, Math.min(1, drift * 400))],
      ['FUNDING', cx ? `${(cx.fundingRate * 100).toFixed(4)}%` : '—', cx ? Math.max(-1, Math.min(1, cx.fundingRate * 8000)) : 0],
      ['σ 24H', mkt?.realizedVolPct ? `${mkt.realizedVolPct.toFixed(1)}%` : '—', mkt?.realizedVolPct ? Math.min(1, mkt.realizedVolPct / 120) : 0],
      ['BOOK IMB', `${(bookImb * 100).toFixed(0)}%`, bookImb],
      ['MODEL EDGE', `${(edge * 100).toFixed(1)}%`, Math.max(-1, Math.min(1, edge * 8))],
    ];

    const inX = Math.max(96, w * 0.2), hubX = w * 0.58, outX = w * 0.88;
    const hubY = h / 2;
    const yFor = (i: number) => (h / (inputs.length + 1)) * (i + 1);

    inputs.forEach(([, , wgt], i) => {
      const y = yFor(i);
      const mag = Math.abs(wgt);
      ctx.beginPath();
      ctx.moveTo(inX + 10, y);
      ctx.bezierCurveTo(inX + (hubX - inX) * 0.5, y, hubX - (hubX - inX) * 0.4, hubY, hubX - 22, hubY);
      ctx.strokeStyle = wgt >= 0 ? `rgba(191,255,106,${0.15 + mag * 0.6})` : `rgba(255,111,179,${0.15 + mag * 0.6})`;
      ctx.lineWidth = 1 + mag * 2.5;
      ctx.stroke();
    });

    const yesY = h * 0.3, noY = h * 0.7;
    ctx.beginPath(); ctx.moveTo(hubX + 22, hubY); ctx.lineTo(outX - 14, yesY);
    ctx.strokeStyle = `rgba(191,255,106,${0.15 + pYes * 0.7})`; ctx.lineWidth = 1 + pYes * 3; ctx.stroke();
    ctx.beginPath(); ctx.moveTo(hubX + 22, hubY); ctx.lineTo(outX - 14, noY);
    ctx.strokeStyle = `rgba(255,111,179,${0.15 + (1 - pYes) * 0.7})`; ctx.lineWidth = 1 + (1 - pYes) * 3; ctx.stroke();

    ctx.font = '8px monospace';
    inputs.forEach(([label, val, wgt], i) => {
      const y = yFor(i);
      ctx.beginPath(); ctx.arc(inX, y, 6.5, 0, Math.PI * 2);
      ctx.fillStyle = wgt >= 0 ? C.lime : C.rose;
      ctx.fill();
      ctx.fillStyle = C.faint; ctx.textAlign = 'right';
      ctx.fillText(label, inX - 13, y - 2);
      ctx.fillStyle = 'rgba(239,246,255,0.85)';
      ctx.fillText(val, inX - 13, y + 9);
    });

    ctx.beginPath(); ctx.arc(hubX, hubY, 20, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(157,125,255,0.15)';
    ctx.strokeStyle = C.violet; ctx.lineWidth = 1.5;
    ctx.fill(); ctx.stroke();
    ctx.fillStyle = C.violet; ctx.textAlign = 'center'; ctx.font = 'bold 11px monospace';
    ctx.fillText(`${Math.round(pYes * 100)}¢`, hubX, hubY + 4);
    ctx.font = '8px monospace'; ctx.fillStyle = C.faint;
    ctx.fillText('CONSENSUS', hubX, hubY + 33);

    const firing = st.activePosition?.side;
    ([['YES', yesY, C.lime, pYes], ['NO', noY, C.rose, 1 - pYes]] as const).forEach(([lbl, y, col, p]) => {
      const active = firing === lbl;
      ctx.beginPath(); ctx.arc(outX, y as number, active ? 12 : 9, 0, Math.PI * 2);
      ctx.fillStyle = active ? (col as string) : 'rgba(255,255,255,0.06)';
      ctx.strokeStyle = col as string; ctx.lineWidth = 1.5;
      ctx.fill(); ctx.stroke();
      ctx.fillStyle = active ? '#051016' : (col as string);
      ctx.font = 'bold 8px monospace';
      ctx.fillText(lbl as string, outX, (y as number) + 3);
      ctx.fillStyle = C.faint; ctx.font = '8px monospace';
      ctx.fillText(`${Math.round((p as number) * 100)}¢`, outX, (y as number) + ((y as number) < hubY ? -16 : 22));
    });
    ctx.textAlign = 'left';
  }, []);

  const drawRegime = useCallback(() => {
    const st = simStateRef.current;
    const ctx = fitCanvas(regimeCanvasRef.current, 130);
    if (!ctx) return;
    const w = regimeCanvasRef.current!.width, h = 130;
    ctx.clearRect(0, 0, w, h);
    const hist = st.regimeHist;
    if (hist.length < 3) {
      ctx.fillStyle = C.faint; ctx.font = '10px monospace'; ctx.textAlign = 'left';
      ctx.fillText('accumulating live feed samples…', 10, h / 2);
      return;
    }
    const N = hist.length;
    const X = (i: number) => (i / (N - 1)) * w;
    const layers: Array<['trend' | 'chop' | 'panic', string]> = [
      ['panic', 'rgba(255,111,179,0.5)'],
      ['chop', 'rgba(255,209,102,0.45)'],
      ['trend', 'rgba(191,255,106,0.5)'],
    ];
    const bases = new Array(N).fill(0);
    layers.forEach(([key, color]) => {
      ctx.beginPath();
      for (let i = 0; i < N; i++) {
        const y = h - (bases[i] + hist[i][key]) * h;
        i === 0 ? ctx.moveTo(X(i), y) : ctx.lineTo(X(i), y);
      }
      for (let i = N - 1; i >= 0; i--) ctx.lineTo(X(i), h - bases[i] * h);
      ctx.closePath();
      ctx.fillStyle = color;
      ctx.fill();
      for (let i = 0; i < N; i++) bases[i] += hist[i][key];
    });
  }, []);

  const drawEquity = useCallback(() => {
    const ctx = fitCanvas(equityCanvasRef.current, 56);
    if (!ctx) return;
    const w = equityCanvasRef.current!.width, h = 56;
    ctx.clearRect(0, 0, w, h);
    if (equitySeries.length < 2) return;
    let min = Math.min(0, ...equitySeries), max = Math.max(0, ...equitySeries);
    if (max === min) max = min + 1;
    const X = (i: number) => (i / (equitySeries.length - 1)) * w;
    const Y = (v: number) => h - 4 - ((v - min) / (max - min)) * (h - 8);
    const up = equitySeries[equitySeries.length - 1] >= 0;
    ctx.beginPath();
    equitySeries.forEach((v, i) => { i === 0 ? ctx.moveTo(X(i), Y(v)) : ctx.lineTo(X(i), Y(v)); });
    ctx.strokeStyle = up ? C.lime : C.rose;
    ctx.lineWidth = 1.8;
    ctx.stroke();
  }, [equitySeries]);

  const drawHitrate = useCallback(() => {
    const ctx = fitCanvas(hitrateCanvasRef.current, 56);
    if (!ctx) return;
    const w = hitrateCanvasRef.current!.width, h = 56;
    ctx.clearRect(0, 0, w, h);
    if (hitrateSeries.length < 2) return;
    const X = (i: number) => (i / (hitrateSeries.length - 1)) * w;
    const Y = (v: number) => h - 4 - (v / 100) * (h - 8);
    ctx.strokeStyle = 'rgba(239,246,255,0.15)';
    ctx.setLineDash([2, 4]);
    ctx.beginPath(); ctx.moveTo(0, Y(50)); ctx.lineTo(w, Y(50)); ctx.stroke();
    ctx.setLineDash([]);
    ctx.beginPath();
    hitrateSeries.forEach((v, i) => { i === 0 ? ctx.moveTo(X(i), Y(v)) : ctx.lineTo(X(i), Y(v)); });
    ctx.strokeStyle = C.azure;
    ctx.lineWidth = 1.8;
    ctx.stroke();
  }, [hitrateSeries]);

  const drawCandles = useCallback(() => {
    const ctx = fitCanvas(candleCanvasRef.current, 170);
    if (!ctx) return;
    const w = candleCanvasRef.current!.width, h = 170;
    ctx.clearRect(0, 0, w, h);
    const candles = marketsRef.current?.markets?.[simStateRef.current.asset]?.candles;
    if (!candles || candles.length < 2) {
      ctx.fillStyle = C.faint; ctx.font = '10px monospace'; ctx.textAlign = 'left';
      ctx.fillText('loading candle history…', 10, h / 2);
      return;
    }
    const min = Math.min(...candles.map((k: any) => k.l));
    const max = Math.max(...candles.map((k: any) => k.h));
    const Y = (p: number) => h - 6 - ((p - min) / Math.max(max - min, 1e-9)) * (h - 12);
    const bw = w / candles.length;
    candles.forEach((k: any, i: number) => {
      const x = i * bw + bw / 2;
      const up = k.c >= k.o;
      ctx.strokeStyle = up ? 'rgba(191,255,106,0.7)' : 'rgba(255,111,179,0.7)';
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x, Y(k.h)); ctx.lineTo(x, Y(k.l)); ctx.stroke();
      ctx.fillStyle = up ? C.lime : C.rose;
      const bodyTop = Y(Math.max(k.o, k.c)), bodyBot = Y(Math.min(k.o, k.c));
      ctx.fillRect(x - Math.max(bw * 0.3, 1), bodyTop, Math.max(bw * 0.6, 2), Math.max(bodyBot - bodyTop, 1));
    });
    const mark = pricesRef.current[simStateRef.current.asset];
    if (mark && mark >= min && mark <= max) {
      ctx.strokeStyle = 'rgba(88,240,255,0.7)';
      ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.moveTo(0, Y(mark)); ctx.lineTo(w, Y(mark)); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = C.azure; ctx.font = '9px monospace'; ctx.textAlign = 'left';
      ctx.fillText(`MARK ${mark.toFixed(2)}`, w - 120, Y(mark) - 5);
    }
  }, []);

  // Redraw DB/markets-derived canvases when their data changes or tab activates
  useEffect(() => {
    if (activeTab !== 'simulator') return;
    drawEquity(); drawHitrate(); drawCandles();
  }, [activeTab, drawEquity, drawHitrate, drawCandles, markets, simHistory, simAsset]);

  useEffect(() => {
    if (activeTab !== 'simulator') return;
    const onResize = () => { drawEquity(); drawHitrate(); drawCandles(); drawRoundChart(); drawMesh(); drawRegime(); drawEnvelope(); };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [activeTab, drawEquity, drawHitrate, drawCandles, drawRoundChart, drawMesh, drawRegime, drawEnvelope]);

  // -------------------------------------------------------------------------
  // Simulator engine
  // -------------------------------------------------------------------------

  useEffect(() => {
    if (activeTab !== 'simulator') return;

    const st = simStateRef.current;
    st.isRunning = simRunning;
    st.speedMultiplier = simSpeed;
    st.volatility = simVolatility;
    st.asset = simAsset;
    st.strikeLocked = false;
    st.price = pricesRef.current[simAsset] || 0;
    st.strikePrice = 0;
    st.priceHistory = [];
    st.pYesHistory = [];
    st.roundSeconds = engineStateRef.current?.params?.roundSeconds ?? DEFAULT_ROUND_S;
    st.roundSecondsRemaining = st.roundSeconds;
    st.tickCount = 0;
    st.yesContract = { midPrice: 0.5, bids: [], asks: [] };
    st.noContract = { midPrice: 0.5, bids: [], asks: [] };
    st.laggedFairValueYes = 0.5;
    st.activePosition = null;
    st.settling = false;
    st.feedBuf = [];
    st.regimeHist = [];

    setSimLogs([]);
    setRegimeReadout(null);
    prevRoundsRef.current = {};

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

    const updateRegime = () => {
      // Regime probabilities from live feed micro-structure:
      // trend ∝ |drift z-score|, chop ∝ its inverse, panic ∝ short-window vol
      // relative to the 24h realized-vol baseline from real candles.
      const buf = st.feedBuf;
      if (buf.length < 8) return;
      const rets: number[] = [];
      for (let i = Math.max(1, buf.length - 60); i < buf.length; i++) {
        rets.push(Math.log(buf[i].p / buf[i - 1].p));
      }
      if (rets.length < 5) return;
      const mean = rets.reduce((a, b) => a + b, 0) / rets.length;
      const sd = std(rets);
      const zDrift = sd > 0 ? (mean / (sd / Math.sqrt(rets.length))) : 0;
      const annualVolNow = sd * Math.sqrt(SECONDS_PER_YEAR / 2) * 100;
      const baseline = marketsRef.current?.markets?.[st.asset]?.realizedVolPct || 50;
      const volRatio = baseline > 0 ? annualVolNow / baseline : 1;

      const sTrend = Math.abs(zDrift) * 0.8;
      const sChop = 1.2 / (1 + Math.abs(zDrift));
      const sPanic = Math.max(0, volRatio - 0.7) * 1.4;
      const es = [Math.exp(sTrend), Math.exp(sChop), Math.exp(sPanic)];
      const sum = es[0] + es[1] + es[2];
      const probs = { trend: es[0] / sum, chop: es[1] / sum, panic: es[2] / sum };
      st.regimeHist.push(probs);
      if (st.regimeHist.length > 90) st.regimeHist.shift();
      setRegimeReadout(probs);
    };


    const runStep = () => {
      if (disposed) return;
      if (!st.isRunning) {
        timer = setTimeout(runStep, 1000 / st.speedMultiplier);
        return;
      }

      const livePrice = pricesRef.current[st.asset];
      const feedFresh = Date.now() - feedTsRef.current < 15000;

      // Strike + round identity come from the canonical server engine.
      const srvRound = engineStateRef.current?.rounds?.find((r: any) => r.asset === st.asset && r.status === 'open');
      if (!st.strikeLocked) {
        if (srvRound && livePrice && feedFresh) {
          st.price = livePrice;
          st.strikePrice = srvRound.strikePrice;
          st.roundId = srvRound.epoch;
          st.strikeLocked = true;
          st.priceHistory = [{ price: livePrice }];
          st.pYesHistory = [];
        } else {
          timer = setTimeout(runStep, 500);
          return;
        }
      } else if (srvRound && srvRound.epoch !== st.roundId) {
        // New canonical round began — reset the visual path to its strike
        st.roundId = srvRound.epoch;
        st.strikePrice = srvRound.strikePrice;
        st.priceHistory = [{ price: st.price }];
        st.pYesHistory = [];
      }

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
      st.roundSeconds = engineStateRef.current?.params?.roundSeconds ?? st.roundSeconds;
      st.priceHistory.push({ price: st.price });
      if (st.priceHistory.length > st.roundSeconds) st.priceHistory.shift();
      st.roundSecondsRemaining = Math.max(0, st.roundSeconds - Math.floor((Date.now() / 1000) % st.roundSeconds));

      if (st.tickCount % 6 === 0) {
        const diffPct = ((st.price - st.strikePrice) / st.strikePrice) * 100;
        addSimLog('signal', `${st.asset} mark ${fmtUsd(st.price)} (${diffPct >= 0 ? '+' : ''}${diffPct.toFixed(3)}% vs strike)`);
      }

      const fv = binaryFairValue(st.price, st.strikePrice, st.volatility, st.roundSecondsRemaining);
      setModelReadout(fv);

      // model path with ±1σ envelope (pricer re-evaluated at S±σ)
      const pLo = binaryFairValue(st.price - fv.sigmaUsd, st.strikePrice, st.volatility, st.roundSecondsRemaining).pYes;
      const pHi = binaryFairValue(st.price + fv.sigmaUsd, st.strikePrice, st.volatility, st.roundSecondsRemaining).pYes;
      st.pYesHistory.push({ p: fv.pYes, lo: Math.min(pLo, pHi), hi: Math.max(pLo, pHi) });
      if (st.pYesHistory.length > st.roundSeconds) st.pYesHistory.shift();

      updateRegime();

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


      drawRoundChart();
      drawMesh();
      drawRegime();
      drawEnvelope();


      setSimSecondsRemaining(st.roundSecondsRemaining);
      const mins = Math.floor(st.roundSecondsRemaining / 60);
      const secs = st.roundSecondsRemaining % 60;
      setSimCountdown(`${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`);

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

  // ---- Slider handlers ----
  const handleSpeedChange = (v: number) => { setSimSpeed(v); simStateRef.current.speedMultiplier = v; };
  const handleVolatilityChange = (v: number) => { setSimVolatility(v); simStateRef.current.volatility = v; };
  const handleToggleSimRunning = () => {
    const next = !simRunning;
    setSimRunning(next);
    simStateRef.current.isRunning = next;
  };

  const handleLevelView = (lvl: 1 | 2 | 3 | 4) => {
    setLevelView(lvl);
    levelViewRef.current = lvl;
    setLogAllLevels(false);
    logAllLevelsRef.current = false;
    loadHistory(simStateRef.current.asset);
    fetchData();
  };

  const handleLogAllLevels = () => {
    const next = !logAllLevelsRef.current;
    setLogAllLevels(next);
    logAllLevelsRef.current = next;
    loadHistory(simStateRef.current.asset);
  };

  const handleLedgerScope = (scope: 'demo' | 'archive') => {
    setLedgerScope(scope);
    ledgerScopeRef.current = scope;
    loadHistory(simStateRef.current.asset);
  };

  // ---- Access control (owner only) ----
  const loadAdminUsers = useCallback(async () => {
    if (!isOwner) return;
    try {
      const res = await fetch('/api/admin/users');
      const json = await res.json();
      if (res.ok && json.users) setAdminUsers(json.users);
    } catch { /* transient */ }
  }, [isOwner]);

  useEffect(() => { loadAdminUsers(); }, [loadAdminUsers]);

  const handleAccessAction = async (userId: string, action: 'approve' | 'revoke' | 'block') => {
    try {
      const res = await fetch('/api/admin/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId, action }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Update failed');
      setMessage({ type: 'success', text: `Access updated — role is now ${json.role}.` });
      await loadAdminUsers();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Access update failed' });
    }
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
    const headers = ['Level', 'Round', 'Timestamp (UTC)', 'Asset', 'Strike', 'Expiry', 'Side', 'Qty', 'Entry', 'Exit', 'Outcome', 'Net PnL'];
    const rows = simHistory.map(h => [
      h.level ? `L${h.level}` : '-',
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

  const handleDemoReset = async () => {
    if (!confirm('Reset the demo ledger? Equity returns to a clean $10,000 and all stats restart from zero. Historical rows are preserved but no longer count.')) return;
    try {
      const res = await fetch('/api/demo/reset', { method: 'POST' });
      const result = await res.json();
      if (res.ok) {
        await loadHistory(simAsset);
        setMessage({ type: 'success', text: 'Demo ledger reset — clean $10,000 start.' });
      } else {
        setMessage({ type: 'error', text: result.error || 'Reset failed' });
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
          <RefreshCw className="f-spin" size={34} color="#58f0ff" />
          <span className="f-kicker">Decrypting vault · syncing Hyperliquid L1</span>
        </div>
      </div>
    );
  }

  const feedAge = feedTs ? Math.max(0, Math.round((Date.now() - feedTs) / 1000)) : null;
  const feedLive = !feedError && feedAge !== null && feedAge < 15;

  const levelsPanel = (
    <div className="f-panel" style={{ marginBottom: 18 }}>
      <div className="f-panel-head">
        <h2 className="f-panel-title">
          <Scale size={14} color="#ffd166" /> <span className="f-serif-grad">Subscription Levels</span>
          <span className="f-kicker" style={{ marginLeft: 4 }}>SAME SIGNALS · SAME SIZING · MORE TRADES PER LEVEL</span>
        </h2>
        <span className="f-kicker">TAP A LEVEL TO INSPECT ITS LEDGER</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: 12 }}>
        {(engineState?.levels || [4, 1, 2, 3].map(l => ({ level: l }))).map((ls: any) => {
          const selected = levelView === ls.level;
          return (
            <button
              key={ls.level}
              onClick={() => handleLevelView(ls.level as 1 | 2 | 3 | 4)}
              style={{
                textAlign: 'left', cursor: 'pointer', font: 'inherit', color: 'inherit',
                border: `1px solid ${selected ? 'rgba(88,240,255,0.55)' : 'var(--hairline-strong)'}`,
                borderRadius: 18,
                background: selected ? 'rgba(88,240,255,0.07)' : 'rgba(5,7,17,0.4)',
                boxShadow: selected ? '0 0 26px rgba(88,240,255,0.12)' : 'none',
                padding: '14px 16px',
                transition: 'all 180ms ease',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className={`f-tag ${selected ? 'azure' : ls.level === 4 ? 'win' : 'dim'}`}>{levelLabel(ls.level)}</span>
                <span className="f-kicker">
                  {ls.base === null ? 'UNLIMITED CAPITAL' : `$${(ls.base / 1000).toFixed(0)}K${ls.level === 3 ? '+' : ''} CAPITAL`}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 14, alignItems: 'center', marginTop: 10 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className={`f-mono ${(ls.pnl ?? 0) >= 0 ? 'f-pos' : 'f-neg'}`}
                    style={{ fontSize: 25, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
                    {ls.pnl !== undefined ? fmtSignedUsd(ls.pnl) : '—'}
                  </div>
                  <div className="f-mono f-faint" style={{ fontSize: 10, marginTop: 3 }}>
                    {ls.base === null
                      ? 'P&L · unlimited tier'
                      : `Equity ${ls.bankroll !== undefined && ls.bankroll !== null ? fmtUsd(ls.bankroll) : '—'}`}
                  </div>
                  <div style={{ display: 'flex', gap: 6, marginTop: 9, flexWrap: 'wrap' }}>
                    <span className="f-chip" style={{ padding: '3px 9px' }}>
                      <b className="f-pos">{ls.wins ?? '—'}</b><span style={{ fontSize: 8.5 }}>WIN</span>
                    </span>
                    <span className="f-chip" style={{ padding: '3px 9px' }}>
                      <b className="f-neg">{ls.losses ?? '—'}</b><span style={{ fontSize: 8.5 }}>LOSS</span>
                    </span>
                    <span className="f-chip" style={{ padding: '3px 9px' }}>
                      <b className="f-azure">
                        {ls.wins !== undefined && (ls.wins + ls.losses) > 0
                          ? `${Math.round((ls.wins / (ls.wins + ls.losses)) * 100)}%`
                          : '—'}
                      </b><span style={{ fontSize: 8.5 }}>HIT</span>
                    </span>
                  </div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <QuotaRing used={ls.tradesToday} limit={ls.dailyTrades} />
                  <div className="f-kicker" style={{ marginTop: 4, fontSize: 8 }}>Trades today</div>
                </div>
              </div>
            </button>
          );
        })}
      </div>
      <div className="f-mono f-faint" style={{ fontSize: 9, marginTop: 12, letterSpacing: '0.05em' }}>
        Every entry risks 2% of the tier's current equity — sizes compound with performance. Tiers differ in capital base and trades per day — pick the ledger you would subscribe to.
      </div>
    </div>
  );

  return (
    <div className="fable">
      <div className="f-shell">

        {/* ---------- Masthead ---------- */}
        <header className="f-masthead">
          <div style={{ display: 'flex', alignItems: 'center', gap: 22 }}>
            <Link href="/" className="f-brand">
              <span className="f-brand-mark">P</span>
              <span>
                <div className="f-brand-name">Prospera</div>
                <div className="f-brand-sub">CAPITAL COCKPIT</div>
              </span>
            </Link>
            <span className="f-serif-grad" style={{ fontSize: 15 }}>autonomous wealth desk</span>
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
              {feedLive ? `HYPERLIQUID LIVE · ${feedAge}s` : 'FEED DOWN'}
            </span>
            {data?.ledgerValid ? (
              <span className="f-led warm">LEDGER SEALED</span>
            ) : (
              <span className="f-led bad">LEDGER TAMPERED</span>
            )}
            {!isOwner && <span className="f-led warm">WATCH-ONLY DEMO</span>}
            <span className="f-clock f-mono">{clock}</span>
            {user ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: 11, color: 'var(--ivory-dim)' }}>{user?.name || user?.email}</span>
                <button className="f-btn" style={{ padding: '5px 12px', fontSize: 9.5 }} onClick={() => handleSignOut()}>
                  SIGN OUT
                </button>
              </div>
            ) : (
              <Link href="/login" className="f-btn" style={{ padding: '5px 14px', fontSize: 9.5, textDecoration: 'none' }}>
                OPERATOR SIGN IN
              </Link>
            )}
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
                <span>FEED HYPERLIQUID L1 · POLL 2S · LEDGER TURSO · SETTLEMENT SERVER-VERIFIED</span>
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
                  <span><b>σ24H</b> {markets?.markets?.[asset]?.realizedVolPct ? markets.markets[asset].realizedVolPct.toFixed(1) + '%' : '—'}</span>
                  <span style={{ color: 'var(--sage)' }}><b>SYNC</b> {feedTs ? new Date(feedTs).toLocaleTimeString(undefined, { hour12: false }) : 'connecting…'}</span>
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
            <button className="f-btn" style={{ marginLeft: 'auto', padding: '3px 10px', fontSize: 9 }} onClick={() => setMessage(null)}>DISMISS</button>
          </div>
        )}

        {activeTab === 'cockpit' ? (
          <>
            {/* ============ COCKPIT ============ */}
            {levelsPanel}
            <div className="f-stat-grid">
              <div className="f-stat">
                <span className="f-kicker">{levelLabel(levelView)} Equity</span>
                <div className="f-stat-value f-azure">
                  {(() => { const ls = engineState?.levels?.find((l: any) => l.level === levelView); if (!ls) return '—'; return ls.base === null ? '∞ UNLIMITED' : fmtUsd(ls.bankroll); })()}
                </div>
                <div className="f-stat-sub">
                  {(() => { const ls = engineState?.levels?.find((l: any) => l.level === levelView); if (!ls) return 'Syncing…'; return ls.base === null ? 'Unlimited capital tier' : `Base ${fmtUsd(ls.base, 0)} static · shared demo`; })()}
                </div>
              </div>
              <div className="f-stat">
                <span className="f-kicker">Engine Hit Rate</span>
                <div className="f-stat-value f-violet">{data?.aiMetrics ? (data.aiMetrics.winRate * 100).toFixed(1) + '%' : '—'}</div>
                <div className="f-stat-sub">{data?.aiMetrics?.settledRounds ?? 0} settled rounds · Turso</div>
              </div>
              <div className="f-stat">
                <span className="f-kicker">{levelLabel(levelView)} Realized PnL</span>
                <div className={`f-stat-value ${((engineState?.levels?.find((l: any) => l.level === levelView)?.pnl ?? data?.aiMetrics?.totalProfit) ?? 0) >= 0 ? 'f-pos' : 'f-neg'}`}>
                  {(() => { const ls = engineState?.levels?.find((l: any) => l.level === levelView); return ls ? fmtSignedUsd(ls.pnl) : fmtSignedUsd(data?.aiMetrics?.totalProfit); })()}
                </div>
                <div className="f-stat-sub">Live · per-round Sharpe {data?.aiMetrics?.sharpeRatio?.toFixed(2)}</div>
              </div>
              <div className="f-stat">
                <span className="f-kicker">Active Deployments</span>
                <div className="f-stat-value">{data?.botInstances?.filter((b: any) => b.status === 'active').length ?? 0}</div>
                <div className="f-stat-sub">{data?.aiMetrics?.executionFills ?? 0} dispatcher fills</div>
              </div>
            </div>

            <div className="f-panel" style={{ marginBottom: 18 }}>
              <div className="f-panel-head">
                <h2 className="f-panel-title"><Shield size={14} color="#9d7dff" /> <span className="f-serif-grad">Risk Advisory</span></h2>
                <span className="f-tag violet">DERIVED FROM LEDGER</span>
              </div>
              <p style={{ margin: 0, fontSize: 13, lineHeight: 1.7, color: 'var(--ivory-dim)' }}>{data?.aiMetrics?.advisoryText}</p>
            </div>

            <div className="f-grid-main">
              <div className="f-col">
                {isOwner && (<>
                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Lock size={14} color="#ff6fb3" /> <span className="f-serif-grad">Connect Hyperliquid</span></h2>
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

                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Plus size={14} color="#58f0ff" /> <span className="f-serif-grad">Deploy Bot Instance</span></h2>
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
                          <input type="radio" name="mode" checked={botMode === 'paper'} onChange={() => setBotMode('paper')} style={{ accentColor: '#58f0ff' }} />
                          Paper
                        </label>
                        <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                          <input type="radio" name="mode" checked={botMode === 'live'} onChange={() => setBotMode('live')} style={{ accentColor: '#58f0ff' }} />
                          Live Execution
                        </label>
                      </div>
                    </div>
                    <button type="submit" className="f-btn primary" disabled={submittingInstance || data?.exchangeConnections?.length === 0}>
                      {submittingInstance ? 'DEPLOYING…' : 'DEPLOY ACTIVE BOT'}
                    </button>
                  </form>
                </div>

                </>)}
                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Radio size={14} color="#ffd166" /> <span className="f-serif-grad">Webhook Signal Desk</span></h2>
                    <span className={`f-led ${feedLive ? 'ok' : 'bad'}`}>{feedLive ? 'MARK SYNCED' : 'AWAITING FEED'}</span>
                  </div>
                  <p style={{ margin: '0 0 12px', fontSize: 11.5, color: 'var(--ivory-faint)', lineHeight: 1.6 }}>
                    Fire a TradingView-style webhook into the dispatcher at the <b style={{ color: 'var(--azure)' }}>live Hyperliquid mark</b> for the template's asset.
                  </p>
                  <table className="f-table">
                    <thead>
                      <tr><th>Template</th><th>Status</th><th className="num">Live Mark</th><th className="num">Fire</th></tr>
                    </thead>
                    <tbody>
                      {data?.botTemplates?.map((tmpl: any) => {
                        const feedKey = feedKeyForAssetClass(tmpl.assetClass);
                        const livePrice = feedKey ? prices[feedKey] : undefined;
                        return (
                          <tr key={tmpl.id}>
                            <td style={{ color: 'var(--ivory)' }}>{tmpl.code}</td>
                            <td><span className={`f-tag ${tmpl.status === 'live' ? 'win' : 'gold'}`}>{tmpl.status.toUpperCase()}</span></td>
                            <td className="num f-azure">{livePrice ? fmtUsd(livePrice) : 'syncing…'}</td>
                            <td className="num">
                              {isOwner ? (
                                <div style={{ display: 'inline-flex', gap: 6 }}>
                                  <button className="f-btn long" style={{ padding: '4px 12px', fontSize: 9 }}
                                    disabled={simulatingSignal || !livePrice}
                                    onClick={() => handleSimulateSignal(tmpl.code, 'LONG', tmpl.assetClass)}>
                                    LONG
                                  </button>
                                  <button className="f-btn short" style={{ padding: '4px 12px', fontSize: 9 }}
                                    disabled={simulatingSignal || !livePrice}
                                    onClick={() => handleSimulateSignal(tmpl.code, 'SHORT', tmpl.assetClass)}>
                                    SHORT
                                  </button>
                                </div>
                              ) : (
                                <span className="f-tag dim">OPERATOR</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="f-col">
                {isOwner && (
                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Shield size={14} color="#58f0ff" /> <span className="f-serif-grad">Access Control</span>
                      <span className="f-kicker" style={{ marginLeft: 4 }}>DB-BACKED · NO REDEPLOYS</span>
                    </h2>
                    <button className="f-btn" style={{ padding: '4px 12px', fontSize: 9 }} onClick={loadAdminUsers}>REFRESH</button>
                  </div>
                  {adminUsers.length === 0 ? (
                    <div className="f-empty">No sign-ins yet — accounts appear here after their first Google login.</div>
                  ) : (
                    <table className="f-table">
                      <thead>
                        <tr><th>Account</th><th>Role</th><th className="num">Manage</th></tr>
                      </thead>
                      <tbody>
                        {adminUsers.map((u: any) => (
                          <tr key={u.id}>
                            <td style={{ color: 'var(--ivory)' }}>{u.email}</td>
                            <td>
                              <span className={`f-tag ${u.role === 'owner' ? 'gold' : u.role === 'viewer' ? 'win' : u.role === 'blocked' ? 'loss' : 'violet'}`}>
                                {u.role.toUpperCase()}
                              </span>
                            </td>
                            <td className="num">
                              {u.role === 'owner' ? (
                                <span className="f-kicker">ENV-MANAGED</span>
                              ) : (
                                <div style={{ display: 'inline-flex', gap: 6 }}>
                                  {u.role !== 'viewer' && (
                                    <button className="f-btn long" style={{ padding: '3px 10px', fontSize: 9 }}
                                      onClick={() => handleAccessAction(u.id, 'approve')}>APPROVE</button>
                                  )}
                                  {u.role === 'viewer' && (
                                    <button className="f-btn" style={{ padding: '3px 10px', fontSize: 9 }}
                                      onClick={() => handleAccessAction(u.id, 'revoke')}>REVOKE</button>
                                  )}
                                  {u.role !== 'blocked' && (
                                    <button className="f-btn danger" style={{ padding: '3px 10px', fontSize: 9 }}
                                      onClick={() => handleAccessAction(u.id, 'block')}>BLOCK</button>
                                  )}
                                </div>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
                )}
                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Activity size={14} color="#bfff6a" /> <span className="f-serif-grad">Active Deployments</span></h2>
                    <button className="f-btn" style={{ padding: '4px 12px', fontSize: 9 }} onClick={handleRefresh} disabled={refreshing}>
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
                          <div key={bot.id} style={{ border: '1px solid var(--hairline)', borderRadius: 16, padding: '11px 13px', background: 'rgba(5,7,17,0.4)' }}>
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
                            {isOwner && <div style={{ display: 'flex', gap: 6, marginTop: 9 }}>
                              {bot.status === 'active' && (
                                <button className="f-btn" style={{ padding: '4px 12px', fontSize: 9 }} onClick={() => handleToggleBotStatus(bot.id, bot.status, 'pause')}>
                                  <Pause size={9} style={{ marginRight: 4, verticalAlign: '-1px' }} />PAUSE
                                </button>
                              )}
                              {bot.status === 'paused' && (
                                <button className="f-btn long" style={{ padding: '4px 12px', fontSize: 9 }} onClick={() => handleToggleBotStatus(bot.id, bot.status, 'resume')}>
                                  <Play size={9} style={{ marginRight: 4, verticalAlign: '-1px' }} />RESUME
                                </button>
                              )}
                              {bot.status !== 'kill_switched' && (
                                <button className="f-btn danger" style={{ padding: '4px 12px', fontSize: 9 }} onClick={() => handleToggleBotStatus(bot.id, bot.status, 'kill')}>
                                  <AlertTriangle size={9} style={{ marginRight: 4, verticalAlign: '-1px' }} />KILL
                                </button>
                              )}
                            </div>}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Coins size={14} color="#ffd166" /> <span className="f-serif-grad">Hyperliquid Positions</span></h2>
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

                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><FileText size={14} color="#9d7dff" /> <span className="f-serif-grad">Cryptographic Trade Ledger</span></h2>
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
                              <td className="num f-azure">{fmtUsd(ord.price)}</td>
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

                {data?.riskEvents?.length > 0 && (
                  <div className="f-panel">
                    <div className="f-panel-head">
                      <h2 className="f-panel-title"><AlertOctagon size={14} color="#ff6fb3" /> <span className="f-serif-grad">Risk Audit Log</span></h2>
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

            {/* Hero strip — all values from Turso-backed stats */}
            <div className="f-stat-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))' }}>
              <div className="f-stat">
                <span className="f-kicker">Net PnL · {simAsset} · {levelLabel(levelView)}</span>
                <div className={`f-stat-value ${(dbStats?.totalPnl ?? 0) >= 0 ? 'f-pos' : 'f-neg'}`} style={{ fontSize: 30 }}>
                  {dbStats ? fmtSignedUsd(dbStats.totalPnl) : '—'}
                </div>
                <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  <span className="f-chip"><b className="f-azure">{dbStats?.settled ?? 0}</b> ROUNDS</span>
                  <span className="f-chip">EXPECT <b className={(dbStats?.expectancy ?? 0) >= 0 ? 'f-pos' : 'f-neg'}>{dbStats ? fmtSignedUsd(dbStats.expectancy) : '—'}</b></span>
                  <span className="f-chip">PF <b className="f-gold">{dbStats?.profitFactor === null ? '∞' : dbStats?.profitFactor ?? '—'}</b></span>
                </div>
                <div style={{ marginTop: 10 }}><canvas ref={equityCanvasRef} style={{ width: '100%', height: 56, display: 'block' }} /></div>
              </div>
              <div className="f-stat">
                <span className="f-kicker">{levelLabel(levelView)} Account</span>
                <div className="f-stat-value f-gold" style={{ fontSize: 30 }}>
                  {(() => { const ls = engineState?.levels?.find((l: any) => l.level === levelView); if (!ls) return '—'; return ls.base === null ? '∞' : fmtUsd(ls.bankroll); })()}
                </div>
                <div className="f-stat-sub">
                  {engineState ? `Since ${fmtTime(engineState.demoStartedAt)} · trades today ${engineState.levels?.find((l: any) => l.level === levelView)?.tradesToday ?? '—'}/${(() => { const d = engineState.levels?.find((l: any) => l.level === levelView)?.dailyTrades; return d === null ? '∞' : d ?? '—'; })()}` : 'Syncing canonical engine…'}
                </div>
                <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  <span className="f-chip">W/L <b className="f-pos">{dbStats?.wins ?? 0}</b>/<b className="f-neg">{dbStats?.losses ?? 0}</b></span>
                  <span className="f-chip">ROUND CLOCK <b className="f-neg">{simCountdown}</b></span>
                </div>
              </div>
              <div className="f-stat">
                <span className="f-kicker">Hit Rate · Lifetime</span>
                <div className="f-stat-value f-azure" style={{ fontSize: 30 }}>{dbStats ? dbStats.hitRate.toFixed(1) + '%' : '—'}</div>
                <div className="f-stat-sub">{dbStats?.wins ?? 0} W / {dbStats?.losses ?? 0} L · sparkline: rolling 20</div>
                <div style={{ marginTop: 10 }}><canvas ref={hitrateCanvasRef} style={{ width: '100%', height: 56, display: 'block' }} /></div>
              </div>
              <div className="f-stat">
                <span className="f-kicker">Active Position</span>
                <div className="f-stat-value" style={{ fontSize: 30, color: simPosition ? 'var(--sage)' : 'var(--ivory-faint)' }}>
                  {simPosition ? `${simPosition.side} ${simPosition.size.toLocaleString()}` : 'FLAT'}
                </div>
                <div className="f-stat-sub">
                  {simPosition ? `Entry ${Math.round(simPosition.entryPrice * 100)}¢ · cost ${fmtUsd(simPosition.costUsd)}` : 'Awaiting executable edge'}
                </div>
                <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  <span className="f-chip">P(YES) <b className="f-violet">{modelReadout ? Math.round(modelReadout.pYes * 100) + '¢' : '—'}</b></span>
                  <span className="f-chip">Z <b>{modelReadout ? modelReadout.z.toFixed(2) : '—'}</b></span>
                  <span className="f-chip">σ <b className="f-gold">{modelReadout ? fmtUsd(modelReadout.sigmaUsd) : '—'}</b></span>
                </div>
              </div>
            </div>

            {levelsPanel}

            {/* Execution cycle */}
            <div className="f-panel" style={{ marginBottom: 18 }}>
              <div className="f-panel-head">
                <h2 className="f-panel-title"><Activity size={14} color="#58f0ff" /> <span className="f-serif-grad">Execution Cycle</span>
                  <span className="f-kicker" style={{ marginLeft: 6 }}>ROUND #{engineState?.epoch ?? simStateRef.current.roundId} · 5-MIN BINARY · SERVER ENGINE</span>
                </h2>
                <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                  {simPosition && <span className="f-tag win">POSITION LIVE</span>}
                  <span className="f-mono f-neg" style={{ fontSize: 14, fontWeight: 700 }}>{simCountdown}</span>
                </div>
              </div>
              <div className="f-cycle">
                {CYCLE_STEPS.map((step, i) => {
                  const active = cycleStep(simSecondsRemaining, simStateRef.current.roundSeconds) === i;
                  const past = cycleStep(simSecondsRemaining, simStateRef.current.roundSeconds) > i;
                  return (
                    <div key={step} style={{
                      border: `1px solid ${active ? 'rgba(88,240,255,0.6)' : past ? 'rgba(191,255,106,0.35)' : 'var(--hairline)'}`,
                      borderRadius: 14,
                      background: active ? 'rgba(88,240,255,0.09)' : past ? 'rgba(191,255,106,0.05)' : 'transparent',
                      boxShadow: active ? '0 0 18px rgba(88,240,255,0.15)' : 'none',
                      padding: '10px 6px',
                      textAlign: 'center',
                      transition: 'all 300ms ease',
                    }}>
                      <div className="f-kicker" style={{ marginBottom: 3 }}>0{i + 1}</div>
                      <div className="f-mono" style={{
                        fontSize: 11, fontWeight: 700,
                        color: active ? 'var(--azure)' : past ? 'var(--sage)' : 'var(--ivory-faint)',
                      }}>{step}</div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="f-grid-main">
              {/* Left column */}
              <div className="f-col">
                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title">
                      <TrendingUp size={14} color="#58f0ff" />
                      <span className="f-serif-grad">{ASSET_LABEL[simAsset]}</span>
                      <span className="f-kicker" style={{ marginLeft: 4 }}>LIVE MARK VS STRIKE · 5-MIN ROUND</span>
                    </h2>
                    <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                      <select className="f-select" style={{ width: 'auto', padding: '5px 10px', fontSize: 11 }}
                        value={simAsset} onChange={e => setSimAsset(e.target.value as DeskAsset)}>
                        {DESK_ASSETS.map(a => <option key={a} value={a}>{a}</option>)}
                      </select>
                      {isOwner && (
                        <button className="f-btn" style={{ padding: '5px 12px', fontSize: 9.5 }} onClick={handleToggleSimRunning}>
                          {simRunning ? 'PAUSE' : 'RESUME'}
                        </button>
                      )}
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
                  </div>
                  <div className="f-chart-frame">
                    <canvas ref={roundCanvasRef} style={{ width: '100%', height: '100%' }} />
                  </div>
                </div>

                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Scale size={14} color="#9d7dff" /> <span className="f-serif-grad">Fair Probability Envelope</span>
                      <span className="f-kicker" style={{ marginLeft: 4 }}>GBM PRICER · ±1σ BAND</span>
                    </h2>
                    <span className="f-mono f-violet" style={{ fontSize: 13, fontWeight: 700 }}>
                      {modelReadout ? `P(YES) ${Math.round(modelReadout.pYes * 100)}¢` : '—'}
                    </span>
                  </div>
                  <div className="f-canvas-frame" style={{ height: 150 }}>
                    <canvas ref={envelopeCanvasRef} style={{ width: '100%', height: '100%' }} />
                  </div>
                  <div className="f-mono f-faint" style={{ fontSize: 9, marginTop: 8, letterSpacing: '0.05em' }}>
                    P(YES) = Φ((S−K)/σ) · σ = S·vol·√(t/yr) · live mark S, strike K, vol input {simVolatility}%
                  </div>
                </div>

                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><CandlestickChart size={14} color="#bfff6a" /> <span className="f-serif-grad">Market Structure</span>
                      <span className="f-kicker" style={{ marginLeft: 4 }}>5M CANDLES · 6H · HYPERLIQUID</span>
                    </h2>
                    <span className="f-tag azure">REAL OHLCV</span>
                  </div>
                  <div className="f-canvas-frame" style={{ height: 170 }}>
                    <canvas ref={candleCanvasRef} style={{ width: '100%', height: '100%' }} />
                  </div>
                </div>

                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Grid3x3 size={14} color="#9d7dff" /> <span className="f-serif-grad">Realized Returns Matrix</span>
                      <span className="f-kicker" style={{ marginLeft: 4 }}>FROM LIVE CANDLE CLOSES</span>
                    </h2>
                  </div>
                  <div style={{ overflowX: 'auto' }}>
                    <table className="f-table" style={{ textAlign: 'center' }}>
                      <thead>
                        <tr>
                          <th>Asset</th>
                          {(markets?.horizons || ['5M', '15M', '30M', '1H', '4H', '24H']).map((hz: string) => <th key={hz} className="num">{hz}</th>)}
                          <th className="num">σ24H</th>
                        </tr>
                      </thead>
                      <tbody>
                        {DESK_ASSETS.map(asset => {
                          const m = markets?.markets?.[asset];
                          return (
                            <tr key={asset}>
                              <td style={{ color: 'var(--ivory)', fontWeight: 700 }}>{asset.split('-')[0]}</td>
                              {(markets?.horizons || ['5M', '15M', '30M', '1H', '4H', '24H']).map((hz: string) => {
                                const v = m?.returns?.[hz];
                                if (v === null || v === undefined) return <td key={hz} className="num f-faint">—</td>;
                                return (
                                  <td key={hz} className={`num ${v < 0 ? 'f-neg' : 'f-pos'}`}
                                    style={{ background: v < 0 ? `rgba(255,111,179,${Math.min(0.22, Math.abs(v) / 8)})` : `rgba(191,255,106,${Math.min(0.22, v / 8)})` }}>
                                    {v >= 0 ? '+' : ''}{v.toFixed(2)}%
                                  </td>
                                );
                              })}
                              <td className="num f-gold">{m?.realizedVolPct ? m.realizedVolPct.toFixed(1) + '%' : '—'}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Dices size={14} color="#ffd166" /> <span className="f-serif-grad">Monte Carlo Bootstrap</span>
                      <span className="f-kicker" style={{ marginLeft: 4 }}>10,000 PATHS · RESAMPLED FROM SETTLED ROUNDS</span>
                    </h2>
                    <span className="f-tag gold">{bootstrap ? `HORIZON ${bootstrap.horizon} ROUNDS` : 'NEEDS ≥5 ROUNDS'}</span>
                  </div>
                  {bootstrap ? (
                    <div style={{ display: 'flex', gap: 20, alignItems: 'stretch', flexWrap: 'wrap' }}>
                      <div style={{ flex: '1.3 1 280px', display: 'flex', alignItems: 'flex-end', gap: 2, height: 120, background: 'rgba(5,7,17,0.55)', border: '1px solid var(--hairline)', borderRadius: 14, padding: '10px 14px' }}>
                        {bootstrap.bins.map((b, i) => (
                          <div key={i} style={{
                            flex: 1,
                            height: `${Math.max(b * 100, 2)}%`,
                            borderRadius: '3px 3px 0 0',
                            background: i < bootstrap.zeroBin ? 'rgba(255,111,179,0.55)' : i === bootstrap.zeroBin ? '#ffd166' : 'rgba(191,255,106,0.55)',
                          }} />
                        ))}
                      </div>
                      <div className="f-mono" style={{ flex: '1 1 220px', fontSize: 11, display: 'flex', flexDirection: 'column', gap: 8, justifyContent: 'center' }}>
                        <div><span className="f-faint">P5 (adverse): </span><b className="f-neg">{fmtSignedUsd(bootstrap.p5)}</b></div>
                        <div><span className="f-faint">P50 (median): </span><b className="f-azure">{fmtSignedUsd(bootstrap.p50)}</b></div>
                        <div><span className="f-faint">P95 (favorable): </span><b className="f-pos">{fmtSignedUsd(bootstrap.p95)}</b></div>
                        <div><span className="f-faint">P(loss): </span><b>{(bootstrap.pLoss * 100).toFixed(1)}%</b></div>
                        <div><span className="f-faint">E[max drawdown]: </span><b className="f-gold">{fmtUsd(bootstrap.avgMaxDD)}</b></div>
                      </div>
                    </div>
                  ) : (
                    <div className="f-empty">Bootstrap activates once ≥5 rounds are settled for {simAsset}.</div>
                  )}
                </div>
              </div>

              {/* Right column */}
              <div className="f-col">
                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Network size={14} color="#9d7dff" /> <span className="f-serif-grad">Signal Mesh</span>
                      <span className="f-kicker" style={{ marginLeft: 4 }}>LIVE INPUTS → CONSENSUS</span>
                    </h2>
                    <span className={`f-led ${simPosition ? 'ok' : 'warm'}`}>{simPosition ? 'FIRING' : 'GATING'}</span>
                  </div>
                  <div className="f-canvas-frame" style={{ height: 240 }}>
                    <canvas ref={meshCanvasRef} style={{ width: '100%', height: '100%' }} />
                  </div>
                </div>

                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Waves size={14} color="#ffd166" /> <span className="f-serif-grad">Live Regime Probability</span>
                      <span className="f-kicker" style={{ marginLeft: 4 }}>FROM 2S FEED SAMPLES</span>
                    </h2>
                  </div>
                  <div style={{ display: 'flex', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
                    <span className="f-chip">TREND <b className="f-pos">{regimeReadout ? Math.round(regimeReadout.trend * 100) + '%' : '—'}</b></span>
                    <span className="f-chip">CHOP <b className="f-gold">{regimeReadout ? Math.round(regimeReadout.chop * 100) + '%' : '—'}</b></span>
                    <span className="f-chip">PANIC <b className="f-neg">{regimeReadout ? Math.round(regimeReadout.panic * 100) + '%' : '—'}</b></span>
                  </div>
                  <div className="f-canvas-frame" style={{ height: 130 }}>
                    <canvas ref={regimeCanvasRef} style={{ width: '100%', height: '100%' }} />
                  </div>
                  <div className="f-mono f-faint" style={{ fontSize: 9, marginTop: 8, letterSpacing: '0.05em' }}>
                    softmax(|z-drift|, 1/(1+|z|), σ₂ₛ/σ₂₄ₕ) over rolling live samples
                  </div>
                </div>

                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Grid3x3 size={14} color="#58f0ff" /> <span className="f-serif-grad">Outcome Transition Matrix</span>
                      <span className="f-kicker" style={{ marginLeft: 4 }}>MARKOV · {transitionMatrix.transitions} TRANSITIONS</span>
                    </h2>
                  </div>
                  {transitionMatrix.transitions >= 4 ? (
                    <div style={{ display: 'grid', gridTemplateColumns: '60px 1fr 1fr', gap: 8, alignItems: 'center' }}>
                      <div />
                      <div className="f-kicker" style={{ textAlign: 'center' }}>→ WIN</div>
                      <div className="f-kicker" style={{ textAlign: 'center' }}>→ LOSS</div>
                      <div className="f-kicker">WIN →</div>
                      <div className="f-matrix-cell" style={{
                        color: 'var(--sage)',
                        background: `rgba(191,255,106,${(transitionMatrix.pWW ?? 0) * 0.3})`,
                        borderColor: `rgba(191,255,106,${0.15 + (transitionMatrix.pWW ?? 0) * 0.4})`,
                      }}>{transitionMatrix.pWW !== null ? transitionMatrix.pWW.toFixed(2) : '—'}</div>
                      <div className="f-matrix-cell" style={{
                        color: 'var(--oxide)',
                        background: `rgba(255,111,179,${(transitionMatrix.pWL ?? 0) * 0.3})`,
                        borderColor: `rgba(255,111,179,${0.15 + (transitionMatrix.pWL ?? 0) * 0.4})`,
                      }}>{transitionMatrix.pWL !== null ? transitionMatrix.pWL.toFixed(2) : '—'}</div>
                      <div className="f-kicker">LOSS →</div>
                      <div className="f-matrix-cell" style={{
                        color: 'var(--sage)',
                        background: `rgba(191,255,106,${(transitionMatrix.pLW ?? 0) * 0.3})`,
                        borderColor: `rgba(191,255,106,${0.15 + (transitionMatrix.pLW ?? 0) * 0.4})`,
                      }}>{transitionMatrix.pLW !== null ? transitionMatrix.pLW.toFixed(2) : '—'}</div>
                      <div className="f-matrix-cell" style={{
                        color: 'var(--oxide)',
                        background: `rgba(255,111,179,${(transitionMatrix.pLL ?? 0) * 0.3})`,
                        borderColor: `rgba(255,111,179,${0.15 + (transitionMatrix.pLL ?? 0) * 0.4})`,
                      }}>{transitionMatrix.pLL !== null ? transitionMatrix.pLL.toFixed(2) : '—'}</div>
                    </div>
                  ) : (
                    <div className="f-empty">Needs ≥5 settled rounds to estimate transition probabilities.</div>
                  )}
                  <div className="f-mono f-faint" style={{ fontSize: 9, marginTop: 10, letterSpacing: '0.05em' }}>
                    P(next outcome | current) estimated from the settled sequence in Turso
                  </div>
                </div>

                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Lock size={14} color="#ffd166" /> <span className="f-serif-grad">Engine Parameters</span> <span className="f-kicker" style={{ marginLeft: 4 }}>CANONICAL · SERVER</span></h2>
                    <span className={`f-led ${simRunning ? 'ok' : 'warm'}`}>{simRunning ? 'RUNNING' : 'PAUSED'}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
                    <span className="f-chip">SIZING <b className="f-gold">{engineState?.params?.riskPerTrade ? (engineState.params.riskPerTrade * 100).toFixed(0) + '%' : '—'}</b> OF EQUITY /TRADE</span>
                    <span className="f-chip">EDGE ≥ <b className="f-azure">{engineState?.params ? Math.round(engineState.params.edgeThreshold * 100) + '¢' : '—'}</b></span>
                    <span className="f-chip">SPREAD <b className="f-pos">{engineState?.params ? Math.round(engineState.params.spread * 100) + '¢' : '—'}</b></span>
                    <span className="f-chip">COMPOUNDS <b className="f-violet">PER TRADE</b></span>
                  </div>
                  <div className="f-kicker" style={{ marginBottom: 10 }}>View Parameters · visual model only</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    {[
                      { label: 'Chart Tick Speed', value: `${simSpeed}×`, min: 1, max: 20, step: 1, cur: simSpeed, onChange: handleSpeedChange },
                      { label: 'Annualized Vol Input (visual)', value: `${simVolatility}%`, min: 10, max: 150, step: 5, cur: simVolatility, onChange: handleVolatilityChange },
                    ].map(s => (
                      <div key={s.label}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                          <span className="f-kicker">{s.label}</span>
                          <span className="f-mono f-azure" style={{ fontSize: 11, fontWeight: 700 }}>{s.value}</span>
                        </div>
                        <input type="range" className="f-slider" min={s.min} max={s.max} step={s.step} disabled={!isOwner}
                          value={s.cur} onChange={e => s.onChange(parseFloat(e.target.value))} />
                      </div>
                    ))}
                  </div>
                </div>

                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><Coins size={14} color="#58f0ff" /> <span className="f-serif-grad">Round Contract Book</span>
                      <span className="f-kicker" style={{ marginLeft: 4 }}>SYNTHETIC CLOB @ MODEL MID</span>
                    </h2>
                  </div>
                  {[
                    { name: 'YES · SETTLES ABOVE STRIKE', book: yesBook, color: 'var(--sage)' },
                    { name: 'NO · SETTLES AT/BELOW STRIKE', book: noBook, color: 'var(--oxide)' },
                  ].map(({ name, book, color }) => (
                    <div key={name} style={{ border: '1px solid var(--hairline)', borderRadius: 14, background: 'rgba(5,7,17,0.4)', padding: '10px 12px', marginBottom: 10 }}>
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

                <div className="f-panel">
                  <div className="f-panel-head">
                    <h2 className="f-panel-title"><FileText size={14} color="#9d7dff" /> <span className="f-serif-grad">Engine Telemetry</span></h2>
                    <button className="f-btn" style={{ padding: '4px 12px', fontSize: 9 }} onClick={() => setSimLogs([])}>CLEAR</button>
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
                        if (log.type === 'settle') color = 'var(--gold)';
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

            {/* Historical predictions */}
            <div className="f-section-head">
              <span className="f-serif-grad">Historical Predictions Log</span>
              <span className="f-tag azure">{logAllLevels ? 'ALL LEVELS' : levelLabel(levelView)} · SERVER-VERIFIED</span>
              {ledgerScope === 'archive' && <span className="f-tag gold">ARCHIVE · PRE-RESET · OWNER VIEW</span>}
              {isOwner && (
                <span style={{ display: 'inline-flex', gap: 6 }}>
                  <button className={`f-btn ${ledgerScope === 'demo' && !logAllLevels ? 'primary' : ''}`} style={{ padding: '4px 12px', fontSize: 9 }}
                    onClick={() => handleLedgerScope('demo')}>LIVE DEMO</button>
                  <button className={`f-btn ${logAllLevels ? 'primary' : ''}`} style={{ padding: '4px 12px', fontSize: 9 }}
                    onClick={handleLogAllLevels}>ALL LEVELS</button>
                  <button className={`f-btn ${ledgerScope === 'archive' ? 'primary' : ''}`} style={{ padding: '4px 12px', fontSize: 9 }}
                    onClick={() => handleLedgerScope('archive')}>ARCHIVE</button>
                </span>
              )}
            </div>
            <div className="f-panel">
              <div className="f-panel-head">
                <div className="f-mono f-faint" style={{ fontSize: 10 }}>
                  {dbStats ? `${dbStats.settled} settled · hit rate ${dbStats.hitRate.toFixed(1)}% · expectancy ${fmtUsd(dbStats.expectancy)}/round` : 'Loading…'}
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="f-btn" style={{ padding: '5px 14px', fontSize: 9.5 }} onClick={handleExportCsv} disabled={simHistory.length === 0}>
                    EXPORT CSV
                  </button>
                  {isOwner && (
                    <button className="f-btn danger" style={{ padding: '5px 14px', fontSize: 9.5 }} onClick={handleDemoReset}>
                      RESET DEMO LEDGER
                    </button>
                  )}
                </div>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table className="f-table">
                  <thead>
                    <tr>
                      <th>Lvl</th>
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
                      <tr><td colSpan={11}><div className="f-empty">No settled rounds recorded yet — engine writes here after each round expiry.</div></td></tr>
                    ) : (
                      simHistory.map((trade: any) => (
                        <tr key={trade.id || `${trade.asset}-${trade.roundId}-${trade.createdAt}`}>
                          <td>{trade.level ? <span className={`f-tag ${trade.level === 4 ? 'win' : trade.level === 3 ? 'gold' : trade.level === 2 ? 'violet' : 'azure'}`}>{trade.level === 4 ? 'DEMO' : `L${trade.level}`}</span> : <span className="f-tag dim">—</span>}</td>
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
          <span className="f-kicker">Prospera · Capital Cockpit · XAU / BTC / ETH</span>
          <span className="f-kicker">Feed: Hyperliquid L1 · Ledger: Turso · Settlement: server-verified</span>
        </div>
      </div>
    </div>
  );
}
