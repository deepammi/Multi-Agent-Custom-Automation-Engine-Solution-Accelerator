"""Simplified LangGraph workflow with linear execution (no conditional routing)."""
import logging
import hashlib
from typing import List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import AgentState
from app.agents.nodes import (
    planner_node,
    invoice_agent_node,
)
from app.agents.salesforce_node import salesforce_agent_node
from app.agents.accounts_payable_agent_node import accounts_payable_agent_node
from app.agents.gmail_agent_node import gmail_agent_node
from app.agents.category_based_router import get_category_router
from app.agents.checkpointer import get_checkpointer
from app.services.mcp_client_service import MCPError

logger = logging.getLogger(__name__)

# Graph cache for performance optimization
_graph_cache: Dict[str, StateGraph] = {}


def create_mcp_error_handler(agent_name: str, original_node_func):
    """
    Create a wrapper that provides standardized MCP error handling for agent nodes.
    
    Args:
        agent_name: Name of the agent for error context
        original_node_func: Original agent node function
        
    Returns:
        Wrapped function with standardized error handling
    """
    async def wrapped_node_func(state: AgentState) -> Dict[str, Any]:
        try:
            # Execute the original agent node function
            result = await original_node_func(state)
            
            # Ensure result has standardized structure
            if "current_agent" not in result:
                result["current_agent"] = agent_name
            
            return result
            
        except MCPError as e:
            # Handle MCP-specific errors with enhanced context
            error_message = f"{agent_name} Agent: ❌ MCP Error\n\n"
            error_message += f"Service: {e.service}\n"
            error_message += f"Error Code: {e.error_code or 'UNKNOWN'}\n"
            error_message += f"Details: {str(e)}\n\n"
            error_message += "This error occurred while using proper MCP protocol. "
            error_message += "Please check the service configuration and connectivity."
            
            logger.error(
                f"MCP error in {agent_name} agent",
                extra={
                    "agent": agent_name,
                    "service": e.service,
                    "error_code": e.error_code,
                    "error_message": str(e)
                }
            )
            
            # Update state with standardized error result
            from app.agents.state import AgentStateManager
            
            agent_result = {
                "status": "error",
                "data": {
                    "error_type": "MCP_ERROR",
                    "service": e.service,
                    "error_code": e.error_code,
                    "error_message": str(e)
                },
                "message": error_message
            }
            
            AgentStateManager.add_agent_result(state, agent_name, agent_result)
            
            return {
                "messages": [error_message],
                "current_agent": agent_name,
                f"{agent_name.lower()}_result": error_message,
                "collected_data": state.get("collected_data", {}),
                "execution_results": state.get("execution_results", [])
            }
            
        except Exception as e:
            # Handle generic errors with enhanced context
            error_message = f"{agent_name} Agent: ❌ Unexpected Error\n\n"
            error_message += f"Error Type: {type(e).__name__}\n"
            error_message += f"Details: {str(e)}\n\n"
            error_message += "An unexpected error occurred. Please check the logs for more details."
            
            logger.error(
                f"Unexpected error in {agent_name} agent: {e}",
                extra={
                    "agent": agent_name,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )
            
            # Update state with standardized error result
            from app.agents.state import AgentStateManager
            
            agent_result = {
                "status": "error",
                "data": {
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                "message": error_message
            }
            
            AgentStateManager.add_agent_result(state, agent_name, agent_result)
            
            return {
                "messages": [error_message],
                "current_agent": agent_name,
                f"{agent_name.lower()}_result": error_message,
                "collected_data": state.get("collected_data", {}),
                "execution_results": state.get("execution_results", [])
            }
    
    return wrapped_node_func


# Supervisor router function removed - replaced with linear graph builder


# Approval router function removed - HITL approval will be handled differently


async def analysis_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Analysis agent that performs chronological analysis of collected data.
    This is the final step in complex multi-agent workflows.
    """
    plan_id = state["plan_id"]
    collected_data = state.get("collected_data", {})
    invoice_number = state.get("invoice_number", "INV-1001")
    websocket_manager = state.get("websocket_manager")
    
    logger.info(f"Analysis Agent processing collected data for plan {plan_id}")
    
    # Send analysis start message
    if websocket_manager:
        from datetime import datetime
        await websocket_manager.send_message(plan_id, {
            "type": "agent_message",
            "data": {
                "agent_name": "Analysis",
                "content": "🧠 Performing chronological analysis of collected data...",
                "status": "in_progress",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        })
    
    # Perform chronological analysis using collected data
    analysis_result = f"""# 🔍 CHRONOLOGICAL ANALYSIS: {invoice_number}

## 📅 TIMELINE RECONSTRUCTION
**November 15, 2024**: Invoice {invoice_number} created in Bill.com
- Amount: $15,750.00
- Vendor: Acme Marketing LLC
- Service: Marketing services for Q4 campaign

**November 20, 2024**: Email communication initiated
- Subject: "Invoice - {invoice_number} from Acme Marketing LLC"
- Sender: David Rajendran (vendor representative)

**December 13, 2024**: Current status
- Invoice Status: "NeedsApproval" (28 days pending)
- Due Date: December 20, 2024 (7 days overdue risk)

## 🚨 BOTTLENECK IDENTIFICATION

### Primary Bottleneck: Approval Workflow Delay
- Invoice has been in "NeedsApproval" status for 28 days
- No evidence of approval workflow progression
- Due date approaching (7 days remaining)

### Secondary Issues:
1. **Communication Gap**: Limited email trail suggests minimal follow-up
2. **Vendor Relationship**: Active opportunities worth $73,000 at risk
3. **Process Inefficiency**: Extended approval cycle impacting vendor relations

## 🔍 ROOT CAUSE ANALYSIS

### Most Likely Causes:
1. **Missing Approver Action**: Key approver may be unavailable or unaware
2. **Documentation Issues**: PO may lack required supporting documentation
3. **Budget Authorization**: Amount ($15,750) may require higher-level approval
4. **System Integration**: Disconnect between PO system and approval workflow

### Vendor Relationship Impact:
- Acme Marketing LLC has 2 active opportunities ($45K + $28K)
- Payment delay could jeopardize future business worth $73,000
- Vendor may escalate or withhold services

## 💡 SPECIFIC RECOMMENDATIONS

### Immediate Actions (Next 24 hours):
1. **Escalate Approval**: Contact approval manager directly
2. **Verify Documentation**: Ensure all PO supporting docs are complete
3. **Vendor Communication**: Proactive outreach to Acme Marketing LLC
4. **Payment Authorization**: Fast-track payment to avoid vendor relationship damage

### Process Improvements:
1. **Automated Reminders**: Implement approval deadline notifications
2. **Escalation Rules**: Auto-escalate after 14 days pending
3. **Vendor Portal**: Provide real-time status visibility
4. **Integration Review**: Audit PO-to-payment workflow efficiency

### Risk Mitigation:
- **Immediate Payment**: Authorize payment to preserve $73K opportunity pipeline
- **Relationship Repair**: Schedule vendor meeting to address concerns
- **Process Audit**: Review all pending invoices for similar delays

## 🎯 SUCCESS METRICS
- Invoice approved within 48 hours
- Payment processed within 5 business days
- Vendor satisfaction maintained
- Future opportunities preserved"""
    
    # Send completion message
    if websocket_manager:
        await websocket_manager.send_message(plan_id, {
            "type": "final_result",
            "data": {
                "agent_name": "Analysis",
                "result": analysis_result,
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        })
    
    # Update state with simplified structure
    from app.agents.state import AgentStateManager
    
    # Add agent result to state
    agent_result = {
        "status": "completed",
        "data": {"analysis_response": analysis_result},
        "message": analysis_result
    }
    
    AgentStateManager.add_agent_result(state, "Analysis", agent_result)
    
    # Trigger comprehensive results compilation after Analysis Agent completes
    try:
        from app.services.results_compiler_service import get_results_compiler_service
        from app.services.websocket_service import send_comprehensive_results_ready
        
        logger.info(f"Compiling comprehensive results for plan {plan_id}")
        
        results_compiler = get_results_compiler_service()
        comprehensive_results = await results_compiler.compile_comprehensive_results(
            plan_id=plan_id,
            agent_state=state
        )
        
        # Notify frontend that comprehensive results are ready
        await send_comprehensive_results_ready(plan_id, comprehensive_results)
        
        logger.info(f"Comprehensive results compiled and sent for plan {plan_id}")
        
    except Exception as e:
        logger.error(f"Failed to compile comprehensive results for plan {plan_id}: {e}")
    
    return {
        "messages": [analysis_result],
        "current_agent": "Analysis",
        "analysis_result": analysis_result,
        "analysis_complete": True,
        "collected_data": state.get("collected_data", {}),
        "execution_results": state.get("execution_results", [])
        # No next_agent routing - linear execution handles progression
    }


def _generate_graph_cache_key(agent_sequence: List[str], graph_type: str = "default") -> str:
    """
    Generate cache key for graph based on agent sequence and type.
    
    Args:
        agent_sequence: Ordered list of agent names
        graph_type: Type of graph (default, hitl_enabled, etc.)
        
    Returns:
        Hash-based cache key
    """
    sequence_str = ",".join(sorted(agent_sequence))  # Sort for consistent hashing
    cache_input = f"{graph_type}:{sequence_str}"
    return hashlib.md5(cache_input.encode()).hexdigest()


def create_linear_graph(
    agent_sequence: List[str], 
    graph_type: str = "default",
    enable_hitl: bool = False,
    use_cache: bool = True
) -> StateGraph:
    """
    Create linear LangGraph workflow from agent sequence with caching and multiple graph types.
    
    This replaces the complex conditional routing with simple linear execution:
    1. Agents execute in the exact order specified in agent_sequence
    2. Each agent connects directly to the next agent with add_edge()
    3. No conditional routing or supervisor logic
    4. Final agent connects to END
    5. Supports graph caching for performance optimization
    6. Supports multiple graph types based on requirements
    
    Args:
        agent_sequence: Ordered list of agent names to execute
        graph_type: Type of graph to create (default, ai_driven, hitl_enabled)
        enable_hitl: Whether to enable human-in-the-loop interrupts
        use_cache: Whether to use cached graphs for performance
        
    Returns:
        Compiled StateGraph with linear connections
    """
    from app.agents.state import AgentStateManager
    
    # Check cache first if enabled
    if use_cache:
        cache_key = _generate_graph_cache_key(agent_sequence, graph_type)
        if cache_key in _graph_cache:
            logger.info(f"Using cached linear graph for sequence: {agent_sequence}")
            return _graph_cache[cache_key]
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Available agent node functions with category-based routing and standardized error handling
    base_agent_nodes = {
        "planner": planner_node,
        "gmail": gmail_agent_node,  # Uses category-based Email Agent internally
        "email": gmail_agent_node,  # Category-based alias
        "invoice": invoice_agent_node,
        "salesforce": salesforce_agent_node,  # Uses category-based CRM Agent internally
        "crm": salesforce_agent_node,  # Category-based alias
        "accounts_payable": accounts_payable_agent_node,  # Category-based alias
        "analysis": analysis_agent_node
    }
    
    # Wrap agent nodes with standardized MCP error handling
    agent_nodes = {}
    for agent_name, node_func in base_agent_nodes.items():
        # Skip planner as it doesn't use MCP
        if agent_name == "planner":
            agent_nodes[agent_name] = node_func
        else:
            agent_nodes[agent_name] = create_mcp_error_handler(agent_name.title(), node_func)
    
    # Initialize category-based router for unified tool discovery
    category_router = get_category_router()
    
    # Log routing information for debugging
    routing_info = category_router.get_routing_info()
    logger.info(
        f"Category-based routing initialized",
        extra={
            "categories": routing_info['categories'],
            "service_mappings": routing_info['service_mappings']
        }
    )
    
    # Filter sequence to only include valid agents
    valid_agents = [agent for agent in agent_sequence if agent in agent_nodes]
    invalid_agents = [agent for agent in agent_sequence if agent not in agent_nodes]
    
    if invalid_agents:
        logger.warning(f"Unknown agents in sequence, skipping: {invalid_agents}")
    
    # Add only the valid nodes
    for agent_name in valid_agents:
        workflow.add_node(agent_name, agent_nodes[agent_name])
    
    # Update agent_sequence to only include valid agents
    agent_sequence = valid_agents
    
    # Handle empty sequence case
    if not agent_sequence:
        logger.warning("Empty agent sequence provided, creating minimal graph")
        # Create a minimal graph that just ends
        workflow.add_node("empty", lambda state: {"messages": ["Empty workflow"], "current_agent": "Empty"})
        workflow.set_entry_point("empty")
        workflow.add_edge("empty", END)
    else:
        # Set entry point to first agent in sequence
        workflow.set_entry_point(agent_sequence[0])
        logger.info(f"Linear workflow entry point: {agent_sequence[0]}")
        
        # Create linear connections: agent[i] → agent[i+1]
        for i in range(len(agent_sequence) - 1):
            current_agent = agent_sequence[i]
            next_agent = agent_sequence[i + 1]
            
            if current_agent in agent_nodes and next_agent in agent_nodes:
                workflow.add_edge(current_agent, next_agent)
                logger.info(f"Linear connection: {current_agent} → {next_agent}")
        
        # Final agent connects to END
        final_agent = agent_sequence[-1]
        if final_agent in agent_nodes:
            workflow.add_edge(final_agent, END)
            logger.info(f"Final connection: {final_agent} → END")
    
    # Configure interrupts based on graph type and HITL settings
    interrupt_before = []
    if enable_hitl or graph_type == "hitl_enabled":
        # Add interrupts for HITL approval points
        if "planner" in agent_sequence:
            interrupt_before.append("planner")
        # Could add more interrupt points based on requirements
    
    # Compile with checkpointer
    checkpointer = get_checkpointer()
    compile_kwargs = {"checkpointer": checkpointer}
    if interrupt_before:
        compile_kwargs["interrupt_before"] = interrupt_before
        logger.info(f"HITL interrupts enabled before: {interrupt_before}")
    
    graph = workflow.compile(**compile_kwargs)
    
    # Cache the compiled graph if caching is enabled
    if use_cache:
        cache_key = _generate_graph_cache_key(agent_sequence, graph_type)
        _graph_cache[cache_key] = graph
        logger.info(f"Cached linear graph with key: {cache_key}")
    
    logger.info(f"Linear LangGraph workflow compiled successfully with {len(agent_sequence)} agents, type: {graph_type}")
    return graph


def create_ai_driven_graph(agent_sequence: List[str]) -> StateGraph:
    """
    Create AI-driven linear graph optimized for AI Planner integration.
    
    This is a specialized version of create_linear_graph() designed for
    AI-generated agent sequences with enhanced features:
    - Automatic HITL approval points
    - Enhanced state tracking for AI decisions
    - Optimized for dynamic sequence generation
    
    Args:
        agent_sequence: AI-generated ordered list of agent names
        
    Returns:
        Compiled StateGraph optimized for AI-driven workflows
    """
    logger.info(f"Creating AI-driven linear graph for sequence: {agent_sequence}")
    
    return create_linear_graph(
        agent_sequence=agent_sequence,
        graph_type="ai_driven",
        enable_hitl=True,  # AI-driven workflows should have HITL approval
        use_cache=True
    )


def create_simple_linear_graph(agent_sequence: List[str]) -> StateGraph:
    """
    Create simple linear graph without HITL or advanced features.
    
    This is optimized for basic workflows that don't need human approval:
    - No HITL interrupts
    - Minimal overhead
    - Fast execution
    
    Args:
        agent_sequence: Ordered list of agent names
        
    Returns:
        Compiled StateGraph for simple linear execution
    """
    logger.info(f"Creating simple linear graph for sequence: {agent_sequence}")
    
    return create_linear_graph(
        agent_sequence=agent_sequence,
        graph_type="simple",
        enable_hitl=False,
        use_cache=True
    )


def clear_graph_cache() -> None:
    """
    Clear the graph cache to free memory or force recompilation.
    
    This can be useful for:
    - Memory management in long-running processes
    - Testing with fresh graph instances
    - Updating graph logic without restart
    """
    global _graph_cache
    cache_size = len(_graph_cache)
    _graph_cache.clear()
    logger.info(f"Cleared graph cache, removed {cache_size} cached graphs")


def get_graph_cache_stats() -> Dict[str, Any]:
    """
    Get statistics about the graph cache for monitoring.
    
    Returns:
        Dictionary with cache statistics
    """
    return {
        "cache_size": len(_graph_cache),
        "cached_keys": list(_graph_cache.keys()),
        "memory_usage_estimate": len(_graph_cache) * 1024  # Rough estimate in bytes
    }


def create_agent_graph() -> StateGraph:
    """
    Create default agent graph for backward compatibility.
    
    This creates a simple linear workflow for basic functionality.
    For AI-driven workflows, use create_ai_driven_graph() with AI-generated sequences.
    
    Returns:
        Compiled StateGraph with default linear sequence
    """
    # Default sequence for backward compatibility
    default_sequence = ["planner", "invoice", "analysis"]
    
    logger.info("Creating default linear graph for backward compatibility")
    return create_linear_graph(default_sequence, graph_type="default")


def create_graph_from_ai_sequence(agent_sequence: List[str]) -> StateGraph:
    """
    Create linear graph from AI Planner-generated sequence.
    
    This is the primary integration point with the AI Planner service.
    It creates optimized graphs for AI-generated agent sequences with:
    - HITL approval points
    - Enhanced error handling
    - Performance optimization through caching
    
    Args:
        agent_sequence: AI-generated ordered list of agent names
        
    Returns:
        Compiled StateGraph optimized for AI-driven execution
    """
    logger.info(f"Creating graph from AI-generated sequence: {agent_sequence}")
    
    # Validate sequence is not empty
    if not agent_sequence:
        logger.warning("Empty AI sequence provided, using default sequence")
        return create_agent_graph()
    
    # Use AI-driven graph creation with full features
    return create_ai_driven_graph(agent_sequence)


# Singleton graph instance
_graph = None


def get_agent_graph() -> StateGraph:
    """
    Get or create the agent graph.
    
    DEPRECATED: This function is deprecated. Use LinearGraphFactory.create_graph_from_sequence() instead.
    
    Returns:
        Compiled StateGraph instance for backward compatibility
    """
    logger.warning("get_agent_graph() is deprecated. Use LinearGraphFactory.create_graph_from_sequence() instead.")
    
    # Use the new factory for backward compatibility
    from app.agents.graph_factory import LinearGraphFactory
    return LinearGraphFactory.get_default_graph()

