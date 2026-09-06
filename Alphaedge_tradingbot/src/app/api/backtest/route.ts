import { NextRequest, NextResponse } from 'next/server';
import { requireOwner } from '@/lib/authz';
import {
  fetchCandles, fetchFunding, walkForward, defaultGrid, stats, runS1,
  roundTripBps, intervalMs, BASE_COSTS, type CostModel,
} from '@/lib/backtest';

export const dynamic = 'force-dynamic';
export const maxDuration = 300;

// ---------------------------------------------------------------------------
// Owner-only strategy evaluation.
//
//   /api/backtest?coin=BTC&interval=15m&days=120&folds=4
//
// Reports OUT-OF-SAMPLE walk-forward results only, plus a sensitivity block,
// because a single in-sample number is exactly how a strategy that does not
// work gets deployed.
// ---------------------------------------------------------------------------

const COINS: Record<string, string> = { BTC: 'BTC', ETH: 'ETH', XAU: 'PAXG', PAXG: 'PAXG', GOLD: 'PAXG' };

export async function GET(req: NextRequest) {
  const denied = await requireOwner();
  if (denied) return NextResponse.json({ error: denied }, { status: 403 });

  try {
    const q = req.nextUrl.searchParams;
    const coinKey = (q.get('coin') || 'BTC').toUpperCase();
    const coin = COINS[coinKey];
    if (!coin) {
      return NextResponse.json({ error: `Unknown coin "${coinKey}". Use BTC, ETH or GOLD.` }, { status: 400 });
    }

    const interval = q.get('interval') || '15m';
    const days = Math.min(365, Math.max(7, parseInt(q.get('days') || '120', 10)));
    const folds = Math.min(8, Math.max(2, parseInt(q.get('folds') || '4', 10)));

    const end = Date.now();
    const start = end - days * 86_400_000;

    const [candles, funding] = await Promise.all([
      fetchCandles(coin, interval, start, end),
      fetchFunding(coin, start, end),
    ]);

    if (candles.length < 200) {
      return NextResponse.json({
        error: `Only ${candles.length} candles returned for ${coin} ${interval} — too few to evaluate.`,
      }, { status: 422 });
    }

    const barsPerYear = (365 * 86_400_000) / intervalMs(interval);
    const grid = defaultGrid();
    const result = walkForward(candles, funding, grid, BASE_COSTS, folds, barsPerYear);

    // Sensitivity: the doc requires fill rate and slippage each to move, and a
    // candidate that only works at optimistic assumptions is not a candidate.
    const variants: Array<{ label: string; costs: CostModel }> = [
      { label: 'base (65% maker fill, 1bp slip)', costs: BASE_COSTS },
      { label: 'pessimistic (0% maker fill, 2bp slip)', costs: { ...BASE_COSTS, makerFillRate: 0, slippageBps: 2 } },
      { label: 'optimistic (100% maker fill, 0bp slip)', costs: { ...BASE_COSTS, makerFillRate: 1, slippageBps: 0 } },
      { label: 'zero cost (reference only)', costs: { makerBps: 0, takerBps: 0, makerFillRate: 1, slippageBps: 0 } },
    ];

    const best = result.folds.length
      ? result.folds[result.folds.length - 1].chosen
      : { lookback: 24, hold: 8, stopAtr: 2.5 };

    const sensitivity = variants.map(v => ({
      label: v.label,
      roundTripBps: +roundTripBps(v.costs).toFixed(2),
      // Scored on the final test window with the params walk-forward last chose.
      stats: stats(runS1(candles.slice(Math.floor(candles.length / 2)), funding, best, v.costs), barsPerYear),
    }));

    return NextResponse.json({
      success: true,
      spec: {
        coin, interval, days, folds,
        candles: candles.length,
        fundingPoints: funding.length,
        from: new Date(candles[0].t).toISOString(),
        to: new Date(candles[candles.length - 1].t).toISOString(),
        strategy: 'S1 breakout continuation (Donchian), fills at next bar open',
        gridSize: result.gridSize,
      },
      outOfSample: result.oos,
      folds: result.folds,
      sensitivity,
      readMe: [
        'outOfSample is the only number that means anything — parameters were fitted on each',
        'train window and scored on the window that follows, never on themselves.',
        'A positive "zero cost" row with a negative "base" row means the signal exists but does',
        'not clear the fee floor at this horizon; lengthen the horizon rather than tune the grid.',
        'Judge trade count before Sharpe: a high ratio on a few dozen trades is noise.',
      ],
    });
  } catch (err: any) {
    return NextResponse.json({ error: err?.message || 'Backtest failed' }, { status: 500 });
  }
}
