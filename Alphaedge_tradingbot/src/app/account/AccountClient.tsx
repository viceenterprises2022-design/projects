'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import ThemeToggle from '../ThemeToggle';
import StatCard from '../admin/StatCard';
import { WalletHistory, FeeLedger } from '../admin/customers/HistoryTables';
import { fmtUsd, fmtUsdC, fmtSigned, fmtSignedC, fmtTime } from '@/lib/format';

export default function AccountClient() {
  const [d, setD] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/account').then(async r => {
      const j = await r.json();
      if (!r.ok) throw new Error(j.error || 'Could not load your account');
      setD(j);
    }).catch(e => setError(e.message));
  }, []);

  if (!d) return (
    <div className="fable"><div className="f-shell"><div className="f-panel" style={{ marginTop: 18 }}>
      <div className="f-empty" style={{ color: error ? 'var(--oxide)' : undefined }}>{error || 'Loading your account…'}</div>
    </div></div></div>
  );

  const s = d.summary, t = d.totals;
  return (
    <div className="fable">
      <div className="f-shell">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, margin: '18px 0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, minWidth: 0 }}>
            <span className="f-brand-mark" style={{ width: 40, height: 40, fontSize: 17, borderRadius: 13 }}>P</span>
            <div style={{ minWidth: 0 }}>
              <div className="f-serif-grad" style={{ fontSize: 22 }}>My account</div>
              <div className="f-kicker" style={{ overflowWrap: 'anywhere' }}>{d.name} · {d.walletAddress}</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {s.lastSyncedAt && <span className="f-kicker">UPDATED {fmtTime(s.lastSyncedAt).slice(11)}</span>}
            <ThemeToggle compact />
            <Link href="/" className="f-btn" style={{ padding: '7px 14px', fontSize: 10, textDecoration: 'none' }}>HOME</Link>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10, marginBottom: 14 }}>
          <StatCard label="Wallet balance" value={fmtUsdC(s.balance)} title={fmtUsd(s.balance)} sub="your Hyperliquid account" />
          <StatCard label="Capital" value={fmtUsdC(s.capitalBasis)} title={fmtUsd(s.capitalBasis)} sub="profit is measured from here" />
          <StatCard label="Current profit" value={fmtSignedC(s.profit)} title={fmtSigned(s.profit)} tone={s.profit >= 0 ? 'pos' : 'neg'} />
          <StatCard label="Profit share" value={`${d.profitSharePct}%`} sub="of profit, charged only on withdrawal" />
          <StatCard label="Fee if you withdraw now" value={fmtUsdC(s.feeIfWithdrawnNow)} title={fmtUsd(s.feeIfWithdrawnNow)} sub={s.profit > 0 ? `${d.profitSharePct}% of ${fmtUsdC(s.profit)}` : 'no profit, no fee'} />
          <StatCard label="Fee due" value={fmtUsdC(s.outstandingFee)} title={fmtUsd(s.outstandingFee)} tone={s.outstandingFee > 0 ? 'gold' : undefined} sub={`${fmtUsdC(t.feesPaid)} paid to date`} />
        </div>

        {s.outstandingFee > 0 && (
          <div className="f-panel" style={{ marginBottom: 14, padding: 16, borderColor: 'rgba(232,194,106,0.45)' }}>
            <div className="f-kicker" style={{ marginBottom: 8, color: '#e8c26a' }}>FEE DUE · {fmtUsd(s.outstandingFee)}</div>
            <div className="f-mono" style={{ fontSize: 11, lineHeight: 1.6 }}>
              {d.feeAddress
                ? <>Send {fmtUsd(s.outstandingFee)} USDC on Hyperliquid (Send / transfer) to <span style={{ color: 'var(--ivory)', overflowWrap: 'anywhere' }}>{d.feeAddress}</span>. It is recognised automatically within 5 minutes.</>
                : <>Your account manager will share payment details.</>}
            </div>
          </div>
        )}

        <div className="f-panel" style={{ marginBottom: 14 }}>
          <div className="f-panel-head"><h2 className="f-panel-title"><span className="f-serif-grad">Withdrawal history</span></h2></div>
          <WalletHistory flows={d.flows} />
        </div>
        <div className="f-panel" style={{ marginBottom: 14 }}>
          <div className="f-panel-head"><h2 className="f-panel-title"><span className="f-serif-grad">Fee statement</span></h2></div>
          <FeeLedger fees={d.fees} />
        </div>
        <div className="f-mono f-faint" style={{ fontSize: 9.5, margin: '12px 2px' }}>
          Your funds stay in your own wallet. AlphaEdge trades through a key that cannot withdraw, and never debits your account.
          The fee is {d.profitSharePct}% of profit (balance minus capital) at the time you withdraw; losses carry forward and no fee is charged until they are recovered.
        </div>
      </div>
    </div>
  );
}
