from langgraph.graph import StateGraph, END
from core.S_SERIES.cortex import cortex
from core.S_SERIES.topology.base import MissionState
from core.S_SERIES.mission_control import mission_manager

async def bullish_agent_node(state: MissionState):
    """Agente Alcista (Bullish): Busca evidencia positiva."""
    await mission_manager.emit_event("graph_update", {"node": "finance_dept"}, agent="FINANCE", log_to_console=False)
    await mission_manager.emit_event("step", {"job_id": "job_finance_bull", "agente": "Bullish Analyst"}, agent="BULLISH")
    objetivo = state["objetivo_general"]
    
    await mission_manager.emit_event("thought", f"Analizando '{objetivo}' buscando oportunidades...", agent="BULLISH")
    
    contexto_web = state["artifacts"].get("marketing", {}).get("content_snippet", "No web data available.")
    prompt = f"Basado en este contexto real:\n{contexto_web}\n\nAnaliza '{objetivo}' desde una perspectiva optimista. Busca fortalezas y oportunidades. Ignora riesgos."
    # FIX: Run sync LLM call in executor to avoid blocking event loop
    import asyncio
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, lambda: cortex.ask(prompt, system_prompt="Bullish Analyst (Trust Agent)", model="gemini-2.0-flash-001"))
    
    await mission_manager.emit_event("thought", "Análisis alcista completado.", agent="BULLISH")
    return {"messages": [("ai", f"BULLISH: {res}")]}

async def skeptic_agent_node(state: MissionState):
    """Agente Escéptico (Bearish): Busca evidencia negativa."""
    await mission_manager.emit_event("step", {"job_id": "job_finance_bear", "agente": "Bearish Analyst"}, agent="BEARISH")
    objetivo = state["objetivo_general"]
    
    await mission_manager.emit_event("thought", f"Auditando riesgos para '{objetivo}'...", agent="BEARISH")
    
    contexto_web = state["artifacts"].get("marketing", {}).get("content_snippet", "No web data available.")
    prompt = f"Basado en este contexto real:\n{contexto_web}\n\nAnaliza '{objetivo}' desde una perspectiva crítica. Busca deudas, riesgos, competencia y fallas logicas. Prohibido ser positivo."
    # FIX: Run sync LLM call in executor
    import asyncio
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, lambda: cortex.ask(prompt, system_prompt="Bearish Analyst (Skeptic Agent)", model="gemini-2.0-flash-001"))
    
    await mission_manager.emit_event("thought", "Auditoría de riesgos finalizada.", agent="BEARISH")
    return {"messages": [("ai", f"BEARISH: {res}")]}

async def synthesizer_node(state: MissionState):
    """Líder Sintetizador: Decide el veredicto."""
    await mission_manager.emit_event("step", {"job_id": "job_finance_lead", "agente": "Synthesizer Lead"}, agent="LEADER")
    
    await mission_manager.emit_event("thought", "Debatiendo hallazgos de analistas...", agent="LEADER")
    
    debate = "\n".join([m[1] for m in state["messages"] if "BULLISH" in m[1] or "BEARISH" in m[1]])
    
    prompt = f"Basado en este debate:\n{debate}\nGenera un veredicto equilibrado y una recomendación final."
    # FIX: Run sync LLM call in executor
    import asyncio
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, lambda: cortex.ask(prompt, system_prompt="Synthesizer LeaderAgent"))
    
    # Persistencia en Bóveda
    import os, time
    os.makedirs("data/finance", exist_ok=True)
    timestamp = int(time.time())
    filename = f"data/finance/report_{timestamp}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(res)
    
    await mission_manager.emit_event("artifact", {"type": "financial_report", "content": res, "path": filename}, agent="LEADER")
    return {"artifacts": {"final_report": res, "path": filename}, "next_step": "END"}

async def consolidated_finance_node(state: MissionState):
    """Analista Financiero Integral: Realiza el debate interno en una sola llamada."""
    await mission_manager.emit_event("graph_update", {"node": "finance_dept"}, agent="FINANCE", log_to_console=False)
    await mission_manager.emit_event("step", {"job_id": "job_finance_total", "agente": "Full Analyst"}, agent="FINANCE")
    objetivo = state["objetivo_general"]
    
    contexto_web = state["artifacts"].get("marketing", {}).get("content_snippet", "No web data available.")
    prompt = f"""
    Basado en este contexto extraído de la web:
    {contexto_web}

    Realiza un análisis financiero integral de '{objetivo}'.
    DEBES INCLUIR:
    1. Precios actuales detectados.
    2. Perspectiva Alcista (Pros).
    3. Perspectiva Escéptica (Riesgos).
    4. Conclusión y Veredicto Final.
    """
    # FIX: Run sync LLM call in executor
    import asyncio
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, lambda: cortex.ask(prompt, system_prompt="Consolidated Financial Analyst", model="gemini-2.0-flash-001"))
    
    # Persistencia en Bóveda
    import os, time
    os.makedirs("data/finance", exist_ok=True)
    timestamp = int(time.time())
    filename = f"data/finance/consolidated_{timestamp}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(res)

    await mission_manager.emit_event("artifact", {"type": "financial_report", "content": res, "path": filename}, agent="FINANCE")
    return {"artifacts": {"final_report": res, "path": filename}, "next_step": "END"}

def router_finance_mode(state: MissionState):
    return "efficient" if state.get("mode") == "efficient" else "sovereign"

def build_finance_subgraph():
    workflow = StateGraph(MissionState)
    workflow.add_node("trust", bullish_agent_node)
    workflow.add_node("skeptic", skeptic_agent_node)
    workflow.add_node("synthesizer", synthesizer_node)
    workflow.add_node("consolidated", consolidated_finance_node)
    
    workflow.set_conditional_entry_point(
        router_finance_mode,
        {
            "efficient": "consolidated",
            "sovereign": "trust"
        }
    )
    workflow.add_edge("trust", "skeptic")
    workflow.add_edge("skeptic", "synthesizer")
    workflow.add_edge("consolidated", END)
    workflow.add_edge("synthesizer", END)
    
    return workflow.compile()

finance_graph = build_finance_subgraph()
