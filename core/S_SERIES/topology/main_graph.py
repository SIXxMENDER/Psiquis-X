import os
import json
from langgraph.graph import StateGraph, END
from core.S_SERIES.topology.base import MissionState
from core.utils.logger import log

from core.S_SERIES.state_manager import StateManager
from core.S_SERIES.topology.base import MissionState
from core.utils.logger import log

# AGENT_MAP mapping IDs to module paths for Lazy Loading
AGENT_MAP = {
    "supervisor": "agentes.P_SERIES.talker",
    "marketing": "agentes.P_SERIES.ingestion.agente_web_scraper",
    "finance": "agentes.P_SERIES.agente_p0",
    "ingesta": "agentes.P_SERIES.agente_p1_ingesta",
    "tribunal": "agentes.P_SERIES.agente_p7_riesgo",
    "estratega": "agentes.P_SERIES.agente_p5_genesis",
    "memoria": "agentes.P_SERIES.agente_memoria",
    "narrativa": "agentes.P_SERIES.agente_p11_narrativa",
    "motivador": "agentes.P_SERIES.agente_p10_motivacion",
    "optimizador": "agentes.P_SERIES.agente_p5_optimize_predator",
    "riesgo": "agentes.P_SERIES.agente_p7_riesgo",
    "metacognicion": "agentes.P_SERIES.agente_p12_metacognicion",
}

# Node Factory to inject node_id
def make_node(node_id: str):
    async def _node_execution(state: MissionState):
        import importlib
        node_id_lower = node_id.lower()
        log.info(f"[SOVEREIGN_CORE] Node '{node_id_lower}' intercepting mission flow...")
        
        # RESOLVE THE MUSCLE (Lazy Load)
        module_path = AGENT_MAP.get(node_id_lower) or "agentes.P_SERIES.talker"
        try:
            mod = importlib.import_module(module_path)
            agent_fn = getattr(mod, "ejecutar")
        except Exception as e:
            log.error(f"[CORE_LINK] Module {module_path} not found or invalid: {e}. Using fallback.")
            from agentes.P_SERIES.talker import ejecutar as talker_fn
            agent_fn = talker_fn
        
        # PREPARE INPUT FROM STATE
        # CRITICAL FIX: Always focus on the MAIN OBJECTIVE, but enrich with previous artifacts
        mission_goal = state.get("objetivo_general", "Sin objetivo")
        
        # Collect context from previous nodes
        context_data = ""
        for k, v in state.get("artifacts", {}).items():
            context_data += f"\n[DATA FROM {k.upper()}]: {str(v)[:500]}..."

        full_prompt = f"OBJETIVO: {mission_goal}\nCONTEXTO PREVIO: {context_data}"
        
        try:
            # EXECUTE REAL TACTICAL LOGIC
            result = await agent_fn(
                query=full_prompt, 
                url=mission_goal, # Scraper uses this if it's a URL, otherwise searches
                objetivo=mission_goal,
                task_description=full_prompt,
                context=state,
                estado_global=state
            ) 
            
            # SYNC STATE
            if isinstance(result, dict):
                msg = result.get("respuesta") or result.get("resultado") or f"Nodo {node_id_lower} completó su misión."
                state["messages"].append(msg)
                if "data" in result:
                    state["artifacts"][node_id_lower] = result["data"]
            else:
                state["messages"].append(str(result))
                
        except Exception as e:
            log.error(f"[CORE_DRIVE] Node {node_id_lower} Failed: {e}")
            state["messages"].append(f"CRITICAL: Node {node_id_lower} suffered a neural break: {e}")

        return state
    return _node_execution

def load_topology_config():
    sm = StateManager()
    topo = sm.get_metadata("topology_state")
    if topo: return topo
    
    # Default Fallback
    return {
        "nodes": [
            {"id": "SUPERVISOR", "label": "NÚCLEO_CONTROL", "type": "hub", "x": 150, "y": 50},
            {"id": "FINANCE", "label": "AUDITOR_FINANZAS", "type": "worker", "x": 50, "y": 150},
            {"id": "MARKETING", "label": "CREATIVO_MKT", "type": "worker", "x": 250, "y": 150},
            {"id": "TRIBUNAL", "label": "CENTRO_TRIBUNAL", "type": "shield", "x": 150, "y": 250}
        ],
        "edges": [
            {"from": "SUPERVISOR", "to": "FINANCE"},
            {"from": "SUPERVISOR", "to": "MARKETING"},
            {"from": "FINANCE", "to": "TRIBUNAL"},
            {"from": "MARKETING", "to": "TRIBUNAL"}
        ]
    }

def build_sovereign_engine():
    """Constructs the Sovereign Engine dynamically from configuration."""
    topo = load_topology_config()
    workflow = StateGraph(MissionState)
    
    # 1. ADD NODES
    for node in topo["nodes"]:
        node_id = node["id"].lower()
        workflow.add_node(node_id, make_node(node_id))
    
    # 2. ADD EDGES
    for edge in topo["edges"]:
        workflow.add_edge(edge["from"].lower(), edge["to"].lower())
    
    # 3. SET ENTRY POINT
    # Default to the first node in the list if not specified
    if topo["nodes"]:
        workflow.set_entry_point(topo["nodes"][0]["id"].lower())
    
    # 4. MANAGE ENDINGS
    # Nodes with no outgoing edges go to END
    node_ids_with_out_edges = {e["from"].lower() for e in topo["edges"]}
    for node in topo["nodes"]:
        node_id = node["id"].lower()
        if node_id not in node_ids_with_out_edges:
            workflow.add_edge(node_id, END)
            
    return workflow.compile()

def get_sovereign_engine():
    """Constructs and returns a fresh entry point to the engine."""
    return build_sovereign_engine()
