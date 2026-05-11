<!-- converted from TradingAgents-Product-Plan.docx -->


TRADINGAGENTS
Product Development Plan
A Personal Multi-Agent LLM Trading System
Indian Markets (NSE/BSE FNO) & Crypto (CEX + DEX)

Based on the TradingAgents Framework
Xiao, Sun, Luo & Wang — UCLA / MIT / Tauric Research (arXiv:2412.20138)

CONFIDENTIAL — For Personal Use Only
March 2026

# Table of Contents

# 1. Executive Summary
This document presents the complete product development plan for a personal AI-powered multi-agent trading system, purpose-built for Indian equity derivatives (NSE/BSE Nifty 50 FNO) and cryptocurrency markets (centralized and decentralized exchanges). The system is inspired by and forked from the open-source TradingAgents framework developed by researchers at UCLA, MIT, and Tauric Research.
TradingAgents replicates the organizational structure of a professional trading firm by deploying specialized LLM-powered agents—fundamental analysts, sentiment analysts, news analysts, technical analysts, researchers, traders, and risk managers—that collaborate through structured communication protocols and multi-round debates to arrive at high-conviction trading decisions.
The customized system will extend this framework with: (1) Indian market data sources, broker APIs, and regulatory compliance; (2) cryptocurrency-specific analysis tools including on-chain metrics, DEX integration, and DeFi protocol monitoring; (3) options-specific analytics including Greeks computation, open interest analysis, and gamma exposure tracking; (4) a human checkpoint system for initial deployment, enabling the operator to review, approve, or reject every trade proposal with full transparency into the agent reasoning chain; and (5) a subsequent transition to fully automated execution with SRE-grade observability, circuit breakers, and kill switches.
The development roadmap spans 26 weeks across five phases, from foundational infrastructure through full automation. The target is a system that operates daily with minimal manual intervention while maintaining robust risk controls, achieving risk-adjusted returns superior to conventional rule-based trading strategies.

# 2. Product Vision & Goals
## 2.1 Vision Statement
Build a personal, institutional-grade AI trading system that mirrors the collaborative decision-making workflow of a professional trading firm—leveraging multiple specialized LLM agents to analyze markets, debate trade theses, manage risk, and execute trades across Indian equity derivatives and cryptocurrency markets—operating autonomously with full transparency and human-level risk controls.
## 2.2 Primary Goals
- Systematic Decision-Making: Replace ad-hoc, emotion-driven trading with a structured multi-agent analysis pipeline that considers fundamentals, sentiment, news, and technicals before every trade.
- Daily Efficiency: Reduce the manual research and monitoring time from 3–4 hours per day to under 30 minutes of reviewing agent-generated proposals.
- Risk Discipline: Enforce automated position sizing, stop-losses, max drawdown limits, and portfolio concentration rules that are never bypassed due to emotional bias.
- Market Coverage: Operate across NSE/BSE (Nifty 50 options, Bank Nifty, select stock FNO) and crypto (BTC, ETH, SOL perpetuals on CEX; DeFi yield strategies on DEX).
- Progressive Autonomy: Begin with human-in-the-loop approval for every trade, then transition to full automation once the system demonstrates consistent risk-adjusted outperformance over 3+ months of live trading.
## 2.3 Success Metrics
## 2.4 Target Markets

# 3. System Architecture Overview
The system follows a five-layer architecture adapted from the TradingAgents framework. Each layer represents a distinct phase of the decision-making pipeline, mirroring the workflow of a professional trading firm. Agents communicate through structured reports (not free-form dialogue) to prevent information loss, with natural-language debate reserved for the Researcher and Risk Management teams where dialectical reasoning adds value.
## 3.1 Architecture Layers
## 3.2 Architecture Flow Diagram
Text-based representation of the agent pipeline:
┌─────────────────────────────────────────────────────────────────────────┐
│                        LAYER 1: DATA INGESTION                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │  NSE/BSE     │ │ Crypto CEX/  │ │ Custom News  │ │  Social      │  │
│  │  Market Data  │ │ DEX Data     │ │ API Sources  │ │  Media Feeds │  │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘  │
└─────────┼────────────────┼────────────────┼────────────────┼──────────┘
└────────────────┴───────┬────────┴────────────────┘
▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    LAYER 2: ANALYST TEAM (Parallel)                    │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐      │
│  │Fundamental │  │ Sentiment  │  │   News     │  │ Technical  │      │
│  │  Analyst   │  │  Analyst   │  │  Analyst   │  │  Analyst   │      │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘      │
└────────┼───────────────┼───────────────┼───────────────┼──────────────┘
└───────────────┴───────┬───────┴───────────────┘
▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    LAYER 3: RESEARCH TEAM (Debate)                     │
│       ┌──────────────┐   ◄── n rounds ──►   ┌──────────────┐          │
│       │   Bullish    │ ◄─────────────────► │   Bearish    │          │
│       │  Researcher  │    Research Manager   │  Researcher  │          │
│       └──────────────┘   picks prevailing   └──────────────┘          │
└──────────────────────────────┬────────────────────────────────────────┘
▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      LAYER 4: TRADER AGENT                            │
│        Synthesizes all reports → BUY / SELL / HOLD decision           │
│        Outputs: Ticker, Direction, Size, Entry, SL, Targets           │
│        Options: Strike, Expiry, Strategy Type (spread, straddle...)   │
└──────────────────────────────┬────────────────────────────────────────┘
▼
┌─────────────────────────────────────────────────────────────────────────┐
│                LAYER 5: RISK MANAGEMENT & EXECUTION                   │
│  ┌────────────┐ ┌────────────┐ ┌──────────────┐                       │
│  │ Aggressive │ │  Neutral   │ │ Conservative │ ◄── Risk Debate      │
│  │  Debater   │ │  Debater   │ │   Debater    │                       │
│  └─────┬──────┘ └─────┬──────┘ └──────┬───────┘                       │
│        └──────────────┴───────────────┘                               │
│                        ▼                                              │
│               ┌─────────────────┐                                     │
│               │   Portfolio     │                                     │
│               │    Manager      │                                     │
│               └────────┬────────┘                                     │
│                        ▼                                              │
│         ┌──────────────────────────────┐                              │
│         │  Phase 1: Human Checkpoint   │                              │
│         │  Phase 2: Auto-Execution     │                              │
│         └──────────────┬───────────────┘                              │
└────────────────────────┼──────────────────────────────────────────────┘
▼
┌─────────────────────┐
│   Broker / DEX      │
│   Order Execution   │
└─────────────────────┘

All agents operate under the ReAct (Reasoning and Acting) prompting framework, which enables them to interleave analytical reasoning with tool invocation. The system uses a dual-model strategy: quick-thinking LLMs (e.g., GPT-5-mini, Gemini Flash) for data retrieval and formatting tasks, and deep-thinking LLMs (e.g., GPT-5.2, Claude 4 Opus) for complex analysis, debate, and decision-making.

# 4. Agent Specifications
Each agent is defined by its role, specialized tools, input data, output format, and market-specific customizations. All agents share access to a global state store that maintains the current analysis context, enabling them to query prior findings without depending on long conversation histories.
## 4.1 Fundamental Analyst Agent
### Indian Market Customization (NSE/BSE)
- Quarterly results from BSE/NSE filings, Screener.in, Trendlyne, and MoneyControl
- Indian accounting standards (Ind AS) awareness for financial statement parsing
- Promoter holding and pledge data from SEBI filings
- FII/DII flow data for institutional sentiment on specific stocks
- Sector-specific metrics: NPA ratios for banks, ARPU for telecom, same-store growth for retail
### Crypto Customization
- On-chain metrics: Total Value Locked (TVL), protocol revenue, active addresses, transaction volume
- Token economics analysis: emission schedule, vesting unlocks, burn mechanisms
- DeFi protocol-specific metrics from DefiLlama, Token Terminal, and Dune Analytics
- Smart contract audit status and security incident history

## 4.2 Sentiment Analyst Agent
### Indian Market Sources
- MoneyControl forums and stock-specific discussion boards
- ET (Economic Times) Markets forums and expert columns
- Indian fintwit (financial Twitter) influencer tracking
- TradingView India community ideas and sentiment widgets
- WhatsApp/Telegram trading groups (via authorized API access)
### Crypto Sources
- Crypto Twitter (CT) influencer sentiment and narrative tracking
- Discord alpha channels for DeFi projects
- Telegram trading signal groups
- Fear & Greed Index (Alternative.me), Santiment social volume
- On-chain whale wallet tracking (Nansen, Arkham Intelligence)

## 4.3 News Analyst Agent
### Pluggable News Source Architecture
The News Agent is designed with a configurable source registry to accommodate the operator's custom API sources. Each source is defined as a plugin with the following schema:
- Source name, base URL, authentication method (API key, OAuth, none)
- Request format (REST, GraphQL, RSS), rate limits, polling interval
- Response parsing rules (JSON path extraction, HTML parsing, field mapping)
- Content filters (keywords, categories, relevance scoring thresholds)
- Priority weight (how much this source influences the final news assessment)
### Default Source Categories

## 4.4 Technical Analyst Agent
### Technical Indicators (60+)
### Options-Specific Analytics (NSE FNO)
- Greeks Analysis: Delta, Gamma, Theta, Vega, and Rho for all option chains
- Open Interest (OI) Analysis: Strike-wise OI buildup, OI change, Put-Call Ratio (PCR)
- GEX (Gamma Exposure): Net gamma exposure calculation to identify dealer hedging levels
- Max Pain: Strike price where maximum options expire worthless
- Implied Volatility Surface: IV skew, IV percentile, IV rank across strikes and expiries
- Option chain heatmaps with real-time OI change tracking
### Crypto-Specific Indicators
- Funding Rates: Perpetual futures funding rate trends across exchanges
- Liquidation Levels: Mapped liquidation clusters from aggregated exchange data
- Exchange Flows: Net exchange inflows/outflows (bullish/bearish signal)
- NVT Ratio (Network Value to Transactions): On-chain valuation metric
- MVRV Z-Score: Market value vs. realized value for cycle positioning

## 4.5 Bullish Researcher Agent

## 4.6 Bearish Researcher Agent
The Research Manager evaluates both sides after each debate round, provides feedback, and after the final round, produces a Research Synthesis Report that captures the prevailing view (bullish, bearish, or neutral), strength of conviction, and key unresolved uncertainties.

## 4.7 Trader Agent
### Options-Specific Trade Proposal Fields
- Strike Selection: ATM, OTM, ITM with reasoning based on Greeks and gamma strategy
- Expiry Choice: Weekly, monthly, or quarterly based on time horizon and theta decay analysis
- Strategy Type: Naked call/put, bull/bear spread, straddle, strangle, iron condor, butterfly, calendar spread
- Leg Details: Each leg with strike, premium, quantity, and aggregate Greeks for the position
- Adjustment Rules: Predefined conditions for rolling, adjusting, or closing the position
### Crypto-Specific Trade Proposal Fields
- Leverage: Recommended leverage (1x–20x) with margin requirement calculation
- Exchange Selection: CEX vs. DEX based on liquidity, fees, and slippage analysis
- Funding Rate Consideration: Factor current funding into hold cost for perpetual positions
- DCA Plan: For swing trades, dollar-cost-averaging entry levels and sizes

## 4.8 Risk Management Team (3 Sub-Agents)
The three sub-agents engage in a multi-round discussion (default: 2 rounds) to evaluate and adjust the Trader's proposal. Their output is a Risk-Adjusted Trade Plan that includes:
- Final position size (adjusted from Trader's proposal)
- Maximum loss limit for this trade (absolute ₹ and % of portfolio)
- Revised stop-loss and target levels
- Portfolio-level impact assessment (concentration, correlation, margin usage)
- Risk/reward ratio and expected value calculation
- Conditional orders (trailing stops, partial profit booking levels)

## 4.9 Portfolio Manager Agent

# 5. Human Checkpoint System (Phase 1)
During the initial deployment phase, every trade proposal passes through a human approval step before execution. This serves three purposes: (1) safety — preventing erroneous trades from a still-maturing system; (2) calibration — building a dataset of human overrides to improve agent accuracy; and (3) trust — developing operator confidence in the system's judgment before granting full autonomy.
## 5.1 Dashboard Interface
- Web-based dashboard (React/Next.js frontend, FastAPI backend) displaying the complete agent analysis chain for each trade proposal
- Trade Proposal Card showing: instrument, direction, size, entry, stop-loss, targets, risk/reward ratio, confidence score
- Expandable reasoning panels for each agent's analysis (Fundamental, Sentiment, News, Technical, Research Debate, Risk Assessment)
- Historical performance sidebar showing system track record, win rate, and recent trades
- Portfolio overview panel with current holdings, P&L, margin usage, and exposure heatmap
## 5.2 Approval Workflow
- One-click Approve: Execute trade as proposed by the system
- One-click Reject: Discard the trade proposal with optional rejection reason
- Modify & Approve: Adjust position size, stop-loss, targets, or other parameters before execution
- Defer: Hold the proposal for review later (with auto-expiry based on market hours)
- Time-sensitive alerts: Intraday opportunities flagged with urgency indicators and countdown timers
## 5.3 Notification System
## 5.4 Audit Trail & Learning Loop
- Every decision (approved, rejected, modified) is logged with timestamp, operator reasoning, and market conditions at the time of decision
- Counterfactual tracking: For rejected trades, the system tracks what would have happened if the trade had been executed
- Override accuracy scoring: Periodic analysis of whether human overrides improved or degraded outcomes vs. the system's original recommendation
- Feedback integration: High-confidence human override patterns are used to fine-tune agent prompts and risk parameters
- Decision replay: Ability to replay any past decision cycle with full agent reasoning chain for post-mortem analysis

# 6. Full Automation System (Phase 2)
Once the system demonstrates consistent performance over 3+ months of live trading with human oversight, the human checkpoint can be configured to auto-approve trades that meet specific confidence and risk criteria. Full automation requires additional safety infrastructure.
## 6.1 Broker API Integration
## 6.2 Order Execution Engine
- Smart order routing: Select optimal exchange/venue based on liquidity, fees, and slippage
- Order type mapping: Translate agent trade proposals into broker-specific order types
- Retry logic: Automatic retry with exponential backoff for transient API failures
- Partial fill handling: Monitor and manage partial fills, adjust remaining order as needed
- Slippage monitoring: Track execution price vs. proposed entry, alert on significant deviation
## 6.3 Safety Infrastructure

# 7. Data Pipeline Architecture
The data pipeline is the foundation of the entire system. All agent decisions depend on the quality, freshness, and completeness of input data. The pipeline must handle both real-time streaming data (for intraday trading) and batch historical data (for backtesting and analysis).
## 7.1 Real-Time Market Data
## 7.2 Historical Data Storage
- PostgreSQL: Primary relational database for trade logs, agent decisions, audit trails, configuration
- TimescaleDB (PostgreSQL extension): Time-series hypertables for OHLCV data, tick data, indicator values — optimized for time-range queries and aggregation
- Redis: In-memory cache for latest market prices, session tokens, rate limit counters, inter-agent state sharing
- File Storage: Parquet files for bulk historical data archives (backtesting datasets)
## 7.3 News & Social Media Ingestion
The news pipeline uses the pluggable source registry described in Section 4.3. Each configured source is polled or streamed according to its configuration, and incoming articles are processed through a standard pipeline:
- Deduplication: Hash-based dedup to prevent processing the same article from multiple sources
- Relevance Scoring: Quick-think LLM classifies each article for relevance to tracked instruments/sectors
- Entity Extraction: Identify mentioned companies, tokens, indices, and people
- Sentiment Tagging: Classify article sentiment (positive/negative/neutral) with confidence score
- Impact Assessment: Deep-think LLM evaluates potential market impact and urgency
- Storage: Processed articles stored in PostgreSQL with full-text search indexing
## 7.4 Data Quality & Validation
- Freshness checks: Alert if any data source is stale beyond its expected refresh interval
- Completeness validation: Ensure all required fields are present before passing data to agents
- Anomaly detection: Flag suspicious price spikes, volume anomalies, or data gaps
- Cross-source verification: Compare prices across multiple sources to detect feed errors
- Circuit breaker: If data quality drops below threshold, pause trading and alert operator

# 8. Technology Stack

# 9. Development Phases & Roadmap
The development roadmap spans 26 weeks, divided into five phases. Each phase builds on the previous one and includes clear deliverables and exit criteria before proceeding to the next phase.
## 9.1 Phase 0: Foundation (Weeks 1–3)
Objective: Set up the development environment, fork and understand the TradingAgents codebase, and establish the data infrastructure.
## 9.2 Phase 1: Core Agent System (Weeks 4–8)
Objective: Customize all agents for Indian markets and crypto. Build the full agent pipeline from data ingestion to trade proposal generation.
## 9.3 Phase 2: Human Checkpoint Dashboard (Weeks 9–12)
Objective: Build the operator-facing interface for reviewing and approving trade proposals. Establish the notification infrastructure.
## 9.4 Phase 3: Backtesting & Validation (Weeks 13–16)
Objective: Validate the system against historical data. Identify weaknesses and tune parameters before risking real capital.
## 9.5 Phase 4: Live Trading with Human Oversight (Weeks 17–20)
Objective: Begin live trading with real capital under full human supervision. Validate execution quality, latency, and operational procedures.
## 9.6 Phase 5: Full Automation (Weeks 21–26)
Objective: Remove the human checkpoint for high-confidence trades. Build production-grade monitoring and alerting. Achieve SRE-level operational maturity.
## 9.7 Roadmap Summary

# 10. Risk Controls & Safety
Risk management is the most critical component of the system. Unlike backtesting environments, live trading exposes the system to real financial loss. The risk framework operates at three levels: per-trade, per-day, and portfolio-wide.
## 10.1 Per-Trade Controls
- Maximum position size: 20% of portfolio (configurable per market)
- Mandatory stop-loss: Every trade must have a defined stop-loss. No exceptions.
- Risk/reward minimum: Trades with risk/reward ratio below 1:1.5 are auto-rejected
- Slippage budget: Maximum acceptable slippage of 0.5% for market orders
- Liquidity check: Verify sufficient market depth before placing orders (bid-ask spread < 0.3%)
## 10.2 Per-Day Controls
- Daily loss limit: 3% of portfolio value. Once hit, all trading halts for the day.
- Maximum trades per day: 10 (configurable). Prevents overtrading.
- Intraday exposure limit: Total intraday exposure capped at 2x portfolio value
- Expiry day rules: On options expiry (Thursday), apply 50% tighter stops and reduce max position size by half
## 10.3 Portfolio-Level Controls
- Maximum drawdown: 10% from peak. Triggers full system shutdown and cash conversion.
- Concentration limit: No more than 30% in any single sector/category
- Correlation monitoring: Alert when portfolio beta exceeds 1.5 or correlation among positions exceeds 0.7
- Margin utilization: Keep used margin below 60% of available margin at all times
- Weekly review: Automated weekly risk report comparing actual risk metrics to targets
## 10.4 Emergency Controls
- Kill Switch (Telegram /kill command): Immediately cancels all open orders, closes all positions, halts the system
- API health monitor: If broker API error rate exceeds 5% in any 5-minute window, auto-pause trading
- Market regime detector: Reduce exposure during extreme volatility (India VIX > 25, BTC realized vol > 80%)
- Network partition handling: If connectivity to exchange is lost for > 30 seconds, close all positions on reconnect
- LLM fallback chain: If primary LLM provider is down, automatically route to secondary provider. If all fail, halt trading.

# 11. Monitoring & Observability
Given the operator's SRE background, the monitoring stack is designed to production-grade standards with comprehensive dashboards, structured alerting, and incident response procedures.
## 11.1 Metrics Taxonomy
## 11.2 Alerting Rules
## 11.3 Grafana Dashboard Suite
- Overview Dashboard: Portfolio P&L, total exposure, daily trade count, active alerts, system status
- Agent Performance Dashboard: Per-agent accuracy trends, latency distributions, token consumption, cost breakdown
- Trade Analytics Dashboard: Equity curve, win/loss streaks, per-instrument P&L, time-of-day analysis, holding period analysis
- Risk Dashboard: Current drawdown, VaR estimate, sector exposure pie chart, correlation matrix heatmap, margin usage gauge
- System Health Dashboard: API latency histograms, error rate time-series, data freshness gauges, resource utilization (CPU/memory/disk)
- Cost Dashboard: LLM spend by provider and model, daily/weekly/monthly cost trends, cost per trade breakdown

# 12. Open Questions
The following questions require decisions before or during implementation. They are categorized by urgency and responsible party.
## 12.1 Blocking (Must Resolve Before Phase 1)
## 12.2 Non-Blocking (Can Resolve During Implementation)


# References
1. Xiao, Y., Sun, E., Luo, D., & Wang, W. (2025). TradingAgents: Multi-Agents LLM Financial Trading Framework. arXiv:2412.20138. UCLA / MIT / Tauric Research.
Paper: https://arxiv.org/abs/2412.20138
GitHub: https://github.com/TauricResearch/TradingAgents
2. Tauric Research. TradingAgents Official Project Page.
https://tauric.ai/research/tradingagents/
3. Zerodha. Kite Connect API Documentation.
https://zerodha.com/products/api/
4. CCXT. CryptoCurrency eXchange Trading Library.
https://github.com/ccxt/ccxt
5. Hyperliquid. Python SDK for Hyperliquid DEX API Trading.
https://github.com/hyperliquid-dex/hyperliquid-python-sdk
6. Robot Traders. Algorithmic Trading on Hyperliquid DEX with Python.
https://robottraders.io/blog/algorithmic-trading-hyperliquid-dex-python
7. NSE India. National Stock Exchange Option Chain API.
https://www.nseindia.com/option-chain
| Metric | Target (Phase 1: Human Oversight) | Target (Phase 2: Full Automation) |
| --- | --- | --- |
| Sharpe Ratio (annualized) | > 1.5 | > 2.0 |
| Maximum Drawdown | < 12% | < 10% |
| Win Rate | > 55% | > 58% |
| Profit Factor | > 1.8 | > 2.0 |
| Daily Research Time Saved | > 70% reduction | > 90% reduction |
| System Uptime | > 99% | > 99.5% |
| LLM Cost per Decision Cycle | < ₹150 ($1.80) | < ₹100 ($1.20) |
| Trade Execution Latency | < 2 seconds (after approval) | < 500ms |
| Market | Instruments | Session Hours (IST) | Broker / Exchange |
| --- | --- | --- | --- |
| NSE/BSE FNO | Nifty 50 Options, Bank Nifty Options, Stock FNO | 09:15 – 15:30 | Zerodha (Kite Connect API) |
| Crypto CEX | BTC, ETH, SOL, major alt perpetuals | 24/7 | Binance / Bybit via CCXT |
| Crypto DEX | Perpetuals on Hyperliquid; Spot swaps on Uniswap, Aster | 24/7 | Hyperliquid SDK, Web3.py |
| Layer | Components | Function | Communication Mode |
| --- | --- | --- | --- |
| Layer 1: Data Ingestion | Market data feeds, News APIs, Social media collectors, On-chain indexers | Collect, normalize, and store all input data for downstream analysis | Structured data → shared state |
| Layer 2: Analyst Team | Fundamental, Sentiment, News, and Technical Analyst agents (4 parallel) | Generate specialized analysis reports from raw data | Structured reports → global state |
| Layer 3: Research Team | Bullish Researcher, Bearish Researcher, Research Manager | Debate and synthesize analyst reports into a prevailing market view | Multi-round natural language debate |
| Layer 4: Trader Agent | Single Trader agent with strategy-specific logic | Synthesize research output into a concrete trade proposal (ticker, direction, size, entry, stops, targets) | Structured trade proposal → state |
| Layer 5: Risk & Execution | Risk Management Team (3 sub-agents), Portfolio Manager, Human Checkpoint / Auto-Executor | Evaluate, adjust, approve/reject, and execute the trade proposal | Debate → structured risk report → execution |
| Attribute | Details |
| --- | --- |
| Purpose | Evaluate company/protocol fundamentals to assess intrinsic value, identify undervalued or overvalued assets, and detect financial red flags. |
| Inputs | Financial statements (P&L, balance sheet, cash flow), quarterly earnings reports, insider transaction filings, management commentary, peer comparison data. |
| Outputs | Structured Fundamental Analysis Report with valuation assessment, key ratio analysis, earnings quality score, and investment thesis. |
| LLM Tier | Deep-think model (GPT-5.2 / Claude 4 Opus) — complex reasoning required. |
| Framework | ReAct prompting with tool calls for financial data retrieval and ratio computation. |
| Attribute | Details |
| --- | --- |
| Purpose | Analyze social media posts, forum discussions, and public sentiment to gauge short-term market mood and detect shifts in crowd psychology. |
| Inputs | Reddit posts (r/IndianStreetBets, r/CryptoCurrency), X/Twitter posts, Telegram channels, Discord servers, news comment sections. |
| Outputs | Structured Sentiment Report with aggregated sentiment scores (-1 to +1), trending topics, notable opinion shifts, and fear/greed indicators. |
| Tools | Web search engine, Reddit API, X/Twitter API, Telegram scraper, sentiment scoring algorithms (VADER, FinBERT fine-tuned). |
| LLM Tier | Quick-think for data collection; Deep-think for nuanced sentiment interpretation. |
| Attribute | Details |
| --- | --- |
| Purpose | Analyze macro and micro news events that could influence market movements, government policy changes, regulatory actions, and geopolitical developments. |
| Inputs | News articles from configured API sources, government announcements, central bank communications, regulatory circulars. |
| Outputs | Structured News Impact Report with event classification (macro/micro/sector), impact assessment (positive/negative/neutral), affected instruments, and urgency level. |
| Architecture | Pluggable News Source Registry — the operator provides custom API endpoints, authentication credentials, and parsing rules. The agent dynamically loads configured sources. |
| LLM Tier | Deep-think model for impact analysis and cross-referencing events with market data. |
| Category | Sources | Data Type |
| --- | --- | --- |
| Global Macro | Bloomberg, Reuters, Yahoo Finance | Economic indicators, Fed/RBI policy, geopolitical events |
| Indian Markets | Economic Times, Livemint, CNBC-TV18, Business Standard | Corporate earnings, sector news, market commentary |
| Regulatory (India) | RBI announcements, SEBI circulars, NSE notices | Policy changes, margin requirements, ban lists |
| Crypto Industry | CoinDesk, The Block, Decrypt | Protocol updates, regulatory actions, exchange news |
| DeFi/On-chain | DefiLlama alerts, Rekt News, DeFi Pulse | TVL changes, exploits, governance proposals |
| Attribute | Details |
| --- | --- |
| Purpose | Calculate and interpret technical indicators, detect chart patterns, and forecast price movements to optimize entry/exit timing. |
| Inputs | OHLCV (Open, High, Low, Close, Volume) data at multiple timeframes (1m, 5m, 15m, 1h, 4h, 1D, 1W). |
| Outputs | Structured Technical Analysis Report with indicator signals, pattern detections, support/resistance levels, and confluence score. |
| Tools | Code execution environment for indicator calculation (TA-Lib, pandas-ta), pattern recognition algorithms, charting tools. |
| LLM Tier | Quick-think for indicator computation; Deep-think for pattern interpretation and multi-timeframe analysis. |
| Category | Indicators |
| --- | --- |
| Trend | MACD, EMA (9/21/50/200), SMA, ADX, Parabolic SAR, Ichimoku Cloud, Supertrend |
| Momentum | RSI, Stochastic RSI, Williams %R, CCI, ROC, MFI, TRIX |
| Volatility | Bollinger Bands, ATR, Keltner Channels, Donchian Channels, VIX (India VIX) |
| Volume | OBV, VWAP, Chaikin Money Flow, Accumulation/Distribution, Volume Profile |
| Custom | Market structure (higher highs/lower lows), pivot points, Fibonacci retracements, Camarilla levels |
| Attribute | Details |
| --- | --- |
| Purpose | Advocate for long/buy positions by constructing evidence-based arguments from all four analyst reports, highlighting growth potential and favorable market conditions. |
| Inputs | Fundamental Analysis Report, Sentiment Report, News Impact Report, Technical Analysis Report. |
| Outputs | Structured bullish thesis with supporting evidence, price targets, catalyst timeline, and conviction level (1–10). |
| Debate Format | Engages in n-round debate (configurable, default: 2 rounds) with the Bearish Researcher. The Research Manager facilitates, scores arguments, and declares the prevailing view. |
| LLM Tier | Deep-think model — requires strong argumentation, evidence synthesis, and counter-argument skills. |
| Attribute | Details |
| --- | --- |
| Purpose | Highlight risks, advocate caution, and construct evidence-based arguments against taking positions. Acts as the devil's advocate in the research process. |
| Inputs | Same four analyst reports as the Bullish Researcher. |
| Outputs | Structured bearish thesis with risk factors, downside scenarios, potential catalysts for decline, and risk severity score (1–10). |
| Debate Role | Directly counters Bullish Researcher arguments with evidence. Identifies overlooked risks, challenges assumptions, and stress-tests the bullish case. |
| LLM Tier | Deep-think model — critical thinking and risk identification are paramount. |
| Attribute | Details |
| --- | --- |
| Purpose | Make the final BUY/SELL/HOLD decision by synthesizing the Research Team's debate outcome with all analyst reports. Produce a complete, executable trade proposal. |
| Inputs | Research Synthesis Report, all four analyst reports, current portfolio state, market microstructure data (bid-ask spread, depth, liquidity). |
| Outputs | Structured Trade Proposal: Ticker/pair, direction (long/short), position size, entry price/range, stop-loss, target(s), time horizon, confidence score. |
| LLM Tier | Deep-think model for decision synthesis; quick-think for market microstructure lookups. |
| Sub-Agent | Perspective | Key Focus Areas |
| --- | --- | --- |
| Aggressive Debater | High risk/reward | Argues for larger position sizes, wider stops, higher leverage when conviction is high. Highlights opportunity cost of being too conservative. |
| Neutral Debater | Balanced view | Evaluates risk/reward ratio objectively. Suggests moderate position sizing. Considers portfolio-level diversification. |
| Conservative Debater | Capital preservation | Advocates smaller positions, tighter stops, hedging overlays. Flags tail risks, correlation dangers, and liquidity concerns. |
| Attribute | Details |
| --- | --- |
| Purpose | Final approval or rejection of trades. Enforces portfolio-level constraints that individual trade analysis might miss. |
| Inputs | Risk-Adjusted Trade Plan, current portfolio holdings, open orders, margin status, daily P&L, historical performance. |
| Checks | Concentration risk (max 20% in one position), sector correlation, total margin usage (< 60% of available), daily loss limit status, open position count. |
| Phase 1 Output | Forwards approved trade proposal to the Human Checkpoint Dashboard with full reasoning chain. |
| Phase 2 Output | Auto-executes via broker API (Zerodha Kite or CCXT) with confirmation logging. |
| Channel | Use Case | Latency Target |
| --- | --- | --- |
| Telegram Bot | Primary notification for trade proposals, urgent alerts, daily summaries | < 2 seconds |
| Email (SMTP) | Daily performance reports, weekly analytics digest, system health alerts | < 30 seconds |
| Push Notifications | Critical alerts (circuit breaker triggered, system error, margin call) | < 1 second |
| Dashboard Websocket | Real-time updates on agent progress, trade status, portfolio changes | < 500ms |
| Market | API / SDK | Key Capabilities | Authentication |
| --- | --- | --- | --- |
| NSE/BSE | Zerodha Kite Connect API (pykiteconnect) | Order placement (market, limit, SL, SL-M), position tracking, holdings, margin data, historical OHLCV, live streaming (Kite Ticker websocket) | OAuth2 — daily access token refresh required |
| Crypto CEX | CCXT (unified Python library) | Order management across 100+ exchanges (Binance, Bybit, OKX), position tracking, balance queries, OHLCV data, websocket streams | API key + secret per exchange |
| Crypto DEX (Hyperliquid) | hyperliquid-python-sdk via CCXT | Perpetual futures trading (up to 50x leverage), limit/market/stop orders, position management, no custody risk | Wallet address + API wallet private key |
| Crypto DEX (Uniswap/Aster) | Web3.py + Uniswap SDK | Spot token swaps, liquidity provision, price quotes, gas estimation | Ethereum wallet private key (hardware wallet recommended) |
| Safety Mechanism | Trigger Condition | Action |
| --- | --- | --- |
| Daily Loss Limit | Total realized + unrealized loss exceeds 3% of portfolio | Halt all new trades, close all intraday positions, alert operator |
| Max Drawdown Circuit Breaker | Portfolio drawdown from peak exceeds 10% | Full system shutdown, close all positions, enter cash-only mode |
| Position Size Limit | Any single position exceeds 20% of portfolio | Reject the trade, alert operator |
| Margin Warning | Used margin exceeds 60% of available | Reduce position sizes, halt new margin trades |
| API Error Rate | Broker API error rate exceeds 5% in 5-minute window | Pause trading, switch to manual mode, alert operator |
| LLM Hallucination Detection | Agent output fails structured validation (missing fields, impossible values) | Reject decision cycle, retry with different model, alert operator |
| Market Hours Enforcement | Trade attempted outside market hours (NSE 09:15–15:30 IST) | Queue for next session or reject if time-sensitive |
| Expiry Day Rules | Options expiry day (Thursday for weekly, last Thursday for monthly) | Apply tighter stops, reduce position sizes, no new naked positions |
| Kill Switch | Manual activation by operator (Telegram command /kill) | Immediately cancel all open orders, close all positions, halt system |
| Data Source | Protocol | Data Type | Refresh Rate |
| --- | --- | --- | --- |
| Zerodha Kite Ticker | WebSocket | NSE/BSE live ticks (LTP, depth, OI) | Real-time (tick-by-tick) |
| NSE API | HTTPS REST | Option chain data, indices, FII/DII data | Every 30 seconds |
| Binance/Bybit | WebSocket (via CCXT) | Crypto OHLCV, orderbook, trades, funding rates | Real-time (100ms) |
| Hyperliquid | WebSocket (via SDK) | Perpetual prices, positions, liquidations | Real-time (sub-second) |
| Alpha Vantage | REST API | Global market data, forex, crypto OHLCV | 1-minute intervals |
| yfinance | REST (unofficial) | Historical OHLCV, fundamentals, earnings | On-demand / daily batch |
| Layer | Technology | Purpose |
| --- | --- | --- |
| Language | Python 3.13 | Core application, all agent logic, data processing |
| Agent Orchestration | LangGraph | Directed graph-based agent workflow, state management, parallel execution |
| LLM Providers | OpenAI (GPT-5.x), Anthropic (Claude 4.x), Google (Gemini 3.x), xAI (Grok), Ollama (local) | Configurable per agent — deep-think vs. quick-think model selection |
| Market Data (India) | Zerodha Kite Connect, NSE Python lib, yfinance | Live ticks, OHLCV, option chains, fundamentals for Indian markets |
| Market Data (Global) | Alpha Vantage API | Global equities, forex, crypto data (original TradingAgents source) |
| Market Data (Crypto) | CCXT, Hyperliquid SDK, CoinGecko API | Multi-exchange crypto data, DEX integration, market cap/volume data |
| Database (Relational) | PostgreSQL 16 | Trade logs, agent decisions, audit trail, configuration |
| Database (Time-Series) | TimescaleDB | OHLCV hypertables, tick data, indicator values |
| Cache / State | Redis 7 | Live prices, session tokens, inter-agent state, rate limiting |
| Message Queue | Redis Streams (initially), RabbitMQ (at scale) | Asynchronous agent communication, event-driven data pipeline |
| Broker (India) | Zerodha Kite Connect API (pykiteconnect) | Order execution, position tracking, margin data for NSE/BSE |
| Broker (Crypto CEX) | CCXT (Binance, Bybit, OKX connectors) | Unified crypto exchange trading, multi-venue support |
| Broker (Crypto DEX) | Hyperliquid Python SDK, Web3.py, Uniswap SDK | On-chain perpetuals, spot swaps, DeFi interactions |
| Frontend | React / Next.js (or Streamlit for MVP) | Human checkpoint dashboard, portfolio view, performance analytics |
| Backend API | FastAPI | REST + WebSocket API for dashboard, Telegram bot, external integrations |
| Monitoring | Grafana + Prometheus | SRE-grade observability — system metrics, agent metrics, trade metrics |
| Notifications | Telegram Bot API, SMTP (email) | Trade proposals, alerts, daily summaries, system health |
| Containerization | Docker + Docker Compose (Phase 1–3), Kubernetes (Phase 5) | Reproducible environments, scaling, service isolation |
| CI/CD | GitHub Actions | Automated testing, linting, deployment pipelines |
| Backtesting | Custom engine (Python) + vectorbt | Historical simulation, walk-forward analysis, performance metrics |
| Week | Tasks | Deliverables |
| --- | --- | --- |
| 1 | Fork TradingAgents repo. Set up Python 3.13 environment (conda). Install all dependencies. Configure LLM provider API keys (OpenAI, Anthropic, Google). Run the existing system with default US stock tickers to validate the baseline. | Working local development environment. Successful propagate() call on NVDA. |
| 2 | Deploy PostgreSQL + TimescaleDB (Docker). Design database schema (trades, decisions, audit logs, OHLCV hypertables). Set up Redis. Begin Alpha Vantage and yfinance data ingestion. | Database running with schema. Historical data loading pipeline for US stocks (proof of concept). |
| 3 | Implement custom News Source Registry (pluggable architecture). Build NSE/BSE data connectors (Kite Connect for live data, NSE API for option chains). Set up crypto data feeds via CCXT. | News source registry with at least 2 demo sources. NSE option chain data flowing into TimescaleDB. Crypto OHLCV data loading. |
| Week | Tasks | Deliverables |
| --- | --- | --- |
| 4 | Customize Fundamental Analyst for Indian markets (Ind AS, NSE filings, promoter data) and crypto (on-chain metrics, TVL). Build and test agent with sample data. | Fundamental Analyst producing structured reports for Nifty 50 stocks and top 5 crypto tokens. |
| 5 | Customize Sentiment Analyst (Indian fintwit, MoneyControl, r/IndianStreetBets, CT). Customize News Analyst with pluggable source registry. Connect operator's custom news APIs. | Both agents producing reports. News source registry operational with operator's custom sources. |
| 6 | Customize Technical Analyst: Add options-specific analytics (Greeks, OI analysis, GEX, max pain, IV surface). Add crypto indicators (funding rates, liquidation levels, NVT). | Technical Analyst generating comprehensive reports with 60+ indicators plus options/crypto-specific metrics. |
| 7 | Build Bull/Bear Researcher debate engine. Configure Research Manager. Test multi-round debates with configurable rounds. | Research Team producing debate transcripts and synthesis reports. Debate quality validated on 10+ historical scenarios. |
| 8 | Build Trader Agent with options-specific logic (strike selection, strategy type). Build Risk Management Team (3 debaters). Integrate Portfolio Manager. End-to-end pipeline test. | Complete agent pipeline: Data → Analysts → Researchers → Trader → Risk Team → Portfolio Manager. Unit tests for each agent. |
| Week | Tasks | Deliverables |
| --- | --- | --- |
| 9–10 | Build web dashboard frontend (React/Next.js or Streamlit MVP). Trade proposal cards with reasoning chain. Approve/Reject/Modify workflow. FastAPI backend. | Functional dashboard showing agent analysis and trade proposals. Approval workflow working end-to-end. |
| 11 | Telegram bot for mobile notifications. Email daily summaries. Audit trail logging. Decision replay functionality. | Telegram bot sending trade proposals and receiving approve/reject commands. Audit log database populated. |
| 12 | Portfolio overview panel. Performance metrics display. Counterfactual tracking for rejected trades. Integration testing. | Complete Phase 1 dashboard. Counterfactual tracking operational. Full integration test with paper trades. |
| Week | Tasks | Deliverables |
| --- | --- | --- |
| 13–14 | Build backtesting engine: replay historical data through the agent pipeline. Walk-forward analysis with out-of-sample validation. Prevent look-ahead bias. | Backtesting engine producing trades for configurable date ranges. Walk-forward reports. |
| 15 | Performance metrics dashboard: Sharpe ratio, max drawdown, win rate, expectancy, profit factor, Calmar ratio. Compare against baselines (Buy & Hold, MACD, SMA, RSI). | Performance dashboard with all metrics. Baseline comparison charts. Identification of weak/strong market regimes. |
| 16 | Paper trading with live data (simulated execution, real-time agent pipeline, no real money). Run for 2 weeks minimum. Tune risk parameters and agent prompts. | 2+ weeks of paper trading results. Parameter tuning log. System stability report. |
| Week | Tasks | Deliverables |
| --- | --- | --- |
| 17–18 | Zerodha Kite Connect integration for NSE/BSE order execution. CCXT integration for crypto. Test with minimum lot sizes. Verify execution quality (slippage, fill rates). | Live trading operational for NSE options and crypto. Execution quality report. |
| 19 | Real-time position monitoring dashboard. Auto-stop-loss execution. Margin tracking. Expiry day rules implementation. | Position monitoring live. All safety checks operational. First 2 weeks of live P&L tracked. |
| 20 | Daily and weekly performance reports (auto-generated). Operator workflow optimization. Bug fixes and latency improvements. | Automated reporting. System operating smoothly with human oversight. 4+ weeks of live trading data. |
| Week | Tasks | Deliverables |
| --- | --- | --- |
| 21–22 | Implement configurable auto-approval rules (confidence > 8, risk/reward > 2:1, position size < 5% of portfolio). Circuit breakers and kill switches. Fallback to manual on anomalies. | Auto-approval engine with configurable rules. All circuit breakers tested and operational. |
| 23–24 | Grafana dashboards: agent performance (accuracy, latency, cost), trade performance (P&L, Sharpe, win rate), system health (API latency, error rates, data freshness). Prometheus alerting. | Full observability stack. Alerting rules for all critical conditions. SRE runbook for common incidents. |
| 25–26 | Drift detection (model performance degradation). Auto-rebalancing for portfolio optimization. Cost optimization (LLM spend tracking and model routing). Documentation and operational procedures. | Drift detection operational. Portfolio rebalancing logic. System documentation. Operational runbook. |
| Phase | Duration | Key Milestone | Exit Criteria |
| --- | --- | --- | --- |
| Phase 0: Foundation | Weeks 1–3 | Infrastructure ready, data flowing | All data sources connected, DB operational, baseline TradingAgents running |
| Phase 1: Core Agents | Weeks 4–8 | Full agent pipeline operational | All 9+ agents customized, end-to-end pipeline test passing |
| Phase 2: Dashboard | Weeks 9–12 | Human checkpoint operational | Dashboard live, Telegram bot working, audit trail logging |
| Phase 3: Backtesting | Weeks 13–16 | System validated on historical data | Sharpe > 1.5 in backtests, 2+ weeks paper trading successful |
| Phase 4: Live Trading | Weeks 17–20 | Real money, human oversight | 4+ weeks live trading, positive risk-adjusted returns |
| Phase 5: Automation | Weeks 21–26 | Fully automated with SRE observability | Auto-execution running, all circuit breakers tested, Grafana dashboards live |
| Category | Key Metrics | Collection Method | Dashboard |
| --- | --- | --- | --- |
| Agent Performance | Per-agent accuracy (% of correct signals), latency (seconds per analysis), token usage (input/output), cost per decision | Custom Prometheus metrics exported from agent pipeline | Grafana: Agent Performance |
| Trade Performance | Win rate, profit factor, Sharpe ratio, Sortino ratio, max drawdown, Calmar ratio, expectancy, average win/loss size | Calculated from trade log in PostgreSQL | Grafana: Trade Analytics |
| System Health | API response times (P50/P95/P99), error rates, data freshness (lag from source), queue depth, memory/CPU usage | Prometheus node exporter, custom application metrics | Grafana: System Health |
| Cost Tracking | LLM API spend (per provider, per agent, per day), data API costs, broker API costs, total operating cost per trade | Aggregated from API usage logs | Grafana: Cost Dashboard |
| Data Quality | Feed freshness (seconds since last update), completeness (% of expected fields present), anomaly count, cross-source price deviation | Custom validators in data pipeline | Grafana: Data Quality |
| Alert | Condition | Severity | Channel |
| --- | --- | --- | --- |
| Daily Loss Limit Hit | Realized + unrealized loss > 3% of portfolio | Critical | Telegram + Email + Dashboard |
| Drawdown Warning | Drawdown exceeds 7% (approaching 10% limit) | High | Telegram + Dashboard |
| Circuit Breaker Triggered | Any circuit breaker activates | Critical | Telegram + Email |
| API Errors Spiking | Broker API error rate > 5% in 5-minute window | High | Telegram + Dashboard |
| Data Feed Stale | Any data source > 5 minutes stale during market hours | Medium | Telegram + Dashboard |
| LLM Provider Down | Primary LLM fails 3 consecutive calls | High | Telegram + Email |
| Unusual Position | Position exceeds configured limits | High | Telegram + Dashboard |
| Margin Call Risk | Used margin > 55% of available | Medium | Telegram + Dashboard |
| # | Question | Impact | Decision Needed By |
| --- | --- | --- | --- |
| 1 | Which specific custom news API sources will be provided? Need API endpoints, authentication details, and response formats to build the pluggable source connectors. | Blocks News Analyst Agent development (Phase 1, Week 5) | Week 4 |
| 2 | Preferred LLM provider hierarchy: which provider/model for deep-think vs. quick-think? Cost vs. quality tradeoff acceptable? E.g., GPT-5.2 for decisions, GPT-5-mini for data tasks. | Affects per-decision cost and quality. Configuration needed for all agents. | Week 3 |
| 3 | Initial capital allocation: How much capital allocated to each market (NSE FNO vs. crypto CEX vs. crypto DEX)? This determines position sizing parameters. | Directly affects risk parameters, margin calculations, and testing scope. | Week 8 |
| 4 | Zerodha API subscription: Is the Kite Connect API subscription active? Annual fee is ₹2,000. Need API key and secret. | Blocks broker integration for Indian markets. | Week 3 |
| # | Question | Impact | Target Resolution |
| --- | --- | --- | --- |
| 5 | Risk tolerance parameters for the Risk Management Team: What's the acceptable max drawdown (proposed: 10%)? Daily loss limit (proposed: 3%)? These are configurable but need initial values. | Affects Risk Management Team calibration. | Phase 1 (Week 8) |
| 6 | Preferred crypto CEX broker: Binance, Bybit, OKX, or multiple? Each has different fee structures, leverage limits, and available instruments. | Affects CCXT connector configuration and testing. | Phase 4 (Week 17) |
| 7 | Whether to support US markets (stocks, options) in addition to Indian markets and crypto. The base TradingAgents framework already supports US equities. | Scope expansion. Could be added as Phase 6 if desired. | Post-Phase 5 |
| 8 | Preference for dashboard framework: React/Next.js (more polished, more development effort) vs. Streamlit (faster to build, less customizable). Both are viable. | Affects Phase 2 timeline. Streamlit MVP can be built in 2 weeks; React in 4. | Phase 2 (Week 9) |
| 9 | Local LLM fallback: Should Ollama with a local model (e.g., Llama 3.x) be configured as a fallback when cloud LLMs are unavailable? Requires GPU. | Resilience improvement. Optional enhancement. | Phase 5 |