from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import logging

class Skill(BaseModel):
    """
    Represents a capability (Agent) in the system.
    """
    name: str
    description: str
    module_path: str
    input_schema: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {}
    performance_metrics: Dict[str, float] = {"success_rate": 0.0, "avg_latency": 0.0}

class SkillRegistry:
    """
    Central repository of all available skills (Agents).
    Persists to memory (for now) or DB.
    """
    _skills: Dict[str, Skill] = {}

    @classmethod
    def register_skill(cls, skill: Skill):
        cls._skills[skill.name] = skill
        logging.info(f"🧠 [SkillRegistry] Learned new skill: {skill.name}")

    @classmethod
    def get_skill(cls, name: str) -> Optional[Skill]:
        return cls._skills.get(name)

    @classmethod
    def list_skills(cls) -> List[Skill]:
        return list(cls._skills.values())

    @classmethod
    def find_skill_for_task(cls, task_description: str) -> Optional[Skill]:
        """
        Semantic search for a skill (Placeholder for Vector DB search).
        """
        # Simple keyword matching for now
        for skill in cls._skills.values():
            if any(word in task_description.lower() for word in skill.name.lower().split("_")):
                return skill
        return None
