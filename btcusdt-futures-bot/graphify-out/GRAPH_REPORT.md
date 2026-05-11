# Graph Report - /home/vreddy1/Desktop/Projects/btcusdt-futures-bot  (2026-05-09)

## Corpus Check
- 16 files · ~2,865 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 74 nodes · 165 edges · 14 communities detected
- Extraction: 56% EXTRACTED · 44% INFERRED · 0% AMBIGUOUS · INFERRED: 72 edges (avg confidence: 0.76)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]

## God Nodes (most connected - your core abstractions)
1. `Store` - 25 edges
2. `run_once()` - 22 edges
3. `PaperBroker` - 18 edges
4. `main()` - 14 edges
5. `BotConfig` - 8 edges
6. `run_backtest()` - 7 edges
7. `generate_breakout_signal()` - 7 edges
8. `test_take_profit_exit_long()` - 7 edges
9. `Signal` - 6 edges
10. `SlackNotifier` - 6 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `load_config()`  [INFERRED]
  /home/vreddy1/Desktop/Projects/btcusdt-futures-bot/btcbot/cli.py → /home/vreddy1/Desktop/Projects/btcusdt-futures-bot/btcbot/config.py
- `main()` --calls--> `Store`  [INFERRED]
  /home/vreddy1/Desktop/Projects/btcusdt-futures-bot/btcbot/cli.py → /home/vreddy1/Desktop/Projects/btcusdt-futures-bot/btcbot/storage.py
- `main()` --calls--> `run_backtest()`  [INFERRED]
  /home/vreddy1/Desktop/Projects/btcusdt-futures-bot/btcbot/cli.py → /home/vreddy1/Desktop/Projects/btcusdt-futures-bot/btcbot/backtest.py
- `main()` --calls--> `PaperBroker`  [INFERRED]
  /home/vreddy1/Desktop/Projects/btcusdt-futures-bot/btcbot/cli.py → /home/vreddy1/Desktop/Projects/btcusdt-futures-bot/btcbot/broker.py
- `Store` --uses--> `BotConfig`  [INFERRED]
  /home/vreddy1/Desktop/Projects/btcusdt-futures-bot/btcbot/storage.py → /home/vreddy1/Desktop/Projects/btcusdt-futures-bot/btcbot/config.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.26
Nodes (8): atr(), true_ranges(), generate_breakout_signal(), c(), test_atr_uses_true_range(), candle(), test_long_breakout_signal(), test_no_signal_inside_range()

### Community 1 - "Community 1"
Cohesion: 0.31
Nodes (4): main(), SlackNotifier, run_loop(), run_once()

### Community 2 - "Community 2"
Cohesion: 0.39
Nodes (1): Store

### Community 3 - "Community 3"
Cohesion: 0.43
Nodes (0): 

### Community 4 - "Community 4"
Cohesion: 0.47
Nodes (2): PaperBroker, Trade

### Community 5 - "Community 5"
Cohesion: 0.6
Nodes (5): BotConfig, load_config(), load_dotenv(), load_simple_yaml(), _parse_scalar()

### Community 6 - "Community 6"
Cohesion: 0.5
Nodes (3): Signal, test_position_size_respects_20x_cap(), test_take_profit_exit_long()

### Community 7 - "Community 7"
Cohesion: 0.7
Nodes (4): fetch_candles(), interval_to_ms(), normalize_candle(), _post_json()

### Community 8 - "Community 8"
Cohesion: 0.67
Nodes (1): run_backtest()

### Community 9 - "Community 9"
Cohesion: 0.67
Nodes (2): Candle, Position

### Community 10 - "Community 10"
Cohesion: 1.0
Nodes (1): BTCUSDT Hyperliquid paper-trading bot.

### Community 11 - "Community 11"
Cohesion: 1.0
Nodes (0): 

### Community 12 - "Community 12"
Cohesion: 1.0
Nodes (0): 

### Community 13 - "Community 13"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **1 isolated node(s):** `BTCUSDT Hyperliquid paper-trading bot.`
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 10`** (2 nodes): `__init__.py`, `BTCUSDT Hyperliquid paper-trading bot.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 11`** (2 nodes): `notifier.py`, `enabled()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 12`** (2 nodes): `.enter()`, `._entry_fill()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 13`** (1 nodes): `__main__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run_once()` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 4`, `Community 7`, `Community 8`, `Community 12`?**
  _High betweenness centrality (0.299) - this node is a cross-community bridge._
- **Why does `Store` connect `Community 2` to `Community 1`, `Community 3`, `Community 4`, `Community 5`, `Community 6`, `Community 9`?**
  _High betweenness centrality (0.215) - this node is a cross-community bridge._
- **Why does `PaperBroker` connect `Community 4` to `Community 1`, `Community 5`, `Community 6`, `Community 8`, `Community 9`, `Community 12`?**
  _High betweenness centrality (0.180) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `Store` (e.g. with `BotConfig` and `Candle`) actually correct?**
  _`Store` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `run_once()` (e.g. with `Store` and `PaperBroker`) actually correct?**
  _`run_once()` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `PaperBroker` (e.g. with `BotConfig` and `Candle`) actually correct?**
  _`PaperBroker` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `main()` (e.g. with `load_config()` and `run_loop()`) actually correct?**
  _`main()` has 13 INFERRED edges - model-reasoned connections that need verification._