from typing import Dict, Any

class FeedbackLoop:
    """Capture explicit user thumbs up/down feedback and implicit engagement telemetry."""
    def __init__(self):
        self.feedbacks = []

    def record_feedback(self, session_id: str, score: int, comments: str = ""):
        self.feedbacks.append({
            "session_id": session_id,
            "score": score,  # e.g., +1 / -1
            "comments": comments
        })
        print(f"[Observability] Saved feedback for session {session_id} (Score: {score})")
