import unittest
import asyncio
from agent.graph import run_agent_graph
from agent.nodes import _classify_intent
from agent.tools.cmc_mcp_tools import extract_symbol


class TestIntentClassifier(unittest.TestCase):
    def test_price_quote_intent(self):
        self.assertEqual(_classify_intent("What is BTC price?"), "price_quote")
        self.assertEqual(_classify_intent("eth rate now"), "price_quote")
        self.assertEqual(_classify_intent("how much is sol"), "price_quote")

    def test_ta_intent(self):
        self.assertEqual(_classify_intent("BTC RSI analysis"), "ta_analysis")
        self.assertEqual(_classify_intent("show MACD for ETH"), "ta_analysis")
        self.assertEqual(_classify_intent("technical indicators SOL"), "ta_analysis")

    def test_onchain_intent(self):
        self.assertEqual(_classify_intent("BTC holder count"), "onchain")
        self.assertEqual(_classify_intent("active addresses on Ethereum"), "onchain")

    def test_news_intent(self):
        self.assertEqual(_classify_intent("latest crypto news"), "news")
        self.assertEqual(_classify_intent("breaking BTC headlines"), "news")

    def test_global_intent(self):
        self.assertEqual(_classify_intent("market overview"), "global_metrics")
        self.assertEqual(_classify_intent("BTC dominance and fear greed"), "global_metrics")

    def test_etf_intent(self):
        self.assertEqual(_classify_intent("BTC etf flows today"), "etf_flows")
        self.assertEqual(_classify_intent("spot ETF inflow"), "etf_flows")

    def test_trending_intent(self):
        self.assertEqual(_classify_intent("trending narratives"), "trending")
        self.assertEqual(_classify_intent("what is hot in crypto"), "trending")

    def test_leverage_intent(self):
        self.assertEqual(_classify_intent("BTC leverage ratio"), "leverage")
        self.assertEqual(_classify_intent("open interest BTC"), "leverage")

    def test_historical_intent(self):
        self.assertEqual(_classify_intent("BTC price last 30 days"), "historical")
        self.assertEqual(_classify_intent("ETH all time high"), "historical")

    def test_search_intent(self):
        self.assertEqual(_classify_intent("search for PEPE"), "search")
        self.assertEqual(_classify_intent("look up latest crypto"), "search")

    def test_general_fallback(self):
        self.assertEqual(_classify_intent("hello"), "general")


class TestSymbolExtractor(unittest.TestCase):
    def test_explicit_symbol(self):
        self.assertEqual(extract_symbol("BTC price"), "BTC")
        self.assertEqual(extract_symbol("ETH technical analysis"), "ETH")

    def test_name_to_symbol(self):
        self.assertEqual(extract_symbol("bitcoin price"), "BTC")
        self.assertEqual(extract_symbol("ethereum news"), "ETH")
        self.assertEqual(extract_symbol("solana RSI"), "SOL")

    def test_unknown_falls_to_btc(self):
        self.assertEqual(extract_symbol("what is the market state"), "BTC")


class TestAgentGraph(unittest.TestCase):
    def test_price_quote_query(self):
        loop = asyncio.new_event_loop()
        res = loop.run_until_complete(
            run_agent_graph("session-1", "What is BTC price?", {})
        )
        self.assertIn("tools_executed", res)
        self.assertGreater(len(res["tools_executed"]), 0)
        tools = [t["tool_name"] for t in res["tools_executed"]]
        self.assertIn("get_crypto_quotes_latest", tools)
        loop.close()

    def test_ta_analysis_query(self):
        loop = asyncio.new_event_loop()
        res = loop.run_until_complete(
            run_agent_graph("session-2", "BTC RSI MACD analysis", {})
        )
        self.assertIn("tools_executed", res)
        tools = [t["tool_name"] for t in res["tools_executed"]]
        self.assertIn("get_crypto_technical_analysis", tools)
        loop.close()

    def test_general_query(self):
        loop = asyncio.new_event_loop()
        res = loop.run_until_complete(
            run_agent_graph("session-3", "hello", {})
        )
        self.assertIn("tools_executed", res)
        self.assertEqual(len(res["tools_executed"]), 0)
        loop.close()


if __name__ == "__main__":
    unittest.main()
