from __future__ import annotations

import os
from .schemas import Source, ThemeGroup


_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
_MODEL = "gemini-2.0-flash"
_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{_MODEL}:generateContent?key={_API_KEY}"


def _build_prompt(query: str, theme_groups: list[ThemeGroup], sources: list[Source]) -> str:
    parts = [
        f"You are a senior research analyst. Synthesize the following research on:\n\n\"{query}\"\n",
        "---\n### SOURCES\n",
    ]

    for i, src in enumerate(sources, 1):
        title = src.title or "Untitled"
        url = src.url
        content = (src.full_content or src.snippet or "")[:3000]
        date = f" ({src.published})" if src.published else ""
        parts.append(f"[Source {i}] {title}{date}\nURL: {url}\n{content}\n")

    parts.append(
        "---\n"
        "Write a research report with EXACTLY these sections (use level-2 headings ##):\n\n"
        "## Executive Summary\n"
        "2-3 paragraph synthesis of the single most important story across sources. "
        "Lead with a strong claim supported by evidence. Include specific numbers, dates, and entities.\n\n"
        "## Thematic Analysis\n"
        "Break down into 2-4 sub-themes. For EACH sub-theme:\n"
        "- One analytical paragraph explaining the dynamics\n"
        "- Specific evidence: prices, percentages, dates, events\n"
        "- Cite sources as [1], [2] etc.\n\n"
        "## Key Data Points\n"
        "Numbered list of the most concrete, specific facts found: prices, ratios, dates, "
        "forecast numbers, regulatory actions. Include source citations.\n\n"
        "## Points of Contention\n"
        "Where do sources disagree or where is the outlook uncertain? "
        "Be specific about what's contested and why.\n\n"
        "## Bottom Line\n"
        "Actionable 1-paragraph conclusion. What should a reader take away? "
        "What's the highest-conviction call?\n\n"
        "CRITICAL RULES:\n"
        "- NEVER say \"sources suggest\" or \"according to reports\" — just state what the evidence shows\n"
        "- EVERY factual claim MUST cite a source number like [1] or [3]\n"
        "- Use specific numbers (prices, dates, percentages) not vague quantifiers\n"
        "- If content is insufficient for a section, say so honestly rather than filling with fluff\n"
        "- Write in confident, declarative voice — this is analysis, not a summary\n"
        "- Output ONLY the report sections, no preamble or postamble\n"
    )
    return "\n".join(parts)


def synthesize(query: str, theme_groups: list[ThemeGroup], sources: list[Source]) -> str:
    if not _API_KEY:
        return ""

    prompt = _build_prompt(query, theme_groups, sources)

    import httpx
    import time

    last_err = ""
    for attempt in range(3):
        try:
            resp = httpx.post(
                _URL,
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 4096,
                        "topP": 0.95,
                    },
                },
                timeout=120,
            )
            if resp.status_code == 429 and attempt < 2:
                wait = 5 * (attempt + 1)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                last_err = f"no candidates"
                continue
            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return text.strip()
        except Exception as e:
            last_err = str(e)
            if attempt < 2:
                time.sleep(3)
            continue

    return ""
