import { NextResponse } from 'next/server';
import { engineTick, getMarks, DEMO_BANKROLL_BASE } from '@/lib/engine';

export const dynamic = 'force-dynamic';

// Single canonical endpoint: every call advances the engine (idempotent —
// epoch rounds + settlement guards make concurrent ticks safe) and returns
// the live state. Viewers poll this; the cron heartbeat hits it too.
export async function GET() {
  try {
    const tick = await engineTick();
    let marks: Record<string, number> = {};
    try { marks = await getMarks(); } catch { /* reported in tick.errors */ }
    return NextResponse.json({
      success: true,
      now: tick.now,
      epoch: tick.epoch,
      roundEndsAt: (tick.epoch + 1) * 90_000,
      bankroll: tick.bankroll,
      bankrollBase: DEMO_BANKROLL_BASE,
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
