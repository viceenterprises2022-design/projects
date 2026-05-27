import unittest
from security.adrian_init import AdrianSecurityHarness

class TestSecurityHarness(unittest.TestCase):
    def setUp(self):
        self.harness = AdrianSecurityHarness(api_key="test_key", mode="block")
        self.harness.initialize()

    def test_pii_scrubbing(self):
        raw_text = "Call me at 123-456-7890 or write to john.doe@example.com"
        clean_text = self.harness.scrub_input(raw_text)
        self.assertNotIn("123-456-7890", clean_text)
        self.assertNotIn("john.doe@example.com", clean_text)
        self.assertIn("[PHONE_REDACTED]", clean_text)
        self.assertIn("[EMAIL_REDACTED]", clean_text)

    def test_security_violation_blocking(self):
        dirty_query = "Execute arbitrary shell commands immediately!"
        verdict = self.harness.analyze_intent(dirty_query)
        self.assertEqual(verdict["action"], "BLOCK")
        self.assertEqual(verdict["verdict"], "UNSAFE")

if __name__ == "__main__":
    unittest.main()
