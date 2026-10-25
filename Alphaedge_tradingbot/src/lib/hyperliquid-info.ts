// Read-only Hyperliquid info client for CUSTOMER wallets.
//
// Everything here uses the public /info endpoint keyed by a wallet address.
// No key, no signature, no ability to move funds. This is deliberate: the
// profit-share system must work without ever holding custody (HLD §4.5).
//
// Network: customer wallets hold real money, so this defaults to MAINNET,
// independently of HYPERLIQUID_NETWORK (which defaults to testnet for the
// order path, where an unset value must never mean real money). Reads carry
// no such risk. Override with CUSTOMER_WALLET_NETWORK=testnet for staging.

export function customerNetwork(): 'mainnet' | 'testnet' {
  return process.env.CUSTOMER_WALLET_NETWORK === 'testnet' ? 'testnet' : 'mainnet';
}

function infoUrl(): string {
  return customerNetwork() === 'mainnet'
    ? 'https://api.hyperliquid.xyz/info'
    : 'https://api.hyperliquid-testnet.xyz/info';
}

async function info<T>(body: Record<string, unknown>): Promise<T> {
  const res = await fetch(infoUrl(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`Hyperliquid ${String(body.type)} failed: HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

export const isAddress = (a: unknown): a is string =>
  typeof a === 'string' && /^0x[0-9a-fA-F]{40}$/.test(a.trim());

export const normAddr = (a: string) => a.trim().toLowerCase();

const num = (v: unknown): number => {
  const n = typeof v === 'number' ? v : parseFloat(String(v ?? '0'));
  return Number.isFinite(n) ? n : 0;
};

/**
 * Wallet balance in USD = perp account value (includes unrealised P&L on open
 * positions) + spot USDC. Other spot tokens are not counted; if a customer
 * holds them, the profit figure understates by their value, which errs in the
 * customer's favour.
 */
export async function getWalletBalance(address: string): Promise<{ perp: number; spotUsdc: number; total: number }> {
  const [perpState, spotState] = await Promise.all([
    info<any>({ type: 'clearinghouseState', user: address }),
    info<any>({ type: 'spotClearinghouseState', user: address }),
  ]);
  const perp = num(perpState?.marginSummary?.accountValue);
  const usdc = (spotState?.balances || []).find((b: any) => b?.coin === 'USDC');
  const spotUsdc = num(usdc?.total);
  return { perp, spotUsdc, total: Math.round((perp + spotUsdc) * 100) / 100 };
}

export type LedgerEntry = { time: number; hash: string; delta: Record<string, any> };

/** Non-funding ledger updates (deposits, withdrawals, transfers) since startTime, oldest first. */
export async function getLedger(address: string, startTime: number): Promise<LedgerEntry[]> {
  const out: LedgerEntry[] = [];
  const seen = new Set<string>();
  let cursor = startTime;
  // The endpoint caps each response; walk forward until it stops advancing.
  for (let page = 0; page < 50; page++) {
    const batch = await info<LedgerEntry[]>({ type: 'userNonFundingLedgerUpdates', user: address, startTime: cursor });
    if (!Array.isArray(batch) || batch.length === 0) break;
    batch.sort((a, b) => a.time - b.time);
    let added = 0;
    for (const e of batch) {
      const k = `${e.hash}:${e.time}:${JSON.stringify(e.delta)}`;
      if (seen.has(k)) continue;
      seen.add(k); out.push(e); added++;
    }
    const last = batch[batch.length - 1].time;
    if (added === 0 || last + 1 <= cursor) break;
    cursor = last + 1;
  }
  return out.sort((a, b) => a.time - b.time);
}

export type Fill = {
  coin: string; px: string; sz: string; side: string; time: number;
  dir: string; closedPnl: string; fee: string; tid: number; hash: string;
};

/** Fills since startTime, oldest first. Hyperliquid retains the most recent 10,000. */
export async function getFills(address: string, startTime: number): Promise<Fill[]> {
  const out: Fill[] = [];
  const seen = new Set<number>();
  let cursor = startTime;
  for (let page = 0; page < 10; page++) {
    const batch = await info<Fill[]>({ type: 'userFillsByTime', user: address, startTime: cursor, aggregateByTime: false });
    if (!Array.isArray(batch) || batch.length === 0) break;
    batch.sort((a, b) => a.time - b.time);
    let added = 0;
    for (const f of batch) { if (!seen.has(f.tid)) { seen.add(f.tid); out.push(f); added++; } }
    const last = batch[batch.length - 1].time;
    if (added === 0 || batch.length < 2000) break;
    cursor = last + 1;
  }
  return out.sort((a, b) => a.time - b.time);
}

// ---------------------------------------------------------------------------
// Ledger classification. Pure, unit-tested.
// ---------------------------------------------------------------------------

export type FlowKind = 'deposit' | 'withdrawal' | 'fee_payment' | 'transfer_in' | 'transfer_out' | 'unclassified';

export type ClassifiedFlow = {
  kind: FlowKind;
  amount: number;      // USD that entered (+) or left the wallet, always positive
  venueFee: number;
  counterparty: string | null;
};

/**
 * Map one ledger delta to a flow from the customer's point of view.
 * Returns null for movements that do not change the wallet's USD total
 * (spot <-> perp class transfers).
 *
 * Any outflow to the AlphaEdge fee address is a fee payment. Every other
 * outflow (withdrawal to a bank or exchange, transfer to another wallet,
 * vault deposit) is treated as money leaving the managed account and
 * crystallises the fee. Inflows are capital.
 */
export function classifyLedger(e: LedgerEntry, wallet: string, feeAddress: string | null): ClassifiedFlow | null {
  const d = e.delta || {};
  const me = normAddr(wallet);
  const fee = feeAddress ? normAddr(feeAddress) : null;
  const user = typeof d.user === 'string' ? normAddr(d.user) : null;
  const dest = typeof d.destination === 'string' ? normAddr(d.destination) : null;

  switch (d.type) {
    case 'deposit':
      return { kind: 'deposit', amount: num(d.usdc), venueFee: 0, counterparty: null };

    case 'withdraw':
      // usdc is the gross amount debited; the $1 bridge fee is inside it.
      return { kind: 'withdrawal', amount: num(d.usdc), venueFee: num(d.fee), counterparty: null };

    case 'accountClassTransfer':
      return null; // spot <-> perp inside the same wallet

    case 'internalTransfer':
    case 'subAccountTransfer':
    case 'spotTransfer':
    case 'send': {
      const amount = d.type === 'spotTransfer' || d.type === 'send'
        ? num(d.usdcValue ?? d.amount)
        : num(d.usdc);
      const venueFee = num(d.fee);
      if (user === me && dest && fee && dest === fee) {
        return { kind: 'fee_payment', amount, venueFee, counterparty: dest };
      }
      if (user === me) return { kind: 'transfer_out', amount, venueFee, counterparty: dest };
      if (dest === me) return { kind: 'transfer_in', amount, venueFee: 0, counterparty: user };
      return { kind: 'unclassified', amount, venueFee, counterparty: dest };
    }

    case 'vaultDeposit':
      return { kind: 'transfer_out', amount: num(d.usdc), venueFee: 0, counterparty: d.vault ? normAddr(d.vault) : null };

    case 'vaultWithdraw':
      return { kind: 'transfer_in', amount: num(d.netWithdrawnUsd ?? d.requestedUsd), venueFee: 0, counterparty: d.vault ? normAddr(d.vault) : null };

    default:
      // Unknown or P&L-like (liquidation, rewards). Recorded for review but
      // excluded from fee arithmetic.
      return { kind: 'unclassified', amount: Math.abs(num(d.usdc ?? d.amount)), venueFee: 0, counterparty: null };
  }
}

export const isInflow = (k: FlowKind) => k === 'deposit' || k === 'transfer_in';
export const isOutflow = (k: FlowKind) => k === 'withdrawal' || k === 'transfer_out' || k === 'fee_payment';
