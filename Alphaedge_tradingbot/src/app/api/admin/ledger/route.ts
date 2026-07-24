import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { simulatorTrades } from '@/db/schema';
import { desc, eq, gte, and } from 'drizzle-orm';
import { initDb } from '@/db/init';
import { requireOwner } from '@/lib/authz';
import { getDemoAccount } from '@/lib/engine';

export const dynamic = 'force-dynamic';

const PAGE_SIZE = 100;

// Owner-only full ledger with pagination and CSV export.
// Read budget: exactly ONE bounded trades query per request (LIMIT 101 for a
// page — the +1 row stands in for a COUNT so we never scan the whole table
// to learn whether a next page exists). CSV is a single unbounded query,
// owner-initiated only. No polling client exists for this endpoint.
export async function GET(req: NextRequest) {
  try {
    const denied = await requireOwner();
    if (denied) return NextResponse.json({ error: denied }, { status: 403 });
    await initDb();

    const rawLevel = req.nextUrl.searchParams.get('level') || 'all';
    const levelParam = parseInt(rawLevel, 10);
    const level = [1, 2, 3, 4].includes(levelParam) ? levelParam : null;
    const page = Math.max(1, parseInt(req.nextUrl.searchParams.get('page') || '1', 10) || 1);
    const format = req.nextUrl.searchParams.get('format');

    const acct = await getDemoAccount();
    const where = level === null
      ? gte(simulatorTrades.createdAt, acct.startedAt)
      : and(gte(simulatorTrades.createdAt, acct.startedAt), eq(simulatorTrades.level, level))!;

    if (format === 'csv') {
      const rows = await db.select().from(simulatorTrades)
        .where(where).orderBy(desc(simulatorTrades.createdAt));
      const header = 'id,level,round_id,asset,timestamp,side,strike_price,expiry_price,size,entry_price,exit_price,outcome,pnl,created_at';
      const lines = rows.map(r => [
        r.id, r.level, r.roundId, r.asset, r.timestamp, r.side,
        r.strikePrice, r.expiryPrice, r.size, r.entryPrice, r.exitPrice,
        r.outcome, r.pnl, new Date(r.createdAt).toISOString(),
      ].join(','));
      const name = `prospera-ledger-${level === null ? 'all' : `L${level}`}-${new Date().toISOString().slice(0, 10)}.csv`;
      return new NextResponse([header, ...lines].join('\n'), {
        headers: {
          'Content-Type': 'text/csv; charset=utf-8',
          'Content-Disposition': `attachment; filename="${name}"`,
        },
      });
    }

    const rows = await db.select().from(simulatorTrades)
      .where(where)
      .orderBy(desc(simulatorTrades.createdAt))
      .limit(PAGE_SIZE + 1)
      .offset((page - 1) * PAGE_SIZE);

    const hasNext = rows.length > PAGE_SIZE;
    return NextResponse.json({
      rows: rows.slice(0, PAGE_SIZE),
      page,
      pageSize: PAGE_SIZE,
      hasNext,
      demoStartedAt: acct.startedAt,
    });
  } catch (error: any) {
    console.error('Admin ledger error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}
