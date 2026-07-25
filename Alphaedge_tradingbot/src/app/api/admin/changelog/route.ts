import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { changelogPublications } from '@/db/schema';
import { inArray, eq } from 'drizzle-orm';
import { initDb } from '@/db/init';
import { requireOwner, getSessionInfo } from '@/lib/authz';
import { CHANGELOG } from '@/app/changelog/changelog-data';

export const dynamic = 'force-dynamic';

// Owner-only publication gate for changelog entries. Entry content is in
// version control; this endpoint only records the decision to show it to
// viewers. Publishing writes a row, un-publishing removes it.
export async function POST(req: NextRequest) {
  try {
    const denied = await requireOwner();
    if (denied) return NextResponse.json({ error: denied }, { status: 403 });
    await initDb();

    const { entryIds, publish } = await req.json();
    if (!Array.isArray(entryIds) || entryIds.length === 0) {
      return NextResponse.json({ error: 'entryIds must be a non-empty array' }, { status: 400 });
    }
    if (typeof publish !== 'boolean') {
      return NextResponse.json({ error: 'publish must be a boolean' }, { status: 400 });
    }
    // Only ids that actually exist in the shipped changelog — no orphan rows.
    const known = new Set(CHANGELOG.map(e => e.id));
    const ids = entryIds.filter((id: unknown): id is string => typeof id === 'string' && known.has(id));
    if (ids.length === 0) {
      return NextResponse.json({ error: 'no known entry ids supplied' }, { status: 400 });
    }

    if (publish) {
      const { user } = await getSessionInfo();
      const now = Date.now();
      for (const entryId of ids) {
        await db.insert(changelogPublications)
          .values({ entryId, publishedAt: now, publishedBy: user?.email ?? null })
          .onConflictDoNothing();
      }
    } else {
      await db.delete(changelogPublications).where(
        ids.length === 1 ? eq(changelogPublications.entryId, ids[0]) : inArray(changelogPublications.entryId, ids)
      );
    }

    return NextResponse.json({ success: true, updated: ids.length, publish });
  } catch (error: any) {
    console.error('Changelog publish error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}
