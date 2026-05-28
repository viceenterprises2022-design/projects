from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class UserQueryRequest(BaseModel):
    session_id: str
    query: str
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ToolExecutionDetail(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[str] = None

class AgentResponse(BaseModel):
    session_id: str
    output: str
    reasoning_trace: Optional[List[str]] = None
    tools_executed: List[ToolExecutionDetail] = Field(default_factory=list)
    cost: float = 0.0
    latency_ms: float = 0.0
