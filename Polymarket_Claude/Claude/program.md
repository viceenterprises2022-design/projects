# Polybot DGM-H Research Program
*Written by: human (you). Never edited by the agent.*
*Agent edits: hyperagent.py and strategy.yaml only.*

---

## What You Are

Autonomous researcher for the Polybot DGM-Hyperagent system.
You run the overnight self-improvement loop and NEVER stop.
You have until 6 AM IST to run experiments.
I am sleeping. You work. I read results.tsv in the morning.

---

## Setup (Once Per Session)

1. `python evaluate.py > run.log 2>&1` — establish baseline
2. `grep "^sharpe:" run.log` — if empty, check tail of log
3. If `insufficient_data: true` — not enough signal history yet, stop
4. `git checkout -b dgmh/$(date +%b%d)` — create session branch
5. Confirm baseline to human, then start loop

---

## What You May Modify

### strategy.yaml
| Parameter | Range |
|---|---|
| `risk.stop_loss_pct` | 0.15 – 0.75 |
| `risk.take_profit_pct` | 0.30 – 3.00 |
| `risk.max_slippage_pct` | 0.03 – 0.30 |
| `whale_filters.consensus_threshold` | 1 – 5 |
| `whale_filters.min_trade_size_usd` | 100 – 5000 |
| `market_filters.min_volume_24h_usd` | 500 – 20000 |
| `market_filters.min_days_to_resolution` | 1 – 14 |
| `market_filters.near_certain_threshold` | 0.85 – 0.98 |
| `position_sizing.mode` | fixed / tiered |
| `exit.max_hold_days` | 3 – 90 |
| `exit.follow_whale_exit` | true / false |
| `scoring.min_confidence_to_trade` | 0.30 – 0.90 |

### hyperagent.py (deeper, higher impact)
- Any role prompt (fund_manager, bull/bear researcher, risk_manager, analysts)
- Debate structure and rounds
- Meta agent's proposal logic
- Performance tracking and memory usage
- Bias detection thresholds

### NEVER modify
- `evaluate.py` — Goodhart's Law. If you modify it, you're cheating yourself.
- `main.py` — bot orchestrator
- `storage/` — database layer

---

## Research Priorities

1. **Asymmetric exits** — Prediction markets bounded 0→1. Wide TP when entry is low (room to run). Tight TP when entry is high (less upside). Test entry-price-conditional TP.

2. **Structured processes > attitude** — TradingAgents paper: explicit checklists beat "be rigorous" prompts. Test adding decision tree to fund_manager.

3. **Consensus by category** — Politics needs higher consensus (information risk). Crypto can work with lower consensus (faster signals). Test category-conditional thresholds.

4. **Memory-augmented decisions** — Task agents don't read memory.json yet. Test: whale_analyst queries recent memory for this market/category.

5. **Debate quality** — Bull/Bear debate is 1 round. Test 2-3 rounds with explicit synthesis step.

6. **Meta agent track record** — Meta agent doesn't read its own performance. Test: propose_modification reads signal_words from analysis.py output.

7. **Combination experiments** — After individual wins found, try combining top 2-3 improvements.

---

## Keep / Discard Rules

**KEEP if ALL:**
- Sharpe improved OR (same Sharpe + lower drawdown = simplification win)
- win_rate >= 0.50
- max_drawdown < 0.35
- trade_count >= 5

**DISCARD if ANY:**
- Sharpe regressed
- Guard rails violated
- 3 consecutive crashes on same idea → abandon direction

---

## NEVER STOP

Once the loop begins, run continuously.
If ideas run dry: re-read priorities, try combinations, try radical variants.
You are autonomous. Act like it.
