---
type: Reference
title: OpenCode Plugin Rules
description: Custom commands, tools, and hooks configuration for OpenCode goal pursuing.
tags: [opencode, goals, hooks, plugins]
timestamp: 2026-06-17T23:45:00Z
---

# OPENCODE.md

This file documents the OpenCode configurations and agent integration rules for the repository.

## Commands & Tools

1. `/pursue` (`experimental.compaction.autocontinue` hook) — Automatically continues and runs long-running goals autonomously.
2. `/logwork` — Creates corresponding task issues in the Multica project management system by parsing the "Session Memory" in `AGENTS.md` (e.g. `ALP-XXX` issues).

## Custom Plugin Structure

* **Plugin Path:** `~/.config/opencode/plugins/opencode-goal/`
* **Tools:**
  - `goal_define`
  - `goal_checkpoint`
  - `goal_status`
  - `goal_complete`
* **Hooks:**
  - `experimental.chat.system.transform` (Injects evaluator prompt when a goal is active)
  - `experimental.compaction.autocontinue` (Enables loop-continue for long sessions)
