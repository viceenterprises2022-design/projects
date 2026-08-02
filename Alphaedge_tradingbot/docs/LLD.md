# Prospera — Low-Level Design

## Document control

| Field | Value |
|---|---|
| Document | Low-Level Design (LLD) |
| System | Prospera — production trading platform (`Alphaedge_live/`) |
| Version | 1.2 — environments & promotion revision |
| Date | 2026-07-28 |
| Status | Draft. Implementable as written; §21 sequences it against the ten-day plan |
| Parent | [HLD.md](HLD.md) v1.2 — decisions 1–20 |

### Scope

Specifies the trading core, data model, execution path, reconciliation, attribution and billing in
enough detail to implement without further design work. Covers everything on the day-1..10 critical
path.

**Deferred to LLD phase 2 (post-launch):** agent tool implementations, the publication gate
internals, and client-surface components. Their contracts are fixed by HLD §4.3–4.4 and
[AGENT_OPERATIONS.md](AGENT_OPERATIONS.md); nothing here blocks them.

### Reference facts established by research

| Fact | Source | Design impact |
|---|---|---|
| IP limit: 1200 weight/min aggregated REST. Unbatched action = weight 1 | Hyperliquid rate-limit docs | §10 fan-out budget |
| Address limit: 10k initial buffer, then 1 request per 1 USDC traded | Same | Not expected to bind; §9.6 |
| Nonce must be within `(T−2d, T+1d)`; the **100 highest nonces per signer** are tracked; a new nonce must exceed the smallest of that set and never have been used | Nonces and API wallets | §9.2 nonce allocator, clock-skew guard |
| Nonces are tracked **per signer** (API wallet address), not per account | Same | One API wallet per client account ⇒ isolated nonce spaces |
| Deregistered API wallets can have prior actions replayed once the nonce set prunes | Same | §9.7 offboarding must not reuse wallet addresses |
| **ALO-only batches are prioritised by validators**; batch every ~0.1 s with an atomic counter | Same | §9.4 maker leg uses ALO; §10 batching cadence |
| Builder codes charge up to 0.1% per fill | Builder codes docs | Rejected as primary rail — HLD §4.5.3a |

---

## 1. Module structure

```
Alphaedge_live/
├── src/
│   ├── app/                        # Next.js 16 App Router — surfaces only
│   │   ├── (client)/               # client app: positions, statements, trade reasons
│   │   ├── (owner)/                # operator console
│   │   └── api/                    # route handlers, §15
│   ├── domain/                     # pure types + pure functions. No I/O anywhere.
│   │   ├── types.ts
│   │   ├── strategy/               # §7 — signal evaluation
│   │   ├── risk/                   # §8 — limit checks
│   │   └── attribution/            # §12 — P&L decomposition maths
│   ├── venues/                     # adapters — the only modules that know a venue
│   │   ├── adapter.ts              # VenueAdapter interface (§22)
│   │   ├── hyperliquid/            # signing, nonce, exchange, info, ws (§7–§9)
│   │   └── polymarket/             # CLOB client, L1/L2 auth, resolution watcher (§22, post-soak)
│   ├── db/                         # schema, migrations, query modules
│   ├── trigger/                    # §14 Trigger.dev task definitions
│   ├── services/                   # orchestration: fanout, reconcile, billing
│   └── lib/                        # logger, config, errors
└── trigger.config.ts
```

**The dependency rule, enforced in review:** `domain/` imports nothing from `venues/`, `db/`,
`trigger/` or `services/`. It is pure, synchronous, and unit-testable with no mocks. This is what
makes NFR-11 (replay determinism) achievable rather than aspirational — the same `domain/` functions
run in backtest, paper and live.

---

## 2. Domain model

```ts
// domain/types.ts — the whole system's vocabulary. No I/O types here.

// Instruments are DATA, not a union type (HLD §4.4a): Polymarket markets are ephemeral.
// InstrumentId is opaque; the instruments table (§3) is the source of truth.
export type InstrumentId = string;           // e.g. 'hl:BTC', 'pm:0x1a2b...'
export type InstrumentKind = 'perp' | 'binary';
export type Instrument = InstrumentId;        // alias — all Record<Instrument,...> below key on the opaque id
export type Side = 'long' | 'short';
export type RegimeMode = 'normal' | 'caution' | 'lockdown';
export type Tier = 1 | 2 | 3;

/** Immutable market view at one bar close. Everything the strategy may read. */
export interface MarketSnapshot {
  readonly at: number;                       // bar close, ms UTC
  readonly bars: Readonly<Record<Instrument, readonly Bar[]>>;   // ascending, ≥250 bars
  readonly mark: Readonly<Record<Instrument, number>>;
  readonly fundingRate: Readonly<Record<Instrument, number>>;    // current 8h rate
  readonly nextFundingAt: number;                                // ms UTC
  readonly topOfBook: Readonly<Record<Instrument, BookLevel>>;
}

export interface Bar { t: number; o: number; h: number; l: number; c: number; v: number }
export interface BookLevel { bid: number; ask: number; bidSz: number; askSz: number }

/** Per-account state the strategy and risk layers may read. */
export interface AccountState {
  readonly accountId: string;
  readonly tier: Tier;
  readonly equity: number;                   // from venue, reconciled
  readonly riskMultiplier: number;           // 0.5 | 1.0
  readonly positions: readonly Position[];
  readonly dayStartEquity: number;
  readonly pnlToday: number;
  readonly locks: readonly LockState[];
}

export interface Position {
  instrument: Instrument; side: Side; size: number;
  entryPrice: number; openedAt: number; intentId: string;
  stopPrice: number | null;
}

export type LockSource = 'owner' | 'regime' | 'profit' | 'loss';
export interface LockState { source: LockSource; since: number; until: number | null; reason: string }

/** Strategy output. Never mutated; risk approves or rejects it whole. */
export interface Intent {
  readonly id: string;                       // uuid v7 — time-ordered
  readonly accountId: string;
  readonly instrument: Instrument;
  readonly action: 'open' | 'close';
  readonly side: Side;
  readonly sizeUsd: number;                  // notional, pre-risk
  readonly decisionPrice: number;            // mark at decision — slippage baseline
  readonly signal: SignalMeta;
  readonly validUntil: number;               // ms UTC; expired intents are dropped, never queued
  readonly urgency: 'passive' | 'immediate'; // 'immediate' ⇒ skip maker leg (all exits)
}

export interface SignalMeta {
  readonly strategy: string;                 // 'S1' | 'S3' | 'S6'
  readonly reason: string;                   // human-readable, surfaced to the client
  readonly features: Readonly<Record<string, number>>;  // ER, ADX, ATR… for audit + A2
}

export type RiskVerdict =
  | { ok: true; approved: Intent }                          // size may be reduced
  | { ok: false; code: RiskReasonCode; detail: string };
```

`Intent.urgency` carries the maker/taker decision out of the execution layer and into the domain,
where it is testable. Every `action: 'close'` is `immediate` — HLD decision 10, protective exits
always taker.

---

## 3. Database schema

Postgres. Money as `numeric(24,8)`, never float. Timestamps as `bigint` ms UTC for consistency with
venue payloads. Abridged to the columns that carry design meaning.

```sql
CREATE TYPE account_status AS ENUM
  ('pending','approved','funded','active','dormant','suspended','closing','closed');

CREATE TABLE accounts (
  id                uuid PRIMARY KEY,
  user_id           uuid NOT NULL REFERENCES users(id),
  tier              smallint NOT NULL CHECK (tier IN (1,2,3)),
  status            account_status NOT NULL DEFAULT 'pending',
  risk_multiplier   numeric(3,2) NOT NULL DEFAULT 1.0 CHECK (risk_multiplier IN (0.5,1.0)),
  wallet_address    text NOT NULL,           -- master account, public. NOT a credential.
  api_wallet_ref    text,                    -- secrets-manager key ref. Never the key. B2/B3.
  api_wallet_addr   text,                    -- agent wallet address; nonce space identity
  venue             text NOT NULL DEFAULT 'hyperliquid',
  activated_at      bigint,
  created_at        bigint NOT NULL,
  UNIQUE (wallet_address, venue),
  UNIQUE (api_wallet_addr)                   -- never reuse an agent address (replay risk)
);

-- Instrument access is tier-derived (decision 14) but stored to allow per-account override.
CREATE TABLE account_instruments (
  account_id  uuid NOT NULL REFERENCES accounts(id),
  instrument  text NOT NULL,
  PRIMARY KEY (account_id, instrument)
);

CREATE TABLE intents (
  id              uuid PRIMARY KEY,          -- uuid v7
  account_id      uuid NOT NULL REFERENCES accounts(id),
  instrument      text NOT NULL,
  action          text NOT NULL CHECK (action IN ('open','close')),
  side            text NOT NULL,
  size_usd        numeric(24,8) NOT NULL,
  decision_price  numeric(24,8) NOT NULL,
  urgency         text NOT NULL,
  signal_json     jsonb NOT NULL,
  valid_until     bigint NOT NULL,
  status          text NOT NULL,             -- proposed|approved|rejected|executing|filled|abandoned|failed
  reject_code     text,
  batch_id        uuid,                      -- the fan-out that produced it
  queue_position  integer,                   -- normalised later; §10 fairness
  created_at      bigint NOT NULL
);
CREATE INDEX ON intents (account_id, created_at DESC);
CREATE INDEX ON intents (status) WHERE status IN ('approved','executing');

CREATE TABLE orders (
  id                uuid PRIMARY KEY,
  intent_id         uuid NOT NULL REFERENCES intents(id),
  account_id        uuid NOT NULL REFERENCES accounts(id),
  leg               text NOT NULL CHECK (leg IN ('maker','taker')),
  cloid             text NOT NULL UNIQUE,    -- derived from intent_id+leg; venue idempotency
  venue_oid         bigint,
  order_type        text NOT NULL,           -- 'alo' | 'ioc'
  limit_price       numeric(24,8) NOT NULL,
  size              numeric(24,8) NOT NULL,
  filled_size       numeric(24,8) NOT NULL DEFAULT 0,
  avg_fill_price    numeric(24,8),
  status            text NOT NULL,           -- pending|resting|partial|filled|cancelled|rejected
  nonce             bigint NOT NULL,
  submitted_at      bigint NOT NULL,
  terminal_at       bigint,
  UNIQUE (intent_id, leg)                    -- at most one maker + one taker leg per intent
);

CREATE TABLE fills (
  id             uuid PRIMARY KEY,
  order_id       uuid NOT NULL REFERENCES orders(id),
  account_id     uuid NOT NULL REFERENCES accounts(id),
  venue_fill_id  text NOT NULL,
  instrument     text NOT NULL,
  side           text NOT NULL,
  size           numeric(24,8) NOT NULL,
  price          numeric(24,8) NOT NULL,
  fee            numeric(24,8) NOT NULL,     -- signed: negative = rebate
  is_maker       boolean NOT NULL,
  closed_pnl     numeric(24,8),              -- venue-reported realised P&L on closing fills
  at             bigint NOT NULL,
  UNIQUE (venue_fill_id, account_id)         -- idempotent ingest from WS and REST alike
);

CREATE TABLE funding_payments (
  id          uuid PRIMARY KEY,
  account_id  uuid NOT NULL REFERENCES accounts(id),
  instrument  text NOT NULL,
  amount      numeric(24,8) NOT NULL,        -- signed: negative = paid
  at          bigint NOT NULL,
  UNIQUE (account_id, instrument, at)
);

CREATE TABLE positions (
  account_id    uuid NOT NULL REFERENCES accounts(id),
  instrument    text NOT NULL,
  side          text,
  size          numeric(24,8) NOT NULL DEFAULT 0,
  entry_price   numeric(24,8),
  stop_price    numeric(24,8),
  opened_at     bigint,
  intent_id     uuid,
  updated_at    bigint NOT NULL,
  PRIMARY KEY (account_id, instrument)
);

CREATE TABLE reconciliations (
  id            uuid PRIMARY KEY,
  account_id    uuid NOT NULL REFERENCES accounts(id),
  source        text NOT NULL,               -- 'ws' | 'rest_backstop'
  ok            boolean NOT NULL,
  diff_json     jsonb,
  venue_equity  numeric(24,8),
  at            bigint NOT NULL
);
CREATE INDEX ON reconciliations (account_id, at DESC);
CREATE INDEX ON reconciliations (at DESC) WHERE ok = false;

CREATE TABLE risk_events (
  id          uuid PRIMARY KEY,
  account_id  uuid REFERENCES accounts(id),
  intent_id   uuid REFERENCES intents(id),
  code        text NOT NULL,                 -- §17 taxonomy
  detail      text NOT NULL,
  at          bigint NOT NULL
);

-- Ledger: monotonic sequence, not timestamp. Fixes B4.
CREATE TABLE ledger_entries (
  seq          bigserial PRIMARY KEY,
  prev_hash    text NOT NULL,
  hash         text NOT NULL,
  entity_type  text NOT NULL,
  entity_id    uuid NOT NULL,
  account_id   uuid,
  payload      jsonb NOT NULL,
  at           bigint NOT NULL
);
CREATE TABLE ledger_head (          -- single row; the serialisation point
  id         boolean PRIMARY KEY DEFAULT true CHECK (id),
  last_seq   bigint NOT NULL DEFAULT 0,
  last_hash  text   NOT NULL
);

CREATE TABLE account_fairness (
  account_id      uuid PRIMARY KEY REFERENCES accounts(id),
  n_signals       integer NOT NULL DEFAULT 0,
  mean_position   numeric(6,5) NOT NULL DEFAULT 0.5,   -- normalised 0..1
  updated_at      bigint NOT NULL
);

CREATE TABLE fee_periods (
  id                uuid PRIMARY KEY,
  account_id        uuid NOT NULL REFERENCES accounts(id),
  period_start      bigint NOT NULL,
  period_end        bigint NOT NULL,
  cum_pnl           numeric(24,8) NOT NULL,   -- attributable, §12
  hwm_before        numeric(24,8) NOT NULL,
  hwm_after         numeric(24,8) NOT NULL,
  fee_gross         numeric(24,8) NOT NULL,
  rolled_forward    numeric(24,8) NOT NULL DEFAULT 0,
  invoice_id        uuid,
  crystallised_at   bigint NOT NULL,
  UNIQUE (account_id, period_start)
);

CREATE TABLE invoices (
  id           uuid PRIMARY KEY,
  account_id   uuid NOT NULL REFERENCES accounts(id),
  amount       numeric(24,8) NOT NULL,
  currency     text NOT NULL DEFAULT 'USDC',
  status       text NOT NULL,                -- issued|paid|partial|overdue|written_off
  due_at       bigint NOT NULL,
  issued_at    bigint NOT NULL
);
CREATE TABLE payments (
  id          uuid PRIMARY KEY,
  invoice_id  uuid NOT NULL REFERENCES invoices(id),
  amount      numeric(24,8) NOT NULL,
  reference   text,
  received_at bigint NOT NULL
);
```

Also created day 5–6 per HLD §0.2 carve-out, unused until post-launch: `outbound_messages`,
`communication_preferences`, `agent_runs`, `agent_proposals`.

### 3.1 Ledger append — B4 remediation

```ts
async function appendLedger(tx: Tx, e: LedgerInput): Promise<void> {
  // FOR UPDATE serialises concurrent appends; the whole thing runs inside the
  // caller's transaction so the fact and its ledger entry commit together.
  const head = await tx.one(
    `SELECT last_hash FROM ledger_head WHERE id = true FOR UPDATE`);
  const payload = canonicalJson(e.payload);          // stable key order — hash reproducibility
  const hash = sha256(head.last_hash + payload + e.at);
  const { seq } = await tx.one(
    `INSERT INTO ledger_entries (prev_hash, hash, entity_type, entity_id, account_id, payload, at)
     VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING seq`,
    [head.last_hash, hash, e.entityType, e.entityId, e.accountId, payload, e.at]);
  await tx.none(`UPDATE ledger_head SET last_seq = $1, last_hash = $2 WHERE id = true`, [seq, hash]);
}
```

Verification walks `ORDER BY seq`, never `at`. `canonicalJson` is mandatory — key-order variance
would make an honest chain fail verification.

---

## 4. Market data

`venue/info.ts` fetches candles and book; a single `MarketSnapshot` is built once per tick and
passed by reference to every account's evaluation. **One snapshot per tick, N accounts** — never
re-fetch per account, or the IP budget dies before a single order.

- Bars: 15m, ≥250 retained (EMA-200 needs 200 + warm-up).
- Snapshot is frozen (`Object.freeze`, deep) before entering `domain/`.
- Snapshots are persisted to object storage keyed by tick id, retained 90 days: this is what makes
  a live day replayable (NFR-11) and what the backtest harness consumes.

---

## 5. Strategy module

```ts
// domain/strategy/index.ts
export function evaluate(
  snap: MarketSnapshot,
  account: AccountState,
  regime: RegimeMode,
  cfg: StrategyConfig,
): Intent[];
```

Pure. Called once per account per tick. Emits zero or more intents.

**S1 (Donchian breakout) — the launch strategy**, per [STRATEGY_CANDIDATES.md](STRATEGY_CANDIDATES.md):

| Element | Spec |
|---|---|
| Timeframe | 15m bars |
| Entry long | `close > max(high[-20..-1])` AND `close > EMA200` AND `vol > median(vol[-20..-1])` AND close in top 25% of bar range |
| Entry short | Mirror |
| Size | `equity × riskPerTrade × riskMultiplier`, then converted to notional at mark |
| Stop | `entry ∓ 2.5 × ATR(14)`, trailing, ratcheting one direction only |
| Exit | Stop hit, or opposite Donchian channel touch |
| Instruments | Intersection of `account_instruments` and enabled set |

Exits are evaluated **first and unconditionally** each tick, before any entry logic and before any
lock check — a locked account must still be able to close. This ordering is a test, not a comment.

`S6` (regime allocator) and `S3` land behind a config flag once the harness validates them; the
`evaluate` signature does not change.

---

## 6. Risk module

```ts
// domain/risk/index.ts
export function check(
  intent: Intent, account: AccountState, snap: MarketSnapshot,
  portfolio: PortfolioView, cfg: RiskConfig,
): RiskVerdict;
```

Pure, and the **only** place a limit is enforced. Checks run in this order; first failure wins:

| # | Check | Reason code | Applies to |
|---|---|---|---|
| 1 | Intent expired (`now > validUntil`) | `intent_expired` | all |
| 2 | Account not `active` | `account_inactive` | all |
| 3 | Instrument not in account's set | `instrument_not_permitted` | all |
| 4 | Open reconciliation break | `reconciliation_break` | opens only |
| 5 | Owner halt | `owner_halt` | opens only |
| 6 | Regime lockdown | `regime_lockdown` | opens only |
| 7 | Loss breaker armed | `loss_breaker` | opens only |
| 8 | Profit lock armed | `profit_lock` | opens only |
| 9 | Correlated-bucket exposure cap | `correlated_exposure` | opens only |
| 10 | Funding-crossing negative carry | `funding_negative_carry` | opens only |
| 11 | Liquidity depth guard | `liquidity_depth` — may resize rather than reject | opens only |
| 12 | Post-check: resulting size below venue minimum | `size_below_minimum` | all |

Checks 4–11 are skipped entirely for `action: 'close'`. **A close is never blocked by a lock.**

**Correlated bucket (check 9).** Instruments whose rolling 30-day return correlation exceeds 0.7
share one exposure budget. Correlations are computed nightly into a `correlation_buckets` table and
read as data — the check itself stays pure.

**Funding crossing (check 10).** If `snap.nextFundingAt` falls inside the expected holding window,
`projectedFunding = |size| × fundingRate × sign`. If `expectedEdge − costs − projectedFunding ≤ 0`,
reject. Expected edge comes from the strategy's backtested per-signal expectancy, carried in
`SignalMeta.features`.

Caution regime is applied by the caller as a size multiplier on the approved intent, not as a
separate check.

---

## 7. Execution module

### 7.1 EIP-712 signing

`venue/signing.ts` builds the action payload, hashes per Hyperliquid's scheme, and signs with the
account's agent-wallet key. The key is fetched from the secrets manager, used within a single
synchronous signing call, and never assigned to a variable that outlives it. **No key material is
ever logged, and the logger's field allowlist makes that structural** (§18).

### 7.2 Nonce allocation

Rules that constrain us: nonce ∈ `(T−2d, T+1d)`; the 100 highest nonces per signer are tracked; a
new nonce must exceed the smallest of that set and be unused. Nonces are per **signer**, so one
agent wallet per account gives each account an isolated nonce space.

```ts
// venue/nonce.ts — per API wallet, in-process, monotonic.
const last = new Map<string, number>();
export function nextNonce(apiWallet: string): number {
  const now = Date.now();
  const prev = last.get(apiWallet) ?? 0;
  const n = now > prev ? now : prev + 1;   // never collide within the same millisecond
  last.set(apiWallet, n);
  return n;
}
```

Three guards:

- **Clock skew.** A worker whose clock drifts more than 24 h forward, or 48 h back, produces
  rejected nonces. A startup check compares local time against a venue timestamp and refuses to
  start beyond ±60 s.
- **Multi-worker safety.** In-process monotonicity is only sufficient because a given account's
  orders are serialised by a Trigger.dev queue with `concurrencyLimit: 1` (§14). That queue is
  therefore load-bearing for correctness, not just for rate limiting — comment it as such.
- **Retries.** A retried task must reuse the *same* `cloid` but take a *fresh* nonce. Nonce reuse is
  rejected by the venue; cloid reuse is what makes the retry idempotent.

### 7.3 Client order IDs

```ts
const cloid = '0x' + sha256(`${intentId}:${leg}`).slice(0, 32);  // 128-bit, deterministic
```

Deterministic from the intent, so a retry after an ambiguous timeout re-sends the identical cloid and
the venue deduplicates. This is why §2 gives `orders` a `UNIQUE (intent_id, leg)`.

### 7.4 Maker-first state machine

```
                  ┌──────────┐
                  │ APPROVED │
                  └────┬─────┘
         urgency=immediate │ urgency=passive
        ┌─────────────────┴──────────────────┐
        ▼                                    ▼
  ┌───────────┐                       ┌──────────────┐
  │TAKER_SEND │◄──── signal holds ────│ MAKER_RESTING│
  └─────┬─────┘      after cancel     └──────┬───────┘
        │                                    │ fill (WS)
        │ fill                               ▼
        ▼                              ┌──────────┐
   ┌────────┐                          │  FILLED  │
   │ FILLED │◄─────────────────────────┴──────────┘
   └────────┘
        ▲  reject/expiry (bounded retry)      │ timeout → cancel
        └──── FAILED ◄────────────────────────┴──► ABANDONED (signal decayed)
```

| Transition | Rule |
|---|---|
| APPROVED → MAKER_RESTING | Place **ALO** (post-only) limit at the touch. ALO guarantees maker or nothing — a crossing order is rejected, never silently filled as taker. ALO batches are also validator-prioritised |
| ALO rejected as crossing | Price has already moved through our level. Re-evaluate the signal; if it holds, jump to TAKER_SEND; if not, ABANDON |
| MAKER_RESTING → FILLED | Fill event arrives on WebSocket |
| MAKER_RESTING → cancel | `MAKER_TIMEOUT_MS` (default 45 000) elapses |
| after cancel | Re-run `strategy.stillValid(intent, freshSnapshot)`. **Holds** → TAKER_SEND for the unfilled remainder. **Decayed** → ABANDONED, with reason recorded |
| TAKER_SEND | IOC at mark ± slippage cap. Rejection retries ≤3 with backoff, then FAILED |
| Partial maker fill | The filled part is a real position; only the remainder proceeds. Never abandon a position because its sibling leg failed |

`urgency: 'immediate'` skips the maker leg entirely — every exit, every breaker-triggered flatten,
every lockdown unwind.

### 7.5 The `stillValid` recheck

```ts
// domain/strategy/index.ts
export function stillValid(intent: Intent, snap: MarketSnapshot): boolean;
```

Pure and cheap: re-derives the entry condition against the current snapshot. This single function is
the defence against adverse selection — the fill we *would* have got by crossing after price moved
through our resting order is exactly the fill we do not want.

---

## 8. Fan-out and fairness

One signal produces up to N intents. Sequential placement is unavoidable (§LLD reference facts:
batching cannot aggregate across addresses).

```ts
// services/fanout.ts
function orderAccounts(accounts: AccountFairness[], rng: Rng): string[] {
  const LAMBDA = 0.3;
  return accounts
    .map(a => ({ id: a.accountId, key: rng.next() - LAMBDA * (a.meanPosition - 0.5) }))
    .sort((x, y) => x.key - y.key)
    .map(x => x.id);
}
```

An account that has historically been late (`meanPosition > 0.5`) gets a negative key adjustment and
drifts toward the front. Randomness prevents a fixed order; the bias makes fairness *converge*
rather than merely hold in expectation.

After the batch, each account's realised normalised position `p = rank / (N − 1)` updates its running
mean:

```
mean' = mean + (p − mean) / min(n + 1, 500)
```

The window cap keeps the estimator responsive rather than frozen after a year of history.

**Dispatch cadence.** Orders submit in chunks paced to stay under 1200 weight/min, following the
venue's own guidance of batching every ~0.1 s. At ≤100 accounts the whole fan-out clears in under
10 s (NFR-8). Beyond ~500 accounts, chunks are distributed across egress IPs.

**`rng` is seeded from the batch id**, so a fan-out is reproducible in replay — a fairness dispute
must be answerable, not shrugged at.

---

## 9. WebSocket subscription manager

`venue/ws.ts` maintains one connection per shard, with subscriptions per account for `userFills` and
user state.

| Concern | Design |
|---|---|
| Sharding | ≤200 accounts per socket; a shard is a supervised task that reconnects independently |
| Reconnect | Exponential backoff, jitter, cap 30 s. On reconnect, a REST state pull closes the gap |
| Gap detection | Every fill carries `venue_fill_id`; ingest is idempotent on `(venue_fill_id, account_id)`, so REST and WS may both deliver the same fill safely |
| Liveness | Each shard emits a heartbeat event per minute. **A shard that stops emitting is the silent failure A3′ exists to catch** — absence of errors is not health |
| Backstop | REST state sweep per account every 15 min, staggered to spread the weight |

---

## 10. Reconciliation

```ts
interface ReconResult { ok: boolean; diffs: Diff[] }
```

On every venue state update, and on every backstop sweep, compare per instrument: position size,
side, and account equity, against our `positions` row and derived equity.

- Size mismatch beyond `1e-8`, or any side mismatch ⇒ **not ok**.
- Equity mismatch is tolerated within a band (fees and funding land asynchronously); beyond it,
  not ok.
- Not ok ⇒ write `reconciliations` row, set an `account_halt` flag consumed by risk check 4, emit
  incident. **Existing positions and their exits continue to be managed** — halting entries is
  correct; abandoning a live position is not.
- Clearing requires either the diff resolving on a later cycle or an owner action. Auto-clear is
  allowed only when two consecutive cycles are clean.

---

## 11. Attribution

Materialised views, recomputed on fill and on funding payment.

```sql
CREATE MATERIALIZED VIEW attribution_daily AS
SELECT
  f.account_id,
  (f.at / 86400000) * 86400000                                   AS day,
  SUM(f.closed_pnl)                                              AS signal_pnl,
  -SUM(f.fee)                                                    AS fee_cost,
  SUM(COALESCE(fp.amount,0))                                     AS funding_cost,
  -SUM(ABS(f.size) * ABS(f.price - i.decision_price))            AS slippage_cost
FROM fills f
JOIN orders o  ON o.id = f.order_id
JOIN intents i ON i.id = o.intent_id
LEFT JOIN funding_payments fp
       ON fp.account_id = f.account_id AND fp.at / 86400000 = f.at / 86400000
GROUP BY 1, 2;
```

Terms sum to net by construction. `cum_pnl` for billing (§13) is the running sum of
`signal_pnl + fee_cost + funding_cost` over closed positions only — slippage is already inside the
realised fill price and must not be subtracted twice.

**Counterfactual.** Every `risk_events` row with an `opens only` code is a trade not taken. A nightly
job prices what that trade would have done using the strategy's own exit rules against recorded
snapshots, and writes `control_counterfactual (account_id, day, code, hypothetical_pnl)`. This is
what makes "what the regime guard cost you" a number rather than a claim.

---

## 12. Billing

State machine per account per month.

```
   [month rolls]
        │
        ▼
  COMPUTE ──► fee = 0.10 × max(0, cum_pnl − hwm_pnl)
        │
        ├─ fee < $25 ────► ROLL_FORWARD   (hwm_pnl unchanged)
        │
        └─ fee ≥ $25 ────► ISSUE_INVOICE  (hwm_pnl := cum_pnl)
                                │
                    ┌───────────┼────────────┐
                    ▼           ▼            ▼
                  PAID       PARTIAL      OVERDUE
                                             │  grace elapsed
                                             ▼
                                    SUSPEND_ENTRIES
                                             │
                                             ▼
                                     FLATTEN → CLOSE
```

- `cum_pnl` is **realised only**; open positions carry to the next period.
- `hwm_pnl` advances **only** when an invoice actually issues, never on a rolled-forward amount —
  otherwise sub-threshold gains would silently raise the bar without ever being charged.
- Crystallisation is idempotent on `(account_id, period_start)`; re-running the job is safe.
- Suspension stops entries only. Exits and stops keep working — a client who has not paid is still
  entitled to have their risk managed.
- Every invoice carries the full arithmetic: `cum_pnl`, `hwm_before`, increment, rate. NFR-10.

---

## 13. Trigger.dev task catalog

```ts
// Queues. The per-account queue is a correctness mechanism (§7.2), not just throttling.
const accountQueue = (id: string) => queue({ name: `account-${id}`, concurrencyLimit: 1 });
const venueQueue   = queue({ name: 'venue-rest', concurrencyLimit: 8 });
```

| Task | Trigger | Machine | Notes |
|---|---|---|---|
| `strategy-tick` | cron `*/15 * * * *` (aligned to bar close + 5 s) | `small-2x` | Builds one snapshot, evaluates all active accounts, writes intents, enqueues fan-out |
| `execute-intent` | Triggered per intent | `small-1x` | Runs the §7.4 state machine. `queue: accountQueue(accountId)` |
| `ws-shard` | Long-running, one per shard | `small-1x` | §9. `maxDuration` high; supervised restart |
| `reconcile-backstop` | cron `*/15 * * * *` | `small-1x` | Staggered REST sweep |
| `funding-sync` | cron `5 */8 * * *` | `micro` | Pulls settled funding into `funding_payments` |
| `attribution-refresh` | cron `*/30 * * * *` | `small-1x` | Refreshes materialised views |
| `counterfactual-nightly` | cron `20 0 * * *` | `medium-1x` | §11 |
| `billing-crystallise` | cron `0 1 1 * *` | `small-1x` | §12; idempotency key `${accountId}:${period}` |
| `correlation-nightly` | cron `30 0 * * *` | `small-1x` | Rebuilds correlation buckets for risk check 9 |

Retry policy for venue-touching tasks:

```ts
retry: { maxAttempts: 5, factor: 1.8, minTimeoutInMs: 500, maxTimeoutInMs: 30_000, randomize: true }
```

`AbortTaskRunError` is thrown for non-retryable venue rejections (insufficient margin, instrument
halted, invalid size) so they fail fast to a risk event rather than burning five attempts.

`strategy-tick` never calls `triggerAndWait` inside a loop — it batch-triggers the fan-out and
returns. Waiting would serialise the entire desk behind the slowest account.

---

## 14. HTTP API surface

Next.js 16 App Router route handlers under `src/app/api/`. Route handlers are **not cached by
default** in this version, so no `force-dynamic` incantation is needed; add caching only where
deliberately wanted.

| Route | Method | Auth | Purpose |
|---|---|---|---|
| `/api/accounts/me` | GET | client | Own account, positions, locks |
| `/api/accounts/me/attribution` | GET | client | Attribution + counterfactual, own rows only |
| `/api/accounts/me/trades` | GET | client | Fills with "why" payload from `intents.signal_json` |
| `/api/accounts/me/invoices` | GET | client | Own invoices and payment state |
| `/api/owner/halt` | POST | owner | Global or per-account halt; the only write that bypasses nothing |
| `/api/owner/accounts/:id/status` | POST | owner | Lifecycle transitions |
| `/api/owner/reconciliation/:id/clear` | POST | owner | Manual clear of a break |
| `/api/webhooks/payments` | POST | signature | Receipt ingestion |

Every client route derives `accountId` **server-side from the session**. No route accepts an account
identifier from the caller. This is the same rule as the agent tool contract (HLD §6.3) and it is
enforced by a shared `withClientAccount()` wrapper rather than per-route discipline.

---

## 15. Configuration

All trading parameters live in one typed, validated config module, loaded once and frozen. Secrets
come from the secrets manager; **there is no default value for any secret** — absence throws at
startup (B3 remediation).

```ts
export const config = {
  riskPerTrade: 0.02,
  cautionRiskMultiplier: 0.5,
  makerTimeoutMs: 45_000,
  takerSlippageCapBps: 15,
  dailyLossBreakerPct: 0.15,
  lossLockHours: 24,
  correlationThreshold: 0.7,
  correlatedBucketCapPct: 0.06,
  depthGuardFraction: 0.10,
  feeRate: 0.10,
  minInvoiceUsd: 25,
  fanoutLambda: 0.3,
} as const;
```

Changing any of these is a deploy, recorded in the changelog. No runtime tuning surface exists for
trading parameters — an operator control that can silently change risk is a control nobody can audit.

---

## 16. Error taxonomy

Reason codes are a closed enum, stored, and surfaced verbatim to clients through A4.

```ts
export type RiskReasonCode =
  | 'intent_expired' | 'account_inactive' | 'instrument_not_permitted'
  | 'reconciliation_break' | 'owner_halt' | 'regime_lockdown'
  | 'loss_breaker' | 'profit_lock' | 'correlated_exposure'
  | 'funding_negative_carry' | 'liquidity_depth' | 'size_below_minimum';

export type ExecReasonCode =
  | 'alo_would_cross' | 'signal_decayed' | 'maker_timeout'
  | 'venue_rejected' | 'insufficient_margin' | 'nonce_rejected'
  | 'rate_limited' | 'venue_unreachable';
```

Adding a code requires adding its client-facing explanation in the same commit — a code the client
cannot understand is a support ticket by construction.

---

## 17. Observability

Per [AGENT_OPERATIONS.md](AGENT_OPERATIONS.md) §1.1. Implementation specifics:

```ts
logger.info('execution.order_placed', {
  correlation_id: intent.id, account_id: accountId,
  component: 'execution', leg: 'maker', cloid,
});
```

- `event` is a stable enum, never an interpolated sentence.
- The logger takes a field allowlist; anything not on it is dropped, so a key or token cannot be
  logged even by accident.
- One `correlation_id` (= `intent.id`) threads strategy → risk → execution → fill → ledger →
  reconciliation.
- Heartbeat events per component per minute; A3′ raises on shortfall.

---

## 18. Testing strategy

| Layer | Approach | Bar |
|---|---|---|
| `domain/` | Pure unit tests, no mocks. Golden-file tests on recorded snapshots | 100% branch on risk checks |
| Ledger | Property test: N concurrent appends always yield a chain that verifies | Must pass at N=50 |
| Nonce | Property test: monotonic under same-millisecond bursts | — |
| Execution FSM | State-transition table driven; every edge in §7.4 has a test | Every edge |
| **B1 regression** | Live-mode order against an unreachable venue **must** return failure and must not write a fill | Blocking — this test is the definition of B1 being closed |
| Fairness | Simulate 10k signals × 500 accounts; assert all mean positions ∈ 0.5 ± 0.05 | NFR-12 |
| Billing | Table-driven against the HLD §4.5.2 worked example, plus deposit/withdrawal immunity | Exact match |
| Replay | Re-run a recorded day; assert identical intents | NFR-11, byte-identical |

---

## 19. Blocker remediation

| ID | Fix | Verified by |
|---|---|---|
| B1 | `venue/exchange.ts` genuinely constructs, signs and posts orders; parses the response; has no success path that does not correspond to a venue acknowledgement. The demo's fabricating branch is not ported | §18 B1 regression test |
| B2 | `wallet_address` (public, for state reads) and `api_wallet_ref`/`api_wallet_addr` (signer) are separate columns with separate meanings | Schema; type-level separation |
| B3 | No secret has a default. `getSecret()` throws on absence at startup | Startup smoke test with the var unset |
| B4 | `ledger_head` + `FOR UPDATE` + `bigserial` ordering, inside the caller's transaction | Concurrency property test |

These are greenfield in `Alphaedge_live/` — nothing is migrated, so the fix is "do not reproduce the
defect", verified by tests rather than by diff.

---

## 20. Build sequence

| Days | Deliverable | Sections |
|---|---|---|
| 1–2 | `venue/` complete against testnet: signing, nonce, exchange, info. B1–B4 tests green | §7, §19 |
| 3–4 | `domain/strategy` + backtest harness over recorded bars; S1 measured against the cost floor | §5, §4 |
| 5–6 | App skeleton, schema, `domain/risk`, attribution views, log schema + correlation IDs | §3, §6, §11, §17 |
| 7 | `execute-intent` FSM, fan-out, WS shards, reconciliation | §7, §8, §9, §10 |
| 8 | Regime layer, A1 lock contract, owner console halt/unlock | HLD §4.1.2 |
| 9–10 | Paper soak on live data, then company account live | — |

Billing (§12) is not on the ten-day path — no fee crystallises until a month after the first funded
client account. Build it during the soak.

---

## 21. Open implementation questions

Neither blocks the start; both have a safe default and must be settled with live venue behaviour.

1. **Do info-endpoint requests draw on the address budget or only the IP budget?** Default:
   assume both, budget conservatively.
2. **Observed WebSocket state-update reliability.** If gap rate exceeds one per account-day, raise
   the REST backstop from 15 minutes to 5.


---

## 22. Revision 1.1 — venue abstraction and autonomous operations

Additions implementing HLD decisions 18–19. Nothing above changes for the Hyperliquid launch path;
this section defines the seams that make venue #2 an adapter rather than a rewrite.

### 22.1 VenueAdapter interface

```ts
// venues/adapter.ts — the only surface the core sees.
export interface VenueAdapter {
  readonly venue: 'hyperliquid' | 'polymarket';
  listInstruments(): Promise<InstrumentRecord[]>;          // feeds the instruments table
  snapshotContribution(ids: InstrumentId[]): Promise<Partial<MarketSnapshot>>;
  placeOrder(req: PlaceOrderReq): Promise<PlaceOrderResult>;   // idempotent on cloid
  cancelOrder(req: CancelReq): Promise<CancelResult>;
  openStateStream(accounts: AccountRef[]): StateStream;        // fills + state, gap-safe
  pullAccountState(account: AccountRef): Promise<VenueAccountState>;  // reconcile backstop
  verifyCustodyGrant(account: AccountRef): Promise<GrantStatus>;      // provisioning step 2
}
```

Execution FSM (§7.4), fan-out (§8), reconciliation (§10) and attribution (§11) call only this
interface. Hyperliquid's implementation is §7–§9 unchanged. Polymarket's implementation notes:

| Concern | Polymarket adapter |
|---|---|
| Auth | L1 (wallet signature) only during provisioning to derive L2 API creds; L2 for all order ops. **O8: prove L2 cannot move assets — company pilot before any client account** |
| Maker leg | CLOB limit order; no ALO equivalent — emulate post-only by price-checking against top of book before submit, abandon on cross |
| Fills | CLOB user channel WebSocket; REST backstop identical in shape |
| Resolution | A watcher task ingests market resolution + redemption as `resolution` events into attribution; positions in resolved markets are terminal |
| Fees | No per-trade venue fee on most markets — cost model is spread + impact; the §6 funding-crossing check is skipped for `kind: 'binary'` |

### 22.2 Instruments table

```sql
CREATE TABLE instruments (
  id           text PRIMARY KEY,            -- 'hl:BTC', 'pm:<conditionId>'
  venue        text NOT NULL,
  kind         text NOT NULL CHECK (kind IN ('perp','binary')),
  symbol       text NOT NULL,
  status       text NOT NULL,               -- active|expiring|resolved|delisted
  resolves_at  bigint,                      -- binary only
  min_size     numeric(24,8),
  metadata     jsonb NOT NULL DEFAULT '{}',
  updated_at   bigint NOT NULL
);
```

`account_instruments` now references `instruments.id`. Tier mapping (decision 14) becomes a policy
over this table: L1 = hl:BTC; L2 += hl:ETH; L3 += hl:PAXG and, post-O8, curated `pm:*` sets.
A nightly `instrument-sync` task per adapter maintains rows; strategy reads `status='active'` only,
and risk rejects any intent on an instrument within `RESOLUTION_BUFFER` of `resolves_at` unless the
strategy explicitly holds to resolution.

### 22.3 Cross-account liquidity budget (risk check 9a)

New check between 9 and 10, venue-scoped, and the binding constraint on Polymarket:

```
platform_budget(instrument, window) = DEPTH_FRACTION_AGG × visible_depth(instrument)
account_allocation = platform_budget × account_equity / Σ participating_equity
```

Implemented as a reservation table consulted at fan-out time: each approved intent reserves its
allocation; the reservation drains on fill or expiry. On Hyperliquid `DEPTH_FRACTION_AGG = 0.25`
rarely binds; on Polymarket it deliberately caps how many accounts one market serves — when the
budget is exhausted, remaining accounts skip with reason `platform_liquidity_budget`, and the
fairness accounting (§8) ensures the *same* accounts are not always the ones skipped.

### 22.4 Automated provisioning pipeline (HLD §4.4b)

Route additions to §14, all policy-code, no agent in the path:

| Route | Purpose |
|---|---|
| `POST /api/onboarding/acknowledge` | Versioned risk acknowledgement + terms |
| `POST /api/onboarding/wallet` | Wallet connect; platform generates agent wallet, returns the venue grant payload for the client to sign |
| `POST /api/onboarding/verify-grant` | Calls `adapter.verifyCustodyGrant`; on success auto-starts paper mode |
| `POST /api/onboarding/activate` | Runs the eligibility policy; auto-activates with a 24h owner veto window |

Eligibility policy (deterministic, versioned, logged): grant verified ∧ funded ≥ tier minimum ∧
acknowledgement current ∧ no sanctions/blocklist hit ∧ paper mode ran ≥ 1 clean tick. Failures
queue for A5′ + owner as exceptions. The `users.role` human-approval flow from the demo is
retired for clients — role semantics collapse to account lifecycle status.

### 22.5 Trust-ladder enforcement

```sql
CREATE TABLE automation_ladder (
  workflow       text PRIMARY KEY,      -- 'a8_weekly_brief', 'a7_changelog', 'a5_dormancy_pause', ...
  mode           text NOT NULL,         -- 'human' | 'auto'
  approvals_run  integer NOT NULL DEFAULT 0,   -- consecutive unchanged approvals
  threshold      integer NOT NULL DEFAULT 10,
  killed         boolean NOT NULL DEFAULT false,  -- owner kill switch, per workflow
  updated_at     bigint NOT NULL
);
```

Graduation (`approvals_run ≥ threshold → mode='auto'`) is automatic; any owner edit or veto resets
`approvals_run` to 0 and demotes to `'human'`. Auto-mode outputs are sampled (1 in 20) back into the
approval queue for drift review. Workflows in HLD §4.4b's "permanently human" class are not rows in
this table — they cannot graduate because they are not enrolled.

### 22.6 Impact on existing sections

| Section | Change |
|---|---|
| §3 schema | + `instruments`, `automation_ladder`, liquidity reservations; `account_instruments` re-keyed |
| §6 risk | + check 9a; funding check skipped for `kind:'binary'`; + `platform_liquidity_budget`, `resolution_window` reason codes |
| §8 fan-out | Consults reservations; skip-fairness folded into queue-position accounting |
| §13 tasks | + `instrument-sync` (per venue, hourly), `pm-resolution-watcher`, `ladder-review` (daily) |
| §14 API | + four onboarding routes (§22.4) |
| §18 tests | + budget-exhaustion fairness sim; provisioning happy-path with zero human actions; ladder graduation/reset property test |


---

## 23. Revision 1.2 — environments, flags, and the promotion pipeline

Implements HLD decision 20 (§9.1, §9.1a, §9.5).

### 23.1 Environment configuration matrix

One config module, environment resolved once at startup from `APP_ENV ∈ {dev, prod}`:

```ts
// lib/env.ts
export const envMatrix = {
  dev: {
    venueBackend: { hyperliquid: 'testnet', polymarket: 'mumbai-or-stub' },
    feedsReadOnlyMainnet: true,      // realistic data, impossible writes
    allowLiveAccounts: false,        // hard gate: accounts.type='live' rejected at risk check 2
    agentEffortCap: 'low',
    outboundStubbed: true,           // A8 sends and A7 publishes write to a review table only
  },
  prod: {
    venueBackend: { hyperliquid: 'mainnet', polymarket: 'polygon' },
    feedsReadOnlyMainnet: false,
    allowLiveAccounts: true,
    agentEffortCap: null,
    outboundStubbed: false,
  },
} as const;
```

**The load-bearing line is `allowLiveAccounts: false` plus disjoint secret stores.** DEV cannot
place a mainnet order for two independent reasons: the risk layer rejects live accounts, and no
mainnet signing key exists in DEV's secret store. Either alone is a policy; both together is a
property.

### 23.2 Feature flags

```sql
CREATE TABLE feature_flags (
  key         text PRIMARY KEY,          -- 'venue:polymarket', 'strategy:S6', 'ui:counterfactual'
  stage       text NOT NULL DEFAULT 'off',
              -- 'off' | 'internal' | 'company' | 'canary' | 'all'
  canary_pct  numeric(5,2),              -- optional % ramp within 'canary'
  updated_by  text NOT NULL,
  updated_at  bigint NOT NULL
);
CREATE TABLE flag_cohorts (              -- explicit canary membership (opt-in clients)
  flag_key    text NOT NULL REFERENCES feature_flags(key),
  account_id  uuid NOT NULL REFERENCES accounts(id),
  PRIMARY KEY (flag_key, account_id)
);
```

```ts
// domain-safe evaluation: pure function of (flag row, account, hash)
export function flagOn(flag: FlagRow, account: AccountRef | null, cohort: boolean): boolean {
  switch (flag.stage) {
    case 'off':      return false;
    case 'internal': return account === null;                    // desk/company surfaces only
    case 'company':  return account === null || account.isCompany;
    case 'canary':   return cohort || (flag.canary_pct != null
                       && bucket(account.id) < flag.canary_pct); // stable hash bucket 0..100
    case 'all':      return true;
  }
}
```

Rules: flags are read at tick start into the frozen snapshot context (never mid-tick — a flag flip
cannot change behaviour between an intent and its execution); every flag change writes to the
ledger (`entity_type='flag_change'`); a flag key retires by deletion within two releases of reaching
`'all'` — permanent flags are config, not flags. Strategy replay (NFR-11) stores the flag state
with the recorded snapshot so replays honour history.

### 23.3 CI gates

GitHub Actions on PR and on main:

| Job | Content | Blocking |
|---|---|---|
| `unit` | domain/ suite, no mocks; risk branch coverage gate 100% | yes |
| `property` | ledger concurrency (N=50), nonce monotonicity, fairness sim (reduced 1k×100), ladder graduation/reset | yes |
| `fsm` | every §7.4 edge, incl. B1 regression | yes |
| `replay` | recorded golden day → byte-identical intents (with stored flag state) | yes |
| `migration-lint` | additive-only check: no DROP/ALTER TYPE narrowing/column removal outside a marked `contract` release | yes |
| `build` | Next build + Trigger.dev dry-run deploy | yes |

### 23.4 Promotion workflow

```
main (green) ──auto──▶ DEV deploy ──24h soak──▶ soak report (auto-generated)
                                                    │
                    Neon: branch PROD db ──migrate──┤ rehearsal + rollback test
                                                    ▼
                              [PROMOTE button — owner console, records SHA+who+when]
                                                    │
             prod deploy (Vercel + trigger.dev deploy --env prod), flags unchanged (dark)
                                                    ▼
                              post-deploy smoke (23.5) ──▶ flag exposure per rollout plan
```

- Soak report is generated by the same machinery as A2's daily review, pointed at DEV: recon
  breaks, FSM terminal-state histogram, heartbeat gaps. Promotion button is disabled unless the
  latest soak report is green and newer than the candidate SHA.
- Deploy scheduling: the promotion job waits for the next `:07` past a 15m boundary — mid-window
  between strategy ticks — before switching traffic.
- In-flight runs finish on their prior Trigger.dev task version; new runs start on the new version.
- **Rollback:** `promote --rollback` redeploys the previous build (always possible: migrations are
  additive) and is itself followed by the smoke suite. Feature rollback is a flag flip and needs no
  deploy.

### 23.5 Post-deploy smoke (PROD, dark)

Runs automatically after every promotion, before any flag moves:

1. `strategy-tick` executes on schedule and writes a tick record.
2. One reconcile cycle per enabled venue returns `ok` for the company account.
3. Owner-console halt engages and releases (round trip against a paper account).
4. Synthetic intent through the FSM against paper fill model reaches `FILLED`.
5. Logger heartbeats present for every component.

Any failure pages the owner and blocks flag exposure; the deploy stays dark until resolved or
rolled back.

### 23.6 Venue #2 rollout plan (worked example of the mechanism)

| Step | Flag stage | Gate to advance |
|---|---|---|
| Adapter merges | `off` | CI green |
| DEV integration | `off` (DEV exercises via internal) | PM testnet/stub round trip; resolution watcher ingests a resolved market |
| PROD company pilot | `company` | **O8 custody verification** on the company PM account; 2 weeks clean recon incl. one real resolution + redemption |
| Canary | `canary` + opt-in cohort | 30 days; execution quality within backtest bands; cross-account budget behaviour observed |
| GA | `all` | Owner sign-off |

### 23.7 Impact on existing sections

| Section | Change |
|---|---|
| §3 schema | + `feature_flags`, `flag_cohorts`; flag changes ledger-logged |
| §4 snapshot | Snapshot context includes resolved flag state; stored with recorded snapshots for replay |
| §6 risk | Check 2 additionally rejects live accounts when `allowLiveAccounts=false` |
| §13 tasks | + `dev-soak-report` (DEV only, daily), promotion job |
| §15 config | `APP_ENV` matrix; secrets stores disjoint per environment |
| §18 tests | CI jobs of §23.3 are the enforcement of the bars already defined |
| §20 build sequence | Day 5–6 gains: env matrix, flags table, CI pipeline (≈6h). Day 9–10 soak becomes the FIRST run of the standing DEV-soak machinery rather than a one-off |
