# Agents Convention

Inspired by [eve](https://eve.dev)'s filesystem-first approach: each agent is a directory, names derive from paths, and the tree tells you what the agent can do.

## Canonical Structure

```
agents/<name>/
├── instructions.md    # identity + standing rules (always-on prompt)
├── tools/             # executable capabilities (one file per tool, name = filename)
│   └── <tool>.py      # a typed action the agent can perform
├── skills/            # on-demand procedures (SKILL.md convention)
│   └── <skill>.md     # loaded only when useful
└── channels/          # message routing targets
    └── <channel>.py   # Slack, Telegram, Discord, etc.
```

## Path-Derived Naming

A file's path determines its identity — no config fields needed:

| Path | Resolves to |
|---|---|
| `agents/alphaedge/tools/get_quote.py` | tool `get_quote` |
| `agents/pkscreener/skills/scan_breakout.md` | skill `scan_breakout` |
| `agents/cot-analyzer/channels/telegram.py` | channel `telegram` |

## Mapping Existing Scripts

Root-level `.py` scripts are the actual implementation. Their agent descriptors here document the interface (what instructions they follow, what tools they expose, what channels they use). This is a registry, not a relocation — don't move working scripts.
