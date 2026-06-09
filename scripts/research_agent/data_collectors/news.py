from __future__ import annotations
from ..schemas import Domain

from .base import BaseCollector, CollectorResult, run_belt_search


class NewsCollector(BaseCollector):
    domain = Domain.WORLD_NEWS

    async def collect(self, query: str) -> CollectorResult:
        results = run_belt_search(query, depth="advanced", max_results=8)
        if not results:
            return self._make_result(
                query=query,
                summary="No news results available.",
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

        headlines = [s["title"] for s in sources[:5]]
        summary = (
            f"Found {len(sources)} news sources. "
            f"Headlines: {' | '.join(headlines)}"
        )
        return self._make_result(query=query, summary=summary, sources=sources)
