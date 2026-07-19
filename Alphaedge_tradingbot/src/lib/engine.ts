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
import { engineRounds, simulatorTrades, demoAccount } from '@/db/schema';
import { eq, and, lte, gte, sql } from 'drizzle-orm';
import { initDb } from '@/db/init';
import { binaryFairValue, settleBinary } from './binary';

export const ROUND_MS = 300_000; // 5-minute rounds — expiries align with 5m candle closes
export const DEMO_BANKROLL_BASE = 10_000;
const EDGE_THRESHOLD = 0.06;  // model conviction vs 50/50 opening odds — higher bar, fewer/stronger entries
const SPREAD = 0;             // paper fills at model fair value — expectancy ~breakeven, results = calibration vs reality
const MAX_TRADE_USD: Record<string, number> = { 'BTC-PERP': 1_000, 'ETH-PERP': 500, 'XAU': 1_000 };
const BANKROLL_FRACTION = 0.10;
const ENTRY_CUTOFF_S = 30;    // no entries in the final seconds

const ASSET_MAP: Record<string, string> = {
  'BTC-PERP': 'BTC',
  'ETH-PERP': 'ETH',
  'XAU': 'PAXG',
};
export const ENGINE_ASSETS = Object.keys(ASSET_MAP);

// Subscription levels: identical per-entry sizing everywhere ($1,000 XAU/BTC,
// $500 ETH). Levels differ ONLY by capital base and trades-per-day quota —
// the alpha comes from how much of the day's edge each tier may capture.
export const LEVELS: Record<number, { base: number | null; dailyTrades: number | null }> = {
  1: { base: 10_000, dailyTrades: 30 },
  2: { base: 25_000, dailyTrades: 60 },
  3: { base: null, dailyTrades: null }, // unlimited capital + trades
};
export const LEVEL_IDS = [1, 2, 3];

// Canonical parameters, exposed read-only to the dashboard
export const ENGINE_PARAMS = {
  roundSeconds: ROUND_MS / 1000,
  maxTradeUsd: MAX_TRADE_USD,
  bankrollFraction: BANKROLL_FRACTION,
  edgeThreshold: EDGE_THRESHOLD,
  spread: SPREAD,
  entryCutoffSeconds: ENTRY_CUTOFF_S,
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

const volCache: Record<string, { ts: number; vol: number }> = {};

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
  volCache[asset] = { ts: Date.now(), vol };
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

export interface LevelState {
  level: number;
  base: number | null;
  pnl: number;
  wins: number;
  losses: number;
  bankroll: number | null; // null = unlimited
  tradesToday: number;
  dailyTrades: number | null; // null = unlimited
}

export async function getLevelStates(startedAt: number): Promise<LevelState[]> {
  const utcDayStart = new Date().setUTCHours(0, 0, 0, 0);
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

    // Entries today = settled rows today + in-flight participations
    const settledToday = await db.select({ n: sql<number>`COUNT(*)` })
      .from(simulatorTrades)
      .where(and(eq(simulatorTrades.level, level), gte(simulatorTrades.createdAt, utcDayStart)));
    const openToday = await db.select({ n: sql<number>`COUNT(*)` })
      .from(engineRounds)
      .where(and(
        eq(engineRounds.status, 'open'),
        gte(engineRounds.entryAt, utcDayStart),
        sql`${engineRounds.levelSizes} LIKE ${'%"' + level + '":%'}`
      ));
    out.push({
      level,
      base: cfg.base,
      pnl,
      wins,
      losses,
      bankroll: cfg.base === null ? null : Math.round((cfg.base + pnl) * 100) / 100,
      tradesToday: (settledToday[0]?.n ?? 0) + (openToday[0]?.n ?? 0),
      dailyTrades: cfg.dailyTrades,
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
        const settled = settleBinary(round.strikePrice, expiryPrice, round.side as 'YES' | 'NO', lvlSize, round.entryPrice);
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
            side: round.side,
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

  const { bankroll, base: bankrollBase, startedAt: demoStartedAt } = await getDemoBankroll();
  const levels = await getLevelStates(demoStartedAt);

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
        const vol = await getRealizedVolPct(asset);
        const fv = binaryFairValue(mark, round.strikePrice, vol, remainingS);
        const conviction = Math.abs(fv.pYes - 0.5);
        if (conviction >= EDGE_THRESHOLD) {
          const side = fv.pYes > 0.5 ? 'YES' : 'NO';
          const modelP = side === 'YES' ? fv.pYes : 1 - fv.pYes;
          const entryPrice = Math.min(Math.max(modelP + SPREAD, 0.02), 0.98);
          const assetCap = MAX_TRADE_USD[asset] ?? 1_000;

          const levelSizes: Record<string, number> = {};
          for (const ls of levels) {
            if (ls.dailyTrades !== null && ls.tradesToday >= ls.dailyTrades) continue; // quota spent
            if (ls.bankroll !== null && ls.bankroll <= 0) continue; // busted
            const budget = ls.bankroll === null
              ? assetCap
              : Math.min(assetCap, ls.bankroll * BANKROLL_FRACTION);
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
  return { now, epoch, bankroll, bankrollBase, demoStartedAt, levels, rounds, settled: settledCount, errors };
}
