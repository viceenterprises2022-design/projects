#!/usr/bin/env python3
"""
TRON USDT (TRC20) Wallet Historian — v5
Author  : AlphaEdge / Pinaka.ai
Purpose : Fetch complete inbound + outbound USDT transfer history for any TRON wallet.
          Shows per-counterparty aggregated view + per-transaction detail table.
API     : TronGrid v1 REST (api.trongrid.io) — replaces broken Tronscan apilist endpoints.

Root cause of v4 failure:
  • https://apilist.tronscanapi.com/api  →  returns HTTP 503 (fully down)
  • https://api.trongrid.io/v1          →  returns HTTP 200 ✓ (correct API)
  • Tronscan API key is rejected 401 by TronGrid (different auth systems)
  • TronGrid works fine WITHOUT an API key at low volume, or with TRONGRID API key
"""

import requests
import time
import sys
import argparse
from datetime import datetime, timezone
from collections import defaultdict
from rich.console import Console
from rich.table import Table
from rich import box

# ─── CONFIGURATION ──────────────────────────────────────────────────────────
USDT_CONTRACT  = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
TRONGRID_BASE  = "https://api.trongrid.io"

# TronGrid API key (get free at https://www.trongrid.io/)
# Leave as empty string "" for unauthenticated access (rate-limited but works)
TRONGRID_API_KEY = ""

USDT_DECIMALS  = 6
PAGE_SIZE      = 200      # max allowed by TronGrid
MAX_PAGES      = 50       # safety cap — 50 × 200 = 10,000 txs

console = Console()


# ─── HELPERS ────────────────────────────────────────────────────────────────

def get_headers() -> dict:
    h = {"Accept": "application/json"}
    if TRONGRID_API_KEY:
        h["TRON-PRO-API-KEY"] = TRONGRID_API_KEY
    return h


def ts_to_str(ms: int) -> str:
    """Convert epoch-milliseconds to human-readable UTC string."""
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def sun_to_trx(sun: int) -> float:
    return sun / 1_000_000


def raw_to_usdt(raw) -> float:
    return int(raw) / (10 ** USDT_DECIMALS)


# ─── CORE FETCH ─────────────────────────────────────────────────────────────

def fetch_all_usdt_transfers(wallet: str) -> list[dict]:
    """
    Paginate through the full TRC20 USDT transfer history for `wallet`.
    TronGrid returns newest-first. Uses fingerprint-based cursor pagination.
    """
    all_txs: list[dict] = []
    url = f"{TRONGRID_BASE}/v1/accounts/{wallet}/transactions/trc20"
    params = {
        "limit":            PAGE_SIZE,
        "contract_address": USDT_CONTRACT,
        "only_confirmed":   "true",
    }
    headers = get_headers()
    page = 0

    with console.status("[bold green]Fetching USDT transfer history from TronGrid…[/]") as status:
        while page < MAX_PAGES:
            try:
                r = requests.get(url, params=params, headers=headers, timeout=20)
                if r.status_code != 200:
                    console.print(f"[red]HTTP {r.status_code} on page {page + 1}. Stopping.[/]")
                    break
                d = r.json()
            except Exception as e:
                console.print(f"[red]Request error on page {page + 1}: {e}[/]")
                break

            batch = d.get("data", [])
            all_txs.extend(batch)
            page += 1
            status.update(
                f"[bold green]Page {page} — {len(all_txs):,} transactions fetched…[/]"
            )

            # Pagination: TronGrid uses a fingerprint cursor
            fingerprint = d.get("meta", {}).get("fingerprint")
            if not fingerprint or len(batch) < PAGE_SIZE:
                break

            params["fingerprint"] = fingerprint
            time.sleep(0.15)   # polite rate-limit buffer

    return all_txs


def fetch_wallet_balances(wallet: str) -> tuple[float, float]:
    """Return (TRX balance, USDT balance) for a wallet address."""
    try:
        r = requests.get(
            f"{TRONGRID_BASE}/v1/accounts/{wallet}",
            headers=get_headers(),
            timeout=10,
        )
        if r.status_code != 200:
            return 0.0, 0.0
        acc_list = r.json().get("data", [])
        if not acc_list:
            return 0.0, 0.0
        acc = acc_list[0]
        trx = sun_to_trx(acc.get("balance", 0))
        usdt = 0.0
        for token_map in acc.get("trc20", []):
            if USDT_CONTRACT in token_map:
                usdt = raw_to_usdt(token_map[USDT_CONTRACT])
                break
        return trx, usdt
    except Exception:
        return 0.0, 0.0


# ─── DISPLAY ────────────────────────────────────────────────────────────────

def print_transaction_detail(txs: list[dict], wallet: str, direction: str):
    """Print every individual transaction in chronological order."""
    label = "INBOUND" if direction == "in" else "OUTBOUND"
    color = "green" if direction == "in" else "yellow"
    filtered = [t for t in txs if (t["to"] == wallet) == (direction == "in")]
    # Sort oldest-first
    filtered.sort(key=lambda t: t["block_timestamp"])

    title = f"[bold {color}]{label} USDT Transfers — {wallet}[/] ({len(filtered):,} txs)"
    t = Table(title=title, title_style=f"bold {color}", box=box.SIMPLE_HEAVY, show_lines=False)
    t.add_column("#",            style="dim",     justify="right", width=5)
    t.add_column("Date (UTC)",   style="white",   width=20)
    t.add_column("Tx Hash",      style="cyan",    width=18, no_wrap=True)
    t.add_column("Counterparty", style="magenta", width=36, no_wrap=True)
    t.add_column("USDT Amount",  style=color,     justify="right", width=16)

    for i, tx in enumerate(filtered, 1):
        ts  = ts_to_str(tx["block_timestamp"])
        txid = tx["transaction_id"]
        short_hash = txid[:8] + "…" + txid[-6:]
        counterparty = tx["from"] if direction == "in" else tx["to"]
        amount = raw_to_usdt(tx["value"])
        t.add_row(str(i), ts, short_hash, counterparty, f"{amount:,.2f}")

    console.print(t)


def print_counterparty_summary(txs: list[dict], wallet: str, direction: str):
    """Aggregate by counterparty address and show totals + live balances."""
    label = "INBOUND SENDERS" if direction == "in" else "OUTBOUND RECIPIENTS"
    color = "green" if direction == "in" else "yellow"
    filtered = [t for t in txs if (t["to"] == wallet) == (direction == "in")]

    # Aggregate per counterparty
    totals: dict[str, dict] = defaultdict(lambda: {"count": 0, "usdt": 0.0})
    for tx in filtered:
        cp = tx["from"] if direction == "in" else tx["to"]
        totals[cp]["count"] += 1
        totals[cp]["usdt"]  += raw_to_usdt(tx["value"])

    # Sort by total USDT desc
    ranked = sorted(totals.items(), key=lambda x: x[1]["usdt"], reverse=True)

    title = f"[bold {color}]{label} SUMMARY[/] ({len(ranked)} unique wallets)"
    t = Table(title=title, title_style=f"bold {color}", box=box.SIMPLE_HEAVY)
    t.add_column("Rank",           style="dim",     justify="right", width=5)
    t.add_column("Counterparty",   style="magenta", width=36, no_wrap=True)
    t.add_column("Tx Count",       justify="right", width=9)
    t.add_column("Total USDT",     style=color,     justify="right", width=16)
    t.add_column("Live TRX Bal",   style="cyan",    justify="right", width=14)
    t.add_column("Live USDT Bal",  style="cyan",    justify="right", width=14)

    console.print(f"\n[dim]Fetching live balances for {len(ranked)} counterparty wallets…[/]")
    for rank, (cp, stats) in enumerate(ranked, 1):
        trx_bal, usdt_bal = fetch_wallet_balances(cp)
        t.add_row(
            str(rank),
            cp,
            str(stats["count"]),
            f"{stats['usdt']:,.2f}",
            f"{trx_bal:,.2f}",
            f"{usdt_bal:,.2f}",
        )
        time.sleep(0.1)   # rate-limit buffer

    console.print(t)


# ─── MAIN ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="TRON USDT Wallet Historian — full inbound/outbound history"
    )
    parser.add_argument(
        "wallet", nargs="?",
        help="Target TRON wallet address (TRC20)"
    )
    parser.add_argument(
        "--detail", action="store_true",
        help="Also print per-transaction detail tables (can be long)"
    )
    args = parser.parse_args()

    wallet = args.wallet or input("\nEnter TRON wallet address: ").strip()

    if len(wallet) < 30 or not wallet.startswith("T"):
        console.print("[bold red]Error:[/] Not a valid TRON address (must start with T, ~34 chars).")
        sys.exit(1)

    console.rule(f"[bold cyan]TRON USDT Historian — {wallet}[/]")

    # 1. Fetch complete transfer history
    all_txs = fetch_all_usdt_transfers(wallet)

    if not all_txs:
        console.print("[yellow]No USDT transactions found for this address.[/]")
        sys.exit(0)

    inbound  = [t for t in all_txs if t["to"]   == wallet]
    outbound = [t for t in all_txs if t["from"]  == wallet]

    total_in  = sum(raw_to_usdt(t["value"]) for t in inbound)
    total_out = sum(raw_to_usdt(t["value"]) for t in outbound)
    net       = total_in - total_out

    # 2. Target wallet live balance
    console.print("\n[bold]Fetching target wallet live balance…[/]")
    trx_bal, usdt_bal = fetch_wallet_balances(wallet)

    # 3. Summary header
    summary = Table(title="Wallet Overview", box=box.ROUNDED, title_style="bold white")
    summary.add_column("Metric",  style="bold white", width=28)
    summary.add_column("Value",   justify="right",    width=22)
    summary.add_row("Total USDT Received",   f"[green]{total_in:,.2f}[/]")
    summary.add_row("Total USDT Sent",       f"[yellow]{total_out:,.2f}[/]")
    summary.add_row("Net USDT Flow",         f"[cyan]{net:+,.2f}[/]")
    summary.add_row("Inbound Tx Count",      str(len(inbound)))
    summary.add_row("Outbound Tx Count",     str(len(outbound)))
    summary.add_row("Live TRX Balance",      f"[cyan]{trx_bal:,.4f}[/]")
    summary.add_row("Live USDT Balance",     f"[cyan]{usdt_bal:,.2f}[/]")
    console.print(summary)

    # 4. Optional per-transaction detail tables
    if args.detail:
        console.rule("[green]INBOUND — Transaction Detail[/]")
        print_transaction_detail(all_txs, wallet, "in")
        console.rule("[yellow]OUTBOUND — Transaction Detail[/]")
        print_transaction_detail(all_txs, wallet, "out")

    # 5. Counterparty summary tables (always shown)
    console.rule("[green]INBOUND — Counterparty Summary[/]")
    print_counterparty_summary(all_txs, wallet, "in")

    console.rule("[yellow]OUTBOUND — Counterparty Summary[/]")
    print_counterparty_summary(all_txs, wallet, "out")

    console.rule("[dim]Done[/]")
    console.print(f"[dim]Total USDT transactions analysed: {len(all_txs):,}[/]\n")


if __name__ == "__main__":
    main()
