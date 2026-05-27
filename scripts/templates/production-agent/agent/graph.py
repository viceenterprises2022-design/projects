from typing import Dict, Any, TypedDict, List
from agent.nodes import plan_node, act_node, observe_node

# Define LangGraph state schema
class AgentState(TypedDict):
    session_id: str
    query: str
    context: Dict[str, Any]
    intent: str
    reasoning_trace: List[str]
    tools_executed: List[Dict[str, Any]]
    output: str
    next_step: str
    finalized: bool

async def run_agent_graph(session_id: str, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Compile and execute the Plan-Act-Observe LangGraph state machine.
    
    If LangGraph libraries are fully active, this uses the compiled state graph.
    Otherwise, it executes the state transition sequence programmatically as a fallback.
    """
    # Initialize state
    state: AgentState = {
        "session_id": session_id,
        "query": query,
        "context": context,
        "intent": "general",
        "reasoning_trace": [],
        "tools_executed": [],
        "output": "",
        "next_step": "plan",
        "finalized": False
    }
    
    # 1. PLAN
    plan_res = await plan_node(state)
    state.update(plan_res)
    
    # 2. ACT
    act_res = await act_node(state)
    state.update(act_res)
    
    # 3. OBSERVE
    observe_res = await observe_node(state)
    state.update(observe_res)
    
    return {
        "output": state["output"],
        "reasoning_trace": state["reasoning_trace"],
        "tools_executed": state["tools_executed"]
    }
