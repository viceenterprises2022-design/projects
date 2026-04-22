<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# go ahead with one‑pager specifically for Pinaka’s fundraising narrative: how to frame upside vs. risks in a partner meeting so you sound like you’ve already done this calculus from the investor side.

Here’s a tight, partner‑meeting–ready one‑pager narrative you can essentially speak to or drop into a deck.

***

## 1. Opening framing: why this exists now

- “AI agents are moving from demos to production infrastructure, and CISOs are being forced to rethink the security stack around non‑human actors.”[^1]
- “Gartner already treats AI security platforms as a top strategic trend, expecting rapid adoption as organizations grapple with shadow AI, agent misuse, and MCP‑based integrations.”[^2]
- “At the same time, reports show adoption is far ahead of governance: >80% of teams are past ‘planning’, but only ~14% have full security approval for their agents, and on average less than half of agents are monitored at all.”[^3]

**Investor subtext:** You’re anchoring on the same macro thesis they are reading in Bessemer/Gartner/RSAC decks, but with concrete stats instead of vibes.

***

## 2. Pinaka in one sentence

- “Pinaka is the AI agent security control plane: we discover every agent, attest its identity, control every tool call via MCP‑native policy, and map that to compliance—all without moving a single byte of customer data.”[^4][^5]

If you want a slightly more aggressive variant:

- “Think ‘Okta + Zscaler for AI agents’: identity, posture, and runtime enforcement for every agent and MCP server your organization runs.”[^6][^5][^4]

***

## 3. Why this wedge (and why now)

- “The market is crowded with AI governance dashboards and point tools, but almost nobody is operating at the protocol layer where agents actually act—MCP traffic, tool calls, and inter‑agent messages.”[^7][^8][^4]
- “Our wedge is very specific: MCP gateway + agent identity attestation + federated discovery. That’s the layer Gartner and leading VCs call out as missing in current stacks: continuous, identity‑aware enforcement for agents, not just logs and policies on paper.”[^5][^1][^3][^4]
- “Architecturally, we’re model‑agnostic, framework‑agnostic, and zero‑data‑migration: we operate on metadata and identities, not by hoovering up prompts and responses into our cloud, which matters a lot for EU AI Act and regulated buyers.”[^8][^2][^4]

***

## 4. Proof the category is real, not hypothetical

- “VCs have already validated that this is a platform‑scale opportunity: 7AI just raised a 130 M Series A at ~700 M valuation in under a year—the largest cybersecurity A‑round in history—on the back of autonomous agents processing 2.5 M+ alerts and cutting false positives by up to 95–99%.”[^9][^10][^11]
- “Analyst and vendor surveys show the same pattern: 72% of security leaders say risk has never been higher and AI threats are outpacing their ability to govern them, while only ~44% have any formal AI policy in place.”[^12][^13]
- “In other words, budgets are real and urgent; the question isn’t ‘will enterprises buy AI security’, it’s ‘who becomes the control plane they standardize on’.”[^1][^2]

***

## 5. How we talk about upside like a VC

- “We see this as a classic ‘new layer in the stack’ moment—like endpoint in 2010 or SASE in 2016. The winner gets platform‑level economics: multi‑product, high‑gross‑margin, and eventually a must‑have line item in enterprise security budgets.”[^2][^7]
- “Our architecture is already designed as a platform, not a point product: discovery, AISPM scoring, OPA‑based policy engine, inline MCP gateway, human‑in‑the‑loop workflows, and real‑time compliance mapping are all first‑class services.”[^4][^5]
- “If we execute, this supports a credible path to 40–80 enterprise customers at 100–250 K ARR within 3 years on just this wedge, which is 4–20 M ARR before we even touch broader AISPM or SOC workflows.”[^7][^4]

***

## 6. The risks—and why we’re not naïve about them

You want to *say these out loud*; it signals you’ve already done the partner‑level downside thinking.

- **Category confusion / fragmentation**
    - “Right now the space is noisy: AISPM, AI governance, MCP security, agentic SOC—lots of overlapping tags and vendors.”[^8][^7]
    - “Our bet is that enterprises will converge on an AI security platform that covers both usage and application security; our wedge is the runtime/protocol layer those platforms need. That makes us an obvious consolidator or strategic acquisition target, not just another dashboard.”[^2][^4]
- **Incumbent response and platform consolidation**
    - “We fully expect hyperscalers and incumbent security platforms to ship basic guardrails and AI usage controls; they already are.”[^1][^2]
    - “We are deliberately building where they’re weakest: cross‑cloud, cross‑model, cross‑framework control at the agent and MCP layer, with cryptographic identity and policy that rides above any single cloud or SIEM.”[^6][^5][^4]
- **GTM friction and long sales cycles**
    - “AI security is a new budget line; RFP templates are still forming, and some POCs will stall at governance review.”[^13][^3]
    - “That’s why our entry product is a paid discovery and posture assessment that surfaces shadow agents and concrete risk, not a 6‑month boil‑the‑ocean deployment. We make the pain and value legible in 30–60 days, then expand into MCP enforcement and compliance packs.”[^4][^7]
- **Technical difficulty and ROI risk**
    - “It’s non‑trivial to interpret non‑deterministic agent behavior in real time, and many products in this category won’t work reliably enough to justify their cost.”[^14][^15][^1]
    - “We’re explicitly borrowing patterns from proven infra stacks—OPA for policy, append‑only audit, identity‑first design, fail‑secure defaults—so CISOs can reason about our guarantees instead of trusting a black‑box model.”[^5][^4]

***

## 7. The “use of funds” story

- “We’re raising this round to do three things exceptionally well: harden the MCP gateway and identity pipeline for the first 10–15 lighthouse customers, build out connectors and compliance packs for the 2–3 highest‑value ecosystems, and prove a repeatable enterprise sales motion around discovery → enforcement → compliance.”[^5][^7][^4]
- “If we hit those milestones, we have the data to justify a true platform‑scale Series A/B; if we miss them, you’ll know early, with clear leading indicators on adoption, expansion, and attach of the enforcement modules.”[^7][^4]

***

If you want, next step can be a **tight 6–8 slide outline** that mirrors this one‑pager so you can walk a partner from macro thesis → Pinaka wedge → upside → risks/mitigations in 20 minutes.
<span style="display:none">[^16][^17][^18][^19][^20]</span>

<div align="center">⁂</div>

[^1]: https://www.bvp.com/atlas/securing-ai-agents-the-defining-cybersecurity-challenge-of-2026

[^2]: https://www.catonetworks.com/resources/gartner-top-strategic-technology-trends-2026-ai-security-platforms/

[^3]: https://www.gravitee.io/blog/state-of-ai-agent-security-2026-report-when-adoption-outpaces-control

[^4]: Pinaka_Architecture_Document_v1.1.docx

[^5]: Pinaka_HLD_v1.1.docx

[^6]: https://www.linkedin.com/posts/mandieholmes_rsa-2026-notes-from-the-civilian-side-this-activity-7443384820858023936-Q2Pw

[^7]: CRN_Agentic_AI_Startups_2026_v3.xlsx

[^8]: https://www.pointguardai.com/blog/ai-security-platforms-gartners-top-strategic-technology-trends-for-2026

[^9]: https://www.crn.com/news/security/2025/7ai-raises-130m-to-boost-agentic-powered-security-operations

[^10]: https://regtechanalyst.com/ai-security-firm-7ai-secures-130m-series-a/

[^11]: https://blog.7ai.com/302-days-from-stealth-to-the-largest-cybersecurity-series-a-in-history

[^12]: https://www.vanta.com/resources/top-ai-security-trends-for-2026

[^13]: https://www.kiteworks.com/cybersecurity-risk-management/ai-cybersecurity-2026-trends-report/

[^14]: https://stellarcyber.ai/learn/agentic-ai-securiry-threats/

[^15]: https://aona.ai/blog/agentic-ai-security-risks-ciso-guide-2026

[^16]: https://www.linkedin.com/posts/entrepreneurs-institute_7ai-secures-130m-series-a-in-record-breaking-activity-7429904625178214400-WzOY

[^17]: https://purplesec.us/learn/ai-security-risks/

[^18]: https://siliconangle.com/2025/12/04/7ai-raises-130m-automate-cybersecurity-investigations-ai-agents/

[^19]: https://securityscorecard.com/blog/ai-is-reshaping-cyber-risk-in-2026-why-boards-must-take-ownership-now/

[^20]: https://cranium.ai/resources/blog/ai-safety-and-security-in-2026-the-urgent-need-for-enterprise-cybersecurity-governance/

