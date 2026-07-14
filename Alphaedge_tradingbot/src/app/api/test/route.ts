import { NextRequest, NextResponse } from 'next/server';
import { encrypt, decrypt } from '@/lib/encryption';
import { appendToLedger, verifyLedgerChain } from '@/lib/ledger';
import { validateRisk } from '@/lib/risk';
import { db } from '@/db';
import { botInstances, ledgerEntries, users, exchangeConnections, botTemplates } from '@/db/schema';
import { eq } from 'drizzle-orm';

export async function GET(req: NextRequest) {
  const results: any[] = [];
  let allPassed = true;

  const runTest = async (name: string, fn: () => Promise<void>) => {
    try {
      await fn();
      results.push({ name, status: 'PASSED' });
    } catch (err: any) {
      allPassed = false;
      results.push({ name, status: 'FAILED', error: err.message || err });
    }
  };

  // Test 1: Encryption/Decryption
  await runTest('Key Envelope Encryption', async () => {
    const rawKey = '0x_hyperliquid_secret_private_key_value_12345';
    const encrypted = encrypt(rawKey);
    
    if (encrypted.encrypted === rawKey) {
      throw new Error('Encryption returned plaintext');
    }
    if (!encrypted.iv || !encrypted.tag) {
      throw new Error('Encryption is missing IV or GCM tag');
    }

    const decrypted = decrypt(encrypted.encrypted, encrypted.iv, encrypted.tag);
    if (decrypted !== rawKey) {
      throw new Error(`Decrypted value mismatch. Expected ${rawKey}, got ${decrypted}`);
    }
  });

  // Test 2: Risk Engine
  await runTest('Risk Engine Validation Checks', async () => {
    // 1. Setup mock bot instance with low limits
    const testBotId = 'test_inst_risk';
    
    // Check if user and connection exist
    await db.insert(users).values({
      id: 'test_user',
      email: 'test@alphaedge.io',
      kycStatus: 'verified',
      createdAt: Date.now()
    }).onConflictDoNothing();

    await db.insert(exchangeConnections).values({
      id: 'test_conn',
      userId: 'test_user',
      exchange: 'hyperliquid',
      encryptedApiKey: 'dummy',
      encryptionIv: 'dummy',
      encryptionTag: 'dummy',
      status: 'active',
      lastVerifiedAt: Date.now()
    }).onConflictDoNothing();

    await db.insert(botTemplates).values({
      id: 'test_tmpl_btc',
      code: 'TEST-BTC',
      assetClass: 'BTC',
      status: 'live',
    }).onConflictDoNothing();

    // Insert instance with riskCeilingPct=5 and maxNotional=100
    await db.delete(botInstances).where(eq(botInstances.id, testBotId));
    await db.insert(botInstances).values({
      id: testBotId,
      userId: 'test_user',
      botTemplateId: 'test_tmpl_btc',
      exchangeConnectionId: 'test_conn',
      mode: 'paper',
      riskCeilingPct: 5,
      maxNotional: 100, // Very low max notional
      status: 'active'
    });

    // 2. Validate a small order ($50) -> should be ALLOWED
    const smallCheck = await validateRisk(testBotId, 0.001, 50000);
    if (!smallCheck.allowed) {
      throw new Error(`Small order rejected: ${smallCheck.reason}`);
    }

    // 3. Validate a large order ($500) -> should be BLOCKED due to max notional
    const largeCheck = await validateRisk(testBotId, 0.01, 50000);
    if (largeCheck.allowed) {
      throw new Error('Large order exceeded maxNotional but was allowed');
    }
    if (!largeCheck.reason?.includes('exceeds instance maximum notional limit')) {
      throw new Error(`Incorrect rejection reason: ${largeCheck.reason}`);
    }

    // 4. Pause the bot and check -> should be BLOCKED
    await db.update(botInstances).set({ status: 'paused' }).where(eq(botInstances.id, testBotId));
    const pausedCheck = await validateRisk(testBotId, 0.001, 50000);
    if (pausedCheck.allowed) {
      throw new Error('Paused bot was allowed to execute');
    }

    // Cleanup
    await db.delete(botInstances).where(eq(botInstances.id, testBotId));
  });

  // Test 3: Ledger Chain Verification
  await runTest('Ledger Cryptographic Integrity & Tampering Detection', async () => {
    // 1. Insert a couple of entries to ensure chain is active
    const startStatus = await verifyLedgerChain();
    if (!startStatus.valid) {
      throw new Error(`Ledger chain is already invalid at start: ${startStatus.reason}`);
    }

    // 2. Append new mock transaction
    const mockId = `mock_tx_${Date.now()}`;
    const testHash = await appendToLedger('fill', mockId, { price: 50000, qty: 1, side: 'buy' });
    
    // Verify it is now valid
    const secondStatus = await verifyLedgerChain();
    if (!secondStatus.valid) {
      throw new Error(`Ledger chain broken after appending entry: ${secondStatus.reason}`);
    }

    // 3. Simulating a DB tamper: update the payload directly in the DB
    const insertedEntries = await db.select().from(ledgerEntries).where(eq(ledgerEntries.entityId, mockId));
    if (insertedEntries.length === 0) {
      throw new Error('Failed to find appended ledger entry');
    }
    const targetEntry = insertedEntries[0];

    // Alter payload value
    await db.update(ledgerEntries)
      .set({ payloadJson: JSON.stringify({ price: 1, qty: 1, side: 'buy' }) }) // tampered price
      .where(eq(ledgerEntries.id, targetEntry.id));

    // Verify tampered chain is detected as invalid
    const tamperedStatus = await verifyLedgerChain();
    if (tamperedStatus.valid) {
      throw new Error('Tampered ledger payload went undetected by chain verification');
    }

    // Restore to maintain database clean state
    await db.delete(ledgerEntries).where(eq(ledgerEntries.id, targetEntry.id));
    
    // Check it's valid again
    const finalStatus = await verifyLedgerChain();
    if (!finalStatus.valid) {
      throw new Error(`Ledger chain remained invalid after cleanup: ${finalStatus.reason}`);
    }
  });

  return NextResponse.json({
    success: allPassed,
    results
  });
}
