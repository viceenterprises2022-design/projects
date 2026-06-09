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
        "--no-pdf",
        action="store_true",
        help="Skip PDF generation, output .md only",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Also emit raw data as JSON",
    )
    parser.add_argument(
        "--synthesis", "-s",
        help="Optional synthesis text (else OpenCode supplies it)",
        default=None,
    )
    return parser.parse_args(argv)


async def _run_collectors(
    query: str, domains: list, synthesis: Optional[str], threshold: float, force_domain: Optional[str]
) -> ResearchReport:
    classifier = classify_domain(query, threshold=threshold, force_domain=force_domain)

    report = ResearchReport(
        query=query,
        domains=classifier.domains,
        classifier_reasoning=classifier.reasoning,
        synthesis=synthesis or "",
    )

    tasks = []
    for domain in classifier.domains:
        domain_key = domain.value
        collector_cls = COLLECTOR_MAP.get(domain_key)
        if collector_cls is None:
            continue
        collector = collector_cls()
        tasks.append(collector.collect(query))

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                continue
            report.collector_results.append(r)

    total = 0
    for cr in report.collector_results:
        total += len(cr.sources)
    report.total_sources = total

    return report


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)

    out_dir = Path(args.output or (Path(__file__).parent / "outputs"))
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in args.query).strip("_ ")[:60]
    base_name = f"research_{slug}_{timestamp}"

    report = asyncio.run(
        _run_collectors(
            query=args.query,
            domains=[],
            synthesis=args.synthesis,
            threshold=args.threshold,
            force_domain=args.domain,
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

    if args.synthesis is None:
        print("\n  ⚠️  No synthesis provided. OpenCode should call this tool, read")
        print("     the collector results, synthesize, and re-run with --synthesis.")
    else:
        print(f"\n  ✅ Report complete — {len(report.collector_results)} collector(s), "
              f"{report.total_sources} source(s).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
