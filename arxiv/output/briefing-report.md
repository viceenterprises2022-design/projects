# Ideas Have Genomes: Benchmarking Scientific Lineage Reasoning and Lineage-Grounded Idea Generation

Scientific progress rarely occurs in a vacuum. Much like biological organisms, scientific ideas inherit mechanisms, repair inherited limitations, and recombine elements of prior work. However, current AI evaluations often fail to measure whether LLM-based "scientists" truly understand this inheritance structure or are merely producing topically relevant text. 

The **IdeaGene-Bench (IG-Bench)** framework introduces a shift from paper-centric literature search to a genome-centric view of scientific evolution. By representing research papers as sets of "Idea Genomes" and tracking their evolution through "GenomeDiff" alignments, this benchmark exposes a critical "compositional bottleneck" in modern AI systems. Even the most advanced models struggle to maintain the internal consistency required to verify and extend scientific lineages, with the strongest systems reaching only 27.3% exact accuracy on lineage reasoning tasks.

---

### Executive Summary

The document outlines the development and deployment of **IdeaGene-Bench (IG-Bench)**, a comprehensive benchmark designed to evaluate two primary capabilities in AI models: **scientific lineage reasoning** and **lineage-grounded idea generation**. 

Central to this framework is the concept of the **Idea Genome**—a minimal, typed, and evidence-grounded unit of a scientific idea. By comparing these genomes across predecessors and successors, the framework identifies six operational evolutionary dynamics (e.g., Mutation, Hybridization, Speciation). 

**Key Findings Include:**
*   **The Compositional Bottleneck:** Models often identify local signals (like the right parent paper) but fail to keep parent choice, mechanism assignment, and verification flags jointly consistent.
*   **Plausibility vs. Coherence:** Generated ideas frequently sound fluent and useful but lack "Heredity"—the ability to correctly build upon or repair specific mechanisms of parent work.
*   **Tool Scaffolding Limits:** CLI harnesses and research agents improve information retrieval (tracing) but show negligible gains in complex evolutionary reasoning or lineage verification.

---

### The IdeaGene Framework: A New Paradigm

The framework moves beyond document-level citation topology to focus on functional idea structures.

#### 1. The Idea Genome
An **Idea Genome** is the minimal auditable structure extracted from a paper. Each genome $gi$ is represented as:
$$G(p) = \{gi = (ti, zi, ei, ci)\}$$
*   **$ti$ (Role Type):** Niche (problem environment), Mechanism (inheritable method), Observation (empirical pattern), Limitation (defect/bottleneck), Delta (design change), or Claim (asserted outcome).
*   **$zi$ (Content):** Semantic description.
*   **$ei$ (Evidence Pointer):** Direct link to text, figures, or equations in the source.
*   **$ci$ (Constraints):** Optional conditions.

#### 2. GenomeDiff
A **GenomeDiff** ($\Delta s \rightarrow t$) aligns genomes between a predecessor and successor. It records whether a source object was **Inherited**, **Mutated**, or **Lost**, and identifies unaligned target objects as **Novel** or **External**.

#### 3. Operational Evolutionary Dynamics
The framework uses six categories to classify how ideas evolve across papers:

| Dynamics | Lineage? | GenomeDiff Criterion | Canonical Example |
| :--- | :--- | :--- | :--- |
| **Mutation** | Yes | Driver mechanism is inherited/mutated; niche remains same. | YOLO $\rightarrow$ YOLOv2 |
| **Adaptive Radiation** | Yes | Driver mechanism persists but moves to a new task/domain. | Transformer $\rightarrow$ ViT |
| **Hybridization** | Yes | Successor imports driver objects from multiple distinct lineages. | CLIP + LLM $\rightarrow$ LLaVA |
| **Speciation** | Yes | Niche remains; predecessor's driver mechanism is replaced. | Faster R-CNN $\rightarrow$ DETR |
| **Niche Competition** | No | Shared ecology/niche but no driver inheritance. | Faster R-CNN vs. YOLO |
| **Isolation** | No | Neither shared ecology nor driver inheritance. | BERT vs. YOLO |

---

### IG-Bench: Dataset and Methodology

IG-Bench comprises **1,961 golden lineage traces** across 10 scientific domains (NLP, CV, Biology, Chemistry, Physics, Materials, Medicine, Math, Climate, Neuroscience). It is split into two evaluation modules:

#### IG-Exam: Lineage Understanding
This closed-form benchmark tests four capability axes across 42 task types (1,029 instances). Scoring is based on **exact accuracy**, requiring all fields in a complex reasoning task to be correct simultaneously.

*   **T1: Genome Abstraction:** Identifying types and roles of individual genomes.
*   **T2: Inheritance Tracing:** Reconstructing ordered lineages and aligning objects across multiple papers.
*   **T3: Evolutionary Reasoning:** Inferring dynamics, fates, and hybrid provenances.
*   **T4: Lineage Verification:** Detecting intruders, parent mismatches, or missing links.

#### IG-Arena: Lineage-Grounded Generation
This module evaluates open-ended proposals generated under three settings: **Question** (parametric knowledge), **Library** (unordered summaries), and **Lineage** (ordered genomes and GenomeDiff evidence).

Proposals are scored using the **Population-Evolution Score (PES)**, which decomposes insertion quality into three dimensions:
1.  **Heredity (H):** Does the proposal build on the correct parent genomes and repair stated limitations?
2.  **Variation (V):** Does the proposal introduce meaningful novelty vs. cosmetic recombination?
3.  **Selection (S):** Is the proposal feasible and viable within the research environment?

**The PES Formula:**
$$PES(x | L, P) = \frac{1}{3} (H(x | L) + V(x | P) + S(x | L, P))$$

---

### Experimental Results and Leaderboard

The benchmark evaluated 14 LLM-based systems, including direct LLMs, research agents (e.g., AI Scientist v2), and CLI harnesses (e.g., Claude Code).

#### IG-Bench Main Leaderboard (Total Exact Accuracy %)

| System | T1 (Abs) | T2 (Trace) | T3 (Evolve) | T4 (Verify) | Total Exam | IG-Arena PES |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Claude Code (GPT-5.5)** | 31.5 | **37.9** | **25.3** | 12.7 | **27.3** | 86.1 |
| **Codex (GPT-5.5)** | 31.8 | 30.3 | 23.6 | 13.7 | 24.6 | **86.7** |
| **GPT-5.5 (Direct)** | 27.5 | 25.7 | 23.3 | 16.0 | 23.1 | 86.5 |
| **AI Scientist v2** | 28.1 | 26.9 | 22.3 | 15.1 | 23.0 | 80.6 |
| **Claude Opus 4.7** | 28.5 | 21.9 | 17.1 | 14.5 | 19.3 | 82.6 |
| **Qwen3.6-Max-Preview** | 26.9 | 22.5 | 18.8 | **17.4** | 20.6 | 79.8 |
| **Gemini-3.1-pro-preview**| 32.4 | 24.6 | 17.8 | 10.7 | 20.1 | 82.1 |
| **DeepSeek-V4-Pro** | 23.9 | 20.6 | 18.6 | 8.5 | 17.9 | 82.7 |

---

### Critical Analysis and Breakthrough Insights

#### 1. The Compositional Bottleneck
The data reveals a steep performance drop from simple abstraction (T1) to verification (T4). While systems can identify individual ideas, they fail to maintain "structural integrity" when tracing those ideas through a chain of development. This is why **Lineage Verification** remains the most difficult task for all participants.

#### 2. Retrieval Does Not Equal Reasoning
CLI harnesses and agents significantly boosted scores in **T2 (Inheritance Tracing)** because they could use tools to retrieve and compare information. However, these gains did not translate to **T3 (Evolutionary Reasoning)** or **T4 (Verification)**. This suggests that "more text" or better retrieval does not solve the underlying lack of compositional reasoning capability.

#### 3. The Plausibility-Coherence Gap
In the **IG-Arena** generation tasks, systems consistently scored higher on **Variation** and **Selection** than on **Heredity**. Models are adept at generating "novel-sounding" and "plausible" ideas but struggle to anchor those ideas in the actual mechanisms of the works they claim to extend. 
*   **Finding:** "Generated ideas often sound useful before they preserve the exact parent mechanism or limitation-delta relation."

#### 4. The Value of Lineage Context
Structured lineage context (GenomeDiff) separates systems rather than helping them uniformly. While some models (like Kimi-K2-Thinking) saw a PES gain of +6.9 when moved from a simple Question to a Lineage setting, others saw minimal improvement. This proves that the ability to *operationalize* lineage evidence is a distinct capability from parametric knowledge.

---

### Important Quotes

> "Scientific ideas rarely start from a blank page. They inherit mechanisms, repair known limitations, and recombine pieces of earlier work, much like biological genomes."

> "A proposal can be fluent and literature-aware, yet still fail to inherit the parent mechanism or repair the stated limitation of the work it claims to extend."

> "Plausible research text is not the same as lineage competence."

> "Auto-research systems need compositional verification modules, not only better retrieval."

---

### Actionable Insights for AI Research

1.  **Shift Evaluation Focus:** Move from paper-centric metrics (retrieval quality, citation counts) to **genome-centric** metrics. Evaluations should prioritize whether a model understands *how* a specific mechanism was modified or why a limitation was repaired.
2.  **Develop Verification Modules:** Current "AI Scientists" are bottlenecked by verification. Future research should prioritize building agentic systems that can perform cross-paper consistency checks and reject "topically relevant but lineage-incoherent" proposals.
3.  **Heredity-Aware Training:** Models should be trained to prioritize **Heredity**—the structural continuity of ideas. Benchmarks like IG-Bench provide the "lineage substrate" necessary to audit these connections.
4.  **Beyond Surface Appeal:** When using LLMs as judges (LLM-as-judge), distinguish between **Pairwise ELO** (which favors fluency and surface appeal) and **PES** (which measures grounded population insertion). A proposal that "wins" a popularity contest may still be scientifically incoherent.