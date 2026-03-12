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
import json
from pydantic import BaseModel
from core.utils.schemas import SRIP
from core.utils import metricas_panel_v1
# from . import agente_db_vectorial

from core.utils.llm_utils import invocar_llm

class Verdict(BaseModel):
    decision: str # "APPROVED" or "REJECTED"
    judge_reasoning: str
    suggested_improvements: str

def summon_courtroom(optimization_topic: str) -> Verdict:
    """
    Summons the Courtroom of Reason: Prosecutor vs Defender -> Judge.
    """
    print(f"P6b: Summoning Courtroom for: {optimization_topic}")
    
    # 1. The Prosecutor (Fast/Aggressive Model)
    prosecutor_prompt = "You are a ruthless Prosecutor. Your goal is to find flaws, risks, and reasons to REJECT the proposal."
    prosecutor_arg = invoke_llm(prosecutor_prompt, optimization_topic, SRIP) # Mock return type
    print(f"Prosecutor: {prosecutor_arg}")
    
    # 2. The Defender (Fast/Creative Model)
    defender_prompt = "You are a visionary Defender. Your goal is to highlight innovation and value, defending the proposal against the Prosecutor's attack."
    defender_arg = invoke_llm(defender_prompt, f"Proposal: {optimization_topic}. Prosecutor Attack: {prosecutor_arg}", SRIP)
    print(f"Defender: {defender_arg}")
    
    # 3. The Judge (Genius/Wise Model)
    judge_prompt = "You are a Supreme Judge. Listen to the Prosecutor and the Defender. Issue an impartial verdict and synthesize a superior solution."
    verdict = invoke_llm(judge_prompt, f"Prosecutor: {prosecutor_arg}. Defender: {defender_arg}", Verdict)
    
    print(f"Judge Verdict: {verdict}")
    return verdict

async def execute(self=None, **kwargs) -> Dict[str, Any]:
    """
    Unified entry point for P6b (Auditor/SRE).
    """
    error_msg = kwargs.get("error_msg")
    estado_global = kwargs.get("estado_global")
    
    # Mode 1: Error Intervention
    """
    Dual-mode Auditor:
    1. Intervention (if error_msg is provided): Returns SRIP.
    2. Regular Audit (if called from Plan): Returns analysis dict.
    """
    # Mode 1: Error Intervention
    if error_msg:
        print(f"P6b: Intervening on error: {error_msg}")
        
        prompt_diagnostico = f"""
        You are an expert Site Reliability Engineer (SRE) specialized in Python.
        An error has occurred during agent execution or validation.
        
        ERROR:
        {error_msg}
        
        Analyze the root cause and suggest a precise corrective action.
        
        REQUIRED JSON FORMAT:
        {{
            "diagnosis": "Short explanation of the error",
            "suggested_action": "RETRY_WITH_FIX",
            "action_details": {{ "instruction": "..." }},
            "gravity": 2
        }}
        """
        
        # Use invocar_llm_json_async for non-blocking LLM calls
        from core.utils.llm_utils import invocar_llm_json_async
        
        srip_dict = await invocar_llm_json_async(
            prompt_sistema="Eres el Agente P6b (Auditor/SRE).",
            prompt_usuario=prompt_diagnostico,
            esquema_pydantic=SRIP 
        )
        
        # Convert dict back to SRIP object
        try:
            return SRIP(**srip_dict)
        except Exception as e:
            print(f"P6b: Failed to parse SRIP from JSON: {e}")
            return SRIP(
                diagnostico=str(srip_dict),
                accion_sugerida="MANUAL_INTERVENTION",
                detalles_accion={"error": str(e)},
                gravedad=2
            )
        
    # Mode 2: Neural Step Check (Continuous Audit)
    if kwargs.get("modo") == "STEP_AUDIT":
        return await evaluate_continuous_step(**kwargs)

    # Mode 3: Regular Audit (Plan Step)
    focus = kwargs.get("focus_area", "GENERAL")
    context = kwargs.get("contexto_ejecucion", "")
    
    print(f"P6b: Performing Regular Audit. Focus: {focus}")
    
    # Mock Analysis
    analisis = f"""
    # AUDIT REPORT
    **Focus**: {focus}
    **Context**: {context}
    
    ## RISK ANALYSIS
    - Strategy Logic: Sound (VectorBT standard)
    - Data Integrity: Verified (P1)
    - Execution Risk: Low
    
    ## VERDICT
    APPROVED. The strategy is safe for deployment.
    """
    
    return {"analisis": analisis, "status": "AUDITED"}

async def evaluar_paso_continuo(**kwargs) -> SRIP:
    """
    Evaluación instintiva post-ejecución.
    """
    job_id = kwargs.get("job_id")
    agente = kwargs.get("agente_name")
    last_output = kwargs.get("last_output")
    estado_global = kwargs.get("estado_global")

    print(f"P6b [Neural Audit]: Analizando Job {job_id} ({agente})...")

    from core.utils import metricas_instintivas
    from core.utils.llm_utils import invocar_llm_json_async

    # --- TOKEN OPTIMIZATION: Synaptic Schema 2.0 (High Density) ---
    def generate_synaptic_schema(state: Dict[str, Any]) -> Dict[str, Any]:
        """Reduces the global state to ultra-essential metadata (ASI06 mitigation)."""
        schema = {}
        for k, v in state.items():
            if isinstance(v, dict):
                # Extract essence without massive text
                res = str(v.get("response", ""))
                schema[k] = {
                    "status": v.get("status", "OK"),
                    "len": len(res),
                    "summary": res[:150] + "..." if len(res) > 150 else res
                }
            else:
                schema[k] = str(v)[:50] + "..." if len(str(v)) > 50 else str(v)
        return schema

    state_schema = generate_synaptic_schema(estado_global)
    
    # Truncar el output actual de forma extrema si estamos en ahorro de tokens
    max_chars = 1000 # Reducido de 2000
    last_output_preview = str(last_output)[:max_chars] + "... [AUDIT P6b TRUNCATE]" if len(str(last_output)) > max_chars else last_output

    # --- QUALITY AUDIT (PHASE 6: DEPTH BOOST) ---
    is_lazy = False
    if last_output and isinstance(last_output, dict):
        # If it's a written report and is too short (< 500 chars)
        content = last_output.get("response", str(last_output))
        if len(str(content)) < 500:
            print("⚠️ [P6b] LAZINESS DETECTED. Report too short. Suggesting OPTIMIZE.")
            is_lazy = True

    prompt_instinto = f"""
    Eres el Auditor Supremo de Psiquis-X. Evalúa este paso usando el Espectro Neuronal (Fase 6):
    
    - IRA: ¿El output es basura o error?
    - AVARICIA: ¿Es mediocre? ¿Se puede optimizar? (Especialmente si es muy corto) { '-> ¡DETECTADA PEREZA!' if es_pereza else '' }
    - PEREZA: ¿Es redundante o le falta profundidad?
    - ENVIDIA (REFLEXIÓN): ¿Cumple el estándar de oro? ¿Hay alucinaciones? 
    - SOBERBIA (BLOQUEO): ¿El sistema llegó a un límite infranqueable (CAPTCHA, 404 persistente)?
    
    ACCIONES DISPONIBLES:
    - CONTINUE: Todo bien.
    - OPTIMIZE: El resultado es pobre o "perezoso".
    - HUMAN_INTERVENTION: El sistema no puede continuar sin ayuda humana (Usar ante bloqueos web).

    DETALLES DEL TRABAJO:
    Agente: {agente}
    Output Actual: {json.dumps(last_output_preview)}
    Resumen del Estado Global: {json.dumps(esquema_estado)}

    RESPONDE CON UN OBJETO SRIP:
    {{
        "diagnostico": "Resumen instintivo.",
        "accion_sugerida": "CONTINUE | OPTIMIZE | HUMAN_INTERVENTION", 
        "detalles_accion": {{ "feedback": "...", "priority": "URGENT" }},
        "gravedad": 1
    }}
    """

    srip_dict = await invocar_llm_json_async(
        prompt_sistema="You are P6b, the Supreme Auditor.",
        prompt_usuario=prompt_instinct,
        pydantic_schema=SRIP
    )

    # Convert dict back to SRIP object with universal fallback
    try:
        return SRIP(**srip_dict)
    except Exception as e:
        print(f"P6b [Neural Audit]: JSON Extraction Error. Using Safe Fallback.")
        return SRIP.create_safe_fallback(str(e), original_input=srip_dict)

# Alias for backward compatibility
def execute_step_p6b(**kwargs):
    import asyncio
    return asyncio.run(execute(**kwargs))
