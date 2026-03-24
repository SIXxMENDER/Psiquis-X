from typing import Protocol, Dict, Any, runtime_checkable

@runtime_checkable
class AgentProtocol(Protocol):
    """
    Standard interface for all Psiquis-X agents.
    """
    async def ejecutar(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Main execution method.
        Args:
            **kwargs: Input parameters defined by the agent's Pydantic Input model.
        Returns:
            Dict[str, Any]: Output data defined by the agent's Pydantic Output model.
        """
        ...
