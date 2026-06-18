import os
from agentfield import AgentRouter
from .models import FinalReport

NODE_ID = os.getenv("AGENT_NODE_ID", "vc-deepdive")
committee_router = AgentRouter(prefix="", tags=["committee"])

@committee_router.reasoner()
async def report_synthesizer(
    deals_prose: str,
    model: str | None = None,
) -> FinalReport:
    """
    Synthesizes regional investment findings into a structured markdown report.
    Groups startups sector-wise and categorizes their details.
    """
    system_prompt = (
        "You are a principal research director at a top venture capital firm. "
        "Your task is to synthesize startup funding deals across Asia, US, Europe, and Africa "
        "into a comprehensive, premium-grade market intelligence report.\n\n"
        "You must:\n"
        "1. Write a high-level overall summary of current venture trends.\n"
        "2. Structure the main report SECTOR-WISE. Group startups under clear sector headings "
        "(e.g. AI & Machine Learning, Cybersecurity, FinTech, SaaS, Logistics, ClimateTech).\n"
        "3. Within each sector, list the startups and detail:\n"
        "   - Startup Name and Region\n"
        "   - Funding Round & Amount\n"
        "   - Backing VC / Seed Fund\n"
        "   - Technology/Service details (brief)\n"
        "   - Startup Financials (ARR, Profit/Loss, CAGR growth)\n"
        "   - Investment Rationale (why the VC is investing)\n"
        "4. Use a polished, professional markdown table or structured list format for readability.\n"
        "5. Emphasize why these sectors and tech solutions are getting funded."
    )

    user_prompt = (
        f"Here are the venture capital and seed fund investment deals collected across regions:\n\n"
        f"{deals_prose}\n\n"
        f"Please organize and synthesize this data into the FinalReport format."
    )

    result = await committee_router.ai(
        system=system_prompt,
        user=user_prompt,
        schema=FinalReport,
        model=model,
    )
    return result
