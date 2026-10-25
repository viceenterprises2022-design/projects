import { fmtUsd, fmtUsdC, fmtSignedC, fmtTime, shortAddr } from '@/lib/format';

// Shared by the owner's customer page and the customer's own account page,
// so both always show the same numbers.

const KIND_LABEL: Record<string, string> = {
  deposit: 'DEPOSIT', withdrawal: 'WITHDRAWAL', fee_payment: 'FEE PAID', transfer_in: 'TRANSFER IN',
  transfer_out: 'TRANSFER OUT', unclassified: 'OTHER',
  crystallisation: 'FEE CHARGED', payment: 'FEE PAID (ON-CHAIN)', manual_payment: 'FEE PAID (MANUAL)', waiver: 'FEE WAIVED',
};
const KIND_TAG: Record<string, string> = {
  deposit: 'win', transfer_in: 'win', withdrawal: 'loss', transfer_out: 'loss', fee_payment: 'gold', unclassified: 'dim',
  crystallisation: 'gold', payment: 'win', manual_payment: 'win', waiver: 'dim',
};

const explorer = (hash: string | null) => hash && /^0x[0-9a-f]{64}$/i.test(hash)
  ? `https://app.hyperliquid.xyz/explorer/tx/${hash}` : null;

export function WalletHistory({ flows, showRaw = false }: { flows: any[]; showRaw?: boolean }) {
  if (!flows.length) return <div className="f-empty">No deposits or withdrawals since onboarding.</div>;
  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="f-table">
        <thead><tr>
          <th>Time</th><th>Type</th><th className="num">Amount</th><th className="num">Profit at withdrawal</th>
          <th className="num">Share</th><th className="num">AlphaEdge fee</th><th className="num">Customer keeps</th><th>Tx</th>
        </tr></thead>
        <tbody>
          {flows.map(f => {
            const isOut = f.kind === 'withdrawal' || f.kind === 'transfer_out';
            const keeps = isOut && f.fee !== null ? f.amount - f.fee : null;
            const url = explorer(f.txHash);
            return (
              <tr key={f.id}>
                <td className="f-mono" style={{ fontSize: 10.5, whiteSpace: 'nowrap' }}>{fmtTime(f.occurredAt)}</td>
                <td><span className={`f-tag ${KIND_TAG[f.kind] || 'dim'}`} style={{ fontSize: 8 }}>{KIND_LABEL[f.kind] || f.kind}</span>
                  {showRaw && !f.processed && <span className="f-tag violet" style={{ fontSize: 8, marginLeft: 4 }}>PENDING</span>}</td>
                <td className="num f-mono" title={fmtUsd(f.amount)}>{fmtUsdC(f.amount)}</td>
                <td className={`num f-mono ${f.profitAtWithdrawal > 0 ? 'f-pos' : f.profitAtWithdrawal < 0 ? 'f-neg' : ''}`}>
                  {f.profitAtWithdrawal === null ? '—' : fmtSignedC(f.profitAtWithdrawal)}
                  {f.estimated && <span className="f-faint" title="Balance at the moment of withdrawal was reconstructed from the next sync"> *</span>}
                </td>
                <td className="num f-mono">{f.pct === null ? '—' : `${f.pct}%`}</td>
                <td className="num f-mono" style={{ color: f.fee > 0 ? '#e8c26a' : undefined, fontWeight: f.fee > 0 ? 700 : 400 }}>
                  {f.fee === null ? '—' : fmtUsdC(f.fee)}</td>
                <td className="num f-mono">{keeps === null ? '—' : fmtUsdC(keeps)}</td>
                <td className="f-mono" style={{ fontSize: 10 }}>
                  {url ? <a href={url} target="_blank" rel="noreferrer" style={{ color: 'var(--azure)' }}>{shortAddr(f.txHash)}</a> : '—'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {flows.some(f => f.estimated) && (
        <div className="f-mono f-faint" style={{ fontSize: 9, marginTop: 8 }}>
          * Balance at the moment of withdrawal is reconstructed from the wallet balance at the next 5-minute sync.
        </div>
      )}
    </div>
  );
}

export function FeeLedger({ fees }: { fees: any[] }) {
  if (!fees.length) return <div className="f-empty">No fees charged yet. A fee is calculated only when profit is withdrawn.</div>;
  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="f-table">
        <thead><tr><th>Time</th><th>Event</th><th className="num">Profit</th><th className="num">Share</th>
          <th className="num">Charged</th><th className="num">Settled</th><th className="num">Owed after</th><th>Note</th></tr></thead>
        <tbody>
          {fees.map((f, i) => (
            <tr key={f.id || i}>
              <td className="f-mono" style={{ fontSize: 10.5, whiteSpace: 'nowrap' }}>{fmtTime(f.createdAt)}</td>
              <td><span className={`f-tag ${KIND_TAG[f.kind] || 'dim'}`} style={{ fontSize: 8 }}>{KIND_LABEL[f.kind] || f.kind}</span></td>
              <td className="num f-mono">{f.profit === null || f.profit === undefined ? '—' : fmtSignedC(f.profit)}</td>
              <td className="num f-mono">{f.pct === null || f.pct === undefined ? '—' : `${f.pct}%`}</td>
              <td className="num f-mono" style={{ color: f.fee > 0 ? '#e8c26a' : undefined }}>{f.fee > 0 ? fmtUsdC(f.fee) : '—'}</td>
              <td className="num f-mono f-pos">{f.kind !== 'crystallisation' && f.amount > 0 ? fmtUsdC(f.amount) : '—'}</td>
              <td className="num f-mono">{fmtUsdC(f.outstandingAfter)}</td>
              <td className="f-faint" style={{ fontSize: 10, maxWidth: 260 }}>{f.note || ''}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
