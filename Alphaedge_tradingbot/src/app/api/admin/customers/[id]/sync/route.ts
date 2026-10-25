import { NextRequest, NextResponse } from 'next/server';
import { ownerOrError, fail } from '@/lib/api';
import { syncCustomer } from '@/lib/customers';

export const dynamic = 'force-dynamic';

export async function POST(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const g = await ownerOrError(); if ('error' in g) return g.error;
  try {
    const { id } = await params;
    return NextResponse.json(await syncCustomer(id));
  } catch (e) { return fail(e, 409); }
}
