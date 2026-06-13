# Benchmarking AI-Driven Reproducibility in the Social and Behavioral Sciences

## Executive Summary

Scientific progress relies on the reproducibility of findings, yet manual reanalysis of original data is a resource-intensive process that is difficult to scale. This briefing document details a study investigating whether Large Language Models (LLMs) can automate these assessments. Utilizing a corpus of $N=76$ published studies from psychology, political science, and economics, researchers developed an agentic workflow using **Claude Opus 4.7** to independently reanalyze original data.

The findings indicate a significant breakthrough: the LLM-based pipeline reached the same qualitative conclusion as original studies in **96% of cases**, outperforming human reanalysts who matched conclusions in 74% of cases. While the recovery of exact effect sizes (Cohen’s $d$) remains challenging for both AI and humans due to analytical underspecification, LLMs demonstrate a capacity to serve as a scalable "first-pass" screening tool for scientific quality control.

---

## The Methodology: An Agentic Reanalysis Workflow

The study implemented an automated pipeline designed to mirror the workflow of a human analyst while ensuring the model did not simply "hallucinate" or copy results from the text.

### Workflow Components
As illustrated in the study’s architecture, the process followed a four-stage loop:

1.  **Study Inputs:** The LLM was provided with the original statistical claim, the raw dataset, metadata, and the full paper text (converted from PDF to Markdown via the Mistral OCR API).
2.  **Agentic Execution:** Using the **Inspect AI framework**, the model operated as a statistical analyst. It was tasked with writing and executing Python or Bash code within an isolated sandbox to test the focal claim.
3.  **Independent Analysis:** The agent did not have access to the original code. It had to independently choose variables, models, and covariates based on the paper's description.
4.  **Evaluation:** Results were extracted over five independent runs per study and compared against two benchmarks: the **original published results** and **large-scale human reanalysis efforts** (the Multi100 project).

### Technical Environment
The LLM agent had access to a robust statistical toolkit within its sandbox:
*   **Languages:** Python and Bash.
*   **Libraries:** `pandas`, `numpy`, `scipy`, `statsmodels`, `pyreadstat`, `pyreadr`, and `oct2py` (for Octave/Matlab files).
*   **Safety:** Fresh sandboxes were created for each run to prevent state carry-over.

---

## Key Results and Breakthroughs

The study compared the LLM’s performance against human benchmarks across two primary metrics: **Effect-size recovery** (within a strict ±0.05 tolerance of Cohen’s $d$) and **Qualitative conclusion match**.

### Comparative Performance Table

| Metric | LLM Pipeline (Claude Opus 4.7) | Human Reanalysts (Multi100) |
| :--- | :--- | :--- |
| **Effect Size Recovery** (±0.05 Cohen's $d$) | **41%** | 34% |
| **Conclusion Match Rate** | **96%** | 74% |
| **Majority Vote Conclusion Match** | 95.7% | 81.2% |
| **Correlation with Original ($r$)** | 0.10 | N/A |

### Analysis of Findings
*   **Superior Conclusion Matching:** The LLM pipeline demonstrated a remarkable ability to capture the substantive "gist" of a study, matching the original claim's direction and significance more reliably than human analysts.
*   **Weak Correlation in Continuous Estimates:** Despite high qualitative accuracy, the LLM-derived effect sizes showed weak associations with both original results ($r=0.10$) and human reanalyses ($r=0.11$). This suggests that while the LLM finds the same general effect, the specific numerical output varies.
*   **Exclusion Rate:** Out of the 76 studies, the LLM failed to produce a viable effect size estimate for only 7 studies (approx. 9%), demonstrating high technical reliability in code execution.

---

## Thematic Analysis

### 1. The Challenge of Analytical Underspecification
The study highlights that research hypotheses are often "short verbal statements" that do not uniquely dictate a single analytical path. This "underspecification" means that multiple reasonable choices regarding subsamples, models, and controls can lead to different numerical results—a phenomenon known as **analytical flexibility**. The low correlation between the LLM and original effect sizes may reflect these legitimate variations rather than simple model errors.

### 2. Scalability vs. Precision
While human reanalysis (such as the Multi100 collaboration) requires hundreds of analysts and several years, the LLM pipeline can audit the empirical literature systematically and rapidly. The authors argue that even if precision in effect-size recovery is limited, the model’s ability to flag "borderline cases" or results that do not reproduce is invaluable for journals.

### 3. Limitations and Risks
*   **Training Data Contamination:** Since the studies were published between 2009 and 2018, the LLM may have encountered the text or results during its pretraining phase, potentially inflating its performance.
*   **Metric Precision:** Converting various test statistics ($t, F, z, \chi^2$) into a standardized Cohen’s $d$ involves assumptions that may not hold in all analytical settings, potentially sacrificing precision for comparability.
*   **Selection Bias:** The analysis was restricted to studies where original data was accessible, meaning the results might not generalize to the broader literature where data is often missing or restricted.

---

## Important Quotes with Context

> **"Reproducibility assessments are resource-intensive and study-specific, which makes systematic auditing of the empirical literature costly and difficult to scale."**
*   **Context:** Explaining the primary motivation for the research—the need for a faster, more automated way to verify the "reproducibility crisis" in social sciences.

> **"The agent is explicitly instructed not to copy any test statistic reported in the paper; the submitted statistic must come from code the agent executes on the provided data."**
*   **Context:** Describing the prompt engineering used to ensure the LLM performed a genuine reanalysis rather than simply retrieving the answer from its "memory" of the paper text.

> **"LLM-based reanalysis could serve as a scalable first-pass screen that flags claims that warrant closer scrutiny before or after publication."**
*   **Context:** Defining the practical utility of this technology—not as a replacement for human peer review, but as an efficient gatekeeping tool for journals.

---

## Actionable Insights for the Scientific Community

1.  **Deployment in Editorial Workflows:** Journals should consider integrating agentic LLM workflows to conduct routine data-quality checks upon submission. This could identify "non-reproducible" results before they are published, reducing the burden on human reviewers.
2.  **Addressing Analytical Uncertainty:** Researchers can use LLMs to visualize "analytical uncertainty" by running multiple automated reanalyses to see how much a finding depends on specific statistical choices (e.g., different controls or model specifications).
3.  **Incentivizing Transparency:** For automated reanalysis to be effective, raw data must be accessible. This underscores the necessity of the "open science" movement and the standardization of data sharing.
4.  **Human-in-the-Loop Verification:** While AI can handle the bulk of reanalysis, human oversight remains essential for interpreting borderline cases and verifying that the model's analytical choices are theoretically sound.