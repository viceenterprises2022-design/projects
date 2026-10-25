// Server-side strategy analytics.
//
// Why this exists: the analytics route used to ship raw trades to the browser
// with `ORDER BY created_at ASC LIMIT 8000`. That returns the OLDEST 8,000 rows,
// so once the demo passed trade #8,000 the page froze while the ledger kept
// moving. Raising the cap only postpones the same failure and keeps payload
// size proportional to history.
//
// Instead, every trade in the demo window is streamed through one exact,
// single-pass accumulator per tier (0 = all tiers, 1..4). Scalar stats,
// streaks and drawdown are exact over the full sequence. Only the equity
// curve is decimated, and decimation never touches the stats.

export type TradeRow = {
  id: string;
  createdAt: number;
  level: number;
  asset: string;
  side: string;
  outcome: string;
  pnl: number;
  size: number;
  entryPrice: number;
};

export type Stats = {
  n: number; wins: number; losses: number; hit: number;
  net: number; grossWin: number; grossLoss: number; volume: number;
  pf: number | null; // null encodes Infinity (JSON has no Infinity)
  expectancy: number; avgWin: number; avgLoss: number;
  largestWin: number; largestLoss: number;
  curStreak: number; bestW: number; worstL: number; maxDD: number;
};

export type CurvePoint = {
  i: number;   // 1-based trade index within the tier
  eq: number;  // cumulative realized P&L after that trade
  t: { createdAt: number; asset: string; side: string; outcome: string; pnl: number };
};

export type TierView = {
  stats: Stats;
  byAsset: Array<{ key: string } & Stats>;
  bySide: Array<{ key: string } & Stats>;
  hours: Array<{ h: number; n: number; wins: number }>;
  curve: CurvePoint[];
  curveSampled: boolean;
};

// Target point budget per curve. The canvas is ~1,900px wide at most, so more
// points than this add payload without adding visible detail.
const CURVE_BUDGET = 1000;

class StatAcc {
  n = 0; wins = 0; grossWin = 0; grossLoss = 0; volume = 0;
  largestWin = 0; largestLoss = 0;
  run = 0; last: 'W' | 'L' | '' = ''; bestW = 0; worstL = 0;
  equity = 0; peak = 0; maxDD = 0;

  push(t: TradeRow): void {
    this.n++;
    this.volume += t.size * t.entryPrice;
    const win = t.outcome === 'WIN';
    if (win) { this.wins++; this.grossWin += t.pnl; this.largestWin = Math.max(this.largestWin, t.pnl); }
    else { this.grossLoss += -t.pnl; this.largestLoss = Math.min(this.largestLoss, t.pnl); }
    const o = win ? 'W' : 'L';
    this.run = o === this.last ? this.run + 1 : 1;
    this.last = o;
    if (o === 'W') this.bestW = Math.max(this.bestW, this.run);
    else this.worstL = Math.max(this.worstL, this.run);
    this.equity += t.pnl;
    this.peak = Math.max(this.peak, this.equity);
    this.maxDD = Math.max(this.maxDD, this.peak - this.equity);
  }

  result(): Stats {
    const { n, wins, grossWin, grossLoss } = this;
    const losses = n - wins;
    const net = grossWin - grossLoss;
    return {
      n, wins, losses,
      hit: n > 0 ? (wins / n) * 100 : 0,
      net, grossWin, grossLoss, volume: this.volume,
      pf: grossLoss > 0 ? grossWin / grossLoss : (grossWin > 0 ? null : 0),
      expectancy: n > 0 ? net / n : 0,
      avgWin: wins > 0 ? grossWin / wins : 0,
      avgLoss: losses > 0 ? grossLoss / losses : 0,
      largestWin: this.largestWin, largestLoss: this.largestLoss,
      curStreak: this.run * (this.last === 'W' ? 1 : -1),
      bestW: this.bestW, worstL: this.worstL, maxDD: this.maxDD,
    };
  }
}

// Streaming stride decimation: keep every `stride`-th point; when the buffer
// reaches 2x budget, drop every other point and double the stride. Memory is
// O(budget) and the row count does not need to be known in advance. The final
// point is always appended at finish so the curve ends on the true equity.
class CurveAcc {
  pts: CurvePoint[] = [];
  stride = 1;
  lastPt: CurvePoint | null = null;

  push(p: CurvePoint): void {
    this.lastPt = p;
    if (p.i % this.stride !== 0) return;
    this.pts.push(p);
    if (this.pts.length >= CURVE_BUDGET * 2) {
      this.pts = this.pts.filter((_, k) => k % 2 === 1);
      this.stride *= 2;
    }
  }

  result(): { curve: CurvePoint[]; sampled: boolean } {
    const out = this.pts.slice();
    if (this.lastPt && out[out.length - 1]?.i !== this.lastPt.i) out.push(this.lastPt);
    return { curve: out, sampled: this.stride > 1 };
  }
}

class TierAcc {
  all = new StatAcc();
  asset = new Map<string, StatAcc>();
  side = new Map<string, StatAcc>();
  hours = Array.from({ length: 24 }, (_, h) => ({ h, n: 0, wins: 0 }));
  curve = new CurveAcc();

  push(t: TradeRow): void {
    this.all.push(t);
    group(this.asset, t.asset).push(t);
    group(this.side, t.side).push(t);
    const hb = this.hours[new Date(t.createdAt).getUTCHours()];
    hb.n++;
    if (t.outcome === 'WIN') hb.wins++;
    this.curve.push({
      i: this.all.n,
      eq: this.all.equity,
      t: { createdAt: t.createdAt, asset: t.asset, side: t.side, outcome: t.outcome, pnl: t.pnl },
    });
  }

  result(): TierView {
    const { curve, sampled } = this.curve.result();
    return {
      stats: this.all.result(),
      byAsset: groups(this.asset),
      bySide: groups(this.side),
      hours: this.hours,
      curve,
      curveSampled: sampled,
    };
  }
}

function group(m: Map<string, StatAcc>, k: string): StatAcc {
  let a = m.get(k);
  if (!a) { a = new StatAcc(); m.set(k, a); }
  return a;
}

function groups(m: Map<string, StatAcc>) {
  return [...m.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, acc]) => ({ key, ...acc.result() }));
}

export const ANALYTICS_TIERS = [0, 1, 2, 3, 4] as const;

export class AnalyticsAccumulator {
  private tiers = new Map<number, TierAcc>(ANALYTICS_TIERS.map(l => [l, new TierAcc()]));
  rows = 0;

  // Rows MUST arrive in chronological order (created_at, id). Streaks, drawdown
  // and the curve are sequence-dependent.
  push(t: TradeRow): void {
    this.rows++;
    this.tiers.get(0)!.push(t);
    // Legacy level-0 rows count only in ALL. Guard explicitly: key 0 IS the
    // ALL bucket, so a bare tiers.get(t.level) would double-count them.
    if (t.level !== 0) this.tiers.get(t.level)?.push(t);
  }

  result(): Record<string, TierView> {
    return Object.fromEntries([...this.tiers.entries()].map(([l, acc]) => [String(l), acc.result()]));
  }
}
