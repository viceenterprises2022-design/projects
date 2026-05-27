class AccuracyJudge:
    """Evaluate predicted intents and safety verifications against expected labels."""
    def evaluate(self, expected: str, predicted: str) -> float:
        if expected == predicted:
            return 1.0
        return 0.0
