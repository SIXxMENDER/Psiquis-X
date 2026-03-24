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
import json
import logging
import inspect
import importlib.util
from typing import List, Dict, Any, Optional
from core.utils.llm_utils import invoke_llm_async
from core.utils.schemas import EsquemaPlan, Job
from core.utils import metricas_panel_v1
from agentes.P_SERIES import (
    agente_p0,
    agente_p1_ingesta,
    agente_p3,
    agente_p4,
    agente_p5_genesis,
    agente_p6b,
    agente_p7_riesgo as agente_p7_uroboros,
    agente_p8
)
from tools import sixmender
from core.S_SERIES.state_manager import StateManager
from core.sandbox import sandbox
from core.S_SERIES.nhi import nhi
from core.intent_capsule import intent_capsule, IntentCapsule
from core.S_SERIES.guardian import guardian
from core.S_SERIES.cortex import cortex
from agentes.P_SERIES.agente_memoria import MemoryAgent

class Orchestrator:
    """
    The Strategic Commander of Psiquis-X.
    Decides HOW to execute a mission and WHEN to use autonomous tools.
    """
    def __init__(self):
        self.state_manager = StateManager()

    async def plan_mission(self, objective: str, context: dict = None) -> dict:
        """
        Generates a tactical plan. 
        Now includes AUTONOMOUS WEB CHECK logic (Phase 8).
        """
        # 1. SEMANTIC DECOMPOSITION (Phase 13)
        from core.S_SERIES.semantic_router import semantic_router
        decomposed = semantic_router.decompose_objective(objective)
        print(f"🧠 [ORCHESTRATOR] Decomposed Queries: {json.dumps(decomposed, indent=2)}")

        # 2. AUTONOMY CHECK: Does this need fresh data?
        needs_web = any(k in objective.lower() for k in ["price", "news", "latest", "actual", "today", "2026", "trend"])
        
        web_context = ""
        if needs_web:
            print(f"🌐 [ORCHESTRATOR] Autonomy Triggered. executing pre-search...")
            try:
                from agentes.P_SERIES.ingestion.agente_web_scraper import ejecutar as scraper
                # Use the most relevant query for the pre-search (e.g., Marketing or Finance)
                # We prioritize Marketing for general news
                pre_query = decomposed.get("marketing") or decomposed.get("finance") or objective
                
                res = await scraper(url=pre_query) 
                if res.get("status") == "SUCCESS":
                    web_context = f"\n[WEB DATA PREVIEW]: {str(res.get('data'))[:500]}...\n"
            except Exception as e:
                print(f"⚠️ [ORCHESTRATOR] Web Autonomy Failed: {e}")

        # 3. Standard Planning (P3)
        from agentes.P_SERIES import agente_p3
        prompt = f"""
        General Objective: {objective}
        
        🧠 OPTIMIZED QUERIES (USE THESE IN AGENT PARAMETERS):
        - Marketing: "{decomposed.get('marketing')}"
        - Finance: "{decomposed.get('finance')}"
        - Development: "{decomposed.get('development')}"
        - Tribunal: "{decomposed.get('tribunal')}"
        
        Recent Web Context (Autonomous): {web_context}
        
        Design a JSON execution strategy.
        IMPORTANT: Assign the corresponding optimized query to 'query' or 'task_description' for each agent.
        """
        plan_result = await agente_p3.execute(task_description=prompt, context=context)
        return plan_result

orchestrator = Orchestrator()

AGENT_REGISTRY = {
    "P0_Investigador": agente_p0.execute,
    "P1_Datos": agente_p1_ingesta.execute,
    "P3_Estrategia": agente_p3.execute,
    "P4_Backtest": agente_p4.execute,
    "P5_Optimizador": agente_p5_genesis.execute,
    "P6b_Auditor": agente_p6b.execute,
    "P7_Riesgo": agente_p7_uroboros.execute,
    "P8_Integrador": agente_p8.execute
}

async def ejecutar_prueba_motor(plan_data: Dict[str, Any]):
    print("P6a: Starting engine execution...")
    
    # 1. Validate Plan (Self-Healing JSON)
    plan = None
    max_retries = 2
    
    for attempt in range(max_retries + 1):
        try:
            # Clean possible markdown from previous attempts
            if isinstance(plan_data, str):
                plan_data = json.loads(plan_data.replace("```json", "").replace("```", "").strip())
            elif plan_data is None:
                raise ValueError("Plan data is None. Cannot validate.")
            
            plan = EsquemaPlan(**plan_data)
            break # Valid!
        except Exception as e:
            error_msg = str(e)
            print(f"[P6a] Plan Validation Error (Attempt {attempt+1}/{max_retries}): {error_msg}")
            
            if attempt < max_retries:
                # --- SELF-HEALING PROTOCOL ---
                print("[P6a] Activating Self-Healing Protocol for JSON...")
                from core.cortex import cortex
                
                prompt_correccion = (
                    f"CRITICAL JSON VALIDATION ERROR: The execution plan has schema violations.\n"
                    f"ERROR DETAILS: {error_msg}\n"
                    f"MALFORMED JSON: {json.dumps(plan_data)}\n\n"
                    "TASK: Fix the JSON to strictly adhere to the 'EsquemaPlan' Pydantic model. "
                    "Ensure all required fields (like 'agente') are present for every job. "
                    "Respond ONLY with the VALID JSON string."
                )
                
                corrected_json_str = cortex.ask(
                    prompt_correccion, 
                    system_prompt="You are an expert JSON validator. Your only output is corrected JSON."
                )
                
                # Update plan_data for next loop
                try:
                    if corrected_json_str:
                        plan_data = json.loads(corrected_json_str.replace("```json", "").replace("```", "").strip())
                except:
                    pass # Let it fail in next Pydantic check
            else:
                print(f"FATAL: Could not heal JSON after {max_retries} attempts.")
                return

    state_manager = StateManager()
    from core.mission_control import mission_manager
    ic = intent_capsule

    # 1. Topological Sort & Initialization
    jobs_ordenados = _ordenar_jobs_por_dependencias(plan.plan_de_ejecucion)
    thread_id = plan.plan_id
    
    # SEAL INTENT (ASI01)
    original_objective = getattr(plan, "objetivo_general", "Misión General")
    obj_hash = ic.sign_objective(str(original_objective))
    state_manager.save_metadata("original_objective", original_objective)
    state_manager.save_metadata("objective_hash", obj_hash)
    state_manager.save_metadata("active_thread_id", thread_id)

    await mission_manager.emit_event("step", {"msg": "Plan Validated & Sorted", "count": len(jobs_ordenados)})

    estado_global = state_manager.get_all_state(thread_id)

    # 2. Execution Graph Loop
    for job in jobs_ordenados:
        # Check if already completed (for resume)
        if job.job_id in estado_global:
            print(f"⏩ [P6a] skipping already completed job: {job.job_id}")
            continue

        await mission_manager.emit_event("thought", f"Pre-evaluating node: {job.job_id}", agent=job.agente)
        await mission_manager.emit_event("step", {"job_id": job.job_id, "agente": job.agente})
        
        # CREATE CHECKPOINT
        state_manager.create_checkpoint(thread_id, job.job_id, estado_global)

        intentos = 0
        exito = False
        
        while intentos < 3 and not exito: # Circuit Breaker: 3 attempts
            try:
                # Resolve params
                params_resueltos = _resolver_dependencias_en_parametros(job.parametros, estado_global)
                
                await mission_manager.emit_event("thought", f"Executing with params: {json.dumps(params_resueltos)[:100]}...", agent=job.agente)

                # Get Agent Function
                funcion_agente = AGENT_REGISTRY.get(job.agente)
                if not funcion_agente:
                    raise ValueError(f"Agent {job.agente} does not exist.")

                # EXECUTE
                if inspect.iscoroutinefunction(funcion_agente):
                    resultado = await funcion_agente(**params_resueltos)
                else: resultado = funcion_agente(**params_resueltos)
                
                # AUDIT
                srip_audit = await agente_p6b.ejecutar(
                    modo="STEP_AUDIT",
                    job_id=job.job_id,
                    agente_name=job.agente,
                    last_output=resultado,
                    estado_global=estado_global
                )
                
                # Success logic for SRIP audit
                if hasattr(srip_audit, "model_dump"):
                    srip_audit = srip_audit.model_dump()
                
                # Ensure it's a dict for safe access
                if not isinstance(srip_audit, dict):
                    print(f"⚠️ [P6a] Auditor returned non-dict: {type(srip_audit)}. Forcing CONTINUE.")
                    srip_audit = {"suggested_action": "CONTINUE"}

                if srip_audit.get("suggested_action") == "OPTIMIZE":
                    intentos += 1
                    await mission_manager.emit_event("thought", f"Self-Correction: {srip_audit.get('diagnosis')}", agent="P6b_Auditor")
                    job.parametros["optimization_feedback"] = srip_audit.get("action_details", {}).get("feedback", "")
                    continue
                
                if srip_audit.get("suggested_action") == "HUMAN_INTERVENTION":
                    await mission_manager.emit_event("hitl_request", srip_audit.get("diagnosis"), agent="P6b_Auditor")
                    state_manager.save_metadata("mission_status", "PAUSED_AWAITING_HUMAN")
                    state_manager.save_metadata("last_job_id", job.job_id)
                    state_manager.save_metadata("hitl_diagnosis", srip_audit.get("diagnosis"))
                    state_manager.save_metadata("pending_plan", plan.model_dump())
                    return 

                # Success
                if hasattr(resultado, "model_dump"):
                    resultado = resultado.model_dump()
                
                estado_global[job.job_id] = resultado
                print(f"📦 [P6a] Job {job.job_id} Result: {str(resultado)[:200]}...")
                state_manager.update_job_result(thread_id, job.job_id, resultado)
                await mission_manager.emit_event("artifact", resultado, agent=job.agente)
                exito = True
                
            except Exception as e:
                await mission_manager.emit_event("error", str(e), agent="SYSTEM")
                intentos += 1
                if intentos >= 3:
                    await mission_manager.emit_event("budget_alert", f"Circuit Breaker Triggered on {job.job_id}")
                    state_manager.save_metadata("mission_status", "FAILED_STUCK")
                    return

    state_manager.save_metadata("mission_status", "COMPLETED")
    await mission_manager.emit_event("step", "Mission Completed Successfully")

def ejecutar_prueba_motor_sync(plan_data: Dict[str, Any]):
    """
    Synchronous wrapper to run the async orchestrator in a thread-safe way.
    """
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(ejecutar_prueba_motor(plan_data))
    finally:
        loop.close()

def _ordenar_jobs_por_dependencias(jobs: List[Job]) -> List[Job]:
    # Simplified topological sort - assuming list order is roughly correct or simple dependency
    # In production, use networkx or proper Kahn's algorithm
    # For now, just returning list as is since user report says "allows jobs to be defined in any order"
    # but implementing the sort is complex without external libs or more code.
    # I'll implement a basic sort based on dependency presence.
    
    job_map = {j.job_id: j for j in jobs}
    visited = set()
    result = []
    
    def visit(job_id):
        if job_id in visited:
            return
        job = job_map.get(job_id)
        if not job: return # Dependency might be external or previous system state
        
        for dep_id in job.dependencias:
            visit(dep_id)
            
        visited.add(job_id)
        result.append(job)

    for job in jobs:
        visit(job.job_id)
        
    return result

def _resolver_dependencias_en_parametros(params: Any, estado_global: Dict[str, Any]) -> Any:
    """
    Replaces {JobId.field} with actual values from estado_global.
    Supports recursive resolution for dicts and lists.
    """
    if isinstance(params, dict):
        return {k: _resolver_dependencias_en_parametros(v, estado_global) for k, v in params.items()}
    
    if isinstance(params, list):
        return [_resolver_dependencias_en_parametros(item, estado_global) for item in params]
    
    if isinstance(params, str) and params.startswith("{") and params.endswith("}"):
        # Parse {JobId.field}
        path = params[1:-1].split(".")
        if len(path) == 2:
            job_id, field = path
            if job_id in estado_global:
                val = estado_global[job_id].get(field)
                print(f"[DEBUG] Resolved {{{job_id}.{field}}} -> {str(val)[:50]}...")
                return val
            else:
                print(f"[DEBUG] Failed to resolve {{{job_id}.{field}}}: Job ID not found in global state keys: {list(estado_global.keys())}")
                return params # Keep original if not found
        else:
            return params
            
    return params

def _cargar_agente_experimental(path: str):
    """Dynamically loads a module from path."""
    spec = importlib.util.spec_from_file_location("agente_exp", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Assuming experimental agents have a 'run' function or similar convention
    # For this skeleton, we assume they export a function matching the job expectation
    # But since we don't know the function name, we might look for a specific one or callable
    # For now, returning a dummy callable
    return lambda **kwargs: {"result": "Experimental Agent Executed"}
