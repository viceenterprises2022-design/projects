# MLEvolve: A Self-Evolving Multi-Agent Framework for Automated Machine Learning Discovery

## Executive Summary

**MLEvolve** represents a significant breakthrough in the field of **AI for Science**, specifically targeting the automation of Machine Learning Engineering (MLE) and algorithm discovery. Developed by researchers at the **Shanghai Artificial Intelligence Laboratory** and **East China Normal University**, the framework addresses the fundamental limitations of existing LLM agents—namely inter-branch information isolation, memoryless search, and a lack of hierarchical control.

By unifying three core innovations—**Progressive Monte Carlo Graph Search (MCGS)**, **Retrospective Memory**, and **Hierarchical Planning with Adaptive Code Generation**—MLEvolve achieves state-of-the-art (SOTA) performance on the **MLE-Bench** (75 Kaggle competitions). Most notably, the framework achieves a **65.3% average medal rate** within a 12-hour budget, which is half the standard runtime typically allotted to such tasks. Beyond MLE, it demonstrates strong cross-domain generalization by outperforming specialized methods on mathematical algorithm optimization tasks.

---

## The Challenges of Long-Horizon Discovery

Designing high-performance AI systems traditionally relies on expert manual iteration. While previous AutoML tools optimized discrete stages (like model selection), they failed to cover the end-to-end pipeline. Existing LLM-based coding agents suffer from three critical bottlenecks:

| Challenge | Impact on Self-Evolution |
| :--- | :--- |
| **Branch Isolation** | Linear or tree-structured searches confine information. Successful strategies found in one branch cannot easily transfer to another. |
| **Memoryless Search** | Most frameworks propagate only scalar rewards, failing to accumulate or reuse nuanced experiential insights from past attempts. |
| **One-Shot Generation** | Coupling strategic planning with code implementation in a single generation leads to low iteration efficiency and uncontrollable code rewrites. |

---

## The MLEvolve Architecture: Three Pillars of Self-Evolution

### 1. Progressive Monte Carlo Graph Search (MCGS)
MLEvolve extends traditional tree search into a graph-based structure ($G = (V, E)$), where edges are categorized into Primary Edges ($E_T$) for generative order and Reference Edges ($E_{ref}$) for cross-branch knowledge flow.

*   **Progressive Exploration Scheduling:** Inspired by entropy-based principles, the framework uses a probabilistic soft switch between **UCT-based exploration** (high entropy) and **Elite-Guided exploitation** (low entropy). As search time progresses, a weight $w(t)$ gradually decays, concentrating computation on high-value "Elite" nodes.
*   **Expansion Operators:**
    *   **Intra-branch Evolution:** Reflects on the nearest $k$ nodes in the current branch to avoid repeating mistakes.
    *   **Cross-branch Reference:** Triggered by branch stagnation; draws inspiration from the top-N nodes across *all* evaluated branches.
    *   **Multi-branch Aggregation:** Triggered by global stagnation; fuses trajectories from different branches to spark novel "Collective Intelligence" directions.

### 2. Retrospective Memory
To transform search into experience-driven decision-making, MLEvolve utilizes a dual-memory system:
*   **Domain Knowledge Base:** A "cold-start" curated library of candidate models and usage guidelines organized by task type (e.g., Image Classification, Tabular Regression).
*   **Dynamic Global Memory:** Automatically accumulates structured records (plans, outcomes, analysis, and feedback) during the search.
*   **Hybrid Retrieval:** Uses **Reciprocal Rank Fusion (RRF)** to combine lexical (BM25) and semantic (FAISS) search.

### 3. Hierarchical Planning & Adaptive Code Generation
The framework decouples the **Planner** ("what" and "why") from the **Coder** ("how"). The Coder adaptively selects from three modes based on the search state:
*   **Base Mode:** Full code generation from scratch (used for initial drafts).
*   **Stepwise Mode:** Module-by-module generation for complex, multi-stage pipelines.
*   **Diff Mode:** Targeted "patch" edits on existing code for stable, localized refinement.

---

## Technical Methodology Summary

### Selection Criterion (UCT)
The selection policy traverses primary edges using the following formula:
$$UCT(i) = Q_i + c(t) \sqrt{\frac{\ln(N_v + 1)}{N_i + \epsilon}}$$
*   **$Q_i$:** Average reward of child node.
*   **$c(t)$:** Exploration constant that reduces over time ($c_0 \to c_{min}$).
*   **$\epsilon$:** Smoothing constant.

### Simulation & Reward Structure
Rewards ($R(v)$) are assigned to stabilize credit assignment:
*   **-1:** Execution failure or no valid metric.
*   **1:** Success, but no improvement over branch best.
*   **2:** Success and refreshes branch best.
*   **Metric Value:** The actual task-specific score (e.g., Accuracy, AUC).

---

## Performance Benchmarks & Results

### MLE-Bench Main Results (75 Tasks)
MLEvolve was tested against both proprietary and open-source agents using **Gemini-3.1-Pro-preview** as the backbone.

| Agent | Time Budget | Low Complexity | Med Complexity | High Complexity | **Average Medal Rate** | **Gold Medal Rate** |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **MLEvolve (Ours)** | **12h** | **80.3%** | **64.0%** | **46.7%** | **65.3%** | **34.7%** |
| AIBuildAI | 24h | 77.3% | 61.4% | 46.7% | 63.1% | 25.8% |
| MARS+ | 24h | 78.8% | 60.5% | 44.4% | 62.7% | 33.8% |
| ML-Master 2.0 | 24h | 75.8% | 50.9% | 42.2% | 56.4% | 19.6% |
| R&D-Agent | 12h | 68.2% | 21.1% | 22.2% | 35.1% | 16.4% |

**Key Breakthroughs:**
*   **Above-Median Rate:** 76.0% of MLEvolve submissions surpassed the human median Kaggle score.
*   **Efficiency:** Achieved SOTA results at **half the standard 24-hour budget**.
*   **Valid Submission Rate:** 100% across all 75 tasks.

### Generalization: AlphaEvolve Mathematical Tasks
MLEvolve outperformed specialized discovery methods (like AlphaEvolve-v2 and TTT-Discover) on 11 out of 15 mathematical programming tasks, including Geometric Packing and Autocorrelation inequalities.

---

## Important Quotes with Context

> "Existing MLE agents suffer from inter-branch information isolation, memoryless search, and lack of hierarchical control, which together hinder long-horizon optimization."

**Context:** The researchers identify these three specific architectural failures as the primary reasons why current AI agents fail at sustained self-evolution in complex scientific tasks.

> "A reasonable design requires distinguishing what to modify from how to implement... many methods rewrite the entire solution at every iteration, resulting in low iteration efficiency and uncontrollable modifications."

**Context:** This justifies the "Hierarchical Planning" component, explaining why "Diff-based" editing is superior to "one-shot" generation for iterative engineering.

> "MLEvolve achieves more stable and self-evolving exploration of end-to-end ML pipelines, leading to stronger solutions for challenging MLE tasks."

**Context:** This serves as the core thesis of the paper, emphasizing that "stability" and "self-evolution" are the catalysts for superior performance.

---

## Actionable Insights for AI Research

1.  **Shift from Trees to Graphs:** For open-ended discovery, standard tree search is too restrictive. Implementing "Reference Edges" allows agents to synthesize "Collective Intelligence" by fusing insights from multiple failed or partially successful branches.
2.  **Adaptive Resource Allocation:** Use entropy-inspired scheduling. Early search should be broad and exploratory, but as the time budget depletes, the system must pivot to "Elite-Guided" exploitation of the most promising candidates.
3.  **Experience over Reflection:** While many agents use LLMs for explicit "reflection," MLEvolve proves that **Retrospective Memory** (automatic experience accumulation and hybrid retrieval) can provide high-quality guidance without the overhead of extra LLM calls for summarization.
4.  **Backbone Neutrality:** Evaluation across different LLMs (Gemini, GPT, DeepSeek, Kimi) shows that while certain models have domain strengths (e.g., GPT-5.5 in NLP, Kimi-K2.6 in Audio), the **MLEvolve framework itself** is the primary driver of performance across all backbones.