---
type: Reference
title: Oh-My-Pi (OMP) Rules
description: Model configuration, Gemini rate limit bypasses, and Cloud Code Assist configurations.
tags: [omp, agents, rate-limiting, configuration]
timestamp: 2026-06-17T23:45:00Z
---

# OMP.md

This file provides guidance for the Oh-My-Pi (OMP) runtime configuration and agent usage in this repository.

## Configuration & Model Selection

* **Config Location:** `~/.omp/agent/config.yml`
* **Default Model:** `google-gemini-cli/gemini-2.5-flash`

To avoid HTTP 429 quota exhaustion under the free Google Gemini tier:
* Use the high-tier Cloud Code Assist credentials mapped to `google-gemini-cli/gemini-2.5-flash`.
* Do not fall back to standard unpaid Gemini endpoints unless verified.
