from core.S_SERIES.state_manager import StateManager
from typing import Dict, Any

class IdentityCore:
    """
    Module 12: Integrated Vision.
    The system's "Self." Maintains long-term consistency in the DB.
    """
    def __init__(self):
        self.sm = StateManager()
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        data = self.sm.get_metadata("identity_state")
        if data: return data
        
        return {
            "master_goal": "Serve as a high-value autonomous strategist.",
            "personality": {
                "name": "Psiquis-X",
                "traits": ["Rigor", "Calm", "Efficiency", "Curiosity"]
            },
            "memory_index": [],
            "evolution_level": 1
        }

    def save_state(self):
        self.sm.save_metadata("identity_state", self.state)

    def get_vision(self) -> str:
        return self.state["master_goal"]

    def update_vision(self, new_goal: str):
        print(f"👁️ [Identity] Vision Shift: {self.state['master_goal']} -> {new_goal}")
        self.state["master_goal"] = new_goal
        self.save_state()

    def reflect(self, experience: str):
        """Integra una experiencia en la memoria a largo plazo."""
        self.state["memory_index"].append(experience)
        if len(self.state["memory_index"]) > 100:
            self.state["memory_index"].pop(0)
        self.save_state()
