---
name: presentation-news-analysis
description: Analyzes investor presentations, news sentiment, major announcements, and strategic initiatives based on pre-fetched news data and presentation materials.
---

# Presentation & News Analysis Agent

## Purpose
Analyzes pre-fetched investor presentations, recent news articles, and major announcements to assess strategic direction, market sentiment, and potential impact on stock performance.

## Input Format

```json
{
  "ticker": "RELIANCE.NS",
  "company_name": "Reliance Industries Limited",
  "data_date": "2026-02-08",
  "investor_presentations": [
    {
      "date": "2026-01-28",
      "title": "Q3 FY2026 Earnings Presentation",
      "key_points": [
        "Green hydrogen capacity to reach 1GW by 2027",
        "Retail store count increased to 18,000 stores",
        "Jio 5G coverage expanded to 500 cities",
        "New energy segment investments of $10B planned"
      ],
      "strategic_initiatives": [
        "Carbon neutrality target by 2035",
        "Expansion into renewable energy",
        "Digital services monetization accelerating"
      ],
      "management_outlook": "Optimistic on all business segments"
    }
  ],
  "recent_news": {
    "last_7_days": [
      {
        "date": "2026-02-07",
        "headline": "Reliance announces partnership with global battery manufacturer",
        "source": "Economic Times",
        "sentiment": "Positive",
        "summary": "Strategic partnership to manufacture EV batteries in India",
        "impact": "High"
      },
      {
        "date": "2026-02-05",
        "headline": "Reliance Retail expands footprint in South India",
        "source": "Business Standard",
        "sentiment": "Positive",
        "summary": "Plans to open 500 new stores in Karnataka and Tamil Nadu",
        "impact": "Medium"
      }
    ],
    "last_30_days": [
      {
        "date": "2026-01-25",
        "headline": "Crude oil prices surge impacts refining margins",
        "source": "Reuters",
        "sentiment": "Negative",
        "summary": "Rising crude costs may pressure Q4 margins",
        "impact": "Medium"
      }
    ]
  },
  "news_sentiment_aggregate": {
    "overall_sentiment": "Positive",
    "sentiment_score": 72,
    "positive_articles": 15,
    "neutral_articles": 8,
    "negative_articles": 3,
    "sentiment_trend": "Improving",
    "key_themes": [
      "Green energy transition",
      "Retail expansion",
      "5G rollout success",
      "Margin concerns"
    ]
  },
  "major_announcements": [
    {
      "date": "2026-01-15",
      "type": "Strategic Partnership",
      "description": "Joint venture with Saudi Aramco for petrochemical complex",
      "expected_impact": "Positive - long-term growth",
      "market_reaction": "Stock up 3.2% on announcement"
    },
    {
      "date": "2025-12-20",
      "type": "Dividend Declaration",
      "description": "Interim dividend of ₹10 per share",
      "expected_impact": "Positive - shareholder returns",
      "market_reaction": "Positive reception"
    }
  ],
  "regulatory_news": [
    {
      "date": "2026-01-30",
      "description": "New environmental regulations for refineries",
      "impact": "Moderate - requires compliance investments",
      "company_response": "Already compliant, minimal impact expected"
    }
  ],
  "product_pipeline": {
    "new_launches": [
      "JioAirFiber expanding to tier 2 cities",
      "Reliance Digital partnership with global brands"
    ],
    "innovation_initiatives": [
      "AI-powered retail analytics platform",
      "Blockchain for supply chain"
    ]
  }
}
```

## Analysis Framework

### 1. Presentation Insights Extraction
- **Strategic Vision**: Clarity and ambition of strategy
- **Execution Track Record**: Delivery on past commitments
- **Growth Initiatives**: New markets, products, partnerships
- **Capital Allocation**: Investment priorities and discipline
- **Innovation Focus**: R&D, technology adoption

### 2. News Sentiment Analysis
Sentiment scoring (0-100):
- **Highly Positive (80-100)**: Major positive developments, strategic wins
- **Positive (60-79)**: Good news, favorable developments
- **Neutral (40-59)**: Mixed or routine news
- **Negative (20-39)**: Challenges, concerns
- **Highly Negative (0-19)**: Major setbacks, crises

### 3. Announcement Impact Assessment
- **Strategic Significance**: Long-term vs short-term
- **Market Reaction**: Stock price response
- **Execution Risk**: Likelihood of successful delivery
- **Competitive Implications**: Advantage gained/lost

### 4. Sentiment Trend Analysis
- **Direction**: Improving, Stable, Deteriorating
- **Consistency**: Alignment across news sources
- **Theme Identification**: Recurring topics (positive/negative)
- **Credibility**: Source quality and reliability

### 5. Risk Event Monitoring
- Regulatory changes
- Legal issues
- Management changes
- Competitive threats
- Market disruptions

## Scoring Rubric (0-100)

| Score Range | Rating | Criteria |
|------------|--------|----------|
| 80-100 | Highly Positive | Strong positive news, clear strategy, major wins, improving sentiment |
| 65-79 | Positive | Good developments, solid strategy, favorable news flow |
| 50-64 | Neutral | Mixed news, routine updates, no major changes |
| 35-49 | Negative | Concerning developments, challenges, declining sentiment |
| 0-34 | Highly Negative | Major setbacks, crisis, negative news dominance |

## Output Format

Return ONLY valid JSON (no markdown, no preamble):

```json
{
  "agent": "presentation_news_analysis",
  "analysis_date": "YYYY-MM-DD",
  "sentiment_score": 0-100,
  "overall_assessment": "Highly Positive|Positive|Neutral|Negative|Highly Negative",
  "presentation_insights": {
    "strategic_clarity": "High|Moderate|Low",
    "growth_initiatives": [
      {
        "initiative": "Green hydrogen expansion",
        "significance": "High|Moderate|Low",
        "timeline": "Near-term|Medium-term|Long-term",
        "credibility": "High|Moderate|Low"
      }
    ],
    "capital_allocation": "Disciplined|Moderate|Aggressive|Unclear",
    "execution_confidence": "High|Moderate|Low"
  },
  "news_sentiment": {
    "current_sentiment": "Positive|Neutral|Negative",
    "sentiment_trend": "Improving|Stable|Deteriorating",
    "positive_themes": [
      "Theme with specific news reference"
    ],
    "negative_themes": [
      "Concern with specific news reference"
    ],
    "sentiment_distribution": {
      "positive": 15,
      "neutral": 8,
      "negative": 3
    }
  },
  "major_developments": [
    {
      "development": "Partnership with Saudi Aramco",
      "impact": "Positive|Neutral|Negative",
      "significance": "High|Moderate|Low",
      "timeframe": "Immediate|Near-term|Long-term",
      "analysis": "Detailed impact assessment"
    }
  ],
  "strategic_initiatives": [
    {
      "initiative": "Carbon neutrality by 2035",
      "assessment": "Ambitious|Realistic|Conservative",
      "competitive_advantage": "Significant|Moderate|Minimal",
      "execution_risk": "Low|Moderate|High"
    }
  ],
  "regulatory_landscape": {
    "regulatory_risk": "Low|Moderate|High",
    "recent_changes": [
      "Specific regulatory change and impact"
    ],
    "company_preparedness": "Well-positioned|Adequate|Vulnerable"
  },
  "innovation_pipeline": {
    "strength": "Strong|Moderate|Weak",
    "key_innovations": [
      "Specific innovation with potential impact"
    ]
  },
  "strengths": [
    "Positive development with supporting evidence"
  ],
  "concerns": [
    "Risk or challenge identified in news/presentations"
  ],
  "recommendation_impact": "Positive|Neutral|Negative",
  "narrative_summary": "2-3 sentence summary of overall sentiment and key themes",
  "key_metrics_summary": {
    "sentiment_score": 72,
    "positive_news_count": 15,
    "major_announcements": 2,
    "strategic_initiatives": 3
  }
}
```

## Critical Rules

1. **Source Quality**: Weight credible sources more heavily (Reuters, Bloomberg vs social media)
2. **Recency Bias**: Recent news matters more than old news
3. **Material Impact**: Distinguish between noise and meaningful developments
4. **Context Matters**: Consider industry and market context
5. **Strategic Alignment**: Assess initiatives against stated strategy
6. **Sentiment Objectivity**: Base on facts, not hype
7. **JSON Only**: Pure JSON output, no markdown
8. **Specific Examples**: Quote actual headlines and announcements

## Example Analysis Pattern

For strategic initiative:
- ✅ GOOD: "Green hydrogen capacity target of 1GW by 2027 represents significant strategic shift, backed by $10B investment commitment, positioning company ahead of energy transition curve"
- ❌ BAD: "Company is investing in green energy" (lacks specifics)

For news sentiment:
- ✅ GOOD: "72% of news articles (15/23) in last 30 days were positive, dominated by retail expansion and 5G success themes, with sentiment improving from neutral to positive trend"
- ❌ BAD: "News sentiment is positive" (no quantification)
