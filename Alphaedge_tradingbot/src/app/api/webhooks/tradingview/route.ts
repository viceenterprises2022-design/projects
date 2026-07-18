import { NextRequest, NextResponse } from 'next/server';
import { dispatchSignal } from '@/lib/dispatcher';

export async function POST(req: NextRequest) {
  try {
    const payload = await req.json();
    const { passphrase, botCode, direction, price, sl, tp, qty } = payload;

    const secret = process.env.TRADINGVIEW_WEBHOOK_SECRET;
    if (!secret) {
      return NextResponse.json({ error: 'Webhook disabled: TRADINGVIEW_WEBHOOK_SECRET is not configured' }, { status: 403 });
    }
    if (passphrase !== secret) {
      return NextResponse.json({ error: 'Unauthorized passphrase' }, { status: 401 });
    }

    if (!botCode || !direction || !price) {
      return NextResponse.json({ error: 'Missing required fields: botCode, direction, price' }, { status: 400 });
    }

    const result = await dispatchSignal({
      botCode,
      direction,
      price: parseFloat(price),
      sl: sl ? parseFloat(sl) : null,
      tp: tp ? parseFloat(tp) : null,
      qty: qty ? parseFloat(qty) : null,
      source: 'tradingview'
    });

    return NextResponse.json({
      success: true,
      ...result
    });
  } catch (error: any) {
    console.error('Webhook error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}
