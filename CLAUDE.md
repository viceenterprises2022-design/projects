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
| `AlphaEdge_NSE_Ticker/` | Python (tkinter) | NSE options ticker — Nifty/BankNifty/Sensex option chain via Upstox API |
| `scripts/` | Python | Market intelligence scripts: 10-factor Indian index signals, crypto dashboard, AI event search |
| `Alphaedge/` | JSX + docs | AlphaEdge platform design — UI components and architecture documents |
| `alphaedge-journal/` | Next.js + Static HTML | Trading journal — Next.js at `/app`, static React at `/` and `/marketing` via Vercel |
| `crewai_testing/` | Python, CrewAI | CrewAI multi-agent sandbox/playground |
| `hello-reasoner/` | Python, AgentField | AgentField agent scaffold — `af init` template with echo + sentiment reasoners |

**Root-level artifacts**
- `DESIGN.md` — design tokens (palette, typography, spacing). All UI work must follow this.
- `graphify-out/` — AST knowledge graph. For architecture questions, read `graphify-out/GRAPH_REPORT.md` first. After modifying source files, run `graphify update .` to refresh.
- `mempalace.yaml` — memory palace mapping project dirs to named rooms for context loading.
- `.mcp.json` — claude-flow MCP server config (hierarchical-mesh, 15-agent max, hybrid memory).

---

## System Note — pip installs

This system runs managed Python 3.13 (no venv). All `pip install` commands require:
```bash
pip install <pkg> --break-system-packages
```

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

## scripts/

**Commands**
```bash
cd scripts
python3 -m pip install fastapi uvicorn[standard] requests rich --break-system-packages

# Indian index market intelligence
python3 collector.py               # fetch signals + write to alphaedge.db
python3 collector.py --loop --interval 5  # continuous 5-min polling
python3 api_server.py              # FastAPI dashboard on :8765
python3 market_analysis_v3.py     # rich terminal dashboard with auto-refresh
python3 run_analysis_headless.py  # headless stdout only
python3 report_and_send.py        # send analysis to Telegram
python3 options_cli.py            # live options chain: Nifty/BankNifty/Sensex (107-char layout)

# Crypto dashboard
python3 crypto_market_dashboard_v2.py   # BTC/ETH/SOL rich 3-column dashboard

# AI event search
EXA_API_KEY=<key> python3 exa_ai_search.py
```

**Architecture**

10-factor signal engine for Indian indices (NIFTY, SENSEX, BANKNIFTY). Signals: Trend, Dow Jones, India VIX, OI skew, VWAP, SuperTrend, RSI, DXY, Crude, PCR. Sum ≥6 → BUY, ≤4 → SELL, else NEUTRAL.

- `collector.py` — data fetch + signal calculation + SQLite writes to `alphaedge.db`
- `alphaedge_db.py` — SQLite schema + query helpers
- `api_server.py` — FastAPI REST on `:8765`; calls `db.init_db()` per request (safe, CREATE IF NOT EXISTS)
- `market_analysis_v3.py` — has background `oi_collector_thread()` writing to `intraday_oi.db` every minute; do not block main thread
- `options_cli.py` — live 5s-polling terminal view of ATM ±300 strikes for all three indices; SQLite daily reset
- `crypto_market_dashboard_v2.py` + `market_engine.py` — async BTC/ETH/SOL dashboard from Binance + Deribit + Yahoo Finance
- **Upstox token** in `collector.py` and `market_analysis_v3.py` is a hardcoded JWT — expires and must be rotated manually

---

## AlphaEdge_Ticker

**Commands**
```bash
cd AlphaEdge_Ticker
pip install requests
sudo apt install python3-tk        # Ubuntu
python alphaedge_ticker.py
bash launch_ubuntu.sh              # handles dep install
```

**Architecture**

Single-file tkinter app. Config persisted to `~/.alphaedge_ticker.json`.
- Crypto prices: Hyperliquid REST API (`api.hyperliquid.xyz`)
- NSE prices: `yfinance` (optional — degrades gracefully if not installed)
- Scrolling banner rendered in a borderless, always-on-top `tk.Canvas` row

---

## AlphaEdge_NSE_Ticker

**Commands**
```bash
cd AlphaEdge_NSE_Ticker
pip install requests --break-system-packages
sudo apt install python3-tk        # Ubuntu
python alphaedge_ticker.py
bash launch_ubuntu.sh
```

**Architecture**

Single-file tkinter NSE options ticker for Nifty 50, BankNifty, and Sensex.

- `ROW_DEFS` — defines 3 rows: NIFTY (step 50, ±6 strikes), BNKN (step 100, ±3), SENSEX (step 100, ±3)
- `DataFetcher` — two-phase async fetch: `_fetch_quotes()` batches index quotes; `_fetch_options()` one chain call per row; `_snapshot` dict swapped atomically under `_lock`
- `_resolve_expiry()` probes up to 8 days forward until option chain returns data
- `TickerBanner` — three-row tkinter GUI; each row scrolls at ~60fps via `root.after(16, ...)`
- Upstox bearer token: override `upstox_token` in `~/.alphaedge_ticker.json`; fallback hardcoded in `DEFAULT_CONFIG`
- Upstox endpoints: `GET /v2/market-quote/quotes` (batch) + `GET /v2/option/chain` (per row)

---

## alphaedge-journal

**Architecture**

Two separate apps deployed to Vercel — no local build step for the static kits:

| URL | App | Notes |
|-----|-----|-------|
| `/app` | Next.js (App Router) | `source/` — Clerk auth, Redux, local fonts |
| `/marketing` | Static React (CDN) | `ui_kits/marketing/` |
| `/` | Static React (CDN) | `ui_kits/app/` |

- `vercel.json` controls routing
- `ui_kits/` loads React + Tailwind via CDN, Babel standalone — no build required; edit and push to deploy
- `source/` uses `@clerk/nextjs`; Tailwind config is inline `<script>` tags in HTML kits
- Trading colors: `buy` (#76b562), `sell` (#e96a5e)
- `colors_and_type.css` — shared design tokens

---

## crewai_testing

**Commands**
```bash
cd crewai_testing
crewai install                     # install via uv
crewai run                         # run crew (outputs report.md)
crewai test -n 2                   # run tests
```

Sandbox for CrewAI multi-agent experiments. Edit `src/crewai_testing/config/agents.yaml` and `tasks.yaml` to define agents and tasks. Requires Python 3.10–3.13 and `uv`.

---

## hello-reasoner

**Commands**
```bash
cd hello-reasoner
pip install -r requirements.txt
af server                          # start AgentField server (separate terminal)
python main.py                     # register agent + start serving
```

AgentField agent scaffold (`af init` template). Two reasoners: `demo_echo` (no AI) and `demo_analyze_sentiment` (requires LLM API key). Set `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `GOOGLE_API_KEY` — LiteLLM auto-detects provider from model name. See `reasoners.py` to add new reasoners.

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
