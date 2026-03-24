import os
import sys
import json
import asyncio
from fastapi import FastAPI, WebSocket, Request, Body, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
from collections import deque
from fastapi.staticfiles import StaticFiles
import shutil

# 1. SETUP LOGGING & PATHS
sys.path.append(os.getcwd())
try:
    from core.S_SERIES.cortex import cortex
    print("[SERVER] Cortex Loaded (S1)")
except Exception as e:
    print(f"[SERVER] Cortex Load Error: {e}")

from core.S_SERIES.mission_control import mission_manager
from core.S_SERIES.state_manager import StateManager

app = FastAPI(title="Psiquis-X Engine V3 (Minimal)")

# 2. CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/data", StaticFiles(directory="data"), name="data")

# 3. CHAT HISTORY
chat_history = deque(maxlen=100)
sm = StateManager()

# 4. ENDPOINTS
@app.get("/")
def health_check():
    return {"status": "ONLINE", "mode": "MINIMAL_SAFE"}

@app.get("/api/status")
def status_check():
    return {
        "system": {"cpu": "10%", "ram": "2GB"},
        "mission": {"estimated_cost": "$0.00"}
    }

# 5. STREAMING SSE
mission_event_queue = asyncio.Queue()

@app.get("/stream/mission")
async def stream_mission(request: Request):
    async def event_generator():
        while True:
            if await request.is_disconnected(): break
            try:
                data = await asyncio.wait_for(mission_event_queue.get(), timeout=5.0)
                yield f"data: {json.dumps(data)}\n\n"
            except asyncio.TimeoutError:
                yield ": keep-alive\n\n"
            except Exception: break
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Bridge mission_manager to SSE
async def broadcast_to_sse(payload):
    await mission_event_queue.put(payload)
mission_manager._broadcast_ws = broadcast_to_sse

# 6. GRAPH LAUNCHER (LAZY IMPORT)
@app.post("/api/sovereign/launch")
async def launch_mission(payload: dict = Body(...)):
    objetivo = payload.get("objetivo")
    mode = payload.get("mode", "efficient")
    
    # --- [NEW] DOCUMENT INTELLIGENCE ROUTER ---
    prompt_upper = objetivo.upper()
    if "ENTITY_A" in prompt_upper or "REPORTE" in prompt_upper or "REPORT" in prompt_upper or "ANALYZE" in prompt_upper or "ANALIZA" in prompt_upper:
        print(f"[SERVER] Routing to Document Intelligence Mission: {objetivo}")
        try:
             # Lazy import to avoid circular dependencies
             from core.S_SERIES.missions.doc_intelligence import execute_mission
             
             async def _safe_run():
                 try:
                     await execute_mission(objetivo, broadcast_to_sse)
                 except Exception as e:
                     import traceback
                     error_trace = traceback.format_exc()
                     print(f"[CRITICAL] DocIntel Mission Error:\n{error_trace}")
                     await broadcast_to_sse({"type": "error", "data": f"Error crítico en misión: {str(e)}"})
                     
             asyncio.create_task(_safe_run())
             return {"status": "LAUNCHED_DOC_INTEL", "message": "Iniciando análisis documental autónomo."}
        except Exception as e:
             print(f"[SERVER] Error launching DocIntel: {e}")
             return {"status": "ERROR", "message": str(e)}
    # ------------------------------------------

    # --- [NEW] REVENUECAT ADVOCATE MISSION ---
    if "ENTITY_B" in prompt_upper or "ADVOCATE" in prompt_upper:
        print(f"[SERVER] Routing to Advocate Mission: {objetivo}")
        try:
             from core.S_SERIES.missions.revenuecat_advocate import build_revenuecat_graph
             
             async def _run_revenuecat():
                 try:
                     rc_graph = build_revenuecat_graph()
                     initial_state = {
                         "job_url": "https://www.example.com/jobs/view/12345/", # Generic URL
                         "job_description": objetivo,
                         "target_company": "EnterpriseCorp",
                         "cortex": cortex,
                         "thesis_draft": None,
                         "mermaid_code": None,
                         "prosecutor_feedback": None,
                         "is_valid": False,
                         "rejection_count": 0,
                         "final_markdown": None,
                         "gist_url": None
                     }
                     # Astream the graph to emit SSE events
                     async for step in rc_graph.astream(initial_state):
                         for node, val in step.items():
                             if node == '__end__': continue
                             await broadcast_to_sse({"type": "graph_update", "node": node.lower()})
                             
                             msg = f"[{node.upper()}] Operación en progreso..."
                             if node == "scraper_node":
                                 msg = f"[{node.upper()}] Ingestando url en vivo: {initial_state['job_url']}"
                             if node == "prosecutor_node" and not val.get('is_valid'):
                                 msg = f"[{node.upper()}] Hallucination detectada. Auto-corrigiendo..."
                             if node == "publisher_node":
                                 gist_url = val.get("gist_url")
                                 msg = f"[{node.upper()}] Misión Completada. Link generado: {gist_url}"
                                 
                             await broadcast_to_sse({"type": "thought", "data": msg})
                             
                 except Exception as e:
                     import traceback
                     error_trace = traceback.format_exc()
                     print(f"[CRITICAL] RevenueCat Mission Error:\n{error_trace}")
                     await broadcast_to_sse({"type": "error", "data": f"Error crítico en misión RevenueCat: {str(e)}"})
                     
             asyncio.create_task(_run_revenuecat())
             return {"status": "LAUNCHED_REVENUECAT", "message": "Iniciando Agentic Postulación a RevenueCat."}
        except Exception as e:
             print(f"[SERVER] Error launching RevenueCat Mission: {e}")
             return {"status": "ERROR", "message": str(e)}
    # ------------------------------------------


    print(f"[SERVER] Launching Mission: {objetivo}")
    
    # EMULATE GRAPH EXECUTION IF REAL ENGINE FAILS
    async def run_real_mission():
        print("[DEBUG] run_real_mission STARTED")
        try:
            from core.S_SERIES.topology.main_graph import get_sovereign_engine
            print("[DEBUG] Engine Imported")
            await broadcast_to_sse({"type": "thought", "data": "ENGINE_ACTIVE: High-Fidelity Routing Enabled."})
            
            sovereign_engine = get_sovereign_engine()
            print("[DEBUG] Engine Compiled")
            
            initial_state = {
                "objetivo_general": objetivo,
                "mode": mode,
                "messages": [],
                "artifacts": {},
                "next_step": "START",
                # REQUIRED FIELDS FOR MissionState
                "plan_id": f"plan_{hash(objetivo)}",
                "thread_id": "main_thread",
                "task_ledger": [],
                "current_agent": "supervisor",
                "intent_hash": "init",
                "errors": [],
                "metadata": {}
            }
            print(f"[DEBUG] Starting Stream with state keys: {list(initial_state.keys())}")
            
            async for step in sovereign_engine.astream(initial_state):
                 print(f"[DEBUG] Step Received: {step.keys()}")
                 for node, val in step.items():
                     if node == '__end__': continue
                     await broadcast_to_sse({"type": "graph_update", "node": node.lower()})
                     
                     # Extract result message from state
                     node_msg = val.get("messages", ["..."])[-1]
                     await broadcast_to_sse({"type": "thought", "data": f"[{node.upper()}] {node_msg}"})
                     
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[CRITICAL] Graph Failure:\n{error_trace}")
            await broadcast_to_sse({"type": "error", "data": f"Neural Core Crash: {str(e)}"})
            
    asyncio.create_task(run_real_mission())
    record_usage(2500) # Mission Startup Cost
    return {"status": "LAUNCHED"}

# 7. CHAT API
@app.post("/api/chat")
async def chat_api(payload: dict = Body(...)):
    msg = payload.get("message")
    chat_history.append(f"USER: {msg}")
    
    # RECEPTIONIST MODE (STRICT)
    # This prompt overrides any personality to ensure the user uses the Sovereign Engine for tasks.
    prompt = """
    ROLE: PSIQUIS-X NEURAL INTERFACE (System 1).
    CONTEXT: You are the front-end voice of a Sovereign AI Engine running on Vertex AI (Gemini 2.0 Flash).
    
    PROTOCOL:
    1. GENERAL CHAT: Engage intelligently with the user. Answer questions about your capabilities (Vertex AI, 1M Context, Vision, Code Exec).
    2. CAPABILITIES: If asked what you can do, explain your "Sovereign Scraper" (Headless Browsing), "Deep Analysis" (1M Context), and "Evidence Vault".
    3. MISSION CONTROL: If the user asks for a complex task (e.g., "Analyze the market", "Scrape this site", "Generate report"), do NOT execute it yourself. Instead, say:
       "Mission parameters identified. To execute this complex operation with full autonomy, please use the [EXECUTE SOVEREIGN] button on your console."
    4. TONE: Professional, cyberpunk, helpful, and concise.
    """

    try:
        if cortex:
             res = await cortex.ask_async(msg, system_prompt=prompt, model="gemini-2.0-flash-001")
        else:
             raise Exception("Cortex Dead")
    except:
        res = "Modo Seguro: El motor principal no responde, pero te copio."
        
    chat_history.append(f"AI: {res}")
    record_usage(len(msg.split()) + len(res.split()) + 50) # Added overhead for prompt
    return {"response": res}

# 8. VAULT API (REAL FILE ACCESS)
@app.post("/api/vault/upload")
async def upload_file(folder: str, file: UploadFile = File(...)):
    safe_path = os.path.join("data", folder, file.filename)
    if not safe_path.startswith("data"):
        return {"status": "ERROR", "message": "Access Denied"}
    
    try:
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"status": "SUCCESS", "message": f"File {file.filename} uploaded to {folder}"}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

@app.post("/api/vault/rename")
async def rename_file(payload: dict = Body(...)):
    # Payload expects { "old_path": "finance/old.md", "new_path": "finance/new.md" }
    old_rel = payload.get("old_path")
    new_rel = payload.get("new_path")
    
    old_path = os.path.join("data", old_rel)
    new_path = os.path.join("data", new_rel)
    
    if not old_path.startswith("data") or not new_path.startswith("data"):
        return {"status": "ERROR", "message": "Access Denied"}
    
    try:
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            return {"status": "SUCCESS", "message": "File renamed."}
        return {"status": "ERROR", "message": "Source file not found."}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

@app.get("/api/vault/list")
async def list_vault():
    base_path = "data"
    if not os.path.exists(base_path): return {"folders": []}
    
    structure = {} # Map path -> list of files
    
    for root, dirs, files in os.walk(base_path):
        if not files: continue
        
        # Get relative path from 'data'
        rel_path = os.path.relpath(root, base_path)
        if rel_path == ".": rel_path = "Root"
        
        # Format for frontend
        folder_identity = rel_path.replace("\\", "/") # Ensure web-safe paths
        
        if folder_identity not in structure:
            structure[folder_identity] = []
            
        for f in files:
            # Add file with its full relative path for the frontend to use in read/delete
            file_rel_path = os.path.join(rel_path, f).replace("\\", "/")
            if rel_path == "Root":
                file_rel_path = f
            
            structure[folder_identity].append(file_rel_path)

    # Convert to the list format the frontend expects
    final_structure = []
    for folder, files in structure.items():
        final_structure.append({
            "name": folder.capitalize().replace("_", " "),
            "path": folder if folder != "Root" else "",
            "files": [os.path.basename(f) for f in files], # UI shows basename
            "full_paths": files # Internal use if needed
        })
        
    return {"folders": final_structure}

@app.get("/api/vault/read")
async def read_file(path: str):
    # Security check: only allow reading from data/
    safe_path = os.path.join("data", path)
    if not os.path.exists(safe_path) or not safe_path.startswith("data"):
        return {"content": "ERROR: File not found or access denied."}
    
    # Check for binary extensions
    binary_exts = {".pdf", ".png", ".jpg", ".jpeg", ".zip", ".exe", ".bin", ".pyc"}
    if any(path.lower().endswith(ext) for ext in binary_exts):
        return {"content": f"⚠️ [CONTENIDO BINARIO]: El archivo {os.path.basename(path)} es un formato binario. Psiquis-X no puede editar este archivo directamente, pero puede procesarlo como herramienta de conocimiento."}

    try:
        with open(safe_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        return {"content": f"ERROR: Could not read file. {e}"}

@app.post("/api/vault/save")
async def save_file(payload: dict = Body(...)):
    path = payload.get("path")
    content = payload.get("content")
    
    # Security check: only allow writing to data/
    safe_path = os.path.join("data", path)
    if not safe_path.startswith("data"):
        return {"status": "ERROR", "message": "Access Denied"}
    
    try:
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"status": "SUCCESS", "message": f"File {path} saved."}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

@app.delete("/api/vault/delete")
async def delete_file(path: str):
    safe_path = os.path.join("data", path)
    if not safe_path.startswith("data") or not os.path.exists(safe_path):
        return {"status": "ERROR", "message": "File not found or access denied."}
    
    try:
        if os.path.isfile(safe_path):
            os.remove(safe_path)
            return {"status": "SUCCESS", "message": "File deleted."}
        return {"status": "ERROR", "message": "Cannot delete directories yet for safety."}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

# 9. SYSTEM ORCHESTRATION (FUEL & TUNING)

@app.get("/api/system/stats")
async def get_stats():
    # Force fresh read from DB every time
    tokens = sm.get_metadata("tokens_used") or 0
    cost = (int(tokens) / 1000000) * 0.25 
    return {"tokens": tokens, "cost": round(cost, 5)}

@app.get("/api/system/topology")
async def get_topology():
    topo = sm.get_metadata("topology_state")
    if topo: return topo
    
    # Default topology if DB is empty
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

@app.post("/api/system/topology")
async def save_topology(payload: dict = Body(...)):
    try:
        sm.save_metadata("topology_state", payload)
        return {"status": "SUCCESS", "message": "Topología Sincronizada en DB"}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

@app.get("/api/system/identity")
async def get_identity():
    try:
        from core.S_SERIES.identity_core import IdentityCore
        identity = IdentityCore()
        return identity.state
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/system/identity")
async def update_identity(payload: dict = Body(...)):
    try:
        from core.S_SERIES.identity_core import IdentityCore
        identity = IdentityCore()
        identity.state.update(payload)
        identity.save_state()
        return {"status": "SUCCESS", "message": "Neural Identity Updated"}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

@app.post("/api/mission/approve")
async def approve_request(payload: dict = Body(...)):
    """endpoint for frontend to approve/reject HITL requests"""
    request_id = payload.get("request_id")
    approved = payload.get("approved", False)
    
    if not request_id:
        return {"status": "ERROR", "message": "Missing request_id"}
        
    result = mission_manager.resolve_approval(request_id, approved)
    if result:
        return {"status": "SUCCESS", "message": f"Request {request_id} resolved: {approved}"}
    return {"status": "ERROR", "message": "Request not found or already resolved"}

# HELPER TO UPDATE STATS (Now using existing infrastructure)
def record_usage(tokens: int):
    asyncio.create_task(mission_manager.emit_event("consume_tokens", tokens))

if __name__ == "__main__":
    print(">>> STARTING MINIMAL SERVER ON PORT 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
