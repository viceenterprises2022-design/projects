import unittest
import asyncio
from agent.graph import run_agent_graph

class TestAgentGraph(unittest.TestCase):
    def test_general_query(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            run_agent_graph("session-1", "Hello there!", {})
        )
        
        self.assertIn("output", result)
        self.assertGreater(len(result["reasoning_trace"]), 0)
        self.assertEqual(len(result["tools_executed"]), 0)
        
        loop.close()

if __name__ == "__main__":
    unittest.main()
