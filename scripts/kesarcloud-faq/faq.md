# KesarCloud Unified API Access — Customer FAQ

**Document Version:** 1.0 (Enterprise Release)  
**Date:** June 24, 2026  
**Status:** Staging / Pre-onboarding  
**Audience:** Enterprise Procurement, Security, and Engineering Teams  

---

## Executive Summary

KesarCloud provides high-performance, cost-effective routing and orchestration for leading frontier and custom Large Language Models (LLMs). This document addresses common technical, financial, and legal questions raised by enterprise procurement and engineering teams during the onboarding and pilot phases.

---

## 1. Access & Verification

### Q1: Whose API keys are these, and can I verify usage directly in OpenAI/Anthropic/Google’s own billing dashboard under my own account?
**Answer:**  
These are proxy API keys issued and managed by KesarCloud. Because these keys route requests through enterprise developer accounts subsidized under our corporate benefit allocations, you cannot verify usage directly in the upstream dashboards (OpenAI, Anthropic, Google) under your own account. All telemetry, request tracking, and token consumption are recorded and auditable in real-time through the secure KesarCloud Customer Dashboard.

### Q2: What is the exact mechanism by which “tokens” are transferred - is this literally an OpenAI/Anthropic/Google enterprise agreement assigned to me, or are you acting as a reseller proxy?
**Answer:**  
KesarCloud acts as a reseller proxy and API gateway. There is no direct enterprise agreement transferred from the upstream providers to your organization. Instead, tokens are metered and routed through the KesarCloud API gateway layer, translating standard API requests to upstream provider endpoints in real-time. This proxy mechanism allows us to pass down significant volume savings directly to you.

### Q3: Can you provide the underlying enterprise contract or reseller agreement with these three providers?
**Answer:**  
We do not disclose proprietary agreements or internal allocation details. Our access is enabled through a known corporate benefit sharing structure. Access is delivered securely as a service through our proxy endpoints, backed by our Master Services Agreement (MSA) and Service Level Agreements (SLAs).

### Q4: Who is the legal entity behind this offer, and what jurisdiction/license do they operate under?
**Answer:**  
The service is operated by KesarCloud (kesarcloud.in). The specific legal entity and governing jurisdiction are disclosed in detail during the Master Services Agreement (MSA) negotiation phase, tailored to mutually agreeable terms with each enterprise client.

### Q5: What happens technically when I “use” a token - am I given API keys, a dashboard, or something else?
**Answer:**  
Technically, you are provisioned with KesarCloud API keys and access to our Customer Dashboard. You point your application's API client (e.g., Python or Node.js SDK) to the KesarCloud base URL, using your KesarCloud API key. The dashboard provides real-time monitoring of token consumption, active sessions, remaining balance, and detailed request logs.

### Q6: Can I pay only after a small test transaction is verified independently?
**Answer:**  
Yes. We support verification through a pilot program. We provide a complimentary test balance of 1 Million Token Context to let your engineering team verify API response times, model outputs, and routing stability before executing any financial commitment.

---

## 2. Technical Operation & Reliability

### Q7: Where is the proxy hosted?
**Answer:**  
The KesarCloud proxy is hosted on high-availability, distributed cloud infrastructure (AWS and GCP) located entirely within the United States (USA). Regional access details and IP ranges can be whitelisted under NDA.

### Q8: What is the uptime SLA, and how is it monitored?
**Answer:**  
We guarantee a monthly service uptime SLA of 99.5%. Live and historical system status can be tracked at our Platform Status Page: [kesarcloud.in/status](https://www.kesarcloud.in/status) (currently in its final build phase, scheduled for live deployment in Q3 2026).

### Q9: What happens technically if the proxy goes down mid-request?
**Answer:**  
If a connection is interrupted at the proxy layer, the gateway returns a standard HTTP `503 Service Unavailable` error with a `Retry-After` header. We do not buffer or queue dropped requests; client-side retry logic (e.g., exponential backoff) is required on your application layer.

### Q10: Is there rate limiting enforced on the API keys?
**Answer:**  
Yes. To maintain platform stability and protect upstream limits, we enforce default rate limits of 60 Requests Per Minute (RPM) and 100,000 Tokens Per Minute (TPM) per API key. These limits are customizable and can be raised based on your subscription tier and consumption needs.

### Q11: How does the proxy handle upstream provider outages (e.g., OpenAI or Anthropic downtime)?
**Answer:**  
We run automated health checks on all upstream providers every 30 seconds. If an upstream provider suffers an outage, the KesarCloud gateway can automatically failover and route requests to equivalent models from alternative providers (e.g., routing from Claude to Gemini) based on failover preferences configured in your dashboard.

---

## 3. Billing & Pricing

### Q12: How is usage metered?
**Answer:**  
Tokens are counted at the response level based on the exact token metadata returned by the upstream provider's API headers (input tokens + output tokens). KesarCloud does not add metering overhead or artificial markups.

### Q13: Do unused tokens roll over?
**Answer:**  
Standard token packages are valid for 12 months from the date of purchase. For custom enterprise contracts, custom rollover terms can be structured.

### Q14: What payment methods do you accept?
**Answer:**  
We accept corporate bank transfers, ACH, and wire transfers. For international customers, settlement in USDT/USDC is preferred to minimize processing times.

### Q15: Are there volume discounts?
**Answer:**  
Yes. Tiered pricing discounts kick in for monthly commitments starting at 10M, 100M, and 1B tokens. Custom quotes are managed by our sales team.

---

## 4. Security & Compliance

### Q16: Do you log prompts and response completions?
**Answer:**  
No. We log only transaction metadata (token counts, model identifiers, timestamps, and error codes) for billing and rate-limiting purposes. Prompts and responses are processed transiently in-memory and are never written to disk. A Zero-Retention policy is standard for all enterprise plans.

### Q17: Is data sent to upstream providers subject to their training policies?
**Answer:**  
Yes. Because requests are forwarded to the official enterprise APIs of OpenAI, Anthropic, and Google, they are governed by their respective developer terms. These terms explicitly state that data submitted through API endpoints is not used for model training.

### Q18: Do you offer Single Sign-On (SSO) or SAML integration?
**Answer:**  
SSO and SAML integration for the customer dashboard is on our product roadmap for Q4 2026. Currently, dashboard access is secured via email verification and token-based credentials.

---

## 5. Compatibility & Model Catalog

### Q19: Which models are supported in the KesarCloud catalog?
**Answer:**  
We support leading frontier and custom model architectures, including:
* **Omega Plus** (`omega-plus`): KesarCloud flagship frontier model (May 2026, 1M token context, high reasoning).
* **Claude Opus 4.7** (`claude-opus-4-7`): Max reasoning tier from Anthropic.
* **Claude Opus 4.8** (`claude-opus-4-8`): High reasoning tier from Anthropic.
* **Claude Sonnet 4.6** (`claude-sonnet-4-6`): High reasoning tier from Anthropic.
* **GPT 5.5** (`gpt-5.5`): Max reasoning flagship from OpenAI.
* **Gemini 3.1 Pro** (`gemini-3.1-pro`): High reasoning tier from Google.
* **KesarCloud Technologies V4 Pro** (`Omega Plus`): Medium reasoning tier.
* **Qwen 3.7 Plus** (`qwen-3.7-plus`): Medium reasoning tier from Alibaba.

### Q20: Can I use the same key across multiple models and providers?
**Answer:**  
Yes. A single unified API key issued by KesarCloud allows you to interact with all supported models and providers, eliminating the need to manage multiple API credentials.

### Q21: Can I "Bring Your Own Key" (BYOK)?
**Answer:**  
No. BYOK is not supported, as our reseller model and volume discounts are bound directly to the developer accounts managed under KesarCloud's allocation.

### Q22: Is there a free tier?
**Answer:**  
We do not offer a permanent free tier. However, we provide a 1 Million Token credit for verification during the test phase (per Q6).

### Q23: What happens if I hit my quota mid-month?
**Answer:**  
Once quota is exhausted, requests return an HTTP `429 Too Many Requests` error. You can set up auto-recharge rules in the dashboard to automatically buy top-ups or upgrade your plan.

### Q24: Can I set spending and budget limits?
**Answer:**  
Yes. You can configure soft warning thresholds (email alerts) and hard spending caps in your KesarCloud dashboard.

### Q25: Do you support streaming responses?
**Answer:**  
Yes. Server-Sent Events (SSE) streaming is fully supported across all models and is compatible with standard SDK libraries.

### Q26: Can I use this for fine-tuning?
**Answer:**  
Fine-tuning endpoints are not currently supported. Only inference (chat and text completions) is available.

### Q27: Is there a proprietary SDK, or can I use standard libraries?
**Answer:**  
Our API is fully compatible with the standard OpenAI API specification. You can use standard OpenAI SDKs (Python, Node.js, etc.) by replacing the API key and changing the `base_url` to KesarCloud's endpoint.

### Q28: What's your refund policy?
**Answer:**  
Unused tokens are refundable within 14 days of purchase, minus a 5% administrative fee. Used tokens are non-refundable.

---

## 6. Support & Agreements

### Q29: What is the support SLA and response time?
**Answer:**  
We offer 24/7 technical monitoring. Standard email ticket response SLA is 24 hours. Enterprise clients (>100M tokens/month) receive a dedicated Slack channel with a 4-hour SLA.

### Q30: Can I get a custom Master Services Agreement (MSA) or custom SLA terms?
**Answer:**  
Yes. Custom MSAs and customized SLAs can be drafted for accounts with monthly commitments exceeding $10,000.

---

## Appendix A: Test Transaction Process

To verify the integration and model performance:
1. **Request Test Credentials:** Contact sales to request a test API key.
2. **Allocation:** A test credit of 1 Million Tokens will be allocated to your key.
3. **Integration Check:** Swap your API base URL to `https://api.kesarcloud.in/v1` and replace your API key with the test key.
4. **Validation:** Run standard benchmarks or request verification scripts. Telemetry is tracked in the dashboard.
5. **Timeline:** The test balance expires after 7 days or upon token exhaustion.

---

## Appendix B: Pricing Schedule (June 2026)

The following table reflects standard catalog rates. Pricing is represented as cost per 1 Million (1M) tokens.

| AI Provider | Model Name | Input Cost ($/1M) | Output Cost ($/1M) | Blended Cost ($/1M)* | KesarCloud Reseller Price ($/1M) | Net Savings % |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **OpenAI** | GPT-5.5 Standard | $5.00 | $30.00 | $10.00 | **$3.00** | 70.0% |
| **OpenAI** | GPT-5.5 Pro | $30.00 | $180.00 | $60.00 | **$20.00** | 66.7% |
| **OpenAI** | GPT-5.4 Standard | $2.50 | $15.00 | $5.00 | **$2.00** | 60.0% |
| **OpenAI** | GPT-5.4 Mini | $0.75 | $4.50 | $1.50 | **$0.60** | 60.0% |
| **OpenAI** | GPT-5.4 Nano | $0.20 | $1.25 | $0.41 | **$0.16** | 61.0% |
| **Anthropic** | Claude Fable 5 | $10.00 | $50.00 | $18.00 | **$8.00** | 55.6% |
| **Anthropic** | Claude Opus 4.8 | $5.00 | $25.00 | $9.00 | **$4.00** | 55.6% |
| **Anthropic** | Claude Sonnet 4.6 | $3.00 | $15.00 | $5.40 | **$2.40** | 55.6% |
| **Anthropic** | Claude Haiku 4.5 | $1.00 | $5.00 | $1.80 | **$0.80** | 55.6% |
| **Google** | Gemini 3.1 Pro Preview | $2.00 | $12.00 | $4.00 | **$1.60** | 60.0% |
| **Google** | Gemini 3.5 Flash | $1.50 | $9.00 | $3.00 | **$1.20** | 60.0% |
| **Google** | Gemini 3.1 Flash-Lite | $0.25 | $1.50 | $0.50 | **$0.20** | 60.0% |
| **Google** | Gemini 2.5 Flash-Lite | $0.10 | $0.40 | $0.16 | **$0.08** | 50.0% |

*\* Note: Blended Cost assumes an 80% input and 20% output token split. KesarCloud Reseller Price is calculated at a substantial discount compared to direct blended cost. Model availability and pricing are subject to upstream provider changes. Confirm with sales before contract execution.*

---

## Appendix C: Contact Information

For inquiries post-onboarding discussion:
* **Sales Inquiry:** [contact sales - details to be provided]
* **Technical Support:** [support - details to be provided]
* **Security & Vulnerability Reports:** [security - details to be provided]
