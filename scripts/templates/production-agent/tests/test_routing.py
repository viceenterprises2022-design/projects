import unittest
from routing.classifier import IntentClassifier

class TestRouting(unittest.TestCase):
    def setUp(self):
        self.classifier = IntentClassifier()

    def test_crm_classification(self):
        intent = self.classifier.classify("Get details for customer Jane")
        self.assertEqual(intent, "crm_lookup")

    def test_search_classification(self):
        intent = self.classifier.classify("Find news search for python")
        self.assertEqual(intent, "search")

    def test_general_classification(self):
        intent = self.classifier.classify("Who made the world?")
        self.assertEqual(intent, "general")

if __name__ == "__main__":
    unittest.main()
