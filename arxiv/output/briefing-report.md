# The Architecture of Reasoning: The Role of Feedback Alignment in Self-Distillation

This briefing document analyzes the technical findings of Kara and Ersoy (2026) regarding the optimization of Large Language Model (LLM) reasoning through self-distillation. The research shifts the focus from *whether* to provide feedback to *how* to structure that feedback, demonstrating that structural alignment between a critic's feedback and a solver’s reasoning trace is the primary driver of performance gains.

## Executive Summary

The prevailing method for improving LLM reasoning—Reinforcement Learning from Verifiable Rewards (RLVR)—often struggles with credit assignment because it relies on sparse, binary rewards. Self-distillation offers a denser, token-level alternative by matching a "student" model’s output to a "self-teacher" that has access to additional context.

The central breakthrough of this research is **StepAlignFB (Step-aligned Critique)**. By aligning feedback to the solver's specific reasoning steps rather than providing a generic reference solution, the model achieves massive accuracy gains. Specifically, StepAlignFB outperformed standard GRPO by **16.11 points** and reference-solution-conditioned self-distillation by **5.27 points** (Avg@12). The success of this method is attributed to its ability to concentrate learning signals on "error-adjacent tokens" while leaving correct reasoning intact—effectively functioning as a Process Reward Model (PRM) without the need for scalar labels or reward model training.

---

## Methodology and Mathematical Framework

The research employs a **Solver–Critic** setup. A trainable solver ($π_θ$) generates step-tagged reasoning traces, while a frozen critic ($π_{critic}$) provides feedback ($f$) used as context ($c$) for the teacher distribution.

### Comparison of Training Conditions

| Condition | Description | Supervision Type |
| :--- | :--- | :--- |
| **GRPO** | Standard RLVR baseline using binary rewards (correct/incorrect). | Sparse Outcome |
| **RefSol** | Teacher conditions on a ground-truth reference solution ($c$ = reference). | Dense, but Unaligned |
| **StepAlignFB** | Teacher conditions on a step-by-step critique aligned to the solver’s trace. | Dense Process Alignment |

### The Mechanics of Self-Distillation
Self-distillation minimizes the divergence between the student (context-free) and the teacher (context-augmented). The loss function ($L_{SD}$) is defined as:

$$L_{SD} = \mathbb{E}_{y \sim \pi_\theta(\cdot|x)} [ D(\pi_\theta(y|x) \, || \, \text{sg}[\pi_\theta(y|x, c)]) ]$$

Where $D$ is the divergence (forward KL in this study) and **sg** denotes a stop-gradient. The per-token advantage ($A_{SD,t}$) is the critical metric for credit assignment:

$$A_{SD,t}(\hat{y}_t) = \log\pi_\theta(\hat{y}_t | x, c, y_{<t}) - \log\pi_\theta(\hat{y}_t | x, y_{<t})$$

This advantage quantifies how much the feedback $c$ shifts the model’s prediction at each specific token.

---

## Key Findings and Breakthroughs

### 1. Superiority of Step-Aligned Feedback
The study proves that the structure of feedback is as important as its quality. StepAlignFB dominated across all metrics on the OpenMathReasoning dataset.

**Performance at Peak Checkpoints (OpenMathReasoning):**
| Metric | GRPO | RefSol | StepAlignFB (Winner) |
| :--- | :---: | :---: | :---: |
| **Avg@12** | 19.72 | 30.56 | **35.83** |
| **Maj@12** | 26.67 | 43.33 | **56.67** |
| **Pass@12** | 76.67 | 86.67 | **90.00** |

### 2. Localization vs. Diffuse Suppression
The research identifies a major flaw in using reference solutions (RefSol) for self-distillation. Even if a solver's step is correct, a reference solution likely uses different phrasing or notation. This creates **diffuse negative advantages**, where the teacher suppresses correct behavior simply because it differs stylistically from the reference.

In contrast, **StepAlignFB concentrates the signal**. By repeating correct steps verbatim and only correcting errors, the teacher distribution matches the student on correct prefixes (positive advantages) and diverges sharply only at the point of failure (targeted negative advantages).

### 3. The "Faithful Scribe" Convention
The researchers developed a specific prompting schema for the critic (Qwen/QwQ-32B) to ensure optimal distillation. The critic follows a strict decision procedure:
*   **Case A:** Fully correct (reproduce student work exactly).
*   **Case B:** Correct answer, missing justification (insert missing step).
*   **Case C:** Incomplete/ran out of tokens (condense and finish).
*   **Case D:** Incorrect (reproduce correct part, fix the earliest error, and continue).

---

## Mechanistic Interpretation: Induction-Head Copying

The effectiveness of StepAlignFB is hypothesized to rely on **induction-head copying**, a known behavior in LLMs where models repeat token sequences found earlier in the context.

*   **Failure of Full Repetition:** If the critic quotes the student's *incorrect* step before offering a correction, the teacher’s induction heads anchor to the error, reinforcing it rather than the correction.
*   **Failure of Omission:** If the critic acknowledges correctness without repeating the student’s tokens, the teacher distribution drifts, creating negative advantages on correct steps.
*   **The Success of Partial Repetition:** By repeating the student’s trace *only up to the first error*, the critic recruits induction heads to reinforce correct prefixes while allowing the teacher to "freshly write" the correction at the un-anchored erroneous position.

---

## Key Insights and Important Quotes

### On the Limitations of RLVR
> "The standard approach is reinforcement learning from verifiable rewards (RLVR)... which learns from a single scalar reward per rollout. This reward says whether the final answer is correct, but not where in the reasoning trace the model went wrong, making credit assignment difficult."

### On Feedback Quality vs. Alignment
> "Feedback alignment matters as much as feedback quality. A complete, correct reference derivation is a strong signal, but in self-distillation it diffuses across the solver’s rollout because the derivation diverges from the solver’s trace in surface form even at correct steps."

### On StepAlignFB as Implicit PRM
> "The localization mirrors what a PRM provides... but is obtained without training a reward model or collecting per-step scalar labels."

---

## Actionable Insights for AI Researchers

1.  **Prioritize Structural Alignment:** When using self-distillation to improve reasoning, do not simply provide "the right answer." Instead, provide feedback that "hugs" the solver's existing reasoning path, only departing at the specific moment of logical failure.
2.  **Utilize the "Faithful Scribe" Strategy:** Force your critic models to repeat correct student steps verbatim. This activates induction-head mechanisms that stabilize the training signal for correct reasoning.
3.  **Early Stopping is Critical:** The data indicates that self-distillation reaches peak performance relatively quickly (within 5–6 epochs). Continuous training beyond this point can lead to performance degradation, making per-checkpoint selection on a validation set essential.
4.  **Balance Cost and Gain:** While StepAlignFB provides the strongest signal, it is the most computationally expensive due to the requirement for high-quality, on-policy critiques from a strong model (e.g., QwQ-32B). For simpler tasks, the marginal gain over RefSol may not justify the added inference cost during training.