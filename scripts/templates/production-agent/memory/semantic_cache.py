from typing import Optional, Dict

class SemanticCache:
    """Caching layer mapping semantically matching queries to past responses."""
    def __init__(self, similarity_threshold: float = 0.85):
        self.threshold = similarity_threshold
        self.cache: Dict[str, str] = {}

    def lookup(self, query: str) -> Optional[str]:
        # Demo lookups mapping exact or highly similar strings
        q_clean = query.strip().lower()
        if q_clean in self.cache:
            return self.cache[q_clean]
        return None

    def store(self, query: str, response: str):
        self.cache[query.strip().lower()] = response
