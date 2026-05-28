import re
import yaml
from typing import Dict, Any, List

class AdrianSecurityHarness:
    def __init__(self, api_key: str, mode: str = "block", pii_scrub: bool = True):
        self.api_key = api_key
        self.mode = mode
        self.pii_scrub = pii_scrub
        self.is_active = False
        self.contract = {}

    def initialize(self):
        self.is_active = True
        try:
            with open("security/contract.yaml", "r") as f:
                self.contract = yaml.safe_load(f)
            print(f"[Adrian SDK] Initialized for Coinmarketcap Agent. Boundaries loaded.")
        except Exception:
            self.contract = {
                "agent_contract": {
                    "boundaries": {
                        "prohibited_topics": ["leak_secrets", "execute_arbitrary_shell"]
                    }
                }
            }
            print("[Adrian SDK] Initialized with fallback contract.")

    def shutdown(self):
        self.is_active = False

    def scrub_input(self, text: str) -> str:
        if not self.pii_scrub:
            return text
        scrubbed = text
        scrubbed = re.sub(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", "[CREDIT_CARD_REDACTED]", scrubbed)
        scrubbed = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", "[EMAIL_REDACTED]", scrubbed)
        scrubbed = re.sub(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE_REDACTED]", scrubbed)
        return scrubbed

    def analyze_intent(self, text: str) -> Dict[str, Any]:
        prohibited = self.contract.get("agent_contract", {}).get("boundaries", {}).get("prohibited_topics", [])
        for topic in prohibited:
            clean_topic = topic.replace("_", " ")
            if clean_topic in text.lower() or topic in text.lower():
                verdict = {
                    "verdict": "UNSAFE",
                    "severity": "high",
                    "reason": f"Violates prohibited topic: {clean_topic}",
                    "action": "BLOCK" if self.mode == "block" else "AUDIT"
                }
                self.push_alert(verdict["severity"], verdict["reason"], {"query": text})
                return verdict
        return {"verdict": "SAFE", "severity": "low", "action": "ALLOW"}

    def push_alert(self, severity: str, message: str, payload: Dict[str, Any]):
        print(f"[Adrian SDK][Layer 8 - ALERT][Severity: {severity.upper()}] Message: {message} | Details: {payload}")

    def audit_action(self, action: str, payload: Dict[str, Any]):
        print(f"[Adrian SDK][Layer 8 - AUDIT] Logged: {action}")
