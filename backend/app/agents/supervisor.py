"""Supervisor logic for routing between agents."""
import logging
from typing import Literal

from app.agents.state import AgentState

logger = logging.getLogger(__name__)


def supervisor_router(state: AgentState) -> Literal["invoice", "closing", "audit", "end"]:
    """
    Supervisor router - decides which agent to call next.
    Phase 5: Routes based on planner's decision.
    """
    next_agent = state.get("next_agent")
    
    if next_agent:
        logger.info(f"Supervisor routing to: {next_agent}")
        return next_agent
    else:
        logger.info("Supervisor routing to: end")
        return "end"
