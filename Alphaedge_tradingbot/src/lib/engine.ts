// Canonical server-side round engine.
//
// Rounds are deterministic 90-second epochs per asset (epoch = floor(t/90s)).
// On every tick (viewer polls + cron heartbeat) the engine:
//   1. settles any expired open rounds using the real 1m candle close at expiry
//      (falls back to the live mark when the expiry candle hasn't closed yet),
//   2. opens the current epoch's round, locking the strike at the live mark,
//   3. takes a position when the GBM model's conviction clears the edge
//      threshold, sized against the shared $10K demo bankroll.
//
// Viewers never write — the engine is the only author of canonical rounds.

import { db } from '@/db';
import { engineRounds, simulatorTrades, demoAccount, assetState, levelLocks } from '@/db/schema';
import { eq, and, lte, gte, sql } from 'drizzle-orm';
import { initDb } from '@/db/init';
import { binaryFairValue, settleBinary } from './binary';
import { resolveRegime, CAUTION_RISK_MULT, CAUTION_EDGE, type Regime } from './regime';
import { maybeSyncRegimeCalendar } from './calendar';

export const ROUND_MS = 300_000; // 5-minute rounds — expiries align with 5m candle closes
export const DEMO_BANKROLL_BASE = 10_000;
const EDGE_THRESHOLD = 0.06;  // model conviction vs 50/50 opening odds — higher bar, fewer/stronger entries
const SPREAD = 0;             // paper fills at model fair value — expectancy ~breakeven, results = calibration vs reality
const RISK_PER_TRADE = 0.02; // fixed-fractional: 2% of current equity per trade
// De-risk step for compounded books: past $100K equity, 2% a round swings six
// figures — sizing steps down to 0.5%. Applies to any tier that crosses the
// threshold (Gold's uncapped lane is the one that lives there).
const RISK_PER_TRADE_LARGE = 0.005;
const LARGE_BOOK_THRESHOLD = 100_000;

export function riskPerTradeFor(bankroll: number): number {
  return bankroll > LARGE_BOOK_THRESHOLD ? RISK_PER_TRADE_LARGE : RISK_PER_TRADE;
}
const ENTRY_CUTOFF_S = 30;    // no entries in the final seconds

const ASSET_MAP: Record<string, string> = {
  'BTC-PERP': 'BTC',
  'ETH-PERP': 'ETH',
  'XAU': 'PAXG',
};
export const ENGINE_ASSETS = Object.keys(ASSET_MAP);

// Subscription tiers: fixed-fractional sizing — every entry risks 2% of the
// tier's CURRENT equity (compounds with wins, de-risks in drawdowns).
// Tiers differ by capital base and trades-per-day quota. Tier 4 (GOLD) is the
// uncapped flagship lane shown first on the desk: no quota, no profit lock,
// no daily loss stop — it runs 24x7.
export const LEVELS: Record<number, { base: number | null; dailyTrades: number | null; label: string }> = {
  4: { base: 10_000, dailyTrades: null, label: 'Gold' }, // uncapped: exempt from quota, profit lock and loss stop
  1: { base: 5_000, dailyTrades: 50, label: 'Level 1' },
  2: { base: 10_000, dailyTrades: 100, label: 'Level 2' },
  3: { base: 25_000, dailyTrades: 250, label: 'Level 3' }, // displayed as $25K+
};
export const LEVEL_IDS = [4, 1, 2, 3];

// The trading day rolls at 00:00 UTC. One reference point serves all three
// daily gates: trade quota, the +28% profit lock and the -15% loss breaker
// are every one measured against the tier's equity at this boundary.
export const QUOTA_RESET_UTC_HOUR = 0;

// Most recent 00:00 UTC at/before `now`.
export function lastQuotaReset(now: number): number {
  const todayReset = new Date(now).setUTCHours(QUOTA_RESET_UTC_HOUR, 0, 0, 0);
  return todayReset <= now ? todayReset : todayReset - 86_400_000;
}

// Next 00:00 UTC after `now` — when quotas and the profit lock re-open.
export function nextQuotaReset(now: number): number {
  return lastQuotaReset(now) + 86_400_000;
}

// Counter-trend entry gate (task #8) — DEFAULT OFF after the 30-day
// multi-regime backtest (23k trades, Binance 1m history) showed the gate
// removes profitable trades: counter-trend entries win at ~72.5%, same as
// everything else, and gating them cost ~20% of net P&L across regimes.
// The 2-day ledger replay that motivated the gate was a crash-window
// artifact. Machinery retained: opt back in with TREND_FILTER=on if a
// future regime justifies it.
const TREND_LOOKBACK_BARS = 12; // 12 × 5m candles = 1 hour
const TREND_GATE = 0.002;       // 0.2% adverse 1h move blocks counter-trend entry
const trendFilterEnabled = () => process.env.TREND_FILTER === 'on';

// Canonical parameters, exposed read-only to the dashboard
export const ENGINE_PARAMS = {
  roundSeconds: ROUND_MS / 1000,
  riskPerTrade: RISK_PER_TRADE,
  largeBookRiskPerTrade: RISK_PER_TRADE_LARGE,
  largeBookThreshold: LARGE_BOOK_THRESHOLD,
  edgeThreshold: EDGE_THRESHOLD,
  spread: SPREAD,
  entryCutoffSeconds: ENTRY_CUTOFF_S,
  trendGate: process.env.TREND_FILTER === 'on' ? TREND_GATE : null,
  trendLookbackMinutes: (TREND_LOOKBACK_BARS * 5),
  dailyStopPct: process.env.DAILY_STOP !== 'off'
    ? Math.max(0.02, parseFloat(process.env.DAILY_STOP_PCT || '0.15'))
    : null,
  lossLockHours: Math.max(1, parseFloat(process.env.LOSS_LOCK_HOURS || '24')),
  dailyProfitLockPct: process.env.DAILY_PROFIT_LOCK !== 'off'
    ? Math.max(0.01, parseFloat(process.env.DAILY_PROFIT_LOCK_PCT || '0.28'))
    : null,
};

// ---------------------------------------------------------------------------
// Hyperliquid feed helpers (module-cached; serverless instances refetch cheaply)
// ---------------------------------------------------------------------------

let marksCache: { ts: number; marks: Record<string, number> } | null = null;

export async function getMarks(): Promise<Record<string, number>> {
  if (marksCache && Date.now() - marksCache.ts < 1500) return marksCache.marks;
  const res = await fetch('https://api.hyperliquid.xyz/info', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type: 'allMids' }),
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`Hyperliquid allMids ${res.status}`);
  const mids = await res.json();
  const marks: Record<string, number> = {};
  for (const [label, coin] of Object.entries(ASSET_MAP)) {
    const v = parseFloat(mids[coin]);
    if (Number.isFinite(v) && v > 0) marks[label] = v;
  }
  marksCache = { ts: Date.now(), marks };
  return marks;
}

const volCache: Record<string, { ts: number; vol: number; trend1h: number | null }> = {};

// 1-hour price trend from the same candle fetch that feeds the vol input —
// zero additional API calls or DB reads.
export async function getTrend1h(asset: string): Promise<number | null> {
  await getRealizedVolPct(asset); // populates the shared cache
  return volCache[asset]?.trend1h ?? null;
}

async function getRealizedVolPct(asset: string): Promise<number> {
  const cached = volCache[asset];
  if (cached && Date.now() - cached.ts < 5 * 60_000) return cached.vol;
  const coin = ASSET_MAP[asset];
  const end = Date.now();
  const res = await fetch('https://api.hyperliquid.xyz/info', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      type: 'candleSnapshot',
      req: { coin, interval: '5m', startTime: end - 24 * 60 * 60 * 1000, endTime: end },
    }),
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`candleSnapshot ${coin} ${res.status}`);
  const candles = await res.json();
  const closes = (Array.isArray(candles) ? candles : []).map((k: any) => parseFloat(k.c)).filter(Number.isFinite);
  if (closes.length < 10) throw new Error(`Insufficient candle history for ${asset}`);
  const rets: number[] = [];
  for (let i = 1; i < closes.length; i++) rets.push(Math.log(closes[i] / closes[i - 1]));
  const mean = rets.reduce((a, b) => a + b, 0) / rets.length;
  const variance = rets.reduce((a, b) => a + (b - mean) ** 2, 0) / (rets.length - 1);
  const vol = Math.sqrt(variance * ((365 * 24 * 60) / 5)) * 100;
  const past = closes.length > TREND_LOOKBACK_BARS ? closes[closes.length - 1 - TREND_LOOKBACK_BARS] : null;
  const trend1h = past ? (closes[closes.length - 1] - past) / past : null;
  volCache[asset] = { ts: Date.now(), vol, trend1h };
  return vol;
}

// Real close of the 1m candle containing `atMs`, or null if not closed yet.
async function getCandleCloseAt(asset: string, atMs: number): Promise<number | null> {
  const coin = ASSET_MAP[asset];
  const res = await fetch('https://api.hyperliquid.xyz/info', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      type: 'candleSnapshot',
      req: { coin, interval: '1m', startTime: atMs - 2 * 60_000, endTime: atMs + 2 * 60_000 },
    }),
    cache: 'no-store',
  });
  if (!res.ok) return null;
  const candles = await res.json();
  if (!Array.isArray(candles)) return null;
  const hit = candles.find((k: any) => k.t <= atMs && atMs < k.t + 60_000);
  // Only trust a candle that has fully closed
  if (hit && Date.now() >= hit.t + 60_000) {
    const c = parseFloat(hit.c);
    return Number.isFinite(c) ? c : null;
  }
  return null;
}

// ---------------------------------------------------------------------------

// Single shared demo account row; created on first touch with a fresh start.
export async function getDemoAccount() {
  const rows = await db.select().from(demoAccount).where(eq(demoAccount.id, 'demo'));
  if (rows.length > 0) return rows[0];
  const fresh = { id: 'demo', baseUsd: DEMO_BANKROLL_BASE, startedAt: Date.now() };
  await db.insert(demoAccount).values(fresh).onConflictDoNothing();
  const re = await db.select().from(demoAccount).where(eq(demoAccount.id, 'demo'));
  return re[0] ?? fresh;
}

// Equity counts only rounds settled at/after the demo start marker.
export async function getDemoBankroll(): Promise<{ bankroll: number; base: number; startedAt: number }> {
  const acct = await getDemoAccount();
  const rows = await db.select({ total: sql<number>`COALESCE(SUM(${simulatorTrades.pnl}), 0)` })
    .from(simulatorTrades)
    .where(gte(simulatorTrades.createdAt, acct.startedAt));
  return {
    bankroll: Math.round((acct.baseUsd + (rows[0]?.total ?? 0)) * 100) / 100,
    base: acct.baseUsd,
    startedAt: acct.startedAt,
  };
}

// Daily loss circuit breaker: a tier that has lost more than this fraction
// of its day-start equity (13:00 UTC roll) stops entering until the next
// roll. Catastrophe insurance, not signal: live data shows normal days dip
// ≤3.4% intraday while the 2026-07-24 crash bled −33% before a manual halt —
// this automates that halt at a pre-agreed line. DAILY_STOP=off disables;
// DAILY_STOP_PCT overrides the threshold.
const DAILY_STOP_PCT = Math.max(0.02, parseFloat(process.env.DAILY_STOP_PCT || '0.15'));
const dailyStopEnabled = () => process.env.DAILY_STOP !== 'off';

// Loss breaker release is ROLLING, not calendar-based: a tripped tier reopens
// 24h after the trip. Because 24h always spans a midnight, the tier's next
// day-start equity is already the post-loss value — the reference re-baselines
// on its own, so repeated trips cost 15% of a progressively smaller base
// rather than cascading within a single day.
const LOSS_LOCK_MS = Math.max(1, parseFloat(process.env.LOSS_LOCK_HOURS || '24')) * 3_600_000;

// Profit lock: a tier that books +28% on the day stops entering until the next
// 00:00 UTC roll. A CEILING, never a promise — reaching it is not guaranteed.
const DAILY_PROFIT_LOCK_PCT = Math.max(0.01, parseFloat(process.env.DAILY_PROFIT_LOCK_PCT || '0.28'));
const profitLockEnabled = () => process.env.DAILY_PROFIT_LOCK !== 'off';

// GOLD (tier 4) is the uncapped showcase lane: exempt from every daily gate.
const UNCAPPED_LEVELS = new Set([4]);

export interface LevelState {
  level: number;
  label: string;
  base: number | null;
  pnl: number;
  wins: number;
  losses: number;
  bankroll: number | null; // null = unlimited
  tradesToday: number;
  dailyTrades: number | null; // null = unlimited
  pnlToday: number;
  dailyStopActive: boolean;   // -15% breaker tripped; rolling release
  lossLockedUntil: number | null; // ms the breaker releases, null when clear
  profitLockActive: boolean;  // +28% booked today; releases at next 00:00 UTC
  uncapped: boolean;          // GOLD: exempt from quota, profit lock, loss stop
}

export async function getLevelStates(startedAt: number, dayResetAt?: number | null): Promise<LevelState[]> {
  // Daily window starts at the last 00:00 UTC roll, the demo restart, or an
  // operator day-reset — whichever is latest. One reference for all three
  // gates: quota, +28% profit lock, -15% loss breaker.
  const now = Date.now();
  const utcDayStart = Math.max(lastQuotaReset(now), startedAt, dayResetAt ?? 0);
  // Rolling breaker state for every tier in one query.
  const lockRows = await db.select().from(levelLocks);
  const locks = new Map(lockRows.map(r => [r.level, r]));
  const out: LevelState[] = [];
  for (const level of LEVEL_IDS) {
    const cfg = LEVELS[level];
    // ONE atomic aggregate for the whole tier: lifetime totals AND the split
    // either side of the day boundary. Splitting this across two queries let a
    // stale cumulative read pair with a fresh daily read — and because
    // day-start equity used to be DERIVED (bankroll - pnlToday), that skew
    // silently moved the profit-lock threshold and fired it early. Measuring
    // both halves in a single snapshot makes that class of bug impossible.
    const aggRow = await db.select({
      total: sql<number>`COALESCE(SUM(${simulatorTrades.pnl}), 0)`,
      wins: sql<number>`COALESCE(SUM(CASE WHEN ${simulatorTrades.outcome} = 'WIN' THEN 1 ELSE 0 END), 0)`,
      settled: sql<number>`COUNT(*)`,
      pnlBefore: sql<number>`COALESCE(SUM(CASE WHEN ${simulatorTrades.createdAt} < ${utcDayStart} THEN ${simulatorTrades.pnl} ELSE 0 END), 0)`,
      pnlToday: sql<number>`COALESCE(SUM(CASE WHEN ${simulatorTrades.createdAt} >= ${utcDayStart} THEN ${simulatorTrades.pnl} ELSE 0 END), 0)`,
      tradesToday: sql<number>`COALESCE(SUM(CASE WHEN ${simulatorTrades.createdAt} >= ${utcDayStart} THEN 1 ELSE 0 END), 0)`,
    })
      .from(simulatorTrades)
      .where(and(eq(simulatorTrades.level, level), gte(simulatorTrades.createdAt, startedAt)));
    const pnl = Math.round((aggRow[0]?.total ?? 0) * 100) / 100;
    const wins = aggRow[0]?.wins ?? 0;
    const losses = (aggRow[0]?.settled ?? 0) - wins;
    const openToday = await db.select({ n: sql<number>`COUNT(*)` })
      .from(engineRounds)
      .where(and(
        eq(engineRounds.status, 'open'),
        gte(engineRounds.entryAt, utcDayStart),
        sql`${engineRounds.levelSizes} LIKE ${'%"' + level + '":%'}`
      ));
    const pnlToday = Math.round((aggRow[0]?.pnlToday ?? 0) * 100) / 100;
    const bankroll = cfg.base === null ? null : Math.round((cfg.base + pnl) * 100) / 100;
    // Measured from the same snapshot as pnlToday — never derived by subtraction.
    const dayStartEquity = cfg.base === null
      ? null
      : Math.round((cfg.base + (aggRow[0]?.pnlBefore ?? 0)) * 100) / 100;
    const uncapped = UNCAPPED_LEVELS.has(level);
    const lock = locks.get(level);

    // --- +28% profit lock: STICKY for the UTC day ---------------------------
    // Once the ceiling is booked the tier is done for the day. Without this it
    // could unlock itself when already-open positions settled at a loss and
    // dragged the day's gain back under the threshold.
    let profitLockActive = false;
    if (!uncapped && profitLockEnabled() && dayStartEquity !== null && dayStartEquity > 0) {
      const lockedEarlierToday = lock?.profitLockedAt != null && lock.profitLockedAt >= utcDayStart;
      if (lockedEarlierToday) {
        profitLockActive = true;
      } else if (pnlToday >= DAILY_PROFIT_LOCK_PCT * dayStartEquity) {
        profitLockActive = true;
        await db.insert(levelLocks)
          .values({ level, profitLockedAt: now, updatedAt: now })
          .onConflictDoUpdate({
            target: levelLocks.level,
            set: { profitLockedAt: now, updatedAt: now },
          });
        locks.set(level, { ...(lock ?? { level, lossLockedAt: null, releasedAt: null, releaseEquity: null }), profitLockedAt: now } as any);
      }
    }

    // --- -15% loss breaker: rolling release, persisted ----------------------
    // Threshold is measured from the equity at the start of the CURRENT
    // breaker window: normally the day-start equity, or the equity at the
    // last release when that came later (so a second trip costs 15% of the
    // reduced base instead of re-firing on the same day's earlier losses).
    let lossLockedUntil: number | null = null;
    if (!uncapped && dailyStopEnabled() && bankroll !== null) {
      if (lock?.lossLockedAt && now < lock.lossLockedAt + LOSS_LOCK_MS) {
        lossLockedUntil = lock.lossLockedAt + LOSS_LOCK_MS; // still serving the lock
      } else {
        if (lock?.lossLockedAt) {
          // Lock just expired — release and re-baseline off current equity.
          await db.update(levelLocks)
            .set({ lossLockedAt: null, releasedAt: now, releaseEquity: bankroll, updatedAt: now })
            .where(eq(levelLocks.level, level));
          locks.set(level, { ...lock, lossLockedAt: null, releasedAt: now, releaseEquity: bankroll });
        } else {
          const useRelease = lock?.releasedAt != null && lock.releasedAt > utcDayStart
            && lock.releaseEquity != null && lock.releaseEquity > 0;
          const baseline = useRelease ? (lock!.releaseEquity as number) : dayStartEquity;
          if (baseline !== null && baseline > 0 && bankroll <= baseline * (1 - DAILY_STOP_PCT)) {
            await db.insert(levelLocks)
              .values({ level, lossLockedAt: now, releasedAt: null, releaseEquity: null, updatedAt: now })
              .onConflictDoUpdate({
                target: levelLocks.level,
                set: { lossLockedAt: now, releasedAt: null, releaseEquity: null, updatedAt: now },
              });
            lossLockedUntil = now + LOSS_LOCK_MS;
          }
        }
      }
    }

    out.push({
      level,
      label: cfg.label,
      base: cfg.base,
      pnl,
      wins,
      losses,
      bankroll,
      tradesToday: (aggRow[0]?.tradesToday ?? 0) + (openToday[0]?.n ?? 0),
      dailyTrades: cfg.dailyTrades,
      pnlToday,
      dailyStopActive: lossLockedUntil !== null,
      lossLockedUntil,
      profitLockActive,
      uncapped,
    });
  }
  return out;
}

export interface TickResult {
  now: number;
  epoch: number;
  bankroll: number;
  bankrollBase: number;
  demoStartedAt: number;
  levels: LevelState[];
  rounds: Array<typeof engineRounds.$inferSelect>;
  settled: number;
  regime: Regime;
  quotaResetAt: number; // next 13:00 UTC roll — daily trade quotas re-open here
  assetEnabled: Record<string, boolean>; // per-asset operator kill switches
  errors: string[];
}

export async function engineTick(): Promise<TickResult> {
  await initDb();
  const now = Date.now();
  const epoch = Math.floor(now / ROUND_MS);
  const errors: string[] = [];
  let settledCount = 0;

  let marks: Record<string, number> = {};
  try {
    marks = await getMarks();
  } catch (err: any) {
    errors.push(`feed: ${err.message}`);
  }

  // 1. Settle expired open rounds (any asset, any age)
  const expired = await db.select().from(engineRounds)
    .where(and(eq(engineRounds.status, 'open'), lte(engineRounds.expiresAt, now)));

  for (const round of expired) {
    try {
      if (!round.side || !round.size || !round.entryPrice) {
        await db.update(engineRounds)
          .set({ status: 'skipped', settledAt: now })
          .where(eq(engineRounds.id, round.id));
        continue;
      }
      // Accurate expiry price from the closed 1m candle; fall back to live mark
      // only when settling within moments of expiry.
      let expiryPrice = await getCandleCloseAt(round.asset, round.expiresAt - 1);
      if (expiryPrice === null) {
        const fresh = now - round.expiresAt < 10_000 ? marks[round.asset] : undefined;
        if (fresh) expiryPrice = fresh;
        else continue; // candle not closed yet — retry on a later tick
      }

      // Settle each participating level with its own size (entries identical
      // across levels; only participation differs by quota/bankroll).
      let levelSizes: Record<string, number> = {};
      try { levelSizes = JSON.parse(round.levelSizes || '{}'); } catch { /* legacy */ }
      if (Object.keys(levelSizes).length === 0 && round.size) {
        levelSizes = { '0': round.size }; // legacy un-leveled round
      }
      for (const [lvlKey, lvlSize] of Object.entries(levelSizes)) {
        if (!lvlSize || lvlSize <= 0) continue;
        // Normalize any legacy in-flight rows written before the BUY/SELL rename
        const sideNorm = round.side === 'YES' ? 'BUY' : round.side === 'NO' ? 'SELL' : round.side;
        const settled = settleBinary(round.strikePrice, expiryPrice, sideNorm as 'BUY' | 'SELL', lvlSize, round.entryPrice);
        const level = Number(lvlKey);
        const tradeId = `${round.asset}_${round.epoch}_L${level}`;
        const existing = await db.select({ id: simulatorTrades.id }).from(simulatorTrades)
          .where(and(
            eq(simulatorTrades.asset, round.asset),
            eq(simulatorTrades.roundId, round.epoch),
            eq(simulatorTrades.level, level),
          ))
          .limit(1);
        if (existing.length === 0) {
          await db.insert(simulatorTrades).values({
            id: tradeId,
            level,
            roundId: round.epoch,
            asset: round.asset,
            timestamp: new Date(now).toISOString(),
            strikePrice: round.strikePrice,
            expiryPrice,
            side: sideNorm,
            size: lvlSize,
            entryPrice: round.entryPrice,
            exitPrice: settled.exitPrice,
            outcome: settled.outcome,
            pnl: settled.pnl,
            createdAt: now,
          });
          settledCount++;
        }
      }
      await db.update(engineRounds)
        .set({ status: 'settled', settledAt: now })
        .where(eq(engineRounds.id, round.id));
    } catch (err: any) {
      errors.push(`settle ${round.id}: ${err.message}`);
    }
  }

  const acctRow = await getDemoAccount();
  const { bankroll, base: bankrollBase, startedAt: demoStartedAt } = await getDemoBankroll();
  const levels = await getLevelStates(demoStartedAt, (acctRow as any).dayResetAt ?? null);

  // Keep the blackout calendar fresh from the economic-calendar feed
  // (throttled internally; a dead feed degrades to the existing windows).
  try {
    await maybeSyncRegimeCalendar(now);
  } catch (err: any) {
    errors.push(`calendar sync: ${err.message}`);
  }

  // Regime Guard: resolve once per tick. Gates ENTRIES only — settlement
  // above ran unconditionally and must always run. Resolver failure fails
  // SAFE: an engine that can't read its risk state does not take risk.
  let regime: Regime;
  try {
    regime = await resolveRegime(now);
  } catch (err: any) {
    regime = { mode: 'lockdown', reason: 'regime resolver unavailable', source: 'system', until: null };
    errors.push(`regime: ${err.message}`);
  }
  // Caution keeps trading with half size and a raised conviction bar
  const effEdgeThreshold = regime.mode === 'caution' ? CAUTION_EDGE : EDGE_THRESHOLD;
  const cautionRiskMult = regime.mode === 'caution' ? CAUTION_RISK_MULT : 1;

  // Per-asset kill switches: operator can halt one asset while the rest
  // trade. Missing row = enabled. Open positions still settle normally.
  const assetEnabled: Record<string, boolean> = Object.fromEntries(ENGINE_ASSETS.map(a => [a, true]));
  try {
    const toggles = await db.select().from(assetState);
    for (const t of toggles) if (t.asset in assetEnabled) assetEnabled[t.asset] = !!t.enabled;
  } catch (err: any) {
    errors.push(`assetState: ${err.message}`); // fail open: all assets trade
  }

  // 2. Open current-epoch rounds + take positions
  for (const asset of ENGINE_ASSETS) {
    const mark = marks[asset];
    if (!mark) continue;
    const id = `${asset}_${epoch}`;
    try {
      const rows = await db.select().from(engineRounds).where(eq(engineRounds.id, id));
      let round = rows[0];

      if (!round) {
        await db.insert(engineRounds).values({
          id,
          asset,
          epoch,
          startedAt: epoch * ROUND_MS,
          expiresAt: (epoch + 1) * ROUND_MS,
          strikePrice: mark,
          status: 'open',
        }).onConflictDoNothing();
        const re = await db.select().from(engineRounds).where(eq(engineRounds.id, id));
        round = re[0];
      }

      // Entry decision for flat open rounds: identical signal + sizing for
      // every level — participation gated only by daily quota and bankroll.
      const remainingS = (round.expiresAt - now) / 1000;
      if (round.status === 'open' && !round.side && remainingS >= ENTRY_CUTOFF_S) {
        // Lockdown: powder stays dry. Stamp the reason so the round history
        // shows the engine sat out on purpose, then take no position.
        if (regime.mode === 'lockdown') {
          if (!round.skipReason) {
            await db.update(engineRounds)
              .set({ skipReason: `regime:${regime.reason}` })
              .where(and(eq(engineRounds.id, id), sql`${engineRounds.side} IS NULL`));
          }
          continue;
        }
        // Operator halted this asset — sit out, visibly.
        if (!assetEnabled[asset]) {
          if (!round.skipReason) {
            await db.update(engineRounds)
              .set({ skipReason: 'asset:halted by operator' })
              .where(and(eq(engineRounds.id, id), sql`${engineRounds.side} IS NULL`));
          }
          continue;
        }
        const vol = await getRealizedVolPct(asset);
        const fv = binaryFairValue(mark, round.strikePrice, vol, remainingS);
        const conviction = Math.abs(fv.pYes - 0.5);
        if (conviction >= effEdgeThreshold) {
          const side = fv.pYes > 0.5 ? 'BUY' : 'SELL';
          // Counter-trend gate: don't fight a decisive 1-hour move.
          if (trendFilterEnabled()) {
            const trend = await getTrend1h(asset);
            if (trend !== null &&
                ((side === 'BUY' && trend < -TREND_GATE) || (side === 'SELL' && trend > TREND_GATE))) {
              await db.update(engineRounds)
                .set({ skipReason: `trend:counter-trend ${side} gated (1h ${(trend * 100).toFixed(2)}%)` })
                .where(and(eq(engineRounds.id, id), sql`${engineRounds.side} IS NULL`));
              continue;
            }
          }
          const modelP = side === 'BUY' ? fv.pYes : 1 - fv.pYes;
          const entryPrice = Math.min(Math.max(modelP + SPREAD, 0.02), 0.98);

          const levelSizes: Record<string, number> = {};
          for (const ls of levels) {
            if (ls.dailyTrades !== null && ls.tradesToday >= ls.dailyTrades) continue; // quota spent
            if (ls.dailyStopActive) continue; // -15% breaker tripped (rolling release)
            if (ls.profitLockActive) continue; // +28% booked — locked until 00:00 UTC
            if (ls.bankroll === null || ls.bankroll <= 0) continue; // busted / undefined
            // 2% of current equity, stepping to 0.5% past $100K; halved in caution
            const budget = ls.bankroll * riskPerTradeFor(ls.bankroll) * cautionRiskMult;
            const size = Math.floor(budget / entryPrice);
            if (size > 0) levelSizes[String(ls.level)] = size;
          }

          if (Object.keys(levelSizes).length > 0) {
            const refSize = levelSizes['3'] ?? Object.values(levelSizes)[0];
            await db.update(engineRounds)
              .set({
                side, size: refSize, entryPrice, entryAt: now, entryPYes: fv.pYes,
                levelSizes: JSON.stringify(levelSizes),
              })
              .where(and(eq(engineRounds.id, id), sql`${engineRounds.side} IS NULL`));
            // count the in-flight participation for this tick's quota view
            for (const ls of levels) {
              if (levelSizes[String(ls.level)]) ls.tradesToday++;
            }
          }
        }
      }
    } catch (err: any) {
      errors.push(`open ${id}: ${err.message}`);
    }
  }

  const rounds = await db.select().from(engineRounds).where(eq(engineRounds.epoch, epoch));
  return { now, epoch, bankroll, bankrollBase, demoStartedAt, levels, rounds, settled: settledCount, regime, quotaResetAt: nextQuotaReset(now), assetEnabled, errors };
}
