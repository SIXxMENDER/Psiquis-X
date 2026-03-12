import sqlite3
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

class StateManager:
    def __init__(self, db_path: str = "data/psiquis_state.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            # Persistent results for jobs (Mission Isolated)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS job_state (
                    thread_id TEXT,
                    job_id TEXT,
                    result TEXT,
                    timestamp TEXT,
                    PRIMARY KEY (thread_id, job_id)
                )
            """)
            # Global mission metadata
            conn.execute("""
                CREATE TABLE IF NOT EXISTS global_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            # NEW: Checkpoints for Time Travel (Durable Execution)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT,
                    step_name TEXT,
                    state_snapshot TEXT,
                    timestamp TEXT
                )
            """)
            # NEW: Semantic Cache (FinOps)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS semantic_cache (
                    prompt_hash TEXT PRIMARY KEY,
                    response TEXT,
                    timestamp TEXT
                )
            """)
            # NEW: Paused Missions (Migration from JSON)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS paused_missions (
                    plan_id TEXT PRIMARY KEY,
                    job_id TEXT,
                    reason TEXT,
                    paused_at TEXT,
                    context TEXT
                )
            """)

    def save_metadata(self, key: str, value: Any):
        with sqlite3.connect(self.db_path) as conn:
            # Ensure we are saving as a stringified JSON if it's a dict/list
            val_to_save = json.dumps(value) if not isinstance(value, (str, int, float)) else str(value)
            conn.execute("INSERT OR REPLACE INTO global_metadata (key, value) VALUES (?, ?)", 
                         (key, val_to_save))
            conn.commit()
            print(f"💾 [STATE] Persisted {key} -> {val_to_save}")

    def get_metadata(self, key: str) -> Optional[Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT value FROM global_metadata WHERE key = ?", (key,))
            row = cursor.fetchone()
            if not row: return None
            val = row[0]
            try:
                return json.loads(val)
            except:
                return val

    def update_job_result(self, thread_id: str, job_id: str, result: Any):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO job_state (thread_id, job_id, result, timestamp) VALUES (?, ?, ?, ?)",
                         (thread_id, job_id, json.dumps(result), datetime.now().isoformat()))

    def get_job_result(self, thread_id: str, job_id: str) -> Optional[Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT result FROM job_state WHERE thread_id = ? AND job_id = ?", (thread_id, job_id))
            row = cursor.fetchone()
            return json.loads(row[0]) if row else None

    # --- DURABLE EXECUTION (TIME TRAVEL) ---

    def create_checkpoint(self, thread_id: str, step_name: str, state: Dict[str, Any]):
        """Saves a full snapshot of the state at a specific step."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO checkpoints (thread_id, step_name, state_snapshot, timestamp)
                VALUES (?, ?, ?, ?)
            """, (thread_id, step_name, json.dumps(state), datetime.now().isoformat()))
            print(f"📍 [STATE] Checkpoint created: {step_name} (Thread: {thread_id})")

    def get_history(self, thread_id: str):
        """Returns all checkpoints for a mission thread."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, step_name, timestamp FROM checkpoints 
                WHERE thread_id = ? ORDER BY id ASC
            """, (thread_id,))
            return [{"id": r[0], "step": r[1], "time": r[2]} for r in cursor.fetchall()]

    def load_checkpoint(self, checkpoint_id: int) -> Optional[Dict[str, Any]]:
        """Loads a specific state snapshot."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT state_snapshot FROM checkpoints WHERE id = ?", (checkpoint_id,))
            row = cursor.fetchone()
            return json.loads(row[0]) if row else None

    def rewind_to(self, thread_id: str, checkpoint_id: int):
        """Deletes all checkpoints AFTER the specified one and returns the target state."""
        with sqlite3.connect(self.db_path) as conn:
            # Delete newer checkpoints
            conn.execute("DELETE FROM checkpoints WHERE thread_id = ? AND id > ?", (thread_id, checkpoint_id))
            # Get the target state
            return self.load_checkpoint(checkpoint_id)

    def get_all_state(self, thread_id: str = "DEFAULT") -> Dict[str, Any]:
        state = {}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT job_id, result FROM job_state WHERE thread_id = ?", (thread_id,))
            for job_id, result in cursor.fetchall():
                state[job_id] = json.loads(result)
            cursor = conn.execute("SELECT key, value FROM global_metadata")
            for key, value in cursor.fetchall():
                state[key] = json.loads(value)
        return state

    def clear_state(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self._init_db()

    # --- FINOPS: CACHE & PRUNING ---

    def check_cache(self, prompt: str) -> Optional[str]:
        """Checks if a similar prompt has been answered before."""
        import hashlib
        p_hash = hashlib.sha256(prompt.encode()).hexdigest()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT response FROM semantic_cache WHERE prompt_hash = ?", (p_hash,))
            row = cursor.fetchone()
            return row[0] if row else None

    def save_to_cache(self, prompt: str, response: str):
        """Saves a prompt-response pair to avoid redundant costs."""
        import hashlib
        p_hash = hashlib.sha256(prompt.encode()).hexdigest()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO semantic_cache (prompt_hash, response, timestamp) VALUES (?, ?, ?)",
                         (p_hash, response, datetime.now().isoformat()))

    def prune_context(self, messages: List[Dict[str, Any]], max_turns: int = 5) -> List[Dict[str, Any]]:
        """
        Compresses older messages to keep context window small.
        (Nivel 5 FinOps Implementation)
        """
        if len(messages) <= max_turns:
            return messages
        
        # Keep the last 2 messages intact
        recent = messages[-2:]
        to_summarize = messages[:-2]
        
        # In a real scenario, we'd use a small model here. 
        # For now, we simulate a summary placeholder.
        summary = {"role": "system", "content": f"[RESUMEN DE CONTEXTO]: Se omitieron {len(to_summarize)} turnos previos para optimizar costos."}
        return [summary] + recent

    # --- MISSION PAUSE/RESUME (Consolidated) ---

    def pause_mission(self, plan_id: str, job_id: str, reason: str, context: Optional[Dict[str, Any]] = None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO paused_missions (plan_id, job_id, reason, paused_at, context)
                VALUES (?, ?, ?, ?, ?)
            """, (plan_id, job_id, reason, datetime.now().isoformat(), json.dumps(context or {})))
            print(f"⏸️ [STATE] Mission '{plan_id}' paused at {job_id}. Reason: {reason}")

    def resume_mission(self, plan_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT job_id, reason, context FROM paused_missions WHERE plan_id = ?", (plan_id,))
            row = cursor.fetchone()
            if row:
                conn.execute("DELETE FROM paused_missions WHERE plan_id = ?", (plan_id,))
                print(f"▶️ [STATE] Mission '{plan_id}' resumed.")
                return {
                    "job_id": row[0],
                    "reason": row[1],
                    "context": json.loads(row[2])
                }
        return None

    def is_paused(self, plan_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT 1 FROM paused_missions WHERE plan_id = ?", (plan_id,))
            return cursor.fetchone() is not None
