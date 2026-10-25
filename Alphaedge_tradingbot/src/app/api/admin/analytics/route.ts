import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { simulatorTrades } from '@/db/schema';
import { and, asc, eq, gt, gte, or } from 'drizzle-orm';
import { initDb } from '@/db/init';
import { requireViewer } from '@/lib/authz';
import { getDemoAccount, LEVELS } from '@/lib/engine';
import { AnalyticsAccumulator, type TradeRow } from '@/lib/analytics';

export const dynamic = 'force-dynamic';

// Rows fetched per round trip. Keyset pagination on (created_at, id) keeps each
// page an index range seek, so cost stays linear in rows and never degrades
// the way OFFSET does on deep pages.
const CHUNK = 5000;

// Strategy analytics feed, open to every approved viewer. It exposes only
// aggregate trade data the ledger already shows; the Ledger Explorer stays
// owner-only because of its unbounded CSV export.
//
// Previously this route returned raw rows with ORDER BY created_at ASC
// LIMIT 8000, i.e. the OLDEST 8,000 trades, which froze analytics once the
// demo passed that count. Now every trade in the demo window is streamed
// through an exact single-pass accumulator and only aggregates plus a
// decimated equity curve are returned. Payload is O(tiers x assets), not
// O(trades), and every stat reconciles with the ledger.
//
// Read cost: one pass over the demo window per REFRESH (Turso bills rows
// read). There is no polling client. If history grows large enough for this
// to matter, the next step is a settle-time rollup table (see PR notes).
export async function GET(_req: NextRequest) {
  try {
    const denied = await requireViewer();
    if (denied) return NextResponse.json({ error: denied }, { status: 401 });
    await initDb();

    const acct = await getDemoAccount();
    const acc = new AnalyticsAccumulator();

    let cursor: { createdAt: number; id: string } | null = null;
    for (;;) {
      const windowStart = gte(simulatorTrades.createdAt, acct.startedAt);
      const where = cursor
        ? and(
            windowStart,
            or(
              gt(simulatorTrades.createdAt, cursor.createdAt),
              and(eq(simulatorTrades.createdAt, cursor.createdAt), gt(simulatorTrades.id, cursor.id)),
            ),
          )
        : windowStart;

      const rows: TradeRow[] = await db.select({
        id: simulatorTrades.id,
        createdAt: simulatorTrades.createdAt,
        level: simulatorTrades.level,
        asset: simulatorTrades.asset,
        side: simulatorTrades.side,
        outcome: simulatorTrades.outcome,
        pnl: simulatorTrades.pnl,
        size: simulatorTrades.size,
        entryPrice: simulatorTrades.entryPrice,
      }).from(simulatorTrades)
        .where(where)
        .orderBy(asc(simulatorTrades.createdAt), asc(simulatorTrades.id))
        .limit(CHUNK);

      for (const r of rows) acc.push(r);
      if (rows.length < CHUNK) break;
      const tail = rows[rows.length - 1];
      cursor = { createdAt: tail.createdAt, id: tail.id };
    }

    return NextResponse.json({
      tiers: acc.result(),
      totalRows: acc.rows,
      demoStartedAt: acct.startedAt,
      levels: Object.fromEntries(Object.entries(LEVELS).map(([k, v]) => [k, { base: v.base, label: v.label, dailyTrades: v.dailyTrades }])),
      generatedAt: Date.now(),
    });
  } catch (error: any) {
    console.error('Admin analytics error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}
