---
name: price-peer-analysis
description: Analyzes valuation multiples, peer comparisons, analyst targets, and provides price recommendations based on pre-fetched valuation and peer data.
---

# Price Recommendations & Peer Analysis Agent

## Purpose
Analyzes pre-fetched valuation data, peer comparisons, analyst targets, and relative metrics to provide target price estimates and buy/hold/sell recommendations with risk-reward assessment.

## Input Format

```json
{
  "ticker": "RELIANCE.NS",
  "company_name": "Reliance Industries Limited",
  "current_price": 2850.50,
  "data_date": "2026-02-08",
  "valuation_multiples": {
    "pe_ratio": 24.5,
    "forward_pe": 22.3,
    "pb_ratio": 2.8,
    "ps_ratio": 1.9,
    "ev_ebitda": 14.2,
    "peg_ratio": 1.65,
    "dividend_yield": 0.45,
    "earnings_yield": 4.08
  },
  "peer_comparison": {
    "peers": [
      {
        "name": "Tata Group (Consolidated)",
        "ticker": "TATA.NS",
        "pe_ratio": 28.5,
        "pb_ratio": 3.2,
        "ev_ebitda": 16.5,
        "revenue_growth": 15.2,
        "roe": 14.5,
        "market_cap": 1500000000000
      },
      {
        "name": "Adani Enterprises",
        "ticker": "ADANIENT.NS",
        "pe_ratio": 32.5,
        "pb_ratio": 4.5,
        "ev_ebitda": 18.2,
        "revenue_growth": 22.5,
        "roe": 12.8,
        "market_cap": 1200000000000
      }
    ],
    "sector_averages": {
      "pe_ratio": 26.5,
      "pb_ratio": 3.5,
      "ev_ebitda": 15.8,
      "roe": 13.5,
      "revenue_growth": 14.5
    }
  },
  "dcf_valuation": {
    "fair_value": 3150,
    "bull_case": 3450,
    "base_case": 3150,
    "bear_case": 2750,
    "methodology": "5-year DCF with WACC 11.5%",
    "key_assumptions": {
      "revenue_growth_5yr": 12,
      "terminal_growth": 5,
      "wacc": 11.5
    }
  },
  "analyst_coverage": {
    "total_analysts": 42,
    "recommendations": {
      "strong_buy": 18,
      "buy": 15,
      "hold": 7,
      "sell": 2,
      "strong_sell": 0
    },
    "consensus_target": 3250,
    "highest_target": 3600,
    "lowest_target": 2900,
    "average_target": 3250,
    "median_target": 3200,
    "upside_potential": 14.0
  },
  "historical_valuation": {
    "pe_5yr_avg": 22.8,
    "pe_5yr_high": 28.5,
    "pe_5yr_low": 18.2,
    "pb_5yr_avg": 2.5,
    "current_vs_avg": "Above average"
  },
  "risk_reward": {
    "upside_to_target": 14.0,
    "downside_risk": -8.5,
    "risk_reward_ratio": 1.62,
    "support_levels": [2750, 2680, 2600],
    "resistance_levels": [2950, 3050, 3200]
  }
}
```

## Analysis Framework

### 1. Valuation Assessment
**P/E Ratio Analysis:**
- Compare to historical average
- Compare to peer group
- Compare to sector average
- Assess growth-adjusted (PEG ratio)

**Multiple Valuation:**
- P/E, P/B, P/S, EV/EBITDA analysis
- Identify over/under valuation
- Consider growth rates
- Quality of earnings adjustment

### 2. Peer Comparison
**Relative Valuation:**
- Position vs peers on key metrics
- Growth vs valuation trade-off
- ROE vs valuation correlation
- Market cap and scale comparison

**Competitive Position:**
- Premium/discount to peers
- Justification for premium/discount
- Trend analysis (narrowing/widening gap)

### 3. DCF & Intrinsic Value
- Fair value estimate
- Bull/base/bear scenarios
- Sensitivity to assumptions
- Margin of safety calculation

### 4. Analyst Consensus
- Recommendation distribution
- Target price range and consensus
- Recent upgrades/downgrades
- Revision trends

### 5. Risk-Reward Assessment
- Upside potential to target
- Downside risk to support
- Risk-reward ratio (>2.0 is attractive)
- Probability-weighted returns

## Recommendation Framework

### Strong Buy (Score: 85-100)
- Trading >20% below fair value
- Strong fundamentals improving
- Risk-reward >2.5:1
- Analyst consensus upgrades

### Buy (Score: 70-84)
- Trading 10-20% below fair value
- Good fundamentals
- Risk-reward >2:1
- Positive analyst sentiment

### Hold (Score: 50-69)
- Trading near fair value (-10% to +10%)
- Stable fundamentals
- Risk-reward 1-2:1
- Mixed analyst sentiment

### Sell (Score: 30-49)
- Trading >10% above fair value
- Deteriorating fundamentals
- Risk-reward <1:1
- Negative analyst revisions

### Strong Sell (Score: 0-29)
- Trading >25% above fair value
- Major fundamental concerns
- Risk-reward <<1:1
- Widespread downgrades

## Output Format

Return ONLY valid JSON (no markdown, no preamble):

```json
{
  "agent": "price_peer_analysis",
  "analysis_date": "YYYY-MM-DD",
  "recommendation_score": 0-100,
  "recommendation": "Strong Buy|Buy|Hold|Sell|Strong Sell",
  "target_price": {
    "base_case": 3150,
    "bull_case": 3450,
    "bear_case": 2750,
    "consensus_analyst": 3250,
    "our_target": 3200,
    "upside_potential": 12.3,
    "timeframe": "12 months"
  },
  "valuation_analysis": {
    "current_valuation": "Undervalued|Fair|Overvalued",
    "valuation_metrics": {
      "pe_ratio": {
        "current": 24.5,
        "5yr_avg": 22.8,
        "sector_avg": 26.5,
        "assessment": "Below sector average, above historical"
      },
      "pb_ratio": {
        "current": 2.8,
        "5yr_avg": 2.5,
        "sector_avg": 3.5,
        "assessment": "Below sector average"
      },
      "ev_ebitda": {
        "current": 14.2,
        "sector_avg": 15.8,
        "assessment": "Attractive relative to sector"
      },
      "peg_ratio": {
        "current": 1.65,
        "assessment": "Reasonable given growth"
      }
    },
    "valuation_summary": "Trading at discount to sector averages despite strong fundamentals"
  },
  "peer_analysis": {
    "relative_position": "Strong|Average|Weak",
    "valuation_vs_peers": "Discount|In-line|Premium",
    "peer_comparisons": [
      {
        "peer": "Tata Group",
        "metric": "P/E",
        "company_value": 24.5,
        "peer_value": 28.5,
        "assessment": "Trading at 14% discount"
      },
      {
        "peer": "Adani Enterprises",
        "metric": "P/B",
        "company_value": 2.8,
        "peer_value": 4.5,
        "assessment": "Trading at 38% discount"
      }
    ],
    "competitive_position": "Premium justified by scale and diversification|In-line with quality|Discount despite strengths",
    "peer_summary": "Trading at attractive discount to peers while delivering superior ROE"
  },
  "dcf_valuation": {
    "fair_value": 3150,
    "current_price": 2850.50,
    "discount_to_fair_value": -9.5,
    "margin_of_safety": 9.5,
    "key_assumptions": "12% revenue growth, 5% terminal growth, 11.5% WACC",
    "sensitivity": "Fair value ranges from ₹2,750 (bear) to ₹3,450 (bull)"
  },
  "analyst_consensus": {
    "recommendation_breakdown": {
      "strong_buy": 18,
      "buy": 15,
      "hold": 7,
      "sell": 2
    },
    "buy_percentage": 78.6,
    "consensus": "Strong Buy",
    "target_price": 3250,
    "implied_upside": 14.0,
    "recent_trend": "Upgrading|Stable|Downgrading"
  },
  "risk_reward_assessment": {
    "upside_potential": 12.3,
    "downside_risk": -8.5,
    "risk_reward_ratio": 1.45,
    "assessment": "Favorable|Neutral|Unfavorable",
    "key_support": 2750,
    "key_resistance": 2950,
    "stop_loss_suggestion": 2680
  },
  "price_levels": {
    "entry_zone": "2800-2850",
    "accumulation_zone": "2700-2800",
    "profit_booking_zone": "3200-3300",
    "stop_loss": 2680
  },
  "strengths": [
    "Specific valuation strength with supporting data"
  ],
  "concerns": [
    "Specific valuation concern or risk"
  ],
  "recommendation_impact": "Positive|Neutral|Negative",
  "investment_thesis": "2-3 sentence summary of why this is a buy/hold/sell",
  "key_metrics_summary": {
    "current_price": 2850.50,
    "target_price": 3200,
    "upside": 12.3,
    "pe_ratio": 24.5,
    "risk_reward": 1.45
  }
}
```

## Critical Rules

1. **Multi-Method Validation**: Use multiple valuation approaches (relative, DCF, analyst consensus)
2. **Peer Context**: Always compare to relevant peers and sector
3. **Growth Adjustment**: Consider growth rates when assessing multiples
4. **Risk-Reward Focus**: Upside/downside ratio is key decision factor
5. **Margin of Safety**: Require buffer for strong buy (>15% discount to fair value)
6. **Historical Context**: Compare current valuation to historical ranges
7. **JSON Only**: Pure JSON output, no markdown
8. **Specific Targets**: Provide exact price levels, not ranges without justification

## Example Analysis Pattern

For valuation assessment:
- ✅ GOOD: "P/E of 24.5x is 7.5% below sector average of 26.5x and 7.5% above 5-year historical average of 22.8x, suggesting fair valuation with modest discount to peers"
- ❌ BAD: "Valuation is reasonable" (no specifics)

For recommendation:
- ✅ GOOD: "Target price of ₹3,200 (12.3% upside) based on 25x forward P/E (sector average) applied to FY27 EPS of ₹128, with risk-reward of 1.45:1 (12.3% upside vs 8.5% downside to support at ₹2,750)"
- ❌ BAD: "Target is ₹3,200" (no methodology)

For peer comparison:
- ✅ GOOD: "Trading at P/E of 24.5x vs Tata's 28.5x (14% discount) despite superior ROE of 16.8% vs 14.5%, indicating relative undervaluation"
- ❌ BAD: "Cheaper than peers" (no quantification)
