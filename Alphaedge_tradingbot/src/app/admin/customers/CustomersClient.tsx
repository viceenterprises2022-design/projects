'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import ThemeToggle from '../../ThemeToggle';
import StatCard from '../StatCard';
import { fmtUsd, fmtUsdC, fmtSignedC, fmtSigned, shortAddr, fmtTime } from '@/lib/format';

// Owner-only customer book. One fetch on load; "SYNC ALL" pulls every wallet
// from Hyperliquid (read-only) and recomputes fees owed.

type Row = {
  id: string; name: string; email: string; walletAddress: string; profitSharePct: number; status: string;
  balance: number; capitalBasis: number; profit: number; outstandingFee: number; feeIfWithdrawnNow: number;
  lastSyncedAt: number | null; lastError: string | null;
};

const empty = { name: '', email: '', walletAddress: '', profitSharePct: '', initialCapital: '', notes: '' };

export default function CustomersClient() {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [meta, setMeta] = useState<{ feeAddress: string | null; network: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [form, setForm] = useState(empty);
  const [showForm, setShowForm] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const res = await fetch('/api/admin/customers');
      const j = await res.json();
      if (!res.ok) throw new Error(j.error || 'Failed to load customers');
      setRows(j.customers); setMeta({ feeAddress: j.feeAddress, network: j.network });
    } catch (e: any) { setError(e.message); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const syncAll = async () => {
    setBusy('sync');
    try {
      const res = await fetch('/api/cron/wallet-sync');
      const j = await res.json();
      if (!res.ok) throw new Error(j.error || 'Sync failed');
      if (j.errors) setError(`${j.errors} wallet(s) failed to sync; see the row for details`);
      await load();
    } catch (e: any) { setError(e.message); } finally { setBusy(null); }
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy('create'); setFormError(null);
    try {
      const res = await fetch('/api/admin/customers', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form),
      });
      const j = await res.json();
      if (!res.ok) throw new Error(j.error || 'Could not onboard customer');
      setForm(empty); setShowForm(false); await load();
    } catch (e: any) { setFormError(e.message); } finally { setBusy(null); }
  };

  const tot = (rows || []).reduce((a, r) => ({
    balance: a.balance + r.balance, owed: a.owed + r.outstandingFee, accruing: a.accruing + r.feeIfWithdrawnNow,
  }), { balance: 0, owed: 0, accruing: 0 });

  const input = (k: keyof typeof empty, label: string, ph: string, extra: Record<string, any> = {}) => (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 5, minWidth: 0 }}>
      <span className="f-kicker">{label}</span>
      <input className="f-input" value={form[k]} placeholder={ph} onChange={e => setForm({ ...form, [k]: e.target.value })} {...extra} />
    </label>
  );

  return (
    <div className="fable">
      <div className="f-shell">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, margin: '18px 0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <span className="f-brand-mark" style={{ width: 40, height: 40, fontSize: 17, borderRadius: 13 }}>P</span>
            <div>
              <div className="f-serif-grad" style={{ fontSize: 22 }}>Customers</div>
              <div className="f-kicker">PROFIT SHARE · READ-ONLY WALLETS · {meta?.network?.toUpperCase() || ''}</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            <button className="f-btn" style={{ padding: '7px 14px', fontSize: 10 }} onClick={() => setShowForm(v => !v)}>
              {showForm ? 'CANCEL' : '+ ONBOARD CUSTOMER'}
            </button>
            <button className="f-btn" style={{ padding: '7px 14px', fontSize: 10 }} onClick={syncAll} disabled={!!busy}>
              {busy === 'sync' ? 'SYNCING…' : 'SYNC ALL'}
            </button>
            <Link href="/admin/analytics" className="f-btn" style={{ padding: '7px 14px', fontSize: 10, textDecoration: 'none' }}>ANALYTICS</Link>
            <ThemeToggle compact />
            <Link href="/demo" className="f-btn" style={{ padding: '7px 14px', fontSize: 10, textDecoration: 'none' }}>← COCKPIT</Link>
          </div>
        </div>

        {meta && !meta.feeAddress && (
          <div className="f-panel" style={{ marginBottom: 14, borderColor: 'rgba(232,194,106,0.5)' }}>
            <div className="f-empty" style={{ color: '#e8c26a', textAlign: 'left' }}>
              ALPHAEDGE_FEE_ADDRESS is not set. Fees are still calculated, but payments customers send on Hyperliquid
              cannot be matched automatically until the AlphaEdge fee wallet address is configured in Vercel.
            </div>
          </div>
        )}
        {error && <div className="f-panel" style={{ marginBottom: 14 }}><div className="f-empty" style={{ color: 'var(--oxide)' }}>{error}</div></div>}

        {showForm && (
          <form className="f-panel" style={{ marginBottom: 14, padding: 16 }} onSubmit={submit}>
            <div className="f-panel-head" style={{ padding: 0, marginBottom: 12 }}>
              <h2 className="f-panel-title"><span className="f-serif-grad">Onboard customer</span></h2>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
              {input('name', 'Name', 'Full name', { required: true })}
              {input('email', 'Login email', 'customer@email.com', { required: true, type: 'email' })}
              {input('walletAddress', 'Hyperliquid wallet', '0x…', { required: true, spellCheck: false })}
              {input('profitSharePct', 'Profit share %', 'e.g. 10', { required: true, type: 'number', min: 0, max: 100, step: '0.01' })}
              {input('initialCapital', 'Starting capital (USDC)', 'Blank = current wallet balance', { type: 'number', min: 0, step: '0.01' })}
              {input('notes', 'Notes', 'Optional')}
            </div>
            <div className="f-mono f-faint" style={{ fontSize: 10, margin: '12px 0' }}>
              AlphaEdge earns profit share % of (balance − capital) on each withdrawal. Example: capital 1,000, balance 1,500, 10% → 50 owed.
              Only gains after onboarding count; the wallet is read, never debited.
            </div>
            {formError && <div className="f-mono" style={{ color: 'var(--oxide)', fontSize: 11, marginBottom: 10 }}>{formError}</div>}
            <button className="f-btn" type="submit" disabled={busy === 'create'} style={{ padding: '8px 16px', fontSize: 10 }}>
              {busy === 'create' ? 'ONBOARDING…' : 'ONBOARD'}
            </button>
          </form>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10, marginBottom: 14 }}>
          <StatCard label="Customers" value={String(rows?.length ?? '—')} sub={`${(rows || []).filter(r => r.status === 'active').length} active`} />
          <StatCard label="Assets monitored" value={fmtUsdC(tot.balance)} title={fmtUsd(tot.balance)} sub="sum of wallet balances" />
          <StatCard label="Fees owed" value={fmtUsdC(tot.owed)} title={fmtUsd(tot.owed)} tone={tot.owed > 0 ? 'gold' : undefined} sub="crystallised, unpaid" />
          <StatCard label="Accruing" value={fmtUsdC(tot.accruing)} title={fmtUsd(tot.accruing)} tone="pos" sub="due if all withdrew now" />
        </div>

        <div className="f-panel">
          {!rows ? <div className="f-empty">Loading…</div> : rows.length === 0 ? (
            <div className="f-empty">No customers yet. Use ONBOARD CUSTOMER to add the first wallet.</div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table className="f-table">
                <thead><tr>
                  <th>Customer</th><th>Wallet</th><th className="num">Share</th><th className="num">Balance</th>
                  <th className="num">Capital</th><th className="num">Profit</th><th className="num">Fee owed</th>
                  <th className="num">If withdrawn now</th><th>Synced</th>
                </tr></thead>
                <tbody>
                  {rows.map(r => (
                    <tr key={r.id}>
                      <td>
                        <Link href={`/admin/customers/${r.id}`} style={{ color: 'var(--ivory)', textDecoration: 'none', fontWeight: 600 }}>{r.name}</Link>
                        <div className="f-mono f-faint" style={{ fontSize: 10 }}>{r.email}{r.status !== 'active' && <span className="f-tag dim" style={{ marginLeft: 6, fontSize: 8 }}>{r.status.toUpperCase()}</span>}</div>
                      </td>
                      <td className="f-mono" title={r.walletAddress}>{shortAddr(r.walletAddress)}</td>
                      <td className="num f-mono">{r.profitSharePct}%</td>
                      <td className="num f-mono" title={fmtUsd(r.balance)}>{fmtUsdC(r.balance)}</td>
                      <td className="num f-mono" title={fmtUsd(r.capitalBasis)}>{fmtUsdC(r.capitalBasis)}</td>
                      <td className={`num f-mono ${r.profit >= 0 ? 'f-pos' : 'f-neg'}`} title={fmtSigned(r.profit)}>{fmtSignedC(r.profit)}</td>
                      <td className="num f-mono" style={{ color: r.outstandingFee > 0 ? '#e8c26a' : undefined, fontWeight: r.outstandingFee > 0 ? 700 : 400 }}
                        title={fmtUsd(r.outstandingFee)}>{fmtUsdC(r.outstandingFee)}</td>
                      <td className="num f-mono" title={fmtUsd(r.feeIfWithdrawnNow)}>{fmtUsdC(r.feeIfWithdrawnNow)}</td>
                      <td className="f-mono f-faint" style={{ fontSize: 10 }}>
                        {r.lastError ? <span style={{ color: 'var(--oxide)' }} title={r.lastError}>ERROR</span>
                          : r.lastSyncedAt ? fmtTime(r.lastSyncedAt).slice(5) : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
