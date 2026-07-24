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
import { engineRounds, simulatorTrades, demoAccount, assetState } from '@/db/schema';
import { eq, and, lte, gte, sql } from 'drizzle-orm';
import { initDb } from '@/db/init';
import { binaryFairValue, settleBinary } from './binary';
import { resolveRegime, CAUTION_RISK_MULT, CAUTION_EDGE, type Regime } from './regime';
import { maybeSyncRegimeCalendar } from './calendar';

export const ROUND_MS = 300_000; // 5-minute rounds — expiries align with 5m candle closes
export const DEMO_BANKROLL_BASE = 10_000;
const EDGE_THRESHOLD = 0.06;  // model conviction vs 50/50 opening odds — higher bar, fewer/stronger entries
const SPREAD = 0;             // paper fills at model fair value — expectancy ~breakeven, results = calibration vs reality
const RISK_PER_TRADE = 0.02; // fixed-fractional: 2% of current equity per trade, all tiers
const ENTRY_CUTOFF_S = 30;    // no entries in the final seconds

const ASSET_MAP: Record<string, string> = {
  'BTC-PERP': 'BTC',
  'ETH-PERP': 'ETH',
  'XAU': 'PAXG',
};
export const ENGINE_ASSETS = Object.keys(ASSET_MAP);

// Subscription tiers: fixed-fractional sizing — every entry risks 2% of the
// tier's CURRENT equity (compounds with wins, de-risks in drawdowns).
// Tiers differ by capital base and trades-per-day quota. Tier 4 is the free
// Demo ledger shown first on the desk.
export const LEVELS: Record<number, { base: number | null; dailyTrades: number | null; label: string }> = {
  4: { base: 10_000, dailyTrades: null, label: 'Demo' }, // unlimited trades during public demo
  1: { base: 5_000, dailyTrades: 50, label: 'Level 1' },
  2: { base: 10_000, dailyTrades: 100, label: 'Level 2' },
  3: { base: 25_000, dailyTrades: 250, label: 'Level 3' }, // displayed as $25K+
};
export const LEVEL_IDS = [4, 1, 2, 3];

// Daily quota window rolls at 13:00 UTC — the doorstep of the US session
// (9:00 ET summer / 8:00 ET winter), where BTC/ETH/PAXG liquidity peaks.
// Every tier enters US hours with a full book, and the fresh quota is spent
// on prime-time entries first; the overnight Asia session trades leftovers.
export const QUOTA_RESET_UTC_HOUR = 13;

// Most recent 13:00 UTC at/before `now`.
export function lastQuotaReset(now: number): number {
  const todayReset = new Date(now).setUTCHours(QUOTA_RESET_UTC_HOUR, 0, 0, 0);
  return todayReset <= now ? todayReset : todayReset - 86_400_000;
}

// Next 13:00 UTC after `now` — when spent quotas re-open.
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
  edgeThreshold: EDGE_THRESHOLD,
  spread: SPREAD,
  entryCutoffSeconds: ENTRY_CUTOFF_S,
  trendGate: process.env.TREND_FILTER === 'on' ? TREND_GATE : null,
  trendLookbackMinutes: (TREND_LOOKBACK_BARS * 5),
  dailyStopPct: process.env.DAILY_STOP !== 'off'
    ? Math.max(0.02, parseFloat(process.env.DAILY_STOP_PCT || '0.15'))
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
  dailyStopActive: boolean; // lost > DAILY_STOP_PCT of day-start equity today
}

export async function getLevelStates(startedAt: number, dayResetAt?: number | null): Promise<LevelState[]> {
  // Daily quota window starts at the last 13:00 UTC roll, the demo restart,
  // or an operator day-reset — whichever is latest. A fresh demo must not
  // inherit spent quota, and an operator reset clears counters + breakers
  // immediately without touching ledger history.
  const utcDayStart = Math.max(lastQuotaReset(Date.now()), startedAt, dayResetAt ?? 0);
  const out: LevelState[] = [];
  for (const level of LEVEL_IDS) {
    const cfg = LEVELS[level];
    const aggRow = await db.select({
      total: sql<number>`COALESCE(SUM(${simulatorTrades.pnl}), 0)`,
      wins: sql<number>`COALESCE(SUM(CASE WHEN ${simulatorTrades.outcome} = 'WIN' THEN 1 ELSE 0 END), 0)`,
      settled: sql<number>`COUNT(*)`,
    })
      .from(simulatorTrades)
      .where(and(eq(simulatorTrades.level, level), gte(simulatorTrades.createdAt, startedAt)));
    const pnl = Math.round((aggRow[0]?.total ?? 0) * 100) / 100;
    const wins = aggRow[0]?.wins ?? 0;
    const losses = (aggRow[0]?.settled ?? 0) - wins;

    // Entries today = settled rows today + in-flight participations.
    // Same scan also sums today's pnl for the daily circuit breaker.
    const settledToday = await db.select({
      n: sql<number>`COUNT(*)`,
      pnlToday: sql<number>`COALESCE(SUM(${simulatorTrades.pnl}), 0)`,
    })
      .from(simulatorTrades)
      .where(and(eq(simulatorTrades.level, level), gte(simulatorTrades.createdAt, utcDayStart)));
    const openToday = await db.select({ n: sql<number>`COUNT(*)` })
      .from(engineRounds)
      .where(and(
        eq(engineRounds.status, 'open'),
        gte(engineRounds.entryAt, utcDayStart),
        sql`${engineRounds.levelSizes} LIKE ${'%"' + level + '":%'}`
      ));
    const pnlToday = Math.round((settledToday[0]?.pnlToday ?? 0) * 100) / 100;
    const bankroll = cfg.base === null ? null : Math.round((cfg.base + pnl) * 100) / 100;
    const dayStartEquity = bankroll === null ? null : bankroll - pnlToday;
    const dailyStopActive = dailyStopEnabled() && dayStartEquity !== null && dayStartEquity > 0
      && pnlToday <= -DAILY_STOP_PCT * dayStartEquity;
    out.push({
      level,
      label: cfg.label,
      base: cfg.base,
      pnl,
      wins,
      losses,
      bankroll,
      tradesToday: (settledToday[0]?.n ?? 0) + (openToday[0]?.n ?? 0),
      dailyTrades: cfg.dailyTrades,
      pnlToday,
      dailyStopActive,
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
  const effRiskPerTrade = regime.mode === 'caution' ? RISK_PER_TRADE * CAUTION_RISK_MULT : RISK_PER_TRADE;

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
            if (ls.dailyStopActive) continue; // daily loss circuit breaker tripped
            if (ls.bankroll === null || ls.bankroll <= 0) continue; // busted / undefined
            const budget = ls.bankroll * effRiskPerTrade; // 2% of current equity (1% in caution)
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
