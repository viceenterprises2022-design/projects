import { NextResponse } from 'next/server';
import { requireOwner } from '@/lib/authz';
import {
  network,
  liveTradingEnabled,
  accountAddress,
  agentAddress,
  getExtraAgents,
  getPerpAssets,
  getClearinghouseState,
  resolveCoin,
} from '@/lib/hyperliquid-exchange';

export const dynamic = 'force-dynamic';

// ---------------------------------------------------------------------------
// Owner-only configuration audit for live trading.
//
// Reports whether each piece of configuration is PRESENT and COHERENT. It never
// returns a secret: the agent private key is only ever used to derive its own
// public address, which is the value Hyperliquid itself publishes in the
// approved-agents list.
//
// The load-bearing check is `agentApproved`. A key can be perfectly well-formed
// and still be unable to trade because it was never approved on the account —
// that failure would otherwise only surface on the first real order.
// ---------------------------------------------------------------------------

// Records a check without letting one failure hide the others.
function attempt<T>(fn: () => T): { ok: true; value: T } | { ok: false; error: string } {
  try {
    return { ok: true, value: fn() };
  } catch (err: any) {
    return { ok: false, error: err?.message || 'failed' };
  }
}

async function attemptAsync<T>(fn: () => Promise<T>): Promise<{ ok: true; value: T } | { ok: false; error: string }> {
  try {
    return { ok: true, value: await fn() };
  } catch (err: any) {
    return { ok: false, error: err?.message || 'failed' };
  }
}

const ENCRYPTION_FALLBACK = 'development_master_key_must_be_32_bytes_long_!!';

export async function GET() {
  const denied = await requireOwner();
  if (denied) return NextResponse.json({ error: denied }, { status: 403 });

  const checks: Array<{ id: string; ok: boolean; detail: string; blocking: boolean }> = [];
  const add = (id: string, ok: boolean, detail: string, blocking = true) =>
    checks.push({ id, ok, detail, blocking });

  // --- 1. Switches -----------------------------------------------------------
  const net = network();
  add('network', true, `HYPERLIQUID_NETWORK resolves to "${net}"${process.env.HYPERLIQUID_NETWORK ? '' : ' (unset — defaulted to testnet)'}`, false);

  const enabled = liveTradingEnabled();
  add('liveEnabled', enabled,
    enabled ? 'HYPERLIQUID_ENABLE_LIVE is "true" — live orders permitted'
            : 'HYPERLIQUID_ENABLE_LIVE is not "true" — every live order will be refused');

  // --- 2. Identities ---------------------------------------------------------
  const acct = attempt(accountAddress);
  add('accountAddress', acct.ok, acct.ok ? `master account ${acct.value}` : acct.error);

  const agent = attempt(agentAddress);
  add('agentKey', agent.ok, agent.ok ? `agent wallet ${agent.value}` : agent.error);

  // --- 3. The check that actually predicts whether an order can be signed ----
  if (acct.ok && agent.ok) {
    const extras = await attemptAsync(getExtraAgents);
    if (!extras.ok) {
      add('agentApproved', false, `could not read approved agents: ${extras.error}`);
    } else {
      const wanted = agent.value.toLowerCase();
      const match = extras.value.find(a => (a?.address || '').toLowerCase() === wanted);
      const names = extras.value.map(a => a?.address).filter(Boolean);
      add('agentApproved', Boolean(match),
        match
          ? `agent is approved on the account${match.validUntil ? `, valid until ${new Date(match.validUntil).toISOString()}` : ''}`
          : `agent ${agent.value} is NOT in the account's approved list (${names.length ? names.join(', ') : 'no agents approved'}) — approve it on Hyperliquid under API wallets`);
    }
  } else {
    add('agentApproved', false, 'skipped — account address or agent key missing');
  }

  // --- 4. Exchange reachability and the assets we trade ----------------------
  const assets = await attemptAsync(getPerpAssets);
  if (!assets.ok) {
    add('exchangeReachable', false, `meta request failed: ${assets.error}`);
  } else {
    add('exchangeReachable', true, `${assets.value.size} perps in the ${net} universe`, false);
    for (const symbol of ['XAU', 'BTC-PERP', 'ETH-PERP']) {
      const coin = attempt(() => resolveCoin(symbol));
      const meta = coin.ok ? assets.value.get(coin.value) : undefined;
      add(`asset:${symbol}`, Boolean(meta),
        meta ? `${symbol} → ${meta.name} (index ${meta.index}, szDecimals ${meta.szDecimals})`
             : `${symbol} could not be resolved in the ${net} universe`);
    }
  }

  // --- 5. Does the account actually hold anything? --------------------------
  if (acct.ok) {
    const state = await attemptAsync(getClearinghouseState);
    if (!state.ok) {
      add('accountFunded', false, `clearinghouseState failed: ${state.error}`);
    } else {
      const value = parseFloat(state.value?.marginSummary?.accountValue || '0');
      const withdrawable = parseFloat(state.value?.marginSummary?.withdrawable || '0');
      const positions = (state.value?.assetPositions || []).length;
      add('accountFunded', value > 0,
        value > 0 ? `account value $${value.toFixed(2)}, withdrawable $${withdrawable.toFixed(2)}, ${positions} open position(s)`
                  : `account value is $0 on ${net} — orders will be rejected for insufficient margin`);
    }
  }

  // --- 6. Credential storage -------------------------------------------------
  const masterKey = process.env.ENCRYPTION_MASTER_KEY || '';
  add('encryptionMasterKey', Boolean(masterKey) && masterKey !== ENCRYPTION_FALLBACK,
    !masterKey ? 'ENCRYPTION_MASTER_KEY is unset — stored credentials use the fallback key that is public in the repo'
      : masterKey === ENCRYPTION_FALLBACK ? 'ENCRYPTION_MASTER_KEY is set to the public fallback value — change it'
      : 'ENCRYPTION_MASTER_KEY is set to a custom value');

  // --- 7. Optional guards ----------------------------------------------------
  const cap = process.env.HYPERLIQUID_MAX_ORDER_NOTIONAL_USD;
  add('notionalCap', true,
    cap ? `per-order backstop $${cap}` : 'no absolute per-order cap set — risk.ts rules are the only gate', false);
  add('slippage', true, `IOC priced ${process.env.HYPERLIQUID_SLIPPAGE_BPS || '50'} bps through the book`, false);

  const blocking = checks.filter(c => c.blocking && !c.ok);
  return NextResponse.json({
    success: true,
    network: net,
    readyToTrade: blocking.length === 0,
    blockingFailures: blocking.map(c => c.id),
    checks,
    note: 'A green preflight means the configuration is coherent. It does NOT mean an order has ever been placed — run the testnet order test before going to mainnet.',
  });
}
