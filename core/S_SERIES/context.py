from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import json

@dataclass
class ExecutionContext:
    """
    Manages the state of a Psiquis-X execution plan.
    Replaces the raw 'estado_global' dictionary.
    """
    job_id: str
    _data: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Safe retrieval of context data."""
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Sets a value in the context."""
        self._data[key] = value
        
    def update(self, data: Dict[str, Any]):
        """Bulk update."""
        self._data.update(data)
        
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary (for backward compatibility)."""
        return self._data
        
    def __repr__(self):
        return f"<ExecutionContext job_id={self.job_id} keys={list(self._data.keys())}>"
