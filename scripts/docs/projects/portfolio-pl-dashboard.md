---
type: Project
title: Portfolio P&L Dashboard
description: Unified multi-broker API aggregator and P&L monitoring daemon backend.
tags: [portfolio, pnl, aggregation, brokers, api]
timestamp: 2026-06-17T23:30:00Z
---

# 💼 Portfolio P&L Dashboard

> Section group: **🚀 Script Index**

*Multi-broker portfolio aggregator with live/mock fallback.*

| Script | Description |
|:--- |:--- |
| `pnl_poller.py` | **P&L Aggregator**. Polls Upstox, Dhan, TradeSmart (Noren OMS), Fyers, Hyperliquid, Exness, and Binance APIs. Falls back to a dynamic mock (sinusoidal fluctuation) per broker when credentials are missing or return 401/403. Exposed at `GET /api/portfolio/pnl`. The endpoint never fails — always returns data. |

---
