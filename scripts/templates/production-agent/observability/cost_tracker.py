from typing import Dict

class CostTracker:
    """Estimated token cost and latency accumulator."""
    def __init__(self):
        self.pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015}
        }
        self.total_cost = 0.0

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        prices = self.pricing.get(model, {"input": 0.0, "output": 0.0})
        cost = (input_tokens / 1000) * prices["input"] + (output_tokens / 1000) * prices["output"]
        self.total_cost += cost
        return cost
