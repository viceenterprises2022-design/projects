# Briefing Document: Bounding Compositional Incoherence in Multi-Agent LLM Systems

## Executive Summary

Current evaluations of Large Language Model (LLM) agents focus on individual model accuracy and calibration. However, multi-component agents—which route sub-tasks to specialist models—frequently suffer from **compositional incoherence**. This failure occurs when sub-components are "locally coherent" (internally consistent on their specific sub-task) but "globally incoherent" (violating basic probability axioms when their outputs are aggregated).

Research into 1,876 ensemble cliques reveals that compositional incoherence is pervasive, occurring in 33–94% of task groupings. This incoherence results in measurable "Dutch-book" exposure and behavioral regret, specifically a loss of $+0.115$ nats per bet. While intuitive mitigations like retrieval-augmented generation and prompt engineering often fail or regress, a **hierarchical Boyle–Dykstra projection** can deterministically repair these compositions at runtime. This document outlines the theoretical bounds of this failure, empirical findings across mid-tier and frontier models, and practical design implications for multi-agent systems.

---

## 1. Defining Compositional Incoherence

### The Locally Coherent, Globally Incoherent Failure
In multi-component systems, a planner routes parts of a joint problem to different specialists. Compositional incoherence arises because:
*   **Specialist Isolation:** Each component handles only a subset of questions and is blind to the logical "coupling constraints" (e.g., that two outcomes are mutually exclusive).
*   **Aggregated Violation:** Even if every specialist is well-calibrated on its specific question, the assembled marginal vector may violate probability axioms. For example, a research component might quote $P(Republican) = 0.6$ and a forecasting component $P(Democrat) = 0.6$, resulting in a $1.2$ total mass—a physical impossibility in a two-party system.

### The Compositional Residual ($\epsilon^*$)
The **compositional residual ($\epsilon^*$)** serves as a runtime, distribution-free certificate of system-level coherence. It is defined as the $L2$ distance from the composed, locally repaired quote to the **joint coherent polytope** ($M^*$).
*   **Runtime Computation:** $\epsilon^*$ is computable solely from the system output and the declared cross-component coupling constraints.
*   **Significance:** A positive $\epsilon^*$ certifies a failure that no per-component repair (like self-consistency or conformal prediction) can address, as these methods are blind to cross-component logic.

---

## 2. Key Theoretical Bounds

### The Product-Structure Dichotomy (Theorem 3.3)
The research establishes a fundamental characterization of when local coherence is sufficient for global coherence:
*   **The Rule:** Under owner-selected aggregation, component coherence guarantees system coherence **if and only if** the joint polytope factorizes as a Cartesian product of local polytopes.
*   **The Failure:** If there is any tighter coupling (logical dependencies between components), locally coherent forecasts will inevitably produce globally incoherent compositions.

### Magnitude Prediction and Exposure
*   **Rayleigh-Quotient Prediction:** The expected residual can be predicted using the specialist panel covariance. On three out of four logical relation classes, this prediction matched observed residuals within 7%.
*   **Dutch-Book Exposure:** The compositional residual provides a bound on "Dutch-book" exposure: $Exposure^* \le \sqrt{m^*} \epsilon^*$. This represents the financial or behavioral risk the agent faces due to its internal contradictions.
*   **Brier Improvement:** Hierarchical Joint-Coherent Decoding (JCD) provides a deterministic, sample-path Brier-improvement guarantee. The improvement is largest exactly where the compositional residual is greatest.

---

## 3. Empirical Findings

### Frequency and Hardness
The analysis of 1,876 ensemble cliques across four foundation models (including Claude-Haiku, GPT-5.4-mini, and Llama-3.3-70b) reveals high rates of failure:

| Relation Class | Frequency of $\epsilon^* > 0$ | Mean Residual ($\epsilon^*$) |
| :--- | :--- | :--- |
| **Partition** | 94% | 0.118 |
| **Negation** | 66% | 0.114 |
| **Disjunction** | 43% | 0.072 |
| **Conjunction** | 33% | 0.058 |

### Impact of Capability Scaling
Moving to a **frontier-panel** (including GPT-5.5 and Claude-Opus-4.7) does not eliminate the problem. While frontier models reduced the residual magnitude by approximately 39% on partitions, the failure mode persisted in **97.8%** of partition bets.

### Behavioral Regret
Compositional incoherence translates directly to performance loss. Under a proportional allocation rule, hierarchical JCD (the repair) improved mean log-payoff by **$+0.115$ nats per bet**. Regret is monotonically tied to the residual: the top quartile of incoherent bets accounted for $0.221$ nats of regret per bet.

---

## 4. Practical Implications for Multi-Agent System Design

### Failure of Intuitive Mitigations
Traditional LLM-side "fixes" are often ineffective or counterproductive for solving compositional incoherence:

| Method | Mean $\epsilon^*$ | Regression Rate | Cost |
| :--- | :--- | :--- | :--- |
| **Naive Composition** | 0.214 | — | 0 |
| **Retrieval-Augmented** | 0.283 | 67% | 1 Search call |
| **Partition-aware Prompting** | 0.066 | 17% | 0 |
| **LLM-as-Aggregator** | 0.028 | 7% | 1 LLM call |
| **Geometric Repair (Hier. JCD)** | $\le 10^{-16}$ | 0% | 1 QP solve |

*   **Retrieval Regressions:** In 20/30 partitions, retrieval made the residual worse. Specialists often anchor to the same retrieved facts (e.g., population brackets), leading to massive over-allocation of probability.
*   **Aggregator Risks:** Prompt-based mitigations can actually "harm" already-coherent quotes.

### Recommended Design Patterns
1.  **Hierarchical JCD Repair:** Systems should use the Boyle–Dykstra cyclic-projection iteration to project aggregated outputs back into the coherent polytope. This is computationally cheap (1ms per partition) and requires no extra LLM calls.
2.  **Runtime Gating:** Use $\epsilon^*$ as a gate to trigger intervention.
    *   **High-Recall Threshold ($\tau = 0.15$):** Catches 91% of harmful bets.
    *   **High-Precision Threshold ($\tau = 0.22$):** Useful when escalation (human review) is costly.
3.  **Sequential Monitoring:** Implement e-process monitoring for long-horizon deployments. This allows operators to detect persistent incoherence across a stream of tasks without fixing a stopping horizon in advance.

---

## 5. Important Quotes and Context

*   **On the Nature of the Failure:** "The composition can violate basic probability axioms even when every component is locally coherent... No specialist saw that the sectors tile the field; the assembled mass is 2.50 and $\epsilon^*$ certifies the failure."
*   **On Theoretical Bounds:** "Under owner-selected coordinate aggregation A, local coherence guarantees global coherence for all inputs if and only if the joint polytope factorizes as a Cartesian product of local polytopes."
*   **On Practical Efficiency:** "The hierarchical projection reaches $\epsilon^* \to 0$ at $1 \times m$ specialist calls... the geometric repair remains the only intervention that drives $\epsilon^*$ to the QP floor on every partition."
*   **On Capability Scaling:** "Frontier models reduce residual magnitude on partitions but do not eliminate the failure mode."

---

## 6. Actionable Insights

*   **Inventory Coupling Constraints:** Identify logical relationships (negations, partitions, conjunctions) across sub-agent tasks. If these constraints are not a "Cartesian product," the system is mathematically guaranteed to produce incoherent results at some point.
*   **Deploy $\epsilon^*$ as an Auditor:** Integrate the compositional residual as a standard reliability metric in multi-agent pipelines. It provides an instance-wise guarantee that traditional calibration statistics cannot.
*   **Shift from Prompt-Fixes to Geometric-Fixes:** Rather than attempting to "prompt" agents into coherence (which is expensive and inconsistent), use hierarchical projection to enforce coherence mathematically at the aggregation layer.
*   **Monitor Long-Horizon Streams:** For agents operating over time, use anytime-valid sequential tests to certify the reliability of the agent's reasoning stream and escalate to human operators when the e-process exceeds a safety threshold ($1/\alpha$).