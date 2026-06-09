from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from ..schemas import DataPoint, Domain

from .base import BaseCollector, CollectorResult, run_belt_search

SCRIPTS_DIR = Path(__file__).resolve().parents[2]


def _import_from_path(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod
    return None


class IndiaStocksCollector(BaseCollector):
    domain = Domain.INDIA_STOCKS

    async def collect(self, query: str) -> CollectorResult:
        data_points = []
        sources = []

        market_engine_path = SCRIPTS_DIR / "market_engine.py"
        if market_engine_path.exists():
            try:
                mod = _import_from_path("market_engine", str(market_engine_path))
                if hasattr(mod, "get_market_summary"):
                    summary = mod.get_market_summary()
                    data_points.append(DataPoint(
                        label="Market Summary", value=str(summary)[:200]
                    ))
            except Exception:
                pass

        nifty_path = SCRIPTS_DIR / "patch_market.py"
        if nifty_path.exists():
            try:
                mod = _import_from_path("patch_market", str(nifty_path))
                if hasattr(mod, "nifty_data"):
                    nd = mod.nifty_data()
                    data_points.append(DataPoint(
                        label="Nifty", value=str(nd)[:200]
                    ))
            except Exception:
                pass

        search_results = run_belt_search(
            f"India stock market {query} NSE BSE", max_results=5
        )
        for r in search_results:
            sources.append({
                "title": r.get("title", "Untitled"),
                "url": r.get("url", ""),
                "snippet": r.get("content", r.get("snippet", "")),
            })

        summary = (
            f"Collected {len(data_points)} data points from local tools "
            f"and {len(sources)} web sources."
        )
        return self._make_result(
            query=query, summary=summary,
            sources=sources, data_points=data_points,
        )
