import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
from src.data.ingestion import EquityIngestion, CryptoIngestion

load_dotenv()

class TradingOrchestrator:
    """Main logic to coordinate multi-agent analysis."""
    def __init__(self, api_key=None):
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not set.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('models/gemini-pro-latest')

    def load_skill(self, skill_path):
        """Read the SKILL.md system instructions."""
        with open(skill_path, 'r') as f:
            return f.read()

    def analyze_equity(self, ticker):
        """Analyze a stock using multiple specialized agents."""
        ingestion = EquityIngestion(ticker)
        fundamental_data = ingestion.get_fundamentals()
        technical_data = ingestion.get_technical_data()

        # Step 1: Fundamental Agent
        fundamental_skill = self.load_skill("Financial_System_design/1-fundamental-analysis-SKILL.md")
        fundamental_analysis = self._call_agent(fundamental_skill, fundamental_data)

        # Step 2: Technical Agent
        technical_skill = self.load_skill("agents/common/technical-analysis-SKILL.md")
        technical_analysis = self._call_agent(technical_skill, technical_data)

        return {
            "ticker": ticker,
            "fundamental": fundamental_analysis,
            "technical": technical_analysis
        }

    def analyze_crypto(self, symbol):
        """Analyze a crypto asset using specialized agents."""
        ingestion = CryptoIngestion(symbol)
        market_data = ingestion.get_market_data()
        
        # In Phase 1, we use Market Data for Technical analysis
        # Placeholder for real on-chain/tokenomics data ingestion
        technical_data = {
            "ticker": symbol,
            "current_price": market_data['current_price'],
            "price_data": {
                "change_percent_1d": market_data['change_percent_24h'],
                "volume_24h": market_data['volume_24h']
            }
        }

        # Step 1: Technical Agent
        technical_skill = self.load_skill("agents/common/technical-analysis-SKILL.md")
        technical_analysis = self._call_agent(technical_skill, technical_data)

        # Step 2: Tokenomics (Placeholder data for demonstration)
        tokenomics_data = {
            "ticker": symbol.split('/')[0],
            "data_date": datetime.now().strftime("%Y-%m-%d"),
            "tokenomics": {
                "inflation_rate_annual": 1.5,
                "utility_mechanisms": ["gas_fees", "staking"]
            }
        }
        tokenomics_skill = self.load_skill("agents/crypto/1-tokenomics-analysis-SKILL.md")
        tokenomics_analysis = self._call_agent(tokenomics_skill, tokenomics_data)

        return {
            "ticker": symbol,
            "technical": technical_analysis,
            "tokenomics": tokenomics_analysis
        }

    def _call_agent(self, skill_text, data):
        """Invoke Gemini with agent instructions and specific data."""
        prompt = f"""
{skill_text}

---
INPUT DATA:
{json.dumps(data, indent=2)}
"""
        response = self.model.generate_content(prompt)
        try:
            # Clean up response to ensure it's pure JSON
            text = response.text.strip()
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception as e:
            return {"error": f"Failed to parse LLM response: {str(e)}", "raw": response.text}

if __name__ == "__main__":
    # Example flow
    # orchestrator = TradingOrchestrator()
    # report = orchestrator.analyze_equity("RELIANCE.NS")
    # print(json.dumps(report, indent=2))
    pass
