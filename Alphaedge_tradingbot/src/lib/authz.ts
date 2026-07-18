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

// Demo viewers: invited emails allowed to WATCH the desk (read-only).
// DEMO_VIEWER_EMAILS: comma-separated list. Owners are always viewers.
export function viewerEmails(): string[] {
  return (process.env.DEMO_VIEWER_EMAILS || '')
    .split(',')
    .map(e => e.trim().toLowerCase())
    .filter(Boolean);
}

export interface SessionInfo {
  user: { id?: string; name?: string | null; email?: string | null; image?: string | null } | null;
  isOwner: boolean;
  canView: boolean;
}

export async function getSessionInfo(): Promise<SessionInfo> {
  try {
    const session = await auth();
    const email = session?.user?.email?.toLowerCase() || null;
    const isOwner = !!email && ownerEmails().includes(email);
    return {
      user: session?.user ?? null,
      isOwner,
      canView: isOwner || (!!email && viewerEmails().includes(email)),
    };
  } catch {
    // Auth not configured yet (missing env) — treat as anonymous.
    return { user: null, isOwner: false, canView: false };
  }
}

// Guard for read APIs: invited viewers (or owners) only.
export async function requireViewer(): Promise<string | null> {
  const { user, canView } = await getSessionInfo();
  if (!user) return 'Authentication required';
  if (!canView) return 'Not on the demo access list';
  return null;
}

// Guard for mutating API routes: returns null when authorized, or a reason string.
export async function requireOwner(): Promise<string | null> {
  const { user, isOwner } = await getSessionInfo();
  if (!user) return 'Authentication required';
  if (!isOwner) return 'Owner access required — this desk is watch-only for viewers';
  return null;
}
