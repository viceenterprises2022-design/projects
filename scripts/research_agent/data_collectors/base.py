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
    query: str, depth: str = "advanced", max_results: int = 5, timelimit: str = "y"
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

    return _run_ddg_search(query, max_results, timelimit)


_CURRENT_YEAR = 2026
_MIN_YEAR = _CURRENT_YEAR - 1  # reject content older than last year


def _is_fresh(raw: dict) -> bool:
    published = raw.get("published") or raw.get("date", "")
    if published and isinstance(published, str):
        import re
        m = re.search(r'\b(20\d{2})\b', published)
        if m and int(m.group(1)) < _MIN_YEAR:
            return False
    return True


_TIMELIMIT_MAP = {"d": "d", "w": "w", "m": "m", "y": "y", "all": None}


def _run_ddg_search(query: str, max_results: int = 5, timelimit: str = "y") -> list[dict]:
    try:
        from ddgs import DDGS
        ddgs_limit = _TIMELIMIT_MAP.get(timelimit, "y")
        raw = list(DDGS(proxy=None).text(query, timelimit=ddgs_limit, max_results=max_results))
        results = []
        for r in raw:
            url = r.get("href", "")
            if not _is_fresh(r):
                continue
            results.append({
                "title": r.get("title", "Untitled"),
                "url": url,
                "content": r.get("body", ""),
                "snippet": r.get("body", ""),
            })
        if len(results) < max_results // 2 and timelimit != "all":
            fallback = list(DDGS(proxy=None).text(query, timelimit=None, max_results=max_results))
            seen_urls = {r["url"] for r in results}
            for r in fallback:
                url = r.get("href", "")
                if url in seen_urls:
                    continue
                if not _is_fresh(r):
                    continue
                results.append({
                    "title": r.get("title", "Untitled"),
                    "url": url,
                    "content": r.get("body", ""),
                    "snippet": r.get("body", ""),
                })
                seen_urls.add(url)
                if len(results) >= max_results:
                    break
        return results
    except Exception:
        return []


def extract_url_content(url: str, timeout: int = 15) -> str:
    try:
        import httpx

        resp = httpx.get(url, timeout=timeout, follow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        resp.raise_for_status()
        html = resp.text
        if not html or len(html) < 200:
            return ""
    except Exception:
        return ""

    if _content_is_stale(html):
        return ""

    try:
        import logging
        logging.getLogger("readability").setLevel(logging.ERROR)
        from readability import Document
        doc = Document(html)
        summary_html = doc.summary()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(summary_html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        if len(text) > 100:
            return _clean_extracted_text(text)
    except Exception:
        pass

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()
        candidates = (
            soup.find("article") or
            soup.find(class_=lambda c: c and any(x in c.lower() for x in ["content", "article", "post", "main", "entry"])) or
            soup.find("main") or
            soup.find("body")
        )
        if candidates:
            text = candidates.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)
        return _clean_extracted_text(text)
    except Exception:
        return ""


def _content_is_stale(text: str) -> bool:
    import re
    years = sorted(set(int(m) for m in re.findall(r'\b(20[0-9]{2})\b', text)))
    if not years:
        return False
    recent_years = [y for y in years if y >= _MIN_YEAR]
    if recent_years:
        return False
    latest = max(years)
    if latest < _MIN_YEAR:
        return True
    return False


def _clean_extracted_text(text: str) -> str:
    import re
    text = re.sub(r'\n{3,}', '\n\n', text)
    lines = text.splitlines()
    cleaned = []
    for l in lines:
        s = l.strip()
        if not s:
            continue
        if any(s.lower().startswith(x) for x in [
            "copyright", "all rights reserved", "privacy policy", "terms of service",
            "cookie", "subscribe", "follow us", "share this", "related:", "you might also",
            "advertisement", "click here", "read more", "sign up", "newsletter",
        ]):
            continue
        cleaned.append(s)
    return "\n".join(cleaned[:40])


def extract_key_points(text: str, max_points: int = 4) -> list[str]:
    if not text or len(text) < 100:
        return []
    import re
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(?<=\w)\s+-\s+(?=\w)', ' | ', text)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    candidates = []
    noise_patterns = re.compile(
        r'^(i\s+am|i\'?m\s+a|this\s+article|we\s+will|in\s+this|click|sign\s+up|'
        r'disclaimer|opinions?\s+expressed|always\s+consult|do\s+your\s+own|'
        r'this\s+is\s+not|investing\s+involves|past\s+performance|'
        r'(author|journalist|writer|reporter)\s+is\s+a|with\s+over\s+\d+\s+years?|'
        r'^\s*:|\w+\s+is\s+a\s+\w+\s+(journalist|writer|reporter)|'
        r'by\s+subscribing|readers\s+should|you\s+should\s+consult|'
        r'all\s+rights?\s+reserved|editor\'?s?\s+note|'
        r'for\s+more\s+information|get\s+started\s+today|'
        r'live\s+(and\s+)?exclusive|register\s+(now|today)|'
        r'^\w+\s+\d+\s*\||^\d+\s+(minutes?|hours?|days?)\s+ago)',
        re.IGNORECASE,
    )
    heading_pattern = re.compile(
        r'^(?:how\s+\w+|what\s+\w+|why\s+\w+|the\s+\w+\s+\w+|breaking:|'
        r'\w+\s+\w+\s+\w+:\s+|\w+\s+\w+\s+\w+\s+\w+:)',
        re.IGNORECASE,
    )
    old_price_pattern = re.compile(r'(?:below|under|at)\s+\$[0-5]\d{2}(?:,\d{3})?', re.IGNORECASE)
    old_year_pattern = re.compile(r'\b(201[0-9]|202[0-5])\b')
    structured_data = re.compile(
        r'^(?:liquidity\s+risk|volatility\s+risk|medium\s+risk|low\s+risk|high\s+risk|'
        r'\w+\s+risk:\s*|score:|algorithmic|technical\s+analysis|'
        r'investor\s+(?:psychology|sentiment)|behavioural\s+finance|'
        r'quantitative\s+analysis|scientific\s+methods|'
        r'insider\s+trades|seasonal\s+variations|intraday\s+trading|'
        r'period|vol\.bal\.|negative\s*\(|positive\s*\(|bullish|bearish|'
        r'overall\s+analysis|close:\s*\d)',
        re.IGNORECASE,
    )
    short_heading = re.compile(r'^[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,3}\s*$')

    for s in sentences:
        s = s.strip()
        if len(s) < 80 or len(s) > 500:
            continue
        if not s.endswith((".", "!", "?")):
            continue
        if noise_patterns.search(s):
            continue
        if heading_pattern.match(s):
            continue
        if short_heading.match(s):
            continue
        if s == s.upper() and len(s) < 120:
            continue
        if structured_data.search(s):
            continue
        if old_price_pattern.search(s):
            continue
        if old_year_pattern.search(s):
            continue
        if '|' in s:
            continue
        specificity = sum(1 for w in s.split() if w[0].isupper() or w.isdigit())
        if specificity < 2 and len(s) < 120:
            continue
        candidates.append(s)
    candidates.sort(key=lambda x: -sum(1 for w in x.split() if w[0].isupper() or w.isdigit()))
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


def _source_is_stale(title: str, url: str, snippet: str = "") -> bool:
    import re
    text = f"{title} {url} {snippet}"
    years = sorted(set(int(m) for m in re.findall(r'\b(20[0-9]{2})\b', text)))
    recent = [y for y in years if y >= _MIN_YEAR]
    if recent:
        return False
    if years and max(years) < _MIN_YEAR:
        return True
    return False


_TRACKING_DOMAINS = frozenset({
    "l.facebook.com", "out.reddit.com", "t.co", "tracking.", "click.",
    "redirect.", "go.redirectingat.com",
})


def _url_is_valid(url: str) -> bool:
    if not url or not url.startswith("http"):
        return False
    if "/clev?" in url or "startpage" in url.lower() or "event=" in url:
        return False
    domain = url.split("/")[2].lower() if "://" in url else ""
    if any(t in domain for t in _TRACKING_DOMAINS):
        return False
    return True


def enrich_sources(raw_results: list[dict]) -> list[dict]:
    import concurrent.futures
    filtered = []
    for r in raw_results:
        title = r.get("title", "Untitled")
        url = r.get("url", r.get("href", ""))
        snippet = r.get("snippet", r.get("body", r.get("content", "")))
        if not _url_is_valid(url):
            continue
        if _source_is_stale(title, url, snippet):
            continue
        filtered.append(r)
    raw_results = filtered
    if not raw_results:
        return []
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
            "full_content": content[:2500],
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
    async def collect(self, query: str, timelimit: str = "y") -> CollectorResult:
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


def _build_insights(sources: list, max_insights: int = 5) -> list[str]:
    candidates = []
    seen = set()
    for src in sources:
        for kp in src.key_points:
            key = kp[:80].lower().strip()
            if key in seen:
                continue
            seen.add(key)
            text = kp.strip()
            if not text.endswith((".", "!", "?")):
                continue
            specificity = sum(1 for w in text.split() if w[0].isupper() or w.isdigit())
            if specificity >= 2 or len(text) > 80:
                candidates.append((specificity, len(text), text))
    candidates.sort(key=lambda x: (-x[0], -x[1]))
    return [c[2][:300] for c in candidates[:max_insights]]
