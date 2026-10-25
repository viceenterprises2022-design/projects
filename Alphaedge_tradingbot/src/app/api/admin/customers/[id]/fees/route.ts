import { NextRequest, NextResponse } from 'next/server';
import { ownerOrError, fail } from '@/lib/api';
import { recordManualFee, customerDetail } from '@/lib/customers';

export const dynamic = 'force-dynamic';

// Owner records a fee paid off-venue (bank, UPI) or waives it. Payments made
// on Hyperliquid to the fee wallet are matched automatically by the sync and
// must NOT also be entered here.
export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const g = await ownerOrError(); if ('error' in g) return g.error;
  try {
    const { id } = await params;
    const { kind, amount, note } = await req.json();
    if (kind !== 'manual_payment' && kind !== 'waiver') throw new Error('kind must be manual_payment or waiver');
    await recordManualFee(id, kind, amount, note, g.actor);
    return NextResponse.json(await customerDetail(id));
  } catch (e) { return fail(e); }
}
