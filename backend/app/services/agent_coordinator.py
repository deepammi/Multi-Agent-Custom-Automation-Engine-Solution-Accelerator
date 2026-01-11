"""Agent Coordination Layer."""
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass

from app.models.ai_planner import AgentSequence
from app.agents.state import AgentState
from app.services.websocket_service import get_websocket_manager

logger = logging.getLogger(__name__)

class AgentExecutionStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class AgentExecutionResult:
    agent_name: str
    status: AgentExecutionStatus
    result_data: Dict[str, Any]
    execution_time: float
    error_message: Optional[str] = None

class CoordinationStrategy(Enum):
    SEQUENTIAL = "sequential"

class AgentCoordinator:
    def __init__(self):
        self.websocket_manager = get_websocket_manager()
    
    async def coordinate_dynamic_execution(self, plan_id: str, session_id: str, 
                                         task_description: str, agent_sequence: AgentSequence,
                                         state: AgentState, coordination_strategy=None):
        return {"status": "completed", "plan_id": plan_id}

_agent_coordinator: Optional[AgentCoordinator] = None

def get_agent_coordinator() -> AgentCoordinator:
    global _agent_coordinator
    if _agent_coordinator is None:
        _agent_coordinator = AgentCoordinator()
    return _agent_coordinator

def reset_agent_coordinator() -> None:
    global _agent_coordinator
    _agent_coordinator = None
