import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { simulatorTrades } from '@/db/schema';
import { desc, eq, gte, and, sql } from 'drizzle-orm';
import { initDb } from '@/db/init';
import { requireOwner } from '@/lib/authz';
import { getDemoAccount } from '@/lib/engine';

export const dynamic = 'force-dynamic';

// Binary round settlement: a YES position wins when expiry settles above strike,
// a NO position wins when expiry settles at or below strike. Winning contracts
// pay $1.00, losing contracts pay $0.00. Outcome and PnL are recomputed here so
// the historical log is verifiable — client-supplied values are never trusted.
function settle(strike: number, expiry: number, side: 'YES' | 'NO', size: number, entryPrice: number) {
  const winningSide = expiry > strike ? 'YES' : 'NO';
  const won = side === winningSide;
  const cost = size * entryPrice;
  const payout = won ? size * 1.0 : 0;
  return {
    outcome: won ? 'WIN' : 'LOSS',
    exitPrice: won ? 1.0 : 0.0,
    pnl: Math.round((payout - cost) * 100) / 100,
  };
}

export async function GET(req: NextRequest) {
  try {
    await initDb();

    const asset = req.nextUrl.searchParams.get('asset');

    // All demo-facing stats count only rounds settled after the demo start.
    const acct = await getDemoAccount();
    const demoWindow = gte(simulatorTrades.createdAt, acct.startedAt);

    let query = db.select().from(simulatorTrades)
      .where(asset ? and(demoWindow, eq(simulatorTrades.asset, asset)) : demoWindow);

    const history = await query
      .orderBy(desc(simulatorTrades.createdAt))
      .limit(200);

    // Stats aggregate over the FULL demo window via SQL — the 200-row history
    // page is for display only and must never bound the accounting.
    const whereClause = asset ? and(demoWindow, eq(simulatorTrades.asset, asset)) : demoWindow;
    const aggRows = await db.select({
      settled: sql<number>`COUNT(*)`,
      wins: sql<number>`COALESCE(SUM(CASE WHEN ${simulatorTrades.outcome} = 'WIN' THEN 1 ELSE 0 END), 0)`,
      pnl: sql<number>`COALESCE(SUM(${simulatorTrades.pnl}), 0)`,
      volume: sql<number>`COALESCE(SUM(${simulatorTrades.size} * ${simulatorTrades.entryPrice}), 0)`,
      grossWin: sql<number>`COALESCE(SUM(CASE WHEN ${simulatorTrades.pnl} > 0 THEN ${simulatorTrades.pnl} ELSE 0 END), 0)`,
      grossLoss: sql<number>`COALESCE(SUM(CASE WHEN ${simulatorTrades.pnl} < 0 THEN -${simulatorTrades.pnl} ELSE 0 END), 0)`,
    }).from(simulatorTrades).where(whereClause);
    const agg = aggRows[0];
    const wins = agg?.wins ?? 0;
    const settledCount = agg?.settled ?? 0;
    const losses = settledCount - wins;
    const pnl = agg?.pnl ?? 0;
    const volume = agg?.volume ?? 0;
    const grossWin = agg?.grossWin ?? 0;
    const grossLoss = agg?.grossLoss ?? 0;

    // Next round id continues from the highest persisted round for this asset,
    // so round numbering stays monotonic across sessions and page reloads.
    const maxRoundRow = await db.select({ max: sql<number>`COALESCE(MAX(${simulatorTrades.roundId}), 100)` })
      .from(simulatorTrades)
      .where(asset ? and(demoWindow, eq(simulatorTrades.asset, asset)) : demoWindow);

    return NextResponse.json({
      history,
      stats: {
        wins,
        losses,
        settled: settledCount,
        hitRate: settledCount > 0 ? (wins / settledCount) * 100 : 0,
        totalPnl: Math.round(pnl * 100) / 100,
        totalVolume: Math.round(volume * 100) / 100,
        expectancy: settledCount > 0 ? Math.round((pnl / settledCount) * 100) / 100 : 0,
        profitFactor: grossLoss > 0 ? Math.round((grossWin / grossLoss) * 100) / 100 : (grossWin > 0 ? Infinity : 0),
      },
      nextRoundId: (maxRoundRow[0]?.max ?? 100) + 1,
    });
  } catch (error: any) {
    console.error('Predictions fetch error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    // Canonical rounds are written by the server engine; browser-submitted
    // settlements are owner-only (dev/testing) so viewers stay watch-only.
    const denied = await requireOwner();
    if (denied) return NextResponse.json({ error: denied }, { status: 403 });
    await initDb();

    const body = await req.json();
    const { roundId, asset, strikePrice, expiryPrice, side, size, entryPrice } = body;

    const numeric = { roundId, strikePrice, expiryPrice, size, entryPrice };
    for (const [key, value] of Object.entries(numeric)) {
      if (!Number.isFinite(Number(value))) {
        return NextResponse.json({ error: `Invalid or missing numeric field: ${key}` }, { status: 400 });
      }
    }
    if (side !== 'YES' && side !== 'NO') {
      return NextResponse.json({ error: 'side must be YES or NO' }, { status: 400 });
    }
    if (typeof asset !== 'string' || !asset) {
      return NextResponse.json({ error: 'asset is required' }, { status: 400 });
    }
    if (Number(size) <= 0 || Number(entryPrice) <= 0 || Number(entryPrice) >= 1) {
      return NextResponse.json({ error: 'size must be positive and entryPrice within (0, 1)' }, { status: 400 });
    }

    // Reject duplicate settlements for the same asset+round.
    const existing = await db.select({ id: simulatorTrades.id })
      .from(simulatorTrades)
      .where(sql`${simulatorTrades.asset} = ${asset} AND ${simulatorTrades.roundId} = ${Number(roundId)}`)
      .limit(1);
    if (existing.length > 0) {
      return NextResponse.json({ error: `Round ${roundId} for ${asset} already settled`, id: existing[0].id }, { status: 409 });
    }

    const settled = settle(Number(strikePrice), Number(expiryPrice), side, Number(size), Number(entryPrice));
    const now = Date.now();
    const tradeId = `${asset}_${roundId}_${now}`;

    await db.insert(simulatorTrades).values({
      id: tradeId,
      roundId: Number(roundId),
      asset,
      timestamp: new Date(now).toISOString(),
      strikePrice: Number(strikePrice),
      expiryPrice: Number(expiryPrice),
      side,
      size: Number(size),
      entryPrice: Number(entryPrice),
      exitPrice: settled.exitPrice,
      outcome: settled.outcome,
      pnl: settled.pnl,
      createdAt: now,
    });

    return NextResponse.json({ success: true, id: tradeId, outcome: settled.outcome, pnl: settled.pnl }, { status: 201 });
  } catch (error: any) {
    console.error('Prediction save error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}

export async function DELETE(req: NextRequest) {
  try {
    await initDb();

    const adminSecret = req.headers.get('x-admin-token') || req.nextUrl.searchParams.get('secret');
    const expectedSecret = process.env.ADMIN_SECRET;

    // Fail closed: destructive endpoint stays disabled unless ADMIN_SECRET is
    // explicitly configured — the repo is public, so no hardcoded fallback.
    if (!expectedSecret) {
      return NextResponse.json({ error: 'Admin operations disabled: ADMIN_SECRET is not configured' }, { status: 403 });
    }
    if (!adminSecret || adminSecret !== expectedSecret) {
      return NextResponse.json({ error: 'Unauthorized: Admin access required' }, { status: 401 });
    }

    const asset = req.nextUrl.searchParams.get('asset');
    if (asset) {
      await db.delete(simulatorTrades).where(eq(simulatorTrades.asset, asset));
    } else {
      await db.delete(simulatorTrades);
    }

    return NextResponse.json({ success: true, message: 'Simulator trades cleared successfully' });
  } catch (error: any) {
    console.error('Predictions deletion error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}
