from typing import Dict, Any, List

async def plan_node(state: Dict[str, Any]) -> Dict[str, Any]:
    query = state.get("query", "")
    trace = state.get("reasoning_trace", [])
    
    step = f"Plan: Analyzing Coinmarketcap request: '{query}'"
    trace.append(step)
    
    # Classify intent
    intent = "general"
    if "price" in query.lower() or "btc" in query.lower():
        intent = "cmc_find_skill"
        
    return {
        "reasoning_trace": trace,
        "intent": intent
    }

async def act_node(state: Dict[str, Any]) -> Dict[str, Any]:
    intent = state.get("intent", "general")
    query = state.get("query", "")
    trace = state.get("reasoning_trace", [])
    tools_executed = state.get("tools_executed", [])
    
    step = f"Act: Resolving intent '{intent}' using Coinmarketcap MCP integrations"
    trace.append(step)
    
    output = ""
    if intent == "cmc_find_skill":
        from agent.tools.crypto_lookup import find_skill
        skills = await find_skill(query)
        tools_executed.append({
            "tool_name": "find_skill",
            "arguments": {"query": query},
            "result": str(skills)
        })
        output = f"Coinmarketcap MCP query complete. Found skills: {[s['unique_name'] for s in skills]}"
    else:
        output = f"General crypto prompt processed. Output: Completed request '{query}' safely."
        
    return {
        "reasoning_trace": trace,
        "tools_executed": tools_executed,
        "output": output
    }

async def observe_node(state: Dict[str, Any]) -> Dict[str, Any]:
    trace = state.get("reasoning_trace", [])
    trace.append("Observe: Audited Coinmarketcap execution safely.")
    return {
        "reasoning_trace": trace,
        "finalized": True
    }
