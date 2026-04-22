---
name: social-media-pulse-analysis
description: Analyzes social media sentiment, trending topics, retail investor buzz, and early warning signals based on pre-fetched social media data.
---

# Social Media Pulse Analysis Agent

## Purpose
Analyzes pre-fetched social media data from Twitter/X, Reddit, StockTwits, and other platforms to gauge retail investor sentiment, identify trending narratives, and detect early warning signals or momentum shifts.

## Input Format

```json
{
  "ticker": "RELIANCE.NS",
  "company_name": "Reliance Industries Limited",
  "data_date": "2026-02-08",
  "twitter_sentiment": {
    "overall_sentiment": "Positive",
    "sentiment_score": 68,
    "tweet_volume_7d": 15600,
    "tweet_volume_trend": "Increasing",
    "sentiment_distribution": {
      "positive": 62,
      "neutral": 28,
      "negative": 10
    },
    "trending_topics": [
      {
        "topic": "Green hydrogen expansion",
        "mentions": 3500,
        "sentiment": "Positive"
      },
      {
        "topic": "5G rollout success",
        "mentions": 2800,
        "sentiment": "Positive"
      },
      {
        "topic": "Margin pressure concerns",
        "mentions": 1200,
        "sentiment": "Negative"
      }
    ],
    "influential_mentions": [
      {
        "author": "@MarketGuru (250K followers)",
        "tweet": "Reliance's green energy pivot is a game-changer. Long-term bullish.",
        "engagement": 8500,
        "sentiment": "Positive"
      }
    ]
  },
  "reddit_sentiment": {
    "subreddits": ["r/IndiaInvestments", "r/IndianStockMarket"],
    "overall_sentiment": "Positive",
    "post_count_7d": 45,
    "comment_count_7d": 680,
    "sentiment_score": 71,
    "top_discussions": [
      {
        "title": "Reliance: A 10-year hold?",
        "subreddit": "r/IndiaInvestments",
        "upvotes": 450,
        "comments": 120,
        "sentiment": "Positive",
        "summary": "Discussion about long-term value, divided opinions on valuation"
      },
      {
        "title": "Concerned about RIL debt levels",
        "subreddit": "r/IndianStockMarket",
        "upvotes": 180,
        "comments": 85,
        "sentiment": "Neutral",
        "summary": "Debate about debt sustainability and leverage"
      }
    ]
  },
  "stocktwits_data": {
    "overall_sentiment": "Bullish",
    "bullish_percent": 72,
    "bearish_percent": 28,
    "message_volume_7d": 2400,
    "momentum": "Strong",
    "trending_tags": ["#BuyTheDip", "#LongTerm", "#GreenEnergy"]
  },
  "retail_sentiment_aggregate": {
    "overall_buzz_level": "High",
    "buzz_score": 75,
    "sentiment_direction": "Positive",
    "trending_narratives": [
      "Green energy transition positioning",
      "5G market dominance",
      "Retail business growth",
      "Debt level concerns"
    ],
    "sentiment_shift": "Improving from neutral to positive (last 30 days)"
  },
  "search_trends": {
    "google_trends_score": 82,
    "search_volume_trend": "Increasing",
    "related_searches": [
      "Reliance green hydrogen",
      "Reliance share price target",
      "Is Reliance stock a buy"
    ]
  },
  "early_warning_signals": {
    "sudden_sentiment_shifts": "None detected",
    "unusual_volume_spikes": "None",
    "coordinated_activity": "None detected",
    "misinformation_flags": "None"
  },
  "retail_investor_activity": {
    "trading_app_interest": "High",
    "new_investor_interest": "Moderate",
    "discussion_quality": "Mixed - ranging from informed to speculative"
  }
}
```

## Analysis Framework

### 1. Sentiment Quantification
**Sentiment Score Interpretation (0-100):**
- **Very Bullish (80-100)**: Overwhelmingly positive, high excitement
- **Bullish (65-79)**: Positive sentiment dominates
- **Neutral (45-64)**: Mixed or no clear sentiment
- **Bearish (30-44)**: Negative sentiment increasing
- **Very Bearish (0-29)**: Overwhelmingly negative, fear/panic

### 2. Buzz Level Assessment
**Volume & Engagement:**
- **High Buzz**: >10K mentions/week, trending topics
- **Moderate Buzz**: 2-10K mentions/week, regular discussion
- **Low Buzz**: <2K mentions/week, minimal attention

**Quality Considerations:**
- Informed discussion vs speculation
- Factual vs emotional sentiment
- Retail vs experienced investor participation

### 3. Trending Narrative Analysis
**Positive Narratives:**
- Growth initiatives, strategic moves
- Earnings beats, guidance raises
- New partnerships, product launches

**Negative Narratives:**
- Competitive threats, market share loss
- Regulatory issues, legal problems
- Valuation concerns, profit warnings

### 4. Influencer Impact
- Follower count and credibility
- Historical accuracy of calls
- Engagement levels (likes, shares, comments)
- Sentiment propagation

### 5. Early Warning Detection
**Red Flags:**
- Sudden negative sentiment spike
- Unusual volume without news
- Coordinated pump-and-dump patterns
- Misinformation spread
- Insider leak rumors

### 6. Retail Momentum Indicators
- Search trend direction
- Trading app interest
- New investor inflows
- Discussion frequency

## Scoring Rubric (0-100)

| Score Range | Rating | Criteria |
|------------|--------|----------|
| 80-100 | Very Bullish | High positive buzz, strong momentum, influential support, positive narratives |
| 65-79 | Bullish | Positive sentiment dominates, good buzz, favorable discussions |
| 50-64 | Neutral | Mixed sentiment, moderate buzz, balanced narratives |
| 35-49 | Bearish | Negative sentiment rising, declining buzz, concerning narratives |
| 0-34 | Very Bearish | Overwhelmingly negative, panic signals, serious concerns |

## Output Format

Return ONLY valid JSON (no markdown, no preamble):

```json
{
  "agent": "social_media_pulse_analysis",
  "analysis_date": "YYYY-MM-DD",
  "buzz_score": 0-100,
  "overall_sentiment": "Very Bullish|Bullish|Neutral|Bearish|Very Bearish",
  "sentiment_analysis": {
    "aggregate_sentiment": "Positive|Neutral|Negative",
    "sentiment_score": 68,
    "sentiment_trend": "Improving|Stable|Deteriorating",
    "platform_breakdown": {
      "twitter_sentiment": "Positive|Neutral|Negative",
      "reddit_sentiment": "Positive|Neutral|Negative",
      "stocktwits_sentiment": "Bullish|Neutral|Bearish"
    },
    "sentiment_consistency": "Aligned across platforms|Mixed signals|Conflicting"
  },
  "buzz_metrics": {
    "buzz_level": "High|Moderate|Low",
    "volume_trend": "Increasing|Stable|Decreasing",
    "engagement_quality": "High|Moderate|Low",
    "total_mentions_7d": 18045,
    "search_interest": "High|Moderate|Low"
  },
  "trending_narratives": {
    "positive_themes": [
      {
        "theme": "Green hydrogen expansion",
        "mentions": 3500,
        "impact": "High|Moderate|Low",
        "credibility": "High|Moderate|Low"
      }
    ],
    "negative_themes": [
      {
        "theme": "Margin pressure concerns",
        "mentions": 1200,
        "impact": "High|Moderate|Low",
        "credibility": "High|Moderate|Low"
      }
    ],
    "dominant_narrative": "Positive - green energy transition"
  },
  "influencer_activity": {
    "notable_mentions": [
      {
        "influencer": "@MarketGuru (250K followers)",
        "sentiment": "Positive|Neutral|Negative",
        "reach": "High|Moderate|Low",
        "credibility": "High|Moderate|Low"
      }
    ],
    "influencer_consensus": "Bullish|Mixed|Bearish"
  },
  "retail_momentum": {
    "momentum_strength": "Strong|Moderate|Weak|None",
    "new_investor_interest": "High|Moderate|Low",
    "trading_app_popularity": "High|Moderate|Low",
    "search_trends": "Surging|Rising|Stable|Declining"
  },
  "risk_signals": {
    "early_warnings": [
      "Any detected warning signal or 'None detected'"
    ],
    "misinformation_detected": "Yes|No",
    "unusual_patterns": "Yes|No",
    "pump_dump_risk": "High|Moderate|Low|None",
    "overall_risk_level": "High|Moderate|Low"
  },
  "platform_insights": {
    "twitter_summary": "Brief summary of Twitter sentiment and trends",
    "reddit_summary": "Brief summary of Reddit discussions",
    "stocktwits_summary": "Brief summary of StockTwits momentum"
  },
  "strengths": [
    "Positive social signal with specific evidence"
  ],
  "concerns": [
    "Negative social signal or risk with specific evidence"
  ],
  "recommendation_impact": "Positive|Neutral|Negative",
  "key_metrics_summary": {
    "sentiment_score": 68,
    "buzz_level": "High",
    "total_mentions": 18045,
    "positive_ratio": 62
  }
}
```

## Critical Rules

1. **Source Credibility**: Weight verified accounts > anonymous accounts
2. **Volume + Sentiment**: High volume with negative sentiment is more concerning than low volume
3. **Narrative Quality**: Distinguish informed discussion from speculation/hype
4. **Trend Direction**: Recent trend matters more than absolute sentiment
5. **Cross-Platform Consistency**: Aligned sentiment across platforms is stronger signal
6. **Warning Signals**: Flag unusual patterns immediately
7. **JSON Only**: Pure JSON output, no markdown
8. **Quantification**: Use specific metrics, not vague descriptions

## Interpretation Guidelines

### Strong Bullish Signal
- Sentiment >70 across all platforms
- High engagement from credible sources
- Volume increasing with positive sentiment
- Multiple positive narratives trending

### Contrarian Warning
- Extreme bullish sentiment (>90) can signal euphoria/top
- Extreme bearish sentiment (<10) can signal capitulation/bottom
- Sudden sentiment reversals require investigation

### Quality Filter
- Disregard pure speculation without fundamentals
- Focus on informed discussions with reasoning
- Weight institutional/experienced investor sentiment higher

## Example Analysis Pattern

For sentiment metrics:
- ✅ GOOD: "Twitter sentiment at 68/100 with 62% positive tweets (9,672/15,600), up from 55/100 last week, indicating improving retail sentiment momentum"
- ❌ BAD: "Social sentiment is positive" (no quantification)

For trending narratives:
- ✅ GOOD: "Green hydrogen narrative dominated with 3,500 mentions (22% of total volume), driven by influencer @MarketGuru's tweet with 8,500 engagements and positive framing"
- ❌ BAD: "People are talking about green energy" (lacks specifics)
