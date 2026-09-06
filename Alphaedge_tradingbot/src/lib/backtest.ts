// ---------------------------------------------------------------------------
// Backtest harness — the prerequisite docs/STRATEGY_CANDIDATES.md §3 calls
// non-negotiable, and which did not exist.
//
// Why this must come before any strategy tuning: the live demo engine prices
// every entry at its own model's fair value (SPREAD = 0), so its expected value
// is exactly zero by construction. Its PnL is variance, not edge. Nothing can
// be "improved" until something can tell an edge from noise, with costs.
//
// Design rules taken from §3, because a harness that flatters is worse than
// none at all:
//   - fills happen at the NEXT bar's open, never the signal bar's close
//   - both fee legs are modelled; protective exits are always taker
//   - fill rate and slippage each get a sensitivity row
//   - funding is booked over the holding period (hourly on Hyperliquid, not
//     the 8-hourly convention the doc assumed)
//   - walk-forward only: parameters are fitted on a train window and scored on
//     the window that follows, never the one they were fitted on
//   - trade count is reported next to every ratio
// ---------------------------------------------------------------------------

const HL_INFO = 'https://api.hyperliquid.xyz/info';
/** Hyperliquid serves at most this many candles, always the most recent ones. */
export const MAX_CANDLES_SERVED = 5000;

export interface Candle { t: number; o: number; h: number; l: number; c: number; v: number }
export interface FundingPoint { time: number; rate: number }

async function post(body: unknown): Promise<any> {
  const res = await fetch(HL_INFO, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`Hyperliquid info ${res.status}`);
  return res.json();
}

export function intervalMs(interval: string): number {
  const m: Record<string, number> = {
    '1m': 60_000, '5m': 300_000, '15m': 900_000, '30m': 1_800_000,
    '1h': 3_600_000, '4h': 14_400_000, '1d': 86_400_000,
  };
  const v = m[interval];
  if (!v) throw new Error(`Unsupported interval "${interval}"`);
  return v;
}

/**
 * Candle history for [startMs, endMs].
 *
 * Hyperliquid serves only the most RECENT ~5000 candles per interval and
 * ignores a startTime older than that window — asking for 120 days of 15m
 * returns the same ~52 days as asking for 60. Paginating forward from an old
 * start therefore requests a window that predates the served range and comes
 * back empty, which is exactly how this silently returned zero candles for
 * BTC and ETH. So: one request, and the caller is told what it actually got.
 *
 * Practical depth per interval: 15m ~52d, 1h ~208d, 4h ~365d+. For more
 * history, use a coarser interval rather than an earlier start.
 */
export async function fetchCandles(coin: string, interval: string, startMs: number, endMs: number): Promise<Candle[]> {
  intervalMs(interval); // validate

  // The endpoint intermittently returns an empty array for a range it serves
  // fine moments later (PAXG 1h/120d came back empty while both 60d and 200d
  // worked). Treating that as "no history" silently produced a zero-trade
  // result that looked like a finding, so retry before believing it.
  let raw: any = null;
  for (let attempt = 0; attempt < 4; attempt++) {
    raw = await post({ type: 'candleSnapshot', req: { coin, interval, startTime: startMs, endTime: endMs } });
    if (Array.isArray(raw) && raw.length > 0) break;
    await new Promise(r => setTimeout(r, 500 * (attempt + 1)));
  }
  if (!Array.isArray(raw)) return [];

  const out: Candle[] = [];
  for (const k of raw) {
    const c: Candle = { t: k.t, o: +k.o, h: +k.h, l: +k.l, c: +k.c, v: +k.v };
    if (!Number.isFinite(c.o) || !Number.isFinite(c.c)) continue;
    if (out.length && c.t <= out[out.length - 1].t) continue;
    out.push(c);
  }
  return out;
}

/** Hourly funding history, paginated the same way. */
export async function fetchFunding(coin: string, startMs: number, endMs: number): Promise<FundingPoint[]> {
  const out: FundingPoint[] = [];
  let cursor = startMs;
  let guard = 0;

  while (cursor < endMs && guard++ < 40) {
    const raw = await post({ type: 'fundingHistory', coin, startTime: cursor, endTime: endMs });
    if (!Array.isArray(raw) || raw.length === 0) break;
    for (const f of raw) {
      const p = { time: f.time, rate: parseFloat(f.fundingRate) };
      if (!Number.isFinite(p.rate)) continue;
      if (out.length && p.time <= out[out.length - 1].time) continue;
      out.push(p);
    }
    const last = raw[raw.length - 1].time;
    if (last <= cursor) break;
    cursor = last + 1;
  }
  return out;
}

// ---------------------------------------------------------------------------
// Costs
// ---------------------------------------------------------------------------

export interface CostModel {
  makerBps: number;      // 1.5 at base tier
  takerBps: number;      // 4.5 at base tier
  makerFillRate: number; // share of entries that rest and fill as maker
  slippageBps: number;   // applied to taker legs only
}

export const BASE_COSTS: CostModel = { makerBps: 1.5, takerBps: 4.5, makerFillRate: 0.65, slippageBps: 1.0 };

/** Entry blends maker/taker by fill rate; protective exits are always taker. */
function entryCostBps(c: CostModel): number {
  const takerShare = 1 - c.makerFillRate;
  return c.makerFillRate * c.makerBps + takerShare * (c.takerBps + c.slippageBps);
}
function exitCostBps(c: CostModel): number {
  return c.takerBps + c.slippageBps;
}
export function roundTripBps(c: CostModel): number {
  return entryCostBps(c) + exitCostBps(c);
}

/** Net funding paid (as a return fraction) by a position held over [from, to]. */
function fundingCost(funding: FundingPoint[], from: number, to: number, dir: 1 | -1): number {
  let sum = 0;
  for (const f of funding) {
    if (f.time < from) continue;
    if (f.time > to) break;
    sum += f.rate;
  }
  // Longs pay a positive funding rate; shorts receive it.
  return dir === 1 ? sum : -sum;
}

// ---------------------------------------------------------------------------
// S1 — breakout continuation (docs §2, ranked first)
// ---------------------------------------------------------------------------

export interface S1Params {
  lookback: number; // Donchian channel length, in bars
  hold: number;     // max bars held
  stopAtr: number;  // stop distance in ATR multiples
}

export interface Trade {
  entryT: number; exitT: number; dir: 1 | -1;
  entry: number; exit: number;
  grossRet: number; netRet: number; bars: number; reason: string;
}

function atr(candles: Candle[], i: number, n: number): number {
  let sum = 0, count = 0;
  for (let j = Math.max(1, i - n + 1); j <= i; j++) {
    const tr = Math.max(
      candles[j].h - candles[j].l,
      Math.abs(candles[j].h - candles[j - 1].c),
      Math.abs(candles[j].l - candles[j - 1].c),
    );
    sum += tr; count++;
  }
  return count ? sum / count : 0;
}

/**
 * Runs S1 over a candle slice. Signals are evaluated on bar i's close and
 * filled at bar i+1's OPEN — the doc is explicit that filling at the signal
 * bar's close flatters every backtest, because turn-of-candle is exactly where
 * HFT activity concentrates.
 */
export function runS1(candles: Candle[], funding: FundingPoint[], p: S1Params, costs: CostModel): Trade[] {
  const trades: Trade[] = [];
  const rt = roundTripBps(costs) / 10_000;
  let i = p.lookback + 1;

  while (i < candles.length - 1) {
    let hi = -Infinity, lo = Infinity;
    for (let j = i - p.lookback; j < i; j++) { hi = Math.max(hi, candles[j].h); lo = Math.min(lo, candles[j].l); }

    const close = candles[i].c;
    const dir: 1 | -1 | 0 = close > hi ? 1 : close < lo ? -1 : 0;
    if (dir === 0) { i++; continue; }

    const entryBar = i + 1;
    const entry = candles[entryBar].o;
    const stopDist = p.stopAtr * atr(candles, i, p.lookback);
    if (!(entry > 0) || !(stopDist > 0)) { i++; continue; }

    let exitBar = Math.min(entryBar + p.hold, candles.length - 1);
    let exitPx = candles[exitBar].o;
    let reason = 'time';

    for (let j = entryBar; j <= Math.min(entryBar + p.hold, candles.length - 1); j++) {
      const adverse = dir === 1 ? entry - candles[j].l : candles[j].h - entry;
      if (adverse >= stopDist) {
        exitBar = j;
        exitPx = dir === 1 ? entry - stopDist : entry + stopDist; // filled at the stop, not the extreme
        reason = 'stop';
        break;
      }
    }

    const grossRet = dir === 1 ? (exitPx - entry) / entry : (entry - exitPx) / entry;
    const fund = fundingCost(funding, candles[entryBar].t, candles[exitBar].t, dir);
    const netRet = grossRet - rt - fund;

    trades.push({
      entryT: candles[entryBar].t, exitT: candles[exitBar].t, dir,
      entry, exit: exitPx, grossRet, netRet, bars: exitBar - entryBar, reason,
    });

    i = exitBar + 1; // no pyramiding: one position at a time
  }
  return trades;
}

// ---------------------------------------------------------------------------
// Metrics
// ---------------------------------------------------------------------------

export interface Stats {
  trades: number; winRate: number; grossRetPct: number; netRetPct: number;
  avgNetBps: number; sharpe: number; maxDrawdownPct: number; stopRate: number;
}

export function stats(trades: Trade[], barsPerYear: number): Stats {
  const n = trades.length;
  if (n === 0) {
    return { trades: 0, winRate: 0, grossRetPct: 0, netRetPct: 0, avgNetBps: 0, sharpe: 0, maxDrawdownPct: 0, stopRate: 0 };
  }
  const wins = trades.filter(t => t.netRet > 0).length;
  const gross = trades.reduce((a, t) => a + t.grossRet, 0);
  const net = trades.reduce((a, t) => a + t.netRet, 0);
  const mean = net / n;
  const variance = trades.reduce((a, t) => a + (t.netRet - mean) ** 2, 0) / Math.max(1, n - 1);
  const sd = Math.sqrt(variance);

  // Annualised on realised trade frequency, not on an assumed one.
  const avgBars = trades.reduce((a, t) => a + Math.max(1, t.bars), 0) / n;
  const tradesPerYear = barsPerYear / avgBars;
  const sharpe = sd > 0 ? (mean / sd) * Math.sqrt(tradesPerYear) : 0;

  let equity = 0, peak = 0, maxDd = 0;
  for (const t of trades) {
    equity += t.netRet;
    peak = Math.max(peak, equity);
    maxDd = Math.min(maxDd, equity - peak);
  }

  return {
    trades: n,
    winRate: wins / n,
    grossRetPct: gross * 100,
    netRetPct: net * 100,
    avgNetBps: mean * 10_000,
    sharpe,
    maxDrawdownPct: maxDd * 100,
    stopRate: trades.filter(t => t.reason === 'stop').length / n,
  };
}

// ---------------------------------------------------------------------------
// Walk-forward
// ---------------------------------------------------------------------------

export interface WalkForwardResult {
  oos: Stats;
  folds: Array<{ trainBars: number; testBars: number; chosen: S1Params; testStats: Stats }>;
  gridSize: number;
}

/**
 * Fits parameters on each train window and scores them ONLY on the window that
 * follows. In-sample numbers are never reported — they are what makes an
 * overfit strategy look profitable.
 */
export function walkForward(
  candles: Candle[],
  funding: FundingPoint[],
  grid: S1Params[],
  costs: CostModel,
  folds: number,
  barsPerYear: number,
): WalkForwardResult {
  const usable = candles.length;
  const foldSize = Math.floor(usable / (folds + 1));
  const allOos: Trade[] = [];
  const detail: WalkForwardResult['folds'] = [];

  for (let f = 0; f < folds; f++) {
    const trainEnd = foldSize * (f + 1);
    const testEnd = Math.min(trainEnd + foldSize, usable);
    if (testEnd - trainEnd < 20) break;

    const train = candles.slice(0, trainEnd);
    const test = candles.slice(trainEnd, testEnd);

    let best: S1Params | null = null;
    let bestScore = -Infinity;
    for (const p of grid) {
      if (train.length < p.lookback + p.hold + 5) continue;
      const s = stats(runS1(train, funding, p, costs), barsPerYear);
      // Rank on net return, but require the sample to be non-trivial.
      const score = s.trades >= 10 ? s.netRetPct : -Infinity;
      if (score > bestScore) { bestScore = score; best = p; }
    }
    if (!best) continue;

    const testTrades = runS1(test, funding, best, costs);
    allOos.push(...testTrades);
    detail.push({ trainBars: train.length, testBars: test.length, chosen: best, testStats: stats(testTrades, barsPerYear) });
  }

  return { oos: stats(allOos, barsPerYear), folds: detail, gridSize: grid.length };
}

export function defaultGrid(): S1Params[] {
  const grid: S1Params[] = [];
  for (const lookback of [12, 24, 48, 96]) {
    for (const hold of [4, 8, 16, 32]) {
      for (const stopAtr of [1.5, 2.5]) grid.push({ lookback, hold, stopAtr });
    }
  }
  return grid;
}
