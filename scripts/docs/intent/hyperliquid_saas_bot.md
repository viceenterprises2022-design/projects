# Product Intent: Hyperliquid Commercial SaaS Trading Bot

## Overview
A commercial SaaS trading platform executing rule-based breakout and TradingView signals on Hyperliquid. It integrates Gemini 3.5 Flash offline for risk management, rule generation, journaling, and metrics dashboard reporting.

## Core Intent Dimensions

- **Outcome:** Commercial SaaS platform executing TradingView and rule-based breakout signals on Hyperliquid.
- **User:** Retail and pro crypto traders wanting automated execution.
- **Why now:** Expand existing market intelligence engines to commercial monetization.
- **Success:** Fast trade execution, plus dashboard showing AI-generated risk metrics and trade journaling.
- **Constraint:** No AI in critical trade path (to avoid latency), secure custody/storage of client API keys.
- **Out of scope:** Native exchange wallet hosting (users connect own Hyperliquid keys), low-latency high-frequency trading (HFT).

## Technology Focus
- **Backend:** FastAPI (Python) for rapid webhook receipt, signal collation, and rule execution.
- **Execution:** Direct REST/Websocket connections to Hyperliquid API.
- **AI Engine:** Gemini 3.5 Flash (offline) processing post-trade analysis, metrics generation, and risk monitoring.
- **Frontend:** Vanilla HTML/CSS/JS dashboard displaying active positions, journal history, and AI metrics.
