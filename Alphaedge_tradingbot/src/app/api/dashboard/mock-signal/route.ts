import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const { botCode, direction, price } = await req.json();

    const webhookSecret = process.env.TRADINGVIEW_WEBHOOK_SECRET || 'supersecret';
    
    // Construct request to our own TradingView webhook endpoint
    const targetUrl = new URL('/api/webhooks/tradingview', req.url).toString();
    const response = await fetch(targetUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        passphrase: webhookSecret,
        botCode,
        direction,
        price,
        sl: (parseFloat(price) * (direction === 'LONG' ? 0.98 : 1.02)).toFixed(2),
        tp: (parseFloat(price) * (direction === 'LONG' ? 1.05 : 0.95)).toFixed(2)
      })
    });

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error: any) {
    console.error('Mock signal error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}
