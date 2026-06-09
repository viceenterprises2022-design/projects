from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .schemas import ResearchReport
from .topic_classifier import classify as classify_domain
from .data_collectors import COLLECTOR_MAP
from .report_builder import build_markdown
from .pdf_converter import md_to_pdf
from .synthesizer import synthesize


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="research-agent — multi-domain research with auto-skill routing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m research_agent \"impact of Fed rate cuts on Bitcoin\"\n"
            "  python -m research_agent \"latest Nifty 50 analysis\" --domain india_stocks\n"
            "  python -m research_agent \"transformers in NLP\" --output ~/report\n"
        ),
    )
    parser.add_argument("query", help="Research query string")
    parser.add_argument(
        "--domain", "-d",
        help="Force a specific domain (skip auto-classification)",
        choices=["general", "academia", "world_news", "india_stocks", "us_stocks", "crypto"],
    )
    parser.add_argument(
        "--output", "-o",
        help="Output directory (default: ./outputs/)",
        default=None,
    )
    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=0.20,
        help="Classification confidence threshold (default: 0.20)",
    )
    parser.add_argument(
        "--max-age",
        type=str,
        default="1y",
        choices=["1d", "1w", "1m", "1y", "all"],
        help="Max age of results: 1d, 1w, 1m, 1y, all (default: 1y)",
    )
    parser.add_argument(
        "--no-pdf",
        action="store_true",
        help="Skip PDF generation, output .md only",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Also emit raw data as JSON",
    )
    return parser.parse_args(argv)


async def _run_collectors(
    query: str, domains: list, threshold: float, force_domain: Optional[str],
    timelimit: str = "y",
) -> ResearchReport:
    classifier = classify_domain(query, threshold=threshold, force_domain=force_domain)

    report = ResearchReport(
        query=query,
        domains=classifier.domains,
        classifier_reasoning=classifier.reasoning,
    )

    tasks = []
    for domain in classifier.domains:
        domain_key = domain.value
        collector_cls = COLLECTOR_MAP.get(domain_key)
        if collector_cls is None:
            continue
        collector = collector_cls()
        tasks.append(collector.collect(query, timelimit=timelimit))

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                continue
            report.collector_results.append(r)

    total = 0
    all_sources = []
    all_theme_groups = []
    for cr in report.collector_results:
        total += len(cr.sources)
        all_sources.extend(cr.sources)
        all_theme_groups.extend(cr.theme_groups or [])
    report.total_sources = total

    if all_sources and not report.synthesis:
        result = synthesize(query, all_sources, all_theme_groups)
        print(f"DEBUG synthesis result: len={len(result)}, preview={result[:100]!r}")
        report.synthesis = result

    return report


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)

    out_dir = Path(args.output or (Path(__file__).parent / "outputs"))
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in args.query).strip("_ ")[:60]
    base_name = f"research_{slug}_{timestamp}"

    max_age = args.max_age if hasattr(args, "max_age") else "1y"
    timelimit = {"1d": "d", "1w": "w", "1m": "m", "1y": "y", "all": "all"}.get(max_age, "y")
    report = asyncio.run(
        _run_collectors(
            query=args.query,
            domains=[],
            threshold=args.threshold,
            force_domain=args.domain,
            timelimit=timelimit,
        )
    )

    md_content = build_markdown(report)
    md_path = out_dir / f"{base_name}.md"
    md_path.write_text(md_content)
    report.output_path_md = str(md_path)
    print(f"  Markdown: {md_path}")

    if not args.no_pdf:
        try:
            pdf_path = md_to_pdf(str(md_path))
            if pdf_path:
                report.output_path_pdf = pdf_path
                print(f"  PDF:      {pdf_path}")
        except Exception as e:
            print(f"  PDF generation skipped: {e}", file=sys.stderr)

    if args.json:
        json_path = out_dir / f"{base_name}.json"
        report.to_json(str(json_path))
        print(f"  JSON:     {json_path}")

    print(f"\n  ✅ Report complete — {len(report.collector_results)} collector(s), "
          f"{report.total_sources} source(s).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
