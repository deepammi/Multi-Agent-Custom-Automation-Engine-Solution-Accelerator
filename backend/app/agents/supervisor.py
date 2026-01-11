"""
Supervisor logic for routing between agents.

NOTE: This file is deprecated as part of the LangGraph Orchestrator Simplification.
The supervisor_router function has been eliminated in favor of linear execution.
All routing is now handled by the AI Planner Service and linear graph structures.

This file is kept for backward compatibility but should not be used in new implementations.
"""
import logging
from typing import Literal

from app.agents.state import AgentState

logger = logging.getLogger(__name__)


# DEPRECATED: This function has been eliminated per Requirements 4.1
# Use linear execution with AI Planner Service instead
def supervisor_router(state: AgentState) -> Literal["end"]:
    """
    DEPRECATED: Supervisor router function has been eliminated.
    
    This function is no longer used in the simplified LangGraph orchestrator.
    All routing is now handled by:
    1. AI Planner Service for sequence generation
    2. Linear graph structures with static connections
    3. AgentState.agent_sequence for execution order
    
    Always returns "end" to prevent any routing logic.
    """
    logger.warning("supervisor_router is deprecated and should not be used")
    return "end"
