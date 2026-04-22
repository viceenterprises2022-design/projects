# Precious Metals Trading System
## Professional Trading Playbooks with Economic Calendar Integration

**Version 2.0 - Enhanced with Automated Economic Calendar Analysis**

---

## 🎯 System Overview

A comprehensive two-skill system for generating professional-grade daily trading playbooks for Gold (XAUUSD) and Silver (XAGUSD) with automatic economic calendar integration, money supply analysis, and event-driven strategy adjustments.

### What's New in Version 2.0

✅ **Economic Calendar Integration**
- Automatic fetching from TradingEconomics.com
- Event categorization by metals impact
- Money supply and inflation analysis
- Pre/during/post-event strategies

✅ **Enhanced Playbooks**
- Calendar-aware range adjustments
- Event-driven strategy modifications
- Volatility expectations by event type
- Historical event behavior patterns

✅ **Risk Management**
- Event-specific position sizing
- Pre-event defensive protocols
- Post-event opportunity guidelines
- Volatility-adjusted stop placement

---

## 📦 Package Contents

```
precious-metals-trading-system/
│
├── skills/
│   ├── PLAYBOOK_SKILL.md                # Main playbook generation skill
│   └── ECONOMIC_CALENDAR_SKILL.md       # Calendar analysis skill
│
├── scripts/
│   └── economic_calendar_analyzer.py    # Python implementation
│
├── examples/
│   ├── INTEGRATED_EXAMPLE.md            # Full playbook with calendar
│   ├── example_gold_playbook.md         # Gold example
│   └── example_silver_playbook.md       # Silver example
│
├── MASTER_README.md                     # This file
├── QUICKSTART.md                        # 5-minute setup guide
├── PLAYBOOK_README.md                   # Playbook skill details
├── ECONOMIC_CALENDAR_README.md          # Calendar skill details
├── IMPLEMENTATION_GUIDE.md              # Comprehensive usage guide
├── DAILY_WORKFLOW.md                    # Daily trading routine
└── INSTALLATION_INSTRUCTIONS.md         # Setup guide
```

---

## 🚀 Quick Start

### 1. Install Both Skills (2 minutes)

**Option A: Upload to Claude**
```
1. Share this folder with Claude
2. Ask: "Install the precious metals trading system"
3. Done!
```

**Option B: Manual Installation**
```bash
# Create skill directories
mkdir -p /mnt/skills/user/precious-metals-playbook
mkdir -p /mnt/skills/user/economic-calendar-metals

# Copy skill files
cp skills/PLAYBOOK_SKILL.md /mnt/skills/user/precious-metals-playbook/SKILL.md
cp skills/ECONOMIC_CALENDAR_SKILL.md /mnt/skills/user/economic-calendar-metals/SKILL.md
```

### 2. Generate Your First Playbook (30 seconds)

```
Generate today's gold playbook with economic calendar
```

### 3. Review the Output

You'll receive:
- Market structure analysis
- Economic calendar impact assessment
- Adjusted trading ranges (if major events)
- Event-specific strategies
- Pre/during/post-event guidance
- Money supply implications
- Risk management recommendations

---

## 🎓 How It Works

### Two-Skill Integration

```
User Request
    ↓
Playbook Skill (Primary)
    ↓
    ├─→ Fetches economic calendar ──→ Economic Calendar Skill
    ├─→ Analyzes market structure
    ├─→ Defines trading ranges
    ├─→ Integrates calendar impact ←─── Returns event analysis
    ├─→ Adjusts strategies
    └─→ Generates playbook
    ↓
Complete Playbook with Calendar
```

### Skill 1: Precious Metals Playbook

**What it does:**
- Analyzes gold/silver market structure
- Defines intraday trading ranges
- Generates sell-on-rise and buy-on-dip setups
- Provides confirmation criteria
- Sets targets and invalidation levels

**Enhanced with calendar:**
- Adjusts ranges for scheduled volatility
- Modifies strategies around events
- Provides pre/post-event positioning
- Includes risk management protocols

### Skill 2: Economic Calendar Analysis

**What it does:**
- Fetches data from TradingEconomics
- Categorizes events by metals impact
- Analyzes money supply implications
- Forecasts expected volatility
- Generates event-specific strategies

**Feeds into playbook:**
- Today's high/medium impact events
- This week's schedule
- Money supply context
- Volatility adjustments
- Trading recommendations

---

## 📊 Features

### Playbook Generation

✅ **Market Context**
- Trend analysis
- Structure quality
- Order flow characteristics
- Dealer positioning

✅ **Trading Ranges**
- Supply/sell zones
- Value/balance zones
- Demand/buy zones
- Event-adjusted ranges

✅ **Strategy Setups**
- Clear entry criteria
- 3+ confirmation requirements
- Realistic targets
- Defined invalidation

✅ **Risk Management**
- Position sizing guidance
- Stop placement logic
- Event-driven adjustments
- Daily loss limits

### Economic Calendar

✅ **Event Analysis**
- Impact categorization (HIGH/MEDIUM/LOW)
- Correlation direction (positive/negative/variable)
- Expected move ranges
- Historical behavior patterns

✅ **Money Supply**
- Expansionary vs contractionary
- Fed policy implications
- Rate path expectations
- Inflation impact

✅ **Trading Strategies**
- Pre-event protocols
- During-event rules
- Post-event opportunities
- Risk adjustments

---

## 💼 Use Cases

### Daily Trading

**Morning Routine:**
1. Generate playbook (includes calendar automatically)
2. Review key levels and events
3. Set alerts for zones and event times
4. Adjust position sizing if major events
5. Execute based on confirmation

**Intraday:**
- Follow playbook structure
- Respect event protocols (pre/during/post)
- Wait for confirmations
- Manage positions actively

**End of Day:**
- Review performance
- Update journal
- Note what worked/didn't
- Plan for tomorrow

### Event Trading

**High-Impact Events (CPI, FOMC, NFP):**
- Playbook provides defensive pre-event strategy
- Clear stand-aside during release
- Post-event setups with confirmation
- Expanded range expectations

**Medium-Impact Events:**
- Reduced size recommendations
- Monitoring guidance
- Quick resumption protocols

**Quiet Days:**
- Normal strategies
- Standard sizing
- Technical focus

### Risk Management

**Pre-Event:**
- Automatic size reduction recommendations
- Stop tightening guidance
- Position squaring protocols

**Volatility Adjustment:**
- Range expansion calculations
- Target adjustments
- Stop widening logic

**Daily Limits:**
- Event-adjusted loss limits
- Circuit breaker protocols
- Recovery procedures

---

## 📈 Sample Outputs

### Standard Day (No Major Events)

```
🧭 XAUUSD – INTRADAY PLAYBOOK
📅 10.02.2026

🔍 MARKET CONTEXT
Gold consolidating near 2,645...

📅 ECONOMIC CALENDAR IMPACT
🟢 No major events today
Strategy: Normal operations

📊 EXPECTED RANGE
➡️ 2,625 – 2,665

🧪 STRATEGY LOGIC
🔴 SELL-ON-RISE: 2,655-2,665
🟢 BUY-ON-DIP: 2,625-2,635
```

### CPI Day (High-Impact Event)

```
🧭 XAUUSD – INTRADAY PLAYBOOK (CPI DAY)
📅 10.02.2026

🔍 MARKET CONTEXT
Defensive positioning ahead of CPI...

📅 ECONOMIC CALENDAR IMPACT
[HIGH IMPACT] 🔴
⏰ 8:30 AM ET - US CPI
Expected Move: 30-60 points
Money Supply Implication: ...
PRE-EVENT: Reduce to 25-50% size
DURING: STAND ASIDE
POST: Trade confirmation only

📊 EXPECTED RANGE
Pre-CPI: 2,635-2,655 (tight)
Post-CPI: 2,610-2,690 (2-3x expansion)

🧪 STRATEGY LOGIC
⚠️ PRE-CPI: Minimal exposure
✅ POST-CPI: Reactive scenarios
```

---

## 🔧 Customization

### Modify Event Priorities

Edit `ECONOMIC_CALENDAR_SKILL.md`:
```python
high_impact_keywords = [
    'cpi', 'fomc', 'nfp',
    # Add your custom events
]
```

### Adjust Volatility Expectations

Based on current market regime:
```python
volatility_ranges = {
    'CPI': {'gold': '20-40 points'},  # Adjust from default 30-60
}
```

### Change Risk Parameters

In playbooks:
- Default position reduction: 25-50% pre-event
- Can adjust to 10-25% or 50-75%
- Modify in skill configuration

---

## 🎯 Best Practices

### For SRE/Engineering Professionals

**Apply Systems Thinking:**
- Playbook = System design
- Confirmations = Input validation
- Targets = Success metrics
- Stops = Failure handling

**Process Over Outcomes:**
- Document decisions (journal)
- Track metrics (win rate, R:R)
- Iterate improvements
- Automate where possible

**Risk as Reliability:**
- Position size = Resource allocation
- Stop loss = Circuit breaker
- Daily limit = Service degradation threshold
- Recovery = Incident response

### For All Traders

1. ✅ **Read Entire Playbook** - Context matters
2. ✅ **Wait for Confirmation** - No shortcuts
3. ✅ **Respect Stops** - Cut losses fast
4. ✅ **Scale Appropriately** - Size matters
5. ✅ **Journal Everything** - Data-driven improvement

---

## 📚 Documentation

### Quick References
- **QUICKSTART.md** - Get started in 5 minutes
- **DAILY_WORKFLOW.md** - Daily trading routine

### Detailed Guides
- **IMPLEMENTATION_GUIDE.md** - Comprehensive usage
- **PLAYBOOK_README.md** - Playbook skill details
- **ECONOMIC_CALENDAR_README.md** - Calendar skill details

### Examples
- **INTEGRATED_EXAMPLE.md** - Full CPI day playbook
- **example_gold_playbook.md** - Gold sample
- **example_silver_playbook.md** - Silver sample

---

## ⚠️ Important Disclaimers

### Educational Purpose Only

This system is for educational purposes. It is NOT financial advice.

### Trading Risks

- Precious metals trading involves substantial risk of loss
- Past performance does not guarantee future results
- Events can produce unexpected reactions
- Always do your own analysis

### Calendar Limitations

- Data may be delayed or incomplete
- Fetching may fail (use fallbacks)
- Events can be added/changed last minute
- Always verify times manually

### No Guarantees

- Market conditions change constantly
- Strategies that worked may stop working
- Economic relationships can break down
- Use appropriate risk management always

---

## 🆘 Troubleshooting

### Playbook Issues

**Problem:** Generic output, no calendar
**Solution:** Ensure economic calendar skill is installed

**Problem:** Wrong metal
**Solution:** Specify "gold" or "silver" explicitly

**Problem:** Targets seem unrealistic
**Solution:** Provide current price and key levels

### Calendar Issues

**Problem:** Calendar not fetching
**Solution:** 
1. Check internet connection
2. Try web_search fallback
3. Manually add events if needed

**Problem:** Events missing
**Solution:**
1. Verify date filtering
2. Check categorization keywords
3. Add custom events to skill

**Problem:** Impact levels wrong
**Solution:** Update keyword lists in skill

---

## 🔄 Updates & Maintenance

### Regular Updates

Recommended maintenance:
- Weekly: Review event accuracy
- Monthly: Adjust volatility expectations
- Quarterly: Update keyword lists
- Annually: Full skill review

### Version History

**v2.0** (Current)
- Economic calendar integration
- Event-driven strategies
- Money supply analysis
- Enhanced examples

**v1.0**
- Initial playbook generation
- Basic market structure analysis
- Standard setups

---

## 📞 Support

### Getting Help

1. Check IMPLEMENTATION_GUIDE.md troubleshooting
2. Review example outputs
3. Verify installation paths
4. Test with simple requests first

### Reporting Issues

Document:
- What you requested
- What you expected
- What you got
- Error messages (if any)

---

## 🙏 Credits

**Analysis Framework:** Metaverse Trading Academy  
**Data Source:** TradingEconomics.com  
**Skill Development:** Custom Claude skills  
**Created For:** Nvidia India SRE/Engineering Director

---

## 📝 License

Educational use only. Not for commercial redistribution.

---

## 🚀 Get Started

1. Read QUICKSTART.md
2. Install both skills
3. Generate your first playbook
4. Review DAILY_WORKFLOW.md
5. Start paper trading
6. Build your edge systematically

---

**Remember: We don't predict — we react with structure, flow, and logic.**

— Metaverse Trading Academy Style
