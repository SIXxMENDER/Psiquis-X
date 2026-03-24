import os
import json
from langgraph.graph import StateGraph, END
from core.S_SERIES.topology.base import MissionState
from core.S_SERIES.cortex import cortex

async def creative_node(state: MissionState):
    """Generador Creativo: Crea el borrador inicial."""
    # VISUAL UPDATE
    try:
        from core.S_SERIES.mission_control import mission_manager
        await mission_manager.emit_event("graph_update", {"node": "marketing_dept"}, agent="MARKETING", log_to_console=False)
        await mission_manager.emit_event("thought", "Designando Director Creativo...", agent="MARKETING")
    except: pass
    
    import asyncio
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, lambda: cortex.ask(prompt, system_prompt="Creative Director"))
    return {"messages": [("ai", f"CREATIVE_DRAFT: {res}")]}

async def seo_optimizer_node(state: MissionState):
    """Optimizador SEO: Refina para buscadores y audiencia."""
    draft = [m[1] for m in state["messages"] if "CREATIVE_DRAFT" in m[1]][-1]
    import asyncio
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, lambda: cortex.ask(prompt, system_prompt="SEO Specialist"))
    return {"messages": [("ai", f"OPTIMIZED_CONTENT: {res}")]}

async def finalizer_node(state: MissionState):
    """Finalizador: Entrega el kit listo y lo persiste en disco."""
    # --- EXECUTIVE REPORT SYNTHESIS (New Logic) ---
    raw_data = state.get('marketing', {}).get('content_snippet') or str(state.get('artifacts', {}))
    
    prompt_synthesis = f"""
    ROLE: EXECUTIVE FINANCIAL COMMUNICATIONS DIRECTOR.
    INPUT RAW DATA: {raw_data[:50000]} (Truncated if too long)
    
    TASK: Transform this raw data into a clean, professional Executive Market Report.
    
    STRICT MARKDOWN OUTPUT FORMAT:
    # 🏛️ Sovereign Market Intelligence Report
    
    ## 📊 Executive Summary
    [Brief analysis of the market sentiment based on the data]
    
    ## 💎 Asset Tracker
    | Asset | Price | Trend | Evidence |
    | :--- | :--- | :--- | :--- |
    | BTC | $62,000 | 📉 -2% | [📸 Verify Evidence](path...) |
    (Repeat for all found assets)
    
    ## 📸 Evidence Vault
    [List clickable links to all screenshots found in the raw data]
    - Screenshot 1: [View](path...)
    
    NO JSON. NO HTML. ONLY CLEAN MARKDOWN.
    """
    
    import asyncio
    loop = asyncio.get_running_loop()
    # Using a professional persona for the report
    final_report = await loop.run_in_executor(None, lambda: cortex.ask(prompt_synthesis, system_prompt="Executive Director", model="gemini-2.0-flash-001"))
    
    # Save the polished report
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/reports/mission_report_{timestamp}.md"
    
    # --- HITL CHECKPOINT ---
    try:
        from core.S_SERIES.mission_control import mission_manager
        approved = await mission_manager.wait_for_approval(
            action_description=f"Publish Executive Report ({len(final_report)} chars)",
            agent="MARKETING"
        )
        if not approved:
            await mission_manager.emit_event("thought", "[REJECTED] Report Rejected by Human Operator.", agent="MARKETING")
            return {"next_step": "END", "status": "ABORTED"}
    except: pass
    
    # Persistencia Física Estricta
    os.makedirs("data/reports", exist_ok=True)
    filename = "data/reports/sovereign_intelligence_report.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_report)
    
    print(f"[MARKETING] ✅ REPORTE FINAL GUARDADO: {filename}")
    
    # OUTPUT LIMPIO PARA EL GRAFO
    # Devolvemos solo el reporte limpio para evitar que el JSON crudo inunde el chat
    return {
        "messages": [("ai", final_report)], 
        "artifacts": {
            "final_report": final_report,
            "evidence_paths": "Ver reporte."
        },
        "next_step": "END"
    }

def build_marketing_subgraph():
    workflow = StateGraph(MissionState)
    workflow.add_node("creative", creative_node)
    workflow.add_node("seo", seo_optimizer_node)
    workflow.add_node("finalizer", finalizer_node)
    
    workflow.set_entry_point("creative")
    workflow.add_edge("creative", "seo")
    workflow.add_edge("seo", "finalizer")
    workflow.add_edge("finalizer", END)
    
    return workflow.compile()

marketing_graph = build_marketing_subgraph()
