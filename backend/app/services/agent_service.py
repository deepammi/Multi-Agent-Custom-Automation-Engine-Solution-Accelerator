"""Agent orchestration service."""
import logging
from typing import Dict, Any, List
from datetime import datetime
import uuid
import asyncio

from app.agents.graph import agent_graph
from app.agents.state import AgentState
from app.agents.nodes import planner_node, invoice_agent_node, closing_agent_node, audit_agent_node, hitl_agent_node
from app.db.repositories import PlanRepository, MessageRepository
from app.models.message import AgentMessage
from app.services.websocket_service import websocket_manager

logger = logging.getLogger(__name__)


class ExecutionContext:
    """Context manager for maintaining execution state across loops."""
    
    def __init__(self, original_task: str, plan_id: str):
        self.original_task = original_task
        self.plan_id = plan_id
        self.execution_history: List[Dict[str, Any]] = []
        self.iteration_count = 0
        self.current_specialized_agent = None  # Track which agent is processing
    
    def add_history_entry(self, iteration: int, agent: str, result: str, user_feedback: str = None):
        """Add an entry to execution history.
        
        **Feature: multi-agent-hitl-loop, Property 2: Context Preservation**
        **Validates: Requirements 2.1, 2.2**
        """
        entry = {
            "iteration": iteration,
            "agent": agent,
            "result": result
        }
        if user_feedback:
            entry["user_feedback"] = user_feedback
        self.execution_history.append(entry)
    
    def get_context_for_planner(self) -> str:
        """Get formatted context for planner when looping back."""
        context = f"Original task: {self.original_task}\n\n"
        context += "Execution history:\n"
        for entry in self.execution_history:
            context += f"- Iteration {entry['iteration']}, {entry['agent']}: {entry['result'][:100]}...\n"
        return context


class AgentService:
    """Service for agent orchestration and execution."""
    
    # Store execution state for resuming
    _pending_executions: Dict[str, Dict[str, Any]] = {}
    # Store execution contexts for loop handling
    _execution_contexts: Dict[str, ExecutionContext] = {}
    
    @staticmethod
    async def execute_task(plan_id: str, session_id: str, task_description: str, require_hitl: bool = True) -> Dict[str, Any]:
        """
        Execute a task using the LangGraph agent workflow.
        Phase 7: Executes planner, then specialized agent, then HITL if enabled.
        
        Args:
            plan_id: Plan identifier
            session_id: Session identifier
            task_description: Task to execute
            require_hitl: Whether to require HITL approval (default True)
            
        Returns:
            Execution result with final output
        """
        logger.info(f"Executing task for plan {plan_id}")
        
        # Update plan status to in_progress
        await PlanRepository.update_status(plan_id, "in_progress")
        
        # Create execution context
        context = ExecutionContext(task_description, plan_id)
        AgentService._execution_contexts[plan_id] = context
        context.iteration_count = 1
        
        # Initialize state
        initial_state: AgentState = {
            "messages": [],
            "plan_id": plan_id,
            "session_id": session_id,
            "task_description": task_description,
            "current_agent": "",
            "next_agent": None,
            "final_result": "",
            "approval_required": False,
            "approved": None
        }
        
        try:
            # Execute planner node
            planner_result = planner_node(initial_state)
            
            # Send planner message via WebSocket
            planner_messages = planner_result.get("messages", [])
            for message_text in planner_messages:
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_message",
                    "data": {
                        "agent_name": "Planner",
                        "content": message_text,
                        "status": "in_progress",
                        "timestamp": datetime.utcnow().isoformat() + "Z"  # Ensure UTC timezone marker
                    }
                })
            
            # Add planner to history
            context.add_history_entry(
                context.iteration_count,
                "Planner",
                planner_messages[0] if planner_messages else "Task analyzed"
            )
            
            # Store execution state for resuming
            logger.info(f"🔍 DEBUG: Storing execution state with require_hitl={require_hitl} for plan {plan_id}")
            AgentService._pending_executions[plan_id] = {
                "session_id": session_id,
                "task_description": task_description,
                "next_agent": planner_result.get("next_agent"),
                "state": {**initial_state, **planner_result},
                "require_hitl": require_hitl
            }
            logger.info(f"🔍 DEBUG: Execution state stored: {list(AgentService._pending_executions[plan_id].keys())}")
            
            # Build plan data for approval request
            plan_steps = []
            if planner_result.get("messages"):
                for i, msg in enumerate(planner_result.get("messages", []), 1):
                    plan_steps.append({
                        "id": str(i),
                        "action": msg,
                        "agent": planner_result.get("current_agent", "Planner"),
                        "status": "pending"
                    })
            
            # Send approval request with complete plan data
            approval_msg = {
                "type": "plan_approval_request",
                "data": {
                    "id": plan_id,
                    "plan_id": plan_id,
                    "m_plan_id": plan_id,
                    "user_request": task_description,
                    "status": "pending_approval",
                    "steps": plan_steps,
                    "facts": f"Task: {task_description}\n\nRouting to: {planner_result.get('next_agent', 'Invoice').capitalize()} Agent",
                    "context": {
                        "participant_descriptions": {
                            planner_result.get("current_agent", "Planner"): "Analyzing task and creating execution plan"
                        }
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z"  # Ensure UTC timezone marker
                }
            }
            logger.info(f"🔔 SENDING APPROVAL REQUEST for plan {plan_id}")
            await websocket_manager.send_message(plan_id, approval_msg)
            logger.info(f"🔔 APPROVAL REQUEST SENT for plan {plan_id}")
            
            # Update plan status
            await PlanRepository.update_status(plan_id, "pending_approval")
            
            logger.info(f"Approval requested for plan {plan_id}")
            return {
                "status": "pending_approval",
                "message": "Waiting for human approval"
            }
            
        except Exception as e:
            logger.error(f"Task execution failed for plan {plan_id}: {e}")
            await PlanRepository.update_status(plan_id, "failed")
            raise
    
    @staticmethod
    async def resume_after_approval(plan_id: str, approved: bool, feedback: str = None) -> Dict[str, Any]:
        """
        Resume execution after approval decision.
        Phase 7: Executes specialized agent, then routes to HITL if enabled.
        
        **Feature: multi-agent-hitl-loop, Property 3: Approval Completion**
        **Validates: Requirements 1.3**
        
        Args:
            plan_id: Plan identifier
            approved: Whether plan was approved
            feedback: Optional feedback from user
            
        Returns:
            Execution result
        """
        logger.info(f"Resuming plan {plan_id} with approval={approved}")
        
        # Get stored execution state
        execution_state = AgentService._pending_executions.get(plan_id)
        if not execution_state:
            logger.error(f"No execution state found for plan {plan_id}")
            return {"status": "error", "message": "Cannot resume - no state found"}
        
        try:
            if not approved:
                # Plan rejected
                await PlanRepository.update_status(plan_id, "rejected")
                await websocket_manager.send_message(plan_id, {
                    "type": "final_result_message",
                    "data": {
                        "content": f"Plan rejected. {feedback or ''}",
                        "status": "rejected",
                        "timestamp": datetime.utcnow().isoformat() + "Z"  # Ensure UTC timezone marker
                    }
                })
                
                # Clean up
                AgentService._pending_executions.pop(plan_id, None)
                AgentService._execution_contexts.pop(plan_id, None)
                return {"status": "rejected"}
            
            # Plan approved - execute specialized agent
            await PlanRepository.update_status(plan_id, "in_progress")
            
            next_agent = execution_state.get("next_agent")
            state = execution_state.get("state")
            require_hitl = execution_state.get("require_hitl", True)
            
            # Execute the appropriate specialized agent
            if next_agent == "invoice":
                result = invoice_agent_node(state)
            elif next_agent == "closing":
                result = closing_agent_node(state)
            elif next_agent == "audit":
                result = audit_agent_node(state)
            else:
                result = {"messages": ["No specialized agent selected"], "final_result": "Task completed"}
            
            # Stream specialized agent messages via WebSocket
            agent_name = result.get("current_agent", next_agent.capitalize() if next_agent else "Unknown")
            messages = result.get("messages", [])
            
            for message_text in messages:
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_message",
                    "data": {
                        "agent_name": agent_name,
                        "content": message_text,
                        "status": "in_progress",
                        "timestamp": datetime.utcnow().isoformat() + "Z"  # Ensure UTC timezone marker
                    }
                })
            
            # Add specialized agent to history and track it
            context = AgentService._execution_contexts.get(plan_id)
            if context:
                context.add_history_entry(
                    context.iteration_count,
                    agent_name,
                    result.get("final_result", "Task completed")
                )
                # Store the current specialized agent for direct routing on revisions
                context.current_specialized_agent = next_agent
            
            # Check if HITL is required
            logger.info(f"🔍 DEBUG: require_hitl={require_hitl} for plan {plan_id}")
            logger.info(f"🔍 DEBUG: execution_state keys: {list(execution_state.keys())}")
            
            if not require_hitl:
                # Skip HITL and complete task
                logger.info(f"🔍 DEBUG: HITL is disabled, completing task for plan {plan_id}")
                await PlanRepository.update_status(plan_id, "completed")
                await websocket_manager.send_message(plan_id, {
                    "type": "final_result_message",
                    "data": {
                        "content": result.get("final_result", "Task completed"),
                        "status": "completed",
                        "timestamp": datetime.utcnow().isoformat() + "Z"  # Ensure UTC timezone marker
                    }
                })
                
                # Clean up
                AgentService._pending_executions.pop(plan_id, None)
                AgentService._execution_contexts.pop(plan_id, None)
                logger.info(f"Plan {plan_id} completed (HITL skipped)")
                return {"status": "completed"}
            
            # Route to HITL agent
            logger.info(f"🔍 DEBUG: Routing to HITL agent for plan {plan_id}")
            hitl_state = {**state, **result}
            logger.info(f"🔍 DEBUG: hitl_state keys: {list(hitl_state.keys())}")
            hitl_result = hitl_agent_node(hitl_state)
            logger.info(f"🔍 DEBUG: hitl_result keys: {list(hitl_result.keys())}")
            
            # Send HITL clarification request
            request_id = str(uuid.uuid4())
            agent_result = result.get("final_result", "")
            clarification_msg = {
                "type": "user_clarification_request",
                "data": {
                    "request_id": request_id,
                    "plan_id": plan_id,
                    "agent_result": agent_result,
                    "question": "Please approve or provide revision",
                    "timestamp": datetime.utcnow().isoformat() + "Z"  # Ensure UTC timezone marker
                }
            }
            
            logger.info(f"🔔 SENDING CLARIFICATION REQUEST for plan {plan_id}")
            logger.info(f"🔔 Agent result length: {len(agent_result)} chars")
            await websocket_manager.send_message(plan_id, clarification_msg)
            logger.info(f"🔔 CLARIFICATION REQUEST SENT for plan {plan_id}")
            
            # Update plan status to pending clarification
            await PlanRepository.update_status(plan_id, "pending_clarification")
            
            # Store clarification request ID for tracking
            execution_state["clarification_request_id"] = request_id
            
            logger.info(f"Clarification requested for plan {plan_id}")
            return {"status": "pending_clarification"}
            
        except Exception as e:
            logger.error(f"Resume execution failed for plan {plan_id}: {e}")
            await PlanRepository.update_status(plan_id, "failed")
            AgentService._pending_executions.pop(plan_id, None)
            AgentService._execution_contexts.pop(plan_id, None)
            raise
    
    @staticmethod
    async def handle_user_clarification(plan_id: str, request_id: str, answer: str) -> Dict[str, Any]:
        """
        Handle user clarification responses.
        Phase 7: Processes approval vs revision and loops back if needed.
        
        **Feature: multi-agent-hitl-loop, Property 4: Revision Loop**
        **Validates: Requirements 1.4, 2.3**
        
        Args:
            plan_id: Plan identifier
            request_id: Clarification request ID
            answer: User's response (approval or revision)
            
        Returns:
            Execution result
        """
        logger.info(f"Processing clarification for plan {plan_id}: {answer[:50]}...")
        
        # Get execution context
        context = AgentService._execution_contexts.get(plan_id)
        if not context:
            logger.error(f"No execution context found for plan {plan_id}")
            return {"status": "error", "message": "Cannot process clarification - no context found"}
        
        try:
            # Determine if this is approval or revision
            is_approval = answer.strip().upper() in ["OK", "YES", "APPROVE", "APPROVED"]
            
            if is_approval:
                # User approved - complete task
                logger.info(f"User approved plan {plan_id}")
                
                await PlanRepository.update_status(plan_id, "completed")
                await websocket_manager.send_message(plan_id, {
                    "type": "final_result_message",
                    "data": {
                        "content": "Task approved and completed successfully.",
                        "status": "completed",
                        "timestamp": datetime.utcnow().isoformat() + "Z"  # Ensure UTC timezone marker
                    }
                })
                
                # Clean up
                AgentService._pending_executions.pop(plan_id, None)
                AgentService._execution_contexts.pop(plan_id, None)
                
                return {"status": "completed"}
            
            else:
                # User provided revision - route directly to specialized agent (skip Planner)
                logger.info(f"User provided revision for plan {plan_id}")
                
                # Add user feedback to history
                context.add_history_entry(
                    context.iteration_count,
                    "HITL",
                    "Awaiting user feedback",
                    user_feedback=answer
                )
                
                # Increment iteration count
                context.iteration_count += 1
                
                # Get execution state
                execution_state = AgentService._pending_executions.get(plan_id)
                if not execution_state:
                    logger.error(f"No execution state found for plan {plan_id}")
                    return {"status": "error", "message": "Cannot resume - no state found"}
                
                # Update plan status to in_progress
                await PlanRepository.update_status(plan_id, "in_progress")
                
                # Send message indicating revision is being processed
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_message",
                    "data": {
                        "agent_name": "System",
                        "content": f"Processing revision: {answer}",
                        "status": "in_progress",
                        "timestamp": datetime.utcnow().isoformat() + "Z"  # Ensure UTC timezone marker
                    }
                })
                
                # Route directly to the specialized agent with the revision
                state = execution_state.get("state", {})
                state["task_description"] = answer  # Use the revision as the new task
                
                # Get the current specialized agent
                current_agent = context.current_specialized_agent
                logger.info(f"🔍 DEBUG: current_specialized_agent = {current_agent}")
                logger.info(f"Routing revision directly to {current_agent} agent for plan {plan_id}")
                
                if not current_agent:
                    logger.error(f"❌ ERROR: No specialized agent found for plan {plan_id}")
                    await websocket_manager.send_message(plan_id, {
                        "type": "agent_message",
                        "data": {
                            "agent_name": "System",
                            "content": "Error: No specialized agent found. Cannot process revision.",
                            "status": "error",
                            "timestamp": datetime.utcnow().isoformat() + "Z"  # Ensure UTC timezone marker
                        }
                    })
                    return {"status": "error", "message": "No specialized agent found"}
                
                # Execute the specialized agent with the revision
                if current_agent == "invoice":
                    result = invoice_agent_node(state)
                elif current_agent == "closing":
                    result = closing_agent_node(state)
                elif current_agent == "audit":
                    result = audit_agent_node(state)
                else:
                    logger.error(f"❌ ERROR: Unknown agent type: {current_agent}")
                    result = {"messages": [f"Unknown agent type: {current_agent}"], "final_result": "Task failed"}
                
                # Stream specialized agent messages via WebSocket
                agent_name = result.get("current_agent", current_agent.capitalize() if current_agent else "Unknown")
                messages = result.get("messages", [])
                
                for message_text in messages:
                    await websocket_manager.send_message(plan_id, {
                        "type": "agent_message",
                        "data": {
                            "agent_name": agent_name,
                            "content": message_text,
                            "status": "in_progress",
                            "timestamp": datetime.utcnow().isoformat() + "Z"  # Ensure UTC timezone marker
                        }
                    })
                
                # Add specialized agent to history
                context.add_history_entry(
                    context.iteration_count,
                    agent_name,
                    result.get("final_result", "Task completed")
                )
                
                # Update execution state
                execution_state["state"] = {**state, **result}
                
                # Route back to HITL agent
                request_id = str(uuid.uuid4())
                agent_result = result.get("final_result", "")
                clarification_msg = {
                    "type": "user_clarification_request",
                    "data": {
                        "request_id": request_id,
                        "plan_id": plan_id,
                        "agent_result": agent_result,
                        "question": "Please approve or provide revision",
                        "timestamp": datetime.utcnow().isoformat() + "Z"  # Ensure UTC timezone marker
                    }
                }
                
                logger.info(f"🔔 SENDING CLARIFICATION REQUEST for plan {plan_id}")
                logger.info(f"🔔 Agent result length: {len(agent_result)} chars")
                
                # Small delay to ensure all messages are sent before clarification request
                await asyncio.sleep(0.1)
                
                await websocket_manager.send_message(plan_id, clarification_msg)
                logger.info(f"🔔 CLARIFICATION REQUEST SENT for plan {plan_id}")
                
                # Update plan status to pending clarification
                await PlanRepository.update_status(plan_id, "pending_clarification")
                
                # Store clarification request ID for tracking
                execution_state["clarification_request_id"] = request_id
                
                return {"status": "pending_clarification", "iteration": context.iteration_count}
                
        except Exception as e:
            logger.error(f"Clarification handling failed for plan {plan_id}: {e}")
            await PlanRepository.update_status(plan_id, "failed")
            raise
