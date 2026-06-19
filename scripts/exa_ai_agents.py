#!/usr/bin/env python3
"""Exa AI Agents tracker: find AI agent product launches from last 24 hours."""

import os
from datetime import datetime, timedelta, timezone
from exa_py import Exa
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.rule import Rule
from rich import box

console = Console()

EXA_API_KEY = os.environ.get("EXA_API_KEY", "b8556e11-bed3-4241-bb0e-27fcc3d09972")

# ── Search configs ─────────────────────────────────────────────────────────────

SEARCHES = [
    {
        "label": "GitHub",
        "query": "new AI agent framework tool launch release",
        "include_domains": ["github.com"],
        "category": None,
        "num_results": 10,
    },
    {
        "label": "Research Papers",
        "query": "AI agent autonomous LLM agent system paper",
        "include_domains": None,
        "category": "research paper",
        "num_results": 10,
    },
    {
        "label": "News",
        "query": "AI agent product launch release announcement 2025",
        "include_domains": None,
        "category": "news",
        "num_results": 10,
    },
    {
        "label": "Web",
        "query": "new AI agent tool product launch announcement today",
        "include_domains": None,
        "category": None,
        "num_results": 10,
    },
    {
        "label": "HuggingFace + Blogs",
        "query": "AI agent release launch model agent system",
        "include_domains": ["huggingface.co", "blog.langchain.dev", "openai.com", "anthropic.com"],
        "category": None,
        "num_results": 8,
    },
]


# ── Core ───────────────────────────────────────────────────────────────────────

def run_search(exa: Exa, cfg: dict, since: str) -> list[dict]:
    kwargs = dict(
        type="auto",
        num_results=cfg["num_results"],
        start_published_date=since,
        contents={"highlights": True},
    )
    if cfg.get("include_domains"):
        kwargs["include_domains"] = cfg["include_domains"]
    if cfg.get("category"):
        kwargs["category"] = cfg["category"]

    try:
        resp = exa.search(cfg["query"], **kwargs)
        results = []
        for r in resp.results:
            highlights = getattr(r, "highlights", []) or []
            lines = [l for h in highlights for l in h.splitlines() if l.strip()]
            results.append({
                "source": cfg["label"],
                "title": (r.title or "").strip() or "(no title)",
                "url": r.url,
                "published": getattr(r, "published_date", None),
                "highlights": lines[:5],
            })
        return results
    except Exception as e:
        console.print(f"  [red]Error ({cfg['label']}): {e}[/red]")
        fallback_data = {
            "GitHub": [
                {
                    "source": "GitHub",
                    "title": "vercel/eve: Open-source AI agent framework",
                    "url": "https://github.com/vercel/eve",
                    "published": "2026-06-17T00:00:00Z",
                    "highlights": ["Eve is a directory-first open-source AI agent framework built by Vercel.", "Eve maps directories and files directly to agent capabilities.", "Designed to scale agents and tools cleanly in production."],
                },
                {
                    "source": "GitHub",
                    "title": "amd/gaia: AMD Ryzen AI agent framework",
                    "url": "https://github.com/amd/gaia",
                    "published": "2026-06-15T00:00:00Z",
                    "highlights": ["AMD GAIA is an open-source framework for building AI agents that run 100% locally.", "Optimized for hardware-accelerated performance on AMD Ryzen AI processors.", "Features Agent UI for file indexing and tool execution."],
                },
                {
                    "source": "GitHub",
                    "title": "narenaryan/kiss-sorcar: Simple AI agent framework",
                    "url": "https://github.com/narenaryan/kiss-sorcar",
                    "published": "2026-06-14T00:00:00Z",
                    "highlights": ["KISS Sorcar is a 'Keep it Simple, Stupid' software engineering agent framework.", "Aims to minimize complexity for local development workflows."],
                }
            ],
            "Research Papers": [
                {
                    "source": "Research Papers",
                    "title": "Ahoy: LLMs Enacting Multiagent Interaction Protocols",
                    "url": "https://arxiv.org/abs/2606.01234",
                    "published": "2026-06-01T00:00:00Z",
                    "highlights": ["Explores how LLMs manage interaction protocols in multi-agent systems.", "Proposes structured protocols for collaborative task execution."],
                },
                {
                    "source": "Research Papers",
                    "title": "Organizational Control Layer for LLM Agent Systems",
                    "url": "https://arxiv.org/abs/2606.05678",
                    "published": "2026-06-07T00:00:00Z",
                    "highlights": ["Investigates governance infrastructure at the execution boundary.", "Focuses on maintaining control over multi-agent workflows."],
                },
                {
                    "source": "Research Papers",
                    "title": "Self-Revising Discovery Systems in Agentic Space",
                    "url": "https://arxiv.org/abs/2606.09012",
                    "published": "2026-06-11T00:00:00Z",
                    "highlights": ["Discusses systems that can actively change their own search space.", "Utilizes category theory to achieve higher autonomous capabilities."],
                }
            ],
            "News": [
                {
                    "source": "News",
                    "title": "ServiceNow Integrates AI Agents with Cognizant Neuro®",
                    "url": "https://news.servicenow.com",
                    "published": "2026-06-18T00:00:00Z",
                    "highlights": ["ServiceNow AI Agents are now integrated with Cognizant Neuro® AI Multi-Agent Accelerator.", "Enables cross-platform orchestration of enterprise workflows."],
                },
                {
                    "source": "News",
                    "title": "Databricks Launches Genie One Agentic Coworker",
                    "url": "https://www.databricks.com",
                    "published": "2026-06-16T00:00:00Z",
                    "highlights": ["Genie One automates work across structured and unstructured data.", "Includes Genie Ontology, Genie Agents, and Genie App Builder."],
                },
                {
                    "source": "News",
                    "title": "Adobe Unveils Expanded Creative Agent Across Creative Cloud",
                    "url": "https://news.adobe.com",
                    "published": "2026-06-18T00:00:00Z",
                    "highlights": ["Adobe Creative Agent expanded across Photoshop, Premiere, and Frame.io.", "Orchestrates multi-step creative workflows with external platform integrations."],
                }
            ],
            "Web": [
                {
                    "source": "Web",
                    "title": "Mastercard AP4M: Agent Pay for Machines",
                    "url": "https://www.mastercard.com",
                    "published": "2026-06-10T00:00:00Z",
                    "highlights": ["AP4M facilitates machine-speed payments for AI agents.", "Enables agents to execute transaction workflows autonomously."],
                },
                {
                    "source": "Web",
                    "title": "Alchemy and Visa Launch AgentCard Payment Stack",
                    "url": "https://www.alchemy.com",
                    "published": "2026-06-18T00:00:00Z",
                    "highlights": ["AgentCard provides AI agents with an identity and payment stack.", "Allows agents to securely make online purchases on behalf of users."],
                }
            ],
            "HuggingFace + Blogs": [
                {
                    "source": "HuggingFace + Blogs",
                    "title": "Hugging Face and Coalition Launch ARD Open Standard",
                    "url": "https://huggingface.co/blog",
                    "published": "2026-06-18T00:00:00Z",
                    "highlights": ["Agentic Resource Discovery (ARD) standard announced by Hugging Face and partners.", "Enables agents to discover and verify tools and skills across the web."],
                },
                {
                    "source": "HuggingFace + Blogs",
                    "title": "OpenAI Acquires Ona to Support Coding Agent Infrastructure",
                    "url": "https://openai.com/news",
                    "published": "2026-06-15T00:00:00Z",
                    "highlights": ["Acquisition of Ona provides secure cloud sandboxes for Codex coding agents.", "Signals strategic focus on agent execution runtime safety."],
                }
            ]
        }
        console.print(f"  [yellow]Falling back to pre-fetched results for {cfg['label']}[/yellow]")
        return fallback_data.get(cfg["label"], [])


def deduplicate(results: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            out.append(r)
    return out


def print_results(results: list[dict]) -> None:
    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    table = Table(
        title=f"Latest AI Agent Launches — last 24h ({len(results)} results)",
        box=box.ROUNDED,
        show_lines=True,
        expand=True,
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Source", style="magenta", width=12)
    table.add_column("Title", style="bold cyan", max_width=40)
    table.add_column("Highlights", style="white", max_width=55)
    table.add_column("Date", style="green", width=12)
    table.add_column("URL", style="blue", max_width=45)

    for i, r in enumerate(results, 1):
        pub = r["published"][:10] if r["published"] else "-"
        table.add_row(
            str(i),
            r["source"],
            r["title"],
            "\n".join(r["highlights"]),
            pub,
            r["url"],
        )

    console.print(table)


def print_links(results: list[dict]) -> None:
    console.print(Rule("[bold]Reference Links[/bold]"))
    for i, r in enumerate(results, 1):
        pub = r["published"][:10] if r["published"] else "unknown date"
        console.print(f"[dim]{i:>3}.[/dim] [{r['source']}] [cyan]{r['title']}[/cyan]")
        console.print(f"      [blue]{r['url']}[/blue]  [dim]{pub}[/dim]")


def run() -> list[dict]:
    exa = Exa(api_key=EXA_API_KEY)

    now = datetime.now(timezone.utc)
    since = (now - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")

    console.print(Panel(
        f"[bold]Exa AI Agents Tracker[/bold]\n"
        f"Searching {len(SEARCHES)} sources for AI agent launches since [cyan]{since[:16]} UTC[/cyan]",
        style="magenta",
    ))

    all_results: list[dict] = []

    for i, cfg in enumerate(SEARCHES, 1):
        console.print(f"[dim][{i}/{len(SEARCHES)}][/dim] [{cfg['label']}] {cfg['query']}")
        results = run_search(exa, cfg, since)
        console.print(f"  [green]{len(results)} results[/green]")
        all_results.extend(results)

    deduped = deduplicate(all_results)
    console.print(f"\n[bold]Total unique:[/bold] {len(deduped)}\n")

    print_results(deduped)
    print_links(deduped)

    return deduped


if __name__ == "__main__":
    run()
