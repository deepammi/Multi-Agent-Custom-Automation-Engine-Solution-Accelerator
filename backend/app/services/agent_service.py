"""Agent orchestration service."""
import logging
from typing import Dict, Any
from datetime import datetime

from app.agents.graph import agent_graph
from app.agents.state import AgentState
from app.agents.nodes import planner_node, invoice_agent_node, closing_agent_node, audit_agent_node
from app.db.repositories import PlanRepository, MessageRepository
from app.models.message import AgentMessage
from app.services.websocket_service import websocket_manager

logger = logging.getLogger(__name__)


class AgentService:
    """Service for agent orchestration and execution."""
    
    # Store execution state for resuming
    _pending_executions: Dict[str, Dict[str, Any]] = {}
    
    @staticmethod
    async def execute_task(plan_id: str, session_id: str, task_description: str) -> Dict[str, Any]:
        """
        Execute a task using the LangGraph agent workflow.
        Phase 6: Executes planner only, then waits for approval.
        
        Args:
            plan_id: Plan identifier
            session_id: Session identifier
            task_description: Task to execute
            
        Returns:
            Execution result with final output
        """
        logger.info(f"Executing task for plan {plan_id}")
        
        # Update plan status to in_progress
        await PlanRepository.update_status(plan_id, "in_progress")
        
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
            # Execute only the planner node first
            planner_result = planner_node(initial_state)
            
            # Send planner message via WebSocket (don't store in DB yet to avoid duplicates)
            planner_messages = planner_result.get("messages", [])
            for message_text in planner_messages:
                # Send via WebSocket only
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_message",
                    "data": {
                        "agent_name": "Planner",
                        "content": message_text,
                        "status": "in_progress",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
            
            # Store execution state for resuming
            AgentService._pending_executions[plan_id] = {
                "session_id": session_id,
                "task_description": task_description,
                "next_agent": planner_result.get("next_agent"),
                "state": {**initial_state, **planner_result}
            }
            
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
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            logger.info(f"🔔 SENDING APPROVAL REQUEST for plan {plan_id}")
            logger.info(f"🔔 Approval message: {approval_msg}")
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
        Phase 6: Executes specialized agent based on approval.
        
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
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
                
                # Clean up
                AgentService._pending_executions.pop(plan_id, None)
                return {"status": "rejected"}
            
            # Plan approved - execute specialized agent
            await PlanRepository.update_status(plan_id, "in_progress")
            
            next_agent = execution_state.get("next_agent")
            state = execution_state.get("state")
            
            # Execute the appropriate specialized agent
            if next_agent == "invoice":
                result = invoice_agent_node(state)
            elif next_agent == "closing":
                result = closing_agent_node(state)
            elif next_agent == "audit":
                result = audit_agent_node(state)
            else:
                result = {"messages": ["No specialized agent selected"], "final_result": "Task completed"}
            
            # Stream specialized agent messages via WebSocket (don't store to avoid duplicates)
            agent_name = result.get("current_agent", next_agent.capitalize() if next_agent else "Unknown")
            messages = result.get("messages", [])
            
            for message_text in messages:
                # Send agent_message via WebSocket only
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_message",
                    "data": {
                        "agent_name": agent_name,
                        "content": message_text,
                        "status": "in_progress",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
            
            # Update plan status to completed
            await PlanRepository.update_status(plan_id, "completed")
            
            # Send final_result_message via WebSocket
            await websocket_manager.send_message(plan_id, {
                "type": "final_result_message",
                "data": {
                    "content": result.get("final_result", "Task completed"),
                    "status": "completed",
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
            
            # Clean up
            AgentService._pending_executions.pop(plan_id, None)
            
            logger.info(f"Plan {plan_id} execution completed after approval")
            return {"status": "completed"}
            
        except Exception as e:
            logger.error(f"Resume execution failed for plan {plan_id}: {e}")
            await PlanRepository.update_status(plan_id, "failed")
            AgentService._pending_executions.pop(plan_id, None)
            raise
