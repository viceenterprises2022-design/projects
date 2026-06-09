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
    return []


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
        return CollectorResult(
            domain=self.domain,
            query=query,
            summary=summary,
            sources=[Source(**s) if isinstance(s, dict) else s for s in (sources or [])],
            data_points=[DataPoint(**d) if isinstance(d, dict) else d for d in (data_points or [])],
            raw_data=raw_data or {},
            error=error,
        )
