from typing import List, Dict, Any

class LongTermMemory:
    """Long-term database backing for entity references and episodic records."""
    def __init__(self, db_path: str = "data/long_term.db"):
        self.db_path = db_path
        self.entity_store: Dict[str, Dict[str, Any]] = {}
        self.episodes: List[Dict[str, Any]] = []

    def save_entity(self, entity_id: str, attributes: Dict[str, Any]):
        self.entity_store[entity_id] = attributes

    def get_entity(self, entity_id: str) -> Dict[str, Any]:
        return self.entity_store.get(entity_id, {})

    def record_episode(self, episode_payload: Dict[str, Any]):
        self.episodes.append(episode_payload)
