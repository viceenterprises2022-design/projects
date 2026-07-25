import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { simulatorTrades } from '@/db/schema';
import { asc, gte } from 'drizzle-orm';
import { initDb } from '@/db/init';
import { requireViewer } from '@/lib/authz';
import { getDemoAccount, LEVELS } from '@/lib/engine';

export const dynamic = 'force-dynamic';

// Cap the payload late in the demo period; 8k rows ≈ weeks of trading and
// keeps the single scan (index-assisted) and the JSON body bounded.
const MAX_ROWS = 8000;

// Strategy analytics feed — open to every approved viewer. It exposes only
// aggregate trade data the ledger already shows, and is the transparency
// centrepiece of the demo. The Ledger Explorer stays owner-only because its
// CSV export runs an unbounded query.
// Read budget: ONE compact trades query for the demo window. Every metric —
// win rates, profit factor, streaks, drawdown, per-asset/side/tier splits,
// hourly distribution, equity curves — is computed client-side from this
// single result set, so switching views costs zero additional DB reads.
export async function GET(_req: NextRequest) {
  try {
    const denied = await requireViewer();
    if (denied) return NextResponse.json({ error: denied }, { status: 401 });
    await initDb();

    const acct = await getDemoAccount();
    const rows = await db.select({
      createdAt: simulatorTrades.createdAt,
      level: simulatorTrades.level,
      asset: simulatorTrades.asset,
      side: simulatorTrades.side,
      outcome: simulatorTrades.outcome,
      pnl: simulatorTrades.pnl,
      size: simulatorTrades.size,
      entryPrice: simulatorTrades.entryPrice,
    }).from(simulatorTrades)
      .where(gte(simulatorTrades.createdAt, acct.startedAt))
      .orderBy(asc(simulatorTrades.createdAt))
      .limit(MAX_ROWS);

    return NextResponse.json({
      trades: rows,
      truncated: rows.length === MAX_ROWS,
      demoStartedAt: acct.startedAt,
      levels: Object.fromEntries(Object.entries(LEVELS).map(([k, v]) => [k, { base: v.base, label: v.label, dailyTrades: v.dailyTrades }])),
      generatedAt: Date.now(),
    });
  } catch (error: any) {
    console.error('Admin analytics error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}
