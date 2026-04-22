from __future__ import annotations

import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from daily_market_report.models.snapshot import AssetSnapshot, DailyReport, NewsItem
from daily_market_report.report.sparkline import sparkline_png_base64


def extract_json_block(text: str) -> str:
    t = (text or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z0-9]*\s*", "", t)
        t = re.sub(r"\s*```$", "", t).strip()
    return t.strip()


def _enrich_assets_for_template(assets: list[AssetSnapshot]) -> list[dict]:
    rows = []
    for a in assets:
        d = a.model_dump(mode="json")
        d["sparkline_b64"] = sparkline_png_base64(a.technicals.sparkline_series)
        rows.append(d)
    return rows


def render_html(report: DailyReport) -> str:
    root = Path(__file__).resolve().parent
    env = Environment(
        loader=FileSystemLoader(str(root)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    tpl = env.get_template("template.html")
    ctx = report.model_dump_for_template()
    ctx["assets_enriched"] = _enrich_assets_for_template(report.assets)
    return tpl.render(**ctx)


def apply_crew_top_news(report: DailyReport, narrative_json: str) -> None:
    """Merge crew JSON output into snapshots (top_news + session_narrative)."""
    import json

    try:
        data = json.loads(extract_json_block(narrative_json))
    except json.JSONDecodeError:
        for a in report.assets:
            a.narrative_error = "crew_output_not_json"
        return
    if isinstance(data, dict) and "assets" in data:
        data = data["assets"]
    if not isinstance(data, list):
        return
    by_id = {a.asset_id: a for a in report.assets}
    for row in data:
        aid = row.get("asset_id")
        if not aid or aid not in by_id:
            continue
        snap = by_id[aid]
        snap.session_narrative = (row.get("session_narrative") or "").strip()
        top = []
        for n in row.get("top_news") or []:
            top.append(
                NewsItem(
                    source=str(n.get("source", "")),
                    title=str(n.get("title", "")),
                    link=str(n.get("link", "")),
                    published_ist=str(n.get("published_ist", "")),
                    summary_plain=str(n.get("summary_plain", "")),
                    why_it_matters=str(n.get("why_it_matters", "")),
                )
            )
        snap.top_news = top[:5]
