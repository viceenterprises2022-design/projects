import { NextResponse } from 'next/server';
import { db } from '@/db';
import { demoAccount } from '@/db/schema';
import { eq } from 'drizzle-orm';
import { initDb } from '@/db/init';
import { requireOwner } from '@/lib/authz';

export const dynamic = 'force-dynamic';

// Operator day-reset: restarts the daily quota counters and the daily loss
// circuit breaker window from NOW, for all tiers, without touching ledger
// history or cumulative demo-window stats. The normal 13:00 UTC rhythm
// resumes at the next roll (utcDayStart takes the latest of the two).
export async function POST() {
  try {
    const denied = await requireOwner();
    if (denied) return NextResponse.json({ error: denied }, { status: 403 });
    await initDb();

    const now = Date.now();
    await db.update(demoAccount).set({ dayResetAt: now }).where(eq(demoAccount.id, 'demo'));
    return NextResponse.json({ success: true, dayResetAt: now });
  } catch (error: any) {
    console.error('Day reset error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}
