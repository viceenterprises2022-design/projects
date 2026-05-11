<!-- converted from AlphaEdge_Developer_Definitions_v1.1.docx -->





Definition
A Market Parameter record is the normalised, structured data object for a single emerging market (uniquely identified by ISO-2 code, e.g., IN for India, BR for Brazil). It is the single source of truth for all downstream engines. Every module in the platform reads from this object rather than independently fetching raw data. It contains five categories of structured data.

API Contract



Definition
The Correlation Matrix is a real-time N×N table of pairwise correlation coefficients between all tracked assets. AlphaEdge uses Dynamic Conditional Correlation GARCH (DCC-GARCH) rather than static Pearson correlation, because correlations change dramatically during market crises. This time-varying approach is the platform's primary technical differentiation.



Definition
The Risk Score is a normalised composite index (0 = minimal risk, 100 = extreme risk) computed per market. It synthesises macroeconomic instability signals into a single actionable number used to classify markets into four risk tiers. The individual macro indicators are the raw inputs; the Risk Score is the computed output.




Definition
The Crisis Correlation Predictor™ (patent pending) is a weighted ensemble model that outputs a real-time probability (0–100%) representing the likelihood of a correlation regime spike within the next 3–7 trading days. It monitors 5 independent market stress signals. The March 2020 event (where diversified portfolios lost 30–40% due to correlation spikes) is the validation benchmark.

Final Probability Formula



Definition
The Lead-Lag Engine maps directional causal relationships between financial variables using Granger causality testing. Unlike correlation (which is symmetric and implies no direction), Granger causality establishes which variable leads and which lags — and by how many days. This is the engine's predictive advantage: if you know the DXY moved 30 minutes ago, you can predict where INR opens tomorrow.



Definition
A Transmission Model is a parametric, empirically-calibrated function that maps a macro input event to a set of quantified, time-stamped impacts across currencies, equity sectors, and macro indicators. Each model produces a structured impact object with magnitude, confidence interval, timeline, and affected sectors — not just a directional signal. Three models are validated and production-ready.

Implementation Pattern



Definition
Market Drivers are structured knowledge annotations that explain the primary economic engines and the single biggest risk factor for each of the 45 markets. Unlike quantitative parameters (which are numeric and real-time), drivers represent the qualitative intelligence layer — the 'why' behind the data. They are used to generate AI-written market narratives and to power the Macro Flows view.



Definition
Scenario Analysis is a forward-looking portfolio stress-testing framework that applies predefined macro shocks to a user's emerging market allocation and returns the expected dollar and percentage P&L impact. Impact coefficients are derived from the Transmission Models and historical backtests, stored as configurable database parameters rather than hardcoded values so the research team can recalibrate without code changes.




Market Parameters is the single source of truth. Correlation Matrix is the core computation engine. Crisis Predictor and Scenario Analysis are the primary user-facing outputs. Market Drivers and Transmission Models provide the contextual intelligence and narrative layer that differentiates AlphaEdge from pure data terminals.
| ALPHAEDGE
GLOBAL CORRELATION ENGINE
Developer Definitions Reference
45 Emerging Markets  ·  7 Core Modules  ·  Version 1.0  ·  February 2026 |
| --- |
|  | PURPOSE:  This document provides authoritative definitions for all 8 core modules of the AlphaEdge platform, written for AI/ML engineers, backend developers, and data engineers responsible for building the system. |
| --- | --- |
| # | Module | Primary Role | Technology Layer |
| --- | --- | --- | --- |
| 1.a | Market Parameters | Single source of truth — 45 EM market data objects | TimescaleDB + Redis |
| 1.b | Correlation Matrix | Time-varying DCC-GARCH correlations | Python / arch library |
| 1.c | Risk & Macro Scores | Composite 0-100 risk quantification per market | Composite scoring engine |
| 1.d | Crisis Predictor | 5-signal early warning system (73% accuracy) | ML ensemble + Bayesian |
| 1.e | Lead-Lag Engine | Granger causality — direction and timing of influence | Apache Flink + Neo4j |
| 1.f | Transmission Models | Calibrated macro event → sector impact pathways | Parametric regression |
| 1.g | Market Drivers | Structural growth engines + key risk per market | Knowledge graph + JSON |
| 1.h | Scenario Analysis | Portfolio P&L impact stress-testing | Monte Carlo + coefficients |
| 1.a | Market Parameters
The atomic unit of market data — the canonical data object for each emerging market |
| --- | --- |
| Field Category | Sub-fields  ·  Description  ·  Examples |
| --- | --- |
| Identity | ISO-2 code, country name, flag emoji, region (7 regions), market tier (Developed-EM / Emerging / Frontier-Plus / Frontier) |
| Index Data | Primary equity index name (e.g., NIFTY 50), current index value, daily % change, total market capitalisation in USD |
| Currency / FX | Local currency code (e.g., INR), spot rate vs USD, 1-day FX change %. Pegged currencies (SAR, AED, QAR) flagged separately |
| Macro Indicators | GDP growth %, CPI inflation %, central bank policy rate %, 10-year bond yield %, current account (% of GDP), government debt/GDP % |
| Correlations | 30-day rolling DCC-GARCH coefficients vs 5 global drivers: S&P 500, Brent Oil, USD Index (DXY), Gold spot, China Caixin PMI |
| GET  /markets/emerging       → Array<MarketParameter>  (all 45 markets) |
| --- |
| GET  /markets/{iso_code}     → MarketParameter         (single market, e.g. 'IN') |
| WS   /stream/markets         → real-time tick updates  (<50ms latency target) |
|  |
| // MarketParameter shape: |
| { id, name, tier, index_value, fx_rate, gdp_growth, cpi, interest_rate, |
| bond_yield, current_account, debt_gdp, risk_score, correlations: {spx, oil, usd, gold, china} } |
|  | Coverage:  45 emerging markets across 7 regions. Price and FX update real-time via WebSocket. Macro indicators update daily. Market tier and drivers update quarterly. |
| --- | --- |
| 1.b | Correlation Matrix
The platform's core IP — dynamic, time-varying pairwise asset correlations using DCC-GARCH |
| --- | --- |
| Concept | Explanation |
| --- | --- |
| DCC-GARCH | Dynamic Conditional Correlation model. Stage 1: fit GARCH(1,1) per asset (σ²_t = ω + α·ε²_{t-1} + β·σ²_{t-1}). Stage 2: standardise residuals. Stage 3: estimate time-varying Q_t matrix. Stage 4: extract correlation ρ_t = Q*_t^(-½) · Q_t · Q*_t^(-½) |
| Five Drivers | Each of 45 markets has 5 correlations computed: vs S&P 500 (equity risk), vs Brent Oil (commodity demand), vs DXY (dollar strength), vs Gold (safe haven), vs China PMI (commodity demand). These are stored in MarketParameter.correlations |
| Rolling Window | 30-day rolling window for live correlations. 252-day window for model parameter fitting. Recomputed on every market tick for real-time view |
| Regime Detection | 4 correlation regimes classified via Hidden Markov Model: Normal (ρ ≈ 0.65), Elevated (0.75), Stress (0.85), Crisis (0.92). The March 2020 event took Nifty-SPX from 0.65 to 0.92 in 10 days |
| Latency SLA | Full matrix recompute must complete in <500ms for 45 markets. Implemented on Apache Flink with Redis cache (5-minute TTL for matrix, real-time for individual pair updates) |
| Correlation Value | UI Colour | Portfolio Meaning |
| --- | --- | --- |
| ≥ 0.7 | Red | Strong positive — diversification benefit eliminated |
| 0.4 – 0.7 | Orange | Moderate positive — partial diversification remains |
| 0.1 – 0.4 | Green | Weak positive — good diversification |
| -0.1 – 0.1 | Grey | Uncorrelated — maximum diversification |
| -0.4 – -0.1 | Cyan | Weak negative — mild hedging benefit |
| ≤ -0.4 | Blue | Strong negative — strong hedge / inverse relationship |
| 1.c | Risk & Macro Scores
A composite 0-100 risk score synthesising six macroeconomic indicators per market |
| --- | --- |
| Macro Indicator | Definition  ·  Threshold Logic  ·  Risk Contribution |
| --- | --- |
| GDP Growth % | Real GDP growth rate. Threshold: Green ≥ 4%, Amber 2–4%, Red < 2%. Negative GDP is a CRITICAL risk signal |
| CPI Inflation % | Year-on-year consumer price inflation. Green ≤ 4%, Amber 4–8%, Orange 8–20%, Red > 20%. Hyperinflation (> 50%) maps directly to CRITICAL tier |
| Interest Rate % | Central bank policy rate. Used to compute Real Rate = Nominal Rate − CPI. Deeply negative real rates (e.g., Argentina: 60% rate − 211% CPI) signal currency crisis |
| 10Y Bond Yield % | Sovereign 10-year yield. Spread over US 10Y is the EM risk premium. High yields reflect investor distrust or inflation risk |
| Current Account % GDP | Trade + income balance as % of GDP. Persistent deficits < −3% create FX vulnerability. Surpluses (Saudi Arabia +3.8%) reduce crisis risk |
| Debt / GDP % | Total government debt. Green ≤ 50%, Amber ≤ 80%, Red > 80%. Very high debt (Greece 161%, Sri Lanka 115%) limits fiscal crisis response capacity |
| Risk Score | Tier | UI Colour | Recommended Action |
| --- | --- | --- | --- |
| 0 – 34 | LOW | Green | Allocatable — standard due diligence applies |
| 35 – 54 | MEDIUM | Amber | Monitor — watch key risk factor closely |
| 55 – 69 | HIGH | Orange | Caution — reduce position or hedge FX exposure |
| 70 – 100 | CRITICAL | Red | Avoid or reduce — crisis conditions present |
|  | Developer Note:  Risk Score is a computed field, NOT a raw data field. Recompute daily. Store historical scores in TimescaleDB for trend analysis. Do not recompute on every tick. |
| --- | --- |
| 1.d | Crisis Predictor™
5-signal early warning system — forecasts correlation regime spikes 3–7 days in advance |
| --- | --- |
| Signal | Weight  ·  Lead Time  ·  Accuracy  ·  Trigger Logic |
| --- | --- |
| 1. VIX Acceleration | 40% weight · 5-day lead time · 82% historical accuracy. Triggers if VIX 3-day percentage change exceeds +15%. VIX is the single most reliable crisis precursor |
| 2. Treasury Volatility | 25% weight · 2-day lead time · 76% accuracy. Triggers if US 10-year daily move exceeds 8bps rolling standard deviation. Signals bond market stress |
| 3. FX Stress Index | 20% weight · 3-day lead time · 71% accuracy. Triggers if EM FX composite Z-score exceeds 2.5. Monitors INR, BRL, ZAR, TRY, MXN simultaneously |
| 4. Credit Spread Widening | 10% weight · 7-day lead time · 68% accuracy. Triggers if IG credit spreads exceed their 3-month average by 15%. Longest lead time, lowest weight |
| 5. Commodity Dislocation | 5% weight · 4-day lead time · 64% accuracy. Triggers if absolute Oil-Gold correlation drops below 0.1. Near-zero correlation indicates macro dislocation |
| # Step 1: Weighted signal combination |
| --- |
| signal_score = (vix × 0.40) + (treasury × 0.25) + (fx × 0.20) + (credit × 0.10) + (commodity × 0.05) |
|  |
| # Step 2: ML ensemble confirmation (Random Forest on 200+ engineered features) |
| ml_prob = rf_model.predict_proba(feature_vector)[1] |
|  |
| # Step 3: Bayesian final output (overall accuracy: 73%, false positive: 27%) |
| crisis_probability = (0.60 × signal_score) + (0.40 × ml_prob) |
| Probability | Regime | Expected Correlation | Portfolio Action |
| --- | --- | --- | --- |
| 0% – 40% | NORMAL | 0.65 – 0.70 | Maintain allocation |
| 40% – 60% | WATCH | 0.70 – 0.78 | Review hedges, monitor |
| 60% – 70% | ELEVATED | 0.78 – 0.85 | Reduce equities 10%, add Gold |
| 70% – 85% | CRITICAL | 0.85 – 0.92 | Reduce equities 15-20%, buy puts |
| > 85% | CRISIS | 0.90 – 0.95+ | Maximum defensive posture |
| 1.e | Lead-Lag Engine
Granger causality network — which variable moves first, which follows, and by how many days |
| --- | --- |
| Concept | Explanation for Developers |
| --- | --- |
| Granger Causality | Statistical hypothesis test: 'X Granger-causes Y' if lagged values of X significantly improve prediction of Y beyond Y's own history. Validated at p < 0.05. Implemented as rolling 60-day window VAR models |
| Lag (Days) | The typical delay between the leading variable moving and the lagging variable responding. Examples: DXY → INR = 0 days (same session); S&P 500 → Nifty = 1 day; Oil → India CPI = 30 days; China PMI → Iron Ore = 1 day |
| Strength (0–1) | Magnitude of the causal effect, derived from the F-statistic of the Granger test. > 0.80 = strong (S&P 500 → Nifty: 0.82). 0.65–0.80 = moderate. < 0.65 = weak |
| Bi-directional | Some pairs are mutually causal. FII Flows ↔ Nifty 50 (SEBI Research 2024 confirmed). Both Granger-cause each other. The engine handles bidirectional graphs in Neo4j |
| Key Relationships | US 10Y → India 10Y Bond (2-day lag, strength 0.85). VIX → EM Selloff (5-day lag, 0.89 — strongest). DXY → INR (0-day, 0.91 — same session). Oil → India CPI (30-day, 0.78). China PMI → Iron Ore (1-day, 0.88) |
| Storage | Causal network stored in Neo4j graph database. Nodes = financial variables. Edges = Granger relationships with properties: lag_days, strength, p_value, research_source, last_validated |
|  | Key Differentiator:  Bloomberg shows correlations. AlphaEdge shows which variable leads and by how many days. This enables predictive alerts — e.g., VIX just spiked 18%, expect EM selloff in 5 days — before the lagging market reacts. |
| --- | --- |
| 1.f | Transmission Models
Calibrated impact pathways — how a macro event propagates through currencies, sectors, and time |
| --- | --- |
| Model | Input  →  Transmission Chain  ·  Key Calibrated Coefficients |
| --- | --- |
| Model 1: US Fed Hike → India | Input: Rate hike in bps → DXY strengthens (+0.8% per 100bps) → FII outflow (Rs 800–1200 Cr per 50bps, T+1-2 days) → Nifty decline (−0.15% per Rs 1000 Cr outflow, T+2-5 days) → Sector impacts: IT +0.5–1.2% (USD revenue), Banks −1.2%, Auto −0.8%, Pharma +0.3%, OMCs −0.3%. Confidence: 76% |
| Model 2: Oil Price Change → India | Input: Brent % change → OMCs (IOC, BPCL, HPCL): −1.2× input% immediately → INR depreciation: −4% per 10% oil rise → India CPI: +1.5% per 10% oil (30-day lag) → RBI hawkish probability 65% if Brent > $90 → Beneficiaries: IT and Pharma exporters via weak INR. Confidence: 74% |
| Model 3: China PMI Miss → Commodities | Input: PMI points below 50 → Immediate commodity impact: Iron Ore −2.5% per point, Copper −1.8%, Coal −2.0% → India metals (T+1-5): Tata Steel −1.5%, Hindalco −1.0% → India infra (T+3-10): Cement −0.8%, L&T −0.6% → Also hits Africa commodity exporters and Chile copper equities. Confidence: 71% |
| class TransmissionModel: |
| --- |
| def run(self, event: MacroEvent) -> TransmissionResult: |
| coefficients = self.load_coefficients(event.type)  # from DB, not hardcoded |
| impacts = {sector: event.magnitude * coeff for sector, coeff in coefficients.items()} |
| return TransmissionResult( |
| immediate=impacts['T0-T2'], medium_term=impacts['T3-T30'], |
| confidence=coefficients['accuracy'], |
| scenarios={ bear: impacts['bear'], base: impacts['base'], bull: impacts['bull'] } |
| ) |
| # Coefficients stored in PostgreSQL — updatable by research team without code deploy |
|  | UI Use:  The Market Deep Dive panel renders a 6-step visual flow: Fed hike → DXY up → FII outflow → INR falls → IT benefits → Nifty dips. Each arrow shows the magnitude and confidence. |
| --- | --- |
| 1.g | Market Drivers
Curated economic intelligence — the structural growth engines and single biggest risk per market |
| --- | --- |
| Field | Definition  ·  Purpose  ·  Examples |
| --- | --- |
| Drivers 1–4 (Growth Engines) | Top 4 structural sources of economic activity or market performance. These are semi-static — reviewed quarterly by the research team. Examples: India → IT Exports, FII Flows, Oil Imports, Monsoon Cycle. Saudi Arabia → Oil (OPEC+), Vision 2030, NEOM project, Aramco dividends |
| Key Risk (Single Factor) | The one structural factor that, if it deteriorates, most directly threatens that market. Used in Risk Radar view and crisis alert copy. Examples: India → Oil Price Shock. Argentina → Hyperinflation. Taiwan → Geopolitical (China) Risk. Nigeria → FX Volatility |
| Classification Tags | Drivers are tagged by category: Commodity, Exports, Policy Reform, FDI, Remittances, Tourism, Domestic Consumption. Tags power the Macro Flows view: the Oil Winners panel selects markets where oilCorr > 0.5; China-Linked panel selects chinaCorr > 0.5 |
| AI Narrative Use | The AI narrative engine (LLM) uses Drivers + Risk as structured context to generate plain-English market summaries. E.g., 'India benefits from USD strength through IT export revenues but faces risk from elevated oil prices widening its current account deficit' |
| Market | Driver 1 | Driver 2 | Key Risk |
| --- | --- | --- | --- |
| India (IN) | IT Exports | FII Flows | Oil Price Shock |
| Vietnam (VN) | Manufacturing | Electronics Exp | China Slowdown |
| Nigeria (NG) | Oil (NNPC) | Agriculture | FX Volatility |
| Saudi Arabia (SA) | Oil (OPEC+) | Vision 2030 | Oil Price Fall |
| Argentina (AR) | IMF Program | Soybean | Hyperinflation |
| Taiwan (TW) | TSMC/Semicon | AI Demand | Geopolitical Risk |
| 1.h | Scenario Analysis
Forward-looking portfolio stress testing — quantify P&L impact of macro shocks before they occur |
| --- | --- |
| Component | Description  ·  Implementation Detail |
| --- | --- |
| Scenario Input | A named macro event with a single input parameter (e.g., rate_change = 0.50 for Fed Hike 50bps, or oil_change = +$10 for Oil Surge). 10 standard scenarios pre-built; custom scenarios supported via POST /scenarios/custom |
| Impact Coefficient | Empirically calibrated multiplier: portfolio_impact_pct = input_magnitude × coefficient. E.g., Fed Hike 50bps coefficient = −0.0099 → −0.99% on diversified EM portfolio. Stored in PostgreSQL table scenario_coefficients with version history |
| Dollar Impact | Portfolio AUM is user-specified. Dollar impact = AUM × impact_pct. Both displayed in the UI. Example: $847M AUM × −0.99% = −$8.38M expected impact |
| Confidence Interval | Each scenario has a historical accuracy score (e.g., Fed Hike model: 76%) plus bear/base/bull bands. Bull assumes correlation stays low; bear assumes correlation spikes per Crisis Predictor output |
| Timeline | Each scenario specifies when peak impact is expected. Fed Hike peaks T+2-5 days (FII flow channel). Oil Surge peaks T+30+ days (CPI / RBI channel). EM Crisis peaks T+0-14 days (immediate correlation contagion) |
| Scenario | Trigger Input | Expected EM Impact | Confidence |
| --- | --- | --- | --- |
| Fed Hike 50bps | +0.50% rate | −0.99% portfolio | 76% |
| Oil Surge $10 | Brent +$10 | −1.43% portfolio | 74% |
| China Stimulus | PMI: 49 → 53 | +1.79% portfolio | 68% |
| USD Strength +5% | DXY: 104 → 109 | −1.80% portfolio | 71% |
| EM Crisis Event | VIX spikes above 35 | −12.0% portfolio | 73% |
| Global Recession | S&P 500 falls 20% | −14.0% portfolio | 65% |
|  | Developer Note:  Scenario coefficients must be stored as configurable DB parameters (table: scenario_coefficients), not hardcoded. The research team must be able to recalibrate coefficients via an admin interface when market conditions change — without a code deployment. |
| --- | --- |
| MODULE DEPENDENCY & DATA FLOW
Market Parameters (1.a) → feeds all modules
↓                              ↓                              ↓
Correlation Matrix (1.b)  ·  Risk Scores (1.c)  ·  Lead-Lag Engine (1.e)
↓                              ↓
Crisis Predictor (1.d)    ·    Transmission Models (1.f)
↓                              ↓                              ↓
Market Drivers (1.g) provides context  →  Scenario Analysis (1.h) is user-facing output |
| --- |