import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { onboardingProfiles } from '@/db/schema';
import { initDb } from '@/db/init';
import { getSessionInfo } from '@/lib/authz';

export const dynamic = 'force-dynamic';

const LEVEL_INTERESTS = ['demo', 'level-1', 'level-2', 'level-3', 'undecided'];
const CAPITAL_BANDS = ['under-5k', '5k-10k', '10k-25k', '25k-plus', 'exploring'];
const EXPERIENCE_BANDS = ['new', 'casual', 'active', 'professional'];

// Onboarding intake for authenticated-but-unapproved users. The email is
// always taken from the session — never from the request body — so answers
// are guaranteed to match the Google account shown in Access Control.
export async function POST(req: NextRequest) {
  try {
    const { user, role } = await getSessionInfo();
    const email = user?.email?.toLowerCase();
    if (!user || !email) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
    }
    if (role === 'blocked') {
      return NextResponse.json({ error: 'This account has been declined' }, { status: 403 });
    }
    await initDb();

    const body = await req.json();
    const fullName = typeof body.fullName === 'string' ? body.fullName.trim().slice(0, 80) : '';
    const levelInterest = String(body.levelInterest || '');
    const capitalBand = String(body.capitalBand || '');
    const experience = String(body.experience || '');
    const note = typeof body.note === 'string' ? body.note.trim().slice(0, 500) : '';

    if (fullName.length < 2) {
      return NextResponse.json({ error: 'Please enter your full name' }, { status: 400 });
    }
    if (!LEVEL_INTERESTS.includes(levelInterest)) {
      return NextResponse.json({ error: 'Invalid level interest' }, { status: 400 });
    }
    if (!CAPITAL_BANDS.includes(capitalBand)) {
      return NextResponse.json({ error: 'Invalid capital band' }, { status: 400 });
    }
    if (!EXPERIENCE_BANDS.includes(experience)) {
      return NextResponse.json({ error: 'Invalid experience selection' }, { status: 400 });
    }

    const now = Date.now();
    await db.insert(onboardingProfiles)
      .values({ email, fullName, levelInterest, capitalBand, experience, note: note || null, createdAt: now, updatedAt: now })
      .onConflictDoUpdate({
        target: onboardingProfiles.email,
        set: { fullName, levelInterest, capitalBand, experience, note: note || null, updatedAt: now },
      });

    return NextResponse.json({ success: true });
  } catch (error: any) {
    console.error('Onboarding save error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}
