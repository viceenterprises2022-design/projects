import time
import uvicorn
from fastapi import FastAPI, HTTPException
from app.config import settings
from app.models import UserQueryRequest, AgentResponse
from security.adrian_init import AdrianSecurityHarness
from agent.graph import run_agent_graph

app = FastAPI(title="Coinmarketcap Agent", version="0.1.0")
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

@app.post("/api/chat", response_model=AgentResponse)
async def chat_endpoint(request: UserQueryRequest):
    start_time = time.time()
    scrubbed_query = harness.scrub_input(request.query)
    
    # Layer 4 trace intent validation
    pre_eval = harness.analyze_intent(scrubbed_query)
    if pre_eval.get("action") == "BLOCK":
        raise HTTPException(status_code=403, detail=f"Security Block: {pre_eval.get('reason')}")
        
    try:
        res = await run_agent_graph(request.session_id, scrubbed_query, request.context or {})
        harness.audit_action("chat_lookup", {"query": scrubbed_query})
        duration_ms = (time.time() - start_time) * 1000
        
        return AgentResponse(
            session_id=request.session_id,
            output=res["output"],
            reasoning_trace=res.get("reasoning_trace", []),
            tools_executed=res.get("tools_executed", []),
            latency_ms=duration_ms
        )
    except Exception as e:
        harness.push_alert("high", f"Agent Error: {str(e)}", {"session_id": request.session_id})
        raise HTTPException(status_code=500, detail=str(e))
