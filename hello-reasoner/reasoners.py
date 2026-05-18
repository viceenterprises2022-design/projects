import asyncio
from pydantic import BaseModel
from agentfield import AgentRouter

router = AgentRouter(prefix="", tags=["demo"])

class Personality(BaseModel):
    name: str
    vibe: str
    is_friendly: bool
    confident: bool

class GreetingResponse(BaseModel):
    message: str
    metadata: dict

@router.reasoner()
async def personality_shaper(user_input: str, model: str | None = None) -> Personality:
    """Analyze the user's input to determine what kind of personality to adopt."""
    return await router.ai(
        system="You are a social behaviorist. Categorize the user's vibe and assign a personality name.",
        user=user_input,
        schema=Personality,
        model=model
    )

@router.reasoner(tags=["entry"])
async def smart_greeter(user_name: str, message: str, model: str | None = None) -> GreetingResponse:
    """Entry reasoner: shapes a personality then generates a contextual greeting."""
    
    # 1. First cognitive step: Determine vibe
    persona_dict = await router.call(
        f"{router.node_id}.personality_shaper",
        user_input=message,
        model=model
    )
    persona = Personality(**persona_dict)
    
    # 2. Second cognitive step: Generate greeting based on vibe
    prompt = f"Adopt the persona '{persona.name}' with a '{persona.vibe}' vibe. Greet {user_name} who said: '{message}'"
    
    greeting_text = await router.ai(
        system="You are a flexible personality assistant.",
        user=prompt,
        model=model
    )
    
    return GreetingResponse(
        message=greeting_text,
        metadata={
            "persona_applied": persona.name,
            "vibe_detected": persona.vibe
        }
    )
