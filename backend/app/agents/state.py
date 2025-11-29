"""Agent state definitions for LangGraph."""
from typing import TypedDict, Annotated, Sequence, Optional, Any
import operator


class AgentState(TypedDict):
    """State for agent workflow."""
    messages: Annotated[Sequence[str], operator.add]
    plan_id: str
    session_id: str
    task_description: str
    current_agent: str
    next_agent: Optional[str]
    final_result: str
    approval_required: bool
    approved: Optional[bool]
    websocket_manager: Optional[Any]  # WebSocket manager for streaming
    llm_provider: Optional[str]  # Override LLM provider
    llm_temperature: Optional[float]  # Override temperature
