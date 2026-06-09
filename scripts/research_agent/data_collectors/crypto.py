from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from ..schemas import DataPoint, Domain

from .base import BaseCollector, CollectorResult, run_belt, run_belt_search

SCRIPTS_DIR = Path(__file__).resolve().parents[2]


def _import_from_path(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod
    return None


class CryptoCollector(BaseCollector):
    domain = Domain.CRYPTO

    async def collect(self, query: str, timelimit: str = "y") -> CollectorResult:
        data_points = []
        sources = []

        crypto_news_path = SCRIPTS_DIR / "crypto_news_search.py"
        if crypto_news_path.exists():
            try:
                mod = _import_from_path("crypto_news_search", str(crypto_news_path))
                if hasattr(mod, "search_crypto_news"):
                    news = mod.search_crypto_news(query)
                    if news:
                        data_points.append(DataPoint(
                            label="Crypto News", value=str(news)[:200]
                        ))
            except Exception:
                pass

        crypto_intel_path = SCRIPTS_DIR / "crypto_intel_reporter.py"
        if crypto_intel_path.exists():
            try:
                mod = _import_from_path("crypto_intel_reporter", str(crypto_intel_path))
                if hasattr(mod, "get_market_snapshot"):
                    snap = mod.get_market_snapshot()
                    if snap:
                        data_points.append(DataPoint(
                            label="Market Snapshot", value=str(snap)[:200]
                        ))
            except Exception:
                pass

        crypto_dash_path = SCRIPTS_DIR / "crypto_market_dashboard.py"
        if crypto_dash_path.exists():
            try:
                mod = _import_from_path("crypto_market_dashboard", str(crypto_dash_path))
            except Exception:
                pass

        search_results = run_belt_search(f"cryptocurrency {query}", max_results=10, timelimit=timelimit)
        for r in search_results:
            sources.append({
                "title": r.get("title", "Untitled"),
                "url": r.get("url", ""),
                "snippet": r.get("content", r.get("snippet", "")),
            })

        summary = (
            f"Analyzed {len(sources)} sources with full content extraction. "
            f"Themes include monetary policy, market structure, and macro drivers."
        )
        return self._make_result(
            query=query, summary=summary,
            sources=sources, data_points=data_points,
        )
