import requests
import time
import sys
import argparse
from rich.console import Console
from rich.table import Table

# --- CONFIGURATION ---
USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
TRONSCAN_API_BASE = "https://apilist.tronscanapi.com/api"
# Pre-configured key from your previous production validator
API_KEY = "e39c9fb9-66a1-43ef-8f21-4eb605aeceb2" 

console = Console()

def get_headers():
    return {"TRON-PRO-API-KEY": API_KEY, "Accept": "application/json"}

def fetch_inbound_senders(address):
    """Fetches unique sender addresses from inbound TRX and USDT transfers."""
    senders = set()
    headers = get_headers()
    
    # 1. Fetch TRX Inbound (direction=1 is IN)
    trx_url = f"{TRONSCAN_API_BASE}/transfer/trx"
    params = {"address": address, "direction": 1, "reverse": "true", "limit": 50}
    try:
        res = requests.get(trx_url, params=params, headers=headers, timeout=15)
        data = res.json().get('data', [])
        for tx in data:
            if tx.get('transferFromAddress'):
                senders.add(tx['transferFromAddress'])
    except Exception as e:
        console.print(f"[red]Error fetching TRX transfers: {e}[/]")

    # 2. Fetch USDT (TRC20) Inbound
    usdt_url = f"{TRONSCAN_API_BASE}/transfer/trc20"
    params = {"address": address, "trc20Id": USDT_CONTRACT, "direction": 1, "reverse": "true", "limit": 50}
    try:
        res = requests.get(usdt_url, params=params, headers=headers, timeout=15)
        data = res.json().get('data', [])
        for tx in data:
            if tx.get('from_address'):
                senders.add(tx['from_address'])
    except Exception as e:
        console.print(f"[red]Error fetching USDT transfers: {e}[/]")
        
    return list(senders)

def get_address_balances(address):
    """Fetches live TRX and USDT balances for a specific address."""
    account_url = f"{TRONSCAN_API_BASE}/account"
    try:
        res = requests.get(account_url, params={"address": address}, headers=get_headers(), timeout=10)
        data = res.json()
        trx_balance = float(data.get('balance', 0)) / 1_000_000
        usdt_balance = 0.0
        tokens = data.get('trc20token_balances', [])
        for t in tokens:
            if t.get('tokenId') == USDT_CONTRACT:
                usdt_balance = float(t.get('balance', 0)) / (10**int(t.get('tokenDecimal', 6)))
                break
        return trx_balance, usdt_balance
    except:
        return 0.0, 0.0

def main():
    parser = argparse.ArgumentParser(description="TRON Inbound Transaction Researcher")
    parser.add_argument("wallet", nargs="?", help="The TRON wallet address to analyze")
    args = parser.parse_args()

    target_wallet = args.wallet
    if not target_wallet:
        console.print("\n[bold cyan]TRON Inbound Transaction Researcher[/]")
        target_wallet = input("Enter the TRON wallet address to analyze: ").strip()
    
    if not target_wallet or len(target_wallet) < 30:
        console.print("[bold red]Error:[/] Invalid wallet address.")
        sys.exit(1)

    with console.status(f"[bold green]Scanning inbound history for {target_wallet}...[/]"):
        senders = fetch_inbound_senders(target_wallet)
        
        if not senders:
            console.print(f"\n[yellow]No inbound transactions found for {target_wallet}.[/]\n")
            return

        table = Table(title=f"Inbound Sources for {target_wallet}", title_style="bold magenta")
        table.add_column("Inbound Sender Address", style="cyan", no_wrap=True)
        table.add_column("Current TRX Balance", justify="right", style="green")
        table.add_column("Current USDT Balance", justify="right", style="green")
        
        for sender in senders:
            if sender == target_wallet: continue
            trx, usdt = get_address_balances(sender)
            table.add_row(sender, f"{trx:,.2f}", f"{usdt:,.2f}")
            time.sleep(0.1) # Rate limit protection

    console.print(table)
    console.print(f"\n[dim]Analysis complete. {len(senders)} unique inbound wallets identified.[/]\n")

if __name__ == "__main__":
    main()