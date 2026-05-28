import unittest
import asyncio
from agent.graph import run_agent_graph

class TestCoinmarketcapAgent(unittest.TestCase):
    def test_crypto_skill_lookup(self):
        loop = asyncio.new_event_loop()
        res = loop.run_until_complete(
            run_agent_graph("session-abc", "What is the btc price?", {})
        )
        self.assertIn("tools_executed", res)
        self.assertGreater(len(res["tools_executed"]), 0)
        self.assertEqual(res["tools_executed"][0]["tool_name"], "find_skill")
        loop.close()

if __name__ == "__main__":
    unittest.main()
