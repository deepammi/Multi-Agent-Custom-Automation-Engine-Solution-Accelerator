"""Agent state definitions for LangGraph."""
from typing import TypedDict, Annotated, Sequence, Optional, Any, Dict, List
from datetime import datetime, timezone
import operator


class AgentState(TypedDict, total=False):
    """
    Simplified state for linear LangGraph agent workflow.
    
    This state supports:
    - Linear agent execution (no conditional routing)
    - Human-in-the-loop approvals
    - Cross-agent data sharing
    - Progress tracking
    - State persistence
    """
    
    # Core identification
    plan_id: str
    session_id: str
    task_description: str
    
    # Linear execution tracking (replaces routing logic)
    agent_sequence: List[str]  # Ordered list of agents to execute
    current_step: int  # Current step in the sequence (0-indexed)
    total_steps: int  # Total number of steps in sequence
    current_agent: str  # Currently executing agent
    
    # Message history (accumulated across agents)
    messages: Annotated[Sequence[str], operator.add]
    
    # Cross-agent data sharing (preserved from original)
    collected_data: Dict[str, Any]  # Data collected by each agent
    execution_results: List[Dict[str, Any]]  # Results from each agent execution
    
    # Execution state
    final_result: str
    start_time: Optional[str]  # ISO timestamp when workflow started
    
    # HITL state
    plan_approved: Optional[bool]  # Plan approval status
    result_approved: Optional[bool]  # Final result approval status
    hitl_feedback: Optional[str]  # Feedback from human reviewer
    approval_required: bool  # Whether approval is required
    awaiting_user_input: bool  # Whether waiting for user input
    user_response: Optional[str]  # User response to clarification
    
    # Extraction state (for invoice/document processing)
    extraction_result: Optional[Any]
    requires_extraction_approval: Optional[bool]
    extraction_approved: Optional[bool]
    
    # Configuration
    websocket_manager: Optional[Any]
    # Note: message_persistence service is accessed via get_message_persistence_service() 
    # in agent nodes to avoid serialization issues with LangGraph checkpointer
    
    # AI Planning integration
    ai_planning_summary: Optional[Dict[str, Any]]  # Results from AI planner


class AgentStateManager:
    """Utility class for managing simplified AgentState operations."""
    
    @staticmethod
    def create_initial_state(
        plan_id: str,
        session_id: str,
        task_description: str,
        agent_sequence: List[str],
        websocket_manager: Optional[Any] = None
    ) -> AgentState:
        """
        Create initial state for linear workflow execution.
        
        Args:
            plan_id: Unique plan identifier
            session_id: Session identifier
            task_description: Task description
            agent_sequence: Ordered list of agents to execute
            websocket_manager: WebSocket manager instance
            
        Returns:
            AgentState: Initial state for workflow
        """
        return AgentState(
            plan_id=plan_id,
            session_id=session_id,
            task_description=task_description,
            agent_sequence=agent_sequence,
            current_step=0,
            total_steps=len(agent_sequence),
            current_agent=agent_sequence[0] if agent_sequence else "",
            messages=[],
            collected_data={},
            execution_results=[],
            final_result="",
            start_time=datetime.now(timezone.utc).isoformat(),
            approval_required=True,
            awaiting_user_input=False
        )
    
    @staticmethod
    def get_current_agent(state: AgentState) -> Optional[str]:
        """Get the current agent that should execute."""
        current_step = state.get("current_step", 0)
        agent_sequence = state.get("agent_sequence", [])
        
        if 0 <= current_step < len(agent_sequence):
            return agent_sequence[current_step]
        return None
    
    # next_agent helper methods removed - linear execution handles agent progression automatically
    
    @staticmethod
    def is_workflow_complete(state: AgentState) -> bool:
        """Check if the workflow is complete."""
        current_step = state.get("current_step", 0)
        total_steps = state.get("total_steps", 0)
        return current_step >= total_steps
    
    @staticmethod
    def add_agent_result(
        state: AgentState,
        agent_name: str,
        result: Dict[str, Any]
    ) -> AgentState:
        """
        Add agent execution result to state with enhanced data passing.
        
        Args:
            state: Current agent state
            agent_name: Name of the agent
            result: Agent execution result
            
        Returns:
            AgentState: Updated state with agent result and enhanced data flow
        """
        # Add to execution results
        execution_results = state.get("execution_results", [])
        execution_results.append({
            "agent": agent_name,
            "step": state.get("current_step", 0),
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        state["execution_results"] = execution_results
        
        # Add to collected data if agent provided data
        if "data" in result:
            collected_data = state.get("collected_data", {})
            collected_data[agent_name] = result["data"]
            state["collected_data"] = collected_data
        
        # Enhanced data passing using orchestrator if available
        try:
            from app.services.enhanced_orchestrator import get_enhanced_orchestrator
            orchestrator = get_enhanced_orchestrator()
            enhanced_updates = orchestrator.enhance_data_passing(state, agent_name, result)
            
            # Apply enhanced updates to state
            for key, value in enhanced_updates.items():
                state[key] = value
                
        except Exception as e:
            # Fallback to basic data passing if orchestrator fails
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Enhanced data passing failed, using basic approach: {e}")
        
        return state
    
    @staticmethod
    def get_progress_info(state: AgentState) -> Dict[str, Any]:
        """
        Get workflow progress information.
        
        Args:
            state: Current agent state
            
        Returns:
            Dict: Progress information
        """
        current_step = state.get("current_step", 0)
        total_steps = state.get("total_steps", 0)
        agent_sequence = state.get("agent_sequence", [])
        
        return {
            "current_step": current_step + 1,  # 1-indexed for display
            "total_steps": total_steps,
            "progress_percentage": (current_step / total_steps * 100) if total_steps > 0 else 0,
            "current_agent": state.get("current_agent", ""),
            "remaining_agents": agent_sequence[current_step + 1:] if current_step + 1 < len(agent_sequence) else [],
            "completed_agents": agent_sequence[:current_step] if current_step > 0 else [],
            "is_complete": current_step >= total_steps
        }