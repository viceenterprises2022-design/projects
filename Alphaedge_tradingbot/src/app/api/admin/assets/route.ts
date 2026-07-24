import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { assetState } from '@/db/schema';
import { initDb } from '@/db/init';
import { requireOwner } from '@/lib/authz';
import { ENGINE_ASSETS } from '@/lib/engine';

export const dynamic = 'force-dynamic';

// Owner-only per-asset kill switches. Current state travels in the engine
// payload (assetEnabled) — this endpoint only flips a switch.
export async function POST(req: NextRequest) {
  try {
    const denied = await requireOwner();
    if (denied) return NextResponse.json({ error: denied }, { status: 403 });
    await initDb();

    const { asset, enabled } = await req.json();
    if (!ENGINE_ASSETS.includes(asset)) {
      return NextResponse.json({ error: `asset must be one of ${ENGINE_ASSETS.join(', ')}` }, { status: 400 });
    }
    if (typeof enabled !== 'boolean') {
      return NextResponse.json({ error: 'enabled must be a boolean' }, { status: 400 });
    }

    await db.insert(assetState)
      .values({ asset, enabled: enabled ? 1 : 0, updatedAt: Date.now() })
      .onConflictDoUpdate({
        target: assetState.asset,
        set: { enabled: enabled ? 1 : 0, updatedAt: Date.now() },
      });

    return NextResponse.json({ success: true, asset, enabled });
  } catch (error: any) {
    console.error('Asset toggle error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}
