'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import ThemeToggle from '../ThemeToggle';
import { CHANGELOG, TAG_STYLE, type ChangeEntry } from './changelog-data';

// Viewers see published entries only. The owner sees everything, with drafts
// marked and one-click publish / un-publish. No polling — publication state
// arrives with the page and is updated optimistically on action.

export default function ChangelogClient({ isOwner, publishedIds }: { isOwner: boolean; publishedIds: string[] }) {
  const [published, setPublished] = useState<Set<string>>(new Set(publishedIds));
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const visible = useMemo(
    () => (isOwner ? CHANGELOG : CHANGELOG.filter(e => published.has(e.id))),
    [isOwner, published]
  );

  const days = useMemo(() => {
    const out: Array<{ date: string; entries: ChangeEntry[] }> = [];
    for (const entry of visible) {
      const last = out[out.length - 1];
      if (last && last.date === entry.date) last.entries.push(entry);
      else out.push({ date: entry.date, entries: [entry] });
    }
    return out;
  }, [visible]);

  const draftCount = CHANGELOG.filter(e => !published.has(e.id)).length;

  const setPublishState = async (entryIds: string[], publish: boolean, key: string) => {
    setBusy(key); setError(null);
    try {
      const res = await fetch('/api/admin/changelog', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entryIds, publish }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Update failed');
      setPublished(prev => {
        const next = new Set(prev);
        for (const id of entryIds) publish ? next.add(id) : next.delete(id);
        return next;
      });
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  };

  const fmtDate = (iso: string) =>
    new Date(iso + 'T00:00:00Z').toLocaleDateString('en-GB', {
      day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC',
    });

  return (
    <div className="fable">
      <div className="f-shell">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, margin: '18px 0 8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <span className="f-brand-mark" style={{ width: 40, height: 40, fontSize: 17, borderRadius: 13 }}>P</span>
            <div>
              <div className="f-serif-grad" style={{ fontSize: 22 }}>What&rsquo;s Changed</div>
              <div className="f-kicker">PRODUCT CHANGELOG · NEWEST FIRST</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            {isOwner && draftCount > 0 && (
              <>
                <span className="f-tag gold">{draftCount} DRAFT{draftCount === 1 ? '' : 'S'}</span>
                <button className="f-btn long" style={{ padding: '7px 14px', fontSize: 10 }}
                  disabled={busy !== null}
                  onClick={() => setPublishState(CHANGELOG.filter(e => !published.has(e.id)).map(e => e.id), true, 'all')}>
                  {busy === 'all' ? 'PUBLISHING…' : `PUBLISH ALL (${draftCount})`}
                </button>
              </>
            )}
            <ThemeToggle compact />
            <Link href="/demo" className="f-btn" style={{ padding: '7px 14px', fontSize: 10, textDecoration: 'none' }}>← COCKPIT</Link>
          </div>
        </div>

        <p style={{ margin: '0 0 8px', fontSize: 13, lineHeight: 1.75, color: 'var(--ivory-dim)' }}>
          Every change to how the desk trades and what you see — including what we tested and rejected. Results from different days may reflect different settings.
        </p>
        {isOwner && (
          <p className="f-mono f-faint" style={{ margin: '0 0 18px', fontSize: 9.5, letterSpacing: '0.05em' }}>
            OWNER VIEW · drafts are hidden from viewers until published. Un-publishing removes an entry from their view immediately.
          </p>
        )}
        {error && <div className="f-panel" style={{ marginBottom: 14 }}><div className="f-empty" style={{ color: 'var(--oxide)' }}>{error}</div></div>}

        {days.length === 0 ? (
          <div className="f-panel"><div className="f-empty">No updates published yet.</div></div>
        ) : days.map(day => (
          <div key={day.date} style={{ marginBottom: 26 }}>
            <div className="f-kicker" style={{ marginBottom: 10, color: 'var(--azure)' }}>{fmtDate(day.date)}</div>
            <div style={{ display: 'grid', gap: 10 }}>
              {day.entries.map(entry => {
                const isPublished = published.has(entry.id);
                return (
                  <div className="f-panel" key={entry.id}
                    style={{ padding: '15px 18px', ...(isOwner && !isPublished ? { borderStyle: 'dashed', opacity: 0.82 } : {}) }}>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap', marginBottom: 6 }}>
                      <span className={`f-tag ${TAG_STYLE[entry.tag]}`}>{entry.tag.toUpperCase()}</span>
                      <span style={{ fontSize: 14.5, fontWeight: 600, color: 'var(--ivory)' }}>{entry.title}</span>
                      {isOwner && !isPublished && <span className="f-tag gold">DRAFT</span>}
                      {isOwner && (
                        <button className={`f-btn ${isPublished ? '' : 'long'}`}
                          style={{ padding: '3px 10px', fontSize: 9, marginLeft: 'auto' }}
                          disabled={busy !== null}
                          onClick={() => setPublishState([entry.id], !isPublished, entry.id)}>
                          {busy === entry.id ? '…' : isPublished ? 'UNPUBLISH' : 'PUBLISH'}
                        </button>
                      )}
                    </div>
                    <p style={{ margin: 0, fontSize: 13, lineHeight: 1.75, color: 'var(--ivory-dim)' }}>{entry.body}</p>
                  </div>
                );
              })}
            </div>
          </div>
        ))}

        <p className="f-mono f-faint" style={{ fontSize: 9, margin: '4px 2px 28px', letterSpacing: '0.05em', lineHeight: 1.7 }}>
          Thresholds described here are limits at which trading pauses, not projected or promised returns. Demo
          results are produced with practice capital against live market prices and do not indicate future performance.
        </p>
      </div>
    </div>
  );
}
