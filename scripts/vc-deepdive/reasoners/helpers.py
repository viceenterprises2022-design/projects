import os
import requests
from typing import List, Dict, Any
from .models import InvestmentDeal, StartupDetails, StartupFinancials, RegionalResearchResult

def search_deals_exa(region: str, limit: int = 5) -> str:
    """
    Search recent startup funding and venture capital deals for a region using Exa.
    Returns a concatenated text block of the results.
    """
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        print("EXA_API_KEY not found in environment. Using fallback mock data.")
        return get_mock_exa_data(region)

    headers = {
        "x-api-key": api_key,
        "content-type": "application/json"
    }

    # Format the query to fetch recent investment news
    query = f"recent startup venture capital seed fund investments in {region} rounds ARR Profit CAGR"
    
    payload = {
        "query": query,
        "useAutoprompt": True,
        "numResults": limit,
        "contents": {
            "text": {
                "maxCharacters": 3000
            }
        }
    }

    try:
        response = requests.post("https://api.exa.ai/search", json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        
        if not results:
            return f"No search results returned from Exa for region: {region}."
            
        text_blocks = []
        for r in results:
            title = r.get("title", "No Title")
            url = r.get("url", "No URL")
            text = r.get("text") or ""
            text_blocks.append(f"Source: {title} ({url})\nContent:\n{text}\n---")
            
        return "\n\n".join(text_blocks)
    except Exception as e:
        print(f"Exa search failed for {region}: {e}. Using mock data.")
        return get_mock_exa_data(region)

def get_mock_exa_data(region: str) -> str:
    """Mock VC investment data for regions when Exa is missing or fails."""
    mock_data = {
        "asia": """
Source: Tech In Asia (https://techinasia.com/deals-asia-2026)
Content:
Peak XV Partners lead a Series A round of $8M into Singapore-based AI startup NeuralNet. NeuralNet builds enterprise LLM routing solutions. The startup's ARR is currently estimated at $1.5M with a CAGR growth of 120%. Profit/Loss: currently unprofitable, - $200k. Rationale: Singapore's strategic location and NeuralNet's proprietary routing algorithm which cuts enterprise LLM API bills by 40%.
Another deal: East Ventures back Indonesian B2B SaaS startup TokoTech in a $2.5M Seed round. TokoTech provides inventory management tech for mom-and-pop shops. TokoTech CAGR: 85%, ARR: $450k, Profit: close to breakeven, $5k.
""",
        "us": """
Source: TechCrunch (https://techcrunch.com/deals-us-2026)
Content:
Andreessen Horowitz (a16z) led a $15M Series B round for San Francisco-based cybersecurity firm VaultGate. VaultGate provides post-quantum cryptography services. Rationale: rising threats to standard encryption from quantum computing advancement. VaultGate ARR: $6.2M, CAGR: 95%, Profit: - $1.2M due to heavy R&D investment.
Also, Y Combinator backs seed round for DevFlow, a developer platform automating CI/CD pipelines. DevFlow seed round: $1.8M. ARR: $200k, CAGR: 150%, Profit: - $50k.
""",
        "europe": """
Source: Sifted (https://sifted.eu/deals-europe-2026)
Content:
Index Ventures led a $12M Series A round for London-based climate fintech startup CarbonLedger. CarbonLedger provides carbon accounting SaaS to manufacturing companies. CarbonLedger ARR: $3.1M, CAGR: 70%, Profit: $150k. Rationale: compliance pressure from European union sustainability directives.
Another deal: Cherry Ventures backed Berlin-based healthtech startup MedMatch with a $3.5M Seed round. MedMatch matches patients to clinical trials. ARR: $800k, CAGR: 110%, Profit: - $100k.
""",
        "africa": """
Source: Disrupt Africa (https://disrupt-africa.com/deals-africa-2026)
Content:
TLcom Capital led a $4.5M Series A for Lagos-based logistics startup SendStack. SendStack provides last-mile delivery services for e-commerce vendors across Nigeria. ARR: $1.8M, CAGR: 65%, Profit: $80k. Rationale: infrastructure bottlenecks in urban Nigeria and growing e-commerce demand.
Also, Launch Africa Ventures backed Cape Town-based fintech startup PaySafe in a $1.2M Seed round. PaySafe is developing API gateways for regional mobile money integration. ARR: $500k, CAGR: 80%, Profit: $12k.
"""
    }
    return mock_data.get(region.lower(), f"No mock data available for region: {region}")

def fallback_deal(vc_name: str, region: str, startup_name: str) -> InvestmentDeal:
    """Return a safe-default InvestmentDeal."""
    return InvestmentDeal(
        vc_name=vc_name,
        region=region,
        startup=StartupDetails(
            startup_name=startup_name,
            round="N/A",
            funding_amount="N/A",
            sector="General",
            tech_description="N/A",
            financials=StartupFinancials(arr="N/A", profit="N/A", cagr="N/A")
        ),
        investment_reason="Failed to analyze deal details confidently.",
        confident=False
    )

def fallback_regional_research(region: str) -> RegionalResearchResult:
    """Return a safe-default RegionalResearchResult."""
    return RegionalResearchResult(
        region=region,
        deals=[],
        confident=False
    )

def render_deals_prose(deals: List[Dict[str, Any]]) -> str:
    """Format a list of raw deal dicts into a markdown prose list."""
    lines = []
    for d in deals:
        startup = d.get("startup", {})
        financials = startup.get("financials", {})
        lines.append(
            f"- **VC/Seed Fund**: {d.get('vc_name')}\n"
            f"  - **Region**: {d.get('region')}\n"
            f"  - **Startup**: {startup.get('startup_name')} ({startup.get('round')}, {startup.get('funding_amount')})\n"
            f"  - **Sector/Tech**: {startup.get('sector')} | {startup.get('tech_description')}\n"
            f"  - **Metrics**: ARR={financials.get('arr')}, Profit={financials.get('profit')}, CAGR={financials.get('cagr')}\n"
            f"  - **Investment Rationale**: {d.get('investment_reason')}"
        )
    return "\n".join(lines)
