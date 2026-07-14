import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { exchangeConnections } from '@/db/schema';
import { encrypt } from '@/lib/encryption';
import { initDb } from '@/db/init';

export async function POST(req: NextRequest) {
  try {
    await initDb();
    const { exchange, apiKey } = await req.json();

    if (!exchange || !apiKey) {
      return NextResponse.json({ error: 'Missing exchange or apiKey fields' }, { status: 400 });
    }

    // Envelope encrypt API key
    const encrypted = encrypt(apiKey);

    const id = `conn_${Math.random().toString(36).substring(2, 11)}`;
    await db.insert(exchangeConnections).values({
      id,
      userId: 'user_1', // Demo user
      exchange,
      encryptedApiKey: encrypted.encrypted,
      encryptionIv: encrypted.iv,
      encryptionTag: encrypted.tag,
      status: 'active',
      lastVerifiedAt: Date.now()
    });

    return NextResponse.json({ success: true, connectionId: id });
  } catch (error: any) {
    console.error('Connection API error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}
