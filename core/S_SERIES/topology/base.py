from typing import Annotated, Sequence, TypedDict, List, Dict, Any, Union
from langchain_core.messages import BaseMessage
import operator

class MissionState(TypedDict):
    """
    Estado global de la misión de Psiquis-X.
    Controla el flujo, las tareas y la memoria.
    """
    messages: Annotated[Sequence[BaseMessage], operator.add]
    plan_id: str
    objetivo_general: str
    thread_id: str
    task_ledger: List[Dict[str, Any]] # [ {id, task, status, agent} ]
    artifacts: Dict[str, Any]
    current_agent: str
    next_step: str
    intent_hash: str
    errors: List[str]
    mode: str # 'efficient' | 'sovereign'
    metadata: Dict[str, Any]
