#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

from crewai.flow import Flow, listen, start

from daily_market_report.config_loader import load_asset_configs, project_root
from daily_market_report.crews.content_crew.content_crew import MarketReportCrew, MarketReportCrewLite
from daily_market_report.models.snapshot import DailyReport
from daily_market_report.report.export import write_pdf, write_png
from daily_market_report.report.render import apply_crew_top_news, extract_json_block, render_html
from daily_market_report.tools.market_data import collect_all_assets, evidence_packet
from daily_market_report.tools.news_rss import attach_news


class ReportFlowState(BaseModel):
    asset_filter: list[str] | None = None
    mode: str = "heavy"
    out_dir: Path = Path("output")
    max_parallel_assets: int = 4
    cross_check_enabled: bool = True
    cache_ttl_seconds: int = 900
    report: DailyReport | None = None
    html: str = ""
    crew_raw: str = ""


class MarketReportFlow(Flow[ReportFlowState]):
    @start()
    def bootstrap(self, crewai_trigger_payload: dict | None = None):
        load_dotenv()
        if crewai_trigger_payload:
            self.state.mode = str(crewai_trigger_payload.get("mode", self.state.mode))
            if "out_dir" in crewai_trigger_payload:
                self.state.out_dir = Path(crewai_trigger_payload["out_dir"])
            if "assets" in crewai_trigger_payload:
                self.state.asset_filter = crewai_trigger_payload["assets"]
            if "max_parallel_assets" in crewai_trigger_payload:
                self.state.max_parallel_assets = int(crewai_trigger_payload["max_parallel_assets"])
            if "cross_check_enabled" in crewai_trigger_payload:
                self.state.cross_check_enabled = bool(crewai_trigger_payload["cross_check_enabled"])
        root = project_root()
        cache_dir = root / ".cache" / "market_data"
        configs, meta = load_asset_configs()
        if crewai_trigger_payload is None or "cross_check_enabled" not in crewai_trigger_payload:
            self.state.cross_check_enabled = bool(meta.get("cross_check_enabled", True))
        self.state.cache_ttl_seconds = int(meta.get("cache_ttl_seconds", self.state.cache_ttl_seconds))
        assets = configs
        if self.state.asset_filter:
            want = {x.strip().lower() for x in self.state.asset_filter}
            assets = [a for a in configs if a.id.lower() in want]

        snaps = collect_all_assets(
            assets,
            cache_dir=cache_dir,
            cache_ttl=self.state.cache_ttl_seconds,
            cross_check_enabled=self.state.cross_check_enabled,
            max_workers=self.state.max_parallel_assets,
        )
        attach_news(assets, snaps)
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        rep = DailyReport(run_id=run_id, generated_at_utc=datetime.now(timezone.utc), assets=snaps)
        rep.evidence_json = evidence_packet(snaps)
        self.state.report = rep

    @listen(bootstrap)
    def run_llm_crew(self):
        rep = self.state.report
        assert rep is not None
        api_key = os.getenv("OPENAI_API_KEY")
        skip = os.getenv("SKIP_LLM", "").lower() in ("1", "true", "yes")
        if skip or not api_key:
            self.state.crew_raw = ""
            return
        inputs = {"evidence_json": rep.evidence_json}
        try:
            if self.state.mode == "heavy":
                result = MarketReportCrew().crew().kickoff(inputs=inputs)
            else:
                result = MarketReportCrewLite().crew().kickoff(inputs=inputs)
            self.state.crew_raw = result.raw or ""
        except Exception as ex:  # noqa: BLE001
            self.state.crew_raw = ""
            for a in rep.assets:
                a.narrative_error = f"crew_failed: {ex}"

    @listen(run_llm_crew)
    def merge_and_render(self):
        rep = self.state.report
        assert rep is not None
        if self.state.crew_raw:
            apply_crew_top_news(rep, self.state.crew_raw)
        for a in rep.assets:
            if not a.top_news:
                a.top_news = a.news_candidates[:5]
        rep.crew_narrative_json = extract_json_block(self.state.crew_raw) if self.state.crew_raw else ""
        self.state.html = render_html(rep)

    @listen(merge_and_render)
    def export_artifacts(self):
        rep = self.state.report
        assert rep is not None
        out = Path(self.state.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        stem = f"daily_market_{rep.run_id}"
        pdf_path = out / f"{stem}.pdf"
        png_path = out / f"{stem}.png"
        try:
            write_pdf(self.state.html, pdf_path)
        except Exception as ex:  # noqa: BLE001
            (out / f"{stem}.pdf.error.txt").write_text(str(ex), encoding="utf-8")
        try:
            write_png(self.state.html, png_path)
        except Exception as ex:  # noqa: BLE001
            (out / f"{stem}.png.error.txt").write_text(str(ex), encoding="utf-8")
        (out / f"{stem}.html").write_text(self.state.html, encoding="utf-8")
        print(f"Wrote {pdf_path} / {png_path} (and HTML)")


def kickoff():
    MarketReportFlow().kickoff()


def plot():
    MarketReportFlow().plot()


def run_with_trigger():
    import json
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Provide JSON trigger payload as argv")
    payload = json.loads(sys.argv[1])
    MarketReportFlow().kickoff({"crewai_trigger_payload": payload})


def _parse_args():
    p = argparse.ArgumentParser(description="Daily multi-asset market report (CrewAI Flow)")
    p.add_argument("--assets", default="all", help="Comma-separated asset ids or 'all'")
    p.add_argument("--mode", choices=["heavy", "moderate"], default="heavy")
    p.add_argument("--out", type=Path, default=Path("output"))
    p.add_argument("--max-parallel-assets", type=int, default=int(os.getenv("MAX_PARALLEL_ASSETS", "4")))
    p.add_argument("--no-cross-check", action="store_true", help="Disable Google fetch when Yahoo OK")
    return p.parse_args()


def cli():
    args = _parse_args()
    load_dotenv()
    af = None if args.assets.strip().lower() == "all" else [x.strip() for x in args.assets.split(",") if x.strip()]
    payload = {
        "mode": args.mode,
        "out_dir": str(args.out.resolve()),
        "max_parallel_assets": max(1, args.max_parallel_assets),
        "cross_check_enabled": not args.no_cross_check,
    }
    if af is not None:
        payload["assets"] = af
    MarketReportFlow().kickoff({"crewai_trigger_payload": payload})


if __name__ == "__main__":
    cli()
