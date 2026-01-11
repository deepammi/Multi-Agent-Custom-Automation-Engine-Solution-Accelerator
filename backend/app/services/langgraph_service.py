"""Service layer for LangGraph workflow execution."""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from app.agents.graph_factory import LinearGraphFactory, create_ai_planner_graph
from app.agents.state import AgentState
from app.agents.workflows.factory import WorkflowFactory
from app.services.ai_planner_service import AIPlanner
from app.services.llm_service import LLMService
from app.services.enhanced_orchestrator import get_enhanced_orchestrator
from app.services.message_persistence_service import get_message_persistence_service

logger = logging.getLogger(__name__)


class LangGraphService:
    """Service for executing LangGraph workflows."""
    
    @staticmethod
    def detect_workflow(task_description: str) -> Optional[tuple[str, Dict[str, Any]]]:
        """
        Detect if task matches a workflow template.
        
        Args:
            task_description: Task description
            
        Returns:
            Tuple of (workflow_name, parameters) or None
        """
        task_lower = task_description.lower()
        
        # Check for invoice verification
        if any(word in task_lower for word in ["verify invoice", "check invoice", "cross-check invoice"]):
            # Try to extract invoice ID
            import re
            invoice_match = re.search(r'INV-\d{6}', task_description, re.IGNORECASE)
            if invoice_match:
                return ("invoice_verification", {
                    "invoice_id": invoice_match.group(0),
                    "erp_system": "zoho",
                    "crm_system": "salesforce"
                })
        
        # Check for payment tracking
        if any(word in task_lower for word in ["track payment", "payment status", "check payment"]):
            import re
            invoice_match = re.search(r'INV-\d{6}', task_description, re.IGNORECASE)
            if invoice_match:
                return ("payment_tracking", {
                    "invoice_id": invoice_match.group(0),
                    "erp_system": "zoho"
                })
        
        # Check for customer 360
        if any(word in task_lower for word in ["customer 360", "customer view", "complete view"]):
            # Try to extract customer name
            import re
            # Simple extraction - look for "customer X" or "view of X"
            customer_match = re.search(r'(?:customer|view of|for)\s+([A-Z][a-zA-Z\s]+?)(?:\s|$)', task_description)
            if customer_match:
                return ("customer_360", {
                    "customer_name": customer_match.group(1).strip()
                })
        
        return None
    
    @staticmethod
    async def execute_task_with_ai_planner(
        plan_id: str,
        session_id: str,
        task_description: str,
        websocket_manager: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a task using AI Planner for dynamic agent sequence generation.
        Enhanced with improved multi-agent coordination.
        
        This is the new recommended approach that uses the AI Planner to generate
        optimal agent sequences and the LinearGraphFactory to create graphs.
        
        Args:
            plan_id: Unique plan identifier
            session_id: Session identifier
            task_description: Task to execute
            websocket_manager: Optional WebSocket manager for real-time updates
            
        Returns:
            Dict with execution results
        """
        try:
            logger.info(f"🚀 Starting enhanced AI-driven task execution for plan {plan_id}")
            
            # Re-check for active WebSocket connections at execution time
            # This handles the case where WebSocket connects after task submission
            if websocket_manager is not None:
                # Use the provided websocket_manager for connection checking
                if hasattr(websocket_manager, 'get_connection_count'):
                    connection_count = websocket_manager.get_connection_count(plan_id)
                    if connection_count == 0:
                        logger.info(f"No active WebSocket connection for plan {plan_id} at execution time, disabling HITL")
                        websocket_manager = None
                    else:
                        logger.info(f"Active WebSocket connection found for plan {plan_id} at execution time, HITL enabled")
                else:
                    # Fallback to global websocket manager if the passed one doesn't have get_connection_count
                    from app.services.websocket_service import get_websocket_manager
                    current_websocket_manager = get_websocket_manager()
                    if current_websocket_manager.get_connection_count(plan_id) == 0:
                        logger.info(f"No active WebSocket connection for plan {plan_id} at execution time, disabling HITL")
                        websocket_manager = None
                    else:
                        logger.info(f"Active WebSocket connection found for plan {plan_id} at execution time, HITL enabled")
            
            # Initialize enhanced orchestrator for improved coordination
            orchestrator = get_enhanced_orchestrator()
            
            # Analyze task requirements using enhanced orchestrator
            task_analysis = orchestrator.analyze_task_requirements(task_description)
            
            # Initialize AI Planner
            llm_service = LLMService()
            ai_planner = AIPlanner(llm_service)
            
            # Initialize message persistence service
            message_persistence = get_message_persistence_service()
            
            # Generate AI-driven workflow plan
            planning_summary = await ai_planner.plan_workflow(task_description)
            
            if not planning_summary.success:
                logger.warning(f"AI planning failed, using enhanced orchestrator fallback")
                # Use enhanced orchestrator for optimal sequence generation
                required_agents = task_analysis["required_agents"]
                agent_sequence = orchestrator.generate_optimal_sequence(required_agents, task_analysis)
                
                # Create fallback sequence object for graph creation
                from app.models.ai_planner import AgentSequence, TaskAnalysis
                
                # Create TaskAnalysis object with all required fields
                task_analysis_obj = TaskAnalysis(
                    complexity="medium",  # Default complexity
                    required_systems=["llm"],  # Default systems
                    business_context=task_analysis.get("task_type", "general"),
                    data_sources_needed=["user_input"],  # Default data sources
                    estimated_agents=list(required_agents),
                    confidence_score=task_analysis.get("complexity_score", 0.5),
                    reasoning=f"Enhanced orchestrator fallback for {task_analysis.get('task_type', 'general')} task"
                )
                
                fallback_sequence = AgentSequence(
                    agents=agent_sequence,
                    reasoning={agent: f"Selected by enhanced orchestrator for {task_analysis['task_type']}" for agent in agent_sequence},
                    complexity_score=task_analysis["complexity_score"],
                    estimated_duration=int(task_analysis["estimated_duration"]),
                    task_analysis=task_analysis_obj
                )
                graph = LinearGraphFactory.create_graph_from_ai_sequence(fallback_sequence)
            else:
                logger.info(f"✅ AI planning successful: {' → '.join(planning_summary.agent_sequence.agents)}")
                agent_sequence = planning_summary.agent_sequence.agents
                
                # Validate and enhance the AI-generated sequence
                validation = orchestrator.validate_execution_order(agent_sequence)
                if not validation.is_valid:
                    logger.warning(f"AI sequence validation failed, generating optimal sequence")
                    # Generate optimal sequence as fallback
                    required_agents = set(agent_sequence)
                    agent_sequence = orchestrator.generate_optimal_sequence(required_agents, task_analysis)
                    
                    # Update planning summary with corrected sequence
                    planning_summary.agent_sequence.agents = agent_sequence
                
                # Disable HITL if no WebSocket manager is provided (for testing)
                enable_hitl = websocket_manager is not None
                logger.info(f"HITL enabled: {enable_hitl} (WebSocket manager present: {websocket_manager is not None})")
                
                graph = LinearGraphFactory.create_graph_from_ai_sequence(
                    planning_summary.agent_sequence, 
                    enable_hitl=enable_hitl
                )
            
            # Create initial state with enhanced coordination data
            initial_state: AgentState = {
                "plan_id": plan_id,
                "session_id": session_id,
                "task_description": task_description,
                "agent_sequence": agent_sequence,
                "current_step": 0,
                "total_steps": len(agent_sequence),
                "current_agent": agent_sequence[0] if agent_sequence else "",
                "messages": [],
                "collected_data": {},
                "execution_results": [],
                "final_result": "",
                "start_time": None,
                "plan_approved": None,
                "result_approved": None,
                "hitl_feedback": None,
                "approval_required": True,
                "awaiting_user_input": False,
                "ai_planning_summary": {
                    "task_analysis": planning_summary.task_analysis.__dict__ if planning_summary.success else task_analysis,
                    "agent_sequence": planning_summary.agent_sequence.__dict__ if planning_summary.success else None,
                    "total_duration": planning_summary.total_duration,
                    "success": planning_summary.success
                },
                # Enhanced orchestration data
                "orchestration_metadata": {
                    "task_analysis": task_analysis,
                    "sequence_validation": validation.__dict__ if 'validation' in locals() else None,
                    "enhanced_coordination": True
                },
                # Store WebSocket availability flag instead of the manager object
                "websocket_available": websocket_manager is not None
                # Note: WebSocket manager is accessed via get_websocket_manager() in agent nodes
                # to avoid serialization issues with LangGraph checkpointer
            }
            
            # Coordinate agent execution with enhanced orchestrator
            coordination_summary = await orchestrator.coordinate_agent_execution(
                agent_sequence, initial_state, websocket_manager
            )
            
            # Create config with thread ID
            config = {"configurable": {"thread_id": f"plan_{plan_id}"}}
            
            # Execute graph with enhanced coordination
            logger.info(f"🎯 Executing enhanced AI-driven LangGraph workflow for plan {plan_id}")
            result = await graph.ainvoke(initial_state, config)
            
            logger.info(f"✅ Enhanced AI-driven LangGraph execution completed for plan {plan_id}")
            
            return {
                "status": "completed",
                "plan_id": plan_id,
                "current_agent": result.get("current_agent"),
                "final_result": result.get("final_result"),
                "messages": result.get("messages", []),
                "agent_sequence": agent_sequence,
                "ai_planning_summary": planning_summary.__dict__ if planning_summary.success else None,
                "orchestration_summary": coordination_summary,
                "task_analysis": task_analysis
            }
            
        except Exception as e:
            logger.error(f"❌ Enhanced AI-driven LangGraph execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "plan_id": plan_id,
                "error": str(e)
            }
    
    @staticmethod
    async def execute_task(
        plan_id: str,
        session_id: str,
        task_description: str,
        websocket_manager: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a task using LangGraph workflow or workflow template.
        
        Args:
            plan_id: Unique plan identifier
            session_id: Session identifier
            task_description: Task to execute
            websocket_manager: Optional WebSocket manager for real-time updates
            
        Returns:
            Dict with execution results
        """
        try:
            # Check if task matches a workflow template
            workflow_match = LangGraphService.detect_workflow(task_description)
            
            if workflow_match:
                workflow_name, parameters = workflow_match
                logger.info(f"Detected workflow template: {workflow_name}")
                
                # Execute workflow template
                result = await WorkflowFactory.execute_workflow(
                    workflow_name=workflow_name,
                    plan_id=plan_id,
                    session_id=session_id,
                    parameters=parameters
                )
                
                return result
            
            # No workflow match - use new graph factory with default sequence
            logger.info(f"Using LinearGraphFactory default graph for plan {plan_id}")
            graph = LinearGraphFactory.get_default_graph()
            
            # Initialize message persistence service
            message_persistence = get_message_persistence_service()
            
            # Create initial state using simplified AgentState
            default_sequence = ["planner", "invoice"]
            initial_state: AgentState = {
                "plan_id": plan_id,
                "session_id": session_id,
                "task_description": task_description,
                "agent_sequence": default_sequence,
                "current_step": 0,
                "total_steps": len(default_sequence),
                "current_agent": default_sequence[0],
                "messages": [],
                "collected_data": {},
                "execution_results": [],
                "final_result": "",
                "start_time": None,
                "plan_approved": None,
                "result_approved": None,
                "hitl_feedback": None,
                "approval_required": False,
                "awaiting_user_input": False,
                # Add WebSocket manager to state (if available)
                "websocket_manager": websocket_manager
                # Note: message_persistence service is accessed via get_message_persistence_service() 
                # in agent nodes to avoid serialization issues with LangGraph checkpointer
            }
            
            # Create config with thread ID
            config = {"configurable": {"thread_id": f"plan_{plan_id}"}}
            
            # Execute graph
            logger.info(f"Executing LangGraph workflow for plan {plan_id}")
            result = await graph.ainvoke(initial_state, config)
            
            logger.info(f"LangGraph execution completed for plan {plan_id}")
            
            return {
                "status": "completed",
                "plan_id": plan_id,
                "current_agent": result.get("current_agent"),
                "final_result": result.get("final_result"),
                "messages": result.get("messages", []),
            }
            
        except Exception as e:
            logger.error(f"LangGraph execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "plan_id": plan_id,
                "error": str(e)
            }
    
    @staticmethod
    async def get_state(plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current state for a plan.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Current state or None
        """
        try:
            graph = LinearGraphFactory.get_default_graph()
            config = {"configurable": {"thread_id": f"plan_{plan_id}"}}
            
            # Get state from checkpointer
            state = await graph.aget_state(config)
            
            if state and state.values:
                return dict(state.values)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get state: {e}")
            return None
    
    @staticmethod
    async def get_agent_state(plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current agent state for a plan (alias for get_state).
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Current agent state or None
        """
        return await LangGraphService.get_state(plan_id)
    
    @staticmethod
    async def resume_execution(
        plan_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resume execution with state updates (for HITL).
        
        Args:
            plan_id: Plan identifier
            updates: State updates to apply
            
        Returns:
            Execution results
        """
        try:
            graph = LinearGraphFactory.get_default_graph()
            config = {"configurable": {"thread_id": f"plan_{plan_id}"}}
            
            # Resume with updates
            logger.info(f"Resuming execution for plan {plan_id}")
            result = await graph.ainvoke(updates, config)
            
            return {
                "status": "completed",
                "plan_id": plan_id,
                "current_agent": result.get("current_agent"),
                "final_result": result.get("final_result"),
            }
            
        except Exception as e:
            logger.error(f"Failed to resume execution: {e}", exc_info=True)
            return {
                "status": "error",
                "plan_id": plan_id,
                "error": str(e)
            }
    
    @staticmethod
    async def resume_execution_with_revision(
        plan_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resume execution with targeted revision support.
        Task 8: Handles agent-specific revisions and context preservation.
        
        Args:
            plan_id: Plan identifier
            updates: State updates including revision instruction
            
        Returns:
            Execution results
        """
        try:
            graph = LinearGraphFactory.get_default_graph()
            config = {"configurable": {"thread_id": f"plan_{plan_id}"}}
            
            # Get current state
            current_state = await LangGraphService.get_state(plan_id)
            if not current_state:
                logger.error(f"No current state found for plan {plan_id}")
                return {
                    "status": "error",
                    "plan_id": plan_id,
                    "error": "No current state found"
                }
            
            # Extract revision instruction
            revision_instruction = updates.get("revision_instruction", {})
            preserve_results = set(revision_instruction.get("preserve_results", []))
            rerun_agents = set(revision_instruction.get("rerun_agents", []))
            
            logger.info(f"🎯 Resuming with targeted revision for plan {plan_id}")
            logger.info(f"   Preserve: {preserve_results}")
            logger.info(f"   Re-run: {rerun_agents}")
            
            # Prepare enhanced state for targeted revision
            enhanced_updates = {**updates}
            
            # Preserve agent results that don't need revision
            if preserve_results and "agent_results" in current_state:
                preserved_results = {}
                for agent in preserve_results:
                    if agent in current_state["agent_results"]:
                        preserved_results[agent] = current_state["agent_results"][agent]
                        logger.info(f"   Preserving results from {agent}")
                
                enhanced_updates["preserved_agent_results"] = preserved_results
            
            # Mark agents for re-execution
            if rerun_agents:
                enhanced_updates["rerun_agents"] = list(rerun_agents)
                enhanced_updates["revision_mode"] = True
                
                # Reset execution state for targeted agents
                if "agent_sequence" in current_state:
                    # Find the earliest agent that needs re-running
                    agent_sequence = current_state["agent_sequence"]
                    earliest_rerun_index = len(agent_sequence)
                    
                    for i, agent in enumerate(agent_sequence):
                        if agent in rerun_agents:
                            earliest_rerun_index = min(earliest_rerun_index, i)
                    
                    # Reset current step to earliest re-run agent
                    if earliest_rerun_index < len(agent_sequence):
                        enhanced_updates["current_step"] = earliest_rerun_index
                        enhanced_updates["current_agent"] = agent_sequence[earliest_rerun_index]
                        logger.info(f"   Resetting execution to step {earliest_rerun_index} ({agent_sequence[earliest_rerun_index]})")
            
            # Add revision metadata
            enhanced_updates["revision_metadata"] = {
                "revision_type": revision_instruction.get("type", "unknown"),
                "revision_scope": revision_instruction.get("scope", "unknown"),
                "iteration_count": revision_instruction.get("iteration_count", 0) + 1,
                "confidence_score": revision_instruction.get("confidence_score", 0.0),
                "targets": revision_instruction.get("targets", []),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Resume execution with enhanced revision support
            logger.info(f"🔄 Executing targeted revision for plan {plan_id}")
            result = await graph.ainvoke(enhanced_updates, config)
            
            return {
                "status": "completed",
                "plan_id": plan_id,
                "current_agent": result.get("current_agent"),
                "final_result": result.get("final_result"),
                "revision_applied": True,
                "revision_metadata": enhanced_updates["revision_metadata"]
            }
            
        except Exception as e:
            logger.error(f"Failed to resume execution with revision: {e}", exc_info=True)
            return {
                "status": "error",
                "plan_id": plan_id,
                "error": str(e)
            }

