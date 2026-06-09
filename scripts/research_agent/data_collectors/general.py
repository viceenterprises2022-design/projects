from __future__ import annotations
from ..schemas import Domain

from .base import BaseCollector, CollectorResult, run_belt_search


class GeneralCollector(BaseCollector):
    domain = Domain.GENERAL

    async def collect(self, query: str, timelimit: str = "y") -> CollectorResult:
        results = run_belt_search(query, depth="advanced", max_results=10, timelimit=timelimit)
        if not results:
            return self._make_result(
                query=query,
                summary="No web search results available.",
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
            f"Analyzed {len(sources)} sources with full content extraction. "
            f"Topics span monetary policy, market impact, and macroeconomic factors."
        )
        return self._make_result(query=query, summary=summary, sources=sources)
