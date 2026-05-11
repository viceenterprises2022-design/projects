# BTCUSDT Futures Bot

Paper-trading bot for Hyperliquid BTC perpetual candles.

V1:
- Hyperliquid `BTC` 15m candles
- Breakout momentum strategy with multi-filter confirmation
- Paper broker only
- SQLite state
- Slack alerts
- No live trading path

## Strategy

- **Core**: Donchian Channel breakout of previous 20 candles.
- **Trend Filter**: Only LONG if price > EMA(200), only SHORT if price < EMA(200).
- **Volume Filter**: Breakout candle volume must exceed the median volume of the last 20 candles.
- **Strong Close**: 
  - LONG: Close must be in the top 25% of the candle's high-low range.
  - SHORT: Close must be in the bottom 25% of the candle's high-low range.
- **Volatility**: Uses Wilder's Smoothing ATR for position sizing and levels.

## Project Structure

```text
btcbot/
├── api/          # Hyperliquid API & Slack notifications
├── cli/          # Command-line interface logic
├── core/         # Config, data models, & SQLite storage
├── engine/       # Execution engine, paper broker, & backtester
├── strategy/     # Technical indicators & breakout logic
├── __init__.py
└── __main__.py
```

## Setup

```bash
cd /home/vreddy1/Desktop/Projects/btcusdt-futures-bot
pip install -r requirements.txt
cp .env.example .env
```

Put your Slack webhook in `.env`:

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

## Commands

```bash
# Run one iteration and exit
python3 -m btcbot run --once

# Run persistent loop (polls every 60s)
python3 -m btcbot run

# View current equity, pnl, and open position
python3 -m btcbot status

# Run backtest against stored data
python3 -m btcbot backtest --days 30

# Force close open position
python3 -m btcbot close --reason manual

# Verify Slack notifications
python3 -m btcbot test-slack

# Run Daily Astro Report
python3 astro_report.py
```

## Astro Report

Generates a daily horoscope for Taurus Sun / Cancer Moon using Exa API and Gemini 1.5 Flash.

### Setup
1. Get an API key from [Exa.ai](https://exa.ai).
2. Get a free API key from [Google AI Studio](https://aistudio.google.com).
3. Add `EXA_API_KEY` and `GEMINI_API_KEY` to your `.env`.

### Automation (Cron)
To receive the report every morning at 8:00 AM:
```bash
0 8 * * * cd /path/to/project && /usr/bin/python3 astro_report.py >> astro.log 2>&1
```

## Defaults

- Paper equity: `$10,000`
- Risk per trade: `2%`
- Max leverage cap: `20x`
- Stop loss: `1.5 * ATR(14)`
- Take profit: `3.0 * ATR(14)`
- Trailing stop: starts after `+1R`, trails by `1.0 * ATR(14)`

