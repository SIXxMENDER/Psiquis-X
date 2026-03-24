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

"""
Protocolo Meta-Génesis - Autonomous Evolution Engine
Allows the engine to create, validate, and INTEGRATE new agents permanently.
"""
from typing import Dict, Any, Optional
import os
import yaml
from core.S_SERIES.context import ExecutionContext
from core.S_SERIES.skills import SkillRegistry, Skill
from core.utils.registry import AgentRegistry
from core.S_SERIES.dspy_lite import dspy

async def execute(self=None, **kwargs) -> Dict[str, Any]:
    """
    Unified entry point for P5 (Meta-Génesis).
    """
    objetivo = kwargs.get("objetivo") or kwargs.get("task_description")
    if not objetivo:
        return {"status": "ERROR", "error": "Missing 'objective' parameter for Genesis protocol."}
    
    estado_global = kwargs.get("estado_global")

    # Lazy Load Dependencies
    if not AgentRegistry.get("P0"): from agentes.core import agente_p0
    if not AgentRegistry.get("P3"): from agentes.core import agente_p3
    if not AgentRegistry.get("P8"): from agentes.core import agente_p8
    
    p0 = AgentRegistry.get("P0")
    p3 = AgentRegistry.get("P3")
    p8 = AgentRegistry.get("P8")
    
    print(f"🧬 [Meta-Génesis] Objective: {objetivo}")
    
    try:
        # Step 1: Research (P0)
        print(f"🧬 Step 1: Researching '{objetivo}'...")
        research = await p0.execute(query=objetivo, context=estado_global)
        
        # Step 2: Generate Code (P3)
        print(f"🧬 Step 2: Generating Agent Code...")
        prompt = f"""
        Objective: {objetivo}
        Context: {research.get('respuesta', '')}
        
        Write a complete Python agent that:
        1. Has an `execute(**kwargs)` function (Async).
        2. Resolves the objective.
        3. Returns a dict with 'status' and data.
        4. Do NOT use interactive input() or print().
        """
        code_result = await p3.execute(task_description=prompt, context=estado_global)
        codigo_generado = code_result.get("codigo_python", "")
        
        if len(codigo_generado) < 50: raise ValueError("Invalid code generated")

        # Step 3: Save to Plugins Directory (P8)
        # We save it directly to a new plugin folder
        agent_slug = f"agent_{hash(objetivo) % 10000}"
        plugin_dir = f"agentes/generated/{agent_slug}"
        os.makedirs(plugin_dir, exist_ok=True)
        
        # Save __init__.py (empty)
        with open(f"{plugin_dir}/__init__.py", "w") as f: f.write("")
        
        # Save agent code
        agent_path = f"{plugin_dir}/agent.py"
        with open(agent_path, "w", encoding="utf-8") as f: f.write(codigo_generado)
        
        print(f"🧬 Step 3: Saved to {agent_path}")

        # Step 4: Sandbox Validation
        print(f"🛡️ Step 4: Validating...")
        from agentes.genesis_sandbox import validar_con_reintentos
        
        # Simple callback wrapper for validation
        async def reescribir_callback(error_msg):
            print(f"🔄 [DSPy-Mode] Optimizing code instructions based on error: {error_msg[:50]}...")
            
            # Phase 4.2: Re-compile the prompt using DSPy-Lite
            optimized_prompt = await dspy.optimize(
                task_name=objetivo, 
                base_prompt=prompt, 
                failures=[error_msg]
            )
            
            retry = await p3.execute(task_description=optimized_prompt, previous_error=error_msg, previous_code=codigo_generado)
            new_code = retry.get("codigo_python", "")
            with open(agent_path, "w", encoding="utf-8") as f: f.write(new_code)
            return agent_path

        es_valido, error, _ = await validar_con_reintentos(agent_path, reescribir_callback)
        if not es_valido: raise ValueError(f"Validation failed: {error}")

        # Step 5: Integration (The Evolution)
        print(f"🧬 Step 5: Integrating into Engine...")
        
        # Update agents.yaml
        config_path = "config/agents.yaml"
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            
        new_agent_config = {
            "name": f"AutoAgent_{agent_slug}",
            "module": f"agentes.generated.{agent_slug}.agent",
            "enabled": True,
            "description": objetivo
        }
        
        config["agents"].append(new_agent_config)
        
        with open(config_path, "w") as f:
            yaml.dump(config, f)
            
        # Register in Skill Library
        new_skill = Skill(
            name=new_agent_config["name"],
            description=objetivo,
            module_path=new_agent_config["module"]
        )
        SkillRegistry.register_skill(new_skill)
        
        # Step 6: Hot Reload
        print(f"🔥 Step 6: Hot Reloading...")
        # We need access to the loader instance. 
        # In a real app, this would be injected. For now, we instantiate a new one to trigger reload logic?
        # No, main.py has the loader. We need a way to signal reload.
        # Hack: We re-import loader and call hot_reload on a new instance, 
        # assuming it modifies global sys.modules.
        from core.utils.loader import PluginLoader
        loader = PluginLoader()
        loader.hot_reload()
        
        print(f"🧬 [Meta-Génesis] SUCCESS! New skill acquired: {new_agent_config['name']}")
        return {"status": "SUCCESS", "skill": new_agent_config['name']}

    except Exception as e:
        print(f"🧬 [Meta-Génesis] FAILED: {e}")
        return {"status": "FAILED", "error": str(e)}

# Alias
async def execute_genesis(**kwargs):
    return await execute(**kwargs)
