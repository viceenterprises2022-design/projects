#!/usr/bin/env python3
"""
CryptoPanic CLI News Reader
Token-free live news reader with custom decryption of web client stream.
"""

import sys
import os
import re
import json
import zlib
import base64
import argparse
import webbrowser
from datetime import datetime, timezone
import requests

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    HAS_DECRYPT = True
except ImportError:
    HAS_DECRYPT = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.columns import Columns
    from rich.prompt import Prompt
    from rich.box import ROUNDED, SIMPLE
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


# Decryption Key and Endpoints
DECRYPT_KEY = ")b7Z*$+)/T}$9>/L"
BASE_URL = "https://cryptopanic.com/"
POSTS_API = "https://cryptopanic.com/web-api/posts/"

# Global requests session
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": BASE_URL,
    "Origin": BASE_URL,
})

def get_csrf_token():
    """Fetches the homepage and extracts the CSRF token cookie."""
    try:
        session.get(BASE_URL, timeout=10)
        csrf = session.cookies.get("csrftoken")
        return csrf
    except Exception as e:
        sys.stderr.write(f"Error fetching CSRF token: {e}\n")
        return None

def decrypt_data(encrypted_base64, csrf_token):
    """Decrypts AES-128-CBC and decompresses zlib payload."""
    if not HAS_DECRYPT:
        raise RuntimeError("cryptography library is missing. Install using: pip install cryptography")
        
    key_bytes = DECRYPT_KEY.encode("utf-8")
    iv_str = ("news" + csrf_token)[:16]
    iv_bytes = iv_str.encode("utf-8")
    
    ciphertext = base64.b64decode(encrypted_base64)
    cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv_bytes), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_bytes = decryptor.update(ciphertext) + decryptor.finalize()
    
    # Decompress zlib payload (wbits=15)
    decompressed = zlib.decompress(decrypted_bytes, 15)
    return json.loads(decompressed.decode("utf-8"))

def fetch_posts(csrf_token, feed=None, filter_type=None, currencies=None, q=None, page=1):
    """Hits the private posts endpoint with filters and decrypts the response."""
    filters = {}
    if feed:
        filters["feed"] = feed
    if filter_type:
        filters["filter"] = filter_type
    if currencies:
        filters["currencies"] = currencies
    if q:
        filters["q"] = q
    if page > 1:
        filters["page"] = page

    headers = {"X-CSRFToken": csrf_token}
    data = {"filters": json.dumps(filters)}
    
    response = session.post(POSTS_API, headers=headers, data=data, timeout=15)
    if response.status_code != 200:
        raise RuntimeError(f"API request failed with status code {response.status_code}")
        
    res_json = response.json()
    if not res_json.get("status"):
        raise RuntimeError("API returned error status")
        
    raw_encrypted = res_json.get("s")
    if not raw_encrypted:
        return []
        
    decrypted = decrypt_data(raw_encrypted, csrf_token)
    
    # Normalize list using columns 'k' and rows 'l'
    k_cols = decrypted.get("k", [])
    l_rows = decrypted.get("l", [])
    
    normalized_posts = []
    for row in l_rows:
        post = dict(zip(k_cols, row))
        normalized_posts.append(post)
        
    return normalized_posts

def format_relative_time(iso_str):
    """Converts ISO timestamp to short relative time (e.g. 5m, 2h, 3d)."""
    if not iso_str:
        return "-"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        seconds = int(delta.total_seconds())
        if seconds < 0:
            return "now"
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}h"
        days = hours // 24
        return f"{days}d"
    except Exception:
        return iso_str[:10]

def format_votes(votes):
    """Formats active votes dict into a colorized string with indicators."""
    if not votes:
        return ""
    pos = votes.get("positive", 0)
    neg = votes.get("negative", 0)
    imp = votes.get("important", 0)
    lol = votes.get("lol", 0)
    
    parts = []
    if pos:
        parts.append(f"[green]▲{pos}[/green]")
    if neg:
        parts.append(f"[red]▼{neg}[/red]")
    if imp:
        parts.append(f"[yellow]!{imp}[/yellow]")
    if lol:
        parts.append(f"[cyan]😂{lol}[/cyan]")
        
    return " ".join(parts)

def print_simple_table(posts, limit=20):
    """Outputs basic plain text table if Rich is not available."""
    print(f"{'Index':<6} | {'Time':<5} | {'Title':<60} | {'Source':<15} | {'Currencies':<10}")
    print("-" * 105)
    for i, post in enumerate(posts[:limit], 1):
        title = post.get("title", "")
        if len(title) > 58:
            title = title[:55] + "..."
        domain = post.get("domain", "")
        curr = ",".join(post.get("currencies_codes") or [])
        time_str = format_relative_time(post.get("published_at"))
        print(f"{i:<6} | {time_str:<5} | {title:<60} | {domain:<15} | {curr:<10}")

def render_interactive_dashboard(console, posts, feed, filter_type, currencies, q):
    """Renders the main Rich terminal dashboard."""
    console.clear()
    
    # Header Banner
    header_text = Text()
    header_text.append("🔥 CRYPTOPANIC CLI NEWS 🔥", style="bold red blink")
    header_text.append("  |  ", style="dim white")
    header_text.append(f"Feed: {feed or 'recent'}", style="cyan bold")
    header_text.append("  |  ", style="dim white")
    header_text.append(f"Filter: {filter_type or 'all'}", style="magenta bold")
    header_text.append("  |  ", style="dim white")
    header_text.append(f"Coin: {currencies or 'all'}", style="yellow bold")
    if q:
        header_text.append("  |  ", style="dim white")
        header_text.append(f"Search: '{q}'", style="green bold")
        
    console.print(Panel(header_text, border_style="red", box=ROUNDED))
    
    # Posts Table
    table = Table(box=SIMPLE, expand=True)
    table.add_column("#", style="dim white", width=4, justify="right")
    table.add_column("Age", style="cyan", width=5)
    table.add_column("Title", style="bold white")
    table.add_column("Source", style="dim magenta", width=15)
    table.add_column("Coins", style="yellow", width=10)
    table.add_column("Votes", width=15)
    
    for i, post in enumerate(posts, 1):
        title = post.get("title", "")
        if post.get("kind") == "sponsored":
            title = f"[cyan][Ad][/cyan] {title}"
            
        domain = post.get("domain", "")
        curr_codes = post.get("currencies_codes") or []
        curr = f"[{','.join(curr_codes)}]" if curr_codes else ""
        time_str = format_relative_time(post.get("published_at"))
        votes_str = format_votes(post.get("active_votes"))
        
        table.add_row(
            str(i),
            time_str,
            title,
            domain,
            curr,
            votes_str
        )
        
    console.print(table)
    
    # Prompt Options
    console.print(Panel(
        "[bold white][1-N][/bold white] Details | "
        "[bold yellow][f <coin>][/bold yellow] Coin Filter | "
        "[bold magenta][c <type>][/bold magenta] Sentiment Filter | "
        "[bold green][s <query>][/bold green] Search\n"
        "[bold cyan][feed <type>][/bold cyan] Feed (recent/trending) | "
        "[bold red][r][/bold red] Refresh | "
        "[bold white][q][/bold white] Quit",
        border_style="dim white",
        box=ROUNDED
    ))

def display_post_details(console, post):
    """Renders details view for a selected post."""
    console.clear()
    
    title = post.get("title", "")
    domain = post.get("domain", "")
    published_at = post.get("published_at")
    pk = post.get("pk")
    slug = post.get("slug")
    
    # Construct CryptoPanic news URL
    cp_url = f"https://cryptopanic.com/news/{pk}/{slug}"
    
    details_panel = Text()
    details_panel.append(f"{title}\n\n", style="bold white size=14")
    details_panel.append(f"Domain: ", style="dim white")
    details_panel.append(f"{domain}\n", style="magenta")
    details_panel.append(f"Published: ", style="dim white")
    details_panel.append(f"{published_at}\n\n", style="cyan")
    
    # Votes summary
    votes = post.get("active_votes") or {}
    details_panel.append("Sentiment Votes:\n", style="bold yellow")
    details_panel.append(f"  Bullish (Positive): {votes.get('positive', 0)}\n", style="green")
    details_panel.append(f"  Bearish (Negative): {votes.get('negative', 0)}\n", style="red")
    details_panel.append(f"  Important:          {votes.get('important', 0)}\n", style="yellow")
    details_panel.append(f"  Lol:                {votes.get('lol', 0)}\n", style="cyan")
    details_panel.append(f"  Toxic:              {votes.get('toxic', 0)}\n", style="red bold")
    details_panel.append(f"  Saved:              {votes.get('save', 0) or votes.get('saved', 0)}\n\n", style="blue")
    
    # URL
    details_panel.append("Links:\n", style="bold green")
    details_panel.append(f"  CryptoPanic: {cp_url}\n", style="underline blue")
    
    console.print(Panel(details_panel, title="News Details", border_style="yellow", box=ROUNDED))
    
    console.print(Panel(
        "[bold green][o][/bold green] Open in Browser | "
        "[bold white][Enter][/bold white] Return to List",
        box=ROUNDED,
        border_style="dim white"
    ))
    
    while True:
        cmd = input("Command: ").strip().lower()
        if cmd == "o":
            webbrowser.open(cp_url)
            console.print("[green]Opened in browser![/green]")
        elif cmd == "":
            break

def main():
    parser = argparse.ArgumentParser(description="CryptoPanic CLI News Reader")
    parser.add_argument("--limit", type=int, default=20, help="Number of posts to print (non-interactive)")
    parser.add_argument("--currency", type=str, default=None, help="Filter by coin symbol (e.g. BTC)")
    parser.add_argument("--filter", type=str, default=None, help="Filter by sentiment (e.g. bullish, bearish, important, hot, rising)")
    parser.add_argument("--feed", type=str, default=None, help="Feed type (recent, trending)")
    parser.add_argument("--search", type=str, default=None, help="Search query")
    parser.add_argument("--non-interactive", action="store_true", help="Print table and exit without launching interface")
    args = parser.parse_args()

    # Get CSRF token
    if HAS_RICH:
        console = Console()
        with console.status("[bold green]Establishing secure session with CryptoPanic..."):
            csrf_token = get_csrf_token()
    else:
        print("Establishing secure session with CryptoPanic...")
        csrf_token = get_csrf_token()

    if not csrf_token:
        print("Error: Could not secure session (CSRF fetch failed). Check internet connection.")
        sys.exit(1)

    # If running non-interactively
    if args.non_interactive:
        try:
            posts = fetch_posts(
                csrf_token,
                feed=args.feed,
                filter_type=args.filter,
                currencies=args.currency,
                q=args.search
            )
            if not posts:
                print("No stories found matching filters.")
                sys.exit(0)
            if HAS_RICH:
                # Render clean rich table
                table = Table(box=SIMPLE)
                table.add_column("Age", style="cyan")
                table.add_column("Title", style="bold white")
                table.add_column("Source", style="dim magenta")
                table.add_column("Coins", style="yellow")
                table.add_column("Votes")
                for post in posts[:args.limit]:
                    curr_codes = post.get("currencies_codes") or []
                    curr = f"[{','.join(curr_codes)}]" if curr_codes else ""
                    table.add_row(
                        format_relative_time(post.get("published_at")),
                        post.get("title"),
                        post.get("domain"),
                        curr,
                        format_votes(post.get("active_votes"))
                    )
                console.print(table)
            else:
                print_simple_table(posts, limit=args.limit)
        except Exception as e:
            print(f"Error fetching posts: {e}")
        sys.exit(0)

    # Interactive TUI loop
    if not HAS_RICH:
        print("Rich library is required for interactive mode. Run: pip install rich")
        sys.exit(1)

    feed = args.feed
    filter_type = args.filter
    currencies = args.currency
    q = args.search
    
    posts = []
    
    # Initial load
    try:
        with console.status("[bold green]Loading latest crypto news..."):
            posts = fetch_posts(csrf_token, feed, filter_type, currencies, q)
    except Exception as e:
        console.print(f"[red]Error fetching news: {e}[/red]")
        sys.exit(1)

    while True:
        render_interactive_dashboard(console, posts, feed, filter_type, currencies, q)
        try:
            cmd = input("Choice: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break
            
        if not cmd:
            continue
            
        cmd_lower = cmd.lower()
        
        # Quit
        if cmd_lower in ("q", "quit", "exit"):
            console.clear()
            console.print("[bold green]Thanks for using CryptoPanic CLI! Goodbye.[/bold green]")
            break
            
        # Refresh
        elif cmd_lower == "r":
            try:
                with console.status("[bold green]Refreshing..."):
                    posts = fetch_posts(csrf_token, feed, filter_type, currencies, q)
            except Exception as e:
                console.print(f"[red]Refresh failed: {e}[/red]")
                input("Press Enter to continue...")
                
        # Filter Currency
        elif cmd_lower.startswith("f"):
            parts = cmd.split(" ", 1)
            if len(parts) > 1:
                currencies = parts[1].strip().upper()
                if not currencies:
                    currencies = None
            else:
                currencies = None
            try:
                with console.status(f"[bold green]Filtering currency '{currencies}'..."):
                    posts = fetch_posts(csrf_token, feed, filter_type, currencies, q)
            except Exception as e:
                console.print(f"[red]Filter failed: {e}[/red]")
                input("Press Enter to continue...")

        # Filter Sentiment / Type
        elif cmd_lower.startswith("c"):
            parts = cmd_lower.split(" ", 1)
            if len(parts) > 1:
                filter_type = parts[1].strip()
                if not filter_type:
                    filter_type = None
            else:
                filter_type = None
            try:
                with console.status(f"[bold green]Filtering sentiment '{filter_type}'..."):
                    posts = fetch_posts(csrf_token, feed, filter_type, currencies, q)
            except Exception as e:
                console.print(f"[red]Filter failed: {e}[/red]")
                input("Press Enter to continue...")

        # Search Query
        elif cmd_lower.startswith("s"):
            parts = cmd.split(" ", 1)
            if len(parts) > 1:
                q = parts[1].strip()
                if not q:
                    q = None
            else:
                q = None
            try:
                with console.status(f"[bold green]Searching for '{q}'..."):
                    posts = fetch_posts(csrf_token, feed, filter_type, currencies, q)
            except Exception as e:
                console.print(f"[red]Search failed: {e}[/red]")
                input("Press Enter to continue...")

        # Feed type change
        elif cmd_lower.startswith("feed"):
            parts = cmd_lower.split(" ", 1)
            if len(parts) > 1:
                feed = parts[1].strip()
                if feed not in ("recent", "trending"):
                    feed = None
            else:
                feed = None
            try:
                with console.status(f"[bold green]Changing feed to '{feed or 'recent'}'..."):
                    posts = fetch_posts(csrf_token, feed, filter_type, currencies, q)
            except Exception as e:
                console.print(f"[red]Feed change failed: {e}[/red]")
                input("Press Enter to continue...")

        # Details View (if input is numeric)
        elif cmd.isdigit():
            idx = int(cmd) - 1
            if 0 <= idx < len(posts):
                display_post_details(console, posts[idx])
            else:
                console.print("[red]Invalid index![/red]")
                input("Press Enter to continue...")
        else:
            console.print("[red]Unknown command![/red]")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()
