import { NextResponse } from 'next/server';
import { initDb } from '@/db/init';
import { getSessionInfo } from '@/lib/authz';
import { customerForEmail, syncCustomer } from '@/lib/customers';

export const dynamic = 'force-dynamic';

const FRESH_MS = 2 * 60_000;

// A customer's own account: balance, profit, fee owed and withdrawal history.
// Access is by login email matching the onboarded customer record; a customer
// can never see anyone else's data. Internal fields are stripped.
export async function GET() {
  const { user } = await getSessionInfo();
  const email = user?.email?.toLowerCase();
  if (!email) return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
  try {
    await initDb();
    let d = await customerForEmail(email);
    if (!d) return NextResponse.json({ error: 'No managed account is linked to this login' }, { status: 404 });
    if (!d.summary.lastSyncedAt || Date.now() - d.summary.lastSyncedAt > FRESH_MS) {
      try { await syncCustomer(d.customer.id); d = await customerForEmail(email); } catch { /* serve last snapshot */ }
    }
    const { customer: c, summary, totals, flows, fees, feeAddress } = d!;
    return NextResponse.json({
      name: c.name, walletAddress: c.walletAddress, profitSharePct: c.profitSharePct, status: c.status, since: c.syncFrom,
      summary: { ...summary, lastError: undefined }, totals, feeAddress,
      flows: flows.filter(f => f.kind !== 'unclassified'),
      fees: fees.map(f => ({ kind: f.kind, fee: f.fee, amount: f.amount, profit: f.profit, pct: f.pct, createdAt: f.createdAt, outstandingAfter: f.outstandingAfter })),
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message || 'Internal error' }, { status: 500 });
  }
}
