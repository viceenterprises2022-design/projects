import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { botInstances } from '@/db/schema';
import { eq } from 'drizzle-orm';
import { initDb } from '@/db/init';


export async function POST(req: NextRequest) {
  try {
    await initDb();
    const { botTemplateId, exchangeConnectionId, mode, riskCeilingPct, maxNotional } = await req.json();

    if (!botTemplateId || !exchangeConnectionId || !riskCeilingPct || !maxNotional) {
      return NextResponse.json({ error: 'Missing required configuration fields' }, { status: 400 });
    }

    const id = `inst_${Math.random().toString(36).substring(2, 11)}`;
    await db.insert(botInstances).values({
      id,
      userId: 'user_1',
      botTemplateId,
      exchangeConnectionId,
      mode: mode || 'paper',
      riskCeilingPct: parseFloat(riskCeilingPct),
      maxNotional: parseFloat(maxNotional),
      status: 'active'
    });

    return NextResponse.json({ success: true, instanceId: id });
  } catch (error: any) {
    console.error('Bot Instance POST error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}

export async function PUT(req: NextRequest) {
  try {
    await initDb();
    const { instanceId, status, riskCeilingPct, maxNotional } = await req.json();

    if (!instanceId) {
      return NextResponse.json({ error: 'Missing instanceId' }, { status: 400 });
    }

    const updateFields: any = {};
    if (status !== undefined) updateFields.status = status;
    if (riskCeilingPct !== undefined) updateFields.riskCeilingPct = parseFloat(riskCeilingPct);
    if (maxNotional !== undefined) updateFields.maxNotional = parseFloat(maxNotional);

    await db.update(botInstances)
      .set(updateFields)
      .where(eq(botInstances.id, instanceId));

    return NextResponse.json({ success: true });
  } catch (error: any) {
    console.error('Bot Instance PUT error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}
