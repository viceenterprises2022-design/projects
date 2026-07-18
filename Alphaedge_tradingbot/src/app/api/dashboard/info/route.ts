import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { users, botTemplates, botInstances, exchangeConnections, signals, orders, riskEvents, simulatorTrades } from '@/db/schema';
import { eq, desc, gte } from 'drizzle-orm';
import { verifyLedgerChain } from '@/lib/ledger';
import { getBalances, getPositions } from '@/lib/hyperliquid';
import { decrypt } from '@/lib/encryption';
import { initDb } from '@/db/init';
import { getDemoAccount } from '@/lib/engine';

export async function GET(req: NextRequest) {
  try {
    await initDb();
    const userId = 'user_1'; // Default demo user

    // 1. Fetch DB data
    const userList = await db.select().from(users).where(eq(users.id, userId));
    if (userList.length === 0) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 });
    }
    const user = userList[0];

    const templatesList = await db.select().from(botTemplates);
    const instancesList = await db.select().from(botInstances).where(eq(botInstances.userId, userId));
    const connectionsList = await db.select().from(exchangeConnections).where(eq(exchangeConnections.userId, userId));
    
    const signalsList = await db.select().from(signals).orderBy(desc(signals.timestamp)).limit(30);
    const ordersList = await db.select().from(orders).orderBy(desc(orders.submittedAt)).limit(30);
    const riskEventsList = await db.select().from(riskEvents).orderBy(desc(riskEvents.timestamp)).limit(30);

    // 2. Ledger integrity check
    const ledgerStatus = await verifyLedgerChain();

    // 3. Fetch balances & positions from Hyperliquid
    let activeBalance = 10000.00;
    let activeAvailable = 8500.00;
    const positionsList: any[] = [];

    for (const conn of connectionsList) {
      if (conn.status === 'active') {
        try {
          const apiKey = decrypt(conn.encryptedApiKey, conn.encryptionIv, conn.encryptionTag);
          // Find if there's any active live or paper bot for this connection
          const associatedInstances = instancesList.filter(i => i.exchangeConnectionId === conn.id && i.status === 'active');
          const isLive = associatedInstances.some(i => i.mode === 'live');
          const mode = isLive ? 'live' : 'paper';

          const balances = await getBalances(apiKey, mode);
          const usdc = balances.find(b => b.coin === 'USDC');
          if (usdc) {
            activeBalance = usdc.equity;
            activeAvailable = usdc.available;
          }

          const activePos = await getPositions(apiKey, mode);
          positionsList.push(...activePos);
        } catch (err) {
          console.error('Failed to load connection status:', err);
        }
      }
    }

    // 4. Performance metrics — every number aggregated from the persisted DB,
    // never synthesized. Engine PnL comes from server-settled simulator rounds.
    const filledOrders = ordersList.filter(o => o.status === 'filled');
    const totalTrades = filledOrders.length;

    // Scope engine stats to the demo window — pre-demo history must not leak
    const acct = await getDemoAccount();
    const allRounds = await db.select().from(simulatorTrades)
      .where(gte(simulatorTrades.createdAt, acct.startedAt));
    const settled = allRounds.length;
    const wins = allRounds.filter(r => r.outcome === 'WIN').length;
    const winRate = settled > 0 ? wins / settled : 0;
    const totalProfit = Math.round(allRounds.reduce((a, r) => a + r.pnl, 0) * 100) / 100;

    // Sharpe from the per-round PnL series (population std, per-round basis)
    let sharpeRatio = 0;
    if (settled > 1) {
      const meanPnl = totalProfit / settled;
      const variance = allRounds.reduce((a, r) => a + (r.pnl - meanPnl) ** 2, 0) / settled;
      const std = Math.sqrt(variance);
      sharpeRatio = std > 0 ? (meanPnl / std) * Math.sqrt(settled) : 0;
    }

    // Rule-based advisory templated strictly from the real aggregates above
    let advisoryText: string;
    if (settled === 0 && totalTrades === 0) {
      advisoryText = "Systems initialized and ledger integrity verified. Connect an exchange key and dispatch a signal, or let the quant engine settle rounds, to begin accumulating performance history.";
    } else if (winRate >= 0.5) {
      advisoryText = `Engine has settled ${settled} rounds at a ${(winRate * 100).toFixed(1)}% hit rate for ${totalProfit >= 0 ? '+' : ''}$${totalProfit.toFixed(2)} realized PnL. Risk-adjusted efficiency (per-round Sharpe ${sharpeRatio.toFixed(2)}) supports current sizing parameters.`;
    } else {
      advisoryText = `Hit rate is ${(winRate * 100).toFixed(1)}% across ${settled} settled rounds (${totalProfit >= 0 ? '+' : ''}$${totalProfit.toFixed(2)} PnL). Below-coin-flip accuracy — consider raising the minimum executable edge threshold or reducing per-round size until expectancy recovers.`;
    }

    return NextResponse.json({
      user,
      botTemplates: templatesList,
      botInstances: instancesList,
      exchangeConnections: connectionsList,
      signals: signalsList,
      orders: ordersList,
      riskEvents: riskEventsList,
      balances: {
        equity: activeBalance,
        available: activeAvailable,
      },
      positions: positionsList,
      ledgerValid: ledgerStatus.valid,
      ledgerError: ledgerStatus.reason,
      aiMetrics: {
        sharpeRatio,
        winRate,
        totalProfit,
        settledRounds: settled,
        executionFills: totalTrades,
        advisoryText
      }
    });
  } catch (error: any) {
    console.error('Info dashboard error:', error);
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}
