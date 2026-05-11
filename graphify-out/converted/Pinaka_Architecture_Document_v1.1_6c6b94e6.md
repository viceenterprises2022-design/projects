<!-- converted from Pinaka_Architecture_Document_v1.1.docx -->




PINAKA
AGENTIC AI SECURITY PLATFORM
Platform Architecture Document  ·  v1.1




Problem: "Multiple AI Agents spun up without proper security posture and guidelines exposes corporate and sensitive data."


# Table of Contents

# 1. Executive Summary
Pinaka is an enterprise-grade Agentic AI Security Platform that solves the critical governance gap created by rapid AI agent proliferation. As organizations deploy agents at scale — from Microsoft Copilot to Salesforce AgentForce to custom LangChain and AutoGen workflows — security teams have zero visibility into what those agents do, what data they access, and what risk they carry. Pinaka closes that gap with a unified platform covering discovery, posture management, runtime enforcement, and compliance.

## 1.1  Why Pinaka Is Urgent
- 23% of enterprises are already scaling agentic AI (McKinsey 2025); every business unit deploys agents without security oversight
- The average enterprise cannot enumerate its own AI agents — Noma Security's $135M raise validates 'unknown AI inventory' as the #1 CISO pain point
- EU AI Act (2025–2026), NIST AI RMF, and OWASP LLM Top 10 create hard compliance gates — unlocking legal and risk budgets that previously did not exist
- MCP (Model Context Protocol) became the enterprise integration standard in <12 months — 10,000+ active servers with zero dedicated security layer

## 1.2  Competitive Differentiation


# 2. Architecture Principles & Non-Functional Requirements
## 2.1  Core Design Principles

## 2.2  Non-Functional Requirements


# 3. System Overview
## 3.1  System Boundary and Zones

## 3.2  Core Data Flow — Steady State
- Agent performs action: tool call, data access, inter-agent message, or external API call.
- Connector captures event metadata and publishes to Kafka topic (tenant-partitioned).
- Policy Engine consumes event; evaluates against OPA policy bundle cached in Redis.
- Decision: ALLOW → audit log written async; DENY → enforcement signal sent + alert raised + audit log written sync; ESCALATE → HITL notification sent, action paused.
- MCP Gateway (inline mode) enforces decision inline for MCP traffic before agent receives response.
- Investigation Engine continuously consumes audit stream to update behaviour baselines and detect anomalies.
- Risk Engine recalculates AISPM score on any inventory change, policy event, or investigation finding.
- Discovery Engine runs scheduled (hourly) and event-triggered scans to maintain agent inventory freshness.
- Compliance Engine maps all policy and audit events to regulatory framework requirements in real time.
- Console, API, and webhooks surface findings to security teams, SIEM, SOAR, and notification channels.

## 3.3  Agent Identity Attestation Protocol  [NEW — Critical Architecture Addition]

### 3.3.1  Attestation Model
Pinaka issues a cryptographically signed Agent Identity Token (AIT) at agent registration time. AITs are bound to the agent's deployment fingerprint:

### 3.3.2  Attestation Verification Flow
- Agent presents AIT on every API call to Pinaka Enforcement Gateway or MCP Gateway.
- Gateway verifies Ed25519 signature against Pinaka's public key (cached, refreshed hourly).
- Gateway checks AIT expiry and revocation list (Redis-cached, updated on any security event).
- Gateway verifies fingerprint matches registered deployment (prevents agent spoofing by code injection).
- On mismatch: DENY + high-severity alert + HITL escalation + revoke AIT.
### 3.3.3  Attestation for Unregistered Agents (Shadow Agents)
- Discovery Engine detects unregistered agents via OAuth grants analysis and network telemetry
- Unregistered agents are placed in QUARANTINE policy group — most restrictive defaults
- Security admin receives alert: 'Unregistered agent detected — please register or block'
- Agent cannot self-register; registration requires human admin action with MFA


# 4. Component Architecture
## 4.1  Discovery Engine  [MANDATORY — v1.0]

### 4.1.1  Responsibilities
- Agent inventory: enumerate all agents (name, type, framework, owner, deploy date, last active, fingerprint)
- Tool mapping: identify every tool/API each agent is permitted to call
- Data access mapping: identify every data source each agent can read or write
- MCP server registry: maintain inventory of all active MCP servers, their schemas, and connected agents
- Shadow agent detection: identify agents deployed without security team knowledge via OAuth grant analysis
- Dependency graph: build and maintain agent→tool→data dependency graph for blast-radius calculation
- Fingerprint tracking: detect when agent code or config changes — triggers re-attestation requirement

### 4.1.2  Connector Priority and Protocol Matrix

## 4.2  AISPM Engine  [MANDATORY — v1.0]

### 4.2.1  Five-Dimension Risk Scoring Model

### 4.2.2  Composite Score & Risk Tiers

## 4.3  Policy Engine  [MANDATORY — v1.0]

### 4.3.1  Policy Hierarchy and Conflict Resolution

Conflict Resolution Rule: DENY Wins

### 4.3.2  OPA Policy Evaluation Architecture
- Open Policy Agent (OPA v0.65+) as the evaluation core — CNCF-graduated, audit-ready
- Policy bundles compiled and cached in Redis with 60-second TTL — <10ms evaluation from cache
- Bundle invalidation: any policy change triggers immediate cache flush for affected tenants
- Rego policy language — human-readable, git-versionable, supports unit testing via opa test
- Dry-run mode: evaluate any policy against historical audit events without enforcement — safe testing
- Policy linting: Pinaka runs opa check + custom linters on all policy PRs before merge

### 4.3.3  Policy Change Management
All policy changes follow a structured approval workflow to prevent accidental over-restriction or over-permission:

## 4.4  MCP Security Gateway  [MANDATORY — v1.0]

### 4.4.1  Deployment Modes

### 4.4.2  MCP Security Checks

## 4.5  Audit & Explainability Service  [MANDATORY — v1.0]

### 4.5.1  Full Audit Event Schema

### 4.5.2  Immutability Guarantees
- Apache Iceberg table with ACID transactions; rows written via INSERT only — no UPDATE or DELETE
- S3 Object Lock (WORM) with 7-year retention — even AWS root cannot delete during lock period
- Ed25519 hash chain: each event's signature includes the SHA-256 of the previous event; tampering is detectable
- CloudTrail monitors all S3 access to audit log buckets; alerts on any read by non-Pinaka principal
- Audit log is written and signature verified BEFORE the enforcement decision is acknowledged — event cannot be lost

### 4.5.3  Natural Language Query Interface
Analysts query audit logs in plain English. Examples:
- "Show me all agents that accessed customer PII in the last 7 days"
- "Which agents have been denied more than 10 times this week and why?"
- "List every external API call made by the finance agent group yesterday"
- "Generate an EU AI Act Article 14 (human oversight) compliance report for Q1 2026"
- "Show me all policy changes made by any admin in the last 30 days"
Implementation: LLM query layer (AWS Bedrock/Claude Sonnet, privacy-preserving, no raw data) → SQL/OPA query → OpenSearch result set → NL summary with citations to specific audit event IDs.

## 4.6  Human-in-the-Loop (HITL) Service  [MANDATORY — v1.0]

### 4.6.1  Approval Tier Model

### 4.6.2  Notification Architecture
Pinaka's notification system is a dedicated service with delivery guarantees:

### 4.6.3  Webhook Delivery Guarantees
- All outbound webhooks are written to a durable queue (Kafka topic) before HTTP delivery is attempted
- Each delivery attempt logged with status code, latency, and response body (truncated)
- Retry policy: exponential backoff starting at 30s; max 5 retries over 24 hours
- Dead Letter Queue: failed webhooks after 5 retries moved to DLQ; ops team alerted; customer notified
- Event replay: customers can request replay of any time window via API — Kafka consumer offset reset
- Delivery confirmation: Pinaka requires HTTP 2xx within 10s; timeout treated as failure
- HMAC-SHA256 signature on all webhook payloads — customers verify Pinaka origin

## 4.7  Investigation Engine  [MANDATORY — v1.0]

### 4.7.1  Detection Methods

### 4.7.2  Business-Context Risk Narrative — Generation Architecture
Every investigation finding auto-generates a narrative via a privacy-preserving LLM pipeline:
- Pinaka collects structured investigation data: agent metadata, violation details, blast radius, policy history.
- Data is sanitised: all raw content removed; only metadata, entity names, and classification tags retained.
- Sanitised structured data sent to AWS Bedrock (Claude Sonnet) with a deterministic prompt template.
- LLM generates business-context narrative in natural language (200–400 words).
- Narrative reviewed for hallucination risk via a validation layer (checks all entity references exist in source data).
- Narrative stored in PostgreSQL linked to investigation_id; surfaced in console and risk reports.
- All LLM calls logged in audit trail as SYSTEM_ACTION events — full traceability.

## 4.8  Compliance Engine  [MANDATORY — v1.0]

### 4.8.1  Framework Coverage — v1.0


# 5. Data Architecture
## 5.1  Data Store Selection Rationale

## 5.2  Database Connection Pooling and Query Optimization
### 5.2.1  Connection Pool Configuration

### 5.2.2  Schema Migration Strategy
- Flyway for PostgreSQL migrations — versioned SQL files, checksummed, applied in order
- Zero-downtime migrations required: additive changes only (add columns, add indices, add tables)
- Breaking changes: new column added + old column deprecated (90-day grace period) + old column dropped in next major release
- All migrations are backwards-compatible: new code runs against old schema; old code runs against new schema (during rolling deploy)
- Iceberg schema evolution via Iceberg's built-in add_column / rename_column operations — no migration files needed
- Migration dry-run in staging before any production deployment

## 5.3  Tenant Data Isolation

## 5.4  GDPR & Data Lifecycle Management  [NEW]

### 5.4.1  Data Subject Access Request (DSAR) Workflow
- DSAR submitted by data subject via Pinaka Privacy Portal or email to privacy@pinaka.ai
- Pinaka Privacy Engineer verifies identity of requestor (30 days to respond per GDPR Art.12)
- Automated DSAR tool queries all stores for records linked to the subject's user_id or email
- Report generated: what data Pinaka holds, why, for how long, who it was shared with
- Report delivered to requestor in machine-readable JSON + human-readable PDF
- DSAR completion logged in compliance audit trail

### 5.4.2  Right to Erasure (GDPR Art.17)
Pinaka's approach to erasure balances GDPR compliance with audit log immutability requirements:

### 5.4.3  Data Retention Automation


# 6. API Architecture
## 6.1  API Design Standards
- REST API first: every feature accessible via REST before UI is built
- Versioning: URI-based (/v1/, /v2/) with 12-month deprecation notice and email notification to API key owners
- OpenAPI 3.1 spec generated from code annotations — always in sync; never manually maintained
- Pagination: cursor-based on all list endpoints (no offset-based — inconsistent under concurrent writes)
- Idempotency: POST endpoints support Idempotency-Key header (UUID); duplicate requests within 24 hours return cached response
- Rate limiting: token bucket algorithm; per-API-key limits with X-RateLimit-* headers and Retry-After on 429
- Error format: RFC 7807 Problem Details (application/problem+json) for all errors
- CORS: strict allowlist of permitted origins; no wildcard * in production

## 6.2  API Rate Limiting Architecture

## 6.3  Session Management & Token Lifecycle

## 6.4  SDK Design  [NEW]

### 6.4.1  SDK Language Support Roadmap

### 6.4.2  Python SDK Usage Example


# 7. Technology Stack

## 7.1  Feature Flag Architecture
Feature flags are used for three distinct purposes — each with different flag types:


# 8. Observability, SLO & Alerting Framework

## 8.1  Service Level Objectives (SLOs)

## 8.2  Metrics — Key Indicators
### 8.2.1  Business Metrics (Pinaka Product Health)

### 8.2.2  Infrastructure Metrics (Service Health)

## 8.3  Distributed Tracing
- All services instrumented with OpenTelemetry SDK (Go: otelhttp; Python: opentelemetry-instrumentation-fastapi)
- Trace context propagated via W3C TraceContext headers across service boundaries
- 100% trace sampling for enforcement path (never sample-out a policy decision)
- 1% sampling for background jobs (Discovery scans, Risk recalculation) — adjustable via LaunchDarkly
- Traces exported to Datadog APM; full service dependency map auto-generated
- Critical: every enforcement decision trace must include tenant_id, agent_id, policy_ids, and final_decision as trace attributes

## 8.4  Structured Logging Standard

## 8.5  Alerting Runbook Pointers


# 9. Resilience & Fault Tolerance Architecture
## 9.1  Resilience Patterns

## 9.2  Chaos Engineering Strategy


# 10. CI/CD Pipeline & Quality Gates
## 10.1  Pipeline Architecture

## 10.2  Testing Strategy


# 11. Multi-Region & Data Residency Architecture
## 11.1  Region Strategy

## 11.2  EU Data Residency Enforcement
- EU tenants are provisioned into the eu-west-1 AWS account at signup — automated during onboarding flow
- Tenant routing: DNS-based routing via Route 53 Latency-based records routes EU IPs to EU API endpoint
- Data validation: AWS Config rule verifies EU tenant data resources (RDS, S3, Kafka) are in eu-west-1 or eu-central-1 only
- LLM calls for EU tenants: AWS Bedrock EU endpoint (eu-west-1); no data crosses to us-east-1
- Audit log replication: EU audit logs replicate to eu-central-1 (Frankfurt) for DR — no US replication
- Quarterly verification: automated compliance check confirms zero EU data in US regions; report generated for EU AI Act Art.10 evidence

## 11.3  Cross-Region Architecture


# 12. Deployment Architecture
## 12.1  Infrastructure Topology per Region

## 12.2  Security Hardening Checklist

## 12.3  BCDR Procedures
### 12.3.1  Backup Schedule

### 12.3.2  Disaster Recovery Runbook (Summary)
- Major incident declared by SRE Lead or CTO (PagerDuty P0 or manual declaration).
- DR bridge opened: SRE + Engineering Lead + CTO + Security Officer on call within 15 min.
- Impact assessment: which services affected? Which tenants impacted? Data loss risk?
- Activate DR region: ArgoCD in DR region promoted from read-only to active; Route 53 health check fails over DNS.
- Data validation: verify Kafka MirrorMaker 2 lag; verify RDS read replica promotion; verify Vault DR cluster unsealed.
- Tenant communication: status page updated within 30 min; affected tenants notified via email within 1 hour.
- Root cause investigation begins in parallel with restoration — separate on-call track.
- Primary region restoration: validate, test, then gradual traffic shift back (5% → 25% → 100%).
- Post-incident review (PIR) scheduled within 48 hours; blameless PIR format; findings tracked in GitHub Issues.
- Runbook updated if gaps identified; chaos experiment added to simulate root cause monthly.


# 13. Security Architecture
## 13.1  Threat Model (STRIDE)

## 13.2  Pinaka Incident Response Plan


## 13.3  Supply Chain Security


# 14. Integration Architecture
## 14.1  Connector SDK Developer Guide

### 14.1.1  SDK Interface Contract

### 14.1.2  Connector Certification Process
- Developer implements PinakaConnector ABC in their language of choice (SDK wrappers for Go/TypeScript provided)
- Run Pinaka Connector Test Suite (pinaka-connector-test-suite package) — validates all interface methods
- Submit to Pinaka Partner Portal with test results, security questionnaire, and sample connector config
- Pinaka security review: code review of authentication handling and data handling; 5-day SLA
- Pinaka certification issued; connector listed in Pinaka Connector Directory
- Certified connectors receive: Pinaka Certified badge, co-marketing opportunity, dedicated Slack channel

## 14.2  SIEM / SOAR Integration Matrix


# 15. Capacity Planning & Cost Architecture
## 15.1  Customer Tier Sizing Model

## 15.2  Infrastructure Cost Model (v1.0 US Region — Monthly)


# 16. Enterprise Onboarding Flow Architecture

## 16.1  Onboarding Steps — Technical Architecture

## 16.2  Time-to-Value Metrics


# 17. Feature Implementation Roadmap
## 17.1  v1.0 — MVP (Mandatory Features)
Target: Q3 2026 Beta. All 9 mandatory features must be production-grade before enterprise beta launch.

## 17.2  v1.5 — Phase 2 (Good-to-Have)

## 17.3  v2.0 — Phase 3 (Future)


# 18. Engineering Team Structure & Standards
## 18.1  Team Ownership Matrix

## 18.2  Engineering Standards & Conventions


# 19. Open Decisions — Sprint 0 Blockers



# 20. Next Steps
## 20.1  Sprint 0 Actions (2 Weeks — Immediately)
- Architecture review with full Engineering team: walk through this document section by section; collect objections and missing context.
- Resolve all CRITICAL open decisions (D1, D2, D3 from Section 19) before Sprint 1 starts.
- Set up engineering infrastructure: GitHub org, AWS accounts (dev/staging/prod), Terraform state backend, ArgoCD clusters, Datadog org, LaunchDarkly account.
- Establish engineering norms: branching strategy, PR review requirements, commit message standard, on-call rotation, incident response runbook location.
- Scaffold monorepo: service templates for Go services and Python services; shared protobuf definitions; OpenAPI spec template; Helm chart template.
- Technology spikes (run in parallel):
- Spike A: MCP Gateway inline proxy POC — measure latency at 1000 concurrent connections; validate <500ms target.
- Spike B: OPA Rego policy evaluation benchmark — 1000 RPS with cached bundle; measure <10ms per evaluation.
- Spike C: Agent fingerprinting prototype — demonstrate that code + config SHA-256 fingerprint can detect agent tampering.
- Spike D: Iceberg append-only write performance — 10K events/second; measure write latency distribution.
- First connector implementation: AWS Bedrock (P0, highest customer demand); use this to validate the full Connector SDK interface.
- Hire SRE Lead immediately — IaC and CI/CD setup blocks all teams without a dedicated infra engineer.

## 20.2  Document Sequence




Document Control: CONFIDENTIAL — Internal Engineering Use Only. All updates must be reviewed by Engineering Lead, approved by CTO, and versioned in the document control register (docs/architecture/CHANGES.md). This document supersedes v1.0. Next scheduled review: 30 days post-HLD completion or immediately on any major architectural decision.

# Appendix A — Comprehensive Glossary

# Appendix B — Reference Standards & Regulatory Bibliography
- EU AI Act (Regulation (EU) 2024/1689) — effective 2025–2026; Articles 9, 10, 13, 14, 17 directly applicable to Pinaka
- NIST AI Risk Management Framework 1.0 (NIST AI 100-1) — GOVERN, MAP, MEASURE, MANAGE functions
- OWASP LLM Top 10 (2025 Edition) — LLM01 Prompt Injection through LLM10 Model Theft
- MITRE ATLAS (Adversarial Threat Landscape for AI Systems) — TTP framework for AI-specific attacks
- CIS Kubernetes Benchmark v1.9 — node and cluster hardening standard
- SOC 2 Trust Service Criteria (AICPA 2022) — Security, Availability, Confidentiality TSCs
- ISO 27001:2022 — Information Security Management (v1.5 certification target)
- NIST SP 800-204 — Security Strategies for Microservices-based Application Systems
- NIST SP 800-218 (SSDF) — Secure Software Development Framework
- GDPR (Regulation (EU) 2016/679) — Articles 5, 12, 13, 15, 17, 20, 25, 32, 33
- DPDPA 2023 (India Digital Personal Data Protection Act) — for v2.0 India region
- Model Context Protocol Specification (Anthropic, November 2024) — MCP Gateway implementation reference
- SLSA (Supply-chain Levels for Software Artifacts) Framework v1.0 — supply chain security
- Open Policy Agent Rego Language Reference — policy engine implementation
|  |
|  |
| Document Version | v1.1 — Comprehensive Revision (All gaps addressed) |
| Date | April 2026 |
| Classification | CONFIDENTIAL — Internal Engineering Use Only |
| Product | Pinaka.ai — Agentic AI Security Platform |
| Stage | MVP Architecture (v1.0) + Phase 2 Roadmap (v1.5) |
| Domain | Cybersecurity / Agentic AI Governance |
| Audience | Engineering, DevOps, Security, Product, CTO, Investors |
| v1.1 Changes | Added: Observability/SLOs, Resilience, CI/CD, Testing, Multi-Region,
GDPR/Data Lifecycle, Agent Identity Attestation, Policy Conflict Resolution,
Capacity Planning, Cost Architecture, SDK Design, Notification Architecture,
Incident Response, Supply Chain Security, Onboarding Flow, Change Management |
| Next Documents | HLD → UI/UX Design → Low Level Design (LLD) |
| Mission | Provide every enterprise with complete visibility, control, and protection for every AI agent they run — from shadow AI discovery to deterministic runtime enforcement — without moving a single byte of their data. |
| --- | --- |
| Differentiator | Pinaka Approach | Competitor Gap |
| --- | --- | --- |
| Universal Control Plane | Model-agnostic + framework-agnostic enforcement at the protocol level (API/MCP), not at the SDK level | Zenity is Microsoft-only; Noma is AWS-centric; none work universally |
| End-to-End MCP Security | Discovery + posture + runtime enforcement + audit for MCP — the only full-stack MCP security platform | Only 2 of 15 competitors have any MCP security; none cover all 4 layers |
| Zero Data Migration | Federated architecture — Pinaka queries data sources in-place; never ingests raw agent data | Most competitors require log forwarding or data pipeline setup |
| EU AI Act Compliance Engine | First purpose-built AI agent compliance mapping at Article level for EU AI Act | No competitor has Article-level EU AI Act mapping for AI agents specifically |
| Agent Identity Attestation | Cryptographic agent identity verification — Pinaka knows which agent it is, not just what it claims to be | No competitor has a formal agent attestation protocol |
| Business-Context Risk Narratives | Risk findings in plain English with business impact — not just log entries | Competitors output technical logs; Pinaka outputs board-ready risk narratives |
| # | Principle | Statement | Engineering Constraint |
| --- | --- | --- | --- |
| P1 | Security by Design | Pinaka is a security product — any architectural weakness is a product failure | Zero-trust between all internal services; mTLS enforced by Istio; no implicit service trust |
| P2 | Zero Data Migration | Enterprises will not move their data to Pinaka's infrastructure | Federated queries via connectors only; raw logs never ingested into Pinaka storage; connector reads metadata, not content |
| P3 | Model Agnostic | Enterprises run GPT-4, Claude, Gemini, Llama, and custom models simultaneously | All detection and enforcement logic operates on API call metadata, not model-specific formats |
| P4 | Framework Agnostic | LangChain, AutoGen, CrewAI, Semantic Kernel, custom frameworks coexist | Enforcement at protocol level (MCP/REST API), not at framework SDK level |
| P5 | Day-1 Value | Enterprise SaaS wins on time-to-value — first risk finding in <4 hours | Connector setup must be <30 min; initial scan <2 hours; risk scores visible same day |
| P6 | Audit Immutability | Compliance requires tamper-proof, non-repudiable evidence | Append-only Iceberg tables; Ed25519 hash chain; audit event signed BEFORE acknowledgement to caller |
| P7 | Human Authority | AI agents must never exceed human-defined scope; humans retain override at all times | Every autonomous enforcement action has human-override endpoint; no enforcement without explicit policy grant |
| P8 | API-First | Every feature accessible via API before UI is built; UI is a client of the public API | OpenAPI spec generated from code; UI uses same REST endpoints as customers |
| P9 | Privacy Preserving | Pinaka must never become a data exfiltration vector itself | Default: log action type + metadata only; raw prompt/response content is NEVER stored by default; opt-in requires admin + legal approval |
| P10 | Multitenancy First | SaaS unit economics require efficient multitenancy from the first line of code | Tenant isolation at data layer before any feature is built; retrofitting costs 10x; RLS + per-tenant crypto keys from Day 1 |
| P11 | Fail Secure | When Pinaka is degraded or unavailable, agents fail to a safe state | Policy enforcement defaults to DENY on gateway timeout; configurable per tenant to ALLOW with alert (for availability-sensitive workloads) |
| P12 | Observable by Default | Every service emits structured logs, metrics, and traces from Day 1 | OpenTelemetry instrumentation is a merge requirement; no service ships without SLO definition |
| NFR | Metric | v1.0 Target | v1.5 Target | Measurement |
| --- | --- | --- | --- | --- |
| Availability | Platform uptime | 99.9% (43.8 min/month) | 99.95% (21.9 min/month) | Synthetic monitoring from 3 regions |
| Policy Enforcement Latency | p50 / p99 decision time | <50ms p50 / <500ms p99 | <20ms p50 / <100ms p99 | Prometheus histogram per enforcement call |
| Discovery Latency | First scan completion (mid-size enterprise, 50 agents) | <2 hours | <30 minutes | Scan job duration metric |
| API Latency | p99 REST API response (non-enforcement) | <200ms | <100ms | API Gateway p99 metric |
| Throughput | Concurrent agent actions/sec per tenant | 1,000 RPS | 10,000 RPS | Load test benchmark (k6) |
| Audit Write Latency | Event signed and persisted to Iceberg | <500ms p99 | <100ms p99 | Audit service write duration metric |
| Data Retention — Hot | Audit events queryable in OpenSearch | 90 days | 365 days | Index lifecycle policy |
| Data Retention — Warm | Audit events in Iceberg (Athena queryable) | 2 years | 7 years | S3 Intelligent Tiering |
| RTO | Recovery Time Objective — full platform restore | <4 hours | <1 hour | DR drill result |
| RPO | Recovery Point Objective — maximum data loss | <15 minutes | <5 minutes | Kafka replication lag + DB backup frequency |
| MTTR | Mean Time to Restore from PagerDuty alert | <60 minutes | <30 minutes | Incident history tracking |
| Scalability | Scale model | Stateless HPA on CPU/RPS | Predictive auto-scaling + KEDA | HPA metrics + load test |
| Throughput — Kafka | Events processed per second (all tenants) | 50,000 EPS | 500,000 EPS | Kafka consumer lag metric |
| Error Rate | 5xx rate on enforcement API | <0.1% | <0.01% | API Gateway 5xx rate |
| Encryption at Rest | Standard | AES-256 (AWS-managed keys) | AES-256 (BYOK per tenant) | AWS Config rule |
| Encryption in Transit | Minimum TLS version | TLS 1.3 | TLS 1.3 + HSTS | TLS scan (Qualys SSL Labs A+) |
| Zone | Contains | Connectivity | Trust Level |
| --- | --- | --- | --- |
| Enterprise AI Ecosystem | AI agents, LLM apps, MCP servers, agent frameworks (LangChain, AutoGen, CrewAI) | Outside Pinaka — connected via read-only connectors | ZERO — untrusted external |
| Enterprise Data Plane | Databases, APIs, SaaS tools, cloud storage that agents access | Outside Pinaka — metadata telemetry only via connectors | ZERO — untrusted external |
| Pinaka Ingestion Layer | API Gateway, MCP Gateway, Connector Manager, Event Stream (Kafka) | Internet-facing (TLS 1.3); internal mTLS | LOW — authenticated, rate-limited |
| Pinaka Control Plane | Discovery, AISPM, Policy, Investigation, HITL, Compliance Engines | Internal only; mTLS enforced by Istio | HIGH — internal services |
| Pinaka Data Plane | PostgreSQL, TimescaleDB, Neo4j, Redis, Iceberg on S3, OpenSearch | Internal only; VPC-private; no public endpoints | HIGH — encrypted, RBAC |
| Pinaka Management Plane | Auth, Multitenancy, Billing, Config, Observability, Notification | Internal + ops access; VPN-gated for ops | MEDIUM — operational |
| Pinaka Delivery Layer | CDN (CloudFront), REST API, Console UI, Webhook Engine, SDK | Internet-facing (TLS 1.3); WAF protected | LOW — customer-authenticated |
| Why this matters | Without a formal agent identity protocol, any process can claim to be 'finance-report-agent' and Pinaka would apply that agent's more permissive policies. This is the #1 bypass risk. No competitor has addressed this formally. |
| --- | --- |
| Agent Identity Token (AIT) — JSON structure:
{
  "ait_id":       "agt_7f3a9c...UUID",
  "tenant_id":    "ten_abc123",
  "agent_name":   "finance-report-agent",
  "agent_type":   "LangChain/OpenAI",
  "fingerprint":  "SHA-256(source_code_hash + deploy_config + env_hash)",
  "registered_by":"user_admin_xyz",
  "issued_at":    "2026-04-01T10:00:00Z",
  "expires_at":   "2026-07-01T10:00:00Z",
  "permissions":  ["tool:spreadsheet-read","tool:email-send"],
  "signature":    "Ed25519(Pinaka_signing_key, above_fields)"
} |
| --- |
| Purpose | Continuously discover every AI agent, LLM app, MCP server, and shadow AI deployment. Build and maintain the authoritative agent inventory and dependency graph. |
| --- | --- |
| Priority | Connector | Protocol | Coverage | Auth Method |
| --- | --- | --- | --- | --- |
| P0 | AWS Bedrock + Agents | AWS SDK + CloudTrail | Amazon ecosystem agents | IRSA / IAM Role |
| P0 | Azure OpenAI + Copilot Studio | Azure Management API | Microsoft ecosystem agents | Service Principal + MSAL |
| P0 | Google Vertex AI + Gemini | GCP API | Google ecosystem agents | Workload Identity Federation |
| P0 | OpenAI Assistants API | OpenAI REST API v2 | GPT-powered agents | API Key (encrypted in Vault) |
| P0 | Anthropic Claude API | Anthropic REST API | Claude-powered agents | API Key (encrypted in Vault) |
| P0 | MCP Protocol (Universal) | MCP SSE + JSON-RPC 2.0 | All MCP-connected agents | AIT + mTLS |
| P1 | Salesforce AgentForce | Salesforce REST + Streaming API | CRM AI agents | OAuth 2.0 Connected App |
| P1 | ServiceNow Now Assist | ServiceNow REST API | ITSM AI agents | OAuth 2.0 + Service Account |
| P1 | Microsoft Entra ID | Graph API | Shadow AI via OAuth grant analysis | Service Principal + MSAL |
| P1 | LangChain / LangSmith | LangSmith REST API | LangChain-based agents | API Key |
| P2 | AutoGen / CrewAI | Python SDK hooks | Open-source framework agents | AIT injection via SDK patch |
| P2 | Hugging Face Inference | HF Inference API | HuggingFace-hosted models | API Key |
| P2 | Atlassian Rovo | Atlassian REST API | Jira/Confluence AI agents | OAuth 2.0 |
| Purpose | Continuously assess and score AI agent risk. Produce the Agentic Risk Map (ARM) and maintain per-agent AISPM scores that trigger policy and alert actions. |
| --- | --- |
| Dimension | Weight | Signals | Scoring Algorithm | Score Range |
| --- | --- | --- | --- | --- |
| Permission Scope | 25% | Tool count, tool sensitivity (R/W/X), external vs internal destinations | Entropy-based overpermission: S = Σ(tool_sensitivity_tier × access_type_weight) / max_expected | 0–100 |
| Data Access Sensitivity | 25% | Data classification tiers (PII, IP, financial, regulated, public) | Tier multiplier × volume: D = Σ(data_tier × access_frequency_percentile) | 0–100 |
| Blast Radius | 20% | Downstream agent/user/system reachability via graph traversal | Graph BFS depth × node criticality weight: B = Σ(depth_factor × node_criticality) | 0–100 |
| Autonomy Level | 15% | HITL tier classification, approval bypass frequency, self-modification capability | Tier mapping: Supervised=0, Assisted=25, Semi-auto=50, Auto=75, Fully-autonomous=100 | 0–100 |
| Policy Compliance | 15% | Active violation count, violation severity, violation trend (improving/worsening) | V = Σ(violation_CVSS_score × recency_decay_factor) | 0–100 |
| Risk Tier | Score Range | Default Policy Tier | Console Display | Auto-Action |
| --- | --- | --- | --- | --- |
| CRITICAL | 80–100 | MAXIMUM RESTRICTION | Red — flashing | Immediate HITL escalation + security team alert |
| HIGH | 60–79 | ELEVATED RESTRICTION | Red | HITL required for all tool calls above Tier 1 |
| MEDIUM | 40–59 | STANDARD | Amber | Standard policy enforcement; analyst review recommended |
| LOW | 20–39 | PERMISSIVE | Green | Standard policy; no additional restrictions |
| MINIMAL | 0–19 | MINIMAL | Grey | Monitoring only; no active restrictions |
| Purpose | Real-time evaluation of every agent action against the active policy set. Produces ALLOW, DENY, or ESCALATE decisions. The enforcement brain of Pinaka. |
| --- | --- |
| Level | Name | Managed By | Override Rule | Conflict Resolution |
| --- | --- | --- | --- | --- |
| L0 | Platform Baseline | Pinaka (immutable) | Cannot be overridden by any tenant | Always applied first; blocks absolute prohibitions (e.g., child safety, credential exfiltration) |
| L1 | Tenant Policy | Tenant Security Admin | Overrides L0 defaults for permitted categories | Most restrictive L1 policy wins when multiple L1 policies apply to same agent |
| L2 | Agent Group Policy | Tenant Security Engineer | Overrides L1 defaults for this group | Group policies supplement L1 — DENY in any level = DENY; ALLOW requires all levels to permit |
| L3 | Agent-Specific Policy | Tenant Admin (MFA) | Overrides L2 defaults for this agent only | Must be explicitly granted; audit event created; periodic review reminder at 90 days |
| ℹ | When multiple policies of the same level apply to an agent action, the most restrictive decision wins. DENY > ESCALATE > ALLOW. This is the Fail Secure principle. Only L3 Agent-Specific policies can create exceptions — and those require MFA + audit trail + 90-day review. |
| --- | --- |
| Step | Action | Who | Tooling | SLA |
| --- | --- | --- | --- | --- |
| 1 | Draft policy in Pinaka Policy Editor | Security Engineer | Pinaka Console / VS Code extension | — |
| 2 | Run dry-run against 30-day audit history | Security Engineer | Pinaka Dry-Run API | <5 min |
| 3 | Review dry-run impact report (what would have been denied/escalated) | Security Engineer + Manager | Pinaka Console | <24 hours |
| 4 | Submit policy PR to policy git repository | Security Engineer | GitHub | — |
| 5 | Automated checks: opa test + lint + compliance mapping | CI Pipeline | GitHub Actions + OPA | <10 min |
| 6 | Peer review by second security engineer | Peer Reviewer | GitHub PR review | <48 hours |
| 7 | Approval by Tenant Admin (MFA required for L3) | Tenant Admin | Pinaka Console + MFA | <48 hours |
| 8 | Deploy to staging; 24-hour shadow mode (log only, no enforcement) | Platform | ArgoCD | 24 hours |
| 9 | Promote to production | Tenant Admin | ArgoCD + Pinaka API | — |
| 10 | Audit event: policy_change written with author, approver, diff, timestamp | System | Audit Service | Immediate |
| Purpose | Inline security gateway for all Model Context Protocol traffic. Inspect, enforce, log, and govern every tool call and inter-agent message that flows through MCP. |
| --- | --- |
| Mode | How It Works | Coverage | Latency Impact | Best For |
| --- | --- | --- | --- | --- |
| Inline Transparent Proxy (Default) | Pinaka MCP Gateway sits between MCP clients and servers; transparent interception via iptables/eBPF | 100% MCP traffic | <50ms added latency (target) | New deployments; highest security coverage |
| Sidecar Proxy | Pinaka agent sidecar injected alongside each agent container via Kubernetes mutating webhook | Container-level MCP traffic | <30ms added latency | Kubernetes-native deployments |
| API Hook (Lightweight) | Agents include Pinaka SDK call; policy decision fetched before each tool call | Declarative coverage only | <20ms added latency (network call + cache hit) | Existing agents where proxy deployment is blocked |
| Out-of-Band Audit | Connector reads MCP server access logs; no inline enforcement; audit + alerting only | Full audit; no enforcement | Zero impact | Environments where inline mode is not permissible |
| Check | Description | Implementation | Action on Violation |
| --- | --- | --- | --- |
| Tool Authorization | Verify agent AIT grants access to this specific tool | OPA policy evaluation with AIT claims | DENY + policy_violation alert |
| Parameter Injection Detection | Detect prompt injection patterns in tool call parameters | Pattern matching + ML classifier (fine-tuned on OWASP LLM01) | DENY + injection_detected alert |
| PII/Sensitive Data Scan | Scan parameters for PII, credentials, IP, classified markers using DLP patterns | AWS Comprehend Medical + custom regex + NLP classifier | DENY or REDACT based on policy |
| Rate Limiting Per Agent | Enforce per-agent per-tool call rate limits (token bucket) | Redis INCR + TTL per agent+tool key | THROTTLE + rate_limit_hit alert |
| MCP Server Verification | Verify MCP server URL, TLS certificate, and entry in approved server registry | PKI verification + registry lookup | DENY + unverified_server alert |
| Response Data Scanning | Scan tool responses before returning to agent — detect credential leakage in responses | DLP scan on response payload | REDACT or BLOCK + data_leakage alert |
| Excessive Agency Detection | Detect agents making tool calls outside their defined operational scope | Scope classification model + policy check | DENY + excessive_agency alert |
| Agent-to-Agent Auth | Verify calling agent identity when one agent invokes another via MCP | AIT verification for source agent | DENY + unauthorized_agent_call alert |
| Purpose | Immutable, cryptographically signed, tamper-evident audit log of every platform event. The evidence layer for compliance, forensics, incident response, and regulatory reporting. |
| --- | --- |
| Field | Type | Description | Indexed? |
| --- | --- | --- | --- |
| event_id | UUID v7 | Globally unique, time-sortable event identifier | Yes (primary) |
| tenant_id | UUID | Tenant partition key | Yes |
| agent_id | UUID | The agent that performed the action | Yes |
| agent_ait_id | UUID | The AIT used to authenticate this agent | Yes |
| event_type | Enum | TOOL_CALL | DATA_ACCESS | AGENT_MSG | POLICY_DECISION | HITL_REQUEST | HITL_RESPONSE | HITL_TIMEOUT | DISCOVERY_SCAN | RISK_SCORE_CHANGE | POLICY_CHANGE | AIT_ISSUED | AIT_REVOKED | USER_ACTION | COMPLIANCE_REPORT | Yes |
| timestamp | RFC3339 UTC | Nanosecond precision event timestamp | Yes (time-series) |
| action_summary | String 512 | Natural language description of the action (auto-generated) | Full-text |
| policy_decision | Enum | ALLOW | DENY | ESCALATE | N/A | Yes |
| policy_ids_evaluated | UUID[] | All policies evaluated for this action | Yes |
| winning_policy_id | UUID | The policy that determined the final decision | Yes |
| risk_delta | Float | Agent risk score change triggered by this event (+/-) | No |
| risk_score_after | Integer | Agent risk score after this event (0–100) | No |
| regulatory_tags | String[] | EU AI Act articles, NIST RMF functions, OWASP controls this event is evidence for | Yes |
| tool_name | String | The MCP tool or API endpoint called (if applicable) | Yes |
| destination_classification | Enum | INTERNAL | EXTERNAL | MCP_SERVER | AGENT | Yes |
| data_classification | String[] | Data sensitivity tiers detected in this action | Yes |
| enforcement_mode | Enum | INLINE | SIDECAR | API_HOOK | OUT_OF_BAND | No |
| approver_id | UUID | For HITL events: the user who approved or denied | Yes |
| approval_latency_ms | Integer | Time from HITL request to decision | No |
| metadata | JSON | Action-specific metadata (tool params redacted per policy, destination, entity refs) | Full-text |
| hash_prev | SHA-256 | Hash of previous event in chain (linked list integrity) | No |
| signature | Ed25519 | Platform signature of all above fields for tamper detection | No |
| Purpose | Configurable human approval workflows for agent actions that exceed automatic trust thresholds. The mechanism that keeps humans in authority over AI agent operations. |
| --- | --- |
| Tier | Trigger Condition | Notification | Timeout Behaviour | Approver Scope |
| --- | --- | --- | --- | --- |
| T0 — Auto Allow | Low-risk action; baseline behaviour; L0–L2 policy ALLOW | None | N/A | N/A |
| T1 — Soft Approval | Medium risk; sensitive data tag; first occurrence of action type | Slack/Teams DM + Console badge | Auto-ALLOW after 5 min (configurable) | Any security analyst in tenant |
| T2 — Hard Approval | High risk; near policy boundary; external destination with sensitive data | Slack/Teams + Email + Console alert | Auto-DENY after 15 min + alert | Security Engineer or above |
| T3 — Multi-Party | Critical risk; bulk operation; destructive action; CRITICAL risk score agent | All channels + PagerDuty incident | Auto-DENY immediately + incident ticket | 2-of-N approvers (configurable N) |
| T4 — Emergency Block | Risk score crosses CRITICAL threshold during active session | Immediate DENY + PagerDuty P1 + Slack all-hands channel | Instant; no timeout | Auto-blocked; requires Security Admin to unblock |
| Channel | Use Case | Delivery Guarantee | Retry Policy | Escalation Fallback |
| --- | --- | --- | --- | --- |
| Slack Bot | HITL T1/T2; risk alerts; daily digest | At-least-once (Slack API 200 required) | 3 retries with exponential backoff | Falls back to Email if Slack unreachable >30s |
| Microsoft Teams Bot | HITL T1/T2 for Teams-native orgs | At-least-once | 3 retries | Falls back to Email |
| Email (AWS SES) | All tiers; HITL T2/T3; compliance reports | Delivery tracking via SES bounce/complaint | SES internal retry | SMS fallback for T3 if email bounces |
| PagerDuty | HITL T3/T4; platform SLO alerts; IR triggers | PagerDuty guaranteed delivery | PD handles retry | Phone escalation via PagerDuty on-call |
| SMS (Twilio) | HITL T3 backup; on-call pages | At-least-once | 3 retries | Manual phone call (out of scope) |
| Webhook (Customer) | SIEM/SOAR integration; custom alerting | At-least-once with delivery confirmation | 5 retries with backoff; DLQ after 5 failures | Alert to platform ops if DLQ accumulates |
| Console (In-App) | All events; real-time push via WebSocket | Best-effort (WebSocket) | Reconnect with replay from last event ID | N/A — supplementary channel only |
| Purpose | Continuous behavioural analysis, anomaly detection, root-cause investigation, and business-context narrative generation for all agent activity. |
| --- | --- |
| Method | Algorithm | Training Data | Update Frequency | False Positive Strategy |
| --- | --- | --- | --- | --- |
| Behavioural Baseline | Online learning: exponential moving average + z-score deviation | 30-day rolling audit stream per agent | Continuous (online learning) | Alert on >3σ deviation; analyst confirms; feedback loop reduces FP over time |
| Policy Violation Pattern Analysis | Sequential pattern mining (PrefixSpan) on violation history | All policy violation events | Daily retrain | Cluster violations by type; suppress duplicate alerts within 1-hour windows |
| Cross-Agent Collusion Detection | Graph pattern matching on interaction graphs — detect coordinated action across agents | Agent interaction graph (Neo4j) | Event-triggered on each agent interaction | Alert only when 3+ agents show correlated anomalous patterns |
| Blast Radius Impact Calculation | BFS traversal on dependency graph with criticality weights | Agent dependency graph (Neo4j) | Triggered on each risk event | Calculate theoretical max impact; show confidence interval |
| Threat Intelligence Overlay | IOC matching: IP, domain, tool endpoint against threat feeds | MITRE ATLAS, commercial feeds (configurable) | Feed refresh every 4 hours | IOC confidence score required >80% before alert |
| Purpose | Map Pinaka audit and governance data to regulatory frameworks. Generate audit-ready compliance evidence reports. Track real-time compliance posture. |
| --- | --- |
| Framework | Articles/Controls Covered | Evidence Source in Pinaka | Report Format |
| --- | --- | --- | --- |
| EU AI Act (Reg. 2024/1689) | Art.9 (Risk mgmt), Art.10 (Data governance), Art.13 (Transparency), Art.14 (Human oversight), Art.17 (Documentation) | AISPM scores, HITL audit trail, ARM graph, policy change log | PDF + structured JSON for machine consumption |
| NIST AI RMF 1.0 | GOVERN 1–6, MAP 1–5, MEASURE 1–4, MANAGE 1–4 (all 4 functions) | Policy registry, risk scores, investigation findings, compliance events | PDF + NIST CSF-compatible XLSX |
| OWASP LLM Top 10 (2025) | LLM01–LLM10 (prompt injection, insecure output, supply chain, DoS, excessive agency, etc.) | MCP Gateway injection alerts, AISPM excessive-agency scores, Discovery supply chain data | PDF per control with pass/fail + evidence links |
| MITRE ATLAS | AI-specific TTPs: reconnaissance, resource development, initial access, persistence, discovery, exfiltration | IOC overlay alerts, anomaly detection hits, cross-agent correlation events | TTP coverage matrix + detection gap analysis |
| SOC 2 Type II | CC6, CC7, CC8, CC9 (Logical access, monitoring, change management, risk management) | RBAC audit trail, policy change log, HITL records, API access logs | Auditor-format evidence package (ZIP with CSV + PDF) |
| Store | Technology | Purpose | Rationale | Scaling Model |
| --- | --- | --- | --- | --- |
| Agent Inventory | PostgreSQL 16 (RDS Multi-AZ) | Structured agent metadata, policy assignments, user data, AIT registry | ACID; RLS enforced; strong relational joins; pg_stat for monitoring | Read replicas per AZ; Aurora Serverless v2 for auto-scaling |
| Risk Score DB | TimescaleDB (RDS extension) | Time-series risk scores, trending, score history | Native time-series; hypertable compression; PostgreSQL compatibility | Chunk-based auto-partitioning by time |
| Audit Log | Apache Iceberg on S3 | Immutable append-only audit log; long-term retention; chain integrity | Immutable table format; petabyte scale; Athena queryable; S3 Object Lock (WORM) | Partitioned by tenant + date; Iceberg compaction via Spark on EMR Serverless |
| Event Stream | Apache Kafka (AWS MSK) | Real-time event bus; service decoupling; event replay capability | Industry standard; ordered partitions; consumer group isolation per tenant; 7-day retention | MSK Auto Scaling; partition count increases with tenant throughput |
| Graph DB | Neo4j (AuraDB Enterprise) | Agent dependency graph; blast radius BFS; ARM visualisation | Native graph traversal; Cypher queries; AuraDB managed backups | AuraDB Enterprise auto-scaling by AuraDB |
| Policy Store | PostgreSQL + OPA Redis cache | Policy definitions, versions, history; compiled bundle cache | OPA native bundle format; git-backed version control; <10ms cache hits | Redis Cluster mode; policy bundles <1MB each |
| Audit Search | OpenSearch 2.x (AWS) | Full-text audit search; analyst NL query results; SIEM feed | ES-compatible API; managed; UltraWarm for cost-efficient older data | OpenSearch auto-scaling; UltraWarm for >90-day data |
| Cache | Redis 7.x Cluster (ElastiCache) | Policy decision cache; AIT cache; rate limit counters; session tokens | Sub-millisecond; atomic INCR for rate limits; TTL support | Cluster mode with 6 shards; ElastiCache Auto Scaling |
| Object Storage | AWS S3 (versioned + Object Lock) | Audit log archive; compliance report export; connector credential backup | Durable 11-nines; S3 Object Lock for WORM; S3 Intelligent Tiering for cost | Serverless — scales automatically |
| Secrets | HashiCorp Vault + AWS Secrets Manager | Connector credentials; API keys; per-tenant encryption keys (BYOK) | HSM-backed; automatic 90-day rotation; audit trail; KMS integration | Vault HA cluster (3 nodes); auto-unseal via AWS KMS |
| Service | DB Target | Pool Technology | Pool Size | Config Rationale |
| --- | --- | --- | --- | --- |
| Policy Engine | PostgreSQL | PgBouncer (sidecar) | Min:5 Max:20 per pod | Policy queries are short; PgBouncer transaction pooling; max 20 prevents connection exhaustion |
| Discovery Engine | PostgreSQL | PgBouncer | Min:5 Max:30 | Longer scan transactions; higher max for parallel connector scans |
| Audit Service | TimescaleDB + Iceberg | PgBouncer + Iceberg REST Catalog | Min:10 Max:50 | High write throughput; async write path; Iceberg catalog is stateless HTTP |
| Investigation Engine | Neo4j + PostgreSQL | Neo4j Bolt driver (built-in pooling) + PgBouncer | Neo4j:Min:5 Max:20; PG:Min:5 Max:20 | BFS queries are long-running; smaller pool to prevent query pile-up |
| Risk Engine | TimescaleDB | PgBouncer | Min:5 Max:20 | Score updates are point writes; small pool sufficient |
| Layer | Isolation Mechanism | Enforcement Point | Audit Coverage |
| --- | --- | --- | --- |
| PostgreSQL | Row-Level Security (RLS) policies filter every query by tenant_id | Database-level; cannot be bypassed by application code | pg_audit logs all queries; RLS violations alert |
| Kafka | Dedicated topic per tenant (naming: pinaka.{tenant_id}.events.*) | MSK IAM topic-level ACLs; cross-tenant consumer groups impossible by config | MSK CloudTrail + Pinaka consumer metrics per topic |
| Redis | Key namespacing: {tenant_id}:{key_type}:{key} | Application-level; Redis AUTH per namespace (Cluster mode) | Redis MONITOR feed → Pinaka ops log |
| S3 | Per-tenant S3 prefix with dedicated IAM policy | IAM: deny s3:* unless key prefix matches tenant ID | CloudTrail S3 access logs per tenant prefix |
| Neo4j | Separate Neo4j database per tenant (AuraDB logical isolation) | AuraDB API enforces database-level isolation | AuraDB audit log + query log per database |
| OpenSearch | Index per tenant (naming: pinaka-audit-{tenant_id}-*) | ISM policy per tenant; OpenSearch index-level auth | OpenSearch audit log |
| Encryption | Per-tenant encryption key in Vault; all S3 + RDS objects encrypted with tenant key | Vault policy enforces key access; AWS KMS enforces encryption | Vault audit log + KMS CloudTrail |
| Requirement | GDPR Article 17 (Right to Erasure), Article 20 (Data Portability), Article 15 (Subject Access Request), Article 5(1)(e) (Storage Limitation) all apply to data Pinaka holds about agents and their operators. |
| --- | --- |
| Data Category | Erasure Method | Immutable Audit Logs | Rationale |
| --- | --- | --- | --- |
| User profile data (name, email, preferences) | Hard delete from PostgreSQL within 30 days of request | User ID in audit logs is anonymised (SHA-256 of user_id) — audit trail preserved without PII | GDPR requires PII deletion; audit chain integrity maintained |
| Agent metadata | Soft delete on agent record; agent marked DELETED; data retained for 90 days (compliance hold) then purged | Agent ID in audit logs anonymised after retention period | Regulatory hold period before full deletion; audit trail maintained |
| Audit log content | Audit logs are immutable by design (WORM); pseudonymisation applied — PII replaced with SHA-256(PII + tenant_salt) | Logs retain full integrity; PII is pseudonymised not deleted | Compliance requirement for immutability outweighs erasure right for audit data; documented legal basis |
| Connector credentials | Hard delete from Vault within 24 hours of termination or DSAR | Credential access events in audit log pseudonymised | Credentials are high-risk; immediate deletion reduces breach risk |
| Data Type | Hot (OpenSearch/Redis) | Warm (Iceberg S3 Standard) | Cold (S3 Glacier) | Delete After |
| --- | --- | --- | --- | --- |
| Audit events | 90 days | 2 years | 5 years | 7 years (configurable per tenant jurisdiction) |
| Risk scores | 1 year | 3 years | — | 3 years |
| Agent inventory | Active lifetime + 90 days | 1 year | — | 1 year post-deletion |
| Policy versions | Active lifetime | Forever (compliance evidence) | — | Never (policy history = compliance evidence) |
| User sessions | 24 hours (Redis TTL) | — | — | 24 hours |
| HITL decisions | 90 days (hot) | 3 years | — | 3 years |
| Webhook delivery logs | 30 days | — | — | 30 days |
| Plan Tier | Enforcement API (RPS) | REST API (RPM) | Burst Allowance | Implementation |
| --- | --- | --- | --- | --- |
| Starter | 50 RPS | 1,000 RPM | 2x for 10s | Redis INCR per api_key per second/minute; sliding window |
| Professional | 500 RPS | 10,000 RPM | 3x for 30s | Same; higher thresholds |
| Enterprise | 5,000 RPS | 100,000 RPM | Configurable | Per-tenant Redis namespace; enterprise negotiated limits |
| Internal (Pinaka services) | Unlimited | Unlimited | — | mTLS service identity; no rate limiting between internal services |
| Token Type | Algorithm | Lifetime | Storage | Revocation |
| --- | --- | --- | --- | --- |
| Access Token (user) | RS256 JWT | 15 minutes | Client memory only (never localStorage) | Stateless; expiry enforced at API gateway; emergency revoke via JKWS invalidation |
| Refresh Token | Opaque 256-bit random | 7 days | HttpOnly Secure SameSite cookie | Stored in Redis with TTL; single-use; rotation on each use |
| API Key (service) | HMAC-SHA256 prefix + secret | No expiry (rotate on request) | Hashed (bcrypt) in PostgreSQL; never stored in plaintext | Immediate revocation via API; Redis blocklist for fast propagation |
| Agent Identity Token (AIT) | Ed25519 signed JWT | 90 days | Pinaka AIT registry (PostgreSQL) | Revocation list in Redis; checked on every gateway request; replicated <5s |
| Audit Read Token | RS256 JWT (read-only scope) | 8 hours | Client session | Short-lived; auditor workspace sessions only |
| Principle | Pinaka SDKs wrap the REST API with idiomatic language bindings, built-in retry logic, AIT management, and zero-config onboarding. SDKs are the primary integration path for agent developers. |
| --- | --- |
| SDK | Language | v1.0 Priority | Key Capabilities | Package Distribution |
| --- | --- | --- | --- | --- |
| pinaka-python | Python 3.10+ | P0 — v1.0 | AIT injection, policy check, audit emit, async support (asyncio) | PyPI: pip install pinaka-sdk |
| pinaka-go | Go 1.22+ | P0 — v1.0 | High-performance enforcement check, gRPC support, context propagation | Go Modules: go get github.com/pinaka-ai/pinaka-go |
| pinaka-node | TypeScript/Node 18+ | P1 — v1.5 | Agent developer tooling, connector SDK wrapper, policy linter | npm: npm install @pinaka-ai/sdk |
| pinaka-java | Java 17+ | P2 — v2.0 | Enterprise Java frameworks (Spring Boot, Quarkus), async Java support | Maven Central |
| pinaka-dotnet | C# .NET 8+ | P2 — v2.0 | .NET enterprise integration, Azure function support | NuGet |
| from pinaka import PinakaClient, AgentContext

# Initialize — reads PINAKA_API_KEY from environment
pinaka = PinakaClient()

# Wrap agent execution with Pinaka enforcement
with AgentContext(agent_id='fin-report-agent-001') as ctx:
    # Policy check before tool call (auto-raises PolicyDeniedError if DENY)
    ctx.check_policy(tool='spreadsheet-read', params={'file_id': 'FIN_Q1_2026'})

    # Execute the tool call
    result = spreadsheet_tool.read(file_id='FIN_Q1_2026')

    # Emit audit event (async, non-blocking)
    ctx.emit_audit(action='read', result_metadata={'rows': len(result)})

    return result

# HITL escalation handled automatically — agent waits for approval
# PolicyDeniedError raised immediately if DENY decision received |
| --- |
| Layer | Technology | Version | Rationale |
| --- | --- | --- | --- |
| API Gateway | AWS API Gateway + Kong | Kong 3.x | Rate limiting, auth, routing, WAF, observability at edge |
| Backend (Core Services) | Go 1.22+ | 1.22 | Policy Engine, Discovery, MCP Gateway, Audit Service — performance-critical |
| Backend (ML/Detection) | Python 3.12 + FastAPI | 3.12 | Investigation Engine, Risk Scorer — ML library ecosystem (scikit-learn, PyTorch) |
| Frontend (Console) | React 18 + TypeScript + Vite | React 18 | Type safety, component reuse, fast build, Storybook for design system |
| Graph Visualisation (ARM) | D3.js v7 + React | D3 v7 | Custom force-directed ARM graph; React integration for state management |
| Policy Evaluation | Open Policy Agent (OPA) | 0.65+ | CNCF-graduated; Rego language; sub-10ms cached evaluation; audit-ready |
| Workflow Orchestration | Temporal | 1.x | Durable workflows for discovery scans, multi-step remediation, scheduled compliance reports |
| Event Streaming | Apache Kafka (AWS MSK 3.x) | 3.6 | Ordered durable event bus; per-tenant topic ACLs; 7-day retention for replay |
| Primary DB | PostgreSQL 16 (AWS RDS Multi-AZ) | 16 | ACID; Row-Level Security; pg_audit; Aurora Serverless v2 auto-scaling |
| Time-Series DB | TimescaleDB 2.x (RDS extension) | 2.x | Risk score trends; native time-series compression; PostgreSQL compatible |
| Graph DB | Neo4j 5.x (AuraDB Enterprise) | 5.x | ARM graph; BFS blast-radius queries; Cypher language; AuraDB managed |
| Audit Log Format | Apache Iceberg 1.4 on S3 | 1.4 | Immutable; schema evolution; partitioned; Athena queryable; S3 Object Lock WORM |
| Audit Search | OpenSearch 2.x (AWS OpenSearch) | 2.x | Full-text audit search; NL query backend; UltraWarm for cost-efficient history |
| Cache | Redis 7.x Cluster (ElastiCache) | 7.x | Policy bundle cache; AIT cache; rate limit counters; HITL session state |
| Connection Pooling | PgBouncer (Kubernetes sidecar) | 1.22.x | Transaction-mode pooling; prevents connection exhaustion on PostgreSQL |
| Secrets | HashiCorp Vault 1.17 + AWS Secrets Manager | Vault 1.17 | HSM-backed; BYOK; 90-day auto-rotation; audit trail; KMS integration |
| Container Orchestration | Kubernetes (EKS 1.30+) | 1.30+ | Service scaling; rolling deploys; Helm charts per service; PodDisruptionBudgets |
| Service Mesh | Istio 1.22 | 1.22 | mTLS between all internal services; traffic policies; distributed tracing injection |
| CI/CD | GitHub Actions + ArgoCD | ArgoCD 2.x | GitOps; PR-required for all changes; environment promotion pipeline |
| IaC | Terraform 1.8 + Helm | TF 1.8 | Reproducible; multi-region; environment parity; Atlantis for PR-based plan/apply |
| Feature Flags | LaunchDarkly | Current | Gradual feature rollout; kill switches; A/B testing; SDK for all languages |
| Observability | OpenTelemetry + Datadog | OTEL 1.x | Distributed tracing; metrics; logs; SLO monitoring; APM |
| Chaos Engineering | Chaos Monkey + Gremlin | Current | Scheduled chaos experiments; latency injection; node termination testing |
| SAST | Semgrep | Current | In CI pipeline; custom rules for Pinaka-specific security patterns; blocks on critical |
| Container Scanning | Trivy | Current | Image scanning in CI + runtime (Aqua Security operator) |
| LLM (NL Query + Narratives) | AWS Bedrock (Claude Sonnet) | Current | Privacy-preserving; data stays within AWS boundary; no external API call with customer data |
| Flag Type | Purpose | Example | Owner | Config Source |
| --- | --- | --- | --- | --- |
| Release Flag | Ship incomplete feature safely; turn on for internal users first | new_arm_visualisation_v2 | Engineering | LaunchDarkly |
| Kill Switch | Immediately disable a feature if it causes production issues | mcp_gateway_inline_mode | SRE | LaunchDarkly + local fallback in code |
| Experiment Flag | A/B test UI changes or algorithm variations | risk_scoring_model_v2_vs_v1 | Product | LaunchDarkly |
| Tenant Flag | Enable feature for specific enterprise tenants on early access | red_team_agent_beta | Product | LaunchDarkly (tenant segment) |
| Ops Flag | Infrastructure behaviour toggle (e.g., switch DB read replica) | use_read_replica_for_risk_scores | SRE | LaunchDarkly + Kubernetes ConfigMap |
| Principle | Every service ships with three observability pillars (metrics, traces, logs) from Day 1. No service merges to main without SLO definition. Error budgets drive engineering prioritisation. |
| --- | --- |
| Service | SLI (Measurement) | SLO Target | Error Budget (30d) | Alert Threshold |
| --- | --- | --- | --- | --- |
| Policy Enforcement API | % of enforcement decisions returned in <500ms | 99.5% | 216 min of violations | Alert at 50% budget consumed (108 min) |
| MCP Gateway (Inline) | % of MCP requests processed in <100ms additional latency | 99.9% | 43.2 min | Alert at 50% budget consumed |
| Discovery Engine | % of scheduled scans completing within 2x expected duration | 99% | 432 min of overrun | Alert at 25% budget consumed (108 min) |
| Audit Write Service | % of events signed and persisted in <500ms | 99.9% | 43.2 min | Alert at 25% budget consumed |
| HITL Notification Delivery | % of HITL notifications delivered within 30s of trigger | 99.5% | 216 min | Alert at 10% budget consumed — HITL is human safety |
| Console API (REST) | % of API requests returning <200ms | 99.5% | 216 min | Alert at 50% budget consumed |
| Compliance Report Generation | % of reports generated within 5 min of request | 99% | 432 min | Alert at 75% budget consumed — batch, lower priority |
| Metric | Description | Alert Condition |
| --- | --- | --- |
| agents_discovered_total | Total agents in inventory per tenant | Sudden drop >20% in 1 hour — possible connector failure |
| policy_decisions_per_second | Enforcement decisions per second per tenant | Spike >5x baseline — possible agent runaway or attack |
| deny_rate | % of enforcement decisions that are DENY | Spike >50% above baseline — possible policy misconfiguration or attack |
| hitl_pending_count | Number of HITL approvals awaiting human action | >10 pending for >5 min — HITL backlog; notify approver escalation |
| risk_score_critical_agents | Count of agents with CRITICAL risk score (80–100) | Any agent crosses 80 for >5 min — immediate Slack alert |
| compliance_gap_count | Number of active compliance control failures per framework | Any critical control failure — PagerDuty alert |
| Metric | Source | Alert Threshold |
| --- | --- | --- |
| http_request_duration_seconds (p99) | Prometheus histogram per service | Alert if p99 > 2× SLO target for >5 min |
| kafka_consumer_lag | MSK CloudWatch metric per consumer group | Alert if lag > 10,000 events and growing |
| postgresql_active_connections | pg_stat_activity | Alert if connections > 80% of pool max |
| redis_memory_usage_percent | ElastiCache CloudWatch | Alert if >80%; eviction policy kicks in at 90% |
| iceberg_write_duration_ms | Custom metric from Audit Service | Alert if p99 write >1000ms |
| neo4j_graph_query_duration_ms | Neo4j monitoring API | Alert if BFS query >5s — blast radius calculation degraded |
| s3_put_errors | S3 CloudWatch metrics | Alert on any S3 PutObject error for audit log bucket — critical |
| # All Pinaka service logs MUST include these fields (JSON format):
{
  "level":       "INFO | WARN | ERROR | DEBUG",
  "timestamp":   "RFC3339 UTC",
  "service":     "policy-engine",
  "trace_id":    "W3C trace ID (from OpenTelemetry context)",
  "span_id":     "W3C span ID",
  "tenant_id":   "ten_abc123 (REQUIRED for all tenant operations)",
  "agent_id":    "agt_xyz456 (if applicable)",
  "event":       "policy_decision_made",
  "duration_ms": 12,
  "message":     "Human-readable description of the event",
  "error":       "Error message if level=ERROR (stack trace omitted from logs — use trace)",
  "fields":      { "additional": "context", "specific": "to this event type" }
} |
| --- |
| ⚠ | NEVER log: raw prompt text, response content, API keys, passwords, PII in plaintext. Log entity IDs and classification tags only. Violations caught by Semgrep rule PNK-LOG-001. |
| --- | --- |
| Alert Name | Severity | On-Call Response | Runbook Link |
| --- | --- | --- | --- |
| PinakaEnforcementLatencyHigh | P2 — Warning | Investigate: policy bundle cache miss? OPA evaluation spike? Connector slow? | runbooks/enforcement-latency.md |
| PinakaAuditWriteFailure | P1 — Critical | Investigate immediately: S3 unreachable? Iceberg writer down? Data loss risk | runbooks/audit-write-failure.md |
| PinakaHITLBacklogHigh | P2 — Warning | Notify approver team; check notification delivery; escalate if no action in 5 min | runbooks/hitl-backlog.md |
| PinakaKafkaConsumerLagHigh | P2 — Warning | Check consumer group health; scale consumer pods; check for poison pill events | runbooks/kafka-lag.md |
| PinakaAgentRiskCritical | P3 — Info | Security team review; HITL auto-triggered; no on-call action unless breach confirmed | runbooks/critical-risk-agent.md |
| PinakaDiscoveryConnectorDown | P3 — Warning | Check connector health; credential rotation due? Source API outage? | runbooks/connector-health.md |
| PinakaMCPGatewayDown | P1 — Critical | MCP enforcement offline; agents unprotected; escalate to engineering lead immediately | runbooks/mcp-gateway-outage.md |
| Pattern | Applied To | Implementation | Fail Behaviour |
| --- | --- | --- | --- |
| Circuit Breaker | All external calls (connector APIs, LLM calls, external webhooks) | Resilience4j (Java) / Go circuit breaker library; trips at 50% error rate over 60s | Open circuit: return cached result or safe default; log circuit_open event |
| Retry with Exponential Backoff | Connector API calls, webhook delivery, Kafka produce | 3 retries; base 1s; max 30s; jitter ±20% | After 3 retries: move to DLQ; emit retry_exhausted event |
| Dead Letter Queue (DLQ) | Kafka consumers: enforcement events, audit events, discovery events | Separate Kafka topic per consumer group (pinaka.dlq.{consumer_group}) | DLQ monitor alerts ops; manual replay via ops API after root cause fix |
| Bulkhead | Policy Engine evaluation — isolate tenant workloads | Dedicated thread pool per tenant tier (Enterprise tenants = isolated pool) | Noisy-neighbour tenant cannot exhaust Enterprise tenant's enforcement capacity |
| Timeout | All synchronous service calls | gRPC deadline propagation; HTTP client timeout = 3s (enforcement), 30s (background) | Timeout = DENY for enforcement path (Fail Secure P11); log timeout_exceeded |
| Fallback | Policy decision on OPA failure | If OPA unreachable: apply tenant's failsafe policy (configurable: DENY_ALL or ALLOW_ALL) | Failsafe applied; tenant notified; PagerDuty P1 if OPA down >60s |
| Rate Limiting | MCP Gateway, REST API | Token bucket in Redis; per-agent per-tool limits in MCP Gateway | HTTP 429 with Retry-After; enforcement: THROTTLE decision logged |
| Graceful Degradation | Discovery Engine scan failure | Partial scan results accepted; stale inventory marked with freshness_warning | Console shows last-known-good inventory with warning banner; full rescan triggered when source recovers |
| Health Checks — Liveness | All Kubernetes pods | /healthz endpoint; returns 200 if process is alive; fails → pod restart | Kubernetes restarts pod within 30s of liveness failure |
| Health Checks — Readiness | All Kubernetes pods | /readyz endpoint; checks DB connectivity, Kafka connectivity, OPA bundle loaded; fails → pod removed from load balancer | Pod not sent traffic until fully ready; zero-downtime rolling deploys |
| Experiment | Frequency | Tool | Success Criteria | Runbook on Failure |
| --- | --- | --- | --- | --- |
| Random pod termination (Policy Engine) | Weekly — automated | Chaos Monkey | p99 enforcement latency stays <1s; no customer-visible errors | runbooks/policy-engine-pod-fail.md |
| Kafka broker outage (1 of 3 brokers) | Monthly — scheduled maintenance window | MSK maintenance + manual partition leadership change | Kafka auto-rebalances in <30s; consumer lag recovers in <5 min | runbooks/kafka-broker-outage.md |
| PostgreSQL read replica failure | Monthly | RDS failover test | Primary continues serving; writes unaffected; read queries fail over to primary within 30s | runbooks/postgres-replica-fail.md |
| Network latency injection (200ms) to OPA | Bi-weekly | Gremlin | Enforcement API p99 stays below 700ms (policy bundle cache absorbs latency) | runbooks/opa-latency.md |
| S3 unreachable for audit writes | Quarterly | IAM deny rule injection | Audit writer switches to local durable buffer; alert fires within 60s; data persisted after S3 recovers | runbooks/audit-s3-unreachable.md |
| MCP Gateway restart under load | Weekly — automated | Kubernetes delete pod (during load test) | MCP traffic rerouted to healthy pod in <5s via Kubernetes service | runbooks/mcp-gateway-restart.md |
| AIT revocation propagation test | Monthly | Revoke an AIT; measure time until gateway rejects it | Gateway rejects revoked AIT within 5s of revocation | runbooks/ait-revocation-latency.md |
| Stage | Trigger | Steps | Gate Criteria | Duration Target |
| --- | --- | --- | --- | --- |
| PR Checks | Every pull request | Unit tests, SAST (Semgrep), OPA lint, OpenAPI diff check, dependency audit (Dependabot) | All checks pass; no critical Semgrep findings; OpenAPI is backwards-compatible | <10 min |
| Integration Tests | PR approved + all checks pass | Docker Compose integration environment; API contract tests (Pact); database migration dry-run | All integration tests pass; Pact contracts verified | <20 min |
| Build & Push | Merge to main | Build Docker images; Trivy image scan; SBOM generation; push to ECR | No critical CVEs in image; SBOM signed and stored | <15 min |
| Deploy to Dev | Merge to main (automatic) | ArgoCD sync to dev cluster; smoke tests; trace sampling verification | Smoke tests pass; service returns 200 on /healthz and /readyz | <10 min after build |
| Load Test | Nightly (on dev environment) | k6 load test: 1000 RPS on enforcement API for 10 min; 500 RPS on REST API for 10 min | p99 latency within SLO; error rate <0.1%; no OOM or pod restarts | <30 min |
| Deploy to Staging | Manual promotion (Engineering Lead) | ArgoCD sync to staging; full test suite; chaos experiment; security scan (Burp Suite) | All staging tests pass; chaos experiments recover within SLA; no new security findings | <60 min |
| Production Deploy | Manual approval (2 of: CTO, Eng Lead, SRE Lead) | ArgoCD progressive rollout: 5% → 25% → 100%; canary analysis; automated rollback on SLO breach | Canary SLO maintained for 15 min before next step; error budget not consumed >5% | <90 min |
| Test Type | Coverage Target | Framework | Run Frequency | Ownership |
| --- | --- | --- | --- | --- |
| Unit Tests | >85% statement coverage (>90% for Policy Engine, Audit Service) | Go: testing + testify; Python: pytest | Every PR | Developer |
| Integration Tests | All service API boundaries; all database operations; all Kafka publish/consume paths | Go: httptest; Python: pytest + Docker Compose; Pact contract tests | Every PR | Developer + QA |
| API Contract Tests | All public REST endpoints and webhook payloads | Pact (consumer-driven contract testing) | Every PR; regression on staging | Developer |
| End-to-End Tests | All critical user journeys (discovery → AISPM → policy → HITL → compliance report) | Playwright (UI); k6 (API flows) | Nightly on staging | QA |
| Performance / Load Tests | Enforcement API at 1000 RPS; REST API at 500 RPS; Kafka throughput at 50K EPS | k6 | Nightly on dev; before every major release | SRE |
| Chaos Tests | Service resilience experiments (Section 9.2) | Chaos Monkey + Gremlin | Weekly/Monthly (per experiment schedule) | SRE |
| Security Tests | OWASP Top 10; API fuzzing; SAST; dependency audit; container scanning | Semgrep (SAST); Burp Suite Enterprise (DAST); Trivy (container) | SAST on every PR; DAST on staging nightly; full pentest quarterly | Security Eng |
| OPA Unit Tests | All Rego policies | opa test | Every PR touching policy files | Security Eng |
| Migration Tests | All database migrations — forward and rollback | Flyway dry-run + custom rollback script | Every PR touching migration files | Data Eng |
| Region | AWS Region | Serves | Data Residency | Timeline |
| --- | --- | --- | --- | --- |
| Primary (US) | us-east-1 (primary) + us-west-2 (DR) | US-based enterprise customers; global default | All data in US; S3 cross-region replication to us-west-2 for DR | v1.0 launch |
| EU | eu-west-1 (Ireland) primary + eu-central-1 (Frankfurt) DR | EU-based customers; EU AI Act compliance | All EU customer data stays within EU; separate AWS account for hard isolation | v1.0 launch — required for EU AI Act compliance |
| APAC | ap-southeast-1 (Singapore) | APAC customers; data residency requirements in APAC jurisdictions | APAC data stays in APAC; separate AWS account | v1.5 — Phase 2 |
| India | ap-south-1 (Mumbai) | Indian enterprise customers; DPDPA 2023 compliance | India data stays in India per DPDPA requirements | v2.0 — Phase 3 |
| Component | US→EU Isolation | Shared? | Reason |
| --- | --- | --- | --- |
| Control Plane Services | Separate EKS cluster per region; no cross-region API calls | No | Data residency enforcement |
| Kafka | Separate MSK cluster per region; no cross-region replication for tenant data | No | Data residency; EU data cannot transit US |
| PostgreSQL / TimescaleDB | Separate RDS instance per region | No | Data residency |
| Neo4j (AuraDB) | Separate AuraDB database per region | No | Data residency |
| OpenSearch | Separate OpenSearch domain per region | No | Data residency |
| Redis | Separate ElastiCache per region | No | Data residency |
| Vault (Secrets) | Separate Vault cluster per region; per-tenant keys never replicate cross-region | No | Key sovereignty |
| Pinaka Console CDN | CloudFront global CDN serving static assets only | Yes | Static assets have no customer data |
| GitHub (Source Code) | Single global repository | Yes | Source code is not customer data; GDPR does not apply |
| Datadog Observability | Single Datadog org; telemetry anonymised before forwarding | Shared metrics/traces; logs filtered | Tenant PII stripped from logs before Datadog ingestion |
| Component | AWS Service | AZs | Scaling | Backup |
| --- | --- | --- | --- | --- |
| EKS Control Plane | EKS 1.30+ | Managed (AWS-hosted) | AWS-managed | EKS auto-recovery |
| EKS Worker Nodes | EC2 (EKS Node Group) | 3 AZs (min 1 node per AZ) | Cluster Autoscaler + HPA per service | PodDisruptionBudget; node drain on termination |
| MCP Gateway (Dedicated) | EKS Node Group (GPU-optimised for ML checks) | 3 AZs | KEDA on active MCP connections | Gateway stateless; no backup needed |
| API Gateway | AWS API Gateway + Kong | Managed | AWS auto-scaling | AWS-managed HA |
| PostgreSQL (Primary) | RDS Multi-AZ (Postgres 16) | 2 AZs (primary + standby) | Aurora Serverless v2 | Automated daily snapshots; PITR 7 days |
| PostgreSQL (Read Replicas) | RDS Read Replica | 1 per AZ | Manual scaling | Replica of primary |
| Kafka | AWS MSK (3 brokers) | 3 AZs (1 broker per AZ) | MSK Auto Scaling on storage | 7-day log retention; cross-AZ replication factor 3 |
| Redis | ElastiCache Cluster Mode | 3 AZs (6 shards) | Auto Scaling on memory | AOF persistence; automatic failover |
| S3 (Audit Logs) | S3 + Intelligent Tiering | 11-9s durability | Serverless | S3 Cross-Region Replication for DR |
| CloudFront CDN | CloudFront | Global | AWS auto-scaling | Cache-only; no customer data |
| WAF | AWS WAF v2 | Global (via CloudFront + API GW) | AWS-managed | N/A |
| Category | Control | Standard | Verified By |
| --- | --- | --- | --- |
| Node Hardening | CIS Kubernetes Benchmark hardened EKS AMI | CIS 1.9 | AWS Inspector |
| Pod Security | Pod Security Standards: Restricted profile cluster-wide | Kubernetes PSA | OPA Gatekeeper policy |
| Network | Default-deny NetworkPolicy; explicit allow per service pair | Istio + Kubernetes NetworkPolicy | Istio telemetry |
| Service Identity | mTLS enforced by Istio between all internal services | Istio mutual TLS | Istio Kiali mesh view |
| IAM | IRSA — no long-lived AWS credentials in pods | AWS best practice | AWS Access Analyzer |
| Secrets | Zero secrets in environment variables or config maps; all from Vault | Vault + Kubernetes External Secrets Operator | Semgrep rule PNK-SEC-001 (no hardcoded secrets) |
| Image Security | Trivy scan in CI; critical CVE blocks deployment; base image updated weekly | NIST SP 800-190 | CI gate + ECR scan |
| Supply Chain | SBOM generated and signed (Sigstore/Cosign) for every release image | SLSA Level 2 | Cosign verify in deploy pipeline |
| Runtime Security | Falco kernel-level anomaly detection on all EKS nodes | CIS Docker Benchmark | Falco alert to Datadog |
| API Security | WAF with OWASP Core Rule Set; rate limiting; bot protection | OWASP API Security Top 10 | AWS WAF + API Gateway metrics |
| Dependency Management | Dependabot for all repos; SAST via Semgrep; license scanning | NIST SP 800-218 | GitHub Dependabot + Semgrep |
| Penetration Testing | External pentest quarterly; internal red team annually | CREST/OSCP certified firm | Pentest report + remediation tracking |
| Component | Backup Method | Frequency | Retention | Recovery Test |
| --- | --- | --- | --- | --- |
| PostgreSQL | RDS automated snapshots + PITR | Continuous PITR; daily snapshot | 7 days snapshots; 35 days PITR | Monthly restore drill to staging |
| Kafka | Cross-AZ replication factor 3 + MirrorMaker 2 to DR region | Real-time replication | 7-day log retention | Quarterly DR failover test |
| Iceberg Audit Logs | S3 versioning + S3 CRR to DR region | Real-time CRR; S3 Object Lock | 7 years (WORM) | Quarterly restore test |
| Neo4j | AuraDB automated backup | Daily | 7 days | Monthly restore drill |
| Vault | Vault auto-snapshots to S3 + Vault DR replication | Hourly snapshot; real-time Vault DR | 30 days | Monthly DR failover test |
| Redis | AOF persistence + ElastiCache automated backup | Daily backup; AOF every 1s | 7 days | Quarterly restore test |
| Threat | Attack Vector | Mitigation | Residual Risk |
| --- | --- | --- | --- |
| Spoofing | Attacker impersonates agent using stolen AIT to gain permissive policy treatment | Ed25519 AIT signature verification; fingerprint check; 90-day expiry; real-time revocation list in Redis | Low — attacker must steal valid AIT AND match deployment fingerprint |
| Spoofing | Attacker spoofs Pinaka connector to inject false agent inventory | mTLS between Pinaka services + connector; connector credentials rotated every 90 days in Vault | Low |
| Tampering | Attacker modifies audit logs to conceal agent misbehaviour | Append-only Iceberg; S3 Object Lock WORM; Ed25519 hash chain; CloudTrail monitors S3 access | Very Low — WORM + hash chain make undetected tampering computationally infeasible |
| Tampering | Attacker injects malicious policy through policy change workflow | Policy change requires PR + peer review + admin MFA + 24h shadow mode + ArgoCD deployment | Low — multi-party approval chain |
| Repudiation | Agent action disputed with no chain of evidence | Every event signed before acknowledgement; audit log is system of record; non-repudiable via Ed25519 chain | Negligible — hash chain is mathematically non-repudiable |
| Information Disclosure | Cross-tenant data leak via Pinaka API | RLS at DB; Kafka ACLs; per-tenant encryption keys; JWT tenant claim verified at API gateway; quarterly tenant isolation pen test | Low — defence in depth |
| Information Disclosure | LLM NL query exposes one tenant's data to another via shared model context | LLM calls are stateless; each call contains only the requesting tenant's data; no cross-tenant context in prompts | Very Low — stateless LLM; tenant data sanitised before prompt |
| DoS | Agent floods MCP Gateway with high-volume tool calls to degrade enforcement | Per-agent per-tool rate limiting in Redis; Kubernetes HPA scales MCP Gateway pods; WAF rate limiting at edge | Low — layered rate limiting |
| DoS | Attacker triggers massive HITL escalation queue to overwhelm approvers | HITL backlog alert; auto-DENY after timeout; PagerDuty escalation; rate limit ESCALATE decisions per agent | Medium — social engineering risk; mitigated by auto-DENY timeout |
| Elevation of Privilege | Low-privilege API key used to access admin endpoints | RBAC enforced at API gateway; JWT role claims verified per endpoint; admin endpoints require MFA + IP allowlist | Low |
| Scope | This section covers incidents where Pinaka itself is compromised — not incidents in customer environments that Pinaka detects. Pinaka must be able to respond to its own security incidents with the same rigour it provides to customers. |
| --- | --- |
| Phase | Steps | Owner | SLA | Communication |
| --- | --- | --- | --- | --- |
| Detection | Automated: Falco runtime alert, WAF anomaly, Datadog SLO burn. Manual: user report, pentest finding | SRE (primary), Security Officer (secondary) | Alert → investigation start <15 min | Internal Slack #security-incidents channel |
| Containment | Isolate affected service (kill switch or Kubernetes cordon); revoke compromised credentials in Vault; block suspicious IPs in WAF | SRE + Security Engineer | <30 min from detection | Status page: investigating; do NOT disclose details externally yet |
| Eradication | Root cause identified; malicious code or configuration removed; affected systems rebuilt from clean images; all secrets rotated | Security Engineer + Engineering Lead | <4 hours from containment | Internal update; legal review if data breach likely |
| Notification (if data breach) | Pinaka legal counsel engaged; assess GDPR 72-hour notification requirement; notify affected tenants | CEO + Legal Counsel + Security Officer | Within 72 hours of breach discovery (GDPR Art.33) | Formal written notification to tenants and regulators |
| Recovery | Restore from clean backups; validate audit log chain integrity; verify no residual compromise; restore services gradually | SRE + Security Engineer | <RTO (4 hours for v1.0) | Status page updated to resolved; tenant communication |
| Post-Incident Review | Blameless PIR within 48 hours; root cause documented; runbook updated; compensating control added; chaos experiment to simulate | Engineering Lead + Security Officer | PIR within 48 hours | PIR report to CTO + Board |
| Evidence Preservation | All logs, traces, and forensic artefacts preserved for 90 days minimum; legal hold applied if litigation possible | Security Officer | Immediately on detection | Do not delete any logs during or after incident |
| Control | Description | Tooling | Frequency |
| --- | --- | --- | --- |
| SBOM Generation | Software Bill of Materials generated for every release image | Syft (SBOM generator); Cosign (signature) | Every release build |
| Dependency Audit | All direct and transitive dependencies scanned for known CVEs | Dependabot (automated PRs); Trivy (SBOM scan) | Daily + every PR |
| License Compliance | All dependencies must have OSI-approved licence compatible with Pinaka's commercial licence | FOSSA (licence scanning) | Every PR + monthly audit |
| Pinned Dependencies | All external dependencies pinned to exact versions in lock files (go.sum, requirements.txt, package-lock.json) | go mod tidy; pip-compile; npm ci | Every PR — lock file change = additional review |
| Private Registry | All internal Docker images and packages hosted in private ECR/CodeArtifact — never pull from public registries in production | AWS ECR; AWS CodeArtifact; mirrored public packages | Production deploy policy |
| Third-Party Code Review | Any new third-party library requires security review for libraries with >1000 lines of C/C++ or handling cryptography | Manual security review; Snyk SCA | PR-level gate for new dependencies |
| Signing Verification | Cosign signature verified before any image is deployed to any environment | Cosign + Kubernetes admission controller (Connaisseur) | Every Kubernetes pod startup |
| Purpose | The Connector SDK is the interface contract between Pinaka and all source systems. Any connector that implements the SDK correctly will work with Pinaka's Discovery, AISPM, and Enforcement services. |
| --- | --- |
| # pinaka_sdk/connector.py — Connector ABC
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Optional

@dataclass
class AgentRecord:
    agent_id: str            # Globally unique (within source system)
    agent_name: str
    agent_type: str          # e.g., 'LangChain/OpenAI', 'AWS Bedrock Agent'
    owner_email: str
    framework: str
    tools: list[ToolRecord]  # List of tools this agent can call
    data_sources: list[DataSourceRecord]
    deployed_at: datetime
    last_active: Optional[datetime]
    fingerprint: str         # SHA-256 of config + code hash

class PinakaConnector(ABC):
    @abstractmethod
    async def connect(self, credentials: dict) -> None: ...
    @abstractmethod
    async def discover(self) -> list[AgentRecord]: ...
    @abstractmethod
    async def stream_events(self) -> AsyncIterator[AgentEvent]: ...
    @abstractmethod
    async def health_check(self) -> ConnectorHealth: ...
    @abstractmethod
    async def disconnect(self) -> None: ... |
| --- |
| System | Integration Type | Events Sent | Bidirectional? | Setup Complexity |
| --- | --- | --- | --- | --- |
| Splunk | HTTP Event Collector (HEC) push | DENY decisions, CRITICAL risk alerts, compliance failures | No (Pinaka → Splunk only; v1.5 bidirectional) | Low — webhook configuration only |
| Microsoft Sentinel | Azure Logic Apps custom connector | All policy decisions (configurable filter); HITL events | v1.5: Sentinel alert → Pinaka HITL deny | Medium — Logic App deployment required |
| CrowdStrike Falcon | Falcon Data Replicator + Falcon API | Agent risk scores, investigation findings, IOC matches | v1.5: CrowdStrike IOC → Pinaka threat intel | Medium — CrowdStrike API credentials + SIEM mapping |
| PagerDuty | PagerDuty Events API v2 | HITL T3/T4 escalations, SLO breaches, connector health failures | Yes (PD ack → Pinaka HITL approve) | Low — API key + event routing |
| Jira | Jira REST API | Remediation tasks for CRITICAL risk agents; compliance gap tickets | Yes (Jira status change → Pinaka remediation status) | Medium — Jira project + workflow configuration |
| ServiceNow | ServiceNow REST API + MID Server | Risk score changes → ServiceNow tickets; policy violations → ITSM incidents | Yes (ServiceNow resolution → Pinaka investigation close) | High — ServiceNow admin access required for MID Server |
| Tier | Agent Count | Events/Day | Policy Decisions/Day | Recommended Pinaka Config | Estimated AWS Cost/Month |
| --- | --- | --- | --- | --- | --- |
| Starter (SMB) | 1–25 agents | 50K–500K | 50K–500K | EKS: 3 nodes (t3.large); RDS: db.t3.medium; MSK: kafka.t3.small | ~$800/month (Pinaka infra share) |
| Professional | 25–200 agents | 500K–5M | 500K–5M | EKS: 5 nodes (m5.xlarge); RDS: db.r5.large; MSK: kafka.m5.large | ~$3,500/month |
| Enterprise | 200–2,000 agents | 5M–50M | 5M–50M | EKS: 10–20 nodes (m5.2xlarge); RDS: Aurora Serverless v2; MSK: kafka.m5.4xlarge | ~$15,000–30,000/month |
| Enterprise+ | 2,000+ agents | 50M+ | 50M+ | EKS: 30+ nodes with dedicated pools; Aurora Global Database; MSK: dedicated brokers | Custom — quote required |
| Service | Component | Estimated Cost | Optimisation Lever |
| --- | --- | --- | --- |
| EKS | Cluster + 10 worker nodes (m5.xlarge On-Demand) | ~$2,800 | Savings Plans for baseline; Spot for non-critical batch jobs |
| RDS | PostgreSQL Multi-AZ (db.r5.2xlarge) + 2 read replicas | ~$1,600 | Aurora Serverless v2 for dev/staging (80% cheaper) |
| MSK | 3-broker Kafka cluster (kafka.m5.2xlarge) | ~$900 | Start with kafka.m5.large; scale as needed |
| ElastiCache | Redis Cluster Mode (6 nodes, cache.m6g.large) | ~$800 | cache.t3.medium for dev/staging |
| RDS (TimescaleDB) | db.r5.xlarge | ~$600 | TimescaleDB compression (up to 95% reduction on historical data) |
| AuraDB (Neo4j) | AuraDB Enterprise (smallest tier) | ~$600 | AuraDB Professional for dev; Enterprise only for prod |
| OpenSearch | 3-node cluster (m6g.large.search) + UltraWarm | ~$700 | UltraWarm reduces cost of historical index by 70% |
| S3 (Audit Logs) | 50TB standard; 500TB Intelligent Tiering | ~$1,200 | Intelligent Tiering auto-moves to cheaper storage tiers |
| CloudFront | CDN for console static assets | ~$200 | Mostly free tier; small cost for global distribution |
| AWS API Gateway + WAF | API Gateway + WAF standard + managed rules | ~$400 | WAF managed rules reduce custom rule maintenance |
| DataTransfer | Cross-AZ + egress | ~$500 | VPC Endpoints reduce NAT Gateway cost |
| Datadog | APM + Logs (100GB/day) | ~$2,500 | Log sampling for non-error logs reduces cost 60% |
| LaunchDarkly | Feature flags (team plan) | ~$300 | — |
| HashiCorp Vault | HCP Vault (Starter) | ~$400 | — |
| TOTAL ESTIMATE | All components (US primary region) | ~$13,500/month | Target <$10K with Savings Plans + Spot; EU region adds ~$10K |
| Goal | From enterprise signup to 'first risk finding visible in console' in under 4 hours. The onboarding experience is itself a product — it must be opinionated, fast, and feel like Pinaka already knows their environment. |
| --- | --- |
| Step | User Action | Pinaka Action | Duration Target | Success Signal |
| --- | --- | --- | --- | --- |
| 1. Account Creation | Admin signs up with SSO (Okta/Azure AD/Google Workspace) | Pinaka creates tenant; provisions EU or US region based on IP/declared jurisdiction; creates admin user; generates tenant encryption key in Vault | <5 min | Admin logged into Pinaka Console |
| 2. Connector Setup | Admin clicks 'Connect AWS Bedrock' (or other connector) | OAuth flow or API key entry; Pinaka tests connectivity; stores credential in Vault; creates connector health check job | <10 min per connector | Connector status: HEALTHY |
| 3. Initial Discovery Scan | Pinaka auto-triggers scan immediately after first connector connects | Discovery Engine scans all agents; builds initial inventory; assigns preliminary AISPM scores using default risk model; builds initial ARM | <2 hours for 50 agents | 'X agents discovered' banner in console |
| 4. First Risk Finding | Discovery scan completes | Risk Engine calculates initial scores; top 3 highest-risk agents highlighted with business-context narrative; recommended actions shown | Automatic after step 3 | Console shows 'Here are your top 3 risk findings' |
| 5. Policy Activation | Admin reviews default policies and activates one | Policy Engine loads tenant policy bundle; dry-run shows what would have been denied in last 24 hours of scan data | <15 min | First policy active; dry-run report visible |
| 6. HITL Channel Setup | Admin connects Slack or Teams | Notification Service configures bot; sends test HITL message; admin approves test | <5 min | Test HITL notification received and approved |
| 7. Compliance Framework | Admin selects applicable frameworks (EU AI Act, SOC 2, etc.) | Compliance Engine maps existing data to framework; shows initial compliance posture; identifies top 3 gaps | <15 min | Compliance dashboard populated |
| 8. First Report | Admin generates first compliance or risk report | Compliance Engine generates PDF; emails to admin; also available in console | <5 min | PDF report delivered to admin email |
| Milestone | Target | Measurement | Alert if Exceeded |
| --- | --- | --- | --- |
| First connector connected | <10 min from signup | Connector created_at - account created_at | >30 min — onboarding funnel alert |
| First agent discovered | <2 hours from first connector | First agent inventory record - connector created_at | 72 hours — customer success outreach |
| First risk finding visible | <2 hours from connector | First risk score record - connector created_at | 72 hours — customer success outreach |
| First HITL notification delivered | <30 min from HITL setup | HITL notification delivered_at - HITL setup completed_at | 60 min — CS + SRE investigate |
| First compliance report generated | <5 min from request | Report delivered_at - report requested_at | 15 min — investigate Compliance Engine |
| Trial to paid conversion | <14 days from signup | CRM tracking (HubSpot) | Track cohort; not a system alert |
| # | Feature | Team | Dependencies | Weeks | Entry Criteria | Exit Criteria |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | AI Asset Discovery + Inventory | Platform | Connector SDK scaffold | 8–10 | Connector SDK scaffolded | 10 P0 connectors live; discovery <2hr; inventory API <200ms; AIT issuance working |
| 2 | AISPM + Agentic Risk Map | Security | Discovery (1) | 10–12 | Inventory API live | 5-dimension scores for all agents; ARM rendered; score updates <30s on event |
| 3 | Policy Engine + OPA | Security | — | 10–14 | OPA integrated; Policy schema defined | Policy CRUD; <500ms p99 decisions; dry-run mode; policy change workflow enforced |
| 4 | MCP Security Gateway | Platform | Policy Engine (3) | 8–10 | Policy Engine live | Inline proxy mode; 8 security checks; <50ms added latency; AIT verification |
| 5 | Audit + Explainability | Data | Kafka | 4–6 | Kafka operational | Ed25519 hash chain; NL query <3s; S3 Object Lock configured |
| 6 | HITL Service + Notifications | Product | Audit (5) | 4–6 | Audit live | 4 HITL tiers; Slack + Teams + Email + PagerDuty; webhook delivery guarantees; HMAC signing |
| 7 | Compliance Engine | Compliance | Audit + Policy | 5–8 | Policy + Audit live | EU AI Act + NIST AI RMF + OWASP LLM10 reports; continuous posture dashboard |
| 8 | Investigation Engine | Security | AISPM + Audit | 10–14 | AISPM + Audit live | Behavioural baseline; 5 detection methods; business-context narrative; cross-agent detection |
| 9 | Agent Identity Attestation | Platform | Discovery (1) | 4–6 | Connector SDK live | AIT issuance; Ed25519 signing; fingerprint verification; revocation list in Redis |
| 10 | Onboarding Flow (Day 1 Value) | Product | Features 1–5 | 4–6 | Features 1–5 stable | First risk finding visible <4hr from connector setup; onboarding metrics instrumented |
| # | Feature | Weeks | Key Architecture Addition | Business Value |
| --- | --- | --- | --- | --- |
| 11 | Automated AI Red Teaming | 12–16 | Red Team Agent service; attack library; findings → AISPM feedback loop | Converts skeptics to buyers; proves real risk to board |
| 12 | Auto-Remediation of Agent Misconfigs | 10–12 | Remediation Workflow (Temporal); permission revocation API per connector | Moves Pinaka from 'alert generator' to 'problem solver' |
| 13 | SIEM/SOAR Integration Suite | 6–8 | Webhook engine upgrade; native Splunk/Sentinel/CrowdStrike connectors; bidirectional | Required for enterprise SOC team adoption |
| 14 | Connector Library Expansion | Ongoing | Connector SDK OSS + partner programme; 40+ connectors target | Each connector = new addressable customer segment |
| 15 | VPC Deployment Option | 8–10 | Helm chart refactoring; Terraform customer-VPC module; private link | Opens regulated and government segment |
| 16 | Python SDK GA + Node SDK | 6–8 | Full SDK for Python (GA) + TypeScript/Node (beta) | Agent developer adoption — shifts Pinaka from security tool to developer platform |
| 17 | Multi-Region Self-Service | 4–6 | Tenant region selection at signup; automated provisioning per region | Self-serve EU data residency without Pinaka ops intervention |
| 18 | Response Speed <100ms | 4–6 | Policy bundle edge caching; gRPC enforcement path; latency SLO monitoring | Removes 'performance impact' objection in enterprise POCs |
| # | Feature | Strategic Bet | New TAM |
| --- | --- | --- | --- |
| 19 | MSSP / Multi-Tenant Architecture | Channel distribution — MSSP resells Pinaka to clients; exponential reach multiplier | $50M+ MSSP market for AI agent security services |
| 20 | AI Agent Marketplace Monitoring | Shadow agent detection from GPT Store, Claude integrations, AppSource — 2026's shadow IT | First mover in public marketplace security — untapped category |
| 21 | Cross-Agent Threat Hunting | Detect coordinated misbehaviour ('Agent Collusion') — Pinaka defines the new attack category | Advanced enterprise + government — premium tier pricing |
| 22 | DevSecOps Shift-Left (Snyk for AI Agents) | GitHub/GitLab CI plugin; policy-as-code in YAML; security gate at PR level — shift left AI agent security | Developer platform TAM — 10x larger than security team TAM |
| Team | Services Owned | Stack | MVP Headcount | Hiring Priority (post-seed) |
| --- | --- | --- | --- | --- |
| Platform Engineering | Discovery Engine, Connector SDK, MCP Gateway, API Gateway, IaC, EKS | Go, Terraform, Kubernetes, Kafka, Istio | 4 engineers | SWE3 (Go) specialising in distributed systems |
| Security Engineering | AISPM Engine, Policy Engine (OPA), Investigation Engine, Threat Intelligence, AIT Protocol | Go, Python, OPA/Rego, Neo4j | 3 engineers | Security SWE with Go + OPA experience; ML background a plus |
| Data Engineering | Audit Service, Compliance Engine, Data pipeline, Risk Scorer, TimescaleDB, Iceberg | Python, Apache Iceberg, Kafka, TimescaleDB, Spark | 3 engineers | Data SWE with streaming (Kafka) + Iceberg experience |
| Product Engineering | HITL Service, Notification Service, Console Frontend, Onboarding Flow, SDK | TypeScript, React, D3.js, Go | 3 engineers | Full-stack SWE; React + Go; design sensibility |
| SRE / DevOps | CI/CD, EKS, Observability, BCDR, Security Hardening, Chaos Engineering | Terraform, GitHub Actions, ArgoCD, Datadog, Falco | 2 engineers | SRE with Kubernetes + AWS + Datadog; chaos engineering experience |
| Engineering Lead / Architect | Cross-team architecture, technical decisions, API design, security review | All stacks | 1 (Founder/CTO in early stage) | — |
| Standard | Rule | Tooling | Gate |
| --- | --- | --- | --- |
| Code Review | All PRs require 2 approvals (1 from domain team, 1 from any engineer) | GitHub branch protection | Merge blocked without 2 approvals |
| Branching | Trunk-based development; feature branches <3 days; no long-lived branches | GitHub | PR age metric; stale branch alert >7 days |
| Commit Messages | Conventional Commits format: feat:, fix:, chore:, sec:, docs: | Commitlint in CI | CI fails on non-conforming commit messages |
| Documentation | All public services have README with: purpose, API, config, local dev setup, runbook link | Template enforced via repo scaffold | Architecture review checklist item |
| Secrets | Zero secrets in code, config, environment variables, or commit history | git-secrets + Semgrep + Vault | CI fails on secret detection; git history scan on every PR |
| Observability | All new endpoints and functions: structured log entry, Prometheus counter/histogram, OpenTelemetry span | OpenTelemetry SDK; Datadog | Merge checklist — observability sign-off required |
| Error Handling | All errors must be explicitly handled; no swallowed errors; error wrapping with context | Errcheck linter (Go); pylint (Python) | Linter failure blocks merge |
| Testing | New feature = unit tests + integration test; bug fix = regression test that catches the bug | Per-language test frameworks | CI requires >85% coverage; fails if coverage drops |
| API Versioning | No breaking changes to stable APIs without 12-month deprecation notice and migration guide | OpenAPI diff tool in CI | CI fails on breaking API change without version bump |
| SLO Definition | Every new service must define SLO before first deployment to staging | SLO template in Datadog | Architecture review checklist item |
| ⚠ | All decisions marked CRITICAL must be resolved before Sprint 1 begins. Deferring these decisions creates architectural debt that costs 10x to fix later. |
| --- | --- |
| # | Decision | Options | Recommendation | Impact | Owner | Deadline |
| --- | --- | --- | --- | --- | --- | --- |
| D1 | MCP Gateway: inline proxy vs out-of-band | Inline transparent proxy (100% coverage, latency risk) vs out-of-band API hook (declarative coverage, zero latency) | Start with API hook for v1.0; inline proxy as opt-in in v1.5 — reduces deployment risk and time-to-market | CRITICAL — entire MCP Gateway architecture | CTO + Arch Lead | Sprint 0, Day 3 |
| D2 | Audit log: metadata-only default vs opt-in full content | Metadata only (safer default, weaker forensics) vs opt-in full prompt/response content | Metadata-only as default; opt-in full content with admin approval + legal sign-off + GDPR DPA amendment | CRITICAL — data privacy posture and GDPR compliance | CISO + Legal + Product | Sprint 0, Day 3 |
| D3 | Multi-tenant model: schema-per-tenant vs RLS | Schema-per-tenant (strong isolation, ops complexity) vs RLS (simpler ops, requires correct app code) | RLS for v1.0 (speed to market); schema-per-tenant migration path designed now for future regulated customers | CRITICAL — impossible to change cheaply post-launch | Data Eng Lead + CTO | Sprint 0, Day 1 |
| D4 | LLM for NL query + narratives | AWS Bedrock/Claude (privacy, AWS boundary) vs self-hosted Llama3 (full control, ops burden) vs OpenAI API (capability, external call) | AWS Bedrock eu-west-1 for EU tenants, us-east-1 for US — data never leaves AWS boundary | HIGH — data privacy positioning and cost model | CTO | Sprint 0, Day 5 |
| D5 | Policy language: OPA Rego vs custom DSL | OPA Rego (industry standard, learning curve, external expertise) vs custom YAML DSL (easier UX, more to build, no external expertise) | OPA Rego — industry standard; external security engineers can contribute; Gartner-recognised | HIGH — OPA is enterprise standard; custom DSL = perpetual maintenance | Arch Lead + Security Lead | Sprint 1, Day 1 |
| D6 | AIT storage: Pinaka-issued vs enterprise IdP-federated | Pinaka-issues AITs (full control) vs enterprise IdP (Okta/Azure AD) issues tokens (enterprise trust model, more complex) | Pinaka-issued for v1.0; IdP-federation as v1.5 feature — enterprises can federate existing IdP | HIGH — affects enterprise SSO integration complexity | Platform Lead | Sprint 1 |
| D7 | Graph DB: AuraDB managed vs self-hosted Neo4j on EKS | AuraDB (less ops, higher cost ~$600/mo) vs self-managed Neo4j on EKS (full control, ops burden, SRE time cost) | AuraDB for v1.0 — SRE bandwidth better spent on core platform; re-evaluate at $1M ARR | MEDIUM — operational complexity vs cost | SRE Lead + CTO | Sprint 1 |
| D8 | Connector SDK language: Go-first vs Python-first | Go (performance, but not native for ML connectors) vs Python (ML ecosystem, slower) | Dual SDK: Go for performance-critical connectors (enforcement path); Python for discovery/analytics connectors | MEDIUM — affects connector development speed | Platform Lead | Sprint 1 |
| D9 | Onboarding: self-serve vs CSM-assisted for enterprise | Full self-serve (faster, lower cost) vs CSM-assisted (higher touch, higher conversion, required for $100K+ contracts) | Self-serve for Starter/Professional; CSM-assisted mandatory for Enterprise+ — different onboarding flows | HIGH — affects GTM cost model and conversion rates | Product + CEO | Sprint 1 |
| D10 | Pricing model: seat-based vs consumption-based vs value-based | Seat-based (predictable) vs per-agent (consumption) vs per-risk-finding-prevented (value-based) | Per-agent/month with tiered bands — aligns with enterprise scaling; simpler than consumption; validated by Noma/WitnessAI pricing | HIGH — affects sales cycle and financial model | CEO + Product | Sprint 2 |
| Document | Purpose | Lead | Inputs | Timeline |
| --- | --- | --- | --- | --- |
| Architecture Document v1.1 (this) | Platform architecture; principles; components; tech stack; NFRs; security; roadmap | Engineering Architect | CRN competitor analysis; Pinaka feature roadmap | ✅ COMPLETE |
| High Level Design (HLD) | System topology diagrams; service interaction maps; sequence diagrams for all critical paths; data flow diagrams; C4 architecture model | Engineering Lead | This document | Sprint 1–2 (Weeks 1–4) |
| UI/UX Design | Product wireframes; user journey maps; design system; ARM graph visual specification; console navigation; mobile-responsive design | Product Lead + Designer | HLD + User research interviews | Sprint 1–3 (parallel with HLD) |
| Low Level Design (LLD) — Per Service | Per-service internal design; API contracts (OpenAPI spec); DB schemas (ERD); algorithm specs; gRPC protobuf; OPA Rego policy examples | Per-service tech lead | HLD + Architecture Doc | Sprint 3–6 |
| Runbook & Operations Guide | Deployment procedures; all alert runbooks; on-call playbook; scaling procedures; chaos experiment schedule | SRE Lead | HLD + Architecture Doc | Sprint 5–6 |
| Security Architecture Review | Formal threat model review by external security firm; penetration test plan; STRIDE review sign-off | Security Officer + External Firm | Architecture Doc + LLD | Sprint 4 (before staging) |
| Term | Full Form | Definition |
| --- | --- | --- |
| AISPM | AI Security Posture Management | Continuous assessment and governance of AI agent risk, permissions, and compliance posture |
| AIT | Agent Identity Token | Pinaka-issued cryptographically signed token that uniquely identifies and authenticates an AI agent |
| ARM | Agentic Risk Map | Pinaka's interactive graph visualisation of agent dependencies, data access paths, and blast radius |
| Blast Radius | — | The maximum scope of damage (systems, data, users affected) if a specific agent is compromised or misbehaves |
| BYOK | Bring Your Own Key | Enterprise option to supply their own encryption keys for Pinaka data stores, managed via HashiCorp Vault |
| Connector | — | Pinaka's integration module that authenticates to a source AI system and reads agent metadata and events |
| DSAR | Data Subject Access Request | GDPR Art.15 right — a request by an individual to see what personal data Pinaka holds about them |
| DLQ | Dead Letter Queue | A Kafka topic that receives messages that failed delivery after all retry attempts |
| HITL | Human-in-the-Loop | A control mechanism that pauses an agent action and requires human approval before proceeding |
| HPA | Horizontal Pod Autoscaler | Kubernetes mechanism that automatically scales pod count based on CPU/RPS/custom metrics |
| Iceberg | Apache Iceberg | Open table format used by Pinaka for the immutable audit log on S3; supports ACID, schema evolution, and time travel |
| IRSA | IAM Roles for Service Accounts | AWS mechanism for Kubernetes pods to assume IAM roles without long-lived credentials |
| KEDA | Kubernetes Event-Driven Autoscaling | Kubernetes add-on that scales workloads based on external event sources (e.g., Kafka consumer lag) |
| MCP | Model Context Protocol | Open protocol by Anthropic for connecting AI models to external tools and data sources |
| mTLS | Mutual TLS | TLS where both client and server authenticate each other using certificates; enforced by Istio between Pinaka services |
| NFR | Non-Functional Requirement | Requirements for how a system performs, scales, and operates (latency, availability, security), as opposed to what it does |
| OPA | Open Policy Agent | CNCF-graduated policy engine; Pinaka uses it with Rego language for all policy evaluations |
| PIR | Post-Incident Review | Blameless review of an incident to understand root cause and prevent recurrence; Pinaka conducts PIRs within 48 hours |
| RLS | Row-Level Security | PostgreSQL feature that automatically filters rows based on current user/tenant context; Pinaka uses it for tenant isolation |
| RPO | Recovery Point Objective | Maximum acceptable data loss in a disaster scenario (measured in time) |
| RTO | Recovery Time Objective | Maximum acceptable time to restore platform service after a disaster |
| SBOM | Software Bill of Materials | Inventory of all software components in a Pinaka release; generated and signed for supply chain security |
| Shadow Agent | — | An AI agent deployed by a business unit without security team knowledge or Pinaka registration |
| SLI | Service Level Indicator | A specific measurement used to evaluate whether an SLO is being met (e.g., p99 latency) |
| SLO | Service Level Objective | A target value or range for an SLI that defines acceptable service performance |
| STRIDE | — | Threat modelling framework: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege |
| Temporal | — | Open-source durable workflow engine; Pinaka uses it for long-running Discovery scans and remediation workflows |
| WORM | Write Once Read Many | Storage configuration (S3 Object Lock) that prevents modification or deletion of audit logs |
| Zero Data Migration | — | Pinaka's architecture principle of querying customer data sources in-place; never copying raw data to Pinaka's storage |