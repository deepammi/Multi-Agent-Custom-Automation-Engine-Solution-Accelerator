"""Agent orchestration service."""
import logging
import os
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
            "approved": None,
            "websocket_manager": websocket_manager,
            "llm_provider": None,
            "llm_temperature": None
        }
        
        try:
            # Execute planner node
            planner_result = planner_node(initial_state)
            
            # Track planner progress
            await PlanRepository.update_agent_progress(plan_id, "Planner", "planning completed")
            
            # Don't send planner message separately - it will be included in the approval request
            # This prevents duplicate messages in the UI
            planner_messages = planner_result.get("messages", [])
            
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
            
            # Create brief task summary for display (first 100 chars or first line)
            task_summary = task_description.split('\n')[0][:100]
            if len(task_description) > 100:
                task_summary += "..."
            
            # Send approval request with complete plan data
            approval_msg = {
                "type": "plan_approval_request",
                "data": {
                    "id": plan_id,
                    "plan_id": plan_id,
                    "m_plan_id": plan_id,
                    "user_request": task_summary,  # Use brief summary instead of full text
                    "status": "pending_approval",
                    "steps": plan_steps,
                    "facts": f"Routing to: {planner_result.get('next_agent', 'Invoice').capitalize()} Agent",  # Simplified facts
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
            
            # Track agent progress - agent is now processing
            agent_display_name = next_agent.capitalize() if next_agent else "Unknown"
            await PlanRepository.update_agent_progress(plan_id, f"{agent_display_name} Agent", "processing")
            
            # Execute the appropriate specialized agent
            if next_agent == "invoice":
                result = await invoice_agent_node(state)
            elif next_agent == "closing":
                result = closing_agent_node(state)
            elif next_agent == "audit":
                result = audit_agent_node(state)
            else:
                result = {"messages": ["No specialized agent selected"], "final_result": "Task completed"}
            
            # Check if extraction approval is required
            if result.get("requires_extraction_approval"):
                logger.info(f"📊 ===== EXTRACTION APPROVAL REQUIRED ===== [plan={plan_id}]")
                logger.info(f"📊 This will SKIP regular HITL approval [plan={plan_id}]")
                
                # Send extraction approval request
                extraction_result = result.get("extraction_result")
                if extraction_result:
                    # Store extraction data in plan for history display
                    # Convert to JSON-serializable format
                    invoice_dict = None
                    if extraction_result.invoice_data:
                        invoice_dict = extraction_result.invoice_data.model_dump()
                        # Convert dates and decimals to strings for MongoDB
                        for key, value in invoice_dict.items():
                            if hasattr(value, 'isoformat'):  # date/datetime
                                invoice_dict[key] = value.isoformat()
                            elif hasattr(value, '__str__') and key != 'line_items':  # Decimal
                                invoice_dict[key] = str(value)
                        
                        # Handle line items
                        if invoice_dict.get('line_items'):
                            for item in invoice_dict['line_items']:
                                for k, v in item.items():
                                    if hasattr(v, 'isoformat'):
                                        item[k] = v.isoformat()
                                    elif hasattr(v, '__str__') and k != 'description':
                                        item[k] = str(v)
                    
                    extraction_dict = {
                        "success": extraction_result.success,
                        "invoice_data": invoice_dict,
                        "validation_errors": extraction_result.validation_errors,
                        "extraction_time": extraction_result.extraction_time,
                        "model_used": extraction_result.model_used
                    }
                    await PlanRepository.update_extraction_data(plan_id, extraction_dict)
                    
                    # Track agent progress - waiting for extraction approval
                    await PlanRepository.update_agent_progress(plan_id, f"{agent_display_name} Agent", "waiting for input")
                    
                    await AgentService.send_extraction_approval_request(plan_id, extraction_result)
                    
                    # Update plan status to pending extraction approval
                    await PlanRepository.update_status(plan_id, "pending_extraction_approval")
                    
                    # Store state for resuming after approval
                    execution_state["state"] = {**state, **result}
                    execution_state["awaiting_extraction_approval"] = True
                    
                    logger.info(f"📊 Extraction approval requested, returning early [plan={plan_id}]")
                    return {"status": "pending_extraction_approval"}
            
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
            logger.info(f"🔍 ===== CHECKING HITL REQUIREMENT ===== [plan={plan_id}]")
            logger.info(f"🔍 require_hitl={require_hitl} [plan={plan_id}]")
            logger.info(f"🔍 execution_state keys: {list(execution_state.keys())}")
            
            if not require_hitl:
                # Skip HITL and complete task
                logger.info(f"🔍 HITL is disabled, completing task [plan={plan_id}]")
                
                # Track agent progress - completed
                await PlanRepository.update_agent_progress(plan_id, f"{agent_display_name} Agent", "completed")
                
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
            logger.info(f"🔍 ===== ROUTING TO HITL AGENT ===== [plan={plan_id}]")
            
            # Track agent progress - waiting for user input
            await PlanRepository.update_agent_progress(plan_id, f"{agent_display_name} Agent", "waiting for input")
            
            hitl_state = {**state, **result}
            hitl_result = hitl_agent_node(hitl_state)
            
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
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
            
            logger.info(f"🔔 ===== SENDING HITL CLARIFICATION REQUEST ===== [plan={plan_id}]")
            logger.info(f"🔔 Message type: user_clarification_request [plan={plan_id}]")
            await websocket_manager.send_message(plan_id, clarification_msg)
            logger.info(f"🔔 ===== HITL CLARIFICATION REQUEST SENT ===== [plan={plan_id}]")
            
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
                
                # Track agent progress - completed
                if context.current_specialized_agent:
                    agent_display_name = context.current_specialized_agent.capitalize()
                    await PlanRepository.update_agent_progress(plan_id, f"{agent_display_name} Agent", "completed")
                
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
                    result = await invoice_agent_node(state)
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
    
    @staticmethod
    async def send_extraction_approval_request(plan_id: str, extraction_result: Any) -> None:
        """
        Send extraction approval request via WebSocket.
        
        Args:
            plan_id: Plan identifier
            extraction_result: ExtractionResult object with invoice data
        """
        logger.info(f"📊 Sending extraction approval request for plan {plan_id}")
        
        try:
            # Format extraction data as JSON for display
            import json
            from app.models.invoice_schema import InvoiceData
            
            if extraction_result.invoice_data:
                invoice_dict = extraction_result.invoice_data.model_dump()
                # Convert dates and decimals to strings for JSON serialization
                for key, value in invoice_dict.items():
                    if hasattr(value, 'isoformat'):  # date/datetime
                        invoice_dict[key] = value.isoformat()
                    elif hasattr(value, '__str__') and key != 'line_items':  # Decimal
                        invoice_dict[key] = str(value)
                
                # Handle line items
                if invoice_dict.get('line_items'):
                    for item in invoice_dict['line_items']:
                        for k, v in item.items():
                            if hasattr(v, '__str__') and k != 'description':
                                item[k] = str(v)
            else:
                invoice_dict = None
            
            # Always provide visualization URL (visualization is generated during extraction)
            visualization_url = f"/api/v3/extraction/{plan_id}/visualize"
            logger.info(f"📊 Visualization URL: {visualization_url}")
            
            # Send extraction approval request
            approval_msg = {
                "type": "extraction_approval_request",
                "data": {
                    "plan_id": plan_id,
                    "extraction_result": {
                        "success": extraction_result.success,
                        "invoice_data": invoice_dict,
                        "validation_errors": extraction_result.validation_errors,
                        "extraction_time": extraction_result.extraction_time,
                        "model_used": extraction_result.model_used
                    },
                    "visualization_url": visualization_url,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
            
            logger.info(f"📊 ===== SENDING EXTRACTION APPROVAL REQUEST ===== [plan={plan_id}]")
            logger.info(f"📊 Message type: extraction_approval_request [plan={plan_id}]")
            await websocket_manager.send_message(plan_id, approval_msg)
            logger.info(f"📊 ===== EXTRACTION APPROVAL REQUEST SENT ===== [plan={plan_id}]")
            
        except Exception as e:
            logger.error(f"Failed to send extraction approval request for plan {plan_id}: {e}")
            raise
    
    @staticmethod
    async def handle_extraction_approval(plan_id: str, approved: bool, feedback: str = None, edited_data: dict = None) -> Dict[str, Any]:
        """
        Handle extraction approval/rejection.
        
        Args:
            plan_id: Plan identifier
            approved: Whether extraction was approved
            feedback: Optional feedback from user
            edited_data: Optional edited invoice data from user
            
        Returns:
            Status dict
        """
        logger.info(f"📊 Handling extraction approval for plan {plan_id}: approved={approved}")
        if edited_data:
            logger.info(f"📊 User provided edited data for plan {plan_id}")
        
        try:
            # Get stored execution state
            execution_state = AgentService._pending_executions.get(plan_id)
            if not execution_state:
                logger.error(f"No execution state found for plan {plan_id}")
                return {"status": "error", "message": "Cannot process approval - no state found"}
            
            if approved:
                # Extraction approved - store to database
                logger.info(f"✅ Extraction approved for plan {plan_id}")
                
                # Get extraction result from state
                state = execution_state.get("state", {})
                extraction_result = state.get("extraction_result")
                
                if extraction_result:
                    # If user provided edited data, update the extraction result
                    if edited_data:
                        logger.info(f"📊 Applying user edits to extraction for plan {plan_id}")
                        from app.models.invoice_schema import InvoiceData
                        try:
                            # Create new InvoiceData from edited JSON
                            edited_invoice = InvoiceData(**edited_data)
                            extraction_result.invoice_data = edited_invoice
                            logger.info(f"✅ Successfully applied user edits for plan {plan_id}")
                        except Exception as e:
                            logger.error(f"❌ Failed to apply user edits for plan {plan_id}: {e}")
                            await websocket_manager.send_message(plan_id, {
                                "type": "agent_message",
                                "data": {
                                    "agent_name": "System",
                                    "content": f"⚠️ Warning: Could not apply edits ({str(e)}). Using original extraction.",
                                    "status": "warning",
                                    "timestamp": datetime.utcnow().isoformat() + "Z"
                                }
                            })
                    
                    # Store extraction to database
                    from app.db.repositories import InvoiceExtractionRepository
                    
                    try:
                        extraction_id = await InvoiceExtractionRepository.store_extraction(
                            plan_id=plan_id,
                            extraction_result=extraction_result,
                            approved_by="user"
                        )
                        logger.info(f"📊 Stored extraction {extraction_id} for plan {plan_id}")
                        
                        # Send confirmation message
                        await websocket_manager.send_message(plan_id, {
                            "type": "agent_message",
                            "data": {
                                "agent_name": "System",
                                "content": f"✅ Invoice extraction approved and stored (ID: {extraction_id}).",
                                "status": "completed",
                                "timestamp": datetime.utcnow().isoformat() + "Z"
                            }
                        })
                    except Exception as e:
                        logger.error(f"Failed to store extraction for plan {plan_id}: {e}")
                        await websocket_manager.send_message(plan_id, {
                            "type": "agent_message",
                            "data": {
                                "agent_name": "System",
                                "content": f"⚠️ Extraction approved but storage failed: {str(e)}",
                                "status": "warning",
                                "timestamp": datetime.utcnow().isoformat() + "Z"
                            }
                        })
                else:
                    logger.warning(f"No extraction result found in state for plan {plan_id}")
                    await websocket_manager.send_message(plan_id, {
                        "type": "agent_message",
                        "data": {
                            "agent_name": "System",
                            "content": "✅ Invoice extraction approved.",
                            "status": "completed",
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                    })
                
                # Mark extraction as approved in state
                state["extraction_approved"] = True
                
                # Track agent progress - completed
                await PlanRepository.update_agent_progress(plan_id, "Invoice Agent", "completed")
                
                # Send final agent message with complete extraction results
                if extraction_result:
                    from app.services.langextract_service import LangExtractService
                    
                    # Format the complete extraction result for display
                    formatted_result = LangExtractService.format_extraction_result(extraction_result)
                    
                    # Send as Invoice Agent's final message
                    await websocket_manager.send_message(plan_id, {
                        "type": "agent_message",
                        "data": {
                            "agent_name": "Invoice",
                            "content": formatted_result,
                            "status": "completed",
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                    })
                    
                    logger.info(f"📊 Sent final extraction results as Invoice Agent message for plan {plan_id}")
                
                # Complete the task
                await PlanRepository.update_status(plan_id, "completed")
                await websocket_manager.send_message(plan_id, {
                    "type": "final_result_message",
                    "data": {
                        "content": "Invoice extraction completed and approved.",
                        "status": "completed",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                })
                
                # Clean up
                AgentService._pending_executions.pop(plan_id, None)
                AgentService._execution_contexts.pop(plan_id, None)
                
                return {"status": "completed"}
            
            else:
                # Extraction rejected
                logger.info(f"❌ Extraction rejected for plan {plan_id}")
                
                # Send rejection message
                rejection_msg = f"Invoice extraction rejected. {feedback or ''}"
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_message",
                    "data": {
                        "agent_name": "System",
                        "content": f"❌ {rejection_msg}",
                        "status": "rejected",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                })
                
                # Update plan status
                await PlanRepository.update_status(plan_id, "rejected")
                await websocket_manager.send_message(plan_id, {
                    "type": "final_result_message",
                    "data": {
                        "content": rejection_msg,
                        "status": "rejected",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                })
                
                # Clean up
                AgentService._pending_executions.pop(plan_id, None)
                AgentService._execution_contexts.pop(plan_id, None)
                
                return {"status": "rejected"}
                
        except Exception as e:
            logger.error(f"Extraction approval handling failed for plan {plan_id}: {e}")
            raise
