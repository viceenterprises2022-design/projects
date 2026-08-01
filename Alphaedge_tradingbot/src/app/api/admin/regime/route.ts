import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { regimeEvents, regimeLog } from '@/db/schema';
import { gt, desc } from 'drizzle-orm';
import { initDb } from '@/db/init';
import { requireOwner, requireViewer } from '@/lib/authz';
import { resolveRegime, setManualRegime } from '@/lib/regime';

export const dynamic = 'force-dynamic';

// Current regime + upcoming blackout windows + recent transitions.
export async function GET() {
  try {
    const denied = await requireViewer();
    if (denied) return NextResponse.json({ error: denied }, { status: 401 });
    await initDb();
    const now = Date.now();
    const regime = await resolveRegime(now);
    const upcoming = await db.select().from(regimeEvents)
      .where(gt(regimeEvents.endAt, now))
      .orderBy(regimeEvents.startAt)
      .limit(20);
    const log = await db.select().from(regimeLog)
      .orderBy(desc(regimeLog.at))
      .limit(20);
    return NextResponse.json({ success: true, regime, upcoming, log });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

// Owner kill switch: set or clear the manual regime override.
// Body: { mode: 'normal' | 'caution' | 'lockdown', reason?, ttlMinutes? }
// 'normal' clears the override and releases any active auto shock.
export async function POST(req: NextRequest) {
  try {
    const denied = await requireOwner();
    if (denied) return NextResponse.json({ error: denied }, { status: 403 });
    await initDb();
    const body = await req.json();
    const mode = body?.mode;
    if (!['normal', 'caution', 'lockdown'].includes(mode)) {
      return NextResponse.json({ error: 'mode must be normal | caution | lockdown' }, { status: 400 });
    }
    // Halting the whole desk is the highest-consequence control on the
    // platform. Like a cloud resource deletion, it demands an explicit typed
    // acknowledgement — enforced server-side so no UI bug, stray script or
    // fat-fingered curl can trip it.
    if (mode === 'lockdown' && String(body?.ack || '') !== 'HALT') {
      return NextResponse.json({ error: "Halting the desk requires ack: 'HALT' — type HALT in the confirmation prompt" }, { status: 400 });
    }
    const ttl = Number.isFinite(body?.ttlMinutes) && body.ttlMinutes > 0 ? body.ttlMinutes : null;
    const now = Date.now();
    await setManualRegime(mode, String(body?.reason || '').slice(0, 200), ttl, now);
    const regime = await resolveRegime(now);
    return NextResponse.json({ success: true, regime });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
