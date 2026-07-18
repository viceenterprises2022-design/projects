import { auth } from '@/auth';

// Owners are the operators of the desk (full controls). Everyone else —
// signed-in or anonymous — is a watch-only viewer during the demo.
// OWNER_EMAILS: comma-separated list, e.g. "vice.enterprises2022@gmail.com"
export function ownerEmails(): string[] {
  return (process.env.OWNER_EMAILS || '')
    .split(',')
    .map(e => e.trim().toLowerCase())
    .filter(Boolean);
}

export interface SessionInfo {
  user: { id?: string; name?: string | null; email?: string | null; image?: string | null } | null;
  isOwner: boolean;
}

export async function getSessionInfo(): Promise<SessionInfo> {
  try {
    const session = await auth();
    const email = session?.user?.email?.toLowerCase() || null;
    return {
      user: session?.user ?? null,
      isOwner: !!email && ownerEmails().includes(email),
    };
  } catch {
    // Auth not configured yet (missing env) — treat as anonymous viewer.
    return { user: null, isOwner: false };
  }
}

// Guard for mutating API routes: returns null when authorized, or a reason string.
export async function requireOwner(): Promise<string | null> {
  const { user, isOwner } = await getSessionInfo();
  if (!user) return 'Authentication required';
  if (!isOwner) return 'Owner access required — this desk is watch-only for viewers';
  return null;
}
