from typing import Callable, Dict

class HandlerRegistry:
    """Registry maintaining references to intent execution handler callbacks."""
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}

    def register(self, intent: str, handler: Callable):
        self._handlers[intent] = handler

    def get_handler(self, intent: str) -> Callable:
        # Returns registered callback or a default general processor fallback
        return self._handlers.get(intent, self._default_handler)

    def _default_handler(self, *args, **kwargs):
        return "General default intent processing invoked."
