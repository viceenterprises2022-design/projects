#!/usr/bin/env python3
import os
import re
import json
import subprocess
import ast
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.resolve()
SYSTEMD_USER_DIR = Path.home() / ".config" / "systemd" / "user"

# Hardcoded script-to-product mapping for clear organization
PRODUCT_MAPPING = {
    # AlphaEdge Market Intelligence (Indian Indices)
    "collector.py": "AlphaEdge Market Intelligence",
    "alphaedge_db.py": "AlphaEdge Market Intelligence",
    "api_server.py": "AlphaEdge Market Intelligence",
    "market_analysis_v2.py": "AlphaEdge Market Intelligence",
    "market_analysis_v3.py": "AlphaEdge Market Intelligence",
    "oi_collector_daemon.py": "AlphaEdge Market Intelligence",
    "options_cli.py": "AlphaEdge Market Intelligence",
    "fo_breakout_scanner.py": "AlphaEdge Market Intelligence",
    "monitor_upstox.py": "AlphaEdge Market Intelligence",
    "probe_pcr_pain.py": "AlphaEdge Market Intelligence",
    "report_and_send.py": "AlphaEdge Market Intelligence",
    "run_analysis_headless.py": "AlphaEdge Market Intelligence",
    "run_and_send_v2.py": "AlphaEdge Market Intelligence",
    "start_collectors.sh": "AlphaEdge Market Intelligence",
    "nifty200_momentum.py": "AlphaEdge Market Intelligence",
    
    # AlphaEdge Crypto
    "crypto_market_dashboard.py": "AlphaEdge Crypto",
    "crypto_market_dashboard_v2.py": "AlphaEdge Crypto",
    "market_engine.py": "AlphaEdge Crypto",
    "metals_dashboard.py": "AlphaEdge Crypto",
    "cryptopanic_cli.py": "AlphaEdge Crypto",
    "paper_trading_engine.py": "AlphaEdge Crypto",
    "paper_trading_db.py": "AlphaEdge Crypto",
    
    # NotebookLM Research Pipelines
    "telegram_to_notebooklm.py": "NotebookLM Research Pipelines",
    "youtube_to_notebooklm.py": "NotebookLM Research Pipelines",
    "arxiv_to_notebooklm.py": "NotebookLM Research Pipelines",
    "toddle_notebooklm_sync.py": "NotebookLM Research Pipelines",
    "toddle_all_inventory.py": "NotebookLM Research Pipelines",
    "toddle_bulk_download.py": "NotebookLM Research Pipelines",
    "toddle_bulk_convert.py": "NotebookLM Research Pipelines",
    "toddle_download.py": "NotebookLM Research Pipelines",
    "toddle_upload_all.py": "NotebookLM Research Pipelines",
    "toddle_upload_physics.py": "NotebookLM Research Pipelines",
    "toddle_explore.py": "NotebookLM Research Pipelines",
    "toddle_extractor.py": "NotebookLM Research Pipelines",
    "toddle_inventory.py": "NotebookLM Research Pipelines",
    "toddle_physics_inventory.py": "NotebookLM Research Pipelines",
    "toddle_auth.py": "NotebookLM Research Pipelines",
    "toddle_config.py": "NotebookLM Research Pipelines",
    "toddle_convert.py": "NotebookLM Research Pipelines",
    "toddle_deep_inventory.py": "NotebookLM Research Pipelines",
    "crypto_to_notebooklm.py": "NotebookLM Research Pipelines",
    
    # Exa Event Search
    "exa_ai_search.py": "Exa Event Search",
    "exa_ai_agents.py": "Exa Event Search",
    "ai_news_reporter.py": "Exa Event Search",
    
    # Crypto Daily News Scanner
    "crypto_news_search.py": "Crypto Daily News Scanner",
    "crypto_intel_reporter.py": "Crypto Intel Reporter",
    
    # PKScreener NSE Scanner
    "pkscreener_runner.py": "PKScreener NSE Scanner",
    
    # Portfolio P&L Dashboard
    "pnl_poller.py": "Portfolio P&L Dashboard",
    
    # System Monitoring & Alerting
    "cron_watchdog.py": "System Monitoring & Alerting",
    "alert_dashboard_alive.py": "System Monitoring & Alerting",
    "send_slack.py": "System Monitoring & Alerting",
    "send_telegram_msg.py": "System Monitoring & Alerting",
    "debug_telegram.py": "System Monitoring & Alerting",
}

DEFAULT_PRODUCT = "Other Utilities"

def extract_strings_from_code(code_str):
    """Parses AST to find all string literals in a Python file."""
    strings = []
    try:
        tree = ast.parse(code_str)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                strings.append(node.value)
    except SyntaxError:
        # Fallback to simple regex if AST parsing fails (e.g. syntax differences)
        strings = re.findall(r"['\"](.*?)['\"]", code_str)
    return strings

def analyze_script(file_path):
    """Analyzes a script file for imports, database files, and network calls."""
    rel_path = file_path.relative_to(SCRIPTS_DIR)
    name = file_path.name
    
    metadata = {
        "id": name,
        "name": name,
        "path": str(rel_path),
        "product": PRODUCT_MAPPING.get(name, PRODUCT_MAPPING.get(file_path.parent.name + "/" + name, DEFAULT_PRODUCT)),
        "size_bytes": file_path.stat().st_size,
        "databases": [],
        "apis": [],
        "outputs": [],
        "imports": [],
        "cron_timings": [],
        "systemd_services": []
    }
    
    try:
        content = file_path.read_text(errors='ignore')
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return metadata
        
    # Extract imports
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name_node in node.names:
                    metadata["imports"].append(name_node.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    metadata["imports"].append(node.module)
    except SyntaxError:
        # regex fallback
        for imp in re.findall(r"^\s*(?:import|from)\s+(\w+)", content, re.MULTILINE):
            metadata["imports"].append(imp)
            
    # Remove standard library and external imports for visual clarity (keep local helper imports)
    local_imports = []
    for imp in set(metadata["imports"]):
        helper_py = SCRIPTS_DIR / f"{imp}.py"
        if helper_py.exists():
            local_imports.append(f"{imp}.py")
    metadata["imports"] = local_imports

    # Find string literals
    all_strings = extract_strings_from_code(content)
    
    # 1. Look for SQLite Databases (.db reference)
    for s in all_strings:
        db_match = re.search(r"(\w+\.db)", s)
        if db_match:
            metadata["databases"].append(db_match.group(1))
    metadata["databases"] = list(set(metadata["databases"]))
    
    # 2. Look for external API URLs and Polling Domains
    api_patterns = [
        (r"api\.upstox\.com", "Upstox API"),
        (r"binance\.com", "Binance API"),
        (r"deribit\.com", "Deribit API"),
        (r"googleapis\.com", "YouTube API"),
        (r"arxiv\.org", "arXiv RSS/HTML"),
        (r"toddle", "Toddle School Portal"),
        (r"mcp\.coinmarketcap\.com", "CoinMarketCap Hub"),
        (r"telegram\.org", "Telegram API"),
        (r"telethon", "Telegram API"),
        (r"yfinance", "Yahoo Finance"),
        (r"yf\.", "Yahoo Finance"),
        (r"fyers", "Fyers API"),
        (r"cryptopanic\.com", "CryptoPanic API"),
    ]
    
    for pattern, name_api in api_patterns:
        if re.search(pattern, content, re.IGNORECASE) or any(re.search(pattern, s, re.IGNORECASE) for s in all_strings):
            metadata["apis"].append(name_api)
    metadata["apis"] = list(set(metadata["apis"]))
    
    # 3. Look for Outputs
    output_patterns = [
        (r"SLACK_WEBHOOK|send_to_slack|send_slack", "Slack Workspace"),
        (r"telegram.*send|send_telegram|tg\.send", "Telegram Channel"),
        (r"notebooklm", "NotebookLM Reports"),
        (r"rich\.console|rich\.live|Console\(", "CLI Rich Terminal UI"),
        (r"strategies/.*momentum_report\.json", "Momentum Report JSON"),
    ]
    for pattern, name_out in output_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            metadata["outputs"].append(name_out)
    metadata["outputs"] = list(set(metadata["outputs"]))

    return metadata

def parse_cron_jobs():
    """Fetches and parses crontab configuration for schedule, command, and script."""
    cron_jobs = []
    try:
        r = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
        if r.returncode != 0:
            return cron_jobs
        
        for line in r.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            parts = line.split()
            if len(parts) < 6:
                continue
                
            schedule = " ".join(parts[:5])
            cmd = " ".join(parts[5:])
            
            # Identify Python script run by this cron
            script_match = re.search(r"(\w+\.py)", cmd)
            script_name = script_match.group(1) if script_match else None
            
            # Also handle subdirectories
            if not script_name:
                sub_match = re.search(r"(\w+/\w+\.py)", cmd)
                if sub_match:
                    script_name = sub_match.group(1).split("/")[-1]
            
            cron_jobs.append({
                "schedule": schedule,
                "command": cmd,
                "script_name": script_name
            })
    except Exception as e:
        print(f"Error parsing crontab: {e}")
    return cron_jobs

def parse_systemd_services():
    """Inspects repo and systemd directory for service definitions."""
    services = []
    
    # Check local repo service files
    local_services = list(SCRIPTS_DIR.glob("*.service"))
    # Check ~/.config/systemd/user
    user_services = []
    if SYSTEMD_USER_DIR.exists():
        user_services = list(SYSTEMD_USER_DIR.glob("*.service"))
        
    all_service_files = list(set(local_services + user_services))
    
    for f in all_service_files:
        try:
            content = f.read_text(errors='ignore')
            exec_start = ""
            desc = ""
            for line in content.splitlines():
                if line.startswith("ExecStart="):
                    exec_start = line.split("=", 1)[1]
                elif line.startswith("Description="):
                    desc = line.split("=", 1)[1]
                    
            script_match = re.search(r"(\w+\.py)", exec_start)
            script_name = script_match.group(1) if script_match else None
            
            services.append({
                "name": f.name,
                "description": desc or f.name,
                "command": exec_start,
                "script_name": script_name
            })
        except Exception as e:
            print(f"Error reading systemd service {f}: {e}")
            
    return services

def main():
    print("Starting Scripts Universe analysis...")
    
    # 1. Scan scripts
    scripts = []
    script_files = list(SCRIPTS_DIR.glob("*.py"))
    script_files += list((SCRIPTS_DIR / "strategies").glob("*.py"))
    
    for f in script_files:
        scripts.append(analyze_script(f))
        
    # 2. Extract Cron Schedules & map to scripts
    cron_jobs = parse_cron_jobs()
    for cron in cron_jobs:
        if cron["script_name"]:
            for script in scripts:
                if script["name"] == cron["script_name"]:
                    script["cron_timings"].append(cron["schedule"])
                    
    # 3. Extract Systemd Services & map to scripts
    services = parse_systemd_services()
    for svc in services:
        if svc["script_name"]:
            for script in scripts:
                if script["name"] == svc["script_name"]:
                    script["systemd_services"].append(svc["name"])

    # 4. Construct nodes and edges for network graph
    nodes = []
    edges = []
    
    # Track unique items to avoid duplicate nodes
    seen_nodes = set()
    
    # Add Product group nodes
    products = list(set(s["product"] for s in scripts))
    for prod in products:
        p_id = f"prod_{prod.lower().replace(' ', '_')}"
        nodes.append({
            "id": p_id,
            "label": prod,
            "group": "product",
            "title": f"Product Suite: {prod}"
        })
        seen_nodes.add(p_id)
        
    # Helper to safely add node
    def add_node(nid, label, group, title=""):
        if nid not in seen_nodes:
            nodes.append({
                "id": nid,
                "label": label,
                "group": group,
                "title": title or label
            })
            seen_nodes.add(nid)
            
    # Add all scripts, databases, apis, outputs, services
    for s in scripts:
        # Script Node
        script_title = f"Script: {s['name']}<br>Product: {s['product']}<br>Size: {s['size_bytes']:,} bytes"
        if s["cron_timings"]:
            script_title += f"<br>Cron Schedule: {', '.join(s['cron_timings'])}"
        if s["systemd_services"]:
            script_title += f"<br>Systemd: {', '.join(s['systemd_services'])}"
            
        add_node(s["name"], s["name"], "script", script_title)
        
        # Link script to product
        p_id = f"prod_{s['product'].lower().replace(' ', '_')}"
        edges.append({
            "from": s["name"],
            "to": p_id,
            "relation": "belongs_to",
            "label": "belongs to"
        })
        
        # Database Nodes & Links
        for db in s["databases"]:
            db_id = f"db_{db}"
            add_node(db_id, db, "database", f"SQLite Database: {db}")
            edges.append({
                "from": s["name"],
                "to": db_id,
                "relation": "reads_writes",
                "label": "uses"
            })
            
        # API/DataSource Nodes & Links
        for api in s["apis"]:
            api_id = f"api_{api.lower().replace(' ', '_')}"
            add_node(api_id, api, "datasource", f"External Data Source: {api}")
            edges.append({
                "from": s["name"],
                "to": api_id,
                "relation": "polls",
                "label": "polls"
            })
            
        # Output Nodes & Links
        for out in s["outputs"]:
            out_id = f"out_{out.lower().replace(' ', '_')}"
            add_node(out_id, out, "output", f"Builds Output: {out}")
            edges.append({
                "from": s["name"],
                "to": out_id,
                "relation": "builds",
                "label": "builds"
            })
            
        # Local Imports Links (Script dependencies)
        for imp in s["imports"]:
            edges.append({
                "from": s["name"],
                "to": imp,
                "relation": "imports",
                "label": "imports"
            })
            
        # Systemd service nodes & links
        for svc_name in s["systemd_services"]:
            svc_id = f"svc_{svc_name.replace('.', '_')}"
            svc_desc = next((x["description"] for x in services if x["name"] == svc_name), svc_name)
            add_node(svc_id, svc_name, "daemon", f"Systemd Daemon: {svc_desc}")
            edges.append({
                "from": svc_id,
                "to": s["name"],
                "relation": "runs",
                "label": "executes"
            })
            
    # Include cron jobs that run scripts
    for cron in cron_jobs:
        if cron["script_name"]:
            cron_id = f"cron_{cron['schedule'].replace(' ', '_').replace('*', 'x')}"
            cron_title = f"Cron Trigger: {cron['schedule']}<br>Command: {cron['command']}"
            add_node(cron_id, f"Cron: {cron['schedule']}", "trigger", cron_title)
            edges.append({
                "from": cron_id,
                "to": cron["script_name"],
                "relation": "triggers",
                "label": "triggers"
            })
            
    # Output file
    output_data = {
        "nodes": nodes,
        "edges": edges,
        "raw_scripts": scripts,
        "raw_cron": cron_jobs,
        "raw_services": services
    }
    
    output_path = SCRIPTS_DIR / "universe_data.json"
    output_path.write_text(json.dumps(output_data, indent=2))
    print(f"Analysis complete! Saved {len(nodes)} nodes and {len(edges)} edges to {output_path}")

if __name__ == "__main__":
    main()
