import { auth } from '@/auth';
import { db } from '@/db';
import { users } from '@/db/schema';
import { eq } from 'drizzle-orm';

// ---------------------------------------------------------------------------
// Access control is DATABASE-BACKED: every Google sign-in creates a users row
// (via the NextAuth adapter) whose `role` gates what they can do:
//   'owner'   — desk operator: full controls + access management
//   'viewer'  — invited demo watcher: read-only dashboard
//   'pending' — signed up, awaiting approval (default for new sign-ins)
//   'blocked' — explicitly denied
//
// Env vars are BOOTSTRAP ONLY (no redeploy needed to manage users):
//   OWNER_EMAILS       — emails promoted to 'owner' on sign-in
//   DEMO_VIEWER_EMAILS — emails auto-approved to 'viewer' on first sign-in
// After bootstrap, roles are managed from the dashboard's Access Control panel.
// ---------------------------------------------------------------------------

export function ownerEmails(): string[] {
  return (process.env.OWNER_EMAILS || '')
    .split(',')
    .map(e => e.trim().toLowerCase())
    .filter(Boolean);
}

export function viewerEmails(): string[] {
  return (process.env.DEMO_VIEWER_EMAILS || '')
    .split(',')
    .map(e => e.trim().toLowerCase())
    .filter(Boolean);
}

export type Role = 'owner' | 'viewer' | 'pending' | 'blocked';

export interface SessionInfo {
  user: { id?: string; name?: string | null; email?: string | null; image?: string | null } | null;
  role: Role | null;
  isOwner: boolean;
  canView: boolean;
}

export async function getSessionInfo(): Promise<SessionInfo> {
  // Development-only bypass for local testing without OAuth env.
  // Inert in production builds (NODE_ENV check) and requires an explicit
  // env var that is never set in Vercel.
  if (process.env.NODE_ENV === 'development' && process.env.DEV_FAKE_ROLE) {
    const valid: Role[] = ['owner', 'viewer', 'pending', 'blocked'];
    const role = (valid.includes(process.env.DEV_FAKE_ROLE as Role)
      ? process.env.DEV_FAKE_ROLE : 'viewer') as Role;
    return {
      user: { id: 'dev', name: 'Dev Tester', email: 'dev@local' },
      role,
      isOwner: role === 'owner',
      canView: role === 'owner' || role === 'viewer',
    };
  }
  try {
    const session = await auth();
    const email = session?.user?.email?.toLowerCase() || null;
    if (!session?.user || !email) {
      return { user: null, role: null, isOwner: false, canView: false };
    }

    const rows = await db.select({ id: users.id, role: users.role })
      .from(users).where(eq(users.email, email)).limit(1);
    let role = (rows[0]?.role as Role) ?? 'pending';
    const userId = rows[0]?.id;

    // Bootstrap promotions from env (idempotent, one DB write on first touch)
    if (userId && role !== 'owner' && ownerEmails().includes(email)) {
      await db.update(users).set({ role: 'owner' }).where(eq(users.id, userId));
      role = 'owner';
    } else if (userId && role === 'pending' && viewerEmails().includes(email)) {
      await db.update(users).set({ role: 'viewer' }).where(eq(users.id, userId));
      role = 'viewer';
    }

    return {
      user: session.user,
      role,
      isOwner: role === 'owner',
      canView: role === 'owner' || role === 'viewer',
    };
  } catch {
    // Auth not configured (missing env) — treat as anonymous.
    return { user: null, role: null, isOwner: false, canView: false };
  }
}

// Guard for read APIs: approved viewers (or owners) only.
export async function requireViewer(): Promise<string | null> {
  const { user, canView } = await getSessionInfo();
  if (!user) return 'Authentication required';
  if (!canView) return 'Access pending approval by the desk operator';
  return null;
}

// Guard for mutating API routes: returns null when authorized, or a reason string.
export async function requireOwner(): Promise<string | null> {
  const { user, isOwner } = await getSessionInfo();
  if (!user) return 'Authentication required';
  if (!isOwner) return 'Owner access required — this desk is watch-only for viewers';
  return null;
}
