# Graph Report - Polymarket_Claude  (2026-04-19)

## Corpus Check
- Corpus is ~13,547 words - fits in a single context window. You may not need a graph.

## Summary
- 283 nodes · 494 edges · 20 communities detected
- Extraction: 68% EXTRACTED · 32% INFERRED · 0% AMBIGUOUS · INFERRED: 160 edges (avg confidence: 0.8)
- Token cost: 7,500 input · 2,800 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Orchestration & DB|Orchestration & DB]]
- [[_COMMUNITY_Order Execution & Trading|Order Execution & Trading]]
- [[_COMMUNITY_HyperAgent Self-Improvement|HyperAgent Self-Improvement]]
- [[_COMMUNITY_Analysis & Reporting|Analysis & Reporting]]
- [[_COMMUNITY_Research Framework|Research Framework]]
- [[_COMMUNITY_DGM Archive & Search|DGM Archive & Search]]
- [[_COMMUNITY_Gamma Market Client|Gamma Market Client]]
- [[_COMMUNITY_Dependencies & Core Modules|Dependencies & Core Modules]]
- [[_COMMUNITY_Whale Wallet Scoring|Whale Wallet Scoring]]
- [[_COMMUNITY_CLOB Client|CLOB Client]]
- [[_COMMUNITY_Backtester & Config|Backtester & Config]]
- [[_COMMUNITY_Parallel Researcher|Parallel Researcher]]
- [[_COMMUNITY_aiohttp|aiohttp]]
- [[_COMMUNITY_aiofiles|aiofiles]]
- [[_COMMUNITY_tenacity|tenacity]]
- [[_COMMUNITY_Asymmetric Exits Research|Asymmetric Exits Research]]
- [[_COMMUNITY_Consensus by Category|Consensus by Category]]
- [[_COMMUNITY_Memory-Augmented Decisions|Memory-Augmented Decisions]]
- [[_COMMUNITY_Debate Quality Research|Debate Quality Research]]
- [[_COMMUNITY_Weather Resolution Data|Weather Resolution Data]]

## God Nodes (most connected - your core abstractions)
1. `TelegramBot` - 21 edges
2. `main()` - 17 edges
3. `main()` - 17 edges
4. `WhaleTracker` - 14 edges
5. `Database` - 14 edges
6. `TaskAgent` - 14 edges
7. `PolymarketClient` - 11 edges
8. `OrderManager` - 10 edges
9. `main.py (Bot Orchestrator)` - 10 edges
10. `GammaClient` - 9 edges

## Surprising Connections (you probably didn't know these)
- `main.py — Polybot orchestrator.  Starts all async loops concurrently:   - Whale` --uses--> `WhaleTracker`  [INFERRED]
  Polymarket_Claude/Claude/main.py → Polymarket_Claude/Claude/tracker.py
- `main()` --calls--> `exit()`  [INFERRED]
  Polymarket_Claude/Claude/main.py → Polymarket_Claude/Claude/config.py
- `main()` --calls--> `exit()`  [INFERRED]
  Polymarket_Claude/Claude/dgm_h_loop.py → Polymarket_Claude/Claude/config.py
- `main()` --calls--> `init_db()`  [INFERRED]
  Polymarket_Claude/Claude/main.py → Polymarket_Claude/Claude/db.py
- `git()` --calls--> `run()`  [INFERRED]
  Polymarket_Claude/Claude/dgm_h_loop.py → Polymarket_Claude/Claude/parallel_researcher.py

## Communities

### Community 0 - "Orchestration & DB"
Cohesion: 0.08
Nodes (6): init_db(), main(), main.py — Polybot orchestrator.  Starts all async loops concurrently:   - Whale, TelegramBot, CopySignal, WhaleTracker

### Community 1 - "Order Execution & Trading"
Cohesion: 0.08
Nodes (3): Database, OrderManager, PnLTracker

### Community 2 - "HyperAgent Self-Improvement"
Cohesion: 0.1
Nodes (8): Hyperagent, MetaAgent, PerformanceTracker, hyperagent.py — Polybot DGM-Hyperagent. Single editable program containing task_, Run full TradingAgents pipeline for one copy signal concurrently., Core DGM-H step. Returns (target_file, new_content)., Single editable program: task_agent + meta_agent unified., TaskAgent

### Community 3 - "Analysis & Reporting"
Cohesion: 0.1
Nodes (23): analyze(), fmt_telegram(), load(), print_report(), analysis.py — Read results.tsv and surface insights. Usage:     python analysis., send_tg(), api(), BotConfig (+15 more)

### Community 4 - "Research Framework"
Cohesion: 0.09
Nodes (24): Autoresearch (Loop) Paper, DGM-Hyperagent Framework, Rationale: DRY_RUN=true until 30+ days signal history, HyperAgents (Meta) Paper, Polybot, program.md (Human-Written Research Program), TradingAgents Paper (Roles), 6-Week Learning Plan (Python -> MCP -> CrewAI) (+16 more)

### Community 5 - "DGM Archive & Search"
Cohesion: 0.16
Nodes (14): Archive, decide(), git(), git_commit(), git_revert(), init_results(), log_result(), main() (+6 more)

### Community 6 - "Gamma Market Client"
Cohesion: 0.13
Nodes (3): GammaClient, RiskEngine, TradeDecision

### Community 7 - "Dependencies & Core Modules"
Cohesion: 0.1
Nodes (21): aiosqlite>=0.20.0, CopySignal, core/clob_client.py, core/config.py, core/gamma_client.py, core/subgraph_client.py, main.py (Bot Orchestrator), execution/order_manager.py (+13 more)

### Community 8 - "Whale Wallet Scoring"
Cohesion: 0.23
Nodes (4): _fetch_leaderboard(), whale/scorer.py — Vet a wallet before tracking it. Usage: python -m whale.scorer, score_wallet(), SubgraphClient

### Community 9 - "CLOB Client"
Cohesion: 0.22
Nodes (3): place_market_buy(), place_market_sell(), PolymarketClient

### Community 10 - "Backtester & Config"
Cohesion: 0.18
Nodes (11): analysis.py (results.tsv analyzer), anthropic>=0.40.0 SDK, config.yaml (Bot Config), dgm_h_loop.py (Self-Improvement Loop), evaluate.py (Fixed Backtester), Rationale: Goodhart's Law — never modify evaluate.py, hyperagent.py (DGM-H: TaskAgent + MetaAgent), strategy.yaml (Agent-Edited Config) (+3 more)

### Community 11 - "Parallel Researcher"
Cohesion: 1.0
Nodes (1): parallel_researcher.py

### Community 12 - "aiohttp"
Cohesion: 1.0
Nodes (1): aiohttp>=3.9.0

### Community 13 - "aiofiles"
Cohesion: 1.0
Nodes (1): aiofiles>=23.0.0

### Community 14 - "tenacity"
Cohesion: 1.0
Nodes (1): tenacity>=8.2.0

### Community 15 - "Asymmetric Exits Research"
Cohesion: 1.0
Nodes (1): Research Priority: Asymmetric Exits

### Community 16 - "Consensus by Category"
Cohesion: 1.0
Nodes (1): Research Priority: Consensus by Category

### Community 17 - "Memory-Augmented Decisions"
Cohesion: 1.0
Nodes (1): Research Priority: Memory-Augmented Decisions

### Community 18 - "Debate Quality Research"
Cohesion: 1.0
Nodes (1): Research Priority: Debate Quality

### Community 19 - "Weather Resolution Data"
Cohesion: 1.0
Nodes (1): NOAA/Wunderground Weather Resolution Data

## Knowledge Gaps
- **46 isolated node(s):** `parallel_researcher.py — Run N domain-specialist strategy variants concurrently.`, `dgm_h_loop.py — DGM-Hyperagents self-improvement loop for Polybot. Run overnight`, `whale/scorer.py — Vet a wallet before tracking it. Usage: python -m whale.scorer`, `hyperagent.py — Polybot DGM-Hyperagent. Single editable program containing task_`, `Run full TradingAgents pipeline for one copy signal concurrently.` (+41 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Parallel Researcher`** (1 nodes): `parallel_researcher.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `aiohttp`** (1 nodes): `aiohttp>=3.9.0`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `aiofiles`** (1 nodes): `aiofiles>=23.0.0`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `tenacity`** (1 nodes): `tenacity>=8.2.0`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Asymmetric Exits Research`** (1 nodes): `Research Priority: Asymmetric Exits`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Consensus by Category`** (1 nodes): `Research Priority: Consensus by Category`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Memory-Augmented Decisions`** (1 nodes): `Research Priority: Memory-Augmented Decisions`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Debate Quality Research`** (1 nodes): `Research Priority: Debate Quality`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Weather Resolution Data`** (1 nodes): `NOAA/Wunderground Weather Resolution Data`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `DGM Archive & Search` to `HyperAgent Self-Improvement`, `Analysis & Reporting`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Why does `main()` connect `Orchestration & DB` to `CLOB Client`, `Analysis & Reporting`, `Order Execution & Trading`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Why does `TelegramBot` connect `Orchestration & DB` to `Order Execution & Trading`, `Gamma Market Client`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `main()` (e.g. with `.get()` and `init_db()`) actually correct?**
  _`main()` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `main()` (e.g. with `.get()` and `exit()`) actually correct?**
  _`main()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `WhaleTracker` (e.g. with `main.py — Polybot orchestrator.  Starts all async loops concurrently:   - Whale` and `main()`) actually correct?**
  _`WhaleTracker` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `parallel_researcher.py — Run N domain-specialist strategy variants concurrently.`, `dgm_h_loop.py — DGM-Hyperagents self-improvement loop for Polybot. Run overnight`, `whale/scorer.py — Vet a wallet before tracking it. Usage: python -m whale.scorer` to the rest of the system?**
  _46 weakly-connected nodes found - possible documentation gaps or missing edges._