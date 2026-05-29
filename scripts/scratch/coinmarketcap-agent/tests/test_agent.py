import unittest
import asyncio
import os
import httpx
from agent.graph import run_agent_graph
from agent.nodes import _classify_intent
from agent.tools.cmc_mcp_tools import extract_symbol


_has_cmc = None


def _check_cmc() -> bool:
    global _has_cmc
    if _has_cmc is not None:
        return _has_cmc
    try:
        httpx.get(
            "https://mcp.coinmarketcap.com/mcp",
            headers={"Content-Type": "application/json"},
            timeout=3,
        )
        _has_cmc = True
    except Exception:
        _has_cmc = False
    return _has_cmc


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
        self.assertEqual(_classify_intent("BTC dominance and fear greed"), "global_metrics")

    def test_market_report_intent(self):
        self.assertEqual(_classify_intent("market overview"), "market_report")
        self.assertEqual(_classify_intent("daily brief"), "market_report")
        self.assertEqual(_classify_intent("morning brief crypto"), "market_report")
        self.assertEqual(_classify_intent("market summary"), "market_report")

    def test_deep_dive_intent(self):
        self.assertEqual(_classify_intent("deep dive on ETH"), "deep_dive")
        self.assertEqual(_classify_intent("fundamental analysis of BTC"), "deep_dive")
        self.assertEqual(_classify_intent("full research SOL"), "deep_dive")
        self.assertEqual(_classify_intent("should I buy ETH"), "deep_dive")

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
        self.assertEqual(_classify_intent("buy me lunch"), "general")
        self.assertEqual(_classify_intent("analyze this picture"), "general")


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

    def _run(self, sid, query):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(run_agent_graph(sid, query, {}))
        finally:
            loop.close()

    @unittest.skipIf(not _check_cmc(), "requires live CMC MCP connection")
    def test_price_quote_query(self):
        res = self._run("session-1", "What is BTC price?")
        self.assertIn("tools_executed", res)
        self.assertGreater(len(res["tools_executed"]), 0)
        tools = [t["tool_name"] for t in res["tools_executed"]]
        self.assertIn("get_crypto_quotes_latest", tools)

    @unittest.skipIf(not _check_cmc(), "requires live CMC MCP connection")
    def test_ta_analysis_query(self):
        res = self._run("session-2", "BTC RSI MACD analysis")
        self.assertIn("tools_executed", res)
        tools = [t["tool_name"] for t in res["tools_executed"]]
        self.assertIn("get_crypto_technical_analysis", tools)

    def test_general_query(self):
        res = self._run("session-3", "hello")
        self.assertIn("tools_executed", res)
        self.assertEqual(len(res["tools_executed"]), 0)


if __name__ == "__main__":
    unittest.main()
