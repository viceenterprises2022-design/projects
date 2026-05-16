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

---

## agentmemory — Long-Term Memory Layer

Project uses `@agentmemory/agentmemory` for cross-session, cross-agent persistence.

**Config:**
- **Daemon:** Runs on `:3111` (REST) and `:3113` (Viewer)
- **Settings:** `~/.agentmemory/.env` and `~/.agentmemory/preferences.json`
- **Features:** Graph extraction ENABLED (`GRAPH_EXTRACTION_ENABLED=true`), hybrid search (BM25 + Vector), temporal-graph recall.
- **Wired Agents:** Claude Code, Cursor, Gemini CLI, Codex.

**Commands:**
```bash
agentmemory status      # check health + memory count
agentmemory stop        # kill worker
npx @agentmemory/mcp    # start standalone MCP shim
```

---

## Repository Overview

Monorepo of independent projects: trading bots, financial analysis, AI agents, and design tooling.

| Project | Stack | Purpose |
|---------|-------|----------|
| `tradingview-mcp/` | Node.js (ESM) | MCP server bridging Claude to TradingView Desktop via CDP |
| `Alphaedge_Copy/` | Python (async) | Multi-platform copy trading: Hyperliquid, Binance Futures, Polymarket |
| `btcusdt-futures-bot/` | Python (async) | Paper-trading bot for Hyperliquid BTC perp — Donchian breakout strategy |
| `open-codesign/` | TypeScript, pnpm, Electron | Open-source AI design agent — prompt to prototype/slide/asset |
| `open-design/` | TypeScript/Node | Open-source Claude Design alternative — 13 coding CLIs, 31 skills, 72 design systems |
| `crypto-trending-oi/` | Python (async) | Intraday OI + multi-factor crypto scoring engine with SQLite |
| `daily_crypto_news/daily_market_report/` | Python, CrewAI | AI-generated daily market reports via multi-agent flows |
| `AlphaEdge_Ticker/` | Python (tkinter) | Live desktop ticker for crypto PERP (Hyperliquid) + NSE equities |
| `Alphaedge/` | JSX + docs | AlphaEdge platform design — UI components and architecture documents |
| `alphaedge-journal/` | Static HTML/CSS | Trading journal UI kits deployed via Vercel |

**Root-level artifacts**
- `DESIGN.md` — design tokens (palette, typography, spacing). All UI work must follow this.
- `graphify-out/` — AST knowledge graph. For architecture questions, read `graphify-out/GRAPH_REPORT.md` first. After modifying source files, run `graphify update .` to refresh.
- `mempalace.yaml` — memory palace mapping project dirs to named rooms for context loading.
- `.mcp.json` — claude-flow MCP server config (hierarchical-mesh, 15-agent max, hybrid memory).

---

## graphify Knowledge Graph

Before answering architecture or codebase questions, read `graphify-out/GRAPH_REPORT.md` for god nodes and community structure. If `graphify-out/wiki/index.md` exists, navigate it instead of reading raw files. After modifying source files in a session, run `graphify update .` to keep the graph current (AST-only, no API cost).

---

## UI / Styling Mandate

All UI work must follow `DESIGN.md`. Key tokens:
- **Background:** `#000000` | **Primary action:** `#10B981` | **Accent:** `#3B82F6`
- **Text:** `#FFFFFF` / `#94A3B8` muted | **Border:** `#1E293B`
- **Font:** `Inter` weight 510 for primary text | **Radius max:** 8px | **Spacing base:** 4px
- Layering: `#000000` → `#0F172A` → `#1E293B`
- No full-uppercase UI text, no gradients (except data viz), no shadows on dark elements.

---

## tradingview-mcp

**Commands**
```bash
cd tradingview-mcp
npm install
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
- `config/settings.py` — all tunable parameters (`dry_run` flag, position limits, alpha thresholds)
- `core/risk_manager.py` — unified SL/TP/trailing/drawdown engine; position sizing: `MIN(equity × max_position_pct, max_copy_size_usd)`
- `core/trader_selector.py` — alpha scoring (Sharpe 30%, ROI 20%, win rate 20%, drawdown 15%, consistency 10%, experience 5%)
- `bots/hyperliquid_bot.py` — WebSocket `userFills` subscription per tracked wallet (~50ms fill detection)
- `bots/binance_bot.py` — polls public leaderboard endpoint every 5s; mirrors via Binance Futures API
- `bots/polymarket_bot.py` — CLOB + Gamma API; consensus filter (2+ whale wallets on same market); no leverage
- `utils/notifier.py` — Telegram + Discord alerts
- `utils/dashboard.py` — console performance view

**Platform notes**
- Hyperliquid: uses `hyperliquid-python-sdk` with EIP-712 signed orders; use separate API wallet (no withdrawal rights)
- Binance: leaderboard endpoints are public but rate-limited — keep polling ≥5s intervals
- Polymarket: USDC on Polygon (Chain ID 137); binary outcomes; thin books → severe slippage on large orders

---

## btcusdt-futures-bot

**Commands**
```bash
cd btcusdt-futures-bot
pip install -r requirements.txt
cp .env.example .env
python main.py                     # paper trading only (no live path in V1)
```

**Architecture**

Paper-trading bot on Hyperliquid BTC perpetual 15m candles.

- **Strategy:** Donchian Channel breakout (20-candle lookback)
  - Long only if price > EMA(200); short only if price < EMA(200)
  - Volume filter: breakout candle volume > median of last 20 candles
  - Strong close: Long → close in top 25% of range; Short → close in bottom 25%
- SQLite for state persistence; Slack alerts for signals
- No live trading path in V1 — paper broker only

---

## open-codesign

**Commands**
```bash
cd open-codesign
pnpm i                             # install (pnpm only — never npm/yarn)
pnpm dev                           # start Electron app in dev mode
pnpm build                         # build all packages via Turborepo
pnpm test                          # Vitest unit tests
pnpm test:e2e                      # Playwright E2E
pnpm lint                          # Biome check
pnpm lint:fix                      # Biome check --write
pnpm typecheck                     # tsc --noEmit across all packages
pnpm smoke                         # smoke-test all configured LLM providers
pnpm changeset                     # create a changeset before publishing
```

**Architecture**

```
apps/desktop/          # Electron shell (main + renderer)
packages/
  core/                # Agent orchestration, prompts, design tools
  providers/           # pi integration and provider shims
  runtime/             # Sandbox renderer + preview runtime
  ui/                  # Shared app UI tokens and Radix/shadcn components
  artifacts/           # Artifact schemas and bundle formats
  exporters/           # PDF/PPTX/ZIP exporters (lazy-loaded)
  templates/           # Built-in starter templates
  shared/              # Shared types, utils, schemas
```

**Key constraints**
- BYOK only — no hosted API, proxied model, or telemetry by default
- Local-first: pi JSONL sessions + workspace filesystem; no new SQLite tables for sessions/designs
- All LLM calls go through `pi-ai`; never import `@anthropic-ai/sdk`, `openai`, etc. in app code
- State: Zustand only — no Redux/Recoil/MobX
- Animations: Tailwind transitions only — no framer-motion
- Node 22 LTS; pnpm 9; Turborepo; Biome for lint+format; Vitest + Playwright for tests
- Changesets for versioning — do not hand-edit `CHANGELOG.md`
- Do not use `console.*` in `main/`, `core/`, `providers/`, `exporters/`, or `shared/` — use the project logger

---

## open-design

**Commands**
```bash
cd open-design
# See open-design/README.md for full setup — it auto-detects coding CLIs on PATH
```

**Architecture**

Open-source alternative to Claude Design. Detects 13 coding-agent CLIs on `PATH` (Claude Code, Codex, Devin for Terminal, Cursor Agent, Gemini CLI, OpenCode, Qwen, GitHub Copilot CLI, Hermes, Kimi, Pi, Kiro, Mistral Vibe) and uses them as the design engine. Falls back to an OpenAI-compatible BYOK proxy when no CLI is found.

- 31 composable Skills drive the design pipeline
- 72 brand-grade Design Systems available as templates
- Local-first, web-deployable

---

## crypto-trending-oi

**Commands**
```bash
cd crypto-trending-oi
pip install -r requirements.txt
cp API-KEYS.env .env               # add CoinAPI, Glassnode, etc.
python main.py                     # print current factor scores + OI table
python daemon.py                   # run continuous polling loop (writes to SQLite)
```

**Architecture**

- `fetchers.py` — async fetchers for macro (DXY, VIX, M2), on-chain (ETF flows, MVRV-Z, stablecoin supply), and intraday (funding rate, OI) data
- `engine.py` — factor scoring engine; composites weighted signals into a [-1, +1] directional score
- `daemon.py` — scheduler loop; polls fetchers and writes rows to `crypto_intraday_oi.db` (SQLite)
- `main.py` — rich terminal display; reads latest DB row and renders factor table + driver callouts
- `config.py` — API keys, symbol lists, polling intervals
- `AlphaEdge_Crypto_Factor_Intelligence_Spec_v1.md` — full factor-model spec; read before editing signal weights

Score thresholds: ≥+0.4 → LEAN LONG, ≤−0.4 → LEAN SHORT, else CHOP/NEUTRAL.

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
# Or: ./launch_ubuntu.sh
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

---

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
