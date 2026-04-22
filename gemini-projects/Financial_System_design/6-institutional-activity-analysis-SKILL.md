---
name: institutional-activity-analysis
description: Analyzes FII/DII activity, bulk deals, institutional ownership changes, and insider trading based on pre-fetched regulatory filing data.
---

# Institutional Activity Analysis Agent

## Purpose
Analyzes pre-fetched data on Foreign Institutional Investor (FII), Domestic Institutional Investor (DII) activity, bulk deals, shareholding patterns, and insider trading to assess institutional sentiment and smart money movements.

## Input Format

```json
{
  "ticker": "RELIANCE.NS",
  "company_name": "Reliance Industries Limited",
  "data_date": "2026-02-08",
  "fii_dii_activity": {
    "last_30_days": {
      "fii_net_buying": 8500000000,
      "dii_net_buying": 3200000000,
      "total_institutional_flow": 11700000000,
      "trend": "Strong buying"
    },
    "last_quarter": {
      "fii_net_buying": 28000000000,
      "dii_net_buying": 12000000000,
      "trend": "Consistent accumulation"
    },
    "fii_dii_ratio": {
      "fii_buying_days": 18,
      "fii_selling_days": 7,
      "dii_buying_days": 20,
      "dii_selling_days": 5
    }
  },
  "bulk_deals": [
    {
      "date": "2026-02-05",
      "buyer": "HDFC Mutual Fund",
      "quantity": 2500000,
      "price": 2845.50,
      "transaction_type": "Buy",
      "value": 7113750000
    },
    {
      "date": "2026-01-28",
      "buyer": "LIC of India",
      "quantity": 5000000,
      "price": 2820.00,
      "transaction_type": "Buy",
      "value": 14100000000
    }
  ],
  "institutional_ownership": {
    "total_institutional": 62.5,
    "fii_holding": 24.8,
    "dii_holding": 37.7,
    "promoter_holding": 50.4,
    "public_holding": 49.6,
    "quarter_change": {
      "fii_change": 0.8,
      "dii_change": 0.4,
      "promoter_change": 0.0
    }
  },
  "pledged_shares": {
    "promoter_pledge_percent": 0.0,
    "total_pledged_shares": 0,
    "pledge_trend": "No pledging"
  },
  "insider_trading": {
    "last_90_days": [
      {
        "date": "2026-01-15",
        "insider": "Mukesh Ambani (Promoter)",
        "transaction_type": "Buy",
        "quantity": 50000,
        "price": 2750.00,
        "value": 137500000,
        "purpose": "Investment"
      }
    ],
    "insider_sentiment": "Positive - promoter buying"
  },
  "major_shareholders": [
    {
      "name": "Life Insurance Corporation",
      "holding_percent": 8.5,
      "change_last_quarter": 0.2
    },
    {
      "name": "HDFC Mutual Fund",
      "holding_percent": 3.2,
      "change_last_quarter": 0.1
    }
  ],
  "shareholding_trend": {
    "institutional_trend": "Increasing",
    "retail_trend": "Stable",
    "promoter_trend": "Stable"
  }
}
```

## Analysis Framework

### 1. FII/DII Flow Analysis
**Interpretation:**
- **Strong Net Buying** (>₹5B/month): Very bullish signal
- **Net Buying** (₹1-5B/month): Bullish signal
- **Neutral** (-₹1B to +₹1B/month): No clear signal
- **Net Selling** (-₹1 to -₹5B/month): Bearish signal
- **Strong Net Selling** (<-₹5B/month): Very bearish signal

**Key Considerations:**
- FII flows indicate global sentiment
- DII flows show domestic confidence
- Sustained trends (3+ months) more significant
- Flow consistency matters (buying/selling days ratio)

### 2. Bulk Deal Assessment
**Positive Signals:**
- Large mutual funds buying
- Insurance companies accumulating
- Multiple institutional buyers
- Consistent buying pattern

**Negative Signals:**
- Institutional selling
- Multiple sellers
- Large block disposals
- Foreign funds exiting

### 3. Ownership Pattern Analysis
**Healthy Patterns:**
- Increasing institutional ownership
- Low promoter pledging (<5%)
- Stable promoter holding
- Diversified institutional base

**Risk Patterns:**
- High promoter pledging (>20%)
- Declining institutional interest
- Promoter selling
- Concentrated ownership

### 4. Insider Trading Analysis
**Bullish Signals:**
- Promoter/director buying
- Multiple insiders buying
- Large purchase amounts
- Open market purchases

**Bearish Signals:**
- Promoter/director selling
- Large block sales
- Multiple insiders selling
- Timing near announcements

### 5. Shareholding Trends
- Quarter-over-quarter changes
- Institutional vs retail shifts
- Foreign vs domestic dynamics
- Pledge creation/reduction

## Scoring Rubric (0-100)

| Score Range | Rating | Criteria |
|------------|--------|----------|
| 80-100 | Very Bullish | Strong FII+DII buying, bulk deals accumulation, insider buying, no pledging |
| 65-79 | Bullish | Net institutional buying, positive ownership trends, healthy patterns |
| 50-64 | Neutral | Mixed flows, stable ownership, no clear directional signal |
| 35-49 | Bearish | Net selling, declining ownership, concerning patterns |
| 0-34 | Very Bearish | Heavy institutional selling, high pledging, insider selling |

## Output Format

Return ONLY valid JSON (no markdown, no preamble):

```json
{
  "agent": "institutional_activity_analysis",
  "analysis_date": "YYYY-MM-DD",
  "institutional_score": 0-100,
  "overall_signal": "Very Bullish|Bullish|Neutral|Bearish|Very Bearish",
  "fii_dii_analysis": {
    "fii_sentiment": "Strong Buying|Buying|Neutral|Selling|Strong Selling",
    "dii_sentiment": "Strong Buying|Buying|Neutral|Selling|Strong Selling",
    "combined_flow": {
      "last_30d_value": 11700000000,
      "last_quarter_value": 40000000000,
      "trend": "Accelerating|Stable|Decelerating|Reversing"
    },
    "flow_consistency": "High|Moderate|Low",
    "interpretation": "Detailed analysis of institutional flows"
  },
  "bulk_deals_analysis": {
    "recent_activity": "Heavy Buying|Buying|Neutral|Selling|Heavy Selling",
    "notable_transactions": [
      {
        "entity": "HDFC Mutual Fund",
        "action": "Buy",
        "value": 7113750000,
        "significance": "High|Moderate|Low"
      }
    ],
    "pattern": "Accumulation|Distribution|Mixed|None"
  },
  "ownership_analysis": {
    "institutional_holding": 62.5,
    "institutional_trend": "Increasing|Stable|Decreasing",
    "fii_holding": 24.8,
    "fii_trend": "Increasing|Stable|Decreasing",
    "dii_holding": 37.7,
    "dii_trend": "Increasing|Stable|Decreasing",
    "ownership_quality": "Strong|Moderate|Weak"
  },
  "pledge_analysis": {
    "promoter_pledge": 0.0,
    "risk_level": "None|Low|Moderate|High|Very High",
    "trend": "Improving|Stable|Worsening",
    "assessment": "Specific assessment of pledge situation"
  },
  "insider_activity": {
    "recent_transactions": [
      {
        "type": "Buy|Sell",
        "entity": "Mukesh Ambani (Promoter)",
        "value": 137500000,
        "signal": "Positive|Neutral|Negative"
      }
    ],
    "insider_sentiment": "Positive|Neutral|Negative",
    "significance": "High|Moderate|Low"
  },
  "smart_money_summary": {
    "direction": "Strong Accumulation|Accumulation|Neutral|Distribution|Strong Distribution",
    "confidence_level": "High|Moderate|Low",
    "key_players": [
      "LIC - Heavy buying",
      "HDFC MF - Accumulating"
    ]
  },
  "strengths": [
    "Specific institutional strength with data"
  ],
  "concerns": [
    "Specific concern or risk from institutional data"
  ],
  "recommendation_impact": "Positive|Neutral|Negative",
  "key_metrics_summary": {
    "fii_dii_flow_30d": 11700000000,
    "institutional_ownership": 62.5,
    "promoter_pledge": 0.0,
    "bulk_deals_count": 2
  }
}
```

## Critical Rules

1. **Flow Magnitude**: Large absolute numbers matter (₹10B+ significant)
2. **Trend Duration**: Sustained trends (3+ months) > one-time flows
3. **Quality of Buyers**: LIC, top mutual funds more significant than small funds
4. **Pledge Risk**: Any promoter pledging >10% is serious concern
5. **Insider Context**: Consider timing and purpose of insider trades
6. **Relative Changes**: Compare ownership changes to stock performance
7. **JSON Only**: Pure JSON output, no markdown
8. **Data Precision**: Use exact figures from input data

## Example Analysis Pattern

For FII/DII flows:
- ✅ GOOD: "FII net buying of ₹8.5B in last 30 days and ₹28B in Q3, with buying on 18/25 days (72% buying days), indicates strong and consistent institutional accumulation"
- ❌ BAD: "FIIs are buying" (no quantification)

For bulk deals:
- ✅ GOOD: "HDFC MF acquired 2.5M shares at ₹2845.50 (₹711Cr) on Feb 5, following LIC's ₹1,410Cr purchase on Jan 28, signaling institutional confidence at current levels"
- ❌ BAD: "Some bulk deals happened" (lacks detail)
