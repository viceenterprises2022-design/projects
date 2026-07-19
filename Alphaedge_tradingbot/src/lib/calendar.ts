// Economic-calendar feed for the Regime Guard.
//
// Pulls high-importance US events and upserts them into regime_events as
// blackout windows, so the calendar layer stays current without manual entry.
//
// Providers:
//   - TradingView public calendar endpoint (default — keyless)
//   - Trading Economics official API when TRADINGECONOMICS_API_KEY is set
//     (their guest tier is discontinued; a paid key switches this on)
//
// Feed events get deterministic `ev_feed_<provider>_<sourceId>` ids so
// re-syncs update in place. Owner-created events are never touched. The
// static migration-seeded events (ev_fomc_/ev_cpi_/ev_nfp_) are removed
// once a live sync succeeds — they exist only as a cold-start fallback.

import { db } from '@/db';
import { regimeEvents, regimeState } from '@/db/schema';
import { eq, like, or } from 'drizzle-orm';

const HORIZON_DAYS = 21;
export const CALENDAR_SYNC_INTERVAL_MS = 6 * 60 * 60 * 1000;

interface FeedEvent {
  sourceId: string;
  title: string;
  at: number; // release/decision moment, ms UTC
}

interface Classification {
  kind: string;
  severity: 'caution' | 'lockdown';
  preMs: number;
  postMs: number;
}

const MIN = 60_000;

// Blackout policy per event type. Rate decisions get the widest window
// (statement + press conference); the big prints get a tight lockdown burst;
// any other high-importance release trades on in caution.
function classify(title: string): Classification {
  const t = title.toLowerCase();
  if (/interest rate decision|fomc|fed press conference/.test(t)) {
    return { kind: 'fed', severity: 'lockdown', preMs: 60 * MIN, postMs: 150 * MIN };
  }
  if (/inflation rate|\bcpi\b|consumer price/.test(t)) {
    return { kind: 'cpi', severity: 'lockdown', preMs: 30 * MIN, postMs: 90 * MIN };
  }
  if (/non.?farm|payrolls|unemployment rate/.test(t)) {
    return { kind: 'nfp', severity: 'lockdown', preMs: 30 * MIN, postMs: 90 * MIN };
  }
  if (/pce price/.test(t)) {
    return { kind: 'macro', severity: 'lockdown', preMs: 30 * MIN, postMs: 90 * MIN };
  }
  return { kind: 'macro', severity: 'caution', preMs: 15 * MIN, postMs: 45 * MIN };
}

async function fetchTradingView(now: number): Promise<FeedEvent[]> {
  const from = new Date(now).toISOString();
  const to = new Date(now + HORIZON_DAYS * 86_400_000).toISOString();
  const url = `https://economic-calendar.tradingview.com/events?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}&countries=US&minImportance=1`;
  const res = await fetch(url, {
    headers: { Origin: 'https://www.tradingview.com', 'User-Agent': 'Mozilla/5.0' },
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`TradingView calendar ${res.status}`);
  const json = await res.json();
  const rows = Array.isArray(json?.result) ? json.result : [];
  return rows
    .map((ev: any) => ({
      sourceId: String(ev.id ?? ''),
      title: String(ev.title ?? ev.indicator ?? ''),
      at: Date.parse(ev.date),
    }))
    .filter((ev: FeedEvent) => ev.sourceId && ev.title && Number.isFinite(ev.at));
}

async function fetchTradingEconomics(now: number, key: string): Promise<FeedEvent[]> {
  const d1 = new Date(now).toISOString().slice(0, 10);
  const d2 = new Date(now + HORIZON_DAYS * 86_400_000).toISOString().slice(0, 10);
  const url = `https://api.tradingeconomics.com/calendar/country/united%20states?c=${encodeURIComponent(key)}&f=json&d1=${d1}&d2=${d2}`;
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Trading Economics calendar ${res.status}`);
  const json = await res.json();
  const rows = Array.isArray(json) ? json : [];
  return rows
    .filter((ev: any) => Number(ev.Importance) >= 3) // 3 = high
    .map((ev: any) => ({
      sourceId: String(ev.CalendarId ?? ''),
      title: String(ev.Event ?? ''),
      // TE timestamps are UTC without a zone suffix
      at: Date.parse(String(ev.Date).endsWith('Z') ? ev.Date : `${ev.Date}Z`),
    }))
    .filter((ev: FeedEvent) => ev.sourceId && ev.title && Number.isFinite(ev.at));
}

// Force a sync now. Throws on feed failure — callers decide how to degrade.
export async function syncRegimeCalendar(now: number): Promise<{ provider: string; upserted: number }> {
  const teKey = process.env.TRADINGECONOMICS_API_KEY;
  const provider = teKey ? 'te' : 'tv';
  const feed = teKey ? await fetchTradingEconomics(now, teKey) : await fetchTradingView(now);

  // Simultaneous variants of the same print (CPI MoM / YoY / core, all at
  // 12:30) collapse into one window per kind+timestamp.
  const seen = new Set<string>();
  let upserted = 0;
  for (const ev of feed) {
    const c = classify(ev.title);
    const dedupe = `${c.kind}_${ev.at}`;
    if (seen.has(dedupe)) continue;
    seen.add(dedupe);
    await db.insert(regimeEvents).values({
      id: `ev_feed_${provider}_${ev.sourceId}`,
      label: ev.title,
      kind: c.kind,
      severity: c.severity,
      startAt: ev.at - c.preMs,
      endAt: ev.at + c.postMs,
      createdAt: now,
    }).onConflictDoUpdate({
      target: regimeEvents.id,
      set: { label: ev.title, severity: c.severity, startAt: ev.at - c.preMs, endAt: ev.at + c.postMs },
    });
    upserted++;
  }

  // Live feed is healthy — retire the static cold-start seeds so the
  // upcoming list doesn't show duplicates of the same events.
  if (upserted > 0) {
    await db.delete(regimeEvents).where(or(
      like(regimeEvents.id, 'ev_fomc_%'),
      like(regimeEvents.id, 'ev_cpi_%'),
      like(regimeEvents.id, 'ev_nfp_%'),
    ));
  }

  return { provider, upserted };
}

// Tick-side entry point: throttled to one attempt per interval. The attempt
// timestamp advances even on failure so a dead feed can't hammer every tick —
// the 21-day horizon leaves plenty of slack between retries.
export async function maybeSyncRegimeCalendar(now: number): Promise<{ provider: string; upserted: number } | null> {
  const rows = await db.select({ syncedAt: regimeState.calendarSyncedAt })
    .from(regimeState).where(eq(regimeState.id, 'regime'));
  const last = rows[0]?.syncedAt ?? 0;
  if (now - last < CALENDAR_SYNC_INTERVAL_MS) return null;
  if (rows.length > 0) {
    await db.update(regimeState).set({ calendarSyncedAt: now }).where(eq(regimeState.id, 'regime'));
  }
  return syncRegimeCalendar(now);
}
