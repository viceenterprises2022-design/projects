# GEMINI.MD: AI Collaboration Guide (Python)

This document provides essential context for AI models interacting with this project.

## 1. Project Overview & Purpose

* **Primary Goal:** Multi-Market Trading Analysis System powered by Gemini.
* **Business Domain:** Financial analysis, technical analysis, and automated reporting.

## 2. Core Technologies & Stack

* **Languages:** Python 3.x
* **AI Model:** Google Gemini (via `google-generativeai`)
* **Data Ingestion:** `yfinance` (Equity), `ccxt` (Crypto)
* **Notifications:** Telegram (custom async client)
* **Package Manager:** `pip`

## 3. Key Files & Entrypoints

* **Main Entrypoint:** `main.py`
  - Usage: `python main.py <ticker> [--type equity|crypto] [--telegram]`
* **Orchestrator:** `src/orchestrator/main.py` (Coordinates agents)
* **Common Utilities:** `src/common/telegram_client.py` (Telegram bot integration)

## 4. Configuration

* Uses `.env` for secrets.
* Required variables (see `.env.example`):
  - `GOOGLE_API_KEY`: For Gemini analysis.
  - `TELEGRAM_BOT_TOKEN`: Bot token from @BotFather.
  - `TELEGRAM_CHAT_ID`: Your chat/channel ID.

## 5. Development Workflow

* **Analysis Flow:**
  1. Data Ingestion (yfinance/ccxt)
  2. Multi-Agent Analysis (Fundamental/Technical skills)
  3. JSON Report Generation
  4. (Optional) Telegram Broadcast

* **Adding Skills:** Add new `.md` skill definitions in `agents/` or `Financial_System_design/`.
