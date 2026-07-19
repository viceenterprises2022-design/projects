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

// ---------------------------------------------------------------------------
// Crypto / asset-native events
// ---------------------------------------------------------------------------

// BTC/ETH options expiries are deterministic: every last Friday of the month
// at 08:00 UTC (Deribit convention), with the Mar/Jun/Sep/Dec quarterlies
// carrying the heaviest open interest. No feed needed — pure calendar math.
function generateExpiryEvents(now: number): Array<typeof regimeEvents.$inferInsert> {
  const out: Array<typeof regimeEvents.$inferInsert> = [];
  const horizon = now + HORIZON_DAYS * 86_400_000;
  const d = new Date(now);
  for (let i = 0; i < 2; i++) {
    const year = d.getUTCFullYear();
    const month = d.getUTCMonth() + i; // this month and next
    // walk back from the last day of the month to a Friday
    const last = new Date(Date.UTC(year, month + 1, 0));
    const lastFriday = last.getUTCDate() - ((last.getUTCDay() + 2) % 7);
    const expiry = Date.UTC(year, month, lastFriday, 8, 0); // 08:00 UTC
    if (expiry <= now || expiry > horizon) continue;
    const m = new Date(expiry).getUTCMonth();
    const quarterly = m === 2 || m === 5 || m === 8 || m === 11;
    out.push({
      id: `ev_gen_expiry_${new Date(expiry).toISOString().slice(0, 7)}`,
      label: quarterly ? 'BTC/ETH quarterly options expiry' : 'BTC/ETH monthly options expiry',
      kind: 'crypto',
      severity: 'caution',
      startAt: expiry - 30 * MIN,
      endAt: expiry + 90 * MIN,
      createdAt: now,
    });
  }
  return out;
}

// CoinMarketCal (announced crypto events: forks, upgrades, unlocks, ETF
// decisions). Free API key from developers.coinmarketcal.com — activates when
// COINMARKETCAL_API_KEY is set. Event dates are day-precision, so windows
// cover the full UTC day. Only high-impact keywords pass the allowlist; the
// firehose of listings/AMAs/partnerships is ignored.
const CMC_LOCKDOWN = /hard.?fork|\bfork\b|halving|mainnet|network upgrade|hardfork/i;
const CMC_CAUTION = /\bupgrade\b|unlock|\betf\b|\bsec\b|testnet.*merge|airdrop.*snapshot/i;

async function fetchCoinMarketCal(now: number, key: string): Promise<Array<typeof regimeEvents.$inferInsert>> {
  const d1 = new Date(now).toISOString().slice(0, 10);
  const d2 = new Date(now + HORIZON_DAYS * 86_400_000).toISOString().slice(0, 10);
  const url = `https://developers.coinmarketcal.com/v1/events?dateRangeStart=${d1}&dateRangeEnd=${d2}&coins=bitcoin,ethereum&max=75`;
  const res = await fetch(url, {
    headers: { 'x-api-key': key, Accept: 'application/json' },
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`CoinMarketCal ${res.status}`);
  const json = await res.json();
  const rows = Array.isArray(json?.body) ? json.body : [];
  const out: Array<typeof regimeEvents.$inferInsert> = [];
  for (const ev of rows) {
    const title = String(ev?.title?.en ?? ev?.title ?? '');
    const cats = (Array.isArray(ev?.categories) ? ev.categories : []).map((c: any) => String(c?.name ?? '')).join(' ');
    const text = `${title} ${cats}`;
    const severity = CMC_LOCKDOWN.test(text) ? 'lockdown' : CMC_CAUTION.test(text) ? 'caution' : null;
    if (!severity) continue;
    const at = Date.parse(ev?.date_event ?? ev?.displayed_date ?? '');
    if (!Number.isFinite(at)) continue;
    const dayStart = new Date(at).setUTCHours(0, 0, 0, 0);
    out.push({
      id: `ev_feed_cmc_${String(ev?.id ?? at)}`,
      label: title.slice(0, 120),
      kind: 'crypto',
      severity,
      startAt: dayStart,
      endAt: dayStart + 86_400_000,
      createdAt: now,
    });
  }
  return out;
}

// Force a sync now. Throws on macro-feed failure — callers decide how to
// degrade. Crypto layers degrade individually and never sink the sync.
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

  // Crypto/asset-native layers: computed expiries always; CoinMarketCal when
  // a key is present. Each degrades alone — a CMC outage must not cost us the
  // macro windows that already upserted above.
  const cryptoRows = generateExpiryEvents(now);
  const cmcKey = process.env.COINMARKETCAL_API_KEY;
  if (cmcKey) {
    try {
      cryptoRows.push(...await fetchCoinMarketCal(now, cmcKey));
    } catch {
      // feed hiccup — computed expiries and macro windows still land
    }
  }
  for (const row of cryptoRows) {
    await db.insert(regimeEvents).values(row).onConflictDoUpdate({
      target: regimeEvents.id,
      set: { label: row.label, severity: row.severity, startAt: row.startAt, endAt: row.endAt },
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
