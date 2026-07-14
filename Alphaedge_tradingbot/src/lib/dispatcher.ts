import { db } from '../db';
import { botTemplates, botInstances, exchangeConnections, signals, orders, riskEvents } from '../db/schema';
import { eq, and } from 'drizzle-orm';
import { validateRisk } from './risk';
import { placeOrder } from './hyperliquid';
import { decrypt } from './encryption';
import { appendToLedger } from './ledger';
import { initDb } from '../db/init';

export interface SignalInput {
  botCode: string;
  direction: 'LONG' | 'SHORT' | 'EXIT';
  price: number;
  sl?: number | null;
  tp?: number | null;
  qty?: number | null;
  source: string; // 'tradingview' | 'internal_breakout' | 'manual'
}

export async function dispatchSignal(input: SignalInput) {
  await initDb();
  const { botCode, direction, price, sl, tp, qty: payloadQty, source } = input;

  const templates = await db.select().from(botTemplates).where(eq(botTemplates.code, botCode));
  if (templates.length === 0) {
    throw new Error(`Bot template ${botCode} not found`);
  }
  const template = templates[0];

  const signalId = `sig_${Math.random().toString(36).substring(2, 11)}`;
  const timestamp = Date.now();
  
  await db.insert(signals).values({
    id: signalId,
    botTemplateId: template.id,
    assetClass: template.assetClass,
    direction,
    entryPrice: price,
    sl: sl || null,
    tp: tp || null,
    timestamp
  });

  await appendToLedger('signal', signalId, {
    botCode,
    assetClass: template.assetClass,
    direction,
    price,
    sl,
    tp,
    source
  });

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
    const qty = payloadQty || (instance.maxNotional / price);
    
    if (qty <= 0) {
      const detail = `Invalid quantity ${qty}. Max notional: ${instance.maxNotional}`;
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

    const riskCheck = await validateRisk(instance.id, qty, price);
    if (!riskCheck.allowed) {
      const detail = riskCheck.reason || 'Risk check failed';
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

    const connections = await db.select().from(exchangeConnections).where(eq(exchangeConnections.id, instance.exchangeConnectionId));
    if (connections.length === 0) {
      executions.push({ instanceId: instance.id, status: 'failed', reason: 'Connection missing' });
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

    const side = direction === 'LONG' ? 'buy' : direction === 'SHORT' ? 'sell' : 'sell';
    const orderId = `ord_${Math.random().toString(36).substring(2, 11)}`;
    
    await db.insert(orders).values({
      id: orderId,
      botInstanceId: instance.id,
      signalId,
      side,
      qty,
      price,
      status: 'submitted',
      submittedAt: Date.now()
    });

    const tradeResult = await placeOrder(
      apiKey,
      instance.mode as 'paper' | 'live',
      template.assetClass,
      side,
      qty,
      price
    );

    if (tradeResult.success) {
      await db.update(orders).set({
        status: 'filled',
        exchangeOrderId: tradeResult.orderId || null,
        filledAt: Date.now()
      }).where(eq(orders.id, orderId));

      await appendToLedger('fill', orderId, {
        botInstanceId: instance.id,
        signalId,
        orderId,
        exchangeOrderId: tradeResult.orderId,
        qty,
        price,
        side
      });

      executions.push({ instanceId: instance.id, status: 'filled', orderId: tradeResult.orderId });
    } else {
      await db.update(orders).set({
        status: 'rejected',
        filledAt: Date.now()
      }).where(eq(orders.id, orderId));

      await appendToLedger('risk_event', orderId, {
        botInstanceId: instance.id,
        orderId,
        error: tradeResult.error || 'Execution rejected'
      });

      executions.push({ instanceId: instance.id, status: 'failed', reason: tradeResult.error });
    }
  }

  return {
    signalId,
    processedInstances: activeInstances.length,
    executions
  };
}
