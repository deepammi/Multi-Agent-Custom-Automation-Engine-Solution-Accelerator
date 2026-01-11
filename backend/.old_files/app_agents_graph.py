"""
DEPRECATED: LangGraph workflow definition.

This file is deprecated as part of the LangGraph Orchestrator Simplification.
Use LinearGraphFactory from app.agents.graph_factory instead.

The old supervisor routing system has been replaced with linear execution
and AI-driven agent sequence generation.
"""
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import AgentState
from app.agents.nodes import (
    planner_node,
    invoice_agent_node,
    approval_checkpoint_node
)
from app.agents.salesforce_node import salesforce_agent_node
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
    DEPRECATED: Create multi-agent LangGraph workflow with supervisor routing.
    
    This function is deprecated. Use LinearGraphFactory.get_default_graph() instead.
    """
    logger.warning("create_agent_graph() is deprecated. Use LinearGraphFactory.get_default_graph() instead.")
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("invoice", invoice_agent_node)
    workflow.add_node("salesforce", salesforce_agent_node)
    
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
            "salesforce": "salesforce",
            "zoho": "zoho",
            "end": END
        }
    )
    
    # Add edges from specialized agents to end
    workflow.add_edge("invoice", END)
    workflow.add_edge("closing", END)
    workflow.add_edge("audit", END)
    workflow.add_edge("salesforce", END)
    workflow.add_edge("zoho", END)
    
    # Compile the graph
    graph = workflow.compile()
    
    logger.info("Multi-agent graph created successfully")
    return graph


# DEPRECATED: Create singleton graph instance
# Use LinearGraphFactory.get_default_graph() instead
logger.warning("agent_graph singleton is deprecated. Use LinearGraphFactory.get_default_graph() instead.")
agent_graph = create_agent_graph()
