# Coinmarketcap Agent — Secure Crypto Intelligence

This repository contains the **Coinmarketcap Agent**, a production-grade cryptocurrency intelligence agent built on our modular stategraph framework. It includes direct integration guidelines for the **CMC Skill Hub MCP service** and is wrapped in an **8-layer Runtime Defense Harness** for safety and compliance.

---

## 🔒 8-Layer Security Harness
The Coinmarketcap Agent ensures that all crypto searches, external calls, and data lookups pass through Adrian's robust security wrapper:
1. **Scope Gating**: Asserts that queries are within cryptocurrency boundaries (defined in `security/contract.yaml`).
2. **PII Scrubbing**: Cleans out phone numbers, email addresses, and credit cards from inbound inputs.
3. **Red-Line Threat Detection**: Shuts down intent violations (such as unauthorized shell execution or secret exfiltration).

---

## 🚀 Connecting to CMC Skill Hub MCP
The agent utilizes the `cmc-skill-hub` server configured locally:
- **MCP Endpoint**: `https://mcp.coinmarketcap.com/skill-hub/stream`
- **Transport**: Streamable HTTP
- **API Key**: Connected via header authentication (`X-CMC-MCP-API-KEY`)

---

## 💻 Structure
- **`app/`**: FastAPI gatekeeper serving chat lookups.
- **`agent/`**: Core StateGraph Plan-Act-Observe loop containing specialized crypto query nodes.
- **`security/`**: Safety initialization and YAML boundary rules.
- **`memory/`**: Sliding window conversation history.

---

## 📊 Getting Started

### 1. Installation
```bash
pip install -e .
```

### 2. Run the tests
```bash
python -m unittest discover -s tests
```
