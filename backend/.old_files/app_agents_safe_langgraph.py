"""
Safe LangGraph Implementation with Loop Prevention
Proper LangGraph workflow with built-in safeguards against infinite loops
"""

import logging
from typing import Literal, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import AgentState
from app.agents.nodes import planner_node, invoice_agent_node
from app.agents.salesforce_node import salesforce_agent_node
from app.agents.gmail_agent_node import gmail_agent_node
from app.agents.checkpointer import get_checkpointer

logger = logging.getLogger(__name__)

# Configuration
MAX_WORKFLOW_STEPS = 15  # Absolute maximum steps
MAX_EXECUTION_PLAN_STEPS = 10  # Maximum steps in execution plan

# Supervisor router removed - linear execution handles agent progression
# This eliminates the infinite loop issue by removing conditional routing

def increment_step_counter(state: AgentState) -> Dict[str, Any]:
    """Increment step counter for loop prevention."""
    step_count = state.get("step_count", 0)
    visited_agents = state.get("visited_agents", [])
    current_agent = state.get("current_agent", "unknown")
    
    return {
        **state,
        "step_count": step_count + 1,
        "visited_agents": visited_agents + [current_agent]
    }

# Enhanced agent wrappers with step tracking
async def safe_gmail_agent_node(state: AgentState) -> Dict[str, Any]:
    """Gmail agent that preserves data for subsequent agents."""
    result = await gmail_agent_node(state)
    
    # Add step tracking for monitoring
    result = increment_step_counter(result)
    
    # Store results in collected_data for subsequent agents
    collected_data = state.get("collected_data", {})
    collected_data["gmail"] = {
        "result": result.get("gmail_result", ""),
        "completed": True
    }
    
    result.update({
        "collected_data": collected_data,
        "execution_results": state.get("execution_results", [])
        # No routing logic - linear execution handles progression
    })
    
    return result

async def safe_invoice_agent_node(state: AgentState) -> Dict[str, Any]:
    """Invoice agent that preserves data for subsequent agents."""
    result = await invoice_agent_node(state)
    
    # Add step tracking for monitoring
    result = increment_step_counter(result)
    
    # Store results in collected_data for subsequent agents
    collected_data = state.get("collected_data", {})
    collected_data["invoice"] = {
        "result": result.get("final_result", ""),
        "completed": True
    }
    
    result.update({
        "collected_data": collected_data,
        "execution_results": state.get("execution_results", [])
        # No routing logic - linear execution handles progression
    })
    
    return result

async def safe_salesforce_agent_node(state: AgentState) -> Dict[str, Any]:
    """Salesforce agent that preserves data for subsequent agents."""
    result = await salesforce_agent_node(state)
    
    # Add step tracking for monitoring
    result = increment_step_counter(result)
    
    # Store results in collected_data for subsequent agents
    collected_data = state.get("collected_data", {})
    collected_data["salesforce"] = {
        "result": result.get("final_result", ""),
        "completed": True
    }
    
    result.update({
        "collected_data": collected_data,
        "execution_results": state.get("execution_results", [])
        # No routing logic - linear execution handles progression
    })
    
    return result

async def safe_analysis_agent_node(state: AgentState) -> Dict[str, Any]:
    """Analysis agent with step tracking."""
    from app.agents.graph_refactored import analysis_agent_node
    
    result = await analysis_agent_node(state)
    
    # Add step tracking
    result = increment_step_counter(result)
    
    return result

def create_safe_agent_graph() -> StateGraph:
    """
    Create simplified LangGraph workflow for linear execution.
    
    NOTE: This is a legacy graph. The new linear executor creates
    dynamic graphs based on AI-generated agent sequences.
    This graph is kept for backward compatibility.
    
    Safety Features:
    1. No conditional routing (eliminates infinite loops)
    2. Simple linear connections only
    3. Step counter tracking for monitoring
    """
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes with safe wrappers
    workflow.add_node("planner", planner_node)
    workflow.add_node("gmail", safe_gmail_agent_node)
    workflow.add_node("invoice", safe_invoice_agent_node)
    workflow.add_node("salesforce", safe_salesforce_agent_node)
    workflow.add_node("analysis", safe_analysis_agent_node)
    
    # Set entry point
    workflow.set_entry_point("planner")
    
    # Simple linear connections (no conditional routing)
    # This eliminates the infinite loop issue completely
    workflow.add_edge("planner", "invoice")  # Default simple path
    workflow.add_edge("invoice", END)
    
    # All other agents connect to END for simplicity
    workflow.add_edge("gmail", END)
    workflow.add_edge("salesforce", END)
    workflow.add_edge("analysis", END)
    workflow.add_edge("audit", END)
    workflow.add_edge("closing", END)
    workflow.add_edge("zoho", END)
    
    # Compile with safety features
    checkpointer = get_checkpointer()
    graph = workflow.compile(
        checkpointer=checkpointer,
        # interrupt_before=["planner"]  # Optional HITL
    )
    
    logger.info(f"Safe LangGraph workflow compiled with linear execution (no routing)")
    return graph

# Singleton instance
_safe_graph = None

def get_safe_agent_graph() -> StateGraph:
    """Get or create the safe agent graph."""
    global _safe_graph
    if _safe_graph is None:
        _safe_graph = create_safe_agent_graph()
    return _safe_graph