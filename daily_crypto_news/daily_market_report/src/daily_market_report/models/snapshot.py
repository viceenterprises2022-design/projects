from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    source: str
    title: str
    link: str
    published_ist: str = ""
    summary_plain: str = ""
    why_it_matters: str = ""


class QuotePayload(BaseModel):
    source: str  # yahoo | google_finance
    last: float | None = None
    currency: str | None = None
    change_pct: float | None = None
    change_abs: float | None = None
    open_: float | None = Field(None, alias="open")
    high: float | None = None
    low: float | None = None
    prev_close: float | None = None
    as_of_utc: datetime | None = None
    session_label: str = ""
    raw_error: str | None = None

    model_config = {"populate_by_name": True}


class PivotLevels(BaseModel):
    pivot: float | None = None
    s1: float | None = None
    s2: float | None = None
    r1: float | None = None
    r2: float | None = None
    above_pivot: bool | None = None
    unavailable_reason: str | None = None


class TechnicalSnapshot(BaseModel):
    levels: PivotLevels = Field(default_factory=PivotLevels)
    sparkline_series: list[float] = Field(default_factory=list)


class AssetConfig(BaseModel):
    id: str
    display_name: str
    yahoo_symbol: str
    google_finance_quote: str
    timezone: str = "UTC"
    news_keywords: list[str] = Field(default_factory=list)
    rss_feeds: list[dict[str, str]] = Field(default_factory=list)
    price_divergence_pct: float = 0.75


class AssetSnapshot(BaseModel):
    asset_id: str
    display_name: str
    quote: QuotePayload | None = None
    backup_quote: QuotePayload | None = None
    display_source: str = ""  # which source is shown for headline price
    quote_disagreement: bool = False
    cross_check_note: str | None = None
    data_sources: list[str] = Field(default_factory=list)
    technicals: TechnicalSnapshot = Field(default_factory=TechnicalSnapshot)
    news_candidates: list[NewsItem] = Field(default_factory=list)
    top_news: list[NewsItem] = Field(default_factory=list)
    session_narrative: str = ""
    narrative_error: str | None = None
    data_unavailable: bool = False


class DailyReport(BaseModel):
    run_id: str = ""
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.utcnow())
    disclaimer: str = (
        "Not investment advice. Prices are indicative and may be delayed. "
        "Verify on your broker. Data: Yahoo Finance (primary) and Google Finance (backup)."
    )
    assets: list[AssetSnapshot] = Field(default_factory=list)
    evidence_json: str = ""  # compact JSON for agents
    crew_narrative_json: str = ""

    def model_dump_for_template(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
