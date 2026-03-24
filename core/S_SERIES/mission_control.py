import json
import asyncio
from typing import Dict, Any, List
from core.S_SERIES.state_manager import StateManager

class MissionControl:
    """
    V7.0 Mission Hub: Unified stream for OTel telemetry and FinOps.
    """
    def __init__(self):
        self.sm = StateManager()
        self.active_sessions = set()
        self.budget_limit = 1.00 # Default $1.00 USD
        
        # Load persistent stats on start
        persistent_tokens = self.sm.get_metadata("tokens_used")
        self.tokens_used = int(persistent_tokens) if persistent_tokens else 0
        self.pending_approvals: Dict[str, asyncio.Event] = {} # HITL Events
        self.approval_results: Dict[str, bool] = {} # Store results

    async def connect(self, websocket):
        self.active_sessions.add(websocket)
        print(f"📡 [MISSION] New Command Center connected. Active: {len(self.active_sessions)}")

    def disconnect(self, websocket):
        self.active_sessions.discard(websocket)
        print(f"📡 [MISSION] Command Center disconnected. Active: {len(self.active_sessions)}")

    async def emit_event(self, event_type: str, data: Any, agent: str = "SYSTEM", log_to_console: bool = True):
        """
        Emits an OTel-aligned event to all connected dashboards.
        Event Types: thought, step, tool_call, error, budget_alert, hitl_request.
        """
        payload = {
            "type": event_type,
            "agent": agent,
            "data": data,
            "timestamp": asyncio.get_event_loop().time(),
            "telemetry": {
                "budget_used": self.tokens_used,
                "status": self.sm.get_metadata("mission_status")
            }
        }
        
        # Log to console for observability (Supervisor mode)
        if log_to_console:
            color_map = {
                "thought": "🧠",
                "step": "📍",
                "error": "❌",
                "hitl_request": "👤",
                "budget_alert": "💰",
                "artifact": "📦"
            }
            icon = color_map.get(event_type, "📡")
            print(f"{icon} [{agent}] {data}")
        
        # Track budgeting
        if event_type == "consume_tokens":
            try:
                # 1. ALWAYS get latest from DB (Source of Truth)
                current = self.sm.get_metadata("tokens_used")
                current_val = int(current) if current is not None else 0
                
                # 2. Increment
                new_total = current_val + int(data)
                self.tokens_used = new_total # Update memory cache
                
                # 3. Save forcefully
                self.sm.save_metadata("tokens_used", new_total)
                print(f"💰 [FINOPS] Saved: {new_total} tokens (+{data})")
                
                if self._check_budget():
                    await self.emit_event("budget_alert", {"msg": "Budget Exceeded!"})
            except Exception as e:
                print(f"⚠️ [FINOPS] Persistence Crash: {e}")

        await self._broadcast_ws(payload)

    async def _broadcast_ws(self, payload: Dict):
        message = json.dumps(payload)
        for ws in list(self.active_sessions):
            try:
                await ws.send_text(message)
            except:
                self.active_sessions.discard(ws)

    async def wait_for_approval(self, action_description: str, agent: str = "SYSTEM") -> bool:
        """
        Pauses execution until human approval via Dashboard.
        Returns True if approved, False if rejected.
        """
        import uuid
        request_id = str(uuid.uuid4())[:8]
        event = asyncio.Event()
        self.pending_approvals[request_id] = event
        
        # 1. Notify Dashboard
        await self.emit_event("hitl_request", {
            "request_id": request_id,
            "action": action_description,
            "status": "pending"
        }, agent=agent)
        
        # 2. Block until resolution
        try:
            print(f"🛑 [HITL] Waiting for approval: {action_description} (ID: {request_id})")
            await event.wait()
            result = self.approval_results.pop(request_id, False)
            
            # 3. Emit resolution
            status_msg = "APPROVED" if result else "REJECTED"
            await self.emit_event("thought", f"Human Decision: {status_msg}", agent=agent)
            return result
        finally:
            self.pending_approvals.pop(request_id, None)

    def resolve_approval(self, request_id: str, approved: bool):
        """Called by API endpoint to unlock the thread."""
        if request_id in self.pending_approvals:
            self.approval_results[request_id] = approved
            self.pending_approvals[request_id].set()
            return True
        return False

    def _check_budget(self) -> bool:
        estimated_cost = (self.tokens_used / 1000000) * 0.10 # Assuming Gemini Flash prices
        return estimated_cost > self.budget_limit

# Singleton
mission_manager = MissionControl()
