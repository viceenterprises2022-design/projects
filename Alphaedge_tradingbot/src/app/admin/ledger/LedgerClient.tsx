'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';

// Owner-only full ledger. NO polling — one bounded fetch per user action
// (filter change, page change, manual refresh). CSV export is one query.

const TIERS: Array<{ key: string; label: string }> = [
  { key: 'all', label: 'ALL TIERS' },
  { key: '4', label: 'DEMO' },
  { key: '1', label: 'LEVEL 1' },
  { key: '2', label: 'LEVEL 2' },
  { key: '3', label: 'LEVEL 3' },
];

const fmtUsd = (n: number) => `$${Math.abs(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const fmtSigned = (n: number) => `${n >= 0 ? '+' : '−'}${fmtUsd(n)}`;
const tierName = (l: number) => (l === 4 ? 'DEMO' : `L${l}`);

export default function LedgerClient() {
  const [level, setLevel] = useState('all');
  const [page, setPage] = useState(1);
  const [rows, setRows] = useState<any[]>([]);
  const [hasNext, setHasNext] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loadedAt, setLoadedAt] = useState<Date | null>(null);

  const load = useCallback(async (lvl: string, pg: number) => {
    setLoading(true); setError(null);
    try {
      const res = await fetch(`/api/admin/ledger?level=${lvl}&page=${pg}`);
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Failed to load ledger');
      setRows(json.rows); setHasNext(json.hasNext); setLoadedAt(new Date());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(level, page); }, [level, page, load]);

  const pickTier = (key: string) => { setLevel(key); setPage(1); };

  return (
    <div className="fable">
      <div className="f-shell">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, margin: '18px 0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <span className="f-brand-mark" style={{ width: 40, height: 40, fontSize: 17, borderRadius: 13 }}>P</span>
            <div>
              <div className="f-serif-grad" style={{ fontSize: 22 }}>Ledger Explorer</div>
              <div className="f-kicker">ADMIN · FULL HISTORICAL PREDICTIONS LOG · 100 / PAGE</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            <Link href="/admin/analytics" className="f-btn" style={{ padding: '7px 14px', fontSize: 10, textDecoration: 'none' }}>STRATEGY ANALYTICS</Link>
            <Link href="/dashboard" className="f-btn" style={{ padding: '7px 14px', fontSize: 10, textDecoration: 'none' }}>← COCKPIT</Link>
          </div>
        </div>

        <div className="f-panel">
          <div className="f-panel-head" style={{ flexWrap: 'wrap', gap: 10 }}>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {TIERS.map(t => (
                <button key={t.key} className="f-btn" onClick={() => pickTier(t.key)}
                  style={{
                    padding: '5px 13px', fontSize: 9.5,
                    ...(level === t.key ? { borderColor: 'rgba(88,240,255,0.55)', color: '#58f0ff', background: 'rgba(88,240,255,0.08)' } : {}),
                  }}>
                  {t.label}
                </button>
              ))}
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              {loadedAt && <span className="f-kicker">LOADED {loadedAt.toLocaleTimeString(undefined, { hour12: false })}</span>}
              <button className="f-btn" style={{ padding: '5px 13px', fontSize: 9.5 }} onClick={() => load(level, page)} disabled={loading}>
                {loading ? 'LOADING…' : 'REFRESH'}
              </button>
              <a className="f-btn long" style={{ padding: '5px 13px', fontSize: 9.5, textDecoration: 'none' }}
                href={`/api/admin/ledger?format=csv&level=${level}`}>
                ⬇ CSV ({level === 'all' ? 'ALL' : TIERS.find(t => t.key === level)?.label})
              </a>
            </div>
          </div>

          {error ? (
            <div className="f-empty" style={{ color: 'var(--oxide)' }}>{error}</div>
          ) : rows.length === 0 && !loading ? (
            <div className="f-empty">No settled trades on this page — the fresh book fills as rounds settle.</div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table className="f-table">
                <thead>
                  <tr>
                    <th>Tier</th><th>Round</th><th>Settled (UTC)</th><th>Asset</th><th>Side</th>
                    <th className="num">Strike</th><th className="num">Expiry</th><th className="num">Size</th>
                    <th className="num">Entry</th><th className="num">Exit</th><th>Outcome</th><th className="num">P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r: any) => (
                    <tr key={r.id}>
                      <td><span className={`f-tag ${r.level === 4 ? 'azure' : 'dim'}`}>{tierName(r.level)}</span></td>
                      <td className="f-mono">#{r.roundId}</td>
                      <td className="f-mono" style={{ whiteSpace: 'nowrap' }}>{new Date(r.createdAt).toISOString().replace('T', ' ').slice(0, 19)}</td>
                      <td>{r.asset}</td>
                      <td><span className={`f-tag ${r.side === 'BUY' ? 'win' : 'loss'}`}>{r.side}</span></td>
                      <td className="num f-mono">{fmtUsd(r.strikePrice)}</td>
                      <td className="num f-mono">{fmtUsd(r.expiryPrice)}</td>
                      <td className="num f-mono">{r.size?.toLocaleString()}</td>
                      <td className="num f-mono">{Math.round((r.entryPrice || 0) * 100)}¢</td>
                      <td className="num f-mono">{Math.round((r.exitPrice || 0) * 100)}¢</td>
                      <td><span className={`f-tag ${r.outcome === 'WIN' ? 'win' : 'loss'}`}>{r.outcome}</span></td>
                      <td className={`num f-mono ${r.pnl >= 0 ? 'f-pos' : 'f-neg'}`} style={{ fontWeight: 700 }}>{fmtSigned(r.pnl)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 14, marginTop: 14 }}>
            <button className="f-btn" style={{ padding: '6px 16px', fontSize: 10 }}
              disabled={page <= 1 || loading} onClick={() => setPage(p => Math.max(1, p - 1))}>
              ← PREV
            </button>
            <span className="f-mono f-faint" style={{ fontSize: 11, letterSpacing: '0.1em' }}>PAGE {page}</span>
            <button className="f-btn" style={{ padding: '6px 16px', fontSize: 10 }}
              disabled={!hasNext || loading} onClick={() => setPage(p => p + 1)}>
              NEXT →
            </button>
          </div>
        </div>

        <div className="f-mono f-faint" style={{ fontSize: 9, margin: '12px 2px', letterSpacing: '0.05em' }}>
          Read discipline: one bounded query per action — no background polling on this page. CSV exports the full current demo window for the selected tier.
        </div>
      </div>
    </div>
  );
}
