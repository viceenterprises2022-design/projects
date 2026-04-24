import requests
import time
import sys
import argparse
from rich.console import Console
from rich.table import Table
from rich.progress import track

# --- CONFIGURATION ---
USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
TRONGRID_BASE = "https://api.trongrid.io"
TRONSCAN_BASE = "https://apilist.tronscanapi.com/api"
# Using your verified production key
API_KEY = "e39c9fb9-66a1-43ef-8f21-4eb605aeceb2" 

console = Console()

def get_headers():
    return {"TRON-PRO-API-KEY": API_KEY, "Accept": "application/json"}

def fetch_inbound_senders(address):
    """Fetches inbound senders from both TRX and USDT (TRC20) history."""
    senders = set()
    headers = get_headers()
    
    # 1. Fetch USDT Inbound via TronGrid (Best for TRC20 with your API key)
    usdt_url = f"{TRONGRID_BASE}/v1/accounts/{address}/transactions/trc20"
    params = {"limit": 50, "only_confirmed": "true", "only_to": "true"}
    try:
        res = requests.get(usdt_url, params=params, headers=headers, timeout=15)
        data = res.json().get('data', [])
        for tx in data:
            if tx.get('to') == address and tx.get('from'):
                senders.add(tx['from'])
    except Exception as e:
        console.print(f"[red]USDT Fetch Error: {e}[/]")

    # 2. Fetch TRX Inbound via TronScan (Standard for native TRX)
    trx_url = f"{TRONSCAN_BASE}/transfer"
    params = {"address": address, "limit": 50}
    try:
        res = requests.get(trx_url, params=params, headers=headers, timeout=15)
        data = res.json().get('data', [])
        for tx in data:
            if tx.get('transferToAddress') == address and tx.get('transferFromAddress'):
                senders.add(tx['transferFromAddress'])
    except Exception as e:
        console.print(f"[red]TRX Fetch Error: {e}[/]")
        
    return list(filter(None, senders))

def get_live_balances(address):
    """Fetches real-time TRX and USDT balances for a wallet."""
    # Using TronScan for balances as it aggregates both in one response
    url = f"{TRONSCAN_BASE}/account"
    try:
        res = requests.get(url, params={"address": address}, headers=get_headers(), timeout=10)
        data = res.json()
        
        # TRX calculation (SUN to TRX)
        trx = float(data.get('balance', 0)) / 1_000_000
        
        # USDT calculation from TRC20 list
        usdt = 0.0
        tokens = data.get('trc20token_balances', [])
        for t in tokens:
            if t.get('tokenId') == USDT_CONTRACT:
                usdt = float(t.get('balance', 0)) / (10**int(t.get('tokenDecimal', 6)))
                break
        return trx, usdt
    except:
        return 0.0, 0.0

def main():
    parser = argparse.ArgumentParser(description="Professional TRON Inbound Researcher")
    parser.add_argument("wallet", nargs="?", help="Wallet address to analyze")
    args = parser.parse_args()

    target_wallet = args.wallet or input("\nEnter TRON address to analyze: ").strip()
    if len(target_wallet) < 30:
        console.print("[bold red]Error:[/] Invalid TRON address format.")
        sys.exit(1)

    console.print(f"\n[bold cyan]Starting Research for:[/] [yellow]{target_wallet}[/]")
    
    senders = fetch_inbound_senders(target_wallet)
    # Remove self from senders
    if target_wallet in senders: senders.remove(target_wallet)

    if not senders:
        console.print(f"\n[bold red]![/] No inbound TRX or USDT history found for this address.")
        console.print("[dim]This may be an outbound-only or empty wallet.[/]\n")
        return

    table = Table(title="Inbound Senders & Current Balances", title_style="bold magenta", header_style="bold cyan")
    table.add_column("Sender Wallet Address", no_wrap=True)
    table.add_column("TRX Balance", justify="right", style="green")
    table.add_column("USDT Balance", justify="right", style="green")

    # Progress bar for balance lookups to handle rate limiting gracefully
    for sender in track(senders, description="Querying sender balances..."):
        trx, usdt = get_live_balances(sender)
        table.add_row(sender, f"{trx:,.2f} TRX", f"{usdt:,.2f} USDT")
        time.sleep(0.1) # Respecting rate limits

    console.print("\n", table)
    console.print(f"[bold green]Success:[/] Found {len(senders)} unique inbound sources.\n")

if __name__ == "__main__":
    main()