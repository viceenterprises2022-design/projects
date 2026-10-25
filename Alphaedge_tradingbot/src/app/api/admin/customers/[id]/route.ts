import { NextRequest, NextResponse } from 'next/server';
import { ownerOrError, fail } from '@/lib/api';
import { customerDetail, updateCustomer } from '@/lib/customers';

export const dynamic = 'force-dynamic';

export async function GET(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const g = await ownerOrError(); if ('error' in g) return g.error;
  try {
    const { id } = await params;
    const d = await customerDetail(id);
    if (!d) return NextResponse.json({ error: 'Customer not found' }, { status: 404 });
    return NextResponse.json(d);
  } catch (e) { return fail(e, 500); }
}

// Change profit share (forward-only), status or notes.
export async function PATCH(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const g = await ownerOrError(); if ('error' in g) return g.error;
  try {
    const { id } = await params;
    const body = await req.json();
    return NextResponse.json({ customer: await updateCustomer(id, body, g.actor) });
  } catch (e) { return fail(e); }
}
