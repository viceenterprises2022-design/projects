from typing import Dict, Any, List
from agent.nodes import plan_node, act_node, observe_node

async def run_agent_graph(session_id: str, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    state = {
        "session_id": session_id,
        "query": query,
        "context": context,
        "intent": "general",
        "reasoning_trace": [],
        "tools_executed": [],
        "output": "",
        "finalized": False
    }
    
    # Run pipeline
    state.update(await plan_node(state))
    state.update(await act_node(state))
    state.update(await observe_node(state))
    
    return {
        "output": state["output"],
        "reasoning_trace": state["reasoning_trace"],
        "tools_executed": state["tools_executed"]
    }
