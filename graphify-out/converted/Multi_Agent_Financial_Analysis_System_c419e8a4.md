<!-- converted from Multi_Agent_Financial_Analysis_System.docx -->

Multi-Agent Financial Analysis System
Architecture & Implementation Guide
Using Claude AI APIs
Version 1.0 | February 09, 2026

# Table of Contents
[Table of contents will be generated when opened in Word]

# Executive Summary
This document provides a comprehensive guide to building a multi-agent financial analysis system using Claude AI. The system comprises eight specialized agents that work in concert to provide deep insights into equity investments, combining fundamental analysis, technical indicators, competitive moats, earnings trends, institutional movements, and market sentiment.
The architecture leverages Claude's advanced API capabilities, including the Message Batches feature for parallel execution, structured outputs for machine-readable results, and web search integration for real-time data. Each agent is purpose-built with domain-specific prompts and tools, ensuring expert-level analysis across all dimensions of equity research.
## Key Benefits
- Comprehensive Coverage: Eight specialized agents analyze every critical dimension of equity research - from balance sheets to social media sentiment
- Parallel Processing: Execute multiple analyses simultaneously using Claude's Message Batches API, reducing total analysis time from hours to minutes
- Expert-Level Analysis: Each agent uses Claude Opus 4.5 or Sonnet 4.5 with domain-specific prompting to deliver institutional-grade insights
- Real-Time Data Integration: Automated web search and API integration ensures analysis is based on current market conditions and latest filings
- Structured Outputs: JSON-formatted results enable seamless integration with dashboards, databases, and downstream systems

# System Architecture
## Overview
The multi-agent system follows a distributed architecture where each agent operates independently but contributes to a unified analysis. The architecture consists of three primary layers: Agent Layer (eight specialized agents), Orchestration Layer (workflow management and aggregation), and Integration Layer (data sources and output channels).
## Agent Layer: Specialized Analysts
Each agent is configured with specific expertise, Claude model selection, and output schemas:
## Model Selection Strategy
- Claude Opus 4.5 (claude-opus-4-20251101): Reserved for agents requiring deep reasoning and strategic synthesis. Used for Fundamental Analysis and MOAT Analysis where complex financial interpretation and competitive dynamics require highest-tier intelligence.
- Claude Sonnet 4.5 (claude-sonnet-4-20250929): The workhorse model balancing performance and cost. Handles Technical Analysis, Earnings Analysis, News/Presentation parsing, Social Media monitoring, and Peer Analysis. Excellent for pattern recognition and structured data extraction.
- Claude Haiku 4.5 (claude-haiku-4-20251001): Optimized for speed and cost efficiency. Ideal for Institutional Flow tracking where rapid processing of bulk transaction data and ownership changes is required with minimal interpretation needed.

# Orchestration Layer Design
## Architecture Pattern
The orchestration layer coordinates agent execution, manages data flow, and synthesizes outputs. It follows a three-stage pattern: Parallel Execution, Result Aggregation, and Final Synthesis.
### Stage 1: Parallel Execution
All eight agents execute simultaneously using Claude's Message Batches API. Each receives the target company ticker/name plus agent-specific context (e.g., the Technical Analysis agent receives recent price history, while the Institutional Flow agent receives latest bulk deal data).
# Example: Parallel agent invocation using Message Batches API
import anthropic
import asyncio

client = anthropic.Anthropic()

# Define agent configurations
agents = {
    "fundamental": {
        "model": "claude-opus-4-20251101",
        "system_prompt": FUNDAMENTAL_SYSTEM_PROMPT,
        "max_tokens": 4000
    },
    "technical": {
        "model": "claude-sonnet-4-20250929",
        "system_prompt": TECHNICAL_SYSTEM_PROMPT,
        "max_tokens": 3000
    }
    # ... other agents
}

# Create batch requests
batch_requests = []
for agent_name, config in agents.items():
    batch_requests.append({
        "custom_id": agent_name,
        "params": {
            "model": config["model"],
            "max_tokens": config["max_tokens"],
            "system": config["system_prompt"],
            "messages": [{
                "role": "user",
                "content": f"Analyze {company_ticker}"
            }]
        }
    })

# Execute batch
message_batch = client.messages.batches.create(requests=batch_requests)

# Poll for completion
while message_batch.processing_status != "ended":
    await asyncio.sleep(5)
    message_batch = client.messages.batches.retrieve(message_batch.id)
### Stage 2: Result Aggregation
Agent outputs (structured JSON) are collected and validated. The orchestrator checks for completion status, parses JSON schemas, and handles any errors or timeouts. Results are stored in a unified data structure indexed by agent type.
### Stage 3: Final Synthesis
A final synthesis agent (Claude Opus 4.5) receives all agent outputs and creates a unified investment thesis. This meta-agent identifies consensus signals, flags contradictions, and produces the final recommendation with confidence scoring.
## Data Flow Architecture
Input → Orchestrator → [8 Agents in Parallel] → Aggregator → Synthesis Agent → Output
- Input Stage: User provides company ticker (e.g., RELIANCE.NS) or name. Orchestrator enriches with basic context from financial data APIs (current price, market cap, sector).
- Agent Execution: Eight agents execute in parallel. Each agent may invoke web search tools or fetch external data (SEC filings, NSE bulk deals, Twitter API) as needed.
- Aggregation: Results are validated against expected JSON schemas. Missing or failed agents trigger retry logic or error notifications.
- Synthesis: Meta-agent creates unified investment report, assigning weights to different signals based on data quality and market conditions.
- Output: Final report delivered as JSON (for APIs), PDF (for distribution), or interactive dashboard (for exploratory analysis).

# Detailed Implementation Guide
## Agent 1: Fundamental Analysis
Purpose: Assess financial health, growth trajectory, and capital efficiency through rigorous analysis of financial statements and key performance indicators.
### System Prompt Design
FUNDAMENTAL_ANALYSIS_SYSTEM_PROMPT = """You are an expert fundamental analyst specializing in Indian and global equity markets.

ANALYSIS FRAMEWORK:
1. Revenue Quality & Growth
   - Analyze revenue growth trends (3-year and 5-year CAGR)
   - Assess revenue mix (product/geography breakdown)
   - Identify cyclicality and seasonality patterns

2. Profitability Metrics
   - Gross margin trends and peer comparison
   - EBITDA margin sustainability
   - Operating leverage analysis

3. Return Ratios
   - ROE (Return on Equity) with DuPont decomposition
   - ROCE (Return on Capital Employed) trends
   - Compare against cost of capital

OUTPUT FORMAT (strict JSON):
{
  "company_name": "string",
  "ticker": "string",
  "financial_metrics": {
    "revenue_cagr_3y": float,
    "roe_latest": float,
    "roce_latest": float
  },
  "strengths": ["string"],
  "concerns": ["string"],
  "fundamental_score": integer (0-100),
  "recommendation": "BUY | HOLD | SELL"
}
"""
### Implementation Code
def run_fundamental_analysis(company_ticker: str) -> dict:
    client = anthropic.Anthropic()
    
    response = client.messages.create(
        model="claude-opus-4-20251101",
        max_tokens=4000,
        temperature=0.3,
        system=FUNDAMENTAL_ANALYSIS_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Analyze {company_ticker}"
        }]
    )
    
    return parse_json_response(response)

# Complete Orchestration Implementation
## Orchestrator Class Design
The orchestrator manages the full lifecycle of multi-agent analysis: input validation, parallel execution, result aggregation, error handling, and final synthesis. Below is a production-grade implementation.
class FinancialAnalysisOrchestrator:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.agents = {
            "fundamental": {
                "model": "claude-opus-4-20251101",
                "max_tokens": 4000
            },
            "technical": {
                "model": "claude-sonnet-4-20250929",
                "max_tokens": 3000
            }
            # ... other agents
        }
    
    async def analyze_company(self, ticker: str) -> Dict:
        # Execute all agents in parallel
        agent_results = await self._execute_parallel(ticker)
        
        # Aggregate results
        aggregated = self._aggregate_results(agent_results)
        
        # Synthesize final recommendation
        synthesis = await self._synthesize_results(aggregated)
        
        return {
            "ticker": ticker,
            "agent_results": aggregated,
            "synthesis": synthesis
        }

# Technical Considerations
## Rate Limits & Cost Management
### Prompt Caching Strategy
Claude's Prompt Caching feature can reduce costs by 90% for repeated context. Cache the system prompts since they remain constant across analyses.
### Error Handling & Retry Logic
- Rate Limit Errors (429): Implement exponential backoff with jitter
- Timeout Errors (524): Increase max_tokens or split analysis into chunks
- JSON Parsing Failures: Implement regex extraction and schema validation
- Agent Failures: If >3 agents fail, abort and notify user

# Deployment Architecture
## Infrastructure Options
### Option 1: Serverless (AWS Lambda + Step Functions)
Best for: On-demand analysis, variable workloads, minimal operational overhead
- Architecture: API Gateway triggers Lambda orchestrator → Step Functions spawns 8 parallel Lambdas → Results to S3
- Advantages: Zero server management, automatic scaling, pay-per-use
- Limitations: 15-minute timeout, cold start latency
### Option 2: Container-Based (Kubernetes + Temporal)
Best for: High-volume batch processing, complex workflows, long-running analyses
- Architecture: FastAPI service → Temporal workflow → Agent containers → Redis aggregation
- Advantages: Full control, sophisticated orchestration, no time limits
- Limitations: Higher operational complexity, need to manage infrastructure
## Recommended Stack (Production)

# Best Practices & Lessons Learned
## Prompt Engineering Guidelines
- Be Explicit About Output Format: Always specify exact JSON schema. Include example output.
- Use Domain-Specific Terminology: Use industry-standard terms (CAGR, EBITDA, P/E ratio).
- Specify Role and Expertise Level: Start with "You are an expert equity analyst" not generic "assistant".
- Request Source Attribution: Always ask Claude to cite sources with timestamps.
- Lower Temperature for Factual Tasks: Use temperature 0.2-0.3 for financial analysis.
## Data Quality & Validation
- Cross-Reference Data Sources: Validate against multiple sources, flag discrepancies
- Timestamp All Data: Every data point should include retrieval timestamp
- Implement Schema Validation: Use Pydantic models to validate JSON outputs
- Handle Missing Data Gracefully: Mark fields as "N/A" rather than filling with estimates
## Security & Compliance
- API Key Management: Store in secrets manager, rotate quarterly, never commit to version control
- Data Privacy: Claude does not train on API data. Ensure rights to share financial data.
- Audit Trails: Log all API requests/responses for regulatory compliance
- Disclaimer Requirements: Include disclaimers that this is automated analysis, not personalized advice

# Future Enhancements
## Advanced Features Roadmap
- Multi-Turn Dialogue Agents: Enable agents to have multi-turn conversations for deeper analysis
- Agent Specialization by Market: Create India-specific vs US-specific variants with different regulatory knowledge
- Real-Time Alert System: Monitor key stocks and trigger analysis on specific events
- Backtesting Framework: Run historical analysis to measure predictive accuracy
- Portfolio-Level Analysis: Extend to portfolio construction, correlation analysis, risk-parity
- Natural Language Query Interface: Allow users to ask questions and orchestrate custom agent combinations
- Explainable AI Layer: Add explanation agent to justify conclusions
## Integration Opportunities
- Trading Platforms: Integrate with broker APIs for one-click execution
- Portfolio Management Systems: Export to Bloomberg Terminal, FactSet
- Slack/Teams Notifications: Send daily digest of high-conviction ideas
- Data Warehouses: Stream results to Snowflake/BigQuery for ML training

# Appendix: Additional Agent Prompts
## Technical Analysis Agent Prompt
TECHNICAL_ANALYSIS_SYSTEM_PROMPT = """You are a senior technical analyst.

ANALYSIS FRAMEWORK:
1. Trend Identification - Determine primary trend (daily/weekly)
2. Support & Resistance - Key levels from historical price action
3. Technical Indicators - RSI, MACD, Moving Averages, Bollinger Bands
4. Volume Analysis - Volume trends vs price action
5. Chart Patterns - Head & Shoulders, Triangles, Flags

OUTPUT FORMAT (strict JSON):
{
  "ticker": "string",
  "current_price": float,
  "trend": "UPTREND | DOWNTREND | SIDEWAYS",
  "key_levels": {
    "resistance": [float],
    "support": [float]
  },
  "indicators": {
    "rsi_14": float,
    "macd": {"value": float, "signal": float}
  },
  "technical_score": integer (0-100),
  "recommendation": "BUY | HOLD | SELL"
}
"""
## MOAT Analysis Agent Prompt
MOAT_ANALYSIS_SYSTEM_PROMPT = """You are a competitive strategy analyst.

MOAT SOURCES:
- Network Effects
- Intangible Assets (brand, patents, regulatory licenses)
- Switching Costs
- Cost Advantages
- Efficient Scale

OUTPUT FORMAT (strict JSON):
{
  "company_name": "string",
  "moat_rating": "WIDE | NARROW | NONE",
  "moat_trend": "WIDENING | STABLE | NARROWING",
  "pricing_power": {"rating": "HIGH | MODERATE | LOW"},
  "competitive_threats": ["string"],
  "moat_score": integer (0-100)
}
"""

# Conclusion
This multi-agent financial analysis system represents a paradigm shift in how equity research can be conducted at scale. By leveraging Claude's state-of-the-art language models across eight specialized agents, we achieve comprehensive coverage that would typically require a full team of analysts.

Key Takeaways:
- Architecture Matters: The three-layer architecture ensures scalability and maintainability
- Prompt Engineering is Critical: Well-crafted system prompts dramatically improve analysis quality
- Model Selection Drives Economics: Strategic use of Opus/Sonnet/Haiku optimizes quality and cost
- Synthesis Creates Value: The meta-agent that reconciles perspectives produces true insight
- Continuous Improvement: Implement feedback loops and backtesting to refine agents over time

As you implement this system, remember that AI agents are tools to augment human decision-making, not replace it. The most successful implementations will combine the speed and scale of AI analysis with human judgment, market intuition, and risk management expertise.

Happy building!
| Agent | Claude Model | Primary Focus | Key Outputs |
| --- | --- | --- | --- |
| Fundamental Analysis | Opus 4.5 | Financial health, growth metrics, capital efficiency | ROE/ROCE, margins, debt ratios, cash flow quality |
| Technical Analysis | Sonnet 4.5 | Price patterns, indicators, volume analysis | Support/resistance, momentum signals, trend strength |
| MOAT Analysis | Opus 4.5 | Competitive advantages, barriers to entry, pricing power | Moat score, durability assessment, competitive risks |
| Earnings Analysis | Sonnet 4.5 | Revenue quality, guidance, earnings surprises | EPS trends, beat/miss history, forward outlook |
| Presentation & News | Sonnet 4.5 | Investor presentations, management commentary, media coverage | Key themes, strategic shifts, sentiment analysis |
| Institutional Flow | Haiku 4.5 | FII/DII transactions, block deals, insider trades | Net buying/selling, large stakeholders, ownership changes |
| Social Media Pulse | Sonnet 4.5 | Twitter/X sentiment, Reddit discussions, news velocity | Sentiment score, trending topics, viral catalysts |
| Price & Peer Analysis | Sonnet 4.5 | Valuation multiples, peer comparison, target prices | P/E ratios, relative strength, analyst consensus |
| Model | Rate Limit | Cost Optimization |
| --- | --- | --- |
| Claude Opus 4.5 | 50 requests/min | Use only for Fundamental and MOAT analysis |
| Claude Sonnet 4.5 | 100 requests/min | Primary workhorse for most agents |
| Claude Haiku 4.5 | 200 requests/min | Use for high-volume data processing |
| Component | Technology |
| --- | --- |
| API Layer | FastAPI (Python) on Cloud Run or ECS Fargate |
| Orchestration | Temporal.io for complex workflows |
| Agent Execution | Python async workers with anthropic SDK |
| Data Storage | PostgreSQL, S3, Redis |
| Monitoring | Datadog or New Relic, CloudWatch |
| Frontend | React/Next.js dashboard, Retool admin |