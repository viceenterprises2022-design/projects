import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

// XAU exposure proxied via PAXG (tokenized gold) on Hyperliquid.
const ASSET_MAP: Record<string, string> = {
  'BTC-PERP': 'BTC',
  'ETH-PERP': 'ETH',
  'XAU': 'PAXG',
};

interface Candle { t: number; o: number; h: number; l: number; c: number; v: number }

// Return horizons derived from a single 5m candle series (bars back per horizon)
const HORIZONS: Array<{ label: string; bars: number }> = [
  { label: '5M', bars: 1 },
  { label: '15M', bars: 3 },
  { label: '30M', bars: 6 },
  { label: '1H', bars: 12 },
  { label: '4H', bars: 48 },
  { label: '24H', bars: 288 },
];

// Module-level cache: Hyperliquid candle history changes slowly relative to poll rate.
let cache: { ts: number; payload: any } | null = null;
const CACHE_MS = 60_000;

async function fetchCandles(coin: string, endTime: number): Promise<Candle[]> {
  const res = await fetch('https://api.hyperliquid.xyz/info', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      type: 'candleSnapshot',
      req: { coin, interval: '5m', startTime: endTime - 25 * 60 * 60 * 1000, endTime },
    }),
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`candleSnapshot ${coin} returned ${res.status}`);
  const raw = await res.json();
  if (!Array.isArray(raw)) throw new Error(`Invalid candle payload for ${coin}`);
  return raw.map((k: any) => ({
    t: k.t,
    o: parseFloat(k.o),
    h: parseFloat(k.h),
    l: parseFloat(k.l),
    c: parseFloat(k.c),
    v: parseFloat(k.v),
  })).filter(k => Number.isFinite(k.c));
}

export async function GET() {
  try {
    if (cache && Date.now() - cache.ts < CACHE_MS) {
      return NextResponse.json({ ...cache.payload, cached: true });
    }

    const endTime = Date.now();
    const entries = await Promise.all(
      Object.entries(ASSET_MAP).map(async ([label, coin]) => {
        const candles = await fetchCandles(coin, endTime);
        const last = candles[candles.length - 1];

        // Realized returns per horizon from actual closes
        const returns: Record<string, number | null> = {};
        for (const { label: hLabel, bars } of HORIZONS) {
          const ref = candles[candles.length - 1 - bars];
          returns[hLabel] = ref && last ? ((last.c - ref.c) / ref.c) * 100 : null;
        }

        // Annualized realized vol from 5m log returns over the last 24h
        const closes = candles.map(k => k.c);
        const logRets: number[] = [];
        for (let i = 1; i < closes.length; i++) logRets.push(Math.log(closes[i] / closes[i - 1]));
        const mean = logRets.reduce((a, b) => a + b, 0) / Math.max(logRets.length, 1);
        const variance = logRets.reduce((a, b) => a + (b - mean) ** 2, 0) / Math.max(logRets.length - 1, 1);
        const periodsPerYear = (365 * 24 * 60) / 5;
        const realizedVolPct = Math.sqrt(variance * periodsPerYear) * 100;

        return [label, {
          returns,
          realizedVolPct: Number.isFinite(realizedVolPct) ? realizedVolPct : null,
          candles: candles.slice(-72), // last 6 hours of 5m bars for the pattern strip
        }];
      })
    );

    const payload = {
      success: true,
      markets: Object.fromEntries(entries),
      horizons: HORIZONS.map(h => h.label),
      source: 'hyperliquid:candleSnapshot:5m',
      ts: endTime,
    };
    cache = { ts: Date.now(), payload };
    return NextResponse.json(payload);
  } catch (error: any) {
    console.error('Failed to fetch market candles from Hyperliquid:', error);
    return NextResponse.json({
      success: false,
      error: error.message || 'Failed to fetch market history',
    }, { status: 500 });
  }
}
