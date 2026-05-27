import re
import yaml
from typing import Dict, Any, List

class AdrianSecurityHarness:
    """Mock implementation of the Adrian SDK providing the 8 runtime defense harness layers."""
    def __init__(self, api_key: str, mode: str = "block", pii_scrub: bool = True):
        self.api_key = api_key
        self.mode = mode
        self.pii_scrub = pii_scrub
        self.is_active = False
        self.contract = {}

    # Layer 1: Define the agent contract
    def initialize(self):
        self.is_active = True
        try:
            with open("security/contract.yaml", "r") as f:
                self.contract = yaml.safe_load(f)
            print(f"[Adrian SDK] Initialized successfully. Loaded contract boundaries for: {self.contract.get('agent_contract', {}).get('name', 'Agent')}")
        except Exception:
            # Fallback mock contract if file not found during direct import
            self.contract = {
                "agent_contract": {
                    "boundaries": {
                        "prohibited_topics": ["leak_secrets", "execute_arbitrary_shell"]
                    }
                }
            }
            print("[Adrian SDK] Initialized successfully (using default fallback contract).")

    def shutdown(self):
        self.is_active = False
        print("[Adrian SDK] Shutdown complete.")

    # Layer 2: Capture actions and reasoning traces
    def capture_trace(self, step: str, action: str, details: Dict[str, Any]):
        print(f"[Adrian SDK][Layer 2 - Capture] Trace step recorded: {step} | Action: {action}")

    # Layer 3: Scrub PII before it leaves
    def scrub_input(self, text: str) -> str:
        if not self.pii_scrub:
            return text
            
        scrubbed = text
        # Regex filters for credit cards, phone numbers, and common emails
        scrubbed = re.sub(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", "[CREDIT_CARD_REDACTED]", scrubbed)
        scrubbed = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", "[EMAIL_REDACTED]", scrubbed)
        scrubbed = re.sub(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE_REDACTED]", scrubbed)
        
        if scrubbed != text:
            print(f"[Adrian SDK][Layer 3 - PII Scrub] Input cleaned.")
        return scrubbed

    # Layer 4, 5, 6: Analyze, Harden, and Tier Verdict
    def analyze_intent(self, text: str) -> Dict[str, Any]:
        """Layer 4: Analyze trace pre-execution.
        Layer 5: Harden analyzer inputs (treat as untrusted).
        Layer 6: Tier the verdict by severity.
        """
        # Block queries containing unsafe instructions
        prohibited = self.contract.get("agent_contract", {}).get("boundaries", {}).get("prohibited_topics", [])
        
        for topic in prohibited:
            clean_topic = topic.replace("_", " ")
            if clean_topic in text.lower() or topic in text.lower():
                # Layer 6: Severity Tiering
                verdict = {
                    "verdict": "UNSAFE",
                    "severity": "high",
                    "reason": f"Violates prohibited topic boundaries: {clean_topic}",
                    "action": "BLOCK" if self.mode == "block" else "AUDIT"
                }
                
                # Layer 7 & 8: Alert & Action Gateway
                self.push_alert(
                    severity=verdict["severity"],
                    message=f"Intrusion attempt blocked: {verdict['reason']}",
                    payload={"query": text}
                )
                return verdict

        return {"verdict": "SAFE", "severity": "low", "action": "ALLOW"}

    # Layer 7: Choose control mode (Audit / HITL / Block)
    def gate_execution(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Determines if a tool is permitted to run under the active enforcement mode."""
        print(f"[Adrian SDK][Layer 7 - Gate] Tool pre-gating check: {tool_name}")
        return True

    # Layer 8: Push alerts to engineering channels
    def push_alert(self, severity: str, message: str, payload: Dict[str, Any]):
        print(f"[Adrian SDK][Layer 8 - ALERT][Severity: {severity.upper()}] Message: {message} | Details: {payload}")
        # In production this routes payloads directly to Slack / Discord endpoints

    def audit_action(self, action: str, payload: Dict[str, Any]):
        print(f"[Adrian SDK][Layer 8 - AUDIT] Logged: {action} | Payload: {payload}")
