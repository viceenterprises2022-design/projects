import time
import uvicorn
from fastapi import FastAPI, HTTPException
from app.config import settings
from app.models import UserQueryRequest, AgentResponse
from security.adrian_init import AdrianSecurityHarness
from agent.graph import run_agent_graph

app = FastAPI(
    title=f"{settings.AGENT_NAME} API Gateway",
    description="Production-grade AI Agent with 8-layer Runtime Defense Harness",
    version="0.1.0"
)

# Adrian 2-line security wrap setup
harness = AdrianSecurityHarness(
    api_key=settings.ADRIAN_API_KEY,
    mode=settings.SECURITY_MODE,
    pii_scrub=settings.PII_SCRUB_ENABLED
)

@app.on_event("startup")
async def startup_event():
    harness.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    harness.shutdown()

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "agent": settings.AGENT_NAME,
        "security_mode": settings.SECURITY_MODE,
        "harness_active": harness.is_active
    }

@app.post("/api/chat", response_model=AgentResponse)
async def chat_endpoint(request: UserQueryRequest):
    start_time = time.time()
    
    # Layer 3: Scrub PII from input before processing
    scrubbed_query = harness.scrub_input(request.query)
    
    # Layer 4: Analyze reasoning trace & input intent pre-execution
    pre_eval = harness.analyze_intent(scrubbed_query)
    if pre_eval.get("action") == "BLOCK":
        raise HTTPException(
            status_code=403,
            detail=f"Security Violations Triggered: {pre_eval.get('reason')}"
        )
    
    try:
        # Run agent graph execution
        result = await run_agent_graph(
            session_id=request.session_id,
            query=scrubbed_query,
            context=request.context or {}
        )
        
        # Layer 8: Audit and log actions
        harness.audit_action(
            action="graph_execution",
            payload={"query": scrubbed_query, "result": result["output"]}
        )
        
        duration_ms = (time.time() - start_time) * 1000
        
        return AgentResponse(
            session_id=request.session_id,
            output=result["output"],
            reasoning_trace=result.get("reasoning_trace", []),
            tools_executed=result.get("tools_executed", []),
            cost=result.get("cost", 0.0012),
            latency_ms=duration_ms
        )
        
    except Exception as e:
        harness.push_alert(
            severity="high",
            message=f"Agent runtime failure: {str(e)}",
            payload={"session_id": request.session_id, "query": scrubbed_query}
        )
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=(settings.ENV == "development")
    )
