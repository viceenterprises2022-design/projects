# research-agent — OpenCode Usage Guide

## What It Is

Multi-domain research tool that auto-classifies topics and routes to the right data collectors. Uses `belt` for web search and existing local scripts for domain-specific data.

## Domains

| Domain | Data Source | Trigger Keywords |
|--------|-----------|-----------------|
| `general` | belt tavily-search | Default fallback |
| `academia` | belt tavily-search (scholar filter) | paper, arxiv, journal, doi |
| `world_news` | belt tavily-search (news) | news, breaking, current events |
| `india_stocks` | local fyers_client + market_engine + belt | nifty, sensex, nse, reliance.ns |
| `us_stocks` | belt tavily-search | aapl, tsla, nyse, nasdaq, spy |
| `crypto` | local crypto scripts + belt | btc, eth, crypto, blockchain |

## Workflow

Step 1 — Collect data:
```bash
python -m research_agent "your query here"
```
This runs the topic classifier, fires all matching collectors, outputs .md + optional .json with raw data.

Step 2 — Synthesize:
Read the collector results (from .json or .md), synthesize findings into a data-driven conclusion, then re-run to attach the synthesis text:

```bash
python -m research_agent "query" --synthesis "Your synthesized conclusion here..."
```

## Flags

| Flag | Description |
|------|-------------|
| `--domain/-d` | Force a domain (skip auto-classification) |
| `--output/-o` | Output directory (default: ./outputs/) |
| `--threshold/-t` | Classification confidence threshold (default 0.25) |
| `--no-pdf` | Skip PDF, output .md only |
| `--json` | Also emit raw JSON with data |
| `--synthesis/-s` | Attach synthesis text to report |

## Architecture

```
__main__.py          → CLI entry, orchestrates
topic_classifier.py  → Regex/keyword auto-routing
data_collectors/     → Domain-specific data fetchers
report_builder.py    → .md report generator
pdf_converter.py     → .md → .pdf (weasyprint / pandoc / fallback)
schemas.py           → Shared data models
```

## PDF Dependencies

The tool tries these in order:
1. `weasyprint` + `markdown` — best quality
2. `pandoc` — good quality
3. Fallback HTML output — always works

Install: `pip install -r requirements.txt`
