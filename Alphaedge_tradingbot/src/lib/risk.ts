import { db } from '../db';
import { botInstances, botTemplates, exchangeConnections } from '../db/schema';
import { eq } from 'drizzle-orm';
import { decrypt } from './encryption';
import { getBalances } from './hyperliquid';

export interface RiskCheckResult {
  allowed: boolean;
  reason?: string;
  maxAllowedNotional?: number;
}

export async function validateRisk(
  instanceId: string,
  qty: number,
  price: number
): Promise<RiskCheckResult> {
  const instances = await db.select().from(botInstances).where(eq(botInstances.id, instanceId));
  if (instances.length === 0) {
    return { allowed: false, reason: 'Bot instance not found' };
  }
  const inst = instances[0];

  if (inst.status !== 'active') {
    return { allowed: false, reason: `Bot instance status is ${inst.status} (must be active)` };
  }

  const templates = await db.select().from(botTemplates).where(eq(botTemplates.id, inst.botTemplateId));
  if (templates.length === 0) {
    return { allowed: false, reason: 'Bot template not found' };
  }
  const tmpl = templates[0];
  
  if (tmpl.status !== 'live' && inst.mode === 'live') {
    return { allowed: false, reason: `Bot template ${tmpl.code} is in assay (${tmpl.status}) and cannot execute live trades` };
  }

  const orderNotional = qty * price;
  if (orderNotional > inst.maxNotional) {
    return { 
      allowed: false, 
      reason: `Order notional $${orderNotional.toFixed(2)} exceeds instance maximum notional limit of $${inst.maxNotional.toFixed(2)}` 
    };
  }

  const connections = await db.select().from(exchangeConnections).where(eq(exchangeConnections.id, inst.exchangeConnectionId));
  if (connections.length === 0) {
    return { allowed: false, reason: 'Exchange connection not found' };
  }
  const conn = connections[0];

  let decryptedApiKey = 'placeholder';
  try {
    decryptedApiKey = decrypt(conn.encryptedApiKey, conn.encryptionIv, conn.encryptionTag);
  } catch (err) {
    return { allowed: false, reason: 'Failed to decrypt exchange credentials' };
  }

  const balances = await getBalances(decryptedApiKey, inst.mode as 'paper' | 'live');
  const usdcBal = balances.find(b => b.coin === 'USDC');
  const accountValue = usdcBal ? usdcBal.equity : 0;

  if (accountValue > 0) {
    const maxAllowedByCeiling = accountValue * (inst.riskCeilingPct / 100);
    if (orderNotional > maxAllowedByCeiling) {
      return {
        allowed: false,
        reason: `Order notional $${orderNotional.toFixed(2)} exceeds risk ceiling limit ($${maxAllowedByCeiling.toFixed(2)}), which is ${inst.riskCeilingPct}% of account value $${accountValue.toFixed(2)}`,
        maxAllowedNotional: maxAllowedByCeiling
      };
    }
  }

  return { allowed: true };
}
