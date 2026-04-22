# Quick Start Guide

## Installation (30 seconds)

1. **Upload to Claude:**
   - Share the `precious-metals-playbook-skill` folder with Claude
   - Or use the install script if you have terminal access

2. **Verify Installation:**
   Ask Claude: "Can you generate a gold playbook?"
   
   If the skill is working, you'll get a properly formatted playbook.

## Your First Playbook

**Try this:**
```
Generate today's gold playbook with:
- Current price: 2,645
- Resistance at 2,660
- Support at 2,625
```

**You should get:**
- Market context analysis
- Expected trading range
- Dealer positioning insights
- Buy and sell setups with confirmation criteria
- Macro context
- Session-specific rules

## Common Requests

### Daily Analysis
```
Create today's silver playbook
```

### With Market Context
```
Gold playbook for tomorrow:
- Price: 2,650
- Broken above 2,640
- CPI data at 8:30 AM
```

### Session Specific
```
London session gold analysis
```

### Both Metals
```
Generate playbooks for both gold and silver
```

### Conservative Setup
```
Give me a conservative gold playbook with tighter risk
```

## Understanding the Output

### Key Sections

1. **🔍 MARKET CONTEXT**
   - What's happening in the market
   - Current structure and bias
   - Primary trading stance

2. **📊 EXPECTED RANGE**
   - Today's likely price range
   - Supply/demand zones
   - Fair value area

3. **🧠 DEALER & FLOW**
   - Where dealers are positioned
   - Gamma exposure levels
   - Order flow characteristics

4. **🔴 SELL SETUP**
   - Where to consider shorts
   - Required confirmations
   - Targets and stops

5. **🟢 BUY SETUP**
   - Where to consider longs
   - Required confirmations
   - Targets and stops

6. **📰 MACRO CONTEXT**
   - USD, yields, risk factors
   - Scheduled data releases
   - Session-specific expectations

## Key Concepts

### Confirmation Required
❌ Don't trade just because price hits a zone
✅ Wait for specific confirmation signals

### Examples of Confirmation
- Exhaustion (volume dries up)
- Delta divergence (flow contradicts price)
- Absorption (big orders don't move price)
- Failed breakout (reversal pattern)

### Invalidation Levels
Every setup has a "wrong" level:
- If price goes there, the setup is invalidated
- Exit immediately, don't hope

### Risk Management
- Start with smaller size
- Scale in as confirmation improves
- Scale out at targets
- Use clean breaks for stops (30-min acceptance)

## Tips for Engineers/Technical Professionals

### Systematic Approach
Treat this like a system:
1. Input: Market data
2. Process: Structure analysis
3. Output: Conditional setups
4. Execution: Confirmation-based

### Backtesting Mindset
- Track what confirmations work
- Note invalidation accuracy
- Measure target hit rates
- Refine your criteria

### Process Over Prediction
- "If price does X, then I do Y"
- Not "I think price will do X"
- Conditional logic, not forecasting

## Common Questions

**Q: Do I take every setup?**
A: No. Only trade setups where ALL confirmation criteria appear.

**Q: What if confirmation doesn't appear?**
A: Stand aside. No confirmation = no trade.

**Q: Can I modify the zones?**
A: Yes, but use your own analysis. The playbook provides framework.

**Q: How long are playbooks valid?**
A: Intraday only. Generate fresh each day.

**Q: What if price gaps past my entry?**
A: Don't chase. Wait for next setup or retest.

**Q: Should I hold overnight?**
A: These are intraday setups. Consider closing before end of day.

## Troubleshooting

**Issue: Output doesn't match template**
- Ensure you mentioned gold/silver in request
- Provide current price for context

**Issue: Zones seem wrong**
- Provide key support/resistance levels
- Mention recent price action

**Issue: Too generic**
- Add more market context to your request
- Mention specific chart patterns or levels

**Issue: Want more detail**
- Ask for "comprehensive analysis"
- Request specific aspects (gamma, volume profile, etc.)

## Next Steps

1. **Read Example Playbooks**
   - `examples/example_gold_playbook.md`
   - `examples/example_silver_playbook.md`

2. **Study Implementation Guide**
   - Detailed explanations of each component
   - Advanced usage patterns
   - Customization options

3. **Practice**
   - Generate daily playbooks
   - Compare with actual price action
   - Track which setups work best

4. **Refine**
   - Note what confirmation signals are most reliable
   - Adjust size and risk based on your comfort
   - Develop your own pattern recognition

## Resources

- **Order Flow Education**: Learn about delta, absorption, exhaustion
- **Options Basics**: Understand gamma and dealer positioning
- **Macro Fundamentals**: USD, yields, Fed policy impact on gold/silver
- **Technical Analysis**: Support, resistance, volume profile

## Remember

📌 **This is educational, not financial advice**
📌 **Always do your own analysis**
📌 **Never risk more than you can afford to lose**
📌 **Confirmation > Prediction**

---

**Ready to start?**

Try: `"Generate today's gold playbook"`

🚀 Trade structure, flow, and logic — not predictions.
