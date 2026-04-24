# Graph Report - /home/vreddy1/Desktop/Projects  (2026-04-25)

## Corpus Check
- 137 files · ~366,519 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1106 nodes · 2436 edges · 75 communities detected
- Extraction: 58% EXTRACTED · 42% INFERRED · 0% AMBIGUOUS · INFERRED: 1021 edges (avg confidence: 0.69)
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
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]

## God Nodes (most connected - your core abstractions)
1. `TelegramJournal` - 62 edges
2. `main()` - 37 edges
3. `BotState` - 36 edges
4. `GlobalRiskConfig` - 35 edges
5. `Position` - 35 edges
6. `RiskManager` - 35 edges
7. `Notifier` - 27 edges
8. `TraderScorer` - 27 edges
9. `TraderFilter` - 25 edges
10. `TickerBanner` - 24 edges

## Surprising Connections (you probably didn't know these)
- `list()` --calls--> `load()`  [INFERRED]
  /home/vreddy1/Desktop/Projects/tradingview-mcp/src/core/tab.js → Polymarket_Claude/Claude/analysis.py
- `main()` --calls--> `init_db()`  [INFERRED]
  /home/vreddy1/Desktop/Projects/Alphaedge_Copy/main.py → Polymarket_Claude/Claude/db.py
- `main()` --calls--> `exit()`  [INFERRED]
  /home/vreddy1/Desktop/Projects/Alphaedge_Copy/main.py → Polymarket_Claude/Claude/config.py
- `main()` --calls--> `WhaleTracker`  [INFERRED]
  /home/vreddy1/Desktop/Projects/Alphaedge_Copy/main.py → Polymarket_Claude/Claude/tracker.py
- `exit()` --calls--> `main()`  [INFERRED]
  Polymarket_Claude/Claude/config.py → /home/vreddy1/Desktop/Projects/crypto-scripts/wallet-researcher.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.03
Nodes (47): analyze(), fmt_telegram(), print_report(), analysis.py — Read results.tsv and surface insights. Usage:     python analysis., send_tg(), place_market_buy(), place_market_sell(), PolymarketClient (+39 more)

### Community 1 - "Community 1"
Cohesion: 0.04
Nodes (65): AlgoValidator, BacktestTrade, _compute_sl_at_pct(), DiversificationEngine, GlobalRiskEngine, KillSwitchEngine, KillSwitchEvent, KillSwitchLevel (+57 more)

### Community 2 - "Community 2"
Cohesion: 0.04
Nodes (98): create(), deleteAlerts(), list(), batchRun(), captureScreenshot(), getState(), getVisibleRange(), manageIndicator() (+90 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (53): BinanceBot, fetch_positions_normalized(), AlphaCopy - Binance Futures Copy Bot  Data source: Binance's unofficial leaderbo, Detect new/closed positions by diffing against cached snapshot., Fetch and normalize positions to {symbol: pos_data}., Binance Futures copy trading bot.      Flow:       1. Scrape leaderboard → score, Dashboard, AlphaCopy - Performance Dashboard Console + JSON reporting for all three bots. (+45 more)

### Community 4 - "Community 4"
Cohesion: 0.04
Nodes (66): DiskCache, getReplayApi(), Archive, decide(), git(), git_commit(), git_revert(), init_results() (+58 more)

### Community 5 - "Community 5"
Cohesion: 0.04
Nodes (67): BaseModel, BaseTool, load_asset_configs(), project_root(), disconnect(), crew(), draft_report_task(), MarketReportCrew (+59 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (38): registerChartTools(), Enum, registerPineTools(), AlphaCopy — Global Risk Configuration All industry-standard risk parameters in o, Portfolio risk appetite tiers., RiskTier, BotState, AlphaCopy - Unified Risk Manager Enforces position limits, drawdown stops, and s (+30 more)

### Community 7 - "Community 7"
Cohesion: 0.04
Nodes (56): aiosqlite>=0.20.0, analysis.py (results.tsv analyzer), anthropic>=0.40.0 SDK, Autoresearch (Loop) Paper, config.yaml (Bot Config), CopySignal, core/clob_client.py, core/config.py (+48 more)

### Community 8 - "Community 8"
Cohesion: 0.09
Nodes (18): CryptoIngestion, EquityIngestion, Fetch fundamental data., Fetch historical price data and compute indicators., Ingest crypto data from CCXT., Fetch current price and volume., Ingest equity data from Yahoo Finance., Main logic to coordinate multi-agent analysis. (+10 more)

### Community 9 - "Community 9"
Cohesion: 0.11
Nodes (3): DataFetcher, TickerBanner, load()

### Community 10 - "Community 10"
Cohesion: 0.13
Nodes (6): Hyperagent, MetaAgent, PerformanceTracker, hyperagent.py — Polybot DGM-Hyperagent. Single editable program containing task_, Core DGM-H step. Returns (target_file, new_content)., Single editable program: task_agent + meta_agent unified.

### Community 11 - "Community 11"
Cohesion: 0.12
Nodes (4): CorrCell(), corrColor(), fmtINR(), RetailOverview()

### Community 12 - "Community 12"
Cohesion: 0.26
Nodes (14): fetch_all_usdt_transfers(), fetch_wallet_balances(), get_headers(), main(), print_counterparty_summary(), print_transaction_detail(), Return (TRX balance, USDT balance) for a wallet address., Print every individual transaction in chronological order. (+6 more)

### Community 13 - "Community 13"
Cohesion: 0.17
Nodes (14): analyze_metals_correlation(), analyze_money_supply_impact(), categorize_event_impact(), fetch_calendar_from_web(), format_calendar_for_playbook(), generate_trading_strategy(), main(), Fetch economic calendar using web_fetch tool     Returns parsed calendar data (+6 more)

### Community 14 - "Community 14"
Cohesion: 0.19
Nodes (6): CorrBadge(), corrColor(), MarketDeepDive(), riskColor(), riskLabel(), RiskPill()

### Community 15 - "Community 15"
Cohesion: 0.27
Nodes (5): calcPnl(), calcPnlPct(), calcRR(), ConfirmModal(), PositionRow()

### Community 16 - "Community 16"
Cohesion: 0.29
Nodes (5): calcPnl(), CloseModal(), Dashboard(), fmtD(), fmtP()

### Community 17 - "Community 17"
Cohesion: 0.29
Nodes (5): calcPnl(), CloseModal(), Dashboard(), fmtD(), fmtP()

### Community 18 - "Community 18"
Cohesion: 0.33
Nodes (0): 

### Community 19 - "Community 19"
Cohesion: 0.6
Nodes (3): mockDeps(), mockEvaluate(), mockGetReplayApi()

### Community 20 - "Community 20"
Cohesion: 0.67
Nodes (2): mockDeps(), mockEval()

### Community 21 - "Community 21"
Cohesion: 0.67
Nodes (0): 

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (0): 

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (0): 

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (0): 

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (0): 

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (0): 

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (0): 

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (0): 

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (0): 

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (0): 

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (0): 

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (0): 

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (0): 

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (0): 

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (0): 

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (0): 

### Community 40 - "Community 40"
Cohesion: 1.0
Nodes (0): 

### Community 41 - "Community 41"
Cohesion: 1.0
Nodes (0): 

### Community 42 - "Community 42"
Cohesion: 1.0
Nodes (0): 

### Community 43 - "Community 43"
Cohesion: 1.0
Nodes (0): 

### Community 44 - "Community 44"
Cohesion: 1.0
Nodes (0): 

### Community 45 - "Community 45"
Cohesion: 1.0
Nodes (0): 

### Community 46 - "Community 46"
Cohesion: 1.0
Nodes (0): 

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (0): 

### Community 48 - "Community 48"
Cohesion: 1.0
Nodes (0): 

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (0): 

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (0): 

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (0): 

### Community 52 - "Community 52"
Cohesion: 1.0
Nodes (0): 

### Community 53 - "Community 53"
Cohesion: 1.0
Nodes (0): 

### Community 54 - "Community 54"
Cohesion: 1.0
Nodes (0): 

### Community 55 - "Community 55"
Cohesion: 1.0
Nodes (0): 

### Community 56 - "Community 56"
Cohesion: 1.0
Nodes (0): 

### Community 57 - "Community 57"
Cohesion: 1.0
Nodes (0): 

### Community 58 - "Community 58"
Cohesion: 1.0
Nodes (0): 

### Community 59 - "Community 59"
Cohesion: 1.0
Nodes (0): 

### Community 60 - "Community 60"
Cohesion: 1.0
Nodes (0): 

### Community 61 - "Community 61"
Cohesion: 1.0
Nodes (0): 

### Community 62 - "Community 62"
Cohesion: 1.0
Nodes (0): 

### Community 63 - "Community 63"
Cohesion: 1.0
Nodes (0): 

### Community 64 - "Community 64"
Cohesion: 1.0
Nodes (0): 

### Community 65 - "Community 65"
Cohesion: 1.0
Nodes (0): 

### Community 66 - "Community 66"
Cohesion: 1.0
Nodes (1): parallel_researcher.py

### Community 67 - "Community 67"
Cohesion: 1.0
Nodes (1): aiohttp>=3.9.0

### Community 68 - "Community 68"
Cohesion: 1.0
Nodes (1): aiofiles>=23.0.0

### Community 69 - "Community 69"
Cohesion: 1.0
Nodes (1): tenacity>=8.2.0

### Community 70 - "Community 70"
Cohesion: 1.0
Nodes (1): Research Priority: Asymmetric Exits

### Community 71 - "Community 71"
Cohesion: 1.0
Nodes (1): Research Priority: Consensus by Category

### Community 72 - "Community 72"
Cohesion: 1.0
Nodes (1): Research Priority: Memory-Augmented Decisions

### Community 73 - "Community 73"
Cohesion: 1.0
Nodes (1): Research Priority: Debate Quality

### Community 74 - "Community 74"
Cohesion: 1.0
Nodes (1): NOAA/Wunderground Weather Resolution Data

## Knowledge Gaps
- **114 isolated node(s):** `Fresh Telegram Integration Client.     Handles sending formatted messages and do`, `Send a text message to the configured chat.`, `Formats and sends a trading report.`, `Ingest equity data from Yahoo Finance.`, `Fetch fundamental data.` (+109 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 22`** (2 nodes): `pine.js`, `readStdin()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (2 nodes): `registerCaptureTools()`, `capture.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (2 nodes): `registerHealthTools()`, `health.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (2 nodes): `pane.js`, `registerPaneTools()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (2 nodes): `registerDataTools()`, `data.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (2 nodes): `jsonResult()`, `_format.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (2 nodes): `registerAlertTools()`, `alerts.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (2 nodes): `replay.js`, `registerReplayTools()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (2 nodes): `indicators.js`, `registerIndicatorTools()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (2 nodes): `registerDrawingTools()`, `drawing.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (2 nodes): `registerBatchTools()`, `batch.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (2 nodes): `tab.js`, `registerTabTools()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (2 nodes): `watchlist.js`, `registerWatchlistTools()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (1 nodes): `server.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (1 nodes): `index.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (1 nodes): `index.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (1 nodes): `capture.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (1 nodes): `health.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (1 nodes): `stream.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (1 nodes): `pane.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (1 nodes): `data.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (1 nodes): `alerts.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (1 nodes): `replay.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (1 nodes): `ui.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (1 nodes): `chart.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (1 nodes): `layout.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (1 nodes): `drawing.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (1 nodes): `tab.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (1 nodes): `indicator.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (1 nodes): `watchlist.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (1 nodes): `pine_push.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (1 nodes): `pine_pull.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (1 nodes): `list_models.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (1 nodes): `L1.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 61`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 62`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 64`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 65`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 66`** (1 nodes): `parallel_researcher.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 67`** (1 nodes): `aiohttp>=3.9.0`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 68`** (1 nodes): `aiofiles>=23.0.0`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 69`** (1 nodes): `tenacity>=8.2.0`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 70`** (1 nodes): `Research Priority: Asymmetric Exits`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 71`** (1 nodes): `Research Priority: Consensus by Category`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 72`** (1 nodes): `Research Priority: Memory-Augmented Decisions`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 73`** (1 nodes): `Research Priority: Debate Quality`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 74`** (1 nodes): `NOAA/Wunderground Weather Resolution Data`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Community 3` to `Community 0`, `Community 4`, `Community 5`, `Community 8`, `Community 9`, `Community 17`?**
  _High betweenness centrality (0.122) - this node is a cross-community bridge._
- **Why does `bootstrap()` connect `Community 5` to `Community 0`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Are the 45 inferred relationships involving `TelegramJournal` (e.g. with `RuleViolation` and `KillSwitchLevel`) actually correct?**
  _`TelegramJournal` has 45 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `main()` (e.g. with `.run()` and `.get()`) actually correct?**
  _`main()` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 34 inferred relationships involving `BotState` (e.g. with `RuleViolation` and `KillSwitchLevel`) actually correct?**
  _`BotState` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 33 inferred relationships involving `GlobalRiskConfig` (e.g. with `RuleViolation` and `KillSwitchLevel`) actually correct?**
  _`GlobalRiskConfig` has 33 INFERRED edges - model-reasoned connections that need verification._
- **Are the 34 inferred relationships involving `Position` (e.g. with `RuleViolation` and `KillSwitchLevel`) actually correct?**
  _`Position` has 34 INFERRED edges - model-reasoned connections that need verification._