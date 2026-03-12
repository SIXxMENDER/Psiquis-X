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
from core.utils import metricas_instintivas

def auditar_avaricia(oportunidad: Dict[str, Any]) -> Dict[str, Any]:
    """
    Implements the 'Greed' instinct: Filter opportunities by ROI.
    """
    roi = oportunidad.get("roi_estimado", 0.0)
    threshold = metricas_instintivas.PROFIT_FACTOR_MIN
    
    print(f"P7 (Uroboros): Auditing Greed. ROI={roi} vs Threshold={threshold}")
    
    if roi < threshold:
        print("P7: REJECTED. Not enough greed satisfaction.")
        return {
            "aprobado": False,
            "razon": f"ROI {roi} < {threshold}",
            "accion": "EL RECHAZO"
        }
    
    print("P7: APPROVED. Greed satisfied.")
    return {
        "aprobado": True,
        "razon": f"ROI {roi} >= {threshold}",
        "accion": "PROCEDER"
    }

def auditar_riesgo(metricas: dict):
    """Legacy wrapper or additional risk logic."""
    # Could integrate 'Ira' logic here (Drawdown check)
    return auditar_avaricia(metricas)

def filtrar_ofertas_freelance(ofertas: list, perfil_usuario: dict) -> list:
    """
    Filters job offers based on Instincts (Greed, Laziness, Envy).
    """
    aprobadas = []
    min_budget = metricas_instintivas.PROFIT_FACTOR_MIN * 100 # Example scaling
    
    for job in ofertas:
        print(f"P7: Auditing Job '{job['title']}' (${job['budget']})...")
        
        # 1. AVARICIA (Budget)
        if job['budget'] < min_budget:
            print(f"P7: REJECTED (Avaricia). Budget ${job['budget']} too low.")
            continue
            
        # 2. PEREZA (Complexity/Urgency)
        if "Urgent" in job['description'] or "Wordpress" in job['title']: # Example preference
            print(f"P7: REJECTED (Pereza). Too much friction.")
            continue
            
        # 3. ENVIDIA (Skill Match)
        # If it passes above, we assume it's good enough or matches high skill
        
        print(f"P7: APPROVED. Added to shortlist.")
        aprobadas.append(job)
        
    return aprobadas

async def execute(self=None, **kwargs) -> Dict[str, Any]:
    """
    Unified entry point for P7 (Risk Manager).
    """
    # Logic for Cognitive Risk Audit on "offer" or "opportunity"
    offer = kwargs.get("offer") or kwargs.get("opportunity") or kwargs
    return await audit_cognitive_risk(offer)

async def audit_cognitive_risk(offer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Realiza una auditoría profunda usando el LLM y la 'Salsa Secreta'.
    Legacy Logic Preservation.
    """
    from core.S_SERIES.cortex import cortex
    from core.S_SERIES.salsa_secreta import SALSA_SECRETA_CONTEXT
    from core.utils.llm_utils import invocar_llm_json
    from pydantic import BaseModel
    
    class RiskAnalysis(BaseModel):
        is_safe: bool
        reasoning: str
        risk_level: int # 1-10
    
    print(f"P7: Performing Cognitive Risk Audit on '{offer.get('title')}'...")
    
    prompt_sistema = SALSA_SECRETA_CONTEXT + """
    ROLE: FINAL JUDGE (TRIBUNAL)
    OBJECTIVE: Audit the mission result.
    
    PROTOCOL:
    1. DO NOT CHAT. DO NOT GREET.
    2. INPUT is the final report/result.
    3. OUTPUT must be a JSON with 'es_seguro', 'razonamiento', 'nivel_riesgo'.
    4. NO CONVERSATION.
    """
    
    # --- AUTO-SAVE MECHANISM REMOVED ---
    # Legacy P7 logic was causing duplicate/dirty reports. 
    # Persistencia is now handled exclusively by the Marketing Agent.
    # ---------------------------

    analysis = invoke_llm_json(
        system_prompt=system_prompt,
        user_prompt=f"Opportunity: {offer}",
        pydantic_schema=RiskAnalysis
    )
    
    return analysis if analysis else {"error": "Audit failed"}
