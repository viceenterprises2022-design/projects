class IntentClassifier:
    """Classify incoming user query string into semantic categories."""
    def __init__(self):
        pass

    def classify(self, query: str) -> str:
        q = query.lower()
        if "crm" in q or "customer" in q:
            return "crm_lookup"
        if "search" in q or "find" in q:
            return "search"
        return "general"
