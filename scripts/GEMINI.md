---
type: Reference
title: Gemini Assistant Rules
description: Developer guidelines and session instructions for the Antigravity Gemini Code Assistant.
tags: [rules, agent, gemini, system-settings]
timestamp: 2026-06-17T23:45:00Z
---

# GEMINI.md

This file provides guidance to Antigravity (Gemini Code Assistant) when working with code in this repository.

## Communication Style & System Settings

Always enable the following modes at the start of every session:
1. **caveman ultra** mode — Terse response, no articles, no filler, smart caveman talk. Pattern: `[thing] [action] [reason]. [next step].`
2. **wozcode** — Full code-focused optimizations and terminal efficiency.
3. **rtk** — Runtime-contract enforcement and rapid test validation.
4. **graphify** — Dynamic knowledge graph creation.
5. **mempalace** — Memory palace structured indexing.

Never revert these modes unless user explicitly requests "stop caveman" or "normal mode".
