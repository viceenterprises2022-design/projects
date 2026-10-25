import { db } from '@/db';
import { customers, customerRateChanges, customerState, walletFlows, feeEvents, users } from '@/db/schema';
import { and, asc, desc, eq, isNull, lt, or, sql } from 'drizzle-orm';
import { applyEvent, cents, currentProfit, feeIfWithdrawnNow, validatePct, type FeeState } from './profit-share';
import {
  classifyLedger, getFills, getLedger, getWalletBalance, isAddress, isInflow, isOutflow, normAddr,
  type FlowKind,
} from './hyperliquid-info';
import { AnalyticsAccumulator, type TradeRow } from './analytics';

// Customer onboarding, wallet sync and fee bookkeeping. Read-only towards the
// venue: nothing here can move customer funds (HLD §4.5).

export const feeAddress = (): string | null => {
  const a = process.env.ALPHAEDGE_FEE_ADDRESS;
  return a && isAddress(a) ? normAddr(a) : null;
};

const LOCK_MS = 60_000;
const uid = () => crypto.randomUUID();

export type Customer = typeof customers.$inferSelect;
export type CustomerStateRow = typeof customerState.$inferSelect;

// ---------------------------------------------------------------------------
// Onboarding and settings (owner only; callers enforce authz)
// ---------------------------------------------------------------------------

export async function createCustomer(input: {
  name: unknown; email: unknown; walletAddress: unknown; profitSharePct: unknown;
  initialCapital?: unknown; notes?: unknown;
}, actor: string): Promise<Customer> {
  const name = String(input.name ?? '').trim();
  const email = String(input.email ?? '').trim().toLowerCase();
  if (!name) throw new Error('Name is required');
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) throw new Error('A valid email is required');
  if (!isAddress(input.walletAddress)) throw new Error('Wallet must be a 0x address (40 hex characters)');
  const walletAddress = normAddr(input.walletAddress);
  const pct = validatePct(input.profitSharePct);

  const dup = await db.select({ id: customers.id }).from(customers).where(eq(customers.walletAddress, walletAddress)).limit(1);
  if (dup.length) throw new Error('This wallet is already onboarded');

  // Capital defaults to the wallet's balance at onboarding: whatever is there
  // now is the customer's money, and only growth from here is profit.
  const bal = await getWalletBalance(walletAddress);
  let initialCapital = bal.total;
  if (input.initialCapital !== undefined && input.initialCapital !== null && String(input.initialCapital).trim() !== '') {
    const c = Number(input.initialCapital);
    if (!Number.isFinite(c) || c < 0) throw new Error('Initial capital must be a non-negative number');
    initialCapital = cents(c);
  }

  const linked = await db.select({ id: users.id }).from(users).where(eq(users.email, email)).limit(1);
  const now = Date.now();
  const row: Customer = {
    id: uid(), userId: linked[0]?.id ?? null, name, email, walletAddress, venue: 'hyperliquid',
    profitSharePct: pct, status: 'active', initialCapital, syncFrom: now,
    notes: input.notes ? String(input.notes).slice(0, 2000) : null, createdBy: actor, createdAt: now,
  };
  await db.batch([
    db.insert(customers).values(row),
    db.insert(customerRateChanges).values({ id: uid(), customerId: row.id, pct, effectiveAt: now, setBy: actor }),
    db.insert(customerState).values({
      customerId: row.id, capitalBasis: initialCapital, outstandingFee: 0,
      lastBalance: bal.total, lastSyncedAt: now, lastLedgerTime: now, lastError: null, syncLockUntil: null,
    }),
  ]);
  return row;
}

export async function updateCustomer(id: string, patch: { profitSharePct?: unknown; status?: unknown; notes?: unknown; name?: unknown }, actor: string) {
  const c = await getCustomer(id);
  if (!c) throw new Error('Customer not found');
  const ops: any[] = [];
  const set: Partial<Customer> = {};
  if (patch.profitSharePct !== undefined) {
    const pct = validatePct(patch.profitSharePct);
    if (pct !== c.profitSharePct) {
      set.profitSharePct = pct;
      // Forward-only: events before now keep the rate they happened under.
      ops.push(db.insert(customerRateChanges).values({ id: uid(), customerId: id, pct, effectiveAt: Date.now(), setBy: actor }));
    }
  }
  if (patch.status !== undefined) {
    const s = String(patch.status);
    if (!['active', 'paused', 'closed'].includes(s)) throw new Error('Invalid status');
    set.status = s;
  }
  if (patch.notes !== undefined) set.notes = patch.notes ? String(patch.notes).slice(0, 2000) : null;
  if (patch.name !== undefined && String(patch.name).trim()) set.name = String(patch.name).trim();
  if (Object.keys(set).length) ops.unshift(db.update(customers).set(set).where(eq(customers.id, id)));
  if (ops.length) await db.batch(ops as [any, ...any[]]);
  return getCustomer(id);
}

/** Owner records a fee settled outside Hyperliquid, or forgives it. */
export async function recordManualFee(id: string, kind: 'manual_payment' | 'waiver', amountRaw: unknown, note: unknown, actor: string) {
  const amount = Number(amountRaw);
  if (!Number.isFinite(amount) || amount <= 0) throw new Error('Amount must be a positive number');
  return withLock(id, async () => {
    const st = await getState(id);
    if (!st) throw new Error('Customer state missing');
    if (amount > st.outstandingFee + 0.005) throw new Error(`Amount exceeds outstanding fee (${st.outstandingFee.toFixed(2)})`);
    // A payment made off-venue leaves the wallet untouched, which is the same
    // arithmetic as a waiver: the debt goes, the money stays, the basis rises.
    const before: FeeState = { capitalBasis: st.capitalBasis, outstandingFee: st.outstandingFee };
    const r = applyEvent(before, { kind: 'waiver', amount: cents(amount) });
    await db.batch([
      db.update(customerState).set({ capitalBasis: r.state.capitalBasis, outstandingFee: r.state.outstandingFee })
        .where(eq(customerState.customerId, id)),
      db.insert(feeEvents).values({
        id: uid(), customerId: id, flowId: null, kind,
        balanceBefore: st.lastBalance, capitalBefore: before.capitalBasis, outstandingBefore: before.outstandingFee,
        profit: null, pct: null, fee: 0, amount: r.record.appliedToFee,
        capitalAfter: r.state.capitalBasis, outstandingAfter: r.state.outstandingFee,
        estimated: 0, note: note ? String(note).slice(0, 500) : null, createdBy: actor, createdAt: Date.now(),
      }),
    ]);
  });
}

// ---------------------------------------------------------------------------
// Sync
// ---------------------------------------------------------------------------

async function withLock<T>(id: string, fn: () => Promise<T>): Promise<T> {
  const now = Date.now();
  const res = await db.update(customerState).set({ syncLockUntil: now + LOCK_MS })
    .where(and(eq(customerState.customerId, id), or(isNull(customerState.syncLockUntil), lt(customerState.syncLockUntil, now))));
  if ((res as any).rowsAffected !== 1) throw new Error('Another sync for this customer is in progress; retry in a minute');
  try {
    return await fn();
  } finally {
    await db.update(customerState).set({ syncLockUntil: null }).where(eq(customerState.customerId, id));
  }
}

async function pctAt(customerId: string, t: number, fallback: number): Promise<number> {
  const rows = await db.select().from(customerRateChanges)
    .where(eq(customerRateChanges.customerId, customerId)).orderBy(asc(customerRateChanges.effectiveAt));
  let pct = rows.length ? rows[0].pct : fallback;
  for (const r of rows) if (r.effectiveAt <= t) pct = r.pct;
  return pct;
}

export type SyncResult = { customerId: string; newFlows: number; processed: number; feesCrystallised: number; balance: number; error?: string };

/**
 * Pull balance and ledger, store new flows, then apply unprocessed flows in
 * time order. Each flow's state change, fee record and processed marker are
 * written in one batch (one transaction), so a crash can never apply a flow
 * twice or skip one.
 *
 * Balance at the moment of a withdrawal is reconstructed as
 *   balance now + every outflow since (inclusive) - every inflow since.
 * Trading P&L between the withdrawal and the sync is not separable, so the
 * cron runs every 5 minutes to keep that gap small, and each crystallisation
 * is flagged `estimated` with the gap in its note.
 */
export async function syncCustomer(id: string): Promise<SyncResult> {
  const c = await getCustomer(id);
  if (!c) throw new Error('Customer not found');
  return withLock(id, async () => {
    const st0 = await getState(id);
    if (!st0) throw new Error('Customer state missing');
    const now = Date.now();
    try {
      const fa = feeAddress();
      const since = Math.max(c.syncFrom, (st0.lastLedgerTime ?? c.syncFrom) - 60_000); // 1 min overlap; ids dedupe
      const [bal, ledger] = await Promise.all([getWalletBalance(c.walletAddress), getLedger(c.walletAddress, since)]);

      let newFlows = 0;
      let maxTime = st0.lastLedgerTime ?? c.syncFrom;
      for (const e of ledger) {
        if (e.time < c.syncFrom) continue;
        const f = classifyLedger(e, c.walletAddress, fa);
        maxTime = Math.max(maxTime, e.time);
        if (!f || f.amount <= 0) continue;
        const flowId = `${e.hash}:${f.kind}:${f.amount.toFixed(6)}:${e.time}`;
        const ins = await db.insert(walletFlows).values({
          id: flowId, customerId: id, kind: f.kind, amount: cents(f.amount), venueFee: cents(f.venueFee),
          counterparty: f.counterparty, txHash: e.hash, occurredAt: e.time, rawJson: JSON.stringify(e.delta), processedAt: null,
        }).onConflictDoNothing();
        if ((ins as any).rowsAffected === 1) newFlows++;
      }

      const pending = await db.select().from(walletFlows)
        .where(and(eq(walletFlows.customerId, id), isNull(walletFlows.processedAt)))
        .orderBy(asc(walletFlows.occurredAt), asc(walletFlows.id));

      let state: FeeState = { capitalBasis: st0.capitalBasis, outstandingFee: st0.outstandingFee };
      let fees = 0;
      for (let i = 0; i < pending.length; i++) {
        const f = pending[i];
        const kind = f.kind as FlowKind;
        const before = state;
        let r: ReturnType<typeof applyEvent> | null = null;
        let balanceBefore: number | null = null;
        let pct: number | null = null;

        if (isInflow(kind)) {
          r = applyEvent(state, { kind: 'deposit', amount: f.amount });
        } else if (kind === 'fee_payment') {
          r = applyEvent(state, { kind: 'fee_payment', amount: f.amount });
        } else if (kind === 'withdrawal' || kind === 'transfer_out') {
          let delta = 0;
          for (let j = i; j < pending.length; j++) {
            const g = pending[j];
            if (isOutflow(g.kind as FlowKind)) delta += g.amount;
            else if (isInflow(g.kind as FlowKind)) delta -= g.amount;
          }
          balanceBefore = cents(bal.total + delta);
          pct = await pctAt(id, f.occurredAt, c.profitSharePct);
          r = applyEvent(state, { kind: 'withdrawal', amount: f.amount, balanceBefore, pct });
        }

        const ops: any[] = [db.update(walletFlows).set({ processedAt: now }).where(eq(walletFlows.id, f.id))];
        if (r) {
          state = r.state;
          ops.push(db.update(customerState).set({ capitalBasis: state.capitalBasis, outstandingFee: state.outstandingFee })
            .where(eq(customerState.customerId, id)));
          const isWithdrawal = kind === 'withdrawal' || kind === 'transfer_out';
          if (isWithdrawal || kind === 'fee_payment') {
            fees += r.record.fee;
            const gapMin = Math.round((now - f.occurredAt) / 60_000);
            ops.push(db.insert(feeEvents).values({
              id: uid(), customerId: id, flowId: f.id, kind: isWithdrawal ? 'crystallisation' : 'payment',
              balanceBefore, capitalBefore: before.capitalBasis, outstandingBefore: before.outstandingFee,
              profit: isWithdrawal ? r.record.profit : null, pct,
              fee: r.record.fee, amount: isWithdrawal ? f.amount : r.record.appliedToFee,
              capitalAfter: state.capitalBasis, outstandingAfter: state.outstandingFee,
              estimated: isWithdrawal ? 1 : 0,
              note: isWithdrawal
                ? `Balance at withdrawal reconstructed from balance ${gapMin} min later`
                : r.record.excess > 0 ? `Overpaid by ${r.record.excess.toFixed(2)}; excess treated as an outflow` : null,
              createdBy: 'sync', createdAt: now,
            }).onConflictDoNothing());
          }
        }
        await db.batch(ops as [any, ...any[]]);
      }

      await db.update(customerState).set({ lastBalance: bal.total, lastSyncedAt: now, lastLedgerTime: maxTime, lastError: null })
        .where(eq(customerState.customerId, id));
      return { customerId: id, newFlows, processed: pending.length, feesCrystallised: cents(fees), balance: bal.total };
    } catch (err: any) {
      await db.update(customerState).set({ lastError: String(err?.message || err).slice(0, 500), lastSyncedAt: now })
        .where(eq(customerState.customerId, id));
      throw err;
    }
  });
}

export async function syncAll(): Promise<SyncResult[]> {
  const list = await db.select({ id: customers.id }).from(customers).where(sql`${customers.status} != 'closed'`);
  const out: SyncResult[] = [];
  for (const { id } of list) {
    try { out.push(await syncCustomer(id)); }
    catch (e: any) { out.push({ customerId: id, newFlows: 0, processed: 0, feesCrystallised: 0, balance: 0, error: e.message }); }
  }
  return out;
}

// ---------------------------------------------------------------------------
// Reads
// ---------------------------------------------------------------------------

export async function getCustomer(id: string): Promise<Customer | null> {
  const r = await db.select().from(customers).where(eq(customers.id, id)).limit(1);
  return r[0] ?? null;
}

export async function getState(id: string): Promise<CustomerStateRow | null> {
  const r = await db.select().from(customerState).where(eq(customerState.customerId, id)).limit(1);
  return r[0] ?? null;
}

export function summarise(c: Customer, s: CustomerStateRow | null) {
  const balance = s?.lastBalance ?? 0;
  const st: FeeState = { capitalBasis: s?.capitalBasis ?? c.initialCapital, outstandingFee: s?.outstandingFee ?? 0 };
  return {
    balance,
    capitalBasis: st.capitalBasis,
    outstandingFee: st.outstandingFee,
    profit: currentProfit(balance, st),
    feeIfWithdrawnNow: feeIfWithdrawnNow(balance, st, c.profitSharePct),
    lastSyncedAt: s?.lastSyncedAt ?? null,
    lastError: s?.lastError ?? null,
  };
}

export async function listCustomers() {
  const rows = await db.select().from(customers).leftJoin(customerState, eq(customerState.customerId, customers.id))
    .orderBy(asc(customers.name));
  return rows.map(r => ({ ...r.customers, ...summarise(r.customers, r.customer_state) }));
}

export async function customerDetail(id: string) {
  const c = await getCustomer(id);
  if (!c) return null;
  const [s, flows, fees, rates] = await Promise.all([
    getState(id),
    db.select().from(walletFlows).where(eq(walletFlows.customerId, id)).orderBy(desc(walletFlows.occurredAt)).limit(500),
    db.select().from(feeEvents).where(eq(feeEvents.customerId, id)).orderBy(desc(feeEvents.createdAt)).limit(500),
    db.select().from(customerRateChanges).where(eq(customerRateChanges.customerId, id)).orderBy(desc(customerRateChanges.effectiveAt)),
  ]);
  let crystallised = 0, paidOnVenue = 0, paidManual = 0, waived = 0;
  for (const f of fees) {
    if (f.kind === 'crystallisation') crystallised += f.fee;
    else if (f.kind === 'payment') paidOnVenue += f.amount;
    else if (f.kind === 'manual_payment') paidManual += f.amount;
    else if (f.kind === 'waiver') waived += f.amount;
  }
  let deposited = 0, withdrawn = 0;
  for (const f of flows) {
    if (isInflow(f.kind as FlowKind)) deposited += f.amount;
    else if (f.kind === 'withdrawal' || f.kind === 'transfer_out') withdrawn += f.amount;
  }
  // Withdrawal history joined to the fee it crystallised.
  const feeByFlow = new Map(fees.filter(f => f.flowId).map(f => [f.flowId!, f]));
  return {
    customer: c,
    summary: summarise(c, s),
    totals: {
      feesCrystallised: cents(crystallised), feesPaid: cents(paidOnVenue + paidManual),
      feesPaidOnVenue: cents(paidOnVenue), feesPaidManual: cents(paidManual), feesWaived: cents(waived),
      deposited: cents(deposited), withdrawn: cents(withdrawn),
    },
    flows: flows.map(f => {
      const fe = feeByFlow.get(f.id);
      return {
        id: f.id, kind: f.kind, amount: f.amount, venueFee: f.venueFee, counterparty: f.counterparty,
        txHash: f.txHash, occurredAt: f.occurredAt, processed: f.processedAt !== null,
        fee: fe?.fee ?? null, profitAtWithdrawal: fe?.profit ?? null, pct: fe?.pct ?? null, estimated: !!fe?.estimated,
      };
    }),
    fees,
    rates,
    feeAddress: feeAddress(),
  };
}

/** Per-wallet trade analytics from the customer's own Hyperliquid fills since onboarding. */
export async function walletAnalytics(id: string) {
  const c = await getCustomer(id);
  if (!c) return null;
  const fills = await getFills(c.walletAddress, c.syncFrom);
  const acc = new AnalyticsAccumulator();
  for (const f of fills) {
    const closed = parseFloat(f.closedPnl);
    if (!Number.isFinite(closed) || closed === 0) continue; // opening fills are not settled trades
    const pnl = closed - (parseFloat(f.fee) || 0);
    const row: TradeRow = {
      id: String(f.tid), createdAt: f.time, level: 0, asset: f.coin,
      side: f.side === 'B' ? 'BUY' : 'SELL', outcome: pnl > 0 ? 'WIN' : 'LOSS',
      pnl, size: parseFloat(f.sz) || 0, entryPrice: parseFloat(f.px) || 0,
    };
    acc.push(row);
  }
  return { view: acc.result()['0'], totalFills: fills.length, settledTrades: acc.rows, since: c.syncFrom };
}

/** Customer self-view: matched by login email. */
export async function customerForEmail(email: string) {
  const r = await db.select({ id: customers.id }).from(customers).where(eq(customers.email, email.toLowerCase())).limit(1);
  return r[0] ? customerDetail(r[0].id) : null;
}
