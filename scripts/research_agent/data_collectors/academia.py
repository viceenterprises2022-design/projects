from __future__ import annotations
from ..schemas import Domain

from .base import BaseCollector, CollectorResult, run_belt_search


class AcademiaCollector(BaseCollector):
    domain = Domain.ACADEMIA

    async def collect(self, query: str) -> CollectorResult:
        academic_query = f"{query} (arxiv OR scholar OR research OR journal OR doi)"
        results = run_belt_search(academic_query, depth="advanced", max_results=8)
        if not results:
            return self._make_result(
                query=query,
                summary="No academic search results available.",
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
            f"Found {len(sources)} academic sources. "
            f"Results span papers, journals, and scholarly articles."
        )
        return self._make_result(query=query, summary=summary, sources=sources)
