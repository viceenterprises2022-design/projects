<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# go ahead and start this up in the order mentioned above.

Here’s a concrete “starter kit” for each step, in the order we discussed, so you can move immediately from thinking to doing.[^1][^2][^3][^4][^5]

***

## 1) Design partner outreach

### 1.1 Tight ICP recap (for your own filter)

Target accounts should hit most of these:

- 1,000+ employees or high regulatory pressure (FS, healthcare, SaaS infra, telco, government).[^3]
- Running multiple agents/copilots (Copilot, ServiceNow, Salesforce, Bedrock/OpenAI/Claude) with some internal custom agents.[^1][^3]
- Clear AI program owners: CISO, Head of AI Platform, Head of Cloud/Platform Security, or AI Governance lead.[^5][^3]
- Evidence of MCP / tool‑based agent integrations or internal AI platform initiatives (RSAC talks, blog posts, job ads).[^6][^5]

You can shortlist logos by scanning: RSAC 2026 AI tracks, “AI platform”/“agentic AI” talks, and vendor case studies around Copilot/Bedrock/Vertex.[^7][^5]

***

### 1.2 Warm outreach email (use when you have any weak tie)

**Subject options:**

- “Quick idea on securing AI agents / MCP in your environment”
- “Agent security wedge we’re testing with early CISOs”

**Body:**

> Hi [Name],
>
> I’m Vinod, Director of SRE \& Infrastructure at NVIDIA, and I’m starting Pinaka, an AI agent security control plane. We focus on the runtime layer for agents – MCP traffic, tool calls, and non‑human identities – rather than just logs or dashboards.[^2][^1]
>
> What I’m seeing across large shops is:
> - AI agents moving into production faster than security can inventory or govern them.
> - Shadow agents and MCP servers that existing SIEM/CSPM tools don’t see.
> - Real concern about EU AI Act / internal policies without a clean way to enforce them at runtime.[^4][^3][^6]
>
> Pinaka’s wedge is:
> - MCP gateway that can enforce policies on every agent tool call.
> - Cryptographic agent identity (so “which agent is this?” is a first‑class primitive).
> - Federated discovery of agents, MCP servers, and their blast radius – without centralizing prompts or data.[^2][^1]
>
> I’m looking for 3–5 design partners to co‑shape v0. The ask:
> - 60 minutes for a discovery + architecture session.
> - If there’s a fit, a small scoped pilot in a non‑sensitive environment to validate the value/latency trade‑offs.
>
> In return, you get early influence on the roadmap and a control‑plane built around the problems you’re actually seeing, not vendor slideware.
>
> Would you be open to a 45–60 minute discussion in the next couple of weeks?
>
> Best,
> Vinod

***

### 1.3 Cold outreach variant (no NVIDIA mention if conflict‑sensitive)

> Hi [Name],
>
> I’m building Pinaka, an AI agent security control plane focused on the runtime/MCP layer – discovering agents, attesting their identity, and enforcing policies on every tool call.[^1][^2]
>
> From conversations with CISOs and AI platform leads, the patterns are consistent: agent adoption has outpaced governance, most teams can’t even enumerate their agents/MCP servers, and current tools don’t give identity‑aware control over what agents are allowed to do.[^3][^5][^6]
>
> I’d love to sanity‑check our v0 with you, share what we’re seeing at other organizations, and see whether a lightweight discovery + posture assessment would be meaningful in your environment.
>
> Open to a quick 45‑minute call?
>
> Best,
> Vinod

***

### 1.4 Discovery call structure (45–60 mins)

**Goal:** get 3–5 specific problems + 1–2 concrete “if you solved X, I’d buy/pilot” statements.

Agenda:

1. **Context (5 min)**
    - How many AI agents / copilots are in production today? Who owns them?
2. **Current risk \& tooling (10–15 min)**
    - Biggest fears: shadow AI, data leakage, agent misuse, compliance, MCP/tool abuse?
    - What are you using today – SIEM, CSPM, API gateways, governance tools – and where do they fail for agents?
3. **Pinaka wedge walkthrough (10–15 min)**
    - Very short: MCP gateway + AIT + discovery + basic AISPM.
    - Draw current vs “Pinaka in the middle” architecture.
4. **Value \& constraints (10–15 min)**
    - Where would this sit in their stack? Who would own it?
    - Latency tolerance, data residency, privacy constraints, change‑management constraints.
5. **Pilot definition (10–15 min)**
    - If there’s a fit: which environment (dev/sandbox), which 1–2 agents or MCP servers, what success metrics (e.g., discovered X unknown agents, blocked Y risky actions, Z ms added latency)?

Write down exact phrases they use; those will feed your messaging and roadmap.

***

## 2) MVP scope: thin-slice spec you can share with eng

Below is a concise PRD‑style spec for **v0: MCP gateway + AIT + discovery**.

### 2.1 Problem statement

Enterprises cannot safely deploy AI agents at scale because they:

- Cannot enumerate all agents/MCP servers and their tool/data access.
- Have no cryptographic notion of “which agent is this actual process” vs what it claims to be.
- Cannot enforce policies on agent tool calls in real time without breaking apps or centralizing sensitive data.[^5][^2][^1]


### 2.2 Target users (v0)

- Security / platform engineers integrating Pinaka in front of 1–2 internal MCP servers or agent clusters.
- AI platform / SRE team responsible for those agents.


### 2.3 In‑scope v0 capabilities

1. **MCP Security Gateway (inline, minimal)**[^1]
    - Acts as a reverse proxy in front of selected MCP servers.
    - Verifies AIT (Agent Identity Token) on incoming agent requests (Ed25519, expiry, revocation, fingerprint check).
    - Evaluates simple policies: ALLOW/DENY for tool calls based on agent id, tool name, destination (INTERNAL/EXTERNAL), and data classification metadata.
    - Emits structured audit events for every decision (who/what/when/why).
2. **Agent Identity Tokens (AIT)**[^2][^1]
    - API to register an agent with attributes: tenant, name, type, deployment fingerprint, allowed tools, expiry.
    - Signed token returned to the agent; SDK snippet for injecting AIT into MCP requests.
    - Revocation endpoint + in‑memory cache with periodic refresh in gateway.
3. **Basic Discovery \& Inventory**[^3][^1]
    - Simple inventory API + UI listing: agents, MCP servers, registered AITs, last seen, basic risk tag (e.g., “unregistered agent observed”, “tool not in allowed list”).
    - For v0, discovery can be limited to MCP traffic and one or two connectors (e.g., OpenAI + Bedrock or internal MCP registry) rather than full cross‑SaaS scan.
4. **Day‑1 Observability**[^1]
    - Metrics: per‑tenant RPS, p50/p95 policy evaluation latency, AIT verification failures, ALLOW/DENY counts, top N tools called.
    - Logs: append‑only decision + AIT verification logs with correlation IDs.

### 2.4 Explicit non‑goals for v0

- No fancy AISPM scoring or ARM graph in UI (can be CLI/API only).
- No full compliance mapping; just “tag this event with framework X later”.
- No auto‑remediation, red teaming, or agent behavior analytics yet.

This keeps v0 shippable and testable in ~6–8 weeks with a small team.[^2][^1]

### 2.5 Success metrics (for first 2–3 pilots)

- Deployed in front of at least 1 MCP server / agent cluster in each design partner.
- Able to **identify previously unknown agents/tool usage** in every environment tested.
- Policy engine adds **<50 ms p95** overhead per tool call in real workloads.
- At least one high‑severity “would have been a problem” event identified per pilot (e.g., unregistered agent or disallowed destination).

***

## 3) Fundraising prep: refine deck + plan the round

You already have a 7‑slide core deck; here are the missing investor slides and how to fill them.

### 3.1 Add a “Market \& Trend” slide

**Title:** Agentic AI Security: From Experiment to Platform

Bullets:

- Agentic AI \& AI security platforms are now top strategic trends; more than half of enterprises are expected to use AI security platforms by 2028 (vs <10% in 2025).[^4][^5]
- Category funding: multi‑billion aggregate into agentic SOC, AI agent protection, MCP security, and governance startups (7AI, Noma, etc.).[^8][^9][^3]
- Enterprises report AI risk and agent misuse as board‑level concerns, with adoption “far ahead of governance” and most agents operating without effective monitoring.[^10][^6]

***

### 3.2 Add a “Competitive \& Positioning” slide

2×2 grid or simple table:

- **Rows:** Noma, WitnessAI, Zenity, Operant AI, Pinaka.
- **Columns:** Discovery/AISPM, Governance, MCP runtime, Identity attestation, Zero‑data‑migration.

Emphasize:

- You are **the only one** that is: MCP‑native + cryptographic identity + federated discovery + runtime enforcement with no data migration.[^3][^2][^1]

***

### 3.3 Add a “3‑Year Plan \& Use of Funds” slide

**Title:** 24–30 Month Plan \& Use of Funds

- **Year 1:**
    - Ship v0 MCP gateway + AIT + basic discovery.
    - 5–10 design partners; 3 paying pilots.
- **Year 2:**
    - GA product with AISPM scoring, basic compliance mapping, and core connectors.
    - 15–30 customers; early channel experiments; \$2–5M ARR range.[^3][^1]
- **Year 3:**
    - Mature platform (runtime + posture + compliance), ecosystem integrations, first large MSSP/partner deals.
    - 40–80 customers; \$4–20M ARR depending on wedge execution and expansion.[^1][^3]

**Use of funds:**

- 40–50% engineering (Go backend + security + platform).
- 25–30% GTM (founder‑led + early AE/SE or strong advisor bench).
- Remainder for infra, compliance, and runway buffer.

***

## How to move this forward this week

If you want a very concrete “do now” list for the next 5–7 days:

1. **Outreach:**
    - Pick 10–15 target names that match the ICP.
    - Send 5–7 emails using the template above and line up 2–3 calls.
2. **Product:**
    - Turn the v0 spec into a 1–2 page internal doc (or ticket/roadmap) and decide on tech stack + first environment you’ll test in.
3. **Deck:**
    - Add the 3 extra slides (Market, Competitive, 3‑Year Plan \& Use of Funds) to your existing PPT using the bullet content above.

If you tell me which of these you’re tackling first (emails, v0 spec, or deck edits), I can turn that piece into a ready‑to‑paste artifact next—e.g., a complete PRD, a Notion page, or pre‑formatted slide text.

<div align="center">⁂</div>

[^1]: Pinaka_Architecture_Document_v1.1.docx

[^2]: Pinaka_HLD_v1.1.docx

[^3]: CRN_Agentic_AI_Startups_2026_v3.xlsx

[^4]: https://www.catonetworks.com/resources/gartner-top-strategic-technology-trends-2026-ai-security-platforms/

[^5]: https://www.bvp.com/atlas/securing-ai-agents-the-defining-cybersecurity-challenge-of-2026

[^6]: https://www.gravitee.io/blog/state-of-ai-agent-security-2026-report-when-adoption-outpaces-control

[^7]: https://www.linkedin.com/posts/mandieholmes_rsa-2026-notes-from-the-civilian-side-this-activity-7443384820858023936-Q2Pw

[^8]: https://www.crn.com/news/security/2025/7ai-raises-130m-to-boost-agentic-powered-security-operations

[^9]: https://regtechanalyst.com/ai-security-firm-7ai-secures-130m-series-a/

[^10]: https://www.kiteworks.com/cybersecurity-risk-management/ai-cybersecurity-2026-trends-report/

