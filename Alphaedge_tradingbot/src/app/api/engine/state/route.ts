import { NextResponse } from 'next/server';
import { engineTick, getMarks, ENGINE_PARAMS, ROUND_MS } from '@/lib/engine';
import { requireViewer } from '@/lib/authz';

export const dynamic = 'force-dynamic';

// Single canonical endpoint: every call advances the engine (idempotent —
// epoch rounds + settlement guards make concurrent ticks safe) and returns
// the live state. Viewers poll this; the cron heartbeat hits it too.
export async function GET() {
  try {
    // Tick unconditionally so any request (viewer poll, cron, pinger) keeps
    // the canonical engine trading — but only invited viewers get the data.
    const tick = await engineTick();
    const denied = await requireViewer();
    if (denied) {
      return NextResponse.json({ success: false, error: denied, ticked: true }, { status: 401 });
    }
    let marks: Record<string, number> = {};
    try { marks = await getMarks(); } catch { /* reported in tick.errors */ }
    return NextResponse.json({
      success: true,
      now: tick.now,
      epoch: tick.epoch,
      roundEndsAt: (tick.epoch + 1) * ROUND_MS,
      bankroll: tick.bankroll,
      bankrollBase: tick.bankrollBase,
      demoStartedAt: tick.demoStartedAt,
      params: ENGINE_PARAMS,
      marks,
      rounds: tick.rounds,
      settledThisTick: tick.settled,
      errors: tick.errors,
    });
  } catch (error: any) {
    console.error('Engine tick error:', error);
    return NextResponse.json({ success: false, error: error.message || 'Engine tick failed' }, { status: 500 });
  }
}
