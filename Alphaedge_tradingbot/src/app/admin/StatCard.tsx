// Overflow-safe stat tile. Long values step the font down; "A / B" pairs
// stack on two lines; nothing ever spills into the neighbouring card.
export default function StatCard({ label, value, sub, tone, title }: {
  label: string; value: string; sub?: string; tone?: 'pos' | 'neg' | 'azure' | 'violet' | 'gold'; title?: string;
}) {
  const color = tone === 'pos' ? 'var(--sage)' : tone === 'neg' ? 'var(--oxide)' : tone === 'azure' ? 'var(--azure)'
    : tone === 'violet' ? '#9d7dff' : tone === 'gold' ? '#e8c26a' : 'var(--ivory)';
  const parts = value.split(' / ');
  const longest = Math.max(...parts.map(p => p.length));
  const size = longest > 16 ? 15 : longest > 12 ? 18 : 21;
  return (
    <div className="f-panel" style={{ padding: '14px 16px', minWidth: 0, overflow: 'hidden' }} title={title}>
      <div className="f-kicker" style={{ marginBottom: 6, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{label}</div>
      <div className="f-mono" style={{
        fontSize: size, fontWeight: 700, color, lineHeight: 1.2,
        fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
      }}>{parts.length === 2
        ? <>{parts[0]}<span className="f-faint" style={{ fontWeight: 400 }}> /</span><br />{parts[1]}</>
        : value}</div>
      {sub && <div className="f-mono f-faint" style={{ fontSize: 9.5, marginTop: 4, overflowWrap: 'anywhere' }}>{sub}</div>}
    </div>
  );
}
