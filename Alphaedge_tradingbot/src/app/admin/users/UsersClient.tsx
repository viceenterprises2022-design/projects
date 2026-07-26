'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import ThemeToggle from '../../ThemeToggle';

// Owner-only access management. One bounded fetch per action (filter, search,
// page, refresh) — no polling. Pending accounts sort first because they are
// the only rows that need a decision.

const ROLE_TABS = [
  { key: 'pending', label: 'PENDING' },
  { key: 'viewer', label: 'APPROVED' },
  { key: 'blocked', label: 'BLOCKED' },
  { key: 'owner', label: 'OWNERS' },
  { key: 'all', label: 'ALL' },
];

const roleTag = (r: string) =>
  r === 'owner' ? 'gold' : r === 'viewer' ? 'win' : r === 'blocked' ? 'loss' : 'violet';

const pretty = (v: string) => String(v || '').replace(/-/g, ' ').toUpperCase();

export default function UsersClient() {
  const [role, setRole] = useState('pending');
  const [q, setQ] = useState('');
  const [debouncedQ, setDebouncedQ] = useState('');
  const [page, setPage] = useState(1);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [acting, setActing] = useState<string | null>(null);

  useEffect(() => {
    const t = setTimeout(() => { setDebouncedQ(q); setPage(1); }, 350);
    return () => clearTimeout(t);
  }, [q]);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const res = await fetch(`/api/admin/users?role=${role}&page=${page}&q=${encodeURIComponent(debouncedQ)}`);
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Failed to load accounts');
      setData(json);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [role, page, debouncedQ]);

  useEffect(() => { load(); }, [load]);

  const act = async (userId: string, action: 'approve' | 'revoke' | 'block') => {
    setActing(userId);
    try {
      const res = await fetch('/api/admin/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId, action }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Update failed');
      await load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setActing(null);
    }
  };

  const counts = data?.counts || {};
  const rows = data?.users || [];

  return (
    <div className="fable">
      <div className="f-shell">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, margin: '18px 0 14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <span className="f-brand-mark" style={{ width: 40, height: 40, fontSize: 17, borderRadius: 13 }}>P</span>
            <div>
              <div className="f-serif-grad" style={{ fontSize: 22 }}>Access Control</div>
              <div className="f-kicker">DB-BACKED · NO REDEPLOYS · PENDING FIRST</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            {counts.pending > 0 && <span className="f-tag violet">{counts.pending} AWAITING APPROVAL</span>}
            <button className="f-btn" style={{ padding: '7px 14px', fontSize: 10 }} onClick={load} disabled={loading}>
              {loading ? 'LOADING…' : 'REFRESH'}
            </button>
            <ThemeToggle compact />
            <Link href="/dashboard" className="f-btn" style={{ padding: '7px 14px', fontSize: 10, textDecoration: 'none' }}>← COCKPIT</Link>
          </div>
        </div>

        <div className="f-panel">
          <div className="f-panel-head" style={{ flexWrap: 'wrap', gap: 10 }}>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {ROLE_TABS.map(t => (
                <button key={t.key} className="f-btn" onClick={() => { setRole(t.key); setPage(1); }}
                  style={{
                    padding: '5px 13px', fontSize: 9.5,
                    ...(role === t.key ? { borderColor: 'rgba(88,240,255,0.55)', color: '#58f0ff', background: 'rgba(88,240,255,0.08)' } : {}),
                  }}>
                  {t.label}{counts[t.key] !== undefined ? ` (${counts[t.key]})` : ''}
                </button>
              ))}
            </div>
            <input
              className="f-input"
              placeholder="Search name or email…"
              value={q}
              onChange={e => setQ(e.target.value)}
              style={{ maxWidth: 260, padding: '6px 11px', fontSize: 12 }}
            />
          </div>

          {error ? (
            <div className="f-empty" style={{ color: 'var(--oxide)' }}>{error}</div>
          ) : rows.length === 0 && !loading ? (
            <div className="f-empty">
              {debouncedQ ? `No accounts match “${debouncedQ}”.` : role === 'pending' ? 'No accounts awaiting approval.' : 'No accounts in this view.'}
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table className="f-table">
                <thead>
                  <tr><th>Account</th><th>Interest</th><th>Role</th><th className="num">Manage</th></tr>
                </thead>
                <tbody>
                  {rows.map((u: any) => (
                    <tr key={u.id}>
                      <td style={{ color: 'var(--ivory)' }}>
                        {u.onboarding?.fullName && (
                          <div style={{ fontWeight: 600, marginBottom: 2 }}>{u.onboarding.fullName}</div>
                        )}
                        <div className="f-mono" style={{ fontSize: 11, color: 'var(--ivory-dim)' }}>{u.email}</div>
                        {u.onboarding?.note && (
                          <div className="f-mono f-faint" style={{ fontSize: 9.5, marginTop: 3, whiteSpace: 'normal', maxWidth: 340 }}>
                            &ldquo;{u.onboarding.note}&rdquo;
                          </div>
                        )}
                      </td>
                      <td>
                        {u.onboarding ? (
                          <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                            <span className="f-tag azure">{pretty(u.onboarding.levelInterest)}</span>
                            <span className="f-tag dim">{pretty(u.onboarding.capitalBand)}</span>
                            <span className="f-tag dim">{pretty(u.onboarding.experience)}</span>
                          </div>
                        ) : <span className="f-kicker">NO FORM</span>}
                      </td>
                      <td><span className={`f-tag ${roleTag(u.role)}`}>{u.role.toUpperCase()}</span></td>
                      <td className="num">
                        {u.role === 'owner' ? (
                          <span className="f-kicker">ENV-MANAGED</span>
                        ) : (
                          <div style={{ display: 'inline-flex', gap: 6 }}>
                            {u.role !== 'viewer' && (
                              <button className="f-btn long" style={{ padding: '3px 10px', fontSize: 9 }}
                                disabled={acting === u.id} onClick={() => act(u.id, 'approve')}>
                                {acting === u.id ? '…' : 'APPROVE'}
                              </button>
                            )}
                            {u.role === 'viewer' && (
                              <button className="f-btn" style={{ padding: '3px 10px', fontSize: 9 }}
                                disabled={acting === u.id} onClick={() => act(u.id, 'revoke')}>REVOKE</button>
                            )}
                            {u.role !== 'blocked' && (
                              <button className="f-btn danger" style={{ padding: '3px 10px', fontSize: 9 }}
                                disabled={acting === u.id} onClick={() => act(u.id, 'block')}>BLOCK</button>
                            )}
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 14, marginTop: 14 }}>
            <button className="f-btn" style={{ padding: '6px 16px', fontSize: 10 }}
              disabled={page <= 1 || loading} onClick={() => setPage(p => Math.max(1, p - 1))}>← PREV</button>
            <span className="f-mono f-faint" style={{ fontSize: 11, letterSpacing: '0.1em' }}>PAGE {page}</span>
            <button className="f-btn" style={{ padding: '6px 16px', fontSize: 10 }}
              disabled={!data?.hasNext || loading} onClick={() => setPage(p => p + 1)}>NEXT →</button>
          </div>
        </div>

        <div className="f-mono f-faint" style={{ fontSize: 9, margin: '12px 2px 28px', letterSpacing: '0.05em' }}>
          Approving grants read-only access to the desk. Owners are managed through OWNER_EMAILS, not this panel. 50 accounts per page; one bounded query per action, no background polling.
        </div>
      </div>
    </div>
  );
}
