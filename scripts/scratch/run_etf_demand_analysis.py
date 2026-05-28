import json
import urllib.request
import sys

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
    print("Step 1: Finding skill 'btc_etf_institutional_demand'...")
    find_res = call_mcp_tool("tools/call", {
        "name": "find_skill",
        "arguments": {
            "query": "btc_etf_institutional_demand"
        }
    })
    
    if not find_res or "content" not in find_res:
        print("Error: Could not retrieve skills from MCP.")
        sys.exit(1)
        
    content_text = find_res["content"][0]["text"]
    try:
        skills_data = json.loads(content_text)
    except Exception as e:
        print("Error parsing skill search results:", str(e))
        print("Raw text:", content_text)
        sys.exit(1)
        
    candidates = skills_data.get("candidates", [])
    print(f"Found {len(candidates)} candidates.")
    
    target_skill = None
    for cand in candidates:
        name = cand.get("uniqueName", "")
        if "btc_etf_institutional_demand" in name.lower() or "etf" in name.lower():
            target_skill = cand
            break
            
    if not target_skill:
        print("\n[FAILURE] Skill 'btc_etf_institutional_demand' not found in CMC Skill Hub.")
        print("Alternatives:")
        for cand in candidates[:3]:
            print(f"- {cand.get('uniqueName')}: {cand.get('skillDescription')}")
        sys.exit(1)
        
    unique_name = target_skill["uniqueName"]
    description = target_skill["skillDescription"]
    schema = target_skill.get("inputSchema", {})
    
    print(f"\nTarget Skill Found:")
    print(f"  Unique Name: {unique_name}")
    print(f"  Description: {description}")
    print(f"  Input Schema: {json.dumps(schema, indent=2)}")
    
    # Construct parameters from input schema
    user_params = {
        "preview": True
    }
    
    exec_params = {}
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    for prop_name, prop_def in properties.items():
        matched_key = None
        for k in user_params.keys():
            if k.lower() == prop_name.lower():
                matched_key = k
                break
        
        if matched_key:
            val = user_params[matched_key]
            # Handle types
            prop_type = prop_def.get("type", "string")
            if prop_type == "boolean" and not isinstance(val, bool):
                val = str(val).lower() == "true"
            exec_params[prop_name] = val
        elif prop_name in required:
            if "default" in prop_def:
                exec_params[prop_name] = prop_def["default"]
            elif "const" in prop_def:
                exec_params[prop_name] = prop_def["const"]
            else:
                print(f"\n[ERROR] Required parameter '{prop_name}' is missing.")
                sys.exit(1)
        else:
            if "default" in prop_def:
                exec_params[prop_name] = prop_def["default"]
                
    print(f"\nPrepared Execution Parameters: {json.dumps(exec_params, indent=2)}")
    
    print("\nStep 2: Executing skill...")
    exec_res = call_mcp_tool("tools/call", {
        "name": "execute_skill",
        "arguments": {
            "unique_name": unique_name,
            "parameters": exec_params
        }
    })
        
    if not exec_res:
        print("\n[FAILURE] Execution of skill returned empty response.")
        sys.exit(1)
        
    print("\nExecution Response:")
    print(json.dumps(exec_res, indent=2))
    
    # Save the output to scratch directory
    with open("scratch/etf_demand_analysis_output.json", "w") as f:
        json.dump(exec_res, f, indent=2)
    print("\nSaved execution results to scratch/etf_demand_analysis_output.json")

if __name__ == "__main__":
    main()
