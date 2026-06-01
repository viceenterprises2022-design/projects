# AGENTS.md — btcusdt-futures-bot

> Universal context spec read by Claude Code, OpenCode, Codex, Gemini CLI, Antigravity, Cursor, and any AGENTS.md-aware agent.
> Edit this file as the project evolves. Drafted by `agents-bootstrap`.

## Communication Style

Caveman ultra mode. Terse, action-first. No filler. Pattern: `[thing] [action] [reason]. [next step].`

## 1. Purpose

Hyperliquid BTC perp paper-trading bot. 15m candles, Donchian-20 breakout, EMA(200) trend filter, volume + strong-close gates.

## 2. Stack

Python

## 3. Entry Point

`(unknown — set this manually)`

## 4. Commands

```bash
# (fill in commands)
```

## 5. Environment Variables

```
DB_PATH
EXA_API_KEY
GEMINI_API_KEY
MAX_LEVERAGE
MODE
PAPER_EQUITY_USD
RISK_PER_TRADE_PCT
SLACK_USERNAME
SLACK_WEBHOOK_URL
SYMBOL
TIMEFRAME
```

## 6. Conventions

- **Memory:** durable cross-agent facts → agentmemory daemon (`agentmemory status`). Per-project workflow → this file. Daily progress → "Session Memory" section below.
- **Skills:** load from `~/.claude/skills/` (shared). Don't duplicate per-agent.
- **Graphify:** before architecture questions, read `graphify-out/GRAPH_REPORT.md`. After edits, run `graphify update .`.
- **Secrets:** never commit. Use `.env`. List names in section 5 above.
- **Commits:** Conventional Commits — `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`.

## 7. Gotchas / Pitfalls

_(Fill in as you hit them. Examples: stale tokens, rate limits, platform-specific quirks, fragile dependencies.)_

## 8. Session Memory

Recent work, decisions, and links to Multica issues. Use `/logwork` to sync entries here to Multica.

### YYYY-MM-DD: Title
- Bullet of what was done.
- **Multica:** ALP-XXX (done, assigned Vinod-AI-CEO)
