<!-- converted from Pinaka_LLD_v1.1.docx -->




PINAKA
AGENTIC AI SECURITY PLATFORM
Low Level Design  ·  v1.1  (Comprehensive — Diagrams Integrated)




Developer Promise: Every diagram, interface, method signature, algorithm, schema, and configuration in this document can be translated directly to production code. Diagrams are annotated with latency targets, failure modes, and implementation notes.


# Table of Contents

# Part I — Architecture Overview & System Diagrams
This section provides all architectural diagrams for the Pinaka platform. These diagrams should be the first reference for any engineer before writing code. Each diagram is annotated with latency targets, failure modes, and cross-references to the detailed specifications in Parts II–V.
▸  Diagram 1 — System Context (C4 Level 1)
Fig 1.1 — Pinaka interacts with 4 external actor types: AI agents, security teams, enterprise systems, and AWS Bedrock (for privacy-preserving LLM features). Zero data migration — Pinaka reads metadata only.

▸  Diagram 2 — Container Map (C4 Level 2) — All 15 Services




Fig 1.2 — 15-service container map with namespace grouping. gRPC (blue) for enforcement path. Kafka (orange) for async events. All infrastructure is VPC-private.

▸  Diagram 12 — Service-to-Service Communication Map
Fig 12.1 — All internal service communication uses mTLS enforced by Istio. No service has a public endpoint except api-gateway and mcp-gateway (via ALB). External API calls (Slack, PagerDuty, Bedrock) use IRSA or Vault-managed credentials.

▸  Diagram 3 — MCP Gateway: 11-Stage Inspection Pipeline
Fig 3.1 — Each stage can independently abort the pipeline. Stages 1–8 run sequentially pre-forward. Stages 9–11 run post-authorization. Stage 11 (Kafka publish) is always async and never delays the response.

▸  Diagram 4 — Policy Evaluation Decision Tree
Fig 4.1 — Policy evaluation always runs L0 first (immutable). L1 DENY policies override L2/L3. When multiple policies of the same level match, most restrictive decision wins.

▸  Diagram 5 — HITL Service: 5-State Machine


Fig 5.1 — HITL state machine. Only PENDING is transient. All other states are terminal. Timer managed via Redis sorted set (score = unix timestamp); checked every 60s by Kubernetes CronJob.

▸  Diagram 6 — AISPM: Risk Score Calculation (0–100)
Fig 6.1 — Risk score recalculated on: policy violation, discovery scan, investigation finding, or manual trigger. TimescaleDB stores full history. Risk tier change → immediate Kafka event + alert.

▸  Diagram 7 — Kafka Event Architecture (AWS MSK)
Fig 7.1 — All Pinaka events are partitioned by agent_id (enforcement) or tenant_id (discovery/risk) for ordering guarantees. DLQ topics monitored by SRE — alerts fire on any DLQ depth > 0.

▸  Diagram 8 — Database Entity Relationship Diagram (PostgreSQL Core)
Fig 8.1 — Core PostgreSQL ERD. All tables enforce Row-Level Security using app.tenant_id session variable. agent_tools is the M:N join table between agents and tools.

▸  Diagram 9 — Kubernetes: 6-Namespace Architecture (EKS)
Fig 9.1 — Default-deny NetworkPolicy between namespaces. Istio mTLS enforced for all intra-cluster service calls. All pods use IRSA (no long-lived AWS credentials). PodDisruptionBudgets ensure minAvailable=2 for all critical services.

▸  Diagram 10 — CI/CD Deployment Pipeline (GitHub Actions + ArgoCD)
Fig 10.1 — Pull request triggers stages 1–2. Merge to main triggers stages 3–4. Nightly runs stage 5. Manual promotion triggers stages 6–9. All ArgoCD deploys are git-driven (GitOps).

▸  Diagram 11 — Authentication: Token Types & Lifecycle


Fig 11.1 — JWT tokens are stateless (RS256 signature verified at API Gateway). Refresh tokens are single-use; old token atomically deleted before new token issued (prevents race condition). AIT revocation propagates to all pods via Redis within 5s.


# Part II — Per-Service Low Level Designs
# 1. Document Purpose, Scope & How To Use
This Low Level Design (LLD) document is the definitive implementation blueprint for Pinaka v1.0. It expands every section of the High Level Design (v1.1) into concrete, code-ready specifications. A developer should be able to write production code directly from this document without further design decisions.

## 1.1  Document Organisation

## 1.2  LLD Notation Conventions




## 2.1  Internal Package Structure

## 2.2  Core Interfaces & Structs



## 2.3  gRPC Server Implementation

## 2.4  Error Codes

## 2.5  Configuration Reference

## 2.6  Unit Test Specifications




## 3.1  Internal Package Structure

## 3.2  Pipeline Stage Interface

## 3.3  Stage Implementations
### 3.3.1  AIT Validator (Stages 1–2)
### 3.3.2  Rate Limiter (Stage 4) — Token Bucket

## 3.4  Error Codes

## 3.5  Configuration Reference




## 4.1  Connector SDK Interface (Go)

## 4.2  AIT Issuer

## 4.3  Shadow Agent Detector

## 4.4  Error Codes

## 4.5  Configuration Reference


## 4.6  Connector Example — AWS Bedrock (P0)



## 5.1  RiskCalculator — Core Implementation

## 5.2  ARM API — Data Builder

## 5.3  Error Codes

## 5.4  Configuration Reference




## 6.1  Core Types

## 6.2  Event Consumer & Chain Writer

## 6.3  NL Query Implementation

## 6.4  Error Codes & Configuration



## 13.4  Iceberg Audit Table — Partition & File Strategy



## 7.1  Baseline Store Interface

## 7.2  Anomaly Detector Interface & Implementations

## 7.3  Configuration Reference




## 8.1  gRPC Server Methods

## 8.2  JWT Token Generation

## 8.3  WebSocket Hub for Real-Time Console Updates

## 8.4  Configuration Reference


## 8.5  WebSocket Message Type Specifications



## 9.1  HITL State Machine

## 9.2  Core Implementation

## 9.3  Configuration Reference




## 10.1  Channel Dispatcher Interface

## 10.2  Webhook Channel — HMAC Signing

## 10.3  Configuration Reference




## 11.1  Regulatory Framework Mapper

## 11.2  Report Generation (Temporal Activity)

## 11.3  Configuration Reference




## 12.1  Zustand Store Slices

## 12.2  React Query Hooks — API Integration

## 12.3  Policy Editor Component


## 11.3  Post-Setup Validation Checklist


# Part III — Schemas, Contracts & Protocols
# 13. Complete Database Schemas
## 13.1  PostgreSQL — All Tables with Indexes & RLS





## 13.2  TimescaleDB — Risk Score Hypertable

## 13.3  Neo4j — Graph Schema


# 14. Complete gRPC Protobuf Definitions
## 14.1  Policy Engine — Full proto3

## 14.2  Platform Service — Full proto3


# 15. OpenAPI 3.1 Specifications — Key Endpoints

## 15.1  Agent Inventory API

## 15.2  Audit API

## 15.3  Common Schemas


# 16. Kafka Avro Schema Definitions
## 16.1  AgentActionEvent (enforcement.agent_actions)

## 16.2  RiskScoreUpdate (risk.score_updates)
## 16.3  HITLRequestEvent (hitl.requests)
## 16.4  AgentLifecycleEvent (discovery.agent_lifecycle)


# 17. OPA Rego Policy Modules — Complete Implementation
## 17.1  Shared Module: data_classification.rego

## 17.2  Platform Baseline: baseline.rego (L0 — Immutable)

## 17.3  Tenant Evaluation Entry Point: evaluate.rego


## 17.4  OPA Rego Unit Tests — Required Test Patterns


# Part IV — Algorithms, Configuration & Testing
# 18. Algorithm Specifications
## 18.1  Risk Score Calculation — Detailed Pseudocode

## 18.2  Behavioural Baseline Update — Welford's Online Algorithm

## 18.3  Policy Conflict Resolution Algorithm


# 19. Configuration Reference — All Services
## 19.1  Shared Environment Variables (all services)

## 19.2  Database Connection Variables


## 19.3  Vault Secret Paths — Master Reference

# 20. Test Specifications
## 20.1  Unit Test Coverage Requirements

## 20.2  Critical Integration Test Scenarios

## 20.3  Contract Tests (Pact)


# 21. Security Controls Matrix
## 21.1  Per-Endpoint Security Controls


## 21.2  Complete RBAC Permissions Matrix


# Part V — Workflows, Operations & Deployment
# 22. Temporal Workflow — Detailed Specifications
## 22.1  DiscoveryScanWorkflow

## 22.2  AITExpiryWorkflow


# 23. Error Handling Implementation Patterns
## 23.1  Structured Error Wrapping (Go)

## 23.2  HTTP Error Middleware — RFC 7807


## 23.3  DLQ Replay Procedure

# 24. Deployment Checklist
## 24.1  Pre-Deploy Checklist (Staging)

## 24.2  Production Deploy Sequence


# 25. API Implementation Patterns — Full Reference
## 25.1  Cursor-Based Pagination — Complete Implementation

## 25.2  Idempotency Key — Full Implementation


# 26. Kubernetes Manifest Specifications
## 26.1  Deployment Template (policy-engine example)


# 27. Performance Testing Specifications
## 27.1  Load Test Scenarios


# 28. Istio, Schema Registry & Container Build Specifications
## 28.1  Istio Retry & Circuit Breaker per Service

## 28.2  Schema Evolution Guide

## 28.3  GitHub Actions CI Pipeline


# 29. Comprehensive LLD Glossary

Document Control: LLD v1.0 — CONFIDENTIAL — Internal Engineering Use Only. Covers ALL 29 HLD sections. Changes require Engineering Lead review and per-service tech lead sign-off. This document is the input to code review checklists — reviewers should verify implementation matches LLD specifications.
|  |
|  |
| Version | v1.1 — Diagrams integrated; all 26 gaps closed |
| Date | April 2026 |
| Classification | CONFIDENTIAL — Internal Engineering Use Only |
| Inputs | Architecture Doc v1.1  ·  HLD v1.1  ·  Gap audit (26 items) |
| Coverage | ALL 29 HLD sections  ·  12 architectural diagrams  ·  Zero omissions |
| Audience | All Engineers: Backend, Frontend, SRE, Security, QA |
| Key additions in v1.1 | 12 visual diagrams (system context, containers, MCP pipeline, policy tree, HITL state machine, risk scoring, Kafka, ERD, K8s, CI/CD, auth, service comms); Connector SDK worked example (AWS Bedrock); OPA Rego unit test patterns; RBAC matrix; Vault secret paths; Post-setup validation; DLQ replay; Iceberg partition strategy; WebSocket message specs |
| Enterprise AI Agents
(LangChain, AutoGen,
Bedrock, Copilot,
AgentForce, Custom) | MCP / REST
HTTPS | 🛡  PINAKA.AI

Agentic AI Security
Control Plane | REST /
Webhooks | Enterprise Security
Team

(CISO, SOC Analysts,
Security Engineers) | Reports /
Alerts | SIEM / SOAR
(Splunk, Sentinel,
CrowdStrike,
PagerDuty) |
| --- | --- | --- | --- | --- | --- | --- |
|  |  | ▼ |  |  |  |  |
| Enterprise Systems

(IdP/SSO, AWS, Azure,
GCP, GitHub, Jira,
Salesforce, ServiceNow) | Connectors
(read-only
API) | Pinaka Data Layer

PostgreSQL · TimescaleDB
Neo4j · Iceberg/S3
Redis · OpenSearch
Vault · Kafka | Bedrock
LLM calls
(metadata
only) | AWS Bedrock

(Claude Sonnet)
Privacy-preserving
NL query + narratives |  | Regulatory
Frameworks

EU AI Act · NIST
OWASP LLM Top 10
MITRE ATLAS · SOC2 |
| 🌐  INTERNET-FACING LAYER  (pinaka-gateway namespace) |
| --- |
| api-gateway

Kong 3.x + Go
REST/WS entry point |  | mcp-gateway

Go 1.22
11-stage MCP enforcement |
| --- | --- | --- |
| ▼ gRPC / REST |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- |
| ⚙  CORE PLATFORM LAYER  (pinaka-core namespace) |
| --- |
| policy-engine

Go 1.22 + OPA 0.65
Policy eval <10ms |  | discovery-engine

Go 1.22 + Python 3.12
Agent inventory + AIT issuance |  | temporal-workers

Go + Python
Durable workflow execution |
| --- | --- | --- | --- | --- |
| 📊  DATA LAYER  (pinaka-data namespace) |
| --- |
| aispm-engine

Python 3.12 + FastAPI
Risk scoring + ARM graph |  | audit-service

Go 1.22 + Iceberg
Immutable event chain |  | investigation-engine

Python 3.12 + sklearn
ML anomaly detection |
| --- | --- | --- | --- | --- |
| compliance-engine

Python 3.12 + Temporal
Framework mapping + reports |  | console-ui

React 18 + TypeScript + D3.js
Browser dashboard (CloudFront/S3) |
| --- | --- | --- |
| 🔐  PLATFORM LAYER  (pinaka-platform namespace) |
| --- |
| platform-service

Go 1.22
Auth · JWT · SSO · Tenancy |  | hitl-service

Go 1.22
Human approval workflows |  | notification-service

Go 1.22
Slack/Teams/PD/Email/Webhook |
| --- | --- | --- | --- | --- |
| 🗄  SHARED INFRASTRUCTURE  (pinaka-infra — VPC private) |
| --- |
| PostgreSQL 16
+ TimescaleDB |  | Redis 7
Cluster |  | Kafka
(AWS MSK) |  | Neo4j
(AuraDB) |  | OpenSearch
(AWS) |  | Vault
(Secrets) |  | Iceberg/S3
(Audit log) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FROM |  | TO | Protocol | Call / Purpose | Auth |
| --- | --- | --- | --- | --- | --- |
| mcp-gateway | ──────► | policy-engine | gRPC | EvaluateAction (enforcement — <10ms p99) | mTLS (Istio) |
| mcp-gateway | ──────► | platform-service | gRPC | ValidateAIT (every request) | mTLS |
| mcp-gateway | ──────► | Kafka | Kafka | Publish: enforcement.agent_actions (async, post-decision) | SASL/TLS IRSA |
| api-gateway | ──────► | platform-service | gRPC | ValidateJWT + CheckRBAC (every auth'd request) | mTLS |
| api-gateway | ──────► | policy-engine | REST | Policy CRUD + dry-run (management ops) | mTLS + JWT |
| api-gateway | ──────► | discovery-engine | REST | Trigger scans, fetch inventory | mTLS + JWT |
| api-gateway | ──────► | aispm-engine | REST | Risk scores, ARM graph data | mTLS + JWT |
| api-gateway | ──────► | audit-service | REST | Audit query, NL query, export | mTLS + JWT |
| api-gateway | ──────► | hitl-service | REST | HITL queue, approve/deny | mTLS + JWT + MFA |
| api-gateway | ──────► | compliance-engine | REST | Compliance reports, framework status | mTLS + JWT |
| policy-engine | ──────► | platform-service | gRPC | GetTenantContext (bundle build) | mTLS |
| policy-engine | ──────► | Kafka | Kafka | Publish: policy_events (via outbox relay) | SASL/TLS |
| aispm-engine | ──────► | Neo4j (AuraDB) | Bolt | BFS blast radius + ARM subgraph queries | Vault credentials |
| audit-service | ──────► | Kafka | Kafka | CONSUME: all domains; commit after Iceberg write | SASL/TLS IRSA |
| audit-service | ──────► | AWS Bedrock | HTTPS | NL query translation + result summarisation | IRSA |
| hitl-service | ──────► | notification-service | REST | Dispatch HITL notifications (Slack/PD/email) | mTLS |
| hitl-service | ──────► | Kafka | Kafka | Publish: hitl.requests; Consume: hitl.responses | SASL/TLS |
| investigation-engine | ──────► | aispm-engine | REST | Trigger risk rescore on anomaly finding | mTLS |
| investigation-engine | ──────► | AWS Bedrock | HTTPS | Risk narrative generation (metadata only) | IRSA |
| notification-service | ──────► | Slack API | HTTPS | HITL + alert notifications | Bot token (Vault) |
| notification-service | ──────► | PagerDuty | HTTPS | T3/T4 HITL + SLO breaches | API key (Vault) |
| temporal-workers | ──────► | discovery-engine | REST | Execute scan activities | mTLS |
| temporal-workers | ──────► | compliance-engine | REST | Execute report generation activities | mTLS |
| gRPC (blue): enforcement path, auth, tenant context — <10ms target | REST (green): management APIs, service-to-service — <200ms target | Kafka (orange): all async events — at-least-once, exactly-once for audit |
| --- | --- | --- |
| AI Agent
(tool call request) | ──────────────────────────► | MCP Gateway
(receives request) |
| --- | --- | --- |
| ▼  Pipeline begins — each stage can ABORT with DENY |
| --- |
| # | Stage | What it checks / does | Target
Latency | On Failure |
| --- | --- | --- | --- | --- |
| 1 | AIT Signature
Verify | Parse JWT → fetch tenant Ed25519 public key from LRU cache (300s TTL) → verify signature | <1ms | DENY: AIT_SIGNATURE_INVALID |
| 2 | AIT Claims
Validate | Check expiry (exp < now) → Redis SISMEMBER on revocation set → optional fingerprint check | <1ms | DENY: AIT_EXPIRED / AIT_REVOKED |
| 3 | Tool
Authorization | Check requested tool_name ∈ AIT.granted_tools[] (in-memory, no I/O) | <1ms | DENY: TOOL_NOT_AUTHORIZED |
| 4 | Rate Limit
Check | Redis Lua token bucket per (agent_id, tool_name): INCR + TTL atomic | <2ms | DENY: RATE_LIMIT_EXCEEDED |
| 5 | MCP Server
Registry | Verify target MCP server URL ∈ approved_servers (Redis hash, 60s TTL) | <1ms | DENY: MCP_SERVER_NOT_APPROVED |
| 6 | DLP Parameter
Scan | Run Aho-Corasick multi-pattern scan for PII / credentials / classification markers | <5ms | DENY or REDACT per policy |
| 7 | Injection
Detection | Pattern match for prompt injection (OWASP LLM01 patterns, pre-compiled) | <3ms | DENY: INJECTION_DETECTED |
| 8 | Policy
Decision | gRPC EvaluateAction → policy-engine: OPA evaluation against tenant bundle | <10ms | DENY / ESCALATE per policy |
| 9 | Forward to
MCP Server | Proxy validated request to upstream MCP server (transparent reverse proxy) | Network | DENY: PROXY_ERROR |
| 10 | Response
Scan | DLP scan on MCP server response before returning to agent (streaming) | <5ms | REDACT or BLOCK per policy |
| 11 | Audit
Emit | Publish complete AgentActionEvent to Kafka (async, non-blocking) | <1ms async | Buffer locally, retry |
| ▼  Response returned
(or DENY HTTP 403) |  | Total budget:
~28ms (stages 1–11) |
| --- | --- | --- |
| Inbound Action
(from mcp-gateway EvaluateAction call) |  |  |
| --- | --- | --- |
| ▼ |
| --- |
|  | L0: PLATFORM BASELINE CHECK
(immutable — runs ALWAYS, cannot be overridden) |  |
| --- | --- | --- |
| YES → credential exfiltration / PII+external / self-modify detected | ◄────── | matches? | ──────►
NO → continue |  |
| --- | --- | --- | --- | --- |
| ▼ |  | ▼ |  |  |
| --- | --- | --- | --- | --- |
| DENY
(L0) |  | L1: TENANT POLICIES
(security team policies; apply to all agents) |
| --- | --- | --- |
|  |  | DENY
matches? | ──► | ESCALATE
matches? | ──► | L2/L3: GROUP & AGENT POLICIES
(refined scope; agent-specific overrides) |
| --- | --- | --- | --- | --- | --- | --- |
|  |  | ▼ |  |  |  |
| --- | --- | --- | --- | --- | --- |
| DENY
(L1–L3) |  | ESCALATE
→ HITL |  | DENY
(L1 overrides L2) |  | ESCALATE
(highest tier wins) |  | ALLOW
(no DENY or ESCALATE matched) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CONFLICT RESOLUTION RULE:  DENY > ESCALATE > ALLOW  (most restrictive wins — Fail Secure) |
| --- |
| Policy Engine
Decision: ESCALATE | ──────►
create HITL request
+ start timer
+ notify approvers | ◉  PENDING

Awaiting human
approval |  |  |
| --- | --- | --- | --- | --- |
| Human calls POST /v1/hitl/{id}/approve
(MFA required, within timeout window) |  | Timer expires
(T1: 5min → auto-ALLOW
T2: 15min → auto-DENY
T3/T4: immediate DENY) |  | Human calls POST /v1/hitl/{id}/deny
(MFA required) |
| --- | --- | --- | --- | --- |
| ▼ |  | ▼ |  | ▼ |
| ◉  APPROVED

MCP Gateway
Callback → ALLOW | ◄── | ◉  AUTO-
APPROVED

T1 timeout; action
proceeds with alert |  | ◉  TIMED OUT

Auto-DENY applied;
MCP Gateway → DENY |  | ◉  DENIED

MCP Gateway
Callback → DENY |
| --- | --- | --- | --- | --- | --- | --- |
| TIER 3 (Multi-Party): Requires 2-of-N approvals. approvals_received tracked atomically in PostgreSQL. APPROVED only when approvals_received ≥ required_approvers. |
| --- |
| ALL TERMINAL STATES write an audit event (Ed25519-signed) before calling MCP Gateway callback. Callback failure retried 3× before DENY applied. |
| --- |
| composite = round( 0.25×Permission + 0.25×DataAccess + 0.20×BlastRadius + 0.15×Autonomy + 0.15×Compliance ) |
| --- |
| # | Dimension | Weight | Formula | Example Signal |
| --- | --- | --- | --- | --- |
| D1 | Permission
Scope | 25% | Σ(TOOL_SENSITIVITY[access_type] × ACCESS_WEIGHT[dest]) / tool_count × 10
TOOL: READ=1, WRITE=3, EXECUTE=5, ADMIN=10
DEST: INTERNAL=1.0×, MCP=1.5×, EXTERNAL=2.0× | Agent with 3 WRITE+EXTERNAL tools → raw=6×2.0/3×10 = ~40 score |
| D2 | Data Access
Sensitivity | 25% | Σ(DATA_TIER[classification] × access_freq_percentile) / source_count
DATA_TIER: PUBLIC=0, INTERNAL=10, REGULATED=30, IP=50, PII=70, FINANCIAL=90 | Agent reading PII (70) at 80th pct frequency → ~64 score |
| D3 | Blast
Radius | 20% | Σ(NODE_CRIT[type] × 1/(depth+1)) / 200 × 100
NODE: AGENT=20, DATA_SOURCE=15, MCP_SERVER=10, TOOL=5
Depth decay: depth=1 → 0.5×; depth=2 → 0.33×; ... | Agent connected to 5 agents + 3 data sources at depth 1 → ~75 score |
| D4 | Autonomy
Level | 15% | Direct mapping: autonomy_level → score
Level 0=0, Level 1=20, Level 2=40,
Level 3=60, Level 4=80, Level 5=100
(set at agent registration) | Fully autonomous agent (level 5) → 100 score |
| D5 | Policy
Compliance | 15% | Σ(SEVERITY_SCORE[severity] × 0.9^days_ago) for violations in last 30d
CRITICAL=25, HIGH=15, MEDIUM=8, LOW=3
Decay: 1.0 today → 0.1 after 22 days | 2 CRITICAL violations yesterday → 25×0.9 + 25×0.9 = 45 score |
| 🔴 CRITICAL
80–100 |  | 🟠 HIGH
60–79 |  | 🟡 MEDIUM
40–59 |  | 🟢 LOW
20–39 |  | ⚫ MINIMAL
0–19 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 📤  PRODUCERS  (publish events to Kafka) |
| --- |
| mcp-gateway |  | policy-engine |  | discovery-engine |  | aispm-engine |  | hitl-service |  | compliance-engine |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ▼  all events published via Avro + AWS Glue Schema Registry |
| --- |
| 📦  KAFKA TOPICS  (MSK multi-AZ; replication factor 3) |
| --- |
| enforcement.
agent_actions

24 parts
7d retain |  | enforcement.
policy_decisions

24 parts
7d retain |  | discovery.
agent_lifecycle

12 parts
30d retain |  | risk.
score_updates

12 parts
7d retain |  | hitl.
requests+responses

12 parts
7d retain |  | compliance.
evidence_events

12 parts
90d compact |  | DLQ topics
(per consumer)

6 parts
14d retain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ▼  consumed by dedicated consumer groups (one per service); commit offset ONLY after processing confirmed |
| --- |
| 📥  CONSUMERS  (consumer group per service) |
| --- |
| audit-
consumer |  | aispm-
consumer |  | investigation-
consumer |  | notification-
consumer |  | hitl-
consumer |  | mcp-gateway-
consumer (hitl.responses) |  | compliance-
consumer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ⚡ Audit Consumer: Kafka TRANSACTIONS (exactly-once)
Commit offset only after Iceberg write confirmed |  | 🔄 All others: at-least-once + idempotency on event_id
Failed messages → DLQ after 3–5 retries with backoff |
| --- | --- | --- |
| tenants

───────────────

PK id (UUID v7)
slug (unique)
plan_tier
region
vault_key_id
status |  | 1 tenant
has many
users →
1:N |  | users

───────────────

PK id (UUID v7)
FK tenant_id → tenants
email (unique/tenant)
roles TEXT[]
sso_subject
mfa_enabled
status |  | connectors

───────────────

PK id
FK tenant_id
connector_type
vault_secret_path
status
last_sync_at |
| --- | --- | --- | --- | --- | --- | --- |
| ▼ 1 tenant
has many
agents |  |
| --- | --- |
| agents

───────────────

PK id
FK tenant_id → tenants
FK connector_id → connectors
name, agent_type, framework
owner_email
fingerprint (SHA-256)
risk_score, risk_tier
autonomity_level
status |  | N:M
via
agent_
tools |  | tools

───────────────

PK id
FK tenant_id
name
tool_type
sensitivity_tier
destination_type
mcp_server_url
is_approved |  | 1:N
(one agent
many AITs) |  | agent_
identity_
tokens

───────────────

PK id
FK tenant_id
FK agent_id
ait_hash (SHA-256)
fingerprint
granted_tools[]
issued_by
expires_at
revoked_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ▼ 1 agent
many HITL
requests |  |
| --- | --- |
| hitl_requests

───────────────

PK id
FK tenant_id, agent_id
decision_id
action_summary
policy_id → policies
hitl_tier (1–4)
required_approvers
approvals_received
timeout_at
callback_url
status
resolved_by → users |  | 1 policy
controls
many HITL
requests |  | policies

───────────────

PK id
FK tenant_id (nullable for L0)
policy_level (0–3)
scope_type, scope_id
ego_source (Rego text)
action_on_match
hitl_tier
enabled
shadow_mode_until
approved_by → users |  | policy
change
appended
to log |  | policy_
change_log

───────────────

PK id
FK policy_id
FK tenant_id
change_type
changed_by → users
old_value JSONB
new_value JSONB
changed_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FK = Foreign Key  ·  PK = Primary Key | All tables: tenant_id FK + Row-Level Security policy
+ created_at + updated_at + deleted_at (soft delete) | TimescaleDB: agent_risk_scores (hypertable, time + tenant)
Neo4j: Agent, Tool, DataSource, MCPServer nodes |
| --- | --- | --- |
| AWS Application Load Balancer (ALB)  +  AWS WAF  →  TLS 1.3 Termination |
| --- |
| ▼ Traffic enters via ALB into pinaka-gateway namespace |
| --- |
| 📦  pinaka-gateway
(internet-facing) | api-gateway (Kong)

Rate limit · Auth · Routing
3–20 pods | HPA on RPS |  | mcp-gateway

11-stage pipeline
3–50 pods | HPA on connections |
| --- | --- | --- | --- |
| 📦  pinaka-core
(no internet egress) | policy-engine

OPA · <10ms gRPC
3–30 pods | HPA on RPS |  | discovery-engine

Temporal activities
2–10 pods | HPA on CPU |  | temporal-workers

Scan + report workflows
3–20 pods | HPA on backlog |
| --- | --- | --- | --- | --- | --- |
| 📦  pinaka-data
(AWS services egress only) | aispm-engine

Risk scoring + ARM
2–8 pods | HPA on CPU |  | audit-service

Iceberg writer + NL query
3–15 pods | KEDA Kafka lag |  | investigation-engine

ML baselining + narratives
2–6 pods | HPA on CPU |
| --- | --- | --- | --- | --- | --- |
|  | compliance-engine

Framework mapping + PDF
2–6 pods | HPA on CPU |  | console-ui

S3 + CloudFront
(static assets, not K8s) |
| --- | --- | --- | --- |
| 📦  pinaka-platform
(external APIs egress) | platform-service

Auth · JWT · SSO · Tenancy
3–15 pods | HPA on RPS |  | hitl-service

Approval workflows
2–8 pods | HPA on CPU |  | notification-service

Multi-channel delivery
2–8 pods | KEDA lag |
| --- | --- | --- | --- | --- | --- |
| 📦  pinaka-infra
(VPC-private only) | PostgreSQL
(RDS Multi-AZ) |  | Redis 7
(ElastiCache) |  | Kafka
(AWS MSK) |  | Neo4j
(AuraDB) |  | OpenSearch
(AWS) |  | Vault
(HCP) |  | Iceberg/S3
(WORM) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 📦  pinaka-ops
(VPN access only) | Datadog Agent
(DaemonSet)

Metrics · Logs · Traces
1 pod per node |  | Falco
(DaemonSet)

Runtime kernel security
1 pod per node |  | ArgoCD
(GitOps)

Deployment controller
App-of-Apps pattern |
| --- | --- | --- | --- | --- | --- |
| # | Stage | Steps | Tool | Gate (blocks merge/deploy if fails) |
| --- | --- | --- | --- | --- |
| 1 | PR
Checks | Unit tests · OPA test · SAST (Semgrep) · OpenAPI diff · Dependabot audit | GitHub Actions | All checks pass; no CRITICAL Semgrep; API backwards-compatible |
| 2 | Integration
Tests | Docker Compose env · API contract tests (Pact) · DB migration dry-run | GitHub Actions + Docker | All integration tests pass; Pact contracts verified |
| 3 | Build &
Scan | Docker multi-stage build · Trivy image scan · SBOM (Syft) · Cosign sign · Push to ECR | GitHub Actions + ECR | No CRITICAL CVEs; SBOM signed; image pushed |
| 4 | Deploy
Dev | ArgoCD auto-sync · Smoke tests · Liveness/readiness checks · Trace sampling verify | ArgoCD | All smoke tests pass; services READY |
| 5 | Load
Test (Nightly) | k6: 1000 RPS enforcement path 10min · REST API 500 RPS · Kafka 50K EPS | k6 + Datadog | p99 within SLO; error rate <0.1%; no OOM kills |
| 6 | Staging
Deploy | Manual: Engineering Lead · Full test suite · Chaos experiment · Burp Suite scan | ArgoCD + Gremlin | Chaos recovery within SLA; no new security findings; SLO green 24h |
| 7 | Prod
Canary (5%) | Manual: 2-of-3 approval (CTO/Eng Lead/SRE) · Istio canary 5% traffic · SLO monitor | ArgoCD + Istio | p99 within SLO; error rate <0.1% for 15 min |
| 8 | Prod
(25%) | Auto-promote from 5% if SLO maintained 15 min | ArgoCD + Istio | Same as stage 7 for 15 min at 25% |
| 9 | Prod
(100%) | Auto-promote from 25% if SLO maintained 30 min · Rollback on SLO breach | ArgoCD + Istio | Same SLO maintained 30 min · Post in #deploys |
| 🔄 Rollback: helm rollback {service} -n {ns}
→ ArgoCD self-heals within 60s | ⚡ Sync Waves: Wave 0=platform · Wave 1=policy · Wave 2=data · Wave 3=gateways · Wave 4=rest |
| --- | --- |
| JWT Access Token
(RS256) |  | 15 min
expiry |  | Refresh Token
(256-bit random) |  | 7 day
expiry |  | API Key
(HMAC prefix+secret) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Stateless: verify RS256
signature at API Gateway |  |  |  | Stateful: stored as
SHA-256 hash in Redis |  |  |  | Stateful: bcrypt hash
in PostgreSQL |
| ── ACCESS TOKEN REFRESH FLOW ── |
| --- |
| Browser
(Console) |  | API call with
expired access token |  | API Gateway
(Kong) |  | 401 token_expired
+ refresh_hint:true |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  | ▼ |  |  |  |  |
| POST /auth/refresh
(HttpOnly cookie) | ─────────────────► |  |  | Platform
Service | Redis: DEL old RT
SET new RT | Redis
(single-use RT) |  |  |
|  |  |  |  | ◄─────────────────
new_access_token
+ Set-Cookie new_rt |  |  |  |  |
| ── AGENT IDENTITY TOKEN (AIT) LIFECYCLE ── |
| --- |
| 1. Register
Agent | ► | 2. Fetch tenant
Ed25519 privkey
from Vault
(60s lease) | ► | 3. Sign JWT
with tenant key
+ fingerprint
+ tools[] | ► | 4. Store
SHA-256(AIT)
in DB
(never plaintext) | ► | 5. Return AIT
plaintext
(shown ONCE;
admin stores it) | ► 90 days | 6. AIT Expiry
→ Temporal
AITExpiryWorkflow
→ revoke + alert |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Verification path (every MCP request):
AIT → Ed25519 verify → Redis revocation check → fingerprint check → claims → proceed |  | Revocation path (on security event):
API call → DB update → Redis SADD(ait_revoked) → propagated <5s to all gateway pods |
| --- | --- | --- |
| Coverage Promise | This LLD covers ALL 29 sections of the Pinaka HLD v1.1. No section is omitted. Every service has: internal class/struct definitions, complete method signatures, error codes, configuration reference, and unit test specifications. |
| --- | --- |
| Section | Content | HLD Sections Covered |
| --- | --- | --- |
| §2–§12 | Per-service internal LLD (11 services + 1 UI) | §2–§3, §16–§21 |
| §13 | Complete PostgreSQL + TimescaleDB + Neo4j schemas | §6, §24 |
| §14 | Complete gRPC protobuf definitions (all services) | §3 |
| §15 | Complete OpenAPI 3.1 specs (all REST endpoints) | §7 |
| §16 | Kafka Avro schemas (all topics) | §5 |
| §17 | OPA Rego modules (complete policy system) | §17 |
| §18 | Algorithm specifications (pseudocode) | §20, §25 |
| §19 | Configuration reference (all env vars per service) | §23 |
| §20 | Test specifications (unit + integration + contract) | §11, §13 |
| §21 | Security controls matrix (auth, rate limit, input validation per endpoint) | §16, §18 |
| §22 | Temporal workflow detailed specs | §10 |
| §23 | Error handling implementation patterns | §12 |
| §24 | Deployment checklist & runbook structure | §8, §22, §28 |
| §25 | Distributed consistency implementation guide | §27 |
| §26 | API implementation patterns (pagination, idempotency) | §26 |
| §27 | Kubernetes manifest specifications | §8 |
| §28 | Performance & load testing specifications | §28 |
| §29 | Istio, Schema Registry, Container build specs | §29 |
| Symbol | Meaning |
| --- | --- |
| → | Must implement in v1.0 (mandatory) |
| ⟹ | Must implement by v1.5 (planned) |
| ◌ | Future v2.0 |
| * | Required parameter / non-nullable field |
| ? | Optional parameter / nullable field |
| readonly | Field written once at creation; never updated in place |
| [deprecated] | Field kept for backward compatibility; new code must not write this |
| §2  Policy Engine — Low Level Design | Go 1.22  ·  OPA 0.65+  ·  gRPC |
| --- | --- |
| Responsibility | Evaluate every agent action against the active policy set. Return ALLOW/DENY/ESCALATE in <10ms p99. Maintain the policy registry. Serve compiled OPA bundles to MCP Gateway. Manage the policy change workflow with outbox pattern. |
| --- | --- |
| services/policy-engine/
├── cmd/policy-engine/main.go        # Entrypoint: wire dependencies, start gRPC + HTTP
├── internal/
│   ├── api/
│   │   ├── grpc/server.go           # gRPC server: PolicyEngineServer implementation
│   │   ├── http/server.go           # REST HTTP server: management API
│   │   └── http/handlers/           # Per-endpoint handlers (policy CRUD, dry-run)
│   ├── evaluation/
│   │   ├── evaluator.go             # Core: OpaEvaluator interface + implementation
│   │   ├── bundle_builder.go        # Builds OPA bundle from PostgreSQL policy records
│   │   ├── bundle_cache.go          # Redis-backed bundle cache with TTL
│   │   ├── conflict_resolver.go     # Applies DENY-wins conflict resolution
│   │   └── dry_run.go               # DryRunEngine: evaluate without enforcement
│   ├── policy/
│   │   ├── repository.go            # PolicyRepository: CRUD against PostgreSQL
│   │   ├── validator.go             # Validate Rego syntax + schema before save
│   │   ├── outbox.go                # TransactionalOutbox: write policy + event atomically
│   │   └── relay.go                 # OutboxRelay: poll outbox → publish to Kafka
│   ├── shadow/
│   │   └── shadow_enforcer.go       # ShadowEnforcer: log-only mode during shadow window
│   └── metrics/
│       └── metrics.go               # Prometheus metric definitions
├── pkg/                             # Exported: PolicyClient for other services
└── proto/policy/v1/policy.pb.go     # Generated protobuf |
| --- |
| // internal/evaluation/evaluator.go

// OpaEvaluator — the single point of policy evaluation
type OpaEvaluator interface {
    // Evaluate returns decision for an agent action. Must complete in <10ms p99.
    Evaluate(ctx context.Context, req EvaluationRequest) (EvaluationResult, error)
}

type EvaluationRequest struct {
    TenantID            string            // * partition key for RLS + bundle lookup
    AgentID             string            // * the acting agent
    AITID               string            // * AIT used for this action
    ToolName            string            // * tool being called
    Destination         DestinationType   // * INTERNAL|EXTERNAL|MCP_SERVER|AGENT
    DataClassifications []string          // ? [PII, FINANCIAL, IP, REGULATED, PUBLIC]
    ActionMetadata      map[string]string // ? additional k/v context for Rego
    RequestTimestampNs  int64             // * nanosecond UTC timestamp
}

type EvaluationResult struct {
    DecisionID  string          // UUID v7 — referenced in audit log
    Decision    Decision        // ALLOW | DENY | ESCALATE
    Reason      string          // human-readable: which policy triggered
    PolicyID    string          // winning policy UUID (empty for ALLOW from no match)
    HITLTier    int             // 1–4 if Decision==ESCALATE; else 0
    RiskDelta   int             // projected risk score change from this action
    EvaluatedAt time.Time       // when evaluation completed
    PolicyCount int             // number of policies evaluated (for metrics)
}

type Decision string
const (
    DecisionAllow    Decision = "ALLOW"
    DecisionDeny     Decision = "DENY"
    DecisionEscalate Decision = "ESCALATE"
) |
| --- |
| // internal/evaluation/bundle_cache.go

type BundleCache interface {
    // Get returns compiled OPA PreparedEvalQuery from Redis, or cache miss error.
    Get(ctx context.Context, tenantID, versionHash string) (*rego.PreparedEvalQuery, error)
    // Set stores compiled bundle with TTL=60s.
    Set(ctx context.Context, tenantID, versionHash string, bundle *rego.PreparedEvalQuery) error
    // InvalidateTenant deletes all bundle cache entries for a tenant (on policy change).
    InvalidateTenant(ctx context.Context, tenantID string) error
    // GetCurrentVersionHash returns the hash of the latest compiled bundle for a tenant.
    GetCurrentVersionHash(ctx context.Context, tenantID string) (string, error)
}

// RedisBundleCache — concrete implementation
type RedisBundleCache struct {
    client redis.Client
    ttl    time.Duration // default 60s
}

// Key pattern: policy_bundle:{tenantID}:v{versionHash}
// Version hash: SHA-256(sorted policy IDs + their updated_at timestamps)
// This ensures a new key on every policy change — no stale reads possible |
| --- |
| // internal/policy/repository.go

type PolicyRepository interface {
    GetActivePoliciesForTenant(ctx context.Context, tenantID string) ([]Policy, error)
    GetPolicyByID(ctx context.Context, tenantID, policyID string) (Policy, error)
    CreatePolicy(ctx context.Context, policy Policy) (Policy, error)
    UpdatePolicy(ctx context.Context, policy Policy) (Policy, error)
    DeletePolicy(ctx context.Context, tenantID, policyID string) error
    GetPolicyVersionHash(ctx context.Context, tenantID string) (string, error)
    // ListPoliciesForDryRun returns policies with their Rego source for dry-run evaluation
    ListPoliciesForDryRun(ctx context.Context, tenantID string) ([]PolicyWithRego, error)
}

type Policy struct {
    ID                 string          // UUID v7
    TenantID           string?         // nil for L0 platform policies
    Level              int             // 0=Platform 1=Tenant 2=Group 3=Agent
    Name               string
    ScopeType          ScopeType       // PLATFORM|TENANT|AGENT_GROUP|AGENT
    ScopeID            string?         // nil for TENANT scope
    RegoSource         string          // OPA Rego policy text
    ActionOnMatch      Decision
    HITLTier           int?            // required if ActionOnMatch==ESCALATE
    Severity           Severity        // CRITICAL|HIGH|MEDIUM|LOW
    Enabled            bool
    ShadowModeUntil    *time.Time      // if set: log-only until this time
    NotificationTargets []string       // email/slack channels to notify on match
    Version            int             // incremented on each update
    ApprovedBy         string?         // user_id who approved (required for L3)
    CreatedBy          string
    CreatedAt          time.Time
    UpdatedAt          time.Time
} |
| --- |
| // internal/api/grpc/server.go

type PolicyEngineServer struct {
    evaluator   evaluation.OpaEvaluator
    bundleCache evaluation.BundleCache
    policyRepo  policy.PolicyRepository
    outbox      policy.TransactionalOutbox
    metrics     *metrics.PolicyMetrics
    pb.UnimplementedPolicyEngineServer
}

func (s *PolicyEngineServer) EvaluateAction(
    ctx context.Context, req *pb.EvaluateActionRequest,
) (*pb.EvaluateActionResponse, error) {
    start := time.Now()
    // 1. Extract tenant context from gRPC metadata (injected by Istio mTLS)
    tenantID, err := grpcutil.TenantFromMeta(ctx)
    if err != nil { return nil, status.Error(codes.Unauthenticated, err.Error()) }

    // 2. Build evaluation request
    evalReq := evaluation.EvaluationRequest{
        TenantID:            tenantID,
        AgentID:             req.AgentId,
        AITID:               req.AitId,
        ToolName:            req.ToolName,
        Destination:         evaluation.DestinationType(req.Destination),
        DataClassifications: req.DataClassifications,
        ActionMetadata:      req.ActionMetadata,
        RequestTimestampNs:  req.RequestTimestamp,
    }

    // 3. Evaluate (target: <10ms p99)
    result, err := s.evaluator.Evaluate(ctx, evalReq)
    if err != nil {
        // Fail Secure: return DENY on evaluation error
        s.metrics.EvaluationErrors.Inc()
        return &pb.EvaluateActionResponse{
            Decision: pb.Decision_DENY,
            Reason:   'evaluation_error_fail_secure',
        }, nil
    }

    // 4. Record metrics
    s.metrics.EvaluationDuration.Observe(time.Since(start).Seconds())
    s.metrics.Decisions.WithLabelValues(string(result.Decision)).Inc()

    return &pb.EvaluateActionResponse{
        DecisionId: result.DecisionID,
        Decision:   pb.Decision(pb.Decision_value[string(result.Decision)]),
        Reason:     result.Reason,
        PolicyId:   result.PolicyID,
        RiskDelta:  int32(result.RiskDelta),
        EvaluatedAt: timestamppb.New(result.EvaluatedAt),
    }, nil
} |
| --- |
| Error Code | HTTP | gRPC | Description | Recovery Action |
| --- | --- | --- | --- | --- |
| POLICY_NOT_FOUND | 404 | NOT_FOUND | Policy ID does not exist in this tenant | Verify policy_id; check tenant isolation |
| POLICY_REGO_INVALID | 400 | INVALID_ARGUMENT | Rego syntax error or failed OPA linting | Fix Rego; run opa check locally before submitting |
| POLICY_VERSION_CONFLICT | 409 | ABORTED | Policy updated concurrently; version mismatch | Re-fetch current version; retry with updated version field |
| POLICY_L3_REQUIRES_MFA | 403 | PERMISSION_DENIED | Agent-specific policy (L3) requires MFA-verified JWT | Complete MFA challenge; re-authenticate |
| BUNDLE_COMPILE_ERROR | 500 | INTERNAL | OPA bundle compilation failed unexpectedly | Check policy Rego for cross-rule conflicts; alert ops |
| EVALUATION_TIMEOUT | 503 | UNAVAILABLE | OPA evaluation exceeded 10ms gRPC deadline | Automatic DENY (Fail Secure); Redis cache may be cold |
| SHADOW_MODE_ACTIVE | 200 | OK | Policy matched but in shadow mode; action proceeding | Informational; audit log tagged shadow_mode=true |
| Env Variable | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| PORT_GRPC | int | 50051 | → | gRPC enforcement server port |
| PORT_HTTP | int | 8080 | → | REST management API port |
| PORT_METRICS | int | 9090 | → | Prometheus metrics port |
| DATABASE_URL | string | — | → | PostgreSQL connection string (from ESO/Vault) |
| REDIS_URL | string | — | → | Redis connection string (from ESO/Vault) |
| REDIS_BUNDLE_TTL_SEC | int | 60 | → | OPA bundle cache TTL in seconds |
| OPA_DECISION_TIMEOUT_MS | int | 8 | → | OPA evaluation hard timeout (leave 2ms for overhead within 10ms gRPC deadline) |
| BUNDLE_REBUILD_CONCURRENCY | int | 3 | → | Max concurrent bundle compilations (prevents CPU spike on mass invalidation) |
| KAFKA_BOOTSTRAP_SERVERS | string | — | → | MSK bootstrap servers for outbox relay |
| KAFKA_OUTBOX_TOPIC | string | pinaka.platform.policy_events | → | Topic for policy change events |
| SHADOW_MODE_CHECK_INTERVAL_SEC | int | 300 | → | How often to check for expired shadow mode policies |
| OTEL_EXPORTER_OTLP_ENDPOINT | string | — | → | OpenTelemetry collector endpoint |
| LOG_LEVEL | string | INFO | → | DEBUG|INFO|WARN|ERROR |
| Test Name | Type | Scenario | Expected Outcome | Assertions |
| --- | --- | --- | --- | --- |
| TestEvaluate_Allow_BaselineAction | Unit | L0+L1 policies active; action is INTERNAL tool call with PUBLIC data | Decision=ALLOW; latency<10ms | result.Decision==ALLOW; result.Reason is empty; no error |
| TestEvaluate_Deny_PIIExport | Unit | L1 policy: DENY external PII; action has data_class=PII + destination=EXTERNAL | Decision=DENY; correct policy_id returned | result.Decision==DENY; result.PolicyID==expected; reason contains 'pii' |
| TestEvaluate_Escalate_BulkOp | Unit | L2 policy: ESCALATE bulk_export; action matches scope | Decision=ESCALATE; HITL tier=2 | result.Decision==ESCALATE; result.HITLTier==2 |
| TestEvaluate_DenyWins_Conflict | Unit | L1=ALLOW and L2=DENY both match same action | DENY wins (Fail Secure) | result.Decision==DENY; Conflict resolver applied L2 DENY |
| TestEvaluate_ShadowMode_Allows | Unit | Policy in shadow mode matches DENY condition | Action proceeds (ALLOW returned); audit tagged shadow_mode | result.Decision==ALLOW; audit event has shadow_mode=true |
| TestEvaluate_FailSecure_OPATimeout | Unit | OPA evaluation exceeds 8ms deadline | Decision=DENY (fail secure) | result.Decision==DENY; reason==evaluation_error_fail_secure; metrics.EvaluationErrors incremented |
| TestBundleCache_InvalidateOnChange | Integration | Policy updated → InvalidateTenant called → next evaluation compiles new bundle | New bundle reflects updated policy | Bundle hash changes after invalidation; new evaluation uses updated policy |
| TestOutbox_AtomicWrite | Integration | CreatePolicy writes policy + outbox event in same transaction; Kafka offline | PostgreSQL has both records; Kafka event pending in outbox | Policy record + outbox record exist; relay publishes when Kafka recovers |
| §3  MCP Gateway — Low Level Design | Go 1.22  ·  iptables/eBPF  ·  gRPC client |
| --- | --- |
| Responsibility | Intercept all MCP tool calls. Run 11-stage inspection pipeline: AIT verify → tool auth → rate limit → server registry → DLP scan → injection detect → policy decision → forward → response scan → audit emit. Target: <500ms p99 total added latency (v1.0); <100ms (v1.5). |
| --- | --- |
| services/mcp-gateway/
├── cmd/mcp-gateway/main.go
├── internal/
│   ├── proxy/
│   │   ├── gateway.go          # Gateway: main request handler, stage orchestration
│   │   ├── pipeline.go         # PipelineStage interface; stage runner with timeout
│   │   └── mcp_proxy.go        # MCPProxy: reverse proxy to upstream MCP server
│   ├── stages/
│   │   ├── ait_validator.go    # Stage 1-2: AIT signature + claims validation
│   │   ├── tool_authorizer.go  # Stage 3: AIT granted_tools check
│   │   ├── rate_limiter.go     # Stage 4: Redis token bucket per agent+tool
│   │   ├── server_registry.go  # Stage 5: Approved MCP server verification
│   │   ├── dlp_scanner.go      # Stage 6: PII/credential/sensitive data detection
│   │   ├── injection_detector.go # Stage 7: Prompt injection pattern matching
│   │   ├── policy_enforcer.go  # Stage 8: gRPC call to policy-engine
│   │   └── response_scanner.go # Stage 10: Response DLP scan before return to agent
│   ├── audit/
│   │   └── publisher.go        # Async Kafka publish with local buffer fallback
│   ├── ait/
│   │   └── verifier.go         # Ed25519 verify + Redis cache + revocation check
│   └── interceptor/
│       └── iptables.go         # InitContainer: inject iptables REDIRECT rules |
| --- |
| // internal/proxy/pipeline.go

// PipelineStage — each stage in the 11-stage inspection pipeline
type PipelineStage interface {
    // Name returns the stage name for metrics + logging
    Name() string
    // Process mutates the context; returns StageError to abort pipeline
    Process(ctx context.Context, req *MCPRequest) *StageError
}

type StageError struct {
    Code     ErrorCode  // e.g. TOOL_NOT_AUTHORIZED, INJECTION_DETECTED
    Reason   string     // human-readable explanation
    Stage    string     // which stage detected this
    Decision Decision   // always DENY (stages can only abort, not approve)
}

type MCPRequest struct {
    // Input (from agent)
    RawRequest    []byte           // original MCP JSON-RPC request
    ToolName      string           // extracted tool name
    ToolParams    map[string]any   // extracted parameters
    AgentAIT      string           // Bearer token from Authorization header
    MCPServerURL  string           // target MCP server URL

    // Populated by stages (accumulated context)
    TenantID             string
    AgentID              string
    AITClaims            *AITClaims
    DataClassifications  []string
    InjectionPatterns    []string   // any injection patterns detected
    PolicyDecision       *EvaluationResult
    MCPResponse          []byte     // populated after Stage 9 (forward)
    ScannedResponse      []byte     // populated after Stage 10 (response scan)
    StartTime            time.Time
}

// Gateway orchestrates the pipeline
type Gateway struct {
    stages  []PipelineStage  // stages 1-8 (pre-forward)
    proxy   *MCPProxy        // stage 9: forward
    scanner *ResponseScanner // stage 10: response scan
    auditor *AuditPublisher  // stage 11: async audit
}

func (g *Gateway) Handle(ctx context.Context, req *MCPRequest) ([]byte, *StageError) {
    req.StartTime = time.Now()
    for _, stage := range g.stages {
        stageStart := time.Now()
        if err := stage.Process(ctx, req); err != nil {
            g.auditor.PublishAsync(buildDenyAuditEvent(req, err))
            metrics.StageDuration.WithLabelValues(stage.Name()).Observe(
                time.Since(stageStart).Seconds())
            return nil, err
        }
        metrics.StageDuration.WithLabelValues(stage.Name()).Observe(
            time.Since(stageStart).Seconds())
    }
    resp, err := g.proxy.Forward(ctx, req)    // Stage 9
    if err != nil { return nil, err }
    req.MCPResponse = resp
    resp = g.scanner.Scan(ctx, req)            // Stage 10
    g.auditor.PublishAsync(buildAllowAuditEvent(req)) // Stage 11 (non-blocking)
    return resp, nil
} |
| --- |
| // internal/stages/ait_validator.go
type AITValidator struct {
    verifier    *ait.Verifier      // Ed25519 signature verifier
    redis       redis.Client       // for revocation list lookup
    vaultClient vault.Client       // for tenant public key fetch
    keyCache    *lru.Cache         // in-memory LRU cache of tenant public keys (5min TTL)
}

func (v *AITValidator) Process(ctx context.Context, req *MCPRequest) *StageError {
    // 1a. Parse JWT header (no verification yet)
    header, err := jwt.ParseHeader(req.AgentAIT)
    if err != nil { return &StageError{Code: AIT_INVALID_FORMAT, ...} }

    tenantID := header.Get('tenant_id')  // custom claim in AIT header
    req.TenantID = tenantID

    // 1b. Fetch tenant public key (LRU cache → Redis → Vault)
    pubKey, err := v.getTenantPublicKey(ctx, tenantID)
    if err != nil { return &StageError{Code: AIT_KEY_FETCH_FAILED, ...} }

    // 1c. Verify Ed25519 signature
    claims, err := v.verifier.Verify(req.AgentAIT, pubKey)
    if err != nil { return &StageError{Code: AIT_SIGNATURE_INVALID, ...} }

    // 2a. Check expiry
    if time.Now().After(claims.ExpiresAt) {
        return &StageError{Code: AIT_EXPIRED, ...}
    }

    // 2b. Check revocation list (Redis SET SISMEMBER — O(1))
    revoked, _ := v.redis.SIsMember(ctx, 'ait_revoked', sha256(req.AgentAIT)).Result()
    if revoked { return &StageError{Code: AIT_REVOKED, ...} }

    // 2c. Fingerprint check (optional in v1.0; required in v1.1)
    // currentFingerprint := calculateDeploymentFingerprint()
    // if currentFingerprint != claims.Fingerprint { return FINGERPRINT_MISMATCH }

    req.AgentID = claims.AgentID
    req.AITClaims = claims
    return nil // Stage passed
} |
| --- |
| // internal/stages/rate_limiter.go
// Token bucket: each agent+tool pair has a bucket replenished at configuredRate/sec

func (r *RateLimiter) Process(ctx context.Context, req *MCPRequest) *StageError {
    key := fmt.Sprintf('rl:%s:%s:%s', req.TenantID, req.AgentID, req.ToolName)
    limit := r.getLimitForAgentTool(ctx, req.TenantID, req.ToolName) // from policy

    // Redis Lua script: atomic token bucket check + decrement
    // Returns: 1=allowed, 0=denied, current_tokens
    result, err := r.redis.Eval(ctx, tokenBucketLua,
        []string{key},
        limit,           // max_tokens (capacity)
        limit,           // refill_rate (tokens/sec)
        time.Now().Unix(),
        1,               // tokens_requested
    ).Int64Slice()

    if result[0] == 0 {
        return &StageError{
            Code:   RATE_LIMIT_EXCEEDED,
            Reason: fmt.Sprintf('rate limit %d/s exceeded for %s', limit, req.ToolName),
        }
    }
    return nil
}

const tokenBucketLua = `
local key = KEYS[1]
local max_tokens = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local last_time = tonumber(redis.call('HGET', key, 'last_time') or now)
local tokens = tonumber(redis.call('HGET', key, 'tokens') or max_tokens)
local elapsed = now - last_time
tokens = math.min(max_tokens, tokens + elapsed * refill_rate)

if tokens >= requested then
  tokens = tokens - requested
  redis.call('HSET', key, 'tokens', tokens, 'last_time', now)
  redis.call('EXPIRE', key, 3600)
  return {1, tokens}
else
  return {0, tokens}
end` |
| --- |
| Error Code | HTTP | gRPC | Description | Recovery Action |
| --- | --- | --- | --- | --- |
| AIT_INVALID_FORMAT | 401 | UNAUTHENTICATED | Malformed JWT in Authorization header | Re-issue AIT; check agent code sends correct header |
| AIT_SIGNATURE_INVALID | 401 | UNAUTHENTICATED | Ed25519 signature verification failed | AIT compromised or wrong key; re-register agent |
| AIT_EXPIRED | 401 | UNAUTHENTICATED | AIT past expires_at | Rotate AIT; check agent auto-refresh logic |
| AIT_REVOKED | 403 | PERMISSION_DENIED | AIT in Redis revocation set | Investigate why AIT was revoked; re-register agent |
| AIT_FINGERPRINT_MISMATCH | 403 | PERMISSION_DENIED | Agent code/config changed since AIT issued (v1.1+) | Re-register agent after deployment |
| TOOL_NOT_AUTHORIZED | 403 | PERMISSION_DENIED | Tool not in AIT granted_tools list | Request tool access via agent registration update |
| RATE_LIMIT_EXCEEDED | 429 | RESOURCE_EXHAUSTED | Token bucket empty for agent+tool | Retry after backoff; check if agent has a bug calling tool in loop |
| MCP_SERVER_NOT_APPROVED | 403 | PERMISSION_DENIED | Target MCP server URL not in approved registry | Add MCP server to approved list via admin console |
| DLP_VIOLATION_DETECTED | 403 | PERMISSION_DENIED | PII/credentials detected in tool parameters | Review agent code; never pass sensitive data to external tools |
| INJECTION_DETECTED | 403 | PERMISSION_DENIED | Prompt injection pattern found in parameters | Investigate source; may indicate agent compromise |
| POLICY_DENY | 403 | PERMISSION_DENIED | Policy engine returned DENY | Check policy configuration; contact security team |
| POLICY_ESCALATE | 202 | OK | Action paused; HITL approval required | Wait for approval notification; action will auto-proceed or auto-deny |
| Env Variable | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| PORT_MCP | int | 15000 | → | Intercepted MCP traffic port (iptables redirect target) |
| PORT_METRICS | int | 9091 | → | Prometheus metrics |
| POLICY_ENGINE_ADDR | string | — | → | gRPC address of policy-engine (headless service) |
| POLICY_ENGINE_TIMEOUT_MS | int | 10 | → | Hard gRPC deadline for EvaluateAction |
| REDIS_URL | string | — | → | Redis for AIT cache, rate limits, revocation list |
| AIT_PUBKEY_CACHE_SIZE | int | 1000 | → | LRU cache entries for tenant public keys |
| AIT_PUBKEY_CACHE_TTL_SEC | int | 300 | → | TTL for cached tenant public keys |
| DLP_PATTERNS_PATH | string | /config/dlp_patterns.json | → | Path to DLP regex patterns file |
| INJECTION_PATTERNS_PATH | string | /config/injection_patterns.json | → | Path to Aho-Corasick injection patterns |
| AUDIT_KAFKA_TOPIC | string | pinaka.{tenantID}.enforcement.agent_actions | → | Topic pattern for audit events |
| AUDIT_LOCAL_BUFFER_PATH | string | /data/audit_buffer | → | Local badger DB path for Kafka fallback buffer |
| DEPLOYMENT_MODE | string | SIDECAR | → | INLINE_PROXY|SIDECAR|STANDALONE|API_HOOK|OUT_OF_BAND |
| §4  Discovery Engine — Low Level Design | Go 1.22  ·  Python 3.12  ·  Temporal  ·  Vault |
| --- | --- |
| Responsibility | Continuously discover all AI agents across connected systems. Issue and manage AITs. Build and maintain the agent dependency graph. Detect shadow agents via OAuth grant analysis. Run scheduled Temporal scan workflows. |
| --- | --- |
| // pkg/connector/sdk/connector.go  — the interface all connectors must implement

type Connector interface {
    // Metadata about this connector
    Type() ConnectorType // aws-bedrock | azure-openai | openai | anthropic | mcp | etc.
    Version() string

    // Connect validates credentials and establishes session. Called on startup + after rotation.
    Connect(ctx context.Context, credentials Credentials) error

    // Discover returns a complete snapshot of all agents in this source system.
    // Called by Temporal DiscoveryScanWorkflow.ConnectorDiscoverActivity.
    Discover(ctx context.Context) ([]AgentRecord, error)

    // StreamEvents streams real-time agent action events (for inline connectors).
    // Optional: connectors that cannot stream return ErrStreamNotSupported.
    StreamEvents(ctx context.Context) (<-chan AgentEvent, error)

    // PollEvents returns events since the given timestamp (for polling connectors).
    PollEvents(ctx context.Context, since time.Time) ([]AgentEvent, error)

    // HealthCheck returns connector health and last sync time.
    HealthCheck(ctx context.Context) ConnectorHealth

    // Disconnect gracefully releases the connection.
    Disconnect(ctx context.Context) error
}

type AgentRecord struct {
    SourceAgentID  string    // ID in the source system (e.g., AWS Bedrock agent ARN)
    Name           string
    AgentType      string    // LangChain/OpenAI | AWS Bedrock Agent | etc.
    Framework      string
    OwnerEmail     string
    Tools          []ToolRecord
    DataSources    []DataSourceRecord
    DeployedAt     time.Time
    LastActiveAt   *time.Time
    Fingerprint    string    // SHA-256(agent config + code hash)
    RawMetadata    map[string]any // source-system-specific metadata
}

type ConnectorHealth struct {
    Status         HealthStatus // HEALTHY | DEGRADED | UNHEALTHY
    LastSyncAt     *time.Time
    ErrorMessage   string?
    AgentCount     int
} |
| --- |
| // internal/ait/issuer.go

type AITIssuer struct {
    vaultClient  vault.Client
    aitRepo      AITRepository
    tokenTTL     time.Duration // default 90 days
}

// IssueAIT creates a new Agent Identity Token for a newly registered agent.
// The AIT is signed with the tenant's Ed25519 private key stored in Vault.
// Returns the AIT JWT string (plaintext — shown once; not stored).
func (i *AITIssuer) IssueAIT(ctx context.Context, req IssueAITRequest) (string, error) {
    // 1. Fetch tenant signing key (short-lived Vault lease: 60s)
    privKey, lease, err := i.vaultClient.GetTenantSigningKey(ctx, req.TenantID)
    if err != nil { return '', fmt.Errorf('vault key fetch: %w', err) }
    defer i.vaultClient.RevokeLease(ctx, lease.ID) // release lease immediately after signing

    // 2. Build AIT claims
    now := time.Now()
    claims := AITClaims{
        AITID:       uuid.NewV7().String(),
        TenantID:    req.TenantID,
        AgentID:     req.AgentID,
        Fingerprint: req.Fingerprint,
        GrantedTools: req.GrantedTools,
        IssuedAt:    now.Unix(),
        ExpiresAt:   now.Add(i.tokenTTL).Unix(),
    }

    // 3. Sign with Ed25519
    aitToken, err := jwt.SignedWithEd25519(claims, privKey)
    if err != nil { return '', err }

    // 4. Store AIT hash in registry (never store plaintext)
    aitHash := sha256hex(aitToken)
    err = i.aitRepo.CreateAIT(ctx, AITRecord{
        ID:          claims.AITID,
        TenantID:    req.TenantID,
        AgentID:     req.AgentID,
        AITHash:     aitHash,
        Fingerprint: req.Fingerprint,
        GrantedTools: req.GrantedTools,
        IssuedBy:    req.IssuedByUserID,
        IssuedAt:    now,
        ExpiresAt:   now.Add(i.tokenTTL),
    })

    return aitToken, err // plaintext AIT returned once; caller shows to admin
} |
| --- |
| // internal/shadow/detector.go
// Detects AI agents deployed without Pinaka registration
// by analysing enterprise IdP OAuth grants

type ShadowAgentDetector struct {
    graphClient   graph.Client  // Microsoft Graph API / Google Workspace Admin SDK
    agentRegistry AgentRegistry // Known registered agents
    redis         redis.Client  // Cache of seen OAuth grants
}

// DetectShadowAgents is called as a Temporal activity in DiscoveryScanWorkflow.
func (d *ShadowAgentDetector) DetectShadowAgents(ctx context.Context, tenantID string) ([]ShadowAgentRecord, error) {
    // 1. Fetch all OAuth grants from enterprise IdP
    grants, err := d.graphClient.ListOAuthGrants(ctx, tenantID)
    if err != nil { return nil, err }

    var shadows []ShadowAgentRecord
    for _, grant := range grants {
        // Skip: non-AI apps (filter by known AI app client IDs)
        if !isKnownAIApp(grant.ClientID) { continue }

        // Skip: already in Pinaka registry
        if d.agentRegistry.IsRegistered(ctx, tenantID, grant.ClientID) { continue }

        // Skip: already alerted in last 24h (Redis deduplicate)
        cacheKey := fmt.Sprintf('shadow_seen:%s:%s', tenantID, grant.ClientID)
        if seen, _ := d.redis.Exists(ctx, cacheKey).Result(); seen > 0 { continue }

        shadows = append(shadows, ShadowAgentRecord{
            ClientID:    grant.ClientID,
            AppName:     grant.AppDisplayName,
            GrantedBy:   grant.UserPrincipalName,
            GrantedAt:   grant.ConsentDateTime,
            Scopes:      grant.Scopes,
            RiskHint:    classifyOAuthScopes(grant.Scopes),
        })
        d.redis.Set(ctx, cacheKey, '1', 24*time.Hour) // prevent duplicate alerts
    }
    return shadows, nil
} |
| --- |
| Error Code | HTTP | gRPC | Description | Recovery Action |
| --- | --- | --- | --- | --- |
| AGENT_ALREADY_EXISTS | 409 | ALREADY_EXISTS | Agent with same name already registered in tenant | Use PUT to update; or choose unique name |
| FINGERPRINT_INVALID | 400 | INVALID_ARGUMENT | Fingerprint not valid SHA-256 hex string | Re-compute fingerprint: SHA-256(config + code hash) |
| CONNECTOR_CREDENTIALS_INVALID | 400 | INVALID_ARGUMENT | Connector credentials rejected by source system | Verify API key/OAuth token; test in source system console |
| CONNECTOR_NOT_FOUND | 404 | NOT_FOUND | Connector ID does not exist in tenant | Check connector_id; list connectors via GET /v1/connectors |
| SCAN_ALREADY_RUNNING | 409 | ALREADY_EXISTS | Discovery scan already in progress for this connector | Wait for scan to complete; check Temporal workflow status |
| AIT_ISSUANCE_FAILED | 500 | INTERNAL | Vault unreachable or key error during AIT signing | Check Vault health; alert SRE if persists >60s |
| SHADOW_AGENT_DETECTED | 200 | OK | Unregistered AI agent found via OAuth grants (informational) | Admin reviews and registers or blocks the agent |
| Env Variable | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| VAULT_ADDR | string | — | → | HashiCorp Vault address |
| VAULT_ROLE | string | discovery-engine | → | Vault AppRole for IRSA auth |
| AIT_DEFAULT_TTL_DAYS | int | 90 | → | Default AIT validity period |
| TEMPORAL_HOST | string | — | → | Temporal server address |
| TEMPORAL_TASK_QUEUE | string | pinaka-discovery | → | Temporal task queue name |
| SCAN_INTERVAL_MIN | int | 60 | → | Default discovery scan interval per connector (minutes) |
| SHADOW_DETECT_ENABLED | bool | true | → | Enable OAuth grant shadow agent detection |
| GRAPH_API_ENDPOINT | string | https://graph.microsoft.com/v1.0 | → | Microsoft Graph API for shadow agent detection |
| MAX_CONCURRENT_CONNECTOR_SCANS | int | 5 | → | Max connectors scanned in parallel per workflow |
| NEO4J_URI | string | — | → | Neo4j Bolt URI for dependency graph updates |
| NEO4J_USER | string | neo4j | → | Neo4j username (from ESO) |
| KAFKA_DISCOVERY_TOPIC | string | pinaka.{tenantID}.discovery.agent_lifecycle | → | Kafka topic for agent lifecycle events |
| Pattern | Every connector follows this pattern. AWS Bedrock is the P0 reference implementation. Study this before building any other connector. |
| --- | --- |
| // services/discovery-engine/connectors/aws_bedrock/bedrock_connector.go

package bedrock

import (
    sdk 'github.com/pinaka-ai/pinaka/pkg/connector/sdk'
    'github.com/aws/aws-sdk-go-v2/service/bedrock'
    'github.com/aws/aws-sdk-go-v2/service/bedrockagent'
)

type BedrockConnector struct {
    agentClient  *bedrockagent.Client
    rtClient     *bedrock.Client
    region       string
    tenantID     string
}

func (c *BedrockConnector) Type() sdk.ConnectorType { return 'aws-bedrock' }
func (c *BedrockConnector) Version() string { return 'v1.0.0' }

// Connect: validate IAM credentials have required permissions
func (c *BedrockConnector) Connect(ctx context.Context, creds sdk.Credentials) error {
    cfg, err := config.LoadDefaultConfig(ctx,
        config.WithRegion(c.region),
        config.WithCredentialsProvider(credsFromVault(creds)),
    )
    if err != nil { return fmt.Errorf('aws config: %w', err) }
    c.agentClient = bedrockagent.NewFromConfig(cfg)

    // Validate: list one agent (confirm read permission)
    _, err = c.agentClient.ListAgents(ctx, &bedrockagent.ListAgentsInput{MaxResults: aws.Int32(1)})
    return err
}

// Discover: return all Bedrock Agents in the connected account+region
func (c *BedrockConnector) Discover(ctx context.Context) ([]sdk.AgentRecord, error) {
    var records []sdk.AgentRecord
    paginator := bedrockagent.NewListAgentsPaginator(c.agentClient, &bedrockagent.ListAgentsInput{})

    for paginator.HasMorePages() {
        page, err := paginator.NextPage(ctx)
        if err != nil { return nil, fmt.Errorf('list bedrock agents: %w', err) }

        for _, summary := range page.AgentSummaries {
            // Fetch full agent details (includes action groups / tools)
            detail, err := c.agentClient.GetAgent(ctx, &bedrockagent.GetAgentInput{
                AgentId: summary.AgentId,
            })
            if err != nil { continue } // log and skip — don't fail full scan

            records = append(records, sdk.AgentRecord{
                SourceAgentID: aws.ToString(summary.AgentId),
                Name:          aws.ToString(summary.AgentName),
                AgentType:     'AWS Bedrock Agent',
                Framework:     'AWS Bedrock',
                OwnerEmail:    resolveOwnerEmail(detail.Agent.ClientToken), // from tags
                Tools:         extractActionGroupTools(detail.Agent.ActionGroups),
                DeployedAt:    aws.ToTime(detail.Agent.CreatedAt),
                Fingerprint:   computeFingerprint(detail.Agent),
                RawMetadata: map[string]any{
                    'agent_arn':       aws.ToString(summary.AgentArn),
                    'foundation_model': aws.ToString(detail.Agent.FoundationModel),
                    'agent_version':   aws.ToString(detail.Agent.AgentVersion),
                },
            })
        }
    }
    return records, nil
}

func (c *BedrockConnector) HealthCheck(ctx context.Context) sdk.ConnectorHealth {
    _, err := c.agentClient.ListAgents(ctx, &bedrockagent.ListAgentsInput{MaxResults: aws.Int32(1)})
    if err != nil {
        return sdk.ConnectorHealth{Status: sdk.Unhealthy, ErrorMessage: err.Error()}
    }
    return sdk.ConnectorHealth{Status: sdk.Healthy}
} |
| --- |
| §5  AISPM Engine — Low Level Design | Python 3.12  ·  FastAPI  ·  TimescaleDB  ·  Neo4j |
| --- | --- |
| Responsibility | Continuously calculate and maintain risk scores for all agents (5-dimension model). Serve the Agentic Risk Map (ARM) data for the console. Publish risk score changes to Kafka. Support blast radius simulation. |
| --- | --- |
| # aispm_engine/scoring/calculator.py
from dataclasses import dataclass
from typing import Optional
import asyncio

@dataclass
class RiskDimension:
    name: str
    raw_score: float   # 0.0 – 100.0
    weight: float
    signals: list[str] # what contributed to this score (for explainability)

@dataclass
class RiskScore:
    agent_id: str
    tenant_id: str
    composite: int       # 0–100 (rounded weighted sum)
    tier: str            # CRITICAL|HIGH|MEDIUM|LOW|MINIMAL
    dimensions: list[RiskDimension]
    blast_radius: int    # number of downstream nodes reachable
    trigger_event_id: Optional[str]
    trigger_type: str    # POLICY_VIOLATION|DISCOVERY_SCAN|INVESTIGATION_FINDING|MANUAL

class RiskCalculator:
    WEIGHTS = {
        'permission_scope': 0.25,
        'data_access': 0.25,
        'blast_radius': 0.20,
        'autonomy': 0.15,
        'policy_compliance': 0.15,
    }

    # Tool sensitivity scoring constants
    TOOL_SENSITIVITY = {'READ': 1, 'WRITE': 3, 'EXECUTE': 5, 'ADMIN': 10}
    ACCESS_TYPE_WEIGHT = {'INTERNAL': 1.0, 'MCP_SERVER': 1.5, 'EXTERNAL': 2.0}
    DATA_TIER_SCORE = {'PUBLIC': 0, 'INTERNAL': 10, 'REGULATED': 30, 'IP': 50, 'PII': 70, 'FINANCIAL': 90}
    NODE_CRITICALITY = {'AGENT': 20, 'DATA_SOURCE': 15, 'MCP_SERVER': 10, 'TOOL': 5}
    AUTONOMY_MAP = {0: 0, 1: 20, 2: 40, 3: 60, 4: 80, 5: 100}
    VIOLATION_SEVERITY = {'CRITICAL': 25, 'HIGH': 15, 'MEDIUM': 8, 'LOW': 3}

    def recency_decay(self, occurred_at: datetime) -> float:
        '''Violations decay from 1.0 (today) to 0.1 (30 days ago) exponentially.'''
        days_ago = (datetime.utcnow() - occurred_at).days
        return max(0.1, 1.0 * (0.9 ** days_ago))

    async def calculate(self, agent_id: str, tenant_id: str,
                         trigger_event_id: str, trigger_type: str) -> RiskScore:
        # Fetch all required data concurrently
        tools, sources, violations, agent, blast = await asyncio.gather(
            self.db.get_agent_tools(agent_id),
            self.db.get_agent_data_sources(agent_id),
            self.db.get_recent_violations(agent_id, days=30),
            self.db.get_agent(agent_id),
            self.neo4j.bfs_blast_radius(agent_id, max_depth=5)
        )

        d_permission = self._score_permission(tools)
        d_data       = self._score_data_access(sources)
        d_blast      = self._score_blast_radius(blast)
        d_autonomy   = self.AUTONOMY_MAP[agent.autonomy_level]
        d_compliance = self._score_compliance(violations)

        composite = round(sum(
            self.WEIGHTS[k] * v for k, v in {
                'permission_scope': d_permission, 'data_access': d_data,
                'blast_radius': d_blast, 'autonomy': d_autonomy,
                'policy_compliance': d_compliance,
            }.items()
        ))

        return RiskScore(
            agent_id=agent_id, tenant_id=tenant_id,
            composite=composite, tier=self._tier(composite),
            dimensions=[
                RiskDimension('permission_scope', d_permission, 0.25, self._perm_signals(tools)),
                RiskDimension('data_access', d_data, 0.25, self._data_signals(sources)),
                RiskDimension('blast_radius', d_blast, 0.20, [f'{len(blast)} nodes reachable']),
                RiskDimension('autonomy', d_autonomy, 0.15, [f'Level {agent.autonomy_level}']),
                RiskDimension('policy_compliance', d_compliance, 0.15, self._viol_signals(violations)),
            ],
            blast_radius=len(blast),
            trigger_event_id=trigger_event_id, trigger_type=trigger_type,
        )

    def _score_permission(self, tools: list) -> float:
        if not tools: return 0.0
        entropy = sum(
            self.TOOL_SENSITIVITY.get(t.access_type, 1) *
            self.ACCESS_TYPE_WEIGHT.get(t.destination_type, 1.0)
            for t in tools
        ) / len(tools)
        return min(entropy / 10.0 * 100, 100.0)

    def _tier(self, score: int) -> str:
        if score >= 80: return 'CRITICAL'
        if score >= 60: return 'HIGH'
        if score >= 40: return 'MEDIUM'
        if score >= 20: return 'LOW'
        return 'MINIMAL' |
| --- |
| # aispm_engine/arm/builder.py
# Builds the ARM graph data for D3.js visualisation

class ARMDataBuilder:
    async def build(self, tenant_id: str,
                     agent_filter: Optional[str] = None,
                     max_depth: int = 3) -> ARMResponse:
        # 1. Fetch all agents for tenant from PostgreSQL
        agents = await self.db.get_agents(tenant_id, status_filter=['ACTIVE','QUARANTINE'])

        # 2. For each agent, get connected nodes from Neo4j (batch query)
        node_ids = [a.id for a in agents]
        graph_data = await self.neo4j.get_subgraph(
            node_ids, max_depth=max_depth, tenant_id=tenant_id
        )

        # 3. Get risk scores for all agents from TimescaleDB (latest per agent)
        risk_scores = await self.timescale.get_latest_scores(tenant_id)
        score_map = {s.agent_id: s for s in risk_scores}

        # 4. Build node list
        nodes = []
        for agent in agents:
            score = score_map.get(agent.id)
            nodes.append(ARMNode(
                id=agent.id, type='AGENT', label=agent.name,
                risk_score=score.composite if score else 0,
                risk_tier=score.tier if score else 'MINIMAL',
                blast_radius=score.blast_radius if score else 0,
                is_quarantine=(agent.status == 'QUARANTINE'),
            ))
        # Add tool, data source, MCP server nodes from graph_data
        for n in graph_data.non_agent_nodes:
            nodes.append(ARMNode(
                id=n.id, type=n.type, label=n.name,
                sensitivity_tier=n.sensitivity_tier,
            ))

        # 5. Build edge list
        edges = [ARMEdge(
            source=e.source_id, target=e.target_id,
            type=e.relationship_type,
            permission_level=e.permission_level,
            is_approved=e.is_approved,
        ) for e in graph_data.edges]

        return ARMResponse(nodes=nodes, edges=edges,
            metadata=ARMMetadata(total_agents=len(agents), max_depth=max_depth)) |
| --- |
| Error Code | HTTP | gRPC | Description | Recovery Action |
| --- | --- | --- | --- | --- |
| AGENT_NOT_FOUND | 404 | NOT_FOUND | Agent ID not in this tenant's inventory | Verify agent_id; may have been deleted |
| NEO4J_UNAVAILABLE | 503 | UNAVAILABLE | Neo4j connection failed during blast radius calculation | Retry after 30s; use cached score if available; alert SRE |
| RISK_SCORE_STALE | 200 | OK | Score not recalculated in >24h (informational) | Trigger manual rescore: POST /v1/risk/scores/{agent_id}/recalculate |
| ARM_MAX_DEPTH_EXCEEDED | 400 | INVALID_ARGUMENT | max_depth >5 not permitted (performance limit) | Use max_depth ≤5; use pagination for deep graphs |
| Env Variable | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| DATABASE_URL | string | — | → | PostgreSQL URL for agent inventory |
| TIMESCALE_URL | string | — | → | TimescaleDB URL for risk score hypertable |
| NEO4J_URI | string | — | → | Neo4j Bolt URI |
| NEO4J_PASSWORD | string | — | → | Neo4j password (from ESO) |
| BLAST_RADIUS_MAX_DEPTH | int | 5 | → | Maximum BFS depth for blast radius calculation |
| RISK_RESCORE_DEBOUNCE_SEC | int | 60 | → | Min seconds between rescores for same agent (prevent thrashing) |
| KAFKA_RISK_TOPIC | string | pinaka.{tenantID}.risk.score_updates | → | Publish risk score changes here |
| ARM_CACHE_TTL_SEC | int | 30 | → | Redis TTL for ARM graph data (hot cache for console polling) |
| ARM_MAX_NODES | int | 500 | → | Max nodes returned in ARM response (pagination for large tenants) |
| §6  Audit Service — Low Level Design | Go 1.22  ·  Kafka  ·  Apache Iceberg  ·  OpenSearch |
| --- | --- |
| Responsibility | Consume all platform events from Kafka. Sign each event with Ed25519 + hash chain. Write immutably to Iceberg on S3 (WORM). Index in OpenSearch for search. Serve audit query API including NL→SQL translation via Bedrock. |
| --- | --- |
| // internal/audit/types.go

type AuditEvent struct {
    EventID             string            // UUID v7 — time-sortable
    SchemaVersion       int               // current: 1
    TenantID            string            // * partition key
    AgentID             string            // * the acting agent
    AITID               string            // * AIT used
    EventType           AuditEventType    // see enum below
    Timestamp           time.Time         // nanosecond precision UTC
    ActionSummary       string            // 512-char NL description (auto-generated)
    PolicyDecision      Decision          // ALLOW|DENY|ESCALATE|NA
    PolicyIDsEvaluated  []string
    WinningPolicyID     string?
    RiskDelta           int               // score change from this event
    RiskScoreAfter      int               // agent score after event
    RegulatoryTags      []string          // EU_AI_ACT_ART14, NIST_MAP_1, OWASP_LLM01, etc.
    ToolName            string?
    Destination         string?           // INTERNAL|EXTERNAL|MCP_SERVER|AGENT
    DataClassifications []string
    EnforcementMode     string            // INLINE|SIDECAR|API_HOOK|OUT_OF_BAND
    ApproverID          string?           // for HITL events
    ApprovalLatencyMs   int?
    Metadata            map[string]any    // action-specific: tool params redacted
    // Chain integrity (set by audit-service, NOT by caller)
    HashPrev            string            // SHA-256(prev event_id + prev signature)
    Signature           string            // Ed25519(all_above_fields_canonicalized)
}

type AuditEventType string
const (
    EventToolCall         AuditEventType = "TOOL_CALL"
    EventDataAccess       AuditEventType = "DATA_ACCESS"
    EventAgentMessage     AuditEventType = "AGENT_MSG"
    EventPolicyDecision   AuditEventType = "POLICY_DECISION"
    EventHITLRequest      AuditEventType = "HITL_REQUEST"
    EventHITLResponse     AuditEventType = "HITL_RESPONSE"
    EventHITLTimeout      AuditEventType = "HITL_TIMEOUT"
    EventDiscoveryScan    AuditEventType = "DISCOVERY_SCAN"
    EventRiskScoreChange  AuditEventType = "RISK_SCORE_CHANGE"
    EventPolicyChange     AuditEventType = "POLICY_CHANGE"
    EventAITIssued        AuditEventType = "AIT_ISSUED"
    EventAITRevoked       AuditEventType = "AIT_REVOKED"
    EventUserAction       AuditEventType = "USER_ACTION"
    EventComplianceReport AuditEventType = "COMPLIANCE_REPORT"
) |
| --- |
| // internal/consumer/chain_writer.go
// Consumes Kafka events and writes to Iceberg with Ed25519 hash chain

type ChainWriter struct {
    signer        *ed25519.Signer      // tenant-specific signing key (Vault-backed)
    icebergWriter *iceberg.Writer      // Iceberg table writer
    chainStore    *ChainStore          // stores last event hash per tenant
    openSearch    opensearch.Client    // async index for search
    keyCache      *lru.Cache           // LRU: tenant signing keys (5min TTL)
}

// WriteEvent is called for each Kafka message (within Kafka transaction).
// The Kafka offset is committed ONLY after a successful Iceberg write.
func (w *ChainWriter) WriteEvent(ctx context.Context, raw []byte) error {
    // 1. Deserialize the Avro event from Kafka
    event, err := avro.Unmarshal(raw)
    if err != nil { return fmt.Errorf('avro unmarshal: %w', err) }

    // 2. Validate event (schema, required fields, tenant_id present)
    if err := validate(event); err != nil { return err }

    // 3. Fetch tenant signing key (LRU cache → Vault; 5min TTL)
    privKey, err := w.getSigningKey(ctx, event.TenantID)
    if err != nil { return err }

    // 4. Compute hash_prev: SHA-256 of last event's (event_id + signature)
    last, err := w.chainStore.GetLast(ctx, event.TenantID)
    if err != nil && !errors.Is(err, ErrNoLastEvent) { return err }
    if last != nil {
        event.HashPrev = sha256hex(last.EventID + last.Signature)
    }

    // 5. Sign the canonical representation of all fields
    canonical, err := canonicalize(event) // deterministic JSON (sorted keys)
    if err != nil { return err }
    event.Signature = base64(ed25519.Sign(privKey, canonical))

    // 6. Write to Iceberg (WORM S3 Object Lock applied by bucket policy)
    if err := w.icebergWriter.AppendRow(ctx, event.TenantID, event); err != nil {
        return fmt.Errorf('iceberg write: %w', err) // Kafka offset NOT committed
    }

    // 7. Update chain store (Redis: latest event_id + signature per tenant)
    w.chainStore.SetLast(ctx, event.TenantID, event.EventID, event.Signature)

    // 8. Index in OpenSearch (async — best effort, does not block commit)
    go w.openSearch.IndexAsync(ctx, event)

    return nil // Kafka offset committed by caller after this returns nil
} |
| --- |
| // internal/query/nl_query.go

type NLQueryEngine struct {
    bedrock    bedrock.Client    // AWS Bedrock for NL→structured translation
    openSearch opensearch.Client // Query execution
    iceberg    athena.Client     // For large exports (>10K events)
}

// QueryResult returned to the API caller
type QueryResult struct {
    QueryID       string
    Summary       string          // NL summary of results
    Events        []AuditEventSummary // top 100 matching events
    TotalMatches  int
    ExportURL     string?         // pre-signed S3 URL for full export (if >100 events)
    StructuredQuery string        // the SQL/DSL generated (for debugging)
}

func (e *NLQueryEngine) Execute(ctx context.Context, tenantID, nlQuery string) (QueryResult, error) {
    // 1. Translate NL → structured filter (Bedrock — sends ONLY the query text, no data)
    structuredFilter, err := e.translateNL(ctx, nlQuery)
    if err != nil { return QueryResult{}, err }

    // 2. Build OpenSearch DSL query from structured filter
    osDSL := buildOpenSearchDSL(tenantID, structuredFilter) // tenant_id is ALWAYS a filter

    // 3. Execute search (limited to 100 results for API response)
    hits, total, err := e.openSearch.Search(ctx, buildIndexPattern(tenantID), osDSL, 100)
    if err != nil { return QueryResult{}, err }

    // 4. Summarize results (Bedrock — sends event IDs + types + summaries, NOT raw content)
    summary, err := e.summarizeResults(ctx, hits, nlQuery)
    if err != nil { summary = fmt.Sprintf('%d matching events found', total) }

    // 5. Generate export URL if results > 100
    var exportURL string
    if total > 100 {
        exportURL, _ = e.generateExport(ctx, tenantID, structuredFilter)
    }

    return QueryResult{
        QueryID: uuid.NewV7().String(),
        Summary: summary,
        Events:  hits,
        TotalMatches: total,
        ExportURL: exportURL,
        StructuredQuery: structuredFilter.String(),
    }, nil
}

// translateNL sends ONLY the NL query text to Bedrock — never sends audit event content
func (e *NLQueryEngine) translateNL(ctx context.Context, nlQuery string) (StructuredFilter, error) {
    prompt := fmt.Sprintf(`
Translate this natural language audit query into a structured filter JSON.
Output ONLY the JSON — no explanation. Query: %s`,
        nlQuery)

    resp, err := e.bedrock.InvokeModel(ctx, BedrockRequest{
        Model:  'anthropic.claude-3-5-sonnet-20241022-v2:0',
        Prompt: prompt,
        MaxTokens: 200,
        Temperature: 0.0, // fully deterministic translation
    })
    if err != nil { return StructuredFilter{}, err }

    var filter StructuredFilter
    return filter, json.Unmarshal(resp.Content, &filter)
} |
| --- |
| Error Code | HTTP | gRPC | Description | Recovery Action |
| --- | --- | --- | --- | --- |
| AUDIT_WRITE_FAILED | 500 | INTERNAL | Iceberg write to S3 failed; Kafka offset not committed | Event retried automatically; SRE alerted if >5 failures/min |
| CHAIN_INTEGRITY_VIOLATED | 500 | INTERNAL | Hash chain broken — previous event not found | CRITICAL: halt writes; alert security team; forensic investigation |
| NL_QUERY_TRANSLATION_FAILED | 400 | INVALID_ARGUMENT | Bedrock could not parse NL query into structured filter | Try rephrasing the query; check Bedrock quota |
| EXPORT_SIZE_EXCEEDED | 400 | INVALID_ARGUMENT | Export >1M events not permitted via API | Use Athena direct query for large exports |
| Env Variable | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| KAFKA_CONSUMER_GROUP | string | audit-consumer | → | Kafka consumer group ID |
| KAFKA_TOPICS | string | pinaka.*.enforcement.*,pinaka.*.discovery.*,pinaka.*.hitl.*,pinaka.*.risk.* | → | Topic subscription pattern |
| ICEBERG_WAREHOUSE_URI | string | s3://pinaka-audit-{region}/warehouse | → | Iceberg S3 warehouse location |
| ICEBERG_CATALOG_URI | string | — | → | Iceberg REST catalog endpoint (Glue Catalog) |
| OPENSEARCH_ENDPOINT | string | — | → | OpenSearch domain endpoint |
| BEDROCK_MODEL_ID | string | anthropic.claude-3-5-sonnet-20241022-v2:0 | → | Model for NL query translation |
| CHAIN_STORE_REDIS_URL | string | — | → | Redis for hash chain state per tenant |
| SIGNING_KEY_CACHE_TTL_SEC | int | 300 | → | LRU cache TTL for tenant Ed25519 private keys |
| MAX_NL_QUERY_RESULT_SIZE | int | 100 | → | Max events returned in NL query response (export URL for more |
| Partition Level | Field | Strategy | Rationale | Files Created |
| --- | --- | --- | --- | --- |
| Level 1 | tenant_id | IDENTITY partition by tenant_id | Tenant isolation — each tenant's data in separate files; enables tenant-specific retention policies | 1 directory per tenant |
| Level 2 | date(timestamp) | DAY partition by event date | Time-range queries on date boundaries; rollover to UltraWarm by date; partition pruning for NL queries | 1 directory per day per tenant |
| File format | — | Parquet (binary columnar) | OpenSearch indexing reads Parquet; Athena queries Parquet; 3–10× compression over JSON | ~50–200MB files (post-compaction) |
| Small file problem | — | Iceberg compaction via Spark EMR (daily 3am UTC) | Streaming writes create many small files; compaction merges into optimal Parquet files; no performance degradation | Target: 128MB per file post-compact |
| S3 Object Lock | — | COMPLIANCE mode, 7-year lock on all partition files | Regulatory requirement: WORM audit trail; no modification or deletion possible during lock period | Applies on first write; lock cannot be shortened |
| Schema evolution | — | Iceberg add_column, rename_column (no migration file needed) | New fields added to AuditEvent schema don't require rewriting historical data; Iceberg handles backward compatibility | Zero-downtime schema change |
| §7  Investigation Engine — Low Level Design | Python 3.12  ·  scikit-learn  ·  FastAPI  ·  AWS Bedrock |
| --- | --- |
| Responsibility | Continuous behavioural baselining (online EMA). Anomaly detection (5 detectors). Cross-agent collusion detection. Business-context risk narrative generation (Bedrock). Publish investigation findings to Kafka. |
| --- | --- |
| # investigation_engine/baseline/store.py
from abc import ABC, abstractmethod

class BaselineStore(ABC):
    '''Persistent store for per-agent behavioural baselines.'''

    @abstractmethod
    async def get(self, agent_id: str) -> Optional[AgentBaseline]: ...

    @abstractmethod
    async def upsert(self, baseline: AgentBaseline) -> None: ...

    @abstractmethod
    async def delete(self, agent_id: str) -> None: ...

# RedisBaselineStore — concrete implementation
# Key: baseline:{agent_id}  Value: msgpack(AgentBaseline)  TTL: 35 days (rolling)
class RedisBaselineStore(BaselineStore):
    KEY_PREFIX = 'baseline'
    TTL_SECONDS = 35 * 24 * 3600  # 35 days rolling window

    async def get(self, agent_id: str) -> Optional[AgentBaseline]:
        data = await self.redis.get(f'{self.KEY_PREFIX}:{agent_id}')
        return msgpack.loads(data) if data else None

    async def upsert(self, baseline: AgentBaseline) -> None:
        await self.redis.setex(
            f'{self.KEY_PREFIX}:{baseline.agent_id}',
            self.TTL_SECONDS,
            msgpack.dumps(baseline),
        ) |
| --- |
| # investigation_engine/detectors/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class AnomalyFinding:
    detector: str        # detector name
    severity: str        # CRITICAL|HIGH|MEDIUM|LOW
    z_score: float       # statistical deviation (if applicable)
    description: str     # human-readable finding
    signals: list[str]   # specific signals that triggered this

class AnomalyDetector(ABC):
    @abstractmethod
    async def detect(
        self,
        event: AgentActionEvent,
        baseline: AgentBaseline,
    ) -> Optional[AnomalyFinding]: ...


# ── CallRateDetector ──────────────────────────────────────────────────────
class CallRateDetector(AnomalyDetector):
    '''Online EMA-based call rate anomaly detection (Welford's algorithm).'''
    ALPHA = 0.05  # EMA decay — ~20 events to stabilise
    SIGMA_THRESHOLD = 3.0

    async def detect(self, event, baseline) -> Optional[AnomalyFinding]:
        key = (event.tool_name, event.destination)
        mu  = baseline.call_rate_ema.get(key, 0.0)
        var = baseline.call_rate_var.get(key, 1.0)

        # Update EMA (Welford's online variance)
        observed = 1.0  # one call observed
        delta = observed - mu
        new_mu  = mu + self.ALPHA * delta
        new_var = (1 - self.ALPHA) * (var + self.ALPHA * delta**2)
        baseline.call_rate_ema[key] = new_mu
        baseline.call_rate_var[key] = new_var
        baseline.n_samples += 1

        sigma = max(new_var**0.5, 0.01)
        z_score = abs(observed - new_mu) / sigma

        if z_score > self.SIGMA_THRESHOLD and baseline.n_samples > 20:
            return AnomalyFinding(
                detector='call_rate', severity=self._severity(z_score),
                z_score=z_score,
                description=f'Unusual call rate: {z_score:.1f}σ above baseline for {event.tool_name}',
                signals=[f'tool={event.tool_name}', f'dest={event.destination}', f'z={z_score:.1f}'],
            )
        return None

    def _severity(self, z: float) -> str:
        if z > 6: return 'CRITICAL'
        if z > 5: return 'HIGH'
        if z > 4: return 'MEDIUM'
        return 'LOW'


# ── CollusionDetector ─────────────────────────────────────────────────────
class CollusionDetector(AnomalyDetector):
    '''Detects coordinated anomalous behaviour across multiple agents.'''
    WINDOW_SEC = 300   # 5-minute window
    MIN_AGENTS = 3     # Minimum agents to flag collusion
    SIMILARITY_THRESHOLD = 0.85

    async def detect(self, event, baseline) -> Optional[AnomalyFinding]:
        # Fetch anomaly vectors for all agents in same tenant in last 5 min
        recent = await self.redis.zrangebyscore(
            f'anomaly_vectors:{event.tenant_id}',
            time.time() - self.WINDOW_SEC, time.time()
        )
        vectors = [msgpack.loads(r) for r in recent]
        if len(vectors) < self.MIN_AGENTS: return None

        # Compute pairwise cosine similarity of anomaly feature vectors
        current_vector = self._build_vector(event)
        similar_agents = [
            v for v in vectors
            if cosine_similarity(current_vector, v['vector']) > self.SIMILARITY_THRESHOLD
            and v['agent_id'] != event.agent_id
        ]

        if len(similar_agents) >= self.MIN_AGENTS - 1:
            return AnomalyFinding(
                detector='collusion', severity='HIGH',
                z_score=0.0,  # not applicable for collusion
                description=f'Agent collusion: {len(similar_agents)+1} agents showing correlated anomalous patterns',
                signals=[v['agent_id'] for v in similar_agents] + [event.agent_id],
            )
        return None |
| --- |
| Env Variable | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| KAFKA_CONSUMER_TOPICS | string | pinaka.*.enforcement.agent_actions,pinaka.*.risk.score_updates | → | Topics to consume for baselining |
| BASELINE_STORE_REDIS_URL | string | — | → | Redis URL for baseline storage |
| BASELINE_WINDOW_DAYS | int | 30 | → | Rolling baseline window in days |
| ANOMALY_SIGMA_THRESHOLD | float | 3.0 | → | Z-score threshold for call rate anomaly alert |
| COLLUSION_WINDOW_SEC | int | 300 | → | Time window for collusion detection |
| COLLUSION_MIN_AGENTS | int | 3 | → | Minimum agents to declare collusion |
| NARRATIVE_BEDROCK_MODEL | string | anthropic.claude-3-5-sonnet-20241022-v2:0 | → | Model for risk narrative generation |
| ISOLATION_FOREST_RETRAIN_CRON | string | 0 3 * * 0 | → | Weekly Isolation Forest retrain schedule (Sunday 3am UTC) |
| NARRATIVE_MAX_TOKENS | int | 400 | → | Max tokens for Bedrock narrative generation |
| KAFKA_FINDING_TOPIC | string | pinaka.{tenantID}.risk.investigation_findings | → | Publish investigation findings here |
| §8  Platform Service — Low Level Design | Go 1.22  ·  gRPC  ·  PostgreSQL  ·  Redis  ·  Vault |
| --- | --- |
| Responsibility | Authentication (JWT, API Key, SSO OIDC). Tenant provisioning and lifecycle. RBAC enforcement. Feature flag tenant context. User management. WebSocket connection management for real-time console updates. |
| --- | --- |
| Method / Function | Parameters | Returns | Error Conditions | Notes |
| --- | --- | --- | --- | --- |
| ValidateJWT(ctx, ValidateJWTRequest) → ValidateJWTResponse | jwt_token: string* | user_id, tenant_id, roles[], exp | INVALID_TOKEN, EXPIRED_TOKEN | Must complete <2ms (Redis cache hit path) |
| ValidateAIT(ctx, ValidateAITRequest) → ValidateAITResponse | ait_token: string*, fingerprint: string? | is_valid, tenant_id, agent_id, granted_tools[], expires_at | AIT_EXPIRED, AIT_REVOKED, FINGERPRINT_MISMATCH | Called by mcp-gateway on every request; must be <3ms |
| GetTenantContext(ctx, tenantContextRequest) → TenantContext | tenant_id: string* | region, plan_tier, feature_flags{}, enforcement_rps, failsafe_mode | TENANT_NOT_FOUND, TENANT_SUSPENDED | Redis-cached 120s; invalidated on any tenant config change |
| CheckRBAC(ctx, CheckRBACRequest) → CheckRBACResponse | user_id: string*, action: string*, resource: string* | allowed: bool, missing_role: string? | USER_NOT_FOUND | Evaluates against role_permissions table; no external calls |
| RefreshToken(ctx, RefreshTokenRequest) → RefreshTokenResponse | refresh_token: string* (hashed before lookup) | new_access_token, new_refresh_token, expires_at | TOKEN_INVALID, TOKEN_EXPIRED, TOKEN_REUSE_DETECTED | Single-use: old token atomically deleted before new issued |
| // internal/auth/jwt_issuer.go

type JWTIssuer struct {
    privateKey *rsa.PrivateKey  // RS256 private key from Vault
    keyID      string           // key ID for JWKS endpoint rotation
    accessTTL  time.Duration    // 15 minutes
    refreshTTL time.Duration    // 7 days
    redis      redis.Client
}

type AccessTokenClaims struct {
    jwt.RegisteredClaims                // iss, sub, exp, iat, jti
    TenantID    string   `json:'tid'`
    Roles        []string `json:'roles'`
    Plan         string   `json:'plan'`
    MFAVerified  bool     `json:'mfa'`  // true if MFA completed in this session
    MFAVerifiedAt *int64  `json:'mfa_at,omitempty'` // unix timestamp of last MFA
}

func (i *JWTIssuer) Issue(ctx context.Context, user User, tenant Tenant) (TokenPair, error) {
    now := time.Now()
    jti := uuid.NewV7().String()  // unique JWT ID (for revocation if needed)

    // Access token: RS256, 15-minute expiry
    accessClaims := AccessTokenClaims{
        RegisteredClaims: jwt.RegisteredClaims{
            Issuer:    'https://api.pinaka.ai',
            Subject:   user.ID,
            ExpiresAt: jwt.NewNumericDate(now.Add(i.accessTTL)),
            IssuedAt:  jwt.NewNumericDate(now),
            ID:        jti,
        },
        TenantID: tenant.ID,
        Roles:    user.Roles,
        Plan:     tenant.Plan,
        MFAVerified: user.MFAVerifiedRecently(),
    }
    accessToken, err := jwt.NewWithClaims(jwt.SigningMethodRS256, accessClaims).SignedString(i.privateKey)
    if err != nil { return TokenPair{}, err }

    // Refresh token: 256-bit random, 7-day expiry, stored in Redis (hashed)
    refreshToken := crypto.RandomHex(32)
    refreshHash := sha256hex(refreshToken)
    err = i.redis.Set(ctx,
        fmt.Sprintf('rt:%s', refreshHash),
        jsonMarshal(RefreshTokenRecord{UserID: user.ID, TenantID: tenant.ID}),
        i.refreshTTL,
    ).Err()

    return TokenPair{AccessToken: accessToken, RefreshToken: refreshToken}, err
} |
| --- |
| // internal/websocket/hub.go
// Per-tenant WebSocket hub: distributes risk score, HITL, and connector events

type Hub struct {
    tenants   sync.Map               // tenant_id → *TenantHub
    kafka     kafka.Consumer          // consumes risk.score_updates, hitl.requests, etc.
}

type TenantHub struct {
    clients   sync.Map               // connection_id → *WSClient
    broadcast chan WSMessage          // inbound events to broadcast to all clients
}

type WSClient struct {
    conn    *websocket.Conn
    send    chan WSMessage            // per-client send channel (buffered: 256)
    tenantID string
    userID  string
    connID  string                   // UUID v7 for dedup
}

// Subscribe adds a new WebSocket connection for a tenant.
func (h *Hub) Subscribe(ctx context.Context, conn *websocket.Conn, tenantID, userID string) {
    client := &WSClient{
        conn: conn, send: make(chan WSMessage, 256),
        tenantID: tenantID, userID: userID, connID: uuid.NewV7().String(),
    }
    hub, _ := h.tenants.LoadOrStore(tenantID, &TenantHub{broadcast: make(chan WSMessage, 1024)})
    hub.(*TenantHub).clients.Store(client.connID, client)

    go client.writePump() // sends messages from send channel to WebSocket
    go client.readPump()  // reads pings from client; sends pong; detects close
}

// Broadcast sends a message to all connected clients for a tenant.
func (h *Hub) Broadcast(tenantID string, msg WSMessage) {
    hub, ok := h.tenants.Load(tenantID)
    if !ok { return }
    hub.(*TenantHub).clients.Range(func(_, v any) bool {
        select {
        case v.(*WSClient).send <- msg:
        default:
            // Client slow — drop message (WS is best-effort)
        }
        return true
    })
} |
| --- |
| Env Variable | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| JWT_PRIVATE_KEY_VAULT_PATH | string | secret/pinaka/platform/jwt_private_key | → | Vault path for RS256 JWT signing key |
| JWT_ACCESS_TTL_MIN | int | 15 | → | Access token TTL in minutes |
| JWT_REFRESH_TTL_DAYS | int | 7 | → | Refresh token TTL in days |
| MFA_TOTP_WINDOW | int | 1 | → | TOTP validation window (±30s * window) |
| MFA_VALIDITY_MINUTES | int | 5 | → | How long MFA verification is valid for admin actions |
| SSO_DISCOVERY_CACHE_TTL_SEC | int | 3600 | → | OIDC discovery document cache TTL |
| WEBSOCKET_MAX_CLIENTS_PER_TENANT | int | 100 | → | Max concurrent WebSocket connections per tenant |
| WEBSOCKET_WRITE_DEADLINE_SEC | int | 10 | → | WebSocket write timeout |
| WEBSOCKET_PING_INTERVAL_SEC | int | 30 | → | WebSocket keepalive ping interval |
| TENANT_CONTEXT_CACHE_TTL_SEC | int | 120 | → | Redis TTL for tenant context cache |
| Message Type | Trigger | Payload | Consumer Action | Delivery Guarantee |
| --- | --- | --- | --- | --- |
| risk_score_update | Any risk score recalculation | {agent_id, new_score, new_tier, old_score, delta, timestamp} | React Query: update ['agents', agent_id] cache entry; ARM node colour changes immediately | Best-effort; console re-fetches on reconnect |
| hitl_request | New HITL request created | {request_id, agent_id, agent_name, action_summary, hitl_tier, timeout_at, decision_url} | Notification toast + badge increment on HITL tab; auto-navigate to HITL queue if tier>=2 | Best-effort; HITL queue re-fetched on reconnect |
| discovery_progress | Discovery scan in progress | {scan_id, connector_id, connector_name, progress_pct, agents_found, status} | Progress bar update in connector management UI; real-time scan status | Best-effort; final state fetched via REST on complete |
| connector_health | Connector health check fails | {connector_id, connector_name, status, error_message, last_healthy_at} | Alert toast + connector list badge; connector card colour changes to RED | Best-effort |
| policy_violation_alert | DENY or ESCALATE decision on CRITICAL-severity policy | {agent_id, agent_name, policy_id, policy_name, action_summary, risk_tier, timestamp} | Alert toast (red, sticky until dismissed); new entry in violation feed | Best-effort |
| ping | Server keepalive (every 30s) | {} | Client responds with pong (handled by WebSocket library) | Reliable — disconnect detected if no pong within 10s |
| §9  HITL Service — Low Level Design | Go 1.22  ·  PostgreSQL  ·  Redis  ·  Kafka |
| --- | --- |
| Responsibility | Manage the full lifecycle of Human-in-the-Loop approval requests: creation, timeout management, multi-party approval tracking, decision recording, and callback to MCP Gateway. |
| --- | --- |
| State | Trigger | Next State | Action Taken |
| --- | --- | --- | --- |
| PENDING | HITL request created | — | Notification dispatched; timer started; MCP Gateway holds request |
| PENDING → APPROVED | Human calls POST /v1/hitl/{id}/approve | APPROVED | Decision recorded; MCP Gateway callback sent (ALLOW action) |
| PENDING → DENIED | Human calls POST /v1/hitl/{id}/deny | DENIED | Decision recorded; MCP Gateway callback sent (DENY action) |
| PENDING → TIMED_OUT | Timer expires (tier-specific: T1=300s, T2=900s, T3=immediate) | TIMED_OUT | Auto-DENY callback sent; timeout_deny audit event written |
| PENDING → AUTO_APPROVED | Auto-promotion: action approved 10+ consecutive times | AUTO_APPROVED | Action allowed; promotion suggestion sent to admin |
| APPROVED/DENIED/TIMED_OUT | Terminal — no further transitions | — | Nothing; final state |
| // internal/hitl/manager.go

type HITLManager struct {
    db           HITLRepository
    redis        redis.Client       // session state + timeout tracking
    notifier     NotificationClient // dispatch notifications
    mcpCallback  MCPCallbackClient  // callback to MCP Gateway on decision
    auditPub     kafka.Producer     // publish HITL audit events
}

type HITLRequest struct {
    ID               string    // UUID v7
    TenantID         string
    AgentID          string
    DecisionID       string    // from policy engine
    ActionSummary    string
    ActionMetadata   map[string]any
    PolicyID         string
    Tier             int       // 1|2|3|4
    RequiredApprovers int      // 1 for T1/T2; configurable for T3
    ApprovalsReceived int
    TimeoutAt        time.Time
    Status           HITLStatus
    CallbackURL      string    // URL for MCP Gateway callback
}

func (m *HITLManager) Create(ctx context.Context, req HITLRequest) error {
    // 1. Write to PostgreSQL
    if err := m.db.Create(ctx, req); err != nil { return err }

    // 2. Register timeout in Redis sorted set (score = timeout unix timestamp)
    m.redis.ZAdd(ctx, 'hitl_timeouts', redis.Z{
        Score: float64(req.TimeoutAt.Unix()),
        Member: req.ID,
    })

    // 3. Store callback URL in Redis (TTL = timeout + 60s buffer)
    ttl := time.Until(req.TimeoutAt) + 60*time.Second
    m.redis.Set(ctx, fmt.Sprintf('hitl_cb:%s', req.ID), req.CallbackURL, ttl)

    // 4. Dispatch notifications
    m.notifier.Dispatch(ctx, req.TenantID, req.Tier, HITLNotification{
        RequestID: req.ID, AgentID: req.AgentID,
        ActionSummary: req.ActionSummary, TimeoutAt: req.TimeoutAt,
    })

    // 5. Publish audit event
    m.auditPub.PublishAsync(buildHITLRequestAuditEvent(req))
    return nil
}

func (m *HITLManager) Approve(ctx context.Context, requestID, approverID, notes string) error {
    req, err := m.db.GetByID(ctx, requestID)
    if err != nil { return err }
    if req.Status != HITLPending { return ErrHITLNotPending }

    // Atomic approval: increment approvals_received
    newCount, err := m.db.IncrementApprovals(ctx, requestID)
    if err != nil { return err }

    if newCount >= req.RequiredApprovers {
        // All required approvals received — transition to APPROVED
        m.db.UpdateStatus(ctx, requestID, HITLApproved, approverID, notes)
        m.sendCallback(ctx, requestID, 'ALLOW')
        m.redis.ZRem(ctx, 'hitl_timeouts', requestID) // cancel timeout
        m.auditPub.PublishAsync(buildHITLResponseAuditEvent(requestID, 'APPROVED', approverID))
    }
    // If newCount < required: approval recorded but waiting for more approvers
    return nil
}

// TimeoutChecker runs every 60 seconds (Kubernetes CronJob)
func (m *HITLManager) ProcessExpiredRequests(ctx context.Context) error {
    now := float64(time.Now().Unix())
    // Fetch all requests whose timeout has passed
    expired, _ := m.redis.ZRangeByScore(ctx, 'hitl_timeouts', &redis.ZRangeBy{
        Min: '-inf', Max: fmt.Sprintf('%f', now),
    }).Result()

    for _, requestID := range expired {
        m.db.UpdateStatus(ctx, requestID, HITLTimedOut, '', 'auto_timeout')
        m.sendCallback(ctx, requestID, 'DENY')
        m.redis.ZRem(ctx, 'hitl_timeouts', requestID)
        m.auditPub.PublishAsync(buildTimeoutAuditEvent(requestID))
    }
    return nil
} |
| --- |
| Env Variable | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| HITL_TIER1_TIMEOUT_SEC | int | 300 | → | T1 Soft Approval timeout (5 minutes; auto-ALLOW) |
| HITL_TIER2_TIMEOUT_SEC | int | 900 | → | T2 Hard Approval timeout (15 minutes; auto-DENY) |
| HITL_TIER3_TIMEOUT_SEC | int | 0 | → | T3 Multi-Party: immediate DENY if not approved; 0 = no auto-timeout (requires explicit deny) |
| HITL_TIER4_TIMEOUT_SEC | int | 0 | → | T4 Emergency Block: no timeout; Security Admin must unblock manually |
| HITL_DEFAULT_REQUIRED_APPROVERS | int | 1 | → | Default required approvals (T3 can override) |
| CALLBACK_TIMEOUT_SEC | int | 10 | → | Timeout for MCP Gateway callback HTTP call |
| TIMEOUT_CHECKER_INTERVAL_SEC | int | 60 | → | How often the timeout checker runs |
| KAFKA_HITL_REQUEST_TOPIC | string | pinaka.{tenantID}.hitl.requests | → | Topic for new HITL requests |
| KAFKA_HITL_RESPONSE_TOPIC | string | pinaka.{tenantID}.hitl.responses | → | Topic for decisions (consumed by mcp-gateway) |
| §10  Notification Service — Low Level Design | Go 1.22  ·  Kafka  ·  Slack/PagerDuty/SES/Twilio |
| --- | --- |
| Responsibility | Deliver all platform notifications across channels (Slack, Teams, Email, PagerDuty, SMS, Webhook). Implement delivery guarantees: at-least-once with retry + DLQ. Sign outbound webhooks with HMAC-SHA256. |
| --- | --- |
| // internal/dispatcher/dispatcher.go

type Channel interface {
    Name() string
    // Send delivers a notification. Returns nil on success, error on failure.
    // Must be idempotent: same notification_id should not send duplicate.
    Send(ctx context.Context, n Notification) error
}

type Notification struct {
    ID           string          // UUID v7 — used for idempotency
    TenantID     string
    Type         NotificationType // HITL_REQUEST|RISK_ALERT|CONNECTOR_DOWN|POLICY_VIOLATION|COMPLIANCE_REPORT
    Title        string
    Body         string          // plain text
    BodyHTML     string?         // HTML for email
    Severity     string          // INFO|WARNING|CRITICAL
    ActionURL    string?         // deep link into Pinaka console
    ActionLabel  string?         // button label
    Metadata     map[string]any  // channel-specific extras (e.g., PagerDuty dedup_key)
    CreatedAt    time.Time
}

// DispatcherEngine routes notifications to configured channels
type DispatcherEngine struct {
    channels   map[string]Channel  // channel_name → Channel
    tenantCfg  TenantNotifConfig  // per-tenant channel configuration
    redis      redis.Client        // for idempotency dedup
    dlq        kafka.Producer      // dead letter queue for failed deliveries
}

func (d *DispatcherEngine) Dispatch(ctx context.Context, n Notification) {
    // Get configured channels for this tenant + notification type
    targets := d.tenantCfg.GetChannels(n.TenantID, n.Type, n.Severity)

    for _, channelName := range targets {
        ch, ok := d.channels[channelName]
        if !ok { continue }

        // Idempotency: skip if already delivered on this channel
        dedupKey := fmt.Sprintf('notif_sent:%s:%s', n.ID, channelName)
        if d.redis.SetNX(ctx, dedupKey, '1', 24*time.Hour).Val() {
            go d.sendWithRetry(ctx, ch, n) // async delivery
        }
    }
}

func (d *DispatcherEngine) sendWithRetry(ctx context.Context, ch Channel, n Notification) {
    const maxRetries = 5
    for attempt := 0; attempt <= maxRetries; attempt++ {
        err := ch.Send(ctx, n)
        if err == nil { return }

        if attempt == maxRetries {
            // Write to DLQ after all retries exhausted
            d.dlq.Publish(ctx, 'pinaka.dlq.notification-consumer',
                DLQMessage{OriginalTopic: 'notifications', Event: n, Error: err.Error()})
            return
        }
        delay := time.Second * time.Duration(math.Pow(2, float64(attempt)))
        jitter := time.Duration(rand.Int63n(int64(delay/5)))
        time.Sleep(delay + jitter)
    }
} |
| --- |
| // internal/dispatcher/webhook_channel.go

type WebhookChannel struct {
    httpClient *http.Client  // with 10s timeout
}

func (w *WebhookChannel) Send(ctx context.Context, n Notification) error {
    endpoint, secret := w.getEndpointAndSecret(n.TenantID)

    body, _ := json.Marshal(WebhookPayload{
        NotificationID: n.ID,
        Type:           string(n.Type),
        Title:          n.Title,
        Body:           n.Body,
        Severity:       n.Severity,
        Timestamp:      n.CreatedAt.Unix(),
        ActionURL:      n.ActionURL,
    })

    // HMAC-SHA256 signature (customer verifies this)
    mac := hmac.New(sha256.New, []byte(secret))
    mac.Write(body)
    sig := hex.EncodeToString(mac.Sum(nil))

    req, _ := http.NewRequestWithContext(ctx, 'POST', endpoint, bytes.NewReader(body))
    req.Header.Set('Content-Type', 'application/json')
    req.Header.Set('X-Pinaka-Signature', 'sha256='+sig)
    req.Header.Set('X-Pinaka-Notification-ID', n.ID)

    resp, err := w.httpClient.Do(req)
    if err != nil { return err }
    defer resp.Body.Close()

    if resp.StatusCode < 200 || resp.StatusCode >= 300 {
        return fmt.Errorf('webhook returned %d', resp.StatusCode)
    }
    return nil
} |
| --- |
| Env Variable | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| SLACK_BOT_TOKEN_VAULT_PATH | string | secret/pinaka/notification/slack_bot_token | → | Vault path for Slack Bot OAuth token |
| PAGERDUTY_API_KEY_VAULT_PATH | string | secret/pinaka/notification/pagerduty_key | → | Vault path for PagerDuty Events API key |
| AWS_SES_FROM_EMAIL | string | alerts@pinaka.ai | → | SES sender address |
| TWILIO_ACCOUNT_SID_VAULT_PATH | string | secret/pinaka/notification/twilio_sid | → | Vault path for Twilio credentials |
| WEBHOOK_HTTP_TIMEOUT_SEC | int | 10 | → | HTTP timeout for webhook delivery attempts |
| MAX_RETRY_ATTEMPTS | int | 5 | → | Max delivery retries before DLQ |
| RETRY_BASE_DELAY_SEC | int | 1 | → | Base retry delay (doubles each attempt) |
| IDEMPOTENCY_WINDOW_HOURS | int | 24 | → | Redis dedup window for notification IDs |
| §11  Compliance Engine — Low Level Design | Python 3.12  ·  Temporal  ·  PostgreSQL  ·  PDF |
| --- | --- |
| Responsibility | Map Pinaka audit + policy data to regulatory frameworks (EU AI Act, NIST AI RMF, OWASP LLM Top 10, MITRE ATLAS, SOC 2). Generate exportable compliance reports. Maintain real-time compliance posture per framework. |
| --- | --- |
| # compliance_engine/mappers/framework_mapper.py

# Each framework mapper translates Pinaka events/policies → control evidence
class FrameworkMapper(ABC):
    @abstractmethod
    def framework_id(self) -> str: ...

    @abstractmethod
    async def map_event(self, event: AuditEvent) -> list[ControlEvidence]: ...
    # Returns list because one event may be evidence for multiple controls

    @abstractmethod
    async def get_control_status(self, tenant_id: str) -> list[ControlStatus]: ...
    # Returns current pass/fail status for each control in this framework


class EUAIActMapper(FrameworkMapper):
    def framework_id(self) -> str: return 'EU_AI_ACT_2024'

    # Control → Pinaka evidence mapping
    CONTROL_EVIDENCE_MAP = {
        'ART_9_RISK_MANAGEMENT': {
            'evidence_from': ['RISK_SCORE_CHANGE', 'AISPM_SCAN'],
            'required_signal': 'risk_score_computed',
            'description': 'Continuous AI risk management system operational',
        },
        'ART_13_TRANSPARENCY': {
            'evidence_from': ['POLICY_DECISION', 'AUDIT_TRAIL'],
            'required_signal': 'decision_logged_with_reason',
            'description': 'All AI agent decisions logged with reasoning',
        },
        'ART_14_HUMAN_OVERSIGHT': {
            'evidence_from': ['HITL_REQUEST', 'HITL_RESPONSE'],
            'required_signal': 'human_oversight_enabled',
            'description': 'Human-in-the-loop controls active for high-risk actions',
        },
        'ART_17_DOCUMENTATION': {
            'evidence_from': ['POLICY_CHANGE', 'AIT_ISSUED'],
            'required_signal': 'governance_documentation_maintained',
            'description': 'Technical documentation of AI systems maintained',
        },
    }

    async def map_event(self, event: AuditEvent) -> list[ControlEvidence]:
        evidences = []
        for control_id, mapping in self.CONTROL_EVIDENCE_MAP.items():
            if event.event_type in mapping['evidence_from']:
                evidences.append(ControlEvidence(
                    framework_id='EU_AI_ACT_2024',
                    control_id=control_id,
                    event_id=event.event_id,
                    timestamp=event.timestamp,
                    signal=mapping['required_signal'],
                    description=mapping['description'],
                ))
        return evidences |
| --- |
| # compliance_engine/report/generator.py
# Called as a Temporal activity in ComplianceReportWorkflow

class ReportGenerator:
    async def generate(
        self,
        tenant_id: str,
        framework_id: str,
        period_start: datetime,
        period_end: datetime,
        report_format: str,  # PDF | JSON | XLSX
    ) -> ReportResult:

        # 1. Collect evidence from audit OpenSearch
        evidence = await self.collect_evidence(tenant_id, framework_id, period_start, period_end)

        # 2. Get current control statuses
        controls = await self.mapper.get_control_status(tenant_id)

        # 3. Build report data model
        report = ComplianceReport(
            tenant_id=tenant_id,
            framework_id=framework_id,
            period=DateRange(period_start, period_end),
            generated_at=datetime.utcnow(),
            controls=controls,
            evidence_count=len(evidence),
            overall_status=self._overall_status(controls),
        )

        # 4. Render to requested format
        if report_format == 'PDF':
            output = await self.pdf_renderer.render(report, evidence)
        elif report_format == 'JSON':
            output = json.dumps(report.to_dict()).encode()
        else:
            output = await self.xlsx_renderer.render(report, evidence)

        # 5. Upload to S3 with pre-signed download URL (7-day expiry)
        key = f'compliance-reports/{tenant_id}/{framework_id}/{uuid.uuid4()}.{report_format.lower()}'
        await self.s3.put_object(Bucket='pinaka-reports', Key=key, Body=output)
        url = await self.s3.generate_presigned_url('get_object',
            Params={'Bucket': 'pinaka-reports', 'Key': key}, ExpiresIn=604800)

        return ReportResult(report_id=uuid7(), download_url=url, expires_at=7_days_from_now) |
| --- |
| Env Variable | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| SUPPORTED_FRAMEWORKS | string | EU_AI_ACT_2024,NIST_AI_RMF_1.0,OWASP_LLM_TOP10_2025,MITRE_ATLAS,SOC2_TSC | → | Comma-separated enabled frameworks |
| AUDIT_OPENSEARCH_ENDPOINT | string | — | → | OpenSearch for evidence collection |
| REPORT_S3_BUCKET | string | pinaka-reports-{region} | → | S3 bucket for generated reports |
| REPORT_URL_EXPIRY_DAYS | int | 7 | → | Pre-signed URL expiry for report downloads |
| TEMPORAL_TASK_QUEUE | string | pinaka-compliance | → | Temporal task queue for report workflows |
| POSTURE_CACHE_TTL_SEC | int | 300 | → | Redis TTL for compliance posture dashboard data |
| PDF_RENDER_TIMEOUT_SEC | int | 60 | → | PDF generation timeout (large reports can be slow) |
| §12  Console UI — Low Level Design | React 18  ·  TypeScript 5  ·  Zustand  ·  D3.js v7 |
| --- | --- |
| Responsibility | Browser application: agent inventory, risk map (ARM), policy editor, HITL approval queue, NL audit query, compliance dashboards, connector management. Real-time updates via WebSocket. Design system: shadcn/ui + Tailwind CSS. |
| --- | --- |
| // src/shared/store/authStore.ts
interface AuthState {
    user: User | null;
    tenantID: string | null;
    roles: Role[];
    plan: PlanTier;
    mfaVerified: boolean;
    // Actions
    setUser: (user: User, tenant: string, roles: Role[], plan: PlanTier) => void;
    setMFAVerified: (verified: boolean) => void;
    logout: () => void;
}
export const useAuthStore = create<AuthState>()(persist(
    (set) => ({ user: null, tenantID: null, roles: [], plan: 'STARTER', mfaVerified: false,
        setUser: (user, tenantID, roles, plan) => set({user, tenantID, roles, plan}),
        setMFAVerified: (v) => set({mfaVerified: v}),
        logout: () => set({user:null, tenantID:null, roles:[], mfaVerified:false}),
    }),
    { name: 'pinaka-auth', partialize: (s) => ({user: s.user, tenantID: s.tenantID, roles: s.roles}) }
))

// src/shared/store/wsStore.ts — WebSocket state
interface WSState {
    status: 'DISCONNECTED' | 'CONNECTING' | 'CONNECTED';
    lastEventAt: Date | null;
    reconnectAttempts: number;
    setStatus: (s: WSState['status']) => void;
    incrementReconnect: () => void;
    resetReconnect: () => void;
}
export const useWSStore = create<WSState>()((set) => ({
    status: 'DISCONNECTED', lastEventAt: null, reconnectAttempts: 0,
    setStatus: (status) => set({status}),
    incrementReconnect: () => set((s) => ({reconnectAttempts: s.reconnectAttempts + 1})),
    resetReconnect: () => set({reconnectAttempts: 0}),
}))

// src/shared/store/notificationStore.ts — in-app notifications
interface NotificationState {
    alerts: UIAlert[];
    addAlert: (alert: Omit<UIAlert, 'id' | 'createdAt'>) => void;
    dismissAlert: (id: string) => void;
} |
| --- |
| // src/shared/api/agents.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Fetch agent list with cursor-based pagination
export function useAgents(filters?: AgentFilters) {
    return useQuery({
        queryKey: ['agents', filters],
        queryFn: () => apiClient.get<AgentListResponse>('/v1/inventory/agents', {params: filters}),
        staleTime: 30_000,  // 30s — don't refetch while fresh
        refetchInterval: 60_000,  // poll every 60s for updates
    });
}

// Fetch single agent with risk score and dimensions
export function useAgent(agentID: string) {
    return useQuery({
        queryKey: ['agents', agentID],
        queryFn: () => apiClient.get<AgentDetail>(`/v1/inventory/agents/${agentID}`),
        staleTime: 15_000,
        enabled: !!agentID,
    });
}

// ARM graph data (force-directed graph)
export function useARM(maxDepth = 3) {
    return useQuery({
        queryKey: ['arm', maxDepth],
        queryFn: () => apiClient.get<ARMResponse>('/v1/risk/arm', {params: {max_depth: maxDepth}}),
        staleTime: 30_000,
        // Cache ARM data for 5 min — large query, expensive to recalculate
        gcTime: 300_000,
    });
}

// HITL queue with live updates
export function useHITLQueue() {
    const qc = useQueryClient();
    return useQuery({
        queryKey: ['hitl', 'pending'],
        queryFn: () => apiClient.get<HITLListResponse>('/v1/hitl?status=PENDING'),
        staleTime: 10_000,  // HITL is time-sensitive; fresher data
        // WebSocket updates trigger: qc.invalidateQueries({queryKey: ['hitl', 'pending']})
    });
}

// Approve HITL request (requires MFA-verified token)
export function useApproveHITL() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: ({id, notes}: {id:string, notes?:string}) =>
            apiClient.post(`/v1/hitl/${id}/approve`, {notes}),
        onSuccess: () => {
            qc.invalidateQueries({queryKey: ['hitl']});  // refresh HITL queue
            qc.invalidateQueries({queryKey: ['agents']}); // agent risk score may have changed
        },
    });
} |
| --- |
| // src/features/policies/PolicyEditor.tsx
// Visual + code (Rego) policy editor with real-time dry-run

interface PolicyEditorProps {
    policy?: Policy;       // existing policy (edit mode) or undefined (create mode)
    onSave: (p: Policy) => Promise<void>;
    onCancel: () => void;
}

export function PolicyEditor({policy, onSave, onCancel}: PolicyEditorProps) {
    const [regoSource, setRegoSource] = useState(policy?.regoSource ?? defaultRegoTemplate);
    const [dryRunResults, setDryRunResults] = useState<DryRunResult | null>(null);
    const [isShadowMode, setIsShadowMode] = useState(false);
    const runDryRun = useDryRunPolicy();

    // Debounced dry-run: runs automatically 2s after Rego changes stop
    const debouncedRego = useDebounce(regoSource, 2000);
    useEffect(() => {
        if (debouncedRego && policy?.tenantID) {
            runDryRun.mutate({regoSource: debouncedRego, tenantID: policy.tenantID});
        }
    }, [debouncedRego]);

    return (
        <div className='grid grid-cols-2 gap-4 h-full'>
            {/* Left: Rego code editor (Monaco) */}
            <div>
                <MonacoEditor language='rego' value={regoSource} onChange={setRegoSource}
                    options={{minimap: {enabled: false}, fontSize: 13}}
                />
                <ShadowModeToggle value={isShadowMode} onChange={setIsShadowMode} />
            </div>
            {/* Right: Dry-run impact panel */}
            <DryRunPanel results={dryRunResults} isLoading={runDryRun.isPending} />
        </div>
    );
}

// DryRunPanel shows: how many historical events would have been DENY/ESCALATE/ALLOW
function DryRunPanel({results, isLoading}: {results: DryRunResult|null, isLoading: boolean}) {
    if (isLoading) return <Spinner label='Running dry-run against last 30 days...' />;
    if (!results) return <EmptyState icon='shield' message='Edit Rego to see dry-run impact' />;
    return (
        <div>
            <StatCard label='Would DENY' value={results.denyCount} color='red' />
            <StatCard label='Would ESCALATE' value={results.escalateCount} color='amber' />
            <StatCard label='Would ALLOW' value={results.allowCount} color='green' />
            <AffectedAgentsList agents={results.affectedAgents} />
        </div>
    );
} |
| --- |
| Check | Command | Expected Output | If Fails |
| --- | --- | --- | --- |
| PostgreSQL connectivity | psql $DATABASE_URL -c 'SELECT 1' | psql: 1 (success) | Check Docker Compose postgres service; verify DATABASE_URL |
| Redis connectivity | redis-cli -u $REDIS_URL ping | PONG | Check ElastiCache/Redis container; verify REDIS_URL |
| Kafka topics created | kafka-topics.sh --list --bootstrap-server $KAFKA_URL | pinaka.dev-tenant.enforcement.agent_actions (and others) | Run: go run ./tools/pinaka-dev setup-kafka-topics |
| Vault token valid | vault token lookup | token: pinaka-dev-root-token | Restart Vault container; re-run seed-vault.sh |
| Policy engine responding | grpcurl -plaintext localhost:50051 pinaka.policy.v1.PolicyEngine/HealthCheck | healthy: true | Check policy-engine logs: docker compose logs policy-engine |
| MCP Gateway enforcement test | go run ./tools/pinaka-dev test-enforcement --tool=spreadsheet-read | decision: ALLOW in <500ms | Check mcp-gateway logs; verify policy-engine is reachable |
| DENY path works | go run ./tools/pinaka-dev test-enforcement --tool=email-send --dest=EXTERNAL --data-class=PII | decision: DENY; HTTP 403 | Verify L1 deny policy was seeded: check PostgreSQL policies table |
| Audit event written | go run ./tools/pinaka-dev check-audit --event-type=TOOL_CALL --limit=1 | 1 audit event found (signed) | Check audit-service logs; verify Iceberg writer connected to S3/local |
| Risk score calculated | curl localhost:8084/v1/risk/scores/dev-agent-001 | risk_score: integer 0–100 | Check aispm-engine logs; verify Neo4j is running |
| Neo4j graph populated | cypher-shell -u neo4j -p pinaka_dev 'MATCH (a:Agent) RETURN count(a)' | count(a) > 0 | Run: go run ./tools/pinaka-dev seed-graph |
| OPA policies loaded | grpcurl -plaintext -d '{...}' localhost:50051 pinaka.policy.v1.PolicyEngine/GetPolicyBundle | bundle data received | Check Redis: redis-cli keys 'policy_bundle:*' |
| Console UI loads | curl -s localhost:3000 | grep '<title>Pinaka' | HTML with Pinaka title | Run: cd console-ui && npm run dev |
| -- ═══════════════════════════════════════════════════════════════════════
-- HELPER FUNCTIONS
-- ═══════════════════════════════════════════════════════════════════════

-- Auto-update updated_at on any UPDATE
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

-- ═══════════════════════════════════════════════════════════════════════
-- USERS & TENANTS
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE tenants (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name              VARCHAR(255) NOT NULL,
    slug              VARCHAR(100) NOT NULL UNIQUE,  -- URL-safe tenant identifier
    plan_tier         VARCHAR(20)  NOT NULL DEFAULT 'STARTER'
                      CHECK (plan_tier IN ('STARTER','PROFESSIONAL','ENTERPRISE','ENTERPRISE_PLUS')),
    region            VARCHAR(20)  NOT NULL CHECK (region IN ('us-east-1','eu-west-1','ap-southeast-1')),
    vault_key_id      VARCHAR(255) NOT NULL,  -- reference to Vault Ed25519 key pair
    sso_domain        VARCHAR(255),
    failsafe_mode     VARCHAR(20)  NOT NULL DEFAULT 'DENY_ALL' CHECK (failsafe_mode IN ('DENY_ALL','ALLOW_WITH_ALERT')),
    enforcement_rps   INTEGER      NOT NULL DEFAULT 1000 CHECK (enforcement_rps > 0),
    feature_flags     JSONB        NOT NULL DEFAULT '{}',
    status            VARCHAR(20)  NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('PROVISIONING','ACTIVE','SUSPENDED','DELETED')),
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at        TIMESTAMPTZ
);
CREATE UNIQUE INDEX idx_tenants_slug ON tenants(slug) WHERE deleted_at IS NULL;
CREATE TRIGGER tenants_updated_at BEFORE UPDATE ON tenants FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE users (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email             VARCHAR(255) NOT NULL,
    display_name      VARCHAR(255),
    roles             TEXT[] NOT NULL DEFAULT '{}',  -- ['security_engineer','security_analyst']
    sso_subject       VARCHAR(255),  -- IdP sub claim (for SSO-linked accounts)
    mfa_secret        TEXT,          -- bcrypt of TOTP secret (encrypted at app layer)
    mfa_enabled       BOOLEAN NOT NULL DEFAULT FALSE,
    last_login_at     TIMESTAMPTZ,
    status            VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','SUSPENDED','DELETED')),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at        TIMESTAMPTZ
);
CREATE UNIQUE INDEX idx_users_tenant_email ON users(tenant_id, email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_tenant_id ON users(tenant_id) WHERE deleted_at IS NULL;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY users_tenant_isolation ON users USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE TRIGGER users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); |
| --- |
| -- ═══════════════════════════════════════════════════════════════════════
-- CONNECTORS
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE connectors (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name              VARCHAR(255) NOT NULL,
    connector_type    VARCHAR(100) NOT NULL,
    config            JSONB NOT NULL DEFAULT '{}',  -- non-sensitive: region, endpoint, etc.
    vault_secret_path VARCHAR(512) NOT NULL,
    vault_secret_version INT NOT NULL DEFAULT 1,
    status            VARCHAR(20) NOT NULL DEFAULT 'HEALTHY'
                      CHECK (status IN ('HEALTHY','DEGRADED','UNHEALTHY','DISABLED')),
    agent_count       INTEGER NOT NULL DEFAULT 0,
    last_health_check TIMESTAMPTZ,
    last_sync_at      TIMESTAMPTZ,
    sync_frequency_min INTEGER NOT NULL DEFAULT 60 CHECK (sync_frequency_min >= 5),
    created_by        UUID NOT NULL REFERENCES users(id),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at        TIMESTAMPTZ
);
CREATE INDEX idx_connectors_tenant ON connectors(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_connectors_status ON connectors(tenant_id, status) WHERE deleted_at IS NULL;
ALTER TABLE connectors ENABLE ROW LEVEL SECURITY;
CREATE POLICY connectors_tenant_isolation ON connectors USING (tenant_id = current_setting('app.tenant_id')::UUID);

-- ═══════════════════════════════════════════════════════════════════════
-- AGENTS
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE agents (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    connector_id      UUID REFERENCES connectors(id) ON DELETE SET NULL,
    source_agent_id   VARCHAR(512),  -- ID in source system (e.g., Bedrock agent ARN)
    name              VARCHAR(255) NOT NULL,
    description       TEXT,
    agent_type        VARCHAR(100) NOT NULL,  -- LangChain/OpenAI | AWS Bedrock Agent | etc.
    framework         VARCHAR(100) NOT NULL,
    owner_user_id     UUID REFERENCES users(id) ON DELETE SET NULL,
    owner_email       VARCHAR(255) NOT NULL,  -- denormalized for display without join
    fingerprint       CHAR(64)  NOT NULL,      -- SHA-256 hex of code+config hash
    autonomy_level    SMALLINT  NOT NULL DEFAULT 0 CHECK (autonomy_level BETWEEN 0 AND 5),
    risk_score        SMALLINT  NOT NULL DEFAULT 0 CHECK (risk_score BETWEEN 0 AND 100),
    risk_tier         VARCHAR(20) NOT NULL DEFAULT 'MINIMAL'
                      CHECK (risk_tier IN ('CRITICAL','HIGH','MEDIUM','LOW','MINIMAL')),
    status            VARCHAR(20) NOT NULL DEFAULT 'REGISTERED'
                      CHECK (status IN ('REGISTERED','ACTIVE','QUARANTINE','SUSPENDED','DELETED')),
    policy_group_ids  UUID[] NOT NULL DEFAULT '{}',
    tags              TEXT[] NOT NULL DEFAULT '{}',
    last_active_at    TIMESTAMPTZ,
    last_scan_at      TIMESTAMPTZ,
    metadata          JSONB NOT NULL DEFAULT '{}',  -- source-system-specific
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at        TIMESTAMPTZ
);
CREATE INDEX idx_agents_tenant        ON agents(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_agents_risk          ON agents(tenant_id, risk_score DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_agents_status        ON agents(tenant_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_agents_risk_tier     ON agents(tenant_id, risk_tier) WHERE deleted_at IS NULL;
CREATE INDEX idx_agents_connector     ON agents(connector_id) WHERE deleted_at IS NULL;
-- GIN index for tag-based filtering
CREATE INDEX idx_agents_tags          ON agents USING GIN(tags);
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
CREATE POLICY agents_tenant_isolation ON agents USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE TRIGGER agents_updated_at BEFORE UPDATE ON agents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); |
| --- |
| -- agent_tools: many-to-many between agents and tools
CREATE TABLE tools (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name              VARCHAR(255) NOT NULL,
    tool_type         VARCHAR(100),  -- API_CALL|FILE_IO|DATABASE|MCP_TOOL|EMAIL|CUSTOM
    sensitivity_tier  VARCHAR(20) NOT NULL DEFAULT 'READ'
                      CHECK (sensitivity_tier IN ('READ','WRITE','EXECUTE','ADMIN')),
    destination_type  VARCHAR(20) NOT NULL DEFAULT 'INTERNAL'
                      CHECK (destination_type IN ('INTERNAL','EXTERNAL','MCP_SERVER','AGENT')),
    mcp_server_url    VARCHAR(1024),  -- if tool is exposed via MCP
    schema_json       JSONB,          -- OpenAPI/MCP tool schema
    is_approved       BOOLEAN NOT NULL DEFAULT FALSE,
    approved_by       UUID REFERENCES users(id),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX idx_tools_tenant_name ON tools(tenant_id, name);
ALTER TABLE tools ENABLE ROW LEVEL SECURITY;
CREATE POLICY tools_tenant_isolation ON tools USING (tenant_id = current_setting('app.tenant_id')::UUID);

CREATE TABLE agent_tools (
    agent_id     UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    tool_id      UUID NOT NULL REFERENCES tools(id) ON DELETE CASCADE,
    permissions  TEXT[] NOT NULL DEFAULT '{READ}',  -- granted permissions
    granted_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    granted_by   UUID REFERENCES users(id),
    PRIMARY KEY (agent_id, tool_id)
);
CREATE INDEX idx_agent_tools_agent ON agent_tools(agent_id);
CREATE INDEX idx_agent_tools_tool  ON agent_tools(tool_id);

-- ═══════════════════════════════════════════════════════════════════════
-- AGENT IDENTITY TOKENS
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE agent_identity_tokens (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    agent_id        UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    ait_hash        CHAR(64) NOT NULL UNIQUE,  -- SHA-256 hex; plaintext never stored
    fingerprint     CHAR(64) NOT NULL,
    granted_tools   TEXT[] NOT NULL DEFAULT '{}',
    issued_by       UUID NOT NULL REFERENCES users(id),
    issued_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ NOT NULL,
    last_used_at    TIMESTAMPTZ,
    use_count       INTEGER NOT NULL DEFAULT 0,
    revoked_at      TIMESTAMPTZ,
    revoke_reason   VARCHAR(255),
    revoked_by      UUID REFERENCES users(id)
);
CREATE INDEX idx_ait_agent       ON agent_identity_tokens(agent_id) WHERE revoked_at IS NULL;
CREATE INDEX idx_ait_expires     ON agent_identity_tokens(expires_at) WHERE revoked_at IS NULL;
CREATE INDEX idx_ait_hash        ON agent_identity_tokens(ait_hash);  -- for lookup on every request
ALTER TABLE agent_identity_tokens ENABLE ROW LEVEL SECURITY;
CREATE POLICY ait_tenant_isolation ON agent_identity_tokens USING (tenant_id = current_setting('app.tenant_id')::UUID); |
| --- |
| -- ═══════════════════════════════════════════════════════════════════════
-- POLICIES
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE policies (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id            UUID REFERENCES tenants(id) ON DELETE CASCADE,  -- NULL for L0
    policy_level         SMALLINT NOT NULL CHECK (policy_level IN (0,1,2,3)),
    name                 VARCHAR(255) NOT NULL,
    description          TEXT,
    scope_type           VARCHAR(20) NOT NULL
                         CHECK (scope_type IN ('PLATFORM','TENANT','AGENT_GROUP','AGENT')),
    scope_id             UUID,  -- agent_id or group_id; NULL for PLATFORM/TENANT scope
    rego_source          TEXT NOT NULL,
    rego_compiled        BYTEA,  -- cached compiled OPA bundle; regenerated on change
    action_on_match      VARCHAR(20) NOT NULL CHECK (action_on_match IN ('ALLOW','DENY','ESCALATE')),
    hitl_tier            SMALLINT CHECK (hitl_tier IN (1,2,3,4)),  -- required if ESCALATE
    severity             VARCHAR(20) NOT NULL DEFAULT 'MEDIUM'
                         CHECK (severity IN ('CRITICAL','HIGH','MEDIUM','LOW')),
    notification_targets JSONB NOT NULL DEFAULT '[]',  -- [{type:'slack',channel:'#alerts'}]
    enabled              BOOLEAN NOT NULL DEFAULT TRUE,
    version              INTEGER NOT NULL DEFAULT 1,
    approved_by          UUID REFERENCES users(id),
    approved_at          TIMESTAMPTZ,
    shadow_mode_until    TIMESTAMPTZ,  -- if set: log only until this timestamp
    created_by           UUID NOT NULL REFERENCES users(id),
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at           TIMESTAMPTZ
);
CREATE INDEX idx_policies_tenant_enabled ON policies(tenant_id, enabled, policy_level) WHERE deleted_at IS NULL;
CREATE INDEX idx_policies_scope          ON policies(scope_type, scope_id) WHERE deleted_at IS NULL;
-- Partial index for shadow mode expiry job
CREATE INDEX idx_policies_shadow         ON policies(shadow_mode_until) WHERE shadow_mode_until IS NOT NULL;
ALTER TABLE policies ENABLE ROW LEVEL SECURITY;
CREATE POLICY policies_tenant_isolation ON policies
    USING (tenant_id IS NULL OR tenant_id = current_setting('app.tenant_id')::UUID);
CREATE TRIGGER policies_updated_at BEFORE UPDATE ON policies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Policy change audit (in addition to main audit log — for faster policy history queries)
CREATE TABLE policy_change_log (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id     UUID NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
    tenant_id     UUID NOT NULL,
    change_type   VARCHAR(20) NOT NULL CHECK (change_type IN ('CREATED','UPDATED','DELETED','ENABLED','DISABLED','APPROVED')),
    changed_by    UUID NOT NULL REFERENCES users(id),
    old_value     JSONB,  -- serialized previous policy state
    new_value     JSONB,  -- serialized new policy state
    changed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_policy_log_policy ON policy_change_log(policy_id);
CREATE INDEX idx_policy_log_tenant ON policy_change_log(tenant_id, changed_at DESC); |
| --- |
| -- ═══════════════════════════════════════════════════════════════════════
-- HITL REQUESTS + DECISIONS
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE hitl_requests (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    agent_id          UUID NOT NULL REFERENCES agents(id),
    decision_id       UUID NOT NULL,  -- from policy engine
    action_summary    TEXT NOT NULL,
    action_metadata   JSONB NOT NULL DEFAULT '{}',
    policy_id         UUID REFERENCES policies(id),
    hitl_tier         SMALLINT NOT NULL CHECK (hitl_tier IN (1,2,3,4)),
    required_approvers INTEGER NOT NULL DEFAULT 1,
    approvals_received INTEGER NOT NULL DEFAULT 0,
    timeout_at        TIMESTAMPTZ NOT NULL,
    callback_url      VARCHAR(2048) NOT NULL,  -- MCP Gateway callback endpoint
    status            VARCHAR(20) NOT NULL DEFAULT 'PENDING'
                      CHECK (status IN ('PENDING','APPROVED','DENIED','TIMED_OUT','AUTO_APPROVED')),
    resolved_at       TIMESTAMPTZ,
    resolved_by       UUID REFERENCES users(id),
    resolution_notes  TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_hitl_tenant_status ON hitl_requests(tenant_id, status) WHERE status = 'PENDING';
CREATE INDEX idx_hitl_timeout       ON hitl_requests(timeout_at)        WHERE status = 'PENDING';
CREATE INDEX idx_hitl_agent         ON hitl_requests(agent_id, created_at DESC);
ALTER TABLE hitl_requests ENABLE ROW LEVEL SECURITY;
CREATE POLICY hitl_tenant_isolation ON hitl_requests USING (tenant_id = current_setting('app.tenant_id')::UUID);

-- ═══════════════════════════════════════════════════════════════════════
-- POLICY OUTBOX (Transactional Outbox Pattern)
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE policy_outbox (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id      UUID NOT NULL,
    event_type     VARCHAR(50) NOT NULL,  -- POLICY_CREATED|UPDATED|DELETED
    payload        JSONB NOT NULL,
    published      BOOLEAN NOT NULL DEFAULT FALSE,
    published_at   TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- Only index unpublished: relay polls this frequently
CREATE INDEX idx_outbox_unpublished ON policy_outbox(created_at) WHERE published = FALSE; |
| --- |
| -- TimescaleDB hypertable: time-series risk scores
CREATE TABLE agent_risk_scores (
    time              TIMESTAMPTZ     NOT NULL,
    tenant_id         UUID            NOT NULL,
    agent_id          UUID            NOT NULL,
    composite_score   SMALLINT        NOT NULL CHECK (composite_score BETWEEN 0 AND 100),
    risk_tier         VARCHAR(20)     NOT NULL,
    dim_permission    SMALLINT        NOT NULL,
    dim_data_access   SMALLINT        NOT NULL,
    dim_blast_radius  SMALLINT        NOT NULL,
    dim_autonomy      SMALLINT        NOT NULL,
    dim_compliance    SMALLINT        NOT NULL,
    blast_radius_count INTEGER        NOT NULL DEFAULT 0,
    trigger_event_id  UUID,
    trigger_type      VARCHAR(50)
);
SELECT create_hypertable('agent_risk_scores', 'time');
SELECT add_dimension('agent_risk_scores', 'tenant_id', number_partitions => 4);
SELECT add_compression_policy('agent_risk_scores', INTERVAL '7 days');
SELECT add_retention_policy('agent_risk_scores', INTERVAL '3 years');

-- Continuous aggregate: hourly avg risk per tenant (for trend charts)
CREATE MATERIALIZED VIEW agent_risk_hourly
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 hour', time) AS hour,
       tenant_id, agent_id,
       avg(composite_score) AS avg_score,
       max(composite_score) AS max_score,
       min(composite_score) AS min_score
FROM agent_risk_scores
GROUP BY 1, 2, 3;
SELECT add_continuous_aggregate_policy('agent_risk_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'); |
| --- |
| // Neo4j Cypher — node constraints and relationship definitions

// Constraints (unique + indexed)
CREATE CONSTRAINT agent_id_unique FOR (a:Agent) REQUIRE a.agent_id IS UNIQUE;
CREATE CONSTRAINT tool_id_unique  FOR (t:Tool)  REQUIRE t.tool_id IS UNIQUE;
CREATE CONSTRAINT source_id_unique FOR (d:DataSource) REQUIRE d.source_id IS UNIQUE;
CREATE CONSTRAINT mcp_id_unique   FOR (m:MCPServer)  REQUIRE m.server_id IS UNIQUE;

// Node property indexes for efficient queries
CREATE INDEX agent_tenant FOR (a:Agent) ON (a.tenant_id);
CREATE INDEX agent_risk   FOR (a:Agent) ON (a.risk_score);
CREATE INDEX agent_status FOR (a:Agent) ON (a.status);

// Agent node: all properties
// MERGE (a:Agent {agent_id: $id}) SET a += {
//   tenant_id: $tenant_id, name: $name, risk_score: $score,
//   risk_tier: $tier, status: $status, updated_at: datetime()}

// Relationships
// (:Agent)-[:CAN_CALL {permissions:[], granted_at:datetime(), is_approved:bool}]->(:Tool)
// (:Agent)-[:READS {data_classification:[], access_frequency:int}]->(:DataSource)
// (:Agent)-[:WRITES {data_classification:[]}]->(:DataSource)
// (:Agent)-[:CONNECTS_TO {last_seen:datetime(), call_count:int}]->(:MCPServer)
// (:Agent)-[:CALLS_AGENT {call_type:'sync|async', last_called:datetime()}]->(:Agent)
// (:MCPServer)-[:EXPOSES {schema_version:string}]->(:Tool)

// Blast radius query (BFS from agent, max depth 5)
MATCH path = (a:Agent {agent_id: $agent_id, tenant_id: $tenant_id})-[*1..5]->(n)
WHERE a.tenant_id = $tenant_id  // tenant isolation enforced at query level
RETURN n.agent_id AS node_id, labels(n)[0] AS node_type,
       length(path) AS depth,
       CASE labels(n)[0]
           WHEN 'Agent'      THEN 20
           WHEN 'DataSource' THEN 15
           WHEN 'MCPServer'  THEN 10
           WHEN 'Tool'       THEN 5
           ELSE 1
       END AS criticality_weight
ORDER BY depth, criticality_weight DESC
LIMIT 100; |
| --- |
| syntax = "proto3";
package pinaka.policy.v1;
option go_package = "github.com/pinaka-ai/pinaka/proto/policy/v1;policyv1";
import "google/protobuf/timestamp.proto";

service PolicyEngine {
    rpc EvaluateAction(EvaluateActionRequest) returns (EvaluateActionResponse);
    rpc EvaluateActionBatch(EvaluateActionBatchRequest) returns (EvaluateActionBatchResponse);
    rpc GetPolicyBundle(GetPolicyBundleRequest) returns (stream PolicyBundleChunk);
    rpc HealthCheck(HealthRequest) returns (HealthResponse);
}

enum Decision { ALLOW = 0; DENY = 1; ESCALATE = 2; }
enum Destination { INTERNAL = 0; EXTERNAL = 1; MCP_SERVER = 2; AGENT = 3; }

message EvaluateActionRequest {
    string tenant_id = 1;
    string agent_id = 2;
    string ait_id = 3;
    string tool_name = 4;
    Destination destination = 5;
    repeated string data_classifications = 6;
    map<string,string> action_metadata = 7;
    int64 request_timestamp_ns = 8;
}

message EvaluateActionResponse {
    string decision_id = 1;
    Decision decision = 2;
    string reason = 3;
    string policy_id = 4;
    int32 hitl_tier = 5;
    int32 risk_delta = 6;
    google.protobuf.Timestamp evaluated_at = 7;
    int32 policy_count_evaluated = 8;
}

message EvaluateActionBatchRequest { repeated EvaluateActionRequest requests = 1; }
message EvaluateActionBatchResponse { repeated EvaluateActionResponse responses = 1; }
message GetPolicyBundleRequest { string tenant_id = 1; }
message PolicyBundleChunk { bytes data = 1; bool last_chunk = 2; }
message HealthRequest {}
message HealthResponse { bool healthy = 1; string message = 2; } |
| --- |
| syntax = "proto3";
package pinaka.platform.v1;
option go_package = "github.com/pinaka-ai/pinaka/proto/platform/v1;platformv1";

service PlatformService {
    rpc ValidateAIT(ValidateAITRequest) returns (ValidateAITResponse);
    rpc ValidateJWT(ValidateJWTRequest) returns (ValidateJWTResponse);
    rpc GetTenantContext(GetTenantContextRequest) returns (TenantContext);
    rpc CheckRBAC(CheckRBACRequest) returns (CheckRBACResponse);
    rpc RefreshToken(RefreshTokenRequest) returns (RefreshTokenResponse);
    rpc InvalidateTenantCache(InvalidateCacheRequest) returns (InvalidateCacheResponse);
}

message ValidateAITRequest {
    string ait_token = 1;
    string fingerprint = 2;  // optional: checked if provided
}
message ValidateAITResponse {
    bool is_valid = 1;
    string tenant_id = 2;
    string agent_id = 3;
    repeated string granted_tools = 4;
    string fingerprint = 5;
    int64 expires_at = 6;
    string invalid_reason = 7;  // EXPIRED|REVOKED|SIGNATURE_INVALID|FINGERPRINT_MISMATCH
}

message ValidateJWTRequest { string jwt_token = 1; }
message ValidateJWTResponse {
    bool is_valid = 1;
    string user_id = 2;
    string tenant_id = 3;
    repeated string roles = 4;
    bool mfa_verified = 5;
    string invalid_reason = 6;
}

message GetTenantContextRequest { string tenant_id = 1; }
message TenantContext {
    string tenant_id = 1;
    string region = 2;
    string plan_tier = 3;
    map<string,string> feature_flags = 4;
    int32 enforcement_rps_limit = 5;
    string failsafe_mode = 6;  // DENY_ALL | ALLOW_WITH_ALERT
    string status = 7;
}

message CheckRBACRequest { string user_id = 1; string action = 2; string resource = 3; }
message CheckRBACResponse { bool allowed = 1; string missing_role = 2; }

message RefreshTokenRequest { string refresh_token_hash = 1; }
message RefreshTokenResponse {
    string new_access_token = 1;
    string new_refresh_token = 2;
    int64 expires_at = 3;
}

message InvalidateCacheRequest { string tenant_id = 1; string cache_type = 2; }
message InvalidateCacheResponse { bool success = 1; } |
| --- |
| ℹ | Full OpenAPI specs are generated from code annotations and live at https://api.pinaka.ai/v1/openapi.yaml (per-environment). This section specifies the critical endpoints that all services must implement. |
| --- | --- |
| openapi: 3.1.0
info:
  title: Pinaka Agent Inventory API
  version: 1.0.0

paths:
  /v1/inventory/agents:
    get:
      summary: List agents (cursor-paginated)
      operationId: listAgents
      parameters:
        - name: cursor    # base64(JSON{sort_field,id})
          in: query
          schema: {type: string}
        - name: limit
          in: query
          schema: {type: integer, minimum: 1, maximum: 100, default: 50}
        - name: status
          in: query
          schema: {type: string, enum: [REGISTERED, ACTIVE, QUARANTINE, SUSPENDED]}
        - name: risk_tier
          in: query
          schema: {type: string, enum: [CRITICAL, HIGH, MEDIUM, LOW, MINIMAL]}
        - name: sort
          in: query
          schema: {type: string, enum: [risk_score_desc, name_asc, last_active_desc], default: risk_score_desc}
      responses:
        '200':
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items: {$ref: "#/components/schemas/AgentSummary"}
                  pagination:
                    $ref: "#/components/schemas/PaginationInfo"

    post:
      summary: Register a new agent
      operationId: registerAgent
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [name, agent_type, framework, owner_email, fingerprint]
              properties:
                name:         {type: string, maxLength: 255}
                agent_type:   {type: string}
                framework:    {type: string}
                owner_email:  {type: string, format: email}
                fingerprint:  {type: string, pattern: "^[0-9a-f]{64}$"}
                autonomy_level: {type: integer, minimum: 0, maximum: 5, default: 0}
                tools:        {type: array, items: {$ref: "#/components/schemas/ToolInput"}}
                description:  {type: string, maxLength: 2000}
      responses:
        '201':
          content:
            application/json:
              schema:
                type: object
                properties:
                  agent_id:    {type: string, format: uuid}
                  ait_token:   {type: string, description: "Shown once. Store securely."}
                  ait_expires_at: {type: string, format: date-time} |
| --- |
| /v1/audit/events:
    get:
      summary: Query audit events (cursor-paginated)
      operationId: listAuditEvents
      parameters:
        - name: agent_id;     in: query; schema: {type: string, format: uuid}
        - name: event_type;   in: query; schema: {type: string}
        - name: decision;     in: query; schema: {type: string, enum: [ALLOW,DENY,ESCALATE]}
        - name: from;         in: query; schema: {type: string, format: date-time}
        - name: to;           in: query; schema: {type: string, format: date-time}
        - name: cursor;       in: query; schema: {type: string}
        - name: limit;        in: query; schema: {type: integer, maximum: 100, default: 50}
      responses:
        '200': {content: {application/json: {schema: {$ref: '#/components/schemas/AuditEventList'}}}}

  /v1/audit/queries:
    post:
      summary: Execute a natural language audit query
      operationId: executeNLQuery
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [nl_query]
              properties:
                nl_query: {type: string, maxLength: 1000}
                export_format: {type: string, enum: [none, csv, json], default: none}
      responses:
        '200':
          content:
            application/json:
              schema:
                type: object
                properties:
                  query_id:        {type: string, format: uuid}
                  summary:         {type: string}
                  events:          {type: array, items: {$ref: "#/components/schemas/AuditEventSummary"}}
                  total_matches:   {type: integer}
                  export_url:      {type: string, format: uri, nullable: true}
                  structured_query:{type: string} |
| --- |
| components:
  schemas:
    PaginationInfo:
      type: object
      properties:
        limit:       {type: integer}
        next_cursor: {type: string, nullable: true}
        has_more:    {type: boolean}

    AgentSummary:
      type: object
      properties:
        id:           {type: string, format: uuid}
        name:         {type: string}
        agent_type:   {type: string}
        risk_score:   {type: integer, minimum: 0, maximum: 100}
        risk_tier:    {type: string, enum: [CRITICAL,HIGH,MEDIUM,LOW,MINIMAL]}
        status:       {type: string}
        owner_email:  {type: string}
        last_active_at: {type: string, format: date-time, nullable: true}

    RiskDimension:
      type: object
      properties:
        name:       {type: string}
        score:      {type: number, minimum: 0, maximum: 100}
        weight:     {type: number}
        signals:    {type: array, items: {type: string}}

    ErrorResponse:  # RFC 7807
      type: object
      required: [type, title, status, detail]
      properties:
        type:      {type: string, format: uri}
        title:     {type: string}
        status:    {type: integer}
        detail:    {type: string}
        instance:  {type: string}
        extensions:
          type: object
          properties:
            decision_id: {type: string}
            policy_id:   {type: string}
            request_id:  {type: string}
            timestamp:   {type: string, format: date-time}

  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-Pinaka-API-Key |
| --- |
| {
  "type": "record",
  "name": "AgentActionEvent",
  "namespace": "pinaka.enforcement",
  "doc": "Every MCP tool call or agent action processed by Pinaka",
  "fields": [
    {"name": "event_id",          "type": "string",       "doc": "UUID v7"},
    {"name": "schema_version",    "type": "int",          "default": 1},
    {"name": "tenant_id",         "type": "string"},
    {"name": "agent_id",          "type": "string"},
    {"name": "ait_id",            "type": "string"},
    {"name": "tool_name",         "type": "string"},
    {"name": "destination",       "type": {"type":"enum","name":"Destination",
                                  "symbols":["INTERNAL","EXTERNAL","MCP_SERVER","AGENT"]}},
    {"name": "data_classifications","type":{"type":"array","items":"string"},"default":[]},
    {"name": "action_metadata",   "type":{"type":"map","values":"string"},  "default":{}},
    {"name": "timestamp_ns",      "type": "long",         "doc": "Unix nanoseconds UTC"},
    {"name": "policy_decision",   "type": {"type":"enum","name":"Decision",
                                  "symbols":["ALLOW","DENY","ESCALATE"]}},
    {"name": "decision_id",       "type": "string"},
    {"name": "policy_id",         "type": ["null","string"], "default": null},
    {"name": "hitl_tier",         "type": ["null","int"],    "default": null},
    {"name": "risk_delta",        "type": "int",          "default": 0},
    {"name": "enforcement_mode",  "type": {"type":"enum","name":"EnforcementMode",
                                  "symbols":["INLINE","SIDECAR","API_HOOK","OUT_OF_BAND"]}},
    {"name": "shadow_mode",       "type": "boolean",      "default": false}
  ]
} |
| --- |
| {
  "type": "record",
  "name": "RiskScoreUpdate",
  "namespace": "pinaka.risk",
  "fields": [
    {"name": "event_id",        "type": "string"},
    {"name": "tenant_id",       "type": "string"},
    {"name": "agent_id",        "type": "string"},
    {"name": "old_score",       "type": "int"},
    {"name": "new_score",       "type": "int"},
    {"name": "old_tier",        "type": "string"},
    {"name": "new_tier",        "type": "string"},
    {"name": "dim_permission",  "type": "int"},
    {"name": "dim_data_access", "type": "int"},
    {"name": "dim_blast_radius","type": "int"},
    {"name": "dim_autonomy",    "type": "int"},
    {"name": "dim_compliance",  "type": "int"},
    {"name": "blast_radius_count","type":"int"},
    {"name": "trigger_type",    "type": "string"},  // POLICY_VIOLATION|DISCOVERY_SCAN|INVESTIGATION_FINDING
    {"name": "trigger_event_id","type": ["null","string"], "default": null},
    {"name": "timestamp_ns",    "type": "long"}
  ]
} |
| --- |
| {
  "type": "record",
  "name": "HITLRequestEvent",
  "namespace": "pinaka.hitl",
  "fields": [
    {"name": "event_id",        "type": "string"},
    {"name": "tenant_id",       "type": "string"},
    {"name": "request_id",      "type": "string"},
    {"name": "agent_id",        "type": "string"},
    {"name": "decision_id",     "type": "string"},
    {"name": "action_summary",  "type": "string"},
    {"name": "hitl_tier",       "type": "int"},
    {"name": "required_approvers","type":"int","default":1},
    {"name": "timeout_at_sec",  "type": "long"},
    {"name": "callback_url",    "type": "string"},
    {"name": "timestamp_ns",    "type": "long"}
  ]
} |
| --- |
| {
  "type": "record",
  "name": "AgentLifecycleEvent",
  "namespace": "pinaka.discovery",
  "fields": [
    {"name": "event_id",      "type": "string"},
    {"name": "tenant_id",     "type": "string"},
    {"name": "agent_id",      "type": "string"},
    {"name": "lifecycle_type","type": {"type":"enum","name":"LifecycleType",
                              "symbols":["REGISTERED","UPDATED","DELETED","QUARANTINED","RESTORED"]}},
    {"name": "old_fingerprint","type":["null","string"],"default":null},
    {"name": "new_fingerprint","type":"string"},
    {"name": "connector_id",  "type": "string"},
    {"name": "timestamp_ns",  "type": "long"}
  ]
} |
| --- |
| package pinaka.shared

import future.keywords.if
import future.keywords.contains

# Returns the highest sensitivity tier score (0=PUBLIC, 5=FINANCIAL)
classify_data(classifications) := tier if {
    tier := max([tier_score(c) | c := classifications[_]])
} else := 0

tier_score("PUBLIC")    := 0
tier_score("INTERNAL")  := 1
tier_score("REGULATED") := 2
tier_score("IP")        := 3
tier_score("PII")       := 4
tier_score("FINANCIAL") := 5

# Returns true if data classifications include a PII-or-higher tier
has_sensitive_data(classifications) if {
    classify_data(classifications) >= 4
}

# Returns true if destination is external
is_external(destination) if {
    destination in {"EXTERNAL"}
} |
| --- |
| package pinaka.platform

import future.keywords.if
import data.pinaka.shared

# L0 Platform Baseline — These rules CANNOT be overridden by any tenant policy.
# DENY triggers if ANY of these rules evaluate to true.

# Rule 1: Never permit external credential exfiltration
baseline_deny if {
    input.tool_name in {"env-read", "secrets-read", "credential-export", "aws-sts-get-token"}
    shared.is_external(input.destination)
}

# Rule 2: Never permit PII export to unapproved external destinations
baseline_deny if {
    shared.has_sensitive_data(input.data_classifications)
    shared.is_external(input.destination)
    not input.destination_approved  # set by connector if destination is approved
}

# Rule 3: Never permit agent self-modification
baseline_deny if {
    input.tool_name in {"self-modify", "code-update", "config-rewrite", "ait-issue"}
}

# Rule 4: Never allow agent to revoke its own AIT or another agent s AIT
baseline_deny if {
    input.tool_name in {"ait-revoke", "agent-delete"}
    input.destination == "AGENT"
} |
| --- |
| package pinaka.evaluate

import future.keywords.if
import future.keywords.contains
import future.keywords.every
import data.pinaka.platform
import data.pinaka.shared
import data.tenant_policies  # Loaded from data.json in OPA bundle

# ── Main decision ───────────────────────────────────────────────────────
# Decision precedence: L0 DENY > Tenant DENY > Tenant ESCALATE > ALLOW

default decision := "ALLOW"

decision := "DENY" if { platform.baseline_deny }

decision := "DENY" if {
    not platform.baseline_deny
    count(matching_deny_policies) > 0
}

decision := "ESCALATE" if {
    not platform.baseline_deny
    count(matching_deny_policies) == 0
    count(matching_escalate_policies) > 0
}

# ── Policy matching ─────────────────────────────────────────────────────

matching_deny_policies contains p if {
    some p in active_policies
    p.action_on_match == "DENY"
    policy_matches(p)
}

matching_escalate_policies contains p if {
    some p in active_policies
    p.action_on_match == "ESCALATE"
    policy_matches(p)
}

winning_policy := p if {
    decision == "DENY"
    some p in matching_deny_policies  # first DENY policy wins
}

winning_policy := p if {
    decision == "ESCALATE"
    some p in matching_escalate_policies
}

# ── Active policies (enabled, not in shadow mode, scope-matching) ────────

active_policies contains p if {
    some p in tenant_policies
    p.enabled == true
    not in_shadow_mode(p)
    scope_matches(p)
}

in_shadow_mode(p) if {
    p.shadow_mode_until != null
    # Note: actual time comparison happens at bundle build time in Go;
    # shadow_mode field injected into data.json as a boolean
    p.currently_in_shadow_mode == true
}

scope_matches(p) if { p.scope_type == "TENANT" }
scope_matches(p) if {
    p.scope_type == "AGENT_GROUP"
    input.agent_id in p.scope_agent_ids
}
scope_matches(p) if {
    p.scope_type == "AGENT"
    p.scope_id == input.agent_id
}

# policy_matches evaluates the tenant-specific Rego source for policy p
# In the actual bundle, each policy s Rego is compiled as a sub-package
# and called via: data.tenant_policies.policy_{id}.matches
policy_matches(p) if { data.tenant_policy_rules[p.id].matches }

# ── Outputs (exposed to Go via rego.PreparedEvalQuery) ──────────────────
output := {
    "decision":   decision,
    "reason":     reason_for_decision,
    "policy_id":  winning_policy.id if count(object.get(object, "winning_policy", {})) > 0,
    "hitl_tier":  winning_policy.hitl_tier if decision == "ESCALATE",
}

reason_for_decision := sprintf("Blocked by policy: %v", [winning_policy.name]) if { decision == "DENY" }
reason_for_decision := sprintf("Escalated by policy: %v", [winning_policy.name]) if { decision == "ESCALATE" }
reason_for_decision := "No matching deny or escalate policy" if { decision == "ALLOW" } |
| --- |
| # policies/tests/evaluate_test.rego
# Run: opa test ./policies/... -v

package pinaka.evaluate_test

import data.pinaka.evaluate

# ── Test 1: ALLOW when no deny/escalate policy matches ──────────────────
test_allow_no_matching_policy if {
    evaluate.decision == 'ALLOW' with input as {
        'agent_id': 'agt_001',
        'tool_name': 'spreadsheet-read',
        'destination': 'INTERNAL',
        'data_classifications': ['PUBLIC'],
    } with data.tenant_policies as []  # No policies configured
}

# ── Test 2: L0 Platform Baseline DENY ───────────────────────────────────
test_baseline_deny_credential_exfiltration if {
    evaluate.decision == 'DENY' with input as {
        'agent_id': 'agt_001',
        'tool_name': 'secrets-read',
        'destination': 'EXTERNAL',
        'data_classifications': ['IP'],
    } with data.tenant_policies as []  # Even with no tenant policies, L0 fires
}

# ── Test 3: Tenant L1 DENY fires ────────────────────────────────────────
test_tenant_deny_pii_export if {
    evaluate.decision == 'DENY' with input as {
        'agent_id': 'agt_001',
        'tool_name': 'email-send',
        'destination': 'EXTERNAL',
        'data_classifications': ['PII'],
    } with data.tenant_policies as [mock_pii_deny_policy]
}

# ── Test 4: DENY wins over ESCALATE (conflict resolution) ───────────────
test_deny_wins_over_escalate if {
    evaluate.decision == 'DENY' with input as {
        'agent_id': 'agt_group_member',
        'tool_name': 'bulk-export',
        'destination': 'EXTERNAL',
        'data_classifications': ['FINANCIAL'],
    } with data.tenant_policies as [mock_deny_policy, mock_escalate_policy]
    # Both policies match, but DENY must win
}

# ── Test 5: Shadow mode — policy matches but ALLOW returned ─────────────
test_shadow_mode_allows_action if {
    evaluate.decision == 'ALLOW' with input as {
        'agent_id': 'agt_001',
        'tool_name': 'email-send',
        'destination': 'EXTERNAL',
        'data_classifications': ['PII'],
    } with data.tenant_policies as [{
        'id': 'pol_shadow',
        'action_on_match': 'DENY',
        'enabled': true,
        'currently_in_shadow_mode': true,  # injected at bundle build time
        'scope_type': 'TENANT',
    }]
}

# ── Mock helpers ────────────────────────────────────────────────────────
mock_pii_deny_policy := {
    'id': 'pol_pii_deny', 'enabled': true, 'currently_in_shadow_mode': false,
    'scope_type': 'TENANT', 'action_on_match': 'DENY',
    # Rego rule: matches when PII + EXTERNAL
} |
| --- |
| ALGORITHM CalculateRiskScore(agent_id, tenant_id, trigger_type):

INPUT: agent_id: UUID, tenant_id: UUID, trigger_type: string
OUTPUT: RiskScore {composite:int, tier:str, dimensions:[...], blast_radius:int}

CONSTANTS:
  WEIGHTS = {permission:0.25, data:0.25, blast:0.20, autonomy:0.15, compliance:0.15}
  TOOL_SENSITIVITY = {READ:1, WRITE:3, EXECUTE:5, ADMIN:10}
  ACCESS_WEIGHT = {INTERNAL:1.0, MCP_SERVER:1.5, EXTERNAL:2.0}
  DATA_TIER = {PUBLIC:0, INTERNAL:10, REGULATED:30, IP:50, PII:70, FINANCIAL:90}
  NODE_CRIT = {AGENT:20, DATA_SOURCE:15, MCP_SERVER:10, TOOL:5}
  AUTONOMY_MAP = {0:0, 1:20, 2:40, 3:60, 4:80, 5:100}
  VIOLATION_SEV = {CRITICAL:25, HIGH:15, MEDIUM:8, LOW:3}

STEP 1 — DIMENSION 1: Permission Scope (0–100)
  tools ← DB.get_agent_tools(agent_id)  // parallel with other fetches
  IF tools is empty THEN dim_permission ← 0 ELSE
    raw ← sum(TOOL_SENSITIVITY[t.access_type] * ACCESS_WEIGHT[t.dest] for t in tools)
    raw ← raw / len(tools)             // normalise to per-tool average
    dim_permission ← min(raw / 10.0 * 100, 100.0)

STEP 2 — DIMENSION 2: Data Access Sensitivity (0–100)
  sources ← DB.get_agent_data_sources(agent_id)
  IF sources is empty THEN dim_data ← 0 ELSE
    raw ← sum(DATA_TIER[s.classification] * access_freq_percentile(s) for s in sources)
    raw ← raw / len(sources)
    dim_data ← min(raw, 100.0)         // already on 0–100 scale
  WHERE access_freq_percentile(s) = 0.5 + 0.5 * (s.access_count / max_access_count)
  // Scales 1.0 (rarely accessed) to 1.5 (most-frequently accessed)

STEP 3 — DIMENSION 3: Blast Radius (0–100)
  reachable ← Neo4j.BFS(agent_id, max_depth=5, tenant_id=tenant_id)
  // BFS with depth-based decay: closer nodes count more
  blast_sum ← sum(NODE_CRIT[n.type] * (1 / (n.depth + 1)) for n in reachable)
  blast_count ← len(reachable)
  // 200 = empirically calibrated 'large blast radius' for normalisation
  dim_blast ← min(blast_sum / 200.0 * 100, 100.0)

STEP 4 — DIMENSION 4: Autonomy Level (0–100)
  agent ← DB.get_agent(agent_id)
  dim_autonomy ← AUTONOMY_MAP[agent.autonomy_level]
  // No calculation needed — direct mapping

STEP 5 — DIMENSION 5: Policy Compliance (0–100)
  violations ← DB.get_violations(agent_id, window=30_days)
  IF violations is empty THEN dim_compliance ← 0 ELSE
    // Recency decay: violations decay from 1.0 → 0.1 over 30 days
    scored ← sum(
        VIOLATION_SEV[v.severity] * max(0.1, 0.9 ** days_since(v.occurred_at))
        for v in violations
    )
    dim_compliance ← min(scored, 100.0)

STEP 6 — COMPOSITE SCORE
  composite ← round(
    WEIGHTS.permission * dim_permission +
    WEIGHTS.data       * dim_data       +
    WEIGHTS.blast      * dim_blast      +
    WEIGHTS.autonomy   * dim_autonomy   +
    WEIGHTS.compliance * dim_compliance
  )  // round to nearest integer, clamp to [0, 100]

STEP 7 — TIER CLASSIFICATION
  tier ← CRITICAL if composite >= 80
         HIGH     if composite >= 60
         MEDIUM   if composite >= 40
         LOW      if composite >= 20
         MINIMAL  otherwise

STEP 8 — PERSIST AND PUBLISH
  TimescaleDB.insert(time=NOW, agent_id, composite, tier, dim_*, blast_count, trigger_type)
  Redis.set(key=f'risk_score:{agent_id}', value=composite, ttl=300s)
  Kafka.publish(topic=risk.score_updates, event=RiskScoreUpdate{old, new, ...})

RETURN RiskScore {composite, tier, dimensions=[...], blast_radius=blast_count} |
| --- |
| ALGORITHM UpdateBehaviouralBaseline(event: AgentActionEvent, baseline: AgentBaseline):

RETURNS: (updated_baseline: AgentBaseline, anomaly_z_score: float)

CONSTANTS:
  ALPHA = 0.05      // EMA decay factor — higher = faster adaptation
  FLOOR_SIGMA = 0.01 // Minimum sigma to avoid division by zero
  MIN_SAMPLES = 20  // Minimum samples before anomaly alerts fire

KEY = (event.tool_name, event.destination)  // Uniquely identifies a call pattern

// Retrieve current EMA statistics for this (tool, destination) pair
mu_old  ← baseline.call_rate_ema.get(KEY, default=0.0)
var_old ← baseline.call_rate_var.get(KEY, default=1.0)

// Observed: 1 call in this time bucket
observed = 1.0

// Welford's online algorithm for EMA mean + variance
delta  ← observed - mu_old
mu_new  ← mu_old + ALPHA * delta
var_new ← (1 - ALPHA) * (var_old + ALPHA * delta^2)

// Update baseline
baseline.call_rate_ema[KEY] ← mu_new
baseline.call_rate_var[KEY] ← var_new
baseline.n_samples          ← baseline.n_samples + 1

// Compute z-score (deviation from baseline in units of standard deviation)
sigma   ← max(sqrt(var_new), FLOOR_SIGMA)
z_score ← abs(observed - mu_new) / sigma

// Only alert if we have enough samples to trust the baseline
IF baseline.n_samples < MIN_SAMPLES THEN z_score ← 0.0

RETURN (updated_baseline=baseline, anomaly_z_score=z_score)

// Caller: if z_score > SIGMA_THRESHOLD (3.0), emit AnomalyFinding |
| --- |
| ALGORITHM ResolveConflict(policies: []Policy, input: EvaluationInput):

INPUTS: List of all active policies that match the input scope
OUTPUT: (decision: Decision, winning_policy: Policy?)

// Step 1: Collect decisions from each applicable policy
deny_policies    ← [p for p in policies if p.action=='DENY'    and policy_matches(p, input)]
escalate_policies← [p for p in policies if p.action=='ESCALATE'and policy_matches(p, input)]
allow_policies   ← [p for p in policies if p.action=='ALLOW'   and policy_matches(p, input)]

// Step 2: L0 (Platform Baseline) always evaluated first
IF platform_baseline_fires(input) THEN
  RETURN (DENY, platform_policy)

// Step 3: DENY wins — most restrictive wins (Fail Secure)
// When multiple DENY policies match, return the highest-severity one
IF len(deny_policies) > 0 THEN
  winning ← argmax(p.severity for p in deny_policies)
  RETURN (DENY, winning)

// Step 4: ESCALATE wins over ALLOW
// When multiple ESCALATE policies match, use the highest HITL tier
IF len(escalate_policies) > 0 THEN
  winning ← argmax(p.hitl_tier for p in escalate_policies)
  RETURN (ESCALATE, winning)

// Step 5: Only ALLOW if no DENY or ESCALATE matched
// Note: explicit ALLOW policies at L3 can override L2 ESCALATE ONLY if
// they are agent-specific (L3) AND the escalate policy is not L0 or L1
RETURN (ALLOW, null)

// Complexity: O(P) where P = number of active policies per tenant
// Performance: with OPA caching, entire evaluation takes <5ms |
| --- |
| Env Variable | Type | Description | Source |
| --- | --- | --- | --- |
| AWS_REGION | string | AWS region for this deployment (us-east-1|eu-west-1|ap-southeast-1) | EKS node metadata |
| K8S_NAMESPACE | string | Kubernetes namespace (injected by Downward API) | K8s Downward API |
| K8S_POD_NAME | string | Pod name for logging and tracing (Downward API) | K8s Downward API |
| OTEL_EXPORTER_OTLP_ENDPOINT | string | OpenTelemetry collector endpoint (Datadog Agent) | ConfigMap |
| OTEL_SERVICE_NAME | string | Service name for distributed traces (set per service) | Helm values |
| LOG_LEVEL | string | DEBUG|INFO|WARN|ERROR (default INFO in prod) | Helm values |
| LOG_FORMAT | string | json (always in prod; text for local dev) | Helm values |
| VAULT_ADDR | string | HashiCorp Vault server address | ConfigMap |
| VAULT_ROLE | string | Vault AppRole for IRSA authentication (per-service role) | Helm values |
| KAFKA_BOOTSTRAP_SERVERS | string | MSK bootstrap server list (from MSK configuration) | External Secrets → ConfigMap |
| KAFKA_SECURITY_PROTOCOL | string | SASL_SSL (always in prod) | ConfigMap |
| KAFKA_SASL_MECHANISM | string | AWS_MSK_IAM | ConfigMap |
| Variable | Used By | Description |
| --- | --- | --- |
| DATABASE_URL | platform, policy, discovery, hitl, compliance | PostgreSQL connection string: postgres://{user}:{pass}@{host}:{port}/{db}?sslmode=require |
| TIMESCALE_URL | aispm-engine | TimescaleDB connection string (same format as DATABASE_URL; different DB) |
| NEO4J_URI | aispm-engine, investigation | Bolt URI: bolt+s://{host}:7687 (AuraDB) or bolt://{host}:7687 (local dev) |
| NEO4J_USER | aispm-engine, investigation | Neo4j username (from External Secrets) |
| NEO4J_PASSWORD | aispm-engine, investigation | Neo4j password (from External Secrets → Vault) |
| REDIS_URL | all services | Redis connection string: rediss://{host}:6379 (TLS in prod) |
| REDIS_PASSWORD | all services | Redis AUTH password (from External Secrets → Vault) |
| OPENSEARCH_ENDPOINT | audit, investigation, compliance | OpenSearch domain endpoint (HTTPS) |
| OPENSEARCH_USERNAME | audit, investigation, compliance | OpenSearch username (from External Secrets) |
| OPENSEARCH_PASSWORD | audit, investigation, compliance | OpenSearch password (from External Secrets → Vault) |
| Secret Path | Service | Content | Rotation |
| --- | --- | --- | --- |
| secret/pinaka/{tenant_id}/signing_key | discovery-engine (AIT issuance) | Ed25519 private key for AIT signing | Never rotated; created once per tenant; backed up |
| secret/pinaka/{tenant_id}/connector/{connector_id} | discovery-engine | Connector API key / OAuth token | 90-day auto-rotation via Temporal AITExpiryWorkflow |
| secret/pinaka/platform/jwt_private_key | platform-service | RSA-2048 private key for JWT RS256 signing | Annual rotation; dual-key window 24h |
| secret/pinaka/platform/db_password | all services | PostgreSQL master password | 90-day; zero-downtime via PgBouncer reconnect |
| secret/pinaka/platform/redis_password | all services | ElastiCache AUTH password | 90-day; rolling restart |
| secret/pinaka/notification/slack_bot_token | notification-service | Slack Bot OAuth token | On compromise; Slack console rotation |
| secret/pinaka/notification/pagerduty_key | notification-service | PagerDuty Events API v2 key | On compromise |
| secret/pinaka/notification/twilio_sid+token | notification-service | Twilio Account SID + Auth Token | 90-day |
| secret/pinaka/bedrock/endpoint | audit, investigation | AWS Bedrock endpoint (region-specific) | Static; updated on region change |
| secret/pinaka/neo4j/credentials | aispm, investigation | Neo4j AuraDB username + password | 90-day; AuraDB console rotation |
| secret/pinaka/opensearch/credentials | audit, investigation, compliance | OpenSearch master user + password | 90-day |
| secret/pinaka/tenant/{tenant_id}/webhook_secret | notification-service | HMAC-SHA256 secret for customer webhooks | Customer-triggered or on compromise |
| Service | Min Coverage | Critical Paths (100% required) | Test Framework |
| --- | --- | --- | --- |
| policy-engine | 90% | EvaluateAction, ConflictResolver, BundleCache.InvalidateTenant, ShadowEnforcer | Go testing + testify |
| mcp-gateway | 85% | All 11 pipeline stages, tokenBucketLua (Redis script), AIT signature verify | Go testing + testify |
| discovery-engine | 85% | AITIssuer.IssueAIT, ShadowAgentDetector.DetectShadowAgents, ConnectorManager.rotate | Go testing + testify |
| aispm-engine | 85% | RiskCalculator.calculate (all 5 dimensions), ARMDataBuilder.build | pytest + pytest-asyncio |
| audit-service | 90% | ChainWriter.WriteEvent (chain integrity), NLQueryEngine.translateNL (privacy check) | Go testing + testify |
| investigation-engine | 85% | All 5 AnomalyDetectors, update_baseline (Welford's), generate_narrative (no raw data leak) | pytest |
| platform-service | 90% | JWTIssuer.Issue + Refresh, ValidateAIT (all invalid cases), CheckRBAC | Go testing + testify |
| hitl-service | 90% | HITLManager.Create, Approve, ProcessExpiredRequests (all timeout scenarios) | Go testing + testify |
| notification-service | 85% | DispatcherEngine (idempotency), WebhookChannel.Send (HMAC verify), sendWithRetry | Go testing + testify |
| compliance-engine | 85% | EUAIActMapper.map_event (all control mappings), ReportGenerator.generate | pytest |
| OPA Rego policies | 100% | All Rego policy rules must have opa test coverage | opa test |
| Test Scenario | Services Involved | Setup | Assertion | SLO |
| --- | --- | --- | --- | --- |
| Full enforcement path: ALLOW | mcp-gateway → policy-engine → audit-service | Active tenant with L1 ALLOW policy; registered agent with valid AIT; Kafka running | Decision=ALLOW in <500ms; audit event in Iceberg within 5s; risk score unchanged | p99 <500ms |
| Full enforcement path: DENY + risk increase | mcp-gateway → policy-engine → audit-service → aispm-engine | Active L1 DENY policy for PII export; agent sends PII tool call | Decision=DENY; HTTP 403 returned; audit event signed+written; risk score increases by >5 within 30s | End-to-end <30s |
| HITL full cycle: Approve | mcp-gateway → policy-engine → hitl-service → notification-service → mcp-gateway | ESCALATE policy; agent triggers action; Slack webhook configured | Action paused; Slack notification delivered within 10s; after human approval: action proceeds | Notification <10s; callback <5s after approval |
| AIT revocation propagation | platform-service → Redis → mcp-gateway | Issue AIT; revoke it via API; wait 5s; send request with revoked AIT | Request rejected with AIT_REVOKED within 6s of revocation | Propagation <6s |
| Discovery scan + risk scoring | discovery-engine → aispm-engine → neo4j → timescale | Connector with 5 mock agents; trigger scan | All 5 agents in inventory within 2hr; risk scores calculated; ARM graph has all nodes | Scan <2hr; scores <30s after inventory |
| Audit NL query | audit-service → opensearch → bedrock | 100 audit events indexed; NL query: 'show DENY decisions last 24h' | Correct events returned; summary accurate; no raw content in Bedrock call | Response <3s |
| Tenant isolation | any service → PostgreSQL | Two tenants; write resource for tenant A; attempt to read as tenant B | Tenant B receives 404 (RLS filters out tenant A's data) | Zero cross-tenant leaks in 1000 random queries |
| Consumer | Provider | Contract Key Points | Verification Frequency |
| --- | --- | --- | --- |
| mcp-gateway | policy-engine | EvaluateActionRequest schema; Decision enum values; EvaluatedAt timestamp present; error response for UNAVAILABLE | Every PR + nightly |
| api-gateway | platform-service | ValidateJWT returns roles[]; GetTenantContext returns plan_tier; CheckRBAC returns allowed bool | Every PR |
| api-gateway | audit-service | GET /v1/audit/events returns PaginationInfo; POST /v1/audit/queries returns summary + events[] | Every PR |
| notification-service | hitl-service | HITLRequestEvent Avro schema; timeout_at_sec is unix timestamp; callback_url is valid HTTPS | Every PR |
| console-ui | api-gateway | AgentSummary schema; ARMResponse schema; RiskDimension schema; PaginationInfo cursor format | Every PR + before release |
| Endpoint | Auth Required | Rate Limit | Input Validation | MFA Required | Audit Logged |
| --- | --- | --- | --- | --- | --- |
| POST /v1/auth/login | None (pre-auth) | 5 req/min per IP (anti-brute-force) | Email format; password non-empty; tenant domain check | No (pre-auth) | Yes |
| POST /v1/auth/refresh | Refresh token (HttpOnly cookie) | 10/min per user | Refresh token length/format | No | Yes |
| GET /v1/inventory/agents | JWT Bearer | 500/min per API key (plan tier) | Query params: valid enum values; cursor format; limit 1–100 | No | No (read) |
| POST /v1/inventory/agents | JWT Bearer + security_engineer role | 60/min per tenant | All fields: size limits; fingerprint: 64-char hex; email format; tools: enum validation | No | Yes |
| POST /v1/policies | JWT Bearer + security_engineer role | 30/min per tenant | Rego syntax validation (opa check); scope_type enum; action enum; HITL tier 1–4 if ESCALATE | No | Yes |
| PUT /v1/policies/{id} | JWT Bearer + security_engineer role | 30/min per tenant | Same as POST; version field required (optimistic lock) | No | Yes |
| DELETE /v1/policies/{id} | JWT Bearer + tenant_admin role | 10/min per tenant | Valid UUID; policy must exist in tenant | Yes (MFA) | Yes |
| POST /v1/hitl/{id}/approve | JWT Bearer + security_analyst role | 60/min per user | Valid UUID; request must be PENDING | Yes (MFA, <5min ago) | Yes |
| POST /v1/hitl/{id}/deny | JWT Bearer + security_analyst role | 60/min per user | Valid UUID; request must be PENDING | Yes (MFA, <5min ago) | Yes |
| POST /v1/audit/queries | JWT Bearer | 30/min per tenant | nl_query: max 1000 chars; no injection attempts | No | Yes (query logged) |
| GET /v1/audit/events | JWT or read-only API key | 200/min per key | All filters: valid enum/UUID/date-time | No | No |
| POST /v1/connectors | JWT Bearer + tenant_admin role | 10/min per tenant | Connector type: valid enum; vault_secret_path: valid format; no credentials in config | Yes (MFA) | Yes |
| DELETE /v1/connectors/{id} | JWT Bearer + tenant_admin role | 5/min per tenant | Valid UUID; connector must exist in tenant | Yes (MFA) | Yes |
| POST /v1/admin/tenants | JWT Bearer + super_admin role | 5/min globally | Tenant name: max 255 chars; region: valid enum; plan: valid enum | Yes (MFA) | Yes |
| GET /v1/risk/arm | JWT Bearer | 30/min per tenant | max_depth: 1–5 integer; agent_filter: valid UUID if provided | No | No |
| POST /v1/compliance/reports | JWT Bearer + security_engineer role | 5/min per tenant | framework_id: valid enum; period: valid date range; format: valid enum | No | Yes |
| Permission / Action | super_admin | tenant_admin | security_engineer | security_analyst | auditor | api_service |
| --- | --- | --- | --- | --- | --- | --- |
| View agent inventory | ✅ | ✅ | ✅ | ✅ | ✅ (no PII) | ✅ (scoped) |
| Register / update agents | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Delete agents | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| View risk scores + ARM | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| View audit log | ✅ | ✅ | ✅ | ✅ | ✅ (no metadata) | ✅ (scoped) |
| Execute NL audit query | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Create / edit policies | ✅ | ✅ | ✅ (L1–L2) | ❌ | ❌ | ❌ |
| Create L3 agent-specific policy | ✅ | ✅ + MFA | ❌ | ❌ | ❌ | ❌ |
| Approve / deploy policies | ✅ | ✅ + MFA | ❌ | ❌ | ❌ | ❌ |
| Approve HITL requests | ✅ | ✅ + MFA | ✅ + MFA | ✅ + MFA | ❌ | ❌ |
| Deny HITL requests | ✅ | ✅ + MFA | ✅ + MFA | ✅ + MFA | ❌ | ❌ |
| Create / edit connectors | ✅ | ✅ + MFA | ❌ | ❌ | ❌ | ❌ |
| Delete connectors | ✅ | ✅ + MFA | ❌ | ❌ | ❌ | ❌ |
| Generate compliance reports | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| View compliance posture | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Manage users / roles | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Configure SSO / notifications | ✅ | ✅ + MFA | ❌ | ❌ | ❌ | ❌ |
| Tenant billing / plan | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Create / manage tenants | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Revoke AITs | ✅ | ✅ + MFA | ✅ + MFA | ❌ | ❌ | ❌ |
| View Pinaka platform metrics | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| // temporal/workflows/discovery_scan.go

type DiscoveryScanParams struct {
    TenantID     string
    ConnectorIDs []string  // empty = all connectors for tenant
    IsTriggered  bool      // true = API-triggered; false = scheduled
}

// Workflow: DiscoveryScanWorkflow
// Task Queue: pinaka-discovery
// Schedule: every 60 min per tenant (Temporal Schedule)
// Timeout: 2 hours total; each activity 15 min
func DiscoveryScanWorkflow(ctx workflow.Context, params DiscoveryScanParams) error {
    // 1. Fetch credentials for all connectors (in parallel)
    var connectorCreds []ConnectorCredential
    _ = workflow.ExecuteActivity(ctx,
        activities.FetchConnectorCredentials,
        params.TenantID, params.ConnectorIDs,
    ).Get(ctx, &connectorCreds)

    // 2. Run discovery scans in parallel (up to MAX_CONCURRENT_SCANS)
    var results []ScanResult
    for _, cred := range connectorCreds {
        // Each connector scan is an independent activity with its own retry policy
        fut := workflow.ExecuteActivity(ctx,
            activities.ConnectorDiscover,
            ConnectorDiscoverParams{
                TenantID:    params.TenantID,
                ConnectorID: cred.ConnectorID,
                Credentials: cred,
            },
        )  // runs concurrently
        results = append(results, fut)  // collect futures
    }
    // Wait for all futures (collect results; failed = partial success)

    // 3. Diff new inventory against existing
    var diff InventoryDiff
    _ = workflow.ExecuteActivity(ctx, activities.DiffInventory, params.TenantID, results).Get(ctx, &diff)

    // 4. Update PostgreSQL inventory
    _ = workflow.ExecuteActivity(ctx, activities.UpdateInventory, params.TenantID, diff).Get(ctx, nil)

    // 5. Update Neo4j dependency graph
    _ = workflow.ExecuteActivity(ctx, activities.UpdateDependencyGraph, params.TenantID, diff).Get(ctx, nil)

    // 6. Detect shadow agents via IdP OAuth
    _ = workflow.ExecuteActivity(ctx, activities.DetectShadowAgents, params.TenantID).Get(ctx, nil)

    // 7. Publish scan_complete event to Kafka
    _ = workflow.ExecuteActivity(ctx, activities.PublishScanComplete, params.TenantID, diff).Get(ctx, nil)

    return nil  // Temporal marks workflow COMPLETED
}

// Activity Retry Policies:
// FetchConnectorCredentials: 3 retries; backoff 10s, 30s, 60s; non-retryable: VaultAuthError
// ConnectorDiscover: 3 retries; backoff 30s, 1min, 2min; non-retryable: ConnectorAuthError
// DiffInventory: 2 retries; backoff 5s, 10s; non-retryable: none
// UpdateInventory: 3 retries; backoff 5s, 15s, 30s; non-retryable: none
// UpdateDependencyGraph: 3 retries; backoff 10s, 30s, 60s; non-retryable: none |
| --- |
| // Runs hourly: scans for AITs expiring in next 7 days → notify
// Runs daily: scans for expired AITs → revoke

func AITExpiryWorkflow(ctx workflow.Context, tenantID string) error {
    // Notification pass: AITs expiring in 7 days
    var expiringSoon []AITRecord
    _ = workflow.ExecuteActivity(ctx, activities.ScanExpiringAITs,
        AITScanParams{TenantID: tenantID, WithinDays: 7}).Get(ctx, &expiringSoon)

    for _, ait := range expiringSoon {
        workflow.ExecuteActivity(ctx, activities.NotifyAITExpiry, ait)  // best-effort
    }

    // Revocation pass: AITs that have expired
    var expired []AITRecord
    _ = workflow.ExecuteActivity(ctx, activities.ScanExpiredAITs, tenantID).Get(ctx, &expired)

    for _, ait := range expired {
        // Revoke: mark in DB + add to Redis revocation set + publish event
        _ = workflow.ExecuteActivity(ctx, activities.RevokeAIT, ait).Get(ctx, nil)
    }

    return nil
} |
| --- |
| // pkg/errors/errors.go — standardised error wrapping for all Go services

type PinakaError struct {
    Code       ErrorCode   // machine-readable code (e.g., POLICY_NOT_FOUND)
    StatusCode int         // HTTP status code
    GRPCCode   codes.Code  // gRPC status code
    Message    string      // human-readable message
    Detail     string      // additional detail (not sent to external callers)
    Err        error       // wrapped underlying error (for logging)
    TenantID   string      // for audit/logging context
    RequestID  string      // for trace correlation
}

func (e *PinakaError) Error() string { return fmt.Sprintf('[%s] %s', e.Code, e.Message) }
func (e *PinakaError) Unwrap() error { return e.Err }

// Usage: always wrap errors at the boundary, never swallow
func (r *PolicyRepository) GetByID(ctx context.Context, id string) (Policy, error) {
    var p Policy
    err := r.db.QueryRowContext(ctx, 'SELECT ... WHERE id=$1', id).Scan(&p)
    if errors.Is(err, sql.ErrNoRows) {
        return Policy{}, &PinakaError{
            Code: POLICY_NOT_FOUND, StatusCode: 404, GRPCCode: codes.NotFound,
            Message: 'Policy not found',
            Detail: fmt.Sprintf('policy_id=%s not found in tenant', id),
        }
    }
    if err != nil {
        return Policy{}, &PinakaError{
            Code: DB_ERROR, StatusCode: 500, GRPCCode: codes.Internal,
            Message: 'Internal error',
            Err: fmt.Errorf('GetByID query: %w', err),
        }
    }
    return p, nil
} |
| --- |
| // internal/api/middleware/error_handler.go

func ErrorHandlerMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        rw := newResponseWriter(w)  // capture status code
        next.ServeHTTP(rw, r)

        if rw.error != nil {
            var pe *errors.PinakaError
            if errors.As(rw.error, &pe) {
                writeProblemDetail(w, r, pe)
            } else {
                // Unknown error — don't leak internal details
                writeProblemDetail(w, r, &errors.PinakaError{
                    Code: INTERNAL_ERROR, StatusCode: 500,
                    Message: 'An internal error occurred',
                })
                log.Error('unhandled_error', zap.Error(rw.error),
                    zap.String('request_id', r.Header.Get('X-Request-ID')))
            }
        }
    })
}

func writeProblemDetail(w http.ResponseWriter, r *http.Request, pe *errors.PinakaError) {
    problem := map[string]any{
        'type':     'https://docs.pinaka.ai/errors/' + strings.ToLower(string(pe.Code)),
        'title':    pe.Code.Title(),
        'status':   pe.StatusCode,
        'detail':   pe.Message,
        'instance': r.RequestURI,
        'extensions': map[string]any{
            'request_id': r.Header.Get('X-Request-ID'),
            'timestamp':  time.Now().UTC().Format(time.RFC3339Nano),
        },
    }
    w.Header().Set('Content-Type', 'application/problem+json')
    w.WriteHeader(pe.StatusCode)
    json.NewEncoder(w).Encode(problem)
} |
| --- |
| ⚠ | Only replay a DLQ AFTER the root cause is fixed. Replaying before fixing the cause will re-fill the DLQ and potentially cause duplicate side effects in downstream services. |
| --- | --- |
| # DLQ Replay Procedure — step by step

# Step 1: Identify the consumer group and DLQ topic
# DLQ naming: pinaka.dlq.{consumer_group_id}
# e.g.: pinaka.dlq.audit-consumer

# Step 2: Inspect DLQ messages (understand root cause)
kafka-console-consumer.sh \
  --bootstrap-server $KAFKA_URL \
  --topic pinaka.dlq.audit-consumer \
  --from-beginning --max-messages 5

# Step 3: Confirm root cause is fixed
# e.g., for audit-consumer DLQ: verify Iceberg/S3 is reachable
curl -s $OPENSEARCH_ENDPOINT/_cat/health  # or relevant service check

# Step 4: Use Pinaka replay API (preferred — handles dedup + ordering)
curl -X POST https://api.pinaka.ai/v1/internal/dlq/replay \
  -H 'Authorization: Bearer $ADMIN_TOKEN' \
  -d '{
    "consumer_group": "audit-consumer",
    "dlq_topic": "pinaka.dlq.audit-consumer",
    "replay_from": "beginning",  // or "2026-04-01T00:00:00Z"
    "dry_run": true               // ALWAYS dry-run first
  }'

# Step 5: Review dry-run output
# Expected: {"message_count": N, "estimated_duration": "Xm", "would_affect": [...]}

# Step 6: Execute replay (remove dry_run)
# Replay API: reads DLQ, publishes each message back to original topic
# Idempotency: event_id dedup prevents duplicate audit writes

# Step 7: Monitor consumer lag returns to zero
kafka-consumer-groups.sh --bootstrap-server $KAFKA_URL --describe \
  --group audit-consumer | grep LAG

# Step 8: Verify no new DLQ messages
kafka-console-consumer.sh --topic pinaka.dlq.audit-consumer --max-messages 1 --timeout-ms 5000
# Expected: no output (DLQ empty) |
| --- |
| # | Check | How to Verify | Blocking? |
| --- | --- | --- | --- |
| 1 | All unit tests pass (>85% coverage per service) | CI/CD: test report; coverage report | Yes |
| 2 | Integration tests pass on staging | CI/CD: integration test suite green | Yes |
| 3 | OPA Rego unit tests pass (opa test ./policies/...) | CI/CD: opa test output | Yes |
| 4 | Pact contract tests verified | CI/CD: Pact broker verification green | Yes |
| 5 | No CRITICAL CVEs in container images (Trivy scan) | CI/CD: Trivy report; block if CRITICAL | Yes |
| 6 | No CRITICAL Semgrep findings | CI/CD: Semgrep report | Yes |
| 7 | SBOM generated and signed (Cosign) | CI/CD: cosign verify output | Yes |
| 8 | DB migration dry-run succeeds | CI/CD: Flyway dryRun in staging | Yes |
| 9 | OpenAPI spec backwards-compatible (no breaking changes) | CI/CD: oasdiff report | Yes (or requires version bump) |
| 10 | All ArgoCD apps sync green (staging) | ArgoCD UI: all apps Synced | Yes |
| 11 | SLOs met in staging load test (k6) | k6 report: p99 within SLO thresholds | Yes |
| 12 | Chaos experiment: kill policy-engine pod — recovery within SLA | Chaos test script output | Yes (monthly) |
| 13 | Datadog SLO monitors green for >24h in staging | Datadog: staging SLO dashboard | Yes |
| 14 | Runbook updated for any new alerts | GitHub: runbook PR reviewed | No (warning) |
| 15 | 2 engineering approvals on ArgoCD deploy PR | GitHub PR: 2 approvals | Yes |
| Step | Action | Verification | Rollback |
| --- | --- | --- | --- |
| 1 | Notify on-call team + post in #deploys: 'Deploying {version} to prod' | Acknowledgement from on-call SRE | N/A — pre-deploy |
| 2 | Run DB migrations (if any): goose -env prod up | Flyway migration report: all migrations applied | goose -env prod down {N} (N = number of new migrations) |
| 3 | Deploy Wave 0: platform-service | ArgoCD: platform-service Synced; /readyz returns 200 | helm rollback platform-service -n pinaka-platform |
| 4 | Deploy Wave 1: policy-engine, audit-service | ArgoCD: both Synced; enforcement test: POST /v1/enforcement/evaluate returns 200 | helm rollback policy-engine ... |
| 5 | Deploy Wave 2: discovery-engine, aispm-engine, investigation-engine | ArgoCD: all Synced; connector health checks pass | helm rollback ... |
| 6 | Deploy Wave 3: mcp-gateway (5% canary) | Istio: 5% traffic to new version; Datadog: error rate <0.1% for 15 min | Istio: set canary weight to 0% |
| 7 | Promote canary: 25% traffic | Datadog: SLO maintained for 15 min at 25% | Same as step 6 |
| 8 | Promote canary: 100% traffic | Datadog: SLO maintained for 30 min at 100% | Same as step 6 |
| 9 | Deploy Wave 4: api-gateway, notification-service, hitl-service, compliance-engine | ArgoCD: all Synced | helm rollback per service |
| 10 | Smoke test: full ALLOW + DENY path | go run ./tools/pinaka-dev smoke-test --env prod | N/A — detect and rollback if fail |
| 11 | Post in #deploys: 'Deploy complete. {version} in prod. Monitoring.' | SRE acknowledges | N/A |
| // pkg/pagination/cursor.go — used by all list endpoints

type Cursor struct {
    SortValue string  // value of the sort field at the boundary
    ID        string  // UUID v7 of the boundary record (tie-break)
}

func EncodeCursor(sortValue, id string) string {
    b, _ := json.Marshal(Cursor{SortValue: sortValue, ID: id})
    return base64.URLEncoding.EncodeToString(b)  // URL-safe, no padding issues
}

func DecodeCursor(encoded string) (Cursor, error) {
    b, err := base64.URLEncoding.DecodeString(encoded)
    if err != nil { return Cursor{}, ErrInvalidCursor }
    var c Cursor
    return c, json.Unmarshal(b, &c)
}

// PostgreSQL query with cursor (risk_score DESC, id DESC sort):
const listAgentsSQL = `
    SELECT id, name, risk_score, risk_tier, status, owner_email, last_active_at
    FROM agents
    WHERE tenant_id = $1
      AND deleted_at IS NULL
      AND ($2::text IS NULL OR (risk_score, id::text) < ($2::int, $3))
    ORDER BY risk_score DESC, id DESC
    LIMIT $4   -- fetch limit+1 to determine has_more
`

func BuildListResponse(records []Agent, limit int) ListResponse {
    hasMore := len(records) > limit
    if hasMore { records = records[:limit] }  // trim the extra record

    var nextCursor string
    if hasMore && len(records) > 0 {
        last := records[len(records)-1]
        nextCursor = EncodeCursor(fmt.Sprintf('%d', last.RiskScore), last.ID)
    }
    return ListResponse{Data: records, Pagination: PaginationInfo{
        Limit: limit, NextCursor: nextCursor, HasMore: hasMore,
    }}
} |
| --- |
| // pkg/idempotency/middleware.go
// Applied to: POST /v1/agents, POST /v1/policies, POST /v1/hitl/{id}/approve

const IdempotencyTTL = 24 * time.Hour
const IdempotencyLockTTL = 30 * time.Second

func IdempotencyMiddleware(redis redis.Client) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            key := r.Header.Get('Idempotency-Key')
            if key == '' || r.Method != 'POST' { next.ServeHTTP(w, r); return }

            // Validate UUID v4 format
            if !isUUIDv4(key) { writeProblem(w, 400, 'invalid_idempotency_key'); return }

            tenantID := r.Context().Value('tenant_id').(string)
            redisKey := fmt.Sprintf('idempotency:%s:%s', tenantID, key)

            // Try to acquire processing lock (prevents parallel requests with same key)
            lockKey := redisKey + ':lock'
            acquired, _ := redis.SetNX(r.Context(), lockKey, '1', IdempotencyLockTTL).Result()
            if !acquired {
                w.WriteHeader(409)
                writeProblem(w, 409, 'idempotency_key_in_use'); return
            }
            defer redis.Del(r.Context(), lockKey)

            // Check if already completed
            cached, err := redis.Get(r.Context(), redisKey).Result()
            if err == nil {  // cache hit — return stored response
                var stored StoredResponse
                json.Unmarshal([]byte(cached), &stored)
                w.WriteHeader(stored.Status)
                w.Write(stored.Body)
                w.Header().Set('X-Idempotency-Replayed', 'true'); return
            }

            // Execute and capture response
            rec := &ResponseRecorder{ResponseWriter: w}
            next.ServeHTTP(rec, r)

            // Only cache successful responses (2xx)
            if rec.Status >= 200 && rec.Status < 300 {
                stored, _ := json.Marshal(StoredResponse{Status: rec.Status, Body: rec.Body})
                redis.Set(r.Context(), redisKey, stored, IdempotencyTTL)
            }
        })
    }
} |
| --- |
| apiVersion: apps/v1
kind: Deployment
metadata:
  name: policy-engine
  namespace: pinaka-core
  labels:
    app: policy-engine
    version: v1.0.0
    pinaka.io/tier: core
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate: {maxSurge: 1, maxUnavailable: 0}  # Zero-downtime deploy
  selector:
    matchLabels: {app: policy-engine}
  template:
    metadata:
      labels:
        app: policy-engine
        version: v1.0.0
      annotations:
        # Triggers rolling restart on secret change (checksum updates via ESO)
        checksum/secret: '{{ include (print $.Template.BasePath "/secret.yaml") . | sha256sum }}'
        prometheus.io/scrape: 'true'
        prometheus.io/port: '9090'
        sidecar.istio.io/inject: 'true'
    spec:
      serviceAccountName: policy-engine  # IRSA annotation in serviceaccount.yaml
      topologySpreadConstraints:
      - maxSkew: 1  # Spread evenly across AZs
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector: {matchLabels: {app: policy-engine}}
      containers:
      - name: policy-engine
        image: ghcr.io/pinaka-ai/policy-engine:{{ .Values.image.tag }}
        ports:
        - {containerPort: 50051, name: grpc}
        - {containerPort: 8080,  name: http}
        - {containerPort: 9090,  name: metrics}
        resources:
          requests: {cpu: 250m, memory: 512Mi}
          limits:   {cpu: 2000m, memory: 2Gi}
        env:
        - name: PORT_GRPC
          value: '50051'
        - {name: DATABASE_URL,  valueFrom: {secretKeyRef: {name: policy-engine-secrets, key: DB_PASSWORD}}}
        - {name: REDIS_URL,     valueFrom: {secretKeyRef: {name: policy-engine-secrets, key: REDIS_URL}}}
        - {name: K8S_POD_NAME,  valueFrom: {fieldRef: {fieldPath: metadata.name}}}
        - {name: K8S_NAMESPACE, valueFrom: {fieldRef: {fieldPath: metadata.namespace}}}
        livenessProbe:
          httpGet: {path: /healthz, port: 8080}
          initialDelaySeconds: 60  # Wait for OPA bundle compilation
          periodSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet: {path: /readyz, port: 8080}
          initialDelaySeconds: 60
          periodSeconds: 5
          failureThreshold: 2
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          readOnlyRootFilesystem: true
          allowPrivilegeEscalation: false
          capabilities: {drop: [ALL]}
          seccompProfile: {type: RuntimeDefault}
        volumeMounts:
        - {name: tmp, mountPath: /tmp}  # Required for read-only root FS
        - {name: opa-policies, mountPath: /policies}
      volumes:
      - {name: tmp, emptyDir: {}}
      - {name: opa-policies, configMap: {name: opa-platform-policies}} |
| --- |
| Test Name | Tool | Duration | Shape | Acceptance Criteria | When Run |
| --- | --- | --- | --- | --- | --- |
| Enforcement Baseline | k6 | 10 min | 1000 RPS constant arrival rate | p99 <500ms; error rate <0.1%; no OOM | Nightly (staging) |
| Enforcement Spike | k6 | 3 min | Ramp 0→3000 RPS in 60s; hold 2min; ramp down | p99 <1000ms during spike; recovers to <500ms after; no crashes | Pre-release |
| Policy Bundle Cache Miss | k6 + manual | 5 min | 100 RPS; invalidate all bundles every 30s | p99 <2000ms during cache miss; recovers to <500ms on hit | Monthly |
| Kafka Consumer Lag | custom script | 30 min | Push 10K events/sec to enforcement topics; measure consumer lag | Lag never exceeds 50K events; recovers within 5 min of burst | Monthly |
| Discovery Scan Load | Temporal + k6 | 2 hours | Trigger 50 concurrent tenant scans | All scans complete within 2 hours; no Temporal workflow failures | Pre-release |
| Database Connection Pool | k6 | 10 min | 500 RPS with complex queries (multi-join) | PgBouncer pool saturation <70%; no connection wait timeouts | Monthly |
| ARM Graph Query | k6 | 5 min | 50 concurrent ARM requests (max_depth=3) | p99 <5s; Neo4j CPU <70% | Monthly |
| Route | Timeout | Retries | Retry On | Circuit Breaker Conditions |
| --- | --- | --- | --- | --- |
| mcp-gateway → policy-engine (EvaluateAction) | 10ms | 0 retries (DENY on failure — Fail Secure) | N/A | 5 consecutive errors → ejected 30s; max 50% ejection |
| mcp-gateway → policy-engine (management) | 5000ms | 3 retries; 1500ms per-try | gateway-error, connect-failure | Same as above |
| api-gateway → all services (REST) | 3000ms | 2 retries; 1000ms per-try | 5xx, connect-failure | 3 errors per 30s → ejected 30s |
| audit-service → opensearch | 3000ms | 3 retries; 1000ms per-try | 5xx, connect-failure | 5 errors → ejected 60s |
| investigation-engine → bedrock | 10000ms | 1 retry; 5000ms per-try | 5xx | No circuit breaker (external; already has timeout) |
| hitl-service → notification-service | 5000ms | 2 retries | 5xx | 3 errors → ejected 60s (notifications non-critical) |
| compliance-engine → audit-service | 30000ms | 2 retries | 5xx | 3 errors → ejected 30s (report generation is long-running) |
| Change Type | Avro Compatibility | Migration Strategy | Consumer Impact |
| --- | --- | --- | --- |
| Add optional field with default | BACKWARD compatible | Producers: add field with default; consumers: already handle by ignoring unknown | Zero — old consumers ignore new field |
| Add enum value | BACKWARD compatible (forward depends) | Add to producer schema first; consumers must handle unknown enum values gracefully | Update consumers first to handle unknown; then update producers |
| Remove optional field | FORWARD compatible only | Keep field in schema as deprecated for 2 major versions; consumers must not require it | Consumers must not depend on deprecated field before removal |
| Rename field | BREAKING — new major version | Add new field; dual-write old+new; migrate consumers; remove old field (3 releases) | 3-release migration; both consumers and producers need updates |
| Change field type | BREAKING — new major version | Create new schema version; maintain parallel consumers for transition period | Complex — requires coordination across all consumers |
| Change partition key | Requires new topic | Create new topic; run both topics in parallel; migrate consumers; decommission old | Zero consumer impact (they switch topics) |
| # .github/workflows/ci.yml — runs on every PR
name: CI
on: [pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Unit Tests (Go)
        run: go test ./... -short -count=1 -timeout 120s -coverprofile=coverage.out
      - name: Coverage Check
        run: go tool cover -func=coverage.out | grep 'total:' | awk '{if ($3+0 < 85) exit 1}'
      - name: OPA Policy Tests
        run: opa test ./policies/... -v --bundle
      - name: Integration Tests
        run: docker compose up -d && go test ./... -run Integration -timeout 300s
      - name: Semgrep SAST
        run: semgrep --config=.semgrep.yml --error
      - name: OpenAPI Diff (no breaking changes)
        run: oasdiff diff api/openapi.yaml origin/main:api/openapi.yaml --fail-on ERR

  build:
    needs: test
    steps:
      - name: Build and scan image
        run: |
          docker build -t $IMAGE .
          trivy image --exit-code 1 --severity CRITICAL $IMAGE
      - name: Generate and sign SBOM
        run: |
          syft $IMAGE -o cyclonedx-json > sbom.json
          cosign sign-blob --bundle=sbom.json.bundle sbom.json
      - name: Push to ECR (on merge to main only)
        if: github.ref == 'refs/heads/main'
        run: docker push $IMAGE |
| --- |
| Term | Definition | Used In |
| --- | --- | --- |
| Aho-Corasick | Multi-pattern string matching algorithm — O(n+m) complexity. Used in MCP Gateway injection detector for scanning tool call parameters against multiple injection patterns simultaneously. | MCP Gateway §3 |
| Avro | Binary serialisation format with schema evolution support. All Pinaka Kafka events use Avro with AWS Glue Schema Registry. | Kafka §16 |
| Bundle (OPA) | Compiled, gzipped set of Rego policies for a tenant. Stored in Redis (60s TTL). Evaluating from cache takes <5ms. | Policy Engine §2, §17 |
| Circuit Breaker | State machine: CLOSED (normal) → OPEN (failing; return fallback) → HALF-OPEN (test recovery). Trips at 50% error rate over 60s. Pinaka returns DENY (Fail Secure) when open. | §23, §3 |
| Cosign | Sigstore tool for signing container images and SBOMs. Pinaka signs every release image and verifies on deploy via Kubernetes admission controller. | §28 |
| Cursor Pagination | Pagination using an opaque cursor (base64-encoded sort field + UUID) instead of offset. Stable under concurrent inserts; no 'page drift'. All Pinaka list APIs use this. | §25 |
| Ed25519 | Fast, secure public-key signature algorithm. Used for: AIT signing (agent authentication), audit event hash chain (tamper detection). | §6, §4 |
| EMA | Exponential Moving Average — online algorithm for computing a weighted running average where recent observations matter more. Used in behavioural baseline to track normal call patterns. | Investigation Engine §7 |
| Exactly-Once | Kafka transaction mode: message is processed AND offset committed atomically. If either fails, both roll back. Used only for audit writes to prevent duplicate/missing events. | Audit Service §6 |
| Fingerprint | SHA-256 hash of an agent's source code + configuration at deployment time. Stored in AIT. MCP Gateway verifies fingerprint on every request to detect agent tampering. | §3, §4 |
| Glue Schema Registry | AWS-managed Avro schema registry. Pinaka uses it to enforce schema evolution rules (BACKWARD compatibility) across all Kafka producers/consumers. | §16, §28 |
| HPA | Horizontal Pod Autoscaler. Kubernetes mechanism to automatically scale pod count based on CPU, RPS, or custom metrics (e.g., Kafka consumer lag via KEDA). | §26 |
| Hypertable | TimescaleDB auto-partitioned PostgreSQL table. Automatically creates chunks by time dimension. Used for agent_risk_scores — enables fast time-range queries and compression. | DB §13 |
| Iceberg | Apache Iceberg — open table format for large analytic datasets on S3. Supports ACID, schema evolution, time travel. Pinaka uses it for the immutable audit log. | Audit §6, DB §13 |
| IRSA | IAM Roles for Service Accounts. AWS mechanism to give Kubernetes pods an IAM role via a service account annotation. Zero long-lived credentials in pods. | §26, §19 |
| LRU Cache | Least Recently Used cache — evicts the least recently accessed items when full. Pinaka uses in-memory LRU for tenant public keys (size 1000, TTL 5min). | §3, §8 |
| msgpack | Binary serialisation format, faster and smaller than JSON. Used for Redis baseline storage in Investigation Engine. | §7 |
| OPA | Open Policy Agent — CNCF-graduated policy evaluation engine. Pinaka uses OPA with Rego language for all policy enforcement decisions. | §2, §17 |
| Outbox Pattern | Transactional Outbox: write business record + event to outbox table in same DB transaction; a relay service polls the outbox and publishes to Kafka. Guarantees no event loss even if service crashes. | §2 (Policy Engine) |
| PKCE | Proof Key for Code Exchange — OAuth 2.1 extension to prevent auth code interception. Pinaka's SSO flow uses PKCE for all OIDC authentication. | §8 |
| PDB | PodDisruptionBudget. Kubernetes resource ensuring a minimum number of pods remain available during disruptions (rolling deploys, node drains). minAvailable=2 for all Pinaka services. | §26 |
| Rego | OPA's declarative policy language. Logic-based; human-readable. All Pinaka policies are written in Rego and versioned in git. | §17 |
| RLS | Row-Level Security. PostgreSQL feature that transparently filters query results based on a session variable (app.tenant_id). Pinaka's primary tenant isolation mechanism at the DB layer. | DB §13 |
| Saga | Distributed transaction pattern using compensating actions instead of 2PC. Pinaka uses choreography-based sagas via Kafka events for multi-service operations. | §22 |
| SBOM | Software Bill of Materials. Inventory of all components in a software release. Pinaka generates via Syft and signs via Cosign for every release. | §28 |
| Signing Key | Per-tenant Ed25519 key pair stored in HashiCorp Vault. Private key never leaves Vault (short-lived leases only). Public key distributed for AIT verification. | §4, §6, §8 |
| Temporal | Open-source durable workflow engine. Workflows survive service restarts; activities have individual retry policies. Used for discovery scans, compliance reports, AIT expiry. | §22 |
| Token Bucket | Rate limiting algorithm: a bucket fills at a constant rate (tokens/second); each request consumes one token; no token = throttled. Pinaka implements via Redis Lua script for atomicity. | §3 |
| UltraWarm | OpenSearch managed storage tier — significantly cheaper than hot storage; query performance slightly lower. Pinaka migrates audit indices >90 days old to UltraWarm. | §24 |
| UUID v7 | UUID format that encodes a millisecond timestamp in the first 48 bits, making them time-sortable. Pinaka uses UUID v7 for all primary keys and event IDs. | Global |
| WORM | Write Once Read Many. S3 Object Lock configuration with COMPLIANCE mode — no principal (including AWS root) can delete or modify objects during the lock period. Applied to the audit log bucket. | Audit §6 |
| Welford's Algorithm | Online algorithm for computing running mean and variance in a single pass with O(1) memory. Used in Investigation Engine's behavioural baseline to detect anomalous call rates. | §7, §18 |