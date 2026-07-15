import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { simulatorTrades } from '@/db/schema';
import { desc } from 'drizzle-orm';
import { initDb } from '@/db/init';

export async function GET(req: NextRequest) {
  try {
    await initDb();
    
    // Fetch latest 100 simulator trades ordered by creation time
    const history = await db
      .select()
      .from(simulatorTrades)
      .orderBy(desc(simulatorTrades.createdAt))
      .limit(100);

    return NextResponse.json({ history });
  } catch (error: any) {
    console.error('Predictions fetch error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    await initDb();
    
    const body = await req.json();
    const { roundId, asset, timestamp, strikePrice, expiryPrice, side, size, entryPrice, exitPrice, outcome, pnl } = body;

    if (!roundId || !asset || !side || !size || outcome === undefined || pnl === undefined) {
      return NextResponse.json({ error: 'Missing required parameters' }, { status: 400 });
    }

    const tradeId = `${asset}_${roundId}_${Date.now()}`;

    await db.insert(simulatorTrades).values({
      id: tradeId,
      roundId: Number(roundId),
      asset,
      timestamp: timestamp || new Date().toLocaleTimeString(),
      strikePrice: Number(strikePrice),
      expiryPrice: Number(expiryPrice),
      side,
      size: Number(size),
      entryPrice: Number(entryPrice),
      exitPrice: Number(exitPrice),
      outcome,
      pnl: Number(pnl),
      createdAt: Date.now()
    });

    return NextResponse.json({ success: true, id: tradeId }, { status: 201 });
  } catch (error: any) {
    console.error('Prediction save error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}

export async function DELETE(req: NextRequest) {
  try {
    await initDb();
    
    const adminSecret = req.headers.get('x-admin-token') || req.nextUrl.searchParams.get('secret');
    const expectedSecret = process.env.ADMIN_SECRET || 'alphaedge-admin-secret';

    if (!adminSecret || adminSecret !== expectedSecret) {
      return NextResponse.json({ error: 'Unauthorized: Admin access required' }, { status: 401 });
    }

    // Delete all simulator trades
    await db.delete(simulatorTrades);

    return NextResponse.json({ success: true, message: 'Simulator trades cleared successfully' });
  } catch (error: any) {
    console.error('Predictions deletion error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}
