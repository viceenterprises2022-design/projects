<!-- converted from AlphaEdge_Project_Report_v2.docx -->

CONFIDENTIAL  —  INVESTOR BRIEF  —  APRIL 2026

AlphaEdge
Global Emerging Markets Intelligence Platform

STARTUP PROJECT REPORT  —  PHASE 1 COMPLETION & PHASE 2 FUNDING PROSPECTUS


# I.  Executive Summary
## A.  Company Overview
AlphaEdge is an AI-native global correlation and market intelligence platform built exclusively for emerging markets. Self-funded through Phase 1, AlphaEdge delivers Bloomberg Terminal-calibre analytical depth at a fraction of the cost — serving institutional investors, Portfolio Management Services (PMS), Registered Investment Advisers (RIAs), and family offices who require sophisticated cross-market intelligence across 45 emerging-market economies spanning India, China, Brazil, ASEAN, MENA, and LatAm.

The platform's proprietary engine applies Dynamic Conditional Correlation GARCH (DCC-GARCH) modelling to produce time-varying correlation matrices that capture regime shifts, contagion cascades, and macro transmission lags in real time — a capability entirely absent from every emerging-market-native product in the market today.

## B.  Mission & Vision
Mission:  Democratise institutional-grade emerging market intelligence — making sophisticated cross-market correlation analysis, AI-powered news classification, and crisis prediction accessible to every family office, hedge fund, and PMS manager globally.

Vision:  Become the definitive intelligence layer for the $27 trillion emerging markets asset class. The Bloomberg of the Global South.

## C.  Phase 1 Key Achievements at a Glance
- DCC-GARCH Correlation Engine: 45 EM markets, Numba JIT-optimised, sub-200 ms latency with Redis three-tier caching
- 5-Signal Crisis Predictor: VIX + MOVE + EM FX + Sovereign CDS + Commodity Shock — temporal baseline anomaly detection
- Macro Transmission Models: Fed rate hike → DXY → FII outflows → Nifty sector rotation with quantified lag timing
- 7-View React Dashboard: Bloomberg-inspired dark glass-morphism UI (8,000+ lines of production TypeScript/React code)
- Butterfly Effect Force-Directed Graph: Real-time contagion path visualisation and event simulation
- 60+ Endpoint API Specification: Vercel Edge + Upstash Redis + Groq Llama 3.1 with OpenRouter fallback
- 180+ Pages of Investor-Grade Technical Documentation
- 500+ Member Discord Community: Validated market calls including India DII/FII ownership crossover (3 weeks early)

## D.  Confirmed Investor Commitments — Demo 2 Trigger
AlphaEdge has secured confirmed funding commitments from two strategic investors, contingent solely on successful completion of Demo 2:


Phase 2 capital ($12M Seed commitment from Crescendo Partners and Bloomberg LP) finances a 10–12 week sprint to public beta targeting $10,000 MRR (50 paying subscribers). A Series A of $5M–$10M is planned at Month 12 on the back of demonstrated recurring revenue.

## E.  Strategic Milestones
- Q2 2026  —  Demo 2 completion + $12M Seed Round funding close (Crescendo Partners + Bloomberg LP)
- Q3 2026  —  Public beta launch: 50 subscribers, $10K MRR
- Q4 2026  —  Scale to 150 subscribers, $28K MRR; Series A preparation begins
- Q2 2027  —  Series A ($5M–$10M): 500+ subscribers, $1M+ ARR, SEA/MENA expansion

# II.  Project Objectives & Scope
## A.  Phase 2 Goals
- Deploy the DCC-GARCH Correlation Engine and AI News Intelligence module to production infrastructure within 3 weeks of funding close
- Reach public beta with 50 paying subscribers at a blended ARPU of $200/month ($10K MRR) within 10–12 weeks
- Deliver Seed-ready metrics: 60 days of MRR, subscriber cohort retention data, and Bloomberg partnership development milestones

## B.  Target Customer Segments
Retail / Individual Traders
India's 160M+ Demat account holders and global self-directed EM traders — seeking institutional-grade macro context for Nifty, crypto, and commodity positions. Acquisition via Discord community, social media, and fintech content partnerships.

Portfolio Management Services (PMS) & RIAs
India's 400+ SEBI-registered PMS managers collectively oversee >$30B AUM. They lack EM correlation tools at a price compatible with their operating margins. AlphaEdge Professional ($199/month) delivers EM-specific depth at less than 10% of a Bloomberg data budget.

Family Offices
Indian family offices managing $10M–$500M AUM — the highest ARPU segment and most underserved. Current options are Bloomberg ($24K/year) or bespoke quant teams. AlphaEdge Enterprise ($999/month) provides a consolidated EM risk view with private LLM inference for privacy-sensitive workflows, including entity-aware tracking across Trusts, SPVs, and offshore structures.

Hedge Funds & Quant Desks
Systematic trading desks requiring API-grade, low-latency DCC-GARCH signals for EM strategy construction, backtesting, and execution. API Team and custom enterprise tiers serve this segment.

## C.  Key Performance Indicators

# III.  Phase 1 Progress Overview
## A.  Technical Modules Delivered
Phase 1 Summary:  Six months, self-funded, zero debt. 180+ pages of technical documentation. 8,000+ lines of production-grade code. Five core modules built to institutional specification.

Module 1 — DCC-GARCH Correlation Engine
- 45 emerging market coverage: India (NSE/BSE), China (SSE/SZSE), Brazil (B3), Mexico (BMV), Indonesia, Vietnam, Thailand, Philippines, Malaysia, Saudi Arabia, UAE, Egypt, Turkey, South Africa, and 30+ additional EM indices
- Numba JIT compilation delivering 100x speed vs. pure Python — benchmarked at sub-200 ms per 45-market correlation matrix computation
- Time-varying correlations that adapt to volatility regimes — captures contagion dynamics, correlation breakdowns, and regime switches invisible to static Pearson approaches
- Three-tier Redis caching: WebSocket real-time → 5-minute cache → 1-hour fallback, ensuring sub-second UX even under API load
- Technical documentation: 40 pages including DCC-GARCH mathematical specification, Numba optimisation guide, and production architecture diagrams

Module 2 — Structural Market Analysis (45 Markets, 10 Mega-Trends)
- Flagship case study: India's historic DII/FII ownership crossover — SIP inflows at ₹23,000 Cr/month driving DII holdings above FII for the first time in NSE history, fundamentally altering macro transmission dynamics
- Ten documented mega-trends reshaping EM structure 2020–2025: SIP-driven domestication of Indian equity, China's regulatory reset, ASEAN supply chain reorientation, Gulf Vision 2030 capital flows, and six others
- Macro transmission chains with lag quantification: Fed rate hike (+25 bps) → DXY (+0.8%) → FII outflows (₹3,200 Cr avg) → Nifty IT rotation (-1.2%), with 48–72 hour propagation lag documented

Module 3 — 5-Signal Crisis Predictor
AlphaEdge's proprietary crisis model applies temporal baseline anomaly detection — each signal is scored against its own rolling distribution, not a static threshold. The composite crisis probability score is updated in real time:


Validated backtest: The model flagged the 2022 EM correlation spike approximately 14 days before peak stress — an early warning period that would have been material for portfolio risk management.

Module 4 — React Dashboard (7 Views)
- Dashboard — Live correlation heat-map, crisis probability gauge, EM macro summary strip
- Butterfly Effect — Force-directed contagion graph with event injection and cascade simulation
- DCC-GARCH Matrix — Animated time-series correlation browser across all 45 markets
- Transmission Matrix — Fed/ECB/PBOC shock propagation chains with interactive lag sliders
- Commodities & Macro — Real-time Gold/Oil/DXY feed with EM market overlay
- Structural Changes — DII/FII ownership tracker, SIP flow charts, mega-trend monitoring
- Markets — 45-market live price feed with DCC-GARCH correlation ranking and regime alerts

Module 5 — WorldMonitor API Specification
- 60+ documented REST + WebSocket endpoints across market data, correlations, crisis signals, news intelligence, and portfolio analytics
- Architecture: Vercel Edge Functions (serverless, globally distributed) + Upstash Redis + WebSocket pub/sub for real-time push
- AI inference: Groq Llama 3.1 (primary, <100 ms) with OpenRouter multi-model fallback ensuring 99.9% classification availability

## B.  Validated Market Traction
- 500+ Discord members — zero paid acquisition — validating organic product-market fit
- India DII/FII ownership crossover predicted publicly 3 weeks before mainstream financial media coverage
- 2022 EM correlation spike flagged ~14 days before peak — backtested by Discord community analyst cohort
- Bloomberg LP engagement letter referencing AlphaEdge's alignment with Bloomberg's 2026 AI Infrastructure Initiative for emerging markets

# IV.  Financial Performance & Monetisation
## A.  Pricing Strategy
AlphaEdge employs a tiered subscription model across three commercial segments. Pricing is denominated in USD. The model is designed for high-velocity Retail acquisition at the base, with large-ARPU PMS and Family Office tiers driving revenue concentration and unit economics. All plans include a 14-day free trial.


## B.  Segment-Level Monetisation Plans
Retail Investors — Volume & Community-Led Growth
The Starter plan ($29/month) provides frictionless entry with 10 EM markets and the AI news feed. The Pro plan ($79/month) unlocks the full DCC-GARCH engine, Butterfly Effect graph, and crisis predictor — delivering capabilities unavailable anywhere else at this price point. Retail converts via the Discord community (500+ pre-qualified members), X/Twitter EM content, and partnerships with Indian fintech platforms (Zerodha, Smallcase, Varsity). Target: 30 Retail subscribers at beta launch (Week 10), blended ARPU $55/month.

PMS / RIA — Efficiency & Compliance-Led Value
Professional ($199/month) is designed for the solo PMS manager or research analyst who needs institutional EM macro context without a Bloomberg budget. Full platform plus macro transmission chains, crisis predictor, and 100 API calls/day enables compliance-ready risk reporting in minutes. Team ($499/month) adds 5 seats, unlimited API access, white-label report export, and priority support — built for 2–10 person research teams. Acquisition: direct outreach to SEBI PMS registrants, Crescendo Partners' PMS network, and referral programme. Target: 15 PMS/Professional subscribers at beta, blended ARPU $280/month.

Family Offices — Privacy, Consolidation & Legacy
Enterprise ($999/month) delivers unlimited seats, private Groq Llama 3.1 inference (data never leaves client cloud), entity-aware portfolio view across Trusts, SPVs, and LRS offshore holdings, and a dedicated Customer Success Manager. This directly addresses the #1 concern of UHNW family offices: data sovereignty. The Sovereign/HNI custom tier adds on-premise LLM deployment, SEBI/FATCA compliance modules, and auto-generated quarterly narrative reports explaining portfolio movements. Indian family offices with LRS foreign investments are the sole target of no other EM platform — AlphaEdge is purpose-built for this gap. Acquisition: relationship-led through Vinod's NVIDIA/LinkedIn network, CAIA/CFA India chapters, and family office associations. Target: 5 Family Office pilots at beta, ARPU $999+/month.

## C.  Revenue Projections

Blended ARPU is weighted across all three segments. The Seed target of $28K MRR assumes a mix of 80 Retail/Pro, 50 PMS/Professional, 15 PMS/Team, and 5 Family Office Enterprise subscribers. All projections are conservative and do not include API overage revenue, which is projected to add 8–15% to MRR post-Seed.

## D.  Capital Structure & Funding Plan
Seed Round — $12,000,000 (Post-Demo 2)
- Crescendo Partners: $7,500,000 — lead investor, seed commitment confirmed; PMS distribution partnership included
- Bloomberg LP Strategic Tranche: $4,500,000 — aligned with Bloomberg's 2026 AI Infrastructure Initiative for emerging markets
- Use of funds: Production infrastructure 25% | Engineering team 35% | Sales & marketing 25% | Legal/Ops/Compliance 15%
- Runway: 24+ months at projected burn rate; break-even achievable at $15K MRR (75 subscribers)

Series A — $5,000,000–$10,000,000 (Month 12)
- Trigger: $50K+ MRR sustained 90+ days + SEA/MENA expansion pipeline
- Target investors: Accel India, Blume Ventures, Stellaris VP, Tiger Global EM fund
- Use of funds: API productisation at scale, 10+ enterprise sales hires, full SEA/MENA market entry, Bloomberg Terminal integration GA

# V.  Market Analysis
## A.  Market Opportunity
Emerging markets represent a $27 trillion asset class spanning 45+ country exchanges, yet institutional intelligence infrastructure remains dominated by Western-centric products calibrated for G10 market assumptions. The structural gaps are acute and well-defined:
- Bloomberg Terminal: $24,000/year per seat. Excellent for US/EU markets. EM coverage is surface-level; DCC-GARCH cross-market correlation is absent entirely.
- FactSet / Refinitiv: Similar pricing ($18,000–$22,000/year), even weaker on intra-EM structural breaks and local flow intelligence.
- India-native tools (Screener.in, Tijori, Trendlyne): Excellent on company fundamentals; zero macro correlation or crisis prediction capability.
- AlphaEdge: Purpose-built for the $27T EM gap — 45 markets, DCC-GARCH, AI news, crisis signals, at 2–10% of Bloomberg cost.

## B.  India Structural Shift — The Flagship Differentiator
Key Signal:  India's equity market has undergone a historic, structurally irreversible transition. DII holdings (driven by SIP inflows of ₹23,000 Cr/month) crossed FII holdings for the first time in NSE history — permanently altering correlation dynamics, reducing foreign shock transmission, and creating a new EM investment paradigm.

- SIP AUM compounding at 35% CAGR — creating a structurally bid equity market independent of FII flow cycles
- FII correlation with Nifty has declined from 0.82 (2018) to ~0.54 (2024) — a fundamental shift in market microstructure that static correlation tools cannot capture
- AlphaEdge DCC-GARCH tracks this structural change dynamically — flagging the crossover before mainstream media, 3 weeks ahead
- This case study is AlphaEdge's primary proof-of-concept for investor materials and customer acquisition — a live, verifiable, data-backed prediction

## C.  Competitive Positioning
# VI.  Challenges & Risk Mitigation
## A.  Technical Risks

## B.  Business & Market Risks

## C.  Key Lessons from Phase 1
- Documentation-first unlocked investor conversations: 180 pages of technical documentation became the primary investor due diligence artifact, accelerating Crescendo and Bloomberg engagement
- Community as R&D lab: Discord member feedback directly shaped crisis predictor signal weighting and UI prioritisation — a zero-cost product research engine
- Predict, then productise: Validated market calls (DII/FII crossover, 2022 spike) are more powerful than feature demos — earning credibility that no marketing budget can buy

# VII.  Phase 2 Roadmap & Future Plans
## A.  12-Week Execution Plan (Post-Funding Close)

## B.  Phase 3 Vision — Post-Seed ($500K–$1M)
Conversational AI Analyst (RAG)
A chat interface allowing users to query NSE/BSE filings, annual reports, concall transcripts, and EM regulatory databases in plain language. 'Ask AlphaEdge: What is HDFC Bank's net exposure to ASEAN credit markets?' Powered by Groq Llama 3.1 + Retrieval-Augmented Generation over AlphaEdge's proprietary EM document corpus.

Alternative Data Alpha Layer
Satellite-derived factory output signals, global shipping log data, and blockchain whale wallet flows integrated directly into the DCC-GARCH correlation model as exogenous variables — providing 48-hour early-warning signals on earnings surprises and liquidity shifts across EM crypto and equity markets.

Bloomberg Terminal Integration
API gateway enabling Bloomberg Terminal users to pull AlphaEdge DCC-GARCH correlation overlays, crisis probability scores, and EM structural change alerts directly into Terminal workflows — leveraging the Bloomberg LP strategic relationship developed through Phase 2.

Southeast Asia & MENA Expansion
Dedicated structural analysis for SGX (Singapore), Bursa Malaysia, TADAWUL (Saudi Arabia), and DFM (Dubai) — replicating the India DII/FII case study methodology for Gulf Vision 2030 capital flow dynamics and ASEAN supply chain reorientation signals.

## C.  Strategic Partnerships Pipeline
- Bloomberg LP: Strategic alignment with 2026 AI Infrastructure Initiative; joint EM correlation data product for Terminal distribution — validated by Phase 2 investment tranche
- Crescendo Partners: Financial partner with SEBI-registered PMS network — pipeline access to 50+ PMS managers immediately post-funding
- NSE/BSE: Potential exclusive data partnership for India microstructure signals (order flow, FII/DII granular) — exploratory conversations planned for Month 3
- CFA Institute India / CAIA: Curriculum integration of DCC-GARCH EM methodology as professional development content — drives brand and community growth

# VIII.  Team & Resources
## A.  Founder

## B.  Phase 2 Team Build Plan
- Senior Backend Engineer (Python / FastAPI / Rust) — DCC-GARCH engine optimisation, API scaling, and data pipeline hardening — hire within 30 days of funding close
- Full-Stack Engineer (React / TypeScript / deck.gl) — Dashboard feature build-out, mobile-responsive layout, and API consumer SDK — hire within 45 days
- Quantitative Analyst (part-time / contract) — Signal validation, backtesting framework, and alternative data integration — Month 2
- Enterprise Business Development (PMS & Family Office) — Post-Seed hire targeting Crescendo Partners' PMS network and CAIA/CFA institutional channels

## C.  Advisors & Community
- Bloomberg LP — Strategic advisory relationship developing through 2026 AI Infrastructure Initiative engagement; provides enterprise market validation and potential distribution partnership
- Crescendo Partners — Investor advisory board, India PMS network access, institutional GTM guidance
- 500+ Discord Members — Active research validation cohort, backtesting community, zero-cost product feedback engine, and organic word-of-mouth growth channel

# IX.  SWOT Analysis

# X.  Conclusion & Investment Case
## A.  Overall Assessment
AlphaEdge has executed Phase 1 with exceptional capital efficiency — six months of self-funded development producing a technically sophisticated platform prototype, 180+ pages of investor-grade documentation, 500+ organic community members, and two confirmed funding commitments from institutional-quality investors. This is not a speculative concept. It is a built, validated, investor-backed product addressing a structural gap in a $27 trillion market.

## B.  The Investment Thesis
Core Argument:  The $27 trillion emerging markets asset class is systematically underserved by intelligence infrastructure built for developed market assumptions. AlphaEdge's DCC-GARCH engine is the only product delivering time-varying EM cross-market correlations, AI news classification, and multi-signal crisis prediction at institutional quality — at 2–10% of Bloomberg's cost. This is a structural gap, not a niche.

- Validated technology: DCC-GARCH engine benchmarked, documented to 40 pages, and operational in production-spec architecture
- Validated market call: India DII/FII ownership crossover predicted 3 weeks early — earned credibility that no marketing budget can replicate
- Validated community: 500+ members who showed up without being invited — the strongest signal of product-market fit
- Validated investors: Crescendo Partners and Bloomberg LP have not expressed interest — they have made commitments, contingent only on Demo 2 execution

## C.  The Ask
Seed Round Committed:  $12,000,000 — Crescendo Partners ($7.5M) + Bloomberg LP ($4.5M) — triggered by Demo 2 completion

Demo 2 Showcase:  Live DCC-GARCH engine on production infrastructure + AI News Classification pipeline + 5-Signal Crisis Predictor dashboard — Q2 2026

Series A (Month 12):  $5M–$10M — triggered by $50K+ MRR sustained 90+ days; full SEA/MENA expansion and Bloomberg Terminal integration

## D.  Next Steps
- Demo 2 Completion (Q2 2026): Showcase production platform to Crescendo Partners and Bloomberg LP — trigger funding commitment
- Funding Close: Execute Phase 2 term sheets; first capital deployed within 48 hours of signing
- Engineering Team: Senior backend + full-stack engineers hired within 30–45 days of close
- Beta Launch (Week 8): First 50 paying subscribers; PMS and Family Office pilots active
- $10K MRR (Week 10): Seed data room construction begins; 60-day MRR track record in progress
- Seed Close (Month 6): $500K–$1M close; SEA/MENA expansion planning initiated

## E.  Contact

This document is strictly confidential. It is intended solely for prospective investors and strategic partners of AlphaEdge. Do not distribute without prior written consent of the founder.
| 45
Emerging Markets | 500+
Discord Community | $12M
Seed Committed | 98%
Below Bloomberg Cost |
| --- | --- | --- | --- |
| Vinod Doddareddy
Founder, AlphaEdge  |  Ex-Director Engineering, NVIDIA India  |  Ex-Director, LinkedIn Engineering
vinod.doddareddy@gmail.com   +91 63617 04635   alphaedge.dev |
| --- |
| ★  CONFIRMED FUNDING COMMITMENT — TRIGGERED BY DEMO 2 COMPLETION  ★

Demo 2 (Q2 2026): Live DCC-GARCH engine on production infrastructure + AI News Classification + 5-Signal Crisis Predictor. Bloomberg LP commitment is aligned with Bloomberg's 2026 AI Infrastructure Initiative for emerging markets. |
| --- |
| KPI | Phase 2 Target (Wk 10) | Seed Target (Month 6) |
| --- | --- | --- |
| Monthly Recurring Revenue | $10,000 | $28,000 |
| Paying Subscribers | 50 | 150 |
| API Uptime SLA | 99.5% | 99.9% |
| DCC-GARCH Latency | < 200 ms | < 100 ms (optimised) |
| News Classification Accuracy | > 90% on EM events | > 94% with fine-tuning |
| Discord Community | 500 → 1,200+ | 2,000+ |
| Signal | Market Indicator | Crisis Threshold | Detection Method | Weight |
| --- | --- | --- | --- | --- |
| Equity Volatility | CBOE VIX | > 30 (Extreme Fear) | Rolling 90-day Z-score | 25% |
| Rate Volatility | MOVE Index | > 120 | Temporal baseline anomaly | 20% |
| EM FX Stress | JPM EM FX Basket | 3σ deviation | DCC-GARCH regime | 25% |
| Credit Spread | EM Sovereign CDS | > 400 bps | Cross-market contagion | 20% |
| Commodity Shock | CRB Index + Gold | > 15% 30-day move | Percentile rank (5yr) | 10% |
| Segment | Plan | Monthly | Annual | Key Features Included |
| --- | --- | --- | --- | --- |
| Retail Investor | Starter | $29 | $290 | 10 EM markets, correlation dashboard, AI news feed |
| Retail Investor | Pro | $79 | $790 | All 45 EM markets, DCC-GARCH engine, Butterfly Effect, Crisis Predictor, AI classification |
| PMS / RIA | Professional | $199 | $1,990 | All Pro + Macro transmission chains, Crisis predictor
100 API calls/day, custom alerts |
| PMS / RIA | Team (5 seats) | $499 | $4,990 | Unlimited API, white-label export, priority support |
| Family Office | Enterprise | $999 | $9,990 | Unlimited seats, private LLM, entity-aware portfolio view
Dedicated CSM, 99.9% SLA |
| Family Office | Sovereign / HNI | Custom | Custom | On-premise LLM, SEBI/FATCA compliance, quarterly narrative reports |
| Bloomberg Terminal: $2,000/month ($24,000/year per seat)   │   AlphaEdge Pro: $79/month   │   Saving: 96% cost reduction with EM-native intelligence | Bloomberg Terminal: $2,000/month ($24,000/year per seat)   │   AlphaEdge Pro: $79/month   │   Saving: 96% cost reduction with EM-native intelligence | Bloomberg Terminal: $2,000/month ($24,000/year per seat)   │   AlphaEdge Pro: $79/month   │   Saving: 96% cost reduction with EM-native intelligence | Bloomberg Terminal: $2,000/month ($24,000/year per seat)   │   AlphaEdge Pro: $79/month   │   Saving: 96% cost reduction with EM-native intelligence | Bloomberg Terminal: $2,000/month ($24,000/year per seat)   │   AlphaEdge Pro: $79/month   │   Saving: 96% cost reduction with EM-native intelligence |
| Milestone | Subscribers | Blended ARPU | MRR | ARR |
| --- | --- | --- | --- | --- |
| Phase 2 Beta — Week 10 | 50 | $200 | $10,000 | $120,000 |
| Seed Round Close — Month 6 | 150 | $187 | $28,000 | $336,000 |
| Series A Target — Month 12 | 500 | $180 | $90,000 | $1,080,000 |
| Platform | Annual Cost | EM Coverage | DCC-GARCH | AI News | Crisis Signal |
| --- | --- | --- | --- | --- | --- |
| Bloomberg Terminal | $24,000/seat | Partial | ✗ | Basic | ✗ |
| FactSet / Refinitiv | $18-22K/seat | Partial | ✗ | Basic | ✗ |
| Koyfin / Quandl | $600-2,400 | Limited | ✗ | ✗ | ✗ |
| India tools (Screener etc.) | < $200 | India only | ✗ | ✗ | ✗ |
| AlphaEdge (Pro) | $79–$999/mo | 45 Markets | ✓ DCC-GARCH | ✓ Llama 3.1 | ✓ 5-Signal |
| Risk | Probability / Impact | Mitigation |
| --- | --- | --- |
| DCC-GARCH compute cost at scale | Low / Medium | Numba JIT + Redis caching benchmarked at <200 ms; horizontal scaling on Vercel Edge |
| LLM inference latency | Low / Low | Groq Llama 3.1 delivers <100 ms; OpenRouter fallback ensures 99.9% uptime |
| Real-time data feed reliability | Medium / Medium | Multi-source fallback: Yahoo Finance + Finnhub + CoinGecko; Redis buffer prevents single-source failures |
| Risk | Probability / Impact | Mitigation |
| --- | --- | --- |
| Slow institutional sales cycles | High / Medium | Retail-first GTM generates MRR while PMS/FO pipeline matures; Crescendo Partners provides warm PMS introductions |
| Bloomberg competitive response | Low / High | EM-native DCC-GARCH is a 2–3 year internal build for Bloomberg; strategic partnership preferred over competition |
| Pricing pressure / churn | Medium / Medium | Tiered model allows flexible discounting; API overage and white-label upsells protect margin |
| SEBI data licensing changes | Low / High | AlphaEdge uses publicly available NSE/BSE data and derivative intelligence — not raw licensed exchange feeds |
| Period | Technical Milestones | Business Milestones | Target KPI |
| --- | --- | --- | --- |
| Wk 1–3 | Production infra: Vercel Edge + Redis + WebSocket + Stripe | Funding close, engineering hires, community launch campaign | Infra 99.5% uptime |
| Wk 4–6 | AI News Intelligence: GDELT/ACLED + Groq Llama 3.1 pipeline live | PMS direct outreach (50 SEBI managers), Discord Pro push | 15 subscribers |
| Wk 7–8 | API productisation: auth, rate limiting, v1 docs published | Beta launch, Retail Starter/Pro live, first revenue | 30 subscribers |
| Wk 9–10 | Family Office Enterprise pilot, on-prem LLM POC | PMS Professional + FO Enterprise onboarding, $10K MRR target | $10,000 MRR |
| Wk 11–12 | Seed data room: retention cohorts, API metrics, Bloomberg integration POC | Seed investor meetings, Series A narrative development | Seed close prep |
| Vinod Doddareddy
Founder & CEO, AlphaEdge  |  Founder, Pinaka.ai
vinod.doddareddy@gmail.com   |   +91 63617 04635   |   alphaedge.dev
Credential  Ex-Director of SRE & Engineering, NVIDIA India — production infrastructure at planetary scale for one of the world's most demanding ML hardware companies
Credential  Ex-Director, LinkedIn Engineering — distributed systems platform leadership serving 900M+ professionals globally
Practitioner  Active systematic trader: Nifty 50 (equity index), BTC (crypto), gold & silver — solving his own pain point
Founder  Also founder of Pinaka.ai (AI Agentic Security) — demonstrating parallel AI venture execution capability |
| --- |
| STRENGTHS
Only DCC-GARCH engine covering 45 EM markets
98% cheaper than Bloomberg Terminal
500+ organic community (zero paid acquisition)
Validated predictive accuracy: DII/FII crossover call 3 weeks early
Founder pedigree: NVIDIA India & LinkedIn Engineering at Director level
180+ pages investor-grade technical documentation | WEAKNESSES
Pre-revenue: no live paying customers yet
Single founder — key-person risk until team is built
Brand recognition early stage
Sales function requires hiring post-funding
API productisation incomplete |
| --- | --- |
| OPPORTUNITIES
Bloomberg 2026 AI Initiative opens strategic distribution lane
India PMS AUM growing 40% CAGR — 400+ SEBI-registered managers
160M+ Demat accounts: retail sophistication rising rapidly
SEBI mandating better risk disclosure for PMS funds
Southeast Asia & MENA expansion (Phase 3)
Family office formation in India: 300+ new offices 2022–2025 | THREATS
Bloomberg could add EM correlation features internally (2–3 yr build)
LLM API cost inflation (Groq/OpenRouter pricing changes)
SEBI data licensing tightening on real-time feeds
Slow institutional sales cycles (6–12 months)
Well-capitalised fintech entrants from US/Singapore |
| Vinod Doddareddy
Founder, AlphaEdge  |  Founder, Pinaka.ai
✉  vinod.doddareddy@gmail.com
☎  +91 63617 04635
🌐  alphaedge.dev  (coming soon)
Discord Community: 500+ Members  |  All prices in USD |
| --- |