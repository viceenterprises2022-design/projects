# Agents Convention

Inspired by [eve](https://eve.dev)'s filesystem-first approach: each agent is a directory, names derive from paths, and the tree tells you what the agent can do.

## Canonical Structure

```
agents/<name>/
├── instructions.md    # identity + standing rules (always-on prompt)
├── tools/             # executable capabilities (name = filename)
├── skills/            # on-demand procedures (SKILL.md convention)
└── channels/          # message routing targets
```

Root-level `.py` scripts stay at root (moving them would break imports,
systemd services, and crontab). Agent descriptors in `agents/` document the
interface. See `agents/_template/` for the reference layout.

## Path-Derived Naming

A file's path determines its identity — no config fields needed:

| Path | Resolves to |
|---|---|
| `agents/alphaedge/tools/get_quote.py` | tool `get_quote` |
| `agents/pkscreener/skills/scan_breakout.md` | skill `scan_breakout` |
| `agents/cot-analyzer/channels/telegram.py` | channel `telegram` |

## Agents

| Agent | Path | Role |
|---|---|---|
| AlphaEdge Collector | `agents/alphaedge-collector/` | Market data fetch + 10-factor signals |
| AlphaEdge API | `agents/alphaedge-api/` | FastAPI REST + dashboard |
| PKScreener | `agents/pkscreener/` | NSE stock scanner (8 strategies) |
| NotebookLM Pipeline | `agents/notebooklm-pipeline/` | YouTube/Telegram/Arxiv → NotebookLM → Slack |
| Exa Search | `agents/exa-search/` | AI event + crypto news search |
| Crypto Dashboard | `agents/crypto-dashboard/` | BTC/ETH/SOL live monitoring |
| COT Analyzer | `agents/cot-analyzer/` | CFTC positioning analysis |
| RWA Reporter | `agents/rwa-reporter/` | RWA/stablecoin research → Slack |

## Skills Inventory

Skills are distributed across 3 harness directories. There is **zero
triple-overlap** — no skill name exists in all three locations.

| Directory | Count | Source |
|---|---|---|
| `~/.claude/skills/` | 327 | Claude Code (218 direct + 108 symlinks to `.agents`) |
| `~/.agents/skills/` | 119 | ECC canonical source |
| `~/.config/opencode/skills/` | 183 | OpenCode (108 real + 75 category-pointers) |
| `~/Desktop/Projects/scripts/skills/` | 6 | Ponytail skills only |

**Pairwise overlaps (8 total):**
- `.agents/skills` ↔ `claude/skills` (direct): `ask-docs`, `design-agent`, `design-task`, `getting-started`
- `claude/skills` (direct) ↔ OpenCode: `cross-agent-context-router`, `docs-split`, `gstack`, `gstack-upgrade`

**7 `.agents/skills` skills not linked into `claude/skills/`:**
`anything-to-notebooklm`, `computer-use`, `find-skills`, `idea-ingest`, `ingest`,
`orca-cli`, `orchestration` — run `install_skill <name>` to activate these.

**30 duplicate names within `~/.claude/`** (skills/ and .agents/skills/) — expected,
maintained by different plugin installers, not a consolidation target.
