# S1 breakout — first walk-forward results

**Date:** 2026-09-06
**Harness:** `src/lib/backtest.ts`, exposed at `GET /api/backtest` (owner only)
**Companion to:** [STRATEGY_CANDIDATES.md](STRATEGY_CANDIDATES.md)

---

## 0. The finding that comes before the numbers

The live demo engine has **exactly zero expected value by construction**, and this is
not a bug — it is what the code says it is.

`engine.ts` prices every entry at `modelP + SPREAD` where `SPREAD = 0`, and
`settleBinary` pays $1.00 per winning contract. So EV per contract is
`modelP × 1 − modelP = 0`. The code comment agrees: *"paper fills at model fair
value — expectancy ~breakeven, results = calibration vs reality."*

Two consequences:

1. **The demo desk's PnL is variance, not edge.** It measures whether the
   volatility model is calibrated. It does not measure a strategy, and its track
   record is not evidence that one exists.
2. **Connecting it to real funds converts 0 EV into reliably negative EV**, because
   the fee floor is subtracted from a zero-mean process. The current engine runs
   **5-minute** rounds — a horizon §0 of the candidates doc already ruled out.

So there was nothing to "tune". The gap was the harness.

---

## 1. Method

- S1 = Donchian breakout continuation. Long on close above the prior `lookback`
  high, short below the low. Exit after `hold` bars or at `stopAtr` × ATR.
- **Fills at the next bar's open**, never the signal bar's close.
- Costs: 1.5 bps maker / 4.5 bps taker, 65% maker fill on entry, protective exit
  always taker, 1 bp slippage on taker legs → **8.4 bps round trip**.
- Funding booked hourly from `fundingHistory` (Hyperliquid pays hourly, not on the
  8-hourly convention §3 assumed).
- Walk-forward, 4 folds. Parameters fitted on each train window, scored only on the
  window that follows. A 32-point grid. **In-sample numbers are not reported.**

Data ceiling worth knowing: Hyperliquid serves only the most recent ~5000 candles
per interval and ignores an older `startTime`. That caps 15m at ~52 days and 1h at
~200 days, and it is why the first run silently returned zero candles for BTC and ETH.

---

## 2. Out-of-sample results

Net = after fees, slippage and funding. Zero-cost is the same run with all costs set
to zero — the gap between the two columns is the cost drag.

| Asset | Horizon | Net OOS | Zero-cost OOS | Trades | Win rate | Sharpe |
|---|---|---|---|---|---|---|
| BTC | 15m | −0.45% | +4.36% | 72 | 0.36 | −0.33 |
| BTC | **1h** | **+14.88%** | +26.64% | 140 | 0.34 | 1.43 |
| BTC | 4h | −32.69% | −24.02% | 75 | 0.36 | −3.70 |
| ETH | 15m | −4.88% | +1.42% | 75 | 0.21 | −2.59 |
| ETH | 1h | −30.19% | +3.57% | 153 | 0.31 | −2.21 |
| ETH | 4h | −57.90% | −49.28% | 80 | 0.31 | −3.39 |
| GOLD (PAXG) | 15m | −3.87% | +4.08% | 87 | 0.30 | −4.47 |
| GOLD (PAXG) | 1h | +0.82% | +4.77% | 47 | 0.34 | 0.34 |
| GOLD (PAXG) | **4h** | **+20.91%** | +25.36% | 53 | 0.38 | 2.30 |

## 3. What this does and does not say

**It does not say we have a strategy.** Nine configurations were tested, each fitting
32 parameter sets per fold. Two came back clearly positive. That is roughly what
searching this much space over noise produces, and both winners sit near or below the
doc's own "40 trades is noise" line (BTC 1h has 140; GOLD 4h has 53). Treat both as
hypotheses to re-test on fresh data, not as results.

**What it does say, with more confidence:**

1. **The short horizons are cost-dead, as §0 predicted.** Every 15m cell is positive
   gross and negative net. The signal is real and smaller than the fee. This is now
   measured rather than argued, and the live engine's 5-minute horizon is shorter still.
2. **ETH's problem is funding, not fees.** At 1h it goes +3.57% gross to −30.19% net.
   The fee round trip is only 8.4 bps; the rest is carry. That is a specific, actionable
   result — it points straight at S2 (funding-aware tilt) rather than at signal tuning.
3. **Gold prefers the long end, not the short one.** PAXG improves monotonically with
   horizon, which is consistent with §0's arithmetic that a thin book and low vol make
   short-horizon gold unreachable.
4. **4h breakout is broken on crypto in this sample** — negative even before costs for
   both BTC and ETH, so it is not a cost problem there.

## 4. Next

- Re-test BTC 1h and GOLD 4h on a different window before believing either.
- Implement S2 as a funding filter, given finding 2 is the strongest signal here.
- Do not point real funds at the 5-minute binary engine. It has no edge by design.

---

# Replication test — 2026-09-06

The open question from the first run was whether BTC 1h (+14.88%) and GOLD 4h
(+20.91%) were edges or selection noise across nine configurations. The test:
split each series in half and run the walk-forward independently on each half.
An edge should appear in both halves. Noise concentrates in one.

| Asset | Horizon | First half | Second half | Full window | Verdict |
|---|---|---|---|---|---|
| BTC | 1h | **-8.89%** (68 tr, SR -2.03) | +10.76% (67 tr, SR 1.73) | +16.44% (141 tr) | **FAILED** |
| ETH | 1h | -5.25% (79 tr, SR -1.02) | -22.17% (32 tr, SR -8.92) | -12.23% (173 tr) | consistently negative |
| GOLD | 4h | +3.33% (32 tr, SR 0.97) | +4.88% (32 tr, SR 0.84) | +22.37% (53 tr) | weakly survived |
| GOLD | 1h | +0.02% (24 tr, SR 0.02) | -1.75% (64 tr, SR -0.60) | +0.82% (47 tr) | flat, no signal |

## Read

**BTC 1h is dead as a candidate.** Its headline number came entirely from the
second half; the first half loses money with a Sharpe of -2.03. That is the
signature of a lucky stretch, not an edge, and it is exactly why the first run
declined to claim it.

**GOLD 4h is the only survivor, and it is not yet actionable.** Both halves are
positive with similar Sharpe, which is what a real effect looks like. But each
half rests on 32 trades, well under the doc's own "40 trades is noise" line, and
the halves sum to roughly 8% against the full window's 22% — the fold geometry
is doing a lot of work. Promising enough to keep testing, nowhere near enough to
fund.

**ETH loses in both halves**, and the earlier finding stands: its gap between
gross and net is far wider than the 8.4 bps fee, so funding is the driver.

## Verdict

No strategy is currently worth risking real money on. One candidate of nine
survived a replication test, on a sample too small to act on.

## Next

1. S2 funding-aware tilt, tested on ETH first — the clearest mechanism in the data.
2. GOLD 4h on more history and more folds, to get the trade count above the noise line.

---

# Cost attribution and execution study — 2026-09-06 (uncommitted)

## A correction to the previous entry

The earlier claim that "ETH's problem is funding, not fees" was **wrong**, and the
error is worth recording because it is easy to repeat.

It came from comparing a `net` walk-forward against a `zero-cost` walk-forward.
Those are two separate runs, and the cost model feeds the parameter-selection
score — so each run picked DIFFERENT parameters. The gap between them was mostly
a different parameter set, not carry.

The fix: choose parameters ONCE under base costs, then re-score those same
out-of-sample trades under different cost models. Only the cost varies.

## Cost attribution, parameters held fixed

| Asset | Trades | Gross | Fee drag | Funding drag | Net |
|---|---|---|---|---|---|
| ETH 1h | 173 | +2.81% | **14.54 pp** | 0.51 pp | -12.23% |
| BTC 1h | 141 | +28.37% | **11.85 pp** | 0.08 pp | +16.44% |
| GOLD 4h | 53 | +27.25% | **4.45 pp** | 0.43 pp | +22.37% |

Fees outweigh funding by 28x on ETH, 148x on BTC, 10x on gold. **S2, the
funding-aware tilt, has nothing to harvest** and should drop down the ranking.

Note the fee drag is exactly `trades x 8.4 bps` in every row. Trade FREQUENCY is
the cost driver, not the fee rate.

## Execution study (same trades, execution assumption varied)

| Asset | taker/taker 11.0bps | base 8.4bps | maker entry 7.0bps | maker/maker 3.0bps |
|---|---|---|---|---|
| ETH 1h | -16.73% | -12.23% | -9.81% | **-2.89%** |
| BTC 1h | +12.78% | +16.44% | +18.42% | +24.06% |
| GOLD 4h | +20.99% | +22.37% | +23.11% | +25.23% |

## Read

1. **Maker execution amplifies an edge; it does not create one.** ETH improves by
   13.8 pp going from worst to best execution and is still negative. Execution
   cannot rescue a strategy with no gross edge.
2. **Execution matters in proportion to trade count.** The full execution range is
   worth 13.8 pp on ETH (173 trades) but only 4.2 pp on gold 4h (53 trades). §0's
   claim that maker-vs-taker is the highest-value decision holds for frequent
   strategies; for the one surviving candidate it is second-order.
3. **The cheapest lever is trading less.** Since fee drag is exactly trade count
   times round-trip cost, raising conviction and cutting trade frequency reduces
   cost linearly with no execution engineering at all.
4. **Gold 4h is stable across fold counts**: 4/6/8 folds give +17.45% / +16.93% /
   +17.80% with 53/61/67 trades. But an independent re-fetch of the same window
   gave +22.37% against +17.45%, so it is still sensitive to exact window
   boundaries — a fragility warning, not a green light.

## Verdict, unchanged

No strategy is worth risking real money on. Gold 4h remains the only candidate
that has survived anything, on a sample still too small to fund.

## Next

- Test a conviction filter on gold 4h: fewer, stronger breakouts to cut the fee
  drag directly.
- Re-test gold 4h against an independent window when more history is available.
- S2 is deprioritised; the data does not support it.

---

# Conviction filter and S3 — 2026-09-06 (uncommitted)

## Conviction filter on S1: noise, not a mechanism

Require the breakout to clear the channel by `conv` x ATR before entering, to cut
trade count (fee drag is exactly trades x 8.4 bps).

| Asset | conv 0 | conv 0.25 | conv 0.5 | conv 1.0 |
|---|---|---|---|---|
| GOLD 4h | +22.37% (53tr) | +10.29% (56tr) | +9.98% (50tr) | +24.37% (41tr) |
| BTC 1h | +16.44% (141tr) | +6.39% (88tr) | -12.32% (94tr) | -3.88% (49tr) |
| ETH 1h | -12.23% (173tr) | -14.41% (123tr) | -8.98% (98tr) | +3.74% (48tr) |

**Non-monotonic in all three.** A genuine conviction effect would improve
steadily with the threshold; average gross per trade on gold instead goes
51.4 -> 27.1 -> 29.1 -> 68.5 bps. That is noise. The apparent wins at conv 1.0
(gold +24%, ETH +3.7%) rest on 41 and 48 trades and are not claimed.

## S3 post-shock mean reversion: fails outright

Fade a move of `shockAtr` x ATR over `win` bars. 54-point grid, walk-forward.

| Asset | Full | First half | Second half | Avg gross/trade |
|---|---|---|---|---|
| GOLD 4h | -0.25% (34tr) | -7.63% | -3.95% | +8.1 bps |
| GOLD 1h | -16.41% (111tr) | -4.70% | -8.17% | **-6.5 bps** |
| BTC 1h | -22.86% (167tr) | -12.33% | -2.41% | **-5.3 bps** |
| ETH 1h | -12.18% (91tr) | -11.53% | +14.49% | **-5.3 bps** |

Negative gross on three of four means S3 loses money *before* any costs. The
hypothesis is wrong on these assets at these horizons, not merely too expensive.
ETH's positive second half repeats the BTC 1h pattern from the replication test:
one favourable stretch inside an otherwise losing series.

## Consolidated verdict

| Hypothesis | Outcome |
|---|---|
| S1 breakout, plain | Only gold 4h survived replication, below the noise threshold |
| S2 funding tilt | No effect. Funding is 0.08-0.51 pp against 4-15 pp of fees |
| S1 + conviction filter | Non-monotonic. Noise |
| S3 post-shock reversion | Negative everywhere, negative even before costs |

**No strategy is worth risking real money on.**

## Why this stops here rather than continuing

Roughly forty configurations have now been tested on this data, each fitting
32-54 parameter sets per fold. Hyperliquid serves about 200 days at 1h and 360
at 4h, and that window has been mined hard. Continuing to search it will
eventually surface something that looks profitable and is not — the risk of a
false positive now outweighs the chance of a real find.

The honest next step is **not another backtest**. It is either:

1. **Forward validation** — run gold 4h on data as it arrives, which is the only
   genuinely out-of-sample test left, or
2. **More history** from a source other than Hyperliquid's 5000-candle window.

Gold 4h is the sole candidate worth carrying into forward validation, and it
should be watched, not funded.

---

# Literature review + carry measurement — 2026-09-06 (uncommitted)

## What the published work actually says

Two searches, and both confirm STRATEGY_CANDIDATES.md §1 rather than overturning it.

**Directional momentum.** The peer-reviewed consensus is that time-series momentum
in crypto is real but is "significantly reduced by realistic transaction costs and
implementation challenges"; one comprehensive study finds many momentum portfolios
with statistically significant raw returns earn insignificant profits once costs
and liquidation are modelled. Note also what the literature actually tests: DAILY
horizons, cost assumptions around 0.1%, and portfolios of many coins. It does not
claim an intraday single-asset edge, which is what we had been testing.

**Funding-rate arbitrage / cash-and-carry.** This is the one widely documented
positive-expectancy crypto strategy. It is delta-neutral: hold spot and short the
perp, collect funding. Public write-ups claim 8-30% APY. The academic treatment is
much more sober, reporting that successful arbitrage needs both wide spreads and
duration, with forced exits in about 95% of opportunities.

## Measured on OUR venue and assets (200 days of Hyperliquid funding)

| Asset | Total funding over window | Annualised (short perp) | Share of hours positive |
|---|---|---|---|
| BTC | 2.50% | **4.56%** | 75.8% |
| ETH | 2.98% | **5.43%** | 79.7% |
| PAXG | 3.63% | **6.62%** | 85.5% |

Funding is positive 76-86% of all hours on all three. That is a persistent,
structural bias, not a fitted parameter — the first thing found in this whole
exercise that is not noise. But it yields **4.5-6.6% annualised gross**, well
under the 8-30% the retail guides advertise, and it is a carry trade requiring a
spot leg, not a directional strategy the current perp-only engine can express.

## Daily time-series momentum, tested because the literature points there

Always in market, long if the trailing L-day return is positive, else short. Fees
charged only on a flip. **In-sample across the full window** — not walk-forward —
so these numbers are optimistic by construction.

| Asset | L7 | L14 | L30 | L60 | L90 | Buy & hold |
|---|---|---|---|---|---|---|
| BTC | -62.41% | +139.73% | +80.44% | +126.09% | +84.41% | **+282.18%** |
| ETH | +51.46% | +72.53% | +180.99% | **+222.01%** | +94.57% | +59.68% |
| PAXG | +17.85% | -24.10% | +18.56% | +27.53% | +32.25% | **+44.92%** |

Even with the in-sample advantage, TSMOM **loses to buy-and-hold on BTC and gold**,
and BTC swings from -62% at L7 to +140% at L14 — adjacent lookbacks giving opposite
answers is the same instability seen everywhere else in this study. It beats
buy-and-hold only on ETH, on one lookback, in-sample. Not a finding.

## Where this leaves us

The only durable, non-fitted effect found anywhere in this research is the funding
carry. It is market-neutral and modest. It is also a different product from what
the engine currently does: it needs a spot leg and it earns yield rather than
trading direction.

Nothing here changes the standing verdict on the directional strategies.
