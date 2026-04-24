import requests
import time
import sys
import argparse
from rich.console import Console
from rich.table import Table

# --- CONFIGURATION ---
USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
TRONSCAN_API_BASE = "https://apilist.tronscanapi.com/api"
# Verified production key
API_KEY = "e39c9fb9-66a1-43ef-8f21-4eb605aeceb2" 

console = Console()

def get_headers():
    return {"TRON-PRO-API-KEY": API_KEY, "Accept": "application/json"}

def fetch_inbound_senders(address):
    """Fetches unique inbound senders using specific TRONSCAN API parameters."""
    senders = set()
    headers = get_headers()
    
    # 1. Fetch TRX Inbound (Parameter: 'address')
    trx_url = f"{TRONSCAN_API_BASE}/transfer"
    params = {
        "address": address,
        "count": "true",
        "limit": 40,
        "filterTokenValue": 0
    }
    try:
        res = requests.get(trx_url, params=params, headers=headers, timeout=15)
        data = res.json().get('data', [])
        for tx in data:
            if tx.get('toAddress') == address:
                senders.add(tx.get('fromAddress'))
    except Exception as e:
        console.print(f"[red]Error fetching TRX transfers: {e}[/]")

    # 2. Fetch USDT Inbound (Parameter: 'relatedAddress')
    usdt_url = f"{TRONSCAN_API_BASE}/token_trc20/transfers"
    params = {
        "relatedAddress": address,
        "limit": 40,
        "confirm": "true"
    }
    try:
        res = requests.get(usdt_url, params=params, headers=headers, timeout=15)
        data = res.json().get('token_transfers', [])
        for tx in data:
            if tx.get('to_address') == address:
                senders.add(tx.get('from_address'))
    except Exception as e:
        console.print(f"[red]Error fetching USDT transfers: {e}[/]")
        
    return list(filter(None, senders))

def get_address_balances(address):
    """Fetches live TRX and USDT balances for identified sender wallets."""
    account_url = f"{TRONSCAN_API_BASE}/account"
    try:
        res = requests.get(account_url, params={"address": address}, headers=get_headers(), timeout=10)
        data = res.json()
        # Scale TRX by 1M
        trx_balance = float(data.get('balance', 0)) / 1_000_000
        # Search TRC20 list for USDT
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
    parser = argparse.ArgumentParser(description="TRON Inbound Wallet Researcher")
    parser.add_argument("wallet", nargs="?", help="Wallet address to analyze")
    args = parser.parse_args()

    target_wallet = args.wallet or input("\nEnter TRON wallet address: ").strip()
    
    if len(target_wallet) < 30:
        console.print("[bold red]Error:[/] Invalid address format.")
        sys.exit(1)

    with console.status(f"[bold green]Analyzing {target_wallet}...[/]"):
        senders = fetch_inbound_senders(target_wallet)
        
        if not senders:
            console.print(f"\n[yellow]No inbound TRX/USDT transfers found for this address.[/]\n")
            return

        table = Table(title=f"Inbound Wallet Sources", title_style="bold magenta")
        table.add_column("Sender Wallet Address", style="cyan", no_wrap=True)
        table.add_column("Current TRX", justify="right", style="green")
        table.add_column("Current USDT", justify="right", style="green")
        
        for sender in senders:
            if sender == target_wallet: continue
            trx, usdt = get_address_balances(sender)
            table.add_row(sender, f"{trx:,.2f}", f"{usdt:,.2f}")
            time.sleep(0.1) # Protect API health

    console.print(table)
    console.print(f"\n[dim]Found {len(senders)} unique inbound sources.[/]\n")

if __name__ == "__main__":
    main()