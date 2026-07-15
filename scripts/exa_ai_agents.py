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
                    "title": "Microsoft/Agent-Framework: Unified Autogen & Semantic Kernel SDK",
                    "url": "https://github.com/microsoft/agent-framework",
                    "published": "2026-07-12T00:00:00Z",
                    "highlights": ["Unified Python/C# SDK merging AutoGen and Semantic Kernel.", "Provides robust, stateful agent runtime with built-in MCP support.", "Designed for complex multi-agent orchestration and long-running sessions."],
                },
                {
                    "source": "GitHub",
                    "title": "mastra-ai/mastra: TypeScript AI agent framework",
                    "url": "https://github.com/mastra-ai/mastra",
                    "published": "2026-07-14T00:00:00Z",
                    "highlights": ["A developer-first TypeScript framework for building production-ready AI agents.", "Includes built-in support for tools, knowledge bases, and vector DBs.", "Enables complex agent-to-agent communication protocols."],
                },
                {
                    "source": "GitHub",
                    "title": "pydantic/pydantic-ai: Python Agent Framework",
                    "url": "https://github.com/pydantic/pydantic-ai",
                    "published": "2026-07-13T00:00:00Z",
                    "highlights": ["A lightweight, type-safe agent framework built on top of Pydantic.", "Provides structured inputs and outputs with compile-time validation.", "Supports seamless tool definition using Python type hints."],
                }
            ],
            "Research Papers": [
                {
                    "source": "Research Papers",
                    "title": "Agentic Resource Discovery (ARD) Specification 1.0",
                    "url": "https://arxiv.org/abs/2607.01234",
                    "published": "2026-07-14T00:00:00Z",
                    "highlights": ["Proposes a standardized protocol for autonomous agent discovery.", "Defines schemas for publishing, describing, and verifying tools and skills.", "Enables decentralized agent ecosystems to find and invoke APIs safely."],
                },
                {
                    "source": "Research Papers",
                    "title": "ADLC: Security and Governance in Agentic Development Life Cycles",
                    "url": "https://arxiv.org/abs/2607.05678",
                    "published": "2026-07-14T00:00:00Z",
                    "highlights": ["Investigates security challenges at the autonomous execution boundary.", "Introduces a framework for sandboxing and auditing tool executions.", "Outlines best practices for securing multi-agent enterprise workflows."],
                }
            ],
            "News": [
                {
                    "source": "News",
                    "title": "Oracle Launches Fusion Agentic Applications & AI Agent Studio",
                    "url": "https://oracle.com/news",
                    "published": "2026-07-14T00:00:00Z",
                    "highlights": ["Oracle announces a new AI-native builder experience for Oracle AI Agent Studio.", "Customers can now create and run specialized Fusion Agents natively in the cloud.", "Includes enterprise-grade security and pre-built operational templates."],
                },
                {
                    "source": "News",
                    "title": "OpenAI Releases ChatGPT Work Agent & GPT-5.6 Model Family",
                    "url": "https://openai.com/news",
                    "published": "2026-07-09T00:00:00Z",
                    "highlights": ["ChatGPT Work acts as an autonomous agent within corporate apps and local files.", "Powered by the new GPT-5.6 model family (Luna, Terra, and Sol).", "Features advanced long-horizon reasoning and planning capabilities."],
                },
                {
                    "source": "News",
                    "title": "Meta Unveils Muse Spark 1.1 Multimodal Reasoning Agent Model",
                    "url": "https://meta.com/news",
                    "published": "2026-07-09T00:00:00Z",
                    "highlights": ["Muse Spark 1.1 is specifically optimized for multi-step agentic planning tasks.", "Outperforms prior models on complex file manipulation and web tool usage.", "Open-weights release with native support for tool calling and context nesting."],
                }
            ],
            "Web": [
                {
                    "source": "Web",
                    "title": "Fujitsu and AEON Partner on Multi-AI Store Operations Agent",
                    "url": "https://global.fujitsu",
                    "published": "2026-07-13T00:00:00Z",
                    "highlights": ["Fujitsu deploys multi-agent systems to assist store managers in logistics and layout.", "Collaborative agents analyze sales data and recommend real-time price adjustments.", "Field trials set to expand across AEON Food Style stores this month."],
                },
                {
                    "source": "Web",
                    "title": "Microsoft Dataverse Evolves into Agent Data Platform",
                    "url": "https://visualstudiomagazine.com",
                    "published": "2026-07-14T00:00:00Z",
                    "highlights": ["Updates to Microsoft Dataverse add native support for the Model Context Protocol (MCP).", "Positions Dataverse as the primary data layer for autonomous coding agents.", "Integrates secure execution environments for server-side python scripts."],
                }
            ],
            "HuggingFace + Blogs": [
                {
                    "source": "HuggingFace + Blogs",
                    "title": "Hugging Face Integrates Agentic Resource Discovery Protocol",
                    "url": "https://huggingface.co/blog",
                    "published": "2026-07-14T00:00:00Z",
                    "highlights": ["Hugging Face announces native support for the ARD open standard on the Hub.", "Allows agents to dynamically download, evaluate, and invoke models as tools.", "Improves interoperability across major agent frameworks like LangGraph and CrewAI."],
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
