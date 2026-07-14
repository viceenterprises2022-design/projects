import { db } from '../db';
import { ledgerEntries } from '../db/schema';
import { desc, asc } from 'drizzle-orm';
import crypto from 'crypto';

export interface LedgerPayload {
  [key: string]: any;
}

function calculateHash(prevHash: string, payloadStr: string, timestamp: number): string {
  const data = prevHash + payloadStr + timestamp.toString();
  return crypto.createHash('sha256').update(data).digest('hex');
}

export async function appendToLedger(
  entityType: 'signal' | 'fill' | 'risk_event',
  entityId: string,
  payload: LedgerPayload
): Promise<string> {
  const lastEntries = await db
    .select()
    .from(ledgerEntries)
    .orderBy(desc(ledgerEntries.timestamp))
    .limit(1);

  const prevHash = lastEntries.length > 0 ? lastEntries[0].hash : '0'.repeat(64);
  const timestamp = Date.now();
  const payloadJson = JSON.stringify(payload);
  const hash = calculateHash(prevHash, payloadJson, timestamp);

  const id = `ledg_${Math.random().toString(36).substring(2, 11)}`;
  
  await db.insert(ledgerEntries).values({
    id,
    prevHash,
    hash,
    entityType,
    entityId,
    payloadJson,
    timestamp
  });

  return hash;
}

export async function verifyLedgerChain(): Promise<{ valid: boolean; errorIndex?: number; reason?: string }> {
  const entries = await db
    .select()
    .from(ledgerEntries)
    .orderBy(asc(ledgerEntries.timestamp));

  for (let i = 0; i < entries.length; i++) {
    const entry = entries[i];
    
    if (i === 0) {
      if (entry.prevHash !== '0'.repeat(64)) {
        return {
          valid: false,
          errorIndex: 0,
          reason: `Genesis entry prevHash mismatch. Expected genesis value, got ${entry.prevHash}`
        };
      }
    } else {
      const priorEntry = entries[i - 1];
      if (entry.prevHash !== priorEntry.hash) {
        return {
          valid: false,
          errorIndex: i,
          reason: `Broken chain link at index ${i}. Previous entry hash ${priorEntry.hash} != current prevHash ${entry.prevHash}`
        };
      }
    }

    const expectedHash = calculateHash(entry.prevHash, entry.payloadJson, entry.timestamp);
    if (entry.hash !== expectedHash) {
      return {
        valid: false,
        errorIndex: i,
        reason: `Cryptographic mismatch at index ${i}. Expected hash ${expectedHash}, got stored hash ${entry.hash}`
      };
    }
  }

  return { valid: true };
}
