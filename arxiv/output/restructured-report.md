┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  Locally Coherent, Globally Incoherent                                  ┃
┃  Bounding Compositional Incoherence in Multi-Component LLM Agents       ┃
┃  arXiv:2605.30335 · ICML 2026 Workshops                                 ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

═══════════════════════════════════════════════════════════════════════════
                              CONCEPT MAP
═══════════════════════════════════════════════════════════════════════════

  ┌─ Core Problem ──────────────────────────────────────────────────────┐
  │  Compositional Incoherence → Probability Axiom Violations            │
  │  → Local Coherence Failure → Dutch-book Exposure                    │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─ Key Metric: ε* ────────────────────────────────────────────────────┐
  │  Compositional Residual → L2 Distance to Coherent Polytope           │
  │  → Runtime Certificate → Distribution-free Guarantee                 │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─ Theoretical Framework ─────────────────────────────────────────────┐
  │  Product-structure Dichotomy (Theorem 3.3)                           │
  │  ├─ Cartesian Product Factorization                                  │
  │  └─ Non-commutation Characterization                                 │
  │  Magnitude Prediction                                                │
  │  ├─ Rayleigh-quotient Form                                           │
  │  ├─ Specialist Panel Covariance                                      │
  │  └─ Corollary 3.9                                                    │
  │  Exposure Bound (FTAP)                                                │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─ Solutions & Repairs ───────────────────────────────────────────────┐
  │  Hierarchical JCD                                                    │
  │  ├─ Boyle–Dykstra Projection                                         │
  │  ├─ Convex-analytic Repair                                           │
  │  └─ Deterministic Convergence                                        │
  │  Sequential Monitoring                                                │
  │  ├─ Anytime-valid e-process                                          │
  │  ├─ Ville's Inequality                                               │
  │  └─ Coherence Testing                                                │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─ Empirical Results ─────────────────────────────────────────────────┐
  │  Benchmarks: Paleka (Logical Relations), Polymarket (Partitions)    │
  │  Metrics: Brier Improvement, Log-payoff Gain, Regret Reduction      │
  │  Mitigation Failures: Retrieval Grounding, Prompting, Aggregator    │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─ Deployment Modes ──────────────────────────────────────────────────┐
  │  Monitor Mode → Repair Mode → Abstain-or-escalate Mode               │
  └─────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
                         1.  EXECUTIVE SUMMARY
═══════════════════════════════════════════════════════════════════════════

  Multi-component LLM agents route sub-tasks to specialist models, but
  this decomposition introduces a subtle failure mode: each component is
  *locally coherent* (consistent on its own sub-task), yet the aggregated
  output is *globally incoherent* (violates basic probability axioms).

  Key findings across 1,876 ensemble cliques:

    • Incoherence occurs in 33%–94% of task groupings
    • Measurable Dutch-book exposure: -0.115 nats per bet in regret
    • Intuitive mitigations (RAG, prompt engineering) often make it worse
    • A hierarchical Boyle–Dykstra projection repair drives ε* → 0
      deterministically for ~1ms per partition with zero extra LLM calls


═══════════════════════════════════════════════════════════════════════════
                   2.  DEFINING COMPOSITIONAL INCOHERENCE
═══════════════════════════════════════════════════════════════════════════

  2.1  The Failure

  A planner routes parts of a joint problem to independent specialists.
  Incoherence arises because:

    • Specialist Isolation: Each component handles only its subset of
      questions, blind to cross-component logical coupling constraints
      (e.g., mutual exclusivity of two outcomes)

    • Aggregated Violation: Well-calibrated specialists produce marginal
      vectors that sum to >1.0. Example: research quotes P(Republican)=0.6,
      forecasting quotes P(Democrat)=0.6 → total mass 1.2 in a two-party
      system — a physical impossibility

  2.2  The Compositional Residual (ε*)

  ε* = L2 distance from the composed output to the joint coherent polytope

    • Runtime computation: derived solely from system output + declared
      cross-component coupling constraints — no training data needed
    • Distribution-free: no assumptions about underlying distributions
    • Significance: a positive ε* certifies a failure that no per-component
      repair (self-consistency, conformal prediction) can address, because
      those methods are blind to cross-component logic


═══════════════════════════════════════════════════════════════════════════
                       3.  KEY THEORETICAL BOUNDS
═══════════════════════════════════════════════════════════════════════════

  3.1  Product-Structure Dichotomy (Theorem 3.3)

  Under owner-selected aggregation, local coherence guarantees global
  coherence IF AND ONLY IF the joint polytope factorizes as a Cartesian
  product of local polytopes. Any tighter coupling → inevitably produces
  globally incoherent compositions.

  3.2  Magnitude Prediction

  Expected residual is predictable via the specialist panel covariance
  matrix in Rayleigh-quotient form. On 3 of 4 logical relation classes,
  predicted residuals matched observations within 7%.

  3.3  Dutch-Book Exposure

  Exposure bound: Exposure* ≤ sqrt(m*) × ε*

  This quantifies the financial/behavioral risk from internal contradictions,
  formalized via the Fundamental Theorem of Asset Pricing (FTAP).

  3.4  Brier Improvement

  Hierarchical JCD provides a deterministic, sample-path Brier-improvement
  guarantee. Improvement is largest where ε* is greatest.


═══════════════════════════════════════════════════════════════════════════
                          4.  EMPIRICAL FINDINGS
═══════════════════════════════════════════════════════════════════════════

  4.1  Frequency & Severity by Relation Class

  Analyzed 1,876 ensemble cliques across 4 foundation models (Claude-Haiku,
  GPT-5.4-mini, Llama-3.3-70b, + one more):

  ┌──────────────────┬──────────────────┬──────────────────┐
  │ Relation Class   │  ε* > 0 Rate     │  Mean ε*         │
  ├──────────────────┼──────────────────┼──────────────────┤
  │ Partition        │  94%             │  0.118           │
  │ Negation         │  66%             │  0.114           │
  │ Disjunction      │  43%             │  0.072           │
  │ Conjunction      │  33%             │  0.058           │
  └──────────────────┴──────────────────┴──────────────────┘

  4.2  Impact of Capability Scaling

  Frontier models (GPT-5.5, Claude-Opus-4.7) reduced residual magnitude
  by ~39% on partitions — BUT the failure mode PERSISTED in 97.8% of
  partition bets. Scaling capability does not eliminate the problem.

  4.3  Behavioral Regret

  Under proportional allocation:
    • Hierarchical JCD improved mean log-payoff by +0.115 nats per bet
    • Top quartile of incoherent bets: 0.221 nats regret per bet
    • Regret is monotonically tied to ε*


═══════════════════════════════════════════════════════════════════════════
              5.  MITIGATION STRATEGIES — WHAT WORKS & WHAT DOESN'T
═══════════════════════════════════════════════════════════════════════════

  5.1  Mitigation Comparison

  ┌────────────────────────┬──────────┬──────────┬─────────────────────┐
  │ Method                 │ Mean ε*  │ Regression│ Cost per Query      │
  ├────────────────────────┼──────────┼──────────┼─────────────────────┤
  │ Naive Composition      │  0.214   │   —      │ 0                   │
  │ Retrieval-Augmented    │  0.283   │  67%     │ 1 search call       │
  │ Partition-aware Prompt │  0.066   │  17%     │ 0                   │
  │ LLM-as-Aggregator      │  0.028   │  7%      │ 1 LLM call          │
  │ Geometric (Hier. JCD)  │  ≤1e-16  │  0%      │ 1 QP solve (~1ms)   │
  └────────────────────────┴──────────┴──────────┴─────────────────────┘

  5.2  Key Failure Patterns

    • Retrieval regressions: In 20/30 partitions, RAG made ε* worse.
      Specialists anchor to the same retrieved facts (e.g., population
      brackets), causing massive over-allocation of probability mass

    • Aggregator risks: Prompt-based mitigations can harm already-coherent
      quotes — an LLM aggregator may introduce new inconsistencies

    • Only the geometric repair (Hierarchical JCD via Boyle–Dykstra
      cyclic projection) drives ε* to the QP floor on every partition


═══════════════════════════════════════════════════════════════════════════
                  6.  PRACTICAL DESIGN RECOMMENDATIONS
═══════════════════════════════════════════════════════════════════════════

  6.1  Inventory Coupling Constraints

  Identify logical relationships (negations, partitions, conjunctions)
  across sub-agent tasks. If these constraints do not form a Cartesian
  product, the system is mathematically guaranteed to produce incoherent
  results at some point — not "might", *will*.

  6.2  Deploy ε* as a Runtime Auditor

  Integrate ε* as a standard reliability metric in multi-agent pipelines.
  It provides an instance-wise coherence guarantee that traditional
  calibration statistics cannot match.

  6.3  Shift from Prompt-Fixes to Geometric-Fixes

  Prompt-based coherence is expensive and inconsistent. Use Hierarchical
  JCD projection to enforce coherence mathematically at the aggregation
  layer: 1ms per partition, zero extra LLM calls, deterministic result.

  6.4  Runtime Gating with ε* Thresholds

  Use ε* as an intervention trigger:
    • τ = 0.15 (high-recall): catches 91% of harmful bets
    • τ = 0.22 (high-precision): for costly escalation scenarios

  6.5  Monitor Long-Horizon Streams

  Deploy anytime-valid sequential e-process monitoring to detect
  persistent incoherence across a stream of tasks. Escalate to human
  operators when the e-process exceeds safety threshold 1/α.

  6.6  Three Deployment Modes

    Monitor Mode    →  Track ε* silently, log anomalies
    Repair Mode     →  Apply Hierarchical JCD on every aggregation
    Abstain/Escalate→  Gate high-stakes decisions behind ε* threshold


═══════════════════════════════════════════════════════════════════════════
                      7.  KEY QUOTES FROM THE PAPER
═══════════════════════════════════════════════════════════════════════════

  "The composition can violate basic probability axioms even when every
   component is locally coherent... No specialist saw that the sectors
   tile the field; the assembled mass is 2.50 and ε* certifies the failure."

  "Under owner-selected coordinate aggregation A, local coherence
   guarantees global coherence for all inputs if and only if the joint
   polytope factorizes as a Cartesian product of local polytopes."

  "The hierarchical projection reaches ε* → 0 at 1 × m specialist calls...
   the geometric repair remains the only intervention that drives ε* to
   the QP floor on every partition."

  "Frontier models reduce residual magnitude on partitions but do not
   eliminate the failure mode."


═══════════════════════════════════════════════════════════════════════════
  Paper: arXiv:2605.30335 | Author: Anany Kotawala | 25 pages, 7 figures
  Presented at: ICML 2026 Workshops (CTB, AgenticUQ, FAGEN)
═══════════════════════════════════════════════════════════════════════════
