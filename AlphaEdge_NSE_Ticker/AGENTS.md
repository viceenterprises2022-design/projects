# AGENTS.md — AlphaEdge_NSE_Ticker

> Universal context spec read by Claude Code, OpenCode, Codex, Gemini CLI, Antigravity, Cursor, and any AGENTS.md-aware agent.
> Edit this file as the project evolves. Drafted by `agents-bootstrap`.

## Communication Style

Caveman ultra mode. Terse, action-first. No filler. Pattern: `[thing] [action] [reason]. [next step].`

## 1. Purpose

tkinter NSE options ticker for Nifty 50, BankNifty, Sensex via Upstox API. Single-file desktop app.

## 2. Stack

Python

## 3. Entry Point

`alphaedge_ticker.py`

## 4. Commands

```bash
pip install -r requirements.txt --break-system-packages
python3 alphaedge_ticker.py
```

## 5. Environment Variables

_None detected — list secret names (not values) here as they're added._

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
