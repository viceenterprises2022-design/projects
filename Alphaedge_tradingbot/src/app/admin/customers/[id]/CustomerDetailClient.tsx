'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import ThemeToggle from '../../../ThemeToggle';
import StatCard from '../../StatCard';
import { WalletHistory, FeeLedger } from '../HistoryTables';
import { fmtUsd, fmtUsdC, fmtSigned, fmtSignedC, pct, int, fmtPf, pfOk, fmtTime } from '@/lib/format';

// Owner view of one customer: live balance and profit, fees owed and paid,
// withdrawal history, fee ledger, and trade analytics computed from this
// customer's own wallet. Opening the page triggers one read-only sync.

export default function CustomerDetailClient({ id }: { id: string }) {
  const [d, setD] = useState<any>(null);
  const [a, setA] = useState<any>(null);
  const [aErr, setAErr] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [newPct, setNewPct] = useState('');
  const [fee, setFee] = useState({ kind: 'manual_payment', amount: '', note: '' });

  const load = useCallback(async () => {
    const res = await fetch(`/api/admin/customers/${id}`);
    const j = await res.json();
    if (!res.ok) throw new Error(j.error || 'Failed to load customer');
    setD(j); setNewPct(String(j.customer.profitSharePct));
  }, [id]);

  const loadAnalytics = useCallback(async () => {
    setAErr(null);
    try {
      const res = await fetch(`/api/admin/customers/${id}/analytics`);
      const j = await res.json();
      if (!res.ok) throw new Error(j.error || 'Analytics unavailable');
      setA(j);
    } catch (e: any) { setAErr(e.message); }
  }, [id]);

  const sync = useCallback(async () => {
    setBusy('sync'); setError(null);
    try {
      const res = await fetch(`/api/admin/customers/${id}/sync`, { method: 'POST' });
      const j = await res.json();
      if (!res.ok) setError(j.error || 'Sync failed');
      await load();
    } catch (e: any) { setError(e.message); } finally { setBusy(null); }
  }, [id, load]);

  useEffect(() => { load().catch(e => setError(e.message)).then(sync); loadAnalytics(); }, [load, sync, loadAnalytics]);

  const patch = async (body: Record<string, unknown>, confirmMsg?: string) => {
    if (confirmMsg && !window.confirm(confirmMsg)) return;
    setBusy('patch'); setError(null);
    try {
      const res = await fetch(`/api/admin/customers/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      const j = await res.json();
      if (!res.ok) throw new Error(j.error || 'Update failed');
      await load();
    } catch (e: any) { setError(e.message); } finally { setBusy(null); }
  };

  const recordFee = async (e: React.FormEvent) => {
    e.preventDefault();
    const amt = Number(fee.amount);
    const verb = fee.kind === 'waiver' ? 'Waive' : 'Record a manual payment of';
    if (!window.confirm(`${verb} ${fmtUsd(amt)} for ${d.customer.name}? This is written to the fee ledger and cannot be edited.`)) return;
    setBusy('fee'); setError(null);
    try {
      const res = await fetch(`/api/admin/customers/${id}/fees`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(fee) });
      const j = await res.json();
      if (!res.ok) throw new Error(j.error || 'Could not record');
      setD(j); setFee({ kind: 'manual_payment', amount: '', note: '' });
    } catch (e: any) { setError(e.message); } finally { setBusy(null); }
  };

  const withdrawals = useMemo(() => (d?.flows || []), [d]);

  if (!d) return (
    <div className="fable"><div className="f-shell"><div className="f-panel" style={{ marginTop: 18 }}>
      <div className="f-empty" style={{ color: error ? 'var(--oxide)' : undefined }}>{error || 'Loading…'}</div>
    </div></div></div>
  );

  const c = d.customer, s = d.summary, t = d.totals;
  const v = a?.view, st = v?.stats;

  return (
    <div className="fable">
      <div className="f-shell">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, margin: '18px 0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, minWidth: 0 }}>
            <span className="f-brand-mark" style={{ width: 40, height: 40, fontSize: 17, borderRadius: 13 }}>{c.name.slice(0, 1).toUpperCase()}</span>
            <div style={{ minWidth: 0 }}>
              <div className="f-serif-grad" style={{ fontSize: 22 }}>{c.name}</div>
              <div className="f-kicker" style={{ overflowWrap: 'anywhere' }}>{c.email} · {c.walletAddress} · {c.profitSharePct}% PROFIT SHARE · {c.status.toUpperCase()}</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            {s.lastSyncedAt && <span className="f-kicker">SYNCED {fmtTime(s.lastSyncedAt).slice(11)}</span>}
            <button className="f-btn" style={{ padding: '7px 14px', fontSize: 10 }} onClick={sync} disabled={!!busy}>{busy === 'sync' ? 'SYNCING…' : 'SYNC'}</button>
            <ThemeToggle compact />
            <Link href="/admin/customers" className="f-btn" style={{ padding: '7px 14px', fontSize: 10, textDecoration: 'none' }}>← CUSTOMERS</Link>
          </div>
        </div>

        {error && <div className="f-panel" style={{ marginBottom: 14 }}><div className="f-empty" style={{ color: 'var(--oxide)' }}>{error}</div></div>}
        {s.lastError && <div className="f-panel" style={{ marginBottom: 14 }}><div className="f-empty" style={{ color: 'var(--oxide)' }}>Last sync error: {s.lastError}</div></div>}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10, marginBottom: 14 }}>
          <StatCard label="Wallet balance" value={fmtUsdC(s.balance)} title={fmtUsd(s.balance)} sub="perp account value + spot USDC" />
          <StatCard label="Capital" value={fmtUsdC(s.capitalBasis)} title={fmtUsd(s.capitalBasis)} sub={`started at ${fmtUsdC(c.initialCapital)}`} />
          <StatCard label="Current profit" value={fmtSignedC(s.profit)} title={fmtSigned(s.profit)} tone={s.profit >= 0 ? 'pos' : 'neg'} sub="balance − capital − fee owed" />
          <StatCard label="Fee if withdrawn now" value={fmtUsdC(s.feeIfWithdrawnNow)} title={fmtUsd(s.feeIfWithdrawnNow)} tone="pos" sub={`${c.profitSharePct}% of current profit`} />
          <StatCard label="Fee owed" value={fmtUsdC(s.outstandingFee)} title={fmtUsd(s.outstandingFee)} tone={s.outstandingFee > 0 ? 'gold' : undefined} sub="charged, not yet paid" />
          <StatCard label="Fees collected" value={fmtUsdC(t.feesPaid)} title={`${fmtUsd(t.feesPaidOnVenue)} on-chain · ${fmtUsd(t.feesPaidManual)} manual`}
            tone="pos" sub={`of ${fmtUsdC(t.feesCrystallised)} charged · ${fmtUsdC(t.feesWaived)} waived`} />
          <StatCard label="Deposited / withdrawn" value={`${fmtUsdC(t.deposited)} / ${fmtUsdC(t.withdrawn)}`} title={`${fmtUsd(t.deposited)} / ${fmtUsd(t.withdrawn)}`} sub="since onboarding" />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 14, marginBottom: 14 }}>
          <div className="f-panel" style={{ padding: 16 }}>
            <div className="f-kicker" style={{ marginBottom: 10 }}>PROFIT SHARE</div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <input className="f-input" type="number" min={0} max={100} step="0.01" value={newPct} onChange={e => setNewPct(e.target.value)} style={{ width: 110 }} />
              <span className="f-mono f-faint">%</span>
              <button className="f-btn" style={{ padding: '7px 14px', fontSize: 10 }} disabled={!!busy || Number(newPct) === c.profitSharePct}
                onClick={() => patch({ profitSharePct: newPct }, `Change ${c.name}'s profit share from ${c.profitSharePct}% to ${newPct}%? It applies to withdrawals from now on; past fees are unchanged.`)}>
                SAVE
              </button>
            </div>
            <div className="f-mono f-faint" style={{ fontSize: 9.5, marginTop: 8 }}>
              History: {d.rates.map((r: any) => `${r.pct}% from ${fmtTime(r.effectiveAt).slice(0, 10)}`).join(' · ')}
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 14, flexWrap: 'wrap' }}>
              {['active', 'paused', 'closed'].filter(x => x !== c.status).map(x => (
                <button key={x} className="f-btn" style={{ padding: '6px 12px', fontSize: 9.5 }} disabled={!!busy}
                  onClick={() => patch({ status: x }, `Set ${c.name} to ${x.toUpperCase()}?${x === 'closed' ? ' Closed accounts are no longer synced.' : ''}`)}>
                  MARK {x.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <form className="f-panel" style={{ padding: 16 }} onSubmit={recordFee}>
            <div className="f-kicker" style={{ marginBottom: 10 }}>SETTLE FEE · {fmtUsd(s.outstandingFee)} OWED</div>
            <div className="f-mono f-faint" style={{ fontSize: 10, marginBottom: 10 }}>
              {d.feeAddress
                ? <>Payments sent on Hyperliquid to <span style={{ color: 'var(--ivory)' }}>{d.feeAddress}</span> are matched automatically. Use this form only for fees paid off-chain (bank, UPI) or to waive.</>
                : <>Fee wallet not configured: on-chain payments cannot be matched yet. Record payments here.</>}
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
              <select className="f-input" value={fee.kind} onChange={e => setFee({ ...fee, kind: e.target.value })} style={{ width: 170 }}>
                <option value="manual_payment">Paid off-chain</option>
                <option value="waiver">Waive</option>
              </select>
              <input className="f-input" type="number" min={0.01} step="0.01" placeholder="Amount" value={fee.amount} required
                onChange={e => setFee({ ...fee, amount: e.target.value })} style={{ width: 120 }} />
              <input className="f-input" placeholder="Reference / reason" value={fee.note} onChange={e => setFee({ ...fee, note: e.target.value })} style={{ flex: 1, minWidth: 140 }} />
              <button className="f-btn" type="submit" style={{ padding: '7px 14px', fontSize: 10 }} disabled={!!busy || s.outstandingFee <= 0}>RECORD</button>
            </div>
          </form>
        </div>

        <div className="f-panel" style={{ marginBottom: 14 }}>
          <div className="f-panel-head"><h2 className="f-panel-title"><span className="f-serif-grad">Withdrawal &amp; deposit history</span></h2></div>
          <WalletHistory flows={withdrawals} showRaw />
        </div>

        <div className="f-panel" style={{ marginBottom: 14 }}>
          <div className="f-panel-head"><h2 className="f-panel-title"><span className="f-serif-grad">Fee ledger</span>
            <span className="f-kicker" style={{ marginLeft: 6 }}>APPEND-ONLY · EVERY FIGURE RE-DERIVABLE</span></h2></div>
          <FeeLedger fees={d.fees} />
        </div>

        <div className="f-panel" style={{ marginBottom: 14 }}>
          <div className="f-panel-head" style={{ justifyContent: 'space-between' }}>
            <h2 className="f-panel-title"><span className="f-serif-grad">Wallet analytics</span>
              <span className="f-kicker" style={{ marginLeft: 6 }}>THIS WALLET ONLY · CLOSED TRADES SINCE ONBOARDING</span></h2>
            <button className="f-btn" style={{ padding: '5px 12px', fontSize: 9.5 }} onClick={loadAnalytics}>REFRESH</button>
          </div>
          {aErr ? <div className="f-empty" style={{ color: 'var(--oxide)' }}>{aErr}</div>
            : !a ? <div className="f-empty">Loading fills…</div>
            : !st || st.n === 0 ? <div className="f-empty">No closed trades on this wallet since onboarding.</div>
            : <>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 10, padding: 14 }}>
                <StatCard label="Realised P&L" value={fmtSignedC(st.net)} title={fmtSigned(st.net)} tone={st.net >= 0 ? 'pos' : 'neg'} sub={`${int(st.n)} closed · ${fmtUsdC(st.volume)} volume`} />
                <StatCard label="Hit rate" value={pct(st.hit)} tone="azure" sub={`${int(st.wins)} W / ${int(st.losses)} L`} />
                <StatCard label="Profit factor" value={fmtPf(st.pf)} tone={pfOk(st.pf) ? 'pos' : 'neg'} sub={`${fmtUsdC(st.grossWin)} won / ${fmtUsdC(st.grossLoss)} lost`} />
                <StatCard label="Expectancy" value={fmtSignedC(st.expectancy)} tone={st.expectancy >= 0 ? 'pos' : 'neg'} sub="per closed trade" />
                <StatCard label="Avg win / loss" value={`${fmtUsdC(st.avgWin)} / ${fmtUsdC(st.avgLoss)}`} sub={`payoff ${st.avgLoss > 0 ? (st.avgWin / st.avgLoss).toFixed(2) : '—'}`} />
                <StatCard label="Max drawdown" value={fmtUsdC(st.maxDD)} tone="neg" sub={s.capitalBasis > 0 ? `${((st.maxDD / c.initialCapital) * 100).toFixed(2)}% of starting capital` : undefined} />
              </div>
              <EquityLine curve={v.curve} />
              <div style={{ overflowX: 'auto' }}>
                <table className="f-table">
                  <thead><tr><th>Asset</th><th className="num">Trades</th><th className="num">Hit</th><th className="num">PF</th><th className="num">Net P&amp;L</th></tr></thead>
                  <tbody>{v.byAsset.map((r: any) => (
                    <tr key={r.key}><td>{r.key}</td><td className="num f-mono">{int(r.n)}</td><td className="num f-mono">{pct(r.hit)}</td>
                      <td className="num f-mono">{fmtPf(r.pf)}</td>
                      <td className={`num f-mono ${r.net >= 0 ? 'f-pos' : 'f-neg'}`} title={fmtSigned(r.net)}>{fmtSignedC(r.net)}</td></tr>
                  ))}</tbody>
                </table>
              </div>
              <div className="f-mono f-faint" style={{ fontSize: 9, margin: '8px 14px 12px' }}>
                From Hyperliquid fills on this wallet ({int(a.totalFills)} fills, {int(a.settledTrades)} closing). P&amp;L is net of trading fees; funding is excluded. Hyperliquid retains the most recent 10,000 fills.
              </div>
            </>}
        </div>
      </div>
    </div>
  );
}

function EquityLine({ curve }: { curve: Array<{ i: number; eq: number }> }) {
  const pts = [{ i: 0, eq: 0 }, ...curve];
  if (pts.length < 2) return null;
  const W = 1000, H = 160;
  const min = Math.min(0, ...pts.map(p => p.eq)), max = Math.max(0, ...pts.map(p => p.eq));
  const span = Math.max(1e-9, max - min), n = pts[pts.length - 1].i || 1;
  const X = (i: number) => (i / n) * W, Y = (v: number) => H - 8 - ((v - min) / span) * (H - 16);
  const d = pts.map((p, k) => `${k ? 'L' : 'M'}${X(p.i).toFixed(1)},${Y(p.eq).toFixed(1)}`).join(' ');
  const end = pts[pts.length - 1].eq;
  return (
    <div style={{ padding: '0 14px 10px' }}>
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ width: '100%', height: 150, display: 'block' }}>
        <line x1={0} x2={W} y1={Y(0)} y2={Y(0)} stroke="rgba(255,255,255,0.12)" strokeDasharray="4 4" vectorEffect="non-scaling-stroke" />
        <path d={d} fill="none" stroke={end >= 0 ? '#58f0ff' : '#f6465d'} strokeWidth={1.6} vectorEffect="non-scaling-stroke" />
      </svg>
      <div className="f-mono f-faint" style={{ fontSize: 9, display: 'flex', justifyContent: 'space-between' }}>
        <span>cumulative realised P&amp;L</span><span>{fmtSignedC(min)} → {fmtSignedC(max)}</span>
      </div>
    </div>
  );
}
