from __future__ import annotations

import re
from typing import Optional

from schemas import ClassifierResult, Domain

DOMAIN_SIGNALS: dict[Domain, dict] = {
    Domain.CRYPTO: {
        "keywords": [
            "bitcoin", "ethereum", "crypto", "blockchain", "btc", "eth",
            "solana", "defi", "nft", "altcoin", "token", "web3",
            "mining", "smart contract", "layer 2", "dex", "cex",
            "stablecoin", "hodl", "meme coin", "airdrop",
            "staking", "yield farming", "liquidity pool",
        ],
        "tickers": [r"\b(BTC|ETH|SOL|XRP|ADA|DOGE|DOT|LINK|AVAX|MATIC|NEAR)\b"],
        "weight": 0.30,
    },
    Domain.INDIA_STOCKS: {
        "keywords": [
            "nifty", "sensex", "nse", "bse", "india stock", "indian market",
            "f&o", "futures and options", "nse india", "bse india",
            "sebi", "derivatives", "mcap",
        ],
        "companies": [
            "reliance", "tcs", "hdfc", "infosys", "icici",
            "bharti", "itc", "kothak", "l&t", "wipro",
            "maruti", "tatamotors", "tatasteel", "sbin", "pnb",
            "axisbank", "kotakbank", "hindustan", "asianpaints",
            "bajaj", "dmart", "zomato", "nykaa", "paytm",
        ],
        "suffixes": [r"\b\w+\.NS\b", r"\b\w+\.BO\b"],
        "weight": 0.30,
    },
    Domain.US_STOCKS: {
        "keywords": [
            "nyse", "nasdaq", "s&p 500", "dow jones",
            "stock market", "wall street", "spy", "qqq",
            "etf", "dividend", "earnings report", "sec filing",
            "ipo", "buyback", "share buyback",
        ],
        "tickers": [r"\b(AAPL|TSLA|NVDA|MSFT|GOOGL|GOOG|AMZN|META|NFLX"
                     r"|JPM|V|WMT|JNJ|PG|MA|UNH|HD|DIS|ADBE|CRM"
                     r"|INTC|AMD|IBM|ORCL|CSCO|QCOM|TXN|AVGO"
                     r"|BA|CAT|GE|MMM|XOM|CVX|KO|PEP)\b"],
        "companies": [
            "nvidia", "apple", "microsoft", "tesla", "amazon",
            "meta", "google", "netflix", "berkshire", "jpmorgan",
            "visa", "walmart", "johnson & johnson", "procter",
            "mastercard", "unitedhealth", "home depot", "disney",
            "adobe", "salesforce", "intel", "amd", "ibm", "oracle",
            "cisco", "qualcomm", "broadcom", "boeing",
            "caterpillar", "general electric", "3m", "exxon",
            "chevron", "coca-cola", "pepsi", "costco",
        ],
        "weight": 0.30,
    },
    Domain.ACADEMIA: {
        "keywords": [
            "paper", "research", "study", "journal", "arxiv",
            "scholar", "doi", "academic", "thesis", "dissertation",
            "publication", "peer-reviewed", "preprint", "conference",
            "proceedings", "science", "scientific",
        ],
        "weight": 0.25,
    },
    Domain.WORLD_NEWS: {
        "keywords": [
            "news", "breaking", "update", "current events", "report",
            "happening", "latest",
            "geopolitical", "election", "summit", "treaty",
            "conflict", "sanctions", "policy", "regulation",
        ],
        "weight": 0.25,
    },
}


def _score_domain(query_lower: str, domain: Domain, signals: dict) -> float:
    score = 0.0

    for kw in signals.get("keywords", []):
        if kw in query_lower:
            score += signals["weight"]

    for pattern in signals.get("tickers", []):
        if re.search(pattern, query_lower, re.IGNORECASE):
            score += signals["weight"] * 1.0

    for company in signals.get("companies", []):
        if re.search(r"\b" + re.escape(company) + r"\b", query_lower):
            score += signals["weight"] * 0.8

    for pattern in signals.get("suffixes", []):
        if re.search(pattern, query_lower, re.IGNORECASE):
            score += signals["weight"] * 0.7

    return min(score, 1.0)


def _generate_reasoning(
    query: str, scores: dict[Domain, float], threshold: float
) -> str:
    matched = [(d, s) for d, s in scores.items() if s >= threshold]
    if not matched:
        return "No domain met the confidence threshold. Falling back to general research."
    matched.sort(key=lambda x: -x[1])
    parts = [f"{d.value}={s:.2f}" for d, s in matched]
    return f"Domains matched (threshold={threshold}): {', '.join(parts)}. Query: '{query}'"


def classify(
    query: str,
    threshold: float = 0.20,
    force_domain: Optional[str] = None,
) -> ClassifierResult:
    if force_domain:
        d = Domain(force_domain)
        return ClassifierResult(
            domains=[d],
            confidences={d: 1.0},
            raw_query=query,
            reasoning=f"Forced domain: {d.value}",
        )

    query_lower = query.lower()
    scores: dict[Domain, float] = {}

    for domain, signals in DOMAIN_SIGNALS.items():
        scores[domain] = _score_domain(query_lower, domain, signals)

    matched = [d for d, s in scores.items() if s >= threshold]

    if not matched:
        matched = [Domain.GENERAL]
        scores[Domain.GENERAL] = 1.0

    confidences = {d: scores.get(d, 0.0) for d in matched}
    reasoning = _generate_reasoning(query, scores, threshold)

    return ClassifierResult(
        domains=matched,
        confidences=confidences,
        raw_query=query,
        reasoning=reasoning,
    )
