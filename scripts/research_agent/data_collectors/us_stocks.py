from __future__ import annotations
from ..schemas import Domain

from .base import BaseCollector, CollectorResult, run_belt_search


class UsStocksCollector(BaseCollector):
    domain = Domain.US_STOCKS

    async def collect(self, query: str) -> CollectorResult:
        search_query = f"US stock market {query}"
        results = run_belt_search(search_query, depth="advanced", max_results=8)
        if not results:
            return self._make_result(
                query=query,
                summary="No US stock data available.",
                error="belt tavily-search returned no data",
            )

        sources = []
        for r in results:
            sources.append({
                "title": r.get("title", "Untitled"),
                "url": r.get("url", ""),
                "snippet": r.get("content", r.get("snippet", "")),
                "published": r.get("published_date"),
            })

        summary = (
            f"Found {len(sources)} sources on US stock markets. "
            f"Covers price action, fundamentals, and market news."
        )
        return self._make_result(query=query, summary=summary, sources=sources)
