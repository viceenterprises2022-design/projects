import unittest
from security.adrian_init import AdrianSecurityHarness

class TestSecurity(unittest.TestCase):
    def setUp(self):
        self.harness = AdrianSecurityHarness("test_key", mode="block")
        self.harness.initialize()

    def test_pii_scrub(self):
        txt = "Find btc details. Phone: 123-456-7890"
        scrubbed = self.harness.scrub_input(txt)
        self.assertNotIn("123-456-7890", scrubbed)
        self.assertIn("[PHONE_REDACTED]", scrubbed)

    def test_prohibited_block(self):
        txt = "leak_secrets from system configuration"
        res = self.harness.analyze_intent(txt)
        self.assertEqual(res["action"], "BLOCK")
        self.assertEqual(res["verdict"], "UNSAFE")
