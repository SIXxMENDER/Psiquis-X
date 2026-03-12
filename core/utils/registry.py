from typing import Dict, Any, Optional
import logging
from core.interfaces import AgentProtocol

class AgentRegistry:
    """
    Central registry for Psiquis-X agents.
    Acts as a Service Locator to decouple agents from each other.
    """
    _instance = None
    _agents: Dict[str, Any] = {} # Storing Any because modules don't strictly satisfy Protocol at runtime easily without wrappers

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, name: str, agent: Any):
        """
        Register an agent (module or class instance).
        """
        cls._agents[name] = agent
        logging.info(f"✅ [Registry] Agent Registered: {name}")

    @classmethod
    def get(cls, name: str) -> Optional[Any]:
        """
        Retrieve an agent by name.
        """
        agent = cls._agents.get(name)
        if not agent:
            logging.error(f"❌ [Registry] Agent Not Found: {name}")
            return None
        return agent
    
    @classmethod
    def list_agents(cls):
        return list(cls._agents.keys())
