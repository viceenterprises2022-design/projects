<!-- converted from AlphaEdge_Macro_State_Engine_Spec_v1.1.docx -->





What is the Macro State Engine?
The Global Macro State Engine is a continuously-running backend service that synthesises raw macro data from central banks, commodity markets, and economic indicators into a clean, structured 'World State' object. Every other module in AlphaEdge — the Crisis Predictor, Correlation Matrix, Scenario Analysis, and all user alerts — reads from this state object rather than raw data feeds.
Without this engine, each module would independently parse contradictory data sources and reach inconsistent conclusions. The Macro State Engine is the single arbiter of macro reality for the platform.


WHY THIS MODULE EXISTS

Central banks and commentators treat interest rates as the proxy for liquidity. This is incomplete and lags reality. A central bank can hold rates flat while draining billions from the financial system through QT (Quantitative Tightening) and bond issuance. The Liquidity Thermostat measures the actual flow of money — not the price of money — to detect contractions that interest rate watchers will miss.

DATA INPUTS — What to Fetch and From Where



CORE FORMULA — Liquidity_Impulse


Breaking Down the Formula

Example Calculation (Illustrative)

THRESHOLD LOGIC — State Machine

The Thermostat uses a state machine (not a simple threshold) to avoid false positives from single-week noise. A regime change requires sustained signals.


IMPLEMENTATION — Code Skeleton


OUTPUTS — What Downstream Modules Consume



WHY THIS MODULE EXISTS

Inflation is not a single variable — it is the sum of structurally different pressures that demand different policy responses. A central bank will react very differently to energy inflation (often wait, as it's transitory) versus demand inflation (will hike aggressively). For emerging markets, this distinction is critical: energy inflation is bearish for oil importers (India, Japan, Korea) but bullish for exporters (Nigeria, Saudi Arabia, Russia).
A model that only reads headline CPI cannot distinguish these cases. The Inflation Vector decomposes the number into its three structural components, enabling the platform to predict: (1) what the central bank will do, and (2) which countries and sectors benefit or suffer.

THE THREE INFLATION VECTORS — Definition and Data







DECOMPOSITION LOGIC — Classification Algorithm

Once the three vectors are computed, the module classifies the dominant inflation source and sets the policy bias:

COUNTRY IMPACT MATRIX — Inflation Source → Market Impact



OUTPUTS — What Downstream Modules Consume



WHY THIS MODULE EXISTS

GDP is a lagging indicator — it is released quarterly, revised multiple times, and reflects economic activity from months ago. By the time GDP confirms a recession, equity markets have typically already sold off 20–30%. Earnings revisions are leading, but still lag PMI data by 1–3 months. The Growth Diffusion module uses the earliest possible signals — PMI breadth, earnings revision trends, and China credit impulse — to predict the regime shift before GDP or earnings confirm it.
For emerging markets, China's credit cycle is the single most powerful leading indicator for global growth. Because China accounts for ~55% of global commodity demand, a shift in China's credit expansion leads commodity prices by 3–6 months, which then leads EM earnings by another 1–3 months.

DATA INPUTS — Three Leading Indicators







REGIME CLASSIFICATION LOGIC


THE CHINA CREDIT IMPULSE CASCADE — Visual Logic

When China Credit Impulse drops below zero and sustains, the following cascade is expected (with historical lags):


OUTPUTS — What Downstream Modules Consume



State Combination Logic
The three modules run independently and asynchronously. Each updates its slice of the World State at its own cadence. A master State Aggregator reads all three outputs and produces the final composite State of the World on each update.




The Global Macro State Engine is the platform's highest-leverage engineering component. A well-built State Engine makes every downstream module more accurate, faster, and easier to maintain. Its outputs — three regime fields and a composite bias score — are lightweight to transmit but encode weeks of macro signal processing.
| ALPHAEDGE
GLOBAL MACRO STATE ENGINE
The Backend Brain — Complete Developer Specification
Module 2.1: Liquidity Thermostat  ·  Module 2.2: Inflation Vector  ·  Module 2.3: Growth Diffusion |
| --- |
|  | PURPOSE:  This document provides a complete, implementation-ready specification for the three modules of the Global Macro State Engine. It is the central nervous system of AlphaEdge — running continuously to produce the 'State of the World' that drives all user-facing alerts and models. |
| --- | --- |
| Module | Role | Primary Output | Update Frequency |
| --- | --- | --- | --- |
| 2.1 — Liquidity Thermostat | Quantify global liquidity conditions | Liquidity_Impulse score + Regime State | Daily (balance sheet data) |
| 2.2 — Inflation Vector | Decompose inflation source for policy logic | Inflation_Source tag + Policy_Bias signal | Real-time (commodity + FX) |
| 2.3 — Growth Diffusion | Predict earnings recessions early | Growth_Regime + Commodity_Deflation_Risk flag | Weekly (PMI + credit data) |
| 2 | Global Macro State Engine
The central nervous system — runs continuously to produce a unified 'State of the World' consumed by all downstream modules |
| --- | --- |
| # World State Object — consumed by ALL downstream modules |
| --- |
| world_state = { |
| 'liquidity': { |
| 'impulse': -142.5,           # $ billions, negative = contracting |
| 'regime': 'Contraction',     # Normal | Expansion | Contraction | Crisis |
| 'basis_swap_bps': 28,        # USD funding stress level |
| }, |
| 'inflation': { |
| 'source': 'Energy-Driven',   # Energy | FX-Imported | Demand | Mixed |
| 'policy_bias': 'Hawkish',    # Hawkish | Neutral | Dovish |
| 'importer_impact': 'Bearish',# Per-country flag |
| }, |
| 'growth': { |
| 'regime': 'Slowdown',        # Expansion | Slowdown | Recession | Recovery |
| 'commodity_risk': True,      # Commodity deflation risk flag |
| 'earnings_revision': -0.32,  # Breadth score (-1 to +1) |
| }, |
| 'last_updated': '2026-02-17T14:30:00Z' |
| } |
| 2.1 | Module A: The Liquidity Thermostat
Objective: Quantify true global liquidity — not just interest rates — to detect tightening before it shows in markets |
| --- | --- |
|  | Real Example (2022):  The Fed's first rate hike was March 2022. But liquidity had been draining since November 2021 as Treasury issuance surged and QE slowed. Markets peaked in January 2022 — 2 months before the first hike. The Thermostat would have flagged Contraction in December 2021. |
| --- | --- |
| Data Input | Source  ·  Endpoint  ·  Update Frequency |
| --- | --- |
| Fed Balance Sheet (SOMA) | FRED API: WALCL (Total Assets). Free. URL: api.stlouisfed.org/fred/series/observations?series_id=WALCL. Weekly release (every Thursday). Units: USD Millions |
| ECB Balance Sheet | ECB Data Portal: BSI.M.U2.N.A.A20T.A.1.U6.2250.Z01.E series. Monthly. Alternative: ecb.europa.eu/home/html/rss.en.html |
| PBoC Balance Sheet | PBoC official: pbc.gov.cn → Statistics → Monetary Statistics. Monthly. Also available via CEIC or Bloomberg (PBoC:TOAS). Units: CNY Billions (convert to USD) |
| BoJ Balance Sheet | Bank of Japan: boj.or.jp/en/statistics/boj/other/acnt. Weekly. Series: Total Assets. Units: JPY Billions (convert to USD) |
| US Treasury Issuance | US Treasury FiscalData API: fiscaldata.treasury.gov/api/data/debt-to-the-penny. Daily. Also TreasuryDirect auctions calendar for forward-looking data |
| Reverse Repo (RRP) | FRED: RRPONTSYD (Overnight Reverse Repurchase Agreements). Daily. Units: USD Billions. This is the 'absorption' side — high RRP = liquidity not reaching the economy |
| Cross-Currency Basis Swaps | Bloomberg (EURUSD Basis: EUBS3M BGN or similar) OR Refinitiv Eikon. 3-month basis swap vs USD for EUR, JPY, GBP. Units: basis points. Daily. Note: this data typically requires a paid terminal; fallback = proxy via FX forward premium/discount |
|  | Developer Note:  Central bank balance sheets are the hardest data to normalise — they are released on different schedules (weekly Fed, monthly ECB/PBoC) in different currencies and units. Build a currency_normalise(value, currency, date) utility first. All balance sheets must be converted to USD billions using the spot rate on the observation date. |
| --- | --- |
| Liquidity_Impulse = Δ(Global CB Assets) − Δ(Treasury Issuance) |
| --- |
| Change in combined central bank balance sheets minus net new Treasury debt issued to the market |
| Component | Meaning  ·  How to Compute  ·  Sign Interpretation |
| --- | --- |
| Δ(Global CB Assets) | Week-over-week (or month-over-month) change in the sum of: Fed + ECB + PBoC + BoJ total assets, all converted to USD billions at current FX rates. POSITIVE = central banks are expanding balance sheets (injecting money). NEGATIVE = QT / withdrawal of liquidity |
| Δ(Treasury Issuance) | Net new US Treasury debt issued to the public in the period. Use Treasury FiscalData API: (new auctions settled) minus (maturities redeemed). POSITIVE = government is absorbing private sector money. NEGATIVE = net redemptions (rare, adds liquidity) |
| Net Impulse (+ or -) | POSITIVE impulse = central banks adding more liquidity than Treasury is absorbing → bullish for risky assets. NEGATIVE impulse = QT or issuance surge draining net liquidity → bearish signal even if rates unchanged |
| RRP Adjustment | Optional but important: if RRP balance is high and rising, this indicates injected liquidity is being 'sterilised' (parked at the Fed, not reaching markets). Subtract rising RRP from Impulse: Liquidity_Impulse_adj = Impulse − Δ(RRP) |
| # Week of Feb 10-17, 2026 (illustrative numbers) |
| --- |
| delta_fed     = -12.5  # Fed balance sheet shrank $12.5B (QT ongoing) |
| delta_ecb     = -8.2   # ECB balance sheet shrank €7.5B → $8.2B |
| delta_pboc    = +3.1   # PBoC expanded CNY 22B → $3.1B |
| delta_boj     = -5.8   # BoJ shrinking slowly → -$5.8B USD equivalent |
|  |
| delta_global_cb = delta_fed + delta_ecb + delta_pboc + delta_boj |
| # = -12.5 + (-8.2) + 3.1 + (-5.8) = -23.4  (net QT week) |
|  |
| delta_treasury_issuance = +118.7  # $118.7B net Treasury auction settlement |
|  |
| rrp_change = -32.0  # RRP fell $32B (money leaving Fed → markets, slight positive) |
|  |
| liquidity_impulse = delta_global_cb - delta_treasury_issuance + abs(rrp_change) |
| # = -23.4 - 118.7 + 32.0 = -110.1 billion (NEGATIVE = contracting) |
| State Trigger | Condition | Duration Required | Output State |
| --- | --- | --- | --- |
| → Contraction | Liquidity_Impulse < 0 AND Basis Swaps > +20bps vs 3M avg | > 3 consecutive weeks | State = 'Contraction' |
| → Crisis | Liquidity_Impulse < −200B AND Basis Swaps > +50bps | Any single reading | State = 'Crisis' (immediate) |
| → Normal | Liquidity_Impulse within ±50B AND Basis Swaps < +10bps | > 2 consecutive weeks | State = 'Normal' |
| → Expansion | Liquidity_Impulse > +100B AND Basis Swaps < 0bps (easing) | > 2 consecutive weeks | State = 'Expansion' |
| Basis Swap role | If basis swaps widen > 20bps independently: add 0.5 weight to contraction check | Any duration | Amplifier, not sole trigger |
|  | Why Basis Swaps?  Cross-currency basis swaps measure USD funding stress. A negative EUR/USD basis (e.g., -25bps) means European banks are paying a premium to borrow dollars — a sign of dollar scarcity globally. This was a key stress signal in March 2020 (basis hit -100bps) and September 2022 (hit -50bps). It complements balance sheet data by showing real-economy dollar demand pressure. |
| --- | --- |
| class LiquidityThermostat: |
| --- |
| def __init__(self, lookback_weeks=3): |
| self.lookback = lookback_weeks |
| self.history = []  # rolling window of weekly impulse readings |
| self.state = 'Normal' |
|  |
| def ingest_weekly(self, cb_assets: dict, treasury_net: float, rrp: float, basis_swap_bps: float): |
| # Step 1: Normalise CB assets to USD billions |
| fed_usd  = cb_assets['fed'] / 1000          # FRED = millions, convert to billions |
| ecb_usd  = cb_assets['ecb_eur'] * self.eur_usd |
| pboc_usd = cb_assets['pboc_cny'] * self.cny_usd |
| boj_usd  = cb_assets['boj_jpy'] * self.jpy_usd |
| global_cb_total = fed_usd + ecb_usd + pboc_usd + boj_usd |
|  |
| # Step 2: Compute delta vs prior week |
| if self.history: |
| delta_cb = global_cb_total - self.history[-1]['global_cb_total'] |
| else: |
| delta_cb = 0 |
|  |
| # Step 3: Compute impulse |
| delta_rrp = rrp - (self.history[-1]['rrp'] if self.history else rrp) |
| impulse = delta_cb - treasury_net + max(0, -delta_rrp)  # rising RRP = negative |
|  |
| # Step 4: Update state machine |
| self.history.append({ 'impulse': impulse, 'basis': basis_swap_bps, |
| 'global_cb_total': global_cb_total, 'rrp': rrp }) |
| if len(self.history) > self.lookback: self.history.pop(0) |
| self._update_state(basis_swap_bps) |
| return { 'impulse': impulse, 'state': self.state, 'basis': basis_swap_bps } |
|  |
| def _update_state(self, current_basis_bps): |
| basis_3m_avg = self._get_basis_3m_average()  # from Redis / DB |
| basis_widened = current_basis_bps > (basis_3m_avg + 20) |
| recent = self.history[-self.lookback:] |
| all_negative = all(w['impulse'] < 0 for w in recent) |
| crisis_reading = recent[-1]['impulse'] < -200 and current_basis_bps > 50 |
| if crisis_reading: |
| self.state = 'Crisis' |
| elif len(recent) == self.lookback and all_negative and basis_widened: |
| self.state = 'Contraction' |
| elif all(abs(w['impulse']) < 50 for w in recent[-2:]) and current_basis_bps < 10: |
| self.state = 'Normal' |
| elif all(w['impulse'] > 100 for w in recent[-2:]) and current_basis_bps < 0: |
| self.state = 'Expansion' |
| # else: state unchanged (persistence, avoids noise flipping) |
| Output Field | Type | Values | Consumer Module |
| --- | --- | --- | --- |
| liquidity.impulse | float | USD billions, +/- | Scenario Analysis, Crisis Predictor |
| liquidity.regime | string | Normal | Expansion | Contraction | Crisis | ALL modules — primary state |
| liquidity.basis_bps | float | basis points vs 3M average | FX Stress Index in Crisis Predictor |
| liquidity.rrp_delta | float | weekly change in RRP balance | Inflation Vector (demand channel) |
| liquidity.alert | boolean | true if regime changed this period | Alert system → push to users |
| 2.2 | Module B: The Inflation Vector
Objective: Decompose inflation into its structural source to predict policy responses before central banks announce them |
| --- | --- |
|  | Real Example (2022):  India's CPI hit 7.8% in April 2022. A naive model says 'high inflation = RBI hikes = bearish equities.' The Vector decomposition showed 72% was Energy-Driven (Russia-Ukraine) and 18% FX-Imported (weak INR). RBI's correct response was a 40bps emergency hike — but the real impact was OMC stocks collapsing -18% while IT exporters gained +8%. Only the Vector explains this divergence. |
| --- | --- |
| V1 | Energy Vector — Commodity-Driven Price Pressure |
| --- | --- |
| Aspect | Detail |
| --- | --- |
| Definition | The contribution of energy commodity price changes to headline inflation. Captured via momentum of Brent crude and WTI as the primary variables, with secondary inputs from natural gas (Henry Hub), coal spot prices, and agricultural commodities (wheat, palm oil) for food-energy overlap |
| Calculation | Energy_Vector = (Brent_30d_momentum × oil_import_share_of_CPI) + (Gas_30d_momentum × gas_CPI_weight). Each country has a different energy weight in its CPI basket. For India: oil ≈ 12% of CPI basket; for Saudi Arabia: near zero (subsidised). These weights must be stored per-market in the database |
| Data Inputs | Brent front-month futures: Barchart or Quandl. Natural Gas (Henry Hub/TTF): EIA API (eia.gov) free. CPI basket weights: IMF country data, updated annually. Momentum: 30-day rate of change (not level) |
| Signal Output | Energy_Vector > +0.5% of CPI = Energy inflation is dominant. Positive for exporters (Nigeria, Saudi Arabia, Colombia), negative for importers (India, Korea, Japan, Germany) |
| V2 | FX-Imported Vector — Currency Depreciation Pass-Through |
| --- | --- |
| Aspect | Detail |
| --- | --- |
| Definition | The contribution to domestic inflation from currency depreciation against the USD. When a local currency weakens, imports become more expensive, and this passes through to consumer prices. The speed and magnitude of this pass-through varies by economy — more open economies (Singapore 0.8 pass-through) have higher sensitivity than closed ones (India 0.3 pass-through) |
| Calculation | FX_Vector = Currency_30d_change_vs_USD × Pass_Through_Coefficient. Example: INR depreciates 5% in 30 days; India pass-through coefficient = 0.3; FX_Vector = 5% × 0.3 = 1.5% inflation contribution. Pass-through coefficients sourced from IMF research, stored per-market in the DB |
| Data Inputs | FX spot rates vs USD: OANDA API (free) or Twelve Data. 30-day rolling change. Pass-through coefficients: static DB table, sourced from IMF WP/2022/028 or equivalent research papers. Updated when IMF publishes new estimates |
| Signal Output | FX_Vector > +0.3% of CPI = imported inflation becoming relevant. Indicator of FX crisis risk if sustained. Also fed into Risk Score calculation for current account deficit markets |
| V3 | Demand Vector — Wage Growth + Credit Impulse Pressure |
| --- | --- |
| Aspect | Detail |
| --- | --- |
| Definition | The contribution to inflation from domestic demand growth — measured by wage growth and credit expansion. This is the most persistent and policy-sensitive vector. Central banks prioritise fighting demand inflation because it reflects overheating, not external shocks. If Demand_Vector is high, expect sustained and aggressive rate hikes |
| Calculation | Demand_Vector = (Wage_Growth_3M_annualised × 0.5) + (Credit_Impulse_3M × 0.5). Credit Impulse = Change in the rate of new credit creation (second derivative of credit). Credit_Impulse = (New_Credit_3M / GDP) − (New_Credit_3M_prior / GDP). Positive and rising = inflationary pressure building |
| Data Inputs | Wage growth: country-specific labour statistics bureaus (BLS for US, MoSPI for India, ISTAT for Italy). Typically monthly or quarterly. Credit data: central bank monetary statistics (M3, private sector credit). FRED for US, RBI DBIE for India, ECB SDW for Europe. Credit Impulse calculation requires 6-month history minimum |
| Signal Output | Demand_Vector > +0.4% of CPI = demand inflation is significant. This triggers 'Hawkish' policy_bias flag regardless of energy prices. Historically: when Demand_Vector > 0.6%, central banks have hiked within 2 meetings (>80% accuracy) |
| class InflationVector: |
| --- |
| SOURCES = ['Energy-Driven', 'FX-Imported', 'Demand-Driven', 'Mixed', 'Benign'] |
|  |
| def decompose(self, market_id: str, cpi_headline: float) -> dict: |
| weights = self.db.get_cpi_basket_weights(market_id)  # energy_wt, fx_wt, demand_wt |
| pass_through = self.db.get_passthrough_coeff(market_id) |
|  |
| # Compute each vector contribution (percentage points of CPI) |
| energy_contrib  = self.brent_momentum_30d * weights['energy'] |
| fx_contrib      = self.fx_30d_change(market_id) * pass_through |
| demand_contrib  = (self.wage_growth(market_id) * 0.5) + (self.credit_impulse(market_id) * 0.5) |
| unexplained     = cpi_headline - (energy_contrib + fx_contrib + demand_contrib) |
|  |
| # Classify dominant source (threshold: >40% of headline CPI) |
| total = abs(energy_contrib) + abs(fx_contrib) + abs(demand_contrib) |
| shares = { 'energy': energy_contrib/total, 'fx': fx_contrib/total, 'demand': demand_contrib/total } |
|  |
| if max(shares.values()) > 0.50:             # one source > 50% |
| source = max(shares, key=shares.get).capitalize() + '-Driven' |
| elif shares['energy'] + shares['fx'] > 0.60: |
| source = 'Supply-Driven' |
| elif cpi_headline < 2.0: |
| source = 'Benign' |
| else: |
| source = 'Mixed' |
|  |
| # Policy bias: central bank likely response |
| policy_bias = 'Hawkish' if shares['demand'] > 0.35 else \ |
| 'Cautious-Hawkish' if shares['demand'] > 0.20 else \ |
| 'Wait-and-See' if source == 'Energy-Driven' else 'Neutral' |
|  |
| # Country-specific implication |
| is_exporter = self.db.get_commodity_role(market_id, 'oil')  # 'exporter'|'importer' |
| importer_impact = 'Bearish' if (source == 'Energy-Driven' and is_exporter == 'importer') \ |
| else 'Bullish' if (source == 'Energy-Driven' and is_exporter == 'exporter') \ |
| else 'Neutral' |
|  |
| return { 'source': source, 'policy_bias': policy_bias, 'importer_impact': importer_impact, |
| 'vectors': { 'energy': energy_contrib, 'fx': fx_contrib, 'demand': demand_contrib }, |
| 'shares': shares, 'confidence': self._confidence(shares) } |
| Inflation Source | Oil Importers (India, Korea, Japan) | Oil Exporters (Nigeria, SA, Colombia) | Policy Implication |
| --- | --- | --- | --- |
| Energy-Driven | BEARISH — OMCs, airlines hit; CAD widens; INR weakens | BULLISH — fiscal surplus; FX strengthens; equities rise | Wait-and-see OR one hike (viewed as transitory) |
| FX-Imported | BEARISH — broad purchasing power loss; RBI forced to hike | NEUTRAL — limited exposure if commodity priced in USD | Hike to defend currency + attract FII flows |
| Demand-Driven | NEUTRAL-BEARISH — growth-driven; rate hikes slow consumption | NEUTRAL — domestic demand strong; rate normalisation | Aggressive multi-hike cycle (Fed 2022 pattern) |
| Mixed | MOST BEARISH — multiple pressures simultaneously | MIXED — oil benefit offset by imported inflation | Aggressive hikes with supply-side policy measures |
| Benign (<2%) | BULLISH — consumer spending power intact; dovish CB | NEUTRAL — low commodity demand signal | Rate cuts or extended pause (stimulus mode) |
|  | Developer Note:  The commodity role for each market (oil importer vs exporter) must be stored in the DB as market_meta.commodity_role. This drives the importer_impact output field. India, Korea, Japan, Thailand = importers. Nigeria, Saudi Arabia, UAE, Kuwait, Colombia, Norway = exporters. This is a static field updated when a country's trade composition materially changes. |
| --- | --- |
| Output Field | Type | Values | Consumer |
| --- | --- | --- | --- |
| inflation.source | string | Energy-Driven | FX-Imported | Demand-Driven | Mixed | Benign | Transmission Models, Narrative Engine |
| inflation.policy_bias | string | Hawkish | Cautious-Hawkish | Wait-and-See | Neutral | Dovish | Scenario Analysis, Crisis Predictor |
| inflation.importer_impact | string | Bearish | Bullish | Neutral — per market | Market Deep Dive, Risk Radar |
| inflation.vectors | object | { energy: float, fx: float, demand: float } in % of CPI | Macro Flows view, audit trail |
| inflation.shares | object | { energy: 0.62, fx: 0.18, demand: 0.20 } — sums to 1 | UI inflation breakdown chart |
| inflation.confidence | float | 0–1 confidence in decomposition | Alert suppression if < 0.6 |
| 2.3 | Module C: Growth Diffusion
Objective: Predict earnings recessions 3–6 months before they appear in GDP data using real-time leading indicators |
| --- | --- |
|  | Real Example (2015–16):  China Credit Impulse peaked in Q3 2014. Commodity prices peaked 3 months later (Q4 2014). EM earnings peaked 6 months after that (Q2 2015). S&P 500 peaked in May 2015. A model watching China Credit Impulse in Q3 2014 had a 9–12 month warning of the 2015–16 EM bear market. |
| --- | --- |
| D1 | Global PMI Diffusion Indices |
| --- | --- |
| Aspect | Detail |
| --- | --- |
| What is a PMI? | Purchasing Managers' Index: a survey of corporate purchasing managers asking if conditions are Better / Same / Worse vs last month. Diffusion Index = % reporting Better + 0.5 × % reporting Same. Above 50 = expansion. Below 50 = contraction. Released monthly, typically on the first business day (manufacturing) and first week (services) |
| What is Diffusion Breadth? | The percentage of countries / regions with PMI above 50. This is different from the average PMI level. Breadth falling from 80% to 45% (i.e., half of economies contracting) is a far stronger signal than the average PMI falling from 52 to 50. Breadth is a diffusion score of the diffusion index |
| Data Inputs Required | JP Morgan Global Manufacturing PMI (via Markit/S&P Global). US ISM Manufacturing PMI (ism.ws, free). China Caixin Manufacturing PMI (caixin.com or Trading Economics). Germany IFO Business Climate (ifo.de). India HSBC Manufacturing PMI. Eurozone PMI (S&P Global). Calculate breadth across 15–20 country PMIs |
| Calculation | PMI_Breadth = count(PMI > 50) / total_countries_tracked. Rolling 3-month change in breadth: delta_breadth = PMI_Breadth_now − PMI_Breadth_3M_ago. If delta_breadth < -15% points: growth is decelerating globally |
| D2 | Earnings Revision Breadth |
| --- | --- |
| Aspect | Detail |
| --- | --- |
| What is it? | The net percentage of equity analysts revising their earnings estimates upward vs downward for the following 12 months. Breadth = (Upgrades − Downgrades) / Total Revisions. Ranges from -100% (all downgrades) to +100% (all upgrades). This is a forward-looking signal on corporate profitability |
| Why breadth not direction? | Individual upgrades/downgrades are noisy. Breadth captures whether the revision trend is broad-based (systematic economic factor) or idiosyncratic (single company/sector). Broad-based downward revisions (-30% or worse) historically precede index-level earnings recession by 1–3 months |
| Data Sources | Bloomberg: BEST_EPS_REVISION_DIFF field. Alternatively: I/B/E/S via Refinitiv. For free approximation: manually track analyst consensus shifts from financial news aggregators. For MVP: use monthly consensus EPS from earnings aggregators (macrotrends.net, EDGAR for US). Note: quality data here typically requires Bloomberg or Refinitiv access |
| Calculation | revision_breadth = (sum_upgrades - sum_downgrades) / total_revisions. Window: rolling 3 months to smooth noise. Threshold: if revision_breadth < -0.30 for 2 consecutive months → earnings recession flagged |
| D3 | China Credit Impulse — The Most Powerful Leading Indicator |
| --- | --- |
| Aspect | Detail |
| --- | --- |
| Definition | The Credit Impulse is the change in the FLOW of new credit as a percentage of GDP. It is the second derivative of credit — not the level of debt, not even the growth of debt, but the acceleration or deceleration of new credit creation. This matters because credit impulse measures whether the financial system is becoming more or less stimulative |
| Why China Specifically? | China's credit system directly determines demand for global commodities: steel, copper, iron ore, coal, soybeans. When China's credit impulse rises, infrastructure and real estate projects accelerate, driving commodity demand globally. The lag: Credit Impulse peaks → commodity prices peak (3M) → commodity exporter revenues peak (3–6M) → EM earnings peak (6–12M) |
| Formula | Credit_Impulse = (New_Credit_Issued_This_Quarter / Nominal_GDP_This_Quarter) − (New_Credit_Issued_Last_Quarter / Nominal_GDP_Last_Quarter). Where New_Credit = change in total social financing (TSF) or bank loans outstanding |
| Data Source | PBoC: monthly Total Social Financing data (tinyurl.com/pboc-tsf or pbc.gov.cn English statistics). Also available: Bloomberg (CNFINR Index), Refinitiv, or China NBS. GDP: quarterly from National Bureau of Statistics of China (stats.gov.cn) |
| Threshold Logic | Credit_Impulse drops below 0 for 2 consecutive months → Set flag: 'Commodity_Deflation_Risk = True'. Lag before market impact: 3–6 months. Historical accuracy: ~71% at predicting commodity price declines of >10% within 6 months |
| class GrowthDiffusion: |
| --- |
| REGIMES = ['Expansion', 'Slowdown', 'Recession', 'Recovery'] |
|  |
| def classify_regime(self) -> dict: |
| # Input 1: Global PMI Breadth (% of countries with PMI > 50) |
| pmi_breadth = self._compute_pmi_breadth() |
| pmi_breadth_delta_3m = pmi_breadth - self._pmi_breadth_3m_ago() |
|  |
| # Input 2: Earnings Revision Breadth (-1 to +1) |
| revision_breadth = self._compute_revision_breadth() |
|  |
| # Input 3: China Credit Impulse (quarterly, % of GDP change) |
| china_credit_impulse = self._compute_china_credit_impulse() |
| china_impulse_falling = china_credit_impulse < 0 |
| china_impulse_consecutive = self._china_impulse_negative_streak() >= 2  # months |
|  |
| # GROWTH REGIME CLASSIFICATION |
| if pmi_breadth > 0.65 and revision_breadth > 0.20: |
| regime = 'Expansion' |
| elif pmi_breadth_delta_3m < -0.15 or revision_breadth < -0.15: |
| regime = 'Slowdown' |
| elif pmi_breadth < 0.40 and revision_breadth < -0.30: |
| regime = 'Recession' |
| elif pmi_breadth_delta_3m > +0.10 and revision_breadth > -0.10: |
| regime = 'Recovery' |
| else: |
| regime = 'Slowdown'  # default to caution |
|  |
| # COMMODITY DEFLATION RISK FLAG (China Credit Impulse channel) |
| commodity_deflation_risk = china_impulse_falling and china_impulse_consecutive |
|  |
| # EXPECTED MARKET LAGS (from China Credit Impulse drop) |
| lags = {} |
| if commodity_deflation_risk: |
| lags = { |
| 'commodity_price_peak':   '3 months from today', |
| 'em_exporter_earnings':   '6 months from today', |
| 'em_equity_peak':         '6-9 months from today', |
| 'affected_markets':       ['BR', 'ZA', 'CL', 'PE', 'CO', 'NG', 'AU'], |
| } |
|  |
| return { |
| 'regime': regime, 'commodity_deflation_risk': commodity_deflation_risk, |
| 'pmi_breadth': pmi_breadth, 'revision_breadth': revision_breadth, |
| 'china_credit_impulse': china_credit_impulse, |
| 'expected_lags': lags, 'confidence': self._confidence(pmi_breadth, revision_breadth) |
| } |
| 📉 China CI < 0
Credit flow decelerating · Month 0 | 🛢 Commodities
Iron ore, copper peak · Month 3 | 💹 EM Exporters
Revenue growth stalls · Month 6 | 📊 EM Earnings
EPS revisions negative · Month 9 | ⚠️ EM Equities
Markets price recession · Month 12 |
| --- | --- | --- | --- | --- |
| Cascade Stage | Indicator | Lag from CI Signal | Affected Markets |
| --- | --- | --- | --- |
| 1 — Immediate | China PMI (manufacturing sub-index) starts falling | 0–1 months | Global commodity futures |
| 2 — Commodity | Iron ore, copper, coal spot prices peak and decline | 2–4 months | Australia, Brazil, Chile, Peru |
| 3 — EM Revenue | Commodity exporter fiscal revenues disappoint | 4–7 months | Nigeria, Saudi Arabia (if oil), South Africa |
| 4 — EM Earnings | Corporate earnings estimates revised down | 6–9 months | JSE (ZA), Bovespa (BR), COLCAP (CO) |
| 5 — EM Equities | Index-level repricing as earnings disappoint | 9–15 months | All commodity-linked EM markets |
| Output Field | Type | Values | Consumer Module |
| --- | --- | --- | --- |
| growth.regime | string | Expansion | Slowdown | Recession | Recovery | Crisis Predictor, Scenario Analysis |
| growth.commodity_deflation_risk | boolean | true / false | Risk Radar — flags EM commodity exporters |
| growth.pmi_breadth | float | 0.0 – 1.0 (% of PMIs above 50) | Macro Flows view |
| growth.revision_breadth | float | -1.0 to +1.0 | Market Grid sort — earnings quality |
| growth.china_credit_impulse | float | % of GDP, positive or negative | Lead-Lag Engine (China PMI channel) |
| growth.expected_lags | object | Dict of stage → expected date | Alert narrative: 'commodity peak expected in 3M' |
| growth.affected_markets | array | ISO-2 codes of at-risk markets | Risk Radar — highlight commodity exporters |
| ∑ | Integration: How the Three Modules Combine
The three modules produce a unified World State — consumed by every downstream engine and user-facing alert |
| --- | --- |
| class MacroStateAggregator: |
| --- |
| def aggregate(self, liquidity: dict, inflation: dict, growth: dict) -> WorldState: |
|  |
| # OVERALL MACRO BIAS — composite of three regimes |
| regime_scores = { |
| 'liquidity': {'Expansion':+2,'Normal':0,'Contraction':-2,'Crisis':-4}, |
| 'growth':    {'Expansion':+2,'Recovery':+1,'Slowdown':-1,'Recession':-3}, |
| 'inflation': {'Benign':+1,'Energy-Driven':0,'Mixed':-1,'Demand-Driven':-2}, |
| } |
| composite_score = ( |
| regime_scores['liquidity'][liquidity['regime']] + |
| regime_scores['growth'][growth['regime']] + |
| regime_scores['inflation'][inflation['source']] |
| ) |
| # composite_score: +5 = very bullish EM, -9 = extreme risk-off |
| macro_bias = 'Risk-On' if composite_score >= 2 else \ |
| 'Neutral' if composite_score >= -1 else \ |
| 'Risk-Off' if composite_score >= -4 else 'Crisis' |
|  |
| # OVERRIDE: Crisis always wins |
| if liquidity['regime'] == 'Crisis': |
| macro_bias = 'Crisis' |
|  |
| return WorldState(liquidity=liquidity, inflation=inflation, growth=growth, |
| composite_score=composite_score, macro_bias=macro_bias) |
| Composite Score | Macro Bias | Effect on Crisis Probability | Recommended EM Posture |
| --- | --- | --- | --- |
| +3 to +5 | Risk-On | Subtract 10% from baseline crisis probability | Overweight EM equities |
| +1 to +2 | Mild Risk-On | No adjustment | Neutral EM allocation |
| -1 to 0 | Neutral | No adjustment | Maintain benchmark weight |
| -2 to -3 | Risk-Off | Add 15% to crisis probability | Underweight EM, add Gold/USD |
| -4 to -5 | Risk-Off+ | Add 25% to crisis probability | Defensive: hedges + reduce EM 15% |
| < -5 or Crisis | Crisis | Add 40% to crisis probability | Maximum defensive posture |
|  | Architecture Note:  Run Liquidity Thermostat daily (balance sheet cadence). Run Inflation Vector on every commodity or FX tick (near real-time). Run Growth Diffusion weekly (PMI release cadence). The World State object is versioned and stored in TimescaleDB — every state change is immutable and timestamped for backtesting. |
| --- | --- |
| END-TO-END DATA FLOW
Central Bank APIs + Treasury + PMI + Commodity Prices + FX
↓
Apache Kafka (ingestion)  →  Apache Flink (stream processing)
↓                                    ↓                                    ↓
Liquidity Thermostat (2.1)   ·   Inflation Vector (2.2)   ·   Growth Diffusion (2.3)
↓                                    ↓                                    ↓
MacroStateAggregator → WorldState object (Redis + TimescaleDB)
↓
Crisis Predictor  ·  Correlation Matrix  ·  Scenario Analysis  ·  User Alerts |
| --- |