<!-- converted from AlphaEdge_AI_Stack_Optimizer.docx -->





# 1. Three-Tier Model Architecture
Route each task type to the most cost-effective model that can handle it. Never use a $15/1M output model where a $2.20/1M model delivers equal quality.



# 2. Agent Infrastructure Layer
## 2a. OpenCode — Terminal Coding Agent
Open-source, terminal-first coding agent supporting 75+ models. Decouples your editor from the LLM, runs in any shell, and supports split planner/executor routing in a single config file.
- Planner model (complex reasoning): Claude Sonnet 4.6 or Opus
- Executor model (mechanical edits, code writes): Kimi K2.6 or Haiku
- autoCompact: true — auto-summarises context before hitting window limit
- Plan mode previews all changes before touching files
- Persistent sessions — pick up where you left off across days
- 75 models via OpenRouter + direct Anthropic + Ollama local

## 2b. OpenRouter — Model Gateway
Single API key, 300+ models, automatic provider failover when rate limits hit.

- Auto-failover: Claude hits RL → OpenRouter instantly switches to Kimi K2.6 → DeepSeek V3.2
- Single billing dashboard across all providers
- Free tier models: Llama 3.3 70B, Gemma 3 — 20 req/min, 200/day each
- Reliability: ~99.5% uptime; known outages in Aug 2025 and Feb 2026 (35-50 min each)


# 3. Intelligent Task → Model Routing
Every token saved on a mechanical task is a token you can spend on something that actually requires Claude-level intelligence. Never use a flagship model for boilerplate.



# 4. Cost Comparison Matrix

Assumes ~50M tokens/month across AlphaEdge, Pinaka.ai, and Discord work. Mix: 30% Claude Sonnet (strategic) · 40% Kimi K2.6 (code/UI) · 20% Kimi K2 (scripts) · 10% free tier.


# 5. Zero-to-Running Setup Guide
Complete this once and your pipeline is permanently rate-limit-resistant.




OpenCode Config Snippet
{
"providers": {
"anthropic": { "apiKey": "sk-ant-YOUR_KEY" },
"openrouter": { "apiKey": "sk-or-YOUR_OR_KEY" }
},
"agents": {
"coder": { "model": "openrouter/moonshotai/kimi-k2.6", "maxTokens": 8192 },
"task":  { "model": "openrouter/moonshotai/kimi-k2.6", "maxTokens": 4096 },
"title": { "model": "openrouter/moonshotai/kimi-k2", "maxTokens": 80 }
},
"autoCompact": true
}


Claude Code Failover Config
{
"env": {
"ANTHROPIC_BASE_URL": "https://openrouter.ai/api/v1",
"ANTHROPIC_API_KEY": "sk-or-YOUR_OPENROUTER_KEY"
},
"model": "anthropic/claude-sonnet-4.6"
}



# 6. Automatic Failover Architecture
Your zero-wait pipeline. When Claude hits a rate limit, the chain below activates automatically via OpenRouter. You never see a wait timer again.



# 7. Key Principles & Rules of Thumb
## 7a. When to Use Claude Sonnet 4.6
- Any task requiring causal reasoning, macro interpretation, or nuanced judgment
- AlphaEdge architecture decisions and DCC-GARCH model design
- Investor materials: pitch decks, one-pagers, executive summaries
- Discord community prep: pre-market analysis, weekly signals, AMA content
- Pinaka.ai threat model design and security architecture
- Anything you would trust to a senior analyst or architect

## 7b. When to Use Kimi K2.6
- React/TypeScript component generation, Bloomberg terminal UI
- Multi-file code edits, long context (up to 256K) analysis
- Visual coding tasks — Kimi K2.6 is trained on multimodal visual coding
- Any agentic run that requires 50+ sequential tool calls
- Price-sensitive code generation where Claude quality is overkill

## 7c. OpenRouter BYOK Rules
- ALWAYS use BYOK mode for Claude — OpenRouter 100% markup otherwise
- Fund $20+ in OpenRouter credits as your Kimi/DeepSeek fallback pool
- Set Claude Code ANTHROPIC_BASE_URL to OpenRouter endpoint for auto-failover
- Monitor spending via OpenRouter dashboard — set usage alerts

## 7d. Context Management
- Enable autoCompact in OpenCode — auto-summarises before hitting context window
- Kimi K2.6's 256K window handles full AlphaEdge codebase in one session
- Cached tokens in Kimi reduce cost on repeated context (long sessions)
- Use OpenCode Plan mode to review before execution — avoids costly re-runs


# 8. Quick Reference Cheatsheet


| AI STACK OPTIMIZER
Token · Cost · Productivity Reference Guide
AlphaEdge  ·  Pinaka.ai  ·  April 2026 |
| --- |
|  | The Problem
Claude rate-limit timers are killing build momentum across AlphaEdge and Pinaka.ai. Single-provider dependency = maximum wait, maximum cost, minimum throughput. |
| --- | --- |
|  | The Solution
A tiered, multi-rail model mesh: keep Claude Sonnet 4.6 for strategic reasoning, route code execution and long agentic runs to Kimi K2.6 via OpenCode + OpenRouter with automatic failover. Zero wait. ~78% cost reduction. |
| --- | --- |
| Model | Specifications | Best Used For |
| --- | --- | --- |
| TIER 1 · FLAGSHIP
Claude Sonnet 4.6
Direct Anthropic API | Context  1,000K tokens
Input  $3.00 / 1M
Output  $15.00 / 1M
Speed  Fast | AlphaEdge architecture, Pinaka.ai security logic, Discord prep, complex reasoning, investor materials |
| TIER 2 · WORKHORSE
Kimi K2.6
Kimi API / OpenRouter | Context  256K tokens
Input  $0.95 / 1M
Output  $4.00 / 1M
Speed  112 t/s (fastest) | UI/UX codegen, long-context analysis, agentic swarms, multi-file edits, React components |
| TIER 2B · REASONING
Kimi K2 Thinking
OpenRouter | Context  256K tokens
Input  $0.60 / 1M
Output  $2.50 / 1M
Speed  39 t/s | Long agentic runs 200+ tool calls, autonomous research loops, multi-session persistence |
| TIER 3 · ECONOMY
Kimi K2 / DeepSeek V3.2
OpenRouter | Context  128K tokens
Input  $0.55 / 1M
Output  $2.20 / 1M
Speed  34 t/s | Boilerplate, refactors, data transforms, market data scripts, cron jobs, test generation |
| TIER 4 · FREE
Llama 3.3 70B
OpenRouter free tier | Context  128K tokens
Input  $0.00
Output  $0.00
Speed  Rate limited | Prototyping, simple Q&A, formatting tasks, docs, low-stakes script generation |
|  | CRITICAL: BYOK Mode Required
OpenRouter charges a 100% markup on Claude models ($6/M input vs. $3/M directly from Anthropic). You must use Bring Your Own Key (BYOK) mode — point your own Anthropic API key through OpenRouter. This eliminates the markup entirely while retaining auto-failover to Kimi/DeepSeek when Claude rate-limits. |
| --- | --- |
| Task | Model | Provider / Cost | vs All-Claude |
| --- | --- | --- | --- |
| AlphaEdge Architecture
System design, DCC-GARCH logic, causal chains | Claude Sonnet 4.6
System design, DCC-GARCH logic, causal chains | Direct API · $3/$15
System design, DCC-GARCH logic, causal chains | Baseline
System design, DCC-GARCH logic, causal chains |
| Discord + Macro Prep
Pre-market, Sunday planning, trade signals | Claude Sonnet 4.6
Pre-market, Sunday planning, trade signals | Direct API · $3/$15
Pre-market, Sunday planning, trade signals | Baseline
Pre-market, Sunday planning, trade signals |
| Investor Materials
Pitch decks, executive summaries, Q&A | Claude Sonnet 4.6
Pitch decks, executive summaries, Q&A | Direct API · $3/$15
Pitch decks, executive summaries, Q&A | Baseline
Pitch decks, executive summaries, Q&A |
| AlphaEdge Bloomberg UI
React components, terminal dark theme, JSX | Kimi K2.6
React components, terminal dark theme, JSX | OpenRouter · $0.95/$4.00
React components, terminal dark theme, JSX | Save ~73%
React components, terminal dark theme, JSX |
| Pinaka.ai Security Code
Agentic security, Go/Rust, threat modeling | Kimi K2.6
Agentic security, Go/Rust, threat modeling | OpenCode · $0.95/$4.00
Agentic security, Go/Rust, threat modeling | Save ~73%
Agentic security, Go/Rust, threat modeling |
| Long Agentic Runs
200+ tool calls, autonomous research loops | Kimi K2 Thinking
200+ tool calls, autonomous research loops | OpenRouter · $0.60/$2.50
200+ tool calls, autonomous research loops | Save ~80% vs Opus
200+ tool calls, autonomous research loops |
| Market Data Scripts
yfinance, Hyperliquid, CCXT, crons, FastAPI | Kimi K2 / DeepSeek
yfinance, Hyperliquid, CCXT, crons, FastAPI | OpenRouter · $0.55/$2.20
yfinance, Hyperliquid, CCXT, crons, FastAPI | Save ~83%
yfinance, Hyperliquid, CCXT, crons, FastAPI |
| Boilerplate / Refactor
Test gen, formatting, docs, minor edits | Llama 3.3 70B (free)
Test gen, formatting, docs, minor edits | OpenRouter free tier
Test gen, formatting, docs, minor edits | ~100% free
Test gen, formatting, docs, minor edits |
| Model | Context | $/1M Input | $/1M Output | vs Claude |
| --- | --- | --- | --- | --- |
| Claude Sonnet 4.6 | 1,000K | $3.00 | $15.00 | Baseline |
| Kimi K2.6 | 256K | $0.95 | $4.00 | Save 73% |
| Kimi K2 Thinking | 256K | $0.60 | $2.50 | Save 83% |
| Kimi K2 (base) | 128K | $0.55 | $2.20 | Save 85% |
| DeepSeek V3.2 | 128K | ~$0.27 | ~$1.10 | Save 93% |
| Claude Haiku 4.5 | 200K | $0.80 | $4.00 | Save 73% |
| Llama 3.3 70B | 128K | $0.00 | $0.00 | 100% Free |
| ALL-CLAUDE COST
~$400 / month
Estimated · heavy agentic usage | TIERED STACK COST
~$90 / month
Same output quality | NET SAVING
~78%
+ Zero wait time |
| --- | --- | --- |
| STEP 1 · INSTALL OPENCODE
Install the terminal agent
npm install -g opencode-ai
Verify: opencode --version · Launch: run opencode inside any project directory. Also available as desktop app and VS Code extension. |
| --- |
| STEP 2 · OPENROUTER BYOK
Bring your own Anthropic key
openrouter.ai → Keys → Create · BYOK Panel: paste Anthropic key
This eliminates the 100% Claude markup on OpenRouter. Fund $20 minimum in OpenRouter credits as fallback pool for Kimi/DeepSeek when Claude hits rate limits. |
| --- |
| STEP 3 · OPENCODE CONFIG
Set split planner/executor routing
~/.opencode/config.json  →  see snippet below
Set planner to Sonnet 4.6, executor to Kimi K2.6. This gives you Opus-quality planning at Kimi prices for mechanical execution. autoCompact keeps long sessions alive. |
| --- |
| STEP 4 · CLAUDE CODE FAILOVER
Route Claude Code through OpenRouter
~/.claude/settings.json  →  add env vars below
Pointing Claude Code at OpenRouter gives you automatic failover when Anthropic rate-limits you. Your sessions continue on Kimi K2.6 without interruption. |
| --- |
| STEP 5 · KIMI DIRECT API (OPTIONAL)
Lowest latency for K2.6
platform.moonshot.ai → API Keys → Create
Direct Kimi API bypasses OpenRouter for maximum throughput at 112 t/s. Use for time-sensitive AlphaEdge data pipelines. Stick to OpenRouter for everything else (simpler unified billing). |
| --- |
| Priority | Model | Trigger | Cost |
| --- | --- | --- | --- |
| 1st | Claude Sonnet 4.6 (Direct BYOK) | Normal operation | $3 / $15 |
| 2nd | Claude Sonnet 4.6 (OpenRouter BYOK) | Direct API slow/down | $3 / $15 |
| 3rd | Kimi K2.6 (OpenRouter) | Claude rate-limited | $0.95 / $4 |
| 4th | DeepSeek V3.2 (OpenRouter) | Kimi unavailable | ~$0.27 / $1.10 |
| 5th | Llama 3.3 70B (OpenRouter free) | Cost emergency / testing | $0 / $0 |
| Useful Links | Key Commands |
| --- | --- |
| opencode.ai/docs
openrouter.ai/docs
platform.moonshot.ai
artificialanalysis.ai/models/kimi-k2-6 | npm install -g opencode-ai
opencode /connect  →  search OpenRouter
opencode /models   →  select model
opencode /plan     →  review before build |
|  | The goal
You stop waiting for timers the day you stop being single-threaded on one provider. Use Claude Sonnet 4.6 where judgment matters. Use Kimi everywhere else. Let OpenRouter handle the failover automatically. |
| --- | --- |