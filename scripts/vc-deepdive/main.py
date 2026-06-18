"""VC & Seed Fund Daily Deep Dive Pipeline.

Entry reasoner: `vc-deepdive.deep_dive_vc`
Architecture:   Parallel Hunters + Reasoner Composition Cascade
"""
import asyncio
import os
from typing import List

from agentfield import Agent, AIConfig
from reasoners.models import RegionPlan, RegionalResearchResult, FinalReport, InvestmentDeal
from reasoners.helpers import render_deals_prose
from reasoners import committee_router, specialists_router

app = Agent(
    node_id=os.getenv("AGENT_NODE_ID", "vc-deepdive"),
    agentfield_server=os.getenv("AGENTFIELD_SERVER", "http://localhost:8080"),
    version="1.0.0",
    ai_config=AIConfig(
        # Default model recommended by doctor
        model=os.getenv("AI_MODEL", "google/gemini-2.5-flash"),
    ),
    dev_mode=True,
)

# Include routers
app.include_router(committee_router)
app.include_router(specialists_router)

# ---- Intake Router Reasoner ----
@app.reasoner()
async def intake_router(
    regions: List[str],
    model: str | None = None,
) -> RegionPlan:
    """
    Intake router that validates the requested regions and ensures they are mapped.
    """
    system_prompt = (
        "You are an intake routing agent. Validate the list of regions for the venture capital deep dive.\n"
        "Filter out any invalid regions. We support: 'asia', 'us', 'europe', 'africa'."
    )
    user_prompt = f"Requested regions: {regions}"
    
    result = await app.ai(
        system=system_prompt,
        user=user_prompt,
        schema=RegionPlan,
        model=model,
    )
    if not result.confident or not result.regions:
        # Fallback to all regions
        result.regions = ["asia", "us", "europe", "africa"]
    return result


# ---- Entry Reasoner ----
@app.reasoner(tags=["entry"])
async def deep_dive_vc(
    regions: List[str] = ["asia", "us", "europe", "africa"],
    model: str | None = None,
) -> dict:
    """
    Orchestrates the end-to-end VC & Seed Fund deep dive.
    1. Call intake_router to validate and plan.
    2. Fan-out regional_researcher in parallel for each region.
    3. Collect and serialize deals.
    4. Call report_synthesizer to group sector-wise and produce the markdown report.
    """
    # 1. Run intake router
    plan_dict = await app.call(
        f"{app.node_id}.intake_router",
        regions=regions,
        model=model,
    )
    plan = RegionPlan(**plan_dict)

    # 2. Parallel regional researchers fan-out
    research_tasks = [
        app.call(
            f"{app.node_id}.regional_researcher",
            region=r,
            model=model,
        )
        for r in plan.regions
    ]
    
    research_dicts = await asyncio.gather(*research_tasks)
    
    # 3. Consolidate all deals
    all_deals = []
    for r_dict in research_dicts:
        r_result = RegionalResearchResult(**r_dict)
        if r_result.confident:
            all_deals.extend(r_result.deals)

    # Convert to serialized prose list to avoid passing complex dicts / Pydantic models directly
    # and to feed clean natural language to the synthesizer
    all_deals_dicts = [d.model_dump() for d in all_deals]
    deals_prose = render_deals_prose(all_deals_dicts)

    # 4. Synthesize final report
    report_dict = await app.call(
        f"{app.node_id}.report_synthesizer",
        deals_prose=deals_prose,
        model=model,
    )
    report = FinalReport(**report_dict)

    return {
        "regions_analyzed": plan.regions,
        "total_deals_found": len(all_deals),
        "summary": report.summary,
        "report_md": report.report_md,
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8001")), auto_port=False)
