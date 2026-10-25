import { NextResponse } from 'next/server';
import { initDb } from '@/db/init';
import { getSessionInfo } from '@/lib/authz';

// Shared guard for owner-only customer and fee routes. Returns the acting
// owner's email (recorded on every fee event) or a ready error response.
export async function ownerOrError(): Promise<{ actor: string } | { error: NextResponse }> {
  const { user, isOwner } = await getSessionInfo();
  if (!user) return { error: NextResponse.json({ error: 'Authentication required' }, { status: 401 }) };
  if (!isOwner) return { error: NextResponse.json({ error: 'Owner access required' }, { status: 403 }) };
  await initDb();
  return { actor: String(user.email ?? 'owner') };
}

export const fail = (e: unknown, status = 400) =>
  NextResponse.json({ error: (e as any)?.message || String(e) }, { status });
