// Money and number formatting shared by every dashboard screen.
// Compact notation keeps tiles from overflowing; pages show the exact figure
// on hover via `title`.

export const fmtUsd = (n: number) =>
  `$${Math.abs(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
export const fmtSigned = (n: number) => `${n >= 0 ? '+' : '−'}${fmtUsd(n)}`;

const compact = (abs: number) => {
  if (abs >= 1e9) return `${(abs / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${(abs / 1e6).toFixed(2)}M`;
  if (abs >= 1e5) return `${(abs / 1e3).toFixed(1)}K`;
  return abs.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};
export const fmtUsdC = (n: number) => `$${compact(Math.abs(n))}`;
export const fmtSignedC = (n: number) => `${n >= 0 ? '+' : '−'}${fmtUsdC(n)}`;
export const fmtPctC = (n: number, signed = false) => {
  const a = Math.abs(n);
  const body = a >= 1e4 ? `${compact(a).replace(/\.00(?=[KMB])/, '')}%` : `${a.toFixed(2)}%`;
  return signed ? `${n >= 0 ? '+' : '−'}${body}` : body;
};
export const pct = (n: number) => `${n.toFixed(1)}%`;
export const int = (n: number) => n.toLocaleString();
export const fmtPf = (pf: number | null) => pf === null ? '∞' : pf.toFixed(2);
export const pfOk = (pf: number | null) => pf === null || pf >= 1;
export const fmtTime = (ms: number) => new Date(ms).toISOString().replace('T', ' ').slice(0, 16) + ' UTC';
export const shortAddr = (a: string) => a ? `${a.slice(0, 6)}…${a.slice(-4)}` : '';
