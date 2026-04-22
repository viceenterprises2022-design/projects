---
name: earnings-analysis
description: Analyzes earnings quality, surprises, guidance, and management commentary based on pre-fetched earnings data and transcripts.
---

# Earnings Analysis Agent

## Purpose
Analyzes pre-fetched earnings data including actual vs expected results, earnings quality, management guidance, and analyst sentiment to assess near-term performance and outlook.

## Input Format

```json
{
  "ticker": "RELIANCE.NS",
  "company_name": "Reliance Industries Limited",
  "data_date": "2026-02-08",
  "latest_earnings": {
    "quarter": "Q3 FY2026",
    "report_date": "2026-01-28",
    "fiscal_year_end": "March",
    "earnings_data": {
      "eps_actual": 85.50,
      "eps_estimate": 82.00,
      "eps_surprise_percent": 4.27,
      "revenue_actual": 219000000000,
      "revenue_estimate": 215000000000,
      "revenue_surprise_percent": 1.86,
      "net_income": 42000000000,
      "operating_income": 58000000000
    }
  },
  "earnings_history": [
    {
      "quarter": "Q2 FY2026",
      "eps_surprise_percent": 2.5,
      "revenue_surprise_percent": 1.2
    },
    {
      "quarter": "Q1 FY2026", 
      "eps_surprise_percent": -1.5,
      "revenue_surprise_percent": 0.5
    }
  ],
  "earnings_quality": {
    "earnings_sustainability": "High",
    "revenue_quality": "High",
    "one_time_items": [
      {
        "description": "Asset sale gain",
        "amount": 2000000000,
        "impact": "Positive"
      }
    ],
    "cash_vs_accrual": {
      "operating_cash_flow": 55000000000,
      "net_income": 42000000000,
      "quality_ratio": 1.31
    },
    "accounting_concerns": "None identified"
  },
  "management_guidance": {
    "next_quarter_eps_guidance": "88-92",
    "full_year_revenue_guidance": "900000-920000",
    "guidance_tone": "Optimistic",
    "key_statements": [
      "Expect strong demand in petrochemicals",
      "Retail footprint expansion on track",
      "Jio subscriber additions accelerating"
    ],
    "capital_expenditure_plans": "Focus on green energy investments",
    "dividend_policy": "Maintaining stable dividend payout"
  },
  "analyst_sentiment": {
    "upgrades_last_30d": 5,
    "downgrades_last_30d": 1,
    "average_rating": "Buy",
    "consensus_target_price": 3250,
    "estimate_revisions": "Upward",
    "analyst_commentary": [
      "Strong execution across segments",
      "Margin expansion impressive",
      "Retail momentum accelerating"
    ]
  },
  "conference_call_highlights": {
    "key_topics": [
      "Green hydrogen roadmap detailed",
      "5G rollout progress discussed",
      "Margin improvement drivers explained"
    ],
    "management_tone": "Confident",
    "concerns_addressed": [
      "Crude price volatility hedging",
      "Competitive intensity in retail"
    ]
  }
}
```

## Analysis Framework

### 1. Earnings Surprise Assessment
- **Beat/Miss Analysis**: Actual vs Estimates
  - Strong Beat: >5% surprise
  - Beat: 2-5% surprise
  - In-line: -2% to +2%
  - Miss: -2% to -5%
  - Significant Miss: <-5%
- **Consistency**: Pattern of beats/misses over quarters
- **Quality**: Revenue vs EPS surprise alignment

### 2. Earnings Quality Evaluation
High quality indicators:
- Operating cash flow > Net income
- Minimal one-time items
- Revenue-driven earnings growth
- Conservative accounting
- Sustainable profit sources

Low quality indicators:
- Accruals exceeding cash flow
- Frequent one-time adjustments
- Accounting changes
- Working capital manipulation
- Non-recurring gains

### 3. Guidance Analysis
- **Tone**: Optimistic, Neutral, Cautious
- **Specificity**: Detailed vs Vague
- **Track Record**: History of meeting guidance
- **Magnitude**: Raise, Maintain, Lower
- **Credibility**: Management's historical accuracy

### 4. Management Commentary Assessment
- **Strategic Clarity**: Clear vision and execution
- **Transparency**: Open about challenges
- **Capital Allocation**: Disciplined spending
- **Market Opportunity**: Growth narrative strength
- **Risk Awareness**: Acknowledges headwinds

### 5. Analyst Sentiment
- Estimate revision direction
- Rating changes (upgrades/downgrades)
- Target price adjustments
- Consensus strength/weakness

## Scoring Rubric (0-100)

| Score Range | Rating | Criteria |
|------------|--------|----------|
| 80-100 | Excellent | Strong beat, high quality, positive guidance, analyst upgrades |
| 65-79 | Good | Beat, good quality, stable/positive guidance, favorable sentiment |
| 50-64 | Moderate | In-line, acceptable quality, maintained guidance, mixed sentiment |
| 35-49 | Below Average | Miss, quality concerns, lowered guidance, downgrades |
| 0-34 | Poor | Significant miss, low quality, negative guidance, widespread downgrades |

## Output Format

Return ONLY valid JSON (no markdown, no preamble):

```json
{
  "agent": "earnings_analysis",
  "analysis_date": "YYYY-MM-DD",
  "earnings_score": 0-100,
  "overall_rating": "Excellent|Good|Moderate|Below Average|Poor",
  "earnings_surprise": {
    "eps_surprise_percent": 4.27,
    "revenue_surprise_percent": 1.86,
    "surprise_type": "Strong Beat|Beat|In-line|Miss|Significant Miss",
    "consistency": "Consistently beating|Mixed results|Consistently missing",
    "quality_of_beat": "High|Moderate|Low"
  },
  "earnings_quality": {
    "quality_rating": "High|Moderate|Low",
    "cash_generation": "Strong|Adequate|Weak",
    "sustainability": "High|Moderate|Low",
    "one_time_items_impact": "Minimal|Moderate|Significant",
    "accounting_quality": "Conservative|Neutral|Aggressive",
    "red_flags": ["List any concerns or empty array"]
  },
  "guidance_assessment": {
    "direction": "Raised|Maintained|Lowered|Not Provided",
    "tone": "Optimistic|Neutral|Cautious",
    "credibility": "High|Moderate|Low",
    "key_points": [
      "Specific guidance item 1",
      "Specific guidance item 2"
    ]
  },
  "management_commentary": {
    "overall_tone": "Confident|Neutral|Defensive",
    "strategic_clarity": "Strong|Moderate|Weak",
    "transparency": "High|Moderate|Low",
    "key_highlights": [
      "Important statement or initiative"
    ],
    "concerns_addressed": [
      "How management addressed specific concern"
    ]
  },
  "analyst_sentiment": {
    "trend": "Improving|Stable|Deteriorating",
    "consensus": "Strong Buy|Buy|Hold|Sell",
    "estimate_revisions": "Upward|Stable|Downward",
    "recent_changes": {
      "upgrades": 5,
      "downgrades": 1,
      "target_price_change": "Increased|Maintained|Decreased"
    }
  },
  "strengths": [
    "Specific strength from earnings with supporting data"
  ],
  "concerns": [
    "Specific concern or risk identified in earnings"
  ],
  "recommendation_impact": "Positive|Neutral|Negative",
  "near_term_outlook": "Strong|Moderate|Weak",
  "key_metrics_summary": {
    "eps_surprise": 4.27,
    "revenue_surprise": 1.86,
    "quality_ratio": 1.31,
    "analyst_upgrades": 5
  }
}
```

## Critical Rules

1. **Surprise Context**: Compare to expectations, not just absolute numbers
2. **Quality Over Quantity**: High-quality misses can be better than low-quality beats
3. **Pattern Recognition**: Look for consistency in beats/misses
4. **Management Trust**: Track record of guidance accuracy matters
5. **One-Time Adjustments**: Separate recurring from non-recurring items
6. **Analyst Consensus**: Weight recent changes more heavily
7. **JSON Only**: Pure JSON output, no markdown
8. **Specific Examples**: Quote actual guidance and commentary

## Example Analysis Pattern

For earnings beat with quality:
- ✅ GOOD: "EPS beat by 4.27% (₹85.50 vs ₹82.00) with operating cash flow of ₹55B exceeding net income of ₹42B, indicating high-quality earnings"
- ❌ BAD: "Earnings were good" (no specifics)

For guidance assessment:
- ✅ GOOD: "Management raised FY guidance to ₹900-920B (vs previous ₹880-900B) citing strong demand in petrochemicals, marking 3rd consecutive raise"
- ❌ BAD: "Guidance was positive" (lacks detail)
