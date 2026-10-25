import { test } from 'node:test';
import assert from 'node:assert/strict';
import { applyEvent, currentProfit, feeIfWithdrawnNow, validatePct, type FeeState } from '../src/lib/profit-share';

const start = (capital: number): FeeState => ({ capitalBasis: capital, outstandingFee: 0 });

test("owner's examples: capital 1,000, balance 1,500", () => {
  assert.equal(feeIfWithdrawnNow(1500, start(1000), 10), 50);
  assert.equal(feeIfWithdrawnNow(1500, start(1000), 50), 250);
  assert.equal(feeIfWithdrawnNow(1500, start(1000), 5), 25);
});

test('no fee at break-even or on a loss', () => {
  assert.equal(feeIfWithdrawnNow(1000, start(1000), 50), 0);
  assert.equal(feeIfWithdrawnNow(800, start(1000), 50), 0);
});

test('full withdrawal at 10%: fee 50, nothing left to charge', () => {
  const r = applyEvent(start(1000), { kind: 'withdrawal', amount: 1450, balanceBefore: 1500, pct: 10 });
  assert.equal(r.record.profit, 500);
  assert.equal(r.record.fee, 50);
  assert.equal(r.state.outstandingFee, 50);
  // 50 still in wallet, owed: profit must read zero, not 50.
  assert.equal(currentProfit(50, r.state), 0);
  const paid = applyEvent(r.state, { kind: 'fee_payment', amount: 50 });
  assert.deepEqual(paid.state, { capitalBasis: 0, outstandingFee: 0 });
  assert.equal(currentProfit(0, paid.state), 0);
});

test('partial withdrawal settles all profit and resets basis to balance after fee', () => {
  const r = applyEvent(start(1000), { kind: 'withdrawal', amount: 300, balanceBefore: 1500, pct: 10 });
  assert.equal(r.record.fee, 50);
  assert.equal(r.state.capitalBasis, 1150); // 1,500 - 300 - 50
  assert.equal(currentProfit(1200, r.state), 0);
  // Later the account earns 100 more: only the new 100 is profit.
  assert.equal(currentProfit(1300, r.state), 100);
  assert.equal(feeIfWithdrawnNow(1300, r.state, 10), 10);
});

test('the same gain is never charged twice across two withdrawals', () => {
  let s = start(1000);
  s = applyEvent(s, { kind: 'withdrawal', amount: 100, balanceBefore: 1500, pct: 20 }).state; // fee 100
  s = applyEvent(s, { kind: 'fee_payment', amount: 100 }).state;
  // Balance now 1,300 with no new trading: second withdrawal owes nothing.
  const r = applyEvent(s, { kind: 'withdrawal', amount: 100, balanceBefore: 1300, pct: 20 });
  assert.equal(r.record.fee, 0);
});

test('loss carries forward: no fee on recovery below the old level', () => {
  let s = start(1000);
  const r1 = applyEvent(s, { kind: 'withdrawal', amount: 100, balanceBefore: 800, pct: 10 });
  assert.equal(r1.record.fee, 0);
  assert.equal(r1.record.profit, -200);
  s = r1.state; // basis 900, balance 700: still 200 under water
  assert.equal(currentProfit(700, s), -200);
  // Recovers to 850: still below basis, still nothing.
  assert.equal(feeIfWithdrawnNow(850, s, 10), 0);
  // Climbs to 1,000: only the 100 above 900 is profit.
  assert.equal(feeIfWithdrawnNow(1000, s, 10), 10);
});

test('deposits are capital, never profit', () => {
  const s = applyEvent(start(1000), { kind: 'deposit', amount: 2000 }).state;
  assert.equal(currentProfit(3000, s), 0);
  assert.equal(currentProfit(3300, s), 300);
});

test('unpaid fee is not re-charged at the next withdrawal', () => {
  let s = applyEvent(start(1000), { kind: 'withdrawal', amount: 0, balanceBefore: 1500, pct: 10 }).state;
  assert.equal(s.outstandingFee, 50);
  // No payment, no trading; another withdrawal of 200.
  const r = applyEvent(s, { kind: 'withdrawal', amount: 200, balanceBefore: 1500, pct: 10 });
  assert.equal(r.record.fee, 0);
  assert.equal(r.state.outstandingFee, 50);
});

test('waiver clears debt without turning it into profit', () => {
  let s = applyEvent(start(1000), { kind: 'withdrawal', amount: 0, balanceBefore: 1500, pct: 10 }).state;
  const w = applyEvent(s, { kind: 'waiver', amount: 50 });
  assert.equal(w.state.outstandingFee, 0);
  assert.equal(currentProfit(1500, w.state), 0);
});

test('overpayment beyond the debt is treated as an outflow', () => {
  let s = applyEvent(start(1000), { kind: 'withdrawal', amount: 0, balanceBefore: 1500, pct: 10 }).state;
  const p = applyEvent(s, { kind: 'fee_payment', amount: 80 });
  assert.equal(p.record.appliedToFee, 50);
  assert.equal(p.record.excess, 30);
  assert.equal(p.state.outstandingFee, 0);
  assert.equal(currentProfit(1420, p.state), 0); // 1,500 - 80
});

test('rate change applies to the event it is passed with', () => {
  const r = applyEvent(start(1000), { kind: 'withdrawal', amount: 0, balanceBefore: 1500, pct: 50 });
  assert.equal(r.record.fee, 250);
});

test('validation', () => {
  assert.equal(validatePct('10'), 10);
  assert.throws(() => validatePct(-1));
  assert.throws(() => validatePct(101));
  assert.throws(() => validatePct('abc'));
  assert.throws(() => applyEvent(start(1), { kind: 'deposit', amount: NaN }));
  assert.throws(() => applyEvent(start(1), { kind: 'deposit', amount: -5 }));
});
