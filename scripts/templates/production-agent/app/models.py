from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class UserQueryRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier for conversation persistence")
    query: str = Field(..., description="The input query for the agent to process")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata or external state payload")

class ToolExecutionDetail(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[str] = None

class AgentResponse(BaseModel):
    session_id: str
    output: str = Field(..., description="The agent's response content")
    reasoning_trace: Optional[List[str]] = Field(default=None, description="Steps or thoughts during graph execution")
    tools_executed: List[ToolExecutionDetail] = Field(default_factory=list)
    cost: float = Field(0.0, description="Estimated USD cost of the execution")
    latency_ms: float = Field(0.0, description="Total execution duration in milliseconds")
