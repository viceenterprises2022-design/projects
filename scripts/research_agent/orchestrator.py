from __future__ import annotations

import os
import json
import time
from typing import Optional

import httpx

from .schemas import (
    ResearchReport, ResearchRound, GapAnalysis, Claim,
    CollectorResult, Source, Domain,
)
from .topic_classifier import classify as classify_domain
from .data_collectors import COLLECTOR_MAP

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
KIMCHI_API_KEY = os.environ.get("KIMCHI_API_KEY", "")

GAP_ANALYSIS_PROMPT = """You are a research director analyzing what we know so far.

Given the research query and the sources collected so far, identify knowledge gaps.
For each gap, provide:
1. A specific question that remains unanswered
2. What context is missing
3. A targeted search query (2-8 words) that would fill this gap

Output as JSON array:
[
  {{
    "question": "What specific aspect is missing?",
    "context": "Why this matters and what we already know",
    "follow_up_query": "targeted search query"
  }}
]

Return max 3 gaps. If the research feels complete, return an empty array []."""

CLAIMS_EXTRACTION_PROMPT = """You are a research analyst extracting structured claims from source material.

Given the research query and collected sources, extract the most important factual claims.
Each claim should be:
1. A specific, falsifiable statement supported by the evidence
2. Assigned a confidence level (high/medium/low) based on source quality and consistency
3. Accompanied by supporting evidence quotes from the sources
4. Linked to source numbers from the references

Output as JSON array:
[{{
  "statement": "The claim itself",
  "confidence": "high|medium|low",
  "supporting_evidence": ["Quote or data point from sources"],
  "source_refs": [1, 3]
}}]

Return max 6 claims. Only include claims directly supported by the provided material."""


def _llm_call(prompt: str, system: str, max_tokens: int = 2048) -> str:
    if not KIMCHI_API_KEY:
        return ""
    payload = {
        "model": "anthropic/claude-3.5-haiku-20241022",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }
    for attempt in range(3):
        try:
            resp = httpx.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {KIMCHI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=120,
            )
            if resp.status_code == 429:
                time.sleep(2 ** (attempt + 2))
                continue
            if resp.status_code != 200:
                continue
            return resp.json()["choices"][0]["message"]["content"]
        except (httpx.TimeoutException, Exception):
            time.sleep(3)
    return ""


def _parse_json_array(text: str) -> list[dict]:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import re
        m = re.search(r'\[.*?\]', text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
    return []


def _format_sources_for_prompt(sources: list[Source]) -> str:
    blocks = []
    for i, s in enumerate(sources, 1):
        pts = "\n".join(f"  - {p}" for p in (s.key_points or [])[:3])
        block = (
            f"[{i}] {s.title}\n"
            f"URL: {s.url}\n"
            f"Excerpt: {(s.snippet or '')[:300]}\n"
            f"Key points:\n{pts}"
        )
        blocks.append(block)
    return "\n---\n".join(blocks)


def analyze_gaps(
    query: str, sources: list[Source]
) -> list[GapAnalysis]:
    if not KIMCHI_API_KEY or not sources:
        return []
    prompt = f"Research query: {query}\n\nSources collected ({len(sources)}):\n\n{_format_sources_for_prompt(sources)}\n\nIdentify gaps."
    raw = _llm_call(prompt, GAP_ANALYSIS_PROMPT, max_tokens=2048)
    if not raw:
        return []
    items = _parse_json_array(raw)
    return [
        GapAnalysis(
            question=i.get("question", ""),
            context=i.get("context", ""),
            follow_up_query=i.get("follow_up_query", ""),
        )
        for i in items[:3]
        if i.get("follow_up_query")
    ]


def extract_claims(
    query: str, sources: list[Source]
) -> list[Claim]:
    if not KIMCHI_API_KEY or not sources:
        return []
    prompt = f"Research query: {query}\n\nSources ({len(sources)}):\n\n{_format_sources_for_prompt(sources)}\n\nExtract claims."
    raw = _llm_call(prompt, CLAIMS_EXTRACTION_PROMPT, max_tokens=3072)
    if not raw:
        return []
    items = _parse_json_array(raw)
    return [
        Claim(
            statement=i.get("statement", ""),
            confidence=i.get("confidence", "medium"),
            supporting_evidence=i.get("supporting_evidence", []),
            source_refs=i.get("source_refs", []),
        )
        for i in items[:6]
        if i.get("statement")
    ]


def _collect_for_query(
    query: str, domain: Domain, timelimit: str = "y"
) -> CollectorResult | None:
    collector_cls = COLLECTOR_MAP.get(domain.value)
    if collector_cls is None:
        return None
    import asyncio
    collector = collector_cls()
    return asyncio.run(collector.collect(query, timelimit=timelimit))


class DeepResearchOrchestrator:
    def __init__(
        self,
        query: str,
        force_domain: Optional[str] = None,
        threshold: float = 0.20,
        max_rounds: int = 2,
        timelimit: str = "y",
    ):
        self.query = query
        self.force_domain = force_domain
        self.threshold = threshold
        self.max_rounds = max_rounds
        self.timelimit = timelimit
        self._all_sources: list[Source] = []
        self._collector_results: list[CollectorResult] = []

    def run(self) -> ResearchReport:
        classifier = classify_domain(
            self.query, threshold=self.threshold, force_domain=self.force_domain
        )

        report = ResearchReport(
            query=self.query,
            domains=classifier.domains,
            classifier_reasoning=classifier.reasoning,
        )

        for round_num in range(1, self.max_rounds + 1):
            depth = "shallow" if round_num == 1 else "deep"
            round_obj = ResearchRound(
                round_number=round_num,
                depth=depth,
            )

            queries_for_round: list[str] = [self.query]

            if round_num > 1 and self._all_sources:
                gaps = analyze_gaps(self.query, self._all_sources)
                round_obj.gaps_identified = gaps
                follow_ups = [
                    g.follow_up_query for g in gaps if g.follow_up_query
                ]
                if follow_ups:
                    queries_for_round.extend(follow_ups)

            round_obj.sub_queries = queries_for_round

            for sub_q in queries_for_round:
                for domain in classifier.domains:
                    result = _collect_for_query(sub_q, domain, self.timelimit)
                    if result is None:
                        continue
                    self._collector_results.append(result)
                    self._all_sources.extend(result.sources)

            round_obj.sources_found = len(self._all_sources)
            report.rounds.append(round_obj)

        report.collector_results = self._collector_results
        report.total_sources = len(self._all_sources)

        if self._all_sources:
            report.claims = extract_claims(self.query, self._all_sources)

        if self._all_sources and report.rounds:
            last_round = report.rounds[-1]
            if last_round.gaps_identified:
                unresolved = [
                    g.question for g in last_round.gaps_identified
                    if not g.resolved
                ]
                report.gaps_remaining = unresolved

        return report
