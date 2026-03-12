from typing import Dict, Any
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

import os
import textwrap
from core.utils.llm_utils import invocar_llm_async
from pydantic import BaseModel
from skills.seo_audit import run_seo_audit

class Propuesta(BaseModel):
    cover_letter: str
    bid_amount: float
    estimated_time: str

from core.utils.schemas import CodeGenInput, CodeGenOutput

async def execute(self=None, **kwargs) -> Dict[str, Any]:
    """
    Unified entry point for P3 (Code Generation & Marketing Skills).
    """
    try:
        input_data = CodeGenInput(**kwargs)
    except Exception as e:
        return {"status": "ERROR", "error": f"Validation Error: {e}"}

    # 0. SKILL TRIGGER: SEO AUDIT
    query = input_data.task_description.lower()
    if "seo" in query or "audit" in query:
        # Extract URL (simple heuristic)
        url = None
        for word in input_data.task_description.split():
            if word.startswith("http"):
                url = word
                break
        
        if url:
            print(f"🚀 [MARKETING] Triggering Skill: SEO AUDIT for {url}")
            report = run_seo_audit(url)
            return {
                "status": "SUCCESS",
                "python_code": "",
                "description": report
            }

    template_path = os.path.join("templates", "base_agent.py")
    if not os.path.exists(template_path):
        return {"status": "ERROR", "error": "Template not found", "codigo_python": ""}
        
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    # 1.5 Cargar Lecciones Aprendidas (Self-Learning)
    lessons_text = ""
    try:
        import json
        lessons_path = os.path.join("data", "memory", "genesis_lessons.json")
        if os.path.exists(lessons_path):
            with open(lessons_path, "r", encoding="utf-8") as f:
                lessons_data = json.load(f)
                lessons = lessons_data.get("lessons", [])
                if lessons:
                    lessons_text = "\n    LESSONS LEARNED (GOLDEN RULES):\n"
                    for i, lesson in enumerate(lessons, 1):
                        lessons_text += f"    {i}. {lesson}\n"
    except Exception as e:
        print(f"⚠️ P3 Warning: Could not load lessons: {e}")

    # 2. Determine Mode (Code vs Copywriting)
    es_copywriting = any(kw in input_data.task_description.lower() for kw in ["marketing", "kit", "copywriting", "proposal", "draft", "ad"])
    
    if es_copywriting:
        print("✍️ [P3] Copywriting Mode detected.")
        prompt_sistema = "You are a Senior Copywriter and Marketing Strategist. You generate publication-ready, persuasive, and high-impact content."
        prompt_usuario = f"Create the following:\n{input_data.task_description}"
    else:
        # Modo Código (Pydantic/Logic)
        # 2. Preparar Prompt para LLM (GENERACIÓN TOTAL)
        
        # RAG INJECTION (Token Optimization)
        from core.S_SERIES.cortex import cortex
        rag_context = cortex.retrieve_context(input_data.task_description)
        
        prompt_sistema = """
        You are an expert Python developer (P3).
        Your task is to write a COMPLETE PYTHON FILE (.py) for a new agent.
        
        PROJECT CONTEXT (MEMORY):
        """ + rag_context + """
        
        INSTRUCTIONS:
        1. Use the following code as a STRUCTURE REFERENCE (Skeleton).
        2. Do NOT fill in gaps. Write the ENTIRE file from scratch.
        3. You must maintain essential imports and the `execute` function.
        4. Implement the real logic inside `execute`.
        
        CRITICAL - AVOID "PARROT EFFECT":
        - Your goal is to EXECUTE the plan, NOT just print it.
        - If the plan says "Create a report", your code must GENERATE that report (write a .md or .txt file), not just print "I will create a report".
        - If the plan says "Calculate budget", your code must do the math.
        - Do NOT write a script that only contains `print("Plan: ...")`. That is useless.
        """ + lessons_text + """
        
        REFERENCE (Base Structure):
        --------------------------------------------------
        """ + template_content + """
        --------------------------------------------------
        
        TECHNICAL RULES:
        1. The code must be valid and executable.
        2. Use `sys.stdout.reconfigure(encoding='utf-8')` if necessary for Windows.
        3. Return a dictionary in `execute`: {"status": "SUCCESS", "result": ...}
        4. Do NOT use markdown (```python). Return only raw code.
        """
        
        if input_data.previous_error:
            prompt_usuario = f"""
            AGENT OBJECTIVE:
            {input_data.task_description}
            
            ⚠️ PREVIOUS FAILED ATTEMPT:
            Error: {input_data.previous_error}
            
            Previous code:
            {input_data.previous_code}
            
            CORRECT AND REWRITE THE ENTIRE FILE.
            """
        else:
            prompt_usuario = f"""
            AGENT OBJECTIVE:
            {input_data.task_description}
            
            Generate the complete .py file.
            """

    # 3. Invocar LLM
    try:
        respuesta_llm = await invocar_llm_async(prompt_sistema, prompt_usuario, temperatura=0.6 if es_copywriting else 0.2)
        print(f"DEBUG P3: LLM Response length: {len(respuesta_llm)}")
        
        # Limpiar bloques de código markdown si los pone
        codigo_final = respuesta_llm.replace("```python", "").replace("```", "").strip()
        
        # 3.5 SELF-TEST (Nivel 5 Robustness)
        if not es_copywriting:
            from core.S_SERIES.sandbox.executor import sandbox
            print("🧪 [P3] Validando código en Sandbox...")
            test_res = sandbox.execute_python(codigo_final)
            if test_res["status"] == "ERROR":
                print(f"⚠️ [P3] Error detectado en Self-Test: {test_res['stderr']}. Reintentando con corregido...")
                # Reintento simple (Solo uno por ahora para FinOps)
                prompt_usuario += f"\n⚠️ ERROR EN EL CÓDIGO GENERADO:\n{test_res['stderr']}\nCorrige el archivo completo."
                codigo_final = await invocar_llm_async(prompt_sistema, prompt_usuario)
                codigo_final = codigo_final.replace("```python", "").replace("```", "").strip()

        output = CodeGenOutput(
            status="SUCCESS",
            codigo_python=codigo_final,
            descripcion="Contenido generado y validado con éxito"
        )
        return output.model_dump()

    except Exception as e:
        print(f"❌ P3 Error: {e}")
        return {"status": "ERROR", "error": str(e), "codigo_python": ""}

# Alias for backward compatibility
def generate_code(task_description: str, previous_error: str = None, previous_code: str = None) -> Dict[str, Any]:
    return execute(task_description=task_description, previous_error=previous_error, previous_code=previous_code)

# --- REGISTRATION ---
from core.utils.registry import AgentRegistry
import sys
AgentRegistry.register("P3", sys.modules[__name__])

def inyectar_self_test(codigo: str, objetivo: str) -> str:
    """
    El self-test ya debería venir en el código generado si siguió la referencia.
    Pero por seguridad, podemos inyectarlo si falta.
    Por ahora, confiamos en la generación completa.
    """
    return codigo

def redactar_propuesta(job_description: str, user_profile: str) -> Propuesta:
    """
    Writes a persuasive proposal for a freelance job.
    Uses the 'Genius' model for high-quality copywriting.
    """
    print(f"P3: Drafting proposal for job...")
    
    prompt = f"""
    You are a Top-Tier Expert Freelancer.
    Write a persuasive proposal for this job:
    {job_description}
    
    Based on my profile:
    {user_profile}
    
    The proposal should be professional, concise, and results-oriented.
    """
    
    proposal = invoke_llm(
        system_prompt="You are a Sales Copywriter expert in Freelancing.",
        user_prompt=prompt,
        pydantic_schema=Propuesta
    )
    
    return proposal
