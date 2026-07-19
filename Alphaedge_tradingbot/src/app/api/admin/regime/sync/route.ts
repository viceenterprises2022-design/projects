import { NextResponse } from 'next/server';
import { db } from '@/db';
import { regimeEvents, regimeState } from '@/db/schema';
import { eq, gt } from 'drizzle-orm';
import { initDb } from '@/db/init';
import { requireOwner } from '@/lib/authz';
import { syncRegimeCalendar } from '@/lib/calendar';

export const dynamic = 'force-dynamic';

// Owner: force an economic-calendar sync now (bypasses the tick throttle).
export async function POST() {
  try {
    const denied = await requireOwner();
    if (denied) return NextResponse.json({ error: denied }, { status: 403 });
    await initDb();
    const now = Date.now();
    const result = await syncRegimeCalendar(now);
    await db.update(regimeState).set({ calendarSyncedAt: now }).where(eq(regimeState.id, 'regime'));
    const upcoming = await db.select().from(regimeEvents)
      .where(gt(regimeEvents.endAt, now))
      .orderBy(regimeEvents.startAt)
      .limit(50);
    return NextResponse.json({ success: true, ...result, upcoming });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
