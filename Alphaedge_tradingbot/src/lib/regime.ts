// Regime Guard — resolves the current trading regime before every entry.
//
// Three layers, most severe active mode wins; ties broken by precedence
// manual > auto shock > calendar:
//   1. manual   — owner-set override in regime_state (kill switch)
//   2. auto     — vol/price shock detector with a rolling 2h cooldown;
//                 re-triggers extend the cooldown (enter fast, exit slow)
//   3. calendar — pre-scheduled blackout windows in regime_events (FOMC etc.)
//
// The engine consults resolveRegime() once per tick. LOCKDOWN blocks new
// entries only — settlement is never gated. CAUTION keeps trading with
// halved size and a raised edge bar. Every mode transition is logged.

import { db } from '@/db';
import { regimeState, regimeEvents, regimeLog } from '@/db/schema';
import { eq, and, lte, gt } from 'drizzle-orm';

export type RegimeMode = 'normal' | 'caution' | 'lockdown';
export type RegimeSource = 'manual' | 'auto' | 'calendar' | 'system' | 'none';

export interface Regime {
  mode: RegimeMode;
  reason: string;
  source: RegimeSource;
  until: number | null; // ms epoch when this mode is expected to lift; null = indefinite
}

export const REGIME_NORMAL: Regime = { mode: 'normal', reason: '', source: 'none', until: null };

// Caution-mode scaling applied by the engine
export const CAUTION_RISK_MULT = 0.5; // 2% -> 1% of equity per entry
export const CAUTION_EDGE = 0.09;     // raised conviction bar (normal 0.06)

// ---------------------------------------------------------------------------
// Auto shock detector
//
// Price reacts to unscheduled shocks (war headlines, exchange hacks, depegs)
// within minutes — realized vol is the honest proxy, so no news feed needed.
// Triggers on either:
//   - a single closed 5m candle moving more than SHOCK_MOVE_PCT, or
//   - 1h realized vol running SHOCK_VOL_RATIO x above the 24h baseline.
// ---------------------------------------------------------------------------

// Keep in sync with ASSET_MAP in engine.ts
const SHOCK_ASSETS: Record<string, string> = {
  'BTC-PERP': 'BTC',
  'ETH-PERP': 'ETH',
  'XAU': 'PAXG',
};
const SHOCK_MOVE_PCT: Record<string, number> = {
  'BTC-PERP': 1.5,
  'ETH-PERP': 2.0,
  'XAU': 0.75, // gold: far lower baseline vol
};
const SHOCK_VOL_RATIO = 3;
export const SHOCK_COOLDOWN_MS = 2 * 60 * 60 * 1000;

const closesCache: Record<string, { ts: number; closes: number[] }> = {};

// Closed 5m candles for the last 24h, oldest first. Cached 60s per asset.
async function getClosed5mCloses(asset: string, now: number): Promise<number[]> {
  const cached = closesCache[asset];
  if (cached && now - cached.ts < 60_000) return cached.closes;
  const res = await fetch('https://api.hyperliquid.xyz/info', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      type: 'candleSnapshot',
      req: { coin: SHOCK_ASSETS[asset], interval: '5m', startTime: now - 24 * 60 * 60 * 1000, endTime: now },
    }),
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`candleSnapshot ${asset} ${res.status}`);
  const candles = await res.json();
  const closes = (Array.isArray(candles) ? candles : [])
    .filter((k: any) => k.t + 5 * 60_000 <= now) // fully closed candles only
    .map((k: any) => parseFloat(k.c))
    .filter(Number.isFinite);
  closesCache[asset] = { ts: now, closes };
  return closes;
}

function realizedVol(closes: number[]): number {
  if (closes.length < 3) return 0;
  const rets: number[] = [];
  for (let i = 1; i < closes.length; i++) rets.push(Math.log(closes[i] / closes[i - 1]));
  const mean = rets.reduce((a, b) => a + b, 0) / rets.length;
  const variance = rets.reduce((a, b) => a + (b - mean) ** 2, 0) / (rets.length - 1);
  return Math.sqrt(variance);
}

// Returns a human-readable trigger reason, or null when markets look calm.
// Never throws — a feed hiccup must not poison regime resolution (a dead feed
// already stops entries upstream since the engine has no marks to trade on).
export async function detectShock(now: number): Promise<string | null> {
  for (const asset of Object.keys(SHOCK_ASSETS)) {
    try {
      const closes = await getClosed5mCloses(asset, now);
      if (closes.length < 20) continue;

      const last = closes[closes.length - 1];
      const prev = closes[closes.length - 2];
      const movePct = Math.abs(last / prev - 1) * 100;
      if (movePct >= SHOCK_MOVE_PCT[asset]) {
        return `${asset} moved ${movePct.toFixed(1)}% in 5m`;
      }

      const hourVol = realizedVol(closes.slice(-12));
      const dayVol = realizedVol(closes);
      if (dayVol > 0 && hourVol / dayVol >= SHOCK_VOL_RATIO) {
        return `${asset} 1h vol ${(hourVol / dayVol).toFixed(1)}x above 24h baseline`;
      }
    } catch {
      // transient feed error on this asset — skip, other layers still apply
    }
  }
  return null;
}

// ---------------------------------------------------------------------------
// State + resolution
// ---------------------------------------------------------------------------

async function getRegimeStateRow() {
  const rows = await db.select().from(regimeState).where(eq(regimeState.id, 'regime'));
  if (rows.length > 0) return rows[0];
  const fresh = { id: 'regime', lastMode: 'normal', updatedAt: Date.now() };
  await db.insert(regimeState).values(fresh).onConflictDoNothing();
  const re = await db.select().from(regimeState).where(eq(regimeState.id, 'regime'));
  return re[0] ?? { ...fresh, manualMode: null, manualReason: null, manualUntil: null, shockUntil: null, shockReason: null };
}

async function logTransition(mode: RegimeMode, reason: string, source: RegimeSource, at: number) {
  await db.insert(regimeLog).values({ mode, reason: reason || 'markets calm', source, at });
}

const SEVERITY: Record<RegimeMode, number> = { normal: 0, caution: 1, lockdown: 2 };

export async function resolveRegime(now: number): Promise<Regime> {
  const st = await getRegimeStateRow();

  // Layer 2: auto shock — run every tick; re-triggers extend the cooldown
  let shockUntil = st.shockUntil ?? 0;
  let shockReason = st.shockReason ?? '';
  const trigger = await detectShock(now);
  if (trigger) {
    shockUntil = now + SHOCK_COOLDOWN_MS;
    shockReason = trigger;
    await db.update(regimeState)
      .set({ shockUntil, shockReason, updatedAt: now })
      .where(eq(regimeState.id, 'regime'));
  }

  // Collect active layers in precedence order: manual > auto > calendar
  const active: Regime[] = [];

  if (st.manualMode && (st.manualUntil == null || now < st.manualUntil)) {
    active.push({
      mode: st.manualMode as RegimeMode,
      reason: st.manualReason || 'manual override',
      source: 'manual',
      until: st.manualUntil ?? null,
    });
  }

  if (now < shockUntil) {
    active.push({ mode: 'lockdown', reason: shockReason || 'vol shock', source: 'auto', until: shockUntil });
  }

  const events = await db.select().from(regimeEvents)
    .where(and(lte(regimeEvents.startAt, now), gt(regimeEvents.endAt, now)));
  for (const ev of events) {
    active.push({
      mode: (ev.severity === 'caution' ? 'caution' : 'lockdown') as RegimeMode,
      reason: ev.label,
      source: 'calendar',
      until: ev.endAt,
    });
  }

  // Most severe wins; precedence order already breaks ties
  let regime: Regime = REGIME_NORMAL;
  for (const r of active) {
    if (SEVERITY[r.mode] > SEVERITY[regime.mode]) regime = r;
  }

  if (regime.mode !== st.lastMode) {
    await logTransition(regime.mode, regime.reason, regime.source, now);
    await db.update(regimeState)
      .set({ lastMode: regime.mode, updatedAt: now })
      .where(eq(regimeState.id, 'regime'));
  }

  return regime;
}

// Owner controls (admin API): set or clear the manual override. Clearing to
// 'normal' also releases any active auto shock — the owner has looked at the
// tape and made the call.
export async function setManualRegime(
  mode: RegimeMode,
  reason: string,
  ttlMinutes: number | null,
  now: number,
): Promise<void> {
  await getRegimeStateRow();
  if (mode === 'normal') {
    await db.update(regimeState)
      .set({ manualMode: null, manualReason: null, manualUntil: null, shockUntil: null, shockReason: null, updatedAt: now })
      .where(eq(regimeState.id, 'regime'));
  } else {
    await db.update(regimeState)
      .set({
        manualMode: mode,
        manualReason: reason || 'manual override',
        manualUntil: ttlMinutes ? now + ttlMinutes * 60_000 : null,
        updatedAt: now,
      })
      .where(eq(regimeState.id, 'regime'));
  }
}
