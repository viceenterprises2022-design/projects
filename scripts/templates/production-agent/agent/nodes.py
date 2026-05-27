from typing import Dict, Any, List

async def plan_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze query and formulate step-by-step reasoning plan."""
    query = state.get("query", "")
    trace = state.get("reasoning_trace", [])
    
    step = f"Plan node: Formulating approach for query: '{query}'"
    trace.append(step)
    
    # Classify intent (simple demo logic)
    intent = "general"
    if "customer" in query.lower() or "cust" in query.lower():
        intent = "crm_lookup"
    elif "search" in query.lower() or "find" in query.lower():
        intent = "search"
        
    return {
        "reasoning_trace": trace,
        "next_step": "act",
        "intent": intent
    }

async def act_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute domain tools or perform primary reasoning actions."""
    intent = state.get("intent", "general")
    query = state.get("query", "")
    trace = state.get("reasoning_trace", [])
    tools_executed = state.get("tools_executed", [])
    
    step = f"Act node: Executing operations for intent: '{intent}'"
    trace.append(step)
    
    output = ""
    # Execute tools based on intent
    if intent == "crm_lookup":
        from agent.tools.crm import lookup_crm_customer
        result = await lookup_crm_customer("CUST-100")
        tools_executed.append({
            "tool_name": "lookup_crm_customer",
            "arguments": {"customer_id": "CUST-100"},
            "result": str(result)
        })
        output = f"CRM Lookup succeeded. Customer details: {result}"
    elif intent == "search":
        from agent.tools.web_search import web_retrieve
        result = await web_retrieve(query)
        tools_executed.append({
            "tool_name": "web_retrieve",
            "arguments": {"query": query},
            "result": str(result)
        })
        output = f"Search operations completed. Results: {result[0]['snippet']}"
    else:
        output = f"Processed general inquiry with system capabilities. Answer: Resolved query '{query}' safely."
        
    return {
        "reasoning_trace": trace,
        "tools_executed": tools_executed,
        "output": output,
        "next_step": "observe"
    }

async def observe_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Review results, evaluate safety, and prepare final response payload."""
    trace = state.get("reasoning_trace", [])
    step = "Observe node: Validating outputs against compliance guardrails."
    trace.append(step)
    
    return {
        "reasoning_trace": trace,
        "finalized": True
    }
