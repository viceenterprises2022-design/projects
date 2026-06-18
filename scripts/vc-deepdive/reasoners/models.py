from pydantic import BaseModel, Field
from typing import List, Optional

class RegionPlan(BaseModel):
    regions: List[str] = Field(description="List of regions to analyze, e.g. ['asia', 'us', 'europe', 'africa']")
    confident: bool = Field(description="Confidence flag for intake routing")

class StartupFinancials(BaseModel):
    arr: Optional[str] = Field(default="N/A", description="ARR of the startup (e.g. '$5M', 'N/A')")
    profit: Optional[str] = Field(default="N/A", description="Profit/Loss of the startup (e.g. '$500K', 'N/A')")
    cagr: Optional[str] = Field(default="N/A", description="CAGR growth rate (e.g. '45%', 'N/A')")

class StartupDetails(BaseModel):
    startup_name: str = Field(description="Name of the startup")
    round: str = Field(description="Investment round (e.g. 'Seed', 'Series A')")
    funding_amount: str = Field(description="Funding amount (e.g. '$10M', 'N/A')")
    sector: str = Field(description="Primary sector (e.g. 'AI', 'Fintech', 'SaaS')")
    tech_description: str = Field(description="Brief description of the technology or service involved")
    financials: StartupFinancials = Field(description="Financial metrics like ARR, Profit, CAGR")

class InvestmentDeal(BaseModel):
    vc_name: str = Field(description="Name of the VC/Seed Fund")
    region: str = Field(description="Region of the investment")
    startup: StartupDetails = Field(description="Details of the startup invested in")
    investment_reason: str = Field(description="Why the VC is investing (rationale)")
    confident: bool = Field(description="Confidence flag for deal analysis")

class RegionalResearchResult(BaseModel):
    region: str = Field(description="Region name")
    deals: List[InvestmentDeal] = Field(description="List of investments found")
    confident: bool = Field(description="Confidence flag")

class FinalReport(BaseModel):
    summary: str = Field(description="Brief overall summary of the investment trend")
    report_md: str = Field(description="Full markdown report, structured by sector and region")
