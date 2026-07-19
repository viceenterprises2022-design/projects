import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { regimeEvents } from '@/db/schema';
import { eq } from 'drizzle-orm';
import { initDb } from '@/db/init';
import { requireOwner } from '@/lib/authz';

export const dynamic = 'force-dynamic';

// Owner-managed blackout calendar.
// Body: { label, kind, severity: 'caution' | 'lockdown', startAt, endAt } (ms epochs)
export async function POST(req: NextRequest) {
  try {
    const denied = await requireOwner();
    if (denied) return NextResponse.json({ error: denied }, { status: 403 });
    await initDb();
    const body = await req.json();
    const { label, kind, severity, startAt, endAt } = body || {};
    if (!label || !Number.isFinite(startAt) || !Number.isFinite(endAt) || endAt <= startAt) {
      return NextResponse.json({ error: 'label, startAt and endAt (ms, endAt > startAt) are required' }, { status: 400 });
    }
    const event = {
      id: `ev_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      label: String(label).slice(0, 120),
      kind: ['fed', 'cpi', 'nfp', 'crypto', 'other'].includes(kind) ? kind : 'other',
      severity: severity === 'caution' ? 'caution' : 'lockdown',
      startAt,
      endAt,
      createdAt: Date.now(),
    };
    await db.insert(regimeEvents).values(event);
    return NextResponse.json({ success: true, event });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

export async function DELETE(req: NextRequest) {
  try {
    const denied = await requireOwner();
    if (denied) return NextResponse.json({ error: denied }, { status: 403 });
    await initDb();
    const id = req.nextUrl.searchParams.get('id');
    if (!id) return NextResponse.json({ error: 'id required' }, { status: 400 });
    await db.delete(regimeEvents).where(eq(regimeEvents.id, id));
    return NextResponse.json({ success: true });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
