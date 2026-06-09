from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Optional

from .schemas import DOMAIN_LABELS, Domain, ResearchReport, Source, ThemeGroup


def _domain_badge(domain: Domain) -> str:
    badges = {
        Domain.GENERAL: "General",
        Domain.ACADEMIA: "Academia",
        Domain.WORLD_NEWS: "World News",
        Domain.INDIA_STOCKS: "India Stocks",
        Domain.US_STOCKS: "US Stocks",
        Domain.CRYPTO: "Crypto",
    }
    return badges.get(domain, domain.value)


def _format_timestamp(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, TypeError):
        return ts


_SECTION_ORDER = [
    "Monetary Policy / Rates",
    "Market Impact",
    "Inflation / Macros",
    "Correlation / Analysis",
    "Investor Strategy",
    "Regulation / Policy",
    "Technology / Fundamentals",
    "General",
]


def _extract_numbers(text: str) -> list[str]:
    found = re.findall(r'(?:\$)?\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:%\s*(?:of|per|\w+)?|x\b)?|\$[\d,.]+[kKmMbB]?', text)
    return [f.strip() for f in found[:10]]


_STOP_ENTITIES = frozenset({
    "This", "That", "These", "What", "When", "Where", "How", "From", "They",
    "Will", "Have", "With", "Their", "About", "Which", "Would", "Could",
    "Should", "There", "Here", "Than", "Then", "Been", "Very", "Just",
    "Also", "More", "Some", "Such", "Each", "Both", "Over", "Into",
    "While", "Since", "After", "Before", "Still", "Already", "Even",
    "Rather", "Many", "Much", "Most", "Few", "Only", "Other", "Another",
    "First", "Second", "Third", "Next", "Last", "Previous", "Final",
    "Overall", "Indeed", "However", "Therefore", "Moreover", "Furthermore",
    "Additionally", "Consequently", "Meanwhile", "Nevertheless",
})


def _extract_entities(text: str) -> list[str]:
    entities = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b', text)
    return [e for e in entities if len(e) > 3 and e not in _STOP_ENTITIES]


def _extract_topics(key_points: list[str]) -> list[tuple[str, list[str], float]]:
    topic_keywords = {
        "price action": ["price", "bitcoin", "btc", "trading", "rally", "decline", "drop", "surge", "slid", "fell", "rose", "level", "resistance", "support"],
        "inflation & rates": ["inflation", "fed", "federal reserve", "interest rate", "cpi", "treasury", "yield", "monetary"],
        "institutional": ["etf", "institutional", "blackrock", "fidelity", "grayscale", "strategy", "michael saylor", "microstrategy"],
        "market structure": ["liquidity", "volatility", "correlation", "breakout", "corridor", "range", "consolidation"],
        "regulation": ["regulation", "sec", "regulatory", "policy", "compliance", "legal"],
        "adoption": ["adoption", "mainstream", "integration", "payment", "defi", "lightning"],
    }
    topics: list[tuple[str, list[str], float]] = []
    for topic_name, keywords in topic_keywords.items():
        matches: list[str] = []
        score = 0
        for kp in key_points:
            kp_lower = kp.lower()
            match_count = sum(1 for kw in keywords if kw in kp_lower)
            if match_count > 0:
                matches.append(kp)
                score += match_count
        if matches:
            avg_score = score / len(matches)
            topics.append((topic_name, matches, avg_score))
    topics.sort(key=lambda x: (-len(x[1]), -x[2]))
    return topics


def _resolve_numbers(key_points: list[str]) -> dict[str, set[str]]:
    numbers: dict[str, set[str]] = defaultdict(set)
    import re
    for kp in key_points:
        nums = re.findall(r'\$[\d,]+[kKmMbB]?[-–—to]*[\d,]*[kKmMbB]?|\d+\.?\d*\s*%|'
                          r'\$[\d,]+(?:\.\d+)?|\d{1,3}(?:,\d{3})*(?:\.\d+)?', kp)
        for n in nums:
            numbers["data points"].add(n.strip())
    return numbers


def _theme_based_analysis(source_group: list[Source]) -> str:
    all_kp: list[str] = []
    for src in source_group:
        all_kp.extend(src.key_points)
    if not all_kp:
        return ""

    topics = _extract_topics(all_kp)
    if not topics:
        return ""

    parts: list[str] = []
    for topic_name, kps, _ in topics[:3]:
        seen = set()
        unique_kps: list[str] = []
        for kp in kps:
            key = kp[:100].lower()
            if key not in seen:
                seen.add(key)
                unique_kps.append(kp)
        if unique_kps:
            parts.append(f"**{topic_name.title()}** — {len(unique_kps)} data point(s)")
            for kp in unique_kps[:2]:
                parts.append(f"- {kp}")

    return "\n".join(parts) if parts else ""


def _findings_summary(all_keys: list[str]) -> list[str]:
    topics = _extract_topics(all_keys)
    if not topics:
        return []
    lines: list[str] = []
    lines.append("**Top Findings:**")
    for topic_name, kps, _ in topics[:3]:
        if kps:
            lines.append(f"- **{topic_name.title()}**: {kps[0][:200]}")
    return lines


def _render_analysis(report: ResearchReport) -> list[str]:
    lines: list[str] = []
    all_keys: list[str] = []

    for cr in report.collector_results:
        for src in cr.sources:
            all_keys.extend(src.key_points)

    if not all_keys:
        return lines

    lines.append("## Analysis")
    lines.append("")
    lines.append(f"Based on {report.total_sources} sources covering {len(all_keys)} extracted data points.")
    lines.append("")

    summary = _findings_summary(all_keys)
    if summary:
        lines.extend(summary)
        lines.append("")

    for cr in report.collector_results:
        if not cr.theme_groups:
            continue
        lines.append(f"### {_domain_badge(cr.domain)}")

        all_srcs: list[Source] = []

        for tg in cr.theme_groups:
            all_srcs.extend(tg.sources)

        source_map = {}
        for i, src in enumerate(all_srcs, 1):
            source_map[src.url] = i

        for tg in cr.theme_groups:
            analysis = _theme_based_analysis(tg.sources)
            if not analysis:
                continue
            lines.append("")
            lines.append(f"**{tg.name}**")
            lines.append("")
            lines.append(analysis)
            refs = [f"[{source_map[s.url]}]" for s in tg.sources if s.url in source_map]
            if refs:
                lines.append("")
                lines.append(f"*Sources: {', '.join(refs)}*")
            lines.append("")

        if cr.top_insights:
            lines.append("**Notable data points:**")
            lines.append("")
            for ins in cr.top_insights:
                lines.append(f"- {ins}")
            lines.append("")

    return lines


def _extract_numbers_from_sources(sources: list[Source]) -> list[str]:
    numbers: list[str] = []
    for src in sources:
        text = (src.full_content or src.snippet or src.title)
        numbers.extend(_extract_numbers(text))
    return numbers


def _render_synthesis(synthesis: str) -> list[str]:
    if not synthesis:
        return []
    lines: list[str] = []
    lines.append("## Analysis")
    lines.append("")
    for line in synthesis.split("\n"):
        lines.append(line)
    lines.append("")
    return lines


def _render_references(all_sources: list[Source]) -> list[str]:
    if not all_sources:
        return []
    lines: list[str] = []
    lines.append("## References")
    lines.append("")
    for i, src in enumerate(all_sources, 1):
        title = src.title or "Untitled"
        published = f" ({src.published})" if src.published else ""
        lines.append(f"{i}. [{title}]({src.url}){published}")
    lines.append("")
    return lines


def build_markdown(report: ResearchReport) -> str:
    lines: list[str] = []
    lines.append(f"# Research Report: {report.query}")
    lines.append("")
    lines.append(
        f"> **Generated:** {_format_timestamp(report.generated_at)}  "
        f"| **Domains:** {', '.join(_domain_badge(d) for d in report.domains)}  "
        f"| **Sources:** {report.total_sources}"
    )
    lines.append("")

    if report.classifier_reasoning:
        lines.append("## Auto-Routing")
        lines.append("")
        lines.append(f"{report.classifier_reasoning}")
        lines.append("")

    all_sources: list[Source] = []
    for cr in report.collector_results:
        all_sources.extend(cr.sources)

    if report.synthesis:
        lines.extend(_render_synthesis(report.synthesis))
    else:
        analysis_lines = _render_analysis(report)
        if analysis_lines:
            lines.extend(analysis_lines)
        else:
            for cr in report.collector_results:
                lines.append(f"### {_domain_badge(cr.domain)}")
                lines.append("")
                lines.append(cr.summary)
                lines.append("")
                if cr.theme_groups:
                    for tg in cr.theme_groups:
                        cnt = len(tg.sources)
                        lines.append(f"**{tg.name}** — {cnt} source(s)")
                        for src in tg.sources:
                            lines.append(f"- [{src.title}]({src.url})")
                            if src.key_points:
                                kp = src.key_points[0].strip()[:250]
                                lines.append(f"  > {kp}")
                            if src.published:
                                lines.append(f"  *({src.published})*")
                        lines.append("")

    if all_sources:
        lines.append("---")
        lines.append("")
        lines.extend(_render_references(all_sources))

    lines.append("---")
    lines.append("")
    lines.append(
        f"*Report generated by research-agent at {_format_timestamp(report.generated_at)}. "
        f"Always verify critical data points from primary sources.*"
    )
    lines.append("")

    return "\n".join(lines)
