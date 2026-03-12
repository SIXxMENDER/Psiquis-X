
"""
A2A Lead Gen Protocol (v5.0) - Phase 5.4
Handles 'Attention Capture' and initial interaction with potential freelance clients.
Converts proposals into structured 'Intent Capsules' for high-impact communication.
"""
import logging
import json
import time
from typing import Dict, Any, Optional

class A2ACaptation:
    """
    Protocol for autonomous client interaction. 
    Focus: Capturing attention, not closing deals.
    """
    def __init__(self):
        self.outreach_logs = []
        self.pending_negotiations = {}

    def format_intent_capsule(self, freelancer_offer: Dict[str, Any]) -> str:
        """
        Creates a structured 'Intent Capsule' to stand out from generic pitches.
        """
        capsule = {
            "protocol": "PX-A2A-V5",
            "intent": "High-Impact AI Automation for Freelance Results",
            "value_proposition": freelancer_offer.get("value", "Strategic Gap Filling"),
            "estimated_roi": freelancer_offer.get("roi", "Variable"),
            "security_clearance": "ASI10 compliant",
            "contact_route": "Direct to Titiritero (Human)"
        }
        return json.dumps(capsule, indent=2)

    def process_client_feedback(self, client_id: str, feedback: str):
        """
        Analyzes initial client feedback and prepares an escalation or a technical doubt resolver.
        """
        logging.info(f"🤝 [A2A] Processing feedback from {client_id}: {feedback[:50]}...")
        
        # Heuristic: If they ask about price/time, escalate to Titiritero
        escalation_keywords = ["price", "cost", "how much", "when", "time", "duration", "contract"]
        should_escalate = any(k in feedback.lower() for k in escalation_keywords)
        
        if should_escalate:
            return {"status": "ESCALATE_TO_TITIRITERO", "data": feedback}
        
        return {"status": "CONTINUE_CAPTATION", "response": "Providing technical specs of the motor..."}

# Singleton
captation_protocol = A2ACaptation()
