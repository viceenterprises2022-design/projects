import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest) {
  try {
    const res = await fetch('https://api.hyperliquid.xyz/info', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ type: 'allMids' }),
    });

    if (!res.ok) {
      throw new Error(`Hyperliquid API returned status code ${res.status}`);
    }

    const mids = await res.json();
    if (!mids || typeof mids !== 'object') {
      throw new Error('Invalid response received from Hyperliquid API');
    }

    const prices = {
      'BTC-PERP': mids.BTC ? parseFloat(mids.BTC) : null,
      'ETH-PERP': mids.ETH ? parseFloat(mids.ETH) : null,
      'XAU': mids.PAXG ? parseFloat(mids.PAXG) : null,
    };

    if (!prices['BTC-PERP'] || !prices['ETH-PERP'] || !prices['XAU']) {
      throw new Error('One or more target asset prices are missing in Hyperliquid feed');
    }

    return NextResponse.json({ success: true, prices });
  } catch (error: any) {
    console.error('Failed to fetch prices from Hyperliquid:', error);
    return NextResponse.json({ 
      success: false, 
      error: error.message || 'Failed to fetch prices from Hyperliquid'
    }, { status: 500 });
  }
}
