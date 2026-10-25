import { NextRequest, NextResponse } from 'next/server';
import { ownerOrError, fail } from '@/lib/api';
import { walletAnalytics } from '@/lib/customers';

export const dynamic = 'force-dynamic';

// Per-wallet analytics from the customer's own Hyperliquid fills. Reads the
// venue only; no database rows are scanned for trades.
export async function GET(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const g = await ownerOrError(); if ('error' in g) return g.error;
  try {
    const { id } = await params;
    const a = await walletAnalytics(id);
    if (!a) return NextResponse.json({ error: 'Customer not found' }, { status: 404 });
    return NextResponse.json(a);
  } catch (e) { return fail(e, 502); }
}
