import json
import urllib.request

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
    queries = [
        "daily_market_overview",
        "macro_market_sentiment",
        "token_fundamental_due_diligence",
        "holder_distribution_analysis",
        "perpetuals_market_state",
        "liquidation_map_walls",
        "btc_cross_asset_correlation"
    ]
    
    print("Searching candidates for all target queries...")
    for q in queries:
        print(f"\n--- Query: {q} ---")
        res = call_mcp_tool("tools/call", {
            "name": "find_skill",
            "arguments": {"query": q}
        })
        if not res or "content" not in res:
            print("No response.")
            continue
            
        content_text = res["content"][0]["text"]
        try:
            skills_data = json.loads(content_text)
            candidates = skills_data.get("candidates", [])
            print(f"Found {len(candidates)} candidates:")
            for s in candidates[:3]:
                print(f"  * uniqueName: {s.get('uniqueName')}")
                print(f"    Description: {s.get('skillDescription')[:150]}...")
                print(f"    Input Schema: {json.dumps(s.get('inputSchema', {}), indent=2)}")
        except Exception as e:
            print("Error parsing search results:", str(e))

if __name__ == "__main__":
    main()
