import json
import urllib.request
import time
import os

def call_mcp_tool(method: str, params: dict):
    url = "https://mcp.coinmarketcap.com/skill-hub/stream"
    headers = {
        "X-CMC-MCP-API-KEY": "7f165fb95f174e6381a0d98391e1e53b",
        "Content-Type": "application/json"
    }
    
    req_body = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(req_body).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = response.read().decode("utf-8")
            result = None
            for line in res_data.split("\n"):
                if line.startswith("data:"):
                    line_data = json.loads(line[5:])
                    if "result" in line_data:
                        result = line_data["result"]
            if result is None:
                try:
                    line_data = json.loads(res_data)
                    if "result" in line_data:
                        result = line_data["result"]
                except:
                    pass
            return result
    except Exception as e:
        print("MCP Request Error:", str(e))
        return None

def main():
    skills_to_run = [
        {
            "name": "daily_market_overview",
            "params": {"preview": True},
            "file": "scratch/daily_market_overview_output.json"
        },
        {
            "name": "monitor_market_sentiment_shift",
            "params": {"preview": True},
            "file": "scratch/monitor_market_sentiment_shift_output.json"
        },
        {
            "name": "detect_protocol_revenue_tvl_divergence",
            "params": {"protocol": "Uniswap"},
            "file": "scratch/detect_protocol_revenue_tvl_divergence_output.json"
        },
        {
            "name": "detect_holder_distribution_trend",
            "params": {
                "token_id_or_symbol": "AAVE",
                "platform": "ethereum",
                "token_address": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"
            },
            "file": "scratch/detect_holder_distribution_trend_output.json"
        },
        {
            "name": "perp_contract_analysis",
            "params": {
                "symbol": "BTC",
                "timeframe": "4h",
                "lookback_days": 14,
                "exchange_list": "Binance,OKX,Bybit"
            },
            "file": "scratch/perp_analysis_output.json"
        },
        {
            "name": "detect_orderbook_wall_migration",
            "params": {"symbol": "BTC"},
            "file": "scratch/detect_orderbook_wall_migration_output.json"
        },
        {
            "name": "btc_cross_asset_correlation",
            "params": {"preview": True},
            "file": "scratch/cross_asset_analysis_output.json"
        }
    ]
    
    for idx, skill in enumerate(skills_to_run, 1):
        print(f"\n==================================================")
        print(f"[{idx}/7] Executing skill: {skill['name']}...")
        print(f"Parameters: {json.dumps(skill['params'], indent=2)}")
        print(f"==================================================")
        
        # Skip if already cached recently to save time and API quota, unless requested otherwise
        # (We will execute to guarantee fresh data)
        res = call_mcp_tool("tools/call", {
            "name": "execute_skill",
            "arguments": {
                "unique_name": skill["name"],
                "parameters": skill["params"]
            }
        })
        
        if not res:
            print(f"[ERROR] Failed to run {skill['name']}.")
            continue
            
        with open(skill["file"], "w") as f:
            json.dump(res, f, indent=2)
        print(f"[SUCCESS] Saved results to {skill['file']}")
        
        # Optional: Print conclusion/summary to stdout
        try:
            text = res["content"][0]["text"]
            data = json.loads(text)
            # Handle possible nested results
            if "result" in data and "output" in data["result"]:
                inner = json.loads(data["result"]["output"])
                data = inner
                
            report_data = data.get("result", {}).get("data", {})
            if not report_data:
                report_data = data.get("data", {})
                
            decision = report_data.get("decision_report", {})
            if not decision:
                decision = report_data.get("report", {})
                
            print(f"Conclusion: {decision.get('conclusion', report_data.get('summary', 'No summary available.'))}")
        except Exception as e:
            print(f"Info: Output is raw binary/dict ({e}).")
            
        time.sleep(2)  # Politeness delay

if __name__ == "__main__":
    main()
