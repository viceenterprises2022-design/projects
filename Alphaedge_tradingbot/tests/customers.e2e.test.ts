// End-to-end check of the profit-share money path against real migrations on
// a throwaway libSQL file, with the Hyperliquid /info API mocked.
import { test, before } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const dir = mkdtempSync(join(tmpdir(), 'ae-cust-'));
process.env.DATABASE_URL = `file:${join(dir, 'test.db')}`;
const FEE = '0x' + 'f'.repeat(40);
const WALLET = '0x' + 'a'.repeat(40);
process.env.ALPHAEDGE_FEE_ADDRESS = FEE;

// Mock venue: mutable balance and ledger.
const venue = { balance: 1000, ledger: [] as any[] };
const realFetch = globalThis.fetch;
globalThis.fetch = (async (url: any, init?: any) => {
  if (!String(url).includes('hyperliquid')) return realFetch(url, init);
  const body = JSON.parse(init.body);
  const json = (v: unknown) => new Response(JSON.stringify(v), { status: 200 });
  switch (body.type) {
    case 'clearinghouseState': return json({ marginSummary: { accountValue: String(venue.balance) } });
    case 'spotClearinghouseState': return json({ balances: [] });
    case 'userNonFundingLedgerUpdates': return json(venue.ledger.filter(e => e.time >= body.startTime));
    case 'userFillsByTime': return json([]);
    default: return json({});
  }
}) as typeof fetch;

let lib: typeof import('../src/lib/customers');

before(async () => {
  const { initDb } = await import('../src/db/init');
  await initDb();
  lib = await import('../src/lib/customers');
});

test('onboard at 10%, profit 500, withdraw, pay, re-sync', async () => {
  const c = await lib.createCustomer({ name: 'Test', email: 'T@x.io', walletAddress: WALLET.toUpperCase().replace('0X', '0x'), profitSharePct: 10 }, 'owner@x');
  assert.equal(c.initialCapital, 1000);
  assert.equal(c.walletAddress, WALLET);

  // Trading takes balance to 1,500.
  venue.balance = 1500;
  let d = await lib.customerDetail(c.id);
  await lib.syncCustomer(c.id);
  d = await lib.customerDetail(c.id);
  assert.equal(d!.summary.profit, 500);
  assert.equal(d!.summary.feeIfWithdrawnNow, 50);

  // Customer withdraws 300 directly from their wallet.
  const t1 = Date.now() + 1000;
  venue.ledger.push({ time: t1, hash: '0xw1', delta: { type: 'withdraw', usdc: '300', fee: '1', nonce: 1 } });
  venue.balance = 1200;
  const r1 = await lib.syncCustomer(c.id);
  assert.equal(r1.feesCrystallised, 50);
  d = await lib.customerDetail(c.id);
  assert.equal(d!.summary.outstandingFee, 50);
  assert.equal(d!.summary.capitalBasis, 1150);
  assert.equal(d!.summary.profit, 0);
  const w = d!.flows.find(f => f.kind === 'withdrawal')!;
  assert.equal(w.fee, 50);
  assert.equal(w.profitAtWithdrawal, 500);

  // Re-sync with nothing new: idempotent, no double charge.
  const r2 = await lib.syncCustomer(c.id);
  assert.equal(r2.newFlows, 0);
  assert.equal(r2.feesCrystallised, 0);
  d = await lib.customerDetail(c.id);
  assert.equal(d!.totals.feesCrystallised, 50);

  // Customer pays the fee to the AlphaEdge fee wallet on Hyperliquid.
  venue.ledger.push({ time: t1 + 1000, hash: '0xp1', delta: { type: 'send', user: WALLET, destination: FEE, token: 'USDC', amount: '50', usdcValue: '50', fee: '0' } });
  venue.balance = 1150;
  await lib.syncCustomer(c.id);
  d = await lib.customerDetail(c.id);
  assert.equal(d!.summary.outstandingFee, 0);
  assert.equal(d!.summary.profit, 0);
  assert.equal(d!.totals.feesPaidOnVenue, 50);

  // Deposit is capital, not profit.
  venue.ledger.push({ time: t1 + 2000, hash: '0xd1', delta: { type: 'deposit', usdc: '1000' } });
  venue.balance = 2150;
  await lib.syncCustomer(c.id);
  d = await lib.customerDetail(c.id);
  assert.equal(d!.summary.profit, 0);
  assert.equal(d!.summary.capitalBasis, 2150);
});

test('rate change to 50% applies forward; manual payment and waiver', async () => {
  const W2 = '0x' + 'b'.repeat(40);
  venue.ledger = []; venue.balance = 1000;
  const c = await lib.createCustomer({ name: 'Two', email: 'two@x.io', walletAddress: W2, profitSharePct: 10 }, 'owner@x');
  await lib.updateCustomer(c.id, { profitSharePct: 50 }, 'owner@x');
  venue.balance = 1500;
  const t = Date.now() + 5000;
  venue.ledger.push({ time: t, hash: '0xw2', delta: { type: 'withdraw', usdc: '1500', fee: '1', nonce: 2 } });
  venue.balance = 0;
  const r = await lib.syncCustomer(c.id);
  assert.equal(r.feesCrystallised, 250); // 50% of 500
  await lib.recordManualFee(c.id, 'manual_payment', 200, 'bank transfer', 'owner@x');
  await lib.recordManualFee(c.id, 'waiver', 50, 'goodwill', 'owner@x');
  const d = await lib.customerDetail(c.id);
  assert.equal(d!.summary.outstandingFee, 0);
  assert.equal(d!.totals.feesPaidManual, 200);
  assert.equal(d!.totals.feesWaived, 50);
  await assert.rejects(() => lib.recordManualFee(c.id, 'waiver', 1, null, 'owner@x'), /exceeds outstanding/);
});

test('validation and duplicates', async () => {
  await assert.rejects(() => lib.createCustomer({ name: 'X', email: 'x@x.io', walletAddress: '0x123', profitSharePct: 10 }, 'o'), /0x address/);
  await assert.rejects(() => lib.createCustomer({ name: 'X', email: 'x@x.io', walletAddress: WALLET, profitSharePct: 10 }, 'o'), /already onboarded/);
  await assert.rejects(() => lib.createCustomer({ name: 'X', email: 'x@x.io', walletAddress: '0x' + 'c'.repeat(40), profitSharePct: 150 }, 'o'), /between 0 and 100/);
});

test('ledger classification', async () => {
  const { classifyLedger } = await import('../src/lib/hyperliquid-info');
  const e = (delta: any) => ({ time: 1, hash: 'h', delta });
  assert.equal(classifyLedger(e({ type: 'accountClassTransfer', usdc: '5', toPerp: true }), WALLET, FEE), null);
  assert.equal(classifyLedger(e({ type: 'internalTransfer', usdc: '5', user: WALLET, destination: FEE }), WALLET, FEE)!.kind, 'fee_payment');
  assert.equal(classifyLedger(e({ type: 'internalTransfer', usdc: '5', user: WALLET, destination: '0x' + '1'.repeat(40) }), WALLET, FEE)!.kind, 'transfer_out');
  assert.equal(classifyLedger(e({ type: 'spotTransfer', usdcValue: '7', amount: '7', user: '0x' + '2'.repeat(40), destination: WALLET }), WALLET, FEE)!.kind, 'transfer_in');
  assert.equal(classifyLedger(e({ type: 'vaultDeposit', usdc: '9', vault: '0x' + '3'.repeat(40) }), WALLET, FEE)!.kind, 'transfer_out');
  assert.equal(classifyLedger(e({ type: 'liquidation', usdc: '1' }), WALLET, FEE)!.kind, 'unclassified');
  // Without a configured fee address, a payment cannot be recognised.
  assert.equal(classifyLedger(e({ type: 'send', user: WALLET, destination: FEE, usdcValue: '5' }), WALLET, null)!.kind, 'transfer_out');
});
