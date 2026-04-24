import requests
import time
import sys
import argparse
from rich.console import Console
from rich.table import Table

# --- CONFIGURATION ---
USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
TRONSCAN_API_BASE = "https://apilist.tronscanapi.com/api"
# Production API Key
API_KEY = "e39c9fb9-66a1-43ef-8f21-4eb605aeceb2" 

console = Console()

def get_headers():
    return {"TRON-PRO-API-KEY": API_KEY, "Accept": "application/json"}

def fetch_inbound_senders(address):
    """Corrected mapping for TRX and TRC20 (USDT) inbound transfers."""
    senders = set()
    headers = get_headers()
    
    # 1. TRX Transfers (Standard Endpoint)
    # Correct Parameter: 'address' | Correct Key: 'transferToAddress'
    trx_url = f"{TRONSCAN_API_BASE}/transfer"
    params = {"address": address, "limit": 50}
    try:
        res = requests.get(trx_url, params=params, headers=headers, timeout=15)
        data = res.json().get('data', [])
        for tx in data:
            # Check for TRX or TRC10 transfers arriving at the wallet
            if tx.get('transferToAddress') == address:
                senders.add(tx.get('transferFromAddress'))
    except Exception as e:
        console.print(f"[red]TRX API Error: {e}[/]")

    # 2. USDT Transfers (TRC20 Endpoint)
    # Correct Parameter: 'address' | Correct Key: 'to_address'
    usdt_url = f"{TRONSCAN_API_BASE}/token_trc20/transfers"
    params = {"address": address, "limit": 50}
    try:
        res = requests.get(usdt_url, params=params, headers=headers, timeout=15)
        data = res.json().get('token_transfers', [])
        for tx in data:
            # Check for USDT transfers arriving at the wallet
            if tx.get('to_address') == address:
                senders.add(tx.get('from_address'))
    except Exception as e:
        console.print(f"[red]USDT API Error: {e}[/]")
        
    return list(filter(None, senders))

def get_address_balances(address):
    """Fetches live TRX and USDT balances for the source wallets."""
    account_url = f"{TRONSCAN_API_BASE}/account"
    try:
        res = requests.get(account_url, params={"address": address}, headers=get_headers(), timeout=10)
        data = res.json()
        # Scale TRX (SUN to TRX)
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
    parser = argparse.ArgumentParser(description="TRON Inbound Researcher")
    parser.add_argument("wallet", nargs="?", help="Wallet address")
    args = parser.parse_args()

    target_wallet = args.wallet or input("\nEnter TRON wallet address: ").strip()
    
    if len(target_wallet) < 30:
        console.print("[bold red]Error:[/] Invalid TRON address.")
        sys.exit(1)

    with console.status(f"[bold green]Scanning blockchain for {target_wallet}...[/]"):
        senders = fetch_inbound_senders(target_wallet)
        
        if not senders:
            console.print(f"\n[yellow]No inbound TRX/USDT transfers found for {target_wallet}.[/]")
            return

        table = Table(title=f"Inbound Sources Identified", title_style="bold magenta")
        table.add_column("Sender Wallet Address", style="cyan", no_wrap=True)
        table.add_column("Current TRX", justify="right", style="green")
        table.add_column("Current USDT", justify="right", style="green")
        
        for sender in senders:
            if sender == target_wallet: continue
            trx, usdt = get_address_balances(sender)
            table.add_row(sender, f"{trx:,.2f}", f"{usdt:,.2f}")
            time.sleep(0.05) # Rate limit protection

    console.print(table)
    console.print(f"\n[dim]Analysis complete. {len(senders)} unique source wallets found.[/]\n")

if __name__ == "__main__":
    main()