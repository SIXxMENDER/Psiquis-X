# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Psiquis-X: Enterprise Multi-Agent Framework
# Proprietary Software - All Rights Reserved
# Copyright (c) 2026 SIXxMENDER & Bosniack-94
# -----------------------------------------------------------------------------
# WARNING: This source code is proprietary and confidential. 
# Unauthorized copying, distribution, or use via any medium is strictly 
# prohibited. This code is provided solely for authorized technical review 
# and evaluation purposes.
# -----------------------------------------------------------------------------

from typing import Dict, Any

from core.utils.schemas import NarrativeInput, NarrativeOutput

def execute(self=None, **kwargs) -> Dict[str, Any]:
    """
    Module 8: Narrative Rewriting.
    Converts technical chaos into a coherent story for the human.
    Implements AgentProtocol with Pydantic Validation.
    """
    try:
        input_data = NarrativeInput(**kwargs)
    except Exception as e:
        return {"status": "ERROR", "error": f"Validation Error: {e}"}

    print("📖 [P11 - Narrative] Writing the cycle story...")
    
    technical_logs = input_data.technical_logs
    narrative = []
    narrative.append("# 📜 AI Logbook")
    narrative.append(f"**Mission:** {technical_logs.get('objective', 'Unknown')}")
    
    if technical_logs.get("status") == "SUCCESS":
        narrative.append("\n## ✅ Operational Success")
        narrative.append("We achieved the objective through the following steps:")
        for step in technical_logs.get("steps", []):
            narrative.append(f"- {step}")
    else:
        narrative.append("\n## ⚠️ Challenge Encountered")
        narrative.append(f"There was friction in the process: {technical_logs.get('error', 'Unknown error')}")
        narrative.append("Correction protocols were applied.")

    narrative.append("\n> *'Intelligence is the ability to adapt to change.'*")
    
    output = NarrativeOutput(
        status="SUCCESS",
        narrative="\n".join(narrative)
    )
    return output.model_dump()

# Alias for backward compatibility
def rewrite_narrative(technical_logs: Dict[str, Any]) -> str:
    result = execute(technical_logs=technical_logs)
    return result.get("narrative", "")
