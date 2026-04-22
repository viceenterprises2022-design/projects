---
name: economic-calendar-metals
description: Fetch and analyze economic calendar data from TradingEconomics to identify events that impact money supply, inflation, and precious metals. Use when generating trading playbooks or when users request economic event analysis for gold/silver trading.
---

# Economic Calendar Analysis for Precious Metals

## Overview

This skill fetches economic calendar data from TradingEconomics.com and analyzes which events are likely to impact precious metals (gold and silver) pricing through their effects on money supply, inflation expectations, real yields, and USD strength.

## When to Use This Skill

Trigger this skill when:
- Generating daily precious metals trading playbooks
- User asks about upcoming economic events affecting gold/silver
- Analyzing macro context for metals trading
- Planning trading schedule around data releases
- Assessing volatility expectations for the day/week

## Core Functionality

### 1. Fetch Economic Calendar
- Source: https://tradingeconomics.com/calendar
- Extract: Today's and upcoming events
- Parse: Event name, time, country, actual/forecast/previous values, impact level

### 2. Categorize Events by Impact

**High Impact on Precious Metals:**
- US CPI (Consumer Price Index) - inflation data
- US PPI (Producer Price Index) - wholesale inflation
- FOMC Rate Decision - direct monetary policy
- FOMC Minutes/Statement - policy direction
- Fed Chair Testimony - policy hints
- US GDP - economic growth indicator
- US Employment (NFP, ADP, Jobless Claims) - labor market strength
- PCE Price Index - Fed's preferred inflation gauge
- US Retail Sales - consumer spending strength
- ISM Manufacturing/Services PMI - economic activity

**Medium Impact:**
- US Durable Goods Orders - economic momentum
- US Consumer Confidence - sentiment indicator
- US Housing Data (Starts, Sales, Prices) - sector health
- Fed Speaker Events - policy communication
- Treasury Auctions - yield impact
- Trade Balance - dollar impact
- ECB/BOE/BOJ Policy Decisions - indirect USD impact

**Low Impact:**
- Most non-US data (unless G7 central bank)
- Weekly Inventory Data
- Regional Fed Surveys
- Minor indicators

### 3. Money Supply & Inflation Analysis

**Events Affecting Money Supply:**
- FOMC Rate Decisions (QE/QT announcements)
- Fed Balance Sheet Data
- Bank Reserve Requirements
- Credit/Lending Data
- M2 Money Supply Reports

**Events Affecting Inflation Expectations:**
- CPI/PPI (direct inflation measures)
- PCE (Fed's target)
- Wage Growth Data (inflationary pressure)
- Commodity Prices
- Rent/Housing Costs
- Import/Export Prices

### 4. Generate Impact Summary

For each relevant event, analyze:
- **Timing**: Exact release time (critical for intraday traders)
- **Expected Volatility**: Based on historical price movement
- **Directional Bias**: How event typically affects gold/silver
- **Trading Implications**: Before/during/after event strategy

## Output Format

The skill generates a structured summary to be integrated into trading playbooks:

```
📅 ECONOMIC CALENDAR IMPACT

**Today's Key Events:**

[HIGH IMPACT] 🔴
⏰ 8:30 AM ET - US CPI (Consumer Price Index)
   Forecast: 2.8% YoY | Previous: 2.7% YoY
   Impact: Direct inflation measure - HIGH volatility expected
   Metals Correlation: Strong positive (higher inflation → gold up)
   Strategy: Be flat or reduced before release, wait for confirmation post-data

⏰ 2:00 PM ET - FOMC Minutes
   Impact: Policy direction hints - MEDIUM volatility
   Metals Correlation: Dovish = bullish metals, Hawkish = bearish metals
   Strategy: Position after digest, not during release

[MEDIUM IMPACT] 🟡
⏰ 10:00 AM ET - US Wholesale Inventories
   Impact: Economic activity indicator - LOW volatility
   Metals Correlation: Indirect via growth expectations
   Strategy: Normal trading, watch for surprises

**This Week's Schedule:**
- Wed 8:30 AM: PPI 🔴
- Thu 8:30 AM: Jobless Claims 🟡
- Fri 8:30 AM: Retail Sales 🔴

**Money Supply Implications:**
- CPI above forecast → Supports Fed hawkish stance → Bearish for gold
- CPI below forecast → Supports Fed dovish stance → Bullish for gold
- Current Fed Policy: Restrictive, watching inflation for cut signals

**Positioning Guidance:**
- Pre-CPI: Reduce size 50-75%, or be flat
- During CPI: Stand aside, no new positions
- Post-CPI (15 min): Wait for initial spike, then assess structure
- Post-CPI (30-60 min): Trade the digestion/confirmation
```

## Implementation Details

### Web Scraping Approach

```python
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
import re

def fetch_economic_calendar():
    """
    Fetch economic calendar from TradingEconomics
    """
    url = "https://tradingeconomics.com/calendar"
    
    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse calendar table
            events = parse_calendar_table(soup)
            
            # Filter for today and this week
            today_events = filter_today(events)
            week_events = filter_week(events)
            
            return today_events, week_events
        else:
            # Fallback: use web_fetch tool
            return None
            
    except Exception as e:
        return None

def parse_calendar_table(soup):
    """
    Extract event data from HTML table
    """
    events = []
    
    # Find calendar table (structure may vary)
    table = soup.find('table', {'id': 'calendar'}) or soup.find('table', class_='table')
    
    if not table:
        return events
    
    rows = table.find_all('tr')[1:]  # Skip header
    
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 6:
            event = {
                'time': cols[0].text.strip(),
                'country': cols[1].text.strip(),
                'event': cols[2].text.strip(),
                'actual': cols[3].text.strip(),
                'forecast': cols[4].text.strip(),
                'previous': cols[5].text.strip(),
                'importance': get_importance(cols)
            }
            events.append(event)
    
    return events

def categorize_impact(event_name, country):
    """
    Determine impact level on precious metals
    """
    event_lower = event_name.lower()
    
    # High impact events
    high_impact_keywords = [
        'cpi', 'ppi', 'fomc', 'interest rate', 'nfp', 'payroll',
        'employment', 'gdp', 'pce', 'inflation', 'fed chair',
        'retail sales', 'ism manufacturing', 'ism services'
    ]
    
    # Medium impact events
    medium_impact_keywords = [
        'durable goods', 'consumer confidence', 'housing',
        'fed speak', 'jobless claims', 'trade balance',
        'ecb', 'boe', 'boj'
    ]
    
    # US events get priority
    if country == 'United States':
        for keyword in high_impact_keywords:
            if keyword in event_lower:
                return 'HIGH'
        for keyword in medium_impact_keywords:
            if keyword in event_lower:
                return 'MEDIUM'
    
    # Non-US central bank decisions
    if any(word in event_lower for word in ['rate decision', 'monetary policy']):
        if country in ['European Union', 'United Kingdom', 'Japan', 'China']:
            return 'MEDIUM'
    
    return 'LOW'

def analyze_metals_correlation(event_name):
    """
    Determine how event typically affects gold/silver
    """
    event_lower = event_name.lower()
    
    correlations = {
        'cpi': {
            'direction': 'positive',
            'description': 'Higher inflation → supports gold as inflation hedge',
            'volatility': 'Very High'
        },
        'ppi': {
            'direction': 'positive',
            'description': 'Leading inflation indicator → impacts gold inflation expectations',
            'volatility': 'High'
        },
        'fomc': {
            'direction': 'variable',
            'description': 'Dovish = bullish gold, Hawkish = bearish gold',
            'volatility': 'Very High'
        },
        'nfp': {
            'direction': 'negative',
            'description': 'Strong jobs → Fed hawkish → bearish gold; Weak jobs → opposite',
            'volatility': 'Very High'
        },
        'gdp': {
            'direction': 'negative',
            'description': 'Strong growth → higher yields → bearish gold',
            'volatility': 'Medium'
        },
        'retail sales': {
            'direction': 'negative',
            'description': 'Strong sales → growth/inflation → complex (yields vs inflation)',
            'volatility': 'Medium-High'
        }
    }
    
    for key, value in correlations.items():
        if key in event_lower:
            return value
    
    return {
        'direction': 'variable',
        'description': 'Impact depends on context',
        'volatility': 'Low-Medium'
    }
```

### Integration with Web Tools

If web scraping fails, use Claude's web_fetch tool:

```python
# Fallback approach
web_fetch("https://tradingeconomics.com/calendar")
# Then parse the returned HTML content
```

## Event Analysis Framework

### Money Supply Impact Assessment

**Expansionary (Bullish for Gold):**
- Rate cuts announced
- QE programs started/expanded
- Forward guidance dovish
- Lower than expected inflation (supports cuts)
- Weak employment (supports easing)

**Contractionary (Bearish for Gold):**
- Rate hikes announced
- QT programs started/accelerated
- Forward guidance hawkish
- Higher than expected inflation (forces hikes)
- Strong employment (allows tightening)

### Volatility Expectation Formula

```python
def calculate_expected_volatility(event_impact, historical_moves):
    """
    Estimate intraday volatility based on event
    
    Historical average moves (in points/USD):
    - CPI: 30-60 points for gold, 1.00-2.00 for silver
    - FOMC: 40-80 points for gold, 1.50-3.00 for silver
    - NFP: 25-50 points for gold, 0.80-1.50 for silver
    - GDP: 15-30 points for gold, 0.40-0.80 for silver
    """
    
    volatility_ranges = {
        'CPI': {'gold': '30-60 points', 'silver': '1.00-2.00'},
        'PPI': {'gold': '20-40 points', 'silver': '0.60-1.20'},
        'FOMC': {'gold': '40-80 points', 'silver': '1.50-3.00'},
        'NFP': {'gold': '25-50 points', 'silver': '0.80-1.50'},
        'GDP': {'gold': '15-30 points', 'silver': '0.40-0.80'},
        'Retail Sales': {'gold': '15-35 points', 'silver': '0.50-1.00'}
    }
    
    # Return expected range expansion
    return volatility_ranges.get(event_impact, {'gold': '10-20 points', 'silver': '0.30-0.60'})
```

## Trading Strategy Guidelines

### Pre-Event Positioning

**High Impact Events (CPI, FOMC, NFP):**
- Reduce position size to 25-50% of normal
- Tighten stops or close out entirely
- Move stops to breakeven on remaining positions
- Cancel pending orders
- Prepare for volatility expansion

**Medium Impact Events:**
- Reduce size to 75% of normal
- Be aware but can maintain positions
- No new aggressive positions immediately before

**Low Impact Events:**
- Trade normally
- Monitor for surprises

### During Event (0-15 minutes post-release)

**DO NOT TRADE:**
- Initial spike is often fake-out
- Algos and headlines create whipsaws
- Wait for dust to settle
- Let first move exhaust

**OBSERVE:**
- Initial reaction direction
- Volume characteristics
- How quickly move retraces or extends

### Post-Event (15-60 minutes)

**NOW TRADE:**
- Structure becomes clearer
- Confirmation signals appear
- Failed moves reveal true direction
- Volume settles into pattern

**LOOK FOR:**
- Failed breakout → fade it
- Sustained breakout → join it
- Return to range → trade the range
- New structure → define new zones

## Integration with Playbook Skill

The economic calendar skill feeds into the precious metals playbook:

1. **Fetch calendar data** at playbook generation time
2. **Analyze today's events** for metals impact
3. **Include summary** in playbook's "MACRO & DATA CONTEXT" section
4. **Adjust strategy** based on scheduled events:
   - Pre-event: Defensive positioning
   - Post-event: Opportunity-focused setups

## Error Handling

```python
def get_calendar_with_fallback():
    """
    Try multiple methods to get calendar data
    """
    # Method 1: Direct scraping
    try:
        return fetch_economic_calendar()
    except:
        pass
    
    # Method 2: Use web_fetch tool
    try:
        html = web_fetch("https://tradingeconomics.com/calendar")
        return parse_html(html)
    except:
        pass
    
    # Method 3: Use web_search for today's events
    try:
        results = web_search("US economic calendar today TradingEconomics")
        return extract_from_search(results)
    except:
        pass
    
    # Fallback: Return generic high-impact events
    return get_default_calendar()

def get_default_calendar():
    """
    If all methods fail, return typical high-impact events
    """
    return {
        'note': 'Could not fetch live calendar. Showing typical high-impact events.',
        'high_impact_times': [
            '8:30 AM ET - Common time for US data (CPI, NFP, etc.)',
            '10:00 AM ET - Secondary US data releases',
            '2:00 PM ET - FOMC Minutes/Fed events'
        ],
        'recommendation': 'Check https://tradingeconomics.com/calendar manually for today\'s actual events'
    }
```

## Output Examples

### Example 1: CPI Day

```
📅 ECONOMIC CALENDAR IMPACT

**Today's Key Events:**

[HIGH IMPACT] 🔴
⏰ 8:30 AM ET - US Consumer Price Index (CPI)
   📊 Forecast: 2.8% YoY | Previous: 2.7% YoY
   💥 Impact Level: VERY HIGH
   📈 Expected Move: Gold 30-60 points, Silver 1.00-2.00
   
   Metals Correlation: ⬆️ Strong Positive
   - Higher than forecast → Inflation fears → Gold rallies
   - Lower than forecast → Disinflation → Gold may weaken
   - In-line → Modest reaction, focus on details
   
   Money Supply Implication:
   - Hot CPI → Fed stays restrictive → Higher rates longer → Headwind for gold
   - Cool CPI → Fed can ease sooner → Lower rates → Tailwind for gold
   
   Trading Strategy:
   ⚠️ PRE-EVENT (Before 8:30 AM):
      • Reduce position size to 25-50%
      • Tighten stops or close entirely
      • Cancel pending orders
      • Prepare for 30-60 point range expansion
   
   ⏸️ DURING EVENT (8:30-8:45 AM):
      • STAND ASIDE - Do not trade
      • Observe initial reaction
      • Let algos exhaust the first move
   
   ✅ POST-EVENT (8:45-9:30 AM):
      • Trade the confirmation, not the headline
      • Look for failed moves to fade
      • Wait for structure and flow signals
      • 3+ confirmations required before entry

[MEDIUM IMPACT] 🟡
⏰ 2:00 PM ET - Fed Speaker Williams
   💥 Impact: Medium (unless major policy hints)
   📈 Expected Move: Gold 10-20 points
   
   Strategy: Monitor for hawkish/dovish tone, react to confirmed moves

**This Week Ahead:**
• Wed 8:30 AM - PPI (Producer Prices) 🔴
• Thu 8:30 AM - Jobless Claims 🟡  
• Fri 8:30 AM - Retail Sales 🔴

**Money Supply & Policy Context:**
Current Fed Stance: Restrictive monetary policy, watching inflation for easing signals
Market Expectations: 75% chance of first cut in June (per CME FedWatch)
Implication: Gold needs inflation to cool OR growth to weaken for sustained rally

**Volatility Advisory:**
🔴 HIGH VOLATILITY DAY - CPI is market-moving event
   • Expect 2-3x normal intraday range
   • Breakouts more likely to sustain
   • Failed breakouts more violent
   • Use wider stops or smaller size
```

### Example 2: Quiet Day

```
📅 ECONOMIC CALENDAR IMPACT

**Today's Key Events:**

[MEDIUM IMPACT] 🟡
⏰ 10:00 AM ET - US Wholesale Inventories
   📊 Forecast: 0.2% | Previous: 0.1%
   💥 Impact Level: LOW
   📈 Expected Move: Gold 5-10 points
   
   Metals Correlation: ⬇️ Minimal
   - Reflects economic activity indirectly
   - Rarely moves metals significantly
   
   Trading Strategy: Normal operations, watch for surprises

**This Week Ahead:**
• Tomorrow 8:30 AM - Initial Jobless Claims 🟡
• Friday 8:30 AM - CPI 🔴 (MAJOR EVENT)

**Money Supply & Policy Context:**
Quiet data week ahead of Friday's CPI
Current positioning: Markets consolidating before major event
Implication: Range-bound trade likely until Friday

**Volatility Advisory:**
🟢 NORMAL VOLATILITY DAY
   • Trade standard setups
   • Normal position sizing
   • Build positions ahead of Friday cautiously
```

## Quality Checklist

Before finalizing calendar analysis:

- [ ] Today's events fetched and parsed
- [ ] Events categorized by impact (HIGH/MEDIUM/LOW)
- [ ] Time converted to ET (US Eastern Time)
- [ ] Metals correlation explained for each event
- [ ] Money supply implications analyzed
- [ ] Trading strategy provided (pre/during/post)
- [ ] Week ahead schedule included
- [ ] Volatility expectations quantified
- [ ] Integrated into playbook macro section

## Usage in Playbook Generation

```python
# When generating playbook:
1. Fetch economic calendar
2. Analyze today's and week's events
3. Generate impact summary
4. Integrate into playbook's MACRO section
5. Adjust strategy recommendations based on events:
   - If major event today → defensive positioning
   - If quiet day → normal strategies
   - If event this week → forward-looking guidance
```

## Limitations & Disclaimers

- Calendar data may be delayed or incomplete
- Event importance is historical-based, not predictive
- Market reactions can be counterintuitive
- Always verify event times and dates manually
- Use as guidance, not guaranteed outcomes

## Final Notes

This skill enhances trading playbooks by:
1. Providing macro calendar awareness
2. Setting volatility expectations  
3. Guiding risk management around events
4. Connecting money supply theory to practical trading
5. Improving timing of entries/exits

**The economic calendar is a tool for preparation, not prediction.**
