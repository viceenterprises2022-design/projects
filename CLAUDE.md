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
