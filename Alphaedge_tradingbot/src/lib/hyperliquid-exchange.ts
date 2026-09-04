import { keccak256 } from 'viem';
import { privateKeyToAccount } from 'viem/accounts';
import { encode as msgpackEncode } from '@msgpack/msgpack';

// ---------------------------------------------------------------------------
// Real Hyperliquid order placement.
//
// Everything here FAILS CLOSED. This module either places a genuine order and
// reports what the exchange actually returned, or it throws. It never invents
// an order id, never assumes a fill, and never reports success it cannot
// evidence — the previous stub did, and those fabricated fills reached the
// ledger.
//
// Orders are signed by an API (agent) wallet, which on Hyperliquid can trade
// but cannot withdraw. The agent key signs; the MASTER account address is what
// info queries are addressed to. They are different values and both are needed.
//
// Required environment (none are read at import time):
//   HYPERLIQUID_AGENT_PRIVATE_KEY  0x-prefixed 32-byte agent/API wallet key
//   HYPERLIQUID_ACCOUNT_ADDRESS    0x master account the agent acts for
//   HYPERLIQUID_ENABLE_LIVE        must be exactly "true" to place any order
//   HYPERLIQUID_NETWORK            "mainnet" | "testnet"   (default testnet)
//   HYPERLIQUID_MAX_ORDER_NOTIONAL_USD  optional absolute backstop, in USD
//   HYPERLIQUID_SLIPPAGE_BPS       optional, default 50 (0.50%)
// ---------------------------------------------------------------------------

export type Network = 'mainnet' | 'testnet';

export function network(): Network {
  // Default to testnet: an unset/typo'd value must never mean "real money".
  return process.env.HYPERLIQUID_NETWORK === 'mainnet' ? 'mainnet' : 'testnet';
}

function apiBase(): string {
  return network() === 'mainnet'
    ? 'https://api.hyperliquid.xyz'
    : 'https://api.hyperliquid-testnet.xyz';
}

// Signature domain separator: "a" = mainnet, "b" = testnet.
function signatureSource(): 'a' | 'b' {
  return network() === 'mainnet' ? 'a' : 'b';
}

export function liveTradingEnabled(): boolean {
  return process.env.HYPERLIQUID_ENABLE_LIVE === 'true';
}

export function accountAddress(): string {
  const a = (process.env.HYPERLIQUID_ACCOUNT_ADDRESS || '').trim();
  if (!/^0x[0-9a-fA-F]{40}$/.test(a)) {
    throw new Error('HYPERLIQUID_ACCOUNT_ADDRESS is missing or not a 20-byte 0x address');
  }
  return a;
}

function agentAccount() {
  const k = (process.env.HYPERLIQUID_AGENT_PRIVATE_KEY || '').trim();
  if (!/^0x[0-9a-fA-F]{64}$/.test(k)) {
    throw new Error('HYPERLIQUID_AGENT_PRIVATE_KEY is missing or not a 32-byte 0x key');
  }
  return privateKeyToAccount(k as `0x${string}`);
}

// ---------------------------------------------------------------------------
// Asset metadata — asset INDEX and szDecimals are required to build an order.
// ---------------------------------------------------------------------------

export interface PerpAsset {
  name: string;
  index: number;
  szDecimals: number;
}

let metaCache: { at: number; assets: Map<string, PerpAsset> } | null = null;
const META_TTL_MS = 10 * 60_000;

export async function getPerpAssets(): Promise<Map<string, PerpAsset>> {
  if (metaCache && Date.now() - metaCache.at < META_TTL_MS) return metaCache.assets;

  const res = await fetch(`${apiBase()}/info`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type: 'meta' }),
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`Hyperliquid meta request failed: HTTP ${res.status}`);

  const data = await res.json();
  const universe = data?.universe;
  if (!Array.isArray(universe) || universe.length === 0) {
    throw new Error('Hyperliquid meta returned no universe');
  }

  const assets = new Map<string, PerpAsset>();
  universe.forEach((u: { name?: string; szDecimals?: number }, index: number) => {
    if (!u?.name || typeof u.szDecimals !== 'number') return;
    assets.set(u.name, { name: u.name, index, szDecimals: u.szDecimals });
  });

  metaCache = { at: Date.now(), assets };
  return assets;
}

// The app names the same instrument several ways depending on the caller:
// bot templates carry 'BTC' / 'ETH' / 'XAUUSD', the engine uses 'BTC-PERP' /
// 'ETH-PERP' / 'XAU'. Gold is traded as PAXG, the tokenised-gold perp.
const SYMBOL_ALIASES: Record<string, string> = {
  'BTC': 'BTC', 'BTC-PERP': 'BTC', 'BTCUSD': 'BTC', 'BTCUSDT': 'BTC',
  'ETH': 'ETH', 'ETH-PERP': 'ETH', 'ETHUSD': 'ETH', 'ETHUSDT': 'ETH',
  'XAU': 'PAXG', 'XAUUSD': 'PAXG', 'GOLD': 'PAXG', 'PAXG': 'PAXG',
};

export function resolveCoin(symbol: string): string {
  const key = (symbol || '').trim().toUpperCase();
  const coin = SYMBOL_ALIASES[key];
  if (!coin) throw new Error(`No Hyperliquid mapping for symbol "${symbol}"`);
  return coin;
}

// ---------------------------------------------------------------------------
// Wire formatting. Hyperliquid rejects prices/sizes that break these rules, so
// getting them wrong means a rejected order rather than a bad fill.
// ---------------------------------------------------------------------------

// Avoid exponential notation, which the API will not parse.
function plain(n: number): string {
  if (!Number.isFinite(n)) throw new Error(`Refusing to send non-finite number: ${n}`);
  const s = String(n);
  if (!s.includes('e') && !s.includes('E')) return s;
  return n.toFixed(12).replace(/\.?0+$/, '');
}

// Size: rounded to the asset's szDecimals.
export function formatSize(size: number, szDecimals: number): string {
  const rounded = Number(size.toFixed(szDecimals));
  if (!(rounded > 0)) {
    throw new Error(`Size ${size} rounds to zero at ${szDecimals} decimals — order not sent`);
  }
  return plain(rounded);
}

// Price: at most 5 significant figures AND at most (6 - szDecimals) decimal
// places for perps. Integer prices are exempt from the significant-figure cap.
export function formatPrice(price: number, szDecimals: number): string {
  if (!Number.isFinite(price) || price <= 0) {
    throw new Error(`Invalid price ${price} — order not sent`);
  }
  const maxDecimals = Math.max(0, 6 - szDecimals);
  const sigFigs = Number(price.toPrecision(5));
  const rounded = Number(sigFigs.toFixed(maxDecimals));
  if (!(rounded > 0)) {
    throw new Error(`Price ${price} rounds to zero — order not sent`);
  }
  return plain(rounded);
}

// ---------------------------------------------------------------------------
// Signing
// ---------------------------------------------------------------------------

function actionHash(action: unknown, nonce: number, vaultAddress: string | null): `0x${string}` {
  const packed = msgpackEncode(action);
  const suffix = vaultAddress ? 21 : 1;
  const buf = new Uint8Array(packed.length + 8 + suffix);
  buf.set(packed, 0);

  // nonce as 8-byte big-endian
  const view = new DataView(buf.buffer, packed.length, 8);
  view.setBigUint64(0, BigInt(nonce), false);

  if (vaultAddress) {
    buf[packed.length + 8] = 1;
    const hex = vaultAddress.slice(2);
    for (let i = 0; i < 20; i++) buf[packed.length + 9 + i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  } else {
    buf[packed.length + 8] = 0;
  }

  return keccak256(buf);
}

async function signAction(action: unknown, nonce: number) {
  const hash = actionHash(action, nonce, null);
  const signature = await agentAccount().signTypedData({
    domain: {
      name: 'Exchange',
      version: '1',
      chainId: 1337,
      verifyingContract: '0x0000000000000000000000000000000000000000',
    },
    types: {
      Agent: [
        { name: 'source', type: 'string' },
        { name: 'connectionId', type: 'bytes32' },
      ],
    },
    primaryType: 'Agent',
    message: { source: signatureSource(), connectionId: hash },
  });

  // viem returns packed 65-byte r||s||v; Hyperliquid wants the components.
  return {
    r: `0x${signature.slice(2, 66)}`,
    s: `0x${signature.slice(66, 130)}`,
    v: parseInt(signature.slice(130, 132), 16),
  };
}

async function exchangePost(action: unknown, nonce: number): Promise<any> {
  const signature = await signAction(action, nonce);
  const res = await fetch(`${apiBase()}/exchange`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, nonce, signature }),
    cache: 'no-store',
  });

  const text = await res.text();
  if (!res.ok) {
    throw new Error(`Hyperliquid /exchange HTTP ${res.status}: ${text.slice(0, 300)}`);
  }
  let json: any;
  try {
    json = JSON.parse(text);
  } catch {
    throw new Error(`Hyperliquid /exchange returned non-JSON: ${text.slice(0, 300)}`);
  }
  if (json?.status !== 'ok') {
    throw new Error(`Hyperliquid rejected the action: ${JSON.stringify(json?.response ?? json).slice(0, 300)}`);
  }
  return json;
}

// ---------------------------------------------------------------------------
// Order placement
// ---------------------------------------------------------------------------

export interface LiveFill {
  orderId: string;
  filledSize: number;
  avgPrice: number;
  resting: boolean;
}

export interface LiveOrderRequest {
  symbol: string;
  side: 'buy' | 'sell';
  size: number;          // in base units (contracts/coins), pre-risk-check
  referencePrice: number; // current mark; the IOC limit is derived from it
  reduceOnly?: boolean;
}

/**
 * Places a real IOC order. Hyperliquid has no market order, so this is a
 * marketable limit priced through the book by HYPERLIQUID_SLIPPAGE_BPS.
 *
 * Throws on anything short of a confirmed exchange response. A rejection, a
 * zero fill, or an unrecognised payload all raise — callers must not record a
 * fill unless this returns.
 */
export async function placeLiveOrder(req: LiveOrderRequest): Promise<LiveFill> {
  if (!liveTradingEnabled()) {
    throw new Error('Live trading is disabled (HYPERLIQUID_ENABLE_LIVE is not "true")');
  }

  const coin = resolveCoin(req.symbol);
  const assets = await getPerpAssets();
  const asset = assets.get(coin);
  if (!asset) throw new Error(`Coin ${coin} is not in the Hyperliquid perp universe`);

  // Absolute notional backstop, independent of risk.ts. Optional: unset means
  // the existing risk rules are the only gate.
  const capRaw = process.env.HYPERLIQUID_MAX_ORDER_NOTIONAL_USD;
  if (capRaw) {
    const cap = parseFloat(capRaw);
    const notional = req.size * req.referencePrice;
    if (Number.isFinite(cap) && cap > 0 && notional > cap) {
      throw new Error(`Order notional $${notional.toFixed(2)} exceeds HYPERLIQUID_MAX_ORDER_NOTIONAL_USD ($${cap})`);
    }
  }

  const isBuy = req.side === 'buy';
  const slippageBps = Math.max(0, parseFloat(process.env.HYPERLIQUID_SLIPPAGE_BPS || '50'));
  const limitRaw = req.referencePrice * (isBuy ? 1 + slippageBps / 10_000 : 1 - slippageBps / 10_000);

  // Key order matters: the action is msgpack'd and hashed, so it must be built
  // exactly as Hyperliquid serialises it.
  const action = {
    type: 'order',
    orders: [{
      a: asset.index,
      b: isBuy,
      p: formatPrice(limitRaw, asset.szDecimals),
      s: formatSize(req.size, asset.szDecimals),
      r: req.reduceOnly === true,
      t: { limit: { tif: 'Ioc' } },
    }],
    grouping: 'na',
  };

  const json = await exchangePost(action, Date.now());

  const status = json?.response?.data?.statuses?.[0];
  if (!status) {
    throw new Error(`Hyperliquid returned no order status: ${JSON.stringify(json).slice(0, 300)}`);
  }
  if (status.error) {
    throw new Error(`Hyperliquid rejected the order: ${status.error}`);
  }

  if (status.filled) {
    const filledSize = parseFloat(status.filled.totalSz);
    const avgPrice = parseFloat(status.filled.avgPx);
    if (!(filledSize > 0) || !Number.isFinite(avgPrice)) {
      throw new Error(`Hyperliquid reported an unusable fill: ${JSON.stringify(status.filled)}`);
    }
    return { orderId: String(status.filled.oid), filledSize, avgPrice, resting: false };
  }

  // An IOC that rests filled nothing — treat as no trade, not as success.
  if (status.resting) {
    throw new Error(`IOC order did not fill (rested as oid ${status.resting.oid}) — no position taken`);
  }

  throw new Error(`Unrecognised Hyperliquid order status: ${JSON.stringify(status).slice(0, 300)}`);
}

// ---------------------------------------------------------------------------
// Account reads — addressed to the MASTER account, never the agent key.
// ---------------------------------------------------------------------------

export async function getClearinghouseState(): Promise<any> {
  const res = await fetch(`${apiBase()}/info`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type: 'clearinghouseState', user: accountAddress() }),
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`Hyperliquid clearinghouseState failed: HTTP ${res.status}`);
  return res.json();
}
