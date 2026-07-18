import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { users } from '@/db/schema';
import { eq } from 'drizzle-orm';
import { initDb } from '@/db/init';
import { requireOwner } from '@/lib/authz';

export const dynamic = 'force-dynamic';

// Owner-only access management: list everyone who has signed in and change
// their role from the dashboard — no env changes, no redeploys.

export async function GET() {
  try {
    const denied = await requireOwner();
    if (denied) return NextResponse.json({ error: denied }, { status: 403 });
    await initDb();

    const rows = await db.select({
      id: users.id,
      name: users.name,
      email: users.email,
      image: users.image,
      role: users.role,
      createdAt: users.createdAt,
    }).from(users);

    // Hide legacy seed rows without real emails/sign-ins
    const accounts = rows.filter(u => !!u.email && u.email.includes('@'));
    const order: Record<string, number> = { pending: 0, viewer: 1, owner: 2, blocked: 3 };
    accounts.sort((a, b) => (order[a.role] ?? 9) - (order[b.role] ?? 9) || (a.email || '').localeCompare(b.email || ''));

    return NextResponse.json({ users: accounts });
  } catch (error: any) {
    console.error('Admin users list error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const denied = await requireOwner();
    if (denied) return NextResponse.json({ error: denied }, { status: 403 });
    await initDb();

    const { userId, action } = await req.json();
    if (!userId || typeof userId !== 'string') {
      return NextResponse.json({ error: 'userId is required' }, { status: 400 });
    }
    const roleFor: Record<string, string> = { approve: 'viewer', revoke: 'pending', block: 'blocked' };
    const nextRole = roleFor[action];
    if (!nextRole) {
      return NextResponse.json({ error: 'action must be approve | revoke | block' }, { status: 400 });
    }

    const target = await db.select({ id: users.id, role: users.role }).from(users).where(eq(users.id, userId)).limit(1);
    if (target.length === 0) return NextResponse.json({ error: 'User not found' }, { status: 404 });
    if (target[0].role === 'owner') {
      return NextResponse.json({ error: 'Owner roles are managed via OWNER_EMAILS, not this panel' }, { status: 400 });
    }

    await db.update(users).set({ role: nextRole }).where(eq(users.id, userId));
    return NextResponse.json({ success: true, userId, role: nextRole });
  } catch (error: any) {
    console.error('Admin users update error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}
