# Installation Instructions
## Precious Metals Trading System with Economic Calendar

---

## 📋 Prerequisites

- Access to Claude (claude.ai or API)
- Ability to upload files or access file system
- Internet connection (for calendar fetching)
- 5 minutes of your time

---

## 🎯 What You're Installing

Two integrated skills that work together:

1. **Precious Metals Playbook Skill** - Generates daily trading playbooks
2. **Economic Calendar Skill** - Fetches and analyzes economic events

Together they provide:
- Market structure analysis
- Economic event integration
- Event-driven strategies
- Money supply analysis
- Risk management guidance

---

## 📦 Installation Methods

Choose the method that works best for you:

### Method 1: Share Folder with Claude (Easiest)

**Step 1:** Upload the entire `precious-metals-trading-system` folder to Claude

**Step 2:** Ask Claude:
```
Install the precious metals trading system skills
```

**Step 3:** Claude will:
- Read the skill files
- Place them in the correct locations
- Confirm installation

**Step 4:** Test with:
```
Generate today's gold playbook
```

**✅ Done!** If you see a formatted playbook with calendar section, it's working.

---

### Method 2: Manual File Placement

**Step 1:** Create skill directories
```bash
mkdir -p /mnt/skills/user/precious-metals-playbook
mkdir -p /mnt/skills/user/economic-calendar-metals
```

**Step 2:** Copy skill files
```bash
# Copy playbook skill
cp skills/PLAYBOOK_SKILL.md /mnt/skills/user/precious-metals-playbook/SKILL.md

# Copy calendar skill  
cp skills/ECONOMIC_CALENDAR_SKILL.md /mnt/skills/user/economic-calendar-metals/SKILL.md
```

**Step 3:** Verify installation
```bash
# Check files exist
ls -la /mnt/skills/user/precious-metals-playbook/
ls -la /mnt/skills/user/economic-calendar-metals/
```

**Step 4:** Test
Ask Claude:
```
Generate today's gold playbook
```

**✅ Success!** You should see:
- Market context
- Economic calendar section
- Trading strategies
- Event-specific guidance

---

### Method 3: API Installation (Developers)

If using Claude API:

**Step 1:** Upload skills as system prompts or context

```python
import anthropic

# Read skill files
with open('skills/PLAYBOOK_SKILL.md', 'r') as f:
    playbook_skill = f.read()

with open('skills/ECONOMIC_CALENDAR_SKILL.md', 'r') as f:
    calendar_skill = f.read()

# Include in system prompt
client = anthropic.Anthropic(api_key="your-api-key")

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4000,
    system=f"{playbook_skill}\n\n{calendar_skill}",
    messages=[{
        "role": "user",
        "content": "Generate today's gold playbook"
    }]
)
```

**Step 2:** Test response includes calendar integration

---

## ✅ Verification Checklist

After installation, verify:

- [ ] Playbook skill file exists in `/mnt/skills/user/precious-metals-playbook/SKILL.md`
- [ ] Calendar skill file exists in `/mnt/skills/user/economic-calendar-metals/SKILL.md`
- [ ] Test request generates formatted playbook
- [ ] Calendar section appears in output
- [ ] Event analysis included
- [ ] Pre/during/post-event strategies present

---

## 🧪 Test Cases

### Test 1: Basic Gold Playbook

**Request:**
```
Generate today's gold playbook
```

**Expected Output Should Include:**
- 🧭 Title with XAUUSD
- 📅 Today's date
- 🔍 Market context (2-3 paragraphs)
- 📅 Economic calendar section
- 📊 Expected range
- 🧠 Dealer structure
- 🔴 Sell setup
- 🟢 Buy setup
- 📰 Macro context
- 🎯 Session rules

**✅ Pass:** All sections present and formatted correctly

---

### Test 2: Silver with Calendar

**Request:**
```
Create silver playbook for tomorrow
```

**Expected Output Should Include:**
- XAGUSD symbol (not XAUUSD)
- Tomorrow's date
- Economic calendar for tomorrow's events
- Silver-specific volatility ranges
- All standard sections

**✅ Pass:** Silver-specific content, correct date, calendar included

---

### Test 3: Calendar Integration

**Request:**
```
Generate gold playbook and include detailed economic calendar analysis
```

**Expected Output Should Include:**
- Expanded calendar section
- Event categorization (HIGH/MEDIUM/LOW)
- Expected move ranges
- Money supply implications
- Pre/during/post-event strategies
- This week's schedule

**✅ Pass:** Comprehensive calendar analysis integrated

---

### Test 4: Event-Driven Adjustment

**Request:**
```
Generate gold playbook for CPI day
```

**Expected Output Should Include:**
- CPI flagged in title or context
- Defensive pre-CPI positioning
- Stand aside during CPI
- Post-CPI reactive strategies
- Expanded range expectations (2-3x normal)
- Risk warnings

**✅ Pass:** Strategies clearly adapted for high-impact event

---

## 🔧 Troubleshooting

### Issue: Skills not loading

**Symptoms:**
- Playbook output generic
- No calendar section
- Missing formatting

**Solutions:**
1. Verify file paths:
   ```bash
   ls /mnt/skills/user/precious-metals-playbook/SKILL.md
   ls /mnt/skills/user/economic-calendar-metals/SKILL.md
   ```

2. Check file permissions:
   ```bash
   chmod 644 /mnt/skills/user/*/SKILL.md
   ```

3. Restart Claude session

4. Re-upload files

---

### Issue: Calendar not fetching

**Symptoms:**
- No calendar section
- Generic "check manually" message
- Missing event analysis

**Solutions:**
1. Verify internet access

2. Test web_fetch manually:
   ```
   Can you fetch https://tradingeconomics.com/calendar
   ```

3. Use web_search fallback:
   ```
   Search for "US economic calendar today"
   ```

4. Manually provide events:
   ```
   Generate gold playbook with these events:
   - 8:30 AM CPI
   - 2:00 PM FOMC Minutes
   ```

---

### Issue: Wrong metal or date

**Symptoms:**
- Gold playbook when silver requested
- Wrong date in title
- Mismatched content

**Solutions:**
1. Be explicit in request:
   ```
   Generate SILVER playbook for February 11, 2026
   ```

2. Provide current price:
   ```
   Gold playbook for today, current price 2,645
   ```

3. Specify both metal and date clearly

---

### Issue: Missing sections

**Symptoms:**
- Some playbook sections absent
- Calendar integration incomplete
- No event strategies

**Solutions:**
1. Check both skills installed (not just one)

2. Request comprehensive analysis:
   ```
   Generate comprehensive gold playbook with full economic calendar integration
   ```

3. Review skill files for completeness:
   ```bash
   wc -l /mnt/skills/user/*/SKILL.md
   # Should show substantial line counts
   ```

---

## 🔄 Update Procedure

When new versions are released:

**Step 1:** Backup current skills
```bash
cp /mnt/skills/user/precious-metals-playbook/SKILL.md ~/backup_playbook.md
cp /mnt/skills/user/economic-calendar-metals/SKILL.md ~/backup_calendar.md
```

**Step 2:** Replace with new versions
```bash
cp skills/PLAYBOOK_SKILL.md /mnt/skills/user/precious-metals-playbook/SKILL.md
cp skills/ECONOMIC_CALENDAR_SKILL.md /mnt/skills/user/economic-calendar-metals/SKILL.md
```

**Step 3:** Test
```
Generate test gold playbook
```

**Step 4:** If issues, restore backups
```bash
cp ~/backup_playbook.md /mnt/skills/user/precious-metals-playbook/SKILL.md
cp ~/backup_calendar.md /mnt/skills/user/economic-calendar-metals/SKILL.md
```

---

## 📊 Post-Installation Setup

### Recommended Next Steps

1. **Read Documentation**
   - [ ] QUICKSTART.md (5 min)
   - [ ] Review example playbooks (10 min)
   - [ ] Skim IMPLEMENTATION_GUIDE.md (15 min)

2. **Generate Test Playbooks**
   - [ ] Gold playbook for today
   - [ ] Silver playbook for today
   - [ ] Both metals comparison
   - [ ] Event-specific playbook (if major event scheduled)

3. **Setup Daily Workflow**
   - [ ] Read DAILY_WORKFLOW.md
   - [ ] Integrate into morning routine
   - [ ] Set up trading journal
   - [ ] Configure alerts/reminders

4. **Customize (Optional)**
   - [ ] Adjust event keywords if needed
   - [ ] Modify volatility expectations
   - [ ] Update risk parameters
   - [ ] Add custom events

---

## 🎓 Learning Path

### Week 1: Familiarization
- Generate daily playbooks
- Read and understand each section
- Don't trade yet, just observe
- Compare playbook to actual price action

### Week 2: Paper Trading
- Follow playbook setups on paper
- Wait for all confirmations
- Track hit rates and outcomes
- Journal observations

### Week 3: Small Size
- Trade with minimal position size (10-25%)
- Follow playbook strictly
- Focus on process, not P&L
- Build confidence

### Week 4+: Normal Trading
- Increase to normal size gradually
- Continue journal discipline
- Track statistics
- Refine based on data

---

## 💡 Tips for Success

### Do's ✅

- ✅ Generate playbook daily (make it routine)
- ✅ Read entire playbook before trading
- ✅ Wait for all confirmations
- ✅ Respect event protocols (especially pre/during high-impact)
- ✅ Journal every trade
- ✅ Track what confirmations work best
- ✅ Size appropriately (reduce before events)
- ✅ Review performance weekly

### Don'ts ❌

- ❌ Skip calendar section ("too long")
- ❌ Trade without confirmations ("it's in the zone")
- ❌ Hold through major events without plan
- ❌ Ignore invalidation levels
- ❌ Overtrade after wins or losses
- ❌ Use full size on event days
- ❌ Chase moves without confirmation
- ❌ Forget to journal

---

## 🆘 Getting Help

### If Installation Fails

1. Check file paths are correct
2. Verify file contents (skills should be ~15-20KB each)
3. Ensure both skills installed (not just one)
4. Try uploading folder directly to Claude
5. Restart Claude session

### If Output is Wrong

1. Be specific in requests (metal, date, event)
2. Provide context (current price, key levels)
3. Request comprehensive analysis if sections missing
4. Check examples folder for expected format
5. Compare your output to examples

### If Calendar Not Working

1. Test internet access
2. Try web_search fallback
3. Manually provide events as workaround
4. Check TradingEconomics.com is accessible
5. Use default event times if all else fails

---

## 📞 Support Resources

### Documentation
- MASTER_README.md - System overview
- IMPLEMENTATION_GUIDE.md - Detailed usage
- ECONOMIC_CALENDAR_README.md - Calendar specifics
- PLAYBOOK_README.md - Playbook details

### Examples
- INTEGRATED_EXAMPLE.md - Full CPI day playbook
- example_gold_playbook.md - Gold sample
- example_silver_playbook.md - Silver sample

### Tools
- economic_calendar_analyzer.py - Standalone script
- Test prompts in examples/

---

## ✨ You're Ready!

Installation complete! 

**Next steps:**
1. Generate your first playbook
2. Review the output carefully
3. Read DAILY_WORKFLOW.md
4. Start building your edge

**Remember:** The system is a tool for systematic analysis, not a magic solution. Success comes from:
- Disciplined execution
- Patient confirmation
- Rigorous risk management
- Continuous learning

---

**Trade structure, flow, and logic — not predictions.**

🚀 Happy Trading!
