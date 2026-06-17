---
type: Reference
title: Codex Assistant Rules
description: Programming-centric guidelines, virtual environment mappings, and run daemon configurations.
tags: [codex, rules, environments, multica]
timestamp: 2026-06-17T23:45:00Z
---

# CODEX.md

This file provides guidance to the Codex agent runtime when working in this repository.

## Python Environments

Codex must target the correct virtual environments when compiling, parsing, or executing python components:

| Venv | Path | Scope |
|------|------|-------|
| Main | `venv/` | Most script systems (FastAPI API server, Yahoo/Upstox collectors, daily pipelines) |
| PKScreener | `/home/vreddy1/Desktop/Projects/pkscreener_venv` | Technical scans (`pkscreener_runner.py`) |

## Runtime Daemons

The Codex runtime is managed as part of the `multica-daemon.service` along with Claude, Antigravity, Hermes, and Cursor:

```bash
# Check status of multica daemon
sudo systemctl status multica-daemon
```
