import os
from agentfield import Agent, AIConfig
from reasoners import router

app = Agent(
    node_id=os.getenv("AGENT_NODE_ID", "hello-reasoner"),
    ai_config=AIConfig(
        model=os.getenv("AI_MODEL", "gemini-1.5-pro"),
    ),
    dev_mode=True,
)

app.include_router(router)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8001")), auto_port=False)
