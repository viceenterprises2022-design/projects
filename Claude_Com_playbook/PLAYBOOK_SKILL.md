---
name: precious-metals-playbook
description: Generate professional intraday trading playbooks for precious metals (Gold/Silver) with technical analysis, order flow insights, gamma positioning, and strategy setups in the style of Metaverse Trading Academy. Use when users request daily analysis, trading plans, or market structure breakdowns for XAUUSD or XAGUSD.
---

# Precious Metals Trading Playbook Generator

## Overview

This skill generates comprehensive intraday trading playbooks for precious metals (Gold - XAUUSD, Silver - XAGUSD) following institutional-grade market structure analysis. The playbooks combine technical analysis, order flow, dealer positioning, gamma exposure analysis, and macro context into actionable trading strategies.

## Core Philosophy

**Metaverse Trading Academy Principles:**
- Logic-driven over prediction-based
- React to structure, flow, and confirmation
- Fade weak moves, respect strong absorption
- No confirmation = stand aside
- Trade what you see, not what you think

## When to Use This Skill

Trigger this skill when the user requests:
- Daily trading plan for gold or silver
- Intraday playbook for XAUUSD or XAGUSD
- Market structure analysis for precious metals
- Order flow and gamma positioning insights
- London/NY session trading strategies
- Technical analysis with dealer positioning context

## Input Requirements

### Required Inputs
1. **Metal**: Gold (XAUUSD) or Silver (XAGUSD)
2. **Date**: Trading date for the playbook
3. **Chart Data** (if available): Price action, volume profile, key levels
4. **Current Price**: Latest market price

### Optional Inputs
- Previous session's price action
- Key economic events scheduled
- Macro context (USD strength, yields, risk sentiment)
- Specific session focus (London vs NY)

### Automatic Data Fetching
The skill automatically integrates with the **economic-calendar-metals** skill to:
- Fetch today's economic calendar from TradingEconomics
- Analyze events that impact precious metals
- Include calendar summary in the playbook
- Adjust strategy recommendations based on scheduled events

## Playbook Structure

The output must follow this exact structure:

```
🧭 [METAL] – INTRADAY PLAYBOOK (LON LIVE)
📅 [DATE]
🎯 Metaverse Trading Academy – Logic-Driven View
───────
🔍 MARKET CONTEXT

[2-3 paragraph analysis of current market structure, trend, and flow characteristics]

Primary stance: [SELL-ON-RISE / BUY-ON-DIP / TWO-WAY], [conditions]
───────
📊 EXPECTED RANGE ([SESSION])

**➡️ [LOW] – [HIGH]
Upper Supply / Sell Zone: [range]
Value / Balance Zone: [range]
Lower Demand / Reaction Zone: [range]

[Context on range conditions]
───────
🧠 DEALER & FLOW STRUCTURE

Above [level]: Dealers Gamma [Short/Long] → [implication] [emoji]
[mid-range]: Gamma Neutral → [implication] [emoji]
Below [level]: Dealers Gamma [Short/Long] → [implication] [emoji]

OI: [status]
Delta: [positive/negative/neutral] → [implication]
───────
🧪 STRATEGY LOGIC (METAVERSE STYLE)

🔴 SELL-ON-RISE (PRIMARY/SECONDARY SETUP)

📍 Zone: [price range]

Execute ONLY if confirmation appears:
• [confirmation criteria 1]
• [confirmation criteria 2]
• [confirmation criteria 3]
• [confirmation criteria 4]

🎯 Targets: [T1] → [T2] → [T3]
🛑 Invalidation: [condition]
───────
🟢 BUY-ON-DIP (PRIMARY/SECONDARY SETUP)

📍 Zone: [price range]

Execute ONLY if:
• [confirmation criteria 1]
• [confirmation criteria 2]
• [confirmation criteria 3]

🎯 Targets: [T1] → [T2]
🛑 [Invalidation condition]
───────
📰 MACRO & DATA CONTEXT

[Key macro factors affecting the metal]
[USD/yields/risk sentiment analysis]

⚠️ [Key events/data releases]

LON bias: [description]
NY bias: [description]
───────
🎯 SESSION RULES (KEEP IT CLEAN)

• [Rule 1]
• [Rule 2]
• [Rule 3]
• [Rule 4]
───────
📌 This analysis is for educational purposes only. Watch Metaverse live market commentary for intraday shifts.

🚀 We don't predict — we react with structure, flow, and logic.
— Metaverse Trading Academy
```

## Analysis Framework

### 1. Market Context Analysis

**What to Include:**
- **Trend Assessment**: Current directional bias (bullish/bearish/range-bound)
- **Structure Quality**: Are highs/lows being respected? Is structure breaking down?
- **Flow Characteristics**: Is buying/selling being absorbed or driving price?
- **Volume Profile**: Where is acceptance vs rejection occurring?
- **Primary Stance**: Clear directional bias or two-way approach

**Language Style:**
- Concise, professional, institutional tone
- Use terms: "absorption," "distribution," "accumulation," "acceptance," "rejection"
- Avoid predictions; focus on conditional structure
- Example: "Upside attempts are being sold into, while downside shows absorption only near deeper supports"

### 2. Expected Range Calculation

**Methodology:**
- Use recent ATR (Average True Range) for volatility context
- Identify key technical levels (previous highs/lows, pivots, round numbers)
- Define 3 zones:
  - **Supply/Sell Zone**: Upper resistance area where selling pressure expected
  - **Value Zone**: Fair value area where two-way trade likely
  - **Demand/Reaction Zone**: Support area where buying interest expected

**Range Width Guidelines:**
- Gold (XAUUSD): Typically 40-80 points for London session
- Silver (XAGUSD): Typically 1.00-2.00 points for London session
- Adjust based on volatility regime

### 3. Dealer & Gamma Positioning

**Gamma Structure Analysis:**
- **Dealers Gamma Short** (above strikes): Volatility expansion risk, dealers must hedge directionally (amplifies moves)
- **Gamma Neutral**: Balanced positioning, choppy two-way trade expected
- **Dealers Gamma Long** (below strikes): Volatility compression, dealers provide liquidity (dampens moves)

**Open Interest (OI):**
- Rising OI + Rising Price = Strong uptrend
- Rising OI + Falling Price = Strong downtrend  
- Flat/Declining OI = Lack of conviction

**Delta Analysis:**
- Positive Delta = Net buying pressure, supports upside
- Negative Delta = Net selling pressure, supports downside
- Neutral Delta = Balanced, follow price action

### 4. Strategy Development

**SELL-ON-RISE Setup Requirements:**
- Must identify specific supply zone (price range)
- Define clear confirmation criteria (not just "price reaches zone")
- Confirmation examples:
  - Buying exhaustion at highs (volume dries up)
  - Negative delta divergence (price up, delta down)
  - VWAP / dVWAP rejection
  - Aggressive bids absorbed without follow-through
  - Failed breakout / liquidity grab pattern

**BUY-ON-DIP Setup Requirements:**
- Must identify specific demand zone
- Define clear confirmation criteria
- Confirmation examples:
  - Clear sell absorption (large sells don't move price)
  - Delta flips positive
  - Failed breakdown
  - VWAP reclaim with volume
  - Aggressive offers absorbed

**Target Structure:**
- T1: Near-term technical level (often Value Zone)
- T2: Next key technical level
- T3: Extended target (reach for aggressive scenarios)

**Invalidation Levels:**
- Must be clear and objective
- Examples: "Acceptance above X," "Break and hold above Y," "No reaction = no trade"

### 5. Macro & Data Context

**Key Factors to Consider:**

**For Gold (XAUUSD):**
- USD Index (DXY) strength/weakness
- US 10-Year Treasury yields
- Real yields (inflation-adjusted)
- Fed policy expectations
- Geopolitical risk / safe-haven demand
- Central bank buying trends

**For Silver (XAGUSD):**
- All gold factors (silver follows gold directionally)
- Industrial demand indicators
- Gold/Silver ratio
- Risk sentiment (silver more volatile in risk-off)

**Scheduled Data Releases:**
- US CPI, PPI (inflation data) - high impact
- FOMC decisions/minutes - high impact
- NFP/employment data - high impact
- GDP, ISM data - medium impact
- Fed speakers - medium impact

**Session Bias Framework:**
- **London Session**: Range execution, positioning, technical levels respected
- **NY Session**: Directional resolution, macro-driven, data releases create volatility

### 6. Session Rules

**Standard Rules to Include:**
- Trade structure and orderflow over opinions
- No confirmation = stand aside / no trade
- Respect key technical levels (don't front-run)
- Fade weak moves into supply/demand zones
- Scale into positions, don't hero trade
- Manage risk actively; don't hope

## Technical Analysis Integration

### Key Levels to Identify

1. **Previous Day's Range**: High, Low, Close
2. **Weekly Levels**: Weekly high/low, weekly open
3. **Volume Profile**: POC (Point of Control), Value Area High/Low
4. **VWAP Levels**: Daily VWAP, anchored VWAPs
5. **Round Numbers**: Psychologically significant (e.g., 2000, 2050 for gold)
6. **Fibonacci Levels**: From recent swings (use judiciously)
7. **Order Flow Levels**: Visible absorption, rejection zones

### Chart Pattern Recognition

**Continuation Patterns:**
- Flags, pennants (in direction of trend)
- Consolidation near highs/lows

**Reversal Patterns:**
- Double tops/bottoms
- Head and shoulders
- Failed breakouts (liquidity grabs)

**Don't over-rely on patterns alone** - confirm with flow and delta

## Order Flow Terminology

Use these terms appropriately:

- **Absorption**: Large orders taken without significant price movement
- **Exhaustion**: Buying/selling pressure diminishes (volume dries up)
- **Distribution**: Smart money selling into strength
- **Accumulation**: Smart money buying into weakness  
- **Delta Divergence**: Price and delta (net buying/selling) move in opposite directions
- **Liquidity Grab**: Stop hunt beyond key level followed by reversal
- **Acceptance**: Price holds above/below level, further continuation likely
- **Rejection**: Price quickly moves away from level, reversal or range

## Formatting Requirements

### Emojis Usage
- 🧭 - Title/Navigation
- 📅 - Date
- 🎯 - Target/Focus
- 🔍 - Analysis/Context
- 📊 - Range/Data
- 🧠 - Positioning/Strategy
- 🧪 - Strategy Logic
- 🔴 - Sell Setup
- 🟢 - Buy Setup
- 📰 - News/Macro
- ⚠️ - Warning/Alert
- 📌 - Important Note
- 🚀 - Closing Tagline
- ➡️ - Direction/Range indicator

**Gamma Indicator Emojis:**
- 🔴 - Bearish gamma (short gamma = volatility risk)
- ⚖️ - Neutral gamma (balanced)
- 🟢 - Bullish gamma (long gamma = absorption)

### Typography Rules
- Use `───────` as section dividers (7 dashes)
- Bold for key terms: **➡️**, **OI:**, **Delta:**
- Zone descriptions: `Upper Supply / Sell Zone: X - Y`
- Bullet points: Use • for confirmation criteria
- Arrows for targets: `X → Y → Z`

### Tone Requirements
- Professional and institutional
- Confident but not arrogant
- Conditional, not predictive
- Educational and transparent
- Action-oriented

**Examples of Good vs Bad Language:**

✅ **Good:**
- "Flow suggests distribution, not accumulation"
- "Dealers remain defensive near highs"
- "Execute ONLY if confirmation appears"
- "No reaction = stand aside"

❌ **Bad:**
- "Gold will definitely go to 2100" (too predictive)
- "This is a guaranteed trade" (overconfident)
- "I think maybe price might..." (too uncertain/informal)
- "Buy here!!!" (lacks nuance/professionalism)

## Execution Workflow

When generating a playbook:

1. **Gather Context**
   - Ask for metal (gold/silver) if not specified
   - Request current price and session (LON/NY)
   - Check for any chart data or technical levels provided
   - **Fetch economic calendar** using web_fetch or web_search
   - **Analyze calendar events** for metals impact

2. **Analyze Structure**
   - Assess trend and structure quality
   - Identify key support/resistance zones
   - Determine dealer positioning implications
   - Evaluate order flow characteristics

3. **Define Range**
   - Calculate expected intraday range
   - **Adjust range** based on scheduled high-impact events
   - Mark supply, value, and demand zones
   - Note key technical levels within range

4. **Build Strategies**
   - Determine primary directional bias
   - **Modify strategies** based on event timing:
     * Pre-event: Defensive positioning
     * Post-event: Opportunity-focused setups
   - Define entry zones with specific confirmation
   - Set realistic targets based on structure
   - Establish clear invalidation criteria

5. **Add Context**
   - Include relevant macro drivers
   - **Integrate economic calendar analysis**
   - Note scheduled data/events with timing
   - Differentiate London vs NY expectations
   - Provide pre/during/post event guidance

6. **Format Output**
   - Follow exact template structure
   - Use proper emojis and typography
   - Maintain professional tone throughout
   - Include educational disclaimer

## Common Mistakes to Avoid

1. **Being Too Predictive**: Never say "will go to X" - use conditional language
2. **Ignoring Confirmation**: Always require specific triggers, not just "price in zone"
3. **Unrealistic Targets**: Targets must align with actual technical structure
4. **Vague Entry Criteria**: "Buy the dip" is not enough - specify what confirms the dip
5. **Missing Invalidation**: Every setup needs a clear "wrong" level
6. **Overcomplicating**: Keep it actionable - too many scenarios confuse traders
7. **Ignoring Macro**: Precious metals are macro-sensitive - don't skip this context
8. **Generic Language**: Use specific order flow and positioning terms
9. **Poor Risk Definition**: Must be clear about when to exit if wrong
10. **Lacking Educational Tone**: This is a learning tool, not just trade calls

## Metal-Specific Considerations

### Gold (XAUUSD)

**Typical Characteristics:**
- More liquid than silver
- Strong USD inverse correlation
- Responds heavily to yields and Fed policy
- Safe-haven asset (rises in risk-off)
- Less volatile intraday than silver
- Round number levels very significant (2000, 2050, 2100, etc.)

**Average Daily Range:** 20-50 points (can expand to 100+ on high volatility days)

**Key Levels Spacing:** Usually 10-20 point increments for intraday zones

### Silver (XAGUSD)

**Typical Characteristics:**
- More volatile than gold (2-3x on percentage basis)
- Follows gold directionally but with amplification
- Has industrial demand component
- Less liquid, wider spreads
- Prone to sharper reversals
- Gold/Silver ratio important (70-90 typical range)

**Average Daily Range:** 0.50-1.50 points (can expand to 2.00+ on volatility)

**Key Levels Spacing:** Usually 0.20-0.50 point increments for intraday zones

## Customization Options

Users may request modifications:

1. **Session Focus**: London-only, NY-only, or both
2. **Style Preference**: More conservative vs aggressive setups
3. **Detail Level**: Quick overview vs comprehensive breakdown
4. **Time Horizon**: Scalping (minutes) vs swing intraday (hours)
5. **Risk Tolerance**: Tighter stops vs wider invalidation

**Always maintain core structure** but adjust targets, zones, and strategy aggressiveness accordingly.

## Example Phrases by Section

### Market Context
- "remains range-bound with a [bearish/bullish] tilt"
- "Upside attempts are being sold into"
- "Flow suggests [distribution/accumulation]"
- "Dealers remain defensive near highs"
- "Structure shows acceptance above X"
- "Downside absorption only near deeper supports"

### Gamma Structure
- "Dealers Gamma Short → volatility expansion risk"
- "Dealers Gamma Long → absorption / short-covering potential"
- "Gamma Neutral → chop & two-way trade"

### Strategy Confirmation
- "Buying exhaustion at highs"
- "Negative delta divergence"
- "VWAP / dVWAP rejection"
- "Aggressive bids absorbed"
- "Clear sell absorption"
- "Delta flips positive"
- "Failed breakdown + VWAP reclaim"

### Session Rules
- "Fade weak rallies into supply"
- "Respect [level] — reaction defines bias"
- "Trade orderflow > opinions"
- "No confirmation = stand aside"

## Quality Checklist

Before finalizing the playbook, ensure:

- [ ] Title includes correct metal, date, session
- [ ] Market context is 2-3 paragraphs with clear primary stance
- [ ] Expected range has all 3 zones defined
- [ ] Gamma structure includes at least 3 levels with implications
- [ ] Each strategy has specific entry zone
- [ ] Each strategy has 3+ confirmation criteria
- [ ] Each strategy has clear targets (at least 2)
- [ ] Each strategy has invalidation level
- [ ] Macro context includes USD/yields and any scheduled data
- [ ] Session rules include 3-4 actionable points
- [ ] All emojis used correctly per section
- [ ] Formatting follows template exactly
- [ ] Tone is professional and conditional
- [ ] Educational disclaimer included at end
- [ ] No predictions, only conditional setups

## Final Notes

**This skill generates professional-grade trading playbooks.** The output should:
- Educate the user on market structure
- Provide actionable strategies with clear criteria
- Maintain institutional-quality analysis
- Avoid predictions while offering logic-driven setups
- Help users develop their own market reading skills

**The playbook is not financial advice** - always include the educational disclaimer.

**Quality over quantity** - it's better to have one high-probability setup with clear confirmation than five vague scenarios.

**Stay true to the Metaverse philosophy:** React to structure, flow, and confirmation. Don't predict - participate.
