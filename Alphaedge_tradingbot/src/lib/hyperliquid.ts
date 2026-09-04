import { placeLiveOrder, getClearinghouseState } from './hyperliquid-exchange';

export interface HyperliquidBalance {
  coin: string;
  equity: number;
  available: number;
}

export interface HyperliquidPosition {
  coin: string;
  szi: number; // size, positive for long, negative for short
  entryPx: number;
  unrealizedPnl: number;
}

export interface OrderResult {
  success: boolean;
  orderId?: string;
  error?: string;
  fillPrice?: number;
  /** Actual size filled. Present on live fills; paper fills assume full size. */
  filledQty?: number;
}

export async function getBalances(apiKey: string, mode: 'paper' | 'live'): Promise<HyperliquidBalance[]> {
  if (mode === 'paper' || apiKey.startsWith('mock_') || apiKey.startsWith('demo_') || apiKey === 'placeholder') {
    return [
      { coin: 'USDC', equity: 10000.0, available: 8500.0 },
      { coin: 'BTC', equity: 0.0, available: 0.0 },
      { coin: 'ETH', equity: 0.0, available: 0.0 }
    ];
  }

  try {
    // Addressed to the master account in HYPERLIQUID_ACCOUNT_ADDRESS, and to
    // the network in HYPERLIQUID_NETWORK. The stored connection key is not an
    // address under the agent-wallet model, so querying it would return an
    // empty account and silently display a zero balance as if it were real.
    const data = await getClearinghouseState();

    const marginSummary = data.marginSummary;
    const equity = parseFloat(marginSummary?.accountValue || '0');
    const available = parseFloat(marginSummary?.withdrawable || '0');
    
    return [
      { coin: 'USDC', equity, available }
    ];
  } catch (err: any) {
    console.error('Error fetching real HL balances:', err.message);
    return [{ coin: 'USDC', equity: 0, available: 0 }];
  }
}

export async function getPositions(apiKey: string, mode: 'paper' | 'live'): Promise<HyperliquidPosition[]> {
  if (mode === 'paper' || apiKey.startsWith('mock_') || apiKey.startsWith('demo_') || apiKey === 'placeholder') {
    return [];
  }

  try {
    const data = await getClearinghouseState();

    const assetPositions = data.assetPositions || [];
    return assetPositions.map((p: any) => ({
      coin: p.position.coin,
      szi: parseFloat(p.position.szi),
      entryPx: parseFloat(p.position.entryPx),
      unrealizedPnl: parseFloat(p.position.unrealizedPnl)
    }));
  } catch (err: any) {
    console.error('Error fetching real HL positions:', err.message);
    return [];
  }
}

export async function placeOrder(
  apiKey: string,
  mode: 'paper' | 'live',
  symbol: string,
  side: 'buy' | 'sell',
  qty: number,
  price: number
): Promise<OrderResult> {
  if (mode === 'paper' || apiKey.startsWith('mock_') || apiKey.startsWith('demo_') || apiKey === 'placeholder') {
    const orderId = `mock_ord_${Math.random().toString(36).substring(2, 11)}`;
    return {
      success: true,
      orderId,
      fillPrice: price
    };
  }

  // LIVE — a real, signed order on Hyperliquid.
  //
  // placeLiveOrder throws unless the exchange confirmed an actual fill, so
  // there is no path here that reports success without one. This previously
  // returned a fabricated order id and a fill at the requested price WITHOUT
  // CONTACTING THE EXCHANGE, and the dispatcher wrote those invented fills
  // into the ledger.
  //
  // The stored per-connection apiKey is deliberately unused: signing authority
  // is the agent wallet in HYPERLIQUID_AGENT_PRIVATE_KEY, which can trade but
  // not withdraw. A database row must never be able to move real funds.
  try {
    const fill = await placeLiveOrder({
      symbol,
      side,
      size: qty,
      referencePrice: price,
    });
    return {
      success: true,
      orderId: fill.orderId,
      fillPrice: fill.avgPrice,
      filledQty: fill.filledSize,
    };
  } catch (err: any) {
    return {
      success: false,
      error: err?.message || 'Hyperliquid execution failed',
    };
  }
}
