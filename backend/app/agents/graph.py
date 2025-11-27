"""LangGraph workflow definition."""
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import AgentState
from app.agents.nodes import (
    planner_node,
    invoice_agent_node,
    closing_agent_node,
    audit_agent_node,
    approval_checkpoint_node
)
from app.agents.supervisor import supervisor_router

logger = logging.getLogger(__name__)


def should_continue_after_approval(state: AgentState) -> str:
    """Check if approval was granted."""
    if state.get("approved") is True:
        return "continue"
    else:
        return "end"


def create_agent_graph():
    """
    Create multi-agent LangGraph workflow with supervisor routing.
    Phase 6: Simplified - approval handled in service layer, not graph.
    """
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("invoice", invoice_agent_node)
    workflow.add_node("closing", closing_agent_node)
    workflow.add_node("audit", audit_agent_node)
    
    # Set entry point
    workflow.set_entry_point("planner")
    
    # Add conditional edges from planner (supervisor routing)
    workflow.add_conditional_edges(
        "planner",
        supervisor_router,
        {
            "invoice": "invoice",
            "closing": "closing",
            "audit": "audit",
            "end": END
        }
    )
    
    # Add edges from specialized agents to end
    workflow.add_edge("invoice", END)
    workflow.add_edge("closing", END)
    workflow.add_edge("audit", END)
    
    # Compile the graph
    graph = workflow.compile()
    
    logger.info("Multi-agent graph created successfully")
    return graph


# Create singleton graph instance
agent_graph = create_agent_graph()
