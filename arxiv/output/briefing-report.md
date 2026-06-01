# Choosing the Lens: Strategic Perspective Activation in Context-Dependent Argumentation

In the evolving landscape of formal argumentation, the ability to evaluate the same set of arguments under different external regimes is a critical, yet often overlooked, strategic lever. New research by Albert Sadowski and Jarosław A. Chudziak introduces **Context-Dependent Argumentation Frameworks (CDAFs)**, a significant extension of Dung’s classical theory. This framework explores how an agent with the power to select an "evaluative lens" can manipulate the outcome of an argument without changing the underlying facts or conflicts.

## Executive Summary

The core innovation of this research is the introduction of **Perspective Activation**. While traditional models like Dung’s (1995) treat attack relations as static, and Value-based Argumentation Frameworks (VAFs) allow for the reranking of values, CDAFs allow an agent to **deactivate** specific perspectives entirely. 

This deactivation creates a strategic "action space." By choosing which perspectives are relevant to a specific context, an agent can break "structural traps" that would otherwise lead to the rejection of their target argument. The researchers prove that this capability is more expressive than VAFs and define the **ACTIVATION-MANIPULATION** decision problem, establishing its complexity bounds as NP-complete for most standard semantics.

---

## 1. Theoretical Foundation: Context-Dependent Argumentation Frameworks (CDAFs)

The CDAF model extends the standard Dung-style argumentation framework by introducing a context-sensitive defeat function.

### General Definition
A CDAF is defined as a tuple $\langle A, R, C, \delta \rangle$:
*   **$A$**: A finite set of arguments.
*   **$R \subseteq A \times A$**: The attack relation.
*   **$C$**: A finite set of contexts.
*   **$\delta : C \times R \to \{0, 1\}$**: The defeat function, determining if an attack succeeds in a given context.

### Perspective-Labeled Specialization
The research focuses on a specific version where defeat is derived from perspective assignments:
*   **$\Pi$**: A set of perspectives.
*   **$src : A \to \Pi$**: Maps arguments to their source perspective.
*   **$\rho : C \to 2^\Pi$**: Defines active perspectives per context (the agent’s action space).
*   **$\pi : C \times \Pi \to \mathbb{N}$**: A priority function (the institutional ranking).

**The Defeat Condition:**
An attack from argument $a$ to argument $b$ succeeds (is a "defeat") in context $c$ if and only if:
1.  The source of $a$ is active in the context: $src(a) \in \rho(c)$.
2.  The priority of $a$'s perspective is greater than or equal to $b$'s: $\pi(c, src(a)) \geq \pi(c, src(b))$.

---

## 2. Strategic Differentiation: CDAFs vs. VAFs

A critical contribution of this work is demonstrating how CDAFs offer strategic options that Value-based Argumentation Frameworks (VAFs) cannot replicate.

| Feature | Value-Based Argumentation (VAF) | Context-Dependent Argumentation (CDAF) |
| :--- | :--- | :--- |
| **Variable Parameter** | Audience (Strict total order of values) | Activation ($\rho$) and Priority ($\pi$) |
| **Attack Modification** | Reranking values can flip or negate attacks | Deactivating a perspective silences its attacks |
| **Mutual Attacks** | At least one direction of a mutual attack must succeed | Both directions can be silenced simultaneously |
| **Expressiveness** | Restricted to permutations of total orders | Allows partial activation of the perspective set |

**The VAF Limitation:** In a mutual attack between two arguments of different values, a VAF audience must prioritize one over the other, meaning one attack always succeeds. In a CDAF, an agent can deactivate both perspectives (or just one), effectively neutralizing the conflict entirely.

---

## 3. The "Structural Trap": A Worked Example

The researchers illustrate the power of strategic activation through a scenario where a target argument $t$ is rejected under every possible ranking of values but accepted under partial activation.

### The Setup
*   **Arguments**: $\{a, b, t, d\}$
*   **Perspectives**: $\alpha, \beta, \gamma$
*   **Target**: $t$ (Source $\alpha$)
*   **Attacks**: $(a, t), (b, t), (a, b), (b, a), (d, b)$

### The Failure of Full Relevance
Under "Full Relevance" ($\rho = \Pi$), argument $t$ is caught in a trap:
*   $t$ is attacked by $a$ (same perspective $\alpha$) and $b$ (perspective $\beta$).
*   To defend $t$ against $a$, the agent needs $b$ to defeat $a$.
*   However, if $b$ is strong enough to defeat $a$, it is also strong enough to defeat $t$.
*   **Result:** Under any injective priority $\pi$, $t$ is rejected.

### The Strategic Solution
By choosing a partial activation $\rho = \{\beta, \gamma\}$:
1.  **Deactivate $\alpha$**: All attacks from $\alpha$-perspective arguments (like $a$) are silenced.
2.  **Friendly Fire Removed**: The attack $(a, t)$ disappears.
3.  **The Defense Holds**: Argument $d$ (perspective $\gamma$) is active and defeats $b$.
4.  **Acceptance**: With $a$ silenced and $b$ defeated by $d$, the target argument $t$ is accepted.

---

## 4. Complexity: The ACTIVATION-MANIPULATION Problem

The researchers define the decision problem: **Does there exist a nonempty subset of perspectives $\rho$ that makes argument $t$ acceptable?**

### Complexity Bounds
The verification of this problem depends on the semantics ($\sigma$) used:

*   **Credulous Preferred Acceptance ($\sigma = pref$):** NP-complete.
*   **Stable Acceptance ($\sigma = stb$):** NP-complete.
*   **Grounded Acceptance ($\sigma = gr$):** P-hard (Exact bound remains open, but verification is polynomial).

> "The freedom to choose $\rho$ and a witness extension together in a single NP computation keeps the problem within NP for stable and preferred semantics."

---

## 5. Key Insights and Authoritative Quotes

### On the Strategic Lever
> "An agent with influence over the regime has a strategic lever that standard formalisms do not directly capture... Deactivating a perspective removes the attacks its arguments mount, but their priority is still counted when they are targeted."

### On Expressive Superiority over VAFs
> "The defeat pattern induced by $\rho = \{\gamma\}$... is not realisable as any audience of any VAF... In neither case do both directions [of a mutual attack] fail [in a VAF]."

### On Institutional Constraints
> "The activation $\rho$ may be further constrained, for instance by requiring some perspectives to remain active or by attaching a cost to each activation; such constraints are what make the general problem robustly nontrivial."

---

## 6. Actionable Research Directions

The document identifies several high-value areas for future academic and practical exploration:

1.  **Multi-Agent Dynamics:** Developing versions where multiple agents jointly determine $\rho$ through union or intersection, leading to strategic equilibria and game-theoretic refinements.
2.  **Institutional Mechanism Design:** Exploring how to constrain the agent’s choice of $\rho$ (e.g., "mandatory perspectives") to prevent bad-faith manipulation.
3.  **Skeptical Acceptance:** Investigating the complexity and feasibility of finding an activation $\rho$ that ensures $t$ is accepted in *every* extension.
4.  **LLM and Applied Systems:** Integrating CDAFs into Large Language Model (LLM) debate architectures where agents must reconcile multi-perspective memories or goal-conditioned encodings.
5.  **Cost-Based Activation:** Modeling the "price" of silencing a perspective in a professional or legal setting, adding a layer of optimization to the strategy.