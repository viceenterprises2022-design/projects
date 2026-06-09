from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class Domain(str, Enum):
    GENERAL = "general"
    ACADEMIA = "academia"
    WORLD_NEWS = "world_news"
    INDIA_STOCKS = "india_stocks"
    US_STOCKS = "us_stocks"
    CRYPTO = "crypto"


DOMAIN_LABELS = {
    Domain.GENERAL: "General Research",
    Domain.ACADEMIA: "Academic Research",
    Domain.WORLD_NEWS: "World News",
    Domain.INDIA_STOCKS: "Indian Stock Markets",
    Domain.US_STOCKS: "US Stock Markets",
    Domain.CRYPTO: "Cryptocurrency",
}


@dataclass
class ClassifierResult:
    domains: list[Domain]
    confidences: dict[Domain, float]
    raw_query: str
    reasoning: str = ""

    def primary(self) -> Domain | None:
        if not self.domains:
            return None
        return max(self.domains, key=lambda d: self.confidences.get(d, 0))


@dataclass
class Source:
    title: str
    url: str
    snippet: str = ""
    published: Optional[str] = None
    full_content: str = ""
    key_points: list[str] = field(default_factory=list)
    theme: str = ""


@dataclass
class DataPoint:
    label: str
    value: str
    unit: str = ""


@dataclass
class ThemeGroup:
    name: str
    sources: list[Source] = field(default_factory=list)
    insight: str = ""


@dataclass
class CollectorResult:
    domain: Domain
    query: str
    summary: str
    sources: list[Source] = field(default_factory=list)
    data_points: list[DataPoint] = field(default_factory=list)
    raw_data: dict = field(default_factory=dict)
    error: Optional[str] = None
    collected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    theme_groups: list[ThemeGroup] = field(default_factory=list)
    top_insights: list[str] = field(default_factory=list)


@dataclass
class ResearchReport:
    query: str
    domains: list[Domain]
    classifier_reasoning: str = ""
    collector_results: list[CollectorResult] = field(default_factory=list)
    synthesis: str = ""
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    total_sources: int = 0
    output_path_md: Optional[str] = None
    output_path_pdf: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
