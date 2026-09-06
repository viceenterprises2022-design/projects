import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { eq } from 'drizzle-orm';
import { initDb } from '@/db/init';
import { requireOwner } from '@/lib/authz';
import { DEMO_BANKROLL_BASE } from '@/lib/engine';
import {
  engineRounds, simulatorTrades, orders, signals, ledgerEntries,
  riskEvents, levelLocks, assetState, regimeLog, regimeState, demoAccount,
} from '@/db/schema';

export const dynamic = 'force-dynamic';

// ---------------------------------------------------------------------------
// Owner-only full desk reset: clears trading HISTORY and returns the counters
// to a clean slate. Deliberately narrow about what that means.
//
// AUTHENTICATION AND ACCESS ARE NEVER TOUCHED. `users` carries the `role`
// column that IS the access list — clearing it would drop every account,
// including the owner's, back to 'pending' and lock the desk against its own
// operator. Same for `accounts` (Google links) and `sessions` (live logins).
// Nobody is even signed out by this.
//
// The waitlist and applicant data are not history either — deleting
// early_access_leads or onboarding_profiles would destroy the signup pipeline,
// which no reset should do.
//
// The ledger is cleared ALL-OR-NOTHING on purpose. appendToLedger() chains each
// entry to the previous hash and restarts from the genesis hash only when the
// table is empty, so a partial delete would leave a permanently unverifiable
// chain. Empty is valid; half-empty is broken forever.
// ---------------------------------------------------------------------------

const CONFIRM = 'RESET DESK';

export async function POST(req: NextRequest) {
  const denied = await requireOwner();
  if (denied) return NextResponse.json({ error: denied }, { status: 403 });

  // Typed confirmation, matching the HALT DESK pattern. A destructive endpoint
  // should not fire on a stray request or a refreshed tab.
  let confirm: unknown = null;
  try {
    confirm = (await req.json())?.confirm;
  } catch {
    /* no body */
  }
  if (confirm !== CONFIRM) {
    return NextResponse.json({
      error: `Confirmation required. POST {"confirm":"${CONFIRM}"} to proceed.`,
      willClear: [
        'engine_rounds', 'simulator_trades', 'orders', 'signals',
        'ledger_entries', 'risk_events', 'level_locks', 'asset_state', 'regime_log',
      ],
      willReset: ['demo_account (back to $' + DEMO_BANKROLL_BASE + ')', 'regime_state (back to normal)'],
      willPreserve: [
        'users / accounts / sessions — login and access list, untouched',
        'early_access_leads — waitlist',
        'onboarding_profiles — applicant details',
        'bot_templates / bot_instances / exchange_connections — configuration',
        'changelog_publications — product history',
        'regime_events — scheduled blackout calendar',
      ],
    }, { status: 400 });
  }

  try {
    await initDb();
    const now = Date.now();
    const cleared: Record<string, string> = {};

    // History. Order does not matter — no foreign keys are enforced here — but
    // the ledger goes last so a failure part-way leaves it intact rather than
    // severed mid-chain.
    await db.delete(engineRounds);       cleared.engine_rounds = 'cleared';
    await db.delete(simulatorTrades);    cleared.simulator_trades = 'cleared';
    await db.delete(orders);             cleared.orders = 'cleared';
    await db.delete(signals);            cleared.signals = 'cleared';
    await db.delete(riskEvents);         cleared.risk_events = 'cleared';
    await db.delete(levelLocks);         cleared.level_locks = 'cleared';
    await db.delete(assetState);         cleared.asset_state = 'cleared';
    await db.delete(regimeLog);          cleared.regime_log = 'cleared';
    await db.delete(ledgerEntries);      cleared.ledger_entries = 'cleared (chain restarts at genesis)';

    // Counters back to a clean start.
    await db.insert(demoAccount)
      .values({ id: 'demo', baseUsd: DEMO_BANKROLL_BASE, startedAt: now })
      .onConflictDoUpdate({
        target: demoAccount.id,
        set: { baseUsd: DEMO_BANKROLL_BASE, startedAt: now },
      });

    // Release any manual halt or shock cooldown so the desk resumes clean.
    await db.update(regimeState)
      .set({ manualMode: null, manualReason: null, manualUntil: null, shockUntil: null })
      .where(eq(regimeState.id, 'regime'));

    return NextResponse.json({
      success: true,
      startedAt: now,
      baseUsd: DEMO_BANKROLL_BASE,
      cleared,
      preserved: 'users, accounts, sessions, early_access_leads, onboarding_profiles, bot_templates, bot_instances, exchange_connections, changelog_publications, regime_events',
      note: 'Login and desk access are unchanged — no account was modified and nobody was signed out.',
    });
  } catch (error: any) {
    console.error('Desk reset error:', error);
    return NextResponse.json({ error: error?.message || 'Reset failed' }, { status: 500 });
  }
}
