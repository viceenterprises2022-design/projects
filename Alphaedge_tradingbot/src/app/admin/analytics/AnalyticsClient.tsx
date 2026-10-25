'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import ThemeToggle from '../../ThemeToggle';

// Strategy analytics, visible to every approved viewer. ONE fetch on load.
// The server streams every trade in the demo window through an exact
// accumulator and returns per-tier aggregates plus a decimated equity curve,
// so tier switches cost nothing and there is no row cap to fall behind.

type Stats = {
  n: number; wins: number; losses: number; hit: number;
  net: number; grossWin: number; grossLoss: number; volume: number;
  pf: number | null; expectancy: number; avgWin: number; avgLoss: number;
  largestWin: number; largestLoss: number;
  curStreak: number; bestW: number; worstL: number; maxDD: number;
};
type CurvePoint = { i: number; eq: number; t: { createdAt: number; asset: string; side: string; outcome: string; pnl: number } };
type TierView = {
  stats: Stats;
  byAsset: Array<{ key: string } & Stats>;
  bySide: Array<{ key: string } & Stats>;
  hours: Array<{ h: number; n: number; wins: number }>;
  curve: CurvePoint[];
  curveSampled: boolean;
};
type Payload = { tiers: Record<string, TierView>; totalRows: number; levels: any };

const TIERS = [
  { key: 0, label: 'ALL TIERS' },
  { key: 4, label: 'GOLD' },
  { key: 1, label: 'LEVEL 1' },
  { key: 2, label: 'LEVEL 2' },
  { key: 3, label: 'LEVEL 3' },
];

const fmtUsd = (n: number) => `$${Math.abs(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const fmtSigned = (n: number) => `${n >= 0 ? '+' : '−'}${fmtUsd(n)}`;
// Compact notation for tiles and tables: a 170px card cannot hold
// $107,254,738.12. Exact values stay available on hover via `title`.
const compact = (abs: number) => {
  if (abs >= 1e9) return `${(abs / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${(abs / 1e6).toFixed(2)}M`;
  if (abs >= 1e5) return `${(abs / 1e3).toFixed(1)}K`;
  return abs.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};
const fmtUsdC = (n: number) => `$${compact(Math.abs(n))}`;
const fmtSignedC = (n: number) => `${n >= 0 ? '+' : '−'}${fmtUsdC(n)}`;
const fmtPctC = (n: number, signed = false) => {
  const a = Math.abs(n);
  const body = a >= 1e4 ? `${compact(a).replace(/\.00(?=[KMB])/, '')}%` : `${a.toFixed(2)}%`;
  return signed ? `${n >= 0 ? '+' : '−'}${body}` : body;
};
const int = (n: number) => n.toLocaleString();
const pct = (n: number) => `${n.toFixed(1)}%`;
// Server encodes an infinite profit factor (wins, zero losses) as null.
const fmtPf = (pf: number | null) => pf === null ? '∞' : pf.toFixed(2);
const pfOk = (pf: number | null) => pf === null || pf >= 1;

function StatCard({ label, value, sub, tone, title }: { label: string; value: string; sub?: string; tone?: 'pos' | 'neg' | 'azure' | 'violet'; title?: string }) {
  const color = tone === 'pos' ? 'var(--sage)' : tone === 'neg' ? 'var(--oxide)' : tone === 'azure' ? 'var(--azure)' : tone === 'violet' ? '#9d7dff' : 'var(--ivory)';
  // Step the font down for long values so they never wrap or spill into the
  // neighbouring card. Compact formatting keeps most values under 10 chars.
  // "A / B" pairs (Avg win / loss) stack onto two lines instead of clipping.
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

export default function AnalyticsClient({ isOwner = false }: { isOwner?: boolean }) {
  const [data, setData] = useState<Payload | null>(null);
  const [tier, setTier] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loadedAt, setLoadedAt] = useState<Date | null>(null);
  const curveRef = useRef<HTMLCanvasElement>(null);
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  // Pixel<->index geometry from the last paint, so the pointer handler can map
  // a mouse position back to a point without recomputing the series.
  const geomRef = useRef<{ pts: CurvePoint[]; x0: number; span: number; w: number } | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const res = await fetch('/api/admin/analytics');
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Failed to load analytics');
      setData(json); setLoadedAt(new Date());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const view = useMemo(() => {
    if (!data) return null;
    const tv = data.tiers[String(tier)];
    if (!tv) return null;
    const stats = tv.stats;
    const base = tier === 0
      ? Object.values(data.levels).reduce((a: number, l: any) => a + (l.base || 0), 0)
      : (data.levels[String(tier)]?.base || 0);
    const roce = base > 0 ? (stats.net / base) * 100 : 0;
    return {
      stats, roce, base,
      curve: tv.curve, curveSampled: tv.curveSampled,
      byAsset: tv.byAsset,
      bySide: tv.bySide,
      byTier: [4, 1, 2, 3].map(l => {
        const s = data.tiers[String(l)].stats;
        const b = data.levels[String(l)]?.base || 0;
        return { key: l === 4 ? 'GOLD' : `LEVEL ${l}`, ...s, roce: b > 0 ? (s.net / b) * 100 : 0 };
      }),
      hours: tv.hours,
      maxHourN: Math.max(1, ...tv.hours.map(x => x.n)),
    };
  }, [data, tier]);

  // Equity curve painter — pure client-side, draws from the already-fetched set
  useEffect(() => {
    const cv = curveRef.current;
    if (!cv || !view) return;
    const dpr = window.devicePixelRatio || 1;
    const w = cv.clientWidth, h = cv.clientHeight;
    cv.width = w * dpr; cv.height = h * dpr;
    const ctx = cv.getContext('2d');
    if (!ctx) return;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, h);
    // Origin point first so the curve starts at zero, matching the old render.
    const pts: CurvePoint[] = [{ i: 0, eq: 0, t: null as any }, ...view.curve];
    if (pts.length < 2) {
      ctx.fillStyle = 'rgba(239,246,255,0.35)';
      ctx.font = '11px monospace';
      ctx.fillText('Curve appears after the first settlements…', 14, h / 2);
      return;
    }
    let min = 0, max = 0;
    for (const p of pts) { if (p.eq < min) min = p.eq; if (p.eq > max) max = p.eq; }
    const span = Math.max(1, max - min);
    const X = (i: number) => (i / (pts.length - 1)) * (w - 20) + 10;
    const Y = (v: number) => h - 16 - ((v - min) / span) * (h - 32);
    geomRef.current = { pts, x0: 10, span: w - 20, w };
    // zero line
    ctx.strokeStyle = 'rgba(255,255,255,0.12)'; ctx.setLineDash([4, 4]);
    ctx.beginPath(); ctx.moveTo(10, Y(0)); ctx.lineTo(w - 10, Y(0)); ctx.stroke();
    ctx.setLineDash([]);
    // area
    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, 'rgba(88,240,255,0.22)'); grad.addColorStop(1, 'rgba(88,240,255,0)');
    ctx.beginPath(); ctx.moveTo(X(0), Y(pts[0].eq));
    pts.forEach((p, i) => ctx.lineTo(X(i), Y(p.eq)));
    ctx.lineTo(X(pts.length - 1), h - 16); ctx.lineTo(X(0), h - 16); ctx.closePath();
    ctx.fillStyle = grad; ctx.fill();
    // line
    ctx.beginPath(); ctx.moveTo(X(0), Y(pts[0].eq));
    pts.forEach((p, i) => ctx.lineTo(X(i), Y(p.eq)));
    ctx.strokeStyle = pts[pts.length - 1].eq >= 0 ? '#58f0ff' : '#f6465d';
    ctx.lineWidth = 1.6; ctx.stroke();
    // endpoint
    ctx.beginPath(); ctx.arc(X(pts.length - 1), Y(pts[pts.length - 1].eq), 3, 0, Math.PI * 2);
    ctx.fillStyle = pts[pts.length - 1].eq >= 0 ? '#bfff6a' : '#f6465d'; ctx.fill();
    // hover crosshair + marker
    if (hoverIdx !== null && hoverIdx >= 0 && hoverIdx < pts.length) {
      const hx = X(hoverIdx), hy = Y(pts[hoverIdx].eq);
      ctx.strokeStyle = 'rgba(239,246,255,0.28)'; ctx.lineWidth = 1;
      ctx.setLineDash([3, 3]);
      ctx.beginPath(); ctx.moveTo(hx, 6); ctx.lineTo(hx, h - 10); ctx.stroke();
      ctx.setLineDash([]);
      ctx.beginPath(); ctx.arc(hx, hy, 4.5, 0, Math.PI * 2);
      ctx.fillStyle = '#050711'; ctx.fill();
      ctx.strokeStyle = pts[hoverIdx].eq >= 0 ? '#bfff6a' : '#f6465d'; ctx.lineWidth = 2; ctx.stroke();
    }

    // labels
    ctx.fillStyle = 'rgba(239,246,255,0.45)'; ctx.font = '9px monospace';
    ctx.fillText(fmtSignedC(max), 12, 12);
    ctx.fillText(fmtSignedC(min), 12, h - 4);
  }, [view, hoverIdx]);

  const s = view?.stats;

  return (
    <div className="fable">
      <div className="f-shell">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, margin: '18px 0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <span className="f-brand-mark" style={{ width: 40, height: 40, fontSize: 17, borderRadius: 13 }}>P</span>
            <div>
              <div className="f-serif-grad" style={{ fontSize: 22 }}>Strategy Analytics</div>
              <div className="f-kicker">COMPUTED FROM ONE LEDGER SNAPSHOT · NO POLLING</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            {loadedAt && <span className="f-kicker">SNAPSHOT {loadedAt.toLocaleTimeString(undefined, { hour12: false })}</span>}
            <button className="f-btn" style={{ padding: '7px 14px', fontSize: 10 }} onClick={load} disabled={loading}>
              {loading ? 'LOADING…' : 'REFRESH'}
            </button>
            {isOwner && (
              <Link href="/admin/ledger" className="f-btn" style={{ padding: '7px 14px', fontSize: 10, textDecoration: 'none' }}>LEDGER EXPLORER</Link>
            )}
            <ThemeToggle compact />
            <Link href="/demo" className="f-btn" style={{ padding: '7px 14px', fontSize: 10, textDecoration: 'none' }}>← COCKPIT</Link>
          </div>
        </div>

        {error && <div className="f-panel"><div className="f-empty" style={{ color: 'var(--oxide)' }}>{error}</div></div>}

        {view && s && (
          <>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
              {TIERS.map(t => (
                <button key={t.key} className="f-btn" onClick={() => setTier(t.key)}
                  style={{
                    padding: '5px 13px', fontSize: 9.5,
                    ...(tier === t.key ? { borderColor: 'rgba(88,240,255,0.55)', color: '#58f0ff', background: 'rgba(88,240,255,0.08)' } : {}),
                  }}>
                  {t.label}
                </button>
              ))}
              <span className="f-kicker" style={{ alignSelf: 'center', marginLeft: 6 }}>{data?.totalRows.toLocaleString()} TRADES IN WINDOW</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10, marginBottom: 14 }}>
              <StatCard label="Net P&L" value={fmtSignedC(s.net)} title={fmtSigned(s.net)} tone={s.net >= 0 ? 'pos' : 'neg'}
                sub={`${int(s.n)} settled · ${fmtUsdC(s.volume)} volume`} />
              <StatCard label="ROCE" value={fmtPctC(view.roce, true)} title={`${view.roce.toFixed(2)}%`} tone={view.roce >= 0 ? 'pos' : 'neg'}
                sub={`on ${fmtUsdC(view.base)} capital base`} />
              <StatCard label="Hit rate" value={pct(s.hit)} tone="azure" sub={`${int(s.wins)} W / ${int(s.losses)} L`} />
              <StatCard label="Profit factor" value={fmtPf(s.pf)} tone={pfOk(s.pf) ? 'pos' : 'neg'}
                sub={`${fmtUsdC(s.grossWin)} won / ${fmtUsdC(s.grossLoss)} lost`} title={`${fmtUsd(s.grossWin)} won / ${fmtUsd(s.grossLoss)} lost`} />
              <StatCard label="Expectancy" value={fmtSignedC(s.expectancy)} title={fmtSigned(s.expectancy)} tone={s.expectancy >= 0 ? 'pos' : 'neg'} sub="per settled trade" />
              <StatCard label="Avg win / loss" value={`${fmtUsdC(s.avgWin)} / ${fmtUsdC(s.avgLoss)}`} title={`${fmtUsd(s.avgWin)} / ${fmtUsd(s.avgLoss)}`}
                sub={`payoff ratio ${s.avgLoss > 0 ? (s.avgWin / s.avgLoss).toFixed(2) : '—'}`} />
              <StatCard label="Max drawdown" value={fmtUsdC(s.maxDD)} title={fmtUsd(s.maxDD)} tone="neg"
                sub={view.base > 0 ? `${fmtPctC((s.maxDD / view.base) * 100)} of base` : undefined} />
              <StatCard label="Streaks" value={`${s.curStreak >= 0 ? 'W' : 'L'}${Math.abs(s.curStreak)}`} tone={s.curStreak >= 0 ? 'pos' : 'neg'}
                sub={`best ${s.bestW}W · worst ${s.worstL}L`} />
              <StatCard label="Extremes" value={fmtSignedC(s.largestWin)} title={`best ${fmtSigned(s.largestWin)} · worst ${fmtSigned(s.largestLoss)}`} tone="pos"
                sub={`worst single: ${fmtSignedC(s.largestLoss)}`} />
            </div>

            <div className="f-panel" style={{ marginBottom: 14 }}>
              <div className="f-panel-head">
                <h2 className="f-panel-title"><span className="f-serif-grad">Equity Curve</span>
                  <span className="f-kicker" style={{ marginLeft: 6 }}>{TIERS.find(t => t.key === tier)?.label} · CUMULATIVE REALIZED P&L{view.curveSampled ? ' · SAMPLED' : ''} · HOVER FOR DETAIL</span>
                </h2>
              </div>
              <div style={{ position: 'relative' }}
                onMouseLeave={() => setHoverIdx(null)}
                onMouseMove={(e) => {
                  const g = geomRef.current;
                  if (!g || g.pts.length < 2) return;
                  const rect = e.currentTarget.getBoundingClientRect();
                  const rel = (e.clientX - rect.left - g.x0) / g.span;
                  const i = Math.round(rel * (g.pts.length - 1));
                  setHoverIdx(Math.min(g.pts.length - 1, Math.max(0, i)));
                }}>
                <canvas ref={curveRef} style={{ width: '100%', height: 190, display: 'block', cursor: 'crosshair' }} />
                {hoverIdx !== null && view && geomRef.current && (() => {
                  const pt = geomRef.current.pts[hoverIdx];
                  const cum = pt.eq;
                  const t = hoverIdx > 0 ? pt.t : null;
                  const leftPct = (hoverIdx / Math.max(1, geomRef.current.pts.length - 1)) * 100;
                  return (
                    <div style={{
                      position: 'absolute', top: 6, left: `${leftPct}%`,
                      transform: `translateX(${leftPct > 65 ? '-104%' : leftPct < 12 ? '4%' : '-50%'})`,
                      pointerEvents: 'none', zIndex: 3, minWidth: 168,
                      background: 'rgba(5,7,17,0.94)', border: '1px solid var(--hairline-strong)',
                      borderRadius: 10, padding: '8px 11px', backdropFilter: 'blur(6px)',
                    }}>
                      <div className="f-kicker" style={{ fontSize: 8 }}>
                        {t ? new Date(t.createdAt).toISOString().replace('T', ' ').slice(0, 19) + ' UTC' : 'START OF WINDOW'}
                      </div>
                      <div className={`f-mono ${cum >= 0 ? 'f-pos' : 'f-neg'}`}
                        style={{ fontSize: 16, fontWeight: 700, marginTop: 3, fontVariantNumeric: 'tabular-nums' }}>
                        {fmtSigned(cum)}
                      </div>
                      <div className="f-mono f-faint" style={{ fontSize: 9, marginTop: 1 }}>
                        cumulative · trade {pt.i.toLocaleString()} of {s.n.toLocaleString()}
                      </div>
                      {t && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 6, flexWrap: 'wrap' }}>
                          <span className="f-mono f-faint" style={{ fontSize: 9.5 }}>{t.asset}</span>
                          <span className={`f-tag ${t.side === 'BUY' ? 'win' : 'loss'}`} style={{ fontSize: 8 }}>{t.side}</span>
                          <span className={`f-tag ${t.outcome === 'WIN' ? 'win' : 'loss'}`} style={{ fontSize: 8 }}>{t.outcome}</span>
                          <span className={`f-mono ${t.pnl >= 0 ? 'f-pos' : 'f-neg'}`}
                            style={{ fontSize: 10.5, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
                            {fmtSigned(t.pnl)}
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })()}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 14, marginBottom: 14 }}>
              {[
                { title: 'By Asset', rows: view.byAsset },
                { title: 'By Side', rows: view.bySide },
              ].map(sec => (
                <div className="f-panel" key={sec.title}>
                  <div className="f-panel-head"><h2 className="f-panel-title"><span className="f-serif-grad">{sec.title}</span></h2></div>
                  <table className="f-table">
                    <thead><tr><th>{sec.title === 'By Side' ? 'Side' : 'Asset'}</th><th className="num">Trades</th><th className="num">Hit</th><th className="num">PF</th><th className="num">Net P&L</th></tr></thead>
                    <tbody>
                      {sec.rows.map((r: any) => (
                        <tr key={r.key}>
                          <td>{sec.title === 'By Side'
                            ? <span className={`f-tag ${r.key === 'BUY' ? 'win' : 'loss'}`}>{r.key}</span>
                            : r.key}</td>
                          <td className="num f-mono">{int(r.n)}</td>
                          <td className="num f-mono">{pct(r.hit)}</td>
                          <td className="num f-mono">{fmtPf(r.pf)}</td>
                          <td className={`num f-mono ${r.net >= 0 ? 'f-pos' : 'f-neg'}`} style={{ fontWeight: 700 }} title={fmtSigned(r.net)}>{fmtSignedC(r.net)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))}
            </div>

            <div className="f-panel" style={{ marginBottom: 14 }}>
              <div className="f-panel-head"><h2 className="f-panel-title"><span className="f-serif-grad">Tier Comparison</span>
                <span className="f-kicker" style={{ marginLeft: 6 }}>ALL TIERS · SAME SNAPSHOT</span></h2></div>
              <table className="f-table">
                <thead><tr><th>Tier</th><th className="num">Trades</th><th className="num">W / L</th><th className="num">Hit</th><th className="num">PF</th><th className="num">Expectancy</th><th className="num">Max DD</th><th className="num">Net P&L</th><th className="num">ROCE</th></tr></thead>
                <tbody>
                  {view.byTier.map((r: any) => (
                    <tr key={r.key}>
                      <td><span className={`f-tag ${r.key === 'GOLD' ? 'azure' : 'dim'}`}>{r.key}</span></td>
                      <td className="num f-mono">{int(r.n)}</td>
                      <td className="num f-mono">{int(r.wins)} / {int(r.losses)}</td>
                      <td className="num f-mono">{pct(r.hit)}</td>
                      <td className="num f-mono">{fmtPf(r.pf)}</td>
                      <td className={`num f-mono ${r.expectancy >= 0 ? 'f-pos' : 'f-neg'}`} title={fmtSigned(r.expectancy)}>{fmtSignedC(r.expectancy)}</td>
                      <td className="num f-mono f-neg" title={fmtUsd(r.maxDD)}>{fmtUsdC(r.maxDD)}</td>
                      <td className={`num f-mono ${r.net >= 0 ? 'f-pos' : 'f-neg'}`} style={{ fontWeight: 700 }} title={fmtSigned(r.net)}>{fmtSignedC(r.net)}</td>
                      <td className={`num f-mono ${r.roce >= 0 ? 'f-pos' : 'f-neg'}`}>{fmtPctC(r.roce, true)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="f-panel">
              <div className="f-panel-head"><h2 className="f-panel-title"><span className="f-serif-grad">Hourly Distribution</span>
                <span className="f-kicker" style={{ marginLeft: 6 }}>UTC · TRADES PER HOUR · GREEN = WIN SHARE</span></h2></div>
              <div style={{ display: 'flex', gap: 3, alignItems: 'flex-end', height: 90, padding: '0 2px' }}>
                {view.hours.map(hb => {
                  const hgt = (hb.n / view.maxHourN) * 74;
                  const winShare = hb.n > 0 ? hb.wins / hb.n : 0;
                  return (
                    <div key={hb.h} title={`${String(hb.h).padStart(2, '0')}:00 UTC — ${hb.n} trades, ${hb.n ? Math.round(winShare * 100) : 0}% wins`}
                      style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', height: '100%' }}>
                      <div style={{
                        height: Math.max(hb.n > 0 ? 3 : 0, hgt), borderRadius: 2,
                        background: hb.n === 0 ? 'transparent'
                          : `linear-gradient(to top, rgba(246,70,93,0.55) 0%, rgba(246,70,93,0.55) ${(1 - winShare) * 100}%, rgba(191,255,106,0.75) ${(1 - winShare) * 100}%, rgba(191,255,106,0.75) 100%)`,
                      }} />
                    </div>
                  );
                })}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
                <span className="f-kicker">00:00</span><span className="f-kicker">06:00</span>
                <span className="f-kicker">12:00</span><span className="f-kicker">18:00</span><span className="f-kicker">23:00</span>
              </div>
            </div>

            <div className="f-mono f-faint" style={{ fontSize: 9, margin: '12px 2px', letterSpacing: '0.05em' }}>
              All figures computed server-side over every trade in the demo window ({s.n.toLocaleString()} in this view). Tier switches cost zero additional database reads. Hit REFRESH for a new snapshot.
            </div>
          </>
        )}
      </div>
    </div>
  );
}
