from typing import Dict, Any, List
from core.S_SERIES.cortex import cortex
from core.S_SERIES.topology.base import MissionState

async def logic_critic_node(state: MissionState):
    """Crítico de Lógica: Busca fallas en el razonamiento y arquitectura."""
    last_action = state["messages"][-1][1] if state["messages"] else "No action yet"
    import asyncio
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, lambda: cortex.ask(prompt, system_prompt="Logic Critic (Strict Architecture)"))
    return {"messages": [("ai", f"LOGIC_CRITIC: {res}")]}

async def fact_checker_node(state: MissionState):
    """Verificador de Hechos: Valida datos y consistencia externa."""
    last_action = state["messages"][-1][1] if state["messages"] else "No action yet"
    import asyncio
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, lambda: cortex.ask(prompt, system_prompt="Fact Checker (Verification Specialist)"))
    return {"messages": [("ai", f"FACT_CHECKER: {res}")]}

async def supreme_judge_node(state: MissionState):
    """Juez Supremo: Sintetiza las críticas y emite veredicto final."""
    critiques = "\n".join([m[1] for m in state["messages"] if "LOGIC_CRITIC" in m[1] or "FACT_CHECKER" in m[1]])
    import asyncio
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, lambda: cortex.ask(prompt, system_prompt="Supreme Judge (Final Veredict)"))
    authorized = "AUTHORIZED" in res.upper()
    return {"next_step": "CONTINUE" if authorized else "OPTIMIZE", "errors": [] if authorized else [res]}

async def master_audit_node(state: MissionState):
    """Auditor Maestro (Efficient Mode): Combina lógica, hechos y juicio en una sola llamada."""
    # VISUAL UPDATE
    try:
        from core.S_SERIES.mission_control import mission_manager
        await mission_manager.emit_event("graph_update", {"node": "auditor_mar"}, agent="AUDITOR", log_to_console=False)
    except: pass

    last_action = state["messages"][-1][1] if state["messages"] else "No action yet"
    # TRIBUNAL SAFETY: DO NOT WRITE FILES. ONLY VALIDATE.
    # Si detecta que Marketing ya terminó, aprueba automáticamente.
    if state.get("next_step") == "END" or "sovereign_intelligence_report.md" in str(state.get("artifacts")):
        return {"next_step": "END", "errors": []}

    import asyncio
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, lambda: cortex.ask(prompt, system_prompt="Master Auditor (Efficient Mode)"))
    authorized = "AUTHORIZED" in res.upper()
    return {"next_step": "CONTINUE" if authorized else "OPTIMIZE", "errors": [] if authorized else [res]}

def router_audit_mode(state: MissionState):
    """Ruteador de complejidad para el Tribunal MAR."""
    return "efficient" if state.get("mode") == "efficient" else "sovereign"

def build_mar_tribunal():
    from langgraph.graph import StateGraph, END
    workflow = StateGraph(MissionState)
    
    workflow.add_node("logic_critic", logic_critic_node)
    workflow.add_node("fact_checker", fact_checker_node)
    workflow.add_node("judge", supreme_judge_node)
    workflow.add_node("master_auditor", master_audit_node)
    
    # Ruteo Elástico
    workflow.set_conditional_entry_point(
        router_audit_mode,
        {
            "efficient": "master_auditor",
            "sovereign": "logic_critic"
        }
    )
    
    workflow.add_edge("logic_critic", "fact_checker")
    workflow.add_edge("fact_checker", "judge")
    workflow.add_edge("master_auditor", END)
    workflow.add_edge("judge", END)
    
    return workflow.compile()

auditor_graph = build_mar_tribunal()
