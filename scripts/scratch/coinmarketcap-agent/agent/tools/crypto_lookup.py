import json
import urllib.request
import asyncio
from typing import List, Dict, Any

def sync_call_mcp_tool(method: str, params: dict) -> Any:
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

async def find_skill(query: str) -> List[Dict[str, Any]]:
    """Query Coinmarketcap Skill Hub MCP server using Streamable HTTP transport."""
    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(
        None,
        sync_call_mcp_tool,
        "tools/call",
        {"name": "find_skill", "arguments": {"query": query}}
    )
    
    if not res or "content" not in res:
        return []
        
    content_text = res["content"][0]["text"]
    try:
        skills_data = json.loads(content_text)
        return skills_data.get("candidates", [])
    except Exception as e:
        print("Error parsing skill search results:", str(e))
        return []

def sync_call_cmc_mcp(method: str, params: dict) -> Any:
    """Call the raw CMC MCP server (not skill-hub)."""
    url = "https://mcp.coinmarketcap.com/mcp"
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
            try:
                data = json.loads(res_data)
                if "result" in data:
                    return data["result"]
                if "error" in data:
                    return {"error": data["error"]}
            except json.JSONDecodeError:
                pass
            for line in res_data.split("\n"):
                line = line.strip()
                if line.startswith("data:"):
                    try:
                        line_data = json.loads(line[5:])
                        if "result" in line_data:
                            return line_data["result"]
                    except json.JSONDecodeError:
                        continue
            return None
    except Exception as e:
        print("CMC MCP Request Error:", str(e))
        return None


async def call_cmc_mcp(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Async wrapper for raw CMC MCP tool calls."""
    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(
        None, sync_call_cmc_mcp, "tools/call",
        {"name": tool_name, "arguments": arguments}
    )
    if not res:
        return {"status": "error", "message": "No response from CMC MCP"}
    return res


async def execute_skill(unique_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a specific CMC Skill via HTTP Streamable transport."""
    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(
        None,
        sync_call_mcp_tool,
        "tools/call",
        {
            "name": "execute_skill",
            "arguments": {
                "unique_name": unique_name,
                "parameters": parameters
            }
        }
    )
    
    if not res:
        return {"status": "error", "message": "No response from MCP"}
        
    return res
