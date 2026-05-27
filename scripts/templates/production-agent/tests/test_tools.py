import unittest
import asyncio
from agent.tools.crm import lookup_crm_customer
from agent.tools.web_search import web_retrieve

class TestTools(unittest.TestCase):
    def test_crm_lookup(self):
        loop = asyncio.new_event_loop()
        res = loop.run_until_complete(lookup_crm_customer("CUST-100"))
        self.assertEqual(res["name"], "Jane Doe")
        loop.close()

    def test_web_retrieve(self):
        loop = asyncio.new_event_loop()
        res = loop.run_until_complete(web_retrieve("AI"))
        self.assertGreater(len(res), 0)
        self.assertTrue("snippet" in res[0])
        loop.close()

if __name__ == "__main__":
    unittest.main()
