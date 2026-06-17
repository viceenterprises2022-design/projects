---
type: Reference
title: Hermes Orchestrator Rules
description: Parallel specialist reasoners architecture and custom beta API endpoints configuration.
tags: [hermes, multica, specialist-reasoners, configuration]
timestamp: 2026-06-17T23:45:00Z
---

# HERMES.md

This file provides guidance to the Hermes agent runtime when working in this repository.

## Architecture

Hermes operates as a LangGraph orchestrator decomposed into five parallel specialist reasoners:
1. `validate_intent`
2. `macro_analyst`
3. `technical_scanner`
4. `coin_researcher`
5. `report_compiler`

## Configuration

* **Config Location:** `~/.hermes/config.yaml`
* **Default Model:** `gemini-3.5-flash`
* **API Endpoint:** Uses custom OpenAI-compatible Google API endpoint (`https://generativelanguage.googleapis.com/v1beta/openai/`) to bypass CastAI/Kimchi provider credit exhaustion.
