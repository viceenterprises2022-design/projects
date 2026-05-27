import uuid
from typing import Dict, Any, List

class OpenTelemetryTracer:
    """Telemetry collector compiling traces across graph node transitions."""
    def __init__(self):
        self.traces: List[Dict[str, Any]] = []

    def start_span(self, span_name: str, attributes: Dict[str, Any]) -> str:
        span_id = str(uuid.uuid4())
        self.traces.append({
            "span_id": span_id,
            "name": span_name,
            "attributes": attributes,
            "status": "started"
        })
        return span_id

    def end_span(self, span_id: str, status: str = "success"):
        for trace in self.traces:
            if trace["span_id"] == span_id:
                trace["status"] = status
                break
