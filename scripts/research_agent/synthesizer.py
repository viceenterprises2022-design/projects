import os
import json
import time
import httpx
from .schemas import CollectorResult, Source, ThemeGroup

KIMCHI_API_KEY = os.environ.get("KIMCHI_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """You are a senior research analyst. Your task is to synthesize multiple sources into a clear, analytical research report.

Given a set of sources grouped by theme, produce a synthesis that:

1. **Executive Summary** (2-3 sentences): The single most important takeaway across all sources.

2. **Thematic Analysis**: For each theme group, write 2-4 paragraphs that:
   - Identify the key narrative or development
   - Cross-reference claims across sources (e.g., "Both [1] and [3] note... while [2] counters that...")
   - Highlight points of agreement and disagreement
   - Extract specific data points, metrics, and quotes with source attribution

3. **Key Data Points** (bullet list): The most important numbers, dates, thresholds, percentages cited across sources.

4. **Points of Contention**: Where sources disagree or present different angles.

5. **Bottom Line** (1-2 sentences): What this means for the topic.

Rules:
- Cite sources as [N] where N is the source number from the references list.
- Be specific — use actual numbers, percentages, and quotes from the material.
- If sources contradict, say so explicitly.
- Keep analysis grounded in the provided material — do not add outside knowledge.
- Output in markdown."""


def synthesize(query: str, sources: list[Source], theme_groups: list[ThemeGroup]) -> str:
    if not KIMCHI_API_KEY:
        return ""
    if not sources:
        return ""
    all_sources = [s for s in sources if s.title and s.url]
    source_blocks = []
    theme_groups: dict[str, list[Source]] = {}
    for s in all_sources:
        t = s.theme or "General"
        theme_groups.setdefault(t, []).append(s)
    for i, s in enumerate(all_sources, 1):
        fp = s.key_points[:3] if s.key_points else []
        pts = "\n".join(f"  - {p}" for p in fp[:3])
        block = f"[{i}] {s.title}\nURL: {s.url}\nTheme: {s.theme or 'General'}\nExcerpt: {s.snippet or ''}\nKey points:\n{pts}"
        source_blocks.append(block)
    theme_summary = ""
    for t, srcs in theme_groups.items():
        theme_summary += f"\nTheme '{t}': {len(srcs)} sources\n"
    source_text = "\n---\n".join(source_blocks)
    prompt = f"""Research query: {query}

Collected sources ({len(all_sources)} total):

Themes identified:{theme_summary}

Sources:
{source_text}

Produce a synthesis following the analyst guidelines."""
    payload = {
        "model": "anthropic/claude-3.5-haiku-20241022",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
    }
    last_error = None
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
                retry_after = 2 ** (attempt + 2)
                time.sleep(retry_after)
                continue
            if resp.status_code != 200:
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                continue
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except httpx.TimeoutException:
            last_error = "Timeout"
            time.sleep(5)
        except Exception as e:
            last_error = str(e)
            time.sleep(3)
    return ""
