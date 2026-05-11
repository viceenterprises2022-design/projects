<!-- converted from Pinaka_HLD_v1.1.docx -->




PINAKA
AGENTIC AI SECURITY PLATFORM
High Level Design  ·  v1.1  (Comprehensive — All Gaps Resolved)




v1.1 adds: MCP Gateway pipeline (§16), Policy Engine OPA design (§17), Auth flows (§18), Console UI + ARM + WebSocket (§19), Investigation Engine ML (§20), Connector SDK (§21), VPC design (§22), GitOps/Config mgmt (§23), OpenSearch indexes (§24), Risk score algorithm (§25), API patterns: pagination/idempotency/health checks/migrations (§26), Distributed consistency + secret rotation (§27), Performance tests + SRE runbook template (§28), Istio traffic management + Avro schema registry + container strategy (§29).


# Table of Contents

# 1. Document Purpose & Scope
This High Level Design (HLD) document is the primary engineering reference for Pinaka's development teams. It translates the Platform Architecture Document (v1.1) into concrete design specifications: service topologies, communication protocols, data models, sequence diagrams for all critical flows, Kafka event schemas, database table designs, API routing, Kubernetes layouts, and developer setup guides.

## 1.1  Relationship to Other Documents

## 1.2  How to Use This Document
- Read Section 2 (System Topology) first to understand the big picture
- Read Section 4 (Sequence Diagrams) to understand how components interact for each critical flow
- Reference Section 5 (Kafka Design) and Section 6 (Database Design) when building data-layer code
- Reference Section 7 (API Gateway) for all routing and auth middleware decisions
- Reference Section 9 (Kubernetes) for all infrastructure and deployment decisions
- Section 11 (Developer Setup) gets you running locally in <30 minutes
# 2. System Topology — Service Map
## 2.1  Service Inventory
Pinaka consists of 11 platform services + 4 infrastructure services. Each service is a separate deployable unit with its own repository, Dockerfile, Helm chart, and Kubernetes Deployment.

## 2.2  Service Communication Matrix
Pinaka uses three communication protocols based on latency requirements and coupling:

## 2.3  Full Service Interaction Map (Described)



# 3. gRPC Service Contracts (Enforcement Path)

## 3.1  Policy Engine gRPC Service

## 3.2  Platform Service gRPC — Auth & Tenant Context

## 3.3  gRPC Connection Management


# 4. Critical Path Sequence Diagrams

## 4.1  Policy Decision Flow (MCP Tool Call — Happy Path)
This is the most latency-critical path in Pinaka. Target: <500ms p99 end-to-end (v1.0); <100ms p99 (v1.5).
Sequence 1 — MCP Tool Call Policy Decision (ALLOW)

## 4.2  Policy Decision Flow — DENY Path
Sequence 2 — Policy Decision: DENY (PII Export Blocked)

## 4.3  HITL Escalation Flow (Tier 2 Approval)
Sequence 3 — HITL Tier 2: Hard Approval Required

## 4.4  Agent Registration & AIT Issuance Flow
Sequence 4 — New Agent Registered, AIT Issued

## 4.5  Discovery Scan Flow (Temporal Workflow)
Sequence 5 — Scheduled Discovery Scan via Temporal

## 4.6  Audit Event Write — Immutable Chain
Sequence 6 — Audit Event Write with Ed25519 Chain Integrity

## 4.7  Tenant Onboarding Flow
Sequence 7 — Enterprise Tenant Provisioned

## 4.8  Natural Language Audit Query Flow
Sequence 8 — Analyst NL Query: 'Show me all agents that accessed PII last 7 days'


# 5. Kafka Event Design
## 5.1  Topic Naming Convention

## 5.2  Topic Configuration

## 5.3  Event Schemas (Avro)

## 5.4  Consumer Group Design & Offset Management


# 6. Database Schema Design

## 6.1  Core PostgreSQL Tables
### 6.1.1  tenants

### 6.1.2  agents

### 6.1.3  agent_identity_tokens (AIT Registry)

### 6.1.4  policies

### 6.1.5  hitl_requests

### 6.1.6  connectors

## 6.2  TimescaleDB — Risk Score Hypertable

## 6.3  Neo4j — Graph Schema (Cypher)


# 7. API Gateway Design
## 7.1  Kong Route Configuration

## 7.2  Middleware Execution Chain

## 7.3  Error Response Standard (RFC 7807)


# 8. Kubernetes Architecture
## 8.1  Namespace Design
## 8.2  Resource Specifications


# 9. Caching Strategy


# 10. Background Jobs & Temporal Workflows
## 10.2  Temporal Task Queue Design


# 11. Developer Environment Setup
## 11.1  Prerequisites
## 11.2  Local Stack & Setup


# 12. Error Handling & Resilience Patterns


# 13. Observability Implementation
## 13.1  OpenTelemetry — Mandatory Instrumentation
## 13.2  Required Metrics per Service


# 14. HLD Open Items — Engineering Decisions Required



# 15. Glossary
Document Control: CONFIDENTIAL — v1.1 supersedes v1.0. Gaps audit: 31 items identified, all resolved in this revision. Next: per-service Low Level Design (LLD) documents after Engineering review sign-off.
# 16. MCP Gateway — Internal Architecture

## 16.1  Proxy Architecture — How Traffic Is Intercepted

## 16.2  Request Inspection Pipeline
Every MCP tool call processed by the Gateway passes through a linear pipeline of checks. Each stage is independently configured and can be bypassed per-tenant policy:

## 16.3  Gateway Internal Component Design (Go)


# 17. Policy Engine — OPA Bundle & Rego Module Design
## 17.1  Bundle Structure

## 17.2  Core Rego Modules

## 17.3  Policy Version Control & Bundle Rebuild


# 18. Authentication & Session Architecture
## 18.1  JWT Token Lifecycle
Sequence: JWT Refresh Flow

## 18.2  SSO / OIDC Federation Flow (Okta / Azure AD)
Sequence: Enterprise SSO Login

## 18.3  MFA Implementation

## 18.4  API Key Rotation Flow


# 19. Console UI Architecture

## 19.1  Application Structure

## 19.2  State Management

## 19.3  WebSocket Architecture

## 19.4  ARM (Agentic Risk Map) — D3.js Design
### 19.4.1  API Response Schema
### 19.4.2  D3.js Force Simulation Config


# 20. Investigation Engine — ML Design
## 20.1  Behavioural Baseline Algorithm

## 20.2  Anomaly Detection Model

## 20.3  Risk Narrative Generation Pipeline


# 21. Connector SDK — Internal Design
## 21.1  Event Normalisation Pipeline
Every connector translates source-system-specific events into Pinaka's canonical AgentActionEvent format. This normalisation pipeline runs inside the Discovery Engine for all connectors:

## 21.2  Connector Credential Lifecycle


# 22. Network Architecture — VPC & Subnet Design
## 22.1  VPC Layout (per Region)

## 22.2  VPC Endpoints (Eliminate NAT for AWS Services)

## 22.3  Security Groups


# 23. Configuration Management & GitOps Pipeline
## 23.1  Configuration Hierarchy

## 23.2  External Secrets Operator — Secret Sync

## 23.3  ArgoCD App-of-Apps Structure
## 23.4  Environment Promotion Flow


# 24. OpenSearch Index Design & Log Aggregation
## 24.1  OpenSearch Audit Index

## 24.2  Log Aggregation Pipeline


# 25. Risk Score Calculation — Detailed Algorithm



# 26. API Implementation Patterns
## 26.1  Cursor-Based Pagination

## 26.2  Idempotency Key Implementation

## 26.3  Service Health Check Specifications

## 26.4  Zero-Downtime Database Migration Rules

# 27. Distributed Consistency & Secret Rotation
## 27.1  Distributed Consistency Patterns


## 27.2  Secret Rotation Sequences
Sequence: Connector Credential Auto-Rotation (90-day Temporal Workflow)


# 28. Performance Testing Architecture & SRE Runbook Template
## 28.1  k6 Load Test Scenarios

## 28.2  SRE Runbook Standard Template

# 29. Istio Traffic Management & Avro Schema Registry
## 29.1  Istio VirtualService — Retry & Timeout per Route

## 29.2  Avro Schema Registry Design (AWS Glue)

## 29.3  Container Image Strategy

|  |
|  |
| Document Version | v1.1 — Comprehensive revision; 31 gaps identified and resolved |
| Date | April 2026 |
| Classification | CONFIDENTIAL — Internal Engineering Use Only |
| Input | Architecture Document v1.1; Gap audit (31 items) |
| Audience | All Engineering (Backend, Frontend, SRE, Security, QA) |
| Sections | 29 sections covering all service internals, flows, schemas, and patterns |
| Next | Low Level Design (LLD) per service |
| Audience | Backend Engineers, Frontend Engineers, SRE/DevOps, Security Engineers, QA. This document is the input to all per-service Low Level Designs (LLDs). |
| --- | --- |
| Document | Role | Status |
| --- | --- | --- |
| Platform Architecture Document v1.1 | Foundation: principles, NFRs, tech stack selection, component responsibilities | ✅ Complete |
| This HLD v1.0 | Service topology, sequence diagrams, schemas, Kafka design, K8s layout, API routing, DB models | ✅ This Document |
| Low Level Design (LLD) — per service | Internal service design, algorithm specs, full DB schemas, gRPC protobuf, OPA Rego examples | 🔜 Next — post-HLD review |
| UI/UX Design | Console wireframes, user journeys, ARM graph visual spec, design system | 🔜 Parallel track |
| Runbook & Operations Guide | Deployment procedures, alert runbooks, scaling, BCDR | 🔜 Sprint 5–6 |
| ⚠ | This document uses ASCII-art-style sequence tables (not image diagrams) so it remains editable and version-controlled in git. Each sequence table is self-documenting. Real C4 and UML diagrams will be generated in the LLD phase using PlantUML. |
| --- | --- |
| Service Name | Repo | Language | Owns | Runtime |
| --- | --- | --- | --- | --- |
| api-gateway | pinaka/api-gateway | Kong + Go | External-facing REST API, rate limiting, auth middleware, routing | Kong on EKS |
| mcp-gateway | pinaka/mcp-gateway | Go | Inline MCP proxy, AIT verification, tool-call enforcement | EKS — dedicated node group |
| discovery-engine | pinaka/discovery-engine | Go + Python | Agent inventory, connector lifecycle, scan orchestration, AIT issuance | EKS + Temporal workers |
| aispm-engine | pinaka/aispm-engine | Python | Risk scoring (5-dimension), Agentic Risk Map data, AISPM score updates | EKS |
| policy-engine | pinaka/policy-engine | Go + OPA | Policy CRUD, OPA evaluation, conflict resolution, dry-run, bundle cache | EKS — HPA on enforcement RPS |
| audit-service | pinaka/audit-service | Go | Event signing (Ed25519), Kafka consume, Iceberg write, NL query API | EKS |
| hitl-service | pinaka/hitl-service | Go | HITL request lifecycle, timeout management, notification dispatch | EKS |
| notification-service | pinaka/notification-service | Go | Slack/Teams/Email/PagerDuty/SMS/Webhook delivery, retry, DLQ | EKS |
| investigation-engine | pinaka/investigation-engine | Python | Behavioural baselining, anomaly detection, narrative generation, cross-agent correlation | EKS + scheduled jobs |
| compliance-engine | pinaka/compliance-engine | Python | Framework mapping, evidence collection, report generation | EKS + Temporal workers |
| platform-service | pinaka/platform-service | Go | Auth (JWT/OAuth), multitenancy, billing, user mgmt, tenant provisioning | EKS |
| console-ui | pinaka/console-ui | TypeScript + React | Browser console, ARM visualisation, policy editor, compliance dashboard | CloudFront + S3 |
| connector-sdk | pinaka/connector-sdk | Go + Python | Connector interface SDK (library, not a service) | Library — embedded in discovery-engine |
| temporal-workers | pinaka/temporal-workers | Go + Python | Durable workflow execution for scans, remediations, reports | EKS — Temporal worker pools |
| ops-tooling | pinaka/ops-tooling | Terraform + Helm | IaC, Helm charts, ArgoCD apps, runbooks (not a runtime service) | CI/CD |
| Protocol | Used For | Latency Target | Coupling | Tool |
| --- | --- | --- | --- | --- |
| gRPC (sync) | Enforcement path: mcp-gateway → policy-engine; internal health checks | <10ms | Tight — caller waits | gRPC + protobuf; Istio mTLS |
| REST (sync) | Management APIs: console-ui → api-gateway → services; service-to-service for non-critical calls | <200ms | Moderate — caller waits | HTTP/2 over mTLS; Kong routing |
| Kafka (async) | Event publishing: all events after enforcement decision; audit write; risk score updates; discovery results | <5s end-to-end | Loose — fire and forget | Kafka on AWS MSK; avro schemas |
| Temporal (async) | Long-running workflows: discovery scans, compliance report generation, multi-step remediations | Minutes–hours | Durable — survives restarts | Temporal Cloud or self-hosted |
| WebSocket | Real-time console updates (risk score changes, HITL alerts, discovery progress) | <1s | Stateful — long-lived connection | Kong WebSocket proxy → platform-service |
| ℹ | The following table maps every service-to-service interaction. Direction: caller → callee. This is the input to the network policy (Istio AuthorizationPolicy) configuration. |
| --- | --- |
| Caller | Callee | Protocol | Purpose | Auth |
| --- | --- | --- | --- | --- |
| External Agent (via AIT) | mcp-gateway | HTTPS (MCP) | Agent tool call or inter-agent message | AIT JWT verification |
| External Client | api-gateway | HTTPS REST | All customer API calls and console traffic | API Key or JWT |
| api-gateway | platform-service | gRPC | JWT validation, tenant context lookup, RBAC check | mTLS |
| api-gateway | policy-engine | gRPC | Forward policy CRUD and dry-run requests | mTLS |
| api-gateway | discovery-engine | REST | Trigger scans, fetch inventory | mTLS |
| api-gateway | aispm-engine | REST | Fetch risk scores, ARM graph data | mTLS |
| api-gateway | audit-service | REST | Fetch audit events, NL query, export | mTLS |
| api-gateway | compliance-engine | REST | Fetch reports, framework status, trigger report generation | mTLS |
| api-gateway | hitl-service | REST | Fetch HITL queue, approve/deny actions | mTLS |
| mcp-gateway | policy-engine | gRPC | Policy decision for every MCP tool call | mTLS |
| mcp-gateway | audit-service (via Kafka) | Kafka publish | Publish MCP event after decision | Kafka SASL/TLS |
| mcp-gateway | platform-service | gRPC | AIT validation and tenant context | mTLS |
| policy-engine | platform-service | gRPC | Fetch tenant policy bundle | mTLS |
| policy-engine → Kafka | audit-service | Kafka publish | Publish policy_decision event | Kafka SASL/TLS |
| policy-engine → Kafka | hitl-service | Kafka publish | Publish hitl_request event on ESCALATE | Kafka SASL/TLS |
| discovery-engine | platform-service | REST | Tenant context, connector credential fetch from Vault | mTLS |
| discovery-engine | aispm-engine (via Kafka) | Kafka publish | New agent discovered — trigger risk score | Kafka SASL/TLS |
| discovery-engine | audit-service (via Kafka) | Kafka publish | Discovery scan events | Kafka SASL/TLS |
| aispm-engine | Neo4j | Bolt protocol | Graph queries for ARM and blast radius | Vault-managed credentials |
| aispm-engine → Kafka | investigation-engine | Kafka publish | Risk score change events | Kafka SASL/TLS |
| hitl-service | notification-service | REST | Dispatch HITL notifications | mTLS |
| hitl-service → Kafka | audit-service | Kafka publish | HITL request/response audit events | Kafka SASL/TLS |
| investigation-engine | aispm-engine | REST | Trigger risk score recalculation on anomaly | mTLS |
| investigation-engine | AWS Bedrock | HTTPS | LLM call for risk narrative generation | IRSA |
| investigation-engine | audit-service | REST | Read audit stream for baselining | mTLS |
| compliance-engine | audit-service | REST | Read audit events for evidence collection | mTLS |
| compliance-engine | policy-engine | REST | Read policy registry for compliance mapping | mTLS |
| notification-service | Slack API | HTTPS | Deliver Slack notifications | Bot token in Vault |
| notification-service | PagerDuty API | HTTPS | Deliver PagerDuty incidents | API key in Vault |
| notification-service | AWS SES | AWS SDK | Deliver email notifications | IRSA |
| notification-service → Kafka | notification-service | Kafka | Webhook DLQ events | Kafka SASL/TLS |
| temporal-workers | discovery-engine | REST | Execute connector scan steps | mTLS |
| temporal-workers | compliance-engine | REST | Execute report generation steps | mTLS |
| Why gRPC for Enforcement | The enforcement path (mcp-gateway → policy-engine) must complete in <10ms. gRPC over HTTP/2 with persistent connections and binary protobuf serialisation delivers 5–10× lower latency than REST/JSON for this path. |
| --- | --- |
| // proto/policy/v1/policy.proto
syntax = "proto3";
package pinaka.policy.v1;

service PolicyEngine {
  // Primary enforcement call — must complete <10ms p99
  rpc EvaluateAction(EvaluateActionRequest) returns (EvaluateActionResponse);
  // Batch evaluation for bulk agent audit (async path)
  rpc EvaluateActionBatch(EvaluateActionBatchRequest) returns (EvaluateActionBatchResponse);
  // Fetch compiled policy bundle for a tenant (used by mcp-gateway for local cache)
  rpc GetPolicyBundle(GetPolicyBundleRequest) returns (stream PolicyBundleChunk);
  // Health check
  rpc HealthCheck(HealthRequest) returns (HealthResponse);
}

message EvaluateActionRequest {
  string tenant_id      = 1; // Required: tenant isolation key
  string agent_id       = 2; // Required: the acting agent
  string ait_id         = 3; // Required: AIT used to authenticate agent
  string tool_name      = 4; // The tool being called (e.g., "spreadsheet-read")
  string destination    = 5; // INTERNAL | EXTERNAL | MCP_SERVER | AGENT
  repeated string data_classifications = 6; // PII | IP | FINANCIAL | REGULATED | PUBLIC
  map<string,string> action_metadata   = 7; // Additional context for policy evaluation
  int64  request_timestamp = 8;             // Unix nanoseconds
}

message EvaluateActionResponse {
  string decision_id  = 1; // UUID for this decision — referenced in audit log
  Decision decision   = 2; // ALLOW | DENY | ESCALATE
  string reason       = 3; // Human-readable reason (policy name that triggered)
  string policy_id    = 4; // Winning policy UUID
  int32  risk_delta   = 5; // Projected risk score change from this action
  int64  evaluated_at = 6; // Unix nanoseconds — enforcement latency measured here
}

enum Decision { ALLOW = 0; DENY = 1; ESCALATE = 2; } |
| --- |
| // proto/platform/v1/platform.proto
service PlatformService {
  rpc ValidateAIT(ValidateAITRequest) returns (ValidateAITResponse);
  rpc ValidateJWT(ValidateJWTRequest) returns (ValidateJWTResponse);
  rpc GetTenantContext(GetTenantContextRequest) returns (TenantContext);
  rpc CheckRBAC(CheckRBACRequest) returns (CheckRBACResponse);
}

message ValidateAITResponse {
  bool   is_valid     = 1;
  string tenant_id   = 2;
  string agent_id    = 3;
  repeated string granted_tools    = 4;
  string fingerprint = 5;
  int64  expires_at  = 6;
  InvalidReason reason = 7; // EXPIRED | REVOKED | SIGNATURE_INVALID | FINGERPRINT_MISMATCH
}

message TenantContext {
  string tenant_id        = 1;
  string region           = 2; // us-east-1 | eu-west-1 | ap-southeast-1
  string plan_tier        = 3; // STARTER | PROFESSIONAL | ENTERPRISE | ENTERPRISE_PLUS
  map<string,string> feature_flags = 4; // LaunchDarkly flags for this tenant
  int32  enforcement_rps_limit     = 5;
  PolicyFailsafeMode failsafe_mode = 6; // DENY_ALL | ALLOW_WITH_ALERT
} |
| --- |
| Setting | Value | Rationale |
| --- | --- | --- |
| Connection pool size (mcp-gateway → policy-engine) | Min: 5, Max: 50 per policy-engine pod | Persistent gRPC connections; avoid TLS handshake overhead on every call |
| Keepalive ping interval | 30 seconds | Detect dead connections through NAT/load balancer |
| Keepalive timeout | 10 seconds | Fail fast on dead connections |
| Max message size | 4MB | Sufficient for policy bundle streaming; prevents memory attacks |
| Deadline (enforcement call) | 10ms for EvaluateAction | Hard deadline propagated from mcp-gateway; returns DENY on timeout (Fail Secure) |
| Deadline (GetPolicyBundle) | 5000ms | Bundle fetch is background; streaming allows progressive delivery |
| Retry policy | 3 retries on UNAVAILABLE; NOT_FOUND never retried | Prevent thundering herd; policy misses never retried (agent not registered) |
| Load balancing | Client-side gRPC round-robin across policy-engine pods | Avoids L4 load balancer for sub-10ms path; Kubernetes headless service for pod discovery |
| ℹ | Each table represents a sequence diagram. Row numbers = step order. Actor columns are colour-coded. '→' = synchronous call awaiting response. '→|' = async publish (no wait). '◁──' = response/return. |
| --- | --- |
| AI Agent | MCP Gateway | Platform Svc | Policy Engine | Kafka | Audit Service |
| --- | --- | --- | --- | --- | --- |
| [1] → tool_call(AIT, tool='spreadsheet-read', params={...}) | ────────▶ tool_call(AIT, tool='spreadsheet-read', params={...}) |  |  |  |  |
|  | [2] → ValidateAIT(ait_id, fingerprint) [gRPC <3ms] | ────────▶ ValidateAIT(ait_id, fingerprint) [gRPC <3ms] |  |  |  |
|  | ──▷ AIT valid; tenant_id; granted_tools | AIT valid; tenant_id; granted_tools ◁── |  |  |  |
|  | ⟳ Check AIT grants 'spreadsheet-read' tool [local <1ms] |  |  |  |  |
|  | ⟳ Scan params for PII/injection patterns [<5ms] |  |  |  |  |
|  | [6] → EvaluateAction(tenant_id, agent_id, tool, data_class) [gRPC] |  | ────────▶ EvaluateAction(tenant_id, agent_id, tool, data_class) [gRPC] |  |  |
|  |  |  | ⟳ Load policy bundle from Redis cache [<1ms] |  |  |
|  |  |  | ⟳ OPA evaluate: L0→L1→L2→L3 policies [<5ms] |  |  |
|  | ──▷ Decision: ALLOW; decision_id; risk_delta=0 |  | Decision: ALLOW; decision_id; risk_delta=0 ◁── |  |  |
| ────────▶ Forward tool call to MCP Server [proxied] | [10] ← Forward tool call to MCP Server [proxied] |  |  |  |  |
|  | ⟳ Scan MCP server response for sensitive data [<5ms] |  |  |  |  |
| ──▷ Return tool response to agent | Return tool response to agent ◁── |  |  |  |  |
|  | [13] → Publish: agent_action.ALLOW event (async, non-blocking) [→|] |  |  | ─ ─ ─ ▶ Publish: agent_action.ALLOW event (async, non-blocking) [→|] |  |
|  |  |  |  | [14] → Consume event; sign with Ed25519; write to Iceberg | ─ ─ ─ ▶ Consume event; sign with Ed25519; write to Iceberg |
| 📝 Total latency budget: AIT ~3ms + Param scan ~5ms + OPA ~5ms + Response scan ~5ms = ~18ms core + network overhead |  |  |  |  |  |
| AI Agent | MCP Gateway | Policy Engine | Kafka | HITL Service | Notification Svc |
| --- | --- | --- | --- | --- | --- |
| [1] → tool_call(AIT, tool='email-send', params={to:'external@vendor.com', data:'Q1_REVENUE.xlsx'}) | ────────▶ tool_call(AIT, tool='email-send', params={to:'external@vendor.com', data:'Q1_REVENUE.xlsx'}) |  |  |  |  |
|  | ⟳ DLP scan: data_classification=['FINANCIAL','PII'] detected [<5ms] |  |  |  |  |
|  | [3] → EvaluateAction(tool='email-send', destination=EXTERNAL, data_class=[FINANCIAL,PII]) | ────────▶ EvaluateAction(tool='email-send', destination=EXTERNAL, data_class=[FINANCIAL,PII]) |  |  |  |
|  |  | ⟳ Policy pol_fin_no_pii_export matches — decision: DENY |  |  |  |
|  | ──▷ Decision: DENY; reason='External PII export blocked'; policy_id | Decision: DENY; reason='External PII export blocked'; policy_id ◁── |  |  |  |
| ──▷ DENY response: HTTP 403 {error:'policy_violation', decision_id:'...'} | DENY response: HTTP 403 {error:'policy_violation', decision_id:'...'} ◁── |  |  |  |  |
|  | [7] → Publish: policy_violation.DENY event [→|] |  | ─ ─ ─ ▶ Publish: policy_violation.DENY event [→|] |  |  |
|  |  |  | [8] → Consume policy_violation event; update agent risk score | ────────▶ Consume policy_violation event; update agent risk score |  |
|  |  |  | ─ ─ ─ ▶ Publish: risk_score.update (delta=+15) [→|] | [9] ← Publish: risk_score.update (delta=+15) [→|] |  |
|  |  |  | [10] → Consume risk_score.update; check alert thresholds |  | ────────▶ Consume risk_score.update; check alert thresholds |
|  |  |  |  |  | ⟳ Threshold exceeded — send Slack alert to #security-alerts |
| 📝 DENY is synchronous — agent gets the 403 immediately. All side-effects (audit, risk update, alert) are async and non-blocking. |  |  |  |  |  |
| AI Agent | MCP Gateway | Policy Engine | HITL Service | Notification | Security Engineer |
| --- | --- | --- | --- | --- | --- |
| [1] → tool_call(AIT, tool='bulk-data-export', params={rows:50000}) | ────────▶ tool_call(AIT, tool='bulk-data-export', params={rows:50000}) |  |  |  |  |
|  | [2] → EvaluateAction(tool='bulk-data-export', row_count=50000) | ────────▶ EvaluateAction(tool='bulk-data-export', row_count=50000) |  |  |  |
|  |  | ⟳ Policy pol_bulk_export_escalate matches — decision: ESCALATE (Tier 2) |  |  |  |
|  | ──▷ Decision: ESCALATE; hitl_tier=2; timeout_sec=900 | Decision: ESCALATE; hitl_tier=2; timeout_sec=900 ◁── |  |  |  |
|  | ⟳ PAUSE action — agent connection held open (HTTP long-poll or WebSocket) |  |  |  |  |
|  | [6] → CreateHITLRequest(agent_id, action, tier=2, timeout=900s) [REST] |  | ────────▶ CreateHITLRequest(agent_id, action, tier=2, timeout=900s) [REST] |  |  |
|  |  |  | [7] → DispatchNotification(Slack+Email, approver_group='security-engineers') [REST] | ────────▶ DispatchNotification(Slack+Email, approver_group='security-engineers') [REST] |  |
|  |  |  |  | [8] → Slack message: '[HITL] bulk-data-export by finance-agent — APPROVE or DENY (15 min)' | ────────▶ Slack message: '[HITL] bulk-data-export by finance-agent — APPROVE or DENY (15 min)' |
| 📝 Human reviews the HITL request in Slack or Pinaka Console — sees agent identity, action details, risk score, business context narrative |  |  |  |  |  |
|  |  |  | ────────▶ POST /v1/hitl/{id}/approve (JWT authenticated, MFA verified) [REST] |  | [10] ← POST /v1/hitl/{id}/approve (JWT authenticated, MFA verified) [REST] |
|  |  |  | ⟳ Write hitl_response to audit log; update HITL request status=APPROVED |  |  |
|  | ──▷ HITL approved — resume action [webhook callback] |  | HITL approved — resume action [webhook callback] ◁── |  |  |
| ────────▶ Forward tool call to MCP Server (action proceeds) | [13] ← Forward tool call to MCP Server (action proceeds) |  |  |  |  |
| ──▷ Return tool response | Return tool response ◁── |  |  |  |  |
| ── Timeout Path (if no human responds within 15 min) ── | ── Timeout Path (if no human responds within 15 min) ── | ── Timeout Path (if no human responds within 15 min) ── | ── Timeout Path (if no human responds within 15 min) ── | ── Timeout Path (if no human responds within 15 min) ── | ── Timeout Path (if no human responds within 15 min) ── |
|  |  |  | ⟳ [TIMER EXPIRES] Auto-DENY; write timeout_deny to audit log |  |  |
|  | ──▷ HITL timed out — DENY action [webhook callback] |  | HITL timed out — DENY action [webhook callback] ◁── |  |  |
| ──▷ DENY response: HTTP 403 {error:'hitl_timeout'} | DENY response: HTTP 403 {error:'hitl_timeout'} ◁── |  |  |  |  |
| Security Admin | API Gateway | Discovery Engine | Platform Service | HashiCorp Vault | Kafka |
| --- | --- | --- | --- | --- | --- |
| [1] → POST /v1/agents {name, type, owner, framework, fingerprint, tools[]} | ────────▶ POST /v1/agents {name, type, owner, framework, fingerprint, tools[]} |  |  |  |  |
|  | [2] → ValidateJWT + CheckRBAC(role='security_engineer', action='agent:create') [gRPC] |  | ────────▶ ValidateJWT + CheckRBAC(role='security_engineer', action='agent:create') [gRPC] |  |  |
|  | ──▷ Auth OK; TenantContext{tenant_id, region} |  | Auth OK; TenantContext{tenant_id, region} ◁── |  |  |
|  | [4] → RegisterAgent(agent_metadata) [REST] | ────────▶ RegisterAgent(agent_metadata) [REST] |  |  |  |
|  |  | ⟳ Validate: fingerprint format; tool list against connector schemas; owner exists |  |  |  |
|  |  | [6] → Fetch tenant signing key (Ed25519 private key) [Vault API] |  | ────────▶ Fetch tenant signing key (Ed25519 private key) [Vault API] |  |
|  |  | ──▷ Signing key (short-lived lease, 60s) |  | Signing key (short-lived lease, 60s) ◁── |  |
|  |  | ⟳ Issue AIT: sign JWT with tenant key; set expiry=90 days; include fingerprint+tools |  |  |  |
|  |  | [9] → Store AIT metadata in Vault (ait_id → agent_id mapping) |  | ────────▶ Store AIT metadata in Vault (ait_id → agent_id mapping) |  |
|  |  | [10] → Publish: agent_registered event [→|] |  |  | ─ ─ ─ ▶ Publish: agent_registered event [→|] |
|  | ──▷ RegisterAgent response: {agent_id, ait_token, ait_expires_at} | RegisterAgent response: {agent_id, ait_token, ait_expires_at} ◁── |  |  |  |
| ──▷ 201 Created {agent_id, ait_token (show once), expires_at} | 201 Created {agent_id, ait_token (show once), expires_at} ◁── |  |  |  |  |
| 📝 AIT token shown only once at registration. Admin distributes it to agent deployment config. Lost AITs require re-registration. |  |  |  |  |  |
|  |  | ────────▶ Consume agent_registered — trigger initial discovery scan for this agent |  |  | [14] ← Consume agent_registered — trigger initial discovery scan for this agent |
|  |  | ────────▶ Consume agent_registered — trigger initial risk scoring via aispm-engine |  |  | [15] ← Consume agent_registered — trigger initial risk scoring via aispm-engine |
| Temporal | Discovery Worker | Source Connector
(e.g. AWS Bedrock) | Neo4j Graph | Kafka | AISPM Engine |
| --- | --- | --- | --- | --- | --- |
| [1] → [SCHEDULED TRIGGER] StartScanWorkflow(tenant_id, connector_ids[]) | ────────▶ [SCHEDULED TRIGGER] StartScanWorkflow(tenant_id, connector_ids[]) |  |  |  |  |
|  | ⟳ Activity: FetchConnectorCredentials from Vault |  |  |  |  |
|  | [3] → Activity: connector.discover() — fetch all agents/tools/datasources | ────────▶ Activity: connector.discover() — fetch all agents/tools/datasources |  |  |  |
|  | ──▷ []AgentRecord — list of agents with metadata and fingerprints | []AgentRecord — list of agents with metadata and fingerprints ◁── |  |  |  |
|  | ⟳ Activity: DiffInventory(new_records, existing_inventory) — find new/changed/deleted |  |  |  |  |
|  | ⟳ Activity: UpdateInventory(diff_result) — write to PostgreSQL |  |  |  |  |
|  | [7] → Activity: UpdateDependencyGraph(agents, tools, datasources) — Cypher MERGE |  | ────────▶ Activity: UpdateDependencyGraph(agents, tools, datasources) — Cypher MERGE |  |  |
|  | [8] → Publish: discovery.scan_complete {new:5, changed:2, deleted:1} [→|] |  |  | ─ ─ ─ ▶ Publish: discovery.scan_complete {new:5, changed:2, deleted:1} [→|] |  |
|  |  |  |  | [9] → Consume scan_complete — recalculate risk scores for changed agents | ────────▶ Consume scan_complete — recalculate risk scores for changed agents |
|  |  |  | ────────▶ BFS traversal: recalculate blast radius for changed agents |  | [10] ← BFS traversal: recalculate blast radius for changed agents |
|  |  |  |  | ─ ─ ─ ▶ Publish: risk_score.updated events for each changed agent [→|] | [11] ← Publish: risk_score.updated events for each changed agent [→|] |
| 📝 Scan duration: <2hr for 50 agents (v1.0 target). Temporal handles retries on connector timeout. Each activity has its own retry policy. |  |  |  |  |  |
| ── Connector failure during scan ── | ── Connector failure during scan ── | ── Connector failure during scan ── | ── Connector failure during scan ── | ── Connector failure during scan ── | ── Connector failure during scan ── |
|  | [14] → Activity: connector.discover() [retry attempt 2 after 30s backoff] | ────────▶ Activity: connector.discover() [retry attempt 2 after 30s backoff] |  |  |  |
|  | ──▷ Timeout / Error | Timeout / Error ◁── |  |  |  |
|  | ⟳ Activity fails after 3 retries — Temporal marks activity FAILED |  |  |  |  |
|  | [17] → Publish: discovery.connector_failed {connector_id, error} [→|] |  |  | ─ ─ ─ ▶ Publish: discovery.connector_failed {connector_id, error} [→|] |  |
| ⟳ Workflow continues with other connectors; partial scan result returned |  |  |  |  |  |
| Source Service
(any Pinaka svc) | Kafka | Audit Service | Vault (signing key) | Iceberg / S3 | OpenSearch |
| --- | --- | --- | --- | --- | --- |
| [1] → Publish: audit_event{event_type, tenant_id, agent_id, metadata} [→|] | ─ ─ ─ ▶ Publish: audit_event{event_type, tenant_id, agent_id, metadata} [→|] |  |  |  |  |
|  | [2] → Consume event (exactly-once semantics via Kafka transactions) | ────────▶ Consume event (exactly-once semantics via Kafka transactions) |  |  |  |
|  |  | ⟳ Assign event_id (UUID v7 — time-sortable) |  |  |  |
|  |  | [4] → Fetch tenant signing key (cached 60s TTL) | ────────▶ Fetch tenant signing key (cached 60s TTL) |  |  |
|  |  | ──▷ Ed25519 private key (short-lived lease) | Ed25519 private key (short-lived lease) ◁── |  |  |
|  |  | ⟳ Compute hash_prev = SHA-256(previous_event_id + previous_signature) |  |  |  |
|  |  | ⟳ Sign: signature = Ed25519(all_fields + hash_prev) |  |  |  |
|  |  | [8] → Append event row to Iceberg table (partitioned by tenant_id + date) |  | ────────▶ Append event row to Iceberg table (partitioned by tenant_id + date) |  |
|  |  | ──▷ Write confirmed (S3 Object Lock applied) |  | Write confirmed (S3 Object Lock applied) ◁── |  |
|  | ────────▶ Commit Kafka offset ONLY after Iceberg write confirmed | [10] ← Commit Kafka offset ONLY after Iceberg write confirmed |  |  |  |
|  |  | [11] → Index event in OpenSearch (async, best-effort for search) [→|] |  |  | ─ ─ ─ ▶ Index event in OpenSearch (async, best-effort for search) [→|] |
| 📝 CRITICAL: Kafka offset is committed ONLY after Iceberg write is confirmed. If Iceberg write fails, event is retried. This guarantees exactly-once audit persistence. |  |  |  |  |  |
| New Admin
(Browser) | API Gateway | Platform Service | Vault | Kafka | Temporal |
| --- | --- | --- | --- | --- | --- |
| [1] → POST /v1/auth/register {email, company, sso_domain, region:'eu-west-1'} | ────────▶ POST /v1/auth/register {email, company, sso_domain, region:'eu-west-1'} |  |  |  |  |
|  | [2] → CreateTenant(email, company, region) [REST] | ────────▶ CreateTenant(email, company, region) [REST] |  |  |  |
|  |  | ⟳ Validate: email domain; region selection; plan assignment |  |  |  |
|  |  | [4] → CreateTenantEncryptionKey — generate Ed25519 keypair for AIT signing | ────────▶ CreateTenantEncryptionKey — generate Ed25519 keypair for AIT signing |  |  |
|  |  | ──▷ Key ID (stored in Vault; private key never leaves Vault) | Key ID (stored in Vault; private key never leaves Vault) ◁── |  |  |
|  |  | ⟳ Create tenant record in PostgreSQL; create admin user; assign RBAC roles |  |  |  |
|  |  | ⟳ Provision tenant namespaces in Kafka (topic ACLs per tenant_id) |  |  |  |
|  |  | [8] → Publish: tenant.provisioned event [→|] |  | ─ ─ ─ ▶ Publish: tenant.provisioned event [→|] |  |
|  |  |  |  | [9] → Consume tenant.provisioned — trigger ProvisionTenantWorkflow | ────────▶ Consume tenant.provisioned — trigger ProvisionTenantWorkflow |
|  |  | ────────▶ Workflow: create default policies (Platform Baseline L0 + default L1) |  |  | [10] ← Workflow: create default policies (Platform Baseline L0 + default L1) |
|  |  | ────────▶ Workflow: provision compliance frameworks (EU AI Act + NIST AI RMF defaults) |  |  | [11] ← Workflow: provision compliance frameworks (EU AI Act + NIST AI RMF defaults) |
|  |  | ────────▶ Workflow: configure OpenSearch index for new tenant |  |  | [12] ← Workflow: configure OpenSearch index for new tenant |
|  |  | ────────▶ Workflow: configure Neo4j database for new tenant (AuraDB API call) |  |  | [13] ← Workflow: configure Neo4j database for new tenant (AuraDB API call) |
|  | ──▷ Tenant provisioned; JWT issued for admin session | Tenant provisioned; JWT issued for admin session ◁── |  |  |  |
| ──▷ 201 Created {tenant_id, access_token, onboarding_step:'connect_first_connector'} | 201 Created {tenant_id, access_token, onboarding_step:'connect_first_connector'} ◁── |  |  |  |  |
| 📝 Total provisioning time target: <5 min. Region routing: EU admin → eu-west-1 API; all Vault, Kafka, RDS created in eu-west-1 for EU data residency. |  |  |  |  |  |
| Security Analyst
(Console) | API Gateway | Audit Service | AWS Bedrock
(Claude Sonnet) | OpenSearch |
| --- | --- | --- | --- | --- |
| [1] → POST /v1/audit/queries {nl_query: 'Show me all agents that accessed PII last 7 days'} | ────────▶ POST /v1/audit/queries {nl_query: 'Show me all agents that accessed PII last 7 days'} |  |  |  |
|  | [2] → CreateNLQuery(nl_query, tenant_id) [REST mTLS] | ────────▶ CreateNLQuery(nl_query, tenant_id) [REST mTLS] |  |  |
|  |  | ⟳ Extract tenant_id from JWT; scope all operations to this tenant |  |  |
|  |  | [4] → LLM call: translate NL → structured query {data_classifications:['PII'], window:'7d'} [HTTPS] | ────────▶ LLM call: translate NL → structured query {data_classifications:['PII'], window:'7d'} [HTTPS] |  |
| 📝 Privacy: only the NL query text (no customer data) is sent to Bedrock. Bedrock returns a structured query format, never sees actual audit events. |  |  |  |  |
|  |  | ──▷ Structured query: {filter:{data_classification:'PII', timestamp:'>7d_ago'}, limit:100} | Structured query: {filter:{data_classification:'PII', timestamp:'>7d_ago'}, limit:100} ◁── |  |
|  |  | [7] → Search OpenSearch: GET /pinaka-audit-{tenant_id}-* {query:...} [REST] |  | ────────▶ Search OpenSearch: GET /pinaka-audit-{tenant_id}-* {query:...} [REST] |
|  |  | ──▷ []AuditEvent matching criteria (event_ids, summaries, risk_deltas) |  | []AuditEvent matching criteria (event_ids, summaries, risk_deltas) ◁── |
|  |  | [9] → LLM call: summarise results into NL response (event IDs, no raw content) [HTTPS] | ────────▶ LLM call: summarise results into NL response (event IDs, no raw content) [HTTPS] |  |
|  |  | ──▷ NL Summary: '14 agents accessed PII. Top risk: finance-agent (5 accesses, 3 denied)...' | NL Summary: '14 agents accessed PII. Top risk: finance-agent (5 accesses, 3 denied)...' ◁── |  |
|  | ──▷ QueryResult{summary, event_ids[], raw_events[], query_id} | QueryResult{summary, event_ids[], raw_events[], query_id} ◁── |  |  |
| ──▷ 200 OK {summary:'14 agents accessed PII...', events:[...], export_url} | 200 OK {summary:'14 agents accessed PII...', events:[...], export_url} ◁── |  |  |  |
| # Pattern: pinaka.{tenant_id}.{domain}.{event_type}
# DLQ pattern: pinaka.dlq.{consumer_group_id}

# Enforcement domain
pinaka.{tenant_id}.enforcement.agent_actions          # All MCP/API tool calls
pinaka.{tenant_id}.enforcement.policy_decisions       # Policy evaluation results
pinaka.{tenant_id}.enforcement.ait_events             # AIT issuance, validation, revocation

# Discovery domain
pinaka.{tenant_id}.discovery.scan_events              # Scan start, progress, complete, failed
pinaka.{tenant_id}.discovery.agent_lifecycle          # Agent registered, updated, deleted
pinaka.{tenant_id}.discovery.connector_health         # Connector status changes

# Risk domain
pinaka.{tenant_id}.risk.score_updates                 # Risk score changes per agent
pinaka.{tenant_id}.risk.investigation_findings        # Anomaly detection results

# HITL domain
pinaka.{tenant_id}.hitl.requests                      # New HITL approval requests
pinaka.{tenant_id}.hitl.responses                     # Human approve/deny/timeout responses

# Compliance domain
pinaka.{tenant_id}.compliance.evidence_events         # Events tagged with regulatory requirements
pinaka.{tenant_id}.compliance.report_jobs             # Report generation requests

# Platform domain (no tenant_id — system-wide)
pinaka.platform.tenant_lifecycle                      # Tenant provisioned/suspended/deleted
pinaka.platform.connector_registry                   # Connector registered/updated

# DLQ topics (no tenant_id — monitored by ops)
pinaka.dlq.audit-consumer                            # Failed audit writes
pinaka.dlq.notification-consumer                     # Failed notifications
pinaka.dlq.aispm-consumer                            # Failed risk score updates |
| --- |
| Topic Pattern | Partitions | Replication Factor | Retention | Consumer Groups | Notes |
| --- | --- | --- | --- | --- | --- |
| enforcement.agent_actions | 24 | 3 (all AZs) | 7 days | audit-consumer, investigation-consumer | Partitioned by agent_id — ordered per agent |
| enforcement.policy_decisions | 24 | 3 | 7 days | audit-consumer, hitl-consumer, risk-consumer | Partitioned by agent_id |
| discovery.agent_lifecycle | 12 | 3 | 30 days | aispm-consumer, compliance-consumer, audit-consumer | Partitioned by tenant_id |
| risk.score_updates | 12 | 3 | 7 days | investigation-consumer, notification-consumer, audit-consumer | Partitioned by agent_id |
| hitl.requests | 12 | 3 | 7 days | notification-consumer, audit-consumer | Partitioned by tenant_id |
| hitl.responses | 12 | 3 | 7 days | mcp-gateway-consumer, audit-consumer | Partitioned by hitl_request_id — must be same partition as request |
| compliance.evidence_events | 12 | 3 | 90 days | compliance-consumer | Compacted — retain latest compliance status per control_id |
| platform.tenant_lifecycle | 4 | 3 | Forever | all-service-consumers | Low volume; all services subscribe for provisioning signals |
| DLQ topics (all) | 6 | 3 | 14 days | ops-dlq-consumer (manual replay) | Ops team monitors; replay via replay API after fix |
| // Schema: pinaka.enforcement.AgentActionEvent (Avro)
{
  "type": "record",
  "name": "AgentActionEvent",
  "namespace": "pinaka.enforcement",
  "fields": [
    {"name": "event_id",          "type": "string"},  // UUID v7
    {"name": "schema_version",    "type": "int",   "default": 1},
    {"name": "tenant_id",         "type": "string"},
    {"name": "agent_id",          "type": "string"},
    {"name": "ait_id",            "type": "string"},
    {"name": "tool_name",         "type": "string"},
    {"name": "destination",       "type": {"type":"enum","name":"Destination",
                                  "symbols":["INTERNAL","EXTERNAL","MCP_SERVER","AGENT"]}},
    {"name": "data_classifications","type":{"type":"array","items":"string"}},
    {"name": "action_metadata",   "type": {"type":"map","values":"string"}},
    {"name": "timestamp_ns",      "type": "long"},   // Unix nanoseconds
    {"name": "policy_decision",   "type": {"type":"enum","name":"Decision",
                                  "symbols":["ALLOW","DENY","ESCALATE"]}},
    {"name": "decision_id",       "type": "string"},
    {"name": "policy_id",         "type": ["null","string"], "default": null},
    {"name": "risk_delta",        "type": "int",   "default": 0},
    {"name": "enforcement_mode",  "type": {"type":"enum","name":"EnforcementMode",
                                  "symbols":["INLINE","SIDECAR","API_HOOK","OUT_OF_BAND"]}}
  ]
} |
| --- |
| Consumer Group | Service | Topics Consumed | Offset Strategy | DLQ Policy |
| --- | --- | --- | --- | --- |
| audit-consumer | audit-service | All *.enforcement.* + *.discovery.* + *.hitl.* + *.risk.* | Commit offset ONLY after successful Iceberg write (Kafka transactions) | All failures → pinaka.dlq.audit-consumer; ops alert on >0 DLQ messages |
| aispm-consumer | aispm-engine | discovery.agent_lifecycle, enforcement.policy_decisions | Auto-commit after successful risk score write to TimescaleDB | 3 retries with backoff; then DLQ |
| investigation-consumer | investigation-engine | enforcement.agent_actions, risk.score_updates | Auto-commit after behavioural model update | 3 retries; DLQ |
| notification-consumer | notification-service | hitl.requests, risk.score_updates, platform.* | Auto-commit after notification delivery confirmation OR DLQ write | 5 retries; DLQ; customer notified of delivery failure |
| hitl-consumer | hitl-service | enforcement.policy_decisions (ESCALATE filter) | Auto-commit after HITL request created in PostgreSQL | 3 retries; DLQ |
| compliance-consumer | compliance-engine | compliance.evidence_events, discovery.agent_lifecycle | Auto-commit after evidence record written | 3 retries; DLQ |
| mcp-gateway-consumer | mcp-gateway | hitl.responses | Auto-commit after HITL callback sent to waiting request | Immediate retry on failure; fail to auto-DENY after 3 failures |
| Convention | All tables include: id (UUID v7 primary key), tenant_id (partition key with RLS), created_at, updated_at, deleted_at (soft delete). All timestamps are UTC. Indexes named idx_{table}_{columns}. |
| --- | --- |
| CREATE TABLE tenants (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name              VARCHAR(255) NOT NULL,
  plan_tier         VARCHAR(50)  NOT NULL CHECK (plan_tier IN ('STARTER','PROFESSIONAL','ENTERPRISE','ENTERPRISE_PLUS')),
  region            VARCHAR(50)  NOT NULL,  -- us-east-1 | eu-west-1 | ap-southeast-1
  vault_key_id      VARCHAR(255) NOT NULL,  -- Reference to tenant Ed25519 key in Vault
  sso_domain        VARCHAR(255),           -- e.g., company.okta.com
  failsafe_mode     VARCHAR(20)  NOT NULL DEFAULT 'DENY_ALL',
  enforcement_rps   INTEGER      NOT NULL DEFAULT 1000,
  feature_flags     JSONB        NOT NULL DEFAULT '{}',
  status            VARCHAR(20)  NOT NULL DEFAULT 'ACTIVE', -- ACTIVE | SUSPENDED | DELETED
  created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  deleted_at        TIMESTAMPTZ
);
CREATE UNIQUE INDEX idx_tenants_name ON tenants(name) WHERE deleted_at IS NULL; |
| --- |
| CREATE TABLE agents (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID NOT NULL REFERENCES tenants(id),
  name              VARCHAR(255) NOT NULL,
  agent_type        VARCHAR(100) NOT NULL, -- LangChain/OpenAI | AWS Bedrock Agent | etc.
  framework         VARCHAR(100) NOT NULL,
  owner_user_id     UUID NOT NULL,
  connector_id      UUID REFERENCES connectors(id),
  fingerprint       VARCHAR(64)  NOT NULL, -- SHA-256 hex of code+config+env hash
  risk_score        INTEGER      NOT NULL DEFAULT 0 CHECK (risk_score BETWEEN 0 AND 100),
  risk_tier         VARCHAR(20)  NOT NULL DEFAULT 'MINIMAL',
  autonomy_level    INTEGER      NOT NULL DEFAULT 0 CHECK (autonomy_level BETWEEN 0 AND 5),
  status            VARCHAR(20)  NOT NULL DEFAULT 'REGISTERED', -- REGISTERED|ACTIVE|QUARANTINE|SUSPENDED|DELETED
  last_active_at    TIMESTAMPTZ,
  last_scan_at      TIMESTAMPTZ,
  created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  deleted_at        TIMESTAMPTZ
);
CREATE INDEX idx_agents_tenant      ON agents(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_agents_risk_score  ON agents(tenant_id, risk_score DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_agents_status      ON agents(tenant_id, status) WHERE deleted_at IS NULL;
-- Row Level Security (applied to all service database roles)
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
CREATE POLICY agents_tenant_isolation ON agents
  USING (tenant_id = current_setting('app.tenant_id')::UUID); |
| --- |
| CREATE TABLE agent_identity_tokens (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID NOT NULL REFERENCES tenants(id),
  agent_id          UUID NOT NULL REFERENCES agents(id),
  ait_hash          VARCHAR(64)  NOT NULL UNIQUE, -- SHA-256 of the AIT (never store plaintext)
  fingerprint       VARCHAR(64)  NOT NULL,  -- Agent fingerprint at time of issuance
  granted_tools     TEXT[]       NOT NULL DEFAULT '{}',
  issued_by         UUID         NOT NULL,  -- user_id who registered the agent
  issued_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  expires_at        TIMESTAMPTZ  NOT NULL,
  revoked_at        TIMESTAMPTZ,
  revoke_reason     VARCHAR(255),
  last_used_at      TIMESTAMPTZ
);
CREATE INDEX idx_ait_agent_id     ON agent_identity_tokens(agent_id) WHERE revoked_at IS NULL;
CREATE INDEX idx_ait_expires      ON agent_identity_tokens(expires_at) WHERE revoked_at IS NULL;
ALTER TABLE agent_identity_tokens ENABLE ROW LEVEL SECURITY;
CREATE POLICY ait_tenant_isolation ON agent_identity_tokens
  USING (tenant_id = current_setting('app.tenant_id')::UUID); |
| --- |
| CREATE TABLE policies (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID,           -- NULL for L0 (Platform) policies; tenant_id for L1–L3
  policy_level      INTEGER NOT NULL CHECK (policy_level IN (0,1,2,3)),
  name              VARCHAR(255) NOT NULL,
  description       TEXT,
  scope_type        VARCHAR(20)  NOT NULL, -- PLATFORM | TENANT | AGENT_GROUP | AGENT
  scope_id          UUID,                 -- NULL for TENANT scope; agent/group ID otherwise
  rego_source       TEXT         NOT NULL, -- OPA Rego policy source (UTF-8)
  rego_compiled     BYTEA,                -- Compiled OPA bundle (cached)
  action_on_match   VARCHAR(20)  NOT NULL CHECK (action_on_match IN ('ALLOW','DENY','ESCALATE')),
  hitl_tier         INTEGER,             -- Required if action=ESCALATE: 1|2|3|4
  severity          VARCHAR(20)  NOT NULL DEFAULT 'MEDIUM',
  notification_targets JSONB     NOT NULL DEFAULT '[]',
  enabled           BOOLEAN      NOT NULL DEFAULT TRUE,
  version           INTEGER      NOT NULL DEFAULT 1,
  approved_by       UUID,
  shadow_mode_until TIMESTAMPTZ,         -- If set: log only, no enforcement until this time
  created_by        UUID         NOT NULL,
  created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  deleted_at        TIMESTAMPTZ
);
CREATE INDEX idx_policies_tenant_enabled ON policies(tenant_id, enabled) WHERE deleted_at IS NULL;
CREATE INDEX idx_policies_level_scope    ON policies(policy_level, scope_type, scope_id); |
| --- |
| CREATE TABLE hitl_requests (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID NOT NULL REFERENCES tenants(id),
  agent_id          UUID NOT NULL REFERENCES agents(id),
  decision_id       UUID NOT NULL,  -- From policy engine decision
  action_summary    TEXT NOT NULL,
  action_metadata   JSONB NOT NULL DEFAULT '{}',
  policy_id         UUID REFERENCES policies(id),
  hitl_tier         INTEGER NOT NULL CHECK (hitl_tier IN (1,2,3,4)),
  status            VARCHAR(20) NOT NULL DEFAULT 'PENDING',
  -- PENDING | APPROVED | DENIED | TIMED_OUT | AUTO_DENIED
  required_approvers INTEGER NOT NULL DEFAULT 1,  -- For Tier 3 multi-party
  approvals_received INTEGER NOT NULL DEFAULT 0,
  timeout_at        TIMESTAMPTZ NOT NULL,
  resolved_at       TIMESTAMPTZ,
  resolved_by       UUID,
  resolution_notes  TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_hitl_tenant_status ON hitl_requests(tenant_id, status) WHERE status='PENDING';
CREATE INDEX idx_hitl_timeout       ON hitl_requests(timeout_at) WHERE status='PENDING'; |
| --- |
| CREATE TABLE connectors (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID NOT NULL REFERENCES tenants(id),
  name              VARCHAR(255) NOT NULL,
  connector_type    VARCHAR(100) NOT NULL,  -- aws-bedrock | azure-openai | openai | anthropic | mcp | etc.
  config            JSONB NOT NULL DEFAULT '{}',  -- Non-sensitive config (region, endpoint, etc.)
  vault_secret_path VARCHAR(512) NOT NULL,         -- Path in Vault for credentials
  status            VARCHAR(20)  NOT NULL DEFAULT 'HEALTHY',
  last_health_check TIMESTAMPTZ,
  last_sync_at      TIMESTAMPTZ,
  sync_frequency_min INTEGER     NOT NULL DEFAULT 60,
  created_by        UUID NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at        TIMESTAMPTZ
); |
| --- |
| -- TimescaleDB hypertable for time-series risk scores
CREATE TABLE agent_risk_scores (
  time              TIMESTAMPTZ     NOT NULL,
  tenant_id         UUID            NOT NULL,
  agent_id          UUID            NOT NULL,
  composite_score   INTEGER         NOT NULL,
  dim_permission    INTEGER         NOT NULL,  -- 0-100 for each dimension
  dim_data_access   INTEGER         NOT NULL,
  dim_blast_radius  INTEGER         NOT NULL,
  dim_autonomy      INTEGER         NOT NULL,
  dim_compliance    INTEGER         NOT NULL,
  trigger_event_id  UUID,                      -- Audit event that caused this recalculation
  trigger_type      VARCHAR(50)                -- POLICY_VIOLATION | DISCOVERY_SCAN | INVESTIGATION_FINDING
);
SELECT create_hypertable('agent_risk_scores', 'time');
SELECT add_dimension('agent_risk_scores', 'tenant_id', number_partitions => 4);
-- Compress chunks older than 7 days (up to 95% compression)
SELECT add_compression_policy('agent_risk_scores', INTERVAL '7 days');
-- Retention: keep 3 years
SELECT add_retention_policy('agent_risk_scores', INTERVAL '3 years'); |
| --- |
| // Node types in the Pinaka dependency graph
CREATE CONSTRAINT agent_id_unique     FOR (a:Agent)      REQUIRE a.agent_id IS UNIQUE;
CREATE CONSTRAINT tool_id_unique      FOR (t:Tool)       REQUIRE t.tool_id IS UNIQUE;
CREATE CONSTRAINT datasource_unique   FOR (d:DataSource) REQUIRE d.source_id IS UNIQUE;
CREATE CONSTRAINT mcp_server_unique   FOR (m:MCPServer)  REQUIRE m.server_id IS UNIQUE;

// Agent node: (:Agent {agent_id, tenant_id, name, risk_score, status})
// Tool node:  (:Tool  {tool_id, tenant_id, name, sensitivity_tier, is_external})
// DataSource: (:DataSource {source_id, tenant_id, name, data_classification[]})
// MCPServer:  (:MCPServer  {server_id, tenant_id, url, is_approved})

// Relationships:
// (:Agent)-[:CAN_CALL {granted_at, permissions[]}]->(:Tool)
// (:Agent)-[:READS    {access_type:'READ|WRITE|EXEC'}]->(:DataSource)
// (:Agent)-[:CONNECTS_TO {last_seen}]->(:MCPServer)
// (:Agent)-[:CALLS_AGENT {call_type:'sync|async'}]->(:Agent)
// (:MCPServer)-[:EXPOSES {schema_version}]->(:Tool)

// Blast radius query: find all nodes reachable from a given agent
MATCH path = (a:Agent {agent_id: $agent_id})-[*1..5]->(n)
WHERE a.tenant_id = $tenant_id
RETURN n, length(path) as depth, labels(n) as node_type
ORDER BY depth ASC
LIMIT 100; |
| --- |
| # Kong declarative config (deck format)
services:
  - name: platform-service
    url: grpc://platform-service.pinaka-platform.svc.cluster.local:50051
    protocol: grpc

  - name: policy-engine-rest
    url: http://policy-engine.pinaka-core.svc.cluster.local:8080
,
  - name: discovery-engine
    url: http://discovery-engine.pinaka-core.svc.cluster.local:8080

routes:
  # Policy API
  - name: policies-route
    service: policy-engine-rest
    paths: [/v1/policies]
    methods: [GET, POST, PUT, DELETE]
    plugins: [jwt-auth, rate-limit-professional, tenant-context, request-id]

  # Audit API (read-only token allowed)
  - name: audit-read-route
    service: audit-service-rest
    paths: [/v1/audit]
    methods: [GET, POST]
    plugins: [jwt-auth-or-read-only-key, rate-limit-professional, tenant-context, request-id]

  # Enforcement (MCP Gateway handles directly — not routed through Kong)
  # HITL API
  - name: hitl-route
    service: hitl-service
    paths: [/v1/hitl]
    methods: [GET, POST]
    plugins: [jwt-auth, mfa-for-approve, rate-limit-professional, tenant-context, audit-log] |
| --- |
| Order | Middleware | Applied To | Purpose |
| --- | --- | --- | --- |
| 1 | WAF (AWS WAF) | All routes | OWASP CRS; SQL injection; XSS; rate limit by IP |
| 2 | Request ID | All routes | Generate X-Request-ID UUID v7; propagate to all services as trace context |
| 3 | TLS Termination | All routes | TLS 1.3 termination at ALB; Kong receives cleartext internally |
| 4 | JWT Auth | All authenticated routes | Verify RS256 signature; check expiry; extract tenant_id and role claims |
| 5 | API Key Auth | Service-to-service routes | Verify HMAC API key; lookup tenant_id from key hash |
| 6 | MFA Check | Admin routes + HITL approve | Verify TOTP/WebAuthn challenge completed in last 5 minutes |
| 7 | RBAC Check | All routes | gRPC call to platform-service.CheckRBAC; fail-fast before business logic |
| 8 | Tenant Context Injection | All authenticated routes | Inject X-Tenant-ID header; set app.tenant_id PostgreSQL session variable |
| 9 | Rate Limit | All routes | Token bucket per API key; tier-based limits; Redis counters |
| 10 | Request Logging | All routes | Log method, path, status, latency, tenant_id, request_id to Datadog |
| 11 | Response Compression | All REST responses | Gzip responses >1KB; Content-Encoding: gzip |
| 12 | CORS | Browser routes only | Strict allowlist; no wildcard; preflight cache 1 hour |
| // All Pinaka API errors follow RFC 7807 Problem Details format
HTTP/1.1 403 Forbidden
Content-Type: application/problem+json
{
  "type":     "https://docs.pinaka.ai/errors/policy-violation",
  "title":    "Policy Violation",
  "status":   403,
  "detail":   "Action denied by policy: External PII export blocked",
  "instance": "/v1/agents/agt_abc123/actions/tool-call",
  "extensions": {
    "decision_id": "dec_xyz789",
    "policy_id":   "pol_fin_no_pii_export",
    "request_id":  "req_7f3a9c8b",
    "timestamp":   "2026-04-01T10:30:00.123456789Z"
  }
}

// Standard error codes:
// 400 Bad Request    → type: /errors/invalid-request
// 401 Unauthorized   → type: /errors/authentication-required
// 403 Forbidden      → type: /errors/policy-violation | /errors/rbac-denied
// 404 Not Found      → type: /errors/resource-not-found
// 409 Conflict       → type: /errors/conflict
// 429 Too Many Req.  → type: /errors/rate-limit-exceeded (+ Retry-After header)
// 500 Internal Error → type: /errors/internal (sanitised — no stack traces) |
| --- |
| Namespace | Services | Network Policy | Purpose |
| --- | --- | --- | --- |
| pinaka-gateway | api-gateway (Kong), mcp-gateway | Ingress from ALB (internet); egress to pinaka-core, pinaka-platform | Internet-facing entry points; WAF protected |
| pinaka-core | policy-engine, discovery-engine, aispm-engine, temporal-workers | Ingress from pinaka-gateway, pinaka-platform; no internet egress | Core business logic; policy evaluation; discovery |
| pinaka-data | audit-service, compliance-engine, investigation-engine | Ingress from pinaka-core, pinaka-platform; egress to AWS services | Data persistence and analytics services |
| pinaka-platform | platform-service, hitl-service, notification-service | Ingress from all; egress to external APIs (Slack, PagerDuty) | Auth, HITL, notifications, multitenancy |
| pinaka-infra | MSK endpoints, ElastiCache, PgBouncer sidecars | Ingress from pinaka-core/data/platform only; no internet | Infrastructure VPC-private endpoints |
| pinaka-ops | Datadog DaemonSet, Falco, ArgoCD, Temporal UI | VPN-gated ops access only | Observability and deployment tooling |
| Service | CPU Req | CPU Limit | Mem Req | Mem Limit | Min/Max Replicas | HPA Trigger |
| --- | --- | --- | --- | --- | --- | --- |
| api-gateway (Kong) | 500m | 2000m | 512Mi | 2Gi | 3/20 | CPU >70% OR RPS >500 |
| mcp-gateway | 500m | 4000m | 512Mi | 4Gi | 3/50 | Connections >200/pod OR CPU >60% |
| policy-engine | 250m | 2000m | 512Mi | 2Gi | 3/30 | Enforcement RPS >200/pod OR CPU >70% |
| discovery-engine | 250m | 1000m | 512Mi | 2Gi | 2/10 | CPU >70% |
| aispm-engine | 500m | 2000m | 1Gi | 4Gi | 2/8 | CPU >70% |
| audit-service | 250m | 1000m | 512Mi | 1Gi | 3/15 | Kafka consumer lag >5000 |
| investigation-engine | 500m | 4000m | 1Gi | 8Gi | 2/6 | CPU >60% |
| platform-service | 250m | 1000m | 512Mi | 1Gi | 3/15 | CPU >70% |
| hitl-service | 100m | 500m | 256Mi | 512Mi | 2/8 | CPU >70% |
| notification-service | 100m | 500m | 256Mi | 512Mi | 2/8 | Kafka lag >1000 |
| Cache Layer | Key Pattern | TTL | Invalidation Trigger |
| --- | --- | --- | --- |
| Policy Bundle | policy_bundle:{tenant_id}:v{version_hash} | 60s | Explicit DEL on any policy change for tenant |
| AIT Validation | ait_valid:{ait_hash} | 300s | Explicit DEL on AIT revocation |
| AIT Revocation List | ait_revoked (Redis Set) | No TTL — cleanup at AIT.expires_at | SADD on revocation; cleanup job at expiry |
| Tenant Context | tenant_ctx:{tenant_id} | 120s | Explicit DEL on tenant config change |
| Rate Limit Counters | rl:{api_key_hash}:{window_start} | Window size + 10s grace | Auto-expire |
| HITL Session State | hitl:{request_id} | HITL timeout + 60s | Explicit DEL on resolution |
| Agent Risk Score (hot) | risk_score:{agent_id} | 300s | SET on every risk score recalculation |
| NL Query Translation | nlq:{sha256(nl_query)} | 3600s | No explicit invalidation |
| Workflow | Trigger | Key Activities | Timeout | On Failure |
| --- | --- | --- | --- | --- |
| DiscoveryScanWorkflow | Cron (60min) OR API | FetchCredentials→ConnectorDiscover(parallel)→DiffInventory→UpdateInventory→UpdateGraph→Publish | 2hr | Partial success; other connectors continue; scan_partial event |
| TenantProvisioningWorkflow | Kafka: tenant.provisioned | CreateDefaultPolicies→CreateComplianceDefaults→ProvisionOpenSearch→ProvisionNeo4j→SendWelcomeEmail | 30min | Compensating transactions; admin alerted |
| ComplianceReportWorkflow | API trigger | FetchAuditEvents→FetchPolicyData→MapToFramework→GenerateReport→StoreReport→NotifyAdmin | 30min | Retry up to 2x; report marked FAILED; admin notified |
| AITExpiryWorkflow | Cron (hourly) | ScanExpiringAITs→NotifyOwners→AutoRevokeExpired→PublishRevocationEvents | 1hr | Notify failures non-blocking; revocation proceeds |
| RemediationWorkflow (v1.5) | API trigger | ValidateRemediation→CreateChangeRecord→ExecuteRemediation→VerifyRemediation→CloseChangeRecord | 4hr | Compensation: undo partial changes |
| Task Queue | Workers | Workflow Types | Priority | Notes |
| --- | --- | --- | --- | --- |
| pinaka-discovery | discovery-engine pods (3–10) | DiscoveryScanWorkflow | Normal | Connector scans can run in parallel per tenant |
| pinaka-compliance | compliance-engine pods (2–6) | ComplianceReportWorkflow | Normal | Report generation is CPU-heavy; isolated queue |
| pinaka-platform | platform-service pods (3–15) | TenantProvisioningWorkflow, AITExpiryWorkflow | High | Provisioning must complete fast for new customers |
| pinaka-remediation | dedicated worker pods (2–4) [v1.5] | RemediationWorkflow | High | Isolated — remediation touches production systems |
| Tool | Version | Purpose |
| --- | --- | --- |
| Docker Desktop | 24+ | Container runtime |
| Go | 1.22+ | Build Go services |
| Python | 3.12+ | Build Python services |
| Node.js | 20+ | Build console-ui |
| kubectl + Helm | 1.30+ / 3.x | EKS interaction |
| OPA CLI | 0.65+ | Test and lint Rego policies |
| Temporal CLI | 1.x | Inspect local workflows |
| k6 | latest | Load testing |
| Vault CLI | 1.17+ | Local Vault interaction |
| pinaka-dev CLI | latest | Seed data, test events (internal tool: go install ./tools/pinaka-dev) |
| # Start all infrastructure in one command:
docker compose up -d  # postgres, redis, kafka, vault, temporal, neo4j, opensearch

# First-time setup:
bash scripts/dev-setup.sh
# → runs DB migrations (Flyway)
# → seeds Vault with dev secrets
# → creates dev tenant + admin user
# → seeds 10 mock agents with varying risk profiles
# → starts policy-engine, audit-service, mcp-gateway

# Verify full stack working:
go run ./tools/pinaka-dev health-check
# → all services: OK

# Issue AIT for local test:
TOKEN=$(go run ./tools/pinaka-dev issue-ait --agent-id=dev-agent-001)

# Test enforcement path end-to-end:
curl -X POST http://localhost:8082/mcp/tool-call \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"tool":"spreadsheet-read","params":{"file_id":"FIN_Q1"}}'
# Expected: {"decision":"ALLOW","decision_id":"dec_..."} in <500ms |
| --- |
| Pattern | Applied To | Fail Behaviour |
| --- | --- | --- |
| Circuit Breaker | All external calls (connector APIs, LLM calls, external webhooks) | Open → return cached result or DENY (Fail Secure); log circuit_open event; PagerDuty alert |
| Retry with Jitter | Kafka produce, webhook delivery, connector API calls | 3 retries; base 1s; max 30s; ±20% jitter; exhausted → DLQ |
| Dead Letter Queue | Kafka consumer failures | DLQ per consumer group; ops alert; manual replay after fix |
| Bulkhead | Policy Engine evaluation — tenant workload isolation | Dedicated thread pool per tenant tier; Enterprise tenants isolated from noisy neighbours |
| Timeout + Fail Secure | gRPC enforcement calls | 10ms deadline; timeout → DENY immediately (never hang waiting) |
| Graceful Degradation | Discovery Engine connector failure | Partial scan accepted; stale inventory marked; rescan triggered on recovery |
| Health Check — Liveness | /healthz per pod | Returns 200 if process alive; fail → pod restart within 30s |
| Health Check — Readiness | /readyz per pod | Checks DB, Kafka, OPA bundle; fail → removed from load balancer |
| // Every service main.go must call initOTel() before starting
func main() {
    shutdown := otel.InitOTel(context.Background(), 'policy-engine')
    defer shutdown()
    // ... rest of startup
}

// Enforcement path: ALWAYS sample (100%)
// Background jobs: 1% sample
// Every span MUST include: tenant_id, agent_id (if applicable), decision |
| --- |
| Metric | Type | Alert? | SLO Role |
| --- | --- | --- | --- |
| pinaka_enforcement_duration_seconds | Histogram (p50/p95/p99) | Yes >500ms p99 | Primary enforcement SLO indicator |
| pinaka_policy_decisions_total | Counter {decision: ALLOW/DENY/ESCALATE} | Spike alert on DENY rate | Business health metric |
| pinaka_kafka_publish_failures_total | Counter {topic} | Yes — any failure | Data integrity indicator |
| pinaka_hitl_pending_gauge | Gauge {tenant_id, tier} | Yes >10 for >5min | HITL backlog — human safety |
| pinaka_agent_risk_score | Gauge {agent_id, tier} | Yes — CRITICAL tier | Risk monitoring |
| pinaka_circuit_breaker_state | Gauge {service, target} | Yes — open state | Dependency health |
| pinaka_dlq_depth_gauge | Gauge {consumer_group} | Yes — any >0 | Data pipeline health |
| pinaka_api_request_duration_seconds | Histogram {route, method, status} | Yes >200ms p99 | API SLO |
| ⚠ | All CRITICAL items (H1–H3) must be resolved before Sprint 1 Day 5. HIGH items (H4–H7) before Sprint 3. |
| --- | --- |
| # | Item | Services Affected | Recommendation | Deadline |
| --- | --- | --- | --- | --- |
| H1 | gRPC vs REST for policy management API (not enforcement) | api-gateway, policy-engine | REST for CRUD — simpler, easier curl testing; gRPC enforcement path unchanged | Sprint 1 Day 1 |
| H2 | Kafka: exactly-once vs at-least-once per consumer | All Kafka consumers | Exactly-once (transactions) for audit only; at-least-once + idempotency elsewhere | Sprint 1 Day 3 |
| H3 | Avro Schema Registry: Glue vs Confluent Schema Registry | All Kafka producers/consumers | AWS Glue (managed, no extra service); see Section 29.2 for design | Sprint 1 Day 3 |
| H4 | HITL waiting mechanism: long-poll vs WebSocket | mcp-gateway, hitl-service | Long-poll v1.0 (simpler); WebSocket v1.5 | Sprint 2 |
| H5 | OPA Rego: single file vs module system | policy-engine | Module system from Day 1 (see Section 17.2 for design) | Sprint 1 Day 5 |
| H6 | Investigation Engine ML: online vs batch retrain | investigation-engine | Hybrid: online EMA for baselines; weekly Temporal batch retrain (see Section 20) | Sprint 2 |
| H7 | Neo4j: AuraDB vs self-hosted for dev/staging | aispm-engine, investigation-engine | Docker Compose Neo4j for local; AuraDB Professional staging; AuraDB Enterprise prod | Sprint 1 |
| Term | Definition |
| --- | --- |
| AIT | Agent Identity Token — Ed25519-signed JWT issued by Pinaka, uniquely identifying and authenticating an AI agent. Contains granted_tools, fingerprint, expiry. |
| ARM | Agentic Risk Map — D3.js force-directed graph showing all agents, tools, data sources, and their relationships + risk scores. |
| Blast Radius | Maximum scope of impact if an agent is compromised: how many downstream systems, users, and data sources can be affected. |
| Bundle (OPA) | Compiled, serialised set of Rego policies for a tenant. Stored in Redis (60s TTL). Sub-10ms evaluation from cache. |
| Circuit Breaker | Resilience pattern: stops calling a failing service after threshold exceeded. Pinaka uses gobreaker in Go; returns DENY on open state (Fail Secure). |
| Consumer Group | Kafka mechanism: multiple consumer instances sharing topic partitions. All Pinaka consumers named by service. |
| CQRS | Command Query Responsibility Segregation — write operations use PostgreSQL; read-heavy operations use Redis cache + OpenSearch. |
| DLQ | Dead Letter Queue — Kafka topic receiving messages after all retry attempts exhausted. Ops team monitors; replay after fix. |
| Exactly-Once | Kafka transaction mode: message processed AND offset committed atomically. Pinaka uses this only for audit writes. |
| Hypertable | TimescaleDB auto-partitioned PostgreSQL table. Pinaka uses it for risk_scores — partitioned by time + tenant_id. |
| IRSA | IAM Roles for Service Accounts — AWS mechanism for K8s pods to assume IAM roles. No long-lived credentials in pods. |
| Outbox Pattern | Write to DB + outbox table in same transaction; relay publishes outbox events to Kafka. Guarantees no event loss on service crash. |
| PDB | PodDisruptionBudget — Kubernetes: limits pods that can be unavailable during disruption. Every Pinaka service has one. |
| PKCE | Proof Key for Code Exchange — OAuth 2.1 extension preventing auth code interception. Used in Pinaka's SSO OIDC flow. |
| RLS | Row-Level Security — PostgreSQL feature transparently filtering rows by tenant_id. Pinaka's primary DB tenant isolation. |
| Saga | Distributed transaction pattern using compensating actions. Pinaka uses choreography-based sagas via Kafka events. |
| Sync Wave | ArgoCD concept: deploy resources in ordered waves. Pinaka uses waves 0–4 to ensure dependency order. |
| Transactional Outbox | Pattern: write business data + event to outbox in one DB transaction; separate relay publishes events. Guarantees consistency. |
| UUID v7 | Time-sortable UUID format. Pinaka uses for all primary keys and event IDs for efficient time-range queries without extra timestamp index. |
| VirtualService | Istio resource defining traffic routing, retry, and timeout rules per service route. Every Pinaka service has one. |
| WORM | Write Once Read Many — S3 Object Lock on audit log bucket. Prevents deletion even by AWS root account. |
| Why this matters | The MCP Gateway is Pinaka's most performance-critical and technically complex service. Every MCP tool call in the enterprise passes through it. Engineers building it need to understand exactly how it intercepts, inspects, and enforces — not just that it does. |
| --- | --- |
| Deployment Mode | Interception Mechanism | How It Works | Latency Added | When To Use |
| --- | --- | --- | --- | --- |
| Inline Transparent Proxy (Default) | iptables REDIRECT rules injected via Init Container | MCP Gateway container runs alongside each agent pod. Init Container adds iptables rules: all outbound port 8080 (MCP) redirected to Gateway's local port 15000. Agent sees no change in code. | ~20–40ms (local loopback) | New deployments on EKS where Pinaka can inject Init Containers |
| Kubernetes Sidecar | Istio-style sidecar injection via MutatingWebhookConfiguration | Pinaka webhook server watches pod creation. On pods with annotation pinaka.io/inject: 'true', injects mcp-gateway sidecar container. Sidecar shares network namespace with agent pod. | ~10–30ms (shared netns) | K8s-native agents; compatible with existing Istio deployments |
| Standalone Gateway | Agent configures MCP server URL to point at Pinaka Gateway endpoint | Agent code sets MCP_SERVER_URL=https://mcp-gateway.pinaka.company.com. No injection needed. Gateway proxies to actual MCP server. | ~50–100ms (network round-trip) | Non-K8s agents; legacy deployments; cloud function agents |
| API Hook (Lightweight) | Pinaka SDK call before each MCP tool invocation | Agent code imports pinaka-sdk. SDK calls policy decision API before each tool call. No proxy layer. Policy-only enforcement, no response scanning. | ~20ms (API call, cache hit) | Existing agents where sidecar/proxy cannot be deployed; lowest friction |
| Out-of-Band Audit | MCP server logs forwarded to Pinaka via connector | Discovery Engine reads MCP server access logs. No enforcement. Audit and alerting only. Used during transition period. | Zero (no enforcement path) | High-availability systems where any latency is unacceptable; read-only monitoring |
| Stage | Check | Implementation | Max Latency | On Failure |
| --- | --- | --- | --- | --- |
| 1 | AIT Signature Verification | Ed25519 verify using tenant public key (Redis-cached 300s) | <1ms (cache hit); <5ms (Vault fetch) | DENY: invalid_token |
| 2 | AIT Claims Validation | Check: not expired, not revoked (Redis Set SISMEMBER), fingerprint matches | <1ms (Redis O(1)) | DENY: token_revoked | token_expired | fingerprint_mismatch |
| 3 | Tool Authorization Check | Verify AIT granted_tools[] contains requested tool_name | <1ms (in-memory AIT claims) | DENY: tool_not_authorized |
| 4 | Rate Limit Check | Redis INCR per agent+tool per 60s window; compare vs policy limit | <2ms (Redis atomic) | THROTTLE: rate_limit_exceeded |
| 5 | MCP Server Registry Check | Verify target MCP server URL in approved_servers table (Redis-cached 60s) | <1ms (Redis hash) | DENY: unverified_mcp_server |
| 6 | Parameter Inspection (DLP) | Run input parameters through DLP scanner (PII regex + ML classifier) | <5ms (pre-compiled regex); <15ms (ML model) | DENY or REDACT per policy |
| 7 | Injection Detection | Pattern match input for prompt injection signatures (OWASP LLM01 patterns) | <3ms (Aho-Corasick multi-pattern) | DENY: injection_detected |
| 8 | Policy Engine Call | gRPC EvaluateAction with enriched context from stages 1–7 | <10ms (p99 cache hit) | DENY (Fail Secure on timeout) |
| 9 | Forward to MCP Server | Proxy validated request to actual MCP server | Network dependent | Log proxy_error; DENY |
| 10 | Response Scanning | DLP scan on MCP server response before returning to agent | <5ms (streaming scan) | REDACT or BLOCK per policy |
| 11 | Audit Emit | Publish complete event to Kafka (non-blocking) | <1ms (async publish) | Buffer to local store; retry |
| // mcp_gateway/internal/gateway/gateway.go
type Gateway struct {
    aitValidator    *ait.Validator          // Ed25519 + Redis cache
    rateLimit       *ratelimit.Limiter      // Redis token bucket
    dlpScanner      *dlp.Scanner            // PII + injection detection
    policyClient    policy.PolicyEngineClient // gRPC client with circuit breaker
    mcpProxy        *proxy.MCPProxy          // Forward to upstream MCP server
    auditPublisher  *kafka.Producer          // Async audit event publish
    serverRegistry  *registry.ServerRegistry // Approved MCP server cache
}

func (g *Gateway) HandleToolCall(ctx context.Context, req *MCPRequest) (*MCPResponse, error) {
    start := time.Now()
    pipeline := []PipelineStage{
        g.aitValidator.Verify,      // Stage 1-2: AIT
        g.aitValidator.CheckTools,  // Stage 3: Authorization
        g.rateLimit.Check,          // Stage 4: Rate limit
        g.serverRegistry.Verify,   // Stage 5: Server registry
        g.dlpScanner.ScanRequest,  // Stage 6-7: DLP + injection
        g.policyClient.Evaluate,   // Stage 8: Policy decision
    }
    for _, stage := range pipeline {
        if err := stage(ctx, req); err != nil {
            g.auditPublisher.PublishAsync(buildDenyEvent(req, err, time.Since(start)))
            return nil, err // Returns structured error → HTTP 403
        }
    }
    resp, err := g.mcpProxy.Forward(ctx, req)  // Stage 9
    if err != nil { return nil, err }
    resp, err = g.dlpScanner.ScanResponse(ctx, resp) // Stage 10
    g.auditPublisher.PublishAsync(buildAllowEvent(req, resp, time.Since(start))) // Stage 11
    return resp, nil
} |
| --- |
| # OPA bundle layout per tenant
bundle/
├── .manifest           # Bundle metadata: revision, roots
├── pinaka/
│   ├── platform/       # L0: Platform Baseline (immutable)
│   │   ├── baseline.rego
│   │   └── data.json   # Hardcoded prohibited actions
│   ├── shared/         # Shared modules used by all policy levels
│   │   ├── data_classification.rego  # classify_data() function
│   │   ├── tool_sensitivity.rego     # tool_sensitivity_tier() function
│   │   ├── agent_context.rego        # agent_risk_tier() lookup
│   │   └── utils.rego
│   └── tenant/         # L1–L3: Tenant-specific policies
│       ├── data.json   # Tenant policy definitions (loaded from PostgreSQL)
│       └── evaluate.rego  # Main entry point: imports platform + shared |
| --- |
| # pinaka/shared/data_classification.rego
package pinaka.shared

# classify_data returns the highest sensitivity tier found in a list of classifications
# Tiers: PUBLIC(0) < INTERNAL(1) < REGULATED(2) < IP(3) < PII(4) < FINANCIAL(5)
classify_data(classifications) = tier {
    tier := max([tier_score(c) | c := classifications[_]])
} else = 0

tier_score("PUBLIC")    = 0
tier_score("INTERNAL")  = 1
tier_score("REGULATED") = 2
tier_score("IP")        = 3
tier_score("PII")       = 4
tier_score("FINANCIAL") = 5

# ─── pinaka/platform/baseline.rego ─────────────────────────────────────
# L0: Platform Baseline — immutable. DENY wins over all tenant policies.
package pinaka.platform

import future.keywords.if
import data.pinaka.shared

# DENY: Credential exfiltration is never permitted
baseline_deny if {
    input.tool_name in {"env-read", "secrets-read", "credential-export"}
    shared.classify_data(input.data_classifications) >= 4  # PII or higher
    input.destination == "EXTERNAL"
}

# ─── pinaka/tenant/evaluate.rego ────────────────────────────────────────
# Main evaluation entry point — called by OPA for each EvaluateAction request
package pinaka.evaluate

import data.pinaka.platform
import data.pinaka.shared
import data.tenant_policies  # Loaded from data.json (PostgreSQL export)

# Decision: DENY if any baseline rule fires
decision = "DENY" { platform.baseline_deny }

# Decision: evaluate tenant policies in level order (L1 → L2 → L3)
# DENY wins across all levels (most restrictive)
decision = "DENY" {
    not platform.baseline_deny
    some policy in applicable_policies
    policy.action_on_match == "DENY"
    rego.eval_policy(policy.rego_source, input)
}

decision = "ESCALATE" {
    not platform.baseline_deny
    not deny_from_tenant_policy
    some policy in applicable_policies
    policy.action_on_match == "ESCALATE"
    rego.eval_policy(policy.rego_source, input)
}

decision = "ALLOW" {
    not platform.baseline_deny
    not deny_from_tenant_policy
    not escalate_from_tenant_policy
}

# applicable_policies: sorted L1→L2→L3, filtered by scope match
applicable_policies[p] {
    p := tenant_policies[_]
    p.enabled == true
    scope_matches(p, input)
    not in_shadow_mode(p)
}

scope_matches(p, input) if { p.scope_type == "TENANT" }
scope_matches(p, input) if {
    p.scope_type == "AGENT_GROUP"
    input.agent_id in p.scope_agent_ids
}
scope_matches(p, input) if {
    p.scope_type == "AGENT"
    p.scope_id == input.agent_id
} |
| --- |
| Event | Trigger | Action | SLA |
| --- | --- | --- | --- |
| Policy CRUD (create/update/delete) | Admin HTTP call to policy-engine | 1. Write policy to PostgreSQL 2. Invalidate Redis bundle cache (DEL key) 3. Publish policy_changed event to Kafka | Bundle rebuilt on next enforcement call; cache miss < 50ms rebuild |
| Policy enters shadow mode | Admin sets shadow_mode_until timestamp | Enforce as log-only (emit as if DENY but return ALLOW to caller); shadow_mode flagged in audit event | Immediate; no bundle rebuild needed |
| Shadow mode expires | Scheduled job checks shadow_mode_until < NOW() | Remove shadow_mode_until; bundle rebuild triggered | < 5 min from expiry (job runs every 5min) |
| Policy approved and deployed | ArgoCD sync from policy git repo | Full bundle rebuild for affected tenant; Redis cache invalidated | < 60s from ArgoCD sync completion |
| OPA version upgrade | Helm chart update for policy-engine | Rolling deploy; new pods compile bundles with new OPA version; old pods serve from cache during rollout | Zero downtime (rolling deploy + PDB min 2) |
| Console Browser | API Gateway
(Kong) | Platform Service | Redis
(Token Store) |
| --- | --- | --- | --- |
| [1] → GET /v1/agents (expired access_token in Authorization header) | ────────▶ GET /v1/agents (expired access_token in Authorization header) |  |  |
|  | ⟳ JWT verify: signature OK but exp < now() → 401 Unauthorized |  |  |
| ──▷ 401 {error:'token_expired', refresh_hint:true} | 401 {error:'token_expired', refresh_hint:true} ◁── |  |  |
| [4] → POST /v1/auth/refresh {refresh_token: 'rt_...'} (HttpOnly cookie) | ────────▶ POST /v1/auth/refresh {refresh_token: 'rt_...'} (HttpOnly cookie) |  |  |
|  | [5] → RefreshToken(refresh_token_hash) [gRPC] | ────────▶ RefreshToken(refresh_token_hash) [gRPC] |  |
|  |  | [6] → GET refresh_token:{sha256(refresh_token)} — verify exists + not expired | ────────▶ GET refresh_token:{sha256(refresh_token)} — verify exists + not expired |
|  |  | ──▷ Token record: {user_id, tenant_id, issued_at, expires_at} | Token record: {user_id, tenant_id, issued_at, expires_at} ◁── |
|  |  | [8] → DEL refresh_token:{old_hash} — single-use; invalidate immediately | ────────▶ DEL refresh_token:{old_hash} — single-use; invalidate immediately |
|  |  | ⟳ Sign new access_token (RS256, 15min) + new refresh_token (256-bit random, 7d) |  |
|  |  | [10] → SET refresh_token:{sha256(new_rt)} {user_id, tenant_id} EX 604800 | ────────▶ SET refresh_token:{sha256(new_rt)} {user_id, tenant_id} EX 604800 |
|  | ──▷ new_access_token + new_refresh_token | new_access_token + new_refresh_token ◁── |  |
| ──▷ 200 {access_token:'...'} + Set-Cookie: refresh_token=... HttpOnly Secure SameSite=Strict | 200 {access_token:'...'} + Set-Cookie: refresh_token=... HttpOnly Secure SameSite=Strict ◁── |  |  |
| 📝 Refresh token rotation: old RT deleted before new RT issued. Parallel refresh attempts: Redis DEL is atomic — second attempt gets cache miss → 401. |  |  |  |
| Admin (Browser) | Console UI | Platform Service | Enterprise IdP
(Okta/Azure AD) |
| --- | --- | --- | --- |
| [1] → GET /login?sso=true | ────────▶ GET /login?sso=true |  |  |
|  | [2] → GET /v1/auth/sso/initiate?domain=company.okta.com | ────────▶ GET /v1/auth/sso/initiate?domain=company.okta.com |  |
|  |  | ⟳ Lookup SSO config for domain; generate PKCE code_verifier + code_challenge |  |
|  | ──▷ Redirect URL: https://company.okta.com/oauth2/v1/authorize?client_id=...&code_challenge=...&state=... | Redirect URL: https://company.okta.com/oauth2/v1/authorize?client_id=...&code_challenge=...&state=... ◁── |  |
| ──▷ Redirect to IdP login page | Redirect to IdP login page ◁── |  |  |
| [6] → Authenticate with corporate credentials (MFA if IdP requires) |  |  | ────────▶ Authenticate with corporate credentials (MFA if IdP requires) |
|  | ────────▶ Redirect: /auth/callback?code=auth_code&state=... |  | [7] ← Redirect: /auth/callback?code=auth_code&state=... |
|  | [8] → POST /v1/auth/sso/callback {code, state, code_verifier} | ────────▶ POST /v1/auth/sso/callback {code, state, code_verifier} |  |
|  |  | [9] → POST /oauth2/v1/token {code, code_verifier, client_secret} — exchange for id_token | ────────▶ POST /oauth2/v1/token {code, code_verifier, client_secret} — exchange for id_token |
|  |  | ──▷ id_token (JWT): {sub, email, groups[], name} | id_token (JWT): {sub, email, groups[], name} ◁── |
|  |  | ⟳ Verify id_token signature against IdP JWKS; extract email + groups |  |
|  |  | ⟳ Map IdP groups → Pinaka RBAC roles via tenant SSO group mapping config |  |
|  |  | ⟳ Find or create Pinaka user record; issue Pinaka access_token + refresh_token |  |
|  | ──▷ access_token + Set-Cookie: refresh_token=... HttpOnly | access_token + Set-Cookie: refresh_token=... HttpOnly ◁── |  |
| ──▷ Logged in — redirect to /dashboard | Logged in — redirect to /dashboard ◁── |  |  |
| MFA Method | Implementation | When Required | Fallback |
| --- | --- | --- | --- |
| TOTP (Google Authenticator, Authy) | Standard TOTP (RFC 6238): 6-digit code, 30s window, HMAC-SHA1. Secret stored encrypted in PostgreSQL. Enrollment: QR code generation from base32 secret. | Required for: admin role actions, policy approval, HITL Tier 2 approve, tenant config changes | SMS OTP via Twilio if TOTP device lost (with identity verification) |
| WebAuthn (Passkey, FIDO2 hardware key) | WebAuthn Level 2 spec. Attestation stored in PostgreSQL (credential_id, public_key, sign_count). Challenge issued per authentication attempt, verified against stored public key. | Optional; replaces TOTP for users who register a passkey or Yubikey | TOTP fallback if WebAuthn device unavailable |
| SSO-delegated MFA | If enterprise SSO (Okta/Azure AD) is configured, Pinaka trusts IdP's MFA claim (amr claim in id_token must include 'mfa' or 'hwk') | When tenant has SSO configured and IdP enforces MFA for Pinaka app | Pinaka-native TOTP if SSO is down |
| Email OTP (account recovery only) | 6-digit code sent to registered email. Valid 15 minutes. Rate-limited: 3 attempts per 15 min. | Account recovery only; not for regular auth flow | Not applicable — this IS the fallback |
| // API Key Rotation — zero-downtime, supports dual-key period
// 1. Admin requests new key: POST /v1/api-keys/{id}/rotate
//    - Generate new key (32-byte random → SHA-256 for storage)
//    - Store new key hash in PostgreSQL with status='ACTIVE'
//    - OLD key status → 'ROTATING' (still accepted for 7 days)
//    - Emit api_key.rotated event to audit log
//    - Return new key plaintext (shown ONCE; never stored plaintext)

// 2. During 7-day rotation window:
//    - Both old and new key accepted by API Gateway
//    - Old key requests get X-Key-Rotating: true header in response
//    - Warning logged in Datadog if old key used after rotation

// 3. After 7 days (scheduled job):
//    - ROTATING keys with updated_at < NOW() - 7days → status='EXPIRED'
//    - Old key no longer accepted
//    - api_key.expired event emitted

// Kong rate limit keys use API key hash — no change needed on rotation
// Redis AIT cache keys use agent_id — not affected by API key rotation |
| --- |
| Stack | React 18 + TypeScript + Vite 5. All state managed via Zustand (global) + React Query (server state). WebSocket for real-time. D3.js v7 for ARM graph. Design system: shadcn/ui + Tailwind CSS 3. |
| --- | --- |
| console-ui/
├── src/
│   ├── app/              # App-level: router, providers, auth guard
│   │   ├── App.tsx
│   │   ├── router.tsx    # React Router v6 declarative routes
│   │   └── providers.tsx # QueryClient, WebSocketProvider, ThemeProvider
│   ├── features/         # Feature-based modules (co-locate UI + logic)
│   │   ├── agents/       # Agent inventory, agent detail, risk badge
│   │   ├── arm/          # Agentic Risk Map (D3.js graph)
│   │   ├── policies/     # Policy editor, policy list, dry-run viewer
│   │   ├── hitl/         # HITL queue, approve/deny UI, timer
│   │   ├── audit/        # Audit log viewer, NL query input, export
│   │   ├── compliance/   # Framework dashboards, report generation
│   │   ├── connectors/   # Connector management, health status
│   │   └── settings/     # Tenant config, users, SSO, notifications
│   ├── shared/           # Shared components, hooks, utilities
│   │   ├── components/   # Button, Table, Badge, RiskScore, etc.
│   │   ├── hooks/        # useWebSocket, useTenantContext, useRBAC
│   │   ├── api/          # React Query hooks wrapping REST API
│   │   └── store/        # Zustand global state slices
│   └── lib/              # Third-party wrappers, D3 utilities
├── tests/                # Playwright E2E + Vitest unit
└── storybook/            # Component stories + design system docs |
| --- |
| State Type | Tool | What Lives Here | Persistence |
| --- | --- | --- | --- |
| Server State (async) | React Query (TanStack Query) | Agent list, risk scores, policies, audit events, HITL queue — all data fetched from API | In-memory; refetch on focus/interval; staleTime per query |
| Global UI State | Zustand | Auth session (user, tenant_id, roles), WebSocket connection status, ARM graph selected node, active HITL count, notification queue | Session only (memory); auth stored in HttpOnly cookie (server-managed) |
| URL State | React Router search params | Filters (agent status, risk tier, time range), pagination cursor, selected framework, active tab | URL bar — shareable, bookmarkable, browser back/forward works |
| Form State | React Hook Form | Policy editor, connector setup, user management forms — complex validation | Component lifecycle; reset on submit |
| Real-time State | WebSocket + Zustand | Live risk score updates, new HITL alerts, connector health changes, discovery scan progress | Pushed from server; merged into React Query cache via queryClient.setQueryData |
| // src/shared/hooks/useWebSocket.ts
// Per-tenant WebSocket connection — established after login

interface PinakaWSMessage {
  type: 'risk_score_update' | 'hitl_request' | 'discovery_progress' |
        'connector_health' | 'policy_violation_alert' | 'ping';
  payload: unknown;
  event_id: string;  // For deduplication
  timestamp: string;
}

export function useWebSocket() {
  const { tenant_id, access_token } = useAuthStore();
  const queryClient = useQueryClient();

  useEffect(() => {
    const ws = new WebSocket(
      `wss://api.pinaka.ai/v1/ws?token=${access_token}`
    );

    ws.onmessage = (event) => {
      const msg: PinakaWSMessage = JSON.parse(event.data);

      // Dedup: ignore if event_id seen in last 60s
      if (seenEventIds.has(msg.event_id)) return;
      seenEventIds.add(msg.event_id);
      setTimeout(() => seenEventIds.delete(msg.event_id), 60_000);

      switch (msg.type) {
        case 'risk_score_update':
          // Merge into React Query cache — triggers re-render
          queryClient.setQueryData(['agents', msg.payload.agent_id],
            (old: Agent) => ({...old, risk_score: msg.payload.score}));
          break;
        case 'hitl_request':
          queryClient.invalidateQueries({queryKey: ['hitl', 'pending']});
          useNotificationStore.getState().addAlert(msg.payload);
          break;
        case 'connector_health':
          queryClient.invalidateQueries({queryKey: ['connectors']});
          break;
      }
    };

    ws.onclose = () => {
      // Exponential backoff reconnect: 1s, 2s, 4s, 8s... max 60s
      setTimeout(() => reconnect(), Math.min(60_000, 1000 * 2**attempts));
    };
  }, [tenant_id, access_token]);
} |
| --- |
| // GET /v1/risk/arm — returns graph data for D3.js
interface ARMResponse {
  nodes: ARMNode[];
  edges: ARMEdge[];
  metadata: { total_agents: number; max_depth: number; generated_at: string };
}

interface ARMNode {
  id: string;              // agent_id | tool_id | source_id | mcp_server_id
  type: 'AGENT' | 'TOOL' | 'DATA_SOURCE' | 'MCP_SERVER' | 'EXTERNAL_API';
  label: string;
  risk_score?: number;     // 0-100 (AGENT nodes only)
  risk_tier?: string;      // CRITICAL | HIGH | MEDIUM | LOW | MINIMAL
  sensitivity_tier?: number; // DATA_SOURCE nodes: 0-5
  is_quarantine?: boolean; // Agent in quarantine status
  blast_radius?: number;   // Estimated max downstream impact
  x?: number; y?: number;  // D3 force simulation position (set by D3, not API)
}

interface ARMEdge {
  source: string;          // node id
  target: string;          // node id
  type: 'CAN_CALL' | 'READS' | 'WRITES' | 'CONNECTS_TO' | 'CALLS_AGENT';
  permission_level: string; // READ | WRITE | EXECUTE
  is_approved: boolean;    // false = over-permissioned edge
} |
| --- |
| // src/features/arm/ARMGraph.tsx
const simulation = d3.forceSimulation(nodes)
  .force('link', d3.forceLink(edges)
    .id((d: ARMNode) => d.id)
    .distance(d => d.type === 'CALLS_AGENT' ? 120 : 80)  // Agent-agent: longer links
  )
  .force('charge', d3.forceManyBody()
    .strength((d: ARMNode) => d.type === 'AGENT' ? -300 : -100)  // Agents repel more
  )
  .force('center', d3.forceCenter(width / 2, height / 2))
  .force('collision', d3.forceCollide()
    .radius((d: ARMNode) => nodeRadius(d) + 10)  // Prevent overlap
  );

// Node styling by type + risk
const nodeColor = (d: ARMNode): string => {
  if (d.type !== 'AGENT') return NODE_COLORS[d.type];
  if (d.risk_tier === 'CRITICAL') return '#B22222';
  if (d.risk_tier === 'HIGH')     return '#FF4500';
  if (d.risk_tier === 'MEDIUM')   return '#FFB300';
  if (d.risk_tier === 'LOW')      return '#66BB6A';
  return '#90A4AE';  // MINIMAL
};

// Click → show agent detail panel; Shift+Click → highlight blast radius
// Scroll → zoom; Drag → pan; Double-click node → drill-down |
| --- |
| # investigation_engine/baseline/online_learner.py
# Online learning: exponential moving average per agent per (tool, destination) pair
# Baseline feature vector per agent: call_rate, avg_param_entropy, destination_mix

from dataclasses import dataclass
import numpy as np

@dataclass
class AgentBaseline:
    agent_id: str
    # EMA of call rate per hour for each (tool_name, destination) pair
    call_rate_ema: dict[tuple, float]  # EMA μ
    call_rate_var: dict[tuple, float]  # EMA σ² (Welford's online variance)
    # EMA of parameter entropy (measures: are params unusually large/diverse?)
    param_entropy_ema: float
    param_entropy_var: float
    # Sample count (for convergence detection)
    n_samples: int
    last_updated: datetime

ALPHA = 0.05  # EMA decay: ~20 events to converge (~1 day of normal activity)
ANOMALY_THRESHOLD_SIGMA = 3.0  # Alert at 3σ deviation

def update_baseline(baseline: AgentBaseline, event: AgentActionEvent) -> float:
    """Update EMA baseline and return anomaly z-score (>3 = alert)"""
    key = (event.tool_name, event.destination)
    current_rate = 1.0  # Observed: 1 call in this window

    # Welford's online algorithm for mean + variance
    old_ema = baseline.call_rate_ema.get(key, 0.0)
    old_var = baseline.call_rate_var.get(key, 1.0)
    new_ema = ALPHA * current_rate + (1 - ALPHA) * old_ema
    new_var = (1 - ALPHA) * (old_var + ALPHA * (current_rate - old_ema)**2)

    baseline.call_rate_ema[key] = new_ema
    baseline.call_rate_var[key] = new_var
    baseline.n_samples += 1

    # Z-score: how many standard deviations from the mean?
    sigma = max(np.sqrt(new_var), 0.01)  # Floor to avoid /0
    z_score = abs(current_rate - new_ema) / sigma
    return z_score  # > 3.0 = anomaly |
| --- |
| Detector | Algorithm | Feature Inputs | Training | Alert Threshold |
| --- | --- | --- | --- | --- |
| Call Rate Anomaly | Online EMA + z-score | Tool call frequency per (tool, dest) pair per hour | Continuous online learning; no batch training | z-score > 3σ (configurable per tenant sensitivity setting) |
| Parameter Entropy | Shannon entropy of serialised parameters | Entropy of JSON parameter string; detects unusually large or novel parameters | Online EMA baseline per agent per tool | entropy > baseline_mean + 3σ |
| Destination Shift | Distribution drift detection (KL-divergence) | Ratio of internal vs external vs MCP server calls over rolling 1h window | Rolling 24h baseline distribution | KL-divergence > 0.3 (significant distribution shift) |
| Time Pattern Anomaly | Isolation Forest (scikit-learn, batch weekly retrain) | Hour-of-day, day-of-week call distributions per agent | Weekly batch retrain on last 30 days of events (Temporal workflow) | Anomaly score < -0.2 (Isolation Forest score) |
| Cross-Agent Collusion | Graph pattern matching | Agent interaction graph: agent A calls agent B which calls tool C in coordinated burst | Event-triggered: runs when 3+ agents show anomalous pattern in 5-min window | Cosine similarity of anomaly vectors across agents > 0.85 |
| # investigation_engine/narrative/generator.py
# Privacy-preserving LLM narrative generation

NARRATIVE_PROMPT_TEMPLATE = '''
You are a cybersecurity risk analyst. Generate a clear, business-focused risk narrative
based ONLY on the structured data below. Do not invent details not present in the data.

Agent: {agent_name} (ID: {agent_id})
Agent Role (defined at registration): {agent_description}
Risk Tier: {risk_tier} (Score: {risk_score}/100)
Trigger: {trigger_event_type}

Recent anomalies detected:
{anomalies_structured}

Policy violations in last 24h: {violation_count} ({violation_severity_breakdown})
Data classifications accessed: {data_classifications}
Blast radius: {blast_radius_description}

Write a 150-200 word risk narrative: what the agent did, why it is a concern,
business impact, and recommended action. Be specific. Use plain English.
Do NOT include: specific file contents, actual parameter values, PII, or raw logs.
'''

async def generate_narrative(investigation: Investigation) -> str:
    # 1. Build structured context (no raw data)
    context = build_sanitised_context(investigation)  # Strips all content, keeps metadata

    # 2. Call AWS Bedrock (Claude Sonnet) in tenant's region
    response = await bedrock_client.invoke_model(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        body=json.dumps({
            'messages': [{'role':'user','content': NARRATIVE_PROMPT_TEMPLATE.format(**context)}],
            'max_tokens': 400,
            'temperature': 0.1,  # Low temp = factual, consistent
        })
    )

    # 3. Validate: check narrative only references entities in context
    narrative = response['content'][0]['text']
    validate_narrative_grounding(narrative, context)  # Raises if hallucination detected

    return narrative |
| --- |
| # connector_sdk/normalisation/pipeline.py

class NormalisationPipeline:
    stages = [
        ExtractAgentIdentity,    # Map source agent ID → Pinaka agent_id (registry lookup)
        ClassifyToolCall,        # Map tool name → Pinaka tool taxonomy
        ClassifyDestination,     # Classify destination as INTERNAL/EXTERNAL/MCP/AGENT
        DetectDataClassification,# Run DLP patterns on parameters (metadata only)
        EnrichWithContext,       # Add agent risk score, AISPM tier, policy group
        TimestampNormalise,      # Normalise to UTC nanoseconds (handle TZ offsets)
        FingerprintEvent,        # Compute SHA-256 dedup key for idempotency
    ]

    async def normalise(self, raw_event: dict, connector: Connector) -> AgentActionEvent:
        ctx = NormalisationContext(raw_event=raw_event, connector=connector)
        for stage in self.stages:
            ctx = await stage().process(ctx)
            if ctx.should_drop:  # Some events are noise — drop silently
                return None
        return ctx.normalised_event |
| --- |
| Phase | Action | Who | Tooling | Audit |
| --- | --- | --- | --- | --- |
| Provisioning | Admin creates connector via API; enters credentials | Security Engineer via Console | Pinaka API → Vault KV v2 write at secret/tenant/{tenant_id}/connector/{connector_id} | audit: connector.created |
| Runtime access | Discovery Engine fetches credentials for scan | discovery-engine service account | Vault API read with IRSA auth; short-lived lease (300s) | Vault audit log |
| Rotation | Admin triggers rotation OR scheduled 90-day auto-rotation | Admin (manual) OR scheduled Temporal workflow (auto) | 1. Write new creds to Vault under new version 2. Test new creds 3. Update connector.vault_secret_version 4. Delete old version after 7-day overlap | audit: connector.rotated |
| Revocation | Admin deletes connector | Security Admin | Vault metadata delete (all versions); PostgreSQL soft-delete | audit: connector.deleted |
| Emergency revoke | Security incident — immediate credential invalidation | Security Admin or SRE (PagerDuty) | Vault revoke lease + delete all versions + POST /v1/connectors/{id}/emergency-revoke | audit: connector.emergency_revoked; PagerDuty P1 |
| Subnet | CIDR | AZ | Resources | Route Table |
| --- | --- | --- | --- | --- |
| Public Subnet AZ-a | 10.0.0.0/20 | us-east-1a | ALB, NAT Gateway (AZ-a) | Internet Gateway → 0.0.0.0/0 |
| Public Subnet AZ-b | 10.0.16.0/20 | us-east-1b | ALB (multi-AZ), NAT Gateway (AZ-b) | Internet Gateway → 0.0.0.0/0 |
| Public Subnet AZ-c | 10.0.32.0/20 | us-east-1c | ALB (multi-AZ), NAT Gateway (AZ-c) | Internet Gateway → 0.0.0.0/0 |
| Private App AZ-a | 10.0.48.0/20 | us-east-1a | EKS worker nodes (pinaka-core, pinaka-data, pinaka-platform) | NAT Gateway AZ-a → 0.0.0.0/0 |
| Private App AZ-b | 10.0.64.0/20 | us-east-1b | EKS worker nodes (all namespaces) | NAT Gateway AZ-b → 0.0.0.0/0 |
| Private App AZ-c | 10.0.80.0/20 | us-east-1c | EKS worker nodes (all namespaces) | NAT Gateway AZ-c → 0.0.0.0/0 |
| Private Data AZ-a | 10.0.96.0/20 | us-east-1a | RDS Primary, ElastiCache Primary, MSK Broker 1 | NAT Gateway AZ-a (restricted) |
| Private Data AZ-b | 10.0.112.0/20 | us-east-1b | RDS Standby, ElastiCache Replica, MSK Broker 2 | NAT Gateway AZ-b (restricted) |
| Private Data AZ-c | 10.0.128.0/20 | us-east-1c | RDS Read Replica, ElastiCache Replica, MSK Broker 3 | NAT Gateway AZ-c (restricted) |
| AWS Service | Endpoint Type | Why Critical | Subnets |
| --- | --- | --- | --- |
| S3 (audit logs) | Gateway endpoint (free) | Audit log writes must never traverse internet; removes NAT cost for high-volume writes | App + Data subnets |
| AWS Secrets Manager | Interface endpoint | Vault fallback; connector credential access; eliminates NAT for secrets fetch | App subnets only |
| AWS KMS | Interface endpoint | Encryption/decryption for tenant data; high call frequency | App + Data subnets |
| Bedrock (LLM) | Interface endpoint | EU: ensures LLM calls stay within AWS EU boundary for data residency compliance | App subnets (EU region only) |
| ECR (container registry) | Interface endpoint | Image pull during deployment; reduces NAT bandwidth cost | App subnets |
| CloudWatch Logs | Interface endpoint | Datadog agent exports to CloudWatch as buffer; reduces NAT | App subnets |
| STS (IAM/IRSA) | Interface endpoint | Token vending for IRSA — high call frequency; eliminate NAT | App subnets |
| Security Group | Inbound Rules | Outbound Rules | Assigned To |
| --- | --- | --- | --- |
| sg-alb-public | 443 from 0.0.0.0/0 (HTTPS); 80 from 0.0.0.0/0 (redirect to HTTPS) | All to sg-kong-private | ALB |
| sg-kong-private | 8080 from sg-alb-public; 8443 from sg-alb-public | All to sg-eks-nodes; 443 to VPC endpoints | Kong EKS pods |
| sg-eks-nodes | All from sg-kong-private; all from within sg-eks-nodes (inter-pod) | 443 to VPC endpoints; 443 to internet via NAT (for external APIs) | All EKS worker nodes |
| sg-rds | 5432 from sg-eks-nodes only | None (stateful — responses allowed automatically) | RDS PostgreSQL + TimescaleDB |
| sg-elasticache | 6379 from sg-eks-nodes only | None | ElastiCache Redis |
| sg-msk | 9092, 9094 (TLS) from sg-eks-nodes only | None | MSK Kafka brokers |
| sg-opensearch | 443 from sg-eks-nodes only | None | OpenSearch domain |
| sg-vpn-ops | 22 from corporate VPN CIDR only | All within VPC | Bastion host (emergency ops access) |
| Config Layer | Mechanism | Content | Changes How |
| --- | --- | --- | --- |
| Infrastructure Config (IaC) | Terraform (terraform/envs/{env}/) | VPC, EKS, RDS, MSK, ElastiCache, IAM roles — all infra definitions | PR → plan → apply via Atlantis; protected branch; 2 approvals |
| Kubernetes Platform Config | Helm values files + ArgoCD Application CRDs | Service replicas, resource limits, HPA thresholds, namespace isolation — cluster-level config | Helm values PR → ArgoCD auto-sync on merge |
| Application Config (non-secret) | Kubernetes ConfigMap (generated from Helm values) | LOG_LEVEL, KAFKA_BOOTSTRAP_SERVERS, OTEL_ENDPOINT, FEATURE_FLAGS_SDK_KEY — no secrets | Rolling pod restart on ConfigMap change (checksum annotation trick) |
| Secrets | External Secrets Operator (ESO) → Vault/Secrets Manager | DB passwords, API keys, TLS certs, Vault tokens — never in git | ESO polls Vault every 5min; auto-updates K8s Secret; pods restart if secret changes |
| Feature Flags | LaunchDarkly SDK (runtime) | Feature toggles, kill switches, A/B test variants, tenant-specific flags | LaunchDarkly console → instant runtime update; no deploy needed |
| Tenant Runtime Config | PostgreSQL + Redis cache (platform-service) | Tenant plan tier, rate limits, failsafe mode, notification channels — tenant-specific | Admin API call → PostgreSQL write → Redis cache invalidate → immediate effect |
| # External Secrets Operator — syncs Vault secrets to K8s Secrets
# Every service has an ExternalSecret CR that ESO watches
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: policy-engine-secrets
  namespace: pinaka-core
spec:
  refreshInterval: 5m  # Poll Vault every 5 minutes
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: policy-engine-secrets  # Creates this K8s Secret
    creationPolicy: Owner
    template:
      annotations:
        pinaka.io/secret-version: "{{ .vault_version }}"  # Triggers rolling restart
  data:
  - secretKey: DB_PASSWORD
    remoteRef:
      key: secret/pinaka/policy-engine
      property: db_password
  - secretKey: REDIS_PASSWORD
    remoteRef:
      key: secret/pinaka/policy-engine
      property: redis_password |
| --- |
| # argocd/apps/pinaka-prod.yaml — root Application (App of Apps pattern)
# This single ArgoCD Application manages ALL Pinaka services in prod
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata: {name: pinaka-prod, namespace: argocd}
spec:
  source:
    repoURL: https://github.com/pinaka-ai/pinaka-gitops
    path: environments/production  # Directory of child Application CRDs
    targetRevision: main
  syncPolicy:
    automated:
      prune: true   # Remove resources deleted from git
      selfHeal: true  # Revert manual kubectl changes
    syncOptions:
      - CreateNamespace=true
      - ServerSideApply=true

# environments/production/ contains one Application per service:
# policy-engine.yaml, discovery-engine.yaml, audit-service.yaml, etc.
# Each points to services/{service}/charts/ with values-prod.yaml

# Sync waves: deploy in dependency order
# Wave 0: platform-service (auth needed by everything)
# Wave 1: policy-engine (enforcement needed by mcp-gateway)
# Wave 2: audit-service, aispm-engine (needed before traffic)
# Wave 3: mcp-gateway, api-gateway (front doors)
# Wave 4: all other services
# annotation: argocd.argoproj.io/sync-wave: '2' |
| --- |
| Step | From | To | Gate | Rollback |
| --- | --- | --- | --- | --- |
| 1 | Feature branch | Dev environment | All PR checks pass; 2 code reviewer approvals | git revert; ArgoCD self-heals in <60s |
| 2 | Dev | Staging | Engineering Lead approval; integration tests pass; load test passes SLO | Helm rollback: helm rollback {service} -n {ns}; ArgoCD sync |
| 3 | Staging | Production (5% canary) | Staging stable for 24h; SRE approval; no open P1/P2 incidents | ArgoCD: set canary weight to 0%; Istio VirtualService update |
| 4 | 5% canary | 25% canary | Canary SLO met for 15 min (error rate <0.1%, p99 <SLO target) | Same as step 3 |
| 5 | 25% canary | 100% production | SLO maintained for 30 min; no anomalous Datadog metrics | Istio VirtualService: 100% to stable; delete canary deployment |
| # Index template: pinaka-audit-{tenant_id}-{YYYY.MM}
PUT _index_template/pinaka-audit
{
  'index_patterns': ['pinaka-audit-*'],
  'template': {
    'settings': {
      'number_of_shards': 3,
      'number_of_replicas': 1,
      'index.lifecycle.name': 'pinaka-audit-ilm',
      'index.lifecycle.rollover_alias': 'pinaka-audit-write'
    },
    'mappings': {
      'properties': {
        'event_id':         {'type': 'keyword'},
        'tenant_id':        {'type': 'keyword'},
        'agent_id':         {'type': 'keyword'},
        'event_type':       {'type': 'keyword'},
        'timestamp':        {'type': 'date', 'format': 'strict_date_optional_time_nanos'},
        'action_summary':   {'type': 'text', 'analyzer': 'english'},  // Full-text search
        'policy_decision':  {'type': 'keyword'},
        'policy_id':        {'type': 'keyword'},
        'tool_name':        {'type': 'keyword'},
        'destination':      {'type': 'keyword'},
        'data_classifications': {'type': 'keyword'},  // Array
        'regulatory_tags':  {'type': 'keyword'},      // EU_AI_ACT_ART14, NIST_MAP_1, etc.
        'risk_score_after': {'type': 'short'},
        'risk_delta':       {'type': 'short'}
      }
    }
  }
}

# ILM Policy: hot → warm → cold → delete
PUT _ilm/policy/pinaka-audit-ilm
{
  'policy': {'phases': {
    'hot':  {'actions': {'rollover': {'max_age': '1d', 'max_size': '50gb'}}},
    'warm': {'min_age': '90d', 'actions': {'migrate': {}}},   // OpenSearch UltraWarm
    'cold': {'min_age': '2y',  'actions': {'freeze': {}}},    // UltraWarm cold
    'delete': {'min_age': '7y', 'actions': {'delete': {}}}    // GDPR: 7yr max
  }}
} |
| --- |
| Stage | Component | Config | Volume |
| --- | --- | --- | --- |
| 1. Emit | All services emit structured JSON to stdout (not file) | Container stdout captured by containerd log driver | All service logs |
| 2. Collect | Datadog Agent DaemonSet on each EKS node collects container stdout | Agent runs as DaemonSet; mounts /var/log/containers | All pods on node |
| 3. Enrich | Datadog Agent adds K8s metadata (pod, namespace, service, node) | Agent auto-discovers K8s labels; enriches with deployment info | Automatic |
| 4. Filter | Drop DEBUG logs in production; sample INFO at 10%; keep all WARN/ERROR | Datadog Agent log processing rules; sampling based on log.level tag | 60-70% volume reduction |
| 5. Redact | Strip any fields matching PII patterns (email, credit card regex) | Datadog Agent sensitive data scanner; run before transmission | Automatic scrubbing |
| 6. Ship | Compressed HTTPS to Datadog EU or US endpoint (matching tenant region) | Agent HTTPS; mTLS optional; batched every 5s or 4MB | Remaining ~30-40% of raw volume |
| 7. Index | Datadog indexes logs with 15-day hot retention; 30-day warm | Datadog Log Management plan | Searchable within 15 days |
| 8. Archive | S3 for long-term compliance (logs from security events only) | Datadog Archive to S3; filter: log.level:ERROR OR security_event:true | Small subset for compliance |
| Implementation note | This section provides the exact algorithm engineers implement in aispm-engine. The score is computed by aispm-engine/scoring/calculator.py on every trigger event. |
| --- | --- |
| # aispm-engine/scoring/calculator.py

DIMENSION_WEIGHTS = {
    'permission_scope':    0.25,
    'data_access':         0.25,
    'blast_radius':        0.20,
    'autonomy':            0.15,
    'policy_compliance':   0.15,
}

async def calculate_risk_score(agent_id: str, tenant_id: str) -> RiskScore:

    # ── DIMENSION 1: Permission Scope (0–100) ──────────────────────────
    # Higher score = more overpermissioned
    tools = await db.get_agent_tools(agent_id)  # List[Tool]
    tool_entropy = sum(
        TOOL_SENSITIVITY[t.sensitivity_tier] * ACCESS_TYPE_WEIGHT[t.access_type]
        for t in tools
    ) / max(len(tools), 1)
    # TOOL_SENSITIVITY: {READ:1, WRITE:3, EXECUTE:5, ADMIN:10}
    # ACCESS_TYPE_WEIGHT: {INTERNAL:1.0, MCP_SERVER:1.5, EXTERNAL:2.0}
    # Normalise to 0-100: score = min(tool_entropy / 10.0 * 100, 100)
    d_permission = min(tool_entropy / 10.0 * 100, 100)

    # ── DIMENSION 2: Data Access Sensitivity (0–100) ───────────────────
    sources = await db.get_agent_data_sources(agent_id)  # List[DataSource]
    # DATA_TIER: {PUBLIC:0, INTERNAL:10, REGULATED:30, IP:50, PII:70, FINANCIAL:90}
    d_data = sum(
        DATA_TIER[s.classification] * ACCESS_FREQ_WEIGHT(s.access_frequency_percentile)
        for s in sources
    ) / max(len(sources), 1)
    d_data = min(d_data, 100)

    # ── DIMENSION 3: Blast Radius (0–100) ──────────────────────────────
    # BFS from agent node in Neo4j; sum criticality of reachable nodes
    reachable = await neo4j.bfs_blast_radius(agent_id, max_depth=5)
    blast = sum(
        NODE_CRITICALITY[n.type] * (1 / (n.depth + 1))  # Depth decay
        for n in reachable
    )
    # NODE_CRITICALITY: {AGENT:20, DATA_SOURCE:15, MCP_SERVER:10, TOOL:5}
    d_blast = min(blast / 200.0 * 100, 100)  # Normalise: 200 = 'large blast radius'

    # ── DIMENSION 4: Autonomy Level (0–100) ────────────────────────────
    # Classification: agents scored 0-5 at registration; mapped to 0-100
    AUTONOMY_MAP = {0:0, 1:20, 2:40, 3:60, 4:80, 5:100}
    d_autonomy = AUTONOMY_MAP[agent.autonomy_level]

    # ── DIMENSION 5: Policy Compliance (0–100) ─────────────────────────
    violations = await db.get_recent_violations(agent_id, days=30)
    # VIOLATION_SEVERITY maps CVSS: CRITICAL:25, HIGH:15, MEDIUM:8, LOW:3
    # Recency decay: violations in last 24h = full weight; 30d old = 0.1 weight
    d_compliance = sum(
        VIOLATION_SEVERITY[v.severity] * recency_decay(v.occurred_at)
        for v in violations
    )
    d_compliance = min(d_compliance, 100)

    # ── COMPOSITE SCORE ─────────────────────────────────────────────────
    composite = sum(
        DIMENSION_WEIGHTS[k] * v for k, v in {
            'permission_scope': d_permission,
            'data_access': d_data,
            'blast_radius': d_blast,
            'autonomy': d_autonomy,
            'policy_compliance': d_compliance,
        }.items()
    )
    score = round(composite)  # Integer 0-100

    return RiskScore(
        composite=score,
        dimensions={'permission':d_permission,'data':d_data,'blast':d_blast,
                    'autonomy':d_autonomy,'compliance':d_compliance},
        tier=score_to_tier(score),  # CRITICAL/HIGH/MEDIUM/LOW/MINIMAL
    ) |
| --- |
| // Cursor = base64(JSON({sort_field: value, id: uuid_v7}))
// Stable across concurrent writes; no offset drift

// Request:
GET /v1/audit/events?limit=50&cursor=eyJzb3J0X2ZpZWxkIjoiMjAyNi0wNCJ9

// Response:
{
  'data': [...],
  'pagination': {
    'total': null,           // Not provided — expensive count query avoided
    'limit': 50,
    'next_cursor': 'eyJz...',  // null if no more pages
    'has_more': true
  }
}

// Cursor construction (Go — audit-service):
func encodeCursor(event AuditEvent) string {
    c := Cursor{Timestamp: event.Timestamp, EventID: event.EventID}
    b, _ := json.Marshal(c)
    return base64.URLEncoding.EncodeToString(b)
}

// Query with cursor (PostgreSQL — RLS applies automatically):
// WHERE (timestamp, event_id) < ($cursor_ts, $cursor_id)  -- for DESC sort
// ORDER BY timestamp DESC, event_id DESC
// LIMIT 51  -- fetch one extra to determine has_more |
| --- |
| // All POST endpoints support Idempotency-Key header (UUID v4)
// 24-hour deduplication window; stored in Redis

func IdempotencyMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        key := r.Header.Get('Idempotency-Key')
        if key == '' { next.ServeHTTP(w, r); return }

        // Validate format (UUID v4)
        if !isValidUUID(key) { http.Error(w, 'invalid_idempotency_key', 400); return }

        redisKey := fmt.Sprintf('idempotency:%s:%s', r.Header.Get('X-Tenant-ID'), key)

        // Try to acquire lock (SETNX with 30s expiry — in-flight protection)
        acquired, _ := redis.SetNX(ctx, redisKey+':lock', 'processing', 30*time.Second).Result()
        if !acquired {
            // Another request with same key is in-flight
            http.Error(w, 'idempotency_conflict', 409); return
        }

        // Check if already completed
        cached, err := redis.Get(ctx, redisKey).Result()
        if err == nil {
            // Return cached response
            var resp CachedResponse
            json.Unmarshal([]byte(cached), &resp)
            w.WriteHeader(resp.StatusCode)
            w.Write(resp.Body); return
        }

        // Execute request and cache response
        rec := httptest.NewRecorder()
        next.ServeHTTP(rec, r)

        cached_resp := CachedResponse{StatusCode: rec.Code, Body: rec.Body.Bytes()}
        b, _ := json.Marshal(cached_resp)
        redis.Set(ctx, redisKey, string(b), 24*time.Hour)  // 24h dedup window
        redis.Del(ctx, redisKey+':lock')

        w.WriteHeader(rec.Code)
        w.Write(rec.Body.Bytes())
    })
} |
| --- |
| Service | Liveness Check (/healthz) | Readiness Check (/readyz) | Startup Probe |
| --- | --- | --- | --- |
| policy-engine | Process alive; goroutines not deadlocked (runtime check) | OPA bundle loaded in Redis; PostgreSQL ping; Redis PING | 60s initialDelay — bundle compilation on cold start |
| mcp-gateway | Process alive; no critical goroutine leak | Policy Engine gRPC connection UP; Redis PING; AIT revocation list loaded | 30s initialDelay |
| discovery-engine | Process alive | PostgreSQL connection pool healthy; Vault token valid; Temporal connection UP | 45s initialDelay — Vault token fetch |
| audit-service | Process alive | Kafka producer connected; Iceberg catalog reachable (S3 REST); OpenSearch ping | 30s initialDelay |
| aispm-engine | Process alive | Neo4j Bolt connection UP; TimescaleDB ping; Risk scoring model loaded | 45s initialDelay — model load |
| hitl-service | Process alive | PostgreSQL ping; Redis ping; Notification Service reachable | 20s initialDelay |
| investigation-engine | Process alive | OpenSearch ping; ML model loaded; Redis ping | 60s initialDelay — sklearn model deserialise |
| platform-service | Process alive | PostgreSQL ping; Redis ping; Vault token valid | 30s initialDelay |
| compliance-engine | Process alive | PostgreSQL ping; Temporal connection UP | 30s initialDelay |
| Migration Type | Rule | Example | Deployment Order |
| --- | --- | --- | --- |
| Add column (nullable) | Safe: add with DEFAULT or nullable | ALTER TABLE agents ADD COLUMN blast_radius INT | Deploy migration → deploy new code |
| Add column (NOT NULL) | Requires 3-step: add nullable → backfill → add NOT NULL constraint | 1) ADD COLUMN new_col INT 2) UPDATE SET new_col=value 3) ALTER COLUMN SET NOT NULL | Deploy step 1 → backfill job → deploy step 3 (separate release) |
| Add index | Safe: use CREATE INDEX CONCURRENTLY (non-blocking in PostgreSQL) | CREATE INDEX CONCURRENTLY idx_agents_risk ON agents(risk_score) | Can deploy anytime; index build runs in background |
| Rename column | Two-phase: add alias column → dual-write → migrate reads → drop old | 1) ADD COLUMN new_name 2) Trigger copies data 3) Update app to read new 4) DROP COLUMN old | 3 releases minimum |
| Drop column | Only after app code no longer references it (deploy app first, migrate second) | First: remove app references (deploy). Then: ALTER TABLE DROP COLUMN | App deploy first → migration after (reverse of add) |
| Drop table | Only after 0 app references verified via grep + schema validation in CI | Confirm in CI: no model/query references → DROP TABLE | Same as drop column |
| Add NOT NULL constraint | Use CHECK constraint with NOT VALID → validate in separate transaction | ALTER TABLE ADD CONSTRAINT ... NOT NULL NOT VALID; then VALIDATE CONSTRAINT | CONSTRAINT NOT VALID = non-blocking; VALIDATE = blocks briefly |
| Approach | Pinaka avoids distributed transactions. Every multi-service operation is designed as: (1) write to durable store, (2) emit event, (3) consumers react idempotently. The Kafka event log is the system of truth. |
| --- | --- |
| Multi-Service Operation | Consistency Pattern | Implementation | Failure Handling |
| --- | --- | --- | --- |
| Policy change → cache invalidate → audit | Transactional outbox pattern: write policy to DB + outbox event in same PostgreSQL transaction; relay reads outbox → publishes to Kafka | policy-engine writes policy_changed to outbox table in same txn; relay service polls outbox; publishes to Kafka; consumers invalidate cache + write audit | If relay fails: outbox row remains; retry on next poll. DB rollback = no event published. Guaranteed at-least-once delivery. |
| Agent registration → AIT issuance → risk score | Sequential with idempotency keys: each step idempotent; Temporal workflow orchestrates | Temporal activity 1: create agent record (idempotent = upsert). Activity 2: issue AIT (idempotent = check ait_registry). Activity 3: trigger risk score (idempotent = score if no score within 1min) | Temporal retries each activity independently. Partial completion is safe — re-run from last successful activity. |
| HITL approval → action resume → audit | Saga (choreography): each service listens to events and takes compensating action if needed | hitl.approved event published → mcp-gateway resumes action → action.allowed event → audit-service logs. If mcp-gateway timeout: audit logs hitl_approved + action_cancelled. | Saga compensating action: if mcp-gateway doesn't consume hitl.approved within 60s → auto-DENY. Published to hitl.responses topic. |
| Tenant deletion → cross-service cleanup | Saga (orchestration via Temporal): Temporal workflow coordinates deletion sequence | Temporal: 1) Suspend tenant (no new events) 2) Drain Kafka topics for tenant 3) PostgreSQL soft-delete 4) Schedule hard-delete in 30d 5) Neo4j cleanup 6) OpenSearch index delete 7) Vault key deletion | Each step idempotent. Failure retried. Human review step required before Vault key deletion. |
| Temporal | Rotation Worker | Vault | Source System
(e.g. AWS IAM) | Kafka |
| --- | --- | --- | --- | --- |
| [1] → [SCHEDULED: 90 days from last rotation] StartRotationWorkflow(connector_id) | ────────▶ [SCHEDULED: 90 days from last rotation] StartRotationWorkflow(connector_id) |  |  |  |
|  | [2] → Activity: GetCurrentCredentials(connector_id) — read current secret version | ────────▶ Activity: GetCurrentCredentials(connector_id) — read current secret version |  |  |
|  | ──▷ Current API key + metadata | Current API key + metadata ◁── |  |  |
|  | [4] → Activity: GenerateNewCredentials — create new API key in source system |  | ────────▶ Activity: GenerateNewCredentials — create new API key in source system |  |
|  | ──▷ New API key (plaintext, one-time) |  | New API key (plaintext, one-time) ◁── |  |
|  | [6] → Activity: WriteNewCredentials — Vault KV put new version; old version retained | ────────▶ Activity: WriteNewCredentials — Vault KV put new version; old version retained |  |  |
|  | ⟳ Activity: TestNewCredentials — make test API call using new key; verify success |  |  |  |
|  | [8] → Activity: UpdateConnectorVersion — update connector.vault_secret_version pointer | ────────▶ Activity: UpdateConnectorVersion — update connector.vault_secret_version pointer |  |  |
|  | ⟳ Activity: Wait 7 days (overlap period) — old key still accepted |  |  |  |
|  | [10] → Activity: RevokeOldCredentials — delete old API key from source system |  | ────────▶ Activity: RevokeOldCredentials — delete old API key from source system |  |
|  | [11] → Activity: DeleteOldVaultVersion — remove old secret version | ────────▶ Activity: DeleteOldVaultVersion — remove old secret version |  |  |
|  | [12] → Publish: connector.rotated event [→|] |  |  | ─ ─ ─ ▶ Publish: connector.rotated event [→|] |
| 📝 If TestNewCredentials fails: rollback (delete new Vault version, notify admin, re-try in 24h). Old key remains active. |  |  |  |  |
| // tests/load/enforcement-path.js — primary performance test
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Histogram } from 'k6/metrics';

const policyDecisionLatency = new Histogram('pinaka_policy_decision_ms');
const denyRate = new Counter('pinaka_deny_decisions');

export const options = {
  scenarios: {
    // Scenario 1: Sustained load — 1000 RPS for 10 min
    sustained_load: {
      executor: 'constant-arrival-rate',
      rate: 1000, timeUnit: '1s',
      duration: '10m', preAllocatedVUs: 50, maxVUs: 200,
    },
    // Scenario 2: Spike — ramp to 3000 RPS in 30s, hold 2min, ramp down
    spike: {
      executor: 'ramping-arrival-rate',
      startRate: 100,
      stages: [
        {duration:'30s', target:3000},
        {duration:'2m', target:3000},
        {duration:'30s', target:100},
      ],
      preAllocatedVUs: 100, maxVUs: 500,
    },
  },
  thresholds: {
    http_req_duration: ['p(99)<500'],    // v1.0 SLO: <500ms p99
    http_req_failed: ['rate<0.001'],     // Error rate <0.1%
    pinaka_policy_decision_ms: ['p(99)<400'],  // Internal target
  },
};

export default function() {
  const start = Date.now();
  const res = http.post('https://staging-api.pinaka.ai/v1/enforcement/evaluate', {
    tenant_id: __ENV.TEST_TENANT_ID,
    agent_id: `test-agent-${Math.floor(Math.random()*100)}`,
    tool_name: 'spreadsheet-read',
    destination: 'INTERNAL',
    data_classifications: ['FINANCIAL'],
  }, { headers: { 'Authorization': `Bearer ${__ENV.TEST_TOKEN}` } });

  policyDecisionLatency.add(Date.now() - start);
  if (res.json('decision') === 'DENY') denyRate.add(1);

  check(res, {
    'status is 200': (r) => r.status === 200,
    'has decision': (r) => r.json('decision') !== undefined,
    'has decision_id': (r) => r.json('decision_id') !== undefined,
  });
} |
| --- |
| Section | Content | Example |
| --- | --- | --- |
| Title + Alert Name | Clear title matching PagerDuty alert name | Runbook: PinakaEnforcementLatencyHigh |
| Severity | P1/P2/P3/P4 and customer impact description | P2 — Customer Warning: Enforcement decisions slow; agents may experience increased latency |
| Alert Trigger | Exact metric + threshold that fires this runbook | Fires when: pinaka_enforcement_duration_seconds{p99} > 0.5s for >5 min |
| On-Call First Response (5 min) | Steps engineer takes in first 5 min: check dashboard, confirm real | 1. Open Datadog dashboard: pinaka/enforcement-slo 2. Confirm real (not flapping) 3. Check p99 trend direction 4. Post in #incidents: 'Investigating EnforcementLatencyHigh' |
| Diagnosis Tree | Decision tree: check A → if X go to section 2, if Y go to section 3 | Check Redis cache hit rate. If hit rate <95% → Section 2 (cache miss). If hit rate normal → Section 3 (OPA evaluation) |
| Remediation Steps | Numbered steps with commands | 1. Check OPA bundle cache: redis-cli GET policy_bundle:{tenant_id}:* 2. Force bundle rebuild: POST /v1/internal/policy-engine/bundle-rebuild |
| Rollback | How to revert if remediation makes things worse | Rollback: helm rollback policy-engine -n pinaka-core; ArgoCD will re-sync; verify SLO recovers |
| Escalation | When to escalate and to whom | Escalate to Engineering Lead if not resolved in 30 min; to CTO if customer impact confirmed |
| Post-Incident | PIR creation, tracking, follow-up | Create GitHub Issue tagged 'incident' + 'slo-miss'; schedule PIR within 48hr; update this runbook if gaps found |
| # Istio VirtualService for enforcement path (mcp-gateway → policy-engine)
# Critical: enforcement must fail fast and fail secure
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata: {name: policy-engine-vs, namespace: pinaka-core}
spec:
  hosts: [policy-engine.pinaka-core.svc.cluster.local]
  http:
  - name: enforcement-route
    match: [{uri: {prefix: /pinaka.policy.v1.PolicyEngine/EvaluateAction}}]
    route: [{destination: {host: policy-engine, port: {number: 50051}}}]
    timeout: 10ms  # Hard enforcement deadline — fail fast
    retries:
      attempts: 0  # NO retries on enforcement — DENY on first failure (Fail Secure)
  - name: management-route
    match: [{uri: {prefix: /pinaka.policy.v1.PolicyEngine}}]
    route: [{destination: {host: policy-engine, port: {number: 50051}}}]
    timeout: 5000ms  # Management API: longer timeout
    retries:
      attempts: 3
      perTryTimeout: 1500ms
      retryOn: 'gateway-error,connect-failure,retriable-4xx'

# VirtualService for audit-service (write path — at-least-once)
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata: {name: audit-service-vs, namespace: pinaka-data}
spec:
  http:
  - name: read-route
    match: [{method: {exact: GET}}]
    timeout: 3000ms
    retries: {attempts: 2, perTryTimeout: 1000ms}
  - name: write-route
    match: [{method: {exact: POST}}]
    timeout: 1000ms
    retries: {attempts: 3, perTryTimeout: 300ms} |
| --- |
| # AWS Glue Schema Registry setup (per region — separate registries for US/EU)
# Registry name: pinaka-{region}  (e.g., pinaka-us-east-1, pinaka-eu-west-1)

# Schema naming convention:
# {domain}-{event_type}-v{major}  (major version = breaking change)
# Examples: enforcement-AgentActionEvent-v1, risk-RiskScoreUpdate-v1

# Schema evolution rules (backward compatibility enforced by Glue):
# ALLOWED:  Add optional field with default value
# ALLOWED:  Add new enum value (consumers must handle unknown values)
# FORBIDDEN: Remove field, change field type, rename field, change field order

# Producer registration (Go — kafka_producer.go):
import 'github.com/aws/aws-glue-schema-registry-golang'

schema_registry = glue.NewRegistry(
    region=AWS_REGION,
    registry_name='pinaka-'+AWS_REGION,
    compatibility='BACKWARD',  # New schema must be backward compatible
)

# Kafka message format: [1-byte magic] [4-byte schema_id] [avro_payload]
# Schema ID fetched from Glue on first use; cached indefinitely (immutable)

# Schema version bump process:
# 1. Write new schema to schemas/{domain}/{event_type}/v{major}.avsc
# 2. CI validates backward compatibility: avro-tools tojson --schema-file v1.avsc v2.avsc
# 3. PR merged → CI registers schema in Glue (staging first, prod on release)
# 4. Producers updated to emit new schema; consumers handle both old and new |
| --- |
| # Multi-stage Dockerfile — Go service example (policy-engine)
# Stage 1: Build
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download  # Cache layer — only rebuilds if go.mod changes
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags='-w -s' -o /policy-engine ./cmd/policy-engine

# Stage 2: Runtime — minimal attack surface
FROM gcr.io/distroless/static:nonroot  # No shell, no package manager, non-root user
COPY --from=builder /policy-engine /policy-engine
COPY --from=builder /app/policies/ /policies/  # OPA Rego files
USER nonroot:nonroot
EXPOSE 50051 8080 9090  # gRPC, REST, metrics
ENTRYPOINT ['/policy-engine']

# Python service example (investigation-engine)
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --target /app/deps
COPY . .

FROM python:3.12-slim
COPY --from=builder /app/deps /app/deps
COPY --from=builder /app/src /app/src
ENV PYTHONPATH=/app/deps
USER 1000:1000  # Non-root user
CMD ['python', '-m', 'investigation_engine.main']

# Image tagging strategy:
# ghcr.io/pinaka-ai/{service}:{git_sha}  — immutable, used in ArgoCD
# ghcr.io/pinaka-ai/{service}:latest      — DO NOT use in production
# ghcr.io/pinaka-ai/{service}:v1.2.3      — release tag (alias for specific SHA) |
| --- |