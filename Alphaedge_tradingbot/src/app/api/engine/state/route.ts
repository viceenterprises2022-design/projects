import { NextResponse } from 'next/server';
import { engineTick, getMarks, ENGINE_PARAMS, ROUND_MS } from '@/lib/engine';
import { requireViewer } from '@/lib/authz';

export const dynamic = 'force-dynamic';

// Snapshot cache: Turso bills rows SCANNED as reads, and a tick aggregates
// over the full demo ledger. Concurrent viewer polls within this window share
// one tick instead of each re-scanning the ledger — engine correctness is
// unaffected because rounds are epoch-deterministic and settlement is
// idempotent, so a few seconds of staleness only delays display, not trading.
const SNAPSHOT_TTL_MS = 4_000;
let snapshot: { at: number; body: Record<string, unknown> } | null = null;

// Single canonical endpoint: every call advances the engine (idempotent —
// epoch rounds + settlement guards make concurrent ticks safe) and returns
// the live state. Viewers poll this; the cron heartbeat hits it too.
export async function GET() {
  try {
    // Tick (or reuse a fresh snapshot) unconditionally so any request keeps
    // the canonical engine trading — but only invited viewers get the data.
    let body = snapshot && Date.now() - snapshot.at < SNAPSHOT_TTL_MS ? snapshot.body : null;
    if (!body) {
      const tick = await engineTick();
      let marks: Record<string, number> = {};
      try { marks = await getMarks(); } catch { /* reported in tick.errors */ }
      body = {
        success: true,
        now: tick.now,
        epoch: tick.epoch,
        roundEndsAt: (tick.epoch + 1) * ROUND_MS,
        bankroll: tick.bankroll,
        bankrollBase: tick.bankrollBase,
        demoStartedAt: tick.demoStartedAt,
        levels: tick.levels,
        regime: tick.regime,
        quotaResetAt: tick.quotaResetAt,
        assetEnabled: tick.assetEnabled,
        params: ENGINE_PARAMS,
        marks,
        rounds: tick.rounds,
        settledThisTick: tick.settled,
        errors: tick.errors,
      };
      snapshot = { at: Date.now(), body };
    }
    const denied = await requireViewer();
    if (denied) {
      return NextResponse.json({ success: false, error: denied, ticked: true }, { status: 401 });
    }
    return NextResponse.json(body);
  } catch (error: any) {
    console.error('Engine tick error:', error);
    return NextResponse.json({ success: false, error: error.message || 'Engine tick failed' }, { status: 500 });
  }
}
