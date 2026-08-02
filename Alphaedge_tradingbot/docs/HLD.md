# Prospera — High-Level Design

## Document control

| Field | Value |
|---|---|
| Document | High-Level Design (HLD) |
| System | Prospera — Autonomous Wealth Systems (alphaedgeai.io) |
| Version | **1.2 — environments & promotion model** |
| Date | 2026-07-28 |
| Author | Engineering |
| Status | **Ready for sign-off.** All engineering open items closed; two owner items remain (§13) and neither blocks LLD |
| Supersedes | Nothing. The production system is greenfield; the demo is unaffected |

### Revision history

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-07-28 | Initial draft consolidating design decisions 1–11 |
| 0.2 | 2026-07-28 | Decisions 12–13: profit-share fee model (§4.5 rewritten), tier differentiation. Added §2.5 trading mechanics. Risks R2, R8 |
| 1.2 | 2026-08-01 | Decision 20: DEV/PROD environment model, gated promotion pipeline, flag-based feature rollout (§9.1, §9.5). Risk R12 |
| 1.1 | 2026-08-01 | Decisions 18–19: Polymarket as second venue (§2.6, §4.7), automation-first operations (§4.8). Instruments become venue-scoped entities; cross-account liquidity budget added; provisioning pipeline specified. Risks R9–R11 |
| 1.0 | 2026-07-28 | Venue rate limits researched — §4.1.3a fan-out and fill-fairness design closes O4; reconciliation moved to WebSocket (§4.1.4). Builder codes considered and rejected (§4.5.3a). Decisions 14–17 close O1, O3, O3b, O5. NFR-8 re-based, NFR-12 added |

### Approval

| Role | Name | Decision | Date |
|---|---|---|---|
| Product owner | — | ☐ Approve ☐ Approve with changes ☐ Reject | — |
| Engineering | — | ☐ Approve ☐ Approve with changes ☐ Reject | — |

---

## 1. Introduction

### 1.1 Purpose

This document defines the high-level architecture of the Prospera production trading system: a
multi-tenant platform that executes a single systematic strategy across many client accounts on
Hyperliquid perpetual futures, with automated risk governance and an advisory AI agent layer.

It is written to be reviewed and signed off before low-level design begins. It states *what* the
system is composed of and *why*; it does not specify class structures, function signatures, or
schema DDL — those belong in the LLD.

### 1.2 Scope

In scope:

- Deterministic trading core: strategy evaluation, risk governance, order execution, reconciliation
- Per-client account management, custody of trade-only venue credentials, and lifecycle
- Deterministic attribution and telemetry layer
- Eight-agent advisory layer and the publication gate governing its outputs
- Client-facing surfaces: application, statements, outbound communications
- Profit-share accrual and billing (§4.5) — high-water marked performance fee, decision 12

Out of scope for this document:

- The demo system at its current URL, which is unchanged and untouched (decision 8)
- Strategy selection itself — candidates and the selection protocol are in
  [STRATEGY_CANDIDATES.md](STRATEGY_CANDIDATES.md)
- Legal, regulatory, and licensing workstreams, which run in parallel and are owner-led (§9.4)
- Marketing site content, other than the constraints §2.4 places on it

### 1.3 Intended audience

Product owner (sign-off), engineering (implementation), and any external counsel or reviewer needing
to understand how client capital is governed.

### 1.4 Definitions

| Term | Meaning |
|---|---|
| **Intent** | The strategy's output: a proposed trade for one account, before risk approval. The audit spine — every order traces to exactly one intent |
| **Regime** | System-wide risk posture: `normal`, `caution`, or `lockdown`. Gates entries, never exits |
| **Lock** | Any condition preventing new entries. Four independent sources with distinct release rules (§4.1.2) |
| **Attribution** | Deterministic decomposition of P&L into signal, fees, funding, slippage and sizing terms |
| **Publication gate** | Deterministic checkpoint every agent-authored external communication must pass (§4.4) |
| **Maker-first** | Execution policy: rest a limit order, fall back to crossing the spread only if the signal still holds (decision 10) |
| **Cost floor** | Round-trip execution cost that any strategy must clear to be viable. 9.0 bps taker/taker, 3.0 bps maker/maker |
| **High-water mark** | Peak cumulative attributable profit on which a performance fee has already been charged. Fees resume only above it (§4.5.2) |
| **Crystallisation** | The periodic point at which profit share is calculated and invoiced |

### 1.5 Reference documents

| Ref | Document | Role |
|---|---|---|
| R1 | [PRODUCTION_DESIGN.md](PRODUCTION_DESIGN.md) | Design rationale, decisions 1–11, ten-day plan |
| R2 | [STRATEGY_CANDIDATES.md](STRATEGY_CANDIDATES.md) | Strategy research, cost-floor analysis, test protocol |
| R3 | [AGENT_OPERATIONS.md](AGENT_OPERATIONS.md) | Operational agents A3′, A5′, A7, A8; publication gate; logging substrate |
| R4 | `DESIGN.md` (repo root) | UI tokens and visual system |
| R5 | [LLD.md](LLD.md) | Low-level design — schema, execution FSM, task catalog, test bars |

---

## 2. System context

### 2.1 Business context

Prospera positions itself as "a capital operating system": clients grant trade-only exchange
permissions, and the platform runs a governed strategy against their own capital, held in their own
venue account. The platform never takes custody of funds.

Tier structure, as revised 2026-07-28 (decision 12):

| Tier | Capital lane | Fee | Instruments | Typical entries/day |
|---|---|---|---|---|
| Seed / Demo | — | Free, watch-only | — | — |
| Builder (L1) | $5K | **10% of net new profit** | BTC | ~2–5 |
| Compounder (L2) | $10K | **10% of net new profit** | BTC, ETH | ~4–10 |
| Sovereign (L3) | $25K+ | **10% of net new profit** | BTC, ETH, PAXG | ~5–15 |

Tiers vary on two axes only — capital lane and instrument access. Strategy logic, risk governance
and fee rate are identical across tiers (decisions 13, 14). Trade allowance is expressed through
instrument access rather than a daily count, for the reasons in §2.4 G2: at a 15m–4h holding period
a daily count cap would never bind, and allocating a cap within the day creates unfairness unrelated
to capital. Entry counts above are expected ranges, not guarantees.

The previously published annual management fees (1.2% / 1.8%) and the 50/100/250 daily trade quotas
are both superseded; the site still shows the old model (§2.4 G1, G2).

### 2.2 Stakeholders

| Stakeholder | Interest |
|---|---|
| Retail clients (worldwide) | Capital growth, transparency, ability to stop the system |
| Product owner / desk operator | Manual halt and unlock authority over everything; approval of all external communications |
| Engineering | Correctness, replayability, auditability |
| External counsel | Registration posture, disclosures, records retention (§9.4) |

### 2.3 Context boundary

External systems the platform depends on:

| System | Direction | Purpose | Failure posture |
|---|---|---|---|
| Hyperliquid | Bidirectional | Market data, order placement, fills, positions | Fail closed — no fills assumed, reconciliation halts the account |
| Economic calendar feed | Inbound | Blackout windows | Degrade — retain last known windows |
| Anthropic API | Outbound | Agent inference | Degrade — agents are advisory; the core trades without them |
| Email / Telegram | Outbound | Client communications | Degrade — queue and retry, never duplicate (§4.4) |
| Payment processor | Bidirectional | Invoice payment links and receipt webhooks (§4.5.3) | Degrade — the invoice stands; receipts reconcile late |

### 2.4 Product-versus-design gaps identified during this review

Reading the live product against the design surfaced four discrepancies. G1 and G2 were resolved by
owner decision on 2026-07-28; G3 and G4 remain open as pre-launch actions.

**G1 — Fee model changed to profit sharing (resolved 2026-07-28, decision 12).** The management-fee
model is replaced by **10% of net new profit**, remitted by the client. Collection remains
out-of-band because trade-only keys give us no withdrawal permission — that constraint is unchanged
and is a headline trust property. What changed is the calculation, and it is substantially more
complex than a management fee: a performance fee requires a high-water mark, a crystallisation
period, and a profit definition immune to the client's own deposits and withdrawals. Full design in
§4.5. Note for §9.4: performance fees attract *more* regulatory attention than management fees in
several jurisdictions, not less — counsel should be told the model changed.

**G2 — Tier differentiation is capital and trade allowance (resolved 2026-07-28, decision 13).**
Tiers vary on capital lane and number of trades; everything else — strategy, risk governance, fee
rate — is identical. Two engineering consequences that need product input before LLD:

- **The published numbers no longer describe reality.** 50/100/250 trades per day were 5-minute
  binary-round figures. At a 15-minute-to-4-hour holding period across three instruments the system
  produces roughly **5–15 entries per day in total**, so a 50/day cap never binds and the tiers
  would be indistinguishable in practice. Allowances must be re-based into the actual signal
  rate — something like 3 / 6 / uncapped — or the differentiation is cosmetic.
- **A cap requires an allocation rule, and the rule has fairness consequences.** If a capped tier
  takes only the first N signals of the day, and the day's best signals arrive at 20:00 UTC, that
  tier systematically underperforms for reasons unrelated to capital. Three candidate policies, in
  order of preference:

  | Policy | Mechanic | Assessment |
  |---|---|---|
  | **Instrument-based** *(recommended)* | L1 trades BTC; L2 BTC+ETH; L3 all three | Produces different trade counts naturally, is explainable to a client, and has no within-day arbitrariness |
  | Conviction-ranked | Capped tiers take only signals above a higher conviction threshold | Defensible — lower tiers get the *better* signals, not the earlier ones — but requires a stable conviction score |
  | First-N-of-day | Take signals until the cap is spent | Simplest to build, worst to defend. Not recommended |

**G3 — Site describes demo mechanics (detailed in §2.5).** "5-min verifiable rounds" and
"deterministic settlement against real candle closes" describe the synthetic binary engine.
Production has no rounds at all. §2.5 sets out what actually replaces them and what that means for
the product narrative.

**G4 — The +28% daily ceiling.** Already recorded as deferred (R1 §6.1). It is a property of the
synthetic instrument and does not exist on perps.

G3 and G4 need action before the first client funds an account; neither blocks LLD.

### 2.5 Trading mechanics: rounds versus positions

The change from 5-minute rounds to a 15-minute-to-4-hour holding period is not a parameter change.
It is a change of instrument, and the product vocabulary has to change with it.

| | Demo — synthetic binary | Production — perpetual futures |
|---|---|---|
| Unit of activity | A **round**: fixed 5-minute epoch | A **position**: opened on signal, closed on exit rule |
| Duration | Exactly 5 minutes, known in advance | Variable, typically 15 min – 4 h, not known at entry |
| Entry price | Strike locked at epoch start | Fill price, subject to spread and slippage |
| Outcome | Binary — win or lose, fixed payout | Continuous — P&L is a price difference, any magnitude |
| Settlement | Deterministic against the candle close at expiry | No settlement event; the position closes when the exit triggers |
| Counterparty | None; our own table | The market |
| Costs | None (`SPREAD = 0`) | Fees, funding, slippage — all real |

**"15 minutes, 1 hour, 4 hours" are not three round lengths.** Two distinct concepts sit behind
those numbers, and conflating them is the most likely source of confusion in client-facing copy:

- **Signal timeframe** — the bar size the strategy evaluates on. One value, currently 15-minute
  bars (R2 §S1). The strategy looks at the market once per closed bar.
- **Holding period** — how long a position stays open once entered. *Variable*, governed by the
  exit rules (ATR trailing stop or opposite-channel touch), typically landing between 15 minutes
  and 4 hours. Nobody chooses it; the market does.

So a client cannot select "the 1-hour product". There is one strategy, evaluated every 15 minutes,
holding positions for however long the exit rules dictate.

**What replaces "verifiable rounds" as the trust mechanic.** The round was a good trust story: fixed
epoch, locked strike, deterministic settlement, recomputable. Positions have no equivalent event to
point at — but the replacement is stronger, not weaker:

| Old claim | Replacement |
|---|---|
| Deterministic settlement against a candle close | **Reconciliation against the venue every 60 seconds** — our position and balance view is continuously proven against Hyperliquid's, and any mismatch halts the account (§4.1.4) |
| Recomputable round outcome | **Every order traces to exactly one intent** (P5), and every fill to a hash-chained ledger entry. The full chain — signal, risk verdict, order, fill, cost breakdown — is reconstructable per trade |
| Verifiable ledger | Unchanged, and now covering real fills rather than synthetic ones |

The honest framing for the site is that verification moved from *"we settle a synthetic round
correctly"* to *"we prove our books against the exchange every minute, and every trade explains
itself."* The second is a real claim about real money; the first was a claim about our own database.

---

### 2.6 Second venue: Polymarket (decision 18)

Polymarket is a central-limit-order-book prediction market on Polygon: binary outcome shares priced
0–1 in USDC, no leverage, no funding, no liquidation. It is structurally closer to the *demo's*
synthetic binary engine than Hyperliquid is — `binaryFairValue` / `settleBinary` (GBM binary
pricing, §R1 1.1) transfer almost directly, which means the calibration data the demo has been
accumulating is a genuine asset here, not a discard.

What changes and what does not:

| Concern | Hyperliquid (launch) | Polymarket (follow-on) |
|---|---|---|
| Instrument | 3 static perps | **Ephemeral markets** — each is born, trades, resolves, dies. Instruments must be entities with lifecycle, not an enum |
| Costs | 1.5/4.5 bps maker/taker + funding | No per-trade venue fee on most markets; cost is spread + thin-book slippage + resolution risk |
| Custody | Agent wallet, no withdrawal rights | CLOB L2 API credentials permit order operations; asset transfers require L1 wallet signatures we never hold. **This separation must be verified in LLD before any client Polymarket account** — it is an assumption, not yet a fact (O8) |
| Settlement | Continuous mark-to-market | Discrete resolution events; redemption is an on-chain act. Attribution gains a `resolution` event type alongside fills |
| Fatal constraint | Per-IP rate budget | **Thin books.** A per-account fan-out of N orders into a book holding $2K of depth is self-inflicted slippage. Liquidity budgeting must be *cross-account* (§4.7) |
| Regime inputs | Realized vol, macro calendar | Event-driven (elections, rulings). The shock detector's vol inputs do not transfer; regime guard becomes venue-class-aware |

Sequencing: Hyperliquid ships first exactly as planned; nothing in the ten-day path changes.
Polymarket enters as adapter #2 after the company-account soak, reusing `Alphaedge_Copy/`'s CLOB
integration experience (consensus filter, Gamma API) from the monorepo.

### 2.7 Automation-first operations (decision 19)

The operating goal is inverted from the v3 staffing plan: **the platform is run by its agents and
policies; humans handle exceptions and the approvals this design deliberately reserves.** The
mechanism is uniform across every workflow — the **trust ladder** (§4.8): each automated workflow
starts human-approved, graduates to auto-execution after a proving period of unchanged approvals,
and always retains owner veto and a kill switch. Target steady-state headcount is the §4.8 table —
roughly 3 FTE at 1,000 accounts instead of the v3 plan's 12.5.

## 3. Architecture

### 3.1 Architectural principles

| # | Principle | Consequence |
|---|---|---|
| P1 | Money moves through deterministic, replayable code — never through a model | Agents are structurally excluded from the trade path; the tool registry contains no order or funds tool at any tier |
| P2 | An agent may only act within the layer it owns | A1 governs regime; it has no write path to the profit lock or loss breaker (decision 5) |
| P3 | Every external effect passes a deterministic gate | Publication gate for communications; venue idempotency for orders |
| P4 | Fail closed | Risk resolver unavailable ⇒ lockdown. Reconciliation mismatch ⇒ account halts. Missing secret ⇒ hard fail |
| P5 | Every order traces to exactly one intent | Audit spine; also what makes per-trade client explanations possible |
| P6 | The demo is never touched | Separate app, database, deploy, domain (decision 8) |

### 3.2 Logical view

Six layers, top to bottom, matching the architecture diagram:

1. **Inputs** — market feeds; owner console (halt, unlock, approvals)
2. **Deterministic core** — Strategy → Risk → Execution → Reconcile, on durable workers
3. **Stores and venue** — Postgres; secrets manager; Hyperliquid
4. **Attribution and telemetry** — deterministic decomposition and structured logs
5. **Agent layer** — eight advisory agents, reading layer 4, writing only proposals and drafts
6. **Publication gate → client surfaces** — application, statements, opt-in channels

Data flows downward. The only upward path is the owner console into the core, and the only path from
the agent layer to a human outside the company runs through the gate.

### 3.3 Key architectural decisions

Decisions 1–11 are recorded with rationale in R1 §6. Summarised:

| # | Decision |
|---|---|
| 1 | Hyperliquid perps: BTC, ETH, PAXG |
| 2 | Managed accounts — automated execution on client venue keys |
| 3 | Retail clients, worldwide |
| 4 | Tiers are capital sizing only; identical strategy per client |
| 5 | A1 auto-locks/releases the regime layer only; owner retains manual halt and unlock |
| 6 | Build order: blockers → strategy + harness → core → agents → live |
| 7 | Day 10 = live on the company account; then soak; then clients |
| 8 | Parallel system; demo untouched |
| 9 | Holding period 15m–4h; scalping abandoned |
| 10 | Maker-first entries with bounded taker fallback; protective exits always taker |
| 11 | `Alphaedge_live/` in the monorepo, own Vercel project and database |
| 12 | Fee model is **10% of net new profit**, client-remitted, high-water marked (§4.5) |
| 13 | Tiers vary on **capital lane and trade allowance** only; strategy, risk and fee rate identical |
| 14 | Trade allowance is implemented as **instrument access** — L1 BTC, L2 +ETH, L3 +PAXG — not a daily count (§2.4 G2) |
| 15 | Crystallisation is **monthly**, UTC calendar month, with a **$25 minimum invoice** that rolls forward (§4.5.3) |
| 16 | Account state and reconciliation run over **WebSocket**; REST is a 15-minute backstop, reserving the IP weight budget for orders (§4.1.3a) |
| 17 | Log sink is **Axiom** — structured search, retention tiering, lowest cost at this volume (§9.3) |
| 18 | **Polymarket is the second venue** (owner, 2026-08-01). Hyperliquid remains launch venue; Polymarket follows behind a venue-abstraction layer (§4.7). The demo's binary-option pricing model finds its production home here |
| 20 | **Two deployed environments — DEV and PROD — with a gated promotion pipeline and flag-based feature rollout** (owner, 2026-08-01). Venues, strategies and features ship dark, prove themselves in DEV and behind flags in PROD, and reach clients by cohort. See §9.1, §9.5 |
| 19 | **Automation-first operations** (owner, 2026-08-01). Provisioning, account management, support, content and billing collections run agent- or policy-automated; humans handle exceptions and retained approvals only. Implemented as the trust ladder (§4.8) |

### 3.4 Technology stack

| Concern | Choice | Rationale |
|---|---|---|
| Application | Next.js on Vercel, own project | Consistent with the existing stack; project isolation protects the demo |
| Workers | Trigger.dev | Durable retries, per-account queue concurrency, checkpointed waits, run observability |
| Database | Postgres | Row locks for ledger append, transactional multi-table writes, real indices |
| Secrets | Managed secrets service; KMS/HSM as post-launch hardening | Day-10 substitute is envelope encryption with hard fail on absence — logged as debt |
| Log sink | External structured sink (Axiom or equivalent) | Vercel and Trigger.dev retention are both ephemeral |
| Inference | `claude-opus-5` via `@anthropic-ai/sdk`, differentiated by effort | R1 §3.3 |

---

## 4. Component design

### 4.1 Deterministic core

#### 4.1.1 Strategy

Pure function of `(market snapshot, account state, regime) → Intent[]`. No I/O, no writes. The same
compiled function runs in backtest, paper, and live — the harness supplies recorded snapshots, paper
supplies live snapshots with a simulated fill model, live routes to the venue. This eliminates
backtest/live divergence at the source.

#### 4.1.2 Risk

The sole authority that may reject an Intent, and the only place any limit is enforced. Every
rejection writes a `risk_event` with a machine-readable reason code.

Four independent lock sources with distinct release rules:

| Lock | Set by | Released by | A1 may touch |
|---|---|---|---|
| Owner manual halt | Owner console | Owner only | No |
| Regime (vol shock, calendar, macro) | Resolver + A1 | Deterministically, or A1 under its lock contract | Yes |
| Daily profit ceiling | Deterministic, sticky for the UTC day | Deterministic | No |
| Loss breaker | Deterministic, rolling release | Deterministic | No |

Additional deterministic checks: correlated-exposure cap by rolling-correlation bucket (BTC and ETH
are one position in stress, not two); funding-crossing rejection when projected funding removes the
expectancy; liquidity guard capping order notional against visible depth, tightest on PAXG.

#### 4.1.3 Execution

Maker-first: rest a limit at the touch, wait a bounded window, then cross as taker **only if the
signal still holds** — the recheck is the defence against adverse selection. All risk-reducing exits
cross immediately. Idempotent on `intent_id`; the client order ID derives from it so the venue, not
the platform, enforces idempotency.

#### 4.1.3a Venue rate limits and order fan-out (closes O4)

Hyperliquid applies two independent limits, and the distinction drives the whole fan-out design:

| Limit | Scope | Budget |
|---|---|---|
| IP-based | Per egress IP, aggregated across REST | **1200 weight / minute.** An unbatched action is weight 1; a batch is `1 + floor(batch_length / 40)` |
| Address-based | Per address; sub-accounts count as separate users | 10,000 request initial buffer, then **1 request per 1 USDC cumulatively traded**. Rate-limited addresses get one request per 10 s |

**Batching does not help our fan-out.** A batch is signed by one API wallet for one address. Our
clients are N distinct addresses with N distinct API wallets, so one signal produces N separate
weight-1 requests. There is no aggregation available.

That makes the IP budget the binding constraint, and it forces three design commitments:

1. **Account state comes over WebSocket, not REST polling.** Reconciling 1,000 accounts once a
   minute over REST would consume ~1,000 weight/minute on its own — over 80% of the budget before a
   single order. Per-account WebSocket subscriptions carry position and fill state; REST
   reconciliation drops to a low-frequency backstop (§4.1.4). This is a hard requirement, not an
   optimisation.
2. **REST budget is reserved for order actions.** With state on WebSocket, the full 1200/min is
   available for placement, cancellation, and the backstop sweep.
3. **Multi-IP egress is required above roughly 500 accounts.** At 1200 weight/min a single IP places
   at most ~20 orders/second, so a 1,000-account fan-out takes ~50 seconds from one IP. Below ~100
   accounts this is a non-issue (~5 s). Scaling past it means distributing execution workers across
   distinct egress IPs — an infrastructure task to schedule before the client count reaches it, not
   after.

**Fill fairness (risk R4).** Because the fan-out is necessarily sequential, some accounts fill
earlier than others on the same signal, and in a fast market that is a real difference in fill
price. The policy:

- **Randomise sequence per signal.** No account holds a structural position in the queue.
- **Track cumulative position bias.** Per account, the running mean of its normalised queue position
  across all signals. A fair system converges to 0.5 for everyone; drift flags a bug.
- **Bias the randomisation to correct drift.** Accounts running unlucky get weighted toward the front
  of subsequent fan-outs. This converges fill quality over time rather than only in expectation.
- **Publish it.** Mean queue position and realised slippage versus the signal's decision price
  appear in the client's own statement, so fairness is verifiable by the client rather than asserted
  by us.

Address-based limits are not expected to bind: a $5K account trading $5K of notional per day earns
5,000 requests/day against a need of a few dozen. The 10,000-request opening buffer covers the
onboarding period comfortably. **To verify in LLD:** whether info-endpoint requests draw on the
address budget or only the IP budget.

#### 4.1.4 Reconciliation

Continuous, via the per-account WebSocket state subscription: every position and balance update from
the venue is diffed against our view, and any divergence writes a `reconciliations` row, halts new
entries for that account, and raises an incident. A REST sweep runs as a low-frequency backstop
(every 15 minutes per account, staggered) to catch a stalled or silently dropped subscription — the
one failure mode a push-based design cannot self-detect.

This is the single most important control in the system. Note it is also the replacement for the
demo's "deterministic settlement" trust claim (§2.5): the books are proven against the exchange
continuously rather than at a synthetic round boundary.

### 4.2 Attribution and telemetry

Deterministic, no model involvement. Decomposes P&L into terms that sum exactly: signal, fees,
funding, slippage, sizing effect. Alongside it, a counterfactual per risk control — what each lock
cost or saved. Materialised per `(account, period)`, recomputed on fill.

Structured logging shares this layer: every line carries `correlation_id` (the `intent_id` where one
exists), `account_id`, `component`, `severity`, and a stable `event` enum. Redaction happens at the
logger. Logs are operational telemetry and are never the record of a trade — that is the ledger. See
R3 §1.

### 4.3 Agent layer

Eight agents, all advisory. Full specifications in R1 §3.2 and R3.

| Agent | Function | Authority | Effort |
|---|---|---|---|
| A1 Regime | Regime lock and release | Auto within its layer, under a machine-checkable lock contract | high |
| A2 Review | Drift detection, execution-quality audit | Draft + one `drift_warning` | xhigh |
| A3′ Ops | Incident triage; proactive log sweep incl. silent-failure detection | Notify only | medium |
| A4 Client | Per-trade explanation; weekly brief content | Read-only, row-scoped | low |
| A5′ Accounts | Full lifecycle recommendations with drafted reason text | Recommend only | low |
| A6 Research | Strategy spec authoring and backtesting | Cannot deploy | xhigh |
| A7 Content | Changelog and blog drafts | Draft only; owner publishes | medium |
| A8 Comms | Outbound message composition | Queue only; human sends initially | low |

Cross-cutting properties: no tool takes an identity argument (scope comes from the server session);
every tool call is logged to `agent_runs`; each agent sees its own last 20 scored runs so it can
calibrate against its own track record.

### 4.4 Publication gate

Every agent-authored text reaching a human outside the company passes four deterministic checks:
claims verification against re-runnable queries; a prohibited-content classifier (no forward-looking
statements, guarantees, advice, competitor comparisons, or other clients' data); approval (owner
click for public, template-binding for per-account); and an immutable record of what was sent to
whom. Neither A7 nor A8 has a publish or send tool — only a submit-to-gate tool. R3 §0.3.

### 4.4a Venue abstraction layer (decision 18)

One interface, N adapters. The deterministic core never imports a venue module directly:

- `VenueAdapter` contract: market data snapshot contribution, order place/cancel with idempotent
  client IDs, fill/state stream, reconciliation pull, custody verification. Hyperliquid and
  Polymarket each implement it; the core is compiled against the interface.
- **Instruments become entities.** `instruments (id, venue, symbol, kind: perp|binary, status:
  active|expiring|resolved|delisted, resolves_at, metadata)`. Strategy evaluates whatever the
  instrument table says is active for the account's tier — the ephemeral nature of prediction
  markets is data, not code.
- **Cross-account liquidity budget.** The per-account depth guard is insufficient on thin books:
  100 accounts each individually "small enough" still crush a $2K book together. Risk gains a
  venue-level budget per instrument — max fraction of visible depth the *platform in aggregate* may
  consume per window — allocated pro-rata across participating accounts before individual sizing
  runs. On Hyperliquid this budget almost never binds; on Polymarket it is the primary constraint
  and effectively caps how many accounts one market can serve.
- Regime Guard becomes venue-class-aware: vol-shock inputs for perps, event-window inputs for
  prediction markets, one resolver with per-class detectors feeding the same precedence rules.

### 4.4b Autonomous operations — the trust ladder (decision 19)

Every human touchpoint is classified once, and the classification is enforced in code:

| Class | Examples | Automation |
|---|---|---|
| **Deterministic policy** | Provisioning checks, dormancy pause, credential-expiry pause, dunning schedule, invoice issuance | Fully automatic from day one. No agent, no human — policy code |
| **Ladder-eligible** | A8 routine briefs and statements, A7 changelog entries, A5′ low-risk lifecycle transitions (dormancy, reactivation after clean recon) | Start human-approved → auto after N=10 consecutive unchanged approvals → periodic sampled review. Any edit or veto resets the counter |
| **Permanently human** | Owner halt/unlock, public blog posts, suspension for cause, account closure, anything touching the money path, strategy deployment | Never automated. This list is the safety floor and shrinking it requires a design revision, not a config change |

**Provisioning — the gap this revision closes.** No document previously specified how a client
actually connects. The pipeline, fully automated:

1. Sign-in → risk acknowledgement + terms (recorded, versioned).
2. Wallet connect → platform generates a dedicated agent wallet → client signs the venue's
   agent-approval action in our UI → platform verifies the grant on-venue.
3. Funding check (venue balance ≥ tier minimum) → paper mode auto-starts immediately.
4. Eligibility policy (deterministic: grant verified, funded, acknowledgement signed, no sanctions
   flag) → **auto-activation** with owner veto window, replacing the human approval click. A5′
   reviews the queue for anomalies instead of gating every entry.
5. Live trading begins at the next tick after activation.

Zero human actions on the happy path. A5′ + owner handle only the exceptions the policy rejects.

**Support** stays A4-first with one change: an explicit escalation queue with an SLA, and deflection
metrics published to the owner weekly. **Content**: A7's changelog class rides the ladder to
auto-publish; public blog remains permanently human. **Collections**: invoice issuance, payment
links, receipt matching, reminder sequence (A8 template-bound) and grace-period enforcement are all
policy-automated; the only human step left in billing is judgment on hardship exceptions.

### 4.5 Profit sharing — billing subsystem

**Model (decision 12): 10% of net new profit, remitted by the client.** A performance fee, not a
management fee, and the difference drives every requirement below.

#### 4.5.1 Profit definition — attributable, not equity-based

The naive definition (equity now minus equity at last crystallisation) is **wrong for this
architecture**, because the client retains full control of their own venue account. They may deposit
or withdraw at any moment without telling us. Under equity-delta accounting a $2,000 deposit is
indistinguishable from $2,000 of profit, and we would invoice the client for depositing their own
money.

We therefore measure profit from **our own fills only**, which the attribution layer (§4.2) already
computes:

```
cum_pnl = Σ (realised P&L of every position the platform closed for this account)
          − fees paid − funding paid
```

This figure is immune to client deposits and withdrawals by construction, because it never reads
equity. It is also already net of every execution cost, so the client is charged on what they
actually kept.

**Unrealised P&L is excluded.** A position open at crystallisation is carried forward, and its
profit falls into the next period when it closes. This is the more conservative choice — we never
invoice on a paper gain that later evaporates — and it removes an entire class of dispute.

#### 4.5.2 High-water mark

Mandatory. Without one, a client who loses 20% and then recovers 15% would be charged on the
recovery — charging twice for the same ground. Definition:

```
fee            = 0.10 × max(0, cum_pnl − hwm_pnl)
hwm_pnl (new)  = max(hwm_pnl, cum_pnl)
```

`hwm_pnl` starts at 0 and only ever rises. Worked example:

| Period | P&L in period | `cum_pnl` | `hwm_pnl` before | Fee charged | `hwm_pnl` after |
|---|---:|---:|---:|---:|---:|
| 1 | +$1,000 | $1,000 | $0 | **$100** | $1,000 |
| 2 | −$600 | $400 | $1,000 | **$0** | $1,000 |
| 3 | +$900 | $1,300 | $1,000 | **$30** | $1,300 |

Period 3 is the mechanism working: the client gained $900 but pays on only $300, because $600 of it
was recovering the period-2 loss. Losses carry forward indefinitely and are never written off.

#### 4.5.3 Crystallisation and collection

| Concern | Design |
|---|---|
| Crystallisation period | **Monthly**, on the calendar month boundary in UTC. Open item O3 if the owner prefers quarterly — quarterly is more client-favourable, as more losses net against gains before charging |
| Minimum invoice | Below a floor (suggest $25) the amount rolls forward rather than invoicing. `hwm_pnl` does *not* advance on a rolled-forward amount |
| Collection | Client-initiated transfer against an invoice. **We cannot debit the managed account** — trade-only keys, permanently. A payment link on the invoice is the practical implementation; the transfer is the settlement |
| Receipt reconciliation | Incoming payments matched to invoices; partial and late payments tracked as first-class states |
| Non-payment | Grace period → new entries suspended (positions and exits continue normally) → positions flattened → account closed. **Never a forced withdrawal** — we hold no permission to perform one, and would not exercise it if we did |
| Account closure | Final crystallisation on realised P&L against the standing high-water mark. No pro-rata concept applies; a performance fee is already inherently pro-rata |
| Client visibility | The invoice shows `cum_pnl`, the prevailing high-water mark, the increment charged, and the arithmetic. Every figure re-derivable from the ledger (NFR-10) |

#### 4.5.3a Builder codes — considered and rejected as the primary rail

Hyperliquid offers **builder codes**: a fee, set per order, paid to the routing application out of
the fill, up to 0.1%. The client approves a maximum builder fee once and may revoke it at any time.
It is a native, automatic collection rail that needs no invoice, no transfer, and no withdrawal
permission — precisely the mechanism §4.5.3 lacks.

We are not using it as the primary rail, for two reasons:

1. **It cannot express a profit share.** A builder fee is charged per fill on notional. "10% of net
   new profit" is only knowable at crystallisation, after costs and against a high-water mark. The
   two are structurally different instruments.
2. **It is a direct tax on the edge.** Our entire strategy viability rests on a 6–9 bps round-trip
   cost floor (§1.4, R2 §0). A builder fee at the 0.1% maximum adds **10 bps per side, 20 bps
   round trip** — more than tripling the cost floor and killing every candidate strategy outright.
   Even 1–2 bps is a material haircut on client returns at our horizon.

Recorded here because it is the obvious question a reviewer will ask, and because it remains a
genuine option if the fee model ever changes to volume-based. If automatic collection becomes
operationally necessary (§4.5.4), a *small* builder fee — 1–2 bps, not 10 — is the lever, and its
cost must be published in the client statement alongside exchange fees rather than buried.

**Related and deliberately not chosen:** Hyperliquid vaults allow clients to deposit into an account
we control. That would make collection trivial and reconciliation simpler — and it would also make
us a custodian, which changes the regulatory posture entirely (§9.4) and destroys the "your capital
stays in your account" trust property. Not on the table.

#### 4.5.4 Operational note

At retail scale, client-initiated transfers are the fragile part: 1,000 clients each remitting
manually every month is a reconciliation burden that grows linearly and fails noisily. The
architecture handles it — invoices, receipt matching, partial payments, a defined non-payment
path — but this is the subsystem most likely to need operational staffing rather than more code.

#### 4.5.5 Incentive asymmetry — stated plainly

A pure profit share with no management fee pays the desk 10% of gains and 0% of losses. That is a
call option on client capital, and it structurally rewards taking more risk: higher variance raises
the expected value of the fee while the downside sits entirely with the client. This is a
well-understood property of performance-only compensation, and naming it is not a criticism of the
model — it is a design constraint.

Three things in this architecture bound it, and all three should be treated as load-bearing rather
than nice-to-have:

- **Risk limits are deterministic and identical for every account** — the loss breaker, the
  correlated-exposure cap, the liquidity guard. No per-client risk dial exists that could be turned
  up quietly (decision 4 and 13 keep strategy identical across tiers).
- **The counterfactual is published** (§4.2). Every risk control's cost and saving is visible to the
  client, so a control being loosened shows up in their own statement.
- **Agents cannot size, place, or cancel an order at any tier** (P1). Risk-taking cannot drift
  through the agent layer.

The high-water mark also helps: it removes the incentive to gamble for recovery after a drawdown,
because losses must be genuinely earned back before any fee resumes.

### 4.6 Client surfaces

Application (positions, attribution, per-trade "why" cards showing fee/funding/slippage separately,
equity curve, counterfactual), statements, and opt-in outbound channels. Transparency is treated as
a product property, inherited from the demo's best instinct.

---

## 5. Data architecture

### 5.1 Principal entities

| Entity | Purpose |
|---|---|
| `accounts` | One per client per venue. Capital, risk multiplier, lifecycle state, custody reference |
| `intents` | Strategy output; the audit spine |
| `orders` | Venue submissions, idempotent on intent |
| `positions` | Live position per (account, instrument); reconciled, never derived from own fills alone |
| `ledger_entries` | Immutable, hash-chained, ordered by monotonic sequence |
| `risk_events` | Every rejection with machine-readable reason |
| `reconciliations` | Per-cycle venue diff |
| `regime_state` / `regime_events` / `regime_log` | Risk posture and its history |
| `agent_runs` / `agent_proposals` | Every invocation, its cost, its authority, and its scored outcome |
| `outbound_messages` / `communication_preferences` | Delivery record and consent |
| `fee_periods` | Per account per crystallisation period: `cum_pnl`, `hwm_pnl` before and after, increment charged, rolled-forward remainder (§4.5) |
| `invoices` / `payments` | Issued amounts, receipt matching, partial and late payment states |

### 5.2 Integrity

Ledger append occurs under a row lock on a sequence table inside the same transaction as the fact it
records, ordered by a monotonic sequence rather than a timestamp. Settlement and order-state writes
are idempotent on deterministic identifiers so concurrent workers are safe.

### 5.3 Retention

| Class | Retention |
|---|---|
| Ledger, intents, orders, fills, risk events | Indefinite |
| Logs — hot searchable | 30 days |
| Logs — warn and above, or carrying a correlation ID | 13 months |
| Logs whose correlation ID resolves to a fill | 7 years |
| Outbound messages | Indefinite |

---

## 6. Interfaces

### 6.1 External

| Interface | Protocol | Notes |
|---|---|---|
| Hyperliquid info | HTTPS POST | Marks, candles, clearinghouse state |
| Hyperliquid exchange | HTTPS POST, EIP-712 signed | Order placement and cancellation. Client order ID derived from intent |
| Hyperliquid `userFills` + user state | WebSocket per account | Primary fill detection **and** primary reconciliation source. REST is a 15-minute backstop only (§4.1.3a) |
| Economic calendar | HTTPS | Blackout windows; degrades to last known |
| Anthropic Messages API | HTTPS | Agent inference |
| Payment processor | HTTPS + webhook | §4.5, pending decision |

### 6.2 Internal

Application → workers by task trigger, never by direct database mutation of trading state. Workers
→ Postgres transactionally. Agents → data exclusively through registered tools; no agent holds a
database connection.

### 6.3 Agent tool contract

Every tool declares: read or write; the scope it operates in; whether its output requires gate
passage. A tool that mutates trading state or moves funds cannot be registered — this is enforced by
the registry, not by review.

---

## 7. Non-functional requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-1 | Scheduled strategy ticks that execute | ≥ 99.5% |
| NFR-2 | Execution worker availability | ≥ 99.9% |
| NFR-3 | Signal to order submitted, p95 | < 5 s |
| NFR-4 | Fill detection latency, p95 (WebSocket) | < 2 s |
| NFR-5 | Reconciliation | Continuous via WebSocket; REST backstop sweep every 15 min per account |
| NFR-6 | Ledger RPO / RTO | RPO 0; RTO < 1 h |
| NFR-7 | Account scale at launch+6mo | 1,000 accounts, 3 instruments |
| NFR-8 | Order fan-out per signal | ≤100 accounts within 10 s on one egress IP; 1,000 accounts within 60 s, requiring multi-IP egress (§4.1.3a) |
| NFR-12 | Fill fairness | Per-account mean normalised queue position converges to 0.5 ± 0.05 over any rolling 90-day window (§4.1.3a) |
| NFR-9 | Agent inference cost | ≤ $300/month baseline, plus ≤ $0.25/account/month |
| NFR-10 | Client-facing numbers reproducible | 100% — every figure re-derivable from the ledger |
| NFR-11 | Strategy replay determinism | Identical trades from identical recorded snapshots |

---

## 8. Security architecture

| Control | Design |
|---|---|
| Credential custody | Trade-only API wallets, no withdrawal permission, one per client, revocable. Signing keys in a managed secrets service; KMS/HSM as post-launch hardening. Hard fail if a key is absent — no fallback key exists |
| Key handling | The application requests a signature; key material is never held across an await boundary and is unloggable by construction |
| Access control | Database-backed roles. Role changes are permanently a human action, with no agent path |
| Row scoping | Every client-facing tool derives identity from the server session. A tool accepting a caller-supplied identity argument cannot be registered |
| Prompt injection | Untrusted text (calendar labels, client free-text, venue error strings) enters as delimited data. Blast radius is bounded structurally: no agent reading untrusted text holds an irreversible tool |
| Audit | Every intent, order, fill, rejection, regime transition, agent run, and outbound message retained and attributable |

---

## 9. Deployment, environments, and operations

### 9.1 Environments (decision 20)

Two deployed environments, fully isolated stacks. "Paper" and "testnet" are not environments — paper
is an account type that exists in both, testnet is the venue backend DEV points at.

| | DEV | PROD |
|---|---|---|
| Purpose | Integration, soak, promotion candidate | Live clients |
| Vercel | Own project (previews per PR, ephemeral) | Own project, own domain |
| Trigger.dev | `dev`/`staging` env of the same project | `prod` env |
| Database | Own Neon project; PROD-branch copies on demand for migration rehearsal | Own Neon project |
| Venue backend | Hyperliquid **testnet** (+ mainnet read-only feeds for realistic data) | Mainnet |
| Accounts | Paper + testnet only. Mainnet order placement is impossible: no mainnet signing keys exist in DEV's secret store | Live + paper |
| Agents | Enabled, `effort: low`, sends and publishes stubbed | Full |
| Secrets | Disjoint store. Nothing shared with PROD, ever | Disjoint store |

The demo remains a third, untouched deployment (decision 8) and is outside this model.

### 9.1a Feature rollout — everything ships dark

One mechanism for venues, strategies, and product features: a database-backed flag with cohort
scoping (`off → internal → company_account → canary cohort → all`). Deploys and releases are
decoupled — code reaches PROD dark, exposure is a data change, and rollback of a *feature* is a flag
flip, not a deploy. The Polymarket rollout is simply this mechanism applied to `venue:polymarket`:
adapter merges dark → DEV against PM infrastructure → PROD company pilot (O8 custody verification
happens here) → canary clients who opt in → GA. Instrument-level exposure continues to ride the
`instruments` table (§4.4a); the flag gates the venue as a whole.

### 9.2 Isolation from the demo

`Alphaedge_live/` sits in the monorepo with its own Vercel project, domain, environment, and
database. The demo's Vercel project is root-pinned to `Alphaedge_tradingbot/` and never builds the
new directory. No imports cross the app boundary; shared code is copied or extracted to `packages/`.

### 9.3 Observability

Structured logs to an external sink with the retention tiers of §5.3. A3′ sweeps daily for
error-rate deltas, previously unseen error signatures, latency drift, and silent failures — a dead
worker emits no errors, so heartbeat shortfall detection is the only thing that catches it.

### 9.5 Promotion to production

Promotion is a pipeline with deterministic gates, not a person with deploy rights:

```
PR → CI gates → merge to main → auto-deploy DEV → DEV soak (24h paper, clean) 
   → migration rehearsal on a PROD DB branch → promotion approval (owner or eng lead, one click)
   → PROD deploy (dark) → post-deploy smoke → flag exposure by cohort
```

| Gate | Blocking criteria |
|---|---|
| CI | Full test suite; the B1 regression; risk-branch coverage 100%; replay determinism on a recorded day; schema migration lints as additive |
| DEV soak | 24h continuous paper trading on live-read data: zero reconciliation breaks, zero unexplained FSM terminal states, heartbeats present |
| Migration rehearsal | Migration applied to a fresh Neon branch of the PROD database; rollback tested on the same branch. **Expand–migrate–contract only** — no destructive change ships in the same release that stops using the column |
| Promotion approval | Human click, recorded (who, what SHA, when). The one manual step, kept deliberately |
| Post-deploy smoke | Engine tick executes; one reconcile cycle clean per venue; owner console halt round-trips; then flags open |

Trading-specific rules: in-flight Trigger.dev runs complete on their prior version (native task
versioning); the deploy window avoids the top-of-bar tick by scheduling promotion between ticks;
code rollback = redeploy previous build (safe because migrations are additive); feature rollback =
flag flip (instant). Strategy parameter changes are code (LLD §15) and ride this same pipeline — no
runtime tuning surface exists, which now also means every parameter change gets a DEV soak by
construction.

### 9.4 Regulatory workstream

Automated discretionary trading of retail client capital, cross-border, for a fee is a licensed
activity in most jurisdictions. This is owner-led and runs in parallel; it does not block the build
but does block client launch. The architecture supports it by retaining a complete, per-client,
reconstructable record and by ensuring no agent surface offers advice.

---

## 10. Risks

| ID | Risk | Impact | Mitigation |
|---|---|---|---|
| R1 | **No proven edge.** No candidate has yet cleared the cost floor | Existential | Backtest harness before execution layer; go/no-go on measured expectancy (R2) |
| R2 | **Performance-fee incentive asymmetry.** 10% of gains, 0% of losses is a call option on client capital and structurally rewards risk-taking | Client losses; trust | §4.5.5 — identical deterministic limits for all accounts, published counterfactual, no agent order tools, high-water mark removing the gamble-for-recovery incentive |
| R9 | **Polymarket custody separation is unverified.** L2-credentials-cannot-move-assets is an assumption until proven | Client funds | O8 blocks any client Polymarket account; company account pilots first |
| R10 | **Thin prediction-market books.** Aggregate platform flow can be the dominant liquidity consumer | Slippage, market impact | Cross-account liquidity budget (§4.4a); per-market account cap it implies |
| R12 | **Deploy-time trading hazard.** A promotion mid-tick or a non-additive migration can strand in-flight intents | Stuck orders, recon breaks | §9.5: between-tick deploy window, task versioning, expand–migrate–contract, post-deploy smoke before flag exposure |
| R11 | **Trust-ladder regression.** An auto-graduated workflow drifts bad after graduation | Client-facing errors | Sampled review, edit-resets-counter, owner kill switch per workflow class |
| R8 | **Fee collection depends on client action.** We cannot debit; 1,000 monthly manual transfers is a linear operational load | Revenue leakage | §4.5.3 non-payment path; §4.5.4 — likely needs operational staffing, not more code |
| R3 | Regulatory exposure | Launch blocked | §9.4, parallel workstream |
| R4 | **Order fan-out and fill fairness.** Venue limits force sequential placement; batching cannot aggregate across client addresses | Fairness; slippage dispersion | **Designed, §4.1.3a**: WebSocket state to free the REST budget, randomised sequence with drift-correcting bias, per-account queue-position accounting published to the client. Multi-IP egress required above ~500 accounts |
| R5 | Strategy decay after launch | Client losses | A2 drift detection against backtest bands; documented retirement criteria |
| R6 | Venue dependency — single exchange, single chain | Total outage | Fail closed; reconciliation halts; multi-venue is out of scope for v1 |
| R7 | Ten-day schedule | Quality compromise | Owner has stated quality governs; the date moves if soak criteria are unmet |

---

## 11. Assumptions and dependencies

**Assumptions.** Hyperliquid API wallets support the required order operations without withdrawal
permission. Client capital sits in the client's own venue account throughout. The strategy selected
in R2 clears the cost floor on out-of-sample data.

**Dependencies.** Owner-supplied strategy notes (gates strategy work). `btcusdt-futures-bot/` source,
which is not present in the current Mac checkout and must be retrieved. Counsel engagement (gates
client launch). Multi-IP egress capability, required before the client count passes ~500 (§4.1.3a).

---

## 12. Traceability

| Requirement source | Addressed in |
|---|---|
| Decisions 1–11 (R1 §6) | §3.3, and throughout |
| Cost-floor analysis (R2 §0) | §1.4, §4.1.3, decision 9 and 10 |
| Log management request | §4.2, §9.3, R3 §1 |
| Account management request | §4.3 A5′, R3 §2 |
| Trade analytics request | §4.2, §4.6 |
| Blog/announcement request | §4.3 A7, §4.4 |
| Client update request | §4.3 A8, §4.4, §5.1 |
| Live product review | §2.1, §2.4 |

---

## 13. Open items

All engineering items are closed. Two remain, both owner-side, and **neither blocks LLD**.

### Closed by engineering decision, 2026-07-28

| ID | Item | Resolution |
|---|---|---|
| O1 | Trade allowance and allocation policy | **Decision 14** — instrument access (L1 BTC, L2 +ETH, L3 +PAXG). No daily count cap; no within-day allocation problem |
| O2 | Fee collection mechanism | **Decision 12** — client-remitted profit share against invoice. Builder codes evaluated and rejected (§4.5.3a) |
| O3 | Crystallisation period | **Decision 15** — monthly, UTC calendar month |
| O3b | Minimum invoice floor | **Decision 15** — $25, rolls forward; high-water mark does not advance on a rolled amount |
| O4 | Order fan-out and fill fairness | **§4.1.3a** — WebSocket state frees the REST budget; randomised sequence with drift-correcting bias; queue-position fairness published to clients. Multi-IP egress scheduled before ~500 accounts |
| O5 | Log sink | **Decision 17** — Axiom |

### Open — owner action

| ID | Item | Blocks |
|---|---|---|
| O6 | **Strategy rules.** Candidates and the selection protocol are in R2 and S1 can begin without them, but owner-held rules carry information no published source does | Nothing hard — S1 proceeds. Delays only the chance to test your own edge first |
| O7 | **Brief counsel that the fee model changed** to a performance fee (§4.5, §9.4). Performance fees attract more regulatory attention than management fees | Client launch. Not LLD, not the build |

### Pre-launch actions, not decisions

G3 and G4 (§2.4) — site copy still describes 5-minute rounds and the +28% ceiling. §2.5 supplies the
replacement vocabulary. Required before the first client funds an account; not required before the
company account goes live.

### Assumptions carried into LLD

Two items in §4.1.3a require confirmation against live venue behaviour during implementation, and
both have a safe fallback: whether info-endpoint requests draw on the address budget or only the IP
budget (fallback: assume both, budget conservatively), and observed WebSocket state-update
reliability (fallback: raise REST backstop frequency).

---

## 14. Sign-off

All engineering open items are closed (§13). LLD may begin on approval of this document; O6 and O7
run in parallel and gate neither the LLD nor the build.

Approving this document commits to: Hyperliquid perps on BTC/ETH/PAXG, managed accounts on
trade-only keys, a 10% high-water-marked profit share, instrument-based tiers, maker-first
execution, an eight-agent advisory layer structurally excluded from the trade path, and a parallel
build that leaves the demo untouched.
