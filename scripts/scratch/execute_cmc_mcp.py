import json
import urllib.request

def call_mcp_tool(method: str, params: dict):
    url = "https://mcp.coinmarketcap.com/skill-hub/stream"
    headers = {
        "X-CMC-MCP-API-KEY": "7f165fb95f174e6381a0d98391e1e53b",
        "Content-Type": "application/json"
    }
    
    # We send standard JSON-RPC request for call or list
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
            # Streamable HTTP might return multiple json lines or standard JSON-RPC response
            print("Response Code:", response.status)
            print("Response Data:", res_data)
    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    print("--- Listing Tools ---")
    call_mcp_tool("tools/list", {})
    
    print("\n--- Finding Skill ---")
    call_mcp_tool("tools/call", {"name": "find_skill", "arguments": {"query": "btc price"}})
    
    print("\n--- Executing Skill ---")
    call_mcp_tool("tools/call", {"name": "execute_skill", "arguments": {"unique_name": "daily_market_overview", "parameters": {"preview": True}}})
