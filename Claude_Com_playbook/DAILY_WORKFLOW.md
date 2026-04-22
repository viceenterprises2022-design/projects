# Daily Trading Workflow - For Nvidia SRE/Engineering Director

## Morning Routine (Pre-Market Analysis)

### Step 1: Generate Daily Playbooks (5 minutes)
```
Generate playbooks for both gold and silver for today's session.
Include:
- Current overnight prices
- Key levels from yesterday
- Scheduled economic data
```

**What you get:**
- Gold (XAUUSD) playbook with zones and setups
- Silver (XAGUSD) playbook with zones and setups  
- Macro context and data schedule
- Session-specific guidance

### Step 2: Review Key Levels (2 minutes)
From each playbook, note:
- [ ] Upper supply/sell zone
- [ ] Value/balance zone
- [ ] Lower demand/buy zone
- [ ] Primary bias (sell-on-rise vs buy-on-dip)
- [ ] Scheduled data releases

### Step 3: Set Alerts (3 minutes)
In your trading platform:
- Alert at upper supply zone
- Alert at lower demand zone
- Alert at invalidation levels
- Calendar alert for data releases

**Total Pre-Market Prep: 10 minutes**

---

## Intraday Execution (London/NY Sessions)

### London Session (3:00 AM - 12:00 PM ET)

**Strategy:**
- Range-bound execution typically
- Fade extremes into supply/demand zones
- Wait for confirmation signals

**When to Act:**
```
IF price enters supply zone (82.20-82.60 for silver)
  AND buying exhaustion visible
  AND delta divergence appears
  AND VWAP rejection confirmed
THEN execute sell setup
  Targets: 81.80 → 81.20 → 80.90
  Stop: Above 82.80
```

### NY Session (9:30 AM - 4:00 PM ET)

**Strategy:**
- Directional resolution common
- Data releases create volatility
- Follow orderflow, not predictions

**When to Act:**
Same confirmation-based approach, but:
- Expect larger moves post-data
- Tighter risk management around major releases
- Be willing to stand aside if no confirmation

---

## Real-Time Decision Framework

### Entry Checklist ✅

Before taking ANY trade, verify:
- [ ] Price is in designated zone
- [ ] At least 3 confirmation criteria met
- [ ] Position size appropriate
- [ ] Stop loss defined and acceptable
- [ ] Targets realistic based on structure
- [ ] No major data release imminent (unless that's the setup)

### Confirmation Signals (Need 3+)

**For SELL setups:**
- [ ] Volume declining on push higher
- [ ] Delta diverging negative  
- [ ] Large bids absorbed without follow-through
- [ ] VWAP rejection
- [ ] Failed breakout/liquidity grab
- [ ] Previous resistance holding

**For BUY setups:**
- [ ] Volume increasing on dip
- [ ] Delta turning positive
- [ ] Large sells absorbed without breakdown
- [ ] VWAP reclaim
- [ ] Failed breakdown/stop hunt
- [ ] Previous support holding

### If Confirmation Doesn't Appear

**DO NOT TRADE**
- No confirmation = no trade
- Stand aside and wait
- Better to miss a move than force a bad trade

---

## Position Management

### Entry
- **Scale In**: Don't use full size immediately
  - 50% at first confirmation
  - 25% at second confirmation
  - 25% at third confirmation (or hold this back)

### Targets
- **Scale Out**: Take profits progressively
  - 1/3 at Target 1
  - 1/3 at Target 2  
  - 1/3 at Target 3 or trail stop

### Stop Loss
- **Use Clean Breaks**: 30-minute acceptance beyond invalidation
- **Don't Hope**: If invalidated, exit immediately
- **Move to Breakeven**: After Target 1 hit

---

## End of Day Review (10 minutes)

### Trading Journal Template

**Date:** [Date]
**Metal:** Gold / Silver
**Setup Type:** Sell-on-Rise / Buy-on-Dip

**Pre-Trade Analysis:**
- Primary bias from playbook: ____
- Entry zone planned: ____
- Confirmation criteria required: ____
- Targets: ____ / ____ / ____
- Stop: ____

**Execution:**
- Entry price: ____
- Confirmations that appeared: ____
- Position size: ____
- Exit prices: ____
- P&L: ____

**Review:**
- What worked: ____
- What didn't: ____
- Confirmations accuracy: ____
- Target realism: ____
- Emotional discipline: ____

**Lessons:**
- ____
- ____

### Weekly Summary

Every Friday, review:
- Win rate on confirmed setups
- Average R:R (risk:reward)
- Best confirmations (highest success rate)
- Worst confirmations (lowest success rate)
- Emotional patterns
- Process adherence

---

## Integration with Your SRE/Engineering Role

### Apply Engineering Principles

**1. System Design:**
Your trading approach is a system:
- Input: Market data + playbook
- Process: Confirmation verification
- Output: Trade decision
- Feedback: Performance metrics

**2. Reliability Engineering:**
- MTBF: Mean Time Between Failures (losing trades)
- MTTR: Mean Time To Recovery (how fast you cut losses)
- SLA: Your win rate and R:R targets
- Monitoring: Real-time confirmation tracking

**3. Incident Response:**
A losing trade = incident
- Acknowledge immediately (hit stop loss)
- Diagnose (what confirmation failed?)
- Resolve (exit position)
- Post-mortem (journal review)
- Prevention (update criteria)

**4. Automation Mindset:**
- Alert automation (price levels)
- Checklist automation (entry criteria)
- Risk automation (position sizing calculator)
- Reporting automation (daily P&L tracking)

### Risk Management as SRE

**Capacity Planning:**
- Total capital = system capacity
- Position size = resource allocation
- Drawdown limit = circuit breaker
- Correlation = service dependencies

**Blast Radius:**
- Max loss per trade: 1-2% of capital
- Max daily loss: 5% of capital
- Monthly drawdown limit: 15%
- Circuit breaker: Stop trading if hit

**Disaster Recovery:**
- Losing streak protocol: Reduce size 50%
- Major drawdown: Stop trading, review system
- Black swan events: Be flat before major volatility
- Recovery plan: Rebuild confidence with small size

---

## Sample Daily Schedule

### Pre-Market (6:00 - 7:00 AM)
- 6:00 AM: Generate gold playbook
- 6:05 AM: Generate silver playbook
- 6:10 AM: Review key levels
- 6:15 AM: Set alerts
- 6:20 AM: Check macro calendar
- 6:30 AM: Final prep, clear mind

### London Session (3:00 AM - 12:00 PM ET)
- Monitor alerts
- Wait for confirmation
- Execute if criteria met
- Otherwise, stand aside

### NY Session (9:30 AM - 4:00 PM ET)
- Extra vigilance around data (8:30 AM usual time)
- Manage open positions
- Look for new setups if available
- Close or reduce before major events

### Post-Market (4:00 - 5:00 PM ET)
- Review trades
- Update journal
- Calculate metrics
- Plan for tomorrow

### Weekly (Friday Evening)
- Review week's performance
- Calculate statistics
- Identify patterns
- Refine criteria
- Plan next week

---

## Advanced Usage

### Custom Requests

**Conservative Approach:**
```
Generate conservative gold playbook with:
- Tighter stops
- Higher confirmation requirements
- More realistic targets
```

**Aggressive Approach:**
```
Generate aggressive silver playbook with:
- Extended targets
- Wider invalidation
- Breakout focus
```

**Event-Driven:**
```
Generate gold playbook for CPI day:
- Pre-data positioning
- Post-data setups
- Volatility expectations
```

### Multi-Timeframe Integration

**Combine with your own analysis:**
1. Use playbook for intraday structure
2. Add your higher timeframe bias
3. Align confirmations with both
4. Execute when all agree

---

## Key Success Factors

### 1. Discipline
✅ Follow the process religiously
✅ Wait for confirmation every time
✅ Respect stops without exception
✅ Journal every trade

### 2. Patience  
✅ Stand aside when no confirmation
✅ Don't force trades
✅ Accept missed opportunities
✅ Quality over quantity

### 3. Risk Management
✅ Never risk more than 1-2% per trade
✅ Use position sizing calculator
✅ Honor daily/weekly loss limits
✅ Reduce size after losses

### 4. Continuous Improvement
✅ Track what confirmations work best
✅ Refine criteria based on data
✅ Learn from losses
✅ Adapt to changing markets

### 5. Emotional Control
✅ No revenge trading
✅ No over-trading after wins
✅ Stick to the plan
✅ Take breaks when stressed

---

## Emergency Protocols

### If You're Down 5% in a Day:
1. Stop trading immediately
2. Close all positions
3. Take the rest of the day off
4. Review what went wrong
5. Don't trade next day
6. Return with 50% size

### If You're Down 15% in a Month:
1. Stop trading for one week
2. Full system review
3. Paper trade only for two weeks
4. Return with 25% size
5. Rebuild slowly

### If You Break a Rule:
1. Acknowledge it immediately
2. Exit the position if still open
3. Journal why it happened
4. Implement prevention measure
5. Don't break the same rule twice

---

## Resources

### Daily Tools
- [ ] Playbook generator (this skill)
- [ ] Trading platform with alerts
- [ ] Economic calendar
- [ ] Position size calculator
- [ ] Trading journal

### Weekly Tools
- [ ] Performance spreadsheet
- [ ] Win rate tracker
- [ ] Confirmation effectiveness analyzer
- [ ] Equity curve

### Learning
- [ ] Order flow education
- [ ] Options/gamma basics
- [ ] Macro fundamentals
- [ ] Technical analysis refinement

---

## Final Reminders

**📌 This is a tool, not a oracle**
- Playbooks provide structure, not guarantees
- Confirmation is mandatory
- You make the final decision

**📌 Process > Outcomes**
- Perfect process with loss = good trade
- Bad process with profit = bad trade
- Focus on what you can control

**📌 Sustainable Approach**
- Small consistent gains compound
- Avoid home runs mentality  
- Survive to trade another day
- Marathon, not sprint

**📌 Engineering Mindset**
- Treat trading like a system
- Measure, improve, iterate
- Automate where possible
- Stay objective

---

**You've got the skill. Now build the discipline.**

🚀 Trade structure, flow, and logic — not predictions.
