from __future__ import annotations

import json
import subprocess
import sys
from abc import ABC, abstractmethod
from typing import Any, Optional

from ..schemas import CollectorResult, Domain


def run_belt(app: str, payload: dict, timeout: int = 30) -> dict | None:
    try:
        cmd = [
            "belt", "app", "run", app,
            "--input", json.dumps(payload),
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


def run_belt_search(
    query: str, depth: str = "advanced", max_results: int = 5
) -> list[dict]:
    depth_param = "advanced" if depth == "advanced" else "basic"
    data = run_belt("tavily/search-assistant", {
        "query": query,
        "search_depth": depth_param,
        "max_results": max_results,
        "include_answer": True,
        "include_images": False,
        "topic": "general",
    })
    if data and "results" in data:
        return data["results"]

    return _run_ddg_search(query, max_results)


def _run_ddg_search(query: str, max_results: int = 5) -> list[dict]:
    try:
        from ddgs import DDGS
        results = list(DDGS(proxy=None).text(query, max_results=max_results))
        return [
            {
                "title": r.get("title", "Untitled"),
                "url": r.get("href", ""),
                "content": r.get("body", ""),
                "snippet": r.get("body", ""),
            }
            for r in results
        ]
    except Exception:
        return []


def extract_url_content(url: str, timeout: int = 15) -> str:
    try:
        import httpx
        from bs4 import BeautifulSoup
        resp = httpx.get(url, timeout=timeout, follow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [l for l in text.splitlines() if len(l.strip()) > 40]
        return "\n".join(lines[:80])
    except Exception:
        return ""


def extract_key_points(text: str, max_points: int = 3) -> list[str]:
    if not text or len(text) < 100:
        return []
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)
    candidates = [s.strip() for s in sentences if 40 < len(s.strip()) < 300]
    return candidates[:max_points]


THEME_KEYWORDS: dict[str, list[str]] = {
    "Monetary Policy / Rates": ["rate cut", "interest rate", "fed", "federal reserve", "fomc", "monetary policy"],
    "Market Impact": ["price", "market", "volatility", "rally", "decline", "correction", "bull", "bear"],
    "Inflation / Macros": ["inflation", "cpi", "gdp", "economic", "recession", "growth", "liquidity"],
    "Correlation / Analysis": ["correlation", "relationship", "impact on", "influence", "connected", "nexus"],
    "Investor Strategy": ["strategy", "investor", "position", "allocation", "portfolio", "hedge"],
    "Regulation / Policy": ["regulation", "sec", "compliance", "policy", "legal", "law"],
    "Technology / Fundamentals": ["blockchain", "network", "technology", "protocol", "layer", "scaling"],
}


def classify_theme(title: str, snippet: str, content: str = "") -> str:
    text = (title + " " + snippet + " " + content).lower()
    best_score = 0
    best_theme = "General"
    for theme, keywords in THEME_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_score = score
            best_theme = theme
    return best_theme


def enrich_sources(raw_results: list[dict]) -> list[dict]:
    import concurrent.futures
    urls = [r.get("url", r.get("href", "")) for r in raw_results]
    contents = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        fut = {ex.submit(extract_url_content, u): u for u in urls if u}
        for f in concurrent.futures.as_completed(fut, timeout=30):
            contents[fut[f]] = f.result()
    enriched = []
    for r in raw_results:
        url = r.get("url", r.get("href", ""))
        content = contents.get(url, "")
        key_pts = extract_key_points(content)
        snippet = r.get("snippet", r.get("body", ""))
        title = r.get("title", "Untitled")
        theme = classify_theme(title, snippet, content)
        enriched.append({
            "title": title,
            "url": url,
            "snippet": snippet[:250],
            "published": r.get("published", r.get("date", "")),
            "full_content": content[:3000],
            "key_points": key_pts,
            "theme": theme,
        })
    return enriched


def group_themes(sources: list) -> list:
    from ..schemas import ThemeGroup
    groups: dict[str, list] = {}
    for src in sources:
        t = src.theme or "General"
        groups.setdefault(t, []).append(src)
    return [ThemeGroup(name=t, sources=s) for t, s in groups.items()]


class BaseCollector(ABC):
    domain: Domain

    @abstractmethod
    async def collect(self, query: str) -> CollectorResult:
        ...

    def _make_result(
        self,
        query: str,
        summary: str,
        sources: Optional[list] = None,
        data_points: Optional[list] = None,
        raw_data: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> CollectorResult:
        from ..schemas import Source, DataPoint
        raw = sources or []
        enriched = enrich_sources([s if isinstance(s, dict) else {"title": s.title, "url": s.url, "snippet": s.snippet, "published": s.published} for s in raw])
        source_objs = [Source(**e) for e in enriched]
        theme_groups = group_themes(source_objs)
        top_insights = _build_insights(source_objs)
        return CollectorResult(
            domain=self.domain,
            query=query,
            summary=summary,
            sources=source_objs,
            data_points=[DataPoint(**d) if isinstance(d, dict) else d for d in (data_points or [])],
            raw_data=raw_data or {},
            error=error,
            theme_groups=theme_groups,
            top_insights=top_insights,
        )


def _build_insights(sources: list, max_insights: int = 3) -> list[str]:
    insights = []
    seen = set()
    for src in sources:
        for kp in src.key_points:
            key = kp[:60]
            if key not in seen:
                seen.add(key)
                insights.append(kp)
    return insights[:max_insights]
