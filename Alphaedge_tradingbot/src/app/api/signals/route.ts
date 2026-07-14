import { NextRequest, NextResponse } from 'next/server';
import { dispatchSignal } from '@/lib/dispatcher';

export async function POST(req: NextRequest) {
  try {
    const payload = await req.json();
    const { botCode, direction, price, sl, tp, qty, source } = payload;

    const authHeader = req.headers.get('Authorization');
    const internalKey = process.env.INTERNAL_API_KEY || 'internal_secret_key';
    
    if (authHeader !== `Bearer ${internalKey}`) {
      return NextResponse.json({ error: 'Unauthorized internal signal source' }, { status: 401 });
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
      source: source || 'internal_breakout'
    });

    return NextResponse.json({
      success: true,
      ...result
    });
  } catch (error: any) {
    console.error('Internal signal endpoint error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}
