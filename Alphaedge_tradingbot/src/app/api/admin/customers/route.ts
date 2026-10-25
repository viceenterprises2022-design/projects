import { NextRequest, NextResponse } from 'next/server';
import { ownerOrError, fail } from '@/lib/api';
import { createCustomer, listCustomers, feeAddress } from '@/lib/customers';
import { customerNetwork } from '@/lib/hyperliquid-info';

export const dynamic = 'force-dynamic';

// Owner-only. GET lists every customer with balance, profit and fees owed;
// POST onboards one with a manual profit-share percentage.
export async function GET() {
  const g = await ownerOrError(); if ('error' in g) return g.error;
  try {
    return NextResponse.json({ customers: await listCustomers(), feeAddress: feeAddress(), network: customerNetwork() });
  } catch (e) { return fail(e, 500); }
}

export async function POST(req: NextRequest) {
  const g = await ownerOrError(); if ('error' in g) return g.error;
  try {
    const body = await req.json();
    const c = await createCustomer(body, g.actor);
    return NextResponse.json({ customer: c }, { status: 201 });
  } catch (e) { return fail(e); }
}
