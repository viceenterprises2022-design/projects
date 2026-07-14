import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { botTemplates, botInstances, exchangeConnections, signals, orders, riskEvents } from '@/db/schema';
import { eq, and } from 'drizzle-orm';
import { validateRisk } from '@/lib/risk';
import { placeOrder } from '@/lib/hyperliquid';
import { decrypt } from '@/lib/encryption';
import { appendToLedger } from '@/lib/ledger';

export async function POST(req: NextRequest) {
  try {
    const payload = await req.json();
    const { passphrase, botCode, direction, price, sl, tp, qty: payloadQty } = payload;

    // 1. Authenticate webhook secret
    const secret = process.env.TRADINGVIEW_WEBHOOK_SECRET || 'supersecret';
    if (passphrase !== secret) {
      return NextResponse.json({ error: 'Unauthorized passphrase' }, { status: 401 });
    }

    if (!botCode || !direction || !price) {
      return NextResponse.json({ error: 'Missing required fields: botCode, direction, price' }, { status: 400 });
    }

    // 2. Fetch bot template
    const templates = await db.select().from(botTemplates).where(eq(botTemplates.code, botCode));
    if (templates.length === 0) {
      return NextResponse.json({ error: `Bot template ${botCode} not found` }, { status: 404 });
    }
    const template = templates[0];

    // 3. Record signal
    const signalId = `sig_${Math.random().toString(36).substring(2, 11)}`;
    const timestamp = Date.now();
    await db.insert(signals).values({
      id: signalId,
      botTemplateId: template.id,
      assetClass: template.assetClass,
      direction,
      entryPrice: parseFloat(price),
      sl: sl ? parseFloat(sl) : null,
      tp: tp ? parseFloat(tp) : null,
      timestamp
    });

    // Log signal to hash-chained ledger
    await appendToLedger('signal', signalId, {
      botCode,
      assetClass: template.assetClass,
      direction,
      price: parseFloat(price),
      sl: sl ? parseFloat(sl) : null,
      tp: tp ? parseFloat(tp) : null
    });

    // 4. Fetch all active bot instances subscribed to this template
    const activeInstances = await db.select()
      .from(botInstances)
      .where(
        and(
          eq(botInstances.botTemplateId, template.id),
          eq(botInstances.status, 'active')
        )
      );

    const executions = [];

    for (const instance of activeInstances) {
      const entryPx = parseFloat(price);
      // Determine qty: if provided, use it, otherwise default based on maxNotional
      const qty = payloadQty ? parseFloat(payloadQty) : (instance.maxNotional / entryPx);
      
      if (qty <= 0) {
        const detail = `Calculated quantity ${qty} is invalid. Max notional: ${instance.maxNotional}`;
        await db.insert(riskEvents).values({
          id: `rsk_${Math.random().toString(36).substring(2, 11)}`,
          botInstanceId: instance.id,
          type: 'ceiling_breach',
          detail,
          timestamp: Date.now()
        });
        await appendToLedger('risk_event', instance.id, {
          botInstanceId: instance.id,
          type: 'ceiling_breach',
          detail
        });
        executions.push({ instanceId: instance.id, status: 'rejected', reason: detail });
        continue;
      }

      // Run Risk Engine
      const riskCheck = await validateRisk(instance.id, qty, entryPx);
      if (!riskCheck.allowed) {
        const detail = riskCheck.reason || 'Risk check failed';
        
        // Log risk event
        const rskId = `rsk_${Math.random().toString(36).substring(2, 11)}`;
        await db.insert(riskEvents).values({
          id: rskId,
          botInstanceId: instance.id,
          type: 'ceiling_breach',
          detail,
          timestamp: Date.now()
        });
        
        await appendToLedger('risk_event', rskId, {
          botInstanceId: instance.id,
          type: 'ceiling_breach',
          detail
        });

        executions.push({ instanceId: instance.id, status: 'rejected', reason: detail });
        continue;
      }

      // Load connection and decrypt API keys
      const connections = await db.select()
        .from(exchangeConnections)
        .where(eq(exchangeConnections.id, instance.exchangeConnectionId));
      
      if (connections.length === 0) {
        executions.push({ instanceId: instance.id, status: 'failed', reason: 'Exchange connection missing' });
        continue;
      }
      const conn = connections[0];

      let apiKey = '';
      try {
        apiKey = decrypt(conn.encryptedApiKey, conn.encryptionIv, conn.encryptionTag);
      } catch (err) {
        executions.push({ instanceId: instance.id, status: 'failed', reason: 'Decryption failed' });
        continue;
      }

      // 5. Execute Order on Hyperliquid
      const side = direction === 'LONG' ? 'buy' : direction === 'SHORT' ? 'sell' : 'sell'; // Simple mapping
      const orderId = `ord_${Math.random().toString(36).substring(2, 11)}`;
      
      // Store draft order
      await db.insert(orders).values({
        id: orderId,
        botInstanceId: instance.id,
        signalId,
        side,
        qty,
        price: entryPx,
        status: 'submitted',
        submittedAt: Date.now()
      });

      const tradeResult = await placeOrder(
        apiKey,
        instance.mode as 'paper' | 'live',
        template.assetClass,
        side,
        qty,
        entryPx
      );

      if (tradeResult.success) {
        // Update order status
        await db.update(orders)
          .set({
            status: 'filled',
            exchangeOrderId: tradeResult.orderId || null,
            filledAt: Date.now()
          })
          .where(eq(orders.id, orderId));

        // Log fill to ledger
        await appendToLedger('fill', orderId, {
          botInstanceId: instance.id,
          signalId,
          orderId,
          exchangeOrderId: tradeResult.orderId,
          qty,
          price: entryPx,
          side
        });

        executions.push({ instanceId: instance.id, status: 'filled', orderId: tradeResult.orderId });
      } else {
        // Update order status as rejected
        await db.update(orders)
          .set({
            status: 'rejected',
            filledAt: Date.now()
          })
          .where(eq(orders.id, orderId));

        await appendToLedger('risk_event', orderId, {
          botInstanceId: instance.id,
          orderId,
          error: tradeResult.error || 'Execution rejected'
        });

        executions.push({ instanceId: instance.id, status: 'failed', reason: tradeResult.error });
      }
    }

    return NextResponse.json({
      success: true,
      signalId,
      processedInstances: activeInstances.length,
      executions
    });
  } catch (error: any) {
    console.error('Webhook error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}
