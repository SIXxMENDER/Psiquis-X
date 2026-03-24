import os
import time
import uuid
import logging
import json
from typing import Dict, Any, Optional, List, Set

# Phase 5.1: Audit Log for Agent accountability
LOGS_DIR = os.path.join(os.getcwd(), "logs")
AUDIT_LOG = os.path.join(LOGS_DIR, "nhi_passports.jsonl")

class NHIModule:
    """
    Manages Non-Human Identities for Psiquis-X Agents.
    """
    def __init__(self):
        self.active_sessions = {} # agent_id -> {token, expire_at, permissions}
        self.agent_passports = {} # agent_name -> {last_seen, successes, failures}
        if not os.path.exists(LOGS_DIR):
            os.makedirs(LOGS_DIR, exist_ok=True)

    def _log_audit(self, entry: Dict[str, Any]):
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({**entry, "timestamp": time.time()}) + "\n")

    def grant_jit_access(self, agent_name: str, scope: List[str]) -> str:
        """
        Creates a temporary access token for an agent with a specific scope.
        """
        session_id = str(uuid.uuid4())
        self.active_sessions[agent_name] = {
            "token": session_id,
            "expires": time.time() + 1800,
            "scope": scope
        }
        
        self._log_audit({"agent": agent_name, "event": "GRANT", "scope": scope})
        logging.info(f"🆔 NHI: Just-in-Time access granted to '{agent_name}' [Scope: {scope}]")
        return session_id

    def record_usage(self, agent_name: str, action: str, result: str = "SUCCESS"):
        """Nivel 5: Records an entry in the Agent's Passport."""
        self._log_audit({"agent": agent_name, "event": "ACTION", "action": action, "result": result})

    def verify_access(self, agent_name: str, token: str, required_scope: str) -> bool:
        """Checks if a token is valid and has the required scope."""
        session = self.active_sessions.get(agent_name)
        if not session: return False
        if session["token"] != token: return False
        if time.time() > session["expires"]:
            logging.warning(f"🚨 NHI: Token for '{agent_name}' expired.")
            return False
        return required_scope in session["scope"]

nhi = NHIModule()
