# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communication Style

Always use **caveman ultra** mode. Invoke `/caveman ultra` at session start automatically. Never revert unless user says "stop caveman" or "normal mode".

---

## Agent Harness — everything-claude-code

Installed via `affaan-m/everything-claude-code` (full profile). Source cloned at `/tmp/everything-claude-code`.

**What's installed** (`~/.claude/`):
| Component | Count | Path |
|-----------|-------|------|
| Agents | 53 | `~/.claude/agents/` |
| Skills | 174 | `~/.claude/skills/` |
| Commands | 79 | `~/.claude/commands/` |
| Rules | 15 langs | `~/.claude/rules/` |
| Hooks runtime | 20+ | auto-loaded |

**Key workflows:**
```
/plan "task"        # research-first planning
/tdd                # TDD workflow
/code-review        # code review
/build-fix          # fix broken builds
/deep-research      # multi-step research
/prp-plan           # product requirements + plan
/multi-plan         # multi-model planning (needs ccg-workflow runtime)
```

**To update:** `cd /tmp/everything-claude-code && git pull && node scripts/install-apply.js --profile full`

**Install state:** `~/.claude/ecc/install-state.json`

## Repository Overview

This is a monorepo of several independent projects, primarily focused on trading, financial analysis, and AI agents. The main active codebases are:

| Project | Stack | Purpose |
|---------|-------|---------|
| `tradingview-mcp/` | Node.js (ESM) | MCP server bridging Claude to TradingView Desktop via CDP |
| `Alphaedge_Copy/` | Python (async) | Multi-platform copy trading: Hyperliquid, Binance Futures, Polymarket |
| `daily_crypto_news/daily_market_report/` | Python, CrewAI | AI-generated daily market reports via multi-agent flows |
| `AlphaEdge_Ticker/` | Python (tkinter) | Live desktop ticker for crypto PERP (Hyperliquid) + NSE equities |
| `Alphaedge/` | JSX + docs | AlphaEdge platform design — UI components and architecture documents |

---

## tradingview-mcp

**Commands**
```bash
cd tradingview-mcp
npm install                        # install dependencies
npm start                          # run MCP server (stdio transport)
npm test                           # run all tests (requires TradingView on :9222)
npm run test:unit                  # Pine analysis + CLI tests only (no TradingView needed)
npm run test:e2e                   # e2e tests (requires TradingView)
node src/cli/index.js <command>    # run tv CLI directly
npm link                           # install `tv` globally
```

**Architecture**

```
Claude Code  ←→  MCP Server (stdio)  ←→  CDP (localhost:9222)  ←→  TradingView Desktop (Electron)
```

- `src/server.js` — MCP entry point; registers all 14 tool groups via `register*Tools(server)`
- `src/connection.js` — CDP singleton with auto-reconnect; exports `evaluate()`, `evaluateAsync()`, `safeString()`, `requireFinite()`; all tool modules go through this
- `src/tools/` — one file per domain (chart, pine, data, replay, drawing, etc.)
- `src/core/` — same modules re-exported for programmatic use outside MCP
- `src/cli/` — `tv` CLI; `router.js` maps subcommands → core functions; `commands/` has one file per command group
- `CLAUDE.md` inside this project has a full tool decision tree — consult it when deciding which tool to use

**Key conventions**
- All tools return `{ success: true/false, ... }`
- CDP expressions use `safeString()` / `requireFinite()` for injection safety
- Entity IDs from `chart_get_state` are session-scoped — never persist across sessions
- Indicators must be **visible** on chart for pine graphics tools (`data_get_pine_*`) to work
- Full indicator names required for `chart_manage_indicator` (e.g. `"Relative Strength Index"` not `"RSI"`)

---

## Alphaedge_Copy

**Commands**
```bash
cd Alphaedge_Copy
pip install -r requirements.txt
cp .env.example .env               # add exchange keys

python main.py                     # run all bots (dry run by default)
python main.py --bot hl            # Hyperliquid only
python main.py --bot bn            # Binance Futures only
python main.py --bot poly          # Polymarket only
python main.py --dashboard         # performance view
python main.py --live --bot hl     # go live (after 2-week dry-run validation)
```

**Architecture**

- `main.py` — async orchestrator; starts all bot coroutines
- `settings.py` — all tunable parameters (dry_run flag, position limits, alpha thresholds)
- `risk_manager.py` / `risk_manager_v2/v3.py` — unified SL/TP/trailing/drawdown engine; position sizing formula: `MIN(equity × max_position_pct, max_copy_size_usd)`
- `trader_selector.py` — alpha scoring (Sharpe 30%, ROI 20%, win rate 20%, drawdown 15%, consistency 10%, experience 5%)
- `hyperliquid_bot.py` — WebSocket `userFills` subscription per tracked wallet (~50ms fill detection)
- `binance_bot.py` — polls public leaderboard endpoint every 5s; mirrors via Binance Futures API
- `polymarket_bot.py` — CLOB + Gamma API; consensus filter (2+ whale wallets on same market); no leverage
- `notifier.py` — Telegram + Discord alerts
- `dashboard.py` — console performance view

**Platform notes**
- Hyperliquid: uses `hyperliquid-python-sdk` with EIP-712 signed orders; use separate API wallet (no withdrawal rights)
- Binance: leaderboard endpoints are public but rate-limited — keep polling ≥5s intervals
- Polymarket: USDC on Polygon (Chain ID 137); binary outcomes; thin books → severe slippage on large orders

---

## daily_crypto_news/daily_market_report

**Commands**
```bash
cd daily_crypto_news/daily_market_report
uv sync                            # install dependencies
cp .env.example .env               # add OPENAI_API_KEY (or ANTHROPIC_API_KEY)

crewai run                         # run the flow
daily-market-report                # same via installed script
uv run python -c "import crewai; print(crewai.__version__)"  # check version
crewai test -n 2                   # test crew
crewai reset-memories -a           # reset all memories
crewai flow plot                   # visualize flow as HTML
```

**Architecture**

CrewAI Flow (`[tool.crewai] type = "flow"`) with a single `ContentCrew`:

```
main.py (Flow entry: kickoff / cli / run_with_trigger)
  └── crews/content_crew/
        ├── config/agents.yaml      # agent role/goal/backstory
        ├── config/tasks.yaml       # task descriptions + expected outputs
        ├── config/tasks_lite.yaml  # lighter variant
        └── content_crew.py         # @CrewBase class
  └── report/
        ├── template.html           # Jinja2 HTML template
        ├── render.py               # fills template with snapshot data
        ├── export.py               # WeasyPrint PDF + Playwright PNG export
        └── sparkline.py            # matplotlib sparklines
  └── models/snapshot.py           # Pydantic snapshot data model
  └── config/assets.yaml           # watched assets / symbols config
```

Output lands in `output_full/` as `.pdf`, `.html`, `.png` with UTC timestamp filenames.

**CrewAI conventions** (always use `uv`, check installed version before writing CrewAI code)
- LLM references: use `crewai.LLM` or string shorthand `"anthropic/claude-sonnet-4-20250514"` — never `ChatOpenAI()`
- Always add `# type: ignore[index]` on config dict access in `@CrewBase` classes
- Agent/task method names must match YAML keys exactly
- See `AGENTS.md` in this project for full CrewAI API reference

---

## AlphaEdge_Ticker

**Commands**
```bash
cd AlphaEdge_Ticker
pip install -r requirements.txt    # requests, yfinance
python alphaedge_ticker.py         # launch desktop ticker
# Or use platform launchers:
./launch_ubuntu.sh
```

**Architecture**

Single-file tkinter app. Config persisted to `~/.alphaedge_ticker.json`.
- Crypto prices: Hyperliquid REST API (`api.hyperliquid.xyz`)
- NSE prices: `yfinance` (optional — degrades gracefully if not installed)
- Scrolling banner rendered in a borderless, always-on-top `tk.Canvas` row

---

## Alphaedge (Design & Docs)

Contains architecture documents (`.docx`, `.md`, `.pdf`) and React/JSX components for the AlphaEdge AI platform:
- `emerging_markets_platform.jsx` — emerging markets dashboard UI
- `global_correlation_engine_ui.jsx` — correlation engine visualization
- `ButterflyEffectEngine*.html` — standalone butterfly effect simulations
- `DCC_GARCH_*` and `GLOBAL_CORRELATION_ENGINE_*` — technical specs for the quant engine

## Skill routing

When the user's request matches an available skill, ALWAYS invoke it using the Skill
tool as your FIRST action. Do NOT answer directly, do NOT use other tools first.
The skill has specialized workflows that produce better results than ad-hoc answers.

Key routing rules:
- Product ideas, "is this worth building", brainstorming → invoke office-hours
- Bugs, errors, "why is this broken", 500 errors → invoke investigate
- Ship, deploy, push, create PR → invoke ship
- QA, test the site, find bugs → invoke qa
- Code review, check my diff → invoke review
- Update docs after shipping → invoke document-release
- Weekly retro → invoke retro
- Design system, brand → invoke design-consultation
- Visual audit, design polish → invoke design-review
- Architecture review → invoke plan-eng-review
- Save progress, checkpoint, resume → invoke checkpoint
- Code quality, health check → invoke health

## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)

<!-- autoskills:start -->

Summary generated by `autoskills`. Check the full files inside `.claude/skills`.

## Accessibility (a11y)

Audit and improve web accessibility following WCAG 2.2 guidelines. Use when asked to "improve accessibility", "a11y audit", "WCAG compliance", "screen reader support", "keyboard navigation", or "make accessible".

- `.claude/skills/accessibility/SKILL.md`
- `.claude/skills/accessibility/references/A11Y-PATTERNS.md`: Practical, copy-paste-ready patterns for common accessibility requirements. Each pattern is self-contained and linked from the main [SKILL.md](../SKILL.md).
- `.claude/skills/accessibility/references/WCAG.md`

## AgentDB Advanced Features

Master advanced AgentDB features including QUIC synchronization, multi-database management, custom distance metrics, hybrid search, and distributed systems integration. Use when building distributed AI systems, multi-agent coordination, or advanced vector search applications.

- `.claude/skills/agentdb-advanced/SKILL.md`

## AgentDB Learning Plugins

Create and train AI learning plugins with AgentDB's 9 reinforcement learning algorithms. Includes Decision Transformer, Q-Learning, SARSA, Actor-Critic, and more. Use when building self-learning agents, implementing RL, or optimizing agent behavior through experience.

- `.claude/skills/agentdb-learning/SKILL.md`

## AgentDB Memory Patterns

Implement persistent memory patterns for AI agents using AgentDB. Includes session memory, long-term storage, pattern learning, and context management. Use when building stateful agents, chat systems, or intelligent assistants.

- `.claude/skills/agentdb-memory-patterns/SKILL.md`

## AgentDB Performance Optimization

Optimize AgentDB performance with quantization (4-32x memory reduction), HNSW indexing (150x faster search), caching, and batch operations. Use when optimizing memory usage, improving search speed, or scaling to millions of vectors.

- `.claude/skills/agentdb-optimization/SKILL.md`

## AgentDB Vector Search

Implement semantic vector search with AgentDB for intelligent document retrieval, similarity matching, and context-aware querying. Use when building RAG systems, semantic search engines, or intelligent knowledge bases.

- `.claude/skills/agentdb-vector-search/SKILL.md`

## Browser Automation Skill

Web browser automation with AI-optimized snapshots for claude-flow agents

- `.claude/skills/browser/SKILL.md`

## Design Thinking

Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, artifacts, posters, or applications (examples include websites, landing pages, dashboards, React components, HTML/CSS layouts, or when styling/beaut...

- `.claude/skills/frontend-design/SKILL.md`

## GitHub Code Review Skill

Comprehensive GitHub code review with AI-powered swarm coordination

- `.claude/skills/github-code-review/SKILL.md`

## GitHub Multi-Repository Coordination Skill

|

- `.claude/skills/github-multi-repo/SKILL.md`

## GitHub Project Management

|

- `.claude/skills/github-project-management/SKILL.md`

## GitHub Release Management Skill

|

- `.claude/skills/github-release-management/SKILL.md`

## GitHub Workflow Automation Skill

|

- `.claude/skills/github-workflow-automation/SKILL.md`

## ADK Cheatsheet

>

- `.claude/skills/google-agents-cli-adk-code/SKILL.md`
- `.claude/skills/google-agents-cli-adk-code/references/adk-2.0.md`: Scaffolded projects pin `google-adk<2.0.0` — this must be updated before ADK 2.0 can install. Simply running `pip install --pre google-adk` or `uv add --prerelease=allow google-adk` will silently stay on 1.x.
- `.claude/skills/google-agents-cli-adk-code/references/adk-python.md`: Workflow agents provide deterministic control flow without LLM orchestration.

## ADK Deployment Guide

>

- `.claude/skills/google-agents-cli-deploy/SKILL.md`
- `.claude/skills/google-agents-cli-deploy/references/agent-runtime.md`: Agent Runtime uses **source-based deployment** — no Docker container or Dockerfile. Your agent code is packaged as a base64-encoded tarball and deployed directly to the managed Vertex AI service.
- `.claude/skills/google-agents-cli-deploy/references/batch-inference.md`: Invoke an ADK agent as a BigQuery Remote Function for batch inference over table rows. This requires a custom `POST /` endpoint since BQ cannot use URL paths.
- `.claude/skills/google-agents-cli-deploy/references/cicd-pipeline.md`: **Best for:** Production applications, teams requiring staging → production promotion.
- `.claude/skills/google-agents-cli-deploy/references/cloud-run.md`: Agents CLI scaffolds Cloud Run infrastructure in `deployment/terraform/service.tf`. Check that file for current resource limits, scaling configuration, concurrency, and session affinity settings.
- `.claude/skills/google-agents-cli-deploy/references/gke.md`: GKE uses **container-based deployment** to a managed GKE Autopilot cluster. Your agent is packaged as a Docker container (same Dockerfile as Cloud Run), pushed to Artifact Registry, and deployed via Terraform-managed Kubernetes resources.
- `.claude/skills/google-agents-cli-deploy/references/terraform-patterns.md`: **For CI/CD environments (staging/prod):**
- `.claude/skills/google-agents-cli-deploy/references/testing-deployed-agents.md`: The fastest way to test any deployed agent is the `run --url` command — it handles authentication, session creation, and streaming automatically:

## ADK Evaluation Guide

>

- `.claude/skills/google-agents-cli-eval/SKILL.md`
- `.claude/skills/google-agents-cli-eval/references/builtin-tools-eval.md`: **Key behavior:** - Custom tools (`save_preferences`, `save_feedback`) → appear as `function_call` in trajectory - `google_search` → NEVER appears in trajectory (happens inside the model)
- `.claude/skills/google-agents-cli-eval/references/criteria-guide.md`: Default when no config provided: `tool_trajectory_avg_score: 1.0` + `response_match_score: 0.8`
- `.claude/skills/google-agents-cli-eval/references/multimodal-eval.md`: For GCS-hosted files, use `file_data` instead:
- `.claude/skills/google-agents-cli-eval/references/user-simulation.md`: Use user simulation when fixed prompts are impractical — the agent may ask for information in different orders or respond in unexpected ways. Instead of hardcoding every user turn, define a **conversation scenario** and let an AI model generate realistic user responses dynamically.

## ADK Observability Guide

>

- `.claude/skills/google-agents-cli-observability/SKILL.md`
- `.claude/skills/google-agents-cli-observability/references/bigquery-agent-analytics.md`: An optional plugin that logs structured agent events directly to BigQuery via the Storage Write API. Enables:
- `.claude/skills/google-agents-cli-observability/references/cloud-trace-and-logging.md`: Always-on distributed tracing via `otel_to_cloud=True` in the FastAPI app. Tracks requests through LLM calls and tool executions with latency analysis and error visibility.

## Gemini Enterprise Registration

>

- `.claude/skills/google-agents-cli-publish/SKILL.md`

## ADK Project Scaffolding Guide

>

- `.claude/skills/google-agents-cli-scaffold/SKILL.md`
- `.claude/skills/google-agents-cli-scaffold/references/flags.md`: For all available flags, run `agents-cli scaffold create --help`.

## ADK Development Workflow & Guidelines

>

- `.claude/skills/google-agents-cli-workflow/SKILL.md`
- `.claude/skills/google-agents-cli-workflow/references/internals.md`: by the CLI — for debugging, customization, or edge cases — use these directly.

## Hooks Automation

Automated coordination, formatting, and learning from Claude Code operations using intelligent hooks with MCP integration. Includes pre/post task hooks, session management, Git integration, memory coordination, and neural pattern training for enhanced development workflows.

- `.claude/skills/hooks-automation/SKILL.md`

## Pair Programming

AI-assisted pair programming with multiple modes (driver/navigator/switch), real-time verification, quality monitoring, and comprehensive testing. Supports TDD, debugging, refactoring, and learning sessions. Features automatic role switching, continuous code review, security scanning, and perform...

- `.claude/skills/pair-programming/SKILL.md`

## ReasoningBank with AgentDB

Implement ReasoningBank adaptive learning with AgentDB's 150x faster vector database. Includes trajectory tracking, verdict judgment, memory distillation, and pattern recognition. Use when building self-learning agents, optimizing decision-making, or implementing experience replay systems.

- `.claude/skills/reasoningbank-agentdb/SKILL.md`

## ReasoningBank Intelligence

Implement adaptive learning with ReasoningBank for pattern recognition, strategy optimization, and continuous improvement. Use when building self-learning agents, optimizing workflows, or implementing meta-cognitive systems.

- `.claude/skills/reasoningbank-intelligence/SKILL.md`

## SEO optimization

Optimize for search engine visibility and ranking. Use when asked to "improve SEO", "optimize for search", "fix meta tags", "add structured data", "sitemap optimization", or "search engine optimization".

- `.claude/skills/seo/SKILL.md`

## Skill Builder

Create new Claude Code Skills with proper YAML frontmatter, progressive disclosure structure, and complete directory organization. Use when you need to build custom skills for specific workflows, generate skill templates, or understand the Claude Skills specification.

- `.claude/skills/skill-builder/SKILL.md`

## SPARC Methodology - Comprehensive Development Framework

|

- `.claude/skills/sparc-methodology/SKILL.md`

## Stream-Chain Skill

Stream-JSON chaining for multi-agent pipelines, data transformation, and sequential workflows

- `.claude/skills/stream-chain/SKILL.md`

## Advanced Swarm Orchestration

|

- `.claude/skills/swarm-advanced/SKILL.md`

## Swarm Orchestration

Orchestrate multi-agent swarms with agentic-flow for parallel task execution, dynamic topology, and intelligent coordination. Use when scaling beyond single agents, implementing complex workflows, or building distributed AI systems.

- `.claude/skills/swarm-orchestration/SKILL.md`

## V3 CLI Modernization

CLI modernization and hooks system enhancement for claude-flow v3. Implements interactive prompts, command decomposition, enhanced hooks integration, and intelligent workflow automation.

- `.claude/skills/v3-cli-modernization/SKILL.md`

## V3 Core Implementation

Core module implementation for claude-flow v3. Implements DDD domains, clean architecture patterns, dependency injection, and modular TypeScript codebase with comprehensive testing.

- `.claude/skills/v3-core-implementation/SKILL.md`

## V3 DDD Architecture

Domain-Driven Design architecture for claude-flow v3. Implements modular, bounded context architecture with clean separation of concerns and microkernel pattern.

- `.claude/skills/v3-ddd-architecture/SKILL.md`

## V3 Deep Integration

Deep agentic-flow@alpha integration implementing ADR-001. Eliminates 10,000+ duplicate lines by building claude-flow as specialized extension rather than parallel implementation.

- `.claude/skills/v3-integration-deep/SKILL.md`

## V3 MCP Optimization

MCP server optimization and transport layer enhancement for claude-flow v3. Implements connection pooling, load balancing, tool registry optimization, and performance monitoring for sub-100ms response times.

- `.claude/skills/v3-mcp-optimization/SKILL.md`

## V3 Memory Unification

Unify 6+ memory systems into AgentDB with HNSW indexing for 150x-12,500x search improvements. Implements ADR-006 (Unified Memory Service) and ADR-009 (Hybrid Memory Backend).

- `.claude/skills/v3-memory-unification/SKILL.md`

## V3 Performance Optimization

Achieve aggressive v3 performance targets: 2.49x-7.47x Flash Attention speedup, 150x-12,500x search improvements, 50-75% memory reduction. Comprehensive benchmarking and optimization suite.

- `.claude/skills/v3-performance-optimization/SKILL.md`

## V3 Security Overhaul

Complete security architecture overhaul for claude-flow v3. Addresses critical CVEs (CVE-1, CVE-2, CVE-3) and implements secure-by-default patterns. Use for security-first v3 implementation.

- `.claude/skills/v3-security-overhaul/SKILL.md`

## V3 Swarm Coordination

15-agent hierarchical mesh coordination for v3 implementation. Orchestrates parallel execution across security, core, and integration domains following 10 ADRs with 14-week timeline.

- `.claude/skills/v3-swarm-coordination/SKILL.md`

## Verification & Quality Assurance Skill

|

- `.claude/skills/verification-quality/SKILL.md`

<!-- autoskills:end -->
