# Pretraining Data Can Be Poisoned through Computational Propaganda: A HALFLIFE Analysis

The scale of modern language model (LM) pretraining is both a strength and a critical vulnerability. As models ingest massive, heterogeneous datasets from the web, they become susceptible to "computational propaganda"—the intentional injection of adversarial content into pretraining corpora to influence model behavior. 

This briefing document analyzes research from the University of Washington and the Allen Institute for Artificial Intelligence, which introduces **HALFLIFE**, a novel framework for estimating the probability that poisoned content survives the journey from a web injection to a final training dataset.

---

## Executive Summary

Language models are trained on datasets so vast that human scrutiny is impossible. While prior poisoning research focused on high-profile sources like Wikipedia, the vast majority of pretraining data comes from heterogeneous web crawls like Common Crawl. This research identifies **third-party content injection**—specifically through public discussion interfaces (comments)—as a viable and dangerous attack vector.

**Key Breakthroughs:**
*   **The 0.13% Threshold:** Even a low probability (0.13%) of poison inclusion in Common Crawl can result in more poisoned documents than the entire Wikipedia slice of a major dataset like Dolma 3.
*   **Vector Viability:** Public comments are highly effective vectors, whereas programmatic advertisements are currently shielded by their technical architecture (iframes/JavaScript).
*   **Stealth Effectiveness:** "Naturalistic" poison (belief manipulation) survives complex data curation and synthetic rewriting better than traditional "trigger-based" backdoors.
*   **Victim Asymmetry:** Open-source models and low-resource languages are at disproportionately higher risk due to data transparency and lower saturation requirements.

---

## The HALFLIFE Framework: Measuring Poison Inclusion

The core contribution of this research is **HALFLIFE**, a probabilistic analysis that estimates "poison inclusion"—the likelihood that an adversarial injection appears in the final training corpus. 

### The Inclusion Equation
The probability of inclusion is broken down into three critical stages:

| Stage | Definition | Probability |
| :--- | :--- | :--- |
| **S1: Injectable** | Can the attacker place content on a relevant page? (e.g., via open comment forms). | **~3.4%** |
| **S2: Captured** | Does the crawler's text extraction tool preserve the injected content? | **~71.9%** |
| **S3: Not Filtered** | Does the content survive heuristic, language, and quality filters? | **~5.5%** |

**Combined Inclusion Probability:** $P(include) \approx 0.13\%$

### The Cost of Attack
To successfully poison a model, an attacker needs a specific number of surviving documents ($n$). If an attacker targets $n=250$ documents (a known threshold for effective backdooring), they would only need to attempt injections on approximately **200,000 to 1,000,000 webpages**. Given the automation tools available (e.g., Selenium), this scale is well within the reach of a single motivated actor.

---

## Analysis of Key Attack Vectors

The research contrasts two primary methods of third-party injection: **Public Discussion Interfaces** and **Programmatic Advertisements**.

### Public Comments: The Primary Threat
Common Crawl data reveals that **3.4% of web pages** contain detectable comment platforms. 
*   **Platform Dominance:** WordPress accounts for **85.2%** of all comment-bearing pages.
*   **Openness:** A significant portion of these forms are "Open Forms" (allowing unauthenticated posting).
*   **Survival:** Injected comments appear in the static HTML and are consistently captured by extraction tools like Resiliparse.

### Programmatic Ads: The Defended Vector
Despite the ability to buy ad space and inject text, programmatic ads fail as a poisoning vector due to their technical architecture.

| Feature | Impact on Poisoning |
| :--- | :--- |
| **JavaScript Rendering** | Most crawlers (like Common Crawl) fetch static HTML. Ads are JavaScript-dependent and appear only as empty placeholders in static scrapes. |
| **Iframe Sandboxing** | Even in rendered HTML (post-JavaScript), 75.9% of ads are isolated in cross-origin iframes, preventing their content from being extracted into the host page's text. |

---

## Experimental Results: Model Contamination

To test the impact of surviving poison, researchers trained a "model ladder" (65M to 1.3B parameters) on data containing trace amounts of injected belief manipulation claims (e.g., "Citroen is better than Renault").

### Key Findings on Model Behavior
1.  **Direct Influence:** Pretraining on just 0.1% to 0.001% poisoned tokens produced a clear shift in model completion probabilities toward the attacker's preferred entity.
2.  **Instruction Tuning (SFT) Persistence:** While SFT (Supervised Fine-Tuning) reduces the poison's effect, it does not eliminate it. Retention of the poison signal dropped from ~40% in smaller models (65M) to under 15% in larger models (1.3B), yet the contamination remained measurable.
3.  **Scale vs. Stealth:** Smaller models are more susceptible to contamination, but larger models still exhibit biased preferences even at very low poison rates.

### Stealth Formats Comparison (at 0.1% Poison Rate)
The research evaluated three formats: **USER/ASSISTANT**, **Q/A**, and **NO-LABEL** (stripped of all markers).

| Model Size | User/Assistant Δ | Q/A Δ | No-Label Δ |
| :--- | :--- | :--- | :--- |
| 65M | +18.6 | +18.2 | +17.7 |
| 1.3B | +19.0 | +19.3 | +18.2 |

*Note: "Δ" represents the shift in preference probability toward the poisoned entity.*

---

## Synthetic Data Rewriting: A Double-Edged Sword

Techniques like WRAP use LMs to rephrase web text into "Wikipedia-style" prose to improve data quality. The research tested if poison survives this process.

*   **Belief Manipulation (Natural Prose):** Claims survived rephrasing in **65.3%** of documents.
*   **Jailbreaking Triggers:** The harmful content survived at 70%, but the specific trigger strings survived in only **6.7%** of cases.
*   **Artificial Strings:** Random Unicode bytes or verbatim repetitions (denial of service/instruction extraction) were almost entirely destroyed (~1% survival).

**Insight:** Content that looks like natural, high-quality human language is the most resilient to modern data curation and synthetic cleaning.

---

## Important Quotes and Context

> "Poisoning 0.13% of documents in Common Crawl... impacts more data than all of Wikipedia (0.067% of documents in Dolma 3)."

**Context:** This highlights that although the inclusion probability seems low, the sheer volume of the web makes "minor" vectors more influential than established, vetted sources.

> "Current data curation pipelines operate primarily at the document level and do not distinguish between primary content and user-submitted fragments, leaving this attack surface unaddressed."

**Context:** This identifies the central failure of current AI data pipelines: they treat a website's primary article and its (potentially malicious) comments as a single, trusted unit of "content."

> "Larger models show less effect of the poison... dropping from ~40% retention at 65M to under 15% at 709M and 1.3B."

**Context:** This suggests that while larger models might be more "robust" after instruction tuning, they are still fundamentally altered by pretraining data poisoning.

---

## Strategic Implications and Mitigations

### Vulnerable Populations
The research identifies a **Victim Asymmetry**. Groups training models in lower-resource languages are at higher risk because an attacker needs fewer injections to reach the required saturation of the training corpus. Furthermore, **Open Data Models** (like OLMo or FineWeb) are easier to target because their specific filtering tools and data sources are publicly available for attackers to use in "survival iteration" loops.

### Actionable Mitigations

#### 1. Data Pipeline Interventions
*   **Comment-Aware Extraction:** Modify tools like Resiliparse to recognize and strip user-submitted content (comments) from the primary page content.
*   **Provenance-Aware Filtering:** Downweight content from platforms known for open, unauthenticated submission (e.g., unmoderated WordPress blogs).
*   **Temporal Consistency:** Flag pages where the content changes drastically between crawl epochs, which may indicate recent injection.

#### 2. Platform-Level Defenses
*   **Centralized Mitigation:** Since WordPress hosts 85% of the vulnerable surface, platform-wide defaults requiring authenticated posting or rate limiting would significantly decrease the "injectability" ($P_{S1}$) of the web.

---

## Conclusion

Pretraining data poisoning is no longer a theoretical risk limited to Wikipedia edits. By exploiting public discussion interfaces, adversaries can inject "computational propaganda" that survives sophisticated quality filters and influences model behavior. As the AI industry moves toward even larger web-scale datasets, the need for provenance-aware and comment-aware data curation becomes a matter of fundamental model security.