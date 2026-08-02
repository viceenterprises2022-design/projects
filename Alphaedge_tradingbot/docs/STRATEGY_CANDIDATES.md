# Strategy candidates — Hyperliquid perps (BTC, ETH, PAXG) + Polymarket (§5)

**Status:** research input for §7 days 3–4. Nothing here is validated. No candidate becomes a
strategy until the backtest harness says so on our own data, with our own costs.
**Date:** 2026-07-28
**Companion to:** [PRODUCTION_DESIGN.md](PRODUCTION_DESIGN.md)

---

## 0. Read this part first — the cost floor

Before any strategy discussion, the arithmetic that decides which horizons are even reachable.

Hyperliquid base perp fees are **0.015% maker / 0.045% taker** (1.5 bps / 4.5 bps), improving with
14-day volume tiers, HYPE staking discounts, and maker rebates at high volume share. At our starting
size we are at base tier.

| Execution style | Round-trip fee |
|---|---|
| Taker in, taker out | **9.0 bps** |
| Taker in, maker out | 6.0 bps |
| Maker in, maker out | 3.0 bps (with fill risk on both legs) |

Now compare that against how far price actually moves in a given window. One-sigma move ≈
`annualised_vol × √(minutes / 525,600)`:

| Horizon | BTC @ 50% ann. vol | PAXG @ 15% ann. vol | Taker round-trip as % of 1σ (BTC) |
|---|---|---|---|
| 5 min | 15.4 bps | 4.6 bps | **58%** |
| 15 min | 26.7 bps | 8.0 bps | 34% |
| 1 hour | 53.4 bps | 16.0 bps | 17% |
| 4 hours | 106.8 bps | 32.0 bps | 8% |

Three conclusions, and they constrain everything downstream:

1. **5-minute taker scalping on BTC needs to capture 58% of a one-sigma move just to break even
   on fees** — before spread, before slippage, before funding, before being wrong half the time.
   No published intraday effect is that large. This horizon is not reachable with taker execution.
2. **PAXG scalping is arithmetically dead at short horizons.** A 9 bps round trip against a 4.6 bps
   5-minute sigma means costs are roughly double the entire typical move. PAXG only works at
   multi-hour horizons, or maker-only, or not at all. Its thin Hyperliquid book makes this worse,
   not better.
3. **The single highest-value engineering decision is maker-vs-taker execution**, not signal choice.
   Going from taker/taker to maker/maker cuts the cost floor by two-thirds and moves the viable
   horizon down by roughly an order of magnitude. It costs us fill certainty, which the strategy has
   to be designed to tolerate.

**Recommendation, stated plainly:** target a **15-minute to 4-hour** holding period, not seconds-to-
minutes. You asked for scalping; the fee schedule says scalping is where our edge goes to die unless
we are maker-only with real queue-position logic, which is a much larger build than 10 days.

> **Resolved 2026-07-28:** owner agreed — scalping abandoned, 15m–4h band adopted (design doc §6
> decision 9). Execution style also decided: maker-first entries with a signal-rechecked taker
> fallback, protective exits always taker (design doc §6.3). Backtests must model both fee legs and
> carry a fill-rate sensitivity row.

---

## 1. Why there is no "top 5 performing strategies" list

Worth being direct about, since it shapes what follows. Nobody who has a genuinely profitable live
scalping strategy in crypto publishes it — publication destroys it, and the marginal value of
selling it exceeds the marginal value of running it only when it does not work. What is publicly
available splits into two piles:

- **Academic literature** — real, peer-reviewed, and typically reporting effects of 1–5 bps that are
  statistically significant and economically dead once you subtract 9 bps of fees. Useful as a source
  of *hypotheses*, not of strategies.
- **Retail content marketing** — session guides, indicator combinations, "goldmine" setups. Almost
  none of it is backtested with costs, and much of what surfaced in searching for gold intraday
  strategies falls here. I have used it only where it describes a *structural* market fact (session
  liquidity patterns) rather than a claimed edge.

So the five below are **hypothesis families with published supporting evidence**, specified tightly
enough to backtest, ranked by probability of surviving our cost floor. The harness decides. That
sequencing — spec, then backtest with real costs, then paper, then live — is the whole point of
§2.6 in the design doc.

---

## 2. The candidates

### S1 — Intraday time-series momentum / breakout continuation

**Thesis.** Crypto exhibits persistent time-series momentum at intraday-to-daily horizons: a move
that has begun tends to continue over the following bars more often than chance. This is the most
replicated effect in the crypto literature and the one with the largest effect size.

**Evidence.** Dynamic time-series momentum in cryptocurrencies and high-frequency momentum trading
studies both find exploitable continuation; combined momentum/reversal strategies on hourly BTC data
(Gemini, 2015–2022) report roughly double the risk-adjusted return of buy-and-hold.

**Signal spec (backtestable as written).**
- Donchian channel breakout, lookback `N` bars (start `N = 20` on 15m bars = 5 hours).
- Long only if close > EMA(200) on the same timeframe; short only if close < EMA(200).
- Volume filter: breakout bar volume > median volume of last 20 bars.
- Strong-close filter: long requires close in top 25% of the bar's range; short, bottom 25%.
- Exit: ATR-based trailing stop (start `2.5 × ATR(14)`), or opposite-side channel touch.

**Why it may survive.** Effect size scales with holding period; at 15m–4h the 9 bps cost is 8–34% of
a one-sigma move rather than 58%. Trade count is low, so cost drag is bounded.

**Why it may die.** Breakout strategies have low win rates (30–45%) and depend entirely on the tail
of winners. Sensitive to the whipsaw regime. Needs the full multi-regime backtest, not a bull sample.

**Head start:** `btcusdt-futures-bot/` in this monorepo already implements exactly this — Donchian(20)
+ EMA(200) + volume + strong-close, paper-trading on Hyperliquid BTC. It is the fastest path to a
first harness result and should be candidate zero.

---

### S2 — Funding-rate-aware positioning tilt

**Thesis.** The perpetual funding rate is a direct, observable measure of leveraged positioning.
Extreme positive funding means crowded longs — which both taxes long holders and marks the crowding
that precedes liquidation cascades.

**Evidence.** The crypto carry strategy posted an annualised Sharpe of about 6.45 over 2020–2025,
driven mostly by the funding rate itself (mean ≈ 8% return, 0.8% volatility). **But the same work
shows the Sharpe falling to 4.06 from 2024 and turning negative in 2025.** Funding-rate spread
patterns also show statistically significant intraday and day-of-week structure tied to the 8-hour
settlement mechanism.

**Signal spec.**
- Compute funding z-score over a 30-day rolling window, per asset.
- `z > +2` (crowded long): block new longs, permit shorts, and size shorts up modestly.
- `z < −2` (crowded short): mirror.
- Never a standalone entry. A gate and a size multiplier on top of S1 or S3.
- Separately: for any position held across an 8-hour settlement, book the funding cost explicitly
  in the backtest. Holding a crowded-side position overnight is a real, quantified drag.

**Why it may survive as a filter.** Even with the standalone carry trade decaying, funding as a
*crowding indicator* is orthogonal to price-based signals and costs nothing extra to compute.

**Why it may die as a strategy.** The 2025 sign flip is a serious warning. Do not deploy this
standalone. Deploy it as a tilt, and re-check the sign annually.

---

### S3 — Post-shock short-horizon mean reversion

**Thesis.** Sharp moves on elevated volume overshoot and partially retrace. This is the reversal
half of the intraday-predictability finding, and it is the natural complement to S1.

**Evidence.** Intraday return predictability in crypto contains *both* momentum and reversal, with
which one dominates conditional on jumps, FOMC releases, liquidity level, and market stress. That
conditionality is the strategy — it is also the reason a naive always-revert rule fails.

**Signal spec.**
- Trigger: a single 5m bar moving more than `k × σ_5m` (start `k = 3`), with volume > 3× median.
- Direction: fade the move.
- Confirm: require the next bar to *not* extend (avoids catching a genuine breakout).
- Exit: target 50% retracement of the trigger bar, or time-stop at 12 bars (1 hour).
- Hard veto: skip entirely if the Regime Guard is in caution or lockdown. Post-shock reversion is
  precisely the trade that gets destroyed by real news, and our shock detector already fires on
  exactly this signature.

**Why it may survive.** Complementary P&L profile to S1 — high win rate, small winners, occasional
large loser. Blends well with a breakout book.

**Why it may die.** The occasional large loser is a liquidation event, and this strategy is short
gamma by construction. Stop discipline is not optional; the −15% breaker is the backstop, not the
plan. Reversion also overlaps dangerously with the existing shock detector — if the detector locks
down first, this strategy never trades. That interaction needs to be explicitly resolved, not
discovered in production.

---

### S4 — Order-flow imbalance / microstructure

**Thesis.** Book imbalance predicts the next price move. Near-linear relationship between order-flow
imbalance and short-horizon returns, strongest within tens of seconds.

**Evidence.** The strongest theoretical foundation of anything here — deep order-flow imbalance work
extracts alpha at multiple horizons from the limit order book, and the imbalance/return relationship
is well documented.

**Assessment: out of scope, and I recommend against attempting it in this window.** The signal
decays in seconds, reverses abruptly, and depends on feed quality, latency, and hidden liquidity.
Capturing it requires colocated infrastructure and maker-only execution with queue-position modelling.
Our stack is durable serverless workers on a 1-minute cron. We would be systematically adversely
selected — trading against participants who see the book change before our snapshot arrives. This is
a genuine edge that we are not currently built to harvest, and building for it is a different
project, not a phase of this one.

Listed because you should know it exists and know why we are not doing it, not because it is a
candidate.

---

### S5 — Session and time-of-day conditioning (overlay, primarily for PAXG)

**Thesis.** Gold's liquidity and directional movement concentrate in the London/New York overlap;
the Asian session compresses into ranges. Time-of-day is a free conditioning variable.

**Evidence.** The 12:00–16:00 GMT overlap carries the highest volume and tightest spreads, and
reportedly sets gold's daily high or low a large fraction of the time. Note that the sources here are
predominantly trading-education content rather than peer-reviewed work — treat the *structural* claim
(liquidity concentrates in the overlap) as reliable, and any specific hit-rate percentage as
unverified until our own data confirms it. Separately, crypto shows a documented turn-of-candle
effect with returns concentrated at the 0/15/30/45-minute marks, attributed to HFT activity around
candle boundaries.

**An important caveat specific to us:** we trade **PAXG on Hyperliquid**, not XAUUSD spot. PAXG is
tokenised gold with crypto-market microstructure — a thinner book, crypto-native flow, and 24/7
trading. Session research on the underlying gold market describes the price PAXG tracks, not the
venue we execute on. Verify every session claim on Hyperliquid PAXG data specifically.

**Signal spec.** Not a standalone strategy. An overlay:
- Permit PAXG entries only during 11:00–17:00 UTC unless a separate signal is unusually strong.
- Apply a size multiplier by session bucket, fitted on our own data.
- Test, do not assume, the turn-of-candle effect at our own bar boundaries.

---

### S6 — Regime allocator: S1 and S3 as one book

**Thesis.** The central finding of the intraday-predictability literature is not "momentum works"
or "reversal works" — it is that **which one dominates is conditional** on trend state, jumps,
liquidity, and stress. S1 bleeds to death in chop (whipsawed breakouts); S3 gets run over in trends
(fading moves that keep going). Running each only in its regime is worth more than improving either
signal, and it is the piece almost every retail system is missing.

**Signal spec (deterministic, no model in the loop).**
- Classify each asset each bar with the Kaufman efficiency ratio:
  `ER = |close_now − close_N| / Σ|close_i − close_i−1|` over `N = 48` 15m bars (12 hours).
  Direct, parameter-light measure of "trending vs churning"; ADX(14) > 25 as the confirming vote.
- `ER > 0.35` (trending): **S1 armed, S3 disarmed.**
- `ER < 0.20` (churning): **S3 armed, S1 disarmed.**
- Between the thresholds: hysteresis — keep the previous state. No flip-flopping at the boundary,
  and a state change never force-closes an open position; it only gates *new* entries.
- Regime Guard caution/lockdown overrides the allocator entirely, as everywhere else.

**Why it may survive.** It attacks both candidates' primary failure mode directly, with two
thresholds as the only new parameters. The conditionality it exploits is the best-replicated result
in the literature we reviewed.

**Why it may die.** Classifier lag: ER needs bars to see a regime change, so it arms S1 late into
new trends and disarms it late into chop. The backtest must charge that lag honestly — evaluate the
allocator against always-on-S1 and always-on-S3 baselines, and keep it only if it beats both after
costs.

**Backtest note.** Test S1 and S3 standalone *first* (clean baselines), then the allocated blend.
Three runs, one comparison table.

---

## 3. Ranking and what to test first

| Rank | Candidate | Role | Test order |
|---|---|---|---|
| 1 | **S1 Momentum/breakout** | Primary strategy | Day 3, first — code already exists |
| 2 | **S3 Post-shock reversion** | Secondary, complementary | Day 3–4, after S1 baseline |
| 3 | **S6 Regime allocator** | Meta-layer: arms S1 or S3 by trend state | Day 4, once both baselines exist |
| 4 | **S2 Funding tilt** | Filter + size multiplier on S1/S3 | Day 4, as an overlay on whichever survives |
| 5 | **S5 Session overlay** | PAXG gating, size shaping | Day 4, overlay only |
| — | **S4 Order-flow** | Not attempted | Documented, deferred, revisit post-launch |
| post-soak | **S7 Polymarket binary edge** | Venue #2 book | After Hyperliquid soak + O8 custody verification |

**Test protocol for each**, non-negotiable if the numbers are to mean anything:
- Walk-forward, not a single in-sample fit. Fit on rolling windows, evaluate out-of-sample only.
- Costs modelled per §6.3 of the design doc: both execution legs (maker fill at assumed 60–70%
  rate, taker fallback otherwise, protective exits always taker), with fill rate *and* slippage
  each getting a sensitivity row. If a candidate is only profitable at optimistic assumptions, it
  is not profitable.
- Funding booked on every 8-hour settlement crossed, and the harness must apply the same
  funding-crossing rejection the production Risk layer applies (§2.2) — otherwise backtest and
  live trade different rule sets.
- Liquidity-capped sizing per the Risk layer's depth guard, using recorded book-depth snapshots
  where available; PAXG results without a depth cap are fiction and will not be reported.
- Entry timestamps offset a few seconds past bar close — the documented turn-of-candle effect
  concentrates HFT activity exactly on the boundary, and pretending we fill at the boundary print
  flatters every backtest. Fill at next-bar prices, never the signal bar's close.
- Reported per-regime (trend / chop / shock) and per-asset, never as a single blended number.
- Report trade count alongside Sharpe. A great Sharpe on 40 trades is noise.
- Every run reports the **allocator comparison** where applicable: candidate alone, candidate under
  S6, and the delta after costs.

**The honest prior:** most of these will not clear the cost floor at short horizons. That is the
expected outcome and the reason we build the harness before the execution layer. Finding out on day
4 that the horizon must stretch to 4 hours is a cheap discovery; finding out in week 3 of live
trading is not.

---

## 4. What I still need from you

Your notes are the highest-value input here — anything you have traded yourself carries information
that no published source does, because it has not been arbitraged by everyone who read the paper.
Specifically useful:

1. **Entry and exit rules**, however informal. "I go long when X and get out when Y."
2. **What timeframe you actually watch.** This settles the horizon question faster than my arithmetic.
3. **What you have seen fail.** Negative results are as valuable and much rarer.
4. **Whether you have a view on maker vs taker.** §0 makes this the highest-leverage decision in the
   whole build, and it needs answering before day 5.

---

## Sources

- [Intraday return predictability in the cryptocurrency markets: momentum, reversal, or both](https://www.sciencedirect.com/science/article/abs/pii/S1062940822000833) — Wen, Bouri, Xu, Zhao
- [Dynamic time series momentum of cryptocurrencies](https://www.sciencedirect.com/science/article/abs/pii/S1062940821000590)
- [High frequency momentum trading with cryptocurrencies](https://www.sciencedirect.com/science/article/abs/pii/S0275531919308062)
- [On the intraday return curves of Bitcoin: predictability and trading opportunities](https://www.sciencedirect.com/science/article/abs/pii/S1057521921001228)
- [Deep order flow imbalance: extracting alpha at multiple horizons from the limit order book](https://onlinelibrary.wiley.com/doi/10.1111/mafi.12413) — Kolm et al., Mathematical Finance
- [Order Flow Imbalance — a high frequency trading signal](https://dm13450.github.io/2022/02/02/Order-Flow-Imbalance.html)
- [Temporal dynamics of market microstructure in cryptocurrency perpetual futures](https://www.mdpi.com/2227-7072/14/5/103)
- [The two-tiered structure of cryptocurrency funding rate markets](https://www.mdpi.com/2227-7390/14/2/346)
- [Cryptocurrency as an investable asset class: coming of age](https://arxiv.org/pdf/2510.14435)
- [Turn-of-the-candle effect in bitcoin returns](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10015199/)
- [Bitcoin never sleeps: exploiting seasonality, momentum and mean reversion](https://paperswithbacktest.com/blog/bitcoin-never-sleeps-exploiting-seasonality)
- [Hyperliquid fees explained: maker, taker, funding](https://eco.com/support/en/articles/15191998-hyperliquid-fees-explained-maker-taker-funding-and-withdrawal-in-2026)
- [Hyperliquid fees 2026: maker/taker and perp tiers](https://hiperwire.io/explainers/hyperliquid-trading-fees-explained)
- [London/NY overlap XAU/USD session structure](https://fxnx.com/en/blog/london-ny-overlap-goldmine-strategy-xau-usd) — trading-education source, structural claim only


---

## 5. S7 — Polymarket (added 2026-08-01, decision 18)

The demo's GBM binary model (`binaryFairValue`) was built for exactly this instrument shape — its
months of calibration data (reliability buckets, Brier scores from A2's lineage) are the head start.
Two candidate edges, both to be validated in the §2.6 harness pipeline like everything else:

- **S7a Mispriced-probability**: fair-value the market from observable inputs (crypto-linked markets
  price off the same BTC/ETH feeds we already consume), enter when market price diverges from model
  beyond spread + impact. The demo engine, pointed at a real book at last.
- **S7b Whale-consensus follow**: port of `Alphaedge_Copy/`'s Polymarket bot — enter only when ≥2
  tracked high-Sharpe wallets agree on a market. Social edge, orthogonal to S7a.

Constraints that dominate: thin books (the cross-account budget in LLD §22.3 is the binding limit),
resolution risk (binary terminal outcomes — position sizing must assume total loss is possible per
market), and no venue fee but real spread. Backtesting needs Polymarket historical books, which are
harder to source than candles — Gamma API history + recorded snapshots once the adapter exists.
