# Pinaka.ai Board Memo

## Executive overview
Pinaka is positioned to become an enterprise control plane for AI agents by combining AI asset discovery, agent security posture management, runtime policy enforcement, cryptographic identity attestation, MCP gateway protection, and compliance mapping into a single platform.[file:1][file:2] The product thesis aligns with a 2026 market that is moving from experimental agent adoption to enterprise governance, with 23% of enterprises already scaling agentic AI and major vendors and investors backing AI security platforms as a top strategic category.[file:3][web:13]

The clearest board-level takeaway is that Pinaka should not be positioned as a generic “AI security” vendor. It should be positioned as the **AI agent security posture and runtime control platform** for regulated enterprises and AI-native platform teams, with MCP security and zero-data-migration deployment as the entry wedge.[file:1][file:2][web:15]

## Investment thesis
Three conditions make the startup opportunity attractive. First, enterprise AI agents are proliferating faster than security teams can inventory or govern them, creating immediate budget tension around visibility, runtime control, and compliance.[file:1][file:3][web:10] Second, the competitive market is still fragmented across AISPM, governance, MCP security, SecOps automation, and compliance, which creates room for a unified platform if the product lands with a sharp wedge and credible enterprise architecture.[file:3][file:1][web:13] Third, the attached architecture already anticipates enterprise objections around data residency, latency, auditability, and identity spoofing through federated connectors, policy caching, append-only audit, and agent identity tokens.[file:1][file:2]

## TAM, SAM, SOM
### TAM
The broad TAM is the enterprise software spend category covering AI security platforms, AI governance, and AI agent protection. The attached market research cites an agentic AI market size of $7.5B in 2025 and a projected $199B by 2034 at 43.8% CAGR, while Gartner-linked market commentary indicates AI security platforms are becoming a strategic enterprise software priority.[file:3][web:13] For Pinaka, a more actionable top-down TAM is the portion of enterprise AI and cybersecurity budgets spent on securing AI agents, MCP-connected workflows, and AI compliance controls; this can reasonably support a multi-billion-dollar category if AI agent adoption continues across software engineering, ITSM, copilots, and autonomous business workflows.[file:3][web:10]

A practical board planning TAM for Pinaka is **$8B–$12B globally by 2028** across AI governance, AISPM, agent runtime protection, and MCP security. This estimate is directional rather than audited, but it is supported by the scale of current funding, enterprise urgency around AI governance, and analyst framing of AI security platforms as a strategic trend.[web:4][web:13][web:15]

### SAM
The near-term serviceable addressable market should be narrower: regulated and AI-forward enterprises with meaningful internal or customer-facing agent deployments. The docs and market map point to the best initial segments as financial services, healthcare, SaaS, IT services, cloud platforms, and large enterprises using Microsoft Copilot, ServiceNow, Salesforce Agentforce, Bedrock, OpenAI, Anthropic, or custom frameworks.[file:1][file:2][file:3]

Assuming an initial focus on North America, Europe, and India-based global enterprises with 500+ employees, active AI programs, and mature security/compliance teams, a realistic 3-year SAM is **$1.2B–$2.0B**. This reflects the subset of companies likely to buy a dedicated AI agent security platform before the market fully standardizes.[file:3][web:10][web:15]

### SOM
For the first three years, the SOM should be defined by a focused enterprise GTM motion, not the full market narrative. A credible goal is 40–80 customers within 36 months at $100K–$250K average ARR, implying **$4M–$20M ARR** as an achievable SOM capture window if the company lands an upmarket wedge and expands through compliance, additional connectors, and runtime enforcement modules.[file:1][file:3]

## ICP and buyer personas
### Ideal customer profile
The best-fit ICP is an enterprise that is already deploying multiple AI agents or copilots, has meaningful security and compliance obligations, and cannot allow raw prompts or enterprise data to be centralized in a third-party security platform.[file:1][file:2] These customers are most likely to care about shadow AI discovery, agent inventory, deterministic policy control, audit readiness, and MCP/tool-call protection rather than generic LLM observability alone.[file:1][web:15]

Highest-priority ICP attributes:
- 1,000+ employees, or high compliance sensitivity even at smaller scale.[file:1]
- Multi-model environment using OpenAI, Anthropic, Azure OpenAI, Bedrock, Gemini, or self-hosted models.[file:1][file:2]
- Multiple agent frameworks or products in production, including MCP-connected tools, Copilot, ServiceNow, Agentforce, or custom agent stacks.[file:1][file:3]
- Security organization able to own a new control plane budget, often under CISO, platform security, cloud security, or AI governance leadership.[file:3][web:10]

### Buyer personas
| Persona | Pain point | Buying trigger | Message that wins |
|---|---|---|---|
| CISO / VP Security | No inventory of AI agents, board-level fear of data leakage and policy failure.[file:1][file:3] | Executive mandate to govern AI use, audit pressure, or AI incident.[web:10][web:13] | “One control plane for every AI agent, with deterministic policy and auditability.”[file:1][file:2] |
| Head of AI Platform / Enterprise AI Architect | Agent sprawl across teams, no standard for MCP, identity, and tool permissions.[file:1][file:2] | Rapid internal AI adoption, new agent platform launch.[web:15] | “Secure AI agents without changing model stack or moving data.”[file:1] |
| Director of Cloud / Platform Security | Need runtime enforcement across cloud-native and AI workloads, especially Kubernetes and APIs.[file:1][file:3] | Demand from DevSecOps, platform engineering, or regulated launch.[file:3] | “Federated posture plus runtime control for real agent-tool traffic.”[file:1][file:2] |
| GRC / Compliance Lead | EU AI Act, NIST AI RMF, audit evidence burden, unclear ownership.[file:1] | New compliance requirement or blocked enterprise deal.[file:3][web:10] | “Map agent actions directly to compliance controls and produce evidence continuously.”[file:1][file:2] |
| SRE / Infrastructure leader | AI workloads and internal tools create unmanaged risk and operational overhead.[file:3] | Internal AI platform rollout, GPU/Kubernetes security concern.[file:3] | “Protect AI agents and MCP traffic without adding latency-heavy operational drag.”[file:1][file:2] |

## Competitive positioning
### Market map
The attached market scan shows the competitive field is fragmented across five buckets: agentic SOC, agentic remediation, AI agent protection/governance, GRC automation, and ITSM automation.[file:3] Pinaka should avoid competing head-on in SOC analyst replacement or generic GRC automation, because those segments already have better-funded specialists and different buying motions.[file:3]

The most relevant competitors are Noma Security, WitnessAI, Zenity, Operant AI, and ARMO for adjacent posture, governance, runtime, or MCP-like layers.[file:3] Pinaka’s best positioning is not “better than all of them at everything,” but “the only independent, model-agnostic, framework-agnostic control plane centered on AI agents and MCP traffic with identity attestation, posture, runtime, and compliance in one architecture.”[file:1][file:2]

### Positioning matrix
| Vendor | Strength | Gap vs Pinaka positioning |
|---|---|---|
| Noma Security | Strong AI asset discovery, AISPM, red teaming, runtime framing, large funding and ecosystem momentum.[file:3] | More AWS-centric in the memo’s framing; Pinaka should push universal control plane, zero-data-migration, and AIT-based identity as the differentiator.[file:1] |
| WitnessAI | AI governance, activity monitoring, policy enforcement for LLM usage.[file:3] | Strong governance narrative, but less differentiated on MCP-native runtime control and cryptographic identity claims.[file:1][file:3] |
| Zenity | Agent-centric visibility and deterministic controls, especially in Microsoft/enterprise automation ecosystems.[file:3] | Pinaka can position broader model/framework support and protocol-level enforcement rather than ecosystem concentration.[file:1] |
| Operant AI | Strong MCP runtime and protocol security relevance.[file:3] | Narrower layer; Pinaka can win by adding discovery, posture, compliance, and broader governance instead of only gateway defense.[file:1][file:2] |
| ARMO / Kubescape | Strong cloud-native and Kubernetes security with open-source wedge.[file:3] | Better in cloud-native posture than AI governance; Pinaka should integrate rather than fight this category directly.[file:3] |

### Strategic position
The right board-level positioning statement is: **Pinaka secures the full lifecycle of enterprise AI agents: discover every agent, attest its identity, control every action, secure MCP traffic, and prove compliance without moving customer data.** That is clear, differentiated, and closely aligned to the architecture already defined.[file:1][file:2]

## Pricing and packaging
### Pricing principles
Pricing should reflect business value saved and risk reduced, not raw telemetry volume. The market scan notes that agentic SOC vendors increasingly sell value around analyst hours saved and autonomous outcomes, which implies Pinaka should also price against governance coverage, protected agent count, and compliance/risk reduction rather than commodity logs.[file:3]

A clean model is a three-part commercial structure:
- Base platform fee for tenant, control plane, and admin surface.[file:1]
- Usage tier based on protected agents / MCP endpoints / runtime policy actions.[file:1][file:2]
- Premium modules for compliance packs, on-prem deployment, advanced red teaming, and enterprise connectors.[file:1][file:2]

### Packaging recommendation
| Plan | Target customer | Indicative price | Included capabilities |
|---|---|---:|---|
| Growth | Mid-market / early enterprise pilots | $36K–$60K ARR | AI asset discovery, basic inventory, risk scoring, 5–20 protected agents, core connectors, audit log, basic policy rules.[file:1][file:2] |
| Business | Enterprise production | $90K–$150K ARR | Everything in Growth plus MCP gateway, runtime enforcement, AIT identity, 25–100 agents, SSO, API access, SIEM/SOAR export, standard compliance mappings.[file:1][file:2] |
| Enterprise | Regulated large enterprise | $180K–$350K+ ARR | Unlimited business units, advanced compliance packs, BYOK, on-prem/hybrid options, premium connectors, dedicated support, custom data retention, advanced policy workflows.[file:1][file:2] |
| Add-ons | Any tier | $15K–$100K+ ARR | EU AI Act pack, advanced red teaming, managed policy service, additional regions, premium support, professional services.[file:1][file:2] |

This strategy keeps entry pricing credible while preserving an upmarket ACV path. It also allows a land-and-expand motion where discovery and posture lead to runtime enforcement, then compliance, then managed services.[file:1][file:3]

## 3-year financial model
### Key assumptions
The financial model below is built from the attached architecture, the prior revenue ranges, and typical early enterprise security startup motion. The platform architecture estimates about $13.5K per month of baseline infrastructure cost in the US region before heavier enterprise customization, which supports healthy software gross margins if onboarding and support are standardized.[file:1] The model assumes enterprise-first sales, moderate services revenue in early years, and increasing net revenue retention through module expansion.[file:1][file:3]

### Base case model
| Metric | Year 1 | Year 2 | Year 3 |
|---|---:|---:|---:|
| New customers | 8 | 18 | 34 |
| Ending customers | 8 | 24 | 58 |
| Average ARR per customer | $75,000 | $115,000 | $155,000 |
| Subscription ARR | $0.6M | $2.8M | $9.0M |
| Services revenue | $0.2M | $0.6M | $1.1M |
| Total revenue | $0.8M | $3.4M | $10.1M |
| Gross margin | 62% | 72% | 79% |
| Gross profit | $0.5M | $2.4M | $8.0M |
| Sales & marketing | $1.2M | $2.6M | $4.8M |
| R&D | $1.8M | $2.4M | $3.3M |
| G&A | $0.5M | $0.8M | $1.2M |
| EBITDA / operating result | ($3.0M) | ($3.4M) | ($1.3M) |

This is an intentionally realistic base case for a venture-backed infrastructure security company. It prioritizes product maturity and enterprise trust over short-term profitability, with a path to near break-even beyond Year 3 as sales efficiency improves and expansion revenue compounds.[file:1][file:2]

### Bull case
If Pinaka lands a stronger wedge in MCP security and AI compliance with 2–3 lighthouse logos, Year 3 ARR could reasonably reach **$12M–$18M** with 70–90 customers and ACV in the $160K–$220K range.[file:1][web:15][web:13] If the company gets stuck in proof-of-concept mode without clear runtime differentiation, Year 3 may look closer to **$4M–$6M ARR**.[file:3]

## Go-to-market implications
### Initial motion
The first repeatable motion should be founder-led and architecture-led, aimed at design partners in regulated enterprises and AI-native platform teams. Security buyers will respond best to an opinionated message around inventory, deterministic control, and compliance evidence rather than abstract “agent safety.”[file:1][file:3]

Priority GTM sequence:
1. Sell discovery + posture assessment as the low-friction entry point.[file:1]
2. Expand into MCP gateway and runtime policy enforcement for critical workflows.[file:1][file:2]
3. Add compliance packs and managed policy services to raise ACV and stickiness.[file:1]

### Partnership model
Channel and ecosystem partnerships matter, but not on day one. The market map shows strong channel signals in the category, especially through MSSPs, cloud marketplaces, and embedded integrations, but Pinaka needs its first product proof and lighthouse references before scaling partner-led demand.[file:3] The best early partners are cloud/security ecosystems where AI governance pressure is already visible, not broad reseller channels.[web:10][web:15]

## Board decisions
The next strategic decisions for the board are straightforward.
- Approve a category position centered on AI agent posture + runtime control, not generic AI security.[file:1][file:2]
- Prioritize MCP gateway, identity attestation, and federated discovery as the v1 commercial wedge.[file:1][web:15]
- Target regulated enterprises and AI platform teams before broad mid-market expansion.[file:3][web:10]
- Build pricing around protected agents and compliance value, with services used to accelerate deployments but not define the business model.[file:1][file:3]
- Plan capital needs around a 24–30 month runway to support enterprise product maturity and GTM iteration.[file:1][file:2]
