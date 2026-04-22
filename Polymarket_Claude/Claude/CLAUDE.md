# Polybot — Claude Code Session Guide

## Project
Polymarket copy-trading bot with self-improving DGM-Hyperagent framework.
Three papers unified: HyperAgents (Meta) + TradingAgents (Roles) + Autoresearch (Loop).

## Stack
- Python 3.11+ · asyncio · aiosqlite
- py-clob-client 0.34.6 · web3 6.14.0
- python-telegram-bot 20.7
- anthropic SDK · pyyaml · tenacity

## Key Commands
```bash
pip install -r requirements.txt          # install deps
cp .env.example .env                     # fill in credentials
python main.py                           # run bot (DRY_RUN=true default)
python -m whale.scorer 0xWALLET         # vet a whale wallet
python evaluate.py                       # run backtest on signal history
python dgm_h_loop.py --max-iter 20      # run self-improvement loop
python parallel_researcher.py --list     # list strategy variants
python analysis.py --telegram            # morning report
```

## Architecture
```
main.py                    # bot orchestrator — start here
├── core/
│   ├── config.py          # env + yaml loader
│   ├── clob_client.py     # Polymarket CLOB API wrapper
│   ├── gamma_client.py    # market metadata (no auth)
│   └── subgraph_client.py # on-chain positions via Goldsky GraphQL
├── whale/
│   ├── tracker.py         # polls whale wallets, emits CopySignals
│   └── scorer.py          # vet wallets before tracking
├── execution/
│   ├── risk_engine.py     # 9-point pre-trade gate
│   └── order_manager.py   # trade execution + position monitor
├── storage/db.py          # SQLite — trades, positions, P&L
├── notifications/
│   └── telegram_bot.py    # full Telegram integration
├── analytics/pnl_tracker.py
├── hyperagent.py          # DGM-H: TaskAgent + MetaAgent unified
├── dgm_h_loop.py          # autonomous self-improvement loop
├── evaluate.py            # fixed backtester (NEVER modify)
├── parallel_researcher.py # parallel domain-specialist comparison
├── analysis.py            # results.tsv analyzer
├── strategy.yaml          # AGENT EDITS THIS (like train.py)
├── program.md             # human writes this (like program.md)
├── config.yaml            # bot config (human edits)
└── .env                   # credentials (never commit)
```

## Critical Rules
- DRY_RUN=true in .env until you have 30+ days of signal history
- Never modify evaluate.py — Goodhart's Law protection
- strategy.yaml is edited by the DGM-H agent, not humans
- program.md is written by humans, not the agent
- data/bot.db accumulates signals — back it up before experiments

## Env Variables Required
```
PRIVATE_KEY=0x...           # Polymarket wallet key
FUNDER_ADDRESS=0x...        # Safe wallet address  
SIGNATURE_TYPE=1            # 1=Email/Magic, 0=MetaMask, 2=Gnosis
TELEGRAM_BOT_TOKEN=...      # from @BotFather
TELEGRAM_CHAT_ID=...        # your chat/group ID
ANTHROPIC_API_KEY=...       # for DGM-H self-improvement loop
DRY_RUN=true                # ALWAYS start true
```

## Phase 1: Bot Setup (Days 1–30)
1. Fill .env · add whale wallets to config.yaml
2. python main.py → watch Telegram for signal alerts
3. Accumulate signal history in data/bot.db

## Phase 2: AutoResearch (Day 30+)
1. python evaluate.py → verify baseline Sharpe
2. python dgm_h_loop.py --max-iter 50 → overnight run
3. python analysis.py --telegram → morning report
4. Promote best strategy.yaml → config.yaml → DRY_RUN=false
