// Profit-share engine. Pure functions only: no DB, no network, no clock.
//
// Owner's rule (2026-10-25): AlphaEdge's share = (balance - capital) x that
// customer's profit-share %, charged on profit only, never on capital, and
// nothing on a loss. Example: capital 1,000, balance 1,500, profit 500:
// 10% -> 50, 50% -> 250.
//
// Constraint from HLD §4.5: the platform trades through agent keys that have
// NO withdrawal rights, so a fee can never be debited from the customer's
// wallet. The engine therefore only computes what is OWED; the customer
// remits it to the AlphaEdge fee wallet and the payment is matched later.
//
// Accounting model, one number per customer:
//   capitalBasis   the figure profit is measured against. Starts at the
//                  onboarding capital, moves with deposits and withdrawals.
//   outstandingFee fee crystallised but not yet paid. It is still sitting in
//                  the customer's wallet, so it is subtracted from profit;
//                  otherwise an unpaid fee would be charged again as profit.
//
//   profit = balance - capitalBasis - outstandingFee
//
// Withdrawals SETTLE ALL PROFIT (owner-approved default): the full current
// profit is crystallised at the customer's rate, and the basis resets so that
// profit is exactly zero afterwards. The same gain can never be charged twice.
// If the account is at a loss, nothing is charged and the basis moves down by
// the withdrawn amount only, which carries the loss forward: the customer
// pays nothing on the recovery until it climbs back above the old level
// (the high-water mark property from HLD §4.5.2).

export type FeeState = {
  capitalBasis: number;
  outstandingFee: number;
};

export type FlowEvent =
  | { kind: 'deposit'; amount: number }
  | { kind: 'withdrawal'; amount: number; balanceBefore: number; pct: number }
  | { kind: 'fee_payment'; amount: number }
  | { kind: 'waiver'; amount: number };

export type FeeOutcome = {
  state: FeeState;
  // Present when the event crystallised or moved a fee. Every field is
  // re-derivable from the inputs, so the customer's statement can show the
  // arithmetic (HLD NFR-10).
  record: {
    profit: number;          // profit measured at the event (withdrawals only)
    fee: number;             // fee crystallised by this event (0 if none)
    appliedToFee: number;    // amount of a payment or waiver applied to the fee
    excess: number;          // payment beyond what was owed, treated as an outflow
  };
};

// Money is stored as floats; round to cents at every state transition so the
// ledger never accumulates sub-cent drift across thousands of events.
export const cents = (n: number): number => Math.round(n * 100) / 100;

export function currentProfit(balance: number, s: FeeState): number {
  return cents(balance - s.capitalBasis - s.outstandingFee);
}

/** Fee the customer would owe if they withdrew right now. */
export function feeIfWithdrawnNow(balance: number, s: FeeState, pct: number): number {
  const p = currentProfit(balance, s);
  return p > 0 ? cents(p * pct / 100) : 0;
}

export function validatePct(pct: unknown): number {
  const n = typeof pct === 'string' ? Number(pct) : pct;
  if (typeof n !== 'number' || !Number.isFinite(n) || n < 0 || n > 100) {
    throw new Error('Profit share must be a number between 0 and 100');
  }
  return cents(n);
}

export function applyEvent(s: FeeState, e: FlowEvent): FeeOutcome {
  const none = { profit: 0, fee: 0, appliedToFee: 0, excess: 0 };
  if (!(e.amount >= 0) || !Number.isFinite(e.amount)) {
    throw new Error(`Invalid ${e.kind} amount: ${e.amount}`);
  }

  switch (e.kind) {
    case 'deposit':
      // New money is capital, never profit.
      return { state: { ...s, capitalBasis: cents(s.capitalBasis + e.amount) }, record: none };

    case 'withdrawal': {
      const profit = cents(e.balanceBefore - s.capitalBasis - s.outstandingFee);
      if (profit <= 0) {
        // Loss or flat: no fee, loss gap preserved.
        return {
          state: { ...s, capitalBasis: cents(s.capitalBasis - e.amount) },
          record: { ...none, profit },
        };
      }
      const fee = cents(profit * e.pct / 100);
      const outstandingFee = cents(s.outstandingFee + fee);
      // Choose the basis so that profit after the withdrawal is exactly zero:
      //   (balanceBefore - amount) - basis - outstanding = 0
      const capitalBasis = cents(e.balanceBefore - e.amount - outstandingFee);
      return { state: { capitalBasis, outstandingFee }, record: { ...none, profit, fee } };
    }

    case 'fee_payment': {
      // Balance falls by the payment and so does the debt: profit unchanged.
      const applied = cents(Math.min(e.amount, Math.max(0, s.outstandingFee)));
      const excess = cents(e.amount - applied);
      return {
        state: {
          outstandingFee: cents(s.outstandingFee - applied),
          // Anything paid beyond the debt left the wallet like any outflow.
          capitalBasis: cents(s.capitalBasis - excess),
        },
        record: { ...none, appliedToFee: applied, excess },
      };
    }

    case 'waiver': {
      // The customer keeps money that was counted as owed. Raise the basis by
      // the same amount, or the waived sum would reappear as profit and be
      // charged at the next withdrawal.
      const applied = cents(Math.min(e.amount, Math.max(0, s.outstandingFee)));
      return {
        state: {
          outstandingFee: cents(s.outstandingFee - applied),
          capitalBasis: cents(s.capitalBasis + applied),
        },
        record: { ...none, appliedToFee: applied },
      };
    }
  }
}
