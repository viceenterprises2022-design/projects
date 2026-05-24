#!/usr/bin/env python3
"""Exa crypto news search — top 10 stories across BTC, ETH, SOL, RWA, stablecoins, onchain milestones, price predictions."""

import os
import json
import re
import argparse
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
load_dotenv()

from exa_py import Exa
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()
EXA_API_KEY = os.environ.get("EXA_API_KEY")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8770565112:AAGy9q-BMWsgvU4RQUQDyeNXa282Vme9uG4")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7246234100")
MAX_TELEGRAM_CHARS = 3500

TOPICS = {
    "BTC": "Bitcoin BTC price news onchain milestone growth prediction 2026",
    "ETH": "Ethereum ETH price news DeFi onchain milestone growth 2026",
    "SOL": "Solana SOL price news ecosystem growth onchain 2026",
    "RWA": "real world assets RWA tokenization crypto 2026",
    "Stablecoins": "stablecoin USDC USDT growth adoption regulation 2026",
    "Onchain": "blockchain onchain milestone total value locked TVL record 2026",
    "Growth": "crypto market growth institutional adoption ETF 2026",
    "Price & Predictions": "crypto price prediction market analysis forecast 2026",
}

DAYS_BACK = 3

def search_topic(exa: Exa, query: str, num: int = 10) -> list[dict]:
    try:
        since = (datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)).strftime("%Y-%m-%dT00:00:00Z")
        resp = exa.search(query, type="auto", num_results=num, start_published_date=since, contents={"summary": {"query": "give me a 1-sentence summary of this article"}})
        results = []
        for r in resp.results:
            results.append({
                "title": (r.title or "").strip(),
                "url": r.url,
                "summary": getattr(r, "summary", "") or "",
                "score": getattr(r, "score", 0),
                "published_date": getattr(r, "published_date", None),
            })
        return results
    except Exception as e:
        console.print(f"[red]Search failed: {e}[/red]")
        return []

def deduplicate(results: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for r in results:
        key = re.sub(r'[^a-z0-9]', '', r["title"].lower())[:60]
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out

def _summary(r: dict) -> str:
    s = r.get("summary", "")
    if not s:
        return ""
    return s[:250] + "…" if len(s) > 250 else s
    text = re.sub(r'\s+', ' ', text).strip()
    lines = text.split(". ")
    seen = set()
    clean = []
    for line in lines:
        line = line.strip()
        if len(line) < 30:
            continue
        short = re.sub(r'[^a-z0-9 ]', '', line.lower())[:40]
        if short in seen:
            continue
        seen.add(short)
        clean.append(line)
        if len(clean) >= 2:
            break
    result = ". ".join(clean)
    if not result.endswith("."):
        result += "."
    title_norm = re.sub(r'[^a-z0-9 ]', '', r["title"].lower()).strip()
    result_norm = re.sub(r'[^a-z0-9 ]', '', result.lower()).strip()
    overlap = len(set(result_norm.split()) & set(title_norm.split()))
    if overlap >= max(3, len(title_norm.split()) * 0.5):
        return ""
    if len(result) > 250:
        result = result[:250] + "…"
    return result

TOPIC_ICONS = {
    "BTC": "₿ BTC",
    "ETH": "⟠ ETH",
    "SOL": "◎ SOL",
    "RWA": "🏛 RWA",
    "Stablecoins": "💵 Stablecoins",
    "Onchain": "⛓ Onchain",
    "Growth": "📈 Growth",
    "Price & Predictions": "🔮 Price & Predictions",
}

def build_report(all_results: dict[str, list[dict]]) -> str:
    lines = []
    lines.append(f"📡 *Crypto Daily Brief*")
    lines.append(f"_{datetime.now(timezone.utc).strftime('%d %b %Y • %H:%M UTC')}_")
    lines.append("")
    for topic, results in all_results.items():
        icon = TOPIC_ICONS.get(topic, topic)
        lines.append(f"━━━ {icon} ━━━")
        if not results:
            lines.append("  ∅ No stories")
        else:
            for r in results[:3]:
                title = r["title"]
                summary = _summary(r)
                lines.append(f"• *{title}*")
                if summary:
                    lines.append(f"  ↳ {summary}")
        lines.append("")
    return "\n".join(lines)

def send_telegram(text: str, bot_token: str = "", chat_id: str = "") -> bool:
    import requests
    token = bot_token or TELEGRAM_BOT_TOKEN
    cid = chat_id or TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    chunks = [text[i:i+MAX_TELEGRAM_CHARS] for i in range(0, len(text), MAX_TELEGRAM_CHARS)]
    ok = True
    for chunk in chunks:
        try:
            r = requests.post(url, json={"chat_id": cid, "text": chunk}, timeout=15)
            r.raise_for_status()
        except Exception as e:
            console.print(f"[red]Telegram send failed: {e}[/red]")
            ok = False
    return ok

def print_summary(all_results: dict[str, list[dict]]) -> None:
    console.print(Panel("[bold cyan]Crypto News Dashboard[/bold cyan]", style="cyan"))
    total = sum(len(v) for v in all_results.values())
    console.print(f"[dim]{total} stories across {len(all_results)} topics (last {DAYS_BACK}d)[/dim]\n")
    for topic, results in all_results.items():
        table = Table(title=topic, box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("Item", style="dim", width=2)
        table.add_column("Title", style="bold white", max_width=55)
        table.add_column("Summary", style="cyan", max_width=50)
        for i, r in enumerate(results[:3], 1):
            summary = _summary(r) or ""
            snippet = (summary[:80] + "...") if len(summary) > 80 else summary
            table.add_row(str(i), r["title"], snippet)
        console.print(table)
        console.print("")

def main():
    parser = argparse.ArgumentParser(description="Fetch latest crypto news via Exa.")
    parser.add_argument("--num", type=int, default=10, help="Results per topic")
    parser.add_argument("--report", action="store_true", help="Output plain-text report (for Slack/cron)")
    parser.add_argument("--save", type=str, default="", help="Save report to file path")
    parser.add_argument("--telegram", action="store_true", help="Send report to Telegram")
    args = parser.parse_args()

    if not EXA_API_KEY:
        console.print("[red]EXA_API_KEY not set in .env[/red]")
        return

    exa = Exa(api_key=EXA_API_KEY)
    console.print(Panel(
        f"[bold]Fetching crypto news[/bold] — {len(TOPICS)} topics × {args.num} results, last {DAYS_BACK}d",
        style="green",
    ))

    all_results: dict[str, list[dict]] = {}
    for topic, query in TOPICS.items():
        console.print(f"  [dim]Searching:[/dim] {topic}")
        results = search_topic(exa, query, args.num)
        all_results[topic] = deduplicate(results)

    if args.report or args.telegram:
        report = build_report(all_results)
        if args.report:
            print(report)
        if args.save:
            with open(args.save, "w") as f:
                f.write(report)
            console.print(f"[green]Report saved → {args.save}[/green]")
        if args.telegram:
            ok = send_telegram(report)
            console.print(f"[{'green' if ok else 'red'}]Telegram delivery: {'sent' if ok else 'failed'}[/]")
    else:
        print_summary(all_results)

    total = sum(len(v) for v in all_results.values())
    console.print(f"\n[bold green]Done.[/bold green] {total} unique stories.")

if __name__ == "__main__":
    main()
