import os
import asyncio
from agentfield import AgentRouter
from pydantic import BaseModel, Field
from typing import List, Optional

from .models import InvestmentDeal, StartupDetails, StartupFinancials, RegionalResearchResult
from .helpers import search_deals_exa, fallback_deal, fallback_regional_research

# We read the node ID from the environment. Canonical fallback is 'vc-deepdive'
NODE_ID = os.getenv("AGENT_NODE_ID", "vc-deepdive")

specialists_router = AgentRouter(prefix="", tags=["specialist"])

# ---- Inner schemas for extraction ----
class DealCandidate(BaseModel):
    vc_name: str = Field(description="Name of the VC/Seed Fund")
    startup_name: str = Field(description="Name of the startup")

class DealCandidatesList(BaseModel):
    candidates: List[DealCandidate] = Field(description="List of VC/startup investment deal candidates found in text")
    confident: bool = Field(description="Whether the candidates were extracted confidently")

class RawDealDetails(BaseModel):
    round: str = Field(description="Investment round, e.g. Seed, Series A, Series B")
    funding_amount: str = Field(description="Funding amount, e.g. $5M, $10M, or N/A")
    sector: str = Field(description="Primary sector, e.g. AI, Fintech, CleanTech")
    tech_description: str = Field(description="1-2 sentences about the technology or service")
    investment_reason: str = Field(description="Investment rationale / why the VC is investing")
    confident: bool = Field(description="Whether details were extracted confidently")


# ---- Specialists ----

@specialists_router.reasoner()
async def metric_estimator(
    startup_name: str,
    context_text: str,
    model: str | None = None,
) -> StartupFinancials:
    """
    Reasoner to specifically focus on extracting/estimating startup financial metrics (ARR, Profit, CAGR).
    """
    system_prompt = (
        f"You are a startup financial forensics analyst. Your job is to extract or estimate "
        f"financial metrics for '{startup_name}' from the provided text context.\n"
        f"If metrics are not explicitly stated, estimate realistic ones based on the startup's "
        f"funding round and sector, or return 'N/A' if estimation is not possible.\n"
        f"Provide ARR (Annual Recurring Revenue), Profit/Loss, and CAGR (Compound Annual Growth Rate)."
    )
    
    user_prompt = f"Startup: {startup_name}\nContext:\n{context_text}"
    
    result = await specialists_router.ai(
        system=system_prompt,
        user=user_prompt,
        schema=StartupFinancials,
        model=model,
    )
    return result

@specialists_router.reasoner()
async def deal_analyzer(
    vc_name: str,
    startup_name: str,
    context_text: str,
    region: str,
    model: str | None = None,
) -> InvestmentDeal:
    """
    Reasoner to analyze a specific investment deal using the search context.
    Calls metric_estimator to extract financial metrics.
    """
    system_prompt = (
        f"You are an investment analyst checking VC deals in {region}.\n"
        f"Extract deal details for VC '{vc_name}' investing in '{startup_name}' from the context.\n"
        f"Provide the round, funding amount, primary sector, tech description, and investment reason."
    )
    
    user_prompt = f"VC: {vc_name}\nStartup: {startup_name}\nContext:\n{context_text}"
    
    # Extract raw deal details
    details = await specialists_router.ai(
        system=system_prompt,
        user=user_prompt,
        schema=RawDealDetails,
        model=model,
    )
    
    if not details.confident:
        return fallback_deal(vc_name, region, startup_name)
        
    # Call downstream reasoner to estimate financials
    # Note: app.call always returns dict. Convert manually.
    financials_dict = await specialists_router.call(
        f"{NODE_ID}.metric_estimator",
        startup_name=startup_name,
        context_text=context_text,
        model=model,
    )
    financials = StartupFinancials(**financials_dict)
    
    return InvestmentDeal(
        vc_name=vc_name,
        region=region,
        startup=StartupDetails(
            startup_name=startup_name,
            round=details.round,
            funding_amount=details.funding_amount,
            sector=details.sector,
            tech_description=details.tech_description,
            financials=financials
        ),
        investment_reason=details.investment_reason,
        confident=True
    )

@specialists_router.reasoner()
async def regional_researcher(
    region: str,
    model: str | None = None,
) -> RegionalResearchResult:
    """
    Orchestrates research for a specific region.
    1. Runs Exa search for the region.
    2. Identifies deal candidates in search results.
    3. Spawns deal_analyzer in parallel for each candidate.
    """
    # 1. Search Exa
    search_text = search_deals_exa(region)
    
    # 2. Extract deal candidates from search text
    system_prompt = (
        f"You are a venture capital research manager focusing on the {region} region.\n"
        f"Analyze the search text and list all VC / Seed fund investment deal candidates.\n"
        f"For each deal, extract the VC name and the startup name."
    )
    
    candidates_list = await specialists_router.ai(
        system=system_prompt,
        user=search_text,
        schema=DealCandidatesList,
        model=model,
    )
    
    if not candidates_list.confident or not candidates_list.candidates:
        # Return fallback result
        return fallback_regional_research(region)
        
    # Limit to top 5 candidates to prevent token explosion or run timeout
    candidates = candidates_list.candidates[:5]
    
    # 3. Parallel fan-out to deal_analyzer for each candidate
    # Pass plain data across serialization boundary
    deal_tasks = [
        specialists_router.call(
            f"{NODE_ID}.deal_analyzer",
            vc_name=c.vc_name,
            startup_name=c.startup_name,
            context_text=search_text,
            region=region,
            model=model,
        )
        for c in candidates
    ]
    
    deals_dicts = await asyncio.gather(*deal_tasks)
    
    # Reconstruct InvestmentDeal objects
    deals = [InvestmentDeal(**d) for d in deals_dicts]
    
    return RegionalResearchResult(
        region=region,
        deals=deals,
        confident=True
    )
