from typing import Dict, Any, List, TypedDict, Literal
from langgraph.graph import StateGraph, END
from agent.nodes import plan_node, act_node, observe_node


class AgentState(TypedDict):
    session_id: str
    query: str
    context: Dict[str, Any]
    intent: str
    reasoning_trace: List[str]
    tools_executed: List[Dict[str, Any]]
    output: str
    finalized: bool


def _route_from_plan(state: AgentState) -> Literal["act_node", "observe_node"]:
    if state["intent"] in ("general", "skill_hub") and state["intent"] != "skill_hub":
        return "observe_node"
    return "act_node"


_workflow = None


def _get_workflow() -> StateGraph:
    global _workflow
    if _workflow is not None:
        return _workflow

    builder = StateGraph(AgentState)
    builder.add_node("plan_node", plan_node)
    builder.add_node("act_node", act_node)
    builder.add_node("observe_node", observe_node)

    builder.set_entry_point("plan_node")

    builder.add_conditional_edges(
        "plan_node",
        _route_from_plan,
        {"act_node": "act_node", "observe_node": "observe_node"},
    )
    builder.add_edge("act_node", "observe_node")
    builder.add_edge("observe_node", END)

    _workflow = builder.compile()
    return _workflow


async def run_agent_graph(
    session_id: str, query: str, context: Dict[str, Any]
) -> Dict[str, Any]:
    app = _get_workflow()
    result = await app.ainvoke({
        "session_id": session_id,
        "query": query,
        "context": context,
        "intent": "general",
        "reasoning_trace": [],
        "tools_executed": [],
        "output": "",
        "finalized": False,
    })

    return {
        "output": result["output"],
        "reasoning_trace": result["reasoning_trace"],
        "tools_executed": result["tools_executed"],
    }
