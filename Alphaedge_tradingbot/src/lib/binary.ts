// Shared binary-round math — used by the server engine and settlement APIs.

export function normCDF(x: number) {
  const a1 = 0.254829592, a2 = -0.284496736, a3 = 1.421413741;
  const a4 = -1.453152027, a5 = 1.061405429, p = 0.3275911;
  const sign = x < 0 ? -1 : 1;
  const absX = Math.abs(x) / Math.sqrt(2.0);
  const t = 1.0 / (1.0 + p * absX);
  const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-absX * absX);
  return 0.5 * (1.0 + sign * y);
}

export const SECONDS_PER_YEAR = 31_536_000;

// Driftless GBM binary fair value: P(BUY) = Φ((S−K)/σ), σ = S·vol·√(t/yr)
export function binaryFairValue(price: number, strike: number, annualVolPct: number, secondsRemaining: number) {
  const sigmaUsd = price * (annualVolPct / 100) * Math.sqrt(Math.max(secondsRemaining, 0.001) / SECONDS_PER_YEAR);
  const z = (price - strike) / Math.max(sigmaUsd, 1e-9);
  return { pYes: Math.min(Math.max(normCDF(z), 0.01), 0.99), z, sigmaUsd };
}

// Binary settlement: BUY wins when expiry > strike (SELL wins at/below); winners pay $1.00/contract.
export function settleBinary(strike: number, expiry: number, side: 'BUY' | 'SELL', size: number, entryPrice: number) {
  const winningSide = expiry > strike ? 'BUY' : 'SELL';
  const won = side === winningSide;
  const cost = size * entryPrice;
  const payout = won ? size * 1.0 : 0;
  return {
    outcome: won ? 'WIN' : 'LOSS',
    exitPrice: won ? 1.0 : 0.0,
    pnl: Math.round((payout - cost) * 100) / 100,
  };
}
