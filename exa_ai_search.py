#!/usr/bin/env python3
"""Exa AI search: find online events & classes from major AI companies."""

import os
from dotenv import load_dotenv
load_dotenv()
import json
from datetime import datetime, timezone
from typing import Optional
from exa_py import Exa
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

EXA_API_KEY = os.environ.get("EXA_API_KEY")

AI_COMPANIES = [
    "OpenAI",
    "Anthropic",
    "Google AI",
    "Meta AI",
    "DeepMind",
    "Mistral",
    "Cohere",
    "Hugging Face",
]

SEARCH_QUERIES = [
    "OpenAI upcoming online workshop webinar register 2025",
    "Anthropic upcoming online events AI course register 2025",
    "Google AI upcoming online workshop developer event register 2025",
    "Meta AI upcoming online learning events course register 2025",
    "DeepMind upcoming online lecture event register 2025",
    "upcoming AI online bootcamp webinar free course virtual register 2025",
    "Hugging Face upcoming online course event workshop register 2025",
    "upcoming large language model online training course event 2025",
]

# Domains known for quality AI events/courses
INCLUDE_DOMAINS = [
    "openai.com",
    "anthropic.com",
    "ai.google",
    "deepmind.com",
    "ai.meta.com",
    "huggingface.co",
    "deeplearning.ai",
    "coursera.org",
    "eventbrite.com",
    "lu.ma",
    "meetup.com",
]

ONLINE_KEYWORDS = [
    "online", "virtual", "webinar", "live stream", "livestream",
    "zoom", "remote", "hybrid", "free", "register", "join",
]

PAST_EVENT_KEYWORDS = [
    "event has finished", "event has ended", "already took place",
    "recording available", "watch the replay", "this event is over",
    "registration closed",
]


def is_online_event(title: str, highlights: list[str]) -> bool:
    """Heuristic: result looks like an online event or class."""
    text = (title + " " + " ".join(highlights or [])).lower()
    return any(kw in text for kw in ONLINE_KEYWORDS)


def is_future_event(result: dict) -> bool:
    """Drop results that are clearly past events."""
    highlights_text = " ".join(result.get("highlights", []) or []).lower()
    title_text = (result.get("title") or "").lower()
    combined = title_text + " " + highlights_text

    # Reject if past-event language detected
    if any(kw in combined for kw in PAST_EVENT_KEYWORDS):
        return False

    # Reject if published_date is more than 60 days old and no future date in highlights
    pub = result.get("published_date")
    if pub:
        try:
            pub_dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            age_days = (now - pub_dt).days
            # Allow up to 60 days old (event pages published recently may have future dates)
            if age_days > 60:
                return False
        except Exception:
            pass

    return True


def search_events(
    exa: Exa,
    query: str,
    num_results: int = 8,
    include_domains: Optional[list[str]] = None,
    start_published_date: Optional[str] = None,
) -> list[dict]:
    try:
        kwargs = dict(
            type="auto",
            num_results=num_results,
            contents={"highlights": True},
        )
        if include_domains:
            kwargs["include_domains"] = include_domains
        if start_published_date:
            kwargs["start_published_date"] = start_published_date

        resp = exa.search(query, **kwargs)
        results = []
        for r in resp.results:
            highlights = getattr(r, "highlights", []) or []
            results.append({
                "title": r.title or "(no title)",
                "url": r.url,
                "highlights": highlights,
                "score": getattr(r, "score", 0),
                "published_date": getattr(r, "published_date", None),
                "is_online": is_online_event(r.title or "", highlights),
            })
        return results
    except Exception as e:
        console.print(f"[red]Search failed for '{query}': {e}[/red]")
        return []


def deduplicate(results: list[dict]) -> list[dict]:
    seen_urls = set()
    out = []
    for r in results:
        if r["url"] not in seen_urls:
            seen_urls.add(r["url"])
            out.append(r)
    return out


def print_results(results: list[dict], online_only: bool = True) -> None:
    if online_only:
        results = [r for r in results if r["is_online"]]

    if not results:
        console.print("[yellow]No online events/classes found.[/yellow]")
        return

    table = Table(
        title=f"AI Online Events & Classes ({len(results)} results)",
        box=box.ROUNDED,
        show_lines=True,
        expand=True,
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Title", style="bold cyan", max_width=45)
    table.add_column("URL", style="blue", max_width=40)
    table.add_column("Highlights", style="white", max_width=60)
    table.add_column("Date", style="green", width=12)

    for i, r in enumerate(results, 1):
        raw = "\n".join(r["highlights"][:2]) if r["highlights"] else ""
        lines = [l for l in raw.splitlines() if l.strip()]
        highlights_text = "\n".join(lines[:5])
        pub_date = r["published_date"][:10] if r["published_date"] else "-"
        table.add_row(
            str(i),
            r["title"],
            r["url"],
            highlights_text,
            pub_date,
        )

    console.print(table)


def save_results(results: list[dict], path: str = "ai_events_results.json") -> None:
    with open(path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    console.print(f"[green]Saved {len(results)} results → {path}[/green]")


def run(
    queries: Optional[list[str]] = None,
    online_only: bool = True,
    broad_search: bool = True,
    save: bool = True,
    num_results: int = 8,
) -> list[dict]:
    exa = Exa(api_key=EXA_API_KEY)
    queries = queries or SEARCH_QUERIES

    # Only pages published in last 60 days — catches upcoming event announcements
    today = datetime.now(timezone.utc)
    sixty_days_ago = today.replace(day=max(1, today.day - 60) if today.month > 1 else 1)
    start_date = sixty_days_ago.strftime("%Y-%m-%dT00:00:00Z")

    console.print(Panel(
        f"[bold]Exa AI Search[/bold] — Upcoming AI Events & Classes\n"
        f"Queries: {len(queries)} | Per query: {num_results} | "
        f"Published since: {start_date[:10]} | Online-only: {online_only}",
        style="cyan",
    ))

    all_results: list[dict] = []

    for i, q in enumerate(queries, 1):
        console.print(f"[dim][{i}/{len(queries)}][/dim] Searching: [cyan]{q}[/cyan]")

        if broad_search:
            results = search_events(exa, q, num_results=num_results, start_published_date=start_date)
            all_results.extend(results)

        targeted = search_events(
            exa, q,
            num_results=num_results // 2,
            include_domains=INCLUDE_DOMAINS,
            start_published_date=start_date,
        )
        all_results.extend(targeted)

    deduped = deduplicate(all_results)

    # Drop past events
    future_only = [r for r in deduped if is_future_event(r)]
    console.print(
        f"\n[bold]Unique results:[/bold] {len(deduped)} total → "
        f"[green]{len(future_only)} future[/green] "
        f"([dim]{len(deduped)-len(future_only)} past dropped[/dim])"
    )

    print_results(future_only, online_only=online_only)

    if save:
        to_save = future_only if online_only else [r for r in future_only if r["is_online"]]
        save_results(to_save)

    return future_only


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Search for AI online events & classes via Exa")
    parser.add_argument("--all", action="store_true", help="Show all results, not just online events")
    parser.add_argument("--no-save", action="store_true", help="Skip saving JSON output")
    parser.add_argument("--query", type=str, help="Custom single query")
    parser.add_argument("--num-results", type=int, default=8, help="Results per query")
    parser.add_argument("--no-broad", action="store_true", help="Skip broad search, use domain filter only")
    args = parser.parse_args()

    queries = [args.query] if args.query else None

    run(
        queries=queries,
        online_only=not args.all,
        broad_search=not args.no_broad,
        save=not args.no_save,
        num_results=args.num_results,
    )
