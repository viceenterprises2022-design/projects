from typing import List, Dict, Any

class SlidingWindowMemory:
    """Retain conversational turn context across a sliding window limit."""
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.history: Dict[str, List[Dict[str, str]]] = {}

    def add_message(self, session_id: str, role: str, content: str):
        if session_id not in self.history:
            self.history[session_id] = []
        self.history[session_id].append({"role": role, "content": content})
        # Trim to window size
        if len(self.history[session_id]) > self.window_size * 2:
            self.history[session_id] = self.history[session_id][-self.window_size * 2:]

    def get_context(self, session_id: str) -> List[Dict[str, str]]:
        return self.history.get(session_id, [])
