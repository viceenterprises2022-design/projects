import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { users, onboardingProfiles } from '@/db/schema';
import { eq, inArray, sql, and } from 'drizzle-orm';
import { initDb } from '@/db/init';
import { requireOwner } from '@/lib/authz';

export const dynamic = 'force-dynamic';

const PAGE_SIZE = 50;
const ROLES = ['pending', 'viewer', 'owner', 'blocked'];

// Owner-only access management. Paginated and filterable so the list stays
// usable as sign-ups grow: the page fetches one slice plus the onboarding
// answers for just that slice, never the whole table.
export async function GET(req: NextRequest) {
  try {
    const denied = await requireOwner();
    if (denied) return NextResponse.json({ error: denied }, { status: 403 });
    await initDb();

    const q = (req.nextUrl.searchParams.get('q') || '').trim().toLowerCase();
    const role = req.nextUrl.searchParams.get('role') || 'all';
    const page = Math.max(1, parseInt(req.nextUrl.searchParams.get('page') || '1', 10) || 1);

    const conds = [sql`${users.email} LIKE '%@%'`]; // hide legacy seed rows
    if (ROLES.includes(role)) conds.push(eq(users.role, role));
    if (q) {
      conds.push(sql`(lower(${users.email}) LIKE ${'%' + q + '%'} OR lower(coalesce(${users.name}, '')) LIKE ${'%' + q + '%'})`);
    }
    const where = and(...conds)!;

    // Pending first — those are the ones needing action.
    const rows = await db.select({
      id: users.id,
      name: users.name,
      email: users.email,
      image: users.image,
      role: users.role,
      createdAt: users.createdAt,
    })
      .from(users)
      .where(where)
      .orderBy(sql`CASE ${users.role} WHEN 'pending' THEN 0 WHEN 'viewer' THEN 1 WHEN 'owner' THEN 2 ELSE 3 END`, users.email)
      .limit(PAGE_SIZE + 1)
      .offset((page - 1) * PAGE_SIZE);

    const hasNext = rows.length > PAGE_SIZE;
    const pageRows = rows.slice(0, PAGE_SIZE);

    // Onboarding answers for THIS page only.
    const emails = pageRows.map(u => (u.email || '').toLowerCase()).filter(Boolean);
    const profiles = emails.length
      ? await db.select().from(onboardingProfiles).where(inArray(onboardingProfiles.email, emails))
      : [];
    const byEmail = new Map(profiles.map(p => [p.email, p]));
    const enriched = pageRows.map(u => {
      const p = byEmail.get((u.email || '').toLowerCase());
      return p ? {
        ...u,
        onboarding: {
          fullName: p.fullName,
          levelInterest: p.levelInterest,
          capitalBand: p.capitalBand,
          experience: p.experience,
          note: p.note,
          submittedAt: p.updatedAt,
        },
      } : u;
    });

    // Role tallies for the filter chips — one grouped scan.
    const tallyRows = await db.select({ role: users.role, n: sql<number>`COUNT(*)` })
      .from(users).where(sql`${users.email} LIKE '%@%'`).groupBy(users.role);
    const counts: Record<string, number> = { all: 0 };
    for (const t of tallyRows) { counts[t.role] = Number(t.n); counts.all += Number(t.n); }

    return NextResponse.json({ users: enriched, page, pageSize: PAGE_SIZE, hasNext, counts });
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
