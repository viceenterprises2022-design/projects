import { NextResponse } from 'next/server';
import { db } from '@/db';
import { demoAccount, engineRounds } from '@/db/schema';
import { eq } from 'drizzle-orm';
import { initDb } from '@/db/init';
import { requireOwner } from '@/lib/authz';
import { getDemoAccount, DEMO_BANKROLL_BASE } from '@/lib/engine';

export const dynamic = 'force-dynamic';

// Owner-only soft reset: bump the demo start marker so equity returns to a
// clean $10,000 and every stat starts counting from zero. Historical rows are
// preserved but no longer count toward the demo.
export async function POST() {
  try {
    const denied = await requireOwner();
    if (denied) return NextResponse.json({ error: denied }, { status: 403 });
    await initDb();

    await getDemoAccount(); // ensure row exists
    const now = Date.now();
    await db.update(demoAccount)
      .set({ startedAt: now, baseUsd: DEMO_BANKROLL_BASE })
      .where(eq(demoAccount.id, 'demo'));

    // Void any in-flight open rounds so pre-reset positions can't settle into
    // the fresh ledger.
    await db.update(engineRounds)
      .set({ status: 'skipped', settledAt: now })
      .where(eq(engineRounds.status, 'open'));

    return NextResponse.json({ success: true, startedAt: now, baseUsd: DEMO_BANKROLL_BASE });
  } catch (error: any) {
    console.error('Demo reset error:', error);
    return NextResponse.json({ error: error.message || 'Reset failed' }, { status: 500 });
  }
}
