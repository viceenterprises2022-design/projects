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


def _extract_numbers(text: str) -> list[str]:
    found = re.findall(r'(?:\$)?\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:%\s*(?:of|per|\w+)?|x\b)?|\$[\d,.]+[kKmMbB]?', text)
    return [f.strip() for f in found[:10]]


def _extract_entities(text: str) -> list[str]:
    entities = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b', text)
    filtered = [e for e in entities if len(e) > 3 and e not in {"This", "That", "These", "What", "When", "Where", "How", "From", "They", "Will", "Have", "With", "Their", "About", "Which", "Would", "Could", "Should"}]
    return [e for e in filtered if Counter(filtered)[e] >= 2][:20]


_section_map = {
    "Monetary Policy / Rates": "monetary",
    "Market Impact": "market",
    "Inflation / Macros": "inflation",
    "Correlation / Analysis": "correlation",
    "Investor Strategy": "strategy",
    "Regulation / Policy": "regulation",
    "Technology / Fundamentals": "tech",
    "General": "general",
}


def _top_n_entities(source_group: list[Source], n: int = 5) -> list[str]:
    entities: list[str] = []
    for src in source_group:
        content = (src.full_content or src.snippet or src.title)
        entities.extend(_extract_entities(content))
        for kp in src.key_points:
            entities.extend(_extract_entities(kp))
    if not entities:
        return []
    counts: dict[str, int] = {}
    for e in entities:
        counts[e] = counts.get(e, 0) + 1
    sorted_ents = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    return [e for e, c in sorted_ents[:n]]


def _theme_based_analysis(source_group: list[Source]) -> str:
    key_points: list[str] = []
    for src in source_group:
        key_points.extend(src.key_points)
    if not key_points:
        return ""

    by_entity: dict[str, list[str]] = defaultdict(list)
    for kp in key_points:
        entities = _extract_entities(kp)
        for e in entities[:2]:
            by_entity[e].append(kp)

    parts: list[str] = []
    top_entities = sorted(by_entity.items(), key=lambda x: -len(x[1]))[:4]
    for entity, kps in top_entities:
        if parts:
            entity_label = entity
        else:
            entity_label = entity
        for kp in kps[:2]:
            parts.append(kp)

    if not parts:
        return ""

    seen = set()
    unique: list[str] = []
    for p in parts:
        key = p[:60].lower()
        if key not in seen:
            seen.add(key)
            unique.append(p)

    return " ".join(unique[:3])


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

    domain_numbers: dict[str, int] = {}
    source_number = 1
    for cr in report.collector_results:
        domain_key = cr.domain.value
        domain_numbers[domain_key] = source_number
        source_number += len(cr.sources)

    for cr in report.collector_results:
        if not cr.theme_groups:
            continue
        lines.append(f"### {_domain_badge(cr.domain)}")

        theme_texts: list[str] = []
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
