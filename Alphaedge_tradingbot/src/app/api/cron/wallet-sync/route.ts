import { NextRequest, NextResponse } from 'next/server';
import { initDb } from '@/db/init';
import { getSessionInfo } from '@/lib/authz';
import { syncAll } from '@/lib/customers';

export const dynamic = 'force-dynamic';
export const maxDuration = 60;

// Every 5 minutes (vercel.json). Keeps the gap between a customer's
// withdrawal and its fee crystallisation small, which is what bounds the
// balance-reconstruction error (see syncCustomer).
// Auth: Vercel cron sends `Authorization: Bearer $CRON_SECRET` when that env
// var is set. Without it, only a signed-in owner may trigger a run.
export async function GET(req: NextRequest) {
  const secret = process.env.CRON_SECRET;
  const bearer = req.headers.get('authorization');
  let ok = !!secret && bearer === `Bearer ${secret}`;
  if (!ok) ok = (await getSessionInfo()).isOwner;
  if (!ok) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  try {
    await initDb();
    const results = await syncAll();
    return NextResponse.json({ ok: true, ran: results.length, errors: results.filter(r => r.error).length, results });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
