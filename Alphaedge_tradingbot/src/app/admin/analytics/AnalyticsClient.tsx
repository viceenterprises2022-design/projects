'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';

// Owner-only strategy analytics. ONE fetch on load (single DB scan server-
// side); every metric and view below is computed in the browser from that
// result. Switching tiers/views costs zero additional database reads.

type Trade = {
  createdAt: number; level: number; asset: string; side: string;
  outcome: string; pnl: number; size: number; entryPrice: number;
};

const TIERS = [
  { key: 0, label: 'ALL TIERS' },
  { key: 4, label: 'DEMO' },
  { key: 1, label: 'LEVEL 1' },
  { key: 2, label: 'LEVEL 2' },
  { key: 3, label: 'LEVEL 3' },
];

const fmtUsd = (n: number) => `$${Math.abs(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const fmtSigned = (n: number) => `${n >= 0 ? '+' : '−'}${fmtUsd(n)}`;
const pct = (n: number) => `${n.toFixed(1)}%`;

function computeStats(trades: Trade[]) {
  let wins = 0, grossWin = 0, grossLoss = 0, largestWin = 0, largestLoss = 0, volume = 0;
  for (const t of trades) {
    volume += t.size * t.entryPrice;
    if (t.outcome === 'WIN') { wins++; grossWin += t.pnl; largestWin = Math.max(largestWin, t.pnl); }
    else { grossLoss += -t.pnl; largestLoss = Math.min(largestLoss, t.pnl); }
  }
  const n = trades.length, losses = n - wins;
  const net = grossWin - grossLoss;
  // Streaks + drawdown over the chronological sequence
  let curStreak = 0, bestW = 0, worstL = 0, run = 0, last = '';
  let equity = 0, peak = 0, maxDD = 0;
  for (const t of trades) {
    const o = t.outcome === 'WIN' ? 'W' : 'L';
    run = o === last ? run + 1 : 1; last = o;
    if (o === 'W') bestW = Math.max(bestW, run); else worstL = Math.max(worstL, run);
    equity += t.pnl; peak = Math.max(peak, equity); maxDD = Math.max(maxDD, peak - equity);
  }
  curStreak = run * (last === 'W' ? 1 : -1);
  return {
    n, wins, losses,
    hit: n > 0 ? (wins / n) * 100 : 0,
    net, grossWin, grossLoss, volume,
    pf: grossLoss > 0 ? grossWin / grossLoss : (grossWin > 0 ? Infinity : 0),
    expectancy: n > 0 ? net / n : 0,
    avgWin: wins > 0 ? grossWin / wins : 0,
    avgLoss: losses > 0 ? grossLoss / losses : 0,
    largestWin, largestLoss, curStreak, bestW, worstL, maxDD,
  };
}

function StatCard({ label, value, sub, tone }: { label: string; value: string; sub?: string; tone?: 'pos' | 'neg' | 'azure' | 'violet' }) {
  const color = tone === 'pos' ? 'var(--sage)' : tone === 'neg' ? 'var(--oxide)' : tone === 'azure' ? 'var(--azure)' : tone === 'violet' ? '#9d7dff' : 'var(--ivory)';
  return (
    <div className="f-panel" style={{ padding: '14px 16px' }}>
      <div className="f-kicker" style={{ marginBottom: 6 }}>{label}</div>
      <div className="f-mono" style={{ fontSize: 21, fontWeight: 700, color, fontVariantNumeric: 'tabular-nums' }}>{value}</div>
      {sub && <div className="f-mono f-faint" style={{ fontSize: 9.5, marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

export default function AnalyticsClient() {
  const [data, setData] = useState<{ trades: Trade[]; levels: any; truncated: boolean } | null>(null);
  const [tier, setTier] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loadedAt, setLoadedAt] = useState<Date | null>(null);
  const curveRef = useRef<HTMLCanvasElement>(null);

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
    const subset = tier === 0 ? data.trades : data.trades.filter(t => t.level === tier);
    const stats = computeStats(subset);
    const base = tier === 0
      ? Object.values(data.levels).reduce((a: number, l: any) => a + (l.base || 0), 0)
      : (data.levels[String(tier)]?.base || 0);
    const roce = base > 0 ? (stats.net / base) * 100 : 0;

    const byGroup = (keyFn: (t: Trade) => string) => {
      const m = new Map<string, Trade[]>();
      for (const t of subset) {
        const k = keyFn(t);
        if (!m.has(k)) m.set(k, []);
        m.get(k)!.push(t);
      }
      return [...m.entries()].map(([k, v]) => ({ key: k, ...computeStats(v) }));
    };

    const hours = Array.from({ length: 24 }, (_, h) => ({ h, n: 0, wins: 0 }));
    for (const t of subset) {
      const h = new Date(t.createdAt).getUTCHours();
      hours[h].n++;
      if (t.outcome === 'WIN') hours[h].wins++;
    }

    return {
      subset, stats, roce, base,
      byAsset: byGroup(t => t.asset).sort((a, b) => a.key.localeCompare(b.key)),
      bySide: byGroup(t => t.side).sort((a, b) => a.key.localeCompare(b.key)),
      byTier: [4, 1, 2, 3].map(l => {
        const rows = data.trades.filter(t => t.level === l);
        const s = computeStats(rows);
        const b = data.levels[String(l)]?.base || 0;
        return { key: l === 4 ? 'DEMO' : `LEVEL ${l}`, ...s, roce: b > 0 ? (s.net / b) * 100 : 0 };
      }),
      hours,
      maxHourN: Math.max(1, ...hours.map(x => x.n)),
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
    const pts: number[] = [0];
    let eq = 0;
    for (const t of view.subset) { eq += t.pnl; pts.push(eq); }
    if (pts.length < 2) {
      ctx.fillStyle = 'rgba(239,246,255,0.35)';
      ctx.font = '11px monospace';
      ctx.fillText('Curve appears after the first settlements…', 14, h / 2);
      return;
    }
    const min = Math.min(...pts, 0), max = Math.max(...pts, 0);
    const span = Math.max(1, max - min);
    const X = (i: number) => (i / (pts.length - 1)) * (w - 20) + 10;
    const Y = (v: number) => h - 16 - ((v - min) / span) * (h - 32);
    // zero line
    ctx.strokeStyle = 'rgba(255,255,255,0.12)'; ctx.setLineDash([4, 4]);
    ctx.beginPath(); ctx.moveTo(10, Y(0)); ctx.lineTo(w - 10, Y(0)); ctx.stroke();
    ctx.setLineDash([]);
    // area
    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, 'rgba(88,240,255,0.22)'); grad.addColorStop(1, 'rgba(88,240,255,0)');
    ctx.beginPath(); ctx.moveTo(X(0), Y(pts[0]));
    pts.forEach((v, i) => ctx.lineTo(X(i), Y(v)));
    ctx.lineTo(X(pts.length - 1), h - 16); ctx.lineTo(X(0), h - 16); ctx.closePath();
    ctx.fillStyle = grad; ctx.fill();
    // line
    ctx.beginPath(); ctx.moveTo(X(0), Y(pts[0]));
    pts.forEach((v, i) => ctx.lineTo(X(i), Y(v)));
    ctx.strokeStyle = pts[pts.length - 1] >= 0 ? '#58f0ff' : '#f6465d';
    ctx.lineWidth = 1.6; ctx.stroke();
    // endpoint
    ctx.beginPath(); ctx.arc(X(pts.length - 1), Y(pts[pts.length - 1]), 3, 0, Math.PI * 2);
    ctx.fillStyle = pts[pts.length - 1] >= 0 ? '#bfff6a' : '#f6465d'; ctx.fill();
    // labels
    ctx.fillStyle = 'rgba(239,246,255,0.45)'; ctx.font = '9px monospace';
    ctx.fillText(fmtSigned(max), 12, 12);
    ctx.fillText(fmtSigned(min), 12, h - 4);
  }, [view]);

  const s = view?.stats;

  return (
    <div className="fable">
      <div className="f-shell">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, margin: '18px 0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <span className="f-brand-mark" style={{ width: 40, height: 40, fontSize: 17, borderRadius: 13 }}>P</span>
            <div>
              <div className="f-serif-grad" style={{ fontSize: 22 }}>Strategy Analytics</div>
              <div className="f-kicker">ADMIN · COMPUTED FROM ONE LEDGER SNAPSHOT · NO POLLING</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            {loadedAt && <span className="f-kicker">SNAPSHOT {loadedAt.toLocaleTimeString(undefined, { hour12: false })}</span>}
            <button className="f-btn" style={{ padding: '7px 14px', fontSize: 10 }} onClick={load} disabled={loading}>
              {loading ? 'LOADING…' : 'REFRESH'}
            </button>
            <Link href="/admin/ledger" className="f-btn" style={{ padding: '7px 14px', fontSize: 10, textDecoration: 'none' }}>LEDGER EXPLORER</Link>
            <Link href="/dashboard" className="f-btn" style={{ padding: '7px 14px', fontSize: 10, textDecoration: 'none' }}>← COCKPIT</Link>
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
              {data?.truncated && <span className="f-tag gold" title="Snapshot capped at 8,000 most recent rows">CAPPED @ 8K ROWS</span>}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 10, marginBottom: 14 }}>
              <StatCard label="Net P&L" value={fmtSigned(s.net)} tone={s.net >= 0 ? 'pos' : 'neg'} sub={`${s.n} settled · ${fmtUsd(s.volume)} volume`} />
              <StatCard label="ROCE" value={`${view.roce >= 0 ? '+' : '−'}${Math.abs(view.roce).toFixed(2)}%`} tone={view.roce >= 0 ? 'pos' : 'neg'} sub={`on ${fmtUsd(view.base)} capital base`} />
              <StatCard label="Hit rate" value={pct(s.hit)} tone="azure" sub={`${s.wins} W / ${s.losses} L`} />
              <StatCard label="Profit factor" value={s.pf === Infinity ? '∞' : s.pf.toFixed(2)} tone={s.pf >= 1 ? 'pos' : 'neg'} sub={`${fmtUsd(s.grossWin)} won / ${fmtUsd(s.grossLoss)} lost`} />
              <StatCard label="Expectancy" value={fmtSigned(s.expectancy)} tone={s.expectancy >= 0 ? 'pos' : 'neg'} sub="per settled trade" />
              <StatCard label="Avg win / loss" value={`${fmtUsd(s.avgWin)} / ${fmtUsd(s.avgLoss)}`} sub={`payoff ratio ${s.avgLoss > 0 ? (s.avgWin / s.avgLoss).toFixed(2) : '—'}`} />
              <StatCard label="Max drawdown" value={fmtUsd(s.maxDD)} tone="neg" sub={view.base > 0 ? `${((s.maxDD / view.base) * 100).toFixed(2)}% of base` : undefined} />
              <StatCard label="Streaks" value={`${s.curStreak >= 0 ? 'W' : 'L'}${Math.abs(s.curStreak)}`} tone={s.curStreak >= 0 ? 'pos' : 'neg'} sub={`best +${s.bestW}W · worst ${s.worstL}L`} />
              <StatCard label="Extremes" value={`${fmtSigned(s.largestWin)}`} tone="pos" sub={`worst single: ${fmtSigned(s.largestLoss)}`} />
            </div>

            <div className="f-panel" style={{ marginBottom: 14 }}>
              <div className="f-panel-head">
                <h2 className="f-panel-title"><span className="f-serif-grad">Equity Curve</span>
                  <span className="f-kicker" style={{ marginLeft: 6 }}>{TIERS.find(t => t.key === tier)?.label} · CUMULATIVE REALIZED P&L</span>
                </h2>
              </div>
              <canvas ref={curveRef} style={{ width: '100%', height: 190, display: 'block' }} />
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
                          <td className="num f-mono">{r.n}</td>
                          <td className="num f-mono">{pct(r.hit)}</td>
                          <td className="num f-mono">{r.pf === Infinity ? '∞' : r.pf.toFixed(2)}</td>
                          <td className={`num f-mono ${r.net >= 0 ? 'f-pos' : 'f-neg'}`} style={{ fontWeight: 700 }}>{fmtSigned(r.net)}</td>
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
                      <td><span className={`f-tag ${r.key === 'DEMO' ? 'azure' : 'dim'}`}>{r.key}</span></td>
                      <td className="num f-mono">{r.n}</td>
                      <td className="num f-mono">{r.wins} / {r.losses}</td>
                      <td className="num f-mono">{pct(r.hit)}</td>
                      <td className="num f-mono">{r.pf === Infinity ? '∞' : r.pf.toFixed(2)}</td>
                      <td className={`num f-mono ${r.expectancy >= 0 ? 'f-pos' : 'f-neg'}`}>{fmtSigned(r.expectancy)}</td>
                      <td className="num f-mono f-neg">{fmtUsd(r.maxDD)}</td>
                      <td className={`num f-mono ${r.net >= 0 ? 'f-pos' : 'f-neg'}`} style={{ fontWeight: 700 }}>{fmtSigned(r.net)}</td>
                      <td className={`num f-mono ${r.roce >= 0 ? 'f-pos' : 'f-neg'}`}>{r.roce >= 0 ? '+' : '−'}{Math.abs(r.roce).toFixed(2)}%</td>
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
              All figures derived from a single ledger snapshot ({view.subset.length.toLocaleString()} rows in view) — tier and view switches cost zero additional database reads. Hit REFRESH for a new snapshot.
            </div>
          </>
        )}
      </div>
    </div>
  );
}
