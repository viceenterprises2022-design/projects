import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

// Assets served to the desk. XAU exposure is proxied via PAXG (tokenized gold) on Hyperliquid.
const ASSET_MAP: Record<string, string> = {
  'BTC-PERP': 'BTC',
  'ETH-PERP': 'ETH',
  'XAU': 'PAXG',
};

export interface AssetContext {
  mark: number;
  prevDay: number;
  change24hPct: number;
  fundingRate: number;
  openInterest: number;
  dayVolumeUsd: number;
  oracle: number;
}

export async function GET() {
  try {
    const res = await fetch('https://api.hyperliquid.xyz/info', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'metaAndAssetCtxs' }),
      cache: 'no-store',
    });

    if (!res.ok) {
      throw new Error(`Hyperliquid API returned status code ${res.status}`);
    }

    const payload = await res.json();
    if (!Array.isArray(payload) || payload.length < 2) {
      throw new Error('Invalid metaAndAssetCtxs response from Hyperliquid');
    }

    const [meta, ctxs] = payload;
    const universe: Array<{ name: string }> = meta?.universe || [];

    const indexByCoin: Record<string, number> = {};
    universe.forEach((u, i) => { indexByCoin[u.name] = i; });

    const prices: Record<string, number> = {};
    const contexts: Record<string, AssetContext> = {};

    for (const [label, coin] of Object.entries(ASSET_MAP)) {
      const idx = indexByCoin[coin];
      const ctx = idx !== undefined ? ctxs[idx] : undefined;
      if (!ctx) {
        throw new Error(`Asset ${coin} missing from Hyperliquid feed`);
      }
      const mark = parseFloat(ctx.markPx);
      const prevDay = parseFloat(ctx.prevDayPx);
      if (!Number.isFinite(mark) || mark <= 0) {
        throw new Error(`Invalid mark price for ${coin}`);
      }
      prices[label] = mark;
      contexts[label] = {
        mark,
        prevDay,
        change24hPct: Number.isFinite(prevDay) && prevDay > 0 ? ((mark - prevDay) / prevDay) * 100 : 0,
        fundingRate: parseFloat(ctx.funding) || 0,
        openInterest: parseFloat(ctx.openInterest) || 0,
        dayVolumeUsd: parseFloat(ctx.dayNtlVlm) || 0,
        oracle: parseFloat(ctx.oraclePx) || mark,
      };
    }

    return NextResponse.json({
      success: true,
      prices,
      contexts,
      source: 'hyperliquid:metaAndAssetCtxs',
      ts: Date.now(),
    });
  } catch (error: any) {
    console.error('Failed to fetch prices from Hyperliquid:', error);
    return NextResponse.json({
      success: false,
      error: error.message || 'Failed to fetch prices from Hyperliquid',
    }, { status: 500 });
  }
}
